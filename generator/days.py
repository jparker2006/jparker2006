"""The days: one living thing per day along the near shore (docs/WORLD.md). PLACEHOLDER DRAWINGS: the days artist
replaces them. Keep this interface; world.py and tools/check.py rely on it.

    BAND = dict(x0, x1, base, top)   the strip (art units): days run oldest (x0) to newest (x1); the busiest day of the
                                     window reaches `top`, a day with nothing stays at `base`.
    heights(days) -> [h]             exact size of each day's thing in units: (base - top) * count / max_count. Checked.
    x_of(i, n) -> x                  centre of day i of n.
    shade(x, y, days, light)         -> (r, g, b) or None: the strip (plants and the ground or water they grow from).
    SLICES = 4                       world.py cuts the strip into this many vertical slices that sway gently.

days = [(date, count)] for the rolling last 365 days, oldest first. Draw with kit.engrave() so every moment works.
"""
import kit

BAND = dict(x0=0, x1=1200, base=500, top=432)
SLICES = 4

def heights(days):
    mx = max((c for _, c in days), default=0) or 1
    return [(BAND['base'] - BAND['top']) * c / mx for _, c in days]

def x_of(i, n):
    return BAND['x0'] + (i + .5) * (BAND['x1'] - BAND['x0']) / n

_cache = {}
def shade(x, y, days, light):
    key = id(days)
    if key not in _cache: _cache.clear(); _cache[key] = heights(days)
    hs = _cache[key]; n = len(hs)
    i = int((x - BAND['x0']) / (BAND['x1'] - BAND['x0']) * n)
    if not 0 <= i < n: return None
    if y > BAND['base'] - 3: return kit.engrave(.55, y * 1.3, light)            # the bank of the shore
    cx = x_of(i, n)
    if abs(x - cx) < .5 and BAND['base'] - hs[i] - 3 <= y: return kit.outline(light)   # a plain stalk
    return None
