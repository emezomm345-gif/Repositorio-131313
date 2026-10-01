"""Variants of Emezomm (L.A.S.T universe and others): same model, same face, same animations -
only the texture of the body / arms / legs changes (the outfit), plus optionally the fur colour.

usage: python3 tools/variante.py <base.bbmodel> <skin64.png> <out.bbmodel> [--hide group,...] [--lambda]
       [--fur <palette>] [--head-top <rows>]

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
- --fur <palette>: recolours the DARK fur (head, ears, tufts, tail, lids...) with a gradient map on the base's
  own brightness, so every shade/transition stays where it is. The white/grey fur (muzzle, chest, ear inside,
  tail tip) is part of every Emezomm and keeps its colour (smooth fade between the two). Never recoloured: painted eyes, iris, nose,
  brow band, lash line, props.
- --head-top <rows>: head accessories (cap, goggles, bands...) go on the model's hat shell (0.25 around the
  head): the top <rows> rows of the skin's head + everything on the skin's hat layer. The face underneath is
  untouched (hide the head-top tufts with --hide fur_top if the cap covers them).
- --acessorios <name>: 3D accessories built for a variant (see ACESSORIOS), textured in the new atlas space.
- --pelo <part.face[:rows],...>: in those rows of the skin, the accessory green (a bandana not used by the
  variant) shows the character's own fur (recoloured) instead.
- --brow <palette>: colour of the brow band (palpebra_R/L) to match the variant's fur.
- --emotes <names>: keep only these emotes / settings (and their transitions); --remove-props <prefixes>:
  drop emote props (e.g. holo,bracelete) that no kept emote uses.
- --lambda: the orange mark on the chest becomes a crisp orange lambda symbol.
- Tufts covered by the clothes (--hide: group or element names) are pointed at a transparent texel: the geometry stays, they just
  don't show.
"""
import sys, json, base64, io, zlib, uuid, copy, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acessorios import ACESSORIOS

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


FUR_PALETTES = {   # brightness of the DARK base fur -> colour (light fur is never recoloured, see below)
    'verde': [(0, (0, 26, 12)), (18, (0, 52, 24)), (30, (0, 68, 29)), (50, (0, 84, 27)), (80, (0, 98, 24)),
              (255, (0, 98, 24))],
}
BROW_PALETTES = {  # brightness of the grey brow band -> colour (darker than the fur so it still reads as a brow)
    'verde': [(0, (0, 14, 6)), (40, (0, 22, 9)), (60, (0, 34, 14)), (97, (24, 118, 52)), (255, (60, 160, 80))],
}
LIGHT_FUR = (70, 130)   # brightness where the recolour fades out: from here up the white/grey fur stays as it is
NO_RECOLOUR = ('eye_R_iris', 'eye_L_iris', 'nose', 'palpebra_R', 'palpebra_L', 'hat', 'jacket', 'sleeve', 'Pant',
               'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg')
NO_RECOLOUR_PREFIX = ('holo', 'bracelete', 'suor')
KEEP_COLOURS = {'head': {(0, 0, 0)},                                   # painted eyes
                'palpebra_sup_R': {(71, 71, 71)}, 'palpebra_sup_L': {(71, 71, 71)},   # lash line
                'palpebra_inf_R': {(71, 71, 71)}, 'palpebra_inf_L': {(71, 71, 71)}}


def recolour_fur(T, d, stops, skip=NO_RECOLOUR):
    def rect(uv):
        u0, v0, u1, v1 = uv
        return int(min(v0, v1)), int(np.ceil(max(v0, v1))), int(min(u0, u1)), int(np.ceil(max(u0, u1)))
    fur = np.zeros(T.shape[:2], bool)
    ban = np.zeros(T.shape[:2], bool)
    keep = np.zeros(T.shape[:2], bool)
    for e in d['elements']:
        bad = e['name'] in skip or e['name'].startswith(NO_RECOLOUR_PREFIX)
        for fc in e['faces'].values():
            if fc.get('texture') is None: continue
            y0, y1, x0, x1 = rect(fc['uv'])
            (ban if bad else fur)[y0:y1, x0:x1] = True
            for col in KEEP_COLOURS.get(e['name'], ()):
                keep[y0:y1, x0:x1] |= np.all(T[y0:y1, x0:x1, :3] == col, axis=-1)
    c = T[..., :3].astype(int)
    sat = c.max(-1) - c.min(-1)
    m = fur & ~ban & ~keep & (T[..., 3] > 0) & (sat < 40)
    L = 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]
    xs = [p for p, _ in stops]
    w = np.clip((L - LIGHT_FUR[0]) / (LIGHT_FUR[1] - LIGHT_FUR[0]), 0, 1)   # 0 = dark fur, 1 = light fur
    w = w * w * (3 - 2 * w)
    for ch in range(3):
        new = np.interp(L, xs, [col[ch] for _, col in stops]) * (1 - w) + c[..., ch] * w
        T[..., ch] = np.where(m, new.round(), T[..., ch]).astype(np.uint8)
    return int(m.sum())


def main():
    base, skin_path, out = sys.argv[1:4]
    hide, lam = [], '--lambda' in sys.argv
    fur = sys.argv[sys.argv.index('--fur') + 1] if '--fur' in sys.argv else None
    head_top = int(sys.argv[sys.argv.index('--head-top') + 1]) if '--head-top' in sys.argv else 0
    acess = sys.argv[sys.argv.index('--acessorios') + 1] if '--acessorios' in sys.argv else None
    brow = sys.argv[sys.argv.index('--brow') + 1] if '--brow' in sys.argv else None
    keep_emotes = sys.argv[sys.argv.index('--emotes') + 1].split(',') if '--emotes' in sys.argv else None
    drop_props = sys.argv[sys.argv.index('--remove-props') + 1].split(',') if '--remove-props' in sys.argv else []
    pelo = {}                    # --pelo body.north:0-4,body.up  -> (part, face): (row0, row1) in skin pixels
    if '--pelo' in sys.argv:
        for it in sys.argv[sys.argv.index('--pelo') + 1].split(','):
            pf, _, rr = it.partition(':')
            r0, _, r1 = rr.partition('-')
            pelo[tuple(pf.split('.'))] = (int(r0), int(r1) + 1) if rr else (0, 99)
    if '--hide' in sys.argv:
        hide = sys.argv[sys.argv.index('--hide') + 1].split(',')
    d = json.load(open(base))
    tex = Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
    T = np.zeros((256, 256, 4), np.uint8)
    T[:128, :128] = np.array(tex)                       # old atlas: same pixels, same UVs
    if brow:                                            # brow band colour (texels used only by the band)
        own = np.zeros(T.shape[:2], bool); other = np.zeros(T.shape[:2], bool)
        for e in d['elements']:
            for fc in e['faces'].values():
                if fc.get('texture') is None: continue
                u0, v0, u1, v1 = fc['uv']
                sl = (slice(int(min(v0, v1)), int(np.ceil(max(v0, v1)))), slice(int(min(u0, u1)), int(np.ceil(max(u0, u1)))))
                (own if e['name'] in ('palpebra_R', 'palpebra_L') else other)[sl] = True
        m = own & ~other & (T[..., 3] > 0)
        c = T[..., :3].astype(int)
        L = 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]
        st = BROW_PALETTES[brow]
        for ch in range(3):
            T[..., ch] = np.where(m, np.interp(L, [p_ for p_, _ in st], [col[ch] for _, col in st]).round(),
                                  T[..., ch]).astype(np.uint8)
        print('brow texels recoloured:', int(m.sum()))
    T_fur = T.copy()                                    # the character's own (recoloured) fur, for --pelo
    if fur:
        print('fur texels recoloured:', recolour_fur(T, d, FUR_PALETTES[fur]))
        LIMB_NAMES = ('body', 'right_arm', 'left_arm', 'right_leg', 'left_leg')
        recolour_fur(T_fur, d, FUR_PALETTES[fur], skip=tuple(n for n in NO_RECOLOUR if n not in LIMB_NAMES))
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
            if (part, face) in pelo:
                # accessory green painted on the skin (e.g. a bandana we don't use) -> the character's own fur
                r0, r1 = pelo[(part, face)]
                src = sk[y:y + fh, x:x + fw].astype(int)
                m = (src[..., 0] < 20) & (src[..., 1] > 55) & (src[..., 2] < 40)
                rows_ = np.zeros_like(m); rows_[r0:r1] = True
                m &= rows_
                if face == 'up':
                    m = m[::-1]
                m = m.repeat(2, 0).repeat(2, 1)
                u0, v0, u1, v1 = E[part]['faces'][face]['uv']
                own = T_fur[int(min(v0, v1)):int(max(v0, v1)), int(min(u0, u1)):int(max(u0, u1))]
                if u0 > u1: own = own[:, ::-1]
                if v0 > v1: own = own[::-1]
                big[m] = own[m]
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
    # head accessories on the hat shell: top rows of the skin's head + the skin's hat layer (face untouched)
    hat = next(e for e in d['elements'] if e['name'] == 'hat')
    hat['visibility'] = bool(head_top)              # hidden in the base model; shown when it carries accessories
    for face, (x, y, fw, fh) in box_faces(0, 0, 8, 8, 8).items():
        fc = hat['faces'][face]
        xo, yo = box_faces(32, 0, 8, 8, 8)[face][:2]
        a = np.zeros((fh, fw, 4), np.uint8)
        if head_top:
            b = sk[y:y + fh, x:x + fw].copy()
            if face in ('north', 'south', 'east', 'west'):
                b[head_top:] = 0
            elif face == 'down':
                b[:] = 0
            a = b
        over = Image.fromarray(a); over.alpha_composite(Image.fromarray(sk[yo:yo + fh, xo:xo + fw].copy()))
        a = np.array(over)
        if not head_top or not (a[..., 3] > 0).any():
            fc['uv'], fc['texture'] = [0, 0, 0, 0], None
            continue
        big = upscale(a, 'head', face, 'hat')
        big[..., 3] = np.where(big[..., 3] > 0, 255, 0)
        fc['uv'], fc['texture'] = alloc(2 * fw, 2 * fh), 0
        write(fc, big)

    # 3D accessories: new groups/elements (the existing model is not touched), textured in the new space
    if acess:
        G = {g['name']: g for g in d['groups']}

        def node_of(nodes, uid):
            for n in nodes:
                if isinstance(n, dict):
                    if n['uuid'] == uid:
                        return n
                    r = node_of(n['children'], uid)
                    if r: return r
        for parent, gname, pivot, els, *gextra in ACESSORIOS[acess]():
            g = copy.deepcopy(G['head'])
            g.update(name=gname, uuid=str(uuid.uuid4()), origin=list(pivot),
                     rotation=list((gextra[0] if gextra else {}).get('rotation', [0, 0, 0])))
            d['groups'].append(g)
            G[gname] = g
            kids = []
            for name, f, t, faces, *extra in els:
                extra = dict(extra[0]) if extra else {}
                dens = extra.pop('density', 2)
                glow = extra.pop('glow', False)
                size = {'north': (t[0] - f[0], t[1] - f[1]), 'south': (t[0] - f[0], t[1] - f[1]),
                        'east': (t[2] - f[2], t[1] - f[1]), 'west': (t[2] - f[2], t[1] - f[1]),
                        'up': (t[0] - f[0], t[2] - f[2]), 'down': (t[0] - f[0], t[2] - f[2])}
                fc_all = {}
                for k in ('north', 'east', 'south', 'west', 'up', 'down'):
                    if k not in faces:
                        fc_all[k] = {'uv': [0, 0, 0, 0], 'texture': None}
                        continue
                    img = faces[k]
                    assert img.shape[1::-1] == (round(size[k][0] * dens), round(size[k][1] * dens)), (name, k, img.shape)
                    fc_all[k] = {'uv': alloc(img.shape[1], img.shape[0]), 'texture': 0}
                    write(fc_all[k], img)
                e = {'name': name, 'box_uv': False, 'render_order': 'default', 'locked': False, 'export': True,
                     'scope': 0, 'allow_mirror_modeling': True, 'cpm_glow': glow, 'cpm_recolor': -1,
                     'cpm_extrude': False, 'cpm_data': '', 'from': list(f), 'to': list(t), 'autouv': 0, 'color': 3,
                     'rotation': [0, 0, 0], 'origin': [(f[i] + t[i]) / 2 for i in range(3)], 'faces': fc_all,
                     **extra,
                     'type': 'cube', 'uuid': str(uuid.uuid4())}
                d['elements'].append(e)
                kids.append(e['uuid'])
            node_of(d['outliner'], G[parent]['uuid'])['children'].append(
                {'uuid': g['uuid'], 'isOpen': False, 'children': kids})
        print('accessories:', acess)

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
        members |= {e['uuid'] for e in d['elements'] if e['name'] in hide}   # single elements by name too
        for e in d['elements']:
            if e['uuid'] in members:
                for fc in e['faces'].values():
                    if fc.get('texture') is not None:
                        fc['uv'] = [int(tx), int(ty), int(tx) + 1, int(ty) + 1]
        print('hidden elements:', len(members), 'texel', (int(tx), int(ty)))

    # --emotes: keep only these emotes/settings (custom poses, gestures, layers) and their transitions
    if keep_emotes is not None:
        EMOTE_TYPES = ('custom_pose', 'gesture', 'layer')
        gone = {a['name'] for a in d['animations'] if a['cpm_type'] in EMOTE_TYPES and a['name'] not in keep_emotes}
        d['animations'] = [a for a in d['animations'] if not (
            a['name'] in gone or (a['cpm_type'] in ('setup', 'finish') and a['name'][2:] in gone
                                  and a['name'][:2] in ('c:', 'g:')))]
        print('emotes removed:', sorted(gone))
    # --remove-props: emote props no longer used (groups by name prefix, with their elements)
    if drop_props:
        gid = {g['uuid'] for g in d['groups'] if g['name'].startswith(tuple(drop_props))}
        eid = set()

        def prune(nodes, inside):
            out = []
            for n in nodes:
                if isinstance(n, dict):
                    hit = inside or n['uuid'] in gid
                    kids = prune(n['children'], hit)
                    if not hit:
                        n['children'] = kids
                        out.append(n)
                elif inside:
                    eid.add(n)
                else:
                    out.append(n)
            return out
        d['outliner'] = prune(d['outliner'], False)
        d['groups'] = [g for g in d['groups'] if g['uuid'] not in gid]
        d['elements'] = [e for e in d['elements'] if e['uuid'] not in eid]
        for a in d['animations']:
            for k in [k for k in a['animators'] if k in gid]:
                del a['animators'][k]
        print('props removed:', len(gid), 'groups,', len(eid), 'elements')

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
