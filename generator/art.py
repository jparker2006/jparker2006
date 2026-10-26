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
CLOUD, CLOUD_K = (404, 104), 3.3
LOBES = [(dx * CLOUD_K, dy * CLOUD_K, r * CLOUD_K) for dx, dy, r in [(-27, 5, 10), (-12, -5, 13.5), (8, -8, 15), (26, 1, 11), (-2, 7, 12.5)]]
CLOUD_BOTTOM = CLOUD[1] + 15 * CLOUD_K
BALLOONS = [(650, 160, 1.0), (808, 88, .56)]
DUCKS = [(150, 455, 1.35), (200, 462, 1.0), (240, 459, 1.0), (279, 464, 1.0)]   # a mother leads three, toward the sun's path
TURTLE, KOI = (300, 330, 1.1), (742, 452, 1.25)

# ------------------------------------------------------------------ palette
SKY_TOP, SKY_LOW, WARM = (186, 219, 244), (226, 240, 250), (251, 231, 203)
SKY_INK, INK, WATER_INK, GOLD = (70, 122, 184), (25, 47, 88), (34, 86, 140), (196, 136, 46)
LAKE_FAR, LAKE_NEAR, ROCK = (219, 235, 247), (205, 226, 243), (240, 238, 230)
CLOUD_PAPER, CLOUD_INK, CLOUD_LINE = (253, 254, 255), (128, 168, 214), (62, 104, 160)
DUCK, DUCK_INK, BEAK = (247, 210, 84), (184, 126, 30), (222, 132, 58)
ENV_A, ENV_B, BASKET = (246, 214, 140), (251, 246, 234), (150, 104, 44)

def clamp(v, a=0., b=1.): return a if v < a else b if v > b else v
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def line(phase, width, aa):
    """Ink coverage of a line pattern with lines at integer phase (width and aa in period units)."""
    d = abs(phase - math.floor(phase + .5))
    return clamp((width * .5 - d) / aa + .5)
def q(c): return round(c * 12) / 12        # quantised coverage keeps the PNG palette small

CREST = [ridge_top((px + .5) / S) for px in range(PW)]

def duck_at(x, y):
    for dx, dy, s in DUCKS:
        bx, by = (x - dx) / s, (y - dy) / s
        if math.hypot(bx - 10, by + 10.5) <= 1.25: return 'eye', bx, by
        if ((bx - 15.5) / 3.9) ** 2 + ((by + 8) / 1.9) ** 2 <= 1: return 'beak', bx, by
        body = ((bx / 13) ** 2 + (by / 6.5) ** 2 <= 1 and by > -4.5) or (bx < -9 and -6 < by < 1 and by > -1.6 * (bx + 16))
        if body or math.hypot(bx - 8, by + 9) <= 5.6: return 'body', bx, by
    return None

def friend_at(x, y):
    for (fx, fy, s), name in ((TURTLE, 'turtle'), (KOI, 'koi')):
        lx, ly = (x - fx) / s, (y - fy) / s; x0, y0, x1, y1 = friends.BBOX[name]
        if x0 <= lx <= x1 and y0 <= ly <= y1:
            c = getattr(friends, name)(lx, ly)
            if c: return c
    return None

def balloon_at(x, y):
    """Montgolfier-style hot air balloon: striped gores, ropes, a woven basket (local radius 26)."""
    for bx, by, s in BALLOONS:
        u, v = (x - bx) / s, (y - by) / s
        if not (-30 < u < 30 and -30 < v < 56): continue
        half = 26 * math.sqrt(max(0., 1 - (v / 26) ** 2)) if v < 8 else 26 * math.sqrt(1 - (8 / 26) ** 2) * (1 - (v - 8) / 30) + 3.5 * (v - 8) / 30
        if v < 38 and abs(u) < half:
            if abs(u) > half - .9 or v < -25.1: return INK                                    # outline
            g = math.asin(clamp(u / max(half, 1e-6), -1, 1))                                   # meridian angle
            gore = int((g + math.pi / 2) / (math.pi / 8))
            paper = ENV_A if gore % 2 else ENV_B
            t = clamp(.18 + .32 * (u / 26) * (-1 if bx < SUN[0] else 1) + .2 * clamp((v - 12) / 26))
            if abs((g + math.pi / 2) / (math.pi / 8) - round((g + math.pi / 2) / (math.pi / 8))) * half < .45: return mix(paper, INK, .8)
            return mix(paper, INK, q(line(g * 26 / 1.6, t, .9 / 1.6 / s)))
        if 38 <= v < 45:                                                                         # ropes
            for r0 in (-3.4, 3.4):
                if abs(u - (r0 + (r0 * .45) * (v - 38) / 7)) < .45: return INK
        if 45 <= v < 53 and abs(u) < 5.2:                                                        # basket
            if abs(u) > 4.4 or v < 45.8 or v > 52.2: return INK
            return mix((236, 214, 170), BASKET, q(line((u + v) / 1.6, .45, .5) * .8 + line((u - v) / 1.6, .3, .5) * .4))
    return None

def cloud_at(x, y):
    if y > CLOUD_BOTTOM or abs(x - CLOUD[0]) > 150: return None
    best = -1.
    for dx, dy, r in LOBES:
        v = 1 - math.hypot(x - CLOUD[0] - dx, y - CLOUD[1] - dy) / r
        if v > best: best, lob = v, (dx, dy, r)
    if best <= 0: return None
    dx, dy, r = lob; cx, cy = CLOUD
    if best * r < .95 or CLOUD_BOTTOM - y < .95: return CLOUD_LINE
    ex, ey = x - cx, y - cy - 18                                                                  # face, a little low and wide
    for sx in (-20, 20):
        if math.hypot(ex - sx + 1.3, ey + 1.6) < 1.25: return (255, 255, 255)                     # eye sparkle
        if ((ex - sx) / 3.8) ** 2 + (ey / 5) ** 2 <= 1: return INK
    if abs(math.hypot(ex, ey - 1) - 8.5) < 1.3 and ey > 5.5: return INK                           # smile
    for sx in (-33, 33):
        if ((ex - sx) / 7.5) ** 2 + ((ey - 8) / 3.2) ** 2 <= 1: return mix(CLOUD_PAPER, (240, 168, 150), .55)
    nx, ny = (x - cx - dx) / r, (y - cy - dy) / r
    lit = nx * .45 - ny * .75 + math.sqrt(max(0, 1 - nx * nx - ny * ny)) * .45                   # sun on the right
    t = clamp(.16 - .16 * lit + .3 * clamp((y - cy - 8) / 40))
    ph = (y + 2.4 * math.sin(x / 31 + y / 19) + 1.2 * math.sin(x / 11)) / 2.4
    return mix(CLOUD_PAPER, CLOUD_INK, q(line(ph, t, 1 / S / 2.4)))

def shade(px, py):
    x, y = (px + .5) / S, (py + .5) / S; aa = 1 / S
    d = duck_at(x, y)
    if d:
        part, bx, by = d
        if part == 'eye': return INK
        if part == 'beak': return BEAK
        if math.hypot(bx - 6.5, by + 11.5) < 1.6: return (255, 250, 232)
        return mix(DUCK, DUCK_INK, q(line((y + .5 * math.sin(x / 2.6)) / 1.5, clamp((by + 3) / 9) * .6, aa / 1.5)))
    f = friend_at(x, y)
    if f: return f
    # the range
    cy = CREST[px]
    if cy <= y < WL:
        sl = (CREST[min(px + 2, PW - 1)] - CREST[max(px - 2, 0)]) / (4 / S)
        toward = 1 if x < SUN[0] else -1
        t = .62 * (1 - .38 * math.tanh(sl * toward * 1.4))
        t *= .5 + .5 * clamp((WL - y) / 30)                                                       # mist at the waterline
        rim = math.exp(-abs(x - SUN[0]) / 240)
        if y - cy < 1.8: return mix(ROCK, GOLD, q(.3 + .65 * rim)) if rim > .15 else mix(ROCK, INK, .45)
        c = line((y - cy) / 2.8, clamp(t) * .95, aa / 2.8)
        if t > .5: c = max(c, line((x * .7 + y) / 3, (t - .5) * 1.5, aa / 3))
        return mix(ROCK, INK, q(c))
    # lake
    if y >= HZ:
        f = (y - HZ) / (VH - HZ); paper = mix(LAKE_FAR, LAKE_NEAR, round(f * 4) / 4); ink = WATER_INK
        t = .06 + .1 * f
        h = (WL - CREST[px]) * .38
        if y >= WL and h > .5 and y < WL + h and (int(y * 1.3) + int(x / 9)) % 4:
            t += .38 * (1 - (y - WL) / h); ink = INK                                                # broken mirror of the range
        gx = abs(x - SUN[0]); gw = 12 + (y - HZ) * .3
        if gx < gw and ((int(y * .8) * 5 + int(x / 7)) % 4) < 2: t, ink = .55 * (1 - gx / gw) + .12, GOLD   # sun's path
        for dx, dy, s in DUCKS:
            u, v = (x - dx) / s, (y - dy) / s
            if -36 < u < -8 and abs(abs(v - 2) - (-u - 8) * .16) < .7: t = max(t, .45)
        for (fx, fy, s), a, b in ((TURTLE, 27, 4.6), (KOI, 14, 3)):                                # ripples
            if abs(friends.ell((x - fx) / s, (y - fy) / s, 0, 1.2, a, b)) < .5: t = max(t, .45)
        n = 80 * f ** .72
        wob = .1 * math.sin(x / 9.3 + y * .5) + .07 * math.sin(x / 23.1 - y * .2)
        return mix(paper, ink, q(line(n + wob, clamp(t) * .9, aa * 80 * .72 * max(f, .02) ** -.28 / (VH - HZ))))
    b = balloon_at(x, y)
    if b: return b
    c = cloud_at(x, y)
    if c: return c
    # sky and sun
    ds = math.hypot(x - SUN[0], y - SUN[1]); r = SUN[2]
    if ds < r: return mix((253, 246, 230), GOLD, q(line(ds / 3, .16 + .2 * (ds / r) ** 2, aa / 3) * .85))
    glow = round(math.exp(-(ds - r) / 130) * 8) / 8
    paper = mix(mix(SKY_TOP, SKY_LOW, round(clamp(y / HZ) * 6) / 6), WARM, glow * .9)
    ink = mix(SKY_INK, GOLD, glow * .9)
    t = (.1 - .05 * clamp(y / HZ)) * (1 - .7 * glow)
    w1 = (y + 2 * math.sin((x + .4 * y) / 5.4)) / 2.7
    w2 = (y + 2 * math.sin((-x + .4 * y) / 5.4 + 1.7)) / 2.7
    c = 1 - (1 - line(w1, t, aa / 2.7)) * (1 - line(w2, t, aa / 2.7))
    if ds < r + 80: c = max(c * .5, line(ds / 3.6, .3 * (1 - (ds - r) / 80), aa / 3.6))
    return mix(paper, ink, q(c))

# ------------------------------------------------------------------ PNG (palette when possible)
def chunk(tag, data): return len(data).to_bytes(4, 'big') + tag + data + (zlib.crc32(tag + data) & 0xffffffff).to_bytes(4, 'big')
def png(rows):
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
    size = PW.to_bytes(4, 'big') + PH.to_bytes(4, 'big')
    if pal is not None:
        plte = b''.join(bytes(c) for c in sorted(pal, key=pal.get))
        return head + chunk(b'IHDR', size + b'\x08\x03\x00\x00\x00') + chunk(b'PLTE', plte) + \
            chunk(b'IDAT', zlib.compress(b''.join(idx), 9)) + chunk(b'IEND', b'')
    raw = b''.join(b'\x00' + b''.join(bytes(c) for c in row) for row in rows)
    return head + chunk(b'IHDR', size + b'\x08\x02\x00\x00\x00') + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

def font(name, family):
    data = base64.b64encode(open(os.path.join(ROOT, 'fonts', name), 'rb').read()).decode()
    return f'@font-face{{font-family:"{family}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'

def span_label(s, e):
    s, e = datetime.date.fromisoformat(s), datetime.date.fromisoformat(e)
    return f'{s.day}–{e.day} {MON[e.month].upper()}' if s.month == e.month else f'{s.day} {MON[s.month].upper()} – {e.day} {MON[e.month].upper()}'

def main():
    rows = [[tuple(int(v + .5) for v in shade(px, py)) for px in range(PW)] for py in range(PH)]
    art = png(rows)
    navy, paper = '#192f58', '#e6f1fa'
    halo = f'stroke="{paper}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
    ws, we, wv = WEEKS[PI]
    label = f'BUSIEST WEEK · {span_label(ws, we)} · {wv:,}'
    ty = SUN[1] - SUN[2] - 12
    mono = 'font-family="Geist Mono" font-size="16.5" letter-spacing="1.6"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" role="img">'
           f'<title>Jake Parker: the last 52 weeks of GitHub contributions, engraved as a mountain range rising from a lake</title>'
           f'<style>{font("Geist-Medium.woff2", "Geist")}{font("GeistMono-Regular.woff2", "Geist Mono")}</style>'
           f'<defs><clipPath id="card"><rect width="{VW}" height="{VH}" rx="16"/></clipPath></defs>'
           f'<g clip-path="url(#card)"><image width="{VW}" height="{VH}" href="data:image/png;base64,{base64.b64encode(art).decode()}"/></g>'
           f'<text x="64" y="86" font-family="Geist" font-size="34" letter-spacing="-.4" fill="{navy}" data-bg="{paper}" {halo}>Jake Parker</text>'
           f'<line x1="{PEAK_X:.1f}" y1="{ty + 8:.1f}" x2="{PEAK_X:.1f}" y2="{PEAK_Y - 4:.1f}" stroke="{navy}" stroke-width="1" stroke-opacity=".75"/>'
           f'<circle cx="{PEAK_X:.1f}" cy="{PEAK_Y - 2:.1f}" r="2.4" fill="{navy}"/>'
           f'<text x="{PEAK_X:.1f}" y="{ty:.1f}" text-anchor="middle" {mono} fill="{navy}" data-bg="{paper}" {halo}>{label}</text>'
           f'<text x="{X0 + 4}" y="{WL + 22}" {mono} fill="{navy}" fill-opacity=".85" data-bg="{paper}" {halo}>{MON[int(WEEKS[0][0][5:7])].upper()} {WEEKS[0][0][:4]}</text>'
           f'<text x="{week_x(NW - 1) + 10:.1f}" y="{WL + 22}" text-anchor="middle" {mono} fill="{navy}" fill-opacity=".85" data-bg="{paper}" {halo}>TODAY</text>'
           f'</svg>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'art.svg'), 'w').write(svg)
    meta = {'amp': AMP, 'vmax': WMAX, 'total': TOTAL, 'peak': [ws, wv], 'last': LAST,
            'ridges': [{'month': 'weeks', 'baseline': WL, 'weeks': [[s, e, v, ridge_top(week_x(i))] for i, (s, e, v) in enumerate(WEEKS)]}]}
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))
    readme()
    print(f'art.svg {len(svg) // 1024} KB (png {len(art) // 1024} KB), busiest week {ws}..{we} = {wv}, 52-week total {TOTAL:,}')

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
