#!/usr/bin/env python3
"""Fill README.template.md with today's numbers (the same ones the art is drawn from).

    python3 generator/readme.py                        # -> README.md, quote for now in California
    python3 generator/readme.py --when 2026-11-01T13:00:00   # quote for that California time
"""
import argparse, datetime, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import clock, data

def fmt_day(d): return f'{data.MON[d.month].title()} {d.day}, {d.year}'

# Lines from Aaron Swartz's Guerilla Open Access Manifesto (2008), checked word for word against the original text.
# The README takes turns through them every 7 hours, in this order. 7 doesn't divide a day, so the slots drift 3 hours
# earlier each day and every line gets its share of daytime in California instead of one always landing at night.
QUOTES = [
    '“Information is power. But like all power, there are those who want to keep it for themselves.”',
    '“Sharing isn’t immoral — it’s a moral imperative.”',
    '“Only those blinded by greed would refuse to let a friend make a copy.”',
]
QUOTE_HOURS = 7
QUOTES_FROM = datetime.datetime(2026, 11, 1, tzinfo=clock.TZ)    # the first line's first turn

def quote(when):
    hours = (when.astimezone(datetime.timezone.utc) - QUOTES_FROM).total_seconds() // 3600
    return QUOTES[int(hours // QUOTE_HOURS) % len(QUOTES)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--when'); a = ap.parse_args()
    when = datetime.datetime.fromisoformat(a.when).replace(tzinfo=clock.TZ) if a.when else datetime.datetime.now(clock.TZ)
    days, last = data.load()
    years = data.years(days, last)
    fleet = data.fleet(days, last)
    recent = data.recent_days(days, last)
    best_day, best_count = max(recent, key=lambda p: (p[1], p[0]))
    m, v, tier, kind = fleet[-1]
    year, total = years[-1]
    values = {
        'YEAR': str(year), 'YEAR_TOTAL': f'{total:,}', 'FIRST_YEAR': str(years[0][0]),
        'MONTH': f'{data.MON[m.month].title()} {m.year}', 'MONTH_TOTAL': f'{v:,}',
        'MONTH_CRAFT': data.NAMES[kind] if kind else 'still in its hangar',
        'BEST_DAY': fmt_day(best_day), 'BEST_DAY_COUNT': f'{best_count:,}',
        'UPDATED': fmt_day(last),
        'QUOTE': quote(when),
    }
    root = os.path.dirname(HERE)
    text = open(os.path.join(root, 'README.template.md')).read()
    for k, val in values.items(): text = text.replace('{{' + k + '}}', val)
    assert '{{' not in text, 'unfilled placeholder in README.template.md'
    open(os.path.join(root, 'README.md'), 'w').write(text)
    print('README.md:', ', '.join(f'{k}={val}' for k, val in values.items()))

if __name__ == '__main__':
    main()
