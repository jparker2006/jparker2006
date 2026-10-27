"""Flowers C (engraved superflat): strips, zooms and the full world, on one contact sheet.

    python3 tools/gallery_flowers-c.py quick     # strips and zooms only (uses the cached day -> x map)
    python3 tools/gallery_flowers-c.py           # renders the world too, then the full sheet
"""
import datetime, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generator'))
import data, days, kit, world

OUT = os.path.join(kit.ROOT, 'previews', 'pieces', 'flowers-c')
WORLD = os.path.join(OUT, 'world')
os.makedirs(WORLD, exist_ok=True)
counts, last = data.load()
recent = data.recent_days(counts, last)


def xmap(rebuild=False):
    path = os.path.join(OUT, 'xmap.json')
    if rebuild or not os.path.exists(path):
        world.build('midday', counts, last)              # sets days.XMAP exactly as the world places the days
        json.dump({d.isoformat(): days.XMAP(d) for d, _ in recent}, open(path, 'w'))
    m = json.load(open(path))
    days.XMAP = lambda d: m[d.isoformat()]


def strip(moment, box=(0, 392, 1200, 108)):
    light = kit.LIGHTS[moment]; tint = world.TINT[moment]
    t0 = time.time()
    body, png = kit.raster(lambda x, y: days.shade(x, y, recent, light), 0, days.BAND['top'] - 8, 1200, days.BAND['base'])
    dt = time.time() - t0
    x, y, w, h = box
    bg = '#%02x%02x%02x' % tuple(int(v) for v in kit.mix(tint[2], tint[3], .8))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')
    return svg, body, bg, len(png), dt


def crop(body, bg, x0, x1, y0=392):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {500 - y0}">'
            f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{500 - y0}" fill="{bg}"/>{body}</svg>')


def span(a, b):
    xs = [days.XMAP(d) for d, _ in recent if a <= d <= b]
    return min(xs) - 6, max(xs) + 6


def main():
    quick = 'quick' in sys.argv
    if not quick:
        for m in ('midday', 'golden', 'night'):
            svg, meta = world.build(m, counts, last)
            open(os.path.join(WORLD, m + '.svg'), 'w').write(svg); json.dump(meta, open(os.path.join(WORLD, m + '.json'), 'w'))
            print(m, len(svg) // 1024, 'KB', {k: v for k, v in meta['sizes'].items() if k.startswith('days')})
    xmap(rebuild=not quick)
    items, strips = [], {}
    for m in ('midday', 'night'):
        svg, body, bg, size, dt = strip(m)
        strips[m] = (body, bg)
        open(os.path.join(OUT, f'strip-{m}.svg'), 'w').write(svg)
        print(f'strip {m}: {size // 1024} KB png, {dt:.1f} s')
        items.append((f'Flowers C / full width / {m}', 'All 365 days at 830 px (real size) · each under its month\'s aircraft', svg))
    busy, mid = span(datetime.date(2026, 9, 1), last), span(datetime.date(2026, 6, 1), datetime.date(2026, 8, 31))
    for m in ('midday', 'night'):
        body, bg = strips[m]
        c = (busy[0] + busy[1]) / 2
        items.append((f'2x / busiest stretch, Sep–Oct 2026 / {m}', '600 units at 830 px = 2x reading size', crop(body, bg, c - 300, c + 300)))
    for m in ('midday',):
        body, bg = strips[m]
        c = (mid[0] + mid[1]) / 2
        items.append((f'2x / mid stretch, Jun–Aug 2026 / {m}', '600 units at 830 px = 2x reading size', crop(body, bg, c - 300, c + 300)))
    if quick:
        kit.sheet(items, os.path.join(OUT, 'quick.png'), cols=1, cell=830, title='Flowers C · quick look')
        return
    for m in ('midday', 'golden', 'night'):
        items.append((f'The world / {m}', 'world.py render at real size (830 px)', os.path.join(WORLD, m + '.svg')))
    kit.sheet(items, os.path.join(OUT, 'sheet.png'), cols=1, cell=830,
              title='Flowers C · engraved superflat: a hand-coloured meadow, faces only on the busiest 10% of days')


if __name__ == '__main__':
    main()
