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
    lens_front = grid(["33332",
                       "3HOO2",
                       "2OOD1",
                       "21111"], {**BRONZE, **LENS})
    lens_side = rows(1, [BRONZE['3'], BRONZE['2'], BRONZE['2'], BRONZE['1']])
    lens_top, lens_bot = rows(5, [BRONZE['3']]), rows(5, [BRONZE['1']])
    nose_front = bandana(6, 5, 3)
    nose_front[1:3, 2:4] = (*GREEN[5], 255)                            # cloth pushed out by the nose tip
    nose_front[1, 2] = (*PRINT, 255)
    tail_tip = grid(["GG", "gG", "Gg", "gG", "11"], {'G': GREEN[3], 'g': GREEN[2], '1': GREEN[1]})
    chin = grid(["GgG",
                 "gGg",
                 "GgG",
                 ".gG",
                 "..1"], {'G': GREEN[3], 'g': GREEN[2], '1': GREEN[1]})
    # snout cover: stepped core + two slanted side plates = a wedge tied tight around the snout, narrowing to
    # the nose (checked: covers every point of the snout in front of the head)
    SIDE = 24
    snout = [
        ('bandana_focinho_ponta', (-1.5, 23.45, -6.75), (1.5, 25.95, -4.25),
         {'north': nose_front, 'east': bandana(5, 5, 6), 'west': bandana(5, 5, 7),
          'up': bandana(6, 5, 8, light_top=False), 'down': fill(6, 5, GREEN[1])}),
        ('bandana_focinho_meio', (-2.0, 23.45, -5.75), (2.0, 26.45, -4.25),
         {'north': bandana(8, 6, 9), 'east': bandana(3, 6, 10), 'west': bandana(3, 6, 11),
          'up': bandana(8, 3, 12, light_top=False), 'down': fill(8, 3, GREEN[1])}),
        ('bandana_focinho_base', (-2.5, 23.45, -5.25), (2.5, 26.45, -4.25),
         {'north': bandana(10, 6, 13), 'east': bandana(2, 6, 14), 'west': bandana(2, 6, 15),
          'up': bandana(10, 2, 16, light_top=False), 'down': fill(10, 2, GREEN[1])}),
    ]
    for sg, nm in ((1, 'R'), (-1, 'L')):
        c = (sg * 2.05, 24.7, -5.5)
        snout.append(('bandana_focinho_lado_' + nm, (c[0] - 0.25, c[1] - 1.25, c[2] - 1.5),
                      (c[0] + 0.25, c[1] + 1.25, c[2] + 1.5),
                      {'north': rows(1, [GREEN[4]] + [GREEN[3]] * 3 + [GREEN[1]]),
                       'east': bandana(6, 5, 17 + sg), 'west': bandana(6, 5, 19 + sg),
                       'up': rows(1, [GREEN[4]] * 6), 'down': rows(1, [GREEN[1]] * 6)},
                      {'rotation': [0, sg * SIDE, 0], 'origin': list(c)}))
    return [
        ('head', 'acess_gorro', (0, 30, 0), [
            ('gorro', (-4.25, 29.0, -4.25), (4.25, 32.5, 4.25),
             {'north': cap_side(17, 7), 'south': cap_side(17, 7), 'east': cap_side(17, 7),
              'west': cap_side(17, 7), 'up': cap_top(17, 17)}),
            ('gorro_alca', (-4.5, 30.3, -4.5), (4.5, 31.3, 4.5),
             {'north': strap(18, 2), 'south': strap(18, 2), 'east': strap(18, 2, buckle=True),
              'west': strap(18, 2), 'up': rows(18, [STRAP[1]] * 18), 'down': rows(18, [STRAP[2]] * 18)}),
        ]),
        ('head', 'acess_oculos', (0, 30.8, -4.7), [
            ('oculos_lente_R', (1.25, 29.8, -5.0), (3.75, 31.8, -4.5),
             {'north': lens_front, 'east': lens_side, 'west': lens_side, 'up': lens_top, 'down': lens_bot}),
            ('oculos_lente_L', (-3.75, 29.8, -5.0), (-1.25, 31.8, -4.5),
             {'north': lens_front[:, ::-1].copy(), 'east': lens_side, 'west': lens_side, 'up': lens_top,
              'down': lens_bot}),
            ('oculos_ponte', (-1.25, 30.55, -5.0), (1.25, 31.05, -4.5),
             {'north': rows(5, [BRONZE['2']]), 'up': rows(5, [BRONZE['3']]), 'down': rows(5, [BRONZE['1']])}),
        ]),
        ('head', 'acess_bandana', (0, 25, 0), [
            ('bandana_faixa', (-4.25, 23.75, -4.25), (4.25, 26.25, 4.25),
             {'north': bandana(17, 5, 1), 'south': bandana(17, 5, 2), 'east': bandana(17, 5, 4),
              'west': bandana(17, 5, 5), 'down': fill(17, 17, GREEN[1])}),
            ('bandana_no', (-0.5, 24.5, 4.25), (0.5, 25.5, 4.75),
             {'south': rows(2, [GREEN[4], GREEN[2]]), 'east': rows(1, [GREEN[3], GREEN[1]]),
              'west': rows(1, [GREEN[3], GREEN[1]]), 'up': rows(2, [GREEN[4]]), 'down': rows(2, [GREEN[1]])}),
            ('bandana_ponta_1', (-1.25, 22.0, 4.5), (-0.25, 24.5, 4.5), {'south': tail_tip}),
            ('bandana_ponta_2', (0.25, 22.0, 4.5), (1.25, 24.5, 4.5), {'south': tail_tip[:, ::-1].copy()}),
            # the cloth hanging under the chin (2D, facing forward), slightly open
            ('bandana_queixo_R', (0.1, 21.4, -4.3), (1.6, 23.9, -4.3), {'north': chin[:, ::-1].copy()},
             {'rotation': [0, 0, -8], 'origin': [0.85, 23.9, -4.3]}),
            ('bandana_queixo_L', (-1.6, 21.4, -4.3), (-0.1, 23.9, -4.3), {'north': chin},
             {'rotation': [0, 0, 8], 'origin': [-0.85, 23.9, -4.3]}),
        ]),
        ('focinho', 'acess_bandana_focinho', (0, 24.75, -5.5), snout),
    ]


ACESSORIOS = {'cacadores': cacadores}
