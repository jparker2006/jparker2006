"""One day, one shoreline form; zero days leave open water.

BAND / SLICES, heights(days), x_of(i, n), and shade(x, y, days, light)
are the world compositor's interface. All three forms share exact linear
heights. FORM selects reeds (A), wildflowers (B), or waves (C).
"""
import math
import kit

BAND = dict(x0=0, x1=1200, base=500, top=432)
SLICES = 4
FORM = 'A'


def heights(days):
    mx = max((c for _, c in days), default=0) or 1
    return [(BAND['base'] - BAND['top']) * c / mx for _, c in days]


def x_of(i, n):
    return BAND['x0'] + (i + .5) * (BAND['x1'] - BAND['x0']) / n


_cache_days = None
_cache = None


def _plants(days):
    # Retain the input itself: unlike an id-only cache, this cannot reuse stale
    # geometry when Python recycles an old list's address. Inputs are immutable
    # for a render (the same convention as the other world pieces).
    global _cache_days, _cache
    if days is _cache_days:
        return _cache
    bins = [[] for _ in range(120)]
    for i, h in enumerate(heights(days)):
        if h <= 0:
            continue
        seed = days[i][0].toordinal()
        r = kit.rnd(seed, 871, seed * 31)
        bend = (r - .35) * min(9, h * .21)
        cx = x_of(i, len(days))
        bend = kit.clamp(bend, BAND['x0'] + .15 - cx, BAND['x1'] - .15 - cx)
        plant = (cx, h, bend, r)
        # Blades and wave shoulders can extend beyond their day's slot, but
        # their root stays at the chronological x. Binning keeps shade cheap.
        for b in range(max(0, int((cx - 16) / 10)), min(120, int((cx + 16) / 10) + 1)):
            bins[b].append(plant)
    _cache_days, _cache = days, bins
    return bins


def _stem(cx, bend, t):
    return cx + bend * t * t


def _reed(x, y, cx, h, bend, r, light, flower=False):
    base = BAND['base']
    t = (base - y) / h
    sx = _stem(cx, bend, t)
    # The upper envelope is clipped to [base-height, base], even for the
    # tiniest day. No minimum height, decorative stalk, or head above the tip.
    stem_top = 1.0
    if h > (17 if flower else 23):
        hh = min(4.2 if flower else 8, h * .18)
        stem_top = 1 - hh / h
        cy = base - h + hh
        tipx = _stem(cx, bend, 1 - hh / h)
        if flower:
            # Five unequal-looking petals from an elliptical rosette; the
            # upward petal touches the exact data summit.
            u, v = (x - tipx) / (hh * .85), (y - cy) / hh
            angle = math.atan2(u, -v)
            radius = math.hypot(u, v)
            edge = .78 + .22 * math.cos(5 * angle)
            if radius <= edge:
                if radius < .25:
                    return kit.outline(light)
                if radius > edge - .14:
                    return kit.outline(light, .8)
                return kit.engrave(kit.form(u, v, light), y + x * .4, light, sp=1.8)
        else:
            hw = min(1.65, .8 + h * .014)
            d = kit.ell(x, y, tipx, cy, hw, hh)
            if d <= 0:
                nx, ny = (x - tipx) / hw, (y - cy) / hh
                tone = kit.form(nx, ny, light)
                # Only a low, warm sun gilds the sun-facing side of a head.
                lx, ly = light['sun']
                if not light['night'] and lx > .8 and ly < 0 and nx > .35:
                    return kit.warm(.48, y + nx * .6, light)
                if d > -.32:
                    return kit.outline(light, .85)
                return kit.engrave(.3 + .65 * tone, y + .45 * nx, light, sp=1.6)
    width = min(.55, .26 + h * .006) * (1 - .36 * t)
    if t <= stem_top and abs(x - sx) < width:
        return kit.outline(light, .86)
    # Two tapered, bowed blades attached to the same root/stem, never extra
    # data plants. Their tips stay well below the main tip.
    if h > 3:
        for side, start, end in ((-1, .08, .61 + r * .12), (1, .22, .47 + r * .13)):
            if start < t < end:
                u = (t - start) / (end - start)
                anchor = _stem(cx, bend, start)
                spread = min(8, h * .25) * side
                bx = anchor + spread * (2 * u - u * u) + bend * .25 * u
                blade = min(1.1, h * .027) * math.sin(math.pi * u) ** .7
                if abs(x - bx) < blade:
                    return kit.engrave(.65, (x - bx) * 2 + y * .16, light, sp=1.7) if blade > .7 else kit.outline(light, .8)
    return None


def _wave(x, y, cx, h, bend, r, light):
    t = (BAND['base'] - y) / h
    # A fine hooked crest, widening into a low shoulder at the root. Three
    # engraved contour cuts make the tall crests read as water, not stalks.
    width = min(10, 1.5 + h * .22)
    crest = kit.clamp(cx + bend * .5 + width * .32, BAND['x0'] + .15, BAND['x1'] - .15)
    u = (x - crest) / width
    if not -1 <= u <= .65:
        return None
    envelope = (1 - u * u) ** 3 if u < 0 else max(0, 1 - (u / .65) ** .5)
    if t > envelope:
        return None
    edge = (envelope - t) * h
    if edge < .6:
        return kit.outline(light, .85)
    # White open interior with contours following the swept shoulder.
    phase = (t / max(envelope, .001)) * 7 + .4 * u
    tone = .24 + .38 * (1 - t) + .15 * (-light['sun'][0] * u)
    return kit.engrave(tone, phase, light, sp=2.1)


def shade(x, y, days, light):
    if not BAND['x0'] <= x < BAND['x1'] or not BAND['top'] <= y <= BAND['base']:
        return None
    plants = _plants(days)[min(119, int(x / 10))]
    # Frontmost plant wins; transparency elsewhere leaves the world's water
    # intact, especially the genuinely empty winter months.
    for cx, h, bend, r in reversed(plants):
        if y < BAND['base'] - h:
            continue
        if FORM == 'C':
            color = _wave(x, y, cx, h, bend, r, light)
        else:
            color = _reed(x, y, cx, h, bend, r, light, flower=FORM == 'B')
        if color is not None:
            return color
    return None
