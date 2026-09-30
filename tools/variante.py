"""Variants of Emezomm (L.A.S.T universe and others): same model, same face, same animations -
only the texture of the body / arms / legs changes (the outfit), plus optionally the fur colour.

usage: python3 tools/variante.py <base.bbmodel> <skin64.png> <out.bbmodel> [--hide group,...] [--lambda]

- The 64x64 skin is read in the standard Minecraft layout; the outer layer (jacket, sleeves, pants) is
  kept for the second-layer shell (see below). Pixels with alpha < 128 are ignored (eraser leftovers).
- The head is never touched (the face is the same in every variant).
- Each face of body / arms / legs is redrawn at the model resolution (2 px per unit): Scale2x keeps the pixel-art
  look but smooths diagonals, then a light fabric finish (dither on large flat areas, soft shading from top
  to bottom and a darker seam where two materials meet).
- The outer layer is ALSO drawn on the model's own second-layer shell (jacket / sleeves / pants, 0.15 bigger
  than the body), like vanilla Minecraft, at the same 2 px per unit. It does not fit in the 128x128 atlas, so
  the variant's texture is 256x256: the whole 128 atlas stays in the top-left corner with the same UVs and the
  second layer goes into the new space.
- --lambda: the orange mark on the chest becomes a crisp orange lambda symbol.
- Tufts covered by the clothes (--hide) are pointed at a transparent texel: the geometry stays, they just
  don't show.
"""
import sys, json, base64, io, zlib
import numpy as np
from PIL import Image

LIMBS = {  # model element -> standard skin origin of (base, overlay) box, box size (w, h, d)
    'body': ((16, 16), (16, 32), (8, 12, 4)),
    'right_arm': ((40, 16), (40, 32), (4, 12, 4)),
    'left_arm': ((32, 48), (48, 48), (4, 12, 4)),
    'right_leg': ((0, 16), (0, 32), (4, 12, 4)),
    'left_leg': ((16, 48), (0, 48), (4, 12, 4)),
}


def box_faces(ox, oy, w, h, dd):
    """standard skin box layout -> {blockbench face: (x, y, w, h)}; +X = the character's right = east."""
    return {'east': (ox, oy + dd, dd, h), 'north': (ox + dd, oy + dd, w, h),
            'west': (ox + dd + w, oy + dd, dd, h), 'south': (ox + 2 * dd + w, oy + dd, w, h),
            'up': (ox + dd, oy, w, dd), 'down': (ox + dd + w, oy, w, dd)}


def scale2x(a):
    """EPX / Scale2x on an RGBA array (h, w, 4) -> (2h, 2w, 4)."""
    h, w = a.shape[:2]
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    out = np.zeros((2 * h, 2 * w, 4), a.dtype)
    eq = lambda x, y: np.all(x == y, axis=-1)
    for y in range(h):
        for x in range(w):
            P = p[y + 1, x + 1]
            A, B, C, D = p[y, x + 1], p[y + 1, x + 2], p[y + 1, x], p[y + 2, x + 1]   # up, right, left, down
            o = [P.copy() for _ in range(4)]
            if eq(C, A) and not eq(C, D) and not eq(A, B):
                o[0] = A
            if eq(A, B) and not eq(A, C) and not eq(B, D):
                o[1] = B
            if eq(D, C) and not eq(D, B) and not eq(C, A):
                o[2] = C
            if eq(B, D) and not eq(B, A) and not eq(D, C):
                o[3] = D
            out[2 * y, 2 * x], out[2 * y, 2 * x + 1], out[2 * y + 1, 2 * x], out[2 * y + 1, 2 * x + 1] = o
    return out


def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def finish(a, seed=0):
    """Light fabric finish on an upscaled face (keeps the palette readable, no realism)."""
    a = a.astype(float)
    h, w = a.shape[:2]
    L = lum(a)
    rgb = a[..., :3]
    # soft light from the top: +4% at the top edge -> -5% at the bottom edge
    k = np.linspace(1.04, 0.95, h)[:, None, None]
    rgb *= k
    # seams: a pixel next to a clearly darker material gets a touch darker (reads as a fold / stitch)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = np.roll(np.roll(L, dy, 0), dx, 1)
        edge = (L - nb) > 60
        if dy == 1: edge[0, :] = False
        if dy == -1: edge[-1, :] = False
        if dx == 1: edge[:, 0] = False
        if dx == -1: edge[:, -1] = False
        rgb[edge] *= 0.9
    # dither on flat areas (checker, +-1.2 %), so big panels are not a single flat colour
    yy, xx = np.mgrid[0:h, 0:w]
    rng = np.random.default_rng(seed)
    flat = np.ones((h, w), bool)
    for dy, dx in ((0, 1), (1, 0)):
        flat &= np.abs(L - np.roll(np.roll(L, dy, 0), dx, 1)) < 8
    noise = np.where((xx + yy) % 2 == 0, 1.012, 0.988) * (1 + rng.uniform(-0.006, 0.006, (h, w)))
    rgb[flat] *= noise[flat][:, None]
    a[..., :3] = np.clip(rgb, 0, 255)
    return a.round().astype(np.uint8)


LAMBDA = ["AA....",
          ".AB...",
          ".AB...",
          "..AB..",
          "..AB..",
          ".A.AB.",
          ".A.AB.",
          "A...AB"]


def draw_lambda(face, x0=5, y0=1):
    """Orange lambda on the white shirt of the body front (16 x 24 px face); B = shade of the long stroke."""
    col = {'A': (255, 128, 20, 255), 'B': (214, 92, 8, 255)}
    for j, row in enumerate(LAMBDA):
        for i, ch in enumerate(row):
            if ch in col:
                face[y0 + j, x0 + i] = col[ch]


def main():
    base, skin_path, out = sys.argv[1:4]
    hide, lam = [], '--lambda' in sys.argv
    if '--hide' in sys.argv:
        hide = sys.argv[sys.argv.index('--hide') + 1].split(',')
    d = json.load(open(base))
    tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
    T = np.zeros((256, 256, 4), np.uint8)
    T[:128, :128] = np.array(tex)                       # old atlas: same pixels, same UVs
    sk = np.array(Image.open(skin_path).convert('RGBA'))
    sk[sk[..., 3] < 128] = 0
    ORANGE = lambda c: (c[..., 0] > 200) & (c[..., 1] < 170) & (c[..., 2] < 90) & (c[..., 3] > 0)
    if lam:                                             # drop the old orange mark (the lambda replaces it)
        for y, x in np.argwhere(ORANGE(sk)):
            nb = [sk[y + dy, x + dx] for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0))
                  if not ORANGE(sk[y + dy, x + dx][None])[0]]
            sk[y, x] = max(nb, key=lambda c: int(c[:3].sum())) if nb else sk[y, x]
    E = {e['name']: e for e in d['elements']}

    def upscale(a, part, face, seed_extra=''):
        if face == 'up':
            a = a[::-1]                                       # skin top: front at the bottom; model: at the top
        sm, nn = scale2x(a), a.repeat(2, 0).repeat(2, 1)
        # coloured details (logos, badges) stay crisp: no smoothing where a saturated colour is involved
        sat = lambda c: (c[..., :3].max(-1).astype(int) - c[..., :3].min(-1)) > 60
        keep = sat(sm) | sat(nn)
        sm[keep] = nn[keep]
        return finish(sm, seed=zlib.crc32((part + face + seed_extra).encode()))

    def write(fc, big):
        u0, v0, u1, v1 = fc['uv']
        x0, y0, x1, y1 = int(min(u0, u1)), int(min(v0, v1)), int(max(u0, u1)), int(max(v0, v1))
        assert (x1 - x0, y1 - y0) == big.shape[1::-1], (fc['uv'], big.shape)
        if u0 > u1: big = big[:, ::-1]
        if v0 > v1: big = big[::-1]
        T[y0:y1, x0:x1] = big

    # --- base layer (opaque)
    for part, ((bx, by), (ox, oy), (w, h, dd)) in LIMBS.items():
        for face, (x, y, fw, fh) in box_faces(bx, by, w, h, dd).items():
            a = sk[y:y + fh, x:x + fw].copy()
            a[..., 3] = 255
            big = upscale(a, part, face)
            if lam and part == 'body' and face == 'north':
                draw_lambda(big)
            write(E[part]['faces'][face], big)

    # --- second layer on the shell elements, packed into the new space (right half, then bottom-left)
    shells = {}
    for e in d['elements']:
        cx = (e['from'][0] + e['to'][0]) / 2
        if e['name'] == 'jacket': shells['body'] = e
        elif e['name'] == 'sleeve': shells['right_arm' if cx > 0 else 'left_arm'] = e
        elif e['name'] == 'Pant': shells['right_leg' if cx > 0 else 'left_leg'] = e
    shelf = [128, 0, 0]                                  # x, y, row height (packs in x 128..256, then y 128..256)

    def alloc(w_, h_):
        if shelf[0] + w_ > 256:
            shelf[0], shelf[1], shelf[2] = (128 if shelf[1] < 128 else 0), shelf[1] + shelf[2], 0
        if shelf[1] + h_ > 128 and shelf[1] < 128 and shelf[0] == 128:
            shelf[0], shelf[1], shelf[2] = 0, 128, 0
        r = [shelf[0], shelf[1], shelf[0] + w_, shelf[1] + h_]
        shelf[0] += w_
        shelf[2] = max(shelf[2], h_)
        assert r[3] <= 256, 'no room'
        return r
    for part, ((bx, by), (ox, oy), (w, h, dd)) in LIMBS.items():
        e = shells[part]
        for face, (x, y, fw, fh) in box_faces(ox, oy, w, h, dd).items():
            a = sk[y:y + fh, x:x + fw].copy()
            fc = e['faces'][face]
            if not (a[..., 3] > 0).any():                  # nothing on this face: keep it empty
                fc['uv'], fc['texture'] = [0, 0, 0, 0], None
                continue
            big = upscale(a, part, face, 'shell')
            big[..., 3] = np.where(big[..., 3] > 0, 255, 0)
            if lam and part == 'body' and face == 'north':
                draw_lambda(big)                            # the shirt is on the outer layer too
            fc['uv'], fc['texture'] = alloc(2 * fw, 2 * fh), 0
            write(fc, big)
    for e in d['elements']:                              # the hat layer stays empty (the head never changes)
        if e['name'] == 'hat':
            for fc in e['faces'].values():
                fc['uv'], fc['texture'] = [0, 0, 0, 0], None

    # tufts under the clothes: point every face at one transparent texel that no face uses
    if hide:
        used = np.zeros((256, 256), bool)
        for e in d['elements']:
            for fc in e['faces'].values():
                if fc.get('texture') is None: continue
                u0, v0, u1, v1 = fc['uv']
                used[int(min(v0, v1)):int(np.ceil(max(v0, v1))), int(min(u0, u1)):int(np.ceil(max(u0, u1)))] = True
        free = np.argwhere((T[..., 3] == 0) & ~used)
        ty, tx = free[-1]
        G = {g['uuid']: g['name'] for g in d['groups']}
        members = set()

        def walk(nodes, inside):
            for n in nodes:
                if isinstance(n, dict):
                    walk(n['children'], inside or G[n['uuid']] in hide)
                elif inside:
                    members.add(n)
        walk(d['outliner'], False)
        for e in d['elements']:
            if e['uuid'] in members:
                for fc in e['faces'].values():
                    if fc.get('texture') is not None:
                        fc['uv'] = [int(tx), int(ty), int(tx) + 1, int(ty) + 1]
        print('hidden elements:', len(members), 'texel', (int(tx), int(ty)))

    d['resolution'] = {'width': 256, 'height': 256}
    for k in ('width', 'height', 'uv_width', 'uv_height'):
        d['textures'][0][k] = 256
    im = Image.fromarray(T)
    buf = io.BytesIO(); im.save(buf, 'PNG')
    d['textures'][0]['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    name = out.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    png = name.replace('skin_', 'Emezomm-CPM_') + '_256.png'
    d['textures'][0]['name'] = d['textures'][0]['relative_path'] = png
    d['name'] = name
    json.dump(d, open(out, 'w'))
    im.save(out.rsplit('/', 1)[0] + '/' + png)
    print('ok', out, png)


if __name__ == '__main__':
    main()
