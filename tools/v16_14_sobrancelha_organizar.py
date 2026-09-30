"""v16.14: retexture the eyebrows ("Palbebra") and tidy up the outliner.

Nothing is moved: no element from/to/origin/rotation and no group origin/rotation is changed.
Only the eyebrow face UVs, a few unused texture pixels, and names/grouping change.

usage: python3 tools/v16_14_sobrancelha_organizar.py <in.bbmodel> <out.bbmodel>
"""
import json, base64, io, os, sys, copy, uuid
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))
tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
T = tex.load()
groups = {g['uuid']: g for g in d['groups']}
els = {e['uuid']: e for e in d['elements']}

# ---------------------------------------------------------------- eyebrow texture
# 4 px per unit, colours from the skin: highlight on top, fur in the middle, dark line over the eye.
H, M, K = (45, 45, 45), (30, 28, 27), (12, 12, 12)
U, V = 16, 52                      # unused, transparent texture area
for y in range(V, V + 5):
    for x in range(U, U + 8):
        assert T[x, y][3] == 0, 'texture area not free'
for x in range(6):                 # front 6x3 at (16,52)
    for y, c in enumerate((H, M, K)):
        T[U + x, V + y] = c + (255,)
for y, c in enumerate((H, M, K)):  # side 1x3 at (22,52)
    T[U + 6, V + y] = c + (255,)
for x in range(6):
    T[U + x, V + 3] = H + (255,)   # top    6x1 at (16,55)
    T[U + x, V + 4] = K + (255,)   # bottom 6x1 at (16,56)

# The brows are rotated 180° on Z, so every UV is given rotated 180° (u and v swapped end for end)
# and the local "down" face is the one that ends up on top.
BROW_FACES = {
    'north': {'uv': [U + 6, V + 3, U, V], 'texture': 0},
    'east':  {'uv': [U + 7, V + 3, U + 6, V], 'texture': 0},
    'west':  {'uv': [U + 7, V + 3, U + 6, V], 'texture': 0},
    'down':  {'uv': [U + 6, V + 4, U, V + 3], 'texture': 0},   # visible on top
    'up':    {'uv': [U + 6, V + 5, U, V + 4], 'texture': 0},   # visible underneath
    'south': {'uv': [127, 127, 128, 128], 'texture': 0},       # inside the head
}


# ---------------------------------------------------------------- helpers
def node(gid, nodes=None):
    for n in (d['outliner'] if nodes is None else nodes):
        if isinstance(n, dict):
            if n['uuid'] == gid:
                return n
            f = node(gid, n['children'])
            if f:
                return f


def group_named(name):
    return next(g for g in d['groups'] if g['name'] == name)


def rename_group(old, new):
    group_named(old)['name'] = new


def child_elements(gname):
    return [els[c] for c in node(group_named(gname)['uuid'])['children'] if isinstance(c, str)]


# ---------------------------------------------------------------- eyebrows
rename_group('Palbebra', 'sobrancelhas')
for e in child_elements('sobrancelhas'):
    e['name'] = 'sobrancelha_R' if e['origin'][0] > 0 else 'sobrancelha_L'
    e['faces'] = copy.deepcopy(BROW_FACES)

# ---------------------------------------------------------------- names
rename_group('Iris olho', 'olhos')
rename_group('Orelhas', 'orelhas')
rename_group('r', 'orelha_R')
rename_group('ear_L', 'orelha_L')
rename_group('bone3', 'focinho')
for e in child_elements('focinho'):
    if e['name'] == 'snout':
        e['name'] = 'snout_top' if e['rotation'][0] > -10 else 'snout_bottom'

# ---------------------------------------------------------------- cheeks into their own group
# (group rotation 0 -> nothing moves)
head = node(group_named('head')['uuid'])
cheeks = [c for c in head['children'] if isinstance(c, str) and els[c]['name'] in ('cheek_R', 'cheek_L')]
g = copy.deepcopy(group_named('focinho'))
g.update(name='bochechas', uuid=str(uuid.uuid4()), origin=[0, 25.5, -2.5], rotation=[0, 0, 0])
d['groups'].append(g)
i = head['children'].index(cheeks[0])
for c in cheeks:
    head['children'].remove(c)
head['children'].insert(i, {'uuid': g['uuid'], 'isOpen': False, 'children': cheeks})

# ---------------------------------------------------------------- order inside head:
# base cube, face (olhos, sobrancelhas, focinho, bochechas), orelhas, pelos
ORDER = ['head', 'hat', 'olhos', 'sobrancelhas', 'focinho', 'bochechas', 'orelhas', 'fur_head']


def key(c):
    name = els[c]['name'] if isinstance(c, str) else groups.get(c['uuid'], g)['name']
    return ORDER.index(name) if name in ORDER else len(ORDER)


head['children'].sort(key=key)


def close(nodes):
    for n in nodes:
        if isinstance(n, dict):
            n['isOpen'] = False
            close(n['children'])


close(d['outliner'])

# ---------------------------------------------------------------- save
d['textures'][0]['name'] = d['textures'][0]['relative_path'] = 'Emezomm-CPM_v16_14_128_tufos.png'
buf = io.BytesIO(); tex.save(buf, 'PNG')
d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
json.dump(d, open(OUT, 'w'))
tex.save(os.path.join(os.path.dirname(OUT) or '.', d['textures'][0]['name']))
print('ok')
