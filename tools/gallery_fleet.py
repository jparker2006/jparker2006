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
        args = sys.argv[2:]; m = args.pop(0) if args and args[0] in kit.LIGHTS else 'midday'
        kinds = args or ('balloon', 'airliner', 'airship')
        shoot_svg(zoom_svg(m, kinds), os.path.join(OUT, f'zoom-{m}.png'), README * 2, scale=2); print('zoom', m)
    elif cmd == 'big':                                    # big [moment] [ppu] kinds...: a close look for the artist
        args = sys.argv[2:]; m = args.pop(0) if args and args[0] in kit.LIGHTS else 'midday'
        if args and args[0] == 'parked':                  # the hangar for a quiet month
            w, h = fleet.PARKED; light = dict(kit.LIGHTS[m])
            img, _ = kit.raster(lambda x, y: fleet.parked(x - 15, y - 9, light), 2, 2, 28, 16)
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 18" width="30" height="18">{backdrop(m, 30, 18)}{img}</svg>'
            shoot_svg(svg, os.path.join(OUT, f'big-{m}.png'), 20, scale=1); print('big parked', m); return
        ppu = float(args.pop(0)) if args and args[0].replace('.', '').isdigit() else 6
        shoot_svg(zoom_svg(m, args or ('balloon',)), os.path.join(OUT, f'big-{m}.png'), ppu, scale=1); print('big', m)
    elif cmd == 'world':                                  # world [scale] moments...: the rendered world at README width
        args = sys.argv[2:]; sc = float(args.pop(0)) if args and args[0].replace('.', '').isdigit() else 1
        for m in args or ['midday']:
            svg = os.path.join(OUT, 'world', f'{m}.svg')
            page = f'<html><body style="margin:0;background:#fff"><img style="display:block;width:830px" src="file://{svg}"></body></html>'
            kit.shoot(page, 830, 346 + 90, os.path.join(OUT, f'world-{m}@{sc:g}x.png'), scale=sc); print('world', m, sc)
    elif cmd == 'mass':
        prev = 0
        for k, a in mass().items(): print(f'{k:12} {a:7.0f} sq units', '' if a > prev else '  <-- NOT BIGGER'); prev = a
    elif cmd == 'sheet':
        if '--keep' not in sys.argv:
            subprocess.run([sys.executable, os.path.join(ROOT, 'generator', 'world.py'), '--all', '--out', os.path.join(OUT, 'world')], check=True)
        W2 = 1660 / (2 * README)                          # a 1660 px cell at 2x README scale, in art units (= 1200)
        def side(svgs, gap=16):
            """Several SVGs side by side in one SVG (each keeps its own units)."""
            import re
            x, H, body = 0, 0, []
            for i, sv in enumerate(svgs):
                sv = sv.replace('id="g"', f'id="g{i}"').replace('url(#g)', f'url(#g{i})')     # each keeps its own sky
                m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', sv); w, h = float(m[1]), float(m[2])
                body.append(sv.replace('<svg ', f'<svg x="{x:.1f}" y="0" ', 1)); x += w + gap; H = max(H, h)
            return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x - gap:.1f} {H:.1f}" width="{x - gap:.1f}" height="{H:.1f}">{"".join(body)}</svg>'
        def pair(ms, out):
            """Worlds side by side at real README size (830 CSS px each)."""
            imgs = ''.join(f'<img style="display:block;width:830px" src="file://{os.path.join(OUT, "world", m + ".svg")}">' for m in ms)
            kit.shoot(f'<html><body style="margin:0;background:#f6f8fa;display:flex;align-items:flex-start;overflow:hidden">{imgs}</body></html>',
                      830 * len(ms), 346, out, scale=1.5)
            return out
        pair(('midday', 'golden'), os.path.join(OUT, 'row-day.png')); pair(('night', 'dusk'), os.path.join(OUT, 'row-night.png'))
        items = [('1 · Lineup, midday (2x README scale)', 'all nine at true relative size; Stearman-blue biplane, airmail paper plane, '
                  'red-and-gold airliner, green-band blimp, blue-and-gold banded airship with a red container', lineup_svg('midday', scale_w=W2)),
                 ('1b · Lineup, night (2x)', 'white-line print; liveries quieted by kit.pigment, gold = cabin, nav lights, burner', lineup_svg('night', scale_w=W2)),
                 ('1c · Lineups at real size (830 px canvas: 1 unit = 0.69 px), midday and night', 'what the README shows',
                  side([lineup_svg('midday', scale_w=1200, captions=False), lineup_svg('night', scale_w=1200, captions=False)], 0)),
                 ('2 · 2x zoom: hot air balloon, jet airliner, cargo airship (midday | night)', 'README scale x2',
                  side([zoom_svg('midday', ('balloon', 'airliner', 'airship')), zoom_svg('night', ('balloon', 'airliner', 'airship'))], 24)),
                 ('3 · World at real size: midday | golden hour', 'real data: Nov biplane, Dec–Mar hangars, Apr drone, May jet, Jun airliner, '
                  'Jul + Sep blimps, Aug balloon, Oct airship', os.path.join(OUT, 'row-day.png')),
                 ('3b · World at real size: night | dusk', 'the night print keeps the liveries, quietly', os.path.join(OUT, 'row-night.png'))]
        kit.sheet(items, os.path.join(OUT, 'sheet.png'), cols=1, cell=1660, title='Planes A · Golden-age liveries')
        print('sheet ->', os.path.join(OUT, 'sheet.png'))

if __name__ == '__main__':
    main()
