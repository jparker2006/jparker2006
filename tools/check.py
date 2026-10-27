#!/usr/bin/env python3
"""Automatic gates for the world art. Design agents must not edit this file.

    python3 tools/check.py assets/art.svg [more.svg ...]      (each SVG needs the .json that world.py writes next to it)

Hard gates (exit 1 if any fail):
  years     mountain totals match the data; every summit is exactly base - amp * sqrt(total / max), at its slot centre;
            no land inside a year's slot rises above that year's summit (checked on mountains.crest)
  fleet     the 12 rolling months match the data; each tier is 9 + ceil(log2(month / record)), each craft its tier's kind
  days      the 365 rolling days match the data; each day's height is (base - top) * sqrt(count / max), also via days.heights()
  numbers   every number printed in the art (microprint included) is a real number from the data
  text      readable labels are >= 11 px when the art is shown 830 px wide (GitHub's README width), microprint excepted
  contrast  readable labels have >= 4.5:1 contrast against the colour behind them (their data-bg)
  safe      no scripts, foreignObject, external links or external url() references
Soft (reported only): file size (aim for < 500 KB).
"""
import datetime, json, math, os, re, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'generator'))
import data, mountains, days as daysmod

NS = '{http://www.w3.org/2000/svg}'

def lum(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda v: v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)
def blend(fg, bg, a):
    F = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]; B = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(F[i] * a + B[i] * (1 - a)) for i in range(3))
def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)

def check(svg_path):
    fails, notes = [], []
    raw = open(svg_path).read(); root = ET.fromstring(raw)
    meta = json.load(open(os.path.splitext(svg_path)[0] + '.json'))
    days_, _ = data.load()
    last = datetime.date.fromisoformat(meta['last'])
    # years
    years = data.years(days_, last)
    if [(y['year'], y['total']) for y in meta['years']] != years: fails.append('years: totals do not match the data')
    band = mountains.BAND; mx = max((t for _, t in years), default=0) or 1
    w = (band['x1'] - band['x0']) / len(years)
    for i, (y, (yr, tot)) in enumerate(zip(meta['years'], years)):
        want = (band['x0'] + (i + .5) * w, band['base'] - band['amp'] * math.sqrt(tot / mx))   # square-root scale, labeled
        if abs(y['summit'][0] - want[0]) > 1e-6 or abs(y['summit'][1] - want[1]) > 1e-6:
            fails.append(f'years: {yr} summit {y["summit"]} != {want}')
        x0 = band['x0'] + i * w
        hi = min(mountains.crest(x0 + w * k / 400, years) for k in range(401))
        if hi < want[1] - .05: fails.append(f'years: land in the {yr} slot rises above its summit ({hi:.2f} < {want[1]:.2f})')
    # fleet
    rec = data.record_month(days_)
    if meta['record_month'] != rec: fails.append(f'fleet: record month {meta["record_month"]} != {rec}')
    months = data.months(days_, last)
    if [(f['month'], f['total']) for f in meta['fleet']] != [(m.isoformat()[:7], v) for m, v in months]:
        fails.append('fleet: months do not match the data')
    for f in meta['fleet']:
        t = f['tier']; v = f['total']
        want = 0 if v <= 0 else max(1, min(9, 9 + math.ceil(math.log2(v / rec) - 1e-12)))
        if t != want: fails.append(f'fleet: {f["month"]} tier {t} != {want}')
        if f['kind'] != (data.KINDS[t - 1] if t else None): fails.append(f'fleet: {f["month"]} flies {f["kind"]} for tier {t}')
    # days
    recent = data.recent_days(days_, last)
    counts = [c for _, c in recent]
    if meta['days']['counts'] != counts: fails.append('days: counts do not match the data')
    b = meta['days']['band']; dmax = max(counts) or 1
    want = [(b['base'] - b['top']) * (c / dmax) ** .5 for c in counts]          # square-root scale, tallest labeled
    if any(abs(a - z) > 1e-9 for a, z in zip(meta['days']['heights'], want)) or any(abs(a - z) > 1e-9 for a, z in zip(daysmod.heights(recent), want)):
        fails.append('days: heights do not follow the square-root scale')
    # numbers
    allowed = {str(y) for y, _ in years} | {f'{t:,}' for _, t in years} | {str(t) for _, t in years}
    allowed |= {f'{v:,}' for _, v in months} | {str(v) for _, v in months} | {f'{m.year}' for m, _ in months}
    allowed |= {f'{m.year % 100:02d}' for m, _ in months}                      # NOV '25 ... OCT '26
    allowed |= {str(c) for c in counts} | {f'{c:,}' for c in counts} | {str(d.day) for d, _ in recent}   # the tallest reed's label
    texts = list(root.iter(NS + 'text'))
    for t in texts:
        s = ''.join(t.itertext())
        for tok in re.findall(r"(?<![A-Za-z0-9])\d[\d,]*", s):
            if tok not in allowed and tok.replace(',', '') not in allowed:
                fails.append(f'numbers: "{tok}" in "{s}" is not a number from the data')
    # text size and contrast
    vb = [float(v) for v in root.get('viewBox').split()]; scale = 830 / vb[2]
    readable = [t for t in texts if t.get('data-micro') != '1' and t.get('data-halo') != '1']   # halos are backing, not labels
    for t in readable:
        s = ''.join(t.itertext()); px = float(t.get('font-size', 16)) * scale
        if px < 11 - 1e-6: fails.append(f'text: "{s}" is {px:.1f} px at 830 px wide (min 11)')
        bg = t.get('data-bg'); fill = t.get('fill', '#000000'); op = float(t.get('fill-opacity', 1))
        if not bg: fails.append(f'contrast: "{s}" has no data-bg'); continue
        cr = ratio(blend(fill, bg, op), bg)
        if cr < 4.5: fails.append(f'contrast: "{s}" is {cr:.2f}:1 (min 4.5)')
    # safety
    low = raw.lower()
    for pat, why in [('<script', 'script'), ('foreignobject', 'foreignObject'), ('href="http', 'external link'),
                     ("href='http", 'external link'), ('url(http', 'external url()'), ('@import', '@import')]:
        if pat in low: fails.append(f'safe: contains {why}')
    kb = len(raw.encode()) / 1024
    notes.append(f'size {kb:.0f} KB' + (' (over 500 KB)' if kb > 500 else ''))
    notes.append(f'{len(readable)} readable labels, smallest {min(float(t.get("font-size", 16)) for t in readable) * scale:.1f} px')
    return fails, notes

if __name__ == '__main__':
    bad = 0
    for path in sys.argv[1:]:
        fails, notes = check(path)
        print(f'{os.path.basename(path)}: ' + ('PASS' if not fails else f'FAILED {len(fails)}') + ' · ' + ' · '.join(notes))
        for f in fails: print('   FAIL', f)
        bad += bool(fails)
    sys.exit(1 if bad else 0)
