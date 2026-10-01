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
def coin_parts():
    """solid gold coin, 1.25 across: rim, field and a stamped emblem; round look (cut corners)"""
    CO = {'1': (255, 232, 140), '2': (236, 190, 72), '3': (196, 142, 40), '4': (150, 104, 26), '5': (110, 74, 16)}
    face = grid([".334.",
                 "32523",
                 "35153",
                 "32524",
                 ".444."], CO)
    edge = grid(["3", "2", "1", "2", "4"], CO)
    return [('moeda', (5.0, 20.0, -0.125), (6.25, 21.25, 0.125),
             {'north': face, 'south': face[:, ::-1].copy(), 'east': edge, 'west': edge,
              'up': grid(["32123"], CO), 'down': grid(["44544"], CO)}, {'density': 4})]


def goggles(lens_front, lens_side, lens_top, lens_bot):
    """goggles on the forehead, tilted like the player's edit; plain glass, strap around the head"""
    return [('head', 'acess_oculos', (0, 31.1, -4.5), [
            ('oculos_lente_R', (1.25, 30.1, -4.75), (3.75, 32.1, -4.25),
             {'north': lens_front, 'east': lens_side, 'west': lens_side, 'up': lens_top, 'down': lens_bot}),
            ('oculos_lente_L', (-3.75, 30.1, -4.75), (-1.25, 32.1, -4.25),
             {'north': lens_front[:, ::-1].copy(), 'east': lens_side, 'west': lens_side, 'up': lens_top,
              'down': lens_bot}),
            ('oculos_ponte', (-1.25, 30.85, -4.75), (1.25, 31.35, -4.25),
             {'north': rows(5, [BRONZE['2']]), 'up': rows(5, [BRONZE['3']]), 'down': rows(5, [BRONZE['1']])}),
            ('oculos_alca', (-4.25, 30.6, -4.25), (4.25, 31.6, 5.25),
             {'north': strap(17, 2), 'south': strap(17, 2), 'east': strap(19, 2, buckle=True),
              'west': strap(19, 2), 'down': rows(17, [STRAP[2]] * 19)}),
         ], {'rotation': [25, 0, 0]})]


def cacadores():
    """Bounty hunters: goggles on the forehead (the player's tilted style), the neck bandana like the reference
    (tip in its own group so it can swing) and the coin of the coin-toss emote."""
    lens_front = grid(["33332",
                       "3HOO2",
                       "2OOD1",
                       "21111"], {**BRONZE, **LENS})
    lens_side = rows(1, [BRONZE['3'], BRONZE['2'], BRONZE['2'], BRONZE['1']])
    lens_top, lens_bot = rows(5, [BRONZE['3']]), rows(5, [BRONZE['1']])
    return goggles(lens_front, lens_side, lens_top, lens_bot) + bandana_pescoco() + [
        ('right_arm', 'prop_moeda', (5.625, 20.625, 0.0), coin_parts()),
    ]


# ------------------------------------------------------------------ white variant (templar-like outfit)
CREAM = [(247, 241, 236), (236, 222, 212), (215, 199, 187), (189, 178, 168)]
GOLDW = [(230, 187, 119), (204, 165, 104), (170, 132, 80)]


def collar(w, h, seed=0):
    """cream collar with a gold trim on top and bottom (the gold/cream band of the skin's hat layer)"""
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            c = CREAM[0] if (x + y + seed) % 4 else CREAM[1]
            a[y, x] = (*c, 255)
    a[0] = (*GOLDW[0], 255)
    a[0, ::4] = (*GOLDW[1], 255)
    a[-1] = (*GOLDW[1], 255)
    if h > 3:
        a[-2] = (*CREAM[2], 255)
    return a


def gold_band(w, h, front_gap=0):
    """gold band of the hood rim; front_gap = transparent middle (the face shows through at the front)"""
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            c = GOLDW[0] if y == 0 else GOLDW[1]
            if y == 0 and x % 5 == 2: c = (242, 206, 146)               # highlights
            if y == h - 1 and x % 3 == 0: c = GOLDW[2]
            a[y, x] = (*c, 255)
    if front_gap:
        m = (w - front_gap) // 2
        a[:, m:m + front_gap] = 0
    return a


def hood(w, h, seed=0):
    """cream cloth of the hood/cowl with soft folds"""
    a = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            c = CREAM[0] if (x + seed) % 5 in (1, 2) else CREAM[1]
            if (x + seed) % 5 == 4: c = (228, 215, 205)
            if y == h - 1: c = CREAM[2]
            a[y, x] = (*c, 255)
    return a


def branca():
    """the hood rim / collar of the skin, in 3D: a gold band around the head (higher at the back, lower at the
    front where only its corners show beside the muzzle), cream hood cloth below it and a cream cowl around the
    neck with a gold clasp. Tilted 14 deg like the skin."""
    TILT = {'rotation': [-14, 0, 0]}
    return [
        ('head', 'acess_capuz', (0, 25.5, 0), [
            ('capuz_faixa', (-4.25, 25.25, -4.25), (4.25, 26.25, 4.25),
             {'north': gold_band(17, 2, front_gap=11), 'south': gold_band(17, 2), 'east': gold_band(17, 2),
              'west': gold_band(17, 2), 'up': rows(17, [GOLDW[0]] * 17), 'down': rows(17, [GOLDW[2]] * 17)}),
            ('capuz_pano', (-4.25, 23.75, -4.25), (4.25, 25.25, 4.25),
             {'north': hood(17, 3, 0), 'south': hood(17, 3, 1), 'east': hood(17, 3, 2), 'west': hood(17, 3, 3),
              'down': rows(17, [CREAM[2]] * 17)}, {'origin': [0, 25.5, 0]}),
        ], TILT),
        ('body', 'acess_gola', (0, 23.0, 0), [
            ('gola', (-4.25, 22.0, -2.75), (4.25, 24.0, 2.75),
             {'north': hood(17, 4, 4), 'south': hood(17, 4, 5), 'east': hood(11, 4, 6), 'west': hood(11, 4, 7),
              'up': rows(17, [CREAM[1]] * 11), 'down': rows(17, [CREAM[3]] * 11)}),
            ('gola_fecho', (-0.5, 22.5, -3.25), (0.5, 23.5, -2.75),
             {'north': grid(["12", "23"], {'1': GOLDW[0], '2': GOLDW[1], '3': GOLDW[2]}),
              'east': rows(1, [GOLDW[0], GOLDW[2]]), 'west': rows(1, [GOLDW[0], GOLDW[2]]),
              'up': rows(2, [GOLDW[0]]), 'down': rows(2, [GOLDW[2]])})]),
    ]


ACESSORIOS = {'cacadores': cacadores, 'branca': branca}
