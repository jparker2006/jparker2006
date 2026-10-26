#!/usr/bin/env python3
"""Fleet gallery: lineups, zooms and the contact sheet for the fleet piece.

    python3 tools/gallery_fleet.py lineup [moment ...]   # quick lineup PNGs -> previews/pieces/fleet/lineup-<moment>.png
    python3 tools/gallery_fleet.py zoom [kind ...]       # 2x (README) zoom PNG -> previews/pieces/fleet/zoom.png
    python3 tools/gallery_fleet.py mass                  # visual mass (ink pixels) per kind: must grow with tier
    python3 tools/gallery_fleet.py sheet                 # the contact sheet (renders the world too)
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'generator'))
import kit, fleet, world, data
from kit import mix

OUT = os.path.join(ROOT, 'previews', 'pieces', 'fleet')
README = 830 / kit.VW                                    # px per unit on the README

def craft(kind, x, y, light):
    """One craft at (x, y) the way world.py composes it: the body raster, then its moving parts on top."""
    w, h = fleet.SIZE[kind]
    img, _ = kit.raster(lambda xx, yy: fleet.shade(kind, xx - x, yy - y, light), x - w / 2 - 1, y - h / 2 - 1, x + w / 2 + 1, y + h / 2 + 1)
    out = [img]
    for p in fleet.parts(kind):
        u0, v0, u1, v1 = p['box']
        pimg, _ = kit.raster(lambda xx, yy, p=p: p['shade'](xx - x, yy - y, light), x + u0, y + v0, x + u1, y + v1)
        out.append(pimg)
    return ''.join(out)

def backdrop(moment, w, h):
    t = world.TINT[moment]
    return (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{world.hexc(t[0])}"/>'
            f'<stop offset="1" stop-color="{world.hexc(t[1])}"/></linearGradient></defs><rect width="{w}" height="{h}" fill="url(#g)"/>')

def lineup_svg(moment, kinds=data.KINDS, gap=10, scale_w=None, captions=True, pad=12):
    """All kinds side by side at true relative size (each slot is at least as wide as its caption)."""
    light = dict(kit.LIGHTS[moment]); H = 64 + (16 if captions else 0)
    slot = {k: max(fleet.SIZE[k][0], 40 if captions else 0) for k in kinds}
    width = sum(slot.values()) + gap * (len(kinds) - 1) + 2 * pad
    W = max(width, scale_w or 0); x = pad + (W - width) / 2; body = []
    ink = world.TEXT_INK[moment]
    for k in kinds:
        w, h = fleet.SIZE[k]; cx = x + slot[k] / 2
        body.append(craft(k, cx, 34, light))
        if captions:
            body.append(f'<text x="{cx:.1f}" y="{H - 9}" text-anchor="middle" font-family="Geist Mono" font-size="5.4" fill="{ink}">'
                        f'{data.NAMES[k]}</text><text x="{cx:.1f}" y="{H - 2.5}" text-anchor="middle" font-family="Geist Mono" '
                        f'font-size="4.4" fill="{ink}" fill-opacity=".75">{w} x {h} · tier {data.KINDS.index(k) + 1}</text>')
        x += slot[k] + gap
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" width="{W:.0f}" height="{H}">'
            f'<style>{kit.fonts()}</style>{backdrop(moment, W, H)}{"".join(body)}</svg>')

def zoom_svg(moment, kinds=('helicopter', 'airliner', 'airship'), gap=14, pad=8):
    light = dict(kit.LIGHTS[moment]); H = max(fleet.SIZE[k][1] for k in kinds) + 2 * pad
    W = sum(fleet.SIZE[k][0] for k in kinds) + gap * (len(kinds) - 1) + 2 * pad; x = pad; body = []
    for k in kinds:
        w, h = fleet.SIZE[k]; body.append(craft(k, x + w / 2, H / 2, light)); x += w + gap
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{backdrop(moment, W, H)}{"".join(body)}</svg>'

def shoot_svg(svg, out, px_per_unit, scale=1):
    import re
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg); W, H = float(m[1]), float(m[2])
    w, h = round(W * px_per_unit), round(H * px_per_unit)
    page = f'<html><body style="margin:0;background:#fff"><img style="display:block;width:{w}px" src="data:image/svg+xml;base64,{__import__("base64").b64encode(svg.encode()).decode()}"></body></html>'
    kit.shoot(page, w, max(h, 200) + 90, out, scale=scale)    # headless windows lose ~90 px to chrome

def mass():
    light = dict(kit.LIGHTS['midday']); res = {}
    for k in data.KINDS:
        w, h = fleet.SIZE[k]; n = 0
        for py in range(int(h * kit.S) + 2):
            for px in range(int(w * kit.S) + 2):
                u, v = -w / 2 + (px + .5) / kit.S, -h / 2 + (py + .5) / kit.S
                if fleet.shade(k, u, v, light) or any(p['shade'](u, v, light) for p in fleet.parts(k)): n += 1
        res[k] = n / kit.S ** 2
    return res

def main():
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'lineup'
    if cmd == 'lineup':
        for m in sys.argv[2:] or ['midday']:
            shoot_svg(lineup_svg(m), os.path.join(OUT, f'lineup-{m}.png'), README * 2, scale=1); print('lineup', m)
    elif cmd == 'zoom':
        kinds = sys.argv[2:] or ('helicopter', 'airliner', 'airship')
        shoot_svg(zoom_svg('midday', kinds), os.path.join(OUT, 'zoom.png'), README * 2, scale=2); print('zoom')
    elif cmd == 'mass':
        prev = 0
        for k, a in mass().items(): print(f'{k:12} {a:7.0f} sq units', '' if a > prev else '  <-- NOT BIGGER'); prev = a
    elif cmd == 'sheet':
        subprocess.run([sys.executable, os.path.join(ROOT, 'generator', 'world.py'), '--all', '--out', os.path.join(OUT, 'world')], check=True)
        width_units = 1240 / README
        items = [('1 · Lineup, midday', 'all nine at true relative size, 2x README scale; captions give the length in units', lineup_svg('midday')),
                 ('1b · Lineup at real README size', '830 px wide canvas: 1 unit = 0.69 px', lineup_svg('midday', scale_w=width_units, captions=False)),
                 ('2 · Lineup, night', 'the white-line flip; gold = cabin lights, nav lights, burner', lineup_svg('night')),
                 ('2b · Lineup, golden hour', 'warm rims on the sun side, gold window glints', lineup_svg('golden')),
                 ('3 · 2x zoom: helicopter, jet airliner, cargo airship', 'midday, README scale x2', zoom_svg('midday')),
                 ('3b · 2x zoom at night', 'white-line print', zoom_svg('night'))]
        for m, note in (('midday', 'real data: Nov prop plane, Dec–Mar parked, Apr drone, May jet, Jun airliner, Jul blimp, Aug balloon, Sep blimp, Oct airship'),
                        ('golden', 'golden hour'), ('night', 'night')):
            items.append((f'4 · World, {m}', note, os.path.join(OUT, 'world', f'{m}.svg')))
        kit.sheet(items, os.path.join(OUT, 'sheet.png'), cols=1, cell=1240, title='The fleet (months): paper plane → cargo airship')
        print('sheet ->', os.path.join(OUT, 'sheet.png'))

if __name__ == '__main__':
    main()
