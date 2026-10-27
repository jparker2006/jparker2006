"""Shared engraving toolkit for every piece of the world (standard library only).

Everything is drawn as an engraving: ink lines whose width follows the tone underneath. Pieces never pick colours
directly. They describe *tone* (0 = in full light, 1 = deep shade) and a line *phase* (which way the lines run), and
`engrave()` turns that into ink on paper for the current moment of the day, including night, where the print flips
to pale lines on navy (a white-line engraving).

Coordinates: art units on a 1200 x 500 canvas, x to the right, y down. Rasters are drawn at S pixels per unit.
"""
import base64, html, math, os, subprocess, tempfile, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VW, VH, S = 1200, 500, 1.4

# ------------------------------------------------------------------ light: one preset per moment of the day
# paper = bare paper (light); ink = the engraving ink; gold = the one warm accent (sun, its light, ducks, burners);
# sun = unit vector pointing *toward* the light source (screen space, y down); night = white-line print.
LIGHTS = {
    'dawn':    dict(paper=(250, 243, 236), ink=(24, 72, 138), hair=(70, 110, 172), gold=(204, 138, 52), sun=(-.96, -.28), night=False),
    'morning': dict(paper=(249, 246, 240), ink=(24, 72, 138), hair=(70, 110, 172), gold=(198, 136, 48), sun=(-.62, -.78), night=False),
    'midday':  dict(paper=(248, 246, 239), ink=(24, 72, 138), hair=(70, 110, 172), gold=(196, 136, 46), sun=(.22, -.97), night=False),
    'golden':  dict(paper=(250, 241, 224), ink=(24, 72, 138), hair=(70, 110, 172), gold=(210, 140, 44), sun=(.95, -.3), night=False),
    'dusk':    dict(paper=(240, 232, 236), ink=(24, 62, 124), hair=(84, 104, 160), gold=(214, 132, 76), sun=(.98, .18), night=False),
    'night':   dict(paper=(14, 27, 58), ink=(206, 218, 240), hair=(120, 146, 196), gold=(234, 206, 140), sun=(.5, -.86), night=True),
}

# ------------------------------------------------------------------ accent pigments (shared by the flowers and the aircraft)
# Decoration only, never data. Neighbouring hues also differ in lightness, so they stay distinct for colourblind eyes.
PIGMENTS = dict(vermilion=(228, 87, 46), marigold=(244, 178, 38), leaf=(76, 156, 84), sky=(78, 150, 222),
                plum=(150, 92, 170), rose=(238, 132, 160), coral=(244, 128, 96), cream=(252, 246, 228))
def pigment(name, light, amount=1.):
    """A pigment as it reads in this moment's light: full by day, quieter and cooler at night."""
    c = PIGMENTS[name]
    if light['night']: c = mix(c, light['paper'], .45)
    return mix(light['paper'], c, amount)

# ------------------------------------------------------------------ maths
def clamp(v, a=0., b=1.): return a if v < a else b if v > b else v
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def q(c): return round(c * 12) / 12        # quantised coverage keeps the PNG palette small
BAYER = [[(v + .5) / 16 for v in row] for row in ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))]
def dither(a, x, y, n=6):
    """Ordered-dither a 0..1 amount into n steps (smooth gradients without blowing up the palette)."""
    return clamp(math.floor(clamp(a) * n + BAYER[int(y * S) % 4][int(x * S) % 4]) / n)
def rnd(*a):
    """Deterministic pseudo-random 0..1 from integers (the art must render identically every time)."""
    h = 2166136261
    for v in a: h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    return h / 4294967295

def line(phase, width, aa):
    """Ink coverage of a line pattern: lines at integer phase, `width` and anti-alias `aa` in period units."""
    d = abs(phase - math.floor(phase + .5))
    return clamp((width * .5 - d) / aa + .5)

# ------------------------------------------------------------------ signed distances (negative inside), in units
def ell(x, y, cx, cy, a, b):
    """Approximate signed distance to an ellipse."""
    u, v = (x - cx) / a, (y - cy) / b
    k0 = math.hypot(u, v); k1 = math.hypot(u / a, v / b)
    return k0 * (k0 - 1) / k1 if k1 > 1e-9 else -min(a, b)
def cap(x, y, x1, y1, x2, y2, r):
    """Signed distance to a capsule (a stroke from x1,y1 to x2,y2 with radius r)."""
    dx, dy = x2 - x1, y2 - y1
    h = clamp(((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1e-9))
    return math.hypot(x - x1 - dx * h, y - y1 - dy * h) - r
def box(x, y, cx, cy, hw, hh, r=0.):
    """Signed distance to a rounded rectangle."""
    qx, qy = abs(x - cx) - hw + r, abs(y - cy) - hh + r
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r
def poly(x, y, pts):
    """Signed distance to a closed polygon [(x, y), ...]."""
    d, s, n = float('inf'), 1, len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i - 1]
        ex, ey, wx, wy = bx - ax, by - ay, x - ax, y - ay
        h = clamp((wx * ex + wy * ey) / (ex * ex + ey * ey or 1e-9))
        d = min(d, math.hypot(wx - ex * h, wy - ey * h))
        c1, c2, c3 = y >= ay, y < by, ex * wy > ey * wx
        if (c1 and c2 and c3) or (not c1 and not c2 and not c3): s = -s
    return s * d
def smin(a, b, k):
    """Smooth union of two distances (k = blend radius)."""
    h = clamp(.5 + .5 * (b - a) / k); return b + (a - b) * h - k * h * (1 - h)

def form(nx, ny, light):
    """Tone of a rounded form at normalised position (nx, ny in -1..1 across the form): 0 lit .. 1 shade,
    lit from light['sun']."""
    nz = math.sqrt(max(0., 1 - nx * nx - ny * ny))
    lx, ly = light['sun']; lz = .55
    k = math.sqrt(lx * lx + ly * ly + lz * lz)
    return clamp(.5 - .5 * (nx * lx + ny * ly + nz * lz) / k * 1.6)

# ------------------------------------------------------------------ ink on paper
def engrave(tone, phase, light, sp=2.4):
    """Ink on paper for a surface: tone 0..1 (light..shade), lines running along `phase` (units), period sp.
    At night this flips to a white-line print: pale lines where the light falls, bare navy in shadow."""
    t = clamp(tone)
    if light['night']: t = (1 - t) * .72
    return mix(light['paper'], light['ink'], q(line(phase / sp, t, 1 / S / sp)))
def outline(light, a=.9):
    """Colour of a fine outline (dark ink by day, pale ink by night)."""
    return mix(light['paper'], light['ink'], a)
def warm(tone, phase, light, sp=2.2, base=None):
    """The gold accent, engraved the same way (sun-lit rims, burners, ducks). base = the gold's own paper colour."""
    paper = base or mix(light['paper'], light['gold'], .35)
    return mix(paper, light['gold'], q(line(phase / sp, clamp(tone) * .9, 1 / S / sp)))

# ------------------------------------------------------------------ rasters
def _chunk(tag, data): return len(data).to_bytes(4, 'big') + tag + data + (zlib.crc32(tag + data) & 0xffffffff).to_bytes(4, 'big')
def png(rows):
    """rows of (r, g, b) or (r, g, b, a) tuples -> PNG bytes (indexed colour when it fits in 256, else true colour)."""
    h, w = len(rows), len(rows[0]); pal, idx = {}, []
    for row in rows:
        out = bytearray(b'\x00')
        for c in row:
            if c not in pal:
                if len(pal) == 256: pal = None; break
                pal[c] = len(pal)
            out.append(pal[c])
        if pal is None: break
        idx.append(bytes(out))
    head, size = b'\x89PNG\r\n\x1a\n', w.to_bytes(4, 'big') + h.to_bytes(4, 'big')
    if pal is not None:
        cols = sorted(pal, key=pal.get)
        trns = _chunk(b'tRNS', bytes(c[3] for c in cols)) if any(len(c) == 4 for c in cols) else b''
        return (head + _chunk(b'IHDR', size + b'\x08\x03\x00\x00\x00') + _chunk(b'PLTE', b''.join(bytes(c[:3]) for c in cols)) + trns
                + _chunk(b'IDAT', zlib.compress(b''.join(idx), 9)) + _chunk(b'IEND', b''))
    alpha = len(rows[0][0]) == 4
    raw = b''.join(b'\x00' + b''.join(bytes(c) for c in row) for row in rows)
    return head + _chunk(b'IHDR', size + (b'\x08\x06' if alpha else b'\x08\x02') + b'\x00\x00\x00') + _chunk(b'IDAT', zlib.compress(raw, 9)) + _chunk(b'IEND', b'')

def raster(fn, x0, y0, x1, y1, aa=True):
    """Rasterise fn(x, y) -> colour | None over a box (art units) into a transparent PNG, 2x2 supersampled at the
    edges. aa=True samples every pixel 5 times (safe for hairline detail); aa='edges' samples pixel centres first
    and supersamples only where coverage changes (about 3x faster for solid masses such as land).
    Returns (svg <image> markup, png bytes)."""
    w, h = max(1, round((x1 - x0) * S)), max(1, round((y1 - y0) * S)); rows = []
    if aa == 'edges':
        grid = [[fn(x0 + (px + .5) / S, y0 + (py + .5) / S) for px in range(w)] for py in range(h)]
        for py in range(h):
            row = []
            for px in range(w):
                c = grid[py][px]
                nb = [grid[py + dy][px + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= px + dx < w and 0 <= py + dy < h]
                if c is not None and all(v is not None for v in nb): row.append(tuple(int(v + .5) for v in c) + (255,)); continue
                if c is None and all(v is None for v in nb): row.append((0, 0, 0, 0)); continue
                hits = [fn(x0 + (px + .25 + .5 * i) / S, y0 + (py + .25 + .5 * j) / S) for i in (0, 1) for j in (0, 1)]
                n = sum(1 for v in hits if v)
                if not n: row.append((0, 0, 0, 0)); continue
                c = c or next(v for v in hits if v)
                row.append(tuple(int(v + .5) for v in c) + (round(n / 4 * 255),))
            rows.append(row)
        data = png(rows)
        return (f'<image x="{x0:.2f}" y="{y0:.2f}" width="{x1 - x0:.2f}" height="{y1 - y0:.2f}" '
                f'href="data:image/png;base64,{base64.b64encode(data).decode()}"/>', data)
    for py in range(h):
        row = []
        for px in range(w):
            cx, cy = x0 + (px + .5) / S, y0 + (py + .5) / S
            c = fn(cx, cy)
            if aa:
                hits = [fn(x0 + (px + .25 + .5 * i) / S, y0 + (py + .25 + .5 * j) / S) for i in (0, 1) for j in (0, 1)]
                n = sum(1 for v in hits if v)
                if not n: row.append((0, 0, 0, 0)); continue
                c = c or next(v for v in hits if v)
                row.append(tuple(int(v + .5) for v in c) + (round(n / 4 * 255),))
            else:
                row.append(tuple(int(v + .5) for v in c) + (255,) if c else (0, 0, 0, 0))
        rows.append(row)
    data = png(rows)
    return (f'<image x="{x0:.2f}" y="{y0:.2f}" width="{x1 - x0:.2f}" height="{y1 - y0:.2f}" '
            f'href="data:image/png;base64,{base64.b64encode(data).decode()}"/>', data)

def font(name, family):
    data = base64.b64encode(open(os.path.join(ROOT, 'fonts', name), 'rb').read()).decode()
    return f'@font-face{{font-family:"{family}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'
FONTS = None
def fonts():
    global FONTS
    if FONTS is None: FONTS = font('Geist-Medium.woff2', 'Geist') + font('GeistMono-Regular.woff2', 'Geist Mono')
    return FONTS

# ------------------------------------------------------------------ previews and contact sheets
def shoot(page_html, width, height, out, scale=2):
    """Screenshot an HTML page with headless Chromium (one at a time: the sandbox has limited memory)."""
    with tempfile.TemporaryDirectory(prefix='kit-shot.') as tmp:
        p = os.path.join(tmp, 'p.html'); open(p, 'w').write(page_html)
        subprocess.run(['flock', '/tmp/profile-art-render.lock', 'chromium', '--headless=new', '--no-sandbox',
                        f'--user-data-dir={tmp}/chrome', '--hide-scrollbars', f'--force-device-scale-factor={scale}',
                        f'--window-size={width},{height}', f'--screenshot={out}', f'file://{p}'], check=True, capture_output=True)

def sheet(items, out, cols=3, cell=520, title=None):
    """Contact sheet: items = [(label, note, svg_markup_or_png_path)] -> out (PNG)."""
    def media(m):
        if m.endswith('.png') or m.endswith('.jpg') or m.endswith('.svg'): return f'<img src="file://{os.path.abspath(m)}" style="width:{cell}px">'
        uri = 'data:image/svg+xml;base64,' + base64.b64encode(m.encode()).decode()      # isolated, like GitHub's <img>
        return f'<img src="{uri}" style="width:{cell}px">'
    cells = ''.join(f'<div><b>{html.escape(a)}</b><span>{html.escape(b)}</span>{media(m)}</div>' for a, b, m in items)
    css = ('body{margin:0;background:#f6f8fa;font:15px ui-monospace,Menlo,"DejaVu Sans Mono",monospace;color:#13233f}'
           f'.g{{display:grid;grid-template-columns:repeat({cols},{cell}px);gap:18px 16px;padding:18px}}'
           'b{display:block;font-size:15px;letter-spacing:.5px}span{display:block;color:#57606a;font-size:12.5px;margin:2px 0 6px}'
           'img,div>div{border-radius:8px;overflow:hidden;display:block}h1{font-size:18px;margin:18px 18px 0}')
    top = f'<h1>{html.escape(title)}</h1>' if title else ''
    page = f'<html><head><meta charset="utf-8"><style>{css}</style></head><body>{top}<div class="g">{cells}</div></body></html>'
    width = cols * (cell + 16) + 20
    shoot(page, width, measure(page, width), out, scale=1.5)

def measure(page_html, width):
    """Height (CSS px) the page needs at this width."""
    probe = page_html.replace('</body>', '<script>onload=()=>{document.title="H="+document.documentElement.scrollHeight}</script></body>')
    with tempfile.TemporaryDirectory(prefix='kit-measure.') as tmp:
        p = os.path.join(tmp, 'p.html'); open(p, 'w').write(probe)
        r = subprocess.run(['flock', '/tmp/profile-art-render.lock', 'chromium', '--headless=new', '--no-sandbox', f'--user-data-dir={tmp}/chrome',
                            f'--window-size={width},800', '--virtual-time-budget=3000', '--dump-dom', f'file://{p}'], capture_output=True, text=True)
    import re
    m = re.search(r'<title>H=(\d+)</title>', r.stdout)
    return int(m.group(1)) if m else 1200
