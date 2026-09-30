"""v16.24 (from v16.23): toggles + emotes. Everything from v16.23 is kept as is.
  - toggles (CPM layers): "Esconder orelhas", "Esconder cauda"
  - continuous emotes (CPM custom poses: loop until the player moves, with enter/leave transitions):
    Descansar, Parecer serio, Deitar e olhar o ceu, Flexoes
  - one-shot emotes (CPM gestures, eased in and out): Alerta de emergencia, Mapa 3D, Holograma de missao,
    Investigar, Saudacao, Pensativo, Comemoracao, Dar de ombros
  - emote props, hidden while unused: bracelet inside the left forearm, holograms (3D map, mission panel,
    alert signal, confirmation) inside the body - translucent, glowing, pulled out by the emotes

usage: python3 tools/v16_24_emotes.py <in.bbmodel> <out.bbmodel>
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
GRP_BY_UUID = lambda u: next(g for g in d['groups'] if g['uuid'] == u)


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


cen = lambda e: [(e['from'][i] + e['to'][i]) / 2 for i in range(3)]
for name, parent, kids, pivot in (          # wrappers from v16.18 (only created if missing)
        ('iris_R', 'olhos', ['eye_R_iris'], cen(ELS['eye_R_iris'])),
        ('iris_L', 'olhos', ['eye_L_iris'], cen(ELS['eye_L_iris'])),
        ('palp_R', 'palpebras', ['palpebra_R'], [cen(ELS['palpebra_R'])[0], ELS['palpebra_R']['to'][1], -4.05]),
        ('palp_L', 'palpebras', ['palpebra_L'], [cen(ELS['palpebra_L'])[0], ELS['palpebra_L']['to'][1], -4.05]),
        ('nariz', 'focinho', ['nose'], [0, ELS['nose']['from'][1], ELS['nose']['to'][2]]),
        ('orelha_L_mov', 'orelhas', ['orelha_L'], GRP['orelha_L']['origin']),
        ('orelha_R_mov', 'orelhas', ['orelha_R'], GRP['orelha_R']['origin'])):
    if name not in GRP:
        wrap(name, parent, kids, pivot)


def unwrap(name):
    """Remove a (zero-rotation) wrapper bone, putting its children back where it was."""
    if name not in GRP:
        return
    g = GRP.pop(name)
    def walk(nodes):
        for i, n in enumerate(nodes):
            if isinstance(n, dict):
                if n['uuid'] == g['uuid']:
                    nodes[i:i + 1] = n['children']
                    return True
                if walk(n['children']):
                    return True
    walk(d['outliner'])
    d['groups'].remove(g)


unwrap('mandibula')

tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
T = tex.load()

# ------------------------------------------------ new eyelids (hidden inside the head while open)
OCC = np.array(tex)[:, :, 3] > 0
for e in d['elements']:
    for fc in e['faces'].values():
        x0, y0, x1, y1 = fc['uv']
        OCC[int(min(y0, y1)):int(math.ceil(max(y0, y1))), int(min(x0, x1)):int(math.ceil(max(x0, x1)))] = True
OCC[127, 127] = True


def put(rows):
    h, w = len(rows), len(rows[0])
    for y in range(128 - h + 1):
        for x in range(128 - w + 1):
            if not OCC[y:y + h, x:x + w].any():
                OCC[y:y + h, x:x + w] = True
                for j, row in enumerate(rows):
                    for i, c in enumerate(row):
                        T[x + i, y + j] = c
                return [x, y, x + w, y + h]
    raise RuntimeError('texture full')


FURC, LASH = (25, 24, 24, 255), (71, 71, 71, 255)     # face fur around the eyes / grey lash line
M, L = FURC, LASH
if 'palp_sup_R' not in GRP:                             # only when the lids still have to be made
    UP_FRONT = put([[M] * 6, [M] * 6, [L, M, M, M, M, L], [M, L, L, L, L, M]])   # closed-eye curve
    LO_FRONT = put([[M] * 6, [M] * 6])
    SIDE4, SIDE2 = put([[M]] * 4), put([[M]] * 2)
    EDGE = put([[M] * 6])
BLANK = {'uv': [127, 127, 128, 128], 'texture': 0}
EYE_TOP, EYE_MID, EYE_BOT = 27.95, 27.0, 26.42          # painted eye: y 26.5..28.5, lid band covers the top
Z_IN = (-3.99, -3.96)                                   # just behind the face -> invisible while open


def lid(name, x0, x1, y0, y1, side_uv, front_uv):
    return {
        'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
        'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
        'from': [x0, y0, Z_IN[0]], 'to': [x1, y1, Z_IN[1]], 'autouv': 0, 'color': 2, 'rotation': [0, 0, 0],
        'origin': [(x0 + x1) / 2, (y0 + y1) / 2, sum(Z_IN) / 2],
        'faces': {'north': {'uv': front_uv, 'texture': 0}, 'south': copy.deepcopy(BLANK),
                  'east': {'uv': side_uv, 'texture': 0}, 'west': {'uv': side_uv, 'texture': 0},
                  'up': {'uv': EDGE, 'texture': 0}, 'down': {'uv': EDGE, 'texture': 0}},
        'type': 'cube', 'uuid': str(uuid.uuid4()),
    }


def new_bone(name, parent, pivot, element):
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=[round(v, 4) for v in pivot], rotation=[0, 0, 0])
    d['groups'].append(g)
    GRP[name] = g
    d['elements'].append(element)
    ELS[element['name']] = element
    find_node(d['outliner'], GRP[parent]['uuid'])['children'].append(
        {'uuid': g['uuid'], 'isOpen': False, 'children': [element['uuid']]})


for s, (x0, x1) in (('R', (1.45, 3.05)), ('L', (-3.05, -1.45))):
    if 'palp_sup_' + s in GRP:
        continue
    cx, cz = (x0 + x1) / 2, sum(Z_IN) / 2
    new_bone('palp_sup_' + s, 'palpebras', (cx, EYE_TOP, cz),                      # pivot = top edge
             lid('palpebra_sup_' + s, x0, x1, EYE_MID, EYE_TOP, SIDE4, UP_FRONT))
    new_bone('palp_inf_' + s, 'palpebras', (cx, EYE_BOT, cz),                      # pivot = bottom edge
             lid('palpebra_inf_' + s, x0, x1, EYE_BOT, EYE_MID, SIDE2, LO_FRONT))

# lids deeper inside the head (0.1 behind the face instead of 0.01 -> no depth fight)
LID_Z = (-3.90, -3.87)
for s_ in 'RL':
    for part in ('sup', 'inf'):
        e = ELS['palpebra_%s_%s' % (part, s_)]
        e['from'][2], e['to'][2] = LID_Z
        e['origin'][2] = sum(LID_Z) / 2

# fur-coloured cover over the top of the painted eye, just in front of the face and behind the iris front
# and the grey band: hidden at rest, it keeps a tilted band from uncovering the black eye above it
if 'cobre_olho_R' not in ELS:
    if 'OCC' not in globals():
        OCC = np.array(tex)[:, :, 3] > 0
        for e in d['elements']:
            for fc in e['faces'].values():
                x0, y0, x1, y1 = fc['uv']
                OCC[int(min(y0, y1)):int(math.ceil(max(y0, y1))), int(min(x0, x1)):int(math.ceil(max(x0, x1)))] = True
        OCC[127, 127] = True
    cover_uv = put([[(25, 24, 24, 255)] * 6] * 2)
    for s_, (x0, x1) in (('R', (1.45, 3.05)), ('L', (-3.05, -1.45))):
        e = {'name': 'cobre_olho_' + s_, 'box_uv': False, 'render_order': 'default', 'locked': False,
             'export': True, 'scope': 0, 'allow_mirror_modeling': True, 'cpm_glow': False, 'cpm_recolor': -1,
             'cpm_extrude': False, 'cpm_data': '', 'from': [x0, 28.1, -4.035], 'to': [x1, 28.53, -4.035],
             'autouv': 0, 'color': 2, 'rotation': [0, 0, 0], 'origin': [(x0 + x1) / 2, 28.315, -4.035],
             'faces': {'north': {'uv': cover_uv, 'texture': 0},
                       **{f: {'uv': [0, 0, 0, 0], 'texture': None} for f in ('south', 'east', 'west', 'up', 'down')}},
             'type': 'cube', 'uuid': str(uuid.uuid4())}
        d['elements'].append(e)
        ELS[e['name']] = e
        find_node(d['outliner'], GRP['palpebras']['uuid'])['children'].append(e['uuid'])

# ------------------------------------------------ emote props (hidden inside the body / arm at rest)
# holograms: translucent glowing cyan planes kept inside the body; the emotes move them out in front
# of the chest and scale them up. The bracelet sits inside the left forearm and is scaled up so it
# appears around the wrist. Nothing of this is visible when no emote is playing.
HC1, HC2, HC3, HCD = (120, 235, 255, 210), (60, 170, 230, 170), (210, 250, 255, 235), (40, 120, 170, 110)
HR, HG = (255, 90, 90, 235), (120, 255, 150, 235)
MET, MET2, LED = (52, 52, 54, 255), (36, 36, 37, 255), (100, 230, 255, 255)


def prop_el(name, f, t, faces, glow=True):
    full = {k: {'uv': [0, 0, 0, 0], 'texture': None} for k in ('north', 'south', 'east', 'west', 'up', 'down')}
    for k, uvr in faces.items():
        full[k] = {'uv': uvr, 'texture': 0}
    e = {'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True, 'scope': 0,
         'allow_mirror_modeling': True, 'cpm_glow': glow, 'cpm_recolor': -1, 'cpm_extrude': False, 'cpm_data': '',
         'from': list(f), 'to': list(t), 'autouv': 0, 'color': 5, 'rotation': [0, 0, 0],
         'origin': [(f[i] + t[i]) / 2 for i in range(3)], 'faces': full, 'type': 'cube', 'uuid': str(uuid.uuid4())}
    d['elements'].append(e)
    ELS[name] = e
    return e['uuid']


def prop_group(name, parent, pivot, kids):
    g = copy.deepcopy(TEMPLATE)
    g.update(name=name, uuid=str(uuid.uuid4()), origin=list(pivot), rotation=[0, 0, 0])
    d['groups'].append(g)
    GRP[name] = g
    node = {'uuid': g['uuid'], 'isOpen': False, 'children': kids}
    find_node(d['outliner'], GRP[parent]['uuid'])['children'].append(node)
    return node


if 'holo' not in GRP:
    grid = put([[HC1 if (x in (0, 7) or y in (0, 7)) else (HC2 if (x % 2 == 0 or y % 2 == 0) else HCD)
                 for x in range(8)] for y in range(8)])
    relief = put([[HC3, HC1], [HC1, HC2]])
    panel = put([[HC1] * 8,
                 [HC1, HC3, HC3, HCD, HC3, HC3, HC3, HC1],
                 [HC1, HCD, HCD, HCD, HCD, HCD, HCD, HC1],
                 [HC1, HC3, HC3, HC3, HCD, HC2, HC2, HC1],
                 [HC1] * 8])
    card = put([[HC3, HC3, HC3], [HC1, HC2, HC1]])
    sinal = put([[HC1, HC2, HC2, HC2, HC1],
                 [HC2, HCD, HR, HCD, HC2],
                 [HC2, HR, HR, HR, HC2],
                 [HC2, HCD, HR, HCD, HC2],
                 [HC1, HC2, HC2, HC2, HC1]])
    ok = put([[HCD, HCD, HG], [HG, HCD, HG], [HCD, HG, HCD]])
    b_side = put([[MET2] * 8, [MET, LED, MET, MET, LED, MET, MET, LED], [MET2] * 8])
    b_cap = put([[MET2, MET], [MET, MET2]])

    CZ = (-0.06, 0.06)                          # holograms are 0.12 thick (two faces, never coplanar)
    holo = prop_group('holo', 'body', (0, 18, 0), [])
    prop_group('holo_mapa', 'holo', (0, 18, 0), [
        prop_el('holo_mapa_base', (-1.8, 17.94, -1.8), (1.8, 18.06, 1.8), {'up': grid, 'down': grid}),
        prop_el('holo_mapa_relevo_1', (-1.2, 18.06, -0.9), (-0.4, 18.9, -0.1),
                {k: relief for k in ('north', 'south', 'east', 'west', 'up')}),
        prop_el('holo_mapa_relevo_2', (0.2, 18.06, 0.2), (1.0, 19.3, 1.0),
                {k: relief for k in ('north', 'south', 'east', 'west', 'up')}),
        prop_el('holo_mapa_relevo_3', (-0.6, 18.06, 0.6), (0.0, 18.6, 1.2),
                {k: relief for k in ('north', 'south', 'east', 'west', 'up')})])
    prop_group('holo_painel', 'holo', (0, 18, 0), [
        prop_el('holo_painel_tela', (-1.8, 16.8, CZ[0]), (1.8, 19.2, CZ[1]), {'north': panel, 'south': panel})])
    prop_group('holo_card', 'holo_painel', (0, 18, 0), [
        prop_el('holo_painel_card', (-0.7, 17.2, -0.26), (0.7, 18.0, -0.14), {'north': card, 'south': card})])
    prop_group('holo_sinal', 'holo', (0, 18, 0), [
        prop_el('holo_sinal_radar', (-1.2, 16.8, CZ[0]), (1.2, 19.2, CZ[1]), {'north': sinal, 'south': sinal})])
    prop_group('holo_ok', 'holo', (0, 18, 0), [
        prop_el('holo_ok_check', (-0.6, 17.4, CZ[0]), (0.6, 18.6, CZ[1]), {'north': ok, 'south': ok})])
    prop_group('bracelete', 'left_arm', (-6, 14.2, 0), [
        prop_el('bracelete_aro', (-7.85, 13.6, -1.85), (-4.15, 14.8, 1.85),
                {'north': b_side, 'south': b_side, 'east': b_side, 'west': b_side, 'up': b_cap, 'down': b_cap})])

# glowing, bright iris (already so in v16.18 - kept)
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


# ============================================================ per-tuft bones (lift around the root)
FUR = ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows', 'fur_chest_edge_R', 'fur_chest_edge_L']
UUID2EL = {e['uuid']: e for e in d['elements']}
TUFTS = {}          # fur group -> [tuft bone names]
LIFT_AXIS = {}      # tuft bone -> (axis in the parent frame, parent rotation matrix)


def axis_angle(axis, deg):
    x, y, z = axis
    c, s_, C = math.cos(math.radians(deg)), math.sin(math.radians(deg)), 1 - math.cos(math.radians(deg))
    return np.array([[c + x * x * C, x * y * C - z * s_, x * z * C + y * s_],
                     [y * x * C + z * s_, c + y * y * C, y * z * C - x * s_],
                     [z * x * C - y * s_, z * y * C + x * s_, c + z * z * C]])


for g in FUR:
    node = find_node(d['outliner'], GRP[g]['uuid'])
    P = rotmat(GRP[g]['rotation'])
    TUFTS[g] = []
    for child in list(node['children']):
        if isinstance(child, dict):                 # already wrapped (re-run)
            name = GRP_BY_UUID(child['uuid'])['name']
            e = UUID2EL[child['children'][0]]
        else:
            e = UUID2EL[child]
            name = 'mov_' + e['name']
            wrap(name, g, [e['name']], e['origin'])
        TUFTS[g].append(name)
        R = P @ rotmat(e.get('rotation', [0, 0, 0]))           # tuft orientation in the model
        r, up, face = R[:, 0], R[:, 1], -R[:, 2]                # width axis, root->tip, outer side
        sgn = 1.0 if np.dot(np.cross(r, up), face) > 0 else -1.0
        LIFT_AXIS[name] = (sgn * r, P)


def lift_euler(bone, deg):
    """Rotation of a tuft around its own root that lifts its tip `deg` degrees away from the skin
    (negative = lays it down towards the skin), expressed in the tuft bone's frame."""
    ax, P = LIFT_AXIS[bone]
    return euler_zyx(P.T @ axis_angle(ax / np.linalg.norm(ax), deg) @ P)


# ============================================================ animation builder
TAIL = ['cauda', 'cauda_1', 'cauda_2', 'cauda_3', 'cauda_ponta']
ANIMS = []


class Anim:
    def __init__(self, name, cpm_type, length, loop='loop', layer_default=0, additive=True, priority=0):
        self.name, self.type, self.length, self.loop = name, cpm_type, length, loop
        self.tracks = {}          # bone -> channel -> list of functions (summed / multiplied)
        self.layer_default = layer_default
        self.additive, self.priority, self._lids = additive, priority, None
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

    def lids(self):
        """Separate NON-additive animation that alone drives the eyelids for this state (see header)."""
        if self._lids is None:
            prio = LID_PRIORITY.get(self.type, 20)
            self._lids = Anim(self.name + ' - olhos', self.type, self.length, self.loop, additive=False,
                              priority=prio)
        return self._lids

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
                    # keyframe = delta as it should look: the CPM exporter flips X/Y of the keyframe
                    # exactly like it flips X/Y of the group rotation, so no extra sign change here
                    kfs.append({'channel': ch, 'data_points': [{'x': round(v[0], 3), 'y': round(v[1], 3),
                                                                 'z': round(v[2], 3)}],
                                'uuid': str(uuid.uuid4()), 'time': round(t, 4), 'color': -1,
                                'interpolation': 'linear'})
            animators[GRP[bone]['uuid']] = {'name': bone, 'type': 'bone', 'keyframes': kfs}
        return {
            'uuid': str(uuid.uuid4()), 'name': self.name, 'loop': self.loop, 'override': False,
            'length': self.length, 'snapping': FPS, 'selected': False, 'anim_time_update': '',
            'blend_weight': '', 'start_delay': '', 'loop_delay': '', 'animators': animators,
            'cpm_type': self.type, 'cpm_additive': self.additive, 'cpm_layerCtrl': True, 'cpm_commandCtrl': False,
            'cpm_priority': self.priority, 'cpm_order': len([a for a in ANIMS[:ANIMS.index(self)] if a.type == self.type]),
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


LID_FWD = 0.21      # from inside the head (0.1 deep) to just in front of the iris (behind the grey band)
LID_PRIORITY = {'global': 0, 'sleeping': 40, 'dying': 40, 'bow_left': 30, 'bow_right': 30,
                'spyglass_left': 30, 'spyglass_right': 30}


def eyes_open(a, fn, side='RL'):
    """fn(t) = how open the eye is (1 open, 0 shut). The upper lid grows down from the grey band and the
    lower lid grows up; they meet on the eye line when shut. While open they stay hidden in the head."""
    cov = lambda t: 1 - fn(t)
    show = lambda t: min(1.0, cov(t) * 25)
    L_ = a.lids()
    for s in side:
        # upper lid does the squinting; the lower lid only comes up for a real (almost) closed eye
        L_.scl('palp_sup_' + s, lambda t: (1.0, max(0.04, cov(t)), 1.0))
        L_.scl('palp_inf_' + s, lambda t: (1.0, max(0.04, (cov(t) - 0.4) / 0.6), 1.0))
        for part in ('sup', 'inf'):
            L_.pos('palp_%s_%s' % (part, s), lambda t: (0.0, 0.0, -LID_FWD * show(t)))
        a.pos('palp_' + s, lambda t: (0.0, -0.16 * cov(t), 0.0))       # band comes down onto the shut lid


def brows(a, lift=0.0, tilt=0.0, fn=None):
    """Expression with the lids (the model has no separate brows): lift = up/down,
    tilt > 0 = inner ends down (angry), < 0 = inner ends up (sad)."""
    f = fn or (lambda t: 1.0)
    a.pos('palp_R', lambda t: (0.0, lift * f(t), 0.0)).rot('palp_R', lambda t: (0.0, 0.0, tilt * f(t)))
    a.pos('palp_L', lambda t: (0.0, lift * f(t), 0.0)).rot('palp_L', lambda t: (0.0, 0.0, -tilt * f(t)))


LIFT_MIN, LIFT_MAX = 0.0, 22.0      # tufts only lift from their rest pose and settle back: never into the body


def fur_lift(a, groups, fn):
    """fn(t, i) -> lift in degrees for the i-th tuft; clamped so a tuft never goes into the body."""
    i = 0
    for g in groups:
        for b in TUFTS[g]:
            a.rot(b, (lambda b, i: lambda t: lift_euler(b, max(LIFT_MIN, min(LIFT_MAX, fn(t, i)))))(b, i))
            i += 1


def fur_flutter(a, amp, period, bones=FUR, axis=0, base=0.0):
    """Fur moving in the air: each tuft lifts/settles around its own root, a bit out of phase."""
    fur_lift(a, bones, lambda t, i: abs(base) + amp * (1 + math.sin(2 * math.pi * (t / period + i * 0.23))) / 2)


def puff(a, k, bones, fn=None):
    """Bristling. Fur groups: tufts stand up around their roots (no scaling -> they stay on the skin).
    Other bones (the tail) are still scaled."""
    f = fn or (lambda t: 1.0)
    fur = [b for b in bones if b in TUFTS]
    if fur:
        fur_lift(a, fur, lambda t, i: 70 * (k - 1) * f(t))
    for b in bones:
        if b not in TUFTS:
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
fur_lift(a, ['fur_chest_rows', 'fur_chest_edge_R', 'fur_chest_edge_L'], lambda t, i: 3.0 * (br(t) + 1) / 2)
a.scl('bochechas', lambda t: (1 + 0.015 * (br(t) + 1) / 2, 1.0, 1 + 0.015 * (br(t) + 1) / 2))

a = Anim('Orelhas vivas', 'global', 7.0)
tw_L, tw_R, both = twitch([1.5], 0.28), twitch([4.2, 4.55], 0.24), twitch([6.1], 0.35)
sway = wave(7.0 / 2)
ears_fn(a, fn_back=lambda t: 1.2 * sway(t) + 8 * tw_L(t) + 6 * both(t), fn_twist=lambda t: 16 * tw_L(t), side='L')
ears_fn(a, fn_back=lambda t: -1.2 * sway(t) + 8 * tw_R(t) + 6 * both(t), fn_twist=lambda t: 16 * tw_R(t), side='R')

a = Anim('Focinho farejando', 'global', 5.0)
sn = twitch([1.0, 1.16, 3.7], 0.12)                           # small, quick and rare
a.pos('nariz', lambda t: (0.0, 0.02 * sn(t), -0.01 * sn(t)))
a.scl('nariz', lambda t: (1 + 0.025 * sn(t), 1 + 0.015 * sn(t), 1.0))
a.rot('focinho', lambda t: (-0.4 * sn(t), 0.0, 0.0))

a = Anim('Pelos balancando', 'global', 4.0)
fur_flutter(a, 1.5, 4.0, ['fur_top', 'fur_back'])
fur_flutter(a, 2.0, 2.0, ['fur_cheek_R', 'fur_cheek_L'])
fur_flutter(a, 1.2, 4.0, ['fur_chest_edge_R', 'fur_chest_edge_L'])

a = Anim('Olhar em volta', 'global', 9.0)
look = curve([(0, 0), (2.0, 0), (2.15, -0.15), (3.6, -0.15), (3.75, 0), (5.6, 0), (5.75, 0.15), (7.0, 0.15),
              (7.2, 0), (9.0, 0)])                              # small: added to the head-follow below
for s in 'RL':
    a.pos('iris_' + s, lambda t: (look(t), 0.0, 0.0))

BAND_UP = 0.14      # grey lid band rests a little higher -> more eye shows, friendlier face

a = Anim('Expressao', 'global', 10.0)
raise_ = curve([(0, 0), (2.6, 0), (2.8, 1), (3.3, 1), (3.6, 0), (7.2, 0), (7.35, 0.7), (7.9, 0.7), (8.2, 0), (10, 0)])
curious = curve([(0, 0), (5.0, 0), (5.2, 1), (5.9, 1), (6.2, 0), (10, 0)])
a.pos('palp_R', lambda t: (0.0, BAND_UP + 0.1 * raise_(t) + 0.1 * curious(t), 0.0))   # one brow up = curious
a.pos('palp_L', lambda t: (0.0, BAND_UP + 0.1 * raise_(t), 0.0))
a.rot('palp_R', lambda t: (0.0, 0.0, -5 * curious(t)))
a.rot('palp_L', lambda t: (0.0, 0.0, 2 * raise_(t)))
ears_fn(a, fn_back=lambda t: -4 * raise_(t), side='RL')
ears_fn(a, fn_twist=lambda t: -8 * curious(t), side='R')

# ============================================================ POSES (automatic, by player state)
a = Anim('Parado - cauda', 'standing', 3.2)
tail_wave(a, 3.0, 3.2, lag=0.1, grow=1.2)
tail_wave(a, 1.2, 1.6, lag=0.08, axis=0)

a = Anim('Andando', 'walking', 0.8)
tail_wave(a, 7.0, 0.8, lag=0.1, grow=1.18, lift=(-8, -3, -2, 0, 0))   # carried a little higher
tail_wave(a, 2.0, 0.4, lag=0.1, axis=0)
ears_fn(a, fn_back=lambda t: 3 * wave(0.4)(t))
fur_flutter(a, 1.6, 0.4, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L'], axis=0)
fur_lift(a, ['fur_chest_rows'], lambda t, i: 2.5 * (1 + wave(0.4, 0.25 + i * 0.1)(t)) / 2)

a = Anim('Correndo', 'running', 0.5)
tail_pose(a, rx=(-22, -9, -15, 1, -9))                       # extended straight back, a bit above level
tail_wave(a, 4.0, 0.5, lag=0.12, grow=1.2)
tail_wave(a, 2.5, 0.25, lag=0.12, axis=0)
ears(a, back=28, out=6)
ears_fn(a, fn_back=lambda t: 3 * wave(0.25)(t))
fur_flutter(a, 3.0, 0.25, ['fur_top', 'fur_back'], axis=0, base=10)
fur_flutter(a, 3.0, 0.25, ['fur_cheek_R', 'fur_cheek_L'], axis=1)
fur_flutter(a, 2.0, 0.25, ['fur_chest_rows'], axis=0, base=-6)

a = Anim('Agachado - espreitando', 'sneaking', 2.4)
tail_pose(a, rx=(46, 8, 4, 2, -4))                           # low (the body already leans ~28° forward when crouching)
tail_wave(a, 2.5, 2.4, lag=0.1)
a.rot('cauda_ponta', lambda t: (0.0, 6 * twitch([1.4], 0.3)(t), 0.0))
ears(a, back=-10, out=8, twist=-6)                           # focused forward, a bit low
eyes_open(a, c(0.8))
brows(a, lift=-0.08)

a = Anim('Agachado andando', 'sneak_walk', 1.2)
tail_pose(a, rx=(46, 8, 4, 2, -4))
tail_wave(a, 4.0, 1.2, lag=0.12, grow=1.2)
ears(a, back=-10, out=8, twist=-6)
ears_fn(a, fn_back=lambda t: 2 * wave(0.6)(t))
eyes_open(a, c(0.8))
brows(a, lift=-0.08)

a = Anim('Pulando', 'jumping', 0.6)
tail_pose(a, rx=(-26, -8, -10, 0, -6))                       # tail rises with the jump
tail_wave(a, 2.0, 0.3, lag=0.12, axis=0)
ears(a, back=14)
fur_flutter(a, 2.5, 0.3, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L'], axis=0, base=4)

a = Anim('Caindo', 'falling', 0.3)
tail_pose(a, rx=(-58, -10, -18, -4, -12))                    # air drag pushes the tail up
tail_wave(a, 4.0, 0.3, lag=0.15, grow=1.3)
tail_wave(a, 3.0, 0.15, lag=0.15, grow=1.2, axis=0)
ears(a, back=34, out=10)
ears_fn(a, fn_back=lambda t: 4 * wave(0.15)(t))
fur_flutter(a, 4.0, 0.15, FUR, axis=0, base=8)
a.scl('olho_R', c((1.08, 1.12, 1.0))).scl('olho_L', c((1.08, 1.12, 1.0)))
brows(a, lift=0.15)

a = Anim('Nadando', 'swimming', 1.2)
tail_pose(a, rx=(40, 4, 2, 0, -2))                           # body horizontal: tail follows the legs
tail_wave(a, 7.0, 1.2, lag=0.15, grow=1.25)
ears(a, back=50, out=4)
fur_flutter(a, 2.0, 0.6, ['fur_top', 'fur_back'], axis=0, base=12)
fur_flutter(a, 2.0, 0.6, ['fur_chest_rows'], axis=0, base=-8)

a = Anim('Voando (elytra)', 'flying', 0.4)
tail_pose(a, rx=(42, 4, 2, 0, -2))                           # body horizontal: tail follows the legs
tail_wave(a, 1.5, 0.4, lag=0.15, grow=1.3)
ears(a, back=60, out=2)
fur_flutter(a, 3.0, 0.2, FUR, axis=0, base=10)

a = Anim('Voo criativo', 'creative_flying', 2.0)
tail_pose(a, rx=(-16, -6, -8, 0, -4))
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
a.scl('olho_R', c((1.1, 1.15, 1.0))).scl('olho_L', c((1.1, 1.15, 1.0)))
brows(a, lift=0.18, tilt=-10)
puff(a, 1.15, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'])

a = Anim('Congelando', 'freezing', 0.24)
ears(a, back=30, out=20)
tail_pose(a, rx=(6, -4, -6, -4, -4), ry=(18, 22, 24, 24, 20))
shiver = wave(0.12)
for b in ['orelha_R_mov', 'orelha_L_mov'] + TAIL:
    a.rot(b, lambda t: (0.0, 0.0, 1.5 * shiver(t)))
fur_lift(a, FUR, lambda t, i: 3.0 + 2.0 * shiver(t + i * 0.03))
eyes_open(a, c(0.6))
brows(a, tilt=-10)
puff(a, 1.1, ['fur_top', 'fur_back', 'fur_cheek_R', 'fur_cheek_L', 'fur_chest_rows'])

a = Anim('Rastejando', 'crawling', 1.0)
tail_pose(a, rx=(40, 4, 2, 0, -2))                           # body horizontal: tail follows the legs
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
a = Anim('Vida', 'health', 1.0)                                # 0 = almost dead, 1 = full health
low = curve([(0, 1), (0.35, 0.6), (0.6, 0), (1, 0)])
ears_fn(a, fn_back=lambda t: 30 * low(t), fn_out=lambda t: 32 * low(t))
tail_pose(a, rx=(24, 8, 6, 4, 4), fn=low)
brows(a, tilt=-12, fn=low)
a.pos('palp_R', lambda t: (0.0, -0.08 * low(t), 0.0)).pos('palp_L', lambda t: (0.0, -0.08 * low(t), 0.0))

a = Anim('Virando a cabeca', 'head_rotation_yaw', 1.0)        # 0 / 1 = head turned to each side
yaw = curve([(0, -1), (0.5, 0), (1, 1)], ease=lambda x: x)
lead = lambda t: max(-1.0, min(1.0, 1.6 * yaw(t)))           # the eyes get there before the head
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.32 * lead(t), 0.0, 0.0))   # + idle 0.15 = max 0.47 (room: 0.62)
ears_fn(a, fn_twist=lambda t: 10 * yaw(t), side='L')
ears_fn(a, fn_twist=lambda t: -10 * yaw(t), side='R')
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (0.0, -(2 + i) * yaw(t), 0.0))       # tail balances the other way

a = Anim('Olhando cima/baixo', 'head_rotation_pitch', 1.0)     # 0 = looking up, 1 = looking down
up = curve([(0, 1), (0.5, 0), (1, 0)], ease=lambda x: x)       # 1 when looking straight up
down = curve([(0, 0), (0.5, 0), (1, 1)], ease=lambda x: x)     # 1 when looking straight down
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, 0.28 * up(t) - 0.18 * down(t), 0.0))   # stays inside the painted eye
a.pos('palp_R', lambda t: (0.0, -0.1 * down(t), 0.0)).pos('palp_L', lambda t: (0.0, -0.1 * down(t), 0.0))  # frown
brows(a, lift=1.0, tilt=0.0, fn=lambda t: 0.1 * up(t) - 0.08 * down(t))
a.rot('palp_R', lambda t: (0.0, 0.0, 6 * down(t))).rot('palp_L', lambda t: (0.0, 0.0, -6 * down(t)))
ears_fn(a, fn_back=lambda t: 12 * up(t) - 6 * down(t))

# armour / helmet: tuck away what would poke through
HIDE = lambda t: (0.02, 0.02, 0.02)
a = Anim('Com capacete', 'armor_head', 1.0)
for b in ('fur_top', 'fur_back'):
    a.scl(b, HIDE)
# the ears are hidden by their own NON-additive animation (priority 50): the 'Ignorar capacete' toggle
# (priority 60) sets them back to full size, and 'Esconder orelhas' (priority 70) still wins over both
EAR_HIDE_PRIO, EAR_SHOW_PRIO, EAR_OFF_PRIO = 50, 60, 70
Anim('Com capacete - orelhas', 'armor_head', 1.0, additive=False, priority=EAR_HIDE_PRIO).scl('orelhas', HIDE)
a = Anim('Com peitoral', 'armor_body', 1.0)
for b in ('fur_chest', 'fur_cauda_raiz'):
    a.scl(b, HIDE)
a = Anim('Com calca', 'armor_legs', 1.0)
a.scl('fur_cauda_raiz', HIDE)
a = Anim('Com cabeca de mob', 'wearing_skull', 1.0)
for b in ('fur_top', 'fur_back'):
    a.scl(b, HIDE)
Anim('Com cabeca de mob - orelhas', 'wearing_skull', 1.0, additive=False, priority=EAR_HIDE_PRIO).scl('orelhas', HIDE)

# ============================================================ SMOOTH TRANSITIONS (CPM setup / finish)
def staged(pose_anim, dur=0.3):
    """Enter (setup) and leave (finish) animations for a pose: ease from nothing to the pose's first
    frame and back, so entering/leaving a state is never a snap."""
    e = smooth
    for kind in ('setup', 'finish'):
        st = Anim('p:' + pose_anim.type, kind, dur, loop='once')
        for bone, chans in pose_anim.tracks.items():
            for ch in chans:
                v0 = pose_anim.value(bone, ch, 0.0)
                w = (lambda t: e(t / dur)) if kind == 'setup' else (lambda t: 1 - e(t / dur))
                if ch == 'scale':
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(1 + (x - 1) * w(t) for x in v0))(v0, w))
                else:
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(x * w(t) for x in v0))(v0, w))


STAGED = {'walking': 0.3, 'running': 0.3, 'sneaking': 0.35, 'sneak_walk': 0.35, 'jumping': 0.15,
          'falling': 0.4, 'swimming': 0.4, 'flying': 0.4, 'creative_flying': 0.4, 'crawling': 0.35,
          'sleeping': 0.6, 'riding': 0.4, 'on_ladder': 0.3, 'climbing_on_ladder': 0.3,
          'blocking_left': 0.2, 'blocking_right': 0.2, 'spyglass_left': 0.2, 'spyglass_right': 0.2}
for an in [x for x in ANIMS if x.type in STAGED and x.additive and not x.name.startswith('p:')]:
    staged(an, STAGED[an.type])

# ============================================================ SETTINGS (CPM toggles)
a = Anim('Esconder orelhas', 'layer', 1.0, additive=False, priority=EAR_OFF_PRIO)
a.scl('orelhas', c((0.01, 0.01, 0.01)))
a = Anim('Ignorar capacete', 'layer', 1.0, additive=False, priority=EAR_SHOW_PRIO)   # ears always visible
a.scl('orelhas', c((1.0, 1.0, 1.0)))
a = Anim('Esconder cauda', 'layer', 1.0)
a.scl('cauda', c((0.01, 0.01, 0.01)))
a.scl('fur_cauda_raiz', c((0.01, 0.01, 0.01)))

# ============================================================ EMOTES - rig helpers
PIVOT = {'head': (0, 24, 0), 'body': (0, 24, 0), 'right_arm': (5, 22, 0), 'left_arm': (-5, 22, 0),
         'right_leg': (1.9, 12, 0), 'left_leg': (-1.9, 12, 0)}
UPPER = ('head', 'body', 'right_arm', 'left_arm')
HIP = np.array([0.0, 12.0, 0.0])


def R_to(v_from, v_to):
    """Shortest rotation taking direction v_from onto v_to."""
    a_, b_ = norm(v_from), norm(v_to)
    v = np.cross(a_, b_)
    c_ = float(a_ @ b_)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c_ > 0 else rotmat((180, 0, 0))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c_))


def norm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


HANG = (0, -1, 0)


def aim(direction, frame=np.eye(3)):
    """Arm/leg rotation (euler) so the limb points along `direction` (model space), for a limb whose
    parent frame is `frame` (identity, or the torso rotation when the torso is tilted)."""
    return euler_zyx(frame.T @ R_to(HANG, direction))


def aim_at(bone, target, frame=np.eye(3), offset=np.zeros(3)):
    """Limb pointing from its (moved) shoulder/hip to a target point."""
    p = np.array(PIVOT[bone], float) + offset
    return aim(np.array(target, float) - p, frame)


def rig(torso=(0, 0, 0), drop=(0, 0, 0), limbs=None, whole=None, whole_c=(0, 0, 0)):
    """Full-body pose -> {bone: (rot, pos)}.
    torso: tilt of head/body/arms around the hips; drop: move everything; limbs: extra rotation of a part
    in its parent frame (euler, or matrix); whole: rotate the whole body rigidly around whole_c."""
    limbs = limbs or {}
    Rt = rotmat(torso)
    Rw = rotmat(whole) if whole is not None else np.eye(3)
    Cw = np.array(whole_c, float)
    out = {}
    for b, p in PIVOT.items():
        p = np.array(p, float)
        R = Rt if b in UPPER else np.eye(3)
        q = HIP + Rt @ (p - HIP) if b in UPPER else p.copy()
        L = limbs.get(b, (0, 0, 0))
        L = L if isinstance(L, np.ndarray) else rotmat(L)
        Rf = Rw @ R @ L
        qf = Cw + Rw @ (q - Cw) + np.array(drop, float)
        out[b] = (euler_zyx(Rf), tuple(qf - p))
    return out


def keyposes(a, frames, ease=smooth):
    """frames: [(time, {bone: (rot, pos)} or {bone: {'r':..,'p':..,'s':..}})] eased between keys.
    Bones missing in a frame are neutral there."""
    bones = set()
    for _, f in frames:
        bones |= set(f)
    for b in bones:
        for ch, idx, neutral in (('rotation', 0, Z3), ('position', 1, Z3), ('scale', 2, O3)):
            pts = []
            used = False
            for t, f in frames:
                v = f.get(b)
                if v is None:
                    val = neutral
                elif isinstance(v, dict):
                    val = tuple(v.get('rps'[idx], neutral))
                    used |= ('rps'[idx]) in v
                else:
                    val = tuple(v[idx]) if idx < len(v) else neutral
                    used |= idx < len(v)
                pts.append((t, val))
            if used:
                a.add(b, ch, curve(pts, ease))


def merge(*poses):
    out = {}
    for p in poses:
        out.update(p)
    return out


NEUTRAL = {}


def staged_custom(an, dur=0.45):
    """Enter/leave transitions for a custom pose (CPM 'c:<name>' setup/finish)."""
    for kind in ('setup', 'finish'):
        st = Anim('c:' + an.name, kind, dur, loop='once')
        for bone, chans in an.tracks.items():
            for ch in chans:
                v0 = an.value(bone, ch, 0.0)
                w = (lambda t: smooth(t / dur)) if kind == 'setup' else (lambda t: 1 - smooth(t / dur))
                if ch == 'scale':
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(1 + (x - 1) * w(t) for x in v0))(v0, w))
                else:
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(x * w(t) for x in v0))(v0, w))


def rest_tail(a, rx, ry=(0, 0, 0, 0, 0)):
    tail_pose(a, rx=rx, ry=ry)


# ============================================================ EMOTES 1 - continuous (custom poses, loop;
# CPM ends a custom pose by itself as soon as the player starts moving)
def arm_to(bone, target, torso=(0, 0, 0), drop=(0, 0, 0)):
    """Arm aimed at a world point when the torso is tilted around the hips and everything is dropped."""
    Rt = rotmat(torso)
    p = np.array(PIVOT[bone], float)
    sh = HIP + Rt @ (p - HIP) + np.array(drop, float)
    return aim(np.array(target, float) - sh, Rt)


# --- Deitar e olhar o ceu: lies on the back, hands behind the head
a = Anim('Deitar e olhar o ceu', 'custom_pose', 5.0)
LIE = (90, 0, 0)
lie = rig(whole=LIE, whole_c=(0, 12, 0), drop=(0, -10, -6), limbs={
    'right_arm': aim_at('right_arm', (2.2, 31.5, 2.6)), 'left_arm': aim_at('left_arm', (-2.2, 31.5, 2.6)),
    'right_leg': (14, 0, 3), 'left_leg': (0, 0, -2), 'head': (-10, 0, 0)})
for b, (r, p) in lie.items():
    a.rot(b, c(r)).pos(b, c(p))
breath_e3 = wave(5.0, -0.25)
ears(a, back=10, out=34)
tail_pose(a, rx=(40, 4, 2, 0, -4), ry=(38, 12, 8, 4, 2))       # along the ground, to the side (not into it)
a.rot('cauda_ponta', lambda t: (0.0, 8 * twitch([3.1], 0.6)(t), 0.0))
fur_lift(a, ['fur_chest_rows', 'fur_chest_edge_R', 'fur_chest_edge_L'], lambda t, i: 2.5 * (breath_e3(t) + 1) / 2)
brows(a, lift=0.08)
staged_custom(a, 0.6)

# --- Pensativo: hand on the chin, looks up and thinks until the player moves
a = Anim('Pensativo', 'custom_pose', 4.6)
chin = aim_at('right_arm', (1.2, 24.4, -4.4))
hold = aim_at('left_arm', (1.8, 17.2, -3.4))
think = {'right_arm': (chin, Z3), 'left_arm': (hold, Z3), 'head': ((-16, 0, -10), Z3)}
keyposes(a, [(0.0, think), (1.5, merge(think, {'head': ((-18, 6, -12), Z3)})),
             (3.1, merge(think, {'head': ((-14, -3, -8), Z3)})), (4.6, think)])
ears_fn(a, fn_twist=lambda t: 18 * twitch([1.6, 2.5], 0.3)(t), fn_back=lambda t: 10 * twitch([1.6, 2.5], 0.3)(t),
        side='L')
a.pos('palp_R', c((0.0, 0.1, 0.0))).rot('palp_R', c((0.0, 0.0, -5.0)))
iris_e10 = curve([(0, -0.15), (1.5, -0.05), (3.1, -0.2), (4.6, -0.15)])
for s in 'RL':
    a.pos('iris_' + s, lambda t: (iris_e10(t), 0.22, 0.0))
tail_wave(a, 3.5, 2.3)
staged_custom(a, 0.5)

# --- Tristeza: head hanging, shoulders dropped, ears and tail down, slow heavy breathing (no crying)
a = Anim('Tristeza', 'custom_pose', 5.0)
sigh_e13 = curve([(0, 0), (1.6, 0), (2.4, 1), (3.0, 1), (4.2, 0), (5.0, 0)])     # one deep sigh per loop
sad = lambda k: rig(torso=(-9 + 2 * k, 0, 2), drop=(0, -0.4 + 0.25 * k, 0), limbs={
    'head': (-30 + 6 * k, 0, 6), 'right_arm': (7, 0, -5), 'left_arm': (6, 0, 5),
    'right_leg': (0, 0, -1), 'left_leg': (0, 0, 1)})
for b in PIVOT:
    a.rot(b, (lambda b: lambda t: sad(sigh_e13(t))[b][0])(b))
    a.pos(b, (lambda b: lambda t: sad(sigh_e13(t))[b][1])(b))
a.pos('right_arm', c((0.0, -0.5, 0.0))).pos('left_arm', c((0.0, -0.5, 0.0)))   # shoulders dropped
ears(a, back=26, out=38)
a.rot('orelha_R_mov', lambda t: (0.0, 0.0, 3 * twitch([3.4], 0.8)(t)))
brows(a, lift=-0.12, tilt=-14)                                                    # sad lids, heavy band
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.18, 0.0))
tail_pose(a, rx=(34, 10, 8, 6, 4))
a.rot('cauda', lambda t: (0.0, 3 * math.sin(2 * math.pi * t / 5.0), 0.0))
a.rot('cauda_ponta', lambda t: (0.0, 6 * twitch([1.1], 0.9)(t), 0.0))
staged_custom(a, 0.8)

# ============================================================ EMOTES 2 - one-shot gestures (start and end at
# the normal pose with easing, so they blend in and out by themselves)
H_OUT = lambda x, y, z: (x - 0.0, y - 18.0, z - 0.0)       # hologram target (model space) -> delta from rest


def holo(a, group, keys):
    """keys: [(t, target position or None(hidden), scale)] for a hologram group."""
    frames = []
    for t, pos, s in keys:
        if pos is None:
            frames.append((t, {group: {'p': (0, 0, 0), 's': (1, 1, 1)}}))
        else:
            frames.append((t, {group: {'p': H_OUT(*pos), 's': (s, s, s)}}))
    keyposes(a, frames)


BR = {'s': (1.28, 1.0, 1.28)}
BR0 = {'s': (1, 1, 1)}

# --- Alerta de emergencia: taps the bracelet, sends the signal, watches the confirmation
a = Anim('Alerta de emergencia', 'gesture', 5.0, loop='once')
wrist_up = aim_at('left_arm', (-1.0, 18.5, -6.5))
tap = aim_at('right_arm', (-0.6, 19.4, -6.8))
tap_in = aim_at('right_arm', (-0.9, 19.1, -6.4))
look_wrist = (26, 14, 0)
keyposes(a, [
    (0.0, {}),
    (0.6, {'left_arm': (wrist_up, Z3), 'head': (look_wrist, Z3)}),
    (0.85, {'left_arm': (wrist_up, Z3), 'right_arm': (tap, Z3), 'head': (look_wrist, Z3)}),
    (1.0, {'left_arm': (wrist_up, Z3), 'right_arm': (tap_in, Z3), 'head': (look_wrist, Z3)}),
    (1.12, {'left_arm': (wrist_up, Z3), 'right_arm': (tap, Z3), 'head': (look_wrist, Z3)}),
    (1.25, {'left_arm': (wrist_up, Z3), 'right_arm': (tap_in, Z3), 'head': (look_wrist, Z3)}),
    (1.5, {'left_arm': (wrist_up, Z3), 'head': ((10, 8, 0), Z3)}),
    (3.4, {'left_arm': (wrist_up, Z3), 'head': ((8, 8, 0), Z3)}),
    (3.7, {'left_arm': (wrist_up, Z3), 'head': ((16, 8, 0), Z3)}),          # nod at the confirmation
    (3.9, {'left_arm': (wrist_up, Z3), 'head': ((6, 8, 0), Z3)}),
    (4.4, {'left_arm': (wrist_up, Z3)}),
    (5.0, {})])
keyposes(a, [(0, {'bracelete': BR0}), (0.35, {'bracelete': BR0}), (0.55, {'bracelete': BR}),
             (4.5, {'bracelete': BR}), (4.75, {'bracelete': BR0}), (5.0, {'bracelete': BR0})])
holo(a, 'holo_sinal', [(0, None, 1), (1.3, None, 1), (1.45, (-2.2, 21.5, -9.5), 0.7),
                       (3.3, (-2.2, 21.5, -9.5), 1.1), (3.45, None, 1), (5.0, None, 1)])
pulse_e5 = lambda t: 1 + 0.35 * max(0.0, math.sin(2 * math.pi * (t - 1.45) / 0.45)) if 1.45 < t < 3.3 else 1.0
a.scl('holo_sinal', lambda t: (pulse_e5(t), pulse_e5(t), pulse_e5(t)))
holo(a, 'holo_ok', [(0, None, 1), (3.45, None, 1), (3.6, (-1.8, 21.8, -9.5), 1.6), (4.3, (-1.8, 21.8, -9.5), 1.6),
                    (4.45, None, 1), (5.0, None, 1)])
env_e5 = curve([(0, 0), (0.5, 1), (4.4, 1), (5.0, 0)])
ears_fn(a, fn_back=lambda t: -10 * env_e5(t), fn_twist=lambda t: -8 * env_e5(t))
brows(a, lift=0.08, fn=lambda t: env_e5(t) * (1 if t < 3.4 else 1.6))
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.2 * env_e5(t), -0.12 * env_e5(t), 0.0))
a.rot('cauda', lambda t: (-6 * env_e5(t), 0.0, 0.0))

# --- Mapa 3D: projects a 3D map and spins it with the hands
a = Anim('Mapa 3D', 'gesture', 7.0, loop='once')
MAP = (-0.5, 19.8, -9.0)
palm = aim_at('left_arm', (-1.5, 17.2, -7.0))
sweep = lambda x: aim_at('right_arm', (x, 21.6, -8.4))
frames = [(0.0, {}), (0.6, {'left_arm': (palm, Z3), 'head': ((14, 5, 0), Z3)})]
tt = 1.3
for x in (1.8, -1.6, 1.6, -1.8, 1.4, -1.2):                  # swipes that spin_e6 the map
    frames.append((tt, {'left_arm': (palm, Z3), 'right_arm': (sweep(x), Z3), 'head': ((12, 3, 0), Z3)}))
    tt += 0.7
frames += [(5.9, {'left_arm': (palm, Z3), 'head': ((14, 5, 0), Z3)}), (7.0, {})]
keyposes(a, frames)
keyposes(a, [(0, {'bracelete': BR0}), (0.3, {'bracelete': BR0}), (0.5, {'bracelete': BR}),
             (6.4, {'bracelete': BR}), (6.7, {'bracelete': BR0}), (7.0, {'bracelete': BR0})])
holo(a, 'holo_mapa', [(0, None, 1), (0.7, None, 1), (1.1, MAP, 2.1), (5.8, MAP, 2.1), (6.3, None, 1), (7.0, None, 1)])
spin_e6 = curve([(0, 0), (1.3, 0), (5.5, 300), (7.0, 360)])
a.rot('holo_mapa', lambda t: (0.0, spin_e6(t), 0.0))
env_e6 = curve([(0, 0), (0.6, 1), (6.2, 1), (7.0, 0)])
ears_fn(a, fn_back=lambda t: -10 * env_e6(t), fn_twist=lambda t: -10 * env_e6(t))
brows(a, lift=0.1, fn=env_e6)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.12 * math.sin(2 * math.pi * t / 1.4) * env_e6(t), -0.1 * env_e6(t), 0.0))
tail_wave(a, 3.0, 1.4)

# --- Holograma de missao: raises the bracelet, projects an interface and browses it with the other hand
a = Anim('Holograma de missao', 'gesture', 7.0, loop='once')
PANEL = (-1.0, 23.4, -9.6)
raise_l = aim_at('left_arm', (-3.0, 21.0, -8.0))
touch = lambda x, y, push=0.0: aim_at('right_arm', (x, y, -8.6 + push))
frames = [(0.0, {}), (0.6, {'left_arm': (raise_l, Z3), 'head': ((-4, 6, 0), Z3)})]
tt = 1.4
for x, y in ((0.4, 24.0), (-1.4, 23.0), (0.8, 22.4), (-0.6, 23.8)):
    frames.append((tt, {'left_arm': (raise_l, Z3), 'right_arm': (touch(x, y), Z3), 'head': ((-4, 4, 0), Z3)}))
    frames.append((tt + 0.25, {'left_arm': (raise_l, Z3), 'right_arm': (touch(x, y, -0.8), Z3),
                               'head': ((-4, 4, 0), Z3)}))
    tt += 0.9
frames += [(5.9, {'left_arm': (raise_l, Z3), 'head': ((-4, 6, 0), Z3)}), (7.0, {})]
keyposes(a, frames)
keyposes(a, [(0, {'bracelete': BR0}), (0.3, {'bracelete': BR0}), (0.5, {'bracelete': BR}),
             (6.4, {'bracelete': BR}), (6.7, {'bracelete': BR0}), (7.0, {'bracelete': BR0})])
holo(a, 'holo_painel', [(0, None, 1), (0.8, None, 1), (1.2, PANEL, 1.8), (5.8, PANEL, 1.8), (6.3, None, 1),
                        (7.0, None, 1)])
card_e7 = curve([(0, 0), (1.9, 0), (2.1, 0.9), (2.8, 0.9), (3.0, -0.9), (3.7, -0.9), (3.9, 0.5), (4.6, 0.5),
              (4.8, 0), (7, 0)])
a.pos('holo_card', lambda t: (card_e7(t), 0.0, 0.0))
env_e7 = curve([(0, 0), (0.6, 1), (6.2, 1), (7.0, 0)])
ears_fn(a, fn_back=lambda t: -8 * env_e7(t), fn_twist=lambda t: -8 * env_e7(t))
brows(a, lift=0.06, fn=env_e7)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.15 * math.sin(2 * math.pi * t / 0.9) * env_e7(t), 0.15 * env_e7(t), 0.0))

# --- Investigar: kneels and examines something on the ground
a = Anim('Investigar', 'gesture', 5.2, loop='once')
Rt = rotmat((-32, 0, 0))
kneel = lambda poke=0.0, tilt=0.0: rig(torso=(-32, 0, tilt), drop=(0, -5.2, 0), limbs={
    'left_leg': (62, 0, 0), 'right_leg': (-55, 0, 2),
    'right_arm': aim_at('right_arm', (2.0, 2.0 + poke, -9.0), Rt, Rt @ (np.array(PIVOT['right_arm']) - HIP)
                        + HIP - np.array(PIVOT['right_arm']) + np.array((0, -5.2, 0))),
    'left_arm': (50, 0, -10), 'head': (28, 0, tilt * 1.5)})
keyposes(a, [(0.0, {}), (0.7, kneel()), (1.5, kneel(0.8, 4)), (1.8, kneel(0, 4)), (2.4, kneel(0.8, -5)),
             (2.7, kneel(0, -5)), (3.6, kneel(0.5, 0)), (4.4, kneel()), (5.2, {})])
env_e8 = curve([(0, 0), (0.7, 1), (4.4, 1), (5.2, 0)])
sn_e8 = twitch([1.3, 1.45, 2.9, 3.05, 3.2], 0.13)
a.pos('nariz', lambda t: (0.0, 0.03 * sn_e8(t), -0.02 * sn_e8(t)))
ears_fn(a, fn_back=lambda t: -12 * env_e8(t), fn_twist=lambda t: -6 * env_e8(t) + 14 * twitch([2.2], 0.3)(t))
brows(a, lift=0.05, tilt=4, fn=env_e8)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.1 * math.sin(2 * math.pi * t / 1.7) * env_e8(t), -0.16 * env_e8(t), 0.0))
tail_wave(a, 4.0, 1.2, lag=0.12)
a.rot('cauda', lambda t: (18 * env_e8(t), 0.0, 0.0))                       # tail low while crouched

# --- Saudacao: waves, tilts the head and wags the tail
a = Anim('Saudacao', 'gesture', 3.0, loop='once')
arm_up_e9 = aim_at('right_arm', (8.0, 32.0, -2.5))
frames = [(0.0, {}), (0.35, {'right_arm': (arm_up_e9, Z3)})]
for i, t in enumerate((0.55, 0.8, 1.05, 1.3, 1.55, 1.8, 2.05)):
    frames.append((t, {'right_arm': (tuple(np.add(arm_up_e9, (0, 0, 14 if i % 2 == 0 else -10))), Z3),
                       'head': ((6, 0, 12), Z3)}))
frames += [(2.4, {'right_arm': (arm_up_e9, Z3), 'head': ((0, 0, 6), Z3)}), (3.0, {})]
keyposes(a, frames)
env_e9 = curve([(0, 0), (0.35, 1), (2.4, 1), (3.0, 0)])
ears_fn(a, fn_back=lambda t: -8 * env_e9(t), fn_twist=lambda t: -8 * env_e9(t))
brows(a, lift=0.12, fn=env_e9)
tail_wave(a, 16.0, 0.5, lag=0.12, grow=1.1)
a.rot('cauda', lambda t: (-12 * env_e9(t), 0.0, 0.0))

# --- Alongamento / aquecimento: stretches up, bends to the sides, pulls each arm, swings the legs
a = Anim('Alongamento', 'gesture', 9.0, loop='once')
UPR = aim((0.45, 1, 0.08))
UPL = aim((-0.45, 1, 0.08))
reach = lambda tz, k=1.0: rig(torso=(4 * k, 0, tz), limbs={
    'right_arm': aim((0.45 - 0.5 * tz / 20, 1, 0.08), rotmat((4 * k, 0, tz))) if tz else UPR,
    'left_arm': aim((-0.45 - 0.5 * tz / 20, 1, 0.08), rotmat((4 * k, 0, tz))) if tz else UPL,
    'head': (12 * k, 0, 0)})
cross_r = {'right_arm': (aim_at('right_arm', (-6.0, 19.5, -4.0)), Z3),
           'left_arm': (aim_at('left_arm', (-0.6, 19.2, -4.2)), Z3), 'head': ((0, -12, 0), Z3)}
cross_l = {'left_arm': (aim_at('left_arm', (6.0, 19.5, -4.0)), Z3),
           'right_arm': (aim_at('right_arm', (0.6, 19.2, -4.2)), Z3), 'head': ((0, 12, 0), Z3)}
hips = {'right_arm': ((0, 0, 32), Z3), 'left_arm': ((0, 0, -32), Z3)}
swing = lambda side, k: merge(hips, {side: ((58 * k, 0, 0), Z3),
                                      'body': ((-3 * k, 0, 0), Z3)})
keyposes(a, [
    (0.0, {}),
    (0.7, reach(0)),                         # arms up, on the toes of the stretch
    (1.5, merge(reach(0, 1.6), {'right_leg': (Z3, (0, 0.6, 0)), 'left_leg': (Z3, (0, 0.6, 0)),
                                'body': (Z3, (0, 0.6, 0))})),
    (2.1, reach(16)), (2.7, reach(16)),      # bend to the left side...
    (3.3, reach(-16)), (3.9, reach(-16)),    # ...and to the right
    (4.5, cross_r), (5.1, cross_r),          # pull the right arm across the chest
    (5.6, cross_l), (6.2, cross_l),          # and the left one
    (6.6, hips), (6.9, swing('right_leg', 1)), (7.2, swing('right_leg', 0)),
    (7.5, swing('left_leg', 1)), (7.8, swing('left_leg', 0)),
    (8.3, hips), (9.0, {})])
# the full-body lift at 1.5 (going on the toes) also lifts head and arms
keyposes(a, [(0.0, {}), (0.7, {}), (1.5, {'head': {'p': (0, 0.6, 0)}, 'right_arm': {'p': (0, 0.6, 0)},
                                          'left_arm': {'p': (0, 0.6, 0)}}), (2.1, {}), (9.0, {})])
env_e14 = curve([(0, 0), (0.7, 1), (8.3, 1), (9.0, 0)])
yawn_e14 = curve([(0, 0), (0.7, 0), (1.5, 1), (2.1, 0), (9, 0)])
ears_fn(a, fn_back=lambda t: 22 * yawn_e14(t) - 6 * env_e14(t) + 14 * twitch([6.9, 7.5], 0.3)(t),
        fn_out=lambda t: 10 * yawn_e14(t))
brows(a, lift=0.1, fn=lambda t: env_e14(t) - 1.6 * yawn_e14(t))           # eyes squeezed in the big stretch
fur_flutter(a, 6.0, 0.5, base=0.0)
tail_pose(a, rx=(-30, -8, -6, 0, 0), fn=yawn_e14)                          # tail stretches up too
tail_wave(a, 7.0, 0.9, lag=0.12)

# --- Finalizando missao: opens the mission hologram, checks the last item and closes it satisfied
a = Anim('Finalizando missao', 'gesture', 7.0, loop='once')
PANEL2 = (-1.0, 23.4, -9.6)
raise_l2 = aim_at('left_arm', (-3.0, 21.0, -8.0))
touch2 = lambda x, y, push=0.0: aim_at('right_arm', (x, y, -8.6 + push))
fist = rig(limbs={'right_arm': aim((0.35, 0.8, -0.5)), 'head': (8, 0, 0)})             # small victory pump
keyposes(a, [
    (0.0, {}),
    (0.6, {'left_arm': (raise_l2, Z3), 'head': ((-4, 6, 0), Z3)}),
    (1.5, {'left_arm': (raise_l2, Z3), 'right_arm': (touch2(0.6, 23.2), Z3), 'head': ((-4, 4, 0), Z3)}),
    (1.75, {'left_arm': (raise_l2, Z3), 'right_arm': (touch2(0.6, 23.2, -0.8), Z3), 'head': ((-4, 4, 0), Z3)}),
    (2.2, {'left_arm': (raise_l2, Z3), 'right_arm': (touch2(-0.4, 22.6), Z3), 'head': ((-2, 2, 0), Z3)}),
    (2.8, {'left_arm': (raise_l2, Z3), 'right_arm': (touch2(-1.0, 23.0), Z3), 'head': ((-2, 2, 0), Z3)}),
    (3.0, {'left_arm': (raise_l2, Z3), 'right_arm': (touch2(-1.0, 23.0, -1.0), Z3), 'head': ((0, 2, 0), Z3)}),
    (3.3, {'left_arm': (raise_l2, Z3), 'head': ((-6, 4, 0), Z3)}),
    (3.9, {'left_arm': (raise_l2, Z3), 'head': ((6, 4, 0), Z3)}),             # nod: done!
    (4.2, {'left_arm': (raise_l2, Z3), 'head': ((-4, 4, 0), Z3)}),
    (5.0, {'left_arm': (raise_l2, Z3)}),
    (5.5, merge(fist, {'left_arm': ((0, 0, 0), Z3)})),
    (6.1, merge(fist, {'left_arm': ((0, 0, 0), Z3)})),
    (7.0, {})])
keyposes(a, [(0, {'bracelete': BR0}), (0.3, {'bracelete': BR0}), (0.5, {'bracelete': BR}),
             (5.2, {'bracelete': BR}), (5.5, {'bracelete': BR0}), (7.0, {'bracelete': BR0})])
holo(a, 'holo_painel', [(0, None, 1), (0.8, None, 1), (1.2, PANEL2, 1.8), (4.5, PANEL2, 1.8),
                        (4.95, None, 1), (7.0, None, 1)])
card_e15 = curve([(0, 0), (2.0, 0), (2.3, -0.9), (4.5, -0.9), (4.6, 0), (7, 0)])  # card slides to the last item
a.pos('holo_card', lambda t: (card_e15(t), 0.0, 0.0))
OKP = (-1.0, 23.4, -10.1)                                                     # check mark in front of the panel
holo(a, 'holo_ok', [(0, None, 1), (3.0, None, 1), (3.12, OKP, 2.4), (3.3, OKP, 1.7), (3.45, OKP, 1.9),
                    (4.4, OKP, 1.9), (4.55, None, 1), (7.0, None, 1)])
a.rot('holo_ok', lambda t: (0.0, 0.0, curve([(0, 0), (3.0, 0), (3.12, -25), (3.35, 6), (3.5, 0), (7, 0)])(t)))
env_e15 = curve([(0, 0), (0.6, 1), (6.2, 1), (7.0, 0)])
done_e15 = curve([(0, 0), (3.0, 0), (3.3, 1), (6.2, 1), (7.0, 0)])
ears_fn(a, fn_back=lambda t: -8 * env_e15(t) - 6 * done_e15(t), fn_twist=lambda t: -8 * env_e15(t))
brows(a, lift=0.06, fn=lambda t: env_e15(t) + 0.8 * done_e15(t))
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.12 * math.sin(2 * math.pi * t / 0.9) * (env_e15(t) - done_e15(t)),
                                  0.15 * env_e15(t) - 0.1 * done_e15(t), 0.0))
for i, b in enumerate(TAIL):                                                  # happy wag once it's done
    a.rot(b, lambda t, i=i: (0.0, 12 * 1.1 ** i * math.sin(2 * math.pi * (t / 0.5 - 0.12 * i)) * done_e15(t), 0.0))
a.rot('cauda', lambda t: (-10 * done_e15(t), 0.0, 0.0))

# --- Pouso de heroi: lands from high up, knee and hand on the ground, looks up and rises dramatically
a = Anim('Pouso de heroi', 'gesture', 5.2, loop='once')
LAND_T, LAND_D = (-34, 0, 5), (0, -6.2, 0)
land = lambda head_x, torso=LAND_T, drop=LAND_D: rig(torso=torso, drop=drop, limbs={
    'right_leg': (-62, 0, 4), 'left_leg': (68, 0, -6),
    'right_arm': arm_to('right_arm', (3.0, 0.3, -7.2), torso, drop),
    'left_arm': aim((-0.7, -0.15, 0.9), rotmat(torso)),
    'head': (head_x, 0, -4)})
air = rig(drop=(0, 2.5, 0), limbs={'right_arm': (-20, 0, 55), 'left_arm': (-20, 0, -55),
                                   'right_leg': (18, 0, 6), 'left_leg': (-12, 0, -6), 'head': (-14, 0, 0)})
rise1 = rig(torso=(-18, 0, 2), drop=(0, -3.4, 0), limbs={
    'right_leg': (-30, 0, 3), 'left_leg': (40, 0, -4), 'right_arm': (10, 0, 10), 'left_arm': (-10, 0, -18),
    'head': (18, 0, -2)})
proud = rig(torso=(3, 0, 0), limbs={'right_arm': (0, 0, 12), 'left_arm': (0, 0, -12),
                                    'right_leg': (0, 0, -4), 'left_leg': (0, 0, 4), 'head': (7, 0, 0)})
keyposes(a, [
    (0.0, {}),
    (0.22, air),                              # coming down
    (0.38, land(-8, torso=(-40, 0, 6), drop=(0, -7.0, 0))),   # IMPACT (a bit deeper)
    (0.62, land(-6)),                         # settles
    (1.5, land(-6)),                          # head down... (dramatic pause)
    (2.3, land(34)),                          # ...slowly looks up, straight ahead
    (2.9, land(34)),
    (3.7, rise1),                             # pushes off the ground
    (4.3, proud), (4.6, proud),               # stands tall
    (5.2, {})])
impact_e16 = curve([(0, 0), (0.3, 0), (0.38, 1), (0.9, 0), (5.2, 0)])
env_e16 = curve([(0, 0), (0.38, 1), (3.7, 1), (4.6, 0.4), (5.2, 0)])
look_e16 = curve([(0, 0), (1.5, 0), (2.3, 1), (3.7, 1), (4.6, 0.3), (5.2, 0)])
fur_lift(a, FUR, lambda t, i: 18 * impact_e16(t) * (0.7 + 0.3 * math.sin(i * 1.7)))   # fur blown up on impact
ears_fn(a, fn_back=lambda t: 34 * impact_e16(t) + 10 * env_e16(t) * (1 - look_e16(t)) - 10 * look_e16(t),
        fn_out=lambda t: 16 * impact_e16(t))
brows(a, lift=-0.06, tilt=12, fn=lambda t: env_e16(t) * look_e16(t) + 0.5 * impact_e16(t))   # determined look
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.14 * env_e16(t) * (1 - look_e16(t)) + 0.12 * look_e16(t), 0.0))
tail_pose(a, rx=(-40, -12, -10, -4, -6), fn=curve([(0, 0), (0.22, 1), (0.38, 0.2), (5.2, 0)]))  # up while falling
tail_pose(a, rx=(22, 6, 4, 2, 0), ry=(30, 10, 8, 6, 4), fn=curve([(0, 0), (0.3, 0), (0.45, 1), (3.3, 1),
                                                                    (4.3, 0), (5.2, 0)]))       # sweeps the ground
tail_wave(a, 9.0, 1.0, lag=0.12, grow=1.1)

# ============================================================ save
d['animations'] = [x.to_json() for x in ANIMS]
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_25_128.png'
d['name'] = 'skin_v16.25'
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok: %d animations, %d keyframes' % (len(ANIMS), sum(len(v['keyframes']) for x in d['animations']
                                                           for v in x['animators'].values())))
