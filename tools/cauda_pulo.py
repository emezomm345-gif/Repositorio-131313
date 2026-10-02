"""Tail lower when jumping and in creative flight (it rose too much, also because the body leans while jumping).

usage: python3 tools/cauda_pulo.py <in.bbmodel> <out.bbmodel>
Tail lift (x rotation) in the jumping / creative-flight animations and their entry / exit is cut to 25% (the
sway stays); while jumping the tail base also compensates the 8 deg forward lean of the body it hangs from.
"""
import json, sys, uuid

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
G = {g['uuid']: g['name'] for g in d['groups']}
TAIL = ('cauda', 'cauda_1', 'cauda_2', 'cauda_3', 'cauda_ponta')
for a in d['animations']:
    if not (a['cpm_type'] in ('jumping', 'creative_flying') or a['name'].rstrip('2') in ('p:jumping', 'p:creative_flying')):
        continue
    for u, an in a['animators'].items():
        if G[u] in TAIL:
            for k in an['keyframes']:
                if k['channel'] == 'rotation':
                    dp = k['data_points'][0]
                    dp['x'] = round(float(dp['x']) * 0.25, 3)
    if a['name'] == 'Pulando' and a['cpm_type'] == 'jumping':
        tail = next(u for u in a['animators'] if G[u] == 'cauda')
        for k in a['animators'][tail]['keyframes']:
            if k['channel'] == 'rotation':
                k['data_points'][0]['x'] = round(float(k['data_points'][0]['x']) + 8.0, 3)
d['name'] = OUT.rsplit('/', 1)[-1].rsplit('.', 1)[0]
json.dump(d, open(OUT, 'w'))
print('ok')
