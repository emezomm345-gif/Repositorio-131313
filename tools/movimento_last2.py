"""L.A.S.T only: real running / jumping cycles, stable postures for everything else.

usage: python3 tools/movimento_last2.py <skin_v16.30_LAST.bbmodel> <skin_v16.33_LAST.bbmodel>

What CPM allows (learned in game):
- A pose animation restarts every time the pose is entered. "Walking" / "sneak walking" are detected from the
  position change between frames and are re-entered all the time, so a cycle of our own restarts constantly there.
  Those keep the vanilla swing (synced, it never restarts) with an additive posture.
- "Crawling" / "swimming" stay on while you lie still, so nothing there may move by itself: vanilla strokes (they
  move only when you move) + a static posture.
- "Running" (sprint flag) and "jumping" (jump event) are stable: there the arms/legs (running) and the legs
  (jumping) are our own cycles (non-additive, at Minecraft's tempo) with shoulders, bob, weight and head in sync,
  starting on the passing pose with a very short entry.
- The attack swing is recreated (non-additive, from the vanilla formula) so it also shows while running.
- Turning: the legs twist with the body and the leg on that side steps out.
"""
import json, sys, os, math, uuid, copy
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
assert len(d['groups']) == n_groups
EXISTING = d['animations']
BODY = ('head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg')
LIMBS = ('right_arm', 'left_arm', 'right_leg', 'left_leg')
UID = {b: GRP[b]['uuid'] for b in GRP}
EPS = 0.05
P_WALK, P_ITEM, P_PUNCH = -1, 5, 6              # non-additive priorities: cycles < item poses < attack


# ------------------------------------------------------------------ file helpers
def main_of(cpm_type):
    for x in EXISTING:
        if x['cpm_type'] == cpm_type and x['cpm_additive'] and not x['name'].startswith(('p:', 'c:', 'g:')):
            return x


def staged_of(cpm_type):
    return {x['cpm_type']: x for x in EXISTING
            if x['name'] in ('p:' + cpm_type, 'p:' + cpm_type + '2') and x['cpm_type'] in ('setup', 'finish')}


def strip(anim, bones, channels=('rotation', 'position', 'scale')):
    for b in bones:
        u = UID[b]
        if u in anim['animators']:
            ks = [k for k in anim['animators'][u]['keyframes'] if k['channel'] not in channels]
            if ks:
                anim['animators'][u]['keyframes'] = ks
            else:
                del anim['animators'][u]


def tracks_json(an):
    j = an.to_json()
    out = {}
    for uid, anim in j['animators'].items():
        kfs = []
        for ch in ('rotation', 'position', 'scale'):
            ks = [k for k in anim['keyframes'] if k['channel'] == ch]
            if not ks:
                continue
            base = 1.0 if ch == 'scale' else 0.0
            if an.additive and max(abs(k['data_points'][0][a] - base) for k in ks for a in 'xyz') < EPS:
                continue
            kfs += ks
        if kfs:
            out[uid] = dict(anim, keyframes=kfs)
    return out


def merge_into(target, an):
    for uid, anim in tracks_json(an).items():
        if uid in target['animators']:
            have = {k['channel'] for k in target['animators'][uid]['keyframes']}
            target['animators'][uid]['keyframes'] += [k for k in anim['keyframes'] if k['channel'] not in have]
        else:
            target['animators'][uid] = anim


NEW = []


def emit(an):
    j = an.to_json()
    j['animators'] = tracks_json(an)
    NEW.append(j)


DELAY = {'body': 0.0, 'right_leg': 0.04, 'left_leg': 0.08, 'right_arm': 0.12, 'left_arm': 0.16, 'head': 0.22}


def weighted(kind, antic, over):
    if kind == 'setup':
        return curve([(0, 0), (0.2, -antic), (0.66, 1 + over), (0.84, 1 - 0.35 * over), (1, 1)])
    return curve([(0, 1), (0.14, 1 + 0.5 * antic), (0.64, -over), (0.84, 0.35 * over), (1, 0)])


def stage(cpm_type, an, antic=0.06, over=0.08):
    """additive tracks of `an` into the existing p:<pose> transitions"""
    for kind, target in staged_of(cpm_type).items():
        dur = target['length']
        w = weighted(kind, antic, over)
        tmp = Anim('tmp', kind, dur, loop='once')
        for bone, chans in an.tracks.items():
            d0 = DELAY.get(bone, 0.25) * dur
            u = (lambda d0: lambda t: max(0.0, min(1.0, (t - d0) / (dur - d0))))(d0)
            for ch in chans:
                v0 = an.value(bone, ch, 0.0)
                tmp.add(bone, ch, (lambda v0, u, w: lambda t: tuple(x * w(u(t)) for x in v0))(v0, u, w))
        merge_into(target, tmp)


def upper_at(x=0.0, y=0.0, z=0.0, drop=(0, 0, 0)):
    """torso rotated around the hips (body, arms and head follow), legs stay"""
    r = rig(torso=(x, y, z), drop=drop)
    return {b: r[b] for b in ('body', 'right_arm', 'left_arm', 'head')}


def lerp_cycle(points, L):
    """closed periodic curve through (phase 0..1, value) keys, eased; value at 1 == value at 0"""
    pts = sorted(points) + [(1.0, sorted(points)[0][1])]
    f = curve(pts)
    return lambda t: f((t / L) % 1.0)


# ================================================================== the walking / running cycle
PASSING = 0.31                                  # phase of the cycle where the right leg passes under the body


def shift(an, dt):
    """move the start of a loop by dt (the cycle itself is unchanged)"""
    for chans in an.tracks.values():
        for ch, fns in chans.items():
            chans[ch] = [(lambda f: lambda t: f(t + dt))(f) for f in fns]


def gait(name, cpm_type, L, legs_amp, arm_amp, twist, bob, roll, lean, arm_fwd, arm_out, head_fix,
         lift=0.0, tail_x=0.0, extra_corpo=None):
    """non-additive limbs + additive body for one locomotion cycle of length L (phase 0 = right leg forward)"""
    # leg: forward swing is quick (foot lifted), the push back under the body is slower and planted
    leg_shape = [(0.0, 1.0), (0.12, 0.92), (0.5, -1.0), (0.62, -0.92), (0.82, 0.25)]
    leg = lerp_cycle(leg_shape, L)
    arm = lerp_cycle([(0.0, -1.0), (0.1, -1.04), (0.5, 1.0), (0.6, 1.04)], L)      # opposite to the same-side leg
    ph = lambda t, p: (t + p * L)
    walk = Anim(name + ' - passos', cpm_type, L, additive=False, priority=P_WALK)
    walk.rot('right_leg', lambda t: (legs_amp * leg(t), 0.0, 0.0))
    walk.rot('left_leg', lambda t: (legs_amp * leg(ph(t, 0.5)), 0.0, 0.0))
    lag = 0.06                                                    # arms follow the shoulders a little later

    def tw(t):                                                    # shoulder twist: right shoulder forward with the right arm
        return twist * arm(t - lag * L * 0.5)

    walk.rot('right_arm', lambda t: (arm_fwd + arm_amp * arm(t - lag * L), tw(t), arm_out + 1.5 * max(0.0, arm(t - lag * L))))
    walk.rot('left_arm', lambda t: (arm_fwd + arm_amp * arm(ph(t, 0.5) - lag * L), tw(t), -arm_out - 1.5 * max(0.0, arm(ph(t, 0.5) - lag * L))))
    # legs open a little sideways while swinging through (feet do not cross)
    walk.rot('right_leg', lambda t: (0.0, 0.0, lift * max(0.0, math.sin(2 * math.pi * (t / L - 0.25)))))
    walk.rot('left_leg', lambda t: (0.0, 0.0, -lift * max(0.0, math.sin(2 * math.pi * (t / L + 0.25)))))

    corpo = Anim(name + ' - corpo', cpm_type, L)
    bob_f = lambda t: bob * math.cos(4 * math.pi * (t / L) - 0.6)     # lowest just after each contact (phase 0, 0.5)
    roll_f = lambda t: roll * math.sin(2 * math.pi * (t / L - 0.08))  # weight rolls onto the stance leg
    memo = {}

    def at(t):
        k = round(t, 4)
        if k not in memo:
            memo[k] = upper_at(lean, tw(t), roll_f(t), drop=(0, -abs(bob) + bob_f(t), 0))
        return memo[k]
    for b in ('body', 'right_arm', 'left_arm', 'head'):
        corpo.pos(b, (lambda b: lambda t: tuple(at(t)[b][1]))(b))
    corpo.rot('body', lambda t: tuple(at(t)['body'][0]))
    # head: keeps the look steady (cancels most of the twist / roll / lean, a moment later)
    corpo.rot('head', lambda t: (head_fix - 0.15 * lean + 1.2 * bob_f(t - 0.04 * L) / max(abs(bob), 1e-6) * 0.6,
                                 -0.6 * tw(t - 0.05 * L), -0.7 * roll_f(t - 0.05 * L)))
    if tail_x:
        corpo.rot('cauda', c((tail_x, 0.0, 0.0)))
    if extra_corpo:
        extra_corpo(corpo)
    # start the loop on the passing pose (legs together, arms down): entering the pose, or coming back to it after
    # a jump, then starts where the vanilla swing also is, instead of snapping to a stretched stride
    for an in (walk, corpo):
        shift(an, PASSING * L)
    return walk, corpo


def install(cpm_type, walk, corpo, antic=0.06, over=0.08, strip_extra=()):
    main = main_of(cpm_type)
    strip(main, BODY + tuple(strip_extra))
    for st in staged_of(cpm_type).values():
        strip(st, BODY + tuple(strip_extra))
    for an in (walk, corpo):
        emit(an)
    stage(cpm_type, corpo, antic, over)


def posture(cpm_type, name, lean=0.0, arms=(0.0, 0.0), arm_y=0.0, head=0.0, legs_z=0.0, antic=0.06, over=0.06):
    """static additive posture over the vanilla swing (it never restarts or moves on its own)"""
    main = main_of(cpm_type)
    strip(main, BODY)
    for st in staged_of(cpm_type).values():
        strip(st, BODY)
    a = Anim(name, cpm_type, main['length'])
    up = upper_at(lean)
    a.rot('body', c(up['body'][0])).pos('body', c(up['body'][1]))
    a.pos('head', c(up['head'][1])).rot('head', c((head, 0.0, 0.0)))
    for b, sgn in (('right_arm', 1), ('left_arm', -1)):
        a.rot(b, c(add3(up[b][0], (arms[0], 0.0, sgn * arms[1]))))
        a.pos(b, c(add3(up[b][1], (0.0, arm_y, 0.0))))
    if legs_z:
        a.rot('right_leg', c((0.0, 0.0, legs_z))).rot('left_leg', c((0.0, 0.0, -legs_z)))
    emit(a)
    stage(cpm_type, a, antic, over)


# walking: CPM detects walking from the position change between frames and re-enters the pose all the time, so a
# cycle of our own would keep restarting: walking keeps the vanilla swing (synced, never restarts) + posture
def lively_walk():
    """Walking stays on the vanilla swing (it is the only thing that never restarts), and on top of it an additive,
    restart-safe layer gives it life: the body bobs twice per stride, rolls onto the stance side and twists the
    shoulders, the arms swing out and back sideways, the head stabilises a moment later. Everything fades in over
    0.3 s from zero, so if CPM re-enters the walking pose the layer just blends in again instead of snapping; the
    loop is long (48 strides) and fades through zero at its seam."""
    main = main_of('walking')
    strip(main, BODY)
    # no entry/exit stage for walking: in CPM the main animations only start after the entry, and the walking pose
    # is re-entered often, so the entry kept the layer from ever showing; the layer fades in by itself instead
    for st in staged_of('walking').values():
        EXISTING.remove(st)
    S = 0.55                                        # Minecraft walking stride (same tempo as the vanilla swing)
    L = S * 48
    a = Anim('Andando - corpo solto', 'walking', L)
    amp = lambda t: smooth(t / 0.15) * smooth((L - t) / 0.15)
    w = lambda per, ph=0.0: (lambda t: math.sin(2 * math.pi * (t / per + ph)))
    bob = lambda t: amp(t) * 0.5 * (1 - math.cos(4 * math.pi * t / S))          # 0..1, twice per stride
    roll, twist = w(S, 0.0), w(S, 0.25)
    memo = {}

    def at(t):
        k = round(t, 4)
        if k not in memo:
            m = amp(t)
            memo[k] = upper_at(-4 * smooth(t / 0.15) - 1.8 * bob(t), 8.0 * m * twist(t), 3.5 * m * roll(t),
                               drop=(0, -0.8 * bob(t), 0))
        return memo[k]
    for b in ('body', 'right_arm', 'left_arm', 'head'):
        a.pos(b, (lambda b: lambda t: tuple(at(t)[b][1]))(b))
    a.rot('body', lambda t: tuple(at(t)['body'][0]))
    # arms: hang off the body, swing out / in and twist with the shoulders (follow-through: a little later)
    a.rot('right_arm', lambda t: add3(at(t)['right_arm'][0], (3 * amp(t), -5 * amp(t) * twist(t - 0.06),
                                                            amp(t) * (5 + 6 * w(S, 0.1)(t)))))
    a.rot('left_arm', lambda t: add3(at(t)['left_arm'][0], (3 * amp(t), -5 * amp(t) * twist(t - 0.06),
                                                           -amp(t) * (5 - 6 * w(S, 0.1)(t)))))
    # head: keeps the look steady, cancels most of the twist / roll a little later, nods with the steps
    a.rot('head', lambda t: (amp(t) * (2.5 + 1.6 * bob(t - 0.05)), -5.5 * amp(t) * twist(t - 0.05),
                             -2.5 * amp(t) * roll(t - 0.05)))
    # legs: hips roll with the weight, legs open a little at each passing
    a.rot('right_leg', lambda t: (0.0, 0.0, amp(t) * (1.5 + 2.5 * w(S, 0.25)(t))))
    a.rot('left_leg', lambda t: (0.0, 0.0, -amp(t) * (1.5 - 2.5 * w(S, 0.25)(t))))
    emit(a)


lively_walk()
# running: sprint stride is 0.47 s (Minecraft caps the limb speed), bigger and bouncier, leaning forward
w, cp = gait('Correndo', 'running', 0.47, legs_amp=52, arm_amp=40, twist=9, bob=0.6, roll=2.2, lean=-12,
             arm_fwd=12, arm_out=5, head_fix=10, lift=2.0, tail_x=20)
install('running', w, cp, antic=0.0, over=0.0)
# sneak walk: same reason as walking (moving detection) -> posture: paws low and forward, shoulders down
posture('sneak_walk', 'Agachado andando - postura', arms=(12.0, 4.0), arm_y=-1.0, head=8.0)

# ================================================================== standing sneak: crouched, alert
sn = main_of('sneaking')
strip(sn, BODY)
for st in staged_of('sneaking').values():
    strip(st, BODY)
a = Anim('Agachado - corpo', 'sneaking', sn['length'])
br = lambda t: math.sin(2 * math.pi * t / sn['length'])
a.rot('right_arm', lambda t: (17 + 1.0 * br(t - 0.1), 0.0, 5.0)).rot('left_arm', lambda t: (14 + 1.0 * br(t - 0.15), 0.0, -5.0))
for b in ('right_arm', 'left_arm'):
    a.pos(b, lambda t: (0.0, -1.0 + 0.12 * br(t), 0.0))            # shoulders low, breathing
a.rot('body', lambda t: (0.6 * br(t), 0.0, 0.7 * math.sin(2 * math.pi * t / sn['length'] + 1.0)))
a.rot('head', lambda t: (10.0, 0.0, -0.4 * math.sin(2 * math.pi * t / sn['length'] + 0.7)))
a.rot('right_leg', c((-2.0, 0.0, 2.0))).rot('left_leg', c((4.0, 0.0, -2.0)))  # feet apart, one a bit ahead
emit(a)
stage('sneaking', a, 0.08, 0.06)

# ================================================================== crawling / swimming
# These poses stay on while you are lying still, so nothing here may move by itself: the vanilla swim/crawl strokes
# (they only move when you move) + a static posture.
posture('crawling', 'Rastejando - postura', head=16.0, legs_z=5.0)
posture('swimming', 'Nadando - postura', head=12.0, legs_z=4.0)

# ================================================================== jumping: legs and arms driven
jm = main_of('jumping')
strip(jm, LIMBS[2:])                                             # the arms keep their additive swing (items keep working)
for st in staged_of('jumping').values():
    strip(st, LIMBS[2:])
J = Anim('Pulando - pernas', 'jumping', jm['length'], additive=False, priority=P_WALK)
push_ = curve([(0, 1.0), (0.07, 1.0), (0.18, 0.0), (0.6, 0.0)])
tuck_r = curve([(0, 0.0), (0.05, 0.0), (0.19, 1.06), (0.29, 0.94), (0.44, 0.22), (0.6, 0.15)])
tuck_l = curve([(0, 0.0), (0.09, 0.0), (0.24, 1.08), (0.33, 0.9), (0.47, 0.28), (0.6, 0.2)])
reach_dn = curve([(0, 0.0), (0.3, 0.0), (0.46, 1.0), (0.6, 1.0)])
J.rot('right_leg', lambda t: (-14 * push_(t) + 36 * tuck_r(t) + 4 * reach_dn(t), 0.0, 2 * tuck_r(t)))
J.rot('left_leg', lambda t: (-10 * push_(t) + 26 * tuck_l(t) - 3 * reach_dn(t), 0.0, -2 * tuck_l(t)))
emit(J)

# ================================================================== turning: legs follow and step out
turn = main_of('head_rotation_yaw')
strip(turn, LIMBS[2:])
a = Anim('tmp_turn', 'head_rotation_yaw', turn['length'])
yaw = lambda t: 90 - 180 * t                                    # + = head turned left
a.rot('right_leg', lambda t: (8 * max(0.0, -yaw(t)) / 90, 0.15 * yaw(t), 3 * max(0.0, -yaw(t)) / 90))   # steps out to the right
a.rot('left_leg', lambda t: (8 * max(0.0, yaw(t)) / 90, 0.15 * yaw(t), -3 * max(0.0, yaw(t)) / 90))     # steps out to the left
merge_into(turn, a)


# ================================================================== item poses (they replace the walking arms)
def item(name, cpm_type, poses, value=False):
    """static (or value-driven) non-additive arm pose; poses: {arm: (rot) or fn(t)->rot}"""
    an = Anim(name, cpm_type, 1.0, additive=False, priority=P_ITEM)
    for b, r in poses.items():
        an.rot(b, r if callable(r) else c(tuple(r)))
    emit(an)


# attack: the swinging arm follows the vanilla swing curve (+ our wind-up / reach), non-additive
def vanilla_swing(f):
    """vanilla attack arm (model convention, degrees) at attack progress f"""
    g = 1 - (1 - f) ** 4
    f2 = math.sin(g * math.pi)
    f3 = math.sin(f * math.pi) * 0.7 * 0.75
    body_y = math.sin(math.sqrt(max(f, 0)) * 2 * math.pi) * 0.2
    return math.degrees(f2 * 1.2 + f3), -math.degrees(2 * body_y), -math.degrees(math.sin(f * math.pi) * 0.4)


for side, s in (('right', 1), ('left', -1)):
    me = side + '_arm'
    pa = main_of('punch_' + side)
    strip(pa, (me,))
    reach_k = curve([(0, 0), (0.12, -0.6), (0.34, 1.1), (0.5, 0.9), (0.75, 0.15), (1.0, 0)])
    an = Anim(pa['name'] + ' - braco', 'punch_' + side, 1.0, additive=False, priority=P_PUNCH)
    an.rot(me, lambda t, s=s: (vanilla_swing(t)[0] + 14 * reach_k(t), s * vanilla_swing(t)[1], vanilla_swing(t)[2]))
    emit(an)

# ------------------------------------------------------------------ short entries
# In CPM the main animations of a pose only start after its entry transition (p:<pose> setup); meanwhile the vanilla
# swing shows, and every new entry (after each jump, for example) snapped back to the start. The entries of the
# driven states are now very short, so the cycles start right away.
def stretch(anim, new_len):
    f = new_len / anim['length']
    for a in anim['animators'].values():
        for k in a['keyframes']:
            k['time'] = round(k['time'] * f, 4)
    anim['length'] = new_len


for typ, dur in (('running', 0.1), ('jumping', 0.05)):
    st = staged_of(typ)
    if 'setup' in st:
        stretch(st['setup'], dur)

# ------------------------------------------------------------------ save
order = {}
for x in EXISTING:
    order[x['cpm_type']] = order.get(x['cpm_type'], 0) + 1
for x in NEW:
    x['cpm_order'] = order.get(x['cpm_type'], 0)
    order[x['cpm_type']] = order.get(x['cpm_type'], 0) + 1
    if x['cpm_type'] in ('bow_left', 'bow_right', 'crossbow_ch_left', 'crossbow_ch_right', 'punch_left', 'punch_right'):
        x['loop'] = 'loop'                                      # value-driven: CPM wants them looping
d['animations'] = EXISTING + NEW
json.dump(d, open(OUT, 'w'))
print('ok: %d new animations' % len(NEW))
