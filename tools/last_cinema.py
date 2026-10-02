"""L.A.S.T: "Cinema" emote. A hologram sign appears between the hands and is lifted above the head with both hands.

usage: python3 tools/last_cinema.py <skin_v16.49_LAST.bbmodel> <skin_v16.50_LAST.bbmodel>

The sign (glowing, the same cyan as the other L.A.S.T holograms, film-strip borders and the word CINEMA) rests hidden
inside the torso like the other holograms; the emote scales it up in front of the chest (materialising with a
flicker), the hands take its sides, a short dip, it goes up over the head (overshoot, settle), is held with a light
bob, comes down and dissolves.
"""
import json, sys, os, math, base64, io, uuid, copy
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20

# ------------------------------------------------------------------ atlas
T = np.array(Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA'))
RES = T.shape[0]
used = T[..., 3] > 0
for e in d['elements']:
    for fc in e['faces'].values():
        if fc.get('texture') is not None:
            u0, v0, u1, v1 = fc['uv']
            used[int(min(v0, v1)):int(math.ceil(max(v0, v1))), int(min(u0, u1)):int(math.ceil(max(u0, u1)))] = True


def alloc(w, h):
    for y in range(RES - h + 1):
        for x in range(RES - w + 1):
            if not used[y:y + h, x:x + w].any():
                used[y:y + h, x:x + w] = True
                return [x, y, x + w, y + h]
    raise RuntimeError('atlas full')


# ------------------------------------------------------------------ the sign texture (44 x 16)
FONT = {'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
        'I': ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        'N': ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
        'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
        'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"]}
DARK, MID, LIGHT, WHITE = (40, 120, 170, 110), (60, 170, 230, 170), (120, 235, 255, 210), (210, 250, 255, 235)
W_, H_ = 44, 16
img = np.zeros((H_, W_, 4), np.uint8)
img[:, :] = DARK
img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = LIGHT                       # frame
for y in (1, 2, 13, 14):                                                     # film strip: perforations
    img[y, 1:-1] = MID
    for x in range(3, W_ - 3, 4):
        img[y, x:x + 2] = (0, 0, 0, 0) if y in (1, 14) else WHITE
img[3, 1:-1] = img[12, 1:-1] = MID
x0 = (W_ - (6 * 5 + 5 * 1)) // 2
for i, ch in enumerate('CINEMA'):
    for r, row in enumerate(FONT[ch]):
        for cidx, v in enumerate(row):
            if v == '1':
                img[4 + r, x0 + i * 6 + cidx] = WHITE
                if 4 + r + 1 < 12 and img[4 + r + 1, x0 + i * 6 + cidx][3] != 235:
                    img[4 + r + 1, x0 + i * 6 + cidx] = LIGHT                   # soft glow under the letters

# ------------------------------------------------------------------ sign element + group (inside the torso at rest)
G = {g['name']: g for g in d['groups']}


def node_of(nodes, uid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == uid:
                return n
            r = node_of(n['children'], uid)
            if r:
                return r


DENS = 6
PW, PH = W_ / DENS, H_ / DENS                                                # 7.33 x 2.67 at rest
PIV = (0.0, 18.0, 0.0)
fr, to = (-PW / 2, 18 - PH / 2, -0.025), (PW / 2, 18 + PH / 2, 0.025)
r_n = alloc(W_, H_)
T[r_n[1]:r_n[3], r_n[0]:r_n[2]] = img
r_s = alloc(W_, H_)
T[r_s[1]:r_s[3], r_s[0]:r_s[2]] = img                                     # readable from behind too
faces = {k: {'uv': [0, 0, 0, 0], 'texture': None} for k in ('east', 'west', 'up', 'down')}
faces['north'] = {'uv': r_n, 'texture': 0}
faces['south'] = {'uv': r_s, 'texture': 0}
el = {'name': 'holo_cinema_tela', 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True,
      'scope': 0, 'allow_mirror_modeling': True, 'cpm_glow': True, 'cpm_recolor': -1, 'cpm_extrude': False,
      'cpm_data': '', 'from': list(fr), 'to': list(to), 'autouv': 0, 'color': 3, 'rotation': [0, 0, 0],
      'origin': list(PIV), 'faces': faces, 'type': 'cube', 'uuid': str(uuid.uuid4())}
d['elements'].append(el)
g = copy.deepcopy(G['holo'])
g.update(name='holo_cinema', uuid=str(uuid.uuid4()), origin=list(PIV), rotation=[0, 0, 0])
d['groups'].append(g)
node_of(d['outliner'], G['holo']['uuid'])['children'].append({'uuid': g['uuid'], 'isOpen': False,
                                                              'children': [el['uuid']]})
buf = io.BytesIO()
Image.fromarray(T).save(buf, 'PNG', optimize=True)
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

# ------------------------------------------------------------------ animation
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
EXISTING = list(d['animations'])
HAND = {'right_arm': np.array([6.0, 11.6, 0.0]), 'left_arm': np.array([-6.0, 11.6, 0.0])}


def reach(arm, target):
    A = np.array(PIVOT[arm], float)
    return euler_zyx(R_to(HAND[arm] - A, np.array(target, float) - A))


def on_sphere(arm, x, y):
    A = np.array(PIVOT[arm], float)
    r = np.linalg.norm(HAND[arm] - A)
    dz2 = r * r - (x - A[0]) ** 2 - (y - A[1]) ** 2
    return np.array([x, y, A[2] - math.sqrt(max(0.0, dz2))])


L = 6.4
a = Anim('Cinema', 'gesture', L, loop='once')
# key heights of the hands (y) and how far apart (x); 1 = chest, 2 = over the head
CH = (3.9, 17.0)
UP = (5.2, 32.2)
lift = curve([(0, 0.0), (1.15, 0.0), (1.4, -0.06),                          # anticipation: a small dip
              (2.0, 1.04), (2.2, 0.985), (2.35, 1.0),                         # up, a bit past, settle
              (4.7, 1.0), (5.25, 0.0), (L, 0.0)])
out_k = curve([(0, 0), (0.55, 1.0), (5.55, 1.0), (6.15, 0.0), (L, 0.0)])     # arms out of / back to rest
bob = lambda t: 0.25 * math.sin(2 * math.pi * (t - 2.35) / 1.15) * curve([(0, 0), (2.4, 0), (2.8, 1), (4.4, 1), (4.7, 0), (L, 0)])(t)
size = lambda u: 1.0 + 0.6 * u                                              # 7.3 wide at the chest, 11.7 over the head
show = curve([(0, 0.02), (0.6, 0.02), (0.75, 0.55), (0.8, 0.3), (0.95, 0.9), (1.0, 0.75), (1.15, 1.0),   # flicker in
              (5.3, 1.0), (5.4, 0.6), (5.45, 0.85), (5.7, 0.02), (L, 0.02)], ease=lambda x: x)
memo = {}


ARM_CH = (80.0, 11.0, 0.0)      # arm raise (x), turn in (y), sideways (z): holding the sign at the chest
ARM_UP = (163.0, 0.0, 7.0)      # ... and over the head
# plain x / z angles, interpolated directly: no direction solving per frame, so the arms never flip or spin


def hand_world(arm, rot):
    A = np.array(PIVOT[arm], float)
    return A + rotmat(rot) @ (HAND[arm] - A)


def pose(t):
    k = round(t, 4)
    if k not in memo:
        u = lift(t)
        m = out_k(t)
        ax, ay, az = [c0 + (c1 - c0) * u for c0, c1 in zip(ARM_CH, ARM_UP)]
        rr, rl = (ax * m, ay * m, az * m), (ax * m, -ay * m, -az * m)
        hr, hl = hand_world('right_arm', (ax, ay, az)), hand_world('left_arm', (ax, -ay, -az))
        s = size(max(0.0, u)) * show(t)
        center = (hr + hl) / 2 + np.array([0.0, 0.0, -0.3])
        # at the chest the hands hold the middle of the sides; over the head they hold the bottom corners
        center[1] += smooth((u - 0.3) / 0.5) * PH * size(u) / 2
        memo[k] = (rr, rl, tuple(center - np.array(PIV)), (s, s, s))
    return memo[k]


a.rot('right_arm', lambda t: pose(t)[0]).rot('left_arm', lambda t: pose(t)[1])
a.pos('holo_cinema', lambda t: pose(t)[2] if show(t) > 0.05 else Z3).scl('holo_cinema', lambda t: pose(t)[3])
# head follows the sign up a little and comes back; proud face; ears up, tail happy
look = curve([(0, 0), (0.6, -8), (1.2, -6), (2.1, 14), (2.5, 10), (4.6, 10), (5.3, -6), (6.0, 0), (L, 0)])
a.rot('head', lambda t: (look(t), 0.0, 0.0))
a.rot('body', lambda t: (curve([(0, 0), (1.3, 2.5), (1.45, 3.5), (2.1, -2.0), (2.4, -1.4), (4.7, -1.4), (5.4, 1.0), (L, 0)])(t), 0.0, 0.0))
happy = curve([(0, 0), (0.6, 1), (5.8, 1), (L, 0)])
brows(a, lift=0.08, tilt=-3, fn=happy)
for s_ in 'RL':
    a.pos('iris_' + s_, lambda t: (0.0, 0.12 * curve([(0, 0), (0.7, -1), (1.3, -1), (2.0, 1), (4.7, 1), (5.4, -0.5), (L, 0)])(t), 0.0))
ears_fn(a, fn_back=lambda t: -10 * happy(t), fn_out=lambda t: 4 * happy(t))
tail_wave(a, 7.0, 0.8)

# ------------------------------------------------------------------ save
menu_after = 'Finalizando missao'
order_new = next((x['cpm_order'] for x in EXISTING if x['name'] == menu_after), 14) + 1
for x in EXISTING:
    if x['cpm_type'] in ('layer', 'gesture', 'custom_pose') and x.get('cpm_order', 0) >= order_new:
        x['cpm_order'] += 1
j = a.to_json()
j['cpm_order'] = order_new
d['animations'] = EXISTING + [j]
d['name'] = os.path.basename(OUT).rsplit('.', 1)[0]
json.dump(d, open(OUT, 'w'))
print('ok')
