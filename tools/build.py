"""Adds layered 2D fur tufts (head top/back/sides, cheeks, chest) to the CPM bbmodel."""
import json, base64, io, math, random, uuid, copy, sys
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex_src = d['textures'][0]['source'].split(',', 1)[1]
tex = Image.open(io.BytesIO(base64.b64decode(tex_src))).convert('RGBA')
T = tex.load()

# ---------------------------------------------------------------- palette (taken from the skin)
DARK = dict(base=(12, 12, 12), body=(20, 20, 20), edge=(14, 14, 14), mid=(24, 24, 24),
            hi=(26, 26, 26), tip=(30, 30, 30), warm=(18, 18, 18))
WHITE = dict(base=(207, 207, 207), body=(224, 224, 224), edge=(196, 196, 196), mid=(215, 215, 215),
             hi=(240, 240, 240), tip=(247, 247, 247), warm=(207, 207, 207))


def strip(w, h, pal, seed=0, n=None, taper=0.3, lean_amt=1.0, serrate=True):
    """Layered fur card of broad flame-shaped clumps (with side serrations).
    Row 0 = tip side, row h-1 = root."""
    from PIL import ImageDraw
    rnd = random.Random(seed)
    n = n or max(2, round(w / 6))
    clumps = []
    for i in range(n):
        cx = (i + 0.5) * w / n + rnd.uniform(-0.6, 0.6)
        edge = abs((i + 0.5) / n - 0.5) * 2
        ht = h * (1 - taper * edge) * rnd.uniform(0.82, 1.0)
        hw = w / n * rnd.uniform(0.7, 0.85)
        lean = ((cx - w / 2) / w * 3.0 + rnd.uniform(-0.8, 0.8)) * lean_amt
        clumps.append((cx, ht, hw, lean, 1))
    for i in range(n - 1):  # shorter clumps filling the gaps, drawn in front
        cx = (i + 1) * w / n + rnd.uniform(-0.4, 0.4)
        clumps.append((cx, h * rnd.uniform(0.5, 0.65), w / n * 0.55, rnd.uniform(-0.8, 0.8), 0))
    img = [[None] * w for _ in range(h)]
    for cx, ht, hw, lean, big in sorted(clumps, key=lambda c: -c[1]):
        tip = (cx + lean, h - ht)
        L, R = (cx - hw, h + 0.5), (cx + hw, h + 0.5)
        poly = [L, tip, R]
        if serrate and big and ht > 6 and hw >= 3:
            # one serration on each flank, pointing up/outward
            for side, (bx, by) in ((-1, L), (1, R)):
                f = rnd.uniform(0.4, 0.55)
                px, py = bx + (tip[0] - bx) * f, by + (tip[1] - by) * f
                qx, qy = bx + (tip[0] - bx) * (f - 0.28), by + (tip[1] - by) * (f - 0.28)
                sx, sy = px + side * hw * 0.35, py - ht * 0.02
                if side < 0:
                    poly = [L, (qx, qy), (sx, sy), (px, py)] + poly[1:]
                else:
                    poly = poly[:-1] + [(px, py), (sx, sy), (qx, qy), R]
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        mp = m.load()
        for y in range(h):
            for x in range(w):
                if not mp[x, y]:
                    continue
                t = (h - 0.5 - y) / ht                      # 0 root .. 1 tip
                ax = cx + lean * max(0, min(1, t))
                half = max(0.5, hw * (1 - t))
                s = (x + 0.5 - ax) / half
                if t > 0.9:
                    c = pal['tip']
                elif abs(s) < 0.28 and t > 0.3:
                    c = pal['hi']
                elif s < -0.5:
                    c = pal['edge']
                elif s > 0.55:
                    c = pal['mid']
                else:
                    c = pal['body']
                if y == h - 1:
                    c = pal['warm']
                img[y][x] = c
    return img


# Sprite atlas (4 px per model unit), only in texture areas no face references:
#   band 1: y 108..121, x 0..123     band 2: y 16..29, x 0..63
SPRITES = {
    'dk_wide':  (0, 108, 32, 12, strip(32, 12, DARK, 1, serrate=False)),
    'dk_mid':   (32, 108, 24, 12, strip(24, 12, DARK, 2, serrate=False)),
    'dk_small': (56, 108, 16, 12, strip(16, 12, DARK, 3, n=3, serrate=False)),
    'dk_long':  (72, 108, 12, 14, strip(12, 14, DARK, 4, n=2, taper=0.4)),
    'wt_cheek': (84, 108, 12, 14, strip(12, 14, WHITE, 8, n=2, taper=0.4)),
    'wt_bib':   (96, 108, 16, 14, strip(16, 14, WHITE, 9, n=3, taper=0.35)),
    'wt_small': (112, 108, 12, 10, strip(12, 10, WHITE, 7, n=2)),
    'wt_wide':  (0, 16, 28, 12, strip(28, 12, WHITE, 5)),
    'wt_mid':   (28, 16, 20, 12, strip(20, 12, WHITE, 6)),
    'dk_side':  (48, 16, 16, 12, strip(16, 12, DARK, 10, n=3, taper=0.4)),
}

# clear atlas areas then paint
for (x0, y0, x1, y1) in [(0, 108, 124, 122), (0, 16, 64, 30)]:
    for y in range(y0, y1):
        for x in range(x0, x1):
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
    """2D fur card: root at `base`, tips toward `up`, front side facing `facing`. 4 px = 1 unit at scale 1."""
    width, length = SPRITES[sprite][2] / 4 * scale, SPRITES[sprite][3] / 4 * scale
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
json.dump(d, open(OUT, 'w'))
tex.save(OUT.rsplit('.', 1)[0] + '_texture.png')
print('ok', len(d['elements']))
