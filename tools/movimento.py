"""Body animation for every movement state (CPM has no texture-pack animations: vanilla only swings arms/legs).

usage: python3 tools/movimento.py <model.bbmodel> <out.bbmodel>

How it combines with Minecraft:
- The vanilla arm/leg swing (walking, running, swimming strokes) stays: it is the only thing synced to the real
  speed and it keeps every item pose working (bow following the aim, shield, crossbow, spyglass...).
  On top of it (additive) come posture, weight, anticipation, follow-through and secondary motion.
- Where vanilla does nothing (jump, fall, eat, hurt, ladder, elytra, sleeping, fire, freezing...) the whole body is
  animated here.
- The attack is driven by the swing itself (CPM plays the punch animation with the attack progress), so wind-up,
  strike, follow-through and settle stay synced to every hit.
Existing animations are kept: the new body tracks are added into the same pose animations (tail, ears and fur
keep their current motion) and into their p:<pose> enter/leave transitions, so nothing snaps.
"""
import json, sys, os, math, uuid
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
assert len(d['groups']) == n_groups
EXISTING = d['animations']
BODY = ('head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg')
EPS = 0.05                                       # channels that never move more than this are left out


def main_of(cpm_type):
    """the existing additive animation of a pose (not the eyelid / ear helpers)"""
    for x in EXISTING:
        if x['cpm_type'] == cpm_type and x['cpm_additive'] and not x['name'].startswith(('p:', 'c:', 'g:')):
            return x
    return None


def staged_of(cpm_type):
    # Blockbench renames a repeated name on load ('p:walking' finish -> 'p:walking2'): accept both
    return {x['cpm_type']: x for x in EXISTING
            if x['name'] in ('p:' + cpm_type, 'p:' + cpm_type + '2') and x['cpm_type'] in ('setup', 'finish')}


def ease_curve(antic=0.0, over=0.0):
    return (curve([(0, 0), (0.2, -antic), (0.68, 1 + over), (0.86, 1 - 0.3 * over), (1, 1)]),
            curve([(0, 1), (0.14, 1 + 0.5 * antic), (0.66, -over), (0.86, 0.3 * over), (1, 0)]))


DELAY = {'body': 0.0, 'right_leg': 0.0, 'left_leg': 0.0, 'right_arm': 0.1, 'left_arm': 0.14, 'head': 0.2}


def tracks_json(an):
    """animators of an Anim, without channels that do (almost) nothing"""
    j = an.to_json()
    out = {}
    for uid, anim in j['animators'].items():
        kfs = []
        for ch in ('rotation', 'position', 'scale'):
            ks = [k for k in anim['keyframes'] if k['channel'] == ch]
            if not ks:
                continue
            base = 1.0 if ch == 'scale' else 0.0
            if max(abs(k['data_points'][0][a] - base) for k in ks for a in 'xyz') < (0.004 if ch == 'scale' else EPS):
                continue
            kfs += ks
        if kfs:
            out[uid] = dict(anim, keyframes=kfs)
    return out


def merge_into(target, an):
    """add the body tracks of `an` to an existing animation (never replacing what is there)"""
    for uid, anim in tracks_json(an).items():
        if uid in target['animators']:
            have = {k['channel'] for k in target['animators'][uid]['keyframes']}
            target['animators'][uid]['keyframes'] += [k for k in anim['keyframes'] if k['channel'] not in have]
        else:
            target['animators'][uid] = anim


def stage(cpm_type, an, antic=0.08, over=0.06):
    """enter / leave of the new tracks inside the existing p:<pose> transitions (or new ones)"""
    st = staged_of(cpm_type)
    for kind in ('setup', 'finish'):
        dur = st[kind]['length'] if kind in st else 0.3
        w_in, w_out = ease_curve(antic, over)
        w = w_in if kind == 'setup' else w_out
        tmp = Anim('tmp', kind, dur, loop='once')
        for bone, chans in an.tracks.items():
            d0 = DELAY.get(bone, 0.25) * dur
            u = (lambda d0: lambda t: max(0.0, min(1.0, (t - d0) / (dur - d0))))(d0)
            for ch in chans:
                v0 = an.value(bone, ch, 0.0)
                if ch == 'scale':
                    s = (lambda u, k: lambda t: smooth(u(t)) if k == 'setup' else 1 - smooth(u(t)))(u, kind)
                    tmp.add(bone, ch, (lambda v0, s: lambda t: tuple(1 + (x - 1) * s(t) for x in v0))(v0, s))
                else:
                    tmp.add(bone, ch, (lambda v0, u, w: lambda t: tuple(x * w(u(t)) for x in v0))(v0, u, w))
        if kind in st:
            merge_into(st[kind], tmp)
        else:
            j = tmp.to_json()
            j.update(name='p:' + cpm_type, animators=tracks_json(tmp))
            NEW.append(j)


NEW = []


def body_anim(cpm_type, length=None, name=None, loop='loop'):
    """an Anim whose tracks go into the existing animation of that pose (or a new one if there is none)"""
    ex = main_of(cpm_type)
    an = Anim(name or '__' + cpm_type, cpm_type, ex['length'] if ex else length, loop=loop)
    an._target = ex
    return an


def commit(an, staged=True, antic=0.08, over=0.06):
    if an._target is not None:
        merge_into(an._target, an)
    else:
        j = an.to_json()
        j['animators'] = tracks_json(an)
        NEW.append(j)
    if staged:
        stage(an.type, an, antic, over)


def put(an, pose, fn=None):
    """static pose {bone: (rot, pos)} (optionally scaled by fn(t))"""
    for b, (r, p) in pose.items():
        if any(abs(x) > 1e-6 for x in r):
            an.rot(b, c(tuple(r)) if fn is None else (lambda r: lambda t: mul3(r, fn(t)))(tuple(r)))
        if any(abs(x) > 1e-6 for x in p):
            an.pos(b, c(tuple(p)) if fn is None else (lambda p: lambda t: mul3(p, fn(t)))(tuple(p)))


def lean(deg, extra=None, drop=(0, 0, 0)):
    """torso tilted around the hips (head and arms follow), legs untouched"""
    out = {k: v for k, v in rig(torso=(deg, 0, 0), drop=drop, limbs=extra or {}).items()}
    if not any(drop):
        out.pop('right_leg'), out.pop('left_leg')
    return out


def loop_wave(an, period, phase=0.0):
    """sin wave that closes exactly on the animation length (whole number of cycles)"""
    n = max(1, round(an.length / period))
    return lambda t: math.sin(2 * math.pi * (n * t / an.length + phase))


# ================================================================== standing: weight shift (idle)
a = body_anim('standing')
f = loop_wave(a, a.length)                       # one slow shift per cycle
a.rot('body', lambda t: (0.0, 0.0, 0.7 * f(t)))
a.rot('head', lambda t: (0.0, 0.0, -0.45 * loop_wave(a, a.length, -0.08)(t)))     # head keeps level, a bit later
a.rot('right_arm', lambda t: (0.0, 0.0, 1.6 + 0.5 * loop_wave(a, a.length, -0.12)(t)))   # arms hang off the body
a.rot('left_arm', lambda t: (0.0, 0.0, -1.6 + 0.5 * loop_wave(a, a.length, -0.15)(t)))
commit(a, antic=0.0, over=0.0)

# ================================================================== walking: relaxed lean, arms clear of the body
a = body_anim('walking')
put(a, lean(-2.5, {'head': (2.0, 0, 0), 'right_arm': (0, 0, 3.0), 'left_arm': (0, 0, -3.0)}))
commit(a, antic=0.06, over=0.05)

# ================================================================== running: body forward, head looks ahead
a = body_anim('running')
put(a, lean(-10, {'head': (8.0, 0, 0), 'right_arm': (6.0, 0, 5.0), 'left_arm': (6.0, 0, -5.0)}))
a.rot('right_leg', c((-3.0, 0.0, 0.0))).rot('left_leg', c((-3.0, 0.0, 0.0)))     # hips push back under the lean
commit(a, antic=0.12, over=0.08)

# ================================================================== sneaking: low fox stalking, paws ready
for typ in ('sneaking', 'sneak_walk'):
    a = body_anim(typ)
    put(a, {'head': ((10.0, 0, 0), (0, -0.3, 0)), 'right_arm': ((10.0, 0, 3.0), Z3), 'left_arm': ((10.0, 0, -3.0), Z3)})
    if typ == 'sneaking':                       # stalking: small, slow shift of weight
        f = loop_wave(a, a.length)
        a.rot('body', lambda t, f=f: (0.0, 0.0, 0.8 * f(t)))
    commit(a, antic=0.1, over=0.06)

# ================================================================== jumping: push, tuck, reach for the ground
a = body_anim('jumping')
L = 0.5                                          # the pose lasts 0.5 s after the jump
k_push = curve([(0, 0.2), (0.08, 1), (0.2, 0.2), (L, 0), (a.length, 0)])
k_tuck = curve([(0, 0), (0.1, 0), (0.24, 1.08), (0.32, 0.95), (0.45, 0.3), (a.length, 0.2)])
a.rot('right_arm', lambda t: (-12 * k_push(t) + 18 * k_tuck(t), 0.0, 14 * k_push(t) + 10 * k_tuck(t)))
a.rot('left_arm', lambda t: (-12 * k_push(t) + 15 * k_tuck(t), 0.0, -14 * k_push(t) - 11 * k_tuck(t)))
a.rot('right_leg', lambda t: (-8 * k_push(t) + 26 * k_tuck(t), 0.0, 0.0))        # knees up (thigh forward)
a.rot('left_leg', lambda t: (-6 * k_push(t) + 14 * curve([(0, 0), (0.14, 0), (0.28, 1.1), (0.38, 0.9), (0.5, 0.3), (a.length, 0.2)])(t), 0.0, 0.0))
a.rot('body', lambda t: (3 * k_push(t) - 4 * k_tuck(t), 0.0, 0.0))
a.rot('head', lambda t: (-4 * k_push(t) + 5 * k_tuck(t), 0.0, 0.0))
commit(a, antic=0.0, over=0.0)

# ================================================================== falling: arms out for balance, legs ready
a = body_anim('falling')
fl_r = loop_wave(a, a.length)
fl_l = loop_wave(a, a.length, -0.3)
a.rot('right_arm', lambda t: (8 + 6 * fl_r(t), 0.0, 55 + 7 * fl_r(t)))
a.rot('left_arm', lambda t: (8 + 6 * fl_l(t), 0.0, -52 - 7 * fl_l(t)))
a.rot('right_leg', lambda t: (12 + 6 * loop_wave(a, a.length, 0.2)(t), 0.0, 4.0))
a.rot('left_leg', lambda t: (-6 + 6 * loop_wave(a, a.length, 0.55)(t), 0.0, -4.0))
a.rot('body', c((4.0, 0.0, 0.0)))
a.rot('head', c((-14.0, 0.0, 0.0)))              # looks at where he will land
commit(a, antic=0.1, over=0.1)

# ================================================================== swimming / crawling: body wave, head forward
for typ, head_up, amp in (('swimming', 12.0, 2.5), ('crawling', 16.0, 1.5)):
    a = body_anim(typ)
    w = loop_wave(a, a.length)
    a.rot('body', lambda t, w=w, amp=amp: (0.0, 0.0, amp * w(t)))
    a.rot('head', lambda t, amp=amp: (head_up, 0.0, -0.6 * amp * loop_wave(a, a.length, -0.1)(t)))
    a.rot('right_leg', lambda t, amp=amp: (0.0, 0.0, 2 + amp * loop_wave(a, a.length, -0.2)(t)))
    a.rot('left_leg', lambda t, amp=amp: (0.0, 0.0, -2 + amp * loop_wave(a, a.length, -0.2)(t)))
    commit(a, antic=0.05, over=0.05)

# ================================================================== elytra: streamlined, arms back
a = body_anim('flying')
fl = loop_wave(a, a.length)
a.rot('right_arm', lambda t: (-22 + 1.2 * fl(t), 0.0, 12 + 1.5 * loop_wave(a, a.length, 0.25)(t)))
a.rot('left_arm', lambda t: (-22 + 1.2 * loop_wave(a, a.length, 0.1)(t), 0.0, -12 - 1.5 * loop_wave(a, a.length, 0.35)(t)))
a.rot('right_leg', c((-4.0, 0.0, 1.5))).rot('left_leg', c((-6.0, 0.0, -1.5)))
a.rot('head', c((10.0, 0.0, 0.0)))
commit(a, antic=0.08, over=0.08)

# ================================================================== creative flight: hovering, legs dangling
a = body_anim('creative_flying')
a.rot('right_leg', lambda t: (8 + 4 * loop_wave(a, a.length)(t), 0.0, 2.0))
a.rot('left_leg', lambda t: (-3 + 4 * loop_wave(a, a.length, -0.18)(t), 0.0, -2.0))
a.rot('right_arm', lambda t: (4.0, 0.0, 9 + 2.5 * loop_wave(a, a.length, -0.08)(t)))
a.rot('left_arm', lambda t: (4.0, 0.0, -9 - 2.5 * loop_wave(a, a.length, -0.12)(t)))
a.rot('body', lambda t: (1.0 * loop_wave(a, a.length, -0.04)(t), 0.0, 0.0))
commit(a, antic=0.0, over=0.06)

# ================================================================== sleeping: curled up like a fox
a = body_anim('sleeping')
br = loop_wave(a, a.length)
a.rot('head', c((-10.0, 0.0, 6.0)))
a.rot('right_arm', lambda t: (28 + 1.2 * br(t), 0.0, -6.0)).rot('left_arm', lambda t: (24 + 1.2 * br(t), 0.0, 8.0))
a.rot('right_leg', c((26.0, 0.0, -4.0))).rot('left_leg', c((32.0, 0.0, 3.0)))
a.rot('body', lambda t: (0.8 * br(t), 0.0, 0.0))
commit(a, antic=0.0, over=0.0)

# ================================================================== riding: hands forward on the reins
a = body_anim('riding')
put(a, lean(-4, {'head': (4.0, 0, 0), 'right_arm': (22.0, -6.0, 4.0), 'left_arm': (22.0, 6.0, -4.0)}))
commit(a)

# ================================================================== dying: goes limp
a = body_anim('dying')
k = curve([(0, 0), (0.35, 1.08), (0.55, 0.97), (0.8, 1.0), (a.length, 1.0)])
a.rot('head', lambda t: (-22 * k(t), 0.0, 10 * k(t)))
a.rot('right_arm', lambda t: (10 * k(t), 0.0, 28 * k(t))).rot('left_arm', lambda t: (6 * k(t), 0.0, -24 * k(t)))
a.rot('right_leg', lambda t: (8 * k(t), 0.0, 6 * k(t))).rot('left_leg', lambda t: (-4 * k(t), 0.0, -5 * k(t)))
commit(a, staged=False)

# ================================================================== hurt: hit, recoil, recover
a = body_anim('hurt')
hit = curve([(0, 0), (0.05, 1.0), (0.16, 0.75), (0.28, -0.22), (0.4, 0.06), (a.length, 0)])
late = lambda dt: (lambda t: hit(max(0.0, t - dt)))
a.rot('body', lambda t: (7 * hit(t), 0.0, 0.0))
a.rot('head', lambda t: (11 * late(0.03)(t), 0.0, -3 * late(0.03)(t)))
a.rot('right_arm', lambda t: (-8 * late(0.04)(t), 0.0, 14 * late(0.04)(t)))
a.rot('left_arm', lambda t: (-8 * late(0.06)(t), 0.0, -14 * late(0.06)(t)))
commit(a, staged=False)

# ================================================================== on fire: patting the flames off
a = body_anim('on_fire')
a.rot('right_arm', lambda t: (18 + 10 * loop_wave(a, a.length)(t), 0.0, 10.0))
a.rot('left_arm', lambda t: (18 + 10 * loop_wave(a, a.length, 0.5)(t), 0.0, -10.0))
a.rot('head', lambda t: (-6.0, 4 * loop_wave(a, a.length, 0.25)(t), 0.0))
commit(a, antic=0.05, over=0.05)

# ================================================================== freezing: hugging himself, shivering
a = body_anim('freezing')
sh = loop_wave(a, a.length / 3)
a.rot('right_arm', lambda t: (24.0, 0.0, -9 + 1.2 * sh(t))).pos('right_arm', c((0.0, 0.35, 0.0)))
a.rot('left_arm', lambda t: (24.0, 0.0, 9 - 1.2 * loop_wave(a, a.length / 3, 0.3)(t))).pos('left_arm', c((0.0, 0.35, 0.0)))
a.rot('head', lambda t: (-7.0, 0.0, 0.8 * sh(t)))
a.rot('body', lambda t: (0.0, 0.0, 0.5 * loop_wave(a, a.length / 3, 0.15)(t)))
commit(a, antic=0.0, over=0.04)

# ================================================================== ladder: hands on the rungs, climbing
a = body_anim('on_ladder')
br = loop_wave(a, a.length)
a.rot('right_arm', lambda t: (138 + br(t), 0.0, -4.0)).rot('left_arm', lambda t: (126 + br(t), 0.0, 4.0))
a.rot('right_leg', c((18.0, 0.0, 0.0)))
a.rot('head', c((12.0, 0.0, 0.0)))
commit(a)
a = body_anim('climbing_on_ladder')
up = loop_wave(a, a.length)
a.rot('right_arm', lambda t: (138 + 16 * up(t), 0.0, -4.0))
a.rot('left_arm', lambda t: (138 - 16 * up(t), 0.0, 4.0))                     # hands alternate on the rungs
a.rot('right_leg', lambda t: (16 - 16 * loop_wave(a, a.length, 0.08)(t), 0.0, 0.0))
a.rot('left_leg', lambda t: (16 + 16 * loop_wave(a, a.length, 0.08)(t), 0.0, 0.0))  # feet follow the hands
a.rot('body', lambda t: (-3.0, 2 * loop_wave(a, a.length, 0.04)(t), 0.0))
a.rot('head', c((14.0, 0.0, 0.0)))
commit(a)

# ================================================================== attack (driven by the swing: 0 = start, 1 = end)
for side, s in (('right', 1), ('left', -1)):
    a = body_anim('punch_' + side)
    arm, other = ('right_arm', 'left_arm') if side == 'right' else ('left_arm', 'right_arm')
    twist = curve([(0, 0), (0.12, -0.45), (0.38, 1.12), (0.55, 1.0), (0.72, 0.35), (0.88, -0.06), (1.0, 0)])
    reach_k = curve([(0, 0), (0.12, -0.6), (0.34, 1.1), (0.5, 0.9), (0.75, 0.15), (1.0, 0)])
    late = lambda f, dt: (lambda t: f(max(0.0, t - dt)))
    a.rot('body', lambda t, s=s: (-4 * max(0.0, twist(t)), 12 * s * twist(t), 0.0))     # wind up, strike, settle
    a.rot('head', lambda t, s=s: (0.0, -8 * s * late(twist, 0.06)(t), 0.0))             # eyes stay on the target
    a.rot(arm, lambda t, s=s: (14 * reach_k(t), 0.0, 4 * s * late(reach_k, 0.04)(t)))
    a.rot(other, lambda t, s=s: (-12 * late(twist, 0.05)(t), 0.0, -6 * s * late(twist, 0.08)(t)))   # counter-swing
    a.rot('right_leg' if s > 0 else 'left_leg', lambda t: (-5 * max(0.0, twist(t)), 0.0, 0.0))     # weight onto the front foot
    commit(a, staged=False)

# ================================================================== eating / drinking: food to the mouth, chewing
for side, s in (('right', 1), ('left', -1)):
    arm = side + '_arm'
    a = body_anim('eating_' + side, length=1.0, name='Comendo (%s)' % ('direita' if s > 0 else 'esquerda'))
    mouth = np.array([1.5 * s, 25.4, -9.0])            # food held just in front of the snout
    A = np.array(PIVOT[arm], float)
    hand = np.array([5.5 * s, 11.6, 0.0])
    rr = euler_zyx(R_to(hand - A, mouth - A))
    rr = (rr[0] - 18.0, rr[1], rr[2])            # vanilla already lifts an arm that holds an item (~18 deg)
    chew = loop_wave(a, 0.25)
    a.rot(arm, lambda t, rr=rr: (rr[0] + 2.5 * loop_wave(a, 0.25, -0.15)(t), rr[1], rr[2]))
    a.rot('head', lambda t: (-6 + 2.2 * chew(t), 0.0, 0.0))
    a.rot('body', c((-2.0, 0.0, 0.0)))
    commit(a, antic=0.1, over=0.08)

# ================================================================== save
order = {}
for x in EXISTING:
    order[x['cpm_type']] = order.get(x['cpm_type'], 0) + 1
for x in NEW:
    x['cpm_order'] = order.get(x['cpm_type'], 0)
    order[x['cpm_type']] = order.get(x['cpm_type'], 0) + 1
d['animations'] = EXISTING + NEW
json.dump(d, open(OUT, 'w'))
print('ok: body motion added to %d animations, %d new' % (
    sum(1 for x in EXISTING if any(GRP_BY_UUID(u)['name'] in BODY for u in x['animators'])), len(NEW)))
