"""Bounty hunters (Cacadores de recompensas) variant: animated accessories + bounty-hunter emotes.

usage: python3 tools/cacadores_emotes.py <variant.bbmodel built by variante.py --acessorios cacadores> <out.bbmodel>

- Accessories in motion: the bandana tip swings (idle sway, steps, wind when running / falling), the goggles bounce
  with the steps and jumps.
- Emote: Jogar moeda (loop until the player moves; the coin rests hidden inside the right arm).
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
REST = {'prop_moeda': (5.625, 20.625, 0.0)}
ARM_OF = {'prop_moeda': 'right_arm'}


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
