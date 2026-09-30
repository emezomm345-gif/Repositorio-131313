"""v16.20 fixes (from v16.19), nothing else touched:

1. CPM export error "Skin Layer settings don't support custom poses and gestures":
   the project's cpm_data now carries the animation encoding settings with the 6 skin layers free
   (hat, jacket, sleeves, pants legs) - same setup as the Plantifox reference model.
2. Flicker on the 2D fur planes: every thin plane (thickness < 0.1) that had BOTH opposite faces textured
   keeps only the face that points outwards; the opposite face gets uv [0,0,0,0] + texture null, which is
   what the CPM exporter treats as "no face". Size, position, rotation, UV and texture of the kept face
   are unchanged.
3. fur_chest_7 was an exact copy of fur_chest_6 in the same place (coplanar duplicate) -> removed.

usage: python3 tools/v16_20_correcoes.py <in.bbmodel> <out.bbmodel>
"""
import json, sys

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC))

# ---------------------------------------------------------------- 1. animation encoding (skin layers)
data = json.loads(d.get('cpm_data') or '{}')
data['anims'] = data.get('anims') or {}
data['anims'].setdefault('anims', {})
data['anims']['free'] = ['hat', 'jacket', 'left_pants_leg', 'right_pants_leg', 'left_sleeve', 'right_sleeve']
data['anims'].setdefault('def', {})
d['cpm_data'] = json.dumps(data, separators=(',', ':'))

# ---------------------------------------------------------------- 2. one textured face per thin plane
NO_FACE = {'uv': [0, 0, 0, 0], 'texture': None}
PAIRS = (('north', 'south', 2), ('east', 'west', 0), ('up', 'down', 1))


def textured(f):
    return f is not None and f.get('texture') is not None and list(f.get('uv', [0, 0, 0, 0]))[:2] != [127, 127] \
        and any(f.get('uv', [0, 0, 0, 0]))


def keep_face(e, a, b):
    """Which of the two opposite faces points outwards (the one that stays textured)."""
    n = e['name']
    if n.endswith('_tufts_behind'):
        return b            # ear tuft behind the ear: seen from the back
    return a                # fur cards, ear tufts, cheeks: their north face is the outer/front side


fixed = []
for e in d['elements']:
    size = [e['to'][i] - e['from'][i] for i in range(3)]
    for a, b, ax in PAIRS:
        if size[ax] < 0.1 and textured(e['faces'].get(a)) and textured(e['faces'].get(b)):
            k = keep_face(e, a, b)
            drop = b if k == a else a
            e['faces'][drop] = dict(NO_FACE)
            fixed.append((e['name'], k, drop))

# ---------------------------------------------------------------- 3. exact duplicate
dup = next((e for e in d['elements'] if e['name'] == 'fur_chest_7'), None)
if dup:
    d['elements'].remove(dup)

    def drop(nodes):
        for n in nodes:
            if isinstance(n, dict):
                if dup['uuid'] in n['children']:
                    n['children'].remove(dup['uuid'])
                drop(n['children'])
    drop(d['outliner'])

d['name'] = 'skin_v16.20'
json.dump(d, open(OUT, 'w'))
print('planes fixed: %d, duplicate removed: %s' % (len(fixed), bool(dup)))
for f in fixed[:200]:
    print('  %-28s keeps %-5s  removes %s' % f)
