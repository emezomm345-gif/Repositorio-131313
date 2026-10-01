"""3D accessories for the variants (pixel art painted in code, 2 px per unit like the rest of the model).

Each builder returns a list of groups: (parent group, new group name, pivot, [element, ...][, {'rotation': ...}])
where an element is (name, from, to, {face: RGBA array}[, {'rotation', 'origin', 'density', 'glow'}]); groups can
be nested (a later group may use an earlier one as parent). density = pixels per unit (default 2). Faces missing from the dict are not drawn. Sizes are chosen so every face
is a whole number of pixels at 2 px per unit (checked by the caller).
"""
import numpy as np


def fill(w, h, col):
    a = np.zeros((h, w, 4), np.uint8)
    a[...] = (*col, 255)
    return a


def rows(w, cols):
    """one colour per row, repeated along the width"""
    return np.array([[(*c, 255)] * w for c in cols], np.uint8)


def grid(lines, pal):
    return np.array([[(*pal[ch], 255) if ch in pal else (0, 0, 0, 0) for ch in ln] for ln in lines], np.uint8)


# ------------------------------------------------------------------ bounty hunters (Cacadores de recompensas)
LEATHER = [(40, 25, 16), (49, 31, 20), (60, 35, 21), (70, 40, 20), (81, 44, 21), (96, 58, 28)]
STITCH = (150, 105, 71)
STRAP = [(130, 127, 127), (96, 94, 94), (73, 73, 73)]
GOLD = [(255, 224, 155), (226, 167, 104), (160, 110, 60)]
BRONZE = {'1': (80, 50, 24), '2': (104, 66, 32), '3': (140, 96, 52), '4': (176, 128, 74)}
LENS = {'H': (255, 214, 120), 'O': (232, 128, 24), 'D': (160, 66, 0), 'R': (110, 44, 0)}
GREEN = [(0, 58, 0), (0, 80, 0), (0, 104, 0), (0, 122, 0), (0, 140, 0), (0, 158, 0)]
PRINT = (110, 200, 110)


def cap_side(w, h):
    """leather panel side: lighter at the top, vertical seams with stitches, darker rim at the bottom."""
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        base = LEATHER[4] if y == 0 else (LEATHER[3] if y < 3 else LEATHER[2])
        for x in range(w):
            c = base
            if (x + y) % 5 == 0 and 0 < y < h - 1:
                c = LEATHER[3] if base == LEATHER[4] else LEATHER[4]      # grain
            a[y, x] = (*c, 255)
    for sx in range(5, w - 1, 6):                                      # seams
        a[:h - 1, sx] = (*LEATHER[1], 255)
        for y in range(1, h - 1, 2):
            a[y, sx - 1] = (*STITCH, 255)
    a[h - 1] = (*LEATHER[1], 255)                                      # rim
    a[h - 1, ::3] = (*LEATHER[0], 255)
    return a


def cap_top(w, h):
    """top of the cap: four panels meeting at a button, lighter towards the middle, stitched seams."""
    a = np.zeros((h, w, 4), np.uint8)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            r = max(abs(x - cx), abs(y - cy)) / max(cx, cy)
            c = LEATHER[5] if r < 0.25 else LEATHER[4] if r < 0.6 else LEATHER[3] if r < 0.85 else LEATHER[2]
            a[y, x] = (*c, 255)
    mx, my = w // 2, h // 2
    a[:, mx] = (*LEATHER[1], 255); a[my, :] = (*LEATHER[1], 255)       # cross seams
    for i in range(1, h, 2):
        a[i, mx - 1] = (*STITCH, 255)
    for i in range(1, w, 2):
        a[my - 1, i] = (*STITCH, 255)
    a[my - 1:my + 1, mx - 1:mx + 1] = (*LEATHER[5], 255)                # button
    a[my - 1, mx - 1] = (*STITCH, 255)
    return a


def strap(w, h, buckle=False):
    a = rows(w, [STRAP[0]] + [STRAP[1]] * (h - 2) + [STRAP[2]])
    if buckle:
        m = w // 2
        a[:, m - 1:m + 2] = (*GOLD[1], 255)
        a[0, m - 1:m + 2] = (*GOLD[0], 255)
        a[-1, m - 1:m + 2] = (*GOLD[2], 255)
        a[:, m] = (*GOLD[2], 255)
    return a


def bandana(w, h, seed=0, light_top=True):
    """green cloth with the print of the skin (checker of two greens + light dots) and soft folds."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            c = GREEN[3] if (x // 2 + y) % 2 == 0 else GREEN[2]
            if light_top and y == 0:
                c = GREEN[4]
            if y == h - 1:
                c = GREEN[1]
            a[y, x] = (*c, 255)
    for x in range(1, w, 4):                                           # print dots
        y = (x // 4) % max(1, h - 2) + (1 if h > 2 else 0)
        if y < h - 1:
            a[y, x] = (*PRINT, 255)
    for _ in range(max(1, w // 6)):                                     # folds
        fx = int(rng.integers(1, max(2, w - 1)))
        a[max(0, h - 3):h - 1, fx] = (*GREEN[1], 255)
    return a


# neck bandana (reference: band around the neck under the chin, triangle on the chest with a light trim and
# diamond motifs). Everything is 3D: the band is a ring around the neck, the triangle is two stepped layers
# (light-green trim behind, darker printed cloth in front, inset -> raised border) and a raised diamond.
BD = {  # forest greens in the same hue as the variant's fur, sage trim like the sleeves (harmonised palette)
    'D': (18, 58, 34), 'd': (24, 72, 42), 'm': (36, 92, 56), 'T': (104, 152, 114), 't': (76, 124, 88),
    'L': (156, 200, 162), 'S': (12, 40, 24)}


def cloth(w, h, seed=0, diamonds=True):
    """dark printed cloth: two greens in diagonal weave, small light diamonds every 4 px"""
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            a[y, x] = (*(BD['d'] if (x + y + seed) % 3 else BD['D']), 255)
    if diamonds:
        for x in range(1 + seed % 2, w - 1, 4):
            for y in range(0, h):
                if (x // 4 + y + seed) % 2 == 0:
                    a[y, x] = (*BD['L'], 255)
    return a


def band(w, h, seed=0):
    """the band around the neck: light trim on top and bottom, printed dark cloth between"""
    a = cloth(w, h, seed)
    a[0] = (*BD['T'], 255)
    a[-1] = (*BD['t'], 255)
    return a


def bandana_triangle(w=15, h=9):
    """the bandana tip like the reference: smooth triangle, dark edge, light outline 1 px inside, printed cloth
    with small diamonds; transparent outside the triangle (cut-out)."""
    a = np.zeros((h, w, 4), np.uint8)
    inside = np.zeros((h, w), bool)
    for y in range(h):
        hw = (w / 2) * (1 - (y + 0.5) / h) + 0.35
        for x in range(w):
            inside[y, x] = abs(x + 0.5 - w / 2) <= hw
    edge = inside & ~(np.roll(inside, 1, 1) & np.roll(inside, -1, 1) & np.roll(inside, -1, 0))
    edge[0] = False                                           # the top edge goes under the band
    inner = inside & ~edge
    ring = inner & ~(np.roll(inner, 1, 1) & np.roll(inner, -1, 1) & np.roll(inner, -1, 0))
    ring[0] = inside[0] & ~edge[0]                            # outline also along the top
    for y in range(h):
        for x in range(w):
            if not inside[y, x]:
                continue
            c = BD['S'] if edge[y, x] else BD['T'] if ring[y, x] else (BD['d'] if (x + y) % 3 else BD['D'])
            a[y, x] = (*c, 255)
    for cx, cy in ((w // 2 - 4, 2), (w // 2 + 4, 2)):            # small diamonds near the top corners
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            if inner[cy + dy, cx + dx] and not ring[cy + dy, cx + dx]:
                a[cy + dy, cx + dx] = (*BD['L'], 255)
    return a


def band_diamonds(w, h, seed=0):
    """band around the neck: light lines top and bottom, a row of small diamonds (like the reference's back)"""
    a = cloth(w, h, seed, diamonds=False)
    a[0] = (*BD['T'], 255)
    a[-1] = (*BD['t'], 255)
    for cx in range(2 + seed % 3, w - 1, 5):
        a[1, cx] = (*BD['L'], 255)
        if h > 3:
            a[2, cx - 1] = (*BD['L'], 255); a[2, cx + 1] = (*BD['L'], 255)
            if h > 4: a[3, cx] = (*BD['L'], 255)
    return a


def bandana_pescoco():
    """[(group spec)] -- band (static, on the body) + the tip in its own group so it can swing."""
    tri = bandana_triangle()
    back = bandana_triangle()[:, ::-1].copy()
    back[..., :3] = np.where(back[..., 3:4] > 0, np.array(BD['S'], np.uint8), back[..., :3])
    band = ('body', 'acess_bandana', (0, 23.25, 0), [
        ('bandana_faixa', (-4.25, 22.25, -2.25), (4.25, 24.25, 2.25),
         {'north': band_diamonds(17, 4, 0), 'south': band_diamonds(17, 4, 1), 'east': band_diamonds(9, 4, 2),
          'west': band_diamonds(9, 4, 3), 'up': rows(17, [BD['m']] * 9), 'down': rows(17, [BD['S']] * 9)})])
    tip = ('acess_bandana', 'bandana_ponta', (0, 22.5, -2.5), [
        ('bandana_triangulo', (-3.75, 18.0, -2.75), (3.75, 22.5, -2.25),
         {'north': tri, 'south': back, 'up': rows(15, [BD['d']])},
         {'rotation': [6, 0, 0], 'origin': [0, 22.5, -2.5]}),
        ('bandana_losango', (-0.5, 19.8, -3.3), (0.5, 20.8, -2.8),
         {'north': grid(["LT", "TL"], BD), 'east': rows(1, [BD['T'], BD['t']]),
          'west': rows(1, [BD['T'], BD['t']]), 'up': rows(2, [BD['L']]), 'down': rows(2, [BD['t']])},
         {'rotation': [6, 0, 45], 'origin': [0, 20.3, -3.05]})])
    return [band, tip]


# ------------------------------------------------------------------ emote props (bounty hunters)
# All of them rest INSIDE an arm or the body (invisible) and are pulled out by the emotes. 4 px per unit.
PAPER = [(232, 214, 160), (218, 196, 138), (198, 172, 112), (170, 140, 86)]
INK, SEAL = (74, 46, 24), (168, 38, 28)


def contract_front():
    """12 x 16 px: aged, torn bounty contract -- header, portrait of the target, text lines, red seal."""
    rng = np.random.default_rng(7)
    a = np.zeros((16, 12, 4), np.uint8)
    for y in range(16):
        for x in range(12):
            c = PAPER[0] if rng.random() > 0.25 else PAPER[1]
            if x in (0, 11) or y in (0, 15):
                c = PAPER[2]
            a[y, x] = (*c, 255)
    for x in range(2, 10):                                     # header "WANTED"
        if x % 2 == 0 or x in (5,): a[1, x] = (*INK, 255)
        a[2, x] = (*INK, 255) if x % 3 else (*PAPER[2], 255)
    for y in range(4, 11):                                     # portrait frame
        a[y, 2] = a[y, 9] = (*PAPER[3], 255)
    a[4, 2:10] = a[10, 2:10] = (*PAPER[3], 255)
    sil = ["........", "..#..#..", "..####..", ".######.", "..####..", ".######."]
    for j, row in enumerate(sil):
        for i, ch in enumerate(row):
            if ch == '#': a[5 + j - 1 if j else 5, 2 + i] = (*INK, 255) if j else a[5, 2 + i]
    for j, row in enumerate(sil[1:]):
        for i, ch in enumerate(row):
            if ch == '#': a[5 + j, 2 + i] = (*INK, 255)
    for y in (12, 13):                                         # text
        for x in range(2, 10):
            if (x + y) % 4: a[y, x] = (*PAPER[3], 255)
    for y, x in ((13, 8), (13, 9), (14, 8), (14, 9), (14, 10)):  # seal
        a[y, x] = (*SEAL, 255)
    for y, x in ((0, 3), (0, 4), (0, 8), (3, 11), (4, 11), (8, 0), (15, 0), (15, 1), (14, 0), (15, 6)):  # torn bits
        a[y, x] = (0, 0, 0, 0)
    for y, x in ((1, 3), (1, 8), (3, 10), (9, 1), (14, 1)):
        a[y, x] = (*PAPER[3], 255)
    return a


def contract_back(front):
    a = front[:, ::-1].copy()
    m = a[..., 3] > 0
    rng = np.random.default_rng(3)
    for y in range(16):
        for x in range(12):
            if m[y, x]:
                c = PAPER[1] if rng.random() > 0.3 else PAPER[2]
                if x in (0, 11) or y in (0, 15): c = PAPER[2]
                a[y, x] = (*c, 255)
    return a


def knife_parts():
    STEEL = {'H': (238, 242, 246), 'S': (196, 202, 210), 's': (150, 156, 164), 'B': (112, 70, 36),
             'b': (86, 52, 26), 'w': (60, 36, 18), 'G': (186, 140, 80), 'g': (140, 100, 52)}
    blade_side = grid([".H.", "HS.", "HSs", "HSs", "HSs", "HSs", "HSs", "HSs", "HSs", "HSs", "HSs", "HSs"], STEEL)
    return [
        ('faca_lamina', (5.875, 16.25, -0.375), (6.125, 19.25, 0.375),
         {'north': grid(["."] + ["s"] * 11, STEEL), 'south': grid(["."] + ["s"] * 11, STEEL),
          'east': blade_side, 'west': blade_side[:, ::-1].copy(), 'down': grid(["s", "s", "s"], STEEL)},
         {'density': 4}),
        ('faca_guarda', (5.5, 16.0, -0.5), (6.5, 16.25, 0.5),
         {k: grid(["GGGG"], STEEL) for k in ('north', 'south', 'east', 'west')} |
         {'up': grid(["GGGG"] * 4, STEEL), 'down': grid(["gggg"] * 4, STEEL)}, {'density': 4}),
        ('faca_cabo', (5.75, 14.5, -0.25), (6.25, 16.0, 0.25),
         {k: grid(["BB", "ww", "bb", "BB", "ww", "bb"], STEEL) for k in ('north', 'south', 'east', 'west')} |
         {'down': grid(["gg", "gg"], STEEL)}, {'density': 4}),
    ]


def stone_parts():
    ST = {'1': (120, 122, 126), '2': (96, 98, 102), '3': (150, 152, 156), '4': (76, 78, 82)}
    return [('pedra_afiar', (-6.375, 18.0, -1.0), (-5.625, 18.5, 1.0),
             {'north': grid(["333", "222"], ST), 'south': grid(["333", "222"], ST),
              'east': grid(["31313131", "24242424"], ST), 'west': grid(["13131313", "42424242"], ST),
              'up': grid(["313"] * 8, ST), 'down': grid(["424"] * 8, ST)}, {'density': 4})]


def charcoal_parts():
    CH = {'k': (34, 30, 28), 'K': (58, 52, 48), 'p': (196, 170, 120)}
    side = grid(["k", "K", "p", "p", "p", "p", "p", "p"], CH)
    return [('carvao', (6.625, 13.5, -0.125), (6.875, 15.5, 0.125),
             {'north': side, 'south': side, 'east': side, 'west': side, 'up': grid(["k"], CH),
              'down': grid(["p"], CH)}, {'density': 4})]


def coin_parts():
    CO = {'1': (255, 226, 120), '2': (232, 184, 64), '3': (184, 132, 36), '4': (130, 90, 20)}
    face = grid(["2112", "1322", "2232", "3223"], CO)
    edge = grid(["3", "2", "2", "3"], CO)
    return [('moeda', (5.0, 20.0, -0.125), (6.0, 21.0, 0.125),
             {'north': face, 'south': face[:, ::-1].copy(), 'east': edge, 'west': edge, 'up': grid(["2222"], CO),
              'down': grid(["3333"], CO)}, {'density': 4, 'glow': True})]   # shines in the air


def stroke_parts():
    INKS = {'r': (120, 24, 20), 'R': (160, 34, 26)}
    return [('contrato_risco_traco', (-7.25, 15.5, 0.0), (-4.75, 15.75, 0.0),
             {'north': grid(["rRRrRRrRRr"], INKS)}, {'density': 4, 'rotation': [0, 0, 32],
                                                      'origin': [-7.25, 15.625, 0.0]})]


def dust_parts(prefix, c):
    DU = {'1': (196, 186, 166), '2': (168, 158, 140)}
    cube = {k: np.array([[(*DU['1'], 150), (*DU['2'], 130)], [(*DU['2'], 130), (*DU['1'], 150)]], np.uint8)
            for k in ('north', 'south', 'east', 'west', 'up', 'down')}
    x, y, z = c
    D4 = {'density': 4}
    return [(prefix + '_1', (x - 0.5, y - 0.25, z - 0.25), (x, y + 0.25, z + 0.25), cube, D4),
            (prefix + '_2', (x, y, z - 0.5), (x + 0.5, y + 0.5, z), cube, D4),
            (prefix + '_3', (x - 0.25, y - 0.75, z), (x + 0.25, y - 0.25, z + 0.5), cube, D4)]


def goggles(lens_front, lens_side, lens_top, lens_bot):
    GL = {'o': (255, 150, 40), 'y': (255, 236, 160)}
    glow = np.array([[(*GL['o'], 190)] * 10 for _ in range(8)], np.uint8)
    glow[1:3, 1:4] = (*GL['y'], 220)
    scan = np.array([[(*GL['y'], 235)] * 10], np.uint8)
    g = [('head', 'acess_oculos', (0, 31.1, -4.5), [
            ('oculos_lente_R', (1.25, 30.1, -4.75), (3.75, 32.1, -4.25),
             {'north': lens_front, 'east': lens_side, 'west': lens_side, 'up': lens_top, 'down': lens_bot}),
            ('oculos_lente_L', (-3.75, 30.1, -4.75), (-1.25, 32.1, -4.25),
             {'north': lens_front[:, ::-1].copy(), 'east': lens_side, 'west': lens_side, 'up': lens_top,
              'down': lens_bot}),
            ('oculos_ponte', (-1.25, 30.85, -4.75), (1.25, 31.35, -4.25),
             {'north': rows(5, [BRONZE['2']]), 'up': rows(5, [BRONZE['3']]), 'down': rows(5, [BRONZE['1']])}),
         ], {'rotation': [25, 0, 0]}),
         # strap in its own group (pivot at the front) so it can be shortened when the goggles go down
         ('acess_oculos', 'oculos_alca_g', (0, 31.1, -4.25), [
            ('oculos_alca', (-4.25, 30.6, -4.25), (4.25, 31.6, 5.25),
             {'north': strap(17, 2), 'south': strap(17, 2), 'east': strap(19, 2, buckle=True),
              'west': strap(19, 2), 'down': rows(17, [STRAP[2]] * 19)})]),
         # lens glow (visual effect of the "Oculos nos olhos" toggle): inside the lenses at rest
         ('acess_oculos', 'oculos_brilho', (0, 31.1, -4.5), [
            ('oculos_brilho_R', (1.25, 30.1, -4.5), (3.75, 32.1, -4.5), {'north': glow}, {'density': 4, 'glow': True}),
            ('oculos_brilho_L', (-3.75, 30.1, -4.5), (-1.25, 32.1, -4.5), {'north': glow[:, ::-1].copy()},
             {'density': 4, 'glow': True})]),
         ('oculos_brilho', 'oculos_scan', (0, 31.9, -4.5), [
            ('oculos_scan_R', (1.25, 31.85, -4.52), (3.75, 32.1, -4.52), {'north': scan}, {'density': 4, 'glow': True}),
            ('oculos_scan_L', (-3.75, 31.85, -4.52), (-1.25, 32.1, -4.52), {'north': scan}, {'density': 4, 'glow': True})]),
         ]
    return g


def cacadores():
    """Bounty hunters: goggles on the forehead (the player's tilted style) with a lens-glow effect, the neck
    bandana like the reference (tip in its own group so it can swing) and the props of the emotes."""
    lens_front = grid(["33332",
                       "3HOO2",
                       "2OOD1",
                       "21111"], {**BRONZE, **LENS})
    lens_side = rows(1, [BRONZE['3'], BRONZE['2'], BRONZE['2'], BRONZE['1']])
    lens_top, lens_bot = rows(5, [BRONZE['3']]), rows(5, [BRONZE['1']])
    front = contract_front()
    return goggles(lens_front, lens_side, lens_top, lens_bot) + bandana_pescoco() + [
        ('right_arm', 'prop_faca', (6.0, 15.25, 0.0), knife_parts()),
        ('right_arm', 'prop_carvao', (6.75, 14.5, 0.0), charcoal_parts()),
        ('right_arm', 'prop_moeda', (5.5, 20.5, 0.0), coin_parts()),
        ('left_arm', 'prop_contrato', (-6.0, 14.0, 0.0), [
            ('contrato_papel', (-7.5, 14.0, -0.05), (-4.5, 18.0, 0.05),
             {'north': front, 'south': contract_back(front)}, {'density': 4})]),
        ('prop_contrato', 'contrato_risco', (-7.25, 15.625, 0.0), stroke_parts()),
        ('left_arm', 'prop_pedra', (-6.0, 18.25, 0.0), stone_parts()),
        ('body', 'poeira_ombro', (-3.0, 22.0, 0.0), dust_parts('poeira_ombro', (-3.0, 22.0, 0.0))),
        ('body', 'poeira_peito', (0.5, 19.0, 0.0), dust_parts('poeira_peito', (0.5, 19.0, 0.0))),
    ]


ACESSORIOS = {'cacadores': cacadores}
