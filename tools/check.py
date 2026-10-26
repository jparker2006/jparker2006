#!/usr/bin/env python3
"""Automatic gates for the profile art. Design agents must not edit this file.

  python3 tools/check.py assets      (DIR holds art.svg and meta.json)

Hard gates (exit 1 if any fail):
  data      every ridge point (day or week) in meta.json matches data/contributions.json, and every crest is
            baseline - amp * value / vmax with one shared amp and vmax (honest, linear, same scale)
  numbers   every number printed in a label is a real number from the data (no invented stats)
  text      every label is >= 11 px when the image is shown 830 px wide (GitHub README width)
  contrast  every label has >= 4.5:1 contrast against the colour behind it (its data-bg)
  safe      no scripts, foreignObject, external links or external url() references
Soft (reported only): file size.
"""
import json, re, sys, os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'contributions.json')
NS = '{http://www.w3.org/2000/svg}'
d = sys.argv[1]
svg_path = next(p for p in (os.path.join(d, 'art.svg'), os.path.join(d, 'variant.svg')) if os.path.exists(p))
meta_path = os.path.join(d, 'meta.json')
raw = open(svg_path).read()
root = ET.fromstring(raw)
meta = json.load(open(meta_path))
days = dict(json.load(open(DATA))['days'])
fails, notes = [], []

def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)
def blend(fg, bg, a):
    F = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]; B = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(F[i] * a + B[i] * (1 - a)) for i in range(3))
def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)

# data
amp, vmax = meta['amp'], meta['vmax']
bad = 0
import datetime
def week_sum(a, b):
    d0, d1 = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    return sum(days.get((d0 + datetime.timedelta(days=i)).isoformat(), 0) for i in range((d1 - d0).days + 1))
values = []
for r in meta['ridges']:
    for item in r.get('days', []):                      # one point per day: [date, value, crest]
        date, v, top = item; values.append(v)
        if days.get(date, 0) != v: bad += 1; continue
        if abs(top - (r['baseline'] - amp * v / vmax)) > .01: bad += 1
    for item in r.get('weeks', []):                     # one point per week: [first, last, value, crest]
        a, b, v, top = item; values.append(v)
        if week_sum(a, b) != v: bad += 1; continue
        if abs(top - (r['baseline'] - amp * v / vmax)) > .01: bad += 1
window_max = max(values)
if window_max != vmax: fails.append(f'data: vmax {vmax} != real max {window_max}')
if bad: fails.append(f'data: {bad} ridge points do not match the data or the shared linear scale')

# numbers
allowed = {str(n) for n in range(0, 32)} | {'2021', '2022', '2023', '2024', '2025', '2026', "'25", "'26"}
allowed |= {str(v) for v in days.values()} | {str(v) for v in values} | {str(meta['total']), str(vmax)}
texts = [t for t in root.iter(NS + 'text')]
for t in texts:
    s = ''.join(t.itertext())
    for tok in re.findall(r"(?<![A-Za-z0-9])'?\d[\d,]*", s):   # skip digits inside words like jparker2006
        if tok.replace(',', '') not in allowed and tok not in allowed:
            fails.append(f'numbers: "{tok}" in "{s}" is not a number from the data')

# text size + contrast
vb = [float(v) for v in root.get('viewBox').split()]
scale = 830 / vb[2]
for t in texts:
    s = ''.join(t.itertext()); size = float(t.get('font-size', 16)); px = size * scale
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
notes.append(f'size: {kb:.0f} KB' + (' (over 500 KB: production build will compress the pixel layer)' if kb > 500 else ''))
notes.append(f'labels: {len(texts)}, smallest {min(float(t.get("font-size", 16)) for t in texts) * scale:.1f} px')
for n in notes: print('note  ', n)
for f in fails: print('FAIL  ', f)
print('PASS   all hard gates' if not fails else f'FAILED {len(fails)} gate(s)')
sys.exit(1 if fails else 0)
