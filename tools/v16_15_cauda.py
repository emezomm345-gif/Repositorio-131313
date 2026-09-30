"""v16.15: adds a segmented, furry fox tail to the model.

Nothing that already exists is moved or retextured: only new elements/groups are added and only
texture pixels that no face uses (and that are transparent) are painted.

Structure (every bone pivot sits exactly on its joint, so the tail can be animated segment by segment):

body
└─ cauda                     pivot where the tail leaves the body
   ├─ tail_base (+ fur)
   └─ cauda_1
      ├─ tail_1 / tail_1_bevel (+ fur)
      └─ cauda_2
         ├─ tail_2 / tail_2_bevel (+ fur)
         └─ cauda_3
            ├─ tail_3 / tail_3_bevel (+ fur)   black -> white transition
            └─ cauda_ponta
               └─ tail_4, tail_tip (+ fur)       white tip

usage: python3 tools/v16_15_cauda.py <in.bbmodel> <out.bbmodel>
"""
import json, base64, io, math, os, sys, copy, uuid, hashlib
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
T = tex.load()
PPU = 2  # texture pixels per unit, same as the skin

# ---------------------------------------------------------------- free texture space
A = np.array(tex)
OCC = A[:, :, 3] > 0
for e in d['elements']:
    for fc in e['faces'].values():
        if fc.get('texture') is None:
            continue
        x0, y0, x1, y1 = fc['uv']
        OCC[int(min(y0, y1)):int(math.ceil(max(y0, y1))), int(min(x0, x1)):int(math.ceil(max(x0, x1)))] = True
OCC[127, 127] = True  # the shared "blank" pixel


def alloc(w, h):
    for y in range(0, 128 - h + 1):
        for x in range(0, 128 - w + 1):
            if not OCC[y:y + h, x:x + w].any():
                OCC[y:y + h, x:x + w] = True
                return x, y
    raise RuntimeError('texture full (%dx%d)' % (w, h))


_cache = {}     # md5 -> (u, v)
_sprites = []   # (u, v, np.array pixels) for sub-rectangle reuse


def put(pixels):
    """pixels: list of rows of RGBA tuples. Identical sprites share the same texture spot, and a
    sprite equal to the top-left corner of a bigger one just points into it."""
    arr = np.array(pixels, dtype=np.uint8)
    h, w = arr.shape[:2]
    key = hashlib.md5(arr.tobytes() + bytes([w, h])).hexdigest()
    if key in _cache:
        return _cache[key] + (w, h)
    for u, v, big in _sprites:
        if big.shape[0] >= h and big.shape[1] >= w and np.array_equal(big[:h, :w], arr):
            _cache[key] = (u, v)
            return (u, v, w, h)
    u, v = alloc(w, h)
    for j in range(h):
        for i in range(w):
            T[u + i, v + j] = tuple(int(c) for c in arr[j, i])
    _cache[key] = (u, v)
    _sprites.append((u, v, arr))
    return (u, v, w, h)


# ---------------------------------------------------------------- colours (all taken from the skin)
DARK = [(19, 19, 19), (24, 23, 23), (27, 25, 24), (31, 30, 28)]   # shade .. light
MID1 = (109, 104, 100)       # warm grey (sleeve stripe)
MID2 = (188, 179, 172)       # warm light grey (chest patch)
WHITE = [(215, 215, 215), (224, 224, 224), (232, 232, 232), (244, 244, 244)]

# ---------------------------------------------------------------- tail layout (straight, along +Z)
# Bones get their rotation afterwards, so all coordinates are written as if the tail were straight.
Y0, Z0 = 13.2, 1.6            # where the tail leaves the lower back (body back = z 2)
SEGS = [  # name, half width, length, bone rotation X (first = droop, then curl up)
    ('base', 1.4, 2.5, 42),
    ('1',    2.2, 3.5, -9),
    ('2',    2.9, 4.0, -9),
    ('3',    2.6, 3.5, -8),
    ('4',    1.9, 2.5, -7),
]
Z_WHITE = Z0 + 2.5 + 3.5 + 4.0 + 2.0   # where the white tip starts (inside segment 3)


def tri(x):
    return abs((x % 1.0) * 2 - 1)


def field(p, detail=None):
    """Colour of the tail surface at p (straight frame): black fur, jagged stepped band, white tip.
    detail = (i, j) texel of the face -> small ordered variation (same pattern on same-size faces,
    so they can share texture space)."""
    x, y, z = p
    ang = math.atan2(y - Y0, x) / (2 * math.pi)
    zb = Z_WHITE + 0.55 * tri(ang * 6)                 # zig-zag border, 6 teeth around the tail
    if z < zb - 0.9:
        k = 1
        if detail:  # a little ordered variation so the fur is not flat
            i, j = detail
            k = (1, 1, 2, 0, 1)[(i * 3 + j * 2 + (j // 2)) % 5]
        return DARK[k]
    if z < zb - 0.45:
        return MID1
    if z < zb:
        return MID2
    k = 2
    if detail:
        i, j = detail
        k = (2, 2, 1, 3, 2)[(i * 2 + j * 3 + (i // 2)) % 5]
    return WHITE[k]


def lighten(c, step):
    """Move a colour one step lighter/darker inside its own ramp (keeps the skin palette)."""
    for ramp in (DARK, WHITE):
        if c in ramp:
            return ramp[max(0, min(len(ramp) - 1, ramp.index(c) + step))]
    return c


# ---------------------------------------------------------------- geometry helpers
def rotmat(r):
    rx, ry, rz = [math.radians(a) for a in r]
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def euler_zyx(R):
    b = math.asin(max(-1, min(1, -R[2, 0])))
    a = math.atan2(R[2, 1], R[2, 2])
    c = math.atan2(R[1, 0], R[0, 0])
    return [round(math.degrees(a), 3), round(math.degrees(b), 3), round(math.degrees(c), 3)]


def norm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


r4 = lambda v: round(float(v), 4)
BLANK = {'uv': [127, 127, 128, 128], 'texture': 0}


def face_corners(f, t, face):
    (x0, y0, z0), (x1, y1, z1) = f, t
    return {
        'north': ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
        'south': ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
        'east':  ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        'west':  ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
        'up':    ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
        'down':  ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0)),
    }[face]


def cube(name, f, t, faces, rotation=(0, 0, 0), origin=None):
    """Tail cuboid; every listed face is painted from the colour field (unlisted faces are hidden)."""
    origin = origin or [(f[i] + t[i]) / 2 for i in range(3)]
    R = rotmat(rotation)
    o = np.array(origin, float)
    out = {}
    for face in ('north', 'south', 'east', 'west', 'up', 'down'):
        if face not in faces:
            out[face] = copy.deepcopy(BLANK)
            continue
        tl, tr, bl = (np.array(c, float) for c in face_corners(f, t, face))
        W = max(1, round(np.linalg.norm(tr - tl) * PPU))
        H = max(1, round(np.linalg.norm(bl - tl) * PPU))
        rows = []
        for j in range(H):
            row = []
            for i in range(W):
                p = tl + (i + 0.5) / W * (tr - tl) + (j + 0.5) / H * (bl - tl)
                wp = R @ (p - o) + o
                c = field(wp, (i, j))
                row.append(c + (255,))
            rows.append(row)
        u, v, w, h = put(rows)
        out[face] = {'uv': [u, v, u + w, v + h], 'texture': 0}
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [r4(v) for v in f], 'to': [r4(v) for v in t], 'autouv': 0, 'color': 3,
        'rotation': [r4(v) for v in rotation], 'origin': [r4(v) for v in origin],
        'faces': out, 'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


# fur cards: same pixel-art locks as the head/chest, coloured from the tail colour field
ART = {
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


def card(name, art, root, flow, normal, tilt=25, scale=1.0, flip=False):
    fl, n = norm(flow), norm(normal)
    fl = norm(fl - (fl @ n) * n)
    tt = math.radians(tilt)
    up = norm(math.cos(tt) * fl + math.sin(tt) * n)
    face = norm(n - (n @ up) * up)
    k = -face
    r = np.cross(up, k)
    R = np.column_stack([r, up, k])
    rows = ART[art]
    sw, sh = len(rows[0]), len(rows)
    w, h = sw / PPU * scale, sh / PPU * scale
    surf = np.array(root, float)
    rt = surf + n * 0.03
    px = []
    for j, row in enumerate(rows):
        line = []
        for i, ch in enumerate(row):
            if ch == '.':
                line.append((0, 0, 0, 0))
                continue
            lx = (-w / 2 + (i + 0.5) * w / sw) if flip else (w / 2 - (i + 0.5) * w / sw)
            ly = h - (j + 0.5) * h / sh
            p = rt + R @ np.array([lx, ly, 0.0])
            p = p - ((p - surf) @ n) * n
            c = field(p)
            ramp_k = sh - 1 - j                                 # rows from the root
            if ramp_k >= 1:
                c = lighten(c, {'M': 0, 'S': -1, 'L': 1}[ch])
            line.append(c + (255,))
        px.append(line)
    u, v, sw_, sh_ = put(px)
    front = [u, v, u + sw, v + sh]
    back = [u + sw, v, u, v + sh]
    faces = {f: copy.deepcopy(BLANK) for f in ('east', 'west', 'up', 'down')}
    faces['north'] = {'uv': front, 'texture': 0}
    faces['south'] = {'uv': back, 'texture': 0}
    bx, by, bz = rt
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [r4(bx - w / 2), r4(by), r4(bz - 0.02)], 'to': [r4(bx + w / 2), r4(by + h), r4(bz + 0.02)],
        'autouv': 0, 'color': 2, 'rotation': euler_zyx(R), 'origin': [r4(bx), r4(by), r4(bz)],
        'faces': faces, 'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


# ---------------------------------------------------------------- outliner helpers
TEMPLATE = next(g for g in d['groups'] if g['name'] == 'bochechas')


def find_node(nodes, gid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == gid:
                return n
            f = find_node(n['children'], gid)
            if f:
                return f


def bone(name, parent, pivot, rotation=(0, 0, 0)):
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[r4(v) for v in pivot], rotation=[r4(v) for v in rotation])
    d['groups'].append(g)
    find_node(d['outliner'], parent)['children'].append({'uuid': g['uuid'], 'isOpen': False, 'children': []})
    return g['uuid']


def add(parent, elements):
    node = find_node(d['outliner'], parent)
    for e in elements:
        d['elements'].append(e)
        node['children'].append(e['uuid'])


def ring_fur(tag, z_root, half, length_scale, art, tilt=24, sides=('up', 'down', 'east', 'west'), diag=True):
    """Layered locks around the tail at z_root, flowing toward the tip."""
    out = []
    N = {'up': (0, 1, 0), 'down': (0, -1, 0), 'east': (1, 0, 0), 'west': (-1, 0, 0)}
    for s in sides:
        n = np.array(N[s], float)
        root = np.array([0, Y0, z_root]) + n * half
        out.append(card('fur_tail_%s_%s' % (tag, s), art, root, (0, 0, 1), n, tilt, length_scale,
                        flip=(s == 'west')))
    if diag:
        for sx, sy, nm in ((1, 1, 'up_R'), (-1, 1, 'up_L'), (1, -1, 'down_R'), (-1, -1, 'down_L')):
            n = norm((sx, sy, 0))
            root = np.array([0, Y0, z_root + 0.5]) + n * half * 1.05
            out.append(card('fur_tail_%s_%s' % (tag, nm), 'lock', root, (0, 0, 1), n, tilt + 4,
                            length_scale * 0.9, flip=(sx < 0)))
    return out


# ---------------------------------------------------------------- build
body = next(g for g in d['groups'] if g['name'] == 'body')['uuid']
ALL = ('north', 'south', 'east', 'west', 'up', 'down')
SIDE = ('east', 'west', 'up', 'down')

# master fur patches: the plain black / white faces of every segment are cut from these
# (the ordered pattern starts at the top-left texel, so a smaller face = a corner of the master)
def face_px(v):
    return int(round(v * PPU))


DARK_MAX = max(max(face_px(2 * hw), face_px(ln)) for _, hw, ln, _ in SEGS)
WHITE_MAX = max(face_px(2 * SEGS[-2][1]), face_px(2 * SEGS[-1][1]), face_px(SEGS[-1][2]))
put([[DARK[(1, 1, 2, 0, 1)[(i * 3 + j * 2 + (j // 2)) % 5]] + (255,) for i in range(DARK_MAX)]
     for j in range(DARK_MAX)])
put([[WHITE[(2, 2, 1, 3, 2)[(i * 2 + j * 3 + (i // 2)) % 5]] + (255,) for i in range(WHITE_MAX)]
     for j in range(WHITE_MAX)])

z = Z0
parent = body
names = {'base': 'cauda', '1': 'cauda_1', '2': 'cauda_2', '3': 'cauda_3', '4': 'cauda_ponta'}
for idx, (tag, hw, ln, rx) in enumerate(SEGS):
    b = bone(names[tag], parent, (0, Y0, z), (rx, 0, 0))
    z0, z1 = z, z + ln
    nxt = SEGS[idx + 1][1] if idx + 1 < len(SEGS) else 0
    faces = list(SIDE)
    if idx > 0 and hw > SEGS[idx - 1][1]:
        faces.append('north')          # front ring visible around the thinner previous segment
    if hw > nxt:
        faces.append('south')          # back ring visible around the thinner next segment / tip
    els = [cube('tail_%s' % tag, (-hw, Y0 - hw, z0), (hw, Y0 + hw, z1), faces)]
    if tag in ('1', '2', '3'):         # 45° bevel cuboid -> octagonal cross-section
        bh = hw * 0.88
        els.append(cube('tail_%s_bevel' % tag, (-bh, Y0 - bh, z0 + 0.15), (bh, Y0 + bh, z1 - 0.1),
                        SIDE, rotation=(0, 0, 45), origin=(0, Y0, (z0 + z1) / 2)))
    # fur: one layer at the joint, one halfway, flowing toward the tip
    if tag == 'base':
        els += ring_fur('base', z0 + 0.9, hw, 0.55, 'row8', tilt=20, diag=False)
    elif tag == '4':
        els += ring_fur('4a', z0 + 0.2, hw, 0.75, 'row8', tilt=26)
        tip = cube('tail_tip', (-1.0, Y0 - 1.0, z1), (1.0, Y0 + 1.0, z1 + 1.5), ('east', 'west', 'up', 'down', 'south'))
        els.append(tip)
        for sx, sy, nm in ((0, 1, 'up'), (0, -1, 'down'), (1, 0, 'R'), (-1, 0, 'L')):
            n = np.array((sx, sy, 0), float)
            els.append(card('fur_tail_tip_%s' % nm, 'lock', np.array([0, Y0, z1 + 0.2]) + n * 1.0,
                            (0, 0, 1), n, 18, 0.85, flip=(sx < 0)))
    else:
        s = hw / 2.0
        els += ring_fur(tag + 'a', z0 + 0.25, hw, 0.62 * s + 0.1, 'row12' if hw >= 2 else 'row8')
        els += ring_fur(tag + 'b', z0 + ln * 0.55, hw, 0.55 * s + 0.1, 'row8', tilt=22, diag=False)
    add(b, els)
    parent = b
    z = z1

# ---------------------------------------------------------------- save
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_15_128_cauda.png'
d['name'] = 'skin_v16.15_cauda'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok: %d elements, %d unique sprites, free px left %d' % (len(d['elements']), len(_cache), (~OCC).sum()))
