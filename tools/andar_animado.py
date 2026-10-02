"""More animated walk, leaning further forward (rebuilds the walking posture and the walking body sway).

usage: python3 tools/andar_animado.py <in.bbmodel> <out.bbmodel>

- 'Andando - postura' (walking pose, fixed, additive): torso leans 8 deg forward around the hips; head, shoulders
  and arms follow the torso (positions too), the head lifts the look back up, arms a bit forward and loose.
- 'Andando - balanco do corpo' (global, on corpo_mov): stronger bob (twice per stride), weight roll and shoulder
  twist at Minecraft's stride tempo.
Everything stays additive (Better Combat / TACZ keep working).
"""
import json, sys, os, math
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
FPS = 20

# 'cabeca_mov': group inside the head holding everything the head carries; the walking nod moves it (never the
# vanilla head, so the look direction stays Minecraft's / the mods')
import copy as _copy, uuid as _uuid
_G = {g['uuid']: g for g in d['groups']}


def _node(ns, name):
    for n in ns:
        if isinstance(n, dict):
            if _G[n['uuid']]['name'] == name:
                return n
            r = _node(n['children'], name)
            if r:
                return r


if not any(g['name'] == 'cabeca_mov' for g in d['groups']):
    _h = _node(d['outliner'], 'head')
    _g = _copy.deepcopy(_G[_h['uuid']])
    _g.update(name='cabeca_mov', uuid=str(_uuid.uuid4()), origin=[0, 24, 0], rotation=[0, 0, 0])
    d['groups'].append(_g)
    _h['children'] = [{'uuid': _g['uuid'], 'isOpen': False, 'children': _h['children']}]
n_groups = len(d['groups'])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animlib.py')).read())
LEAN = float(os.environ.get('LEAN', '-8'))
S = 0.55


def upper(x=0.0, y=0.0, z=0.0, drop=(0, 0, 0)):
    r = rig(torso=(x, y, z), drop=drop)
    return {b: r[b] for b in ('body', 'right_arm', 'left_arm', 'head')}


p = Anim('Andando - postura', 'walking', 1.0)
up = upper(LEAN)
p.rot('body', c(up['body'][0])).pos('body', c(up['body'][1]))
p.pos('head', c(up['head'][1])).rot('head', c((-LEAN * 0.75, 0.0, 0.0)))     # keeps looking ahead
for b, sgn in (('right_arm', 1), ('left_arm', -1)):
    p.rot(b, c(add3(up[b][0], (6.0, -sgn * 3.0, sgn * 4.0)))).pos(b, c(up[b][1]))
for b, sgn in (('right_leg', 1), ('left_leg', -1)):
    p.rot(b, c((0.0, sgn * 1.5, sgn * 0.75)))

g = Anim('Andando - balanco do corpo', 'global', S * 8, priority=-10)
bob = lambda t: 0.5 * (1 - math.cos(4 * math.pi * t / S))
roll = lambda t: math.sin(2 * math.pi * t / S)
twist = lambda t: math.sin(2 * math.pi * (t / S + 0.25))
memo = {}


def at(t):
    k = round(t, 4)
    if k not in memo:
        memo[k] = upper(-2.0 * bob(t), 6.0 * twist(t), 2.8 * roll(t), drop=(0, -0.55 * bob(t), 0))
    return memo[k]


g.rot('corpo_mov', lambda t: tuple(at(t)['body'][0]))
g.pos('corpo_mov', lambda t: tuple(at(t)['body'][1]))
# head: rides on the torso (moves with the bob and the lean of the shoulders), nods a moment after each step,
# tilts against the roll and turns a little against the twist (keeps the look steady)
nod = lambda t: 0.5 * (1 - math.cos(4 * math.pi * (t - 0.04) / S))
HEAD = float(os.environ.get('HEAD', '1'))             # head motion amount (1 = v16.33)
g.pos('cabeca_mov', lambda t: add3(at(t)['head'][1], (0.0, -0.1 * HEAD * nod(t), 0.0)))
g.rot('cabeca_mov', lambda t: (HEAD * (2.4 * nod(t) - 1.0), -3.5 * HEAD * twist(t - 0.05), -2.2 * HEAD * roll(t - 0.06)))

new = {an.name: an.to_json() for an in (p, g)}
for i, a in enumerate(d['animations']):
    if a['name'] in new and a['cpm_type'] == new[a['name']]['cpm_type']:
        j = new[a['name']]
        j['cpm_order'] = a.get('cpm_order', 0)
        d['animations'][i] = j
# the rests that switch the walking sway off in every other state also hold the head group still
E = 0.02
for a in d['animations']:
    if not a['cpm_additive'] and GRP['corpo_mov']['uuid'] in a['animators'] and GRP['cabeca_mov']['uuid'] not in a['animators']:
        src = a['animators'][GRP['corpo_mov']['uuid']]
        a['animators'][GRP['cabeca_mov']['uuid']] = {
            'name': 'cabeca_mov', 'type': 'bone',
            'keyframes': [dict(k, uuid=str(uuid.uuid4()), data_points=[{'x': E, 'y': 0.0, 'z': 0.0} if k['channel'] == 'rotation'
                                                                       else {'x': 0.0, 'y': E, 'z': 0.0}])
                          for k in src['keyframes']]}
d['name'] = os.path.basename(OUT).rsplit('.', 1)[0]
json.dump(d, open(OUT, 'w'))
print('ok')
