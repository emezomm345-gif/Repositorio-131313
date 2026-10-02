"""Running variants that leave the arms to Minecraft / other mods (Better Combat, TACZ...).

usage: python3 tools/compat_corrida.py <in.bbmodel> <out.bbmodel> A|B|C

In every variant the recreated attack arm ('Atacando (...) - braco', non-additive) is removed: the attack swing is
Minecraft's / Better Combat's again.
A  arms and legs: Minecraft / mods. Our running body stays (lean, shoulder twist, bob, head, tail), the arms
   follow the torso (position and tilt).
B  legs: our running stride (non-additive); arms: Minecraft / mods. Body as in A.
C  arms and legs: Minecraft / mods, and our running body never rotates the arms (only moves the shoulders with
   the torso): the arm angles are exactly what the mod sets (aiming with TACZ stays exact).
"""
import json, sys

SRC, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3].upper()
d = json.load(open(SRC))
G = {g['name']: g['uuid'] for g in d['groups']}
ARMS = (G['right_arm'], G['left_arm'])
keep = []
for a in d['animations']:
    if a['name'] in ('Atacando (direita) - braco', 'Atacando (esquerda) - braco'):
        continue
    if a['name'] == 'Correndo - passos':
        if MODE in ('A', 'C'):
            continue
        for u in ARMS:
            a['animators'].pop(u, None)
    if MODE == 'C' and a['name'] in ('Correndo - corpo', 'p:running', 'p:running2'):
        for u in ARMS:
            an = a['animators'].get(u)
            if an:
                an['keyframes'] = [k for k in an['keyframes'] if k['channel'] != 'rotation']
                if not an['keyframes']:
                    del a['animators'][u]
    if MODE == 'A' and a['name'] == 'Correndo - corpo':
        # arms tilt with the torso and swing a bit forward / out (additive, on top of Minecraft's / the mod's arm)
        body = [k for k in a['animators'][G['body']]['keyframes'] if k['channel'] == 'rotation']
        for u, side in ((G['right_arm'], 1), (G['left_arm'], -1)):
            an = a['animators'].setdefault(u, {'name': 'right_arm' if side > 0 else 'left_arm', 'type': 'bone',
                                               'keyframes': []})
            for k in body:
                dp = k['data_points'][0]
                an['keyframes'].append(dict(k, uuid=k['uuid'][:-4] + ('a1b2' if side > 0 else 'c3d4'),
                                            data_points=[{'x': round(float(dp['x']) + 16.0, 3), 'y': dp['y'],
                                                          'z': round(float(dp['z']) + 6.0 * side, 3)}]))
    keep.append(a)
d['animations'] = keep
d['name'] = OUT.rsplit('/', 1)[-1].rsplit('.', 1)[0]
json.dump(d, open(OUT, 'w'))
print(MODE, 'ok', len(d['animations']), 'animations')
