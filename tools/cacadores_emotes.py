"""Bounty hunters (Cacadores de recompensas) variant: animated accessories + bounty-hunter emotes.

usage: python3 tools/cacadores_emotes.py <variant.bbmodel built by variante.py --acessorios cacadores> <out.bbmodel>

- Accessories in motion: the bandana tip swings (idle sway, steps, wind when running / falling), the goggles bounce
  with the steps and jumps.
- Toggle "Oculos nos olhos" (CPM layer): both hands pull the goggles down over the eyes (setup) and push them
  back up to the forehead (finish); the strap tightens. Plain glass, nothing glowing (no tech in this universe).
- Emotes (props come out of the sleeves and go back in; they rest hidden inside the arms):
  Reconhecer o alvo and Finalizando contrato (the contract comes out rolled and is opened with both hands like a
  scroll), Jogar moeda (loop until the player moves), Saudacao do velho oeste.
"""
import json, sys, os, math
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
assert len(d['groups']) == n_groups, 'animlib must not change the model'
EXISTING = list(d['animations'])

# ------------------------------------------------------------------ helpers
HAND = {'right_arm': np.array([6.0, 11.6, 0.0]), 'left_arm': np.array([-6.0, 11.6, 0.0])}
REST = {'prop_carvao': (6.75, 14.5, 0.0), 'prop_moeda': (5.625, 20.625, 0.0), 'prop_contrato': (-6.0, 20.0, 0.0),
        'prop_rolo': (-6.0, 13.75, 0.0)}
ARM_OF = {'prop_carvao': 'right_arm', 'prop_moeda': 'right_arm', 'prop_contrato': 'left_arm', 'prop_rolo': 'left_arm'}
PAPER_W, PAPER_H, SC = 3.75, 6.0, 1.3          # contract size and how much bigger it is shown


def reach(arm, target):
    """arm rotation (euler) that puts the hand on `target` (moved onto the arm's reach sphere)."""
    A = np.array(PIVOT[arm], float)
    return euler_zyx(R_to(HAND[arm] - A, np.array(target, float) - A))


def hand_world(arm, rot):
    A = np.array(PIVOT[arm], float)
    return A + rotmat(rot) @ (HAND[arm] - A)


def place(prop, arm_rot, R, W):
    """(rot, pos) of a prop group (child of its arm) so that its pivot is at world point W with world rotation R."""
    A = np.array(PIVOT[ARM_OF[prop]], float)
    Ra = rotmat(arm_rot)
    return euler_zyx(Ra.T @ R), tuple(Ra.T @ (np.array(W, float) - A) + A - np.array(REST[prop]))


def held(prop, arm_rot, R=np.eye(3), extra_world=(0, 0, 0)):
    """prop in the hand with world rotation R (+ a world offset)"""
    return place(prop, arm_rot, R, hand_world(ARM_OF[prop], arm_rot) + np.array(extra_world, float))


def on_sphere(arm, x, y, z_sign=-1):
    """point (x, y, z) in front of the body that a straight arm can reach exactly"""
    A = np.array(PIVOT[arm], float)
    r = np.linalg.norm(HAND[arm] - A)
    dz2 = r * r - (x - A[0]) ** 2 - (y - A[1]) ** 2
    return np.array([x, y, A[2] + z_sign * math.sqrt(max(0.0, dz2))])


def contract(k, R, top_y=21.6, one_hand=None, spread=1.0):
    """frame of the open contract held by both hands at its top corners.
    k = how unrolled (0.08 rolled .. 1 open); R = world rotation of the paper (local -Z = printed side)."""
    half = PAPER_W * SC / 2 * spread
    # the corner held by the left hand is the one with the smaller world x
    side = 1.0 if (R @ np.array([1.0, 0, 0]))[0] < 0 else -1.0     # local x of the left corner
    lc = on_sphere('left_arm', -half if one_hand != 'show' else -6.4, top_y)
    l = reach('left_arm', lc)
    hl = hand_world('left_arm', l)
    Wp = hl - R @ np.array([side * half, 0, 0])                    # top centre of the paper
    rc = Wp + R @ np.array([-side * half, 0, 0])
    out = {'left_arm': (l, Z3)}
    if one_hand is None:
        out['right_arm'] = (reach('right_arm', rc), Z3)
    r_, p_ = place('prop_contrato', l, R, Wp)
    out['prop_contrato'] = {'r': r_, 'p': p_, 's': (SC, SC * k, SC)}
    bottom = Wp + R @ np.array([0, -PAPER_H * SC * k - 0.25 * SC, 0])
    r2, p2 = place('prop_rolo', l, R, bottom)
    out['prop_rolo'] = {'r': r2, 'p': p2, 's': (SC, SC, SC)}
    return out


def env(points):
    return curve(points)


# ------------------------------------------------------------------ accessories in motion
L_WALK = next(x['length'] for x in EXISTING if x.get('cpm_type') == 'walking' and not x['name'].startswith('p:'))
L_RUN = next(x['length'] for x in EXISTING if x.get('cpm_type') == 'running' and not x['name'].startswith('p:'))

a = Anim('Acessorios balancando', 'global', 6.4)
a.rot('bandana_ponta', lambda t: (2.0 + 2.0 * math.sin(2 * math.pi * t / 3.2), 0.0, 1.5 * math.sin(2 * math.pi * t / 6.4)))

a = Anim('Acessorios andando', 'walking', L_WALK)
a.rot('bandana_ponta', lambda t: (4.0 + 4.0 * math.sin(4 * math.pi * t / L_WALK), 0.0, 3.0 * math.sin(2 * math.pi * t / L_WALK)))
a.rot('acess_oculos', lambda t: (1.5 * math.sin(4 * math.pi * t / L_WALK), 0.0, 0.0))
a.pos('acess_oculos', lambda t: (0.0, 0.05 * math.sin(4 * math.pi * t / L_WALK), 0.0))

a = Anim('Acessorios correndo', 'running', L_RUN)
a.rot('bandana_ponta', lambda t: (14.0 + 6.0 * math.sin(4 * math.pi * t / L_RUN), 0.0, 4.0 * math.sin(2 * math.pi * t / L_RUN)))
a.rot('acess_oculos', lambda t: (3.0 * math.sin(4 * math.pi * t / L_RUN), 0.0, 0.0))
a.pos('acess_oculos', lambda t: (0.0, 0.1 * math.sin(4 * math.pi * t / L_RUN), 0.0))

a = Anim('Acessorios pulando', 'jumping', 0.5, loop='loop')
a.rot('bandana_ponta', c((16.0, 0.0, 0.0)))
a.rot('acess_oculos', c((-5.0, 0.0, 0.0)))

a = Anim('Acessorios caindo', 'falling', 0.6)
a.rot('bandana_ponta', lambda t: (22.0 + 6.0 * math.sin(2 * math.pi * t / 0.3), 0.0, 3.0 * math.sin(2 * math.pi * t / 0.6)))
a.rot('acess_oculos', lambda t: (-6.0 + 1.5 * math.sin(2 * math.pi * t / 0.3), 0.0, 0.0))

# ------------------------------------------------------------------ toggle: goggles over the eyes
GOG_R, GOG_P, STRAP_S = (-25.0, 0.0, 0.0), (0.0, -3.55, 0.0), 8.6 / 9.5
a = Anim('Oculos nos olhos', 'layer', 1.0)
a.rot('acess_oculos', c(GOG_R))                              # upright, over the eyes
a.pos('acess_oculos', c(GOG_P))
a.scl('oculos_alca_g', c((1.0, 1.0, STRAP_S)))               # strap tight around the head
ears(a, back=-6)


def gog(w):
    return {'acess_oculos': {'r': tuple(x * w for x in GOG_R), 'p': tuple(x * w for x in GOG_P)},
            'oculos_alca_g': {'s': (1.0, 1.0, 1 - (1 - STRAP_S) * w)}}


def hands_at(y):
    return {'right_arm': (reach('right_arm', (2.5, y, -5.4)), Z3), 'left_arm': (reach('left_arm', (-2.5, y, -5.4)), Z3)}


st = Anim('g:Oculos nos olhos', 'setup', 1.1, loop='once')        # both hands pull the goggles down
keyposes(st, [(0.0, gog(0)), (0.35, merge(gog(0), hands_at(31.6))), (0.75, merge(gog(1), hands_at(28.2))),
              (1.1, gog(1))])
ears(st, back=-6, fn=curve([(0, 0), (1.1, 1)]))
st = Anim('g:Oculos nos olhos', 'finish', 1.1, loop='once')       # and push them back up to the forehead
keyposes(st, [(0.0, gog(1)), (0.3, merge(gog(1), hands_at(28.2))), (0.75, merge(gog(0), hands_at(31.6))),
              (1.1, gog(0))])
ears(st, back=-6, fn=curve([(0, 1), (1.1, 0)]))

# ------------------------------------------------------------------ Reconhecer o alvo
# takes the contract out rolled, opens it with both hands while looking at the target, compares, nods
a = Anim('Reconhecer o alvo', 'gesture', 7.8, loop='once')
R_READ = rotmat((-14, 0, 0)) @ rotmat((0, 180, 0))           # printed side to the fox, top leaning away
look_far, look_down = ((3, -5, 0), Z3), ((-17, 2, 0), Z3)
keyposes(a, [
    (0.0, {}),
    (0.7, merge(contract(0.08, R_READ, 20.6, spread=0.6), {'head': ((-6, 0, 0), Z3)})),     # out, rolled
    (1.6, merge(contract(1.0, R_READ), {'head': look_far})),                               # opens it, eyes on the target
    (2.4, merge(contract(1.0, R_READ), {'head': look_down})),                              # reads
    (3.1, merge(contract(1.0, R_READ), {'head': ((-15, -3, 0), Z3)})),
    (3.5, merge(contract(1.0, R_READ), {'head': look_far})),                               # target
    (4.0, merge(contract(1.0, R_READ), {'head': look_down})),                              # contract
    (4.5, merge(contract(1.0, R_READ, 21.0), {'head': ((2, -6, 0), Z3)})),                 # target again
    (5.1, merge(contract(1.0, R_READ, 21.0), {'head': ((2, -6, 12), Z3)})),                # tilts the head
    (5.5, merge(contract(1.0, R_READ, 21.0), {'head': ((-11, -4, 4), Z3)})),               # short nod
    (5.75, merge(contract(1.0, R_READ, 21.0), {'head': ((3, -4, 2), Z3)})),
    (6.0, merge(contract(1.0, R_READ, 21.0), {'head': ((0, -3, 0), Z3)})),
    (6.7, merge(contract(0.08, R_READ, 20.6, spread=0.6), {'head': ((-4, 0, 0), Z3)})),    # rolls it up
    (7.3, {'left_arm': ((-12, 0, -4), Z3), 'right_arm': ((-12, 0, 4), Z3)}),               # back in the sleeve
    (7.8, {})])
e_ = env([(0, 0), (0.7, 1), (6.7, 1), (7.8, 0)])
ears_fn(a, fn_back=lambda t: -10 * e_(t) + 8 * twitch([5.5], 0.3)(t), fn_twist=lambda t: -6 * e_(t))
brows(a, lift=-0.05, tilt=5, fn=e_)
down_k = curve([(0, 0), (1.6, 0), (2.4, 1), (3.1, 1), (3.5, 0), (4.0, 1), (4.5, 0), (7.8, 0)])
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.14 * down_k(t), 0.0))
tail_wave(a, 3.0, 2.6)

# ------------------------------------------------------------------ Finalizando contrato
# opens the contract with both hands, strikes the target off with charcoal, shows it and rolls it up
a = Anim('Finalizando contrato', 'gesture', 9.0, loop='once')
open_ = contract(1.0, R_READ)
l_open = open_['left_arm'][0]
hl = hand_world('left_arm', l_open)
side = 1.0 if (R_READ @ np.array([1.0, 0, 0]))[0] < 0 else -1.0
Wp = hl - R_READ @ np.array([side * PAPER_W * SC / 2, 0, 0])


def paper_point(lx, ly):
    """world point of a paper-local point (rest coordinates) when the contract is open"""
    return Wp + R_READ @ (SC * (np.array([lx, ly, 0.0]) - np.array(REST['prop_contrato'])))


S0, S1 = paper_point(-7.0, 18.4), paper_point(-7.0 + 2.75 * math.cos(math.radians(42)),
                                              18.4 - 2.75 * math.sin(math.radians(42)))
TOWARD = R_READ @ np.array([0, 0, -1.0])                        # printed side normal (towards the fox)


def pen_at(P):
    r = reach('right_arm', P + TOWARD * 1.6)
    h = hand_world('right_arm', r)
    return {'right_arm': (r, Z3), 'prop_carvao': place('prop_carvao', r, R_to((0, 1, 0), P - h), h)}


SHOW = contract(1.0, rotmat((0, -14, 0)), 22.6, one_hand='show')   # printed side forward, left hand only
read_f = merge(open_, {'head': look_down})
keyposes(a, [
    (0.0, {}),
    (0.7, merge(contract(0.08, R_READ, 20.6, spread=0.6), {'head': ((-6, 0, 0), Z3)})),
    (1.6, merge(open_, {'head': look_far})),                                          # opens it, looks at the target
    (2.3, read_f),
    (2.8, merge(read_f, {'right_arm': ((-30, 0, 10), Z3)})),                          # right hand takes the charcoal
    (3.3, merge(read_f, pen_at(S0))),
    (4.2, merge(read_f, pen_at(S1))),                                                 # the strike
    (4.7, merge(read_f, {'right_arm': ((-20, 0, 8), Z3), 'head': ((-10, 0, 0), Z3)})),
    (5.6, merge(SHOW, {'head': ((2, -8, 3), Z3)})),                                   # shows it: done
    (6.4, merge(SHOW, {'head': ((-6, -8, 3), Z3)})),
    (6.8, merge(SHOW, {'head': ((0, -6, 0), Z3)})),
    (7.6, merge(contract(0.08, R_READ, 20.6, spread=0.6), {'head': ((-4, 0, 0), Z3)})),
    (8.3, {'left_arm': ((-12, 0, -4), Z3), 'right_arm': ((-12, 0, 4), Z3)}),
    (9.0, {})])
a.pos('contrato_risco', curve([(0, (0, 0, 0)), (3.25, (0, 0, 0)), (3.3, (0, 0, -0.07)), (7.5, (0, 0, -0.07)),
                               (7.55, (0, 0, 0)), (9.0, (0, 0, 0))], ease=lambda x: x))
a.scl('contrato_risco', curve([(0, (1, 1, 1)), (3.25, (1, 1, 1)), (3.3, (0.02, 1, 1)), (4.2, (1, 1, 1)),
                               (9.0, (1, 1, 1))]))
e_ = env([(0, 0), (0.7, 1), (7.6, 1), (9.0, 0)])
done = env([(0, 0), (4.2, 0), (4.7, 1), (7.6, 1), (9.0, 0)])
brows(a, lift=-0.04, tilt=4, fn=lambda t: e_(t) * (1 - done(t)))
brows(a, lift=0.05, tilt=-4, fn=done)
ears_fn(a, fn_back=lambda t: -8 * e_(t) - 6 * done(t), fn_twist=lambda t: -6 * e_(t))
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (0.0, 10 * 1.1 ** i * math.sin(2 * math.pi * (t / 0.55 - 0.12 * i)) * done(t), 0.0))

# ------------------------------------------------------------------ Jogar moeda (loop until the player moves)
L_COIN = 2.6
a = Anim('Jogar moeda', 'custom_pose', L_COIN)
COIN_ARM = reach('right_arm', on_sphere('right_arm', 2.0, 16.6))
T0, T1, H_UP = 0.32, 2.0, 13.0                                  # launch, catch, height above the hand
arm_k = curve([(0, 0), (0.2, 7), (0.32, -11), (0.5, 0), (1.85, 0), (1.98, -6), (2.08, 6), (2.3, 0), (L_COIN, 0)])


def flight(t):
    return min(1.0, max(0.0, (t - T0) / (T1 - T0)))


def up(t):
    u = flight(t)
    return H_UP * 4 * u * (1 - u) if T0 <= t <= T1 else 0.0


def coin_rot(t):
    u = flight(t)
    spin = 1620 * (u * u * (3 - 2 * u))                             # fast after the flick, slowing at the catch
    wob = 18 * math.sin(2 * math.pi * 2.5 * u) * (1 - u)
    return rotmat((90 + spin, 0, wob))


a.rot('right_arm', lambda t: tuple(np.add(COIN_ARM, (arm_k(t), 0, 0))))
a.rot('prop_moeda', lambda t: held('prop_moeda', np.add(COIN_ARM, (arm_k(t), 0, 0)), coin_rot(t))[0])
a.pos('prop_moeda', lambda t: held('prop_moeda', np.add(COIN_ARM, (arm_k(t), 0, 0)), np.eye(3),
                                   (0, 0.5 + up(t), 0))[1])
a.rot('head', lambda t: (-12 + 2.6 * up(t), 0.0, 0.0))          # follows the coin up and down
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.12 + 0.025 * up(t), 0.0))
ears_fn(a, fn_back=lambda t: -0.8 * up(t), fn_twist=lambda t: 12 * twitch([2.05], 0.3)(t), side='RL')
brows(a, lift=0.03, tilt=-3)
tail_wave(a, 4.0, 2.6)
staged_custom(a, 0.5)

# ------------------------------------------------------------------ Saudacao do velho oeste
# hand to the brim (the goggles), head tipped forward a little, then a small wave off
a = Anim('Saudacao do velho oeste', 'gesture', 3.2, loop='once')
BRIM = reach('right_arm', (3.7, 33.2, -5.2))                 # at the temple, like tipping a hat
OFF = reach('right_arm', on_sphere('right_arm', 9.5, 27.0))
keyposes(a, [
    (0.0, {}),
    (0.5, {'right_arm': (BRIM, Z3), 'head': ((-4, -6, 0), Z3)}),
    (0.9, {'right_arm': (BRIM, Z3), 'head': ((-14, -6, 4), Z3), 'body': ((-4, 0, 0), Z3)}),   # tips the head
    (1.6, {'right_arm': (BRIM, Z3), 'head': ((-12, -6, 4), Z3), 'body': ((-3, 0, 0), Z3)}),
    (2.1, {'right_arm': (OFF, Z3), 'head': ((0, -4, 0), Z3)}),                                # hand off, forward
    (3.2, {})])
e_ = env([(0, 0), (0.5, 1), (2.1, 1), (3.2, 0)])
ears_fn(a, fn_back=lambda t: 12 * curve([(0, 0), (0.9, 1), (1.6, 1), (2.1, 0), (3.2, 0)])(t) - 6 * e_(t))
brows(a, lift=0.04, tilt=-3, fn=e_)
tail_wave(a, 8.0, 0.8)

# ------------------------------------------------------------------ save (new animations after the existing ones)
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
json.dump(d, open(OUT, 'w'))
print('ok: %d new animations, %d total' % (len(new), len(d['animations'])))
