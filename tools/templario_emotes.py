"""Templar (white variant) emotes, on top of the player's hand-edited model (nothing of it is changed).

usage: python3 tools/templario_emotes.py <skin_v16.32_BRANCA.bbmodel> <out.bbmodel>

- Props (new groups/elements, hidden inside the right arm while unused, textured in free atlas space):
  a big golden crucifix (with a small ruby) and, inside it, a burst of light (glowing rays + glow disc).
- Rezar (loop until moving): eyes closed, head bowed, hands joined holding the crucifix, praying.
- Meditacao extrema (loop until moving): floats in the air cross-legged, eyes closed, fur and tail drifting.
- Subestimar (expression layer, face only): "e isso?" -- half-lidded, one brow up, looking down at you.
- Explosao de luz (gesture): raises the crucifix with both hands above the head and it bursts into light.
Closed eyes use a separate non-additive lid animation named "<emote>#olhos": CPM ignores what follows '#',
so it belongs to the same emote button (and the name is unique, so Blockbench does not rename it).
"""
import json, sys, os, math, base64, io, uuid, copy
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20

# ------------------------------------------------------------------ atlas: free space allocator
T = np.array(Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA'))
RES = T.shape[0]
used = T[..., 3] > 0
for e in d['elements']:
    for fc in e['faces'].values():
        if fc.get('texture') is None: continue
        u0, v0, u1, v1 = fc['uv']
        used[int(min(v0, v1)):int(math.ceil(max(v0, v1))), int(min(u0, u1)):int(math.ceil(max(u0, u1)))] = True


def alloc(w, h):
    for y in range(RES - h + 1):
        for x in range(RES - w + 1):
            if not used[y:y + h, x:x + w].any():
                used[y:y + h, x:x + w] = True
                return [x, y, x + w, y + h]
    raise RuntimeError('atlas full')


# ------------------------------------------------------------------ props
G = {g['name']: g for g in d['groups']}


def node_of(nodes, uid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == uid: return n
            r = node_of(n['children'], uid)
            if r: return r


def add_group(parent, name, pivot, els, rotation=(0, 0, 0)):
    g = copy.deepcopy(G['head'])
    g.update(name=name, uuid=str(uuid.uuid4()), origin=list(pivot), rotation=list(rotation))
    d['groups'].append(g)
    G[name] = g
    kids = []
    for nm, f, t, faces, *ex in els:
        ex = dict(ex[0]) if ex else {}
        dens = ex.pop('density', 4)
        glow = ex.pop('glow', False)
        size = {'north': (t[0] - f[0], t[1] - f[1]), 'south': (t[0] - f[0], t[1] - f[1]),
                'east': (t[2] - f[2], t[1] - f[1]), 'west': (t[2] - f[2], t[1] - f[1]),
                'up': (t[0] - f[0], t[2] - f[2]), 'down': (t[0] - f[0], t[2] - f[2])}
        fcs = {}
        for k in ('north', 'east', 'south', 'west', 'up', 'down'):
            if k not in faces:
                fcs[k] = {'uv': [0, 0, 0, 0], 'texture': None}
                continue
            img = faces[k]
            assert img.shape[1::-1] == (round(size[k][0] * dens), round(size[k][1] * dens)), (nm, k, img.shape)
            r = alloc(img.shape[1], img.shape[0])
            T[r[1]:r[3], r[0]:r[2]] = img
            fcs[k] = {'uv': r, 'texture': 0}
        e = {'name': nm, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
             'allow_mirror_modeling': True, 'cpm_glow': glow, 'cpm_recolor': -1, 'cpm_extrude': False,
             'cpm_data': '', 'from': list(f), 'to': list(t), 'autouv': 0, 'color': 3, 'rotation': [0, 0, 0],
             'origin': [(f[i] + t[i]) / 2 for i in range(3)], 'faces': fcs, 'type': 'cube',
             'uuid': str(uuid.uuid4()), **ex}
        d['elements'].append(e)
        kids.append(e['uuid'])
    node_of(d['outliner'], G[parent]['uuid'])['children'].append({'uuid': g['uuid'], 'isOpen': False,
                                                                 'children': kids})


GD = {'H': (255, 240, 170), '1': (240, 200, 110), '2': (212, 164, 80), '3': (176, 128, 56), '4': (130, 90, 34),
      'R': (190, 30, 40), 'r': (120, 16, 24), 'W': (255, 236, 236)}


def grid(lines, pal, alpha=255):
    return np.array([[(*pal[ch], alpha) if ch in pal else (0, 0, 0, 0) for ch in ln] for ln in lines], np.uint8)


def gold_face(w, h, flip=False):
    """golden bar face: lit edge, mid, shaded edge; darker rim at the ends, small engraved marks"""
    cols = ['H', '1', '2', '3'][:max(w, 1)] if w <= 4 else ['H'] + ['1'] * (w - 3) + ['2', '3']
    if w == 3:
        cols = ['H', '1', '3']
    if flip:
        cols = cols[::-1]
    rows = []
    for y in range(h):
        r = ''.join(cols)
        if h > 6 and y % 6 == 3:
            r = ''.join('2' if ch == '1' else ch for ch in r)
        if y in (0, h - 1) and h > 3:
            r = ''.join('2' if ch in 'H1' else '4' for ch in r)
        rows.append(r)
    return grid(rows, GD)


def gold_face_h(w, h, flip=False):
    """same, for a horizontal bar (light on top)"""
    return np.ascontiguousarray(np.transpose(gold_face(h, w, flip), (1, 0, 2))[:, :, :])


# crucifix: rests inside the (slim) right arm: x 4..7, y 12..24, z -2..2. The crossbar runs along z at rest
# (the emotes turn it to face forward). Group pivot = the grip, on the lower part of the vertical bar.
cross_els = [
    ('crucifixo_haste', (5.125, 12.5, -0.375), (5.875, 22.5, 0.375),
     {'north': gold_face(3, 40), 'south': gold_face(3, 40, True), 'east': gold_face(3, 40),
      'west': gold_face(3, 40, True), 'up': grid(["H12", "123", "234"], GD), 'down': grid(["234", "343", "434"], GD)}),
    ('crucifixo_braco', (5.125, 19.0, -1.75), (5.875, 19.75, 1.75),
     {'east': gold_face_h(14, 3), 'west': gold_face_h(14, 3, True), 'up': gold_face(3, 14),
      'down': grid(["343"] * 14, GD), 'north': grid(["H12", "123", "234"], GD), 'south': grid(["21H", "321", "432"], GD)}),
    ('crucifixo_rubi', (5.0, 18.875, -0.5), (6.0, 19.875, 0.5),
     {k: grid(["4114", "1WR4", "1Rr4", "4444"], {**GD, '4': (150, 104, 40), '1': (236, 196, 104)})
      for k in ('north', 'south', 'east', 'west', 'up', 'down')}),
]
# light burst, centred on the crossing of the crucifix: a 3D star of glowing rays + glow discs in the 3 planes
LT = {'w': (255, 252, 232), 'y': (255, 238, 156), 'o': (255, 214, 120)}
ray = np.array([[(*LT['o'], 150), (*LT['y'], 215), (*LT['w'], 250), (*LT['y'], 215), (*LT['o'], 150)]], np.uint8)
disc = np.zeros((4, 4, 4), np.uint8)
for y in range(4):
    for x in range(4):
        r = math.hypot(x - 1.5, y - 1.5) / 2.1
        if r < 1:
            disc[y, x] = (*LT['w'], int(240 * (1 - r * r)))
CX, CY, CZ = 5.5, 19.375, 0.0
burst_els = []
for i, ang in enumerate((0, 45, 90, 135)):
    # rays in the plane of the crucifix (face forward when it is held up)
    burst_els.append(('luz_raio_%d' % (i + 1), (CX - 0.025, CY - 0.125, CZ - 0.625), (CX + 0.025, CY + 0.125, CZ + 0.625),
                      {'east': ray, 'west': ray}, {'glow': True, 'rotation': [ang, 0, 0], 'origin': [CX, CY, CZ]}))
    # rays in the plane across it (seen from the sides)
    burst_els.append(('luz_raio_%d' % (i + 5), (CX - 0.625, CY - 0.125, CZ - 0.025), (CX + 0.625, CY + 0.125, CZ + 0.025),
                      {'north': ray, 'south': ray}, {'glow': True, 'rotation': [0, 0, ang], 'origin': [CX, CY, CZ]}))
    # flat ring of rays (seen from above / below)
    burst_els.append(('luz_raio_%d' % (i + 9), (CX - 0.625, CY - 0.025, CZ - 0.125), (CX + 0.625, CY + 0.025, CZ + 0.125),
                      {'up': ray, 'down': ray}, {'glow': True, 'rotation': [0, ang, 0], 'origin': [CX, CY, CZ]}))
burst_els.append(('luz_clarao_1', (CX - 0.025, CY - 0.5, CZ - 0.5), (CX + 0.025, CY + 0.5, CZ + 0.5),
                  {'east': disc, 'west': disc}, {'glow': True}))
burst_els.append(('luz_clarao_2', (CX - 0.5, CY - 0.5, CZ - 0.025), (CX + 0.5, CY + 0.5, CZ + 0.025),
                  {'north': disc, 'south': disc}, {'glow': True}))
burst_els.append(('luz_clarao_3', (CX - 0.5, CY - 0.025, CZ - 0.5), (CX + 0.5, CY + 0.025, CZ + 0.5),
                  {'up': disc, 'down': disc}, {'glow': True}))

GRIP = (5.5, 15.0, 0.0)
add_group('right_arm', 'prop_crucifixo', GRIP, cross_els)
add_group('prop_crucifixo', 'luz_explosao', (CX, CY, CZ), burst_els)

buf = io.BytesIO(); Image.fromarray(T).save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

# ------------------------------------------------------------------ animation tools
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
assert len(d['groups']) == n_groups
EXISTING = list(d['animations'])
HAND = {'right_arm': np.array([5.5, 11.6, 0.0]), 'left_arm': np.array([-5.5, 11.6, 0.0])}   # slim arms
REST = {'prop_crucifixo': np.array(GRIP)}


def reach(arm, target, drop=(0, 0, 0)):
    A = np.array(PIVOT[arm], float) + np.array(drop, float)
    return euler_zyx(R_to(HAND[arm] - np.array(PIVOT[arm], float), np.array(target, float) - A))


def hand_world(arm, rot, drop=(0, 0, 0)):
    A = np.array(PIVOT[arm], float)
    return A + rotmat(rot) @ (HAND[arm] - A) + np.array(drop, float)


def on_sphere(arm, x, y, drop=(0, 0, 0)):
    A = np.array(PIVOT[arm], float) + np.array(drop, float)
    r = np.linalg.norm(HAND[arm] - np.array(PIVOT[arm], float))
    dz2 = r * r - (x - A[0]) ** 2 - (y - A[1]) ** 2
    return np.array([x, y, A[2] - math.sqrt(max(0.0, dz2))])


def place(arm_rot, R, W, drop=(0, 0, 0)):
    """crucifix group (child of the right arm): pivot at world W, world rotation R"""
    A = np.array(PIVOT['right_arm'], float)
    Ra = rotmat(arm_rot)
    return euler_zyx(Ra.T @ R), tuple(Ra.T @ (np.array(W, float) - A - np.array(drop, float)) + A - REST['prop_crucifixo'])


CROSS_UP = rotmat((0, 90, 0))                 # crossbar across, front face forward


def closed_eyes(a, fn=c(0.0), side='RL'):
    """eyes shut (or half shut): lids in their own non-additive animation '<name>#olhos' (same CPM button)"""
    eyes_open(a, fn, side)
    a._lids.name = a.name + '#olhos'


def hands_together(y, drop=(0, 0, 0)):
    """both hands joined in front (straight arms meet on their reach spheres)"""
    tr = on_sphere('right_arm', 0.55, y, drop)
    tl = on_sphere('left_arm', -0.55, y, drop)
    r, l = reach('right_arm', tr, drop), reach('left_arm', tl, drop)
    mid = (hand_world('right_arm', r, drop) + hand_world('left_arm', l, drop)) / 2
    return r, l, mid


def appear(setup, finish, dur):
    """the crucifix appears in the joined hands (grows from the grip) instead of sliding out of the sleeve"""
    grow = curve([(0, 0.05), (0.55 * dur, 0.05), (dur, 1.0)])
    shrink = curve([(0, 1.0), (0.45 * dur, 0.05), (dur, 0.05)])
    setup.scl('prop_crucifixo', lambda t: (grow(t),) * 3)
    finish.scl('prop_crucifixo', lambda t: (shrink(t),) * 3)


def env(points):
    return curve(points)


# ------------------------------------------------------------------ Rezar (loop until the player moves)
a = Anim('Rezar', 'custom_pose', 4.0)
r_p, l_p, mid_p = hands_together(16.0)
cr_r, cr_p = place(r_p, CROSS_UP @ rotmat((-8, 0, 0)), mid_p + np.array([0, 0.3, -0.7]))   # top leaning to the face
for b, v in (('right_arm', r_p), ('left_arm', l_p)):
    a.rot(b, c(v))
a.rot('prop_crucifixo', c(cr_r)).pos('prop_crucifixo', c(cr_p))
a.scl('luz_explosao', c((0.02, 0.02, 0.02)))
breath = wave(4.0, -0.25)
a.rot('head', lambda t: (-22 + 1.5 * breath(t), 0.0, 0.0))        # bowed, breathing
a.rot('body', lambda t: (-3 + 0.6 * breath(t), 0.0, 0.0))
closed_eyes(a)
brows(a, lift=-0.03, tilt=-6)                                       # serene
ears(a, back=14, out=10)
tail_pose(a, rx=(10, 3, 1, 0, 0))
a.rot('cauda_ponta', lambda t: (0.0, 4 * math.sin(2 * math.pi * t / 4.0), 0.0))
staged_custom(a, 0.6)
appear(ANIMS[-2], ANIMS[-1], 0.6)

# ------------------------------------------------------------------ Meditacao extrema (loop until moving)
L_MED = 6.0
a = Anim('Meditacao extrema', 'custom_pose', L_MED)
LIFT = 6.0
bob = wave(3.0, -0.25)
legs = {'right_leg': (84, 38, 0), 'left_leg': (84, -38, 0)}            # crossed in front
knee = {s: np.array(PIVOT[s], float) + rotmat(legs[s]) @ np.array([0, -6.5, 0]) for s in legs}
DROP = (0, LIFT, 0)
arms = {'right_arm': reach('right_arm', knee['right_leg'] + np.array([0.6, 1.2 + LIFT, 0]), DROP),
        'left_arm': reach('left_arm', knee['left_leg'] + np.array([-0.6, 1.2 + LIFT, 0]), DROP)}
lot = rig(drop=DROP, limbs={**legs, **arms, 'head': (4, 0, 0)})
for b, (r, p) in lot.items():
    a.rot(b, c(r))
    a.pos(b, (lambda p: lambda t: (p[0], p[1] + 0.6 * bob(t), p[2]))(p))
a.rot('body', lambda t: (0.0, 3 * math.sin(2 * math.pi * t / L_MED), 0.0))
closed_eyes(a)
brows(a, lift=0.02, tilt=-4)
ears_fn(a, fn_back=lambda t: -4 + 3 * math.sin(2 * math.pi * t / 3.0), fn_out=lambda t: 6.0)
tail_pose(a, rx=(-28, -12, -10, -6, -4), ry=(0, 0, 0, 0, 0))
for i, b in enumerate(TAIL):                                          # tail drifting around the body
    a.rot(b, lambda t, i=i: (4 * math.sin(2 * math.pi * (t / 3.0 - 0.1 * i)), 10 * math.sin(2 * math.pi * (t / L_MED - 0.08 * i)), 0.0))
fur_flutter(a, 8.0, 3.0)                                             # fur floating
staged_custom(a, 0.8)

# ------------------------------------------------------------------ Subestimar (expression layer, face only)
a = Anim('Subestimar', 'layer', 3.0)
a.pos('palp_R', c((0.0, 0.24, 0.0))).rot('palp_R', c((0.0, 0.0, -7.0)))      # one brow up, arched
closed_eyes(a, c(0.5), side='L')                                              # the other eye half-lidded, bored
a.rot('palp_L', c((0.0, 0.0, 4.0)))
for s_ in 'RL':                                                               # looking down at "that"
    a.pos('iris_' + s_, lambda t: (0.1 * curve([(0, 1), (1.4, 1), (1.6, -0.3), (2.6, -0.3), (3.0, 1)])(t), -0.16, 0.0))
ears(a, back=8, out=20)                                                      # "meh"
ears_fn(a, fn_twist=lambda t: 12 * twitch([2.0], 0.3)(t), side='L')
sn = twitch([1.5], 0.35)                                                     # little huff through the nose
a.pos('nariz', lambda t: (0.0, 0.03 * sn(t), -0.02 * sn(t)))
staged_layer(a, 0.3)

# ------------------------------------------------------------------ Explosao de luz (gesture)
a = Anim('Explosao de luz', 'gesture', 6.0, loop='once')
Y_CHEST, Y_UP = 16.6, 30.5                     # hand height: at the chest / above the head (arms almost straight up)
out_k = curve([(0, 0), (0.7, 1), (4.4, 1), (5.4, 0), (6.0, 0)])                 # out of the rest pose and back
lift_k = curve([(0, Y_CHEST), (0.8, Y_CHEST), (1.6, Y_UP), (3.4, Y_UP), (4.4, Y_CHEST), (6.0, Y_CHEST)])
_memo = {}


def held_pose(t):
    """arms + crucifix: hands joined at the current height (exact grip), blended with the rest pose"""
    key = round(t, 4)
    if key not in _memo:
        y = lift_k(t)
        r, l, mid = hands_together(y)
        tilt = (y - Y_CHEST) / (Y_UP - Y_CHEST)
        pr, pp = place(r, CROSS_UP, mid + np.array([0, 0.3 + 0.4 * tilt, -0.7]))
        k = out_k(t)
        _memo[key] = tuple(tuple(k * x for x in v) for v in (r, l, pr, pp))
    return _memo[key]


a.rot('right_arm', lambda t: held_pose(t)[0]).rot('left_arm', lambda t: held_pose(t)[1])
a.rot('prop_crucifixo', lambda t: held_pose(t)[2]).pos('prop_crucifixo', lambda t: held_pose(t)[3])
REC = (0, -0.7, 0)                             # the burst pushes him down a little
keyposes(a, [
    (0.0, {}),
    (0.8, {'head': ((-10, 0, 0), Z3)}),
    (1.6, {'head': ((22, 0, 0), Z3), 'body': ((2, 0, 0), Z3)}),
    (2.25, {'head': ((25, 0, 0), Z3), 'body': ((2, 0, 0), Z3)}),
    (2.45, merge(rig(drop=REC), {'head': ((16, 0, 0), REC), 'body': ((5, 0, 0), REC)})),
    (3.4, {'head': ((20, 0, 0), Z3), 'body': ((2, 0, 0), Z3)}),
    (4.4, {'head': ((-12, 0, 0), Z3)}),
    (6.0, {})])
s_burst = curve([(0, 0.02), (1.8, 0.02), (2.2, 0.7), (2.3, 1.2), (2.42, 10.0), (2.9, 13.0), (3.2, 6.0),
                 (3.35, 0.02), (6.0, 0.02)], ease=lambda x: x)
a.scl('luz_explosao', lambda t: (s_burst(t),) * 3)
cross_s = curve([(0, 0.05), (0.45, 0.05), (0.8, 1.0), (4.4, 1.0), (4.8, 0.05), (6.0, 0.05)])
a.scl('prop_crucifixo', lambda t: (cross_s(t),) * 3)
a.rot('luz_explosao', lambda t: (40 * max(0.0, min(1.0, (t - 2.3) / 1.0)), 0.0, 0.0))   # rays turn while it blows
blast = env([(0, 0), (2.3, 0), (2.45, 1), (3.0, 1), (3.6, 0), (6.0, 0)])
glowing = env([(0, 0), (1.8, 0), (2.3, 1), (3.4, 1), (4.0, 0), (6.0, 0)])
brows(a, lift=-0.12, tilt=4, fn=blast)                                   # eyes narrowed in the light
ears_fn(a, fn_back=lambda t: 40 * blast(t) - 8 * glowing(t) * (1 - blast(t)), fn_out=lambda t: 10 * blast(t))
fur_lift(a, FUR, lambda t, i: 20 * blast(t) * (0.7 + 0.3 * math.sin(i * 1.3)))
tail_pose(a, rx=(-30, -10, -8, -4, -2), fn=blast)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, 0.2 * env([(0, 0), (1.6, 1), (3.4, 1), (4.4, 0), (6.0, 0)])(t), 0.0))

# ------------------------------------------------------------------ save
order = {}
for x in EXISTING:
    order[x['cpm_type']] = order.get(x['cpm_type'], 0) + 1
new = []
for an in ANIMS:
    j = an.to_json()
    j['cpm_order'] = order.get(an.type, 0)
    order[an.type] = order.get(an.type, 0) + 1
    new.append(j)
d['animations'] = EXISTING + new
name = os.path.basename(OUT).rsplit('.', 1)[0]
png = name.replace('skin_', 'Emezomm-CPM_') + '_256.png'
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = png
d['name'] = name
json.dump(d, open(OUT, 'w'))
Image.fromarray(T).save(os.path.join(os.path.dirname(OUT) or '.', png))
print('ok: %d new animations -> %s' % (len(new), [x['name'] for x in new]))
