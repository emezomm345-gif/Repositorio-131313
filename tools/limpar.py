"""Removes what the model no longer uses (keeps everything visible or animated).

usage: python3 tools/limpar.py <in.bbmodel> <out.bbmodel>

- elements hidden in Blockbench (except the vanilla 'hat' box of the head) or with no visible pixel on any face;
- groups left empty by that, and every animation track that pointed to them;
- animations left without any track, and orphan entry/exit transitions;
- texture pixels that no face uses (cleared to transparent).
"""
import json, sys, math, base64, io, collections
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
G = {g['uuid']: g for g in d['groups']}
E = {e['uuid']: e for e in d['elements']}
T = np.array(Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA'))
KEEP = {'hat'}


def rect(fc):
    u0, v0, u1, v1 = fc['uv']
    return int(min(v0, v1)), int(math.ceil(max(v0, v1))), int(min(u0, u1)), int(math.ceil(max(u0, u1)))


def visible(e):
    for fc in e['faces'].values():
        if fc.get('texture') is None:
            continue
        y0, y1, x0, x1 = rect(fc)
        a = T[y0:y1, x0:x1, 3]
        if a.size and a.max() > 0:
            return True
    return False


drop_e = {u for u, e in E.items() if e['name'] not in KEEP and (e.get('visibility') is False or not visible(e))}


def prune(nodes):
    out = []
    for n in nodes:
        if isinstance(n, dict):
            n['children'] = prune(n['children'])
            if n['children']:
                out.append(n)
        elif n not in drop_e:
            out.append(n)
    return out


d['outliner'] = prune(d['outliner'])
alive = set()


def collect(nodes):
    for n in nodes:
        if isinstance(n, dict):
            alive.add(n['uuid'])
            collect(n['children'])


collect(d['outliner'])
drop_g = [G[u]['name'] for u in G if u not in alive]
d['groups'] = [g for g in d['groups'] if g['uuid'] in alive]
d['elements'] = [e for e in d['elements'] if e['uuid'] not in drop_e]

removed_tracks = 0
for a in d['animations']:
    for u in list(a['animators']):
        if u not in alive:
            del a['animators'][u]
            removed_tracks += 1
empty = [a['name'] for a in d['animations'] if not a['animators']]
d['animations'] = [a for a in d['animations'] if a['animators']]

# orphan entry / exit transitions (their pose / emote no longer exists)
poses = {a['cpm_type'] for a in d['animations'] if a['cpm_type'] not in ('setup', 'finish')}
named = {a['name'].split('#')[0] for a in d['animations'] if a['cpm_type'] in ('custom_pose', 'layer', 'gesture')}


def linked(a):
    k, _, n = a['name'].partition(':')
    cands = (n, n[:-1]) if n[-1:].isdigit() else (n,)
    return any((k == 'p' and c in poses) or (k in 'cg' and c in named) for c in cands)


orphans = [a['name'] for a in d['animations'] if a['cpm_type'] in ('setup', 'finish') and not linked(a)]
d['animations'] = [a for a in d['animations'] if not (a['cpm_type'] in ('setup', 'finish') and not linked(a))]

# texture: clear pixels no face uses
used = np.zeros(T.shape[:2], bool)
for e in d['elements']:
    for fc in e['faces'].values():
        if fc.get('texture') is not None:
            y0, y1, x0, x1 = rect(fc)
            used[y0:y1, x0:x1] = True
cleared = int(((T[..., 3] > 0) & ~used).sum())
T[~used] = 0
buf = io.BytesIO()
Image.fromarray(T).save(buf, 'PNG', optimize=True)
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
json.dump(d, open(OUT, 'w'))
print('elements removed:', sorted(E[u]['name'] for u in drop_e))
print('groups removed:', drop_g)
print('animation tracks removed:', removed_tracks, '| empty animations removed:', empty, '| orphan transitions:', orphans)
print('texture pixels cleared:', cleared)
