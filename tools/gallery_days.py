"""Render the three shore studies and the chosen reeds at reading size."""
import datetime
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator'))
import data
import days
import kit

OUT = os.path.join(kit.ROOT, 'previews', 'pieces', 'days')
os.makedirs(OUT, exist_ok=True)


def svg(body, light, box=(0, 424, 1200, 76)):
    x, y, w, h = box
    paper = '#%02x%02x%02x' % light['paper']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{paper}"/>{body}</svg>')


def main():
    counts, last = data.load()
    recent = data.recent_days(counts, last)
    items, renders = [], {}
    for moment in ('midday', 'night'):
        light = kit.LIGHTS[moment]
        for form, name in (('A', 'Reeds in the shallows'), ('B', 'A wildflower bank'), ('C', 'Waves')):
            days.FORM = form
            body, png = kit.raster(lambda x, y: days.shade(x, y, recent, light), 0, 424, 1200, 500)
            renders[form, moment] = body
            art = svg(body, light)
            open(os.path.join(OUT, f'{form}-{moment}.svg'), 'w').write(art)
            items.append((f'{form} / {name} / {moment}', 'Full width at 830 px · oldest left · exact common height scale', art))
    days.FORM = 'A'
    for moment in ('midday', 'night'):
        for label, start, stop in (('Busy / Sep–Oct 2026', datetime.date(2026, 9, 1), last),
                                  ('Quiet / Jan–Mar 2026', datetime.date(2026, 1, 1), datetime.date(2026, 3, 31))):
            # 600 art units at 830 px = precisely 2x the reading-size scale.
            center = (days.x_of((start - recent[0][0]).days, 365) + days.x_of((stop - recent[0][0]).days, 365)) / 2
            x0 = min(600, max(0, center - 300))
            art = svg(renders['A', moment], kit.LIGHTS[moment], (x0, 424, 600, 76))
            items.append((f'A / {label} / {moment}', '2× reading size · surrounding dates included for context', art))
    for moment in ('midday', 'golden', 'night'):
        path = os.path.join(OUT, 'world', moment + '.svg')
        if os.path.exists(path):
            items.append((f'One world / {moment}', 'Chosen reeds · 830 px reading size · other pieces are placeholders', path))
    kit.sheet(items, os.path.join(OUT, 'sheet.png'), cols=1, cell=830,
              title='The days / three shores in cobalt / A selected')
    # Separate true reading-size view for inspection, without sheet scaling.
    path = os.path.join(OUT, 'world', 'midday.svg')
    if os.path.exists(path):
        kit.shoot(f'<html><body style="margin:0"><img width="830" src="file://{path}"></body></html>',
                  830, 346, os.path.join(OUT, 'reading-size.png'), scale=1)


if __name__ == '__main__':
    main()
