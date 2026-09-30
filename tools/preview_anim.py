"""Renders frames of the animations stored in a .bbmodel (reads the keyframes back from the file).

usage: python3 tools/preview_anim.py <model.bbmodel> <out.png> "<anim name>" [...]
"""
import sys, json, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from render import load, render
from PIL import Image, ImageDraw


def lerp_keys(kfs, t):
    kfs = sorted(kfs, key=lambda k: k['time'])
    if t <= kfs[0]['time']:
        k = kfs[0]
        return [float(k['data_points'][0][a]) for a in 'xyz']
    for k0, k1 in zip(kfs, kfs[1:]):
        if t <= k1['time']:
            f = (t - k0['time']) / (k1['time'] - k0['time'])
            return [float(k0['data_points'][0][a]) + (float(k1['data_points'][0][a]) - float(k0['data_points'][0][a])) * f
                    for a in 'xyz']
    return [float(kfs[-1]['data_points'][0][a]) for a in 'xyz']


def pose_at(anims, t):
    pose = {}
    for an in anims:
        for bone in an['animators'].values():
            r, p, s = [0, 0, 0], [0, 0, 0], [1, 1, 1]
            for ch in ('rotation', 'position', 'scale'):
                ks = [k for k in bone['keyframes'] if k['channel'] == ch]
                if not ks:
                    continue
                v = lerp_keys(ks, t % an['length'] if an['length'] else 0)
                if ch == 'rotation':
                    r = [-v[0], -v[1], v[2]]
                elif ch == 'position':
                    p = [-v[0], v[1], v[2]]
                else:
                    s = v
            old = pose.get(bone['name'], ((0, 0, 0), (0, 0, 0), (1, 1, 1)))
            pose[bone['name']] = (tuple(a + b for a, b in zip(old[0], r)), tuple(a + b for a, b in zip(old[1], p)),
                                  tuple(a * b for a, b in zip(old[2], s)))
    return pose


VIEWS = {
    'face': dict(yaw=20, pitch=5, size=(260, 260), center=(0, 28.5, -3), scale=26),
    'tail': dict(yaw=120, pitch=12, size=(260, 260), center=(0, 13, 6), scale=13),
    'back': dict(yaw=180, pitch=8, size=(260, 260), center=(0, 20, 3), scale=11),
}

if __name__ == '__main__':
    path, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    d = json.load(open(path))
    anims = {a['name']: a for a in d['animations']}
    rows = []
    for n in names:
        an = anims[n]
        times = [an['length'] * i / 5 for i in range(5)]
        row = []
        for view in ('face', 'tail', 'back'):
            for t in times:
                q, tex, _ = load(path, pose=pose_at([an], t), data=d)
                im = render(q, tex, **VIEWS[view])
                ImageDraw.Draw(im).text((4, 4), '%s %s t=%.2f' % (n[:18], view, t), fill=(0, 0, 0))
                row.append(im)
        rows.append(row)
    W, H = 260, 260
    sheet = Image.new('RGB', (W * 15, H * len(rows)), (255, 255, 255))
    for j, row in enumerate(rows):
        for i, im in enumerate(row):
            sheet.paste(im, (i * W, j * H))
    sheet.save(out)
