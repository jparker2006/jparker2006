"""The days: a hand-coloured meadow along the near shore, one flower per day; zero days leave open water.

BAND / SLICES, heights(days), x_of(i, n), XMAP and shade(x, y, days, light) are the world compositor's interface.
A day's height is fixed by data (square root of its count on one shared scale) and the top of its flower (top petal
or bud tip) sits exactly at base - height. Everything else is decoration: superflat pigments laid as a flat wash, then
engraved over in cobalt like a hand-coloured print. Tiny days are buds, the rest open into round flowers, daisies and
tulip cups whose heads grow with the day, and only the busiest ~10% of days wear the cloud's face.
"""
import math
import kit

BAND = dict(x0=0, x1=1200, base=500, top=400)
SLICES = 4
XMAP = None          # optional date -> x (world.py puts each day under its month's aircraft)
FACES = .1           # share of blooming days (the busiest) that smile
# petal pigments, ordered so that neighbouring days differ in lightness as well as hue (decoration only)
PETALS = ('marigold', 'plum', 'coral', 'sky', 'rose', 'vermilion')
RAINBOW = ('vermilion', 'coral', 'marigold', 'leaf', 'sky', 'plum', 'rose')


def heights(days):
    """A day's height: square root of its count on one shared scale (the tallest is labeled with its exact count),
    so ordinary days still show and the busiest still stand out."""
    mx = max((c for _, c in days), default=0) or 1
    return [(BAND['base'] - BAND['top']) * (c / mx) ** .5 for _, c in days]


def x_of(i, n):
    return BAND['x0'] + (i + .5) * (BAND['x1'] - BAND['x0']) / n


# ------------------------------------------------------------------ ink and wash
def _q3(c): return round(c * 3) / 3        # few line levels keep each slice inside a 256-colour palette


def paint(colour, tone, phase, light, sp=1.5, wash=.92):
    """A pigment wash with cobalt lines engraved over it (tone 0 lit .. 1 shade; light tones leave bare colour).
    At night the wash is quiet and the lines turn pale where the light falls, like the rest of the white-line print."""
    base = kit.pigment(colour, light, wash) if isinstance(colour, str) else colour
    t = kit.clamp(tone)
    if light['night']:
        c = _q3(kit.line(phase / sp, max(0, .55 - t) * .8, 1 / kit.S / sp))
        return kit.mix(base, light['ink'], c * .5)
    if t < .12: return kit.mix(light['paper'], base, .74)          # the wash runs thinner where the light falls
    c = _q3(kit.line(phase / sp, t * .8, 1 / kit.S / sp))
    return kit.mix(base, light['ink'], c * .8)


def rim(light): return kit.outline(light, .9 if not light['night'] else .6)


def green(name, light):
    g = kit.pigment('leaf', light, .92)
    if name == 'moss': return kit.mix(g, kit.pigment('marigold', light, .92), .3)
    if name == 'sea': return kit.mix(g, kit.pigment('sky', light, .92), .28)
    return g


# ------------------------------------------------------------------ the plants
_cache_days = None
_cache = None


def _plants(days):
    # Retain the input itself: unlike an id-only cache, this cannot reuse stale geometry when Python recycles an
    # old list's address. Inputs are immutable for a render (the same convention as the other world pieces).
    global _cache_days, _cache
    if days is _cache_days:
        return _cache
    hs = heights(days)
    live = sorted((c, d) for (d, c), h in zip(days, hs) if h > 0)
    faced = {d for _, d in live[len(live) - math.ceil(len(live) * FACES):]} if live else set()
    plants, recent = [], []
    for i, h in enumerate(hs):
        if h <= 0:
            continue
        d = days[i][0]
        cx = XMAP(d) if XMAP else x_of(i, len(days))
        p = _plant(cx, h, d.toordinal(), d in faced, recent)
        recent = (recent + [p['hue']])[-2:]
        plants.append(p)
    _fan([p for p in plants if p['kind'] == 'face'])
    bins = [[] for _ in range(120)]
    for p in plants:
        _finish(p)
        for b in range(max(0, int(p['x0'] / 10)), min(120, int(p['x1'] / 10) + 1)):
            bins[b].append(p)
    for b in bins:
        b.sort(key=lambda p: (p['h'], p['cx']))           # shorter days stand in front, like a bank of flowers
    # the faces' heads come first of all (their leaves and stems keep their place in the bank)
    bins = [([p for p in b if p['kind'] == 'face'], b) for b in bins]
    _cache_days, _cache = days, bins
    return bins


def _plant(cx, h, seed, face, recent):
    base = BAND['base']
    r = kit.rnd(seed, 871, seed * 31)
    hue = next(PETALS[(int(r * 60) + k) % 6] for k in range(6) if PETALS[(int(r * 60) + k) % 6] not in recent)
    p = dict(cx=cx, h=h, seed=seed, top=base - h, hue=hue, bend=(r - .45) * min(7, h * .16), sq=1.)
    pick = kit.rnd(seed, 3)
    if h < 9:                                             # a closed bud: its tip is the day's top
        p.update(kind='bud', R=.75 + h * .06, H=1.8 + h * .22)
    elif face:
        R = 5.4 + h * .062
        p.update(kind='face', R=R, n=14, disc=.54, pw=.17, petals=[RAINBOW[(int(r * 7) + j) % 7] for j in range(14)])
    elif h >= 15 and pick < .24:                          # a tulip cup seen from the side
        R = min(6.2, 1.8 + h * .08) * (.9 + .2 * kit.rnd(seed, 5))
        p.update(kind='cup', R=R * .8, H=R * 2.1)
    elif pick < .58:                                      # a daisy of long petals
        R = min(8.5, 2 + h * .105) * (.9 + .2 * kit.rnd(seed, 5))
        n = 9 + int(kit.rnd(seed, 6) * 4)
        col = 'cream' if kit.rnd(seed, 8) < .22 else hue
        p.update(kind='daisy', R=R, n=n, disc=.32, pw=.15 + .3 / n, petals=[col] * n, sq=.78 + .22 * kit.rnd(seed, 7))
    else:                                                 # a round flower, the superflat one
        R = min(8.5, 1.9 + h * .1) * (.9 + .2 * kit.rnd(seed, 5))
        n = 5 + int(kit.rnd(seed, 6) * 3)
        two = PETALS[(PETALS.index(hue) + 3) % 6] if kit.rnd(seed, 8) < .3 else hue
        k = 1.15 * math.sin(math.pi / n); pr = k / (1 + k)
        p.update(kind='round', R=R, n=n, disc=.38, pr=pr, rc=1 - pr, petals=[hue if j % 2 == 0 else two for j in range(n)],
                 sq=.8 + .2 * kit.rnd(seed, 7))
    return p


def _fan(faces):
    """Faces are few and special: lean the busiest stems apart like a bouquet so no smile hides another."""
    for _ in range(60):
        moved = False
        for a in faces:
            for b in faces:
                if a is b or b['cx'] < a['cx']: continue
                ay, by = a['top'] + a['R'], b['top'] + b['R']
                ax, bx = a['cx'] + a['bend'], b['cx'] + b['bend']
                need = (a['R'] + b['R']) * .92
                if abs(ay - by) >= need: continue
                gap = math.sqrt(need * need - (ay - by) ** 2) - (bx - ax)
                if gap <= .05: continue
                for q, s in ((a, -1), (b, 1)):
                    lim = min(26, q['h'] * .4)
                    q['bend'] = kit.clamp(q['bend'] + s * gap * .3, -lim, lim)
                moved = True
        if not moved: break


def _finish(p):
    base, h, seed, cx = BAND['base'], p['h'], p['seed'], p['cx']
    p['bend'] = kit.clamp(p['bend'], BAND['x0'] + .15 - cx, BAND['x1'] - .15 - cx)
    p['hx'] = cx + p['bend']
    if p['kind'] == 'bud': p['hy'] = p['top']
    elif p['kind'] == 'cup': p['hy'] = p['top'] + .7 * p['H']
    else:
        if p['kind'] == 'face':
            # Centre each face on a raster pixel so every smile renders alike. The top stays exact: only the
            # head's size and lean move, by under a pixel. (The world rasters the days from x = 0, y = top - 8.)
            S, y0 = kit.S, BAND['top'] - 8
            p['hx'] = (math.floor(p['hx'] * S) + .5) / S
            p['R'] = y0 + (math.floor((p['top'] + p['R'] - y0) * S) + .5) / S - p['top']
            p['bend'] = p['hx'] - cx
        p['hy'] = p['top'] + p['sq'] * p['R']         # the top petal touches the exact top
    # leaves: broad, overlapping and engraved; low ones from the root, a smaller one up the stem of taller days
    leaves = []
    nl = 1 if h < 9 else 2 + (h > 26) + (h > 52)
    side = 1 if kit.rnd(seed, 9) < .5 else -1
    span = base - p['hy']
    for k in range(nl):
        high = k == nl - 1 and h > 26
        L = (min(13., 2.5 + h * .2) if high else min(22., 3.2 + h * .3) * (1 - .12 * k)) * (.78 + .3 * kit.rnd(seed, 20 + k))
        L = min(L, h * .6)
        a = math.radians((40 if high else 22) + 34 * kit.rnd(seed, 30 + k) + 7 * k) * side
        ay = base - (h * (.28 + .12 * kit.rnd(seed, 70)) if high else min(h * .2, 1 + k * h * .07))
        t = (base - ay) / max(1e-6, span)
        ax = cx + p['bend'] * t * t
        w = L * (.2 + .07 * kit.rnd(seed, 40 + k))
        g = ('leaf', 'moss', 'sea')[int(kit.rnd(seed, 50 + k) * 3)]
        leaves.append((ax, ay, math.sin(a), -math.cos(a), L, w, side, .18 + .2 * kit.rnd(seed, 60 + k), g))
        side = -side
    p['leaves'] = leaves
    # and a few fine grass blades, for the meadow's texture between the leaves
    p['blades'] = [(cx + (kit.rnd(seed, 80 + k) - .5) * 2, min(26., h * .55) * (.55 + .45 * kit.rnd(seed, 90 + k)),
                    (k * 2 - 1) * side * (.2 + .4 * kit.rnd(seed, 100 + k)), .45 + .3 * kit.rnd(seed, 110 + k), k)
                   for k in range(2 if h >= 9 else 0)]
    ext = max([p['R'] * 1.1 + abs(p['bend']) + 1, 3] + [abs(l[2]) * l[4] + l[5] + abs(l[0] - cx) + 1 for l in leaves]
              + [abs(b[0] - cx) + abs(b[2]) * b[1] + 1 for b in p['blades']])
    p['x0'], p['x1'] = cx - ext, cx + ext
    p['sw'] = min(.75, .3 + h * .006)


# ------------------------------------------------------------------ drawing one plant
def _ring(x, y, p, light):
    """Round flowers, daisies and faces: a ring of petals around a disc, seen face on (or a little tilted)."""
    R, sq = p['R'], p['sq']
    u, v = (x - p['hx']) / R, (y - p['hy']) / (R * sq)
    rr = u * u + v * v
    if rr > 1.02: return None
    rad, disc, kind = math.sqrt(rr), p['disc'], p['kind']
    ow = min(.4, .14 + R * .04)                          # finer outlines on small heads
    if rad < disc:
        e = (disc - rad) * R
        if e < ow: return rim(light)
        if kind == 'face': return _face(u / disc, v / disc, p, light)
        tone = .2 + .7 * kit.form(u / disc * .8, v / disc * .8, light)        # a gold disc, crosshatched in shade
        a = kit.line((x + y) / 1.25, tone * .75, .5 / kit.S)
        b = kit.line((x - y) / 1.25, tone * .75, .5 / kit.S)
        if light['night']: return kit.mix(kit.pigment('marigold', light, .7), light['ink'], _q3(min(a, b)) * .5)
        return kit.mix(kit.mix(kit.pigment('marigold', light), (186, 106, 30), .45), light['ink'], _q3(max(a, b)) * .85)
    n = p['n']
    ang = math.atan2(u, -v)                               # 0 = straight up, clockwise
    step = 2 * math.pi / n
    j0 = round(ang / step)
    best = None
    for j in (j0, j0 - 1, j0 + 1):
        a = j * step; sa, ca = math.sin(a), -math.cos(a)
        along, across = u * sa + v * ca, -u * ca + v * sa
        if kind == 'round':
            d = math.hypot(along - p['rc'], across) - p['pr']
        else:                                             # long petals with round ends
            d = math.hypot(across, along - kit.clamp(along, disc * .7, 1 - p['pw'])) - p['pw']
        if d <= 0:
            front = (j % n) % 2 == 0 and not (n % 2 and j % n == n - 1)
            if best is None or (front and not best[3]) or (front == best[3] and d < best[0]):
                best = (d, j % n, along, front, across)
    if best is None: return None
    d, j, along, front, across = best
    if -d * R * sq < ow: return rim(light)
    # one engraved groove down the middle of each petal, swelling in the cup by the disc and on the shaded side
    half = (p['pr'] if kind == 'round' else p['pw']) * R
    cup = kit.clamp(1 - (along - disc) / .3)
    tone = .85 * cup + .9 * max(0, kit.form(u * .9, v * .9, light) - .3) + (0 if front else .2)
    return paint(p['petals'][j], tone * .75, across * R, light, sp=max(1.5, half))


def _face(u, v, p, light):
    """The cloud's face on a cream disc: dot eyes, a small smile, blush. Asleep at night.
    Chunky on purpose: the disc is only a few pixels wide at reading size."""
    night = light['night']
    ink = light['ink'] if not night else (24, 36, 70)
    cream = kit.pigment('cream', light, .97 if not night else .85)
    for sx in (-.34, .34):
        if night:
            if abs(math.hypot(u - sx, v + .14) - .13) < .055 and v > -.12: return ink
            continue
        if ((u - sx) / .15) ** 2 + ((v + .13) / .19) ** 2 <= 1: return ink    # (a sparkle would be under a pixel here)
    if abs(math.hypot(u, v - (.06 if night else .0)) - (.2 if night else .27)) < (.065 if night else .09) and v > (.12 if night else .1): return ink
    for sx in (-.58, .58):
        if ((u - sx) / .18) ** 2 + ((v - .2) / .1) ** 2 <= 1: return kit.mix(cream, kit.pigment('rose', light), .7)
    rad = math.hypot(u, v)                               # a thin engraved crescent on the shaded rim only
    tone = kit.clamp((rad - .74) / .2) * kit.clamp(kit.form(u * .95, v * .95, light) * 1.6 - .5)
    return paint(cream, tone, rad * p['R'] * p['disc'], light, sp=1.2)


def _bud(x, y, p, light):
    t = (y - p['top']) / p['H']                           # 0 at the tip .. 1 at the base of the bud
    if not 0 <= t <= 1: return None
    hw = p['R'] * math.sqrt(t) * (1 - t) ** .25 * 1.35
    dx = x - p['hx']
    if abs(dx) > hw: return None
    if hw - abs(dx) < .36: return rim(light)
    if t > .76: return paint(green('leaf', light), .6, x + y, light)          # sepals
    return paint(p['hue'], .1 + .9 * max(0, kit.form(dx / max(hw, .1), t * 2 - 1, light) - .25), dx * 2.2, light, sp=1.3)


def _cup(x, y, p, light):
    """A tulip seen from the side: two front petals and a bowl, the back petal rising between them to the day's top."""
    W, H, hx, top = p['R'], p['H'], p['hx'], p['top']
    if not (abs(x - hx) < W + .2 and top <= y <= top + H): return None
    ow = min(.4, .14 + W * .05)
    front = min(kit.ell(x, y, hx - .42 * W, top + .58 * H, .58 * W, .42 * H),
                kit.ell(x, y, hx + .42 * W, top + .58 * H, .58 * W, .42 * H),
                kit.ell(x, y, hx, top + .62 * H, .92 * W, .38 * H) if y > top + .62 * H else 1)
    lean = 1 if x > hx else -1
    if front <= 0:
        if -front < ow: return rim(light)
        if abs(x - hx) < ow * .8 and y > top + .3 * H: return rim(light)              # where the two front petals meet
        nx = (x - hx) / W
        tone = .8 * max(0, kit.form(nx * .9, (y - top) / H * 1.6 - .9, light) - .2) + .5 * kit.clamp((y - top - .7 * H) / (.3 * H))
        return paint(p['hue'], tone, (x - hx - lean * .5 * W) * 1.6 + (y - top) * .3, light, sp=1.4)
    back = kit.ell(x, y, hx, top + .42 * H, .44 * W, .42 * H)
    if back > 0: return None
    if -back < ow: return rim(light)
    return paint(p['hue'], .5, (x - hx) * 1.6, light, sp=1.4)                       # the back petal, in shade


def _leaf(x, y, l, light, base):
    ax, ay, dx, dy, L, w, side, curl, g = l
    px, py = x - ax, y - ay
    s = (px * dx + py * dy) / L                           # 0 at the stem .. 1 at the tip
    if not 0 < s < 1: return None
    n = (px * -dy + py * dx) * side                       # across the leaf, signed outward
    n -= curl * L * s * s                                 # the blade droops as it leaves the stem
    hw = w * math.sin(math.pi * s ** .8) ** .7
    if abs(n) > hw: return None
    if hw - abs(n) < .34 or abs(n) < .2 * (1 - s): return rim(light)            # outline and midrib
    lit = (n > 0) == (light['sun'][0] * side > 0)
    ground = kit.clamp((y - (base - 12)) / 12)            # the meadow darkens toward its roots
    tone = (0 if lit else .4) + .45 * ground
    return paint(green(g, light), tone, s * L * 1.1 - abs(n) * 1.6, light, sp=1.5)


def _draw(x, y, p, light, head=True):
    """One day's plant at (x, y): head, then leaves, then the stem (front to back), or None."""
    base, kind = BAND['base'], p['kind']
    if not head: c = None
    elif kind == 'bud': c = _bud(x, y, p, light)
    elif kind == 'cup': c = _cup(x, y, p, light)
    elif y <= p['hy'] + p['R'] * p['sq'] + .5 and abs(x - p['hx']) <= p['R'] + .5: c = _ring(x, y, p, light)
    else: c = None
    if c is not None: return c
    for l in p['leaves']:
        c = _leaf(x, y, l, light, base)
        if c is not None: return c
    for rx, L, lean, w, k in p['blades']:
        t = (base - y) / L
        if 0 <= t <= 1 and abs(x - rx - lean * L * t ** 1.6) < w * (1 - t) ** .8:
            if light['night']: return kit.outline(light, .42 + .2 * k)
            return kit.mix(green('moss' if k else 'sea', light), light['ink'], .2 + .3 * k)
    span = base - p['hy']                                 # the stem: a fine green line from the root to the head
    if y >= p['hy'] and span > 0:
        t = (base - y) / span
        sx = p['cx'] + p['bend'] * t * t
        w = p['sw'] * (1 - .3 * t)
        if abs(x - sx) < w:
            return kit.mix(green('leaf', light), light['ink'], .45) if not light['night'] else kit.outline(light, .55)
    return None


def tip(p):
    """Where a plant's exact top is (for the checks): x, y."""
    return p['hx'], p['top']


def shade(x, y, days, light):
    if not BAND['x0'] <= x < BAND['x1'] or not BAND['top'] <= y <= BAND['base']:
        return None
    # Front-most plant wins; transparency elsewhere leaves the world's water intact, especially the empty winter.
    faces, bank = _plants(days)[min(119, int(x / 10))]
    for p in faces:
        if p['top'] <= y <= p['top'] + 2 * p['R'] and abs(x - p['hx']) <= p['R']:
            c = _ring(x, y, p, light)
            if c is not None:
                return c
    for p in bank:
        if y < p['top'] or not p['x0'] <= x <= p['x1']:
            continue
        c = _draw(x, y, p, light, p['kind'] != 'face')
        if c is not None:
            return c
    return None
