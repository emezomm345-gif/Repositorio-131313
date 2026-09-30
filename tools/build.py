"""Adds layered 2D fur tufts (head top/back/sides, cheeks, chest) to the CPM bbmodel.
Each lock gets its own texture, coloured from the skin right under it (root = exact skin colour).

usage: python3 tools/build.py <original.bbmodel> <output.bbmodel>
"""
import json, base64, io, math, os, uuid, copy, sys
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex_src = d['textures'][0]['source'].split(',', 1)[1]
tex = Image.open(io.BytesIO(base64.b64decode(tex_src))).convert('RGBA')
T = tex.load()

ORIG = tex.copy()          # untouched skin, used to sample the colour under every lock
O = ORIG.load()
PPU = 2  # texture pixels per model unit (same density as the skin)

# Short, slightly drooping locks. Row 0 = tips, last row = root. '.' = transparent.
# The colour of every pixel is taken from the skin right under it; the letter only says
# how it is shaded: M = same as skin, S = a bit darker, L = a bit lighter.
# The root rows stay exactly the skin colour, so the fur looks like it grows out of the body.
ART = {
    'row16': [".L.....L....L...",
              "LMS..L.MS..LMS.L",
              "MMS.LMSMMS.MMMSM",
              "MMMSMMMMMMSMMMMM",
              "MMMMMMMMMMMMMMMM"],
    'row12': ["..L.....L...",
              ".LMS...LMS.L",
              ".MMS.LMMMSLM",
              "LMMMSMMMMSMM",
              "MMMMMMMMMMMM"],
    'row8':  [".L....L.",
              "LMS..LMS",
              "MMS.LMMS",
              "MMMSMMMM",
              "MMMMMMMM"],
    'lock':  ["..L...",
              ".LMS..",
              ".MMS.L",
              "LMMSLM",
              "MMMMMS",
              "MMMMMM"],
}

# every opaque colour the skin already uses: fur pixels are snapped to this palette
_px = np.array(ORIG).reshape(-1, 4)
_cols, _cnt = np.unique(_px[_px[:, 3] == 255][:, :3], axis=0, return_counts=True)
PALETTE = _cols[_cnt >= 3].astype(float)


def snap(c):
    return tuple(int(v) for v in PALETTE[np.argmin(((PALETTE - c) ** 2).sum(1))])


def shade(c, ch, k):
    """c = skin colour under the pixel, ch = ART letter, k = rows away from the root."""
    lum = sum(c) / 3
    dark, light = (-5, 7) if lum < 70 else (-12, 10) if lum < 170 else (-16, 9)
    delta = {'M': 0, 'S': dark, 'L': light}[ch]
    ramp = (0.0, 0.5, 1.0)[min(k, 2)]              # root = pure skin -> full shading
    return snap(np.clip(np.array(c, float) + delta * ramp, 0, 255))


# ---------------------------------------------------------------- skin sampling
ELS = {e['name']: e for e in d['elements']}
FACE_BY_NORMAL = {(1, 0, 0): 'east', (-1, 0, 0): 'west', (0, 1, 0): 'up', (0, -1, 0): 'down',
                  (0, 0, -1): 'north', (0, 0, 1): 'south'}


def face_corners(e, face):
    """TL, TR, BL corners of an (unrotated) cube face, matching Blockbench uv orientation."""
    (x0, y0, z0), (x1, y1, z1) = e['from'], e['to']
    return {
        'north': ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
        'south': ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
        'east':  ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        'west':  ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
        'up':    ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
        'down':  ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0)),
    }[face]


def skin_at(p, normal, bases):
    """Skin colour on the surface point p (face picked by the surface normal)."""
    face = FACE_BY_NORMAL[tuple(int(round(v)) for v in normal)]
    for name in bases:
        e = ELS[name]
        tl, tr, bl = (np.array(c, float) for c in face_corners(e, face))
        ex, ey = tr - tl, bl - tl
        s = min(max((p - tl) @ ex / (ex @ ex), 0), 0.999)
        t = min(max((p - tl) @ ey / (ey @ ey), 0), 0.999)
        u0, v0, u1, v1 = e['faces'][face]['uv']
        c = O[int(u0 + s * (u1 - u0)), int(v0 + t * (v1 - v0))]
        if c[3] == 255:
            return c[:3]
    return c[:3]


# ---------------------------------------------------------------- atlas (texture areas no face uses)
FREE = [(0, 108, 124, 16), (0, 16, 64, 16), (16, 48, 32, 16), (0, 0, 40, 8), (0, 8, 32, 8)]
for fx, fy, fw, fh in FREE:
    for y in range(fy, fy + fh):
        for x in range(fx, fx + fw):
            T[x, y] = (0, 0, 0, 0)
SHELF = 6
_shelves = [[fx, fy + i * SHELF, fx + fw] for fx, fy, fw, fh in FREE for i in range(fh // SHELF)]


def alloc(w, h):
    assert h <= SHELF
    for sh in _shelves:
        if sh[0] + w <= sh[2]:
            u = sh[0]; sh[0] += w
            return u, sh[1]
    raise RuntimeError('texture atlas full')


# ---------------------------------------------------------------- geometry helpers
def euler_zyx(R):
    b = math.asin(max(-1, min(1, -R[2, 0])))
    a = math.atan2(R[2, 1], R[2, 2])
    c = math.atan2(R[1, 0], R[0, 0])
    return [round(math.degrees(a), 3), round(math.degrees(b), 3), round(math.degrees(c), 3)]


def norm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


BLANK = [127, 127, 128, 128]
r4 = lambda v: round(float(v), 4)


def card(name, sprite, root, flow, normal, tilt=22, scale=1.0, flip=False, bases=('head',)):
    """One fur card. `root` sits on the surface, the locks hang along `flow` (a direction
    tangent to the surface) and lift `tilt` degrees away from it along `normal`.
    The element pivot is the root, so rotating it swings the lock like real fur."""
    fl, n = norm(flow), norm(normal)
    fl = norm(fl - (fl @ n) * n)
    t = math.radians(tilt)
    up = norm(math.cos(t) * fl + math.sin(t) * n)          # root -> tips
    face = norm(n - (n @ up) * up)                          # side we look at
    k = -face
    r = np.cross(up, k)
    R = np.column_stack([r, up, k])
    rows = ART[sprite.split('_', 1)[1]]
    sw, sh = len(rows[0]), len(rows)
    su, sv = alloc(sw, sh)
    w, h = sw / PPU * scale, sh / PPU * scale
    surf = np.array(root, float)
    root = surf + n * 0.03
    for j, row in enumerate(rows):                  # paint this lock from the skin under it
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            lx = (-w / 2 + (i + 0.5) * w / sw) if flip else (w / 2 - (i + 0.5) * w / sw)
            ly = h - (j + 0.5) * h / sh
            p = root + R @ np.array([lx, ly, 0.0])
            p = p - ((p - surf) @ n) * n            # drop it onto the body surface
            T[su + i, sv + j] = shade(skin_at(p, n, bases), ch, sh - 1 - j) + (255,)
    front = [su + sw, sv, su, sv + sh] if flip else [su, sv, su + sw, sv + sh]
    back = [front[2], front[1], front[0], front[3]]
    faces = {f: {'uv': BLANK, 'texture': 0} for f in ('east', 'west', 'up', 'down')}
    faces['north'] = {'uv': front, 'texture': 0}
    faces['south'] = {'uv': back, 'texture': 0}
    bx, by, bz = root
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [r4(bx - w / 2), r4(by), r4(bz - 0.02)],
        'to': [r4(bx + w / 2), r4(by + h), r4(bz + 0.02)],
        'autouv': 0, 'color': 2, 'rotation': euler_zyx(R), 'origin': [r4(bx), r4(by), r4(bz)],
        'faces': faces, 'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


def mx(v):
    return [-v[0], v[1], v[2]]


def side(sign, specs):
    """specs are written for the right side (+X); sign=-1 mirrors them to the left."""
    out = []
    for name, sprite, root, flow, normal, *rest in specs:
        tilt = rest[0] if rest else 22
        scale = rest[1] if len(rest) > 1 else 1.0
        if sign < 0:
            name, root, flow, normal = name.replace('_R', '_L'), mx(root), mx(flow), mx(normal)
        out.append((name, sprite, root, flow, normal, tilt, scale, sign < 0))
    return out


# ---------------------------------------------------------------- layout
# Head cube: x -4..4, y 24..32, z -4..4 (front = -Z). Jacket front: z = -2.15.
# (name, sprite, root, flow (hang direction), surface normal, tilt°, scale)
UP, DOWN, BACK, FRONT, RIGHT = (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (1, 0, 0)

HEAD_TOP = [  # rows lying on the head, flowing back, each one overlapping the next
    ('fur_top_1', 'dk_row12', (0.3, 32, -3.3), (0, 0, 1), UP, 30, 0.85),
    ('fur_top_2', 'dk_row16', (0, 32, -1.5), (0, 0, 1), UP, 26, 0.95),
    ('fur_top_3', 'dk_row16', (0.2, 32, 0.5), (0, 0, 1), UP, 24, 1.0),
    ('fur_top_4', 'dk_row16', (0, 32, 2.4), (0, -0.25, 1), UP, 22, 1.05),
]
HEAD_BACK = [  # rows hanging down the back of the head, last one over the nape
    ('fur_back_1', 'dk_row16', (0, 31.9, 4), DOWN, BACK, 24, 1.05),
    ('fur_back_2', 'dk_row16', (0.2, 30.0, 4), DOWN, BACK, 22, 1.05),
    ('fur_back_3', 'dk_row16', (-0.2, 28.1, 4), DOWN, BACK, 20, 1.05),
    ('fur_back_4', 'dk_row16', (0, 26.2, 4), DOWN, BACK, 20, 1.0),
]
SIDE_R = [  # rows hanging down/back along the side of the head
    ('fur_side_R_1', 'dk_row16', (4, 31.8, 0.4), (0, -1, 0.35), RIGHT, 24, 0.9),
    ('fur_side_R_2', 'dk_row16', (4, 29.9, 0.8), (0, -1, 0.4), RIGHT, 22, 0.85),
    ('fur_side_R_3', 'dk_row12', (4, 28.0, 1.8), (0, -1, 0.45), RIGHT, 22, 0.85),
    ('fur_side_R_4', 'dk_lock', (4, 27.0, 3.3), (0, -1, 0.6), RIGHT, 28, 0.9),
]
CHEEK_R = [  # white cheek fluff hanging down/back, plus one lock seen from the front
    ('fur_cheek_R_1', 'wt_row12', (4, 26.6, -1.9), (0, -1, 0.55), RIGHT, 28, 0.6),
    ('fur_cheek_R_2', 'wt_row8', (4, 25.3, -1.6), (0, -1, 0.5), RIGHT, 30, 0.75),
    ('fur_cheek_R_front', 'wt_lock', (3.8, 25.6, -3.0), (0.6, -1, 0.1), FRONT, 12, 0.85),
]
CHEST_ROWS = [  # white rows stacked down the chest, narrowing towards the belly
    ('fur_chest_1', 'wt_row16', (0, 24.3, -2.15), DOWN, FRONT, 26, 0.8),
    ('fur_chest_2', 'wt_row12', (0.1, 22.6, -2.15), DOWN, FRONT, 24, 0.95),
    ('fur_chest_3', 'wt_row12', (-0.1, 20.9, -2.15), DOWN, FRONT, 22, 0.8),
    ('fur_chest_4', 'wt_row8', (0.1, 19.2, -2.15), DOWN, FRONT, 20, 0.95),
    ('fur_chest_5', 'wt_row8', (0, 17.5, -2.15), DOWN, FRONT, 18, 0.75),
    ('fur_chest_6', 'wt_row8', (0, 15.8, -2.15), DOWN, FRONT, 16, 0.55),
]
CHEST_EDGE_R = [
    ('fur_chest_edge_R_1', 'wt_lock', (2.6, 23.9, -2.15), (0.5, -1, 0), FRONT, 18, 0.8),
    ('fur_chest_edge_R_2', 'wt_lock', (2.0, 21.8, -2.15), (0.4, -1, 0), FRONT, 18, 0.7),
]


# ---------------------------------------------------------------- groups
TEMPLATE = next(x for x in d['groups'] if x['name'] == 'bone2')


def find_node(nodes, gid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == gid:
                return n
            f = find_node(n['children'], gid)
            if f:
                return f
    return None


def group(name, parent, pivot, specs=(), bases=('head',)):
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[r4(v) for v in pivot], rotation=[0, 0, 0])
    d['groups'].append(g)
    kids = []
    for s in specs:
        e = card(*s, bases=bases)
        d['elements'].append(e)
        kids.append(e['uuid'])
    find_node(d['outliner'], parent)['children'].append({'uuid': g['uuid'], 'isOpen': False, 'children': kids})
    return g['uuid']


head = next(g for g in d['groups'] if g['name'] == 'head')['uuid']
body = next(g for g in d['groups'] if g['name'] == 'body')['uuid']

fur_head = group('fur_head', head, (0, 24, 0))
group('fur_top', fur_head, (0, 32, -0.5), HEAD_TOP)
group('fur_back', fur_head, (0, 29, 4), HEAD_BACK)
group('fur_side_R', fur_head, (4, 29.8, 1.2), side(1, SIDE_R))
group('fur_side_L', fur_head, (-4, 29.8, 1.2), side(-1, SIDE_R))
group('fur_cheek_R', fur_head, (4, 26, -2.2), side(1, CHEEK_R))
group('fur_cheek_L', fur_head, (-4, 26, -2.2), side(-1, CHEEK_R))

fur_chest = group('fur_chest', body, (0, 24, -2.15))
group('fur_chest_rows', fur_chest, (0, 24.3, -2.15), CHEST_ROWS, ('jacket', 'body'))
group('fur_chest_edge_R', fur_chest, (2.3, 23, -2.15), side(1, CHEST_EDGE_R), ('jacket', 'body'))
group('fur_chest_edge_L', fur_chest, (-2.3, 23, -2.15), side(-1, CHEST_EDGE_R), ('jacket', 'body'))

# ---------------------------------------------------------------- save
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_11_128_tufos.png'
d['name'] = d['name'] + '_tufos'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok', len(d['elements']), 'elements')
