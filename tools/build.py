"""Adds layered 2D fur tufts (head top/back/sides, cheeks, chest) to the CPM bbmodel.

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

# ---------------------------------------------------------------- palette (sampled from the skin)
# R = deepest shade (spare), S = shade / root, M = main, L = light tip
DARK = {'R': (16, 16, 16), 'S': (19, 19, 19), 'M': (24, 23, 23), 'L': (31, 30, 28)}      # head fur
WHITE = {'R': (200, 200, 200), 'S': (215, 215, 215), 'M': (232, 232, 232), 'L': (244, 244, 244)}  # chest / cheeks

PPU = 2  # texture pixels per model unit (same density as the skin)

# Short, slightly drooping locks. Row 0 = tips, last row = root. '.' = transparent.
ART = {
    'row16': [".L.....L....L...",
              "LMS..L.MS..LMS.L",
              "MMS.LMSMMS.MMMSM",
              "MMMSMMMMMMSMMMMM",
              "SSSSSSSSSSSSSSSS"],
    'row12': ["..L.....L...",
              ".LMS...LMS.L",
              ".MMS.LMMMSLM",
              "LMMMSMMMMSMM",
              "SSSSSSSSSSSS"],
    'row8':  [".L....L.",
              "LMS..LMS",
              "MMS.LMMS",
              "MMMSMMMM",
              "SSSSSSSS"],
    'lock':  ["..L...",
              ".LMS..",
              ".MMS.L",
              "LMMSLM",
              "MMMMMS",
              "SSSSSS"],
}


def paint(u, v, key, pal):
    rows = ART[key]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            T[u + x, v + y] = (0, 0, 0, 0) if ch == '.' else pal[ch] + (255,)
    return (u, v, len(rows[0]), len(rows))


# atlas lives in texture rows no face references (y 108..121)
for y in range(108, 122):
    for x in range(0, 124):
        T[x, y] = (0, 0, 0, 0)
SPRITES = {
    'dk_row16': paint(0, 108, 'row16', DARK),
    'dk_row12': paint(16, 108, 'row12', DARK),
    'dk_row8':  paint(28, 108, 'row8', DARK),
    'dk_lock':  paint(36, 108, 'lock', DARK),
    'wt_row16': paint(42, 108, 'row16', WHITE),
    'wt_row12': paint(58, 108, 'row12', WHITE),
    'wt_row8':  paint(70, 108, 'row8', WHITE),
    'wt_lock':  paint(78, 108, 'lock', WHITE),
}
assert T[127, 127][3] == 0


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


def card(name, sprite, root, flow, normal, tilt=22, scale=1.0, flip=False):
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
    su, sv, sw, sh = SPRITES[sprite]
    w, h = sw / PPU * scale, sh / PPU * scale
    root = np.array(root, float) + n * 0.03
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


def group(name, parent, pivot, specs=()):
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[r4(v) for v in pivot], rotation=[0, 0, 0])
    d['groups'].append(g)
    kids = []
    for s in specs:
        e = card(*s)
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
group('fur_chest_rows', fur_chest, (0, 24.3, -2.15), CHEST_ROWS)
group('fur_chest_edge_R', fur_chest, (2.3, 23, -2.15), side(1, CHEST_EDGE_R))
group('fur_chest_edge_L', fur_chest, (-2.3, 23, -2.15), side(-1, CHEST_EDGE_R))

# ---------------------------------------------------------------- save
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_11_128_tufos.png'
d['name'] = d['name'] + '_tufos'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok', len(d['elements']), 'elements')
