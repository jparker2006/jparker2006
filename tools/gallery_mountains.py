#!/usr/bin/env python3
"""Gallery for the mountains piece (years). Fake data lives only here.

    python3 tools/gallery_mountains.py band midday [--future]      # one quick band PNG
    python3 tools/gallery_mountains.py check                       # honesty: exact summits, nothing above them
    python3 tools/gallery_mountains.py sheet                       # the contact sheet (renders the world too)
"""
import math, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'generator'))
import kit, data, mountains, world
from kit import clamp, line, mix, S

OUT = os.path.join(ROOT, 'previews', 'pieces', 'mountains')
BASE = mountains.BAND['base']

def real_years():
    days, last = data.load(); return data.years(days, last)

def future_years():
    return real_years() + [(2027, 3000)]                     # test only: a fake second big year

def water(years, light, kind, sx, x0, x1, y1):
    """A stand-in for world.py's water with mountains.reflect() wired in, to show the richer mirror."""
    ink = light['ink'] if not light['night'] else light['hair']
    def fn(x, y):
        f = (y - BASE) / (500 - BASE); n = 80 * f ** .72; L = int(math.floor(n + .5))
        t = (.06 + .05 * f) if light['night'] else (.06 + .17 * f ** 1.2)
        col = ink
        r = mountains.reflect(x, y, years, light)
        if r:
            tone, k = r
            if k == 'foam': t = 0
            elif ((int(y * 1.3) * 2654435761 + int(x / 13 + 3 * math.sin(y * .7)) * 40503) >> 7) % 7 > 1:
                if k == 'rim': col, t = light['gold'], max(t, .45)
                else: t += tone * .5 * (1 - f * .6)
        if kind in ('sun', 'glow') and abs(x - sx) < 12 + (y - BASE) * .3 and ((L * 2654435761 + int((x + L * 5) / 9) * 40503) >> 6) % 5 > 1:
            t, col = .5 * (1 - abs(x - sx) / (12 + (y - BASE) * .3)) + .14, light['gold']
        wob = .1 * math.sin(x / 9.3 + y * .5) + .07 * math.sin(x / 23.1 - y * .2)
        return col, line(n + wob, clamp(t) * .9, 1 / S * 80 * .72 * max(f, .02) ** -.28 / (500 - BASE))
    return world.alpha_layer(fn, x0, BASE, x1, y1)[0]

def band(years, moment, x0=0, y0=118, x1=1200, y1=352, captions=True, reflect=True):
    """SVG of the far shore: tint plate, sun glow, the mountains and (optionally) their reflection."""
    light = dict(kit.LIGHTS[moment]); tint = world.TINT[moment]; hexc = world.hexc
    summits = mountains.summits(years); kind, sx, sy, sr = world.sun_spec(moment, summits)
    t0 = time.time()
    img, png = kit.raster(lambda x, y: mountains.shade(x, y, years, light), x0, max(y0, min(y for _, y in summits) - 6), x1, BASE + 1)
    dt = time.time() - t0
    wimg = water(years, light, kind, sx, x0, x1, y1) if reflect and y1 > BASE else ''
    P = 'b' + moment[:2]
    sun = ''
    if kind in ('sun', 'glow', 'moon'):
        col = hexc((253, 250, 242)) if kind != 'moon' else '#ece8d6'
        sun = (f'<circle cx="{sx}" cy="{sy}" r="{sr * 4.2:.0f}" fill="url(#{P}g)"/>' +
               (f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="{col}" stroke="{hexc(light["gold"])}" stroke-width="1.5"/>' if kind != 'glow' else ''))
    caps = ''
    if captions:
        caps = ''.join(f'<text x="{x:.1f}" y="{BASE + 19}" text-anchor="middle" font-family="Geist Mono" letter-spacing="1.6" '
                       f'font-size="16.5" fill="{world.TEXT_INK[moment]}">{yr}</text>' for (yr, _), (x, _) in zip(years, summits))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" width="{x1 - x0}" height="{y1 - y0}">'
           f'<style>{kit.fonts()}</style><defs>'
           f'<linearGradient id="{P}s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hexc(tint[0])}"/><stop offset="1" stop-color="{hexc(tint[1])}"/></linearGradient>'
           f'<linearGradient id="{P}w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hexc(tint[2])}"/><stop offset="1" stop-color="{hexc(tint[3])}"/></linearGradient>'
           f'<radialGradient id="{P}g" cx="{sx}" cy="{sy}" r="{sr * 4.2:.0f}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{hexc(tint[4])}" stop-opacity=".95"/>'
           f'<stop offset=".45" stop-color="{hexc(tint[4])}" stop-opacity=".35"/><stop offset="1" stop-color="{hexc(tint[4])}" stop-opacity="0"/></radialGradient></defs>'
           f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{BASE}" fill="url(#{P}s)"/><rect x="{x0}" y="{BASE}" width="{x1 - x0}" height="200" fill="url(#{P}w)"/>'
           f'{sun}{wimg}<rect x="{x0}" y="{BASE - 1.1}" width="{x1 - x0}" height="1" fill="{hexc(light["ink"])}"/>{img}{caps}</svg>')
    return svg, len(png), dt

def to_png(svg, out, width):
    vb = [float(v) for v in svg.split('viewBox="')[1].split('"')[0].split()]
    h = math.ceil(width * vb[3] / vb[2])
    page = f'<html><body style="margin:0"><img src="data:image/svg+xml;base64,{__import__("base64").b64encode(svg.encode()).decode()}" style="display:block;width:{width}px"></body></html>'
    kit.shoot(page, width, h, out, scale=1)

def check(years):
    """Honesty: every summit exact, and no land in a year's slot above that year's summit."""
    S = mountains.summits(years); mx = max(t for _, t in years) or 1; n, w = mountains._slot(years); bad = []
    for i, ((yr, t), (sx, sy)) in enumerate(zip(years, S)):
        want = BASE - mountains.BAND['amp'] * t / mx
        if abs(sy - want) > 1e-9: bad.append(f'{yr}: summit {sy} != {want}')
        if abs(mountains.crest(sx, years) - sy) > 1e-6: bad.append(f'{yr}: crest at summit {mountains.crest(sx, years)} != {sy}')
        a = mountains.BAND['x0'] + i * w
        hi = min(mountains.crest(a + k / 16, years) for k in range(int(w * 16)))
        if hi < sy - 1e-6: bad.append(f'{yr}: land at y={hi:.3f} rises above its summit y={sy:.3f}')
        # the painted pixels too: nothing opaque above the summit inside the slot
        light = kit.LIGHTS['midday']
        for k in range(int(w * 4)):
            x = a + (k + .5) / 4
            if mountains.shade(x, sy - .3, years, light) is not None: bad.append(f'{yr}: pixel above summit at x={x:.2f}'); break
    return bad

def main():
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'sheet'
    if cmd == 'check':
        for name, ys in (('real', real_years()), ('future', future_years()), ('one year', [(2026, 50)]),
                         ('flat', [(2024, 3), (2025, 3), (2026, 3)]), ('zero', [(2025, 0), (2026, 12)])):
            bad = check(ys); print(f'{name:9}', 'OK' if not bad else bad)
        return
    if cmd == 'band':
        moment = sys.argv[2] if len(sys.argv) > 2 else 'midday'
        ys = future_years() if '--future' in sys.argv else real_years()
        crop = [a for a in sys.argv[3:] if a.startswith('--crop=')]
        if crop:
            x0, y0, x1, y1 = (float(v) for v in crop[0][7:].split(','))
            svg, kb, dt = band(ys, moment, x0, y0, x1, y1)
            w = int((x1 - x0) * .69 * 2)
        else:
            svg, kb, dt = band(ys, moment); w = 830
        if '--w2' in sys.argv: w *= 2
        tag = moment + ('-future' if '--future' in sys.argv else '') + ('-crop' if crop else '')
        out = os.path.join(OUT, f'band-{tag}.png'); open(out[:-4] + '.svg', 'w').write(svg)
        to_png(svg, out, w); print(f'{out}  raster {kb // 1024} KB  {dt:.1f}s')
        return
    if cmd == 'sheet':
        ys, fs = real_years(), future_years(); items = []
        for m in ('midday', 'golden', 'night'):
            svg, kb, dt = band(ys, m); items.append((f'{m.upper()} · the band', f'real size (830 px) · {kb // 1024} KB raster · {dt:.1f}s', svg))
        svg, kb, dt = band(ys, 'midday', 600, 110, 1200, 345); items.append(('2x ZOOM · 2024 to 2026', 'midday, reflection via reflect()', svg))
        svg, kb, dt = band(ys, 'midday', 0, 230, 600, 330); items.append(('2x ZOOM · 2021 to 2023', 'midday: wooded hills and an islet', svg))
        svg, kb, dt = band(ys, 'golden', 600, 110, 1200, 345); items.append(('2x ZOOM · golden hour', 'gold rim on the skyline, backlit by the sun', svg))
        svg, kb, dt = band(ys, 'night', 600, 110, 1200, 345); items.append(('2x ZOOM · night', 'white-line print, moonlit snow', svg))
        for m in ('midday', 'golden'):
            svg, kb, dt = band(fs, m); items.append((f'FUTURE (fake 2027 = 3,000) · {m}', 'test data, gallery only', svg))
        wd = os.path.join(OUT, 'world')
        subprocess.run([sys.executable, os.path.join(ROOT, 'generator', 'world.py'), '--all', '--out', wd], check=True)
        for m in ('midday', 'golden', 'night'):
            items.append((f'WORLD · {m}', 'generator/world.py, real data', os.path.join(wd, f'{m}.svg')))
        kit.sheet(items, os.path.join(OUT, 'sheet.png'), cols=2, cell=830, title='Mountains (years): one great 2026 peak, low wooded years, a reef for 2024')
        print(os.path.join(OUT, 'sheet.png'))

if __name__ == '__main__':
    main()
