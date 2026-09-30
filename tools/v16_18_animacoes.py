"""v16.18: CPM animations for everything we added (tail, ears, fur tufts, snout, eyes, lids)
+ glowing white iris.

The model itself is not changed: only zero-rotation "wrapper" bones are inserted around a few parts so
they can be animated on their own (a wrapper with rotation 0 moves nothing), the iris cubes get
cpm_glow, and the grey sides of the iris are painted with the same white as its front.

Animations are Blockbench animations with the CPM plugin fields (cpm_type, cpm_additive, ...):
  cpm_type = a vanilla pose  (walking, running, sleeping, hurt, ...)  -> plays automatically in that state
  cpm_type = "global"        -> always plays
  cpm_type = "gesture"       -> CPM gesture wheel
  cpm_type = "layer"         -> CPM toggle
All of them are additive, so Minecraft's own body/arm/leg animation keeps working untouched.

usage: python3 tools/v16_18_animacoes.py <in.bbmodel> <out.bbmodel>
"""
import json, base64, io, math, os, sys, copy, uuid
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20

# ============================================================ model: wrappers, glow
ELS = {e['name']: e for e in d['elements']}
GRP = {g['name']: g for g in d['groups']}
TEMPLATE = GRP['bochechas']


def find_node(nodes, gid):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == gid:
                return n
            f = find_node(n['children'], gid)
            if f:
                return f


def wrap(name, parent, children, pivot):
    """Insert a zero-rotation bone `name` inside group `parent` around `children`
    (element names or group names) - keeps the children's position in the outliner."""
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[round(v, 4) for v in pivot], rotation=[0, 0, 0])
    d['groups'].append(g)
    GRP[name] = g
    pnode = find_node(d['outliner'], GRP[parent]['uuid'])
    ids = [ELS[c]['uuid'] if c in ELS else GRP[c]['uuid'] for c in children]
    nodes = [c for c in pnode['children'] if (c if isinstance(c, str) else c['uuid']) in ids]
    idx = min(pnode['children'].index(n) for n in nodes)
    for n in nodes:
        pnode['children'].remove(n)
    pnode['children'].insert(idx, {'uuid': g['uuid'], 'isOpen': False, 'children': nodes})


eR, eL = ELS['eye_R'], ELS['eye_L']
cen = lambda e: [(e['from'][i] + e['to'][i]) / 2 for i in range(3)]
wrap('iris_R', 'olhos', ['eye_R_iris'], cen(ELS['eye_R_iris']))
wrap('iris_L', 'olhos', ['eye_L_iris'], cen(ELS['eye_L_iris']))
wrap('olho_R', 'olhos', ['eye_R', 'iris_R'], cen(eR))
wrap('olho_L', 'olhos', ['eye_L', 'iris_L'], cen(eL))
for s in 'RL':
    lid = ELS['palpebra_' + s]
    wrap('palp_' + s, 'palpebras', ['palpebra_' + s], [cen(lid)[0], lid['to'][1], -4.05])     # pivot: top of lid
nose = ELS['nose']
wrap('nariz', 'focinho', ['nose'], [0, nose['from'][1], nose['to'][2]])                      # base of the nose
wrap('mandibula', 'focinho', ['snout_bottom'], [0, 24.35, -3.7])                             # jaw hinge
wrap('orelha_L_mov', 'orelhas', ['orelha_L'], GRP['orelha_L']['origin'])
wrap('orelha_R_mov', 'orelhas', ['orelha_R'], GRP['orelha_R']['origin'])

# glowing, bright iris
tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
T = tex.load()
for n in ('eye_R_iris', 'eye_L_iris'):
    e = ELS[n]
    e['cpm_glow'] = True
    for fc in e['faces'].values():
        x0, y0, x1, y1 = fc['uv']
        if [x0, y0] == [127, 127]:
            continue
        for y in range(int(min(y0, y1)), int(max(y0, y1))):
            for x in range(int(min(x0, x1)), int(max(x0, x1))):
                T[x, y] = (247, 247, 247, 255)
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


# ============================================================ math helpers
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
    return (math.degrees(a), math.degrees(b), math.degrees(c))


EAR_PARENT = rotmat(GRP['orelhas']['rotation'])


def ear(side, back=0.0, out=0.0, twist=0.0):
    """Ear motion described in the world: back = tip goes backwards, out = tip falls to the outside,
    twist = opening turns to the outside. Converted to the ear bone's own frame (it sits inside the
    41° 'orelhas' group)."""
    sg = 1 if side == 'L' else -1
    W = rotmat((0, sg * twist, 0)) @ rotmat((0, 0, sg * out)) @ rotmat((back, 0, 0))
    return euler_zyx(EAR_PARENT.T @ W @ EAR_PARENT)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def curve(points, ease=smooth):
    """points: [(time, value)] -> f(t), eased between points; value = number or tuple."""
    pts = sorted(points)

    def f(t):
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t <= t1:
                a = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
                if isinstance(v0, tuple):
                    return tuple(x + (y - x) * a for x, y in zip(v0, v1))
                return v0 + (v1 - v0) * a
        return pts[-1][1]
    return f


def wave(period, phase=0.0):
    """sin wave with the given period (s) and phase (fraction of a period)."""
    return lambda t: math.sin(2 * math.pi * (t / period + phase))


Z3, O3 = (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
add3 = lambda *vs: tuple(sum(v[i] for v in vs) for i in range(3))
mul3 = lambda v, k: tuple(x * k for x in v)


# ============================================================ animation builder
TAIL = ['cauda', 'cauda_1', 'cauda_2', 'cauda_3', 'cauda_ponta']
FUR = ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows', 'fur_chest_edge_R', 'fur_chest_edge_L']
ANIMS = []


class Anim:
    def __init__(self, name, cpm_type, length, loop='loop', layer_default=0):
        self.name, self.type, self.length, self.loop = name, cpm_type, length, loop
        self.tracks = {}          # bone -> channel -> list of functions (summed / multiplied)
        self.layer_default = layer_default
        ANIMS.append(self)

    def add(self, bone, channel, fn):
        """fn(t) -> (x, y, z) in model convention (rotation deltas in degrees, position in pixels,
        scale factors). Several fns on the same channel are summed (scale: multiplied)."""
        assert bone in GRP, bone
        self.tracks.setdefault(bone, {}).setdefault(channel, []).append(fn)
        return self

    def rot(self, bone, fn):
        return self.add(bone, 'rotation', fn)

    def pos(self, bone, fn):
        return self.add(bone, 'position', fn)

    def scl(self, bone, fn):
        return self.add(bone, 'scale', fn)

    def value(self, bone, channel, t):
        fns = self.tracks[bone][channel]
        if channel == 'scale':
            out = O3
            for f in fns:
                v = f(t)
                out = tuple(a * b for a, b in zip(out, v))
            return out
        return add3(*[f(t) for f in fns])

    def sample(self, bone, t):
        """model-convention (rot, pos, scale) of a bone at time t (for previews)."""
        tr = self.tracks.get(bone, {})
        r = self.value(bone, 'rotation', t) if 'rotation' in tr else Z3
        p = self.value(bone, 'position', t) if 'position' in tr else Z3
        s = self.value(bone, 'scale', t) if 'scale' in tr else O3
        return r, p, s

    def to_json(self):
        animators = {}
        n = max(1, int(round(self.length * FPS)))
        for bone, chans in self.tracks.items():
            kfs = []
            for ch in chans:
                vals = [(i / FPS, self.value(bone, ch, i / FPS)) for i in range(n + 1)]
                # drop keys that a straight line between neighbours already gives (keeps files light)
                keep = [vals[0]]
                for i in range(1, len(vals) - 1):
                    a, b, c = keep[-1], vals[i], vals[i + 1]
                    ta = (b[0] - a[0]) / (c[0] - a[0])
                    if any(abs(b[1][k] - (a[1][k] + (c[1][k] - a[1][k]) * ta)) > 0.02 for k in range(3)):
                        keep.append(b)
                keep.append(vals[-1])
                if all(max(abs(v[k] - keep[0][1][k]) for _, v in keep) < 1e-4 for k in range(3)):
                    keep = [keep[0]]                                   # constant channel -> one key
                for t, v in keep:
                    if ch == 'rotation':
                        v = (-v[0], -v[1], v[2])                       # Blockbench animation convention
                    elif ch == 'position':
                        v = (-v[0], v[1], v[2])
                    kfs.append({'channel': ch, 'data_points': [{'x': round(v[0], 3), 'y': round(v[1], 3),
                                                                 'z': round(v[2], 3)}],
                                'uuid': str(uuid.uuid4()), 'time': round(t, 4), 'color': -1,
                                'interpolation': 'linear'})
            animators[GRP[bone]['uuid']] = {'name': bone, 'type': 'bone', 'keyframes': kfs}
        return {
            'uuid': str(uuid.uuid4()), 'name': self.name, 'loop': self.loop, 'override': False,
            'length': self.length, 'snapping': FPS, 'selected': False, 'anim_time_update': '',
            'blend_weight': '', 'start_delay': '', 'loop_delay': '', 'animators': animators,
            'cpm_type': self.type, 'cpm_additive': True, 'cpm_layerCtrl': True, 'cpm_commandCtrl': False,
            'cpm_priority': 0, 'cpm_order': len([a for a in ANIMS[:ANIMS.index(self)] if a.type == self.type]),
            'cpm_isProperty': False, 'cpm_group': '', 'cpm_layerDefault': self.layer_default,
        }


# ------------------------------------------------------------ reusable motions
def c(v):
    return lambda t: v


def tail_wave(a, amp, period, lag=0.12, grow=1.25, axis=1, lift=None, phase=0.0):
    """Side-to-side (axis=1) or up/down (axis=0) wave running down the tail: every segment follows
    the previous one a little later and a little wider (follow-through)."""
    for i, b in enumerate(TAIL):
        w = wave(period, phase - lag * i)
        k = amp * grow ** i
        a.rot(b, (lambda w, k: lambda t: tuple(k * w(t) if j == axis else 0.0 for j in range(3)))(w, k))
        if lift is not None:
            a.rot(b, c((lift[i], 0.0, 0.0)))


def tail_pose(a, rx=(0, 0, 0, 0, 0), ry=(0, 0, 0, 0, 0), fn=None):
    """Static tail shape (optionally faded in/out by fn(t) in 0..1)."""
    for i, b in enumerate(TAIL):
        v = (rx[i], ry[i], 0.0)
        a.rot(b, c(v) if fn is None else (lambda v: lambda t: mul3(v, fn(t)))(v))


def ears(a, back=0.0, out=0.0, twist=0.0, fn=None, side='RL'):
    for s in side:
        v = ear(s, back, out, twist)
        a.rot('orelha_%s_mov' % s, c(v) if fn is None else (lambda v: lambda t: mul3(v, fn(t)))(v))


def ears_fn(a, fn_back=None, fn_out=None, fn_twist=None, side='RL'):
    z = lambda t: 0.0
    for s in side:
        a.rot('orelha_%s_mov' % s, (lambda s: lambda t: ear(s, (fn_back or z)(t), (fn_out or z)(t),
                                                             (fn_twist or z)(t)))(s))


LID_DROP = ELS['palpebra_R']['from'][1] - 27.40            # lid bottom -> closed-eye line


def eyes_open(a, fn, side='RL'):
    """fn(t) = how open the eye is (1 open, 0 shut). Squashes the eye and slides the lid down over it."""
    for s in side:
        a.scl('olho_' + s, lambda t: (1.0, 0.1 + 0.9 * fn(t), 1.0))
        a.pos('palp_' + s, lambda t: (0.0, -LID_DROP * (1 - fn(t)), 0.0))


def brows(a, lift=0.0, tilt=0.0, fn=None):
    """Expression with the lids (the model has no separate brows): lift = up/down,
    tilt > 0 = inner ends down (angry), < 0 = inner ends up (sad)."""
    f = fn or (lambda t: 1.0)
    a.pos('palp_R', lambda t: (0.0, lift * f(t), 0.0)).rot('palp_R', lambda t: (0.0, 0.0, tilt * f(t)))
    a.pos('palp_L', lambda t: (0.0, lift * f(t), 0.0)).rot('palp_L', lambda t: (0.0, 0.0, -tilt * f(t)))


def fur_flutter(a, amp, period, bones=FUR, axis=0, base=0.0):
    for i, b in enumerate(bones):
        w = wave(period, i * 0.17)
        a.rot(b, (lambda w: lambda t: tuple((base + amp * w(t)) if j == axis else 0.0 for j in range(3)))(w))


def puff(a, k, bones, fn=None):
    f = fn or (lambda t: 1.0)
    for b in bones:
        a.scl(b, lambda t: tuple(1 + (k - 1) * f(t) for _ in range(3)))


def twitch(times, dur=0.22, amp=1.0):
    """0..amp..0 bumps at the given times."""
    def f(t):
        v = 0.0
        for t0 in times:
            x = (t - t0) / dur
            if 0 <= x <= 1:
                v += amp * math.sin(math.pi * x)
        return v
    return f


# ============================================================ GLOBAL (always on)
a = Anim('Piscar', 'global', 6.0)
BL = [(0, 1), (1.9, 1), (2.0, 0), (2.08, 0), (2.22, 1), (4.7, 1), (4.78, 0), (4.84, 0), (4.95, 1),
      (5.08, 1), (5.16, 0), (5.22, 0), (5.36, 1), (6.0, 1)]
eyes_open(a, curve(BL, ease=lambda x: x))

a = Anim('Respirar', 'global', 3.6)
br = wave(3.6, -0.25)
a.scl('fur_chest_rows', lambda t: (1 + 0.02 * (br(t) + 1) / 2, 1 + 0.03 * (br(t) + 1) / 2, 1 + 0.08 * (br(t) + 1) / 2))
a.pos('fur_chest_rows', lambda t: (0.0, 0.03 * (br(t) + 1) / 2, -0.04 * (br(t) + 1) / 2))
for s, sg in (('R', 1), ('L', -1)):
    a.rot('fur_chest_edge_' + s, lambda t, sg=sg: (0.0, 0.0, sg * 2.0 * (br(t) + 1) / 2))
a.scl('bochechas', lambda t: (1 + 0.015 * (br(t) + 1) / 2, 1.0, 1 + 0.015 * (br(t) + 1) / 2))

a = Anim('Orelhas vivas', 'global', 7.0)
tw_L, tw_R, both = twitch([1.5], 0.28), twitch([4.2, 4.55], 0.24), twitch([6.1], 0.35)
sway = wave(7.0 / 2)
ears_fn(a, fn_back=lambda t: 1.2 * sway(t) + 8 * tw_L(t) + 6 * both(t), fn_twist=lambda t: 16 * tw_L(t), side='L')
ears_fn(a, fn_back=lambda t: -1.2 * sway(t) + 8 * tw_R(t) + 6 * both(t), fn_twist=lambda t: 16 * tw_R(t), side='R')

a = Anim('Focinho farejando', 'global', 5.0)
sn = twitch([1.0, 1.18, 1.36, 3.6, 3.75], 0.14)
a.pos('nariz', lambda t: (0.0, 0.06 * sn(t), -0.03 * sn(t)))
a.scl('nariz', lambda t: (1 + 0.08 * sn(t), 1 + 0.05 * sn(t), 1.0))
a.rot('focinho', lambda t: (-1.2 * sn(t), 0.0, 0.0))
a.scl('bochechas', lambda t: (1 + 0.03 * sn(t), 1.0, 1.0))

a = Anim('Pelos balancando', 'global', 4.0)
fur_flutter(a, 1.4, 4.0, ['fur_top', 'fur_back'], axis=0)
fur_flutter(a, 1.8, 2.0, ['fur_cheek_R', 'fur_cheek_L'], axis=1)
fur_flutter(a, 1.0, 4.0, ['fur_chest_edge_R', 'fur_chest_edge_L'], axis=2)

a = Anim('Olhar em volta', 'global', 9.0)
look = curve([(0, 0), (2.0, 0), (2.15, -0.35), (3.6, -0.35), (3.75, 0), (5.6, 0), (5.75, 0.4), (7.0, 0.4),
              (7.2, 0), (9.0, 0)])
for s in 'RL':
    a.pos('iris_' + s, lambda t: (look(t), 0.0, 0.0))

# ============================================================ POSES (automatic, by player state)
a = Anim('Parado - cauda', 'standing', 3.2)
tail_wave(a, 3.0, 3.2, lag=0.1, grow=1.2)
tail_wave(a, 1.2, 1.6, lag=0.08, axis=0)

a = Anim('Andando', 'walking', 0.8)
tail_wave(a, 7.0, 0.8, lag=0.1, grow=1.18, lift=(-4, -2, -1, 0, 0))
tail_wave(a, 2.0, 0.4, lag=0.1, axis=0)
ears_fn(a, fn_back=lambda t: 3 * wave(0.4)(t))
fur_flutter(a, 1.6, 0.4, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L'], axis=0)
a.pos('fur_chest_rows', lambda t: (0.0, 0.05 * wave(0.4, 0.25)(t), 0.0))

a = Anim('Correndo', 'running', 0.5)
tail_pose(a, rx=(-22, -6, -8, -2, -4))                       # tail streams out behind
tail_wave(a, 5.0, 0.5, lag=0.12, grow=1.2)
tail_wave(a, 3.0, 0.25, lag=0.12, axis=0)
ears(a, back=28, out=6)
ears_fn(a, fn_back=lambda t: 3 * wave(0.25)(t))
fur_flutter(a, 3.0, 0.25, ['fur_top', 'fur_back'], axis=0, base=10)
fur_flutter(a, 3.0, 0.25, ['fur_cheek_R', 'fur_cheek_L'], axis=1)
fur_flutter(a, 2.0, 0.25, ['fur_chest_rows'], axis=0, base=-6)

a = Anim('Agachado - espreitando', 'sneaking', 2.4)
tail_pose(a, rx=(14, 2, -3, -3, -4))
tail_wave(a, 2.5, 2.4, lag=0.1)
a.rot('cauda_ponta', lambda t: (0.0, 6 * twitch([1.4], 0.3)(t), 0.0))
ears(a, back=-10, out=8, twist=-6)                           # focused forward, a bit low
eyes_open(a, c(0.8))
brows(a, lift=-0.08)

a = Anim('Agachado andando', 'sneak_walk', 1.2)
tail_pose(a, rx=(14, 2, -3, -3, -4))
tail_wave(a, 5.0, 1.2, lag=0.12, grow=1.2)
ears(a, back=-10, out=8, twist=-6)
ears_fn(a, fn_back=lambda t: 2 * wave(0.6)(t))
eyes_open(a, c(0.8))
brows(a, lift=-0.08)

a = Anim('Pulando', 'jumping', 0.6)
tail_pose(a, rx=(-18, -8, -6, -4, -6))
tail_wave(a, 2.0, 0.3, lag=0.12, axis=0)
ears(a, back=14)
fur_flutter(a, 2.5, 0.3, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L'], axis=0, base=4)

a = Anim('Caindo', 'falling', 0.3)
tail_pose(a, rx=(-34, -6, -8, -4, -6))
tail_wave(a, 4.0, 0.3, lag=0.15, grow=1.3)
ears(a, back=34, out=10)
ears_fn(a, fn_back=lambda t: 4 * wave(0.15)(t))
fur_flutter(a, 4.0, 0.15, FUR, axis=0, base=8)
eyes_open(a, c(1.0))
a.scl('olho_R', c((1.08, 1.12, 1.0))).scl('olho_L', c((1.08, 1.12, 1.0)))
brows(a, lift=0.15)

a = Anim('Nadando', 'swimming', 1.2)
tail_pose(a, rx=(-10, -9, -15, 1, -9))                       # tail straight behind, like a rudder
tail_wave(a, 7.0, 1.2, lag=0.15, grow=1.25)
ears(a, back=50, out=4)
fur_flutter(a, 2.0, 0.6, ['fur_top', 'fur_back'], axis=0, base=12)
fur_flutter(a, 2.0, 0.6, ['fur_chest_rows'], axis=0, base=-8)

a = Anim('Voando (elytra)', 'flying', 0.4)
tail_pose(a, rx=(-10, -9, -15, 1, -9))
tail_wave(a, 1.5, 0.4, lag=0.15, grow=1.3)
ears(a, back=60, out=2)
fur_flutter(a, 3.0, 0.2, FUR, axis=0, base=10)

a = Anim('Voo criativo', 'creative_flying', 2.0)
tail_pose(a, rx=(-12, -3, -3, 0, -2))
tail_wave(a, 4.0, 2.0, lag=0.12, grow=1.2)
ears(a, back=18)
fur_flutter(a, 1.5, 1.0, ['fur_top', 'fur_back'], axis=0, base=4)

a = Anim('Dormindo', 'sleeping', 4.0)
eyes_open(a, c(0.0))
ears(a, back=22, out=28)
tail_pose(a, rx=(-8, -6, -10, -6, -6), ry=(22, 30, 30, 32, 28))   # curled around the body
bth = wave(4.0, -0.25)
a.scl('fur_chest_rows', lambda t: (1.0, 1.0, 1 + 0.08 * (bth(t) + 1) / 2))
ears_fn(a, fn_twist=lambda t: 14 * twitch([2.6], 0.25)(t), side='R')
a.rot('cauda_ponta', lambda t: (0.0, 8 * twitch([3.3], 0.4)(t), 0.0))

a = Anim('Montado', 'riding', 3.0)
tail_pose(a, rx=(22, 6, 0, 0, 0))                            # hangs down relaxed
tail_wave(a, 3.0, 3.0, lag=0.1)
ears(a, back=-4)

a = Anim('Morrendo', 'dying', 1.0)
eyes_open(a, curve([(0, 1), (0.6, 0), (1, 0)]))
ears_fn(a, fn_back=curve([(0, 0), (1, 30)]), fn_out=curve([(0, 0), (1, 40)]))
tail_pose(a, rx=(30, 10, 8, 6, 6), fn=curve([(0, 0), (1, 1)]))

a = Anim('Machucado', 'hurt', 0.5)
ears(a, back=60, out=12)
eyes_open(a, c(0.45))
brows(a, lift=0.05, tilt=-14)
tail_pose(a, rx=(26, 8, 6, 4, 4))                            # tail tucked
puff(a, 1.12, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L'])
a.scl('cauda', c((1.12, 1.12, 1.0)))

a = Anim('Pegando fogo', 'on_fire', 0.3)
ears(a, back=45, out=8)
tail_wave(a, 16.0, 0.3, lag=0.12, grow=1.15, lift=(-10, -4, -2, 0, 0))
eyes_open(a, c(1.0))
a.scl('olho_R', c((1.1, 1.15, 1.0))).scl('olho_L', c((1.1, 1.15, 1.0)))
brows(a, lift=0.18, tilt=-10)
puff(a, 1.15, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'])

a = Anim('Congelando', 'freezing', 0.24)
ears(a, back=30, out=20)
tail_pose(a, rx=(6, -4, -6, -4, -4), ry=(18, 22, 24, 24, 20))
shiver = wave(0.12)
for b in ['orelha_R_mov', 'orelha_L_mov'] + FUR + TAIL:
    a.rot(b, lambda t: (0.0, 0.0, 1.5 * shiver(t)))
eyes_open(a, c(0.6))
brows(a, tilt=-10)
puff(a, 1.1, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'])

for s in ('left', 'right'):
    a = Anim('Comendo (%s)' % ('esquerda' if s == 'left' else 'direita'), 'eating_' + s, 0.4)
    chew = lambda t: (math.sin(2 * math.pi * t / 0.4) + 1) / 2
    a.rot('mandibula', lambda t: (-12 * chew(t), 0.0, 0.0))
    a.pos('nariz', lambda t: (0.0, 0.05 * chew(t), 0.0))
    a.scl('bochechas', lambda t: (1 + 0.06 * chew(t), 1 + 0.03 * chew(t), 1.0))
    eyes_open(a, c(0.7))
    ears(a, back=10, out=6)
    tail_wave(a, 6.0, 0.4, lag=0.1)

a = Anim('Rastejando', 'crawling', 1.0)
tail_pose(a, rx=(-12, -8, -12, 0, -6))
tail_wave(a, 5.0, 1.0, lag=0.12)
ears(a, back=30)

a = Anim('Na escada', 'on_ladder', 2.0)
tail_pose(a, rx=(28, 8, 0, 0, 0))
tail_wave(a, 2.0, 2.0)
ears(a, back=6)

a = Anim('Subindo escada', 'climbing_on_ladder', 0.6)
tail_pose(a, rx=(28, 8, 0, 0, 0))
tail_wave(a, 6.0, 0.6, lag=0.12)
ears_fn(a, fn_back=lambda t: 3 * wave(0.3)(t))

a = Anim('No inventario', 'in_gui', 0.6)
tail_wave(a, 16.0, 0.6, lag=0.12, grow=1.12, lift=(-10, -4, 0, 0, 0))
ears(a, back=-6, twist=-8)
eyes_open(a, c(0.8))
brows(a, lift=0.1)

for s, other in (('left', 'R'), ('right', 'L')):
    pt = 'esquerda' if s == 'left' else 'direita'
    a = Anim('Mirando arco (%s)' % pt, 'bow_' + s, 1.0)          # value = how far the bow is drawn
    ears_fn(a, fn_back=curve([(0, 0), (1, -12)]), fn_twist=curve([(0, 0), (1, -10)]))
    eyes_open(a, curve([(0, 1), (1, 0.15)]), side=other)
    tail_pose(a, rx=(-6, -2, 0, 0, 0), fn=curve([(0, 0), (1, 1)]))
    brows(a, lift=-0.08, tilt=6, fn=curve([(0, 0), (1, 1)]))

    a = Anim('Luneta (%s)' % pt, 'spyglass_' + s, 1.0)
    eyes_open(a, c(0.1), side=other)
    ears(a, back=-12, twist=-8)
    brows(a, lift=0.06)

    a = Anim('Bloqueando (%s)' % pt, 'blocking_' + s, 1.0)
    ears(a, back=26, out=6)
    brows(a, lift=-0.1, tilt=14)
    eyes_open(a, c(0.75))
    tail_pose(a, rx=(12, 4, 0, 0, 0))
    a.scl('cauda', c((1.1, 1.1, 1.0)))

    a = Anim('Atacando (%s)' % pt, 'punch_' + s, 1.0)            # value = swing progress
    k = -1 if s == 'right' else 1
    flick = curve([(0, 0), (0.25, 1), (1, 0)])
    for i, b in enumerate(TAIL):
        a.rot(b, lambda t, i=i: (0.0, k * (6 + 3 * i) * flick(t), 0.0))
    ears_fn(a, fn_back=lambda t: 20 * flick(t))
    brows(a, lift=-0.08, tilt=10, fn=flick)

# value-driven poses (duration = the value 0..1)
a = Anim('Falando', 'speaking', 1.0)
a.rot('mandibula', curve([(0, (0, 0, 0)), (1, (-16, 0, 0))]))
a.pos('nariz', curve([(0, (0, 0, 0)), (1, (0, 0.06, 0))]))
ears_fn(a, fn_back=curve([(0, 0), (1, -5)]))

a = Anim('Vida', 'health', 1.0)                                # 0 = almost dead, 1 = full health
low = curve([(0, 1), (0.35, 0.6), (0.6, 0), (1, 0)])
ears_fn(a, fn_back=lambda t: 30 * low(t), fn_out=lambda t: 32 * low(t))
tail_pose(a, rx=(24, 8, 6, 4, 4), fn=low)
brows(a, tilt=-12, fn=low)
eyes_open(a, lambda t: 1 - 0.35 * low(t))

a = Anim('Virando a cabeca', 'head_rotation_yaw', 1.0)        # 0 / 1 = head turned to each side
yaw = curve([(0, -1), (0.5, 0), (1, 1)], ease=lambda x: x)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.42 * yaw(t), 0.0, 0.0))
ears_fn(a, fn_twist=lambda t: 8 * yaw(t), side='L')
ears_fn(a, fn_twist=lambda t: -8 * yaw(t), side='R')
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (0.0, -(2 + i) * yaw(t), 0.0))       # tail balances the other way

a = Anim('Olhando cima/baixo', 'head_rotation_pitch', 1.0)     # 0 = looking up, 1 = looking down
pit = curve([(0, -1), (0.5, 0), (1, 1)], ease=lambda x: x)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.22 * pit(t), 0.0))
ears_fn(a, fn_back=lambda t: -10 * pit(t))
brows(a, lift=0.06, fn=lambda t: -pit(t))

# armour / helmet: tuck away what would poke through
HIDE = lambda t: (0.02, 0.02, 0.02)
a = Anim('Com capacete', 'armor_head', 1.0)
for b in ('fur_top', 'fur_back', 'orelhas'):
    a.scl(b, HIDE)
a = Anim('Com peitoral', 'armor_body', 1.0)
for b in ('fur_chest', 'fur_cauda_raiz'):
    a.scl(b, HIDE)
a = Anim('Com calca', 'armor_legs', 1.0)
a.scl('fur_cauda_raiz', HIDE)
a = Anim('Com cabeca de mob', 'wearing_skull', 1.0)
for b in ('fur_top', 'fur_back', 'orelhas'):
    a.scl(b, HIDE)

# ============================================================ GESTURES (CPM gesture wheel)
a = Anim('Abanar a cauda', 'gesture', 0.5)
tail_wave(a, 16.0, 0.5, lag=0.13, grow=1.12, lift=(-14, -5, -2, 0, 0))
ears(a, back=-6, twist=-6)
eyes_open(a, c(0.8))
brows(a, lift=0.08)

a = Anim('Feliz', 'gesture', 1.2)
eyes_open(a, c(0.3))                                          # ^ ^
brows(a, lift=0.16, tilt=-6)
ears(a, back=-8, twist=-6)
tail_wave(a, 14.0, 0.6, lag=0.12, grow=1.12, lift=(-12, -4, -2, 0, 0))
a.scl('bochechas', c((1.06, 1.04, 1.0)))
a.rot('mandibula', c((-5.0, 0.0, 0.0)))
puff(a, 1.05, ['fur_cheek_R', 'fur_cheek_L'])

a = Anim('Bravo', 'gesture', 1.6)
brows(a, lift=-0.1, tilt=18)
eyes_open(a, c(0.7))
ears(a, back=45, out=14)
tail_pose(a, rx=(-10, -2, 0, 0, 0))
a.scl('cauda', c((1.16, 1.16, 1.0)))                          # bristled tail
trem = wave(0.08)
for b in TAIL + ['fur_top', 'fur_back']:
    a.rot(b, lambda t: (0.0, 0.0, 0.8 * trem(t)))
puff(a, 1.12, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'])
a.rot('mandibula', lambda t: (-5 - 1.5 * wave(0.8)(t), 0.0, 0.0))  # snarl
a.pos('nariz', c((0.0, 0.07, 0.0)))

a = Anim('Triste', 'gesture', 3.0)
brows(a, lift=0.06, tilt=-16)
eyes_open(a, c(0.65))
ears(a, back=26, out=36)
tail_pose(a, rx=(24, 8, 6, 4, 4))
tail_wave(a, 1.5, 3.0)
a.rot('cauda_ponta', lambda t: (0.0, 5 * twitch([1.8], 0.6)(t), 0.0))

a = Anim('Surpreso', 'gesture', 1.6, loop='once')
env = curve([(0, 0), (0.12, 1), (1.1, 1), (1.6, 0)])
a.scl('olho_R', lambda t: (1 + 0.1 * env(t), 1 + 0.18 * env(t), 1.0))
a.scl('olho_L', lambda t: (1 + 0.1 * env(t), 1 + 0.18 * env(t), 1.0))
brows(a, lift=0.28, fn=env)
ears_fn(a, fn_back=lambda t: -12 * env(t), fn_twist=lambda t: -10 * env(t))
tail_pose(a, rx=(-26, -8, -4, 0, 0), fn=env)
a.scl('cauda', lambda t: (1 + 0.2 * env(t), 1 + 0.2 * env(t), 1.0))
puff(a, 1.15, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'], fn=env)

a = Anim('Farejar', 'gesture', 2.0, loop='once')
env = curve([(0, 0), (0.2, 1), (1.7, 1), (2.0, 0)])
sn = twitch([0.3, 0.45, 0.6, 0.9, 1.05, 1.2, 1.45], 0.13)
a.pos('nariz', lambda t: (0.0, 0.08 * sn(t), -0.05 * sn(t)))
a.scl('nariz', lambda t: (1 + 0.1 * sn(t), 1 + 0.06 * sn(t), 1.0))
a.rot('focinho', lambda t: (-2 * sn(t), 0.0, 0.0))
a.scl('bochechas', lambda t: (1 + 0.04 * sn(t), 1.0, 1.0))
ears_fn(a, fn_back=lambda t: -12 * env(t), fn_twist=lambda t: -8 * env(t))
eyes_open(a, lambda t: 1 - 0.2 * env(t))
brows(a, lift=0.08, fn=env)
a.rot('cauda_ponta', lambda t: (0.0, 6 * twitch([1.3], 0.4)(t), 0.0))

a = Anim('Bocejar', 'gesture', 2.6, loop='once')
jaw = curve([(0, 0), (0.35, 0), (0.9, 1), (1.7, 1), (2.1, 0), (2.6, 0)])
a.rot('mandibula', lambda t: (-30 * jaw(t), 0.0, 0.0))
a.pos('nariz', lambda t: (0.0, 0.08 * jaw(t), 0.0))
eyes_open(a, curve([(0, 1), (0.4, 0.1), (2.2, 0.1), (2.5, 1)]))
brows(a, lift=0.14, tilt=-8, fn=jaw)
ears_fn(a, fn_back=lambda t: 30 * jaw(t), fn_out=lambda t: 16 * jaw(t))
tail_pose(a, rx=(-10, -6, -4, 0, 0), fn=jaw)                  # little stretch of the tail
a.scl('bochechas', lambda t: (1 + 0.05 * jaw(t), 1.0, 1.0))

a = Anim('Piscadela', 'gesture', 0.8, loop='once')
wk = curve([(0, 1), (0.12, 0), (0.45, 0), (0.62, 1), (0.8, 1)])
eyes_open(a, wk, side='R')
a.rot('palp_R', lambda t: (0.0, 0.0, 8 * (1 - wk(t))))
ears_fn(a, fn_twist=lambda t: 14 * twitch([0.15], 0.3)(t), side='R')
a.rot('mandibula', lambda t: (-4 * (1 - wk(t)), 0.0, 0.0))

a = Anim('Sacudir o pelo', 'gesture', 1.2, loop='once')
dec = lambda t: max(0.0, 1 - t / 1.1)
sh = wave(0.16)
for b in FUR:
    a.rot(b, lambda t: (0.0, 0.0, 9 * sh(t) * dec(t)))
puff(a, 1.12, FUR, fn=lambda t: dec(t))
ears_fn(a, fn_back=lambda t: 25 * abs(sh(t)) * dec(t), fn_out=lambda t: 20 * sh(t) * dec(t))
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (0.0, (8 + 3 * i) * wave(0.16, -0.1 * i)(t) * dec(t), 0.0))
eyes_open(a, curve([(0, 1), (0.08, 0), (0.9, 0), (1.1, 1), (1.2, 1)]))

# ============================================================ LAYERS (toggles)
a = Anim('Orelhas para tras', 'layer', 1.0)
ears(a, back=55, out=10)

a = Anim('Orelhas atentas', 'layer', 1.0)
ears(a, back=-12, twist=-12)
a.scl('orelha_R_mov', c((1.0, 1.08, 1.0))).scl('orelha_L_mov', c((1.0, 1.08, 1.0)))

a = Anim('Cauda enrolada', 'layer', 1.0)
tail_pose(a, rx=(-6, -4, -8, -4, -4), ry=(20, 26, 28, 28, 24))

a = Anim('Cauda erguida', 'layer', 1.0)
tail_pose(a, rx=(-38, -8, -12, 0, -6))

# ============================================================ save
d['animations'] = [x.to_json() for x in ANIMS]
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_18_128.png'
d['name'] = 'skin_v16.18_animado'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok: %d animations, %d keyframes' % (len(ANIMS), sum(len(v['keyframes']) for x in d['animations']
                                                           for v in x['animators'].values())))
