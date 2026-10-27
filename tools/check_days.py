"""Check actual shoreline envelopes as well as the shared numeric scale."""
import datetime
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generator'))
import data
import days
import kit

counts, last = data.load()
recent = data.recent_days(counts, last)
hs = days.heights(recent)
assert len(hs) == 365
assert max(hs) == days.BAND['base'] - days.BAND['top']
for (_, count), h in zip(recent, hs):
    assert h == (days.BAND['base'] - days.BAND['top']) * (count / max(c for _, c in recent)) ** .5   # square-root scale
assert days.heights([]) == []
zero = [(last, 0)]
for light in kit.LIGHTS.values():
    assert all(days.shade(x, y, zero, light) is None for x in range(0, 1200, 7) for y in range(days.BAND['top'], 501, 3))
    assert days.shade(600, 500, [], light) is None
# Probe each real plant directly so neighbours cannot hide a bad tip: its top sits exactly at base - height,
# it draws ink right at that top (head, petal or bud tip) in every light, and nothing of it shows above.
banks = days._plants(recent)
plants = {id(p): p for _, bank in banks for p in bank}.values()
assert len(plants) == sum(1 for h in hs if h)
for (date, count), h in zip(recent, hs):
    if not h:
        continue
    cx = days.x_of(recent.index((date, count)), len(recent))
    p = next(p for p in plants if p['cx'] == cx)
    assert p['h'] == h and p['top'] == days.BAND['base'] - h, (date, h)
    tipx, tipy = days.tip(p)
    assert tipy == days.BAND['base'] - h
    for light in kit.LIGHTS.values():
        color = days._draw(tipx, tipy + min(.00001, h / 100), p, light)
        assert color is not None and all(0 <= c <= 255 for c in color), (date, h, light)
    for b in range(120):
        for q in banks[b][1]:
            if q is p: assert q['x0'] <= tipx <= q['x1']
# Public entry point supplies the hard upper/lower envelope clips.
assert days.shade(1100, days.BAND['top'] - .0001, recent, kit.LIGHTS['midday']) is None
assert days.shade(1100, days.BAND['base'] + .0001, recent, kit.LIGHTS['midday']) is None
# Nothing is drawn above any day's own top (shade skips a plant above its top), probed on a dense grid.
tops = {}
for q in plants:
    for x in range(int(q['x0']), int(q['x1']) + 1):
        tops[x] = min(tops.get(x, 501), q['top'])
assert all(days.shade(x + .5, y, recent, kit.LIGHTS['midday']) is None
           for x in range(0, 1200, 3) for y in range(days.BAND['top'], 500, 2) if y < tops.get(x, 501) - 1 and y < tops.get(x + 1, 501) - 1)
# Actual winter has no data; it must not sprout decorative stalks.
assert all(days.shade(days.x_of(i, 365), y, recent, kit.LIGHTS['midday']) is None
           for i, (d, c) in enumerate(recent) if datetime.date(2026, 1, 1) <= d <= datetime.date(2026, 3, 31)
           for y in (432, 460, 490, 499, 500))
print('PASS: exact square-root 365-day scale; every live tip exactly at base - height in all six lights; zero and empty windows; empty winter.')
