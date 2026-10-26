"""The years: one mountain per calendar year on the far shore (docs/WORLD.md). Keep this interface: world.py and
tools/check.py rely on it.

    BAND = dict(x0, x1, base, amp)   years run oldest (x0) to newest (x1); the land stands on y = base (the far shore);
                                     the biggest year's summit is amp units tall.
    summits(years) -> [(x, y)]       the highest point of each year's mountain: y = base - amp * total / max_total. Checked.
    crest(x, years) -> y             top of the land at x (world.py uses it for reflections and keep-outs); base = no land.
    shade(x, y, years, light)        -> (r, g, b) or None: opaque land at (x, y), None in the sky. Just below the base
                                     (y < base + 1) it may draw waterline detail (the reef of a quiet year).
    reflect(x, y, years, light)      -> None or (tone, kind) for a water point y > base (optional, for world.py):
                                     kind 'land' = the mirrored land's tone 0..1 (thicken the water lines by it),
                                     'rim' = a mirrored gold rim, 'foam' = surf around a reef (clear the water lines).

years = [(year, total)], oldest first; the last one is the current year (still growing).

Honesty: the summit of each year sits at its slot centre at exactly base - amp * total / max_total, and no land inside a
year's slot rises above that year's summit (the slot's own summit is the highest point of its slot). Everything else,
the trees, rock, snow, foothills and reefs, is art, shaped to fit under those heights.

The look: forested hills built from rounded tree crowns stacked up the slopes; the great years grow above a treeline into
rock hatched along the fall lines, with ridges and gullies, and above a snowline into snow. Heights of the treeline and
snowline are the same for every year, so a mountain's look follows its size. Nearer masses are darker; the great peak
stands behind its foothills in paler, atmospheric ink. A low sun lights a gold rim along the skyline (kit.warm).
"""
import math
import kit

BAND = dict(x0=40, x1=1160, base=300, amp=165)
TREELINE, SNOWLINE = 70, 122           # heights above the shore (units); the same for every year
Q = 8                                  # silhouette samples per unit

def _slot(years):
    n = len(years); w = (BAND['x1'] - BAND['x0']) / n
    return n, w

def summits(years):
    n, w = _slot(years); mx = max((t for _, t in years), default=0) or 1
    return [(BAND['x0'] + (i + .5) * w, BAND['base'] - BAND['amp'] * t / mx) for i, (_, t) in enumerate(years)]

# ------------------------------------------------------------------ profiles: P(u) falls from 1 (summit) to 0 (foot)
def _table(P):
    """Inverse of a falling profile as a lookup table: v (0..1) -> u."""
    us = [k / 2048 for k in range(2049)]; vs = [P(u) for u in us]; inv = []
    j = 2048
    for k in range(513):
        v = k / 512
        while j > 0 and vs[j - 1] <= v: j -= 1
        inv.append(us[j])
    return lambda v: inv[max(0, min(512, int(v * 512 + .5)))]
def _peak(u): return (1 - u) ** 2.4 * (1 + 1.1 * u)                    # concave flanks sweeping into the skirts
def _hill(u): return 1 - u * u * (3 - 2 * u)                           # a rounded wooded dome
def _shore(u): return 1 - u ** 5                                         # a long low wooded shore
_peak_inv, _hill_inv, _shore_inv = _table(_peak), _table(_hill), _table(_shore)

class Mass:
    """One landform: a profile envelope, an optional forest of crowns, and (for great peaks) rock and snow above it."""
    def __init__(self, c, H, WL, WR, kind, depth, seed, r=3.2, summit=False):
        self.c, self.H, self.WL, self.WR, self.kind, self.depth, self.seed, self.r = c, H, WL, WR, kind, depth, seed, r
        self.P, self.Pinv = dict(peak=(_peak, _peak_inv), shore=(_shore, _shore_inv)).get(kind, (_hill, _hill_inv))
        self.summit = summit
        self.x0, self.x1 = c - WL - r, c + WR + r

    def env(self, x):
        d = x - self.c; W = self.WL if d < 0 else self.WR
        u = abs(d) / W if W > 0 else 1
        return self.H * self.P(u) if u < 1 else 0.

    def treeline(self, x):
        return TREELINE + 7 * math.sin(x * .13 + self.seed) + 4 * math.sin(x * .41 + 2 * self.seed)

    def build(self, cap):
        """Lay out the crowns (rows from the shore up) and sample the silhouette, never above cap(x)."""
        r = self.r; dy, dx = r * .92, r * 1.55
        self.dy, self.dx, self.rows = dy, dx, []
        if self.kind != 'reef':
            top = self.H if self.kind != 'peak' else min(self.H, TREELINE + 16)
            for j in range(int(top / dy) + 2):
                off = self.x0 - dx + (j % 2) * dx * .5 + kit.rnd(self.seed, j, 7) * dx * .4
                row = {}
                for k in range(int((self.x1 - self.x0) / dx) + 3):
                    cx = off + k * dx + (kit.rnd(self.seed, j, k, 1) - .5) * dx * .6
                    rr = r * (.68 + .62 * kit.rnd(self.seed, j, k, 2) ** 1.5)
                    ac = j * dy + r * .3 + (kit.rnd(self.seed, j, k, 3) - .5) * dy * .7
                    lim = min(self.env(cx), cap(cx))
                    if self.kind == 'peak': lim = min(lim, self.treeline(cx) + rr)
                    if ac + rr <= lim and ac > -rr * .3: row[k] = (cx, ac, rr)
                self.rows.append((off, row))
        self.top_crown = None
        if self.summit and self.kind in ('hill', 'shore'):            # the year's summit crown: its top is the summit, exactly
            rr = min(r, self.H); self.top_crown = (self.c, self.H - rr, rr)
        # silhouette samples (heights above the base), capped by the slot heights
        ia, ib = math.floor(self.x0 * Q), math.ceil(self.x1 * Q)
        self.ia, self.sil = ia, []
        crowns = [cr for _, row in self.rows for cr in row.values()] + ([self.top_crown] if self.top_crown else [])
        buckets = {}
        for cr in crowns:
            for b in range(int((cr[0] - cr[2]) // 4), int((cr[0] + cr[2]) // 4) + 1): buckets.setdefault(b, []).append(cr)
        self.buckets = buckets
        for i in range(ia, ib + 1):
            x = i / Q; h = 0.
            for cx, ac, rr in buckets.get(int(x // 4), ()):
                dd = rr * rr - (x - cx) ** 2
                if dd > 0: h = max(h, ac + math.sqrt(dd))
            if self.kind == 'peak':
                e = self.env(x)
                if e > self.treeline(x) - 6: h = max(h, e - self.jag(x))
            elif self.kind == 'reef':
                h = self.env(x)
            self.sil.append(min(h, cap(x)))

    def jag(self, x):
        """Rocky notches cut into the peak's envelope (zero at the summit, so the summit stays exact)."""
        d = x - self.c
        j = 2.2 * abs(math.sin(d * .17 + self.seed)) + 1.1 * abs(math.sin(d * .47 + 2 * self.seed)) + .5 * abs(math.sin(d * 1.3 + self.seed))
        return j * min(1., abs(d) / 7)

    def top(self, x):
        i = int(round(x * Q)) - self.ia
        return self.sil[i] if 0 <= i < len(self.sil) else 0.

    def crown_at(self, x, alt):
        """The front-most crown covering (x, alt) -> (cx, ac, rr, gap) or None. gap = distance to the crown in front."""
        dy, dx = self.dy, self.dx; gap = 9.
        j0 = max(0, int((alt - self.r * 1.9) / dy)); j1 = min(len(self.rows) - 1, int((alt + self.r * 1.7) / dy) + 1)
        best, jb = None, None
        for j in range(j0, j1 + 1):
            if jb is not None and j > jb + 1: break
            off, row = self.rows[j]
            k0 = int((x - off) // dx)
            for k in (k0 - 1, k0, k0 + 1):
                cr = row.get(k)
                if not cr: continue
                cx, ac, rr = cr
                dist = math.hypot(x - cx, alt - ac)
                if dist < rr:
                    if best is None or ac < best[1]: best, jb = cr, j
                elif ac < alt: gap = min(gap, dist - rr)
        tc = self.top_crown
        if tc and math.hypot(x - tc[0], alt - tc[1]) < tc[2] and (best is None or tc[1] < best[1]): best = tc
        return best + (gap,) if best else None

# ------------------------------------------------------------------ the model for a list of years (cached)
_CACHE = {}

def _model(years):
    key = tuple((int(y), int(t)) for y, t in years)
    if key not in _CACHE:
        if len(_CACHE) > 8: _CACHE.clear()
        _CACHE[key] = _build(years)
    return _CACHE[key]

def _build(years):
    base = BAND['base']; n, w = _slot(years); S = summits(years)
    H = [base - sy for _, sy in S]
    edges = [(BAND['x0'] + i * w, BAND['x0'] + (i + 1) * w) for i in range(n)]

    def cap(x):
        if x < BAND['x0']: return H[0] if n else 0.
        if x >= BAND['x1']: return H[-1] if n else 0.
        return H[min(n - 1, int((x - BAND['x0']) / w))]

    def fit(c, Hm, W, side, Pinv, margin):
        """Narrow a flank until it stays under every other slot's summit (with a margin for crowns)."""
        for j, (a, b) in enumerate(edges):
            if side < 0 and b <= c: D = c - b - margin
            elif side > 0 and a >= c: D = a - c - margin
            else: continue
            lim = .9 * H[j]
            if lim >= Hm: continue
            W = min(W, max(1., D) / max(.05, Pinv(lim / Hm)))
        return W

    masses = []
    for i, ((yr, tot), (sx, sy)) in enumerate(zip(years, S)):
        h = H[i]; seed = yr * 7 + 3; jit = lambda k: .85 + .3 * kit.rnd(yr, k)
        if h <= 0: continue
        if h >= 40:                                        # a great year: rock and snow above the forest
            W = 1.25 * h
            WL = fit(sx, h, W * jit(1), -1, _peak_inv, 4); WR = fit(sx, h, W * jit(2), 1, _peak_inv, 4)
            masses.append(Mass(sx, h, WL, WR, 'peak', .55, seed, r=2.9, summit=True))
            # lower summits of the same massif, then forested foothills in front, each under the slot caps
            for k, (dxf, hf, wl, wr, kind, dep) in enumerate(((.66, .46, .95, 1.4, 'peak', .5), (.3, .3, .45, 1.0, 'hill', .26),
                                                              (-.16, .19, .4, .6, 'hill', .2), (.86, .22, .55, .9, 'hill', .14))):
                cf = sx + dxf * h * (.9 + .2 * kit.rnd(yr, 30 + k)); hf = min(h * hf * jit(40 + k), .8 * cap(cf))
                P = _peak_inv if kind == 'peak' else _hill_inv
                wl = fit(cf, hf, wl * h * jit(10 + k), -1, P, 4); wr = fit(cf, hf, wr * h * jit(20 + k), 1, P, 4)
                masses.append(Mass(cf, hf, wl, wr, kind, dep, seed + 11 * k + 5, r=4.4 if kind == 'hill' else 2.9))
        elif h >= 1:                                       # a wooded hill or islet
            r = min(3.2, max(1., h * .45))
            W = max(20., 4.2 * h)
            WL = fit(sx, h, W * jit(1), -1, _hill_inv, r + 1); WR = fit(sx, h, W * jit(2), 1, _hill_inv, r + 1)
            masses.append(Mass(sx, h, WL, WR, 'hill', 0., seed, r=r, summit=True))
        else:                                              # a quiet year: a reef at the waterline
            masses.append(Mass(sx, h, 34, 34, 'reef', 0., seed, r=1.))
    # low wooded shores join neighbouring hills into one coastline (each under both summits), and run off the edges
    for i in range(n - 1):
        if H[i] >= 4 and H[i + 1] >= 4:
            c = (S[i][0] + S[i + 1][0]) / 2; hs = min(2.2, .25 * min(H[i], H[i + 1]))
            masses.append(Mass(c, hs, fit(c, hs, w * .55, -1, _shore_inv, 2), fit(c, hs, w * .55, 1, _shore_inv, 2), 'shore', .05, 91 + i, r=1.5))
    if n and H[0] >= 4:
        c = BAND['x0'] - 14; hs = min(2.6, .3 * H[0])
        masses.append(Mass(c, hs, 60, S[0][0] - c, 'shore', .05, 77, r=1.6))
    for m in masses: m.build(cap)
    masses.sort(key=lambda m: m.depth)                     # front first
    ia = math.floor(-4 * Q); ib = math.ceil((1200 + 4) * Q)
    crest_h = [0.] * (ib - ia + 1)
    for m in masses:
        for k, hv in enumerate(m.sil):
            i = m.ia + k - ia
            if 0 <= i < len(crest_h) and hv > crest_h[i]: crest_h[i] = hv
    return dict(S=S, H=H, masses=masses, ia=ia, crest=crest_h, cap=cap)

def _crest_h(M, x):
    i = int(round(x * Q)) - M['ia']
    return M['crest'][i] if 0 <= i < len(M['crest']) else 0.

def crest(x, years):
    """The true top of the land at x (y, in art units); base where there is no land. Exact at every summit."""
    if not years: return BAND['base']
    M = _model(years)
    for sx, sy in M['S']:
        if abs(x - sx) < .5 / Q: return sy
    return BAND['base'] - _crest_h(M, x)

# ------------------------------------------------------------------ shading
def _low(light):
    """How low the sun is (0 high .. 1 on the horizon): a low sun lights a gold rim along the skyline."""
    return 0. if light['night'] else kit.clamp((.5 - abs(light['sun'][1])) / .3)

def _sample(M, x, y, light):
    """-> (tone, phase, sp, kind) for land at (x, y), or None. kind: 'ink' | 'rim' | 'outline'."""
    base = BAND['base']; alt = base - y
    if alt <= 0: return None
    if alt > _crest_h(M, x): return None
    for m in M['masses']:
        if not (m.x0 <= x <= m.x1): continue
        t = m.top(x)
        if alt > t: continue
        return _shade_mass(M, m, x, y, alt, t, light)
    return None

def _shade_mass(M, m, x, y, alt, t, light):
    sun = light['sun']; low = _low(light)
    ct = _crest_h(M, x); edge = ct - alt
    if low > 0 and edge < 5 * low and abs(ct - t) < .01:                # the skyline catches the low sun
        s = (_crest_h(M, x + 1.5) - _crest_h(M, x - 1.5)) / 3
        nx, ny = -s, -1.; k = math.hypot(nx, ny); face = max(0., (nx * sun[0] + ny * sun[1]) / k)
        wr = 5 * low * (.45 + .55 * face)
        if edge < wr: return (1. if edge < .6 + .9 * face * low else .8 - .55 * edge / wr, edge * 1.4 + x * .05, 1.5, 'rim')
    if t - alt < (.7 if m.depth < .4 else .5):                         # the silhouette line of each mass
        return ((.9 if edge < .9 else .75) - .45 * m.depth, 0, 2.4, 'outline')
    if alt < .8: return (.04, y, 2.4, 'ink')                          # pale beach at the waterline
    haze = m.depth
    n = _normal(m, x, alt)
    if m.kind == 'peak' and alt > m.treeline(x) - 2:
        tone, phase, sp = _rock(m, x, alt, n, light)
    else:
        cr = m.crown_at(x, alt)
        if cr is None:
            if m.kind == 'peak': tone, phase, sp = _rock(m, x, alt, n, light)
            else: tone, phase, sp = .8, y - x * .4, 2.0                   # the shade between trunks
        else:
            cx, ac, rr, gap = cr
            u, v = (x - cx) / rr, (ac - alt) / rr                         # on the crown, v down
            w = math.sqrt(max(0., 1 - u * u - v * v))
            nx, ny, nz = n[0] * .5 + u * .8, n[1] * .5 + v * .8, n[2] * .5 + w * .8
            k = math.sqrt(nx * nx + ny * ny + nz * nz)
            tone = .3 + .6 * _shadow(nx / k, ny / k, nz / k, light) + .14 * max(0., v)
            tone += .1 * kit.clamp(1 - alt / max(m.H, 1))                 # lower slopes sit in the forest's own shade
            tone += .2 * (kit.rnd(int(cx * 8), int(ac * 8)) - .45)          # each crown its own shade
            if gap < .6: tone = max(tone, .95)                            # the dark notch where a crown meets the one in front
            phase, sp = math.hypot(x - cx, (alt - ac + rr * .6) * 1.15), 1.9
            if m.kind == 'peak': tone = .1 + .62 * tone                    # the far forest, in the haze
    tone = tone * (1 - .32 * haze)
    if low: tone = tone * (1 - .45 * low) + .45 * low                    # a low sun: the land turns against the light
    return (kit.clamp(tone), phase, sp, 'ink')

def _shadow(nx, ny, nz, light):
    """Shade 0..1 of a surface with normal n (screen x right, y down, z to the viewer). Relief is modelled with the
    real sun, but its sideways part is at least .75, as an engraver rakes the light to show form."""
    lx, ly = light['sun']
    if abs(lx) < .75: lx = .75 if lx >= 0 else -.75
    ly *= .6; lz = .3; k = math.sqrt(lx * lx + ly * ly + lz * lz)
    return kit.clamp(.55 - .7 * (nx * lx + ny * ly + nz * lz) / k)

def _normal(m, x, alt):
    """The large form's normal: a cone or dome, facing out by its azimuth on the slope."""
    d = x - m.c; v = kit.clamp(alt / m.H, 0, .999)
    W = m.WL if d < 0 else m.WR
    hw = max(.5, m.Pinv(v) * W)
    a = max(-1., min(1., d / hw))
    st = .8 if m.kind == 'peak' else .6; ct = math.sqrt(1 - st * st)
    return (a * st, -ct, math.sqrt(max(0., 1 - a * a)) * st, a, hw)

def _rock(m, x, alt, n, light):
    a, hw = n[3], n[4]; d = x - m.c; s = m.seed
    q = a * 3.4 + .45 * math.sin(a * 4.3 + s) + .3 * math.sin(alt * .09 + s) + .2 * math.sin(alt * .23 + a * 3 + s)
    g = math.cos(2 * math.pi * q)                                         # +1 on a ridge, -1 in a gully
    side = math.sin(2 * math.pi * q)
    side = math.copysign(abs(side) ** .6, side)
    phi = math.asin(a) + .8 * side
    st = .8; ct = .6
    sh = _shadow(math.sin(phi) * st, -ct, math.cos(phi) * st, light)
    tone = .3 + .7 * sh + .14 * (1 - g) / 2
    # fall-line hatching: lines radiate from the summit, branching as the slope widens; a little broken, like a burin
    N = 2 ** math.floor(math.log2(max(1., hw / 2.1)))
    phase = a * N * 2.1 + .15 * math.sin(alt * .5 + a * 7)
    tone *= .82 + .36 * kit.rnd(int(phase / 2.1 + 99), int(alt / 3.2))
    snow = SNOWLINE - 26 * ((1 - g) / 2) ** 2 + 5 * math.sin(d * .17 + s) + 4 * math.sin(d * .53 + 2 * s)
    if alt > snow:                                                        # snow: bare paper, fine lines in shade only
        tone = .3 * kit.clamp(sh - .3)
    elif alt > snow - 2.2: tone = max(tone, .85)                          # the rock edge under the snow
    return tone, phase, 2.1

def _colour(r, light):
    tone, phase, sp, kind = r
    if kind == 'rim': return kit.mix(light['gold'], light['paper'], .12) if tone >= 1 else kit.warm(tone, phase, light, sp)
    if kind == 'outline': return kit.mix(light['paper'], kit.outline(light), tone)
    return kit.engrave(tone, phase, light, sp)

def _reef(M, x, y, light):
    """Waterline detail just under the base: reef rocks awash and the surf around them."""
    for m in M['masses']:
        if m.kind != 'reef' or not (m.c - 34 < x < m.c + 34): continue
        u = (x - m.c) / 34; k = int((x - m.c + 40) / 3.1)
        rock = kit.rnd(m.seed, k, 5) < .55 * (1 - abs(u) ** 2)
        if rock and y < BAND['base'] + .9 - .4 * kit.rnd(m.seed, k, 6): return kit.outline(light)
        if kit.rnd(m.seed, k, 7) < .7 * (1 - abs(u)): return light['paper']
    return None

def shade(x, y, years, light):
    if not years: return None
    M = _model(years)
    if y >= BAND['base']:
        return _reef(M, x, y, light) if y < BAND['base'] + 1.2 else None
    r = _sample(M, x, y, light)
    return _colour(r, light) if r else None

def reflect(x, y, years, light, squash=.5):
    """The land mirrored in still water at (x, y > base): the mirror point is base - (y - base) / squash."""
    if not years or y <= BAND['base']: return None
    M = _model(years); base = BAND['base']
    for m in M['masses']:
        if m.kind == 'reef' and abs(x - m.c) < 34 * (1 + (y - base) * .25) and y - base < 6:
            u = (x - m.c) / (34 * (1 + (y - base) * .25))
            if kit.rnd(m.seed, int((x - m.c) / 4.3), int((y - base) * 1.2), 9) < .6 * (1 - u * u): return (0., 'foam')
    ym = base - (y - base) / squash
    r = _sample(M, x, ym, light)
    if not r: return None
    tone, phase, sp, kind = r
    return (tone if kind == 'ink' else .5, 'rim' if kind == 'rim' else 'land')
