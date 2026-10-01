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


def paper_frame(down, toward=(0, 0, 1)):
    """world rotation of the paper: its top->bottom goes along `down`, printed side (local -Z) faces `toward`"""
    y = -norm(down)
    t = np.array(toward, float)
    zl = -(t - y * (t @ y)); zl = zl / np.linalg.norm(zl)       # local +Z points away from `toward`
    x = np.cross(y, zl)
    return np.column_stack([x, y, zl])


TOP_RD = on_sphere('left_arm', -0.5, 23.2)                       # left hand: top edge
BOT_RD = on_sphere('right_arm', 0.5, 15.0)                       # right hand: the roll at the bottom
DOWN_RD = norm(BOT_RD - TOP_RD)
R_READ = paper_frame(DOWN_RD)                                    # printed side to the fox (reading tilt)
ROLL = 0.25 * SC


def contract_v(k, R=None, top=None, down=None, right_hand=True):
    """contract held vertically: left hand on the top edge, right hand pulling the roll down.
    k = how unrolled (0.08 rolled .. 1 open)."""
    R = R_READ if R is None else R
    down = DOWN_RD if down is None else norm(down)
    top = TOP_RD if top is None else np.array(top, float)
    l = reach('left_arm', top)
    Wp = hand_world('left_arm', l)                               # top centre of the paper = left hand
    bottom = Wp + down * (PAPER_H * SC * k + ROLL)
    out = {'left_arm': (l, Z3)}
    if right_hand:
        out['right_arm'] = (reach('right_arm', bottom + np.array([0.6, 0, 0])), Z3)
    r_, p_ = place('prop_contrato', l, R, Wp)
    out['prop_contrato'] = {'r': r_, 'p': p_, 's': (SC, SC * k, SC)}
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
# takes the contract out rolled, opens it vertically (left hand holds the top, right hand pulls the roll down)
# while looking at the target, reads, compares, and confirms with a cold, serious nod
a = Anim('Reconhecer o alvo', 'gesture', 7.8, loop='once')
look_far, look_down = ((3, -5, 0), Z3), ((-17, 2, 0), Z3)
rolled = contract_v(0.08)
opened = contract_v(1.0)
keyposes(a, [
    (0.0, {}),
    (0.7, merge(rolled, {'head': ((-6, 0, 0), Z3)})),                                  # out, rolled
    (1.6, merge(opened, {'head': look_far})),                                          # pulls it open, eyes on the target
    (2.4, merge(opened, {'head': look_down})),                                         # reads
    (3.1, merge(opened, {'head': ((-15, -3, 0), Z3)})),
    (3.5, merge(opened, {'head': look_far})),                                          # target
    (4.0, merge(opened, {'head': look_down})),                                         # contract
    (4.5, merge(opened, {'head': ((2, -6, 0), Z3)})),                                  # target again
    (5.1, merge(opened, {'head': ((2, -6, 12), Z3)})),                                 # tilts the head
    (5.5, merge(opened, {'head': ((-11, -4, 4), Z3)})),                                # short nod
    (5.75, merge(opened, {'head': ((3, -4, 2), Z3)})),
    (6.0, merge(opened, {'head': ((0, -3, 0), Z3)})),
    (6.7, merge(rolled, {'head': ((-4, 0, 0), Z3)})),                                  # rolls it up
    (7.3, {'left_arm': ((-12, 0, -4), Z3), 'right_arm': ((-12, 0, 4), Z3)}),           # back in the sleeve
    (7.8, {})])
e_ = env([(0, 0), (0.7, 1), (6.7, 1), (7.8, 0)])
cold = env([(0, 0), (4.5, 0), (5.1, 1), (6.7, 1), (7.8, 0)])                         # serious at the conclusion
ears_fn(a, fn_back=lambda t: -10 * e_(t) + 16 * cold(t) + 8 * twitch([5.5], 0.3)(t), fn_twist=lambda t: -6 * e_(t))
brows(a, lift=-0.05, tilt=5, fn=lambda t: e_(t) * (1 - cold(t)))
brows(a, lift=-0.13, tilt=7, fn=cold)
down_k = curve([(0, 0), (1.6, 0), (2.4, 1), (3.1, 1), (3.5, 0), (4.0, 1), (4.5, 0), (7.8, 0)])
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.14 * down_k(t), 0.0))
tail_wave(a, 3.0, 2.6)

# ------------------------------------------------------------------ Finalizando contrato
# opens it the same way, strikes the target off with charcoal, then shows it with a furious, triumphant
# face ("conseguimos, porra!"): fist pump, hard nod, ears pinned, snout wrinkled; rolls it up
a = Anim('Finalizando contrato', 'gesture', 9.4, loop='once')
Wp_o = hand_world('left_arm', reach('left_arm', TOP_RD))


def paper_point(lx, ly):
    """world point of a paper-local point (rest coordinates) when the contract is open"""
    return Wp_o + R_READ @ (SC * (np.array([lx, ly, 0.0]) - np.array(REST['prop_contrato'])))


S0, S1 = paper_point(-7.0, 18.4), paper_point(-7.0 + 2.75 * math.cos(math.radians(42)),
                                              18.4 - 2.75 * math.sin(math.radians(42)))
TOWARD = R_READ @ np.array([0, 0, -1.0])                        # printed side normal (towards the fox)


def pen_at(P):
    r = reach('right_arm', P + TOWARD * 1.6)
    h = hand_world('right_arm', r)
    return {'right_arm': (r, Z3), 'prop_carvao': place('prop_carvao', r, R_to((0, 1, 0), P - h), h)}


# showing it: held up by the top with the left hand, hanging open, printed side forward
SHOW_TOP = on_sphere('left_arm', -6.2, 27.0)
SHOW = contract_v(1.0, R=rotmat((0, -12, 0)), top=SHOW_TOP, down=(0, -1, 0), right_hand=False)
PUMP_UP = reach('right_arm', on_sphere('right_arm', 7.5, 31.5))     # fist up
PUMP_MID = reach('right_arm', on_sphere('right_arm', 8.5, 26.0))
read_f = merge(opened, {'head': look_down})
keyposes(a, [
    (0.0, {}),
    (0.7, merge(rolled, {'head': ((-6, 0, 0), Z3)})),
    (1.6, merge(opened, {'head': look_far})),                                         # opens it, looks at the target
    (2.3, read_f),
    (2.8, merge(read_f, {'right_arm': ((-30, 0, 10), Z3), 'prop_rolo': opened['prop_rolo']})),  # takes the charcoal
    (3.3, merge(read_f, pen_at(S0))),
    (4.2, merge(read_f, pen_at(S1))),                                                 # the strike
    (4.7, merge(read_f, {'right_arm': ((-20, 0, 8), Z3), 'head': ((-10, 0, 0), Z3)})),
    (5.4, merge(SHOW, {'right_arm': (PUMP_MID, Z3), 'head': ((4, -8, 3), Z3)})),     # shows it
    (5.7, merge(SHOW, {'right_arm': (PUMP_UP, Z3), 'head': ((-14, -8, 3), Z3)})),    # fist up + hard nod
    (5.95, merge(SHOW, {'right_arm': (PUMP_MID, Z3), 'head': ((6, -8, 3), Z3)})),
    (6.2, merge(SHOW, {'right_arm': (PUMP_UP, Z3), 'head': ((-12, -8, 3), Z3)})),
    (6.6, merge(SHOW, {'right_arm': ((-10, 0, 14), Z3), 'head': ((2, -8, 3), Z3)})),
    (7.3, merge(SHOW, {'head': ((0, -6, 0), Z3)})),
    (8.1, merge(rolled, {'head': ((-4, 0, 0), Z3)})),
    (8.8, {'left_arm': ((-12, 0, -4), Z3), 'right_arm': ((-12, 0, 4), Z3)}),
    (9.4, {})])
a.pos('contrato_risco', curve([(0, (0, 0, 0)), (3.25, (0, 0, 0)), (3.3, (0, 0, -0.07)), (8.0, (0, 0, -0.07)),
                               (8.05, (0, 0, 0)), (9.4, (0, 0, 0))], ease=lambda x: x))
a.scl('contrato_risco', curve([(0, (1, 1, 1)), (3.25, (1, 1, 1)), (3.3, (0.02, 1, 1)), (4.2, (1, 1, 1)),
                               (9.4, (1, 1, 1))]))
e_ = env([(0, 0), (0.7, 1), (8.1, 1), (9.4, 0)])
fury = env([(0, 0), (4.7, 0), (5.3, 1), (7.3, 1), (8.1, 0), (9.4, 0)])               # "conseguimos, porra!"
brows(a, lift=-0.04, tilt=4, fn=lambda t: e_(t) * (1 - fury(t)))
brows(a, lift=-0.14, tilt=16, fn=fury)
ears_fn(a, fn_back=lambda t: -8 * e_(t) * (1 - fury(t)) + 46 * fury(t), fn_twist=lambda t: -6 * e_(t) * (1 - fury(t)))
sn_f = twitch([5.7, 6.2], 0.35)
a.pos('nariz', lambda t: (0.0, 0.05 * sn_f(t), -0.03 * sn_f(t)))
fur_lift(a, ['fur_top', 'fur_cheek_R', 'fur_cheek_L'], lambda t, i: 12 * fury(t))
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (-14 * fury(t) if i == 0 else 0.0,
                             12 * 1.12 ** i * math.sin(2 * math.pi * (t / 0.45 - 0.1 * i)) * fury(t), 0.0))

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
ears_fn(a, fn_back=lambda t: 14 * e_(t))
brows(a, lift=-0.13, tilt=7, fn=e_)                           # very serious face
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, 0.02 * e_(t), 0.0))
tail_pose(a, rx=(6, 2, 0, 0, 0), fn=e_)                      # tail still and low

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
