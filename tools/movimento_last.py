"""L.A.S.T only: looser, softer body motion for running, jumping/falling, swimming, flying, and turning.

usage: python3 tools/movimento_last.py <skin_v16.29_LAST.bbmodel> <skin_v16.30_LAST.bbmodel>

Replaces the body tracks that tools/movimento.py put in these states (tail, ears, fur and everything else stay):
- Running: deep forward lean that breathes, slow organic sway of the torso (roll/yaw) with the head stabilising a bit
  later, arms loose and slightly out; softer start (small lean back, then forward past the pose, settle) and stop.
- Turning: the "head turned" value animation now also twists the torso and shoulders toward where you look (the legs
  stay planted), and looking up/down tilts the torso a little; tail and ears already followed.
- Jumping: push (arms swing up), tuck with the two legs out of step, apex, legs reach for the ground and the head
  looks down; the leave transition is a real landing (upper body dips, arms swing forward, rebound, settle).
- Falling: slower, looser flailing with overlap between arms and legs.
- Swimming: body rolls with the strokes, head stays level, legs flutter one after the other.
- Elytra: arms back like wings with slow flutter, legs trailing, small roll; creative flight: hovering bob with
  dangling legs and floating arms.
The vanilla arm/leg swing stays underneath (synced to speed; no pops when sprinting, jumping or stopping).
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
BODY_UUID = {GRP[b]['uuid'] for b in BODY}
EPS = 0.05


# ------------------------------------------------------------------ file helpers
def main_of(cpm_type):
    for x in EXISTING:
        if x['cpm_type'] == cpm_type and x['cpm_additive'] and not x['name'].startswith(('p:', 'c:', 'g:')):
            return x


def staged_of(cpm_type):
    return {x['cpm_type']: x for x in EXISTING
            if x['name'] in ('p:' + cpm_type, 'p:' + cpm_type + '2') and x['cpm_type'] in ('setup', 'finish')}


def strip_body(anim):
    for u in list(anim['animators']):
        if u in BODY_UUID:
            del anim['animators'][u]


def tile(anim, n):
    """make a loop n times longer by repeating its keyframes (keeps the existing motion identical)"""
    L = anim['length']
    for a in anim['animators'].values():
        out = []
        for ch in ('rotation', 'position', 'scale'):
            ks = sorted([k for k in a['keyframes'] if k['channel'] == ch], key=lambda k: k['time'])
            if not ks:
                continue
            if len(ks) == 1:
                out += ks
                continue
            body = [k for k in ks if k['time'] < L - 1e-6]
            last = ks[-1]
            for i in range(n):
                for k in body:
                    out.append(dict(copy.deepcopy(k), time=round(k['time'] + i * L, 4), uuid=str(uuid.uuid4())))
            out.append(dict(copy.deepcopy(last), time=round(last['time'] + (n - 1) * L, 4), uuid=str(uuid.uuid4())))
        a['keyframes'] = out
    anim['length'] = round(L * n, 4)


def stretch(anim, new_len):
    f = new_len / anim['length']
    for a in anim['animators'].values():
        for k in a['keyframes']:
            k['time'] = round(k['time'] * f, 4)
    anim['length'] = new_len


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
            if max(abs(k['data_points'][0][a] - base) for k in ks for a in 'xyz') < EPS:
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


DELAY = {'body': 0.0, 'right_leg': 0.04, 'left_leg': 0.08, 'right_arm': 0.12, 'left_arm': 0.16, 'head': 0.22}


def weighted(kind, antic, over):
    if kind == 'setup':
        return curve([(0, 0), (0.2, -antic), (0.66, 1 + over), (0.84, 1 - 0.35 * over), (1, 1)])
    return curve([(0, 1), (0.14, 1 + 0.5 * antic), (0.64, -over), (0.84, 0.35 * over), (1, 0)])


def stage(cpm_type, an, antic, over, start=0.0, finish_fn=None):
    """body tracks into the existing p:<pose> transitions (setup eases in to the pose at t=0, finish eases out
    from the pose at `start`, or uses finish_fn(bone, ch, v0) -> f(t) for a custom leave)"""
    st = staged_of(cpm_type)
    for kind in ('setup', 'finish'):
        target = st[kind]
        dur = target['length']
        w = weighted(kind, antic, over)
        tmp = Anim('tmp', kind, dur, loop='once')
        for bone, chans in an.tracks.items():
            if bone not in BODY:
                continue
            d0 = DELAY.get(bone, 0.25) * dur
            u = (lambda d0: lambda t: max(0.0, min(1.0, (t - d0) / (dur - d0))))(d0)
            for ch in chans:
                v0 = an.value(bone, ch, 0.0 if kind == 'setup' else start)
                if kind == 'finish' and finish_fn is not None:
                    tmp.add(bone, ch, finish_fn(bone, ch, v0, dur))
                else:
                    tmp.add(bone, ch, (lambda v0, u, w: lambda t: tuple(x * w(u(t)) for x in v0))(v0, u, w))
        if kind == 'finish' and finish_fn is not None:
            for bone, ch, fn in getattr(finish_fn, 'extra', lambda dur: [])(dur):
                if bone not in tmp.tracks or ch not in tmp.tracks[bone]:
                    tmp.add(bone, ch, fn)
        merge_into(target, tmp)


def wave(an, period, phase=0.0):
    n = max(1, round(an.length / period))
    return lambda t: math.sin(2 * math.pi * (n * t / an.length + phase))


def upper(x=0.0, y=0.0, z=0.0, head=True):
    """torso turned around the hips by euler (x, y, z): body + arms follow (rotation and shoulder position),
    the head moves with the neck but keeps its own (vanilla) look direction unless head=True"""
    r = rig(torso=(x, y, z))
    out = {b: r[b] for b in ('body', 'right_arm', 'left_arm')}
    out['head'] = (r['head'][0] if head else Z3, r['head'][1])
    return out


def drive(an, fn, bones=('body', 'right_arm', 'left_arm', 'head'), extra=None):
    """tracks from a per-time pose function fn(t) -> {bone: (rot, pos)}; extra(t) -> {bone: rot} added on top"""
    memo = {}

    def at(t):
        k = round(t, 4)
        if k not in memo:
            p = fn(t)
            if extra:
                for b, r in extra(t).items():
                    rr, pp = p.get(b, (Z3, Z3))
                    p[b] = (add3(rr, r), pp)
            memo[k] = p
        return memo[k]
    for b in bones:
        an.rot(b, (lambda b: lambda t: tuple(at(t).get(b, (Z3, Z3))[0]))(b))
        an.pos(b, (lambda b: lambda t: tuple(at(t).get(b, (Z3, Z3))[1]))(b))


def new_anim(cpm_type, length):
    a = Anim('__' + cpm_type, cpm_type, length)
    return a


TARGETS = ('running', 'jumping', 'falling', 'swimming', 'flying', 'creative_flying')
for typ in TARGETS:
    strip_body(main_of(typ))
    for x in staged_of(typ).values():
        strip_body(x)

# ================================================================== running
run = main_of('running')
tile(run, 4)                                            # 0.5 s -> 2 s: room for slow, organic variation
stretch(staged_of('running')['setup'], 0.45)
stretch(staged_of('running')['finish'], 0.5)
a = new_anim('running', run['length'])
breathe = wave(a, 1.0)                                  # the lean breathes once per second
sway = wave(a, 2.0)
sway2 = wave(a, 2.0, 0.27)


def run_pose(t):
    p = upper(-12 + 1.3 * breathe(t), 2.2 * sway2(t), 1.8 * sway(t), head=False)
    late = upper(-12 + 1.3 * breathe(t - 0.12), 2.2 * sway2(t - 0.12), 1.8 * sway(t - 0.12), head=False)
    # head looks ahead: cancels most of the lean / roll, a little later than the torso (it stabilises)
    p['head'] = ((10.5 - 0.9 * breathe(t - 0.12), -1.4 * sway2(t - 0.12), -1.2 * sway(t - 0.12)), p['head'][1])
    return p


drive(a, run_pose, extra=lambda t: {
    'right_arm': (9 + 2.5 * wave(a, 1.0, -0.15)(t), 0.0, 6.5 + 1.5 * wave(a, 2.0, -0.1)(t)),
    'left_arm': (9 + 2.5 * wave(a, 1.0, -0.2)(t), 0.0, -6.5 - 1.5 * wave(a, 2.0, 0.17)(t))})
a.rot('right_leg', lambda t: (-3.5, 0.0, 1.0 + 0.8 * wave(a, 2.0, 0.05)(t)))
a.rot('left_leg', lambda t: (-3.5, 0.0, -1.0 + 0.8 * wave(a, 2.0, 0.05)(t)))
merge_into(run, a)
stage('running', a, antic=0.06, over=0.1)

# ================================================================== turning (value: 0 = head turned left .. 1 = right)
turn = main_of('head_rotation_yaw')
strip_body(turn)
a = new_anim('head_rotation_yaw', turn['length'])
yaw = lambda t: 90 - 180 * t                            # head yaw relative to the body, + = to the left
drive(a, lambda t: upper(0.0, 0.3 * yaw(t), 0.0, head=False), bones=('body', 'right_arm', 'left_arm'))
a.rot('right_leg', lambda t: (0.0, 0.06 * yaw(t), 0.0)).rot('left_leg', lambda t: (0.0, 0.06 * yaw(t), 0.0))
merge_into(turn, a)

look = main_of('head_rotation_pitch')
strip_body(look)
a = new_anim('head_rotation_pitch', look['length'])
pitch = lambda t: 180 * t - 90                          # + = looking down
drive(a, lambda t: upper(-0.1 * pitch(t), 0.0, 0.0, head=False))
merge_into(look, a)

# ================================================================== jumping (pose lasts 0.5 s after the jump)
jump = main_of('jumping')
stretch(staged_of('jumping')['finish'], 0.42)           # leaving the jump = the landing
a = new_anim('jumping', jump['length'])
push = curve([(0, 0.0), (0.07, 1.0), (0.2, 0.25), (0.34, 0.0), (0.6, 0.0)])
tuck_r = curve([(0, 0.0), (0.06, 0.0), (0.2, 1.06), (0.3, 0.92), (0.44, 0.25), (0.6, 0.2)])
tuck_l = curve([(0, 0.0), (0.1, 0.0), (0.25, 1.08), (0.34, 0.9), (0.48, 0.3), (0.6, 0.25)])
float_ = curve([(0, 0.0), (0.12, 0.3), (0.3, 1.0), (0.46, 0.85), (0.6, 0.8)])
look_dn = curve([(0, 0.0), (0.2, -0.4), (0.36, 0.6), (0.5, 1.0), (0.6, 1.0)])


def jump_pose(t):
    # a light forward lean of its own, so a sprint-jump keeps leaning instead of standing up at every jump
    # it builds up during the jump, crossfading with the sprint lean that is fading out
    return upper(-6 * smooth(t / 0.28) - 4 * push(t) + 1 * float_(t) - 2 * look_dn(t), 0.0, 0.0)


drive(a, jump_pose, bones=('body', 'right_arm', 'left_arm'), extra=lambda t: {
    'right_arm': (24 * push(t) + 6 * float_(t), 0.0, 8 * push(t) + 20 * float_(t)),
    'left_arm': (20 * push(max(0, t - 0.03)) + 5 * float_(t - 0.03), 0.0, -8 * push(t - 0.03) - 22 * float_(t - 0.03))})
a.rot('right_leg', lambda t: (-12 * push(t) + 30 * tuck_r(t), 0.0, 1.5 * float_(t)))
a.rot('left_leg', lambda t: (-9 * push(t) + 20 * tuck_l(t), 0.0, -1.5 * float_(t)))
a.rot('head', lambda t: (5 * float_(t) - 14 * look_dn(t), 0.0, 0.0))
merge_into(jump, a)
END = 0.5


def landing(bone, ch, v0, dur):
    """from the jump pose at 0.5 s: impact (upper body dips and leans, arms swing forward), rebound, settle"""
    ease_out = curve([(0, 1), (0.35, 0.0), (1, 0)])
    if bone in ('body', 'right_arm', 'left_arm', 'head') and ch == 'position':
        dip = curve([(0, 0), (0.18, 1.0), (0.42, -0.25), (0.66, 0.08), (1, 0)])
        return lambda t: tuple(x * ease_out(t / dur) + y for x, y in zip(v0, (0.0, -0.9 * dip(t / dur), -0.15 * dip(t / dur))))
    if bone == 'body' and ch == 'rotation':
        lean_ = curve([(0, 0), (0.2, 1.0), (0.45, -0.3), (0.7, 0.08), (1, 0)])
        return lambda t: tuple(x * ease_out(t / dur) + y for x, y in zip(v0, (-5 * lean_(t / dur), 0.0, 0.0)))
    if bone in ('right_arm', 'left_arm') and ch == 'rotation':
        s = 1 if bone == 'right_arm' else -1
        sw = curve([(0, 0), (0.24, 1.0), (0.5, -0.3), (0.74, 0.08), (1, 0)])
        return lambda t: tuple(x * ease_out(t / dur) + y for x, y in zip(v0, (12 * sw(t / dur - 0.05), 0.0, 6 * s * sw(t / dur - 0.05))))
    if bone == 'head' and ch == 'rotation':
        nod = curve([(0, 0), (0.26, 1.0), (0.52, -0.35), (0.78, 0.1), (1, 0)])
        return lambda t: tuple(x * ease_out(t / dur) + y for x, y in zip(v0, (-6 * nod(t / dur - 0.08), 0.0, 0.0)))
    return lambda t: tuple(x * ease_out(t / dur) for x in v0)


landing.extra = lambda dur: [(b, 'position', landing(b, 'position', Z3, dur)) for b in ('body', 'right_arm', 'left_arm', 'head')] + \
    [('head', 'rotation', landing('head', 'rotation', Z3, dur))]
stage('jumping', a, antic=0.0, over=0.0, start=END, finish_fn=landing)

# ================================================================== falling (long falls)
fall = main_of('falling')
tile(fall, 4)                                           # 0.3 -> 1.2 s: slower, looser flailing
a = new_anim('falling', fall['length'])
fr, fl = wave(a, 0.6), wave(a, 0.6, -0.22)
gr, gl = wave(a, 0.4, 0.1), wave(a, 0.4, -0.15)
a.rot('right_arm', lambda t: (10 + 9 * fr(t) + 3 * gr(t), 0.0, 52 + 8 * fr(t - 0.05)))
a.rot('left_arm', lambda t: (10 + 9 * fl(t) + 3 * gl(t), 0.0, -50 - 8 * fl(t - 0.05)))
a.rot('right_leg', lambda t: (10 + 9 * wave(a, 0.6, 0.3)(t), 0.0, 4 + 2 * wave(a, 1.2, 0.1)(t)))
a.rot('left_leg', lambda t: (-4 + 9 * wave(a, 0.6, 0.55)(t), 0.0, -4 - 2 * wave(a, 1.2, 0.35)(t)))
a.rot('body', lambda t: (4.0, 2 * wave(a, 1.2)(t), 1.5 * wave(a, 1.2, 0.25)(t)))
a.rot('head', lambda t: (-14 + 3 * wave(a, 0.6, -0.1)(t), -1.2 * wave(a, 1.2, -0.1)(t), -1.0 * wave(a, 1.2, 0.15)(t)))
merge_into(fall, a)
stage('falling', a, antic=0.12, over=0.12)

# ================================================================== swimming
swim = main_of('swimming')
a = new_anim('swimming', swim['length'])
roll = wave(a, swim['length'])
a.rot('body', lambda t: (0.0, 2.5 * wave(a, swim['length'], 0.25)(t), 6 * roll(t)))
a.rot('head', lambda t: (14.0, -1.5 * wave(a, swim['length'], 0.17)(t), -4.2 * wave(a, swim['length'], -0.08)(t)))
for leg, ph, zz in (('right_leg', 0.0, 3.0), ('left_leg', 0.5, -3.0)):    # flutter kick, one leg after the other
    a.rot(leg, (lambda ph, zz: lambda t: (9 * wave(a, swim['length'] / 2, ph - 0.1)(t), 0.0, zz + 2 * roll(t - 0.1)))(ph, zz))
a.rot('right_arm', lambda t: (0.0, 0.0, 3 + 2 * roll(t - 0.08)))
a.rot('left_arm', lambda t: (0.0, 0.0, -3 + 2 * roll(t - 0.12)))
merge_into(swim, a)
stage('swimming', a, antic=0.08, over=0.08)

# ================================================================== elytra
fly = main_of('flying')
tile(fly, 4)                                            # 0.4 -> 1.6 s
a = new_anim('flying', fly['length'])
a.rot('right_arm', lambda t: (-24 + 2 * wave(a, 0.8)(t), 0.0, 14 + 2.5 * wave(a, 1.6, 0.1)(t)))
a.rot('left_arm', lambda t: (-24 + 2 * wave(a, 0.8, -0.12)(t), 0.0, -14 - 2.5 * wave(a, 1.6, 0.22)(t)))
a.rot('right_leg', lambda t: (-6 + 2.5 * wave(a, 0.4)(t), 0.0, 2.5 + wave(a, 1.6, 0.3)(t)))
a.rot('left_leg', lambda t: (-8 + 2.5 * wave(a, 0.4, 0.4)(t), 0.0, -2.5 - wave(a, 1.6, 0.45)(t)))
a.rot('body', lambda t: (0.0, 0.0, 1.6 * wave(a, 1.6)(t)))
a.rot('head', lambda t: (12.0, 0.0, -1.0 * wave(a, 1.6, -0.08)(t)))
merge_into(fly, a)
stage('flying', a, antic=0.1, over=0.1)

# ================================================================== creative flight: hovering
cf = main_of('creative_flying')
a = new_anim('creative_flying', cf['length'])
hover = wave(a, cf['length'])
for b in BODY:                                          # whole body bobs, limbs answer later
    lag = {'body': 0, 'head': 0.05, 'right_arm': 0.08, 'left_arm': 0.1, 'right_leg': 0.14, 'left_leg': 0.17}[b]
    a.pos(b, (lambda lag: lambda t: (0.0, 0.45 * wave(a, cf['length'], -lag)(t), 0.0))(lag))
a.rot('right_leg', lambda t: (9 + 6 * wave(a, cf['length'], -0.16)(t), 0.0, 2.5))
a.rot('left_leg', lambda t: (-2 + 6 * wave(a, cf['length'], -0.34)(t), 0.0, -2.5))
a.rot('right_arm', lambda t: (5 + 2 * wave(a, cf['length'], -0.1)(t), 0.0, 10 + 3 * wave(a, cf['length'], -0.12)(t)))
a.rot('left_arm', lambda t: (5 + 2 * wave(a, cf['length'], -0.14)(t), 0.0, -10 - 3 * wave(a, cf['length'], -0.18)(t)))
a.rot('body', lambda t: (1.2 * wave(a, cf['length'], -0.03)(t), 0.0, 0.8 * wave(a, cf['length'] / 2, 0.2)(t)))
a.rot('head', lambda t: (-1.0 * wave(a, cf['length'], -0.08)(t), 0.0, 0.0))
merge_into(cf, a)
stage('creative_flying', a, antic=0.06, over=0.08)

json.dump(d, open(OUT, 'w'))
print('ok')
