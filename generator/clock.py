"""Jake's real sky in Los Angeles (standard library only): the sun's elevation (NOAA solar equations), the moment of
the day the art should show, and the moon's phase.

Moments (by solar elevation e, before or after solar noon):
    night   e < -8 deg
    dawn    morning, -8 <= e < 8
    morning morning, e >= 8, before 11:00
    midday  e >= 8 from 11:00 until the afternoon sun drops below 10 deg
    golden  afternoon, -1 <= e < 10       (ends a few minutes after sunset)
    dusk    afternoon, -8 <= e < -1
    python3 generator/clock.py [ISO datetime]
"""
import datetime, math, sys, zoneinfo

LAT, LON = 34.05, -118.25                       # Los Angeles
TZ = zoneinfo.ZoneInfo('America/Los_Angeles')   # handles PDT/PST
MOMENTS = ('dawn', 'morning', 'midday', 'golden', 'dusk', 'night')
LABEL = dict(dawn='DAWN', morning='MORNING', midday='MIDDAY', golden='GOLDEN HOUR', dusk='DUSK', night='NIGHT')

def _solar(u):
    """Declination (deg) and equation of time (min) for an aware UTC datetime."""
    jc = (u.timestamp() / 86400 + 2440587.5 - 2451545) / 36525
    l0 = (280.46646 + jc * (36000.76983 + jc * .0003032)) % 360
    m = 357.52911 + jc * (35999.05029 - .0001537 * jc)
    e = .016708634 - jc * (.000042037 + .0000001267 * jc)
    c = (math.sin(math.radians(m)) * (1.914602 - jc * (.004817 + .000014 * jc)) + math.sin(math.radians(2 * m)) * (.019993 - .000101 * jc)
         + math.sin(math.radians(3 * m)) * .000289)
    app = l0 + c - .00569 - .00478 * math.sin(math.radians(125.04 - 1934.136 * jc))
    eps = 23 + (26 + (21.448 - jc * (46.815 + jc * (.00059 - jc * .001813))) / 60) / 60 + .00256 * math.cos(math.radians(125.04 - 1934.136 * jc))
    decl = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(app))))
    y = math.tan(math.radians(eps / 2)) ** 2
    eot = 4 * math.degrees(y * math.sin(2 * math.radians(l0)) - 2 * e * math.sin(math.radians(m)) + 4 * e * y * math.sin(math.radians(m))
                           * math.cos(2 * math.radians(l0)) - .5 * y * y * math.sin(4 * math.radians(l0)) - 1.25 * e * e * math.sin(2 * math.radians(m)))
    return decl, eot

def elevation(dt):
    """Sun elevation in degrees at an aware datetime, and whether it is before solar noon."""
    u = dt.astimezone(datetime.timezone.utc); decl, eot = _solar(u)
    ha = ((u.hour * 60 + u.minute + u.second / 60 + eot + 4 * LON) / 4 - 180 + 180) % 360 - 180   # hour angle, -180..180
    z = math.acos(max(-1., min(1., math.sin(math.radians(LAT)) * math.sin(math.radians(decl))
                               + math.cos(math.radians(LAT)) * math.cos(math.radians(decl)) * math.cos(math.radians(ha)))))
    return 90 - math.degrees(z), ha < 0

def moment(dt=None):
    dt = (dt or datetime.datetime.now(TZ)).astimezone(TZ)
    e, am = elevation(dt)
    if e < -8: return 'night'
    if am: return 'dawn' if e < 8 else ('morning' if dt.hour < 11 else 'midday')
    return 'midday' if e >= 10 else ('golden' if e >= -1 else 'dusk')

def moon(dt=None):
    """(age in days since new moon, illuminated fraction 0..1, waxing?) from the mean synodic month."""
    dt = (dt or datetime.datetime.now(TZ)).astimezone(datetime.timezone.utc)
    syn = 29.530588853
    age = ((dt - datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)).total_seconds() / 86400) % syn
    return age, (1 - math.cos(2 * math.pi * age / syn)) / 2, age < syn / 2

if __name__ == '__main__':
    now = datetime.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=TZ) if len(sys.argv) > 1 else datetime.datetime.now(TZ)
    e, am = elevation(now); age, lit, wax = moon(now)
    print(f'{now:%Y-%m-%d %H:%M %Z}: sun {e:.1f} deg ({"am" if am else "pm"}) -> {moment(now)}; moon {lit * 100:.0f}% lit ({"waxing" if wax else "waning"})')
    day = now.replace(hour=0, minute=0, second=0, microsecond=0); prev = None
    for i in range(24 * 12):
        t = day + datetime.timedelta(minutes=5 * i); mm = moment(t)
        if mm != prev: print(f'  {t:%H:%M} {mm}'); prev = mm
