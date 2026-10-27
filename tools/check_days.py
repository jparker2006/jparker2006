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
default_form = days.FORM
for form in 'ABC':
    days.FORM = form
    for light in kit.LIGHTS.values():
        assert all(days.shade(x, y, zero, light) is None for x in range(0, 1200, 7) for y in range(days.BAND['top'], 501, 3))
        assert days.shade(600, 500, [], light) is None
    # Probe each real plant directly so neighbours cannot hide a bad tip.
    for i, ((date, count), h) in enumerate(zip(recent, hs)):
        if not h:
            continue
        # The cached primitive preserves the original common scale.
        plants = days._plants(recent)
        cx = days.x_of(i, len(recent))
        p = next(p for p in plants[min(119, int(cx / 10))] if p[0] == cx)
        _, _, bend, r = p
        fn = (lambda x, y: days._wave(x, y, *p, kit.LIGHTS['midday'])) if form == 'C' else (
            lambda x, y: days._reed(x, y, *p, kit.LIGHTS['midday'], flower=form == 'B'))
        # Probe a horizontal line just inside the exact tip. Include the
        # analytic tip coordinate so subpixel plants are not falsely missed.
        if form == 'C':
            width = min(10, 1.5 + h * .22)
            tipx = kit.clamp(cx + bend * .5 + width * .32, .15, 1199.85)
        else:
            if form == 'B': hh = min(7.5, 1.6 + h * .085) if h > 4 else 0
            else: hh = min(12, h * .15) if h > 26 else 0
            tipx = days._stem(cx, bend, 1 - hh / h)
        tipy = days.BAND['base'] - h + min(.00001, h / 100)
        assert fn(tipx, tipy) is not None, (form, date, h)
        for light in kit.LIGHTS.values():
            color = (days._wave(tipx, tipy, *p, light) if form == 'C' else
                     days._reed(tipx, tipy, *p, light, flower=form == 'B'))
            assert color is not None and all(0 <= c <= 255 for c in color)
    # Public entry point supplies the hard upper/lower envelope clips.
    assert days.shade(1100, days.BAND['top'] - .0001, recent, kit.LIGHTS['midday']) is None
    assert days.shade(1100, days.BAND['base'] + .0001, recent, kit.LIGHTS['midday']) is None
    # Actual winter has no data; it must not sprout decorative stalks.
    assert all(days.shade(days.x_of(i, 365), y, recent, kit.LIGHTS['midday']) is None
               for i, (d, c) in enumerate(recent) if datetime.date(2026, 1, 1) <= d <= datetime.date(2026, 3, 31)
               for y in (432, 460, 490, 499, 500))
days.FORM = default_form
print('PASS: exact square-root 365-day scale; all live tips in A/B/C; zero and empty windows; all six lights; empty winter.')
