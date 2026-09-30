"""Variants of Emezomm (L.A.S.T universe and others): same model, same face, same animations -
only the texture of the body / arms / legs changes (the outfit), plus optionally the fur colour.

usage: python3 tools/variante.py <base.bbmodel> <skin64.png> <out.bbmodel> [--hide group,group,...]

- The 64x64 skin is read in the standard Minecraft layout; the outer layer (jacket, sleeves, pants) is merged
  onto the base layer. Pixels with alpha < 128 are ignored (eraser leftovers).
- The head is never touched (the face is the same in every variant).
- Each face of body / arms / legs is redrawn at the model resolution (2 px per unit): Scale2x keeps the pixel-art
  look but smooths diagonals, then a light fabric finish (dither on large flat areas, soft shading from top
  to bottom and a darker seam where two materials meet).
- Tufts covered by the clothes (--hide) are pointed at a transparent texel: the geometry stays, they just
  don't show.
"""
import sys, json, base64, io, zlib
import numpy as np
from PIL import Image

LIMBS = {  # model element -> standard skin origin of (base, overlay) box, box size (w, h, d)
    'body': ((16, 16), (16, 32), (8, 12, 4)),
    'right_arm': ((40, 16), (40, 32), (4, 12, 4)),
    'left_arm': ((32, 48), (48, 48), (4, 12, 4)),
    'right_leg': ((0, 16), (0, 32), (4, 12, 4)),
    'left_leg': ((16, 48), (0, 48), (4, 12, 4)),
}


def box_faces(ox, oy, w, h, dd):
    """standard skin box layout -> {blockbench face: (x, y, w, h)}; +X = the character's right = east."""
    return {'east': (ox, oy + dd, dd, h), 'north': (ox + dd, oy + dd, w, h),
            'west': (ox + dd + w, oy + dd, dd, h), 'south': (ox + 2 * dd + w, oy + dd, w, h),
            'up': (ox + dd, oy, w, dd), 'down': (ox + dd + w, oy, w, dd)}


def scale2x(a):
    """EPX / Scale2x on an RGBA array (h, w, 4) -> (2h, 2w, 4)."""
    h, w = a.shape[:2]
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    out = np.zeros((2 * h, 2 * w, 4), a.dtype)
    eq = lambda x, y: np.all(x == y, axis=-1)
    for y in range(h):
        for x in range(w):
            P = p[y + 1, x + 1]
            A, B, C, D = p[y, x + 1], p[y + 1, x + 2], p[y + 1, x], p[y + 2, x + 1]   # up, right, left, down
            o = [P.copy() for _ in range(4)]
            if eq(C, A) and not eq(C, D) and not eq(A, B):
                o[0] = A
            if eq(A, B) and not eq(A, C) and not eq(B, D):
                o[1] = B
            if eq(D, C) and not eq(D, B) and not eq(C, A):
                o[2] = C
            if eq(B, D) and not eq(B, A) and not eq(D, C):
                o[3] = D
            out[2 * y, 2 * x], out[2 * y, 2 * x + 1], out[2 * y + 1, 2 * x], out[2 * y + 1, 2 * x + 1] = o
    return out


def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def finish(a, seed=0):
    """Light fabric finish on an upscaled face (keeps the palette readable, no realism)."""
    a = a.astype(float)
    h, w = a.shape[:2]
    L = lum(a)
    rgb = a[..., :3]
    # soft light from the top: +4% at the top edge -> -5% at the bottom edge
    k = np.linspace(1.04, 0.95, h)[:, None, None]
    rgb *= k
    # seams: a pixel next to a clearly darker material gets a touch darker (reads as a fold / stitch)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = np.roll(np.roll(L, dy, 0), dx, 1)
        edge = (L - nb) > 60
        if dy == 1: edge[0, :] = False
        if dy == -1: edge[-1, :] = False
        if dx == 1: edge[:, 0] = False
        if dx == -1: edge[:, -1] = False
        rgb[edge] *= 0.9
    # dither on flat areas (checker, +-1.2 %), so big panels are not a single flat colour
    yy, xx = np.mgrid[0:h, 0:w]
    rng = np.random.default_rng(seed)
    flat = np.ones((h, w), bool)
    for dy, dx in ((0, 1), (1, 0)):
        flat &= np.abs(L - np.roll(np.roll(L, dy, 0), dx, 1)) < 8
    noise = np.where((xx + yy) % 2 == 0, 1.012, 0.988) * (1 + rng.uniform(-0.006, 0.006, (h, w)))
    rgb[flat] *= noise[flat][:, None]
    a[..., :3] = np.clip(rgb, 0, 255)
    return a.round().astype(np.uint8)


def main():
    base, skin_path, out = sys.argv[1:4]
    hide = []
    if '--hide' in sys.argv:
        hide = sys.argv[sys.argv.index('--hide') + 1].split(',')
    d = json.load(open(base))
    tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
    T = np.array(tex)
    sk = np.array(Image.open(skin_path).convert('RGBA'))
    sk[sk[..., 3] < 128] = 0
    E = {e['name']: e for e in d['elements']}

    for part, ((bx, by), (ox, oy), (w, h, dd)) in LIMBS.items():
        fb, fo = box_faces(bx, by, w, h, dd), box_faces(ox, oy, w, h, dd)
        for i, (face, (x, y, fw, fh)) in enumerate(fb.items()):
            img = Image.fromarray(sk[y:y + fh, x:x + fw].copy())
            xo, yo = fo[face][:2]
            img.alpha_composite(Image.fromarray(sk[yo:yo + fh, xo:xo + fw].copy()))
            a = np.array(img)
            a[..., 3] = 255                                   # base layer is opaque
            if face == 'up':
                a = a[::-1]                                   # skin top: front at the bottom; model: at the top
            sm, nn = scale2x(a), a.repeat(2, 0).repeat(2, 1)
            # coloured details (logos, badges) stay crisp: no smoothing where a saturated colour is involved
            sat = lambda c: (c[..., :3].max(-1).astype(int) - c[..., :3].min(-1)) > 60
            keep = sat(sm) | sat(nn)
            sm[keep] = nn[keep]
            big = finish(sm, seed=zlib.crc32((part + face).encode()))
            u0, v0, u1, v1 = E[part]['faces'][face]['uv']
            x0, y0, x1, y1 = int(min(u0, u1)), int(min(v0, v1)), int(max(u0, u1)), int(max(v0, v1))
            assert (x1 - x0, y1 - y0) == (2 * fw, 2 * fh), (part, face)
            if u0 > u1: big = big[:, ::-1]
            if v0 > v1: big = big[::-1]
            T[y0:y1, x0:x1] = big

    # tufts under the clothes: point every face at one transparent texel that no face uses
    if hide:
        used = np.zeros((128, 128), bool)
        for e in d['elements']:
            for fc in e['faces'].values():
                if fc.get('texture') is None: continue
                u0, v0, u1, v1 = fc['uv']
                used[int(min(v0, v1)):int(np.ceil(max(v0, v1))), int(min(u0, u1)):int(np.ceil(max(u0, u1)))] = True
        free = np.argwhere((T[..., 3] == 0) & ~used)
        ty, tx = free[-1]
        G = {g['uuid']: g['name'] for g in d['groups']}
        members = set()

        def walk(nodes, inside):
            for n in nodes:
                if isinstance(n, dict):
                    walk(n['children'], inside or G[n['uuid']] in hide)
                elif inside:
                    members.add(n)
        walk(d['outliner'], False)
        for e in d['elements']:
            if e['uuid'] in members:
                for fc in e['faces'].values():
                    if fc.get('texture') is not None:
                        fc['uv'] = [int(tx), int(ty), int(tx) + 1, int(ty) + 1]
        print('hidden elements:', len(members), 'texel', (int(tx), int(ty)))

    im = Image.fromarray(T)
    buf = io.BytesIO(); im.save(buf, 'PNG')
    d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    name = out.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    png = name.replace('skin_', 'Emezomm-CPM_') + '_128.png'
    d['textures'][0]['name'] = d['textures'][0]['relative_path'] = png
    d['name'] = name
    json.dump(d, open(out, 'w'))
    im.save(out.rsplit('/', 1)[0] + '/' + png)
    print('ok', out, png)


if __name__ == '__main__':
    main()
