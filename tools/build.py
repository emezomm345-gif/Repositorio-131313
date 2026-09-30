"""Adds layered 2D fur tufts (head top/back/sides, cheeks, chest) to the CPM bbmodel."""
import json, base64, io, math, os, random, uuid, copy, sys
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex_src = d['textures'][0]['source'].split(',', 1)[1]
tex = Image.open(io.BytesIO(base64.b64decode(tex_src))).convert('RGBA')
T = tex.load()

# ---------------------------------------------------------------- palette (taken from the skin)
DARK = dict(main=(24, 24, 24), shade=(16, 16, 16), light=(36, 36, 36))
WHITE = dict(main=(224, 224, 224), shade=(196, 196, 196), light=(240, 240, 240))


PPU = 2  # texture pixels per model unit (same density as the skin)


# Hand-drawn pixel-art tufts. M = main, S = shade, L = light tip, . = gap/transparent.
ART = {
    'wide': ["..L......L....L.",
             ".LM.....MM...LM.",
             ".MMS..L.MMS..MMS",
             "MMMS.MM.MMSM.MMS",
             "MM.SMMMSM.SMMMSM",
             "MMMMMMMMMMMMMMMM"],
    'mid':  ["...L......L.",
             "..LM.....MM.",
             "..MMS.L..MMS",
             ".MMMSMM.MM.S",
             "MM.SMMMSMMSM",
             "MMMMMMMMMMMM"],
    'small': ["..L.....",
              ".LM...L.",
              ".MMS.MM.",
              "MMMSMMMS",
              "M.MSMM.S",
              "MMMMMMMM"],
    'long': ["..L...",
             "..M...",
             ".MMS..",
             ".MMS.L",
             "MM.SMM",
             "MMMSMS",
             "MMMMMM"],
    'side': ["...L....",
             "..MM..L.",
             ".MMMS.MS",
             ".M.MSMMS",
             "MMMMSM.S",
             "MMMMMMMM"],
    'cheek': ["...L..",
              "..LM..",
              "..MMS.",
              ".MM.S.",
              "LMMMSS",
              "MMMMMS",
              "MMMMMM"],
    'bib':  [".L....L.",
             ".M...LM.",
             "MMS..MMS",
             "MMS.MMMS",
             "M.SMM.MS",
             "MMSMMMMS",
             "MMMMMMMM"],
    'tiny': [".L..L.",
             ".MS.MS",
             "MMSMMS",
             "M.MM.S",
             "MMMMMM"],
    'wwide': ["..L.....L...L.",
              ".LM....MM..LM.",
              ".MMS.L.MMS.MMS",
              "MMMSMM.M.SMMMS",
              "M.MSMMSMMSM.MS",
              "MMMMMMMMMMMMMM"],
    'wmid': ["..L....L..",
             ".LM...MM..",
             ".MMS.LMMS.",
             "MMMSMM.MSM",
             "M.MSMMSM.S",
             "MMMMMMMMMM"],
}


def art(key, pal):
    m = {'M': pal['main'], 'S': pal['shade'], 'L': pal['light'], '.': None}
    return [[m[ch] for ch in row] for row in ART[key]]


def sprite(u, v, key, pal):
    rows = ART[key]
    return (u, v, len(rows[0]), len(rows), art(key, pal))


# Sprite atlas (2 px per model unit), in texture rows no face references (y 108..121)
SPRITES = {
    'dk_wide':  sprite(0, 108, 'wide', DARK),
    'dk_mid':   sprite(16, 108, 'mid', DARK),
    'dk_small': sprite(28, 108, 'small', DARK),
    'dk_long':  sprite(36, 108, 'long', DARK),
    'dk_side':  sprite(42, 108, 'side', DARK),
    'wt_cheek': sprite(50, 108, 'cheek', WHITE),
    'wt_bib':   sprite(56, 108, 'bib', WHITE),
    'wt_small': sprite(64, 108, 'tiny', WHITE),
    'wt_wide':  sprite(70, 108, 'wwide', WHITE),
    'wt_mid':   sprite(84, 108, 'wmid', WHITE),
}

for y in range(108, 122):
    for x in range(0, 124):
        T[x, y] = (0, 0, 0, 0)
for name, (u, v, w, h, px) in SPRITES.items():
    for y in range(h):
        for x in range(w):
            c = px[y][x]
            T[u + x, v + y] = (0, 0, 0, 0) if c is None else c + (255,)
assert T[127, 127][3] == 0


# ---------------------------------------------------------------- geometry helpers
def euler_zyx(R):
    b = math.asin(max(-1, min(1, -R[2, 0])))
    a = math.atan2(R[2, 1], R[2, 2])
    c = math.atan2(R[1, 0], R[0, 0])
    return [round(math.degrees(a), 4), round(math.degrees(b), 4), round(math.degrees(c), 4)]


def norm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


BLANK = [127, 127, 128, 128]


def tuft(name, sprite, base, up, facing, scale=1.0, flip=False):
    """2D fur card: root at `base`, tips toward `up`, front side facing `facing`. PPU px = 1 unit at scale 1."""
    width, length = SPRITES[sprite][2] / PPU * scale, SPRITES[sprite][3] / PPU * scale
    u = norm(up)
    n = np.array(facing, float)
    n = norm(n - (n @ u) * u)
    k = -n
    r = np.cross(u, k)
    R = np.column_stack([r, u, k])
    bx, by, bz = base
    su, sv, sw, sh, _ = SPRITES[sprite]
    front = [su + sw, sv, su, sv + sh] if flip else [su, sv, su + sw, sv + sh]
    back = [front[2], front[1], front[0], front[3]]  # mirrored so both sides line up
    faces = {f: {'uv': BLANK, 'texture': 0} for f in ('east', 'west', 'up', 'down')}
    faces['north'] = {'uv': front, 'texture': 0}
    faces['south'] = {'uv': back, 'texture': 0}
    r4 = lambda v: round(float(v), 4)
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [r4(bx - width / 2), r4(by), r4(bz - 0.02)],
        'to': [r4(bx + width / 2), r4(by + length), r4(bz + 0.02)],
        'autouv': 0, 'color': 2, 'rotation': euler_zyx(R), 'origin': [r4(bx), r4(by), r4(bz)],
        'faces': faces, 'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


def mirror(spec):
    name, sprite, base, up, facing = spec[:5]
    scale = spec[5] if len(spec) > 5 else 1.0
    m = lambda v: [-v[0], v[1], v[2]]
    return (name.replace('_R_', '_L_'), sprite, m(base), m(up), m(facing), scale, True)


def sym(specs):
    return specs + [mirror(s) for s in specs]


# ---------------------------------------------------------------- tuft layout
# Head cube spans x -4..4, y 24..32, z -4..4 (front = -Z). Body/jacket front at z = -2.15.
# (name, sprite, root point, tip direction, facing direction, scale)
HEAD_TOP = [
    ('fur_top_back',   'dk_wide',  (0, 31.0, 2.4),   (0, 1, 0.75),     (0, 0.3, -1), 0.95),
    ('fur_top_mid',    'dk_mid',   (0.4, 31.2, 0.4), (0, 1, 0.4),      (0, 0, -1)),
    ('fur_top_front',  'dk_small', (-0.6, 31.4, -1.8), (0.15, 1, -0.05), (0, 0, -1), 0.9),
    ('fur_top_fringe', 'dk_small', (1.3, 31.4, -3.4), (0.35, 1, -0.45), (0, 0, -1), 0.7),
]
HEAD_BACK = [
    ('fur_back_fill',  'dk_wide',  (0, 25.2, 4.06),  (0, 1, 0.08),     (0, 0, 1), 1.05),
    ('fur_back_top',   'dk_wide',  (0, 29.6, 4.2),   (0, 1, 0.6),      (0, 0, 1), 1.0),
    ('fur_back_nape',  'dk_wide',  (0, 25.6, 4.12),  (0, -1, 0.5),     (0, 0, 1), 0.9),
] + sym([
    ('fur_back_R_side', 'dk_side', (3.2, 28.6, 4.14), (1, 0.25, 0.35),  (0, 0, 1)),
    ('fur_back_R_low',  'dk_small', (3.0, 26.2, 4.16), (1, -0.45, 0.35), (0, 0, 1), 0.9),
])
HEAD_SIDE = sym([
    # dark fluff sweeping back/out from the upper sides of the head
    ('fur_side_R_up',    'dk_side',  (4.04, 29.8, 1.2),  (0.3, 0.6, 1),   (1, 0, 0)),
    ('fur_side_R_back',  'dk_long',  (4.04, 27.6, 2.2),  (0.25, -0.1, 1), (1, 0, 0)),
    ('fur_side_R_out',   'dk_small', (3.9, 29.4, 1.6),   (1, 0.45, 0.25), (0.25, 0, -1), 0.85),
    ('fur_side_R_out2',  'dk_small', (3.9, 27.4, 2.6),   (1, -0.1, 0.3),  (0.3, 0, -1), 0.8),
    # white cheek fluff, layered, pointing out and a little down / back
    ('fur_cheek_R_back', 'wt_cheek', (3.7, 26.0, -0.8),  (1, -0.05, 0.4), (0.35, 0, -1), 0.95),
    ('fur_cheek_R_mid',  'wt_cheek', (3.6, 25.3, -2.0),  (1, -0.35, 0.15), (0.45, 0, -1), 0.9),
    ('fur_cheek_R_low',  'wt_small', (3.3, 24.4, -2.8),  (1, -0.85, 0),   (0.4, 0, -1), 0.9),
    ('fur_cheek_R_side', 'wt_cheek', (4.04, 25.4, -2.9), (0.15, -0.2, 1), (1, 0, 0), 1.2),
    ('fur_cheek_R_side2', 'wt_small', (4.06, 24.4, -2.2), (0.2, -0.6, 1), (1, 0, 0), 1.0),
])
CHEST = [
    ('fur_chest_ruff', 'wt_wide',  (0, 24.1, -2.3),    (0, -1, -0.9),  (0, 0.6, -1), 1.0),
    ('fur_chest_2',    'wt_mid',   (0.2, 22.6, -2.25), (0, -1, -0.55), (0, 0.3, -1), 1.1),
    ('fur_chest_3',    'wt_bib',   (-0.2, 20.6, -2.22), (0, -1, -0.45), (0, 0.2, -1), 1.15),
    ('fur_chest_4',    'wt_bib',   (0.15, 18.3, -2.2), (0, -1, -0.35), (0, 0.1, -1), 0.95),
    ('fur_chest_5',    'wt_small', (-0.1, 16.1, -2.2), (0, -1, -0.3), (0, 0, -1), 0.9),
    # profile cards (x = 0 plane) so the chest fluff sticks out when seen from the side
    ('fur_chest_profile_1', 'wt_cheek', (0, 23.9, -2.2), (0, -0.55, -1), (1, 0, 0), 1.0),
    ('fur_chest_profile_2', 'wt_small', (0, 21.4, -2.18), (0, -0.9, -0.8), (1, 0, 0), 1.0),
] + sym([
    ('fur_chest_R_neck', 'wt_small', (2.2, 23.7, -2.3),  (1, -0.45, -0.35), (0, 0.2, -1), 0.9),
    ('fur_chest_R_edge', 'wt_small', (1.7, 21.6, -2.25), (1, -0.8, -0.3),  (0, 0.1, -1), 0.8),
    ('fur_chest_R_edge2', 'wt_small', (1.4, 19.2, -2.22), (1, -1.1, -0.25), (0, 0, -1), 0.7),
])


def add_group(name, parent_uuid, origin, specs):
    g = copy.deepcopy(next(x for x in d['groups'] if x['name'] == 'bone2'))
    g.update(name=name, uuid=str(uuid.uuid4()), origin=list(origin), rotation=[0, 0, 0])
    d['groups'].append(g)
    kids = []
    for s in specs:
        e = tuft(*s)
        d['elements'].append(e)
        kids.append(e['uuid'])
    node = {'uuid': g['uuid'], 'isOpen': False, 'children': kids}

    def find(nodes):
        for n in nodes:
            if isinstance(n, dict):
                if n['uuid'] == parent_uuid:
                    n['children'].append(node)
                    return True
                if find(n['children']):
                    return True
        return False
    assert find(d['outliner'])


head = next(g for g in d['groups'] if g['name'] == 'head')['uuid']
body = next(g for g in d['groups'] if g['name'] == 'body')['uuid']
add_group('fur_head_top', head, (0, 31, 0), HEAD_TOP)
add_group('fur_head_back', head, (0, 28, 4), HEAD_BACK)
add_group('fur_head_sides', head, (0, 26, 0), HEAD_SIDE)
add_group('fur_chest', body, (0, 20, -2.2), CHEST)

buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
d['name'] = d['name'] + '_tufos'
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_11_128_tufos.png'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT), d['textures'][0]['name']))
print('ok', len(d['elements']))
