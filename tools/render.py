"""Minimal software renderer for Blockbench (.bbmodel) cube models -> PNG previews."""
import json, base64, io, sys, math
import numpy as np
from PIL import Image


def rotmat(r):
    rx, ry, rz = [math.radians(a) for a in r]
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X  # Blockbench cube euler order ZYX


def face_quads(e):
    f = np.array(e['from'], float); t = np.array(e['to'], float)
    inf = e.get('inflate', 0) or 0
    f -= inf; t += inf
    x0, y0, z0 = f; x1, y1, z1 = t
    # corners ordered: top-left, top-right, bottom-right, bottom-left (as seen from outside)
    Q = {
        'north': [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
        'south': [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
        'east':  [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        'west':  [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        'up':    [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        'down':  [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }
    R = rotmat(e.get('rotation', [0, 0, 0]))
    o = np.array(e.get('origin', [0, 0, 0]), float)
    out = []
    for name, pts in Q.items():
        fc = e['faces'].get(name)
        if not fc or fc.get('texture') is None:
            continue
        P = (np.array(pts) - o) @ R.T + o
        u0, v0, u1, v1 = fc['uv']
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        rot = fc.get('rotation', 0) // 90
        uv = uv[-rot:] + uv[:-rot] if rot else uv
        out.append((P, np.array(uv, float)))
    return out


def load(path, pose=None, data=None):
    """pose: {group name: (rot_delta_xyz, pos_delta_xyz, scale_xyz)} in model convention."""
    d = data if data is not None else json.load(open(path))
    pose = pose or {}
    src = d['textures'][0]['source'].split(',', 1)[1]
    tex = np.array(Image.open(io.BytesIO(base64.b64decode(src))).convert('RGBA')).astype(float)
    els = {e['uuid']: e for e in d['elements']}
    grps = {g['uuid']: g for g in d['groups']}
    quads = []

    def walk(node, chain):
        if isinstance(node, str):
            e = els.get(node)
            if not e or e.get('visibility') is False or e.get('type', 'cube') != 'cube':
                return
            for P, UV in face_quads(e):
                UV = UV * (128.0 / d.get('resolution', {}).get('width', 128))   # render() assumes 128 units
                for g in reversed(chain):  # innermost group first
                    dr, dp, ds = pose.get(g['name'], ((0, 0, 0), (0, 0, 0), (1, 1, 1)))
                    R = rotmat([a + b for a, b in zip(g.get('rotation', [0, 0, 0]), dr)])
                    o = np.array(g['origin'], float)
                    P = ((P - o) * np.array(ds, float)) @ R.T + o + np.array(dp, float)
                quads.append((P, UV))
            return
        g = grps[node['uuid']]
        if g.get('visibility') is False:
            return
        for ch in node['children']:
            walk(ch, chain + [g])

    for n in d['outliner']:
        walk(n, [])
    return quads, tex, d


def render(quads, tex, yaw=0, pitch=0, size=(480, 640), center=(0, 17, 0), scale=16, bg=(190, 205, 230), cull=False):
    W, H = size
    th, tw = tex.shape[:2]
    uvs = np.array([tw / 128.0, th / 128.0])
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    # camera looks from -Z toward +Z at yaw=0 (front view)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    M = Rx @ Ry
    img = np.zeros((H, W, 3)); img[:] = bg
    zb = np.full((H, W), np.inf)
    light = np.array([0.35, 0.8, -0.5]); light /= np.linalg.norm(light)
    c = np.array(center, float)
    for P, UV in quads:
        V = (P - c) @ M.T
        n = np.cross(P[1] - P[0], P[3] - P[0])
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n /= nn
        shade = 0.55 + 0.45 * max(0.0, float(n @ light))
        if cull and float((M @ n)[2]) < 0:     # back face (n here is the inward normal)
            continue
        # screen: x -> -X world at front view (player's right shows on viewer's left)
        sx = W / 2 - V[:, 0] * scale
        syy = H / 2 - V[:, 1] * scale
        depth = V[:, 2]
        for tri in ((0, 1, 2), (0, 2, 3)):
            ax, ay = sx[list(tri)], syy[list(tri)]
            xmin, xmax = int(max(0, math.floor(ax.min()))), int(min(W - 1, math.ceil(ax.max())))
            ymin, ymax = int(max(0, math.floor(ay.min()))), int(min(H - 1, math.ceil(ay.max())))
            if xmin > xmax or ymin > ymax:
                continue
            X, Y = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            x0, x1, x2 = ax; y0, y1, y2 = ay
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            w0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
            w1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not m.any():
                continue
            t = [UV[i] * uvs for i in tri]
            u = w0 * t[0][0] + w1 * t[1][0] + w2 * t[2][0]
            v = w0 * t[0][1] + w1 * t[1][1] + w2 * t[2][1]
            z = w0 * depth[tri[0]] + w1 * depth[tri[1]] + w2 * depth[tri[2]]
            ui = np.clip(np.floor(u).astype(int), 0, tw - 1)
            vi = np.clip(np.floor(v).astype(int), 0, th - 1)
            col = tex[vi, ui]
            m &= col[..., 3] > 127
            sub = zb[ymin:ymax + 1, xmin:xmax + 1]
            m &= z < sub
            if not m.any():
                continue
            sub[m] = z[m]
            img[ymin:ymax + 1, xmin:xmax + 1][m] = col[..., :3][m] * shade
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def sheet(path, out):
    quads, tex, _ = load(path)
    views = [(0, 5), (90, 5), (180, 5), (-90, 5), (35, 10)]
    ims = [render(quads, tex, yaw=y, pitch=p) for y, p in views]
    heads = [render(quads, tex, yaw=y, pitch=p, size=(360, 360), center=(0, 29, 0), scale=26)
             for y, p in [(0, 0), (90, 0), (180, 0), (35, 15)]]
    W = sum(i.width for i in ims)
    S = Image.new('RGB', (W, 640 + 360), (190, 205, 230))
    x = 0
    for i in ims:
        S.paste(i, (x, 0)); x += i.width
    x = 0
    for i in heads:
        S.paste(i, (x, 640)); x += i.width
    S.save(out)


if __name__ == '__main__':
    sheet(sys.argv[1], sys.argv[2])
