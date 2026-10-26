"""The data rules, as locked in the concept grill (2026-10-26). Pure functions, standard library only.

- Years are mountains: one per calendar year, from the first year with a contribution. Summit height is linear in
  that year's total, on one shared scale.
- Months are a fleet: the rolling last 12 months (the newest is the current, partial month). Each month flies one
  aircraft. Each step up the fleet means double the work, measured against the record month:
      tier = 9 + ceil(log2(month / record)), clamped to 1..9; a month with no contributions flies nothing (parked).
- Days are living things on the shore: the rolling last 365 days, one per day, size linear in that day's count.
"""
import datetime, json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ('paper_plane', 'drone', 'helicopter', 'prop_plane', 'private_jet', 'balloon', 'airliner', 'blimp', 'airship')
NAMES = dict(paper_plane='paper plane', drone='drone', helicopter='helicopter', prop_plane='prop plane',
             private_jet='private jet', balloon='hot air balloon', airliner='jet airliner', blimp='blimp', airship='cargo airship')
MON = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

def load(path=None):
    """-> (days: {'YYYY-MM-DD': count}, last: date of the newest day in the data)."""
    days = dict(json.load(open(path or os.path.join(ROOT, 'data', 'contributions.json')))['days'])
    return days, datetime.date.fromisoformat(max(days))

def years(days, last):
    """[(year, total)] for every calendar year from the first one with a contribution through last.year."""
    first = min(int(d[:4]) for d, v in days.items() if v) if any(days.values()) else last.year
    return [(y, sum(v for d, v in days.items() if d[:4] == str(y) and d <= last.isoformat())) for y in range(first, last.year + 1)]

def month_total(days, y, m, last=None):
    key = f'{y}-{m:02d}'
    return sum(v for d, v in days.items() if d[:7] == key and (last is None or d <= last.isoformat()))

def months(days, last):
    """[(first-of-month date, total)] for the rolling last 12 months, oldest first; the last one is the current month."""
    out = []
    for back in range(11, -1, -1):
        m, y = last.month - back, last.year
        while m <= 0: m, y = m + 12, y - 1
        out.append((datetime.date(y, m, 1), month_total(days, y, m, last)))
    return out

def record_month(days):
    """The biggest month total ever (including the current, partial month)."""
    totals = {}
    for d, v in days.items(): totals[d[:7]] = totals.get(d[:7], 0) + v
    return max(totals.values(), default=0)

def tier(v, record):
    """0 (parked) .. 9 (cargo airship). Each step up = double the work."""
    if v <= 0 or record <= 0: return 0
    return max(1, min(9, 9 + math.ceil(math.log2(v / record) - 1e-12)))

def kind(v, record):
    t = tier(v, record)
    return KINDS[t - 1] if t else None

def recent_days(days, last, n=365):
    """[(date, count)] for the last n days, oldest first."""
    return [((last - datetime.timedelta(days=n - 1 - i)), days.get((last - datetime.timedelta(days=n - 1 - i)).isoformat(), 0)) for i in range(n)]

def fleet(days, last):
    """[(first-of-month, total, tier, kind)] for the rolling 12 months."""
    rec = record_month(days)
    return [(m, v, tier(v, rec), kind(v, rec)) for m, v in months(days, last)]

if __name__ == '__main__':
    d, last = load()
    print('last day', last, '| record month', record_month(d))
    print('years ', years(d, last))
    for m, v, t, k in fleet(d, last): print(f'  {MON[m.month]} {m.year}  {v:>5}  tier {t}  {NAMES.get(k, "parked")}')
    r = recent_days(d, last); print('days  ', len(r), r[0], r[-1], 'max', max(c for _, c in r))
