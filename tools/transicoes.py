"""Smooth hand-overs between walking, running and jumping (all additive: Better Combat / TACZ keep working).

usage: python3 tools/transicoes.py <in.bbmodel> <out.bbmodel>

CPM can not blend into the walking pose (it keeps re-entering it), so the trick is to make the neighbours START and
END on the walking posture:
- running entry (p:running setup, 0.4 s) starts on the walking posture and eases to the running lean;
- jumping ('Pulando - corpo', additive) carries the walking posture the whole jump, so walk -> jump -> walk / run
  never straightens up; on top: a push (arms down, legs back), the tuck (legs up one after the other, arms up and
  out), reaching for the ground and a small head nod; it returns to the posture before landing.
"""
import json, sys, os, math, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preview_anim import lerp_keys

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
G = {g['name']: g['uuid'] for g in d['groups']}
A = {(a['name'], a['cpm_type']): a for a in d['animations']}
post = A[('Andando - postura', 'walking')]
sm = lambda x: max(0.0, min(1.0, x)) ** 2 * (3 - 2 * max(0.0, min(1.0, x)))
POST = {}                                        # (group uuid, channel) -> walking posture value
for u, an in post['animators'].items():
    for ch in ('rotation', 'position'):
        ks = [k for k in an['keyframes'] if k['channel'] == ch]
        if ks:
            POST[(u, ch)] = lerp_keys(ks, 0)


def kf(ch, t, v):
    return {'channel': ch, 'data_points': [{'x': round(v[0], 3), 'y': round(v[1], 3), 'z': round(v[2], 3)}],
            'uuid': str(uuid.uuid4()), 'time': round(t, 4), 'color': -1, 'interpolation': 'linear'}


# ---------------- running entry: 0.4 s, from the walking posture to the running lean
setup = next(a for a in d['animations'] if a['name'] in ('p:running', 'p:running2') and a['cpm_type'] == 'setup')
L0, L = setup['length'], 0.4
for an in setup['animators'].values():
    for k in an['keyframes']:
        k['time'] = round(k['time'] * L / L0, 4)
setup['length'] = L
N = int(round(L / 0.05))
for (u, ch), wv in POST.items():
    an = setup['animators'].setdefault(u, {'name': next(n for n, x in G.items() if x == u), 'type': 'bone', 'keyframes': []})
    old = [k for k in an['keyframes'] if k['channel'] == ch]
    new = []
    for i in range(N + 1):
        t = i * L / N
        base = lerp_keys(old, t) if old else [0, 0, 0]
        f = 1 - sm(t / L)
        new.append(kf(ch, t, [b + w * f for b, w in zip(base, wv)]))
    an['keyframes'] = [k for k in an['keyframes'] if k['channel'] != ch] + new

# ---------------- jumping body (additive): walking posture + jump motion that is zero at take-off and landing
JL = 0.6
push = lambda t: math.sin(math.pi * min(1.0, t / 0.12)) if t < 0.12 else 0.0
tuck_r = lambda t: sm((t - 0.06) / 0.14) * (1 - sm((t - 0.3) / 0.16))
tuck_l = lambda t: sm((t - 0.1) / 0.14) * (1 - sm((t - 0.33) / 0.15))
reach = lambda t: sm((t - 0.3) / 0.1) * (1 - sm((t - 0.42) / 0.08))
arms = lambda t: sm((t - 0.04) / 0.14) * (1 - sm((t - 0.3) / 0.18))
MOTION = {
    'right_leg': lambda t: (-8 * push(t) + 26 * tuck_r(t) + 4 * reach(t), 0.0, 0.0),
    'left_leg': lambda t: (-6 * push(t) + 18 * tuck_l(t) - 3 * reach(t), 0.0, 0.0),
    'right_arm': lambda t: (-6 * push(t) + 10 * arms(t), 0.0, 9 * arms(t)),
    'left_arm': lambda t: (-6 * push(t) + 9 * arms(t - 0.02), 0.0, -10 * arms(t - 0.02)),
    'head': lambda t: (-3 * push(t) + 4 * arms(t - 0.04) - 5 * reach(t), 0.0, 0.0),
    'body': lambda t: (2 * push(t) - 2 * arms(t), 0.0, 0.0),
}
animators = {}
for name, fn in MOTION.items():
    u = G[name]
    keys = []
    for i in range(int(JL * 20) + 1):
        t = i / 20
        pv = POST.get((u, 'rotation'), [0, 0, 0])
        keys.append(kf('rotation', t, [a + b for a, b in zip(pv, fn(t))]))
    if (u, 'position') in POST:
        keys.append(kf('position', 0.0, POST[(u, 'position')]))
    animators[u] = {'name': name, 'type': 'bone', 'keyframes': keys}
jump = dict(post, uuid=str(uuid.uuid4()), name='Pulando - corpo', cpm_type='jumping', length=JL, animators=animators,
            cpm_order=0)
d['animations'] = [a for a in d['animations'] if a['name'] != 'Pulando - corpo'] + [jump]
d['name'] = os.path.basename(OUT).rsplit('.', 1)[0]
json.dump(d, open(OUT, 'w'))
print('ok')
