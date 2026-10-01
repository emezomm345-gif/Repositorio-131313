"""Bounty hunters (Cacadores de recompensas) variant: animated accessories + bounty-hunter emotes.

usage: python3 tools/cacadores_emotes.py <variant.bbmodel built by variante.py --acessorios cacadores> <out.bbmodel>

- Accessories in motion: the bandana tip swings (idle sway, steps, wind when running / falling), the goggles bounce
  with the steps and jumps.
- Toggle "Oculos nos olhos" (CPM layer): the goggles come down over the eyes, the strap tightens and the lenses
  light up with a scanning line (visual effect), with smooth in/out.
- Emotes (props come out of the sleeves and go back in; they rest hidden inside the arms / body):
  Reconhecer o alvo, Encarar o horizonte, Afiar a lamina, Limpar a poeira (one-shot gestures),
  Jogar moeda (loop until the player moves), Finalizando contrato (one-shot).
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
REST = {'prop_faca': (6.0, 15.25, 0.0), 'prop_carvao': (6.75, 14.5, 0.0), 'prop_moeda': (5.5, 20.5, 0.0),
        'prop_contrato': (-6.0, 14.0, 0.0), 'prop_pedra': (-6.0, 18.25, 0.0)}
ARM_OF = {'prop_faca': 'right_arm', 'prop_carvao': 'right_arm', 'prop_moeda': 'right_arm',
          'prop_contrato': 'left_arm', 'prop_pedra': 'left_arm'}


def reach(arm, target):
    """arm rotation (euler) that puts the hand exactly on `target` (moved onto the arm's reach sphere)."""
    A = np.array(PIVOT[arm], float)
    h = HAND[arm] - A
    t = np.array(target, float) - A
    return euler_zyx(R_to(h, t))


def hand_world(arm, rot):
    A = np.array(PIVOT[arm], float)
    return A + rotmat(rot) @ (HAND[arm] - A)


def held(prop, arm_rot, world_rot=np.eye(3), extra_world=(0, 0, 0)):
    """(rot, pos) of a prop group so that it sits in the hand with a given WORLD orientation (+ a world offset)."""
    arm = ARM_OF[prop]
    Ra = rotmat(arm_rot)
    Rw = world_rot if isinstance(world_rot, np.ndarray) else rotmat(world_rot)
    pos = HAND[arm] - np.array(REST[prop]) + Ra.T @ np.array(extra_world, float)
    return euler_zyx(Ra.T @ Rw), tuple(pos)


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

# ------------------------------------------------------------------ toggle: goggles over the eyes (visual effect)
a = Anim('Oculos nos olhos', 'layer', 1.2)
a.rot('acess_oculos', c((-25.0, 0.0, 0.0)))                  # upright
a.pos('acess_oculos', c((0.0, -3.55, 0.0)))                  # lens centre on the eyes
a.scl('oculos_alca_g', c((1.0, 1.0, 8.6 / 9.5)))             # strap tight around the head (no tilt any more)
a.pos('oculos_brilho', c((0.0, 0.0, -0.3)))                  # glowing lenses come to the front
a.pos('oculos_scan', lambda t: (0.0, -1.75 * (t / 1.2), 0.0))  # scanning line top -> bottom
ears(a, back=-6)
staged_layer(a, 0.4)

# ------------------------------------------------------------------ Reconhecer o alvo
a = Anim('Reconhecer o alvo', 'gesture', 7.4, loop='once')
READ_L = reach('left_arm', (-1.6, 17.6, -7.4))
CMP_L = reach('left_arm', (-8.6, 24.2, -9.4))          # arm out to the side, poster next to the face
read_paper = rotmat((-32, 0, 0)) @ rotmat((0, 180, 0))       # printed side to the fox, top leaning away
show_paper = rotmat((0, -18, 0))                             # printed side forward, turned a bit to the front
P_READ = held('prop_contrato', READ_L, read_paper)
P_CMP = held('prop_contrato', CMP_L, show_paper)
read = {'left_arm': (READ_L, Z3), 'prop_contrato': P_READ, 'head': ((-22, 10, 0), Z3)}
keyposes(a, [
    (0.0, {}),
    (0.8, read),
    (1.6, merge(read, {'head': ((-24, 6, 0), Z3)})),
    (2.3, merge(read, {'head': ((-20, 12, 0), Z3)})),
    (2.7, merge(read, {'head': ((2, -4, 0), Z3)})),                       # glance forward
    (3.3, merge(read, {'head': ((-20, 10, 0), Z3)})),                     # back to the contract
    (4.1, {'left_arm': (CMP_L, Z3), 'prop_contrato': P_CMP, 'head': ((1, -6, 0), Z3)}),   # compares
    (5.0, {'left_arm': (CMP_L, Z3), 'prop_contrato': P_CMP, 'head': ((1, -6, 12), Z3)}),  # tilts the head
    (5.5, {'left_arm': (CMP_L, Z3), 'prop_contrato': P_CMP, 'head': ((-11, -4, 4), Z3)}), # short nod
    (5.75, {'left_arm': (CMP_L, Z3), 'prop_contrato': P_CMP, 'head': ((3, -4, 2), Z3)}),
    (6.0, {'left_arm': (CMP_L, Z3), 'prop_contrato': P_CMP, 'head': ((0, -3, 0), Z3)}),
    (6.7, {'left_arm': ((-10, 0, -4), Z3)}),
    (7.4, {})])
e_ = env([(0, 0), (0.8, 1), (6.4, 1), (7.4, 0)])
ears_fn(a, fn_back=lambda t: -10 * e_(t) + 8 * twitch([5.5], 0.3)(t), fn_twist=lambda t: -6 * e_(t))
brows(a, lift=-0.05, tilt=5, fn=e_)
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.14 * curve([(0, 0), (0.8, 1), (2.5, 1), (2.7, 0), (3.2, 0), (3.3, 1),
                                                      (3.9, 1), (4.1, 0), (7.4, 0)])(t), 0.0))
tail_wave(a, 3.0, 2.4)

# ------------------------------------------------------------------ Encarar o horizonte
a = Anim('Encarar o horizonte', 'gesture', 6.2, loop='once')
VISOR = reach('right_arm', (2.0, 32.6, -6.6))          # hand above the goggles, shading the eyes
vis = lambda yaw: {'right_arm': (VISOR, Z3), 'head': ((6, yaw, 0), Z3), 'body': ((-2, 0, 0), Z3)}
keyposes(a, [(0.0, {}), (0.9, vis(14)), (2.0, vis(14)), (3.4, vis(-14)), (4.2, vis(-14)), (4.7, vis(0)),
             (6.2, {})], ease=smooth)
e_ = env([(0, 0), (0.9, 1), (4.7, 1), (6.2, 0)])
ears_fn(a, fn_back=lambda t: -14 * e_(t), fn_twist=lambda t: -8 * e_(t))
brows(a, lift=-0.1, tilt=6, fn=e_)                           # squinting at the distance
tail_pose(a, rx=(8, 2, 0, 0, 0), fn=e_)

# ------------------------------------------------------------------ Afiar a lamina
a = Anim('Afiar a lamina', 'gesture', 8.6, loop='once')
K_HAND = (1.6, 15.2, -6.4)
KNIFE_R = reach('right_arm', K_HAND)
blade_dir = norm((-1.0, 0.12, -0.18))
knife_world = R_to((0, 1, 0), blade_dir)
P_KNIFE = held('prop_faca', KNIFE_R, knife_world)
Hk = hand_world('right_arm', KNIFE_R)


def stone_at(u, lift=0.35):
    """left arm + stone so that the stone sits on the blade at fraction u (0 = base, 1 = tip)"""
    T = Hk + blade_dir * (1.4 + 2.4 * u) + np.array([0, lift, 0])
    r = reach('left_arm', T)
    return {'left_arm': (r, Z3), 'prop_pedra': held('prop_pedra', r, rotmat((0, 90, 0)) @ R_to((0, 0, 1), blade_dir))}


knife = {'right_arm': (KNIFE_R, Z3), 'prop_faca': P_KNIFE, 'head': ((-26, 4, 0), Z3)}
frames = [(0.0, {}), (0.9, merge(knife, stone_at(0.0, 0.8)))]
t0 = 1.3
for k in range(4):                                            # four calm strokes base -> tip
    frames.append((t0, merge(knife, stone_at(0.0))))
    frames.append((t0 + 0.6, merge(knife, stone_at(1.0))))
    frames.append((t0 + 0.9, merge(knife, stone_at(0.5, 0.9))))
    t0 += 0.95
THUMB = reach('left_arm', Hk + blade_dir * 2.6 + np.array([0, -0.15, -0.5]))
thumb = {'left_arm': (THUMB, Z3), 'prop_pedra': held('prop_pedra', THUMB, rotmat((0, 90, 0)))}
SHEATH = reach('right_arm', (4.6, 12.6, -2.6))
frames += [(5.3, merge(knife, thumb, {'head': ((-24, 8, 0), Z3)})),               # tests the edge
           (5.6, merge(knife, thumb, {'head': ((-22, 8, 0), Z3)})),
           (6.1, merge(knife, {'left_arm': ((-8, 0, -6), Z3), 'head': ((-6, 0, 0), Z3)})),   # satisfied
           (6.9, {'right_arm': (SHEATH, Z3), 'prop_faca': held('prop_faca', SHEATH, rotmat((180, 0, 0))),
                  'head': ((-14, -14, 0), Z3)}),                                   # into the sheath
           (7.6, {'right_arm': (SHEATH, Z3), 'head': ((-8, -8, 0), Z3)}),
           (8.6, {})]
keyposes(a, frames)
e_ = env([(0, 0), (0.9, 1), (7.6, 1), (8.6, 0)])
ears_fn(a, fn_back=lambda t: -8 * e_(t) + 18 * twitch([5.45], 0.3)(t), fn_twist=lambda t: -5 * e_(t))
brows(a, lift=-0.06, tilt=3, fn=e_)
tail_wave(a, 2.5, 2.8)

# ------------------------------------------------------------------ Limpar a poeira
a = Anim('Limpar a poeira', 'gesture', 4.4, loop='once')
SLV = (-4.6, 19.4, -3.1)
CH_L, CH_R = (-2.3, 15.4, -2.7), (2.3, 15.4, -2.7)
r_slv, r_slv_in = reach('right_arm', SLV), reach('right_arm', (-4.3, 19.4, -2.5))
r_ch, r_ch_in = reach('right_arm', CH_L), reach('right_arm', (-2.3, 15.4, -2.3))
l_ch, l_ch_in = reach('left_arm', CH_R), reach('left_arm', (2.3, 15.4, -2.3))
proud = {'head': ((7, 0, 0), Z3), 'body': ((-2, 0, 0), Z3)}
keyposes(a, [
    (0.0, {}),
    (0.45, merge(proud, {'right_arm': (r_slv, Z3), 'head': ((-6, 18, 0), Z3)})),
    (0.6, merge(proud, {'right_arm': (r_slv_in, Z3), 'head': ((-6, 18, 0), Z3)})),     # pat
    (0.78, merge(proud, {'right_arm': (r_slv, Z3), 'head': ((-6, 18, 0), Z3)})),
    (0.93, merge(proud, {'right_arm': (r_slv_in, Z3), 'head': ((-6, 18, 0), Z3)})),    # pat
    (1.35, merge(proud, {'right_arm': (r_ch, Z3), 'left_arm': (l_ch, Z3), 'head': ((-10, 0, 0), Z3)})),
    (1.5, merge(proud, {'right_arm': (r_ch_in, Z3), 'left_arm': (l_ch, Z3), 'head': ((-10, 0, 0), Z3)})),
    (1.68, merge(proud, {'right_arm': (r_ch, Z3), 'left_arm': (l_ch_in, Z3), 'head': ((-10, 0, 0), Z3)})),
    (1.86, merge(proud, {'right_arm': (r_ch_in, Z3), 'left_arm': (l_ch, Z3), 'head': ((-10, 0, 0), Z3)})),
    (2.04, merge(proud, {'right_arm': (r_ch, Z3), 'left_arm': (l_ch_in, Z3), 'head': ((-10, 0, 0), Z3)})),
    (2.5, merge(proud, {'right_arm': ((6, 0, 6), (0, -0.5, 0)), 'left_arm': ((6, 0, -6), (0, -0.5, 0))})),  # tug
    (2.8, merge(proud, {'right_arm': ((0, 0, 4), Z3), 'left_arm': ((0, 0, -4), Z3)})),
    (3.6, proud),
    (4.4, {})])


def dust_puff(a, group, times, rest, at, drift=(-0.3, 1.1, -0.9)):
    pts_p, pts_s = [(0, Z3)], [(0, (1, 1, 1))]
    for t0 in times:
        p0 = tuple(np.subtract(at, rest))
        p1 = tuple(np.add(p0, drift))
        # each puff lives 0.3 s (pats are >= 0.33 s apart, so the keys never interleave)
        pts_p += [(t0 - 0.01, Z3), (t0, p0), (t0 + 0.3, p1), (t0 + 0.31, Z3)]
        pts_s += [(t0 - 0.01, (0.02, 0.02, 0.02)), (t0, (0.5, 0.5, 0.5)), (t0 + 0.1, (1.9, 1.9, 1.9)),
                  (t0 + 0.3, (0.3, 0.3, 0.3)), (t0 + 0.31, (1, 1, 1))]
    pts_p.append((a.length, Z3)); pts_s.append((a.length, (1, 1, 1)))
    a.pos(group, curve(pts_p, ease=lambda x: x))
    a.scl(group, curve(pts_s, ease=lambda x: x))


dust_puff(a, 'poeira_ombro', [0.6, 0.93], (-3.0, 22.0, 0.0), (-6.2, 21.9, -2.6))     # beside the patting hand
dust_puff(a, 'poeira_peito', [1.5, 1.86], (0.5, 19.0, 0.0), (0.0, 18.4, -2.9))
e_ = env([(0, 0), (0.45, 1), (3.6, 1), (4.4, 0)])
brows(a, lift=0.04, tilt=-3, fn=e_)
ears_fn(a, fn_back=lambda t: -6 * e_(t) + 10 * twitch([0.6, 1.5], 0.25)(t))
tail_wave(a, 6.0, 1.1)

# ------------------------------------------------------------------ Jogar moeda (loop until the player moves)
L_COIN = 1.8
a = Anim('Jogar moeda', 'custom_pose', L_COIN)
COIN_ARM = reach('right_arm', (2.2, 15.8, -6.6))
flick = curve([(0, 0), (0.08, 0), (0.16, -7), (0.3, 0), (1.38, 0), (1.46, 5), (1.6, 0), (L_COIN, 0)])
def up(t):
    u = (t - 0.14) / 1.24
    return 6.2 * 4 * u * (1 - u) if 0 <= u <= 1 else 0.0

spin = lambda t: 900 * min(1.0, max(0.0, (t - 0.14) / 1.24))
a.rot('right_arm', lambda t: tuple(np.add(COIN_ARM, (flick(t), 0, 0))))
a.rot('prop_moeda', lambda t: held('prop_moeda', COIN_ARM, rotmat((90 + spin(t), 0, 0)))[0])
a.pos('prop_moeda', lambda t: held('prop_moeda', COIN_ARM, np.eye(3), (0, 0.45 + up(t), 0))[1])
a.rot('head', lambda t: (-8 + 3.0 * up(t), 0.0, 0.0))     # follows the coin
for s in 'RL':
    a.pos('iris_' + s, lambda t: (0.0, -0.1 + 0.045 * up(t), 0.0))
brows(a, lift=0.04, tilt=-3)
ears_fn(a, fn_twist=lambda t: 12 * twitch([1.45], 0.3)(t), side='R')
tail_wave(a, 4.0, 1.8)
staged_custom(a, 0.5)

# ------------------------------------------------------------------ Finalizando contrato
a = Anim('Finalizando contrato', 'gesture', 7.4, loop='once')
DESK_L = reach('left_arm', (-1.4, 16.6, -7.4))
desk_paper = rotmat((-58, 0, 0)) @ rotmat((0, 180, 0))       # almost flat, printed side up to the fox
P_DESK = held('prop_contrato', DESK_L, desk_paper)
Hp = hand_world('left_arm', DESK_L)
paper_centre = Hp + rotmat((-58, 0, 0)) @ rotmat((0, 180, 0)) @ np.array([0, 2.0, 0])
pen = lambda dx, dy: reach('right_arm', paper_centre + np.array([dx, 1.6 + dy, 0.4]))
pen_rot = lambda r: held('prop_carvao', r, rotmat((160, 0, 0)))
write = {'left_arm': (DESK_L, Z3), 'prop_contrato': P_DESK, 'head': ((-30, 6, 0), Z3)}
SHOW_L = reach('left_arm', (-8.6, 24.2, -9.4))
P_SHOW = held('prop_contrato', SHOW_L, rotmat((0, -18, 0)))
r0, r1 = pen(-1.4, 0.9), pen(1.2, -0.9)
keyposes(a, [
    (0.0, {}),
    (0.8, write),
    (1.5, merge(write, {'right_arm': (r0, Z3), 'prop_carvao': pen_rot(r0)})),
    (2.6, merge(write, {'right_arm': (r0, Z3), 'prop_carvao': pen_rot(r0)})),
    (3.4, merge(write, {'right_arm': (r1, Z3), 'prop_carvao': pen_rot(r1)})),     # the strike
    (3.9, merge(write, {'right_arm': ((-20, 0, 6), Z3), 'head': ((-22, 0, 0), Z3)})),
    (4.7, {'left_arm': (SHOW_L, Z3), 'prop_contrato': P_SHOW, 'head': ((0, -10, 4), Z3)}),   # shows it: done
    (5.5, {'left_arm': (SHOW_L, Z3), 'prop_contrato': P_SHOW, 'head': ((-4, -10, 4), Z3)}),
    (6.3, {'left_arm': ((-14, 0, -4), Z3), 'prop_contrato': {'s': (1, 0.3, 1)}}),          # folds and stores
    (7.4, {})])
a.pos('contrato_risco', curve([(0, (0, 0, 0)), (2.55, (0, 0, 0)), (2.6, (0, 0, -0.07)), (6.3, (0, 0, -0.07)),
                               (6.35, (0, 0, 0)), (7.4, (0, 0, 0))], ease=lambda x: x))
a.scl('contrato_risco', curve([(0, (1, 1, 1)), (2.55, (1, 1, 1)), (2.6, (0.02, 1, 1)), (3.4, (1, 1, 1)),
                               (7.4, (1, 1, 1))]))
e_ = env([(0, 0), (0.8, 1), (6.3, 1), (7.4, 0)])
done = env([(0, 0), (3.4, 0), (3.9, 1), (6.3, 1), (7.4, 0)])
brows(a, lift=-0.04, tilt=4, fn=lambda t: e_(t) * (1 - done(t)))
brows(a, lift=0.05, tilt=-4, fn=done)
ears_fn(a, fn_back=lambda t: -8 * e_(t) - 6 * done(t), fn_twist=lambda t: -6 * e_(t))
for i, b in enumerate(TAIL):
    a.rot(b, lambda t, i=i: (0.0, 10 * 1.1 ** i * math.sin(2 * math.pi * (t / 0.55 - 0.12 * i)) * done(t), 0.0))

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
