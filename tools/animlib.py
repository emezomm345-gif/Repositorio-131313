"""Animation helpers shared by the generators (extracted from tools/v16_28_emotes.py).

Use:  d = json.load(...); FPS = 20; exec(open('tools/animlib.py').read())  -> Anim, keyposes, rig, aim_at, ears...
New animations are collected in ANIMS. Needs `d` (the model) and FPS in the calling namespace.
"""
import math, uuid, copy
import numpy as np
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


def arm_to(bone, target, torso=(0, 0, 0), drop=(0, 0, 0)):
    """Arm aimed at a world point when the torso is tilted around the hips and everything is dropped."""
    Rt = rotmat(torso)
    p = np.array(PIVOT[bone], float)
    sh = HIP + Rt @ (p - HIP) + np.array(drop, float)
    return aim(np.array(target, float) - sh, Rt)


def staged_layer(an, dur=0.35):
    """Enter/leave transitions for a layer (CPM 'g:<name>' setup/finish)."""
    for kind in ('setup', 'finish'):
        st = Anim('g:' + an.name, kind, dur, loop='once')
        for bone, chans in an.tracks.items():
            for ch in chans:
                v0 = an.value(bone, ch, 0.0)
                w = (lambda t: smooth(t / dur)) if kind == 'setup' else (lambda t: 1 - smooth(t / dur))
                if ch == 'scale':
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(1 + (x - 1) * w(t) for x in v0))(v0, w))
                else:
                    st.add(bone, ch, (lambda v0, w: lambda t: tuple(x * w(t) for x in v0))(v0, w))


