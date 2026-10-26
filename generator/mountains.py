"""The years: one mountain per calendar year on the far shore (docs/WORLD.md). PLACEHOLDER DRAWINGS: the mountains
artist replaces them. Keep this interface; world.py and tools/check.py rely on it.

    BAND = dict(x0, x1, base, amp)   years run oldest (x0) to newest (x1); the land stands on y = base (the far shore);
                                     the biggest year's summit is amp units tall.
    summits(years) -> [(x, y)]       the highest point of each year's mountain: y = base - amp * total / max_total. Checked.
    crest(x, years) -> y             top of the land at x (world.py uses it for reflections and keep-outs); base = no land.
    shade(x, y, years, light)        -> (r, g, b) or None: opaque land at (x, y), None in the sky and below the base.

years = [(year, total)], oldest first; the last one is the current year (still growing). Summits must be exact and no
part of a year's mountain may rise above its own summit. Draw with kit.engrave() so every moment works.
"""
import kit

BAND = dict(x0=40, x1=1160, base=300, amp=165)

def _slot(years):
    n = len(years); w = (BAND['x1'] - BAND['x0']) / n
    return n, w

def summits(years):
    n, w = _slot(years); mx = max((t for _, t in years), default=0) or 1
    return [(BAND['x0'] + (i + .5) * w, BAND['base'] - BAND['amp'] * t / mx) for i, (_, t) in enumerate(years)]

def crest(x, years):
    n, w = _slot(years); best = BAND['base']
    for (sx, sy) in summits(years):
        h = BAND['base'] - sy
        if h > 0: best = min(best, sy + abs(x - sx) * (h / (w * .55)))     # simple cone, half-width = 0.55 slot
    return min(best, BAND['base'])

def shade(x, y, years, light):
    top = crest(x, years)
    if not top <= y < BAND['base']: return None
    if y - top < 1: return kit.outline(light)
    return kit.engrave(.45, y - top, light)
