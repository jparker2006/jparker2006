#!/usr/bin/env python3
"""Profile art for github.com/jparker2006.

The last 52 weeks of public GitHub contributions, engraved as one mountain range rising out of a lake:
time runs left to right, each peak is one week, heights share one linear scale. Quiet weeks stay flat
and become the lake. The sun sets behind the busiest week. Everything else (cloud, balloons, ducks,
turtle, koi) is scenery, never data. Every surface is a line-halftone "engraving": ink lines whose
width follows the tone underneath.

    python3 generator/art.py [data/contributions.json] [assets]

Writes assets/art.svg (embedded PNG + live text + fonts), assets/meta.json (for tools/check.py) and
README.md (from README.template.md). Standard library only.
"""
import base64, datetime, json, math, os, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import friends

# ------------------------------------------------------------------ data: 52 weeks ending today
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'contributions.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'assets')
DAYS = dict(json.load(open(DATA))['days'])
LAST = max(DAYS)
NW = 52
_end = datetime.date.fromisoformat(LAST)
WEEKS = []                                             # (first day, last day, contributions)
for w in range(NW - 1, -1, -1):
    e = _end - datetime.timedelta(days=7 * w); s = e - datetime.timedelta(days=6)
    WEEKS.append((s.isoformat(), e.isoformat(), sum(DAYS.get((s + datetime.timedelta(days=i)).isoformat(), 0) for i in range(7))))
WV = [w[2] for w in WEEKS]
WMAX = max(WV)
PI = max(range(NW), key=lambda i: (WV[i], i))         # busiest week (latest one if tied)
TOTAL = sum(WV)
DMAX_DATE = max((d for d in DAYS if d >= WEEKS[0][0]), key=lambda d: (DAYS[d], d))
MON = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# ------------------------------------------------------------------ composition (SVG units)
VW, VH, S = 1200, 500, 1.4                 # 2.4:1 widescreen; raster = 1.4 px per unit
PW, PH = round(VW * S), round(VH * S)
HZ, WL, AMP = 300, 374, 200                # far horizon, the range's waterline, height of the busiest week
X0, SPAN = 40, 980                         # the 52 weeks; the calm water to the right is the future
def week_x(i): return X0 + (i + .5) / NW * SPAN

def spline(vs, p):
    n = len(vs); p = max(0., min(n - 1., p)); i = min(int(p), n - 2); t = p - i
    p0, p1, p2, p3 = vs[max(i - 1, 0)], vs[i], vs[i + 1], vs[min(i + 2, n - 1)]
    return max(0., .5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))

def ridge_top(x):
    """Crest at x: exact at every week's centre, one linear scale. The ends slope into the water over half a
    week (outside the 52 weeks there is no data, so nothing is invented)."""
    p = (x - X0) / SPAN * NW - .5
    if 0 <= p <= NW - 1: return WL - AMP * spline(WV, p) / WMAX
    e, f = (0, 1 + p * 2) if p < 0 else (NW - 1, 1 - (p - NW + 1) * 2)
    return WL - AMP * WV[e] / WMAX * max(0., f) ** 2

PEAK_X = week_x(PI); PEAK_Y = ridge_top(PEAK_X)
SUN = (PEAK_X, HZ - 45, 95)                # setting sun, behind the busiest week
CLOUD = (404, 150)                         # centre of the cloud's flat base (bottom edge)
CLOUD_PARTS = [(-52, -40, 34), (6, -64, 50), (62, -36, 28)]   # circles on a shared baseline (dx, dy, r)
CLOUD_PILL = (110, 56)                     # half-width, height of the rounded base
BALLOONS = [(650, 160, 1.0), (200, 232, .45)]        # big one central, a small one low and far: they step toward the sun
DUCKS = [(150, 455, 1.35), (200, 462, 1.0), (240, 459, 1.0), (279, 464, 1.0)]   # a mother leads three, toward the sun's path
TURTLE, KOI = (420, 412, .95), (742, 452, 1.25)
GULLS = [(758, 198, 1.25), (792, 212, 1.0), (733, 220, .85)]
def _reeds(x0, x1, n, hmin, hmax, lean, seed):
    out = []
    for i in range(n):
        f = ((i * 7919 + seed * 104729) % 1000) / 1000; g = ((i * 3571 + seed * 7177) % 1000) / 1000
        bx = x0 + (x1 - x0) * (i + .5 * f) / n; h = hmin + (hmax - hmin) * g
        out.append((bx, h, lean * (g - .3) * h / 100, 2.2 + 1.6 * f, g > .62))     # base x, height, lean, width, cattail?
    return out
REEDS = (_reeds(-8, 34, 5, 44, 104, 26, 1) + _reeds(50, 88, 3, 34, 70, 18, 3)
         + _reeds(1104, 1132, 3, 46, 92, -20, 2) + _reeds(1150, 1208, 6, 60, 138, -30, 4))   # uneven clumps

# ------------------------------------------------------------------ palette
SKY_TOP, SKY_LOW, WARM = (178, 212, 241), (214, 233, 249), (250, 234, 210)
SKY_INK, INK, WATER_INK, GOLD = (70, 122, 184), (25, 47, 88), (34, 86, 140), (196, 136, 46)
LAKE_FAR, LAKE_NEAR, ROCK, SNOW = (219, 235, 247), (214, 232, 247), (240, 238, 230), (252, 253, 255)
CLOUD_PAPER, CLOUD_INK, CLOUD_LINE = (253, 254, 255), (128, 168, 214), (62, 104, 160)
DUCK, DUCK_INK, BEAK = (247, 210, 84), (184, 126, 30), (222, 132, 58)
ENV_A, ENV_B, BASKET = (238, 186, 82), (252, 247, 236), (150, 104, 44)
BALLOON_INK, REED_INK, REED_HI, FACE_INK, BLUSH = INK, INK, (90, 128, 176), INK, (240, 168, 150)
NIGHT = False
BAYER = [[(v + .5) / 16 for v in row] for row in ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))]

def set_theme(name):
    """Night is a white-line engraving: pale lines on deep navy paper, a moon instead of the sun,
    glowing balloons as the one warm light, sleeping cloud and ducks."""
    global NIGHT, SKY_TOP, SKY_LOW, WARM, SKY_INK, INK, WATER_INK, GOLD, LAKE_FAR, LAKE_NEAR, ROCK, SNOW
    global CLOUD_PAPER, CLOUD_INK, CLOUD_LINE, DUCK, DUCK_INK, BEAK, ENV_A, ENV_B, BASKET
    global BALLOON_INK, REED_INK, REED_HI, FACE_INK, BLUSH
    NIGHT = name == 'night'
    if not NIGHT: return
    SKY_TOP, SKY_LOW, WARM = (9, 18, 41), (25, 44, 82), (40, 60, 100)
    SKY_INK, INK, WATER_INK, GOLD = (140, 168, 214), (176, 198, 232), (118, 154, 206), (230, 206, 146)
    LAKE_FAR, LAKE_NEAR, ROCK, SNOW = (18, 34, 66), (11, 24, 51), (13, 25, 50), (108, 132, 178)
    CLOUD_PAPER, CLOUD_INK, CLOUD_LINE = (106, 128, 172), (66, 86, 130), (196, 210, 236)
    DUCK, DUCK_INK, BEAK = (194, 166, 88), (124, 98, 40), (176, 108, 52)
    ENV_A, ENV_B, BASKET = (248, 186, 80), (252, 224, 150), (108, 72, 28)
    BALLOON_INK, REED_INK, REED_HI, FACE_INK, BLUSH = (116, 70, 22), (4, 10, 24), (58, 84, 128), (28, 42, 74), (170, 112, 104)
    friends.NAVY, friends.PAPER, friends.WATER_INK = (6, 12, 28), (18, 34, 66), (118, 154, 206)
    friends.SHELL_INK, friends.SHELL_PAPER, friends.SKIN_INK, friends.SKIN_PAPER = (70, 56, 30), (128, 112, 82), (50, 66, 44), (100, 118, 96)
    friends.KOI_INK, friends.KOI_PAPER, friends.FIN_PAPER = (150, 80, 36), (196, 150, 110), (150, 160, 182)
    friends.EYE_PAPER, friends.BLUSH = (190, 196, 210), (170, 110, 100)

def clamp(v, a=0., b=1.): return a if v < a else b if v > b else v
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def line(phase, width, aa):
    """Ink coverage of a line pattern with lines at integer phase (width and aa in period units)."""
    d = abs(phase - math.floor(phase + .5))
    return clamp((width * .5 - d) / aa + .5)
def q(c): return round(c * 12) / 12        # quantised coverage keeps the PNG palette small

CREST = [ridge_top((px + .5) / S) for px in range(PW)]

def _duck_shape(bx, by):
    body = ((bx / 13) ** 2 + (by / 6.5) ** 2 <= 1 and by > -4.5) or (bx < -9 and -6 < by < 1 and by > -1.6 * (bx + 16))
    return body or math.hypot(bx - 8, by + 9) <= 5.6 or ((bx - 15.5) / 3.9) ** 2 + ((by + 8) / 1.9) ** 2 <= 1
def duck_at(x, y):
    for dx, dy, s in DUCKS:
        bx, by = (x - dx) / s, (y - dy) / s
        if not (-18 < bx < 21 and -17 < by < 8): continue
        if _duck_shape(bx, by) and not all(_duck_shape(bx + ox, by + oy) for ox, oy in ((.8, 0), (-.8, 0), (0, .8), (0, -.8))):
            return 'edge', bx, by
        if (abs(math.hypot(bx - 10, by + 11.2) - 1.6) < .45 and by > -11.2) if NIGHT else math.hypot(bx - 10, by + 10.5) <= 1.25: return 'eye', bx, by
        if ((bx - 15.5) / 3.9) ** 2 + ((by + 8) / 1.9) ** 2 <= 1: return 'beak', bx, by
        body = ((bx / 13) ** 2 + (by / 6.5) ** 2 <= 1 and by > -4.5) or (bx < -9 and -6 < by < 1 and by > -1.6 * (bx + 16))
        if body or math.hypot(bx - 8, by + 9) <= 5.6: return 'body', bx, by
    return None

def reed_at(x, y):
    """Dark engraved reeds in the near corners (repoussoir): they frame the lake and push the range back."""
    if 90 < x < 1100 or y < VH - 140: return None
    for bx, h, lean, w, cat in REEDS:
        t = (VH + 4 - y) / h                                                            # 0 at the bottom, 1 at the tip
        if not 0 <= t <= 1: continue
        cx = bx + lean * t * t
        if cat and .6 < t < .86 and abs(x - cx) < w * 1.7:                             # cattail head, hatched
            return mix(REED_INK, REED_HI, q(line((y - x * .5) / 1.6, .32, .5) * .8))
        half = w * (1 - t) ** .7 * .5 + .25
        if abs(x - cx) < half:
            return mix(REED_INK, REED_HI, .75) if abs(x - cx - half * .3) < .32 and half > .9 else REED_INK   # a pale line along the blade
    return None

def gull_at(x, y, items=None):
    for gx, gy, s in (GULLS if items is None else items):
        u, v = (x - gx) / s, (y - gy) / s
        if abs(u) < 9 and -4 < v < 2:
            arc = -3.2 * (1 - (abs(u) - 4.5) ** 2 / 20) if abs(u) < 9 else 0          # an "m" of two wing arcs
            if abs(v - arc) < .75 * (1 - abs(u) / 11): return INK
    return None

def friend_at(x, y, items=None):
    for (fx, fy, s), name in (((TURTLE, 'turtle'), (KOI, 'koi')) if items is None else items):
        lx, ly = (x - fx) / s, (y - fy) / s; x0, y0, x1, y1 = friends.BBOX[name]
        if x0 <= lx <= x1 and y0 <= ly <= y1:
            c = getattr(friends, name)(lx, ly)
            if c: return c
    return None

def balloon_at(x, y, items=None):
    """Montgolfier-style hot air balloon: striped gores, ropes, a woven basket (local radius 26)."""
    for bx, by, s in (BALLOONS if items is None else items):
        u, v = (x - bx) / s, (y - by) / s
        if not (-30 < u < 30 and -30 < v < 56): continue
        half = 26 * math.sqrt(max(0., 1 - (v / 26) ** 2)) if v < 8 else 26 * math.sqrt(1 - (8 / 26) ** 2) * (1 - (v - 8) / 30) + 3.5 * (v - 8) / 30
        if v < 38 and abs(u) < half:
            if abs(u) > half - .9 or v < -25.1: return BALLOON_INK                            # outline
            g = math.asin(clamp(u / max(half, 1e-6), -1, 1))                                   # meridian angle
            gore = int((g + math.pi / 2) / (math.pi / 8))
            paper = ENV_A if gore % 2 else ENV_B
            t = clamp(.12 + .3 * (u / 26) * (-1 if bx < SUN[0] else 1) + .2 * clamp((v - 12) / 26))
            if NIGHT: t = clamp(.06 + .24 * clamp((v + 26) / 64) ** 1.5)                          # lit from inside: bright at the throat
            if abs((g + math.pi / 2) / (math.pi / 8) - round((g + math.pi / 2) / (math.pi / 8))) * half < .45: return mix(paper, BALLOON_INK, .8)
            return mix(paper, BALLOON_INK, q(line(g * 26 / 1.6, t, .9 / 1.6 / s)))
        if 36 <= v < 41 and abs(u) < 2.6: return (250, 214, 120) if v < 39 else (236, 150, 60)     # burner glow
        if 38 <= v < 45:                                                                         # ropes
            for r0 in (-3.4, 3.4):
                if abs(u - (r0 + (r0 * .45) * (v - 38) / 7)) < .45: return BALLOON_INK
        if 45 <= v < 53 and abs(u) < 5.2:                                                        # basket
            if abs(u) > 4.4 or v < 45.8 or v > 52.2: return BALLOON_INK
            return mix((236, 214, 170), BASKET, q(line((u + v) / 1.6, .45, .5) * .8 + line((u - v) / 1.6, .3, .5) * .4))
    return None

def smin(a, b, k):
    h = clamp(.5 + .5 * (b - a) / k); return b + (a - b) * h - k * h * (1 - h)
def cloud_sdf(x, y):
    """Signed distance (units, negative inside) to a clean cartoon cloud: three circles on a pill, smoothly joined."""
    u, v = x - CLOUD[0], y - CLOUD[1]
    hw, h = CLOUD_PILL; r = h / 2
    qx = max(abs(u) - (hw - r), 0); d = math.hypot(qx, v + r) - r                     # pill: bottom edge at v = 0
    for dx, dy, cr in CLOUD_PARTS: d = smin(d, math.hypot(u - dx, v - dy) - cr, 9)
    return d
def cloud_at(x, y):
    u, v = x - CLOUD[0], y - CLOUD[1]
    if not (-120 < u < 122 and -116 < v < 2): return None
    d = cloud_sdf(x, y)
    if d > 0: return None
    if d > -(.8 + .8 * clamp((v + 60) / 60)): return CLOUD_LINE                          # outline: fine on top, heavier underneath
    if u > 50 and -2.2 < d < -1.2 and -70 < v < -14: return mix(CLOUD_PAPER, GOLD, .45)  # faint warm rim facing the sun
    ex, ey = u - 6, v + 30                                                             # face on the big puff
    for sx in (-24, 24):
        if NIGHT:
            if abs(math.hypot(ex - sx, ey + 1) - 4.6) < 1.1 and ey > -.5: return FACE_INK   # sleeping eyes
            continue
        if math.hypot(ex - sx + 1.5, ey + 2) < 1.5: return (255, 255, 255)             # eye sparkle
        if ((ex - sx) / 4.2) ** 2 + (ey / 5.6) ** 2 <= 1: return FACE_INK
    if abs(math.hypot(ex, ey - 1) - (6.5 if NIGHT else 9.5)) < 1.3 and ey > (4.5 if NIGHT else 6): return FACE_INK   # smile
    for sx in (-42, 42):
        if ((ex - sx) / 8) ** 2 + ((ey - 9) / 3.4) ** 2 <= 1: return mix(CLOUD_PAPER, BLUSH, .55)
    t = clamp(.36 * clamp((v + 44) / 44) ** 1.6 - .1 * clamp(u / 110))                # clean white crown, shaded underneath
    if t < .03: return CLOUD_PAPER
    ph = -d / 2.5                                                                       # lines follow the outline
    return mix(CLOUD_PAPER, CLOUD_INK, q(line(ph, t, 1 / S / 2.5)))

def VIG(x, y):
    """Vignette: a little more ink toward the corners, so the eye settles on the summit."""
    return .07 * clamp((math.hypot((x - VW / 2) / (VW / 2), (y - VH / 2) / (VH / 2)) - .75) / .6) ** 1.5

_ws, _we, _wv = WEEKS[PI]
def _span(s, e):
    s, e = datetime.date.fromisoformat(s), datetime.date.fromisoformat(e)
    return f'{s.day}–{e.day} {MON[e.month].upper()}' if s.month == e.month else f'{s.day} {MON[s.month].upper()} – {e.day} {MON[e.month].upper()}'
LBL = [f'BUSIEST WEEK · {_span(_ws, _we)}', f'{_wv:,} CONTRIBUTIONS']
LBL_SIZE, LBL_TRACK = 16.5, .8
def mono_w(t, size=LBL_SIZE, track=LBL_TRACK): return len(t) * (size * .6 + track)
LBL_W = max(map(mono_w, LBL))
LBL_X = min(max(PEAK_X, 64 + LBL_W / 2), VW - 64 - LBL_W / 2)      # keep a right margin even when the peak moves
LBL_Y2 = SUN[1] - SUN[2] - 14; LBL_Y1 = LBL_Y2 - 21
START = f'{MON[int(WEEKS[0][0][5:7])].upper()} {WEEKS[0][0][:4]}'
TODAY_X = week_x(NW - 1) + 10
BOXES = [(58, 56, 64 + 11 * 34 * .56 + 8, 98),                                          # title "Jake Parker"
         (LBL_X - LBL_W / 2 - 8, LBL_Y1 - 17, LBL_X + LBL_W / 2 + 8, LBL_Y2 + 7),          # busiest-week label
         (58, WL + 8, 64 + mono_w(START) + 6, WL + 28),
         (TODAY_X - mono_w('TODAY') / 2 - 6, WL + 8, TODAY_X + mono_w('TODAY') / 2 + 6, WL + 28)]
def knock(x, y):
    """0 inside the text boxes, easing back to 1 over 5 units: lines stop short of the letters, like on a banknote."""
    k = 1.
    for x0, y0, x1, y1 in BOXES:
        dx = max(x0 - x, 0, x - x1); dy = max(y0 - y, 0, y - y1)
        k = min(k, clamp(math.hypot(dx, dy) / 14))
    return (.7 + .3 * k) if NIGHT else (.3 + .7 * k)

ANIMATED = True                             # cloud, balloons, gulls and koi live on their own moving layers
def shade(px, py):
    x, y = (px + .5) / S, (py + .5) / S; aa = 1 / S
    d = duck_at(x, y)
    if d:
        part, bx, by = d
        if part == 'eye': return FACE_INK if NIGHT else INK
        if part == 'edge': return FACE_INK if NIGHT else INK
        if part == 'beak': return BEAK
        if not NIGHT and math.hypot(bx - 6.5, by + 11.5) < 1.6: return (255, 250, 232)
        return mix(DUCK, DUCK_INK, q(line((y + .5 * math.sin(x / 2.6)) / 1.5, clamp((by + 3) / 9) * .6, aa / 1.5)))
    f = friend_at(x, y, ((TURTLE, 'turtle'),) if ANIMATED else None)
    if f: return f
    rd = reed_at(x, y)
    if rd: return rd
    # the range
    cy = CREST[px]
    if cy <= y < WL:
        sl = (CREST[min(px + 2, PW - 1)] - CREST[max(px - 2, 0)]) / (4 / S)
        toward = 1 if x < SUN[0] else -1
        if NIGHT:
            lit = .5 + .5 * math.tanh(sl * toward * 1.4); moon = math.exp(-abs(x - SUN[0]) / 300)
            rim = math.exp(-abs(x - SUN[0]) / 240)
            if y - cy < 1.8: return mix(ROCK, GOLD, q(.35 + .6 * rim)) if rim > .15 else mix(ROCK, INK, .5)
            hgt = (WL - cy) / AMP
            if y - cy < clamp((hgt - .5) / .5) * 34 * (.7 + .3 * math.sin(x / 7.3) * math.sin(x / 2.9 + 1)):
                return mix(SNOW, (236, 242, 252), q(line((y - cy) / 2.6, .4 + .25 * lit, aa / 2.6)))   # moonlit snow
            t = .1 + .3 * lit * (.5 + .5 * moon) + .12 * (1 - clamp((WL - y) / 26))
            return mix(ROCK, INK, q(line((y - cy) / 2.8, clamp(t), aa / 2.8)))
        t = .62 * (1 - .38 * math.tanh(sl * toward * 1.4))
        back = math.exp(-abs(x - SUN[0]) / 110)                                                   # backlit by the sun: both faces in shade
        t = t * (1 - back) + .58 * back
        t *= .5 + .5 * clamp((WL - y) / 30)                                                       # mist at the waterline
        rim = math.exp(-abs(x - SUN[0]) / 240)
        if y - cy < 1.8: return mix(ROCK, GOLD, q(.3 + .65 * rim)) if rim > .15 else mix(ROCK, INK, .45)
        hgt = (WL - cy) / AMP                                                                   # 0 at the water, 1 at the busiest week
        snow = clamp((hgt - .5) / .5) * 34 * (.7 + .3 * math.sin(x / 7.3) * math.sin(x / 2.9 + 1))
        if y - cy < snow:
            return mix(SNOW, INK, q(line((y - cy) / 3.4, .06 + .1 * clamp(t), aa / 3.4)))      # snowcap: sparse fine lines
        c = line((y - cy) / 3.0, clamp(t) * .92, aa / 3.0)                                       # contour lines that follow the crest
        if t > .55: c = max(c, line((x + .35 * (y - cy) * toward) / 4.2, (t - .55) * 1.4, aa / 4.2))   # rock ribs, deep shade only
        return mix(ROCK, INK, q(c))
    # lake
    if y >= HZ:
        f = (y - HZ) / (VH - HZ); paper = LAKE_NEAR; ink = WATER_INK
        gx = abs(x - SUN[0]); gw = 12 + (y - HZ) * .3
        t = (.07 + .05 * f) if NIGHT else (.05 + .17 * f ** 1.2) * (1 - .55 * math.exp(-gx / (gw * 2.2)))
        if y < WL: t *= .7                                                                       # the far strip: finer, misty
        if y >= WL:                                                                             # the range, mirrored and broken by ripples
            ym = WL - (y - WL) / .5
            if CREST[px] <= ym < WL and ((int(y * 1.3) * 2654435761 + int(x / 13 + 3 * math.sin(y * .7)) * 40503) >> 7) % 7 > 1:
                hgt = (WL - CREST[px]) / AMP
                snowy = ym - CREST[px] < clamp((hgt - .5) / .5) * 34
                if NIGHT: t = .24 if snowy else t * .25
                else: t += (.1 if snowy else .34) * (1 - (y - WL) / (VH - WL) * .6); ink = INK
        n = 80 * f ** .72; L = int(math.floor(n + .5))
        if gx < gw and ((L * 2654435761 + int((x + L * 5) / 9) * 40503) >> 6) % 5 > 1: t, ink = .5 * (1 - gx / gw) + .14, GOLD   # sun's path: long broken dashes
        for dx, dy, s in DUCKS:
            u, v = (x - dx) / s, (y - dy) / s
            if -36 < u < -8 and abs(abs(v - 2) - (-u - 8) * .16) < .7: t = max(t, .45)
        for (fx, fy, s), a, b in ((TURTLE, 27, 4.6), (KOI, 14, 3)):                                # ripples
            if abs(friends.ell((x - fx) / s, (y - fy) / s, 0, 1.2, a, b)) < .5: t = max(t, .45)
        t += VIG(x, y)
        if ink is WATER_INK and ((L * 2246822519 + int((x + L * 37) / (16 + (L * 7) % 23)) * 3266489917) >> 9) % 9 == 0: t = 0   # gaps: stillness
        wob = .1 * math.sin(x / 9.3 + y * .5) + .07 * math.sin(x / 23.1 - y * .2)
        return mix(paper, ink, q(line(n + wob, clamp(t) * .9 * knock(x, y), aa * 80 * .72 * max(f, .02) ** -.28 / (VH - HZ))))
    if not ANIMATED:
        for fn in (balloon_at, gull_at, cloud_at):
            v = fn(x, y)
            if v: return v
    # sky and sun
    ds = math.hypot(x - SUN[0], y - SUN[1]); r = SUN[2]
    if ds < r:
        th = math.atan2(y - SUN[1], x - SUN[0])
        w = .03 + .27 * (ds / r) ** 2                                                          # near-white core, richer rim
        c1 = line((ds + 3.6 * math.cos(16 * th)) / 5, w, aa / 5)                              # two interlaced wave rings
        c2 = line((ds + 3.6 * math.cos(16 * th + math.pi)) / 5, w, aa / 5)
        c3 = line(ds / 9 , .1, aa / 9) if ds > r - 3 else 0
        return mix((238, 232, 212) if NIGHT else (253, 246, 230), (196, 172, 120) if NIGHT else GOLD, q(max(c1, c2, c3) * .9))
    glow = math.exp(-(ds - r) / 120)
    warm = glow * .85 > BAYER[int(y * S) % 4][int(x * S) % 4]                                       # dithered warmth: no banding rings
    deep = clamp((ds - r) / 900) ** .9                                                                 # deeper blue away from the sun
    paper = WARM if warm and not NIGHT else (SKY_TOP if NIGHT else (SKY_TOP if deep > BAYER[int(y * S) % 4][int(x * S) % 4] * 1.15 else SKY_LOW))
    ink = mix(SKY_INK, GOLD, round(glow * 6) / 6 * .9)
    t = (.022 + .018 * clamp(1 - y / HZ)) if NIGHT else (.025 + .07 * deep)                       # quiet lines; the sun stays the lightest
    t = (t + VIG(x, y)) * knock(x, y)
    w1 = (y + 2.6 * math.sin((x + .4 * y) / 11)) / 4.4
    w2 = (y + 2.6 * math.sin((-x + .4 * y) / 11 + 1.7)) / 4.4
    c = 1 - (1 - line(w1, t, aa / 4.4)) * (1 - line(w2, t, aa / 4.4))
    if ds < r + 45: c = max(c * .5, line(ds / 3.6, .24 * (1 - (ds - r) / 45) * knock(x, y), aa / 3.6))
    th = math.atan2(y - SUN[1], x - SUN[0])
    if not NIGHT and ds > r + 30 and y < HZ - 2:                                         # engraved sunrays, fading smoothly
        fade = math.exp(-(ds - r - 30) / 60) * clamp((ds - r - 30) / 30) * knock(x, y)
        ray = line(th * 36 / math.pi, .075 * fade * (1 if int(math.floor(th * 36 / math.pi + .5)) % 2 else .4), aa * 36 / math.pi / ds)
        if ray > c: c = ray; ink = mix(ink, GOLD, .6)
    return mix(paper, ink, q(c))

# ------------------------------------------------------------------ PNG (palette when possible)
def chunk(tag, data): return len(data).to_bytes(4, 'big') + tag + data + (zlib.crc32(tag + data) & 0xffffffff).to_bytes(4, 'big')
def png(rows, w=None, h=None):
    w, h = w or PW, h or PH
    pal, idx = {}, []
    for row in rows:
        out = bytearray(b'\x00')
        for c in row:
            if c not in pal:
                if len(pal) == 256: pal = None; break
                pal[c] = len(pal)
            out.append(pal[c])
        if pal is None: break
        idx.append(bytes(out))
    head = b'\x89PNG\r\n\x1a\n'
    size = w.to_bytes(4, 'big') + h.to_bytes(4, 'big')
    if pal is not None:
        cols = sorted(pal, key=pal.get)
        plte = b''.join(bytes(c[:3]) for c in cols)
        trns = chunk(b'tRNS', bytes(c[3] for c in cols)) if any(len(c) == 4 for c in cols) else b''
        return head + chunk(b'IHDR', size + b'\x08\x03\x00\x00\x00') + chunk(b'PLTE', plte) + trns + \
            chunk(b'IDAT', zlib.compress(b''.join(idx), 9)) + chunk(b'IEND', b'')
    alpha = len(rows[0][0]) == 4                                   # truecolour fallback keeps transparency for sprites
    raw = b''.join(b'\x00' + b''.join(bytes(c) for c in row) for row in rows)
    return head + chunk(b'IHDR', size + (b'\x08\x06\x00\x00\x00' if alpha else b'\x08\x02\x00\x00\x00')) + \
        chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

def font(name, family):
    data = base64.b64encode(open(os.path.join(ROOT, 'fonts', name), 'rb').read()).decode()
    return f'@font-face{{font-family:"{family}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'

def sprite(fn, x0, y0, x1, y1):
    """Render one sprite on a transparent layer, 2x2 supersampled at the edges. Returns (svg <image>, KB)."""
    w, h = round((x1 - x0) * S), round((y1 - y0) * S); rows = []
    for py in range(h):
        row = []
        for px in range(w):
            hits = [fn(x0 + (px + .25 + .5 * i) / S, y0 + (py + .25 + .5 * j) / S) for i in (0, 1) for j in (0, 1)]
            got = [c for c in hits if c]
            if not got: row.append((0, 0, 0, 0)); continue
            c = fn(x0 + (px + .5) / S, y0 + (py + .5) / S) or got[0]
            row.append(tuple(int(v + .5) for v in c) + (round(len(got) / 4 * 255),))
        rows.append(row)
    data = png(rows, w, h)
    return (f'<image x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" href="data:image/png;base64,{base64.b64encode(data).decode()}"/>',
            len(data) // 1024)

MOTION = """
@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(-16px,3px)}}
@keyframes bob{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-9px)}}
@keyframes glide{0%,100%{transform:translate(0,0)}50%{transform:translate(-14px,-4px)}}
@keyframes leap{0%,60%,100%{transform:translate(0,56px)}68%{transform:translate(-4px,0)}73%{transform:translate(-7px,-1px)}82%{transform:translate(-12px,56px)}}
@keyframes ripple{0%,81%{opacity:0;transform:scale(.35)}85%{opacity:.9}100%{opacity:0;transform:scale(1.6)}}
@keyframes twinkle{0%,100%{opacity:0}50%{opacity:1}}
.cloud{animation:drift 22s ease-in-out infinite}.b1{animation:bob 10s ease-in-out infinite}
.b2{animation:bob 13s ease-in-out -5s infinite}.gulls{animation:glide 16s ease-in-out infinite}
.koi{animation:leap 9s ease-in-out infinite}.ring{transform-box:fill-box;transform-origin:center;animation:ripple 9s ease-out infinite;opacity:0}.glint{animation:twinkle 3.2s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.koi{transform:none}.ring{opacity:0}}
"""

def glints():
    """Glints that twinkle on open water near the sun's (or moon's) path (vector, so they stay crisp)."""
    out, i = [], 0
    for k in range(60):
        x = SUN[0] + (((k * 7919) % 1000) / 1000 - .5) * 260; y = HZ + 6 + ((k * 104729) % 1000) / 1000 * (VH - HZ - 14)
        px = min(max(int(x * S), 0), PW - 1)
        if abs(x - SUN[0]) > 30 + (y - HZ) * .45 or CREST[px] <= y < WL or reed_at(x, y) or duck_at(x, y): continue
        out.append(f'<rect class="glint" x="{x:.1f}" y="{y:.1f}" width="{2.6 + (k % 3):.1f}" height="1" fill="{"#efe2b8" if NIGHT else "#f3c86a"}" '
                   f'style="animation-delay:-{(k * .37) % 3.2:.2f}s"/>'); i += 1
        if i == 16: break
    return ''.join(out)

def clear_sky(x, y, pad=0):
    """True where small sky details may go: away from the moon, cloud, balloons, title and label."""
    if y > HZ - 8 or math.hypot(x - SUN[0], y - SUN[1]) < SUN[2] + 110 + pad: return False
    if cloud_sdf(x, y) < 14 + pad or (40 - pad < x < 270 + pad and 50 - pad < y < 100 + pad): return False
    if abs(x - PEAK_X) < 190 + pad and 125 - pad < y < 160 + pad: return False
    return all(math.hypot(x - bx, y - by - 10 * sc) > 46 * sc + pad for bx, by, sc in BALLOONS)

def stars():
    """Night sky: small four-point stars, a third of them twinkling."""
    out, n = [], 0
    for k in range(400):
        x = ((k * 7919 + 13) % 1187) + 6.5; y = ((k * 104729 + 7) % 997) / 997 * (HZ - 20) + 6
        if not clear_sky(x, y) or ((x * 3 + y) % 7) < 2.4: continue
        r = .7 + ((k * 31) % 9) / 9
        tw = (f' class="star" style="animation-delay:-{(k * .53) % 4:.2f}s"' if k % 3 == 0 else '') + f' fill-opacity="{.4 + .6 * ((k * 17) % 10) / 10:.2f}"'
        out.append(f'<path d="M{x:.1f} {y - 2.4 * r:.1f}L{x + .55 * r:.1f} {y - .55 * r:.1f}L{x + 2.4 * r:.1f} {y:.1f}L{x + .55 * r:.1f} {y + .55 * r:.1f}'
                   f'L{x:.1f} {y + 2.4 * r:.1f}L{x - .55 * r:.1f} {y + .55 * r:.1f}L{x - 2.4 * r:.1f} {y:.1f}L{x - .55 * r:.1f} {y - .55 * r:.1f}Z" fill="#e8eefb"{tw}/>')
        n += 1
        if n == 30: break
    return ''.join(out)

def fireflies():
    """Night: warm fireflies drifting over the reeds."""
    out = []
    for k in range(9):
        side = k % 2; x = (14 + ((k * 37) % 70)) if side == 0 else (1116 + ((k * 53) % 76)); y = 372 + ((k * 61) % 90)
        out.append(f'<circle class="fly" cx="{x}" cy="{y}" r="{1.3 + (k % 3) * .35:.2f}" fill="#f6d27a" style="animation-delay:-{k * .7:.1f}s"/>')
    return ''.join(out)

MOTION = """
@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(-16px,3px)}}
@keyframes bob{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-9px)}}
@keyframes glide{0%,100%{transform:translate(0,0)}50%{transform:translate(-14px,-4px)}}
@keyframes leap{0%,60%,100%{transform:translate(0,56px)}68%{transform:translate(-4px,0)}73%{transform:translate(-7px,-1px)}82%{transform:translate(-12px,56px)}}
@keyframes ripple{0%,81%{opacity:0;transform:scale(.35)}85%{opacity:.9}100%{opacity:0;transform:scale(1.6)}}
@keyframes twinkle{0%,100%{opacity:0}50%{opacity:1}}
@keyframes shine{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes float{0%{opacity:0;transform:translate(0,6px)}30%,70%{opacity:1}100%{opacity:0;transform:translate(8px,-10px)}}
@keyframes wander{0%,100%{transform:translate(0,0);opacity:.2}50%{transform:translate(6px,-8px);opacity:1}}
.cloud{animation:drift 22s ease-in-out infinite}.b1{animation:bob 10s ease-in-out infinite}
.b2{animation:bob 13s ease-in-out -5s infinite}.gulls{animation:glide 16s ease-in-out infinite}
.koi{animation:leap 9s ease-in-out infinite}.ring{transform-box:fill-box;transform-origin:center;animation:ripple 9s ease-out infinite;opacity:0}.glint{animation:twinkle 3.2s ease-in-out infinite}
.star{animation:shine 4s ease-in-out infinite}.fly{animation:wander 5s ease-in-out infinite}
.z1{animation:float 4.5s ease-in-out infinite}.z2{animation:float 4.5s ease-in-out -1.5s infinite}.z3{animation:float 4.5s ease-in-out -3s infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.koi{transform:none}.ring{opacity:0}}
"""

def span_label(s, e):
    s, e = datetime.date.fromisoformat(s), datetime.date.fromisoformat(e)
    return f'{s.day}–{e.day} {MON[e.month].upper()}' if s.month == e.month else f'{s.day} {MON[s.month].upper()} – {e.day} {MON[e.month].upper()}'

def microtext(ink):
    """Banknote microprint: the real ledger, one entry per week, along the waterline. A hairline of texture at
    normal size; zoom in and every week's count is there."""
    out = []
    for i, (st, en, v) in enumerate(WEEKS):
        d = datetime.date.fromisoformat(st)
        out.append(f'<text x="{week_x(i):.1f}" y="{WL + 3.6:.1f}" text-anchor="middle" font-family="Geist Mono" font-size="2.6" '
                   f'fill="{ink}" fill-opacity=".5" data-micro="1" aria-hidden="true">{d.day} {MON[d.month].upper()} {v:,}</text>')
    return ''.join(out)

def build(theme):
    set_theme(theme)
    rows = [[tuple(int(v + .5) for v in shade(px, py)) for px in range(PW)] for py in range(PH)]
    art = png(rows)
    cx, cy = CLOUD
    layers = [('cloud', sprite(cloud_at, cx - 122, cy - 118, cx + 124, cy + 3))]
    for i, (bx, by, sc) in enumerate(BALLOONS):
        layers.append((f'b{i + 1}', sprite(lambda x, y, b=(bx, by, sc): balloon_at(x, y, [b]), bx - 31 * sc, by - 31 * sc, bx + 31 * sc, by + 55 * sc)))
    if not NIGHT:
        gx0 = min(g[0] - 12 * g[2] for g in GULLS); gx1 = max(g[0] + 12 * g[2] for g in GULLS)
        gy0 = min(g[1] - 6 * g[2] for g in GULLS); gy1 = max(g[1] + 4 * g[2] for g in GULLS)
        layers.append(('gulls', sprite(gull_at, gx0, gy0, gx1, gy1)))
    kx, ky, ks = KOI
    layers.append(('koi', sprite(lambda x, y: friend_at(x, y, ((KOI, 'koi'),)), kx - 36 * ks, ky - 42 * ks, kx + 28 * ks, ky + 6 * ks)))
    koi_clip = f'<clipPath id="water-koi"><rect x="{kx - 40 * ks:.1f}" y="{ky - 60 * ks:.1f}" width="{70 * ks:.1f}" height="{60 * ks + 1.5:.1f}"/></clipPath>'
    moving = ''.join((f'<g clip-path="url(#water-koi)"><g class="koi">{img}</g></g>' if name == 'koi' else f'<g class="{name}">{img}</g>')
                     for name, (img, kb) in layers)
    ink = '#e6edf8' if NIGHT else '#192f58'
    hexc = lambda c: '#%02x%02x%02x' % tuple(int(v) for v in c)
    sky, lake = (hexc(SKY_TOP), hexc(LAKE_NEAR)) if NIGHT else (hexc(SKY_LOW), hexc(LAKE_NEAR))
    halo = ''
    mono = f'font-family="Geist Mono" font-size="{LBL_SIZE}" letter-spacing="{LBL_TRACK}"'
    ring_ink = '#b9cdec' if NIGHT else '#22568c'
    rings = ''.join(f'<ellipse class="ring" cx="{kx - 12 * ks:.1f}" cy="{ky + 1:.1f}" rx="{a * ks:.1f}" ry="{b * ks:.1f}" fill="none" '
                    f'stroke="{ring_ink}" stroke-width=".9" style="animation-delay:{dl}s"/>' for a, b, dl in ((12, 2.6, 0), (20, 4.2, .25)))
    extras = (stars() + fireflies()) if NIGHT else ''
    zzz = ''.join(f'<text class="z{i + 1}" x="{cx + 84 + 13 * i}" y="{cy - 76 - 15 * i}" font-family="Geist Mono" font-size="{16 + 3 * i}" '
                  f'fill="{ink}" data-bg="{sky}">z</text>' for i in range(3)) if NIGHT else ''
    title = 'Jake Parker: the last 52 weeks of GitHub contributions, engraved as a mountain range rising from a lake' + (' at night' if NIGHT else '')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" role="img">'
           f'<title>{title}</title>'
           f'<style>{font("Geist-Medium.woff2", "Geist")}{font("GeistMono-Regular.woff2", "Geist Mono")}</style>'
           f'<style>{MOTION}</style>'
           f'<defs><clipPath id="card"><rect width="{VW}" height="{VH}" rx="16"/></clipPath>{koi_clip}</defs>'
           f'<g clip-path="url(#card)"><image width="{VW}" height="{VH}" href="data:image/png;base64,{base64.b64encode(art).decode()}"/>'
           f'{extras}{glints()}{rings}{moving}</g>{zzz}'
           f'<text x="64" y="86" font-family="Geist" font-size="34" letter-spacing="-.4" fill="{ink}" data-bg="{sky}">Jake Parker</text>'
           f'<polyline points="{LBL_X:.1f},{LBL_Y2 + 7:.1f} {PEAK_X:.1f},{LBL_Y2 + 7 + (8 if LBL_X != PEAK_X else 0):.1f} {PEAK_X:.1f},{PEAK_Y - 4:.1f}" fill="none" stroke="{ink}" stroke-width="1" stroke-opacity=".75"/>'
           f'<circle cx="{PEAK_X:.1f}" cy="{PEAK_Y - 2:.1f}" r="2.4" fill="{ink}"/>'
           f'<text x="{LBL_X:.1f}" y="{LBL_Y1:.1f}" text-anchor="middle" {mono} fill="{ink}" data-bg="{sky}">{LBL[0]}</text>'
           f'<text x="{LBL_X:.1f}" y="{LBL_Y2:.1f}" text-anchor="middle" {mono} fill="{ink}" fill-opacity=".85" data-bg="{sky}">{LBL[1]}</text>'
           f'{microtext(ink)}'
           f'<text x="64" y="{WL + 22}" {mono} fill="{ink}" fill-opacity=".85" data-bg="{lake}">{START}</text>'
           f'<text x="{TODAY_X:.1f}" y="{WL + 22}" text-anchor="middle" {mono} fill="{ink}" fill-opacity=".85" data-bg="{lake}">TODAY</text>'
           f'</svg>')
    print(f'{theme}: {len(svg) // 1024} KB (background {len(art) // 1024} KB; layers ' + ', '.join(f'{n} {kb}' for n, (_, kb) in layers) + ')')
    return svg

def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, name in (('day', 'art.svg'), ('night', 'art-night.svg')):
        open(os.path.join(OUT, name), 'w').write(build(theme))
    ws, we, wv = WEEKS[PI]
    meta = {'amp': AMP, 'vmax': WMAX, 'total': TOTAL, 'peak': [ws, wv], 'last': LAST,
            'ridges': [{'month': 'weeks', 'baseline': WL, 'weeks': [[s, e, v, ridge_top(week_x(i))] for i, (s, e, v) in enumerate(WEEKS)]}]}
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))
    readme()
    print(f'busiest week {ws}..{we} = {wv}, 52-week total {TOTAL:,}')

def readme():
    """Fill README.template.md with the same numbers the art shows."""
    tpl = os.path.join(ROOT, 'README.template.md')
    if not os.path.exists(tpl): return
    ws, we, wv = WEEKS[PI]; first = WEEKS[0][0]; last31 = sorted(DAYS.items())[-31:]
    fmt = lambda d: f'{MON[int(d[5:7])]} {int(d[8:])}, {d[:4]}'
    vals = {'TOTAL': f'{TOTAL:,}', 'FIRST': fmt(first), 'LAST': fmt(LAST), 'WEEK_VALUE': f'{wv:,}',
            'WEEK_SPAN': f'{fmt(ws)} – {fmt(we)}', 'DAY_VALUE': str(DAYS[DMAX_DATE]), 'DAY_DATE': fmt(DMAX_DATE),
            'LAST31': f'{sum(v for _, v in last31):,}'}
    text = open(tpl).read()
    for k, v in vals.items(): text = text.replace('{{' + k + '}}', v)
    open(os.path.join(ROOT, 'README.md'), 'w').write(text)

if __name__ == '__main__':
    main()
