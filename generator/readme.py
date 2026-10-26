#!/usr/bin/env python3
"""Fill README.template.md with today's numbers (the same ones the art is drawn from).

    python3 generator/readme.py            # -> README.md
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import data

def fmt_day(d): return f'{data.MON[d.month].title()} {d.day}, {d.year}'

def main():
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
    }
    root = os.path.dirname(HERE)
    text = open(os.path.join(root, 'README.template.md')).read()
    for k, val in values.items(): text = text.replace('{{' + k + '}}', val)
    assert '{{' not in text, 'unfilled placeholder in README.template.md'
    open(os.path.join(root, 'README.md'), 'w').write(text)
    print('README.md:', ', '.join(f'{k}={val}' for k, val in values.items()))

if __name__ == '__main__':
    main()
