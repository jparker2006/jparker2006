#!/usr/bin/env python3
"""Profile art for github.com/jparker2006.

The last twelve months of public GitHub contributions, engraved as a landscape: one ridge per month
(oldest at the back), ridge height = contributions that day on one shared linear scale. Quiet stretches
are a calm lake. The sun sets behind the busiest day. Every surface is drawn by a line-halftone
"engraving" shader: ink lines on paper whose width follows the tone underneath.

    python3 generator/art.py [data/contributions.json] [assets]

Writes assets/art.svg (embedded PNG + live text + fonts), assets/meta.json (for tools/check.py) and
README.md (from README.template.md). Standard library only.
"""
import base64, calendar, json, math, os, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ data
def load(path):
    days = dict(json.load(open(path))['days'])
    last = max(d for d, v in days.items())
    y, m = int(last[:4]), int(last[5:7])
    months = []
    for back in range(11, -1, -1):
        mm, yy = m - back, y
        while mm <= 0: mm, yy = mm + 12, yy - 1
        months.append((yy, mm))
    dates = [[f'{yy}-{mm:02d}-{d:02d}' for d in range(1, calendar.monthrange(yy, mm)[1] + 1)
              if f'{yy}-{mm:02d}-{d:02d}' <= last] for yy, mm in months]
    values = [[days.get(d, 0) for d in ds] for ds in dates]
    return days, last, months, dates, values

DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'contributions.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'assets')
DAYS, LAST, MONTHS, DATES, VALUES = load(DATA)
K = len(MONTHS)
VMAX = max(max(v) for v in VALUES)
PK, PI = max(((k, i) for k in range(K) for i in range(len(VALUES[k]))), key=lambda p: (VALUES[p[0]][p[1]], p))
PEAK_DATE = DATES[PK][PI]
TOTAL = sum(map(sum, VALUES))
MON = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# ------------------------------------------------------------------ composition (SVG units)
VW, VH, S = 1200, 500, 1.4                 # 2.4:1 widescreen; raster = 1.4 px per unit
PW, PH = round(VW * S), round(VH * S)
HZ, FRONT, AMP = 255, 405, 200             # horizon (oldest month's waterline), newest waterline, busiest-day height
SPAN = 1060                                # width of day 1 .. day 31
def baseline(k): return HZ + (FRONT - HZ) * (k / (K - 1)) ** 1.6
_px = 70 + PI / 30 * SPAN                  # centre the busiest day when we can
X0 = min(max(70 + (600 - _px), 40), 1160 - SPAN)
def day_x(i): return X0 + i / 30 * SPAN
PEAK_X = day_x(PI)

def spline(vs, p):
    n = len(vs)
    if n == 1: return float(vs[0])
    p = max(0., min(n - 1., p)); i = min(int(p), n - 2); t = p - i
    p0, p1, p2, p3 = vs[max(i - 1, 0)], vs[i], vs[i + 1], vs[min(i + 2, n - 1)]
    return max(0., .5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))

def ridge_top(k, x):
    """Crest of month k at x: exact at every day, one shared linear scale. Ends slope into the water over half
    a day instead of stopping in a cliff (there is no data outside day 1 .. last day, so nothing is invented)."""
    b, vs = baseline(k), VALUES[k]; x1 = day_x(len(vs) - 1); half = .5 * SPAN / 30
    if x < X0: e, f = X0, max(0., 1 - (X0 - x) / half)
    elif x > x1: e, f = x1, max(0., 1 - (x - x1) / half)
    else: return b - AMP * spline(vs, (x - X0) / SPAN * 30) / VMAX
    return b - (b - ridge_top(k, e)) * f * f

PEAK_Y = ridge_top(PK, PEAK_X)
SUN = (PEAK_X, HZ - 40, 92)                # setting sun, half under the horizon, behind the summit
CLOUD = (962, 122)
LOBES = [(dx * 3.7, dy * 3.7, r * 3.7) for dx, dy, r in
         [(-24, 4, 8.5), (-10, -6, 12.5), (8, -9, 14), (25, -1, 10.5), (-32, 9, 6.5), (-17, 8, 9), (0, 9, 10.5), (17, 8, 9.5), (33, 9, 6.5)]]
CLOUD_BOTTOM = CLOUD[1] + 14 * 3.7
DUCKS = [(300, 452, 1.35), (352, 459, 1.0), (392, 456, 1.0), (430, 461, 1.0)]   # mother leads three, toward the sun's path

# ------------------------------------------------------------------ palette: two inks on paper
PAPER, WARM, SUNP, CLOUDP = (243, 238, 226), (247, 230, 205), (251, 244, 228), (249, 247, 241)
INK, WATER, GOLD = (25, 47, 88), (24, 66, 104), (196, 136, 46)
DUCK, DUCK_INK, BEAK = (247, 210, 84), (184, 126, 30), (222, 132, 58)

def clamp(v, a=0., b=1.): return a if v < a else b if v > b else v
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def line(phase, width, aa):
    """Ink coverage of a line pattern with lines at integer phase (width and aa in period units)."""
    d = abs(phase - math.floor(phase + .5))
    return clamp((width * .5 - d) / aa + .5)
def q(c): return round(c * 12) / 12        # quantised coverage keeps the PNG palette small

CREST = [[ridge_top(k, (px + .5) / S) for px in range(PW)] for k in range(K)]
BASE = [baseline(k) for k in range(K)]

def duck_at(x, y):
    for dx, dy, s in DUCKS:
        bx, by = (x - dx) / s, (y - dy) / s
        if math.hypot(bx - 10, by + 10.5) <= 1.25: return 'eye', bx, by
        if ((bx - 15.5) / 3.9) ** 2 + ((by + 8) / 1.9) ** 2 <= 1: return 'beak', bx, by
        body = ((bx / 13) ** 2 + (by / 6.5) ** 2 <= 1 and by > -4.5) or (bx < -9 and -6 < by < 1 and by > -1.6 * (bx + 16))
        if body or math.hypot(bx - 8, by + 9) <= 5.6: return 'body', bx, by
    return None

def shade(px, py):
    x, y = (px + .5) / S, (py + .5) / S; aa = 1 / S
    d = duck_at(x, y)
    if d:
        part, bx, by = d
        if part == 'eye': return INK
        if part == 'beak': return BEAK
        if math.hypot(bx - 6.5, by + 11.5) < 1.6: return (255, 250, 232)            # glint on the head
        return mix(DUCK, DUCK_INK, q(line((y + .5 * math.sin(x / 2.6)) / 1.5, clamp((by + 3) / 9) * .6, aa / 1.5)))
    # mountains: the nearest ridge that covers this pixel
    for k in range(K - 1, -1, -1):
        cy = CREST[k][px]
        if cy <= y < BASE[k]:
            depth = k / (K - 1)
            sl = (CREST[k][min(px + 2, PW - 1)] - CREST[k][max(px - 2, 0)]) / (4 / S)
            toward = 1 if x < SUN[0] else -1                                           # sunward side is lit
            t = (.1 + .52 * depth ** 1.3) * (1 - .35 * math.tanh(sl * toward * 1.4))
            t *= .45 + .55 * clamp((BASE[k] - y) / 34)                                 # mist at the waterline
            sp = 1.7 + 1.2 * depth
            rim = math.exp(-abs(x - SUN[0]) / 230) * (.35 + .65 * depth)
            if y - cy < 1.7: return mix(PAPER, GOLD, q(.25 + .7 * rim)) if rim > .12 else mix(PAPER, INK, q(.25 * depth))
            c = line((y - cy) / sp, clamp(t) * .95, aa / sp)
            if t > .5: c = max(c, line((x * .7 + y) / 3, (t - .5) * 1.5, aa / 3))     # cross-hatch the deepest shade
            return mix(PAPER, INK, q(c))
    # lake
    if y >= HZ:
        f = (y - HZ) / (VH - HZ); t = .05 + .1 * f; ink = WATER
        for k in range(K - 1, -1, -1):                                                 # broken mirror of the ridges
            h = (BASE[k] - CREST[k][px]) * .5
            if h > .5 and BASE[k] <= y < BASE[k] + h:
                if (int(y * 1.3) + int(x / 9 + k * 3)) % 4: t += .32 * (1 - (y - BASE[k]) / h) * (.4 + .6 * k / (K - 1))
                break
        gx = abs(x - SUN[0]); gw = 14 + (y - HZ) * .3
        if gx < gw and ((int(y * .8) * 5 + int(x / 7)) % 4) < 2:                       # the sun's path on the water
            t, ink = .55 * (1 - gx / gw) + .1, GOLD
        for dx, dy, s in DUCKS:                                                        # wakes
            u, v = (x - dx) / s, (y - dy) / s
            if -36 < u < -8 and abs(abs(v - 2) - (-u - 8) * .16) < .7: t = max(t, .45)
        n = 96 * f ** .72
        wob = .1 * math.sin(x / 9.3 + y * .5) + .07 * math.sin(x / 23.1 - y * .2)
        return mix(PAPER, ink, q(line(n + wob, clamp(t) * .9, aa * 96 * .72 * max(f, .02) ** -.28 / (VH - HZ))))
    # cloud: engraved billows, sun-warmed on the left, small happy face
    if y <= CLOUD_BOTTOM:
        best = -1.
        for i, (dx, dy, r) in enumerate(LOBES):
            v = 1 - math.hypot(x - CLOUD[0] - dx, y - CLOUD[1] - dy) / r
            if v > best: best, lob = v, (dx, dy, r)
        if best > 0:
            dx, dy, r = lob; cx, cy = CLOUD
            if best * r < .9 or CLOUD_BOTTOM - y < .9: return mix(PAPER, INK, .72)
            ex, ey = x - cx, y - cy - 12
            for sx in (-21, 21):
                if ((ex - sx) / 3.3) ** 2 + (ey / 4.6) ** 2 <= 1: return INK
            if abs(math.hypot(ex, ey + 1) - 10) < 1.4 and ey > 5.5: return INK
            for sx in (-36, 36):
                if ((ex - sx) / 7.5) ** 2 + ((ey - 8) / 3) ** 2 <= 1: return mix(CLOUDP, (238, 180, 150), .55)
            nx, ny = (x - cx - dx) / r, (y - cy - dy) / r
            lit = -nx * .55 - ny * .7 + math.sqrt(max(0, 1 - nx * nx - ny * ny)) * .45
            t = clamp(.2 - .2 * lit + .26 * clamp((y - cy - 10) / 34))
            ph = (y + 2.4 * math.sin(x / 31 + y / 19) + 1.2 * math.sin(x / 11)) / 2.4
            c = line(ph, t, aa / 2.4)
            warm = clamp(-nx) * math.exp(-max(0, y - cy) / 60)
            return mix(CLOUDP, mix(INK, GOLD, q(warm * .8)), q(c))
    # sky and sun
    ds = math.hypot(x - SUN[0], y - SUN[1]); r = SUN[2]
    if ds < r: return mix(SUNP, GOLD, q(line(ds / 3, .16 + .2 * (ds / r) ** 2, aa / 3) * .85))
    glow = round(math.exp(-(ds - r) / 120) * 8) / 8
    paper, ink = mix(PAPER, WARM, glow * .85), mix(INK, GOLD, glow * .9)
    t = (.12 - .07 * clamp(y / HZ)) * (1 - .75 * glow) + .04 * clamp((abs(x - 600) - 420) / 180)
    w1 = (y + 2 * math.sin((x + .4 * y) / 5.4)) / 2.7
    w2 = (y + 2 * math.sin((-x + .4 * y) / 5.4 + 1.7)) / 2.7
    c = 1 - (1 - line(w1, t, aa / 2.7)) * (1 - line(w2, t, aa / 2.7))
    if ds < r + 80: c = max(c * .5, line(ds / 3.6, .3 * (1 - (ds - r) / 80), aa / 3.6))        # halo rings
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
    if pal is not None:
        plte = b''.join(bytes(c) for c in sorted(pal, key=pal.get))
        return head + chunk(b'IHDR', PW.to_bytes(4, 'big') + PH.to_bytes(4, 'big') + b'\x08\x03\x00\x00\x00') + \
            chunk(b'PLTE', plte) + chunk(b'IDAT', zlib.compress(b''.join(idx), 9)) + chunk(b'IEND', b'')
    raw = b''.join(b'\x00' + b''.join(bytes(c) for c in row) for row in rows)
    return head + chunk(b'IHDR', PW.to_bytes(4, 'big') + PH.to_bytes(4, 'big') + b'\x08\x02\x00\x00\x00') + \
        chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

def font(name, family):
    data = base64.b64encode(open(os.path.join(ROOT, 'fonts', name), 'rb').read()).decode()
    return f'@font-face{{font-family:"{family}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'

def main():
    rows = [[tuple(int(v + .5) for v in shade(px, py)) for px in range(PW)] for py in range(PH)]
    art = png(rows)
    m, d = int(PEAK_DATE[5:7]), int(PEAK_DATE[8:])
    label = f'BUSIEST DAY · {d} {MON[m].upper()} {PEAK_DATE[:4]} · {VMAX}'
    navy, paper = '#192f58', '#f3eee2'
    halo = f'stroke="{paper}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
    ty = SUN[1] - SUN[2] - 12
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" role="img">'
           f'<title>Jake Parker: twelve months of GitHub contributions, engraved as mountains rising from a lake</title>'
           f'<style>{font("Geist-Medium.woff2", "Geist")}{font("GeistMono-Regular.woff2", "Geist Mono")}</style>'
           f'<defs><clipPath id="card"><rect width="{VW}" height="{VH}" rx="16"/></clipPath></defs>'
           f'<g clip-path="url(#card)"><image width="{VW}" height="{VH}" href="data:image/png;base64,{base64.b64encode(art).decode()}"/></g>'
           f'<text x="64" y="86" font-family="Geist" font-size="34" letter-spacing="-.4" fill="{navy}" data-bg="{paper}" {halo}>Jake Parker</text>'
           f'<line x1="{PEAK_X:.1f}" y1="{ty + 8:.1f}" x2="{PEAK_X:.1f}" y2="{PEAK_Y - 4:.1f}" stroke="{navy}" stroke-width="1" stroke-opacity=".75"/>'
           f'<circle cx="{PEAK_X:.1f}" cy="{PEAK_Y - 2:.1f}" r="2.4" fill="{navy}"/>'
           f'<text x="{PEAK_X:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="Geist Mono" font-size="16.5" letter-spacing="1.6" fill="{navy}" fill-opacity=".92" data-bg="{paper}" {halo}>{label}</text>'
           f'</svg>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'art.svg'), 'w').write(svg)
    meta = {'amp': AMP, 'vmax': VMAX, 'total': TOTAL, 'peak': [PEAK_DATE, VMAX], 'last': LAST,
            'ridges': [{'month': f'{yy}-{mm:02d}', 'baseline': baseline(k),
                        'days': [[DATES[k][i], VALUES[k][i], ridge_top(k, day_x(i))] for i in range(len(VALUES[k]))]}
                       for k, (yy, mm) in enumerate(MONTHS)]}
    json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))
    readme(m, d)
    print(f'art.svg {len(svg) // 1024} KB (png {len(art) // 1024} KB), busiest day {PEAK_DATE} = {VMAX}, total {TOTAL:,}')

def readme(m, d):
    """Fill README.template.md with the same numbers the art shows."""
    tpl = os.path.join(ROOT, 'README.template.md')
    if not os.path.exists(tpl): return
    first = DATES[0][0]; last31 = sorted(DAYS.items())[-31:]
    vals = {'TOTAL': f'{TOTAL:,}', 'FIRST': f'{MON[int(first[5:7])]} {first[:4]}', 'LAST': f'{MON[int(LAST[5:7])]} {int(LAST[8:])}, {LAST[:4]}',
            'PEAK_VALUE': str(VMAX), 'PEAK_DATE': f'{MON[m]} {d}, {PEAK_DATE[:4]}',
            'LAST31': f'{sum(v for _, v in last31):,}', 'QUIET': str(sum(1 for vs in VALUES for v in vs if v == 0))}
    text = open(tpl).read()
    for k, v in vals.items(): text = text.replace('{{' + k + '}}', v)
    open(os.path.join(ROOT, 'README.md'), 'w').write(text)

if __name__ == '__main__':
    main()
