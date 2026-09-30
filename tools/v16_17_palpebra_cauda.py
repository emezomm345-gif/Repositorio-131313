"""v16.17 (from the user's v16.16):
  1. eyebrows retextured like the reference (grey, arched)       - geometry untouched
  2. new eyelids (palpebra_R / palpebra_L) over the top of each eye, own group with the pivot on the lid line
  3. tail -> body colour transition: tail_base repainted from the body's back colours into the tail fur,
     plus a ring of locks (fur_cauda_raiz) growing from the body over the tail root
Everything else is kept exactly as it is.

usage: python3 tools/v16_17_palpebra_cauda.py <in.bbmodel> <out.bbmodel>
"""
import json, base64, io, math, os, sys, copy, uuid, hashlib
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
T = tex.load()
ORIG = tex.copy().load()
ELS = {e['name']: e for e in d['elements']}
GRP = {g['name']: g for g in d['groups']}

# ---------------------------------------------------------------- texture space
OCC = np.array(tex)[:, :, 3] > 0
for e in d['elements']:
    for fc in e['faces'].values():
        if fc.get('texture') is None:
            continue
        x0, y0, x1, y1 = fc['uv']
        OCC[int(min(y0, y1)):int(math.ceil(max(y0, y1))), int(min(x0, x1)):int(math.ceil(max(x0, x1)))] = True
OCC[127, 127] = True
_cache = {}


def put(rows):
    """rows of RGBA tuples -> (u, v, w, h) in free texture space (identical sprites are shared)."""
    arr = np.array(rows, dtype=np.uint8)
    h, w = arr.shape[:2]
    key = hashlib.md5(arr.tobytes() + bytes([w, h])).hexdigest()
    if key not in _cache:
        for y in range(128 - h + 1):
            for x in range(128 - w + 1):
                if not OCC[y:y + h, x:x + w].any():
                    OCC[y:y + h, x:x + w] = True
                    for j in range(h):
                        for i in range(w):
                            T[x + i, y + j] = tuple(int(c) for c in arr[j, i])
                    _cache[key] = (x, y)
                    break
            if key in _cache:
                break
        else:
            raise RuntimeError('texture full')
    return _cache[key] + (w, h)


def uv(rect, rot180=False):
    u, v, w, h = rect
    return [u + w, v + h, u, v] if rot180 else [u, v, u + w, v + h]


# palette (all from the skin)
_px = np.array(tex).reshape(-1, 4)
_cols, _cnt = np.unique(_px[_px[:, 3] == 255][:, :3], axis=0, return_counts=True)
PALETTE = _cols[_cnt >= 3].astype(float)


def snap(c):
    return tuple(int(v) for v in PALETTE[np.argmin(((PALETTE - np.array(c, float)) ** 2).sum(1))])


# ---------------------------------------------------------------- 1. eyebrows (texture only)
G1, G2, G3 = (108, 108, 108), (94, 94, 94), (71, 71, 71)   # light / mid / dark grey from the skin
X = (0, 0, 0, 0)
A = lambda c: c + (255,)
# front 6x3 as seen upright: arched (ends one pixel lower than the middle)
BROW_FRONT = [[X, A(G1), A(G1), A(G1), A(G1), X],
              [A(G1), A(G2), A(G2), A(G2), A(G2), A(G1)],
              [A(G2), X, X, X, X, A(G2)]]
brow_front = put(BROW_FRONT)
brow_side = put([[A(G1)], [A(G2)], [A(G2)]])
brow_top = put([[A(G1)] * 6])
brow_bottom = put([[A(G3)] * 6])
for name in ('sobrancelha_R', 'sobrancelha_L'):
    e = ELS[name]
    # the brows are rotated 180° on Z: every UV is given rotated 180°, the local "down" face is on top
    e['faces'] = {
        'north': {'uv': uv(brow_front, True), 'texture': 0},
        'east': {'uv': uv(brow_side, True), 'texture': 0},
        'west': {'uv': uv(brow_side, True), 'texture': 0},
        'down': {'uv': uv(brow_top, True), 'texture': 0},
        'up': {'uv': uv(brow_bottom, True), 'texture': 0},
        'south': {'uv': [127, 127, 128, 128], 'texture': 0},
    }

# ---------------------------------------------------------------- helpers for new elements
r4 = lambda v: round(float(v), 4)
BLANK = {'uv': [127, 127, 128, 128], 'texture': 0}


def element(name, f, t, faces, rotation=(0, 0, 0), origin=None, color=2):
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [r4(v) for v in f], 'to': [r4(v) for v in t], 'autouv': 0, 'color': color,
        'rotation': [r4(v) for v in rotation],
        'origin': [r4(v) for v in (origin or [(f[i] + t[i]) / 2 for i in range(3)])],
        'faces': {k: faces.get(k, copy.deepcopy(BLANK)) for k in ('north', 'south', 'east', 'west', 'up', 'down')},
        'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


def find_node(nodes, gid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == gid:
                return n
            f = find_node(n['children'], gid)
            if f:
                return f


def new_group(name, parent_name, pivot, after=None):
    g = copy.deepcopy(GRP['bochechas'])
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[r4(v) for v in pivot], rotation=[0, 0, 0])
    d['groups'].append(g)
    GRP[name] = g
    parent = find_node(d['outliner'], GRP[parent_name]['uuid'])
    node = {'uuid': g['uuid'], 'isOpen': False, 'children': []}
    idx = len(parent['children'])
    if after:
        for i, c in enumerate(parent['children']):
            if isinstance(c, dict) and c['uuid'] == GRP[after]['uuid']:
                idx = i + 1
    parent['children'].insert(idx, node)
    return node


# ---------------------------------------------------------------- 2. eyelids
LID_TOP, LID_BOT = (97, 97, 97), (60, 60, 60)
lid_front = put([[A(LID_TOP)] * 6, [A(LID_BOT)] * 6])
lid_side = put([[A(LID_TOP)], [A(LID_BOT)]])
lid_top = put([[A(LID_TOP)] * 6])
lid_under = put([[A((40, 40, 40))] * 6])
node = new_group('palpebras', 'head', (0.025, 28.52, -4.1), after='sobrancelhas')
for side in ('R', 'L'):
    eye = ELS['eye_' + side]
    x0, x1 = eye['from'][0] - 0.03, eye['to'][0] + 0.03
    top = eye['to'][1]                               # 28.5194
    lid = element('palpebra_' + side, (x0, top - 0.5, -4.14), (x1, top - 0.18, -3.97),
                  {'north': {'uv': uv(lid_front), 'texture': 0},
                   'east': {'uv': uv(lid_side), 'texture': 0},
                   'west': {'uv': uv(lid_side), 'texture': 0},
                   'up': {'uv': uv(lid_top), 'texture': 0},
                   'down': {'uv': uv(lid_under), 'texture': 0}},
                  origin=((x0 + x1) / 2, top - 0.18, -4.05))  # pivot on the lid line (for blinking)
    d['elements'].append(lid)
    node['children'].append(lid['uuid'])


# ---------------------------------------------------------------- 3. tail <-> body transition
def rotmat(r):
    rx, ry, rz = [math.radians(a) for a in r]
    Xm = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ym = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Zm = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Zm @ Ym @ Xm


def euler_zyx(R):
    b = math.asin(max(-1, min(1, -R[2, 0])))
    a = math.atan2(R[2, 1], R[2, 2])
    c = math.atan2(R[1, 0], R[0, 0])
    return [round(math.degrees(a), 3), round(math.degrees(b), 3), round(math.degrees(c), 3)]


def norm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


BODY = ELS['body']
BU0, BV0, BU1, BV1 = BODY['faces']['south']['uv']
BACK_Z = BODY['to'][2]                                   # 2


def body_back(x, y):
    """Colour of the body's back (south face) at x, y."""
    s = min(max((x - BODY['from'][0]) / (BODY['to'][0] - BODY['from'][0]), 0), 0.999)
    t = min(max((BODY['to'][1] - y) / (BODY['to'][1] - BODY['from'][1]), 0), 0.999)
    return ORIG[int(BU0 + s * (BU1 - BU0)), int(BV0 + t * (BV1 - BV0))][:3]


DARK = [(19, 19, 19), (24, 23, 23), (27, 25, 24), (31, 30, 28)]


def tail_fur(i, j):                                      # same ordered pattern the tail already uses
    return DARK[(1, 1, 2, 0, 1)[(i * 3 + j * 2 + (j // 2)) % 5]]


TAIL = GRP['cauda']
TR = rotmat(TAIL['rotation'])
TO = np.array(TAIL['origin'], float)
to_world = lambda p: TR @ (np.array(p, float) - TO) + TO


def face_corners(f, t, face):
    (x0, y0, z0), (x1, y1, z1) = f, t
    return {'east': ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
            'west': ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
            'up': ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
            'down': ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0))}[face]


# 3a. repaint tail_base: body colour where it leaves the back -> stepped, dithered -> tail fur
base = ELS['tail_base']
f, t = base['from'], base['to']
PPU = 2
for face in ('east', 'west', 'up', 'down'):
    tl, tr, bl = (np.array(c, float) for c in face_corners(f, t, face))
    W, H = max(1, round(np.linalg.norm(tr - tl) * PPU)), max(1, round(np.linalg.norm(bl - tl) * PPU))
    rows = []
    for j in range(H):
        row = []
        for i in range(W):
            p = tl + (i + 0.5) / W * (tr - tl) + (j + 0.5) / H * (bl - tl)
            wp = to_world(p)
            depth = wp[2] - BACK_Z                        # how far out of the back this texel is
            skin, fur = body_back(wp[0], wp[1]), tail_fur(i, j)
            if depth < 0.45:
                c = skin
            elif depth < 0.95:                             # dithered step between the two
                c = skin if (i + j) % 2 else snap((np.array(skin) + np.array(fur)) / 2)
            elif depth < 1.4:
                c = snap((np.array(skin) + 2 * np.array(fur)) / 3) if (i + j) % 2 else fur
            else:
                c = fur
            row.append(A(c))
        rows.append(row)
    base['faces'][face] = {'uv': uv(put(rows)), 'texture': 0}

# 3b. ring of short locks growing out of the back and lying over the tail root
LOCK = ["..L...",
        ".LMS..",
        ".MMS.L",
        "LMMSLM",
        "MMMMMS",
        "MMMMMM"]
tail_dir = norm(TR @ np.array([0, 0, 1.0]))
hw = (t[0] - f[0]) / 2
axis_y = (f[1] + t[1]) / 2
ring = new_group('fur_cauda_raiz', 'body', (0, axis_y, BACK_Z))
for k, ang in enumerate(range(0, 360, 45)):
    a = math.radians(ang)
    radial = np.array([math.cos(a), math.sin(a), 0.0])
    n = norm(radial - (radial @ tail_dir) * tail_dir)   # outward from the tail surface
    root = np.array([0, axis_y, BACK_Z + 0.05]) + radial * (hw + 0.1)
    up = norm(math.cos(math.radians(22)) * tail_dir + math.sin(math.radians(22)) * n)
    face_dir = norm(n - (n @ up) * up)
    R = np.column_stack([np.cross(up, -face_dir), up, -face_dir])
    sw, sh, scale = 6, 6, 0.75
    w, h = sw / PPU * scale, sh / PPU * scale
    rows = []
    for j, line in enumerate(LOCK):
        row = []
        for i, ch in enumerate(line):
            if ch == '.':
                row.append(X)
                continue
            from_root = sh - 1 - j
            lx, ly = w / 2 - (i + 0.5) * w / sw, h - (j + 0.5) * h / sh
            p = root + R @ np.array([lx, ly, 0.0])
            skin, fur = body_back(p[0], p[1]), tail_fur(i, j)
            if from_root <= 1:
                c = skin                                  # root = body colour
            elif from_root == 2:
                c = snap((np.array(skin) + np.array(fur)) / 2)
            else:
                c = fur                                   # tips = tail fur
            if from_root >= 2 and ch in 'SL':
                c = DARK[max(0, min(3, DARK.index(c) + (1 if ch == 'L' else -1)))] if c in DARK else c
            row.append(A(c))
        rows.append(row)
    rect = put(rows)
    lock = element('fur_cauda_raiz_%d' % (k + 1), (root[0] - w / 2, root[1], root[2] - 0.02),
                   (root[0] + w / 2, root[1] + h, root[2] + 0.02),
                   {'north': {'uv': uv(rect), 'texture': 0},
                    'south': {'uv': [rect[0] + rect[2], rect[1], rect[0], rect[1] + rect[3]], 'texture': 0}},
                   rotation=euler_zyx(R), origin=list(root))
    d['elements'].append(lock)
    ring['children'].append(lock['uuid'])

# ---------------------------------------------------------------- save
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_17_128.png'
d['name'] = 'skin_v16.17'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok: %d elements, free px left %d' % (len(d['elements']), (~OCC).sum()))
