"""3D accessories for the variants (pixel art painted in code, 2 px per unit like the rest of the model).

Each builder returns a list of groups: (parent group, new group name, pivot, [element, ...]) where an element is
(name, from, to, {face: RGBA array}[, {'rotation': [x, y, z], 'origin': [x, y, z]}]). Faces missing from the dict are not drawn. Sizes are chosen so every face
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


def cacadores():
    """Goggles only (cap and bandana removed on request): two bronze-framed orange lenses on the forehead,
    a bridge and the grey strap around the head that holds them."""
    lens_front = grid(["33332",
                       "3HOO2",
                       "2OOD1",
                       "21111"], {**BRONZE, **LENS})
    lens_side = rows(1, [BRONZE['3'], BRONZE['2'], BRONZE['2'], BRONZE['1']])
    lens_top, lens_bot = rows(5, [BRONZE['3']]), rows(5, [BRONZE['1']])
    return [
        ('head', 'acess_oculos', (0, 30.8, -4.5), [
            ('oculos_alca', (-4.25, 30.3, -4.25), (4.25, 31.3, 4.25),
             {'north': strap(17, 2), 'south': strap(17, 2), 'east': strap(17, 2, buckle=True),
              'west': strap(17, 2), 'down': rows(17, [STRAP[2]] * 17)}),
            ('oculos_lente_R', (1.25, 29.8, -4.75), (3.75, 31.8, -4.25),
             {'north': lens_front, 'east': lens_side, 'west': lens_side, 'up': lens_top, 'down': lens_bot}),
            ('oculos_lente_L', (-3.75, 29.8, -4.75), (-1.25, 31.8, -4.25),
             {'north': lens_front[:, ::-1].copy(), 'east': lens_side, 'west': lens_side, 'up': lens_top,
              'down': lens_bot}),
            ('oculos_ponte', (-1.25, 30.55, -4.75), (1.25, 31.05, -4.25),
             {'north': rows(5, [BRONZE['2']]), 'up': rows(5, [BRONZE['3']]), 'down': rows(5, [BRONZE['1']])}),
        ]),
    ]


ACESSORIOS = {'cacadores': cacadores}
