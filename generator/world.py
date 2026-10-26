#!/usr/bin/env python3
"""Compose the world for one moment of Jake's day (docs/WORLD.md).

    python3 generator/world.py                       # the real moment in Los Angeles -> assets/art.svg
    python3 generator/world.py --moment golden --out previews/world/golden.svg
    python3 generator/world.py --all --out previews/world        # all six moments

Layers, bottom to top: tint plate (vector gradients), sky and water engraving (ink with alpha), mountains (years),
days, cast (cloud, ducks, turtle, koi), fleet (months), text. Motion is CSS inside the SVG.
"""
import argparse, base64, datetime, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kit, data, clock, fleet, days as daysmod, mountains, friends
from kit import clamp, mix, line, q, BAYER, VW, VH, S

HZ = mountains.BAND['base']                          # the far shore and horizon
SLOT_X0, SLOT_X1 = 64, 1136                          # the 12 months, oldest left
CLOUD_SCALE = .82

# ------------------------------------------------------------------ the tint plate under the engraving, per moment
TINT = {   # sky top, sky at the horizon, water far, water near, sun glow
    'dawn':    ((182, 194, 232), (250, 222, 204), (236, 222, 222), (200, 206, 234), (252, 212, 176)),
    'morning': ((176, 206, 240), (234, 240, 247), (224, 235, 246), (198, 218, 240), (252, 240, 214)),
    'midday':  ((172, 208, 242), (222, 237, 249), (219, 235, 247), (194, 220, 243), (250, 240, 214)),
    'golden':  ((160, 190, 230), (252, 214, 170), (248, 224, 192), (204, 204, 222), (252, 214, 150)),
    'dusk':    ((84, 96, 160), (232, 176, 182), (196, 166, 192), (84, 92, 148), (238, 166, 136)),
    'night':   ((9, 19, 44), (26, 44, 86), (22, 38, 76), (9, 19, 43), (70, 92, 140)),
}
TEXT_INK = dict(dawn='#18488a', morning='#18488a', midday='#18488a', golden='#18488a', dusk='#f4ecf2', night='#e6edf8')

def hexc(c): return '#%02x%02x%02x' % tuple(int(round(v)) for v in c)

def sun_spec(moment, summits):
    """Where the light source sits for each hand-composed moment."""
    nx = summits[-1][0] if summits else 900
    return {'dawn': ('sun', 150, HZ - 8, 66), 'morning': ('sun', 236, 122, 50), 'midday': ('sun', 612, 60, 44),
            'golden': ('sun', nx, HZ - 40, 90), 'dusk': ('glow', nx, HZ + 30, 90), 'night': ('moon', 880, 92, 36)}[moment]

# ------------------------------------------------------------------ the cast (always there, never data)
DUCKS = [(150, 424, 1.3), (199, 431, 1.0), (238, 428, 1.0), (276, 433, 1.0)]     # a mother leads three
TURTLE, KOI = (452, 388, .95), (760, 418, 1.2)

def cloud_sdf(u, v):
    parts = [(-52, -40, 34), (6, -64, 50), (62, -36, 28)]; hw, h = 110, 56; r = h / 2
    d = math.hypot(max(abs(u) - (hw - r), 0), v + r) - r
    for dx, dy, cr in parts: d = kit.smin(d, math.hypot(u - dx, v - dy) - cr, 9)
    return d

def cloud_at(u, v, light):
    """The round smiling cloud. (u, v) relative to the centre of its flat base; unscaled units."""
    if not (-120 < u < 122 and -116 < v < 2): return None
    d = cloud_sdf(u, v)
    if d > 0: return None
    night = light['night']
    paper = mix((112, 132, 176), (150, 168, 206), .3) if night else (252, 251, 248)
    ink = (60, 80, 124) if night else light['ink']
    if d > -(.8 + .8 * clamp((v + 60) / 60)): return (210, 220, 240) if night else light['ink']
    ex, ey = u - 6, v + 30
    for sx in (-24, 24):
        if night:
            if abs(math.hypot(ex - sx, ey + 1) - 4.6) < 1.1 and ey > -.5: return (24, 36, 70)
            continue
        if math.hypot(ex - sx + 1.5, ey + 2) < 1.5: return (255, 255, 255)
        if ((ex - sx) / 4.2) ** 2 + (ey / 5.6) ** 2 <= 1: return light['ink']
    if abs(math.hypot(ex, ey - 1) - (6.5 if night else 9.5)) < 1.3 and ey > (4.5 if night else 6): return (24, 36, 70) if night else light['ink']
    for sx in (-42, 42):
        if ((ex - sx) / 8) ** 2 + ((ey - 9) / 3.4) ** 2 <= 1: return mix(paper, (232, 186, 160), .6)
    t = clamp(.36 * clamp((v + 44) / 44) ** 1.6 - .1 * clamp(u / 110))
    if t < .03: return paper
    return mix(paper, ink, q(line(-d / 2.5, t, 1 / S / 2.5)))

def duck_at(x, y, light):
    gold = light['gold']; body = mix(gold, (252, 226, 120), .55) if not light['night'] else mix(gold, (120, 110, 80), .35)
    dark, beak = mix(gold, (140, 90, 20), .55), (226, 132, 58) if not light['night'] else (170, 104, 52)
    for dx, dy, s in DUCKS:
        bx, by = (x - dx) / s, (y - dy) / s
        if not (-18 < bx < 21 and -17 < by < 8): continue
        def shape(a, b):
            body_ = ((a / 13) ** 2 + (b / 6.5) ** 2 <= 1 and b > -4.5) or (a < -9 and -6 < b < 1 and b > -1.6 * (a + 16))
            return body_ or math.hypot(a - 8, b + 9) <= 5.6 or ((a - 15.5) / 3.9) ** 2 + ((b + 8) / 1.9) ** 2 <= 1
        if not shape(bx, by): continue
        if light['night']:
            if abs(math.hypot(bx - 10, by + 11.2) - 1.6) < .45 and by > -11.2: return (30, 30, 30)     # asleep
        elif math.hypot(bx - 10, by + 10.5) <= 1.25: return light['ink']
        if not all(shape(bx + ox, by + oy) for ox, oy in ((.8, 0), (-.8, 0), (0, .8), (0, -.8))): return kit.outline(light) if not light['night'] else (40, 50, 80)
        if ((bx - 15.5) / 3.9) ** 2 + ((by + 8) / 1.9) ** 2 <= 1: return beak
        return mix(body, dark, q(line((y + .5 * math.sin(x / 2.6)) / 1.5, clamp((by + 3) / 9) * .6, 1 / S / 1.5)))
    return None

def set_friend_colours(light):
    f = friends
    if light['night']:
        f.NAVY, f.PAPER, f.WATER_INK = (6, 12, 28), (18, 34, 66), (118, 154, 206)
        f.SHELL_INK, f.SHELL_PAPER, f.SKIN_INK, f.SKIN_PAPER = (60, 54, 40), (120, 116, 100), (44, 60, 52), (96, 112, 108)
        f.KOI_INK, f.KOI_PAPER, f.FIN_PAPER = (170, 110, 60), (190, 160, 130), (150, 160, 182)
        f.EYE_PAPER, f.BLUSH = (190, 196, 210), (170, 110, 100)
    else:
        f.NAVY, f.PAPER, f.WATER_INK = light['ink'], light['paper'], light['ink']
        f.SHELL_INK, f.SHELL_PAPER, f.SKIN_INK, f.SKIN_PAPER = light['ink'], light['paper'], light['ink'], light['paper']
        f.KOI_INK, f.KOI_PAPER, f.FIN_PAPER = (212, 116, 46), (252, 228, 194), light['paper']
        f.EYE_PAPER, f.BLUSH = light['paper'], (236, 190, 160)

def friend(name, x, y, anchor):
    fx, fy, s = anchor
    lx, ly = (x - fx) / s, (y - fy) / s; x0, y0, x1, y1 = friends.BBOX[name]
    if x0 <= lx <= x1 and y0 <= ly <= y1: return getattr(friends, name)(lx, ly)
    return None

# ------------------------------------------------------------------ placement
def overlaps(a, b, m=0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])

def slot_x(i): return SLOT_X0 + (i + .5) * (SLOT_X1 - SLOT_X0) / 12

def place_fleet(months, keepouts):
    """x follows the month, y the craft's natural altitude; big craft are placed first, small ones dodge."""
    placed = {}
    for i in sorted(range(len(months)), key=lambda i: (-months[i][2], i)):
        kind = months[i][3]
        if not kind: continue
        w, h = fleet.SIZE[kind]; x0 = min(max(slot_x(i), 18 + w / 2), VW - 18 - w / 2); y0 = fleet.ALTITUDE[kind]
        best = None
        for dy in (0, -14, 14, -28, 28, -42, 42, -58, 58, -76, 76):
            for dx in (0, -16, 16, -32, 32, -48, 48):
                x, y = min(max(x0 + dx, 18 + w / 2), VW - 18 - w / 2), y0 + dy
                b = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
                if b[1] < 14 or b[3] > HZ - 6: continue
                if any(overlaps(b, o, 8) for o in keepouts) or any(overlaps(b, p[2], 10) for p in placed.values()): continue
                best = (x, y, b); break
            if best: break
        placed[i] = best or (x0, y0, (x0 - w / 2, y0 - h / 2, x0 + w / 2, y0 + h / 2))
    return placed

def place_cloud(boxes, title_box):
    """The cloud floats in the emptiest stretch of sky (it never covers a month)."""
    s = CLOUD_SCALE; best, score = (330, 152), -float('inf')
    for cx in range(240, 960, 16):
        for cy in range(118, 214, 8):
            b = (cx - 120 * s, cy - 116 * s, cx + 122 * s, cy + 2 * s)
            if overlaps(b, title_box, 10): continue
            gap = min([max(o[0] - b[2], b[0] - o[2], o[1] - b[3], b[1] - o[3]) for o in boxes] + [400])
            if gap > score: best, score = (cx, cy), gap
    return best

# ------------------------------------------------------------------ the sky and water engraving (ink with alpha)
def alpha_layer(fn, x0, y0, x1, y1):
    w, h = round((x1 - x0) * S), round((y1 - y0) * S); rows = []
    for py in range(h):
        row = []
        for px in range(w):
            r = fn(x0 + (px + .5) / S, y0 + (py + .5) / S)
            if r is None: row.append((0, 0, 0, 0)); continue
            c, a = r
            a = round(clamp(a) * 12) / 12
            row.append((0, 0, 0, 0) if a <= 0 else tuple(int(v + .5) for v in c) + (int(a * 255),))
        rows.append(row)
    data_ = kit.png(rows)
    return (f'<image x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" href="data:image/png;base64,{base64.b64encode(data_).decode()}"/>', data_)

def make_sky_water(moment, light, sun, years):
    kind, sx, sy, sr = sun
    night = light['night']
    crest = [mountains.crest((px + .5) / S, years) for px in range(VW * S.__int__() + 2)] if False else None
    cache = {}
    def crest_at(x):
        k = int(x * 2)
        if k not in cache: cache[k] = mountains.crest(k / 2, years)
        return cache[k]
    gold, hair, ink = light['gold'], light['hair'], light['ink']
    def fn(x, y):
        ds = math.hypot(x - sx, y - sy)
        if y < HZ:
            # the light source
            if kind == 'sun' and ds < sr:
                th = math.atan2(y - sy, x - sx); w = .03 + .27 * (ds / sr) ** 2
                c1 = line((ds + 3.6 * math.cos(16 * th)) / 5, w, 1 / S / 5); c2 = line((ds + 3.6 * math.cos(16 * th + math.pi)) / 5, w, 1 / S / 5)
                rim = line(ds / 9, .1, 1 / S / 9) if ds > sr - 3 else 0
                return mix((253, 250, 242), gold, q(max(c1, c2, rim) * .9)), 1
            if kind == 'moon' and ds < sr:
                age, lit, wax = clock.moon(WHEN)
                k = math.cos(2 * math.pi * age / 29.530588853)              # terminator: +1 new .. -1 full
                u, v = (x - sx) / sr, (y - sy) / sr
                edge = math.sqrt(max(0., 1 - v * v)); term = k * edge
                bright = (u > term) if wax else (u < -term)
                base = (236, 232, 214) if bright else (40, 56, 96)
                c = line(ds / 3, .14 if bright else .2, 1 / S / 3)
                return mix(base, (180, 170, 140) if bright else (70, 90, 136), q(c * .8)), 1
            deep = clamp((ds - sr) / 900) ** .9
            t = (.03 + .02 * clamp(1 - y / HZ)) if night else (.03 + .08 * deep)
            w1 = (y + 2.6 * math.sin((x + .4 * y) / 11)) / 4.4; w2 = (y + 2.6 * math.sin((-x + .4 * y) / 11 + 1.7)) / 4.4
            c = 1 - (1 - line(w1, t, 1 / S / 4.4)) * (1 - line(w2, t, 1 / S / 4.4)); col = hair
            if kind in ('sun', 'moon') and ds < sr + 46:                      # halo rings
                rc = line(ds / 3.6, .24 * (1 - (ds - sr) / 46), 1 / S / 3.6)
                if rc > c: c, col = rc, (gold if kind == 'sun' else (196, 206, 232))
            if kind == 'sun' and ds > sr + 30:                                 # engraved rays, fading
                th = math.atan2(y - sy, x - sx); fade = math.exp(-(ds - sr - 30) / 60) * clamp((ds - sr - 30) / 30)
                ray = line(th * 36 / math.pi, .075 * fade * (1 if int(math.floor(th * 36 / math.pi + .5)) % 2 else .4), 1 / S * 36 / math.pi / max(ds, 1))
                if ray > c: c, col = ray, mix(hair, gold, .6)
            if abs(y - (HZ - .6)) < .5: c, col = max(c, .5), ink                 # the far shore line
            return col, c
        # water: perspective lines, the land's broken reflection, the sun's (or moon's) path, stillness
        f = (y - HZ) / (VH - HZ); gx = abs(x - sx); gw = 12 + (y - HZ) * .3
        t = (.06 + .05 * f) if night else (.06 + .17 * f ** 1.2) * (1 - .55 * math.exp(-gx / (gw * 2.2)))
        col = ink if not night else hair
        n = 80 * f ** .72; L = int(math.floor(n + .5))
        ym = HZ - (y - HZ) / .5
        if crest_at(x) <= ym < HZ and ((int(y * 1.3) * 2654435761 + int(x / 13 + 3 * math.sin(y * .7)) * 40503) >> 7) % 7 > 1:
            t += .3 * (1 - f * .6)
        if kind in ('sun', 'glow', 'moon') and gx < gw and ((L * 2654435761 + int((x + L * 5) / 9) * 40503) >> 6) % 5 > 1:
            t, col = .5 * (1 - gx / gw) + .14, (gold if kind != 'moon' else (226, 222, 200))
        elif ((L * 2246822519 + int((x + L * 37) / (16 + (L * 7) % 23)) * 3266489917) >> 9) % 9 == 0: t = 0
        for (fx, fy, s), a, b in ((TURTLE, 27, 4.6), (KOI, 14, 3)):
            if abs(kit.ell((x - fx) / s, (y - fy) / s, 0, 1.2, a, b)) < .5: t = max(t, .45)
        for dx, dy, s in DUCKS:
            uu, vv = (x - dx) / s, (y - dy) / s
            if -36 < uu < -8 and abs(abs(vv - 2) - (-uu - 8) * .16) < .7: t = max(t, .45)
        wob = .1 * math.sin(x / 9.3 + y * .5) + .07 * math.sin(x / 23.1 - y * .2)
        return col, line(n + wob, clamp(t) * .9, 1 / S * 80 * .72 * max(f, .02) ** -.28 / (VH - HZ))
    return alpha_layer(fn, 0, 0, VW, VH)

# ------------------------------------------------------------------ build
MOTION_CSS = """
@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(-14px,2px)}}
@keyframes bob{0%,100%{transform:translate(0,0)}50%{transform:translate(0,-6px)}}
@keyframes hover{0%,100%{transform:translate(0,0)}25%{transform:translate(.6px,-1.2px)}50%{transform:translate(-.4px,-.4px)}75%{transform:translate(.4px,-1.4px)}}
@keyframes spinx{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.18)}}
@keyframes spiny{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.18)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes sway{0%,100%{transform:skewX(0deg)}50%{transform:skewX(-1.6deg)}}
@keyframes leap{0%,60%,100%{transform:translate(0,56px)}68%{transform:translate(-4px,0)}73%{transform:translate(-7px,-1px)}82%{transform:translate(-12px,56px)}}
@keyframes ripple{0%,81%{opacity:0;transform:scale(.35)}85%{opacity:.9}100%{opacity:0;transform:scale(1.6)}}
@keyframes twinkle{0%,100%{opacity:.25}50%{opacity:1}}
.cloud{animation:drift 26s ease-in-out infinite}.bob{animation:bob 11s ease-in-out infinite}.hover{animation:hover 2.6s ease-in-out infinite}
.spin-x{animation:spinx .32s linear infinite}.spin-y{animation:spiny .28s linear infinite}.spin{animation:spin .6s linear infinite}
.sway{animation:sway 7s ease-in-out infinite}.koi{animation:leap 9s ease-in-out infinite}.star{animation:twinkle 4s ease-in-out infinite}
.ring{transform-box:fill-box;transform-origin:center;animation:ripple 9s ease-out infinite;opacity:0}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.koi{transform:none}.ring{opacity:0}}
"""

def build(moment, days_, last):
    light = dict(kit.LIGHTS[moment]); night = light['night']
    years = data.years(days_, last); months = data.fleet(days_, last); recent = data.recent_days(days_, last)
    summits = mountains.summits(years); sun = sun_spec(moment, summits)
    tint = TINT[moment]; text_ink = TEXT_INK[moment]
    set_friend_colours(light)
    out, sizes = [], {}
    P = moment[:2] + '-'
    # 1. tint plate
    kind, sx, sy, sr = sun
    defs = (f'<clipPath id="{P}card"><rect width="{VW}" height="{VH}" rx="16"/></clipPath>'
            f'<linearGradient id="{P}sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hexc(tint[0])}"/><stop offset="1" stop-color="{hexc(tint[1])}"/></linearGradient>'
            f'<linearGradient id="{P}water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hexc(tint[2])}"/><stop offset="1" stop-color="{hexc(tint[3])}"/></linearGradient>'
            f'<radialGradient id="{P}glow" cx="{sx}" cy="{sy}" r="{sr * 4.2:.0f}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{hexc(tint[4])}" stop-opacity=".95"/>'
            f'<stop offset=".45" stop-color="{hexc(tint[4])}" stop-opacity=".35"/><stop offset="1" stop-color="{hexc(tint[4])}" stop-opacity="0"/></radialGradient>')
    out.append(f'<rect width="{VW}" height="{HZ}" fill="url(#{P}sky)"/><rect y="{HZ}" width="{VW}" height="{VH - HZ}" fill="url(#{P}water)"/>'
               f'<rect width="{VW}" height="{VH}" fill="url(#{P}glow)"/>')
    # 2. sky and water engraving
    img, b = make_sky_water(moment, light, sun, years); out.append(img); sizes['sky+water'] = len(b)
    # 3. mountains
    top = min(y for _, y in summits) - 6
    img, b = kit.raster(lambda x, y: mountains.shade(x, y, years, light), 0, max(0, top), VW, HZ + 1); out.append(img); sizes['mountains'] = len(b)
    # 4. days, in slices that sway
    B = daysmod.BAND; n = daysmod.SLICES; dt = B['top'] - 8; sl = []
    for k in range(n):
        x0, x1 = B['x0'] + k * (B['x1'] - B['x0']) / n, B['x0'] + (k + 1) * (B['x1'] - B['x0']) / n
        img, b = kit.raster(lambda x, y: daysmod.shade(x, y, recent, light), x0, dt, x1, B['base'])
        sl.append(f'<g class="sway" style="transform-origin:{(x0 + x1) / 2:.1f}px {B["base"]}px;animation-delay:-{k * 1.7:.1f}s">{img}</g>')
        sizes[f'days{k}'] = len(b)
    days_svg = ''.join(sl)
    # 5. cast on the water
    img, b = kit.raster(lambda x, y: duck_at(x, y, light), 120, 400, 310, 446); out_cast = [img]; sizes['ducks'] = len(b)
    img, b = kit.raster(lambda x, y: friend('turtle', x, y, TURTLE), TURTLE[0] - 24, TURTLE[1] - 18, TURTLE[0] + 32, TURTLE[1] + 4); out_cast.append(img)
    kx, ky, ks = KOI
    img, b = kit.raster(lambda x, y: friend('koi', x, y, KOI), kx - 36 * ks, ky - 42 * ks, kx + 28 * ks, ky + 6 * ks); sizes['koi'] = len(b)
    ring_ink = hexc(light['ink'] if not night else light['hair'])
    out_cast.append(f'<g clip-path="url(#{P}koi)"><g class="koi">{img}</g></g>' + ''.join(
        f'<ellipse class="ring" cx="{kx - 12 * ks:.1f}" cy="{ky + 1:.1f}" rx="{a * ks:.1f}" ry="{bb * ks:.1f}" fill="none" stroke="{ring_ink}" '
        f'stroke-width=".9" style="animation-delay:{dl}s"/>' for a, bb, dl in ((12, 2.6, 0), (20, 4.2, .25))))
    defs += f'<clipPath id="{P}koi"><rect x="{kx - 40 * ks:.1f}" y="{ky - 60 * ks:.1f}" width="{70 * ks:.1f}" height="{60 * ks + 1.5:.1f}"/></clipPath>'
    # 6. fleet (months), placed around the title, the summits and each other
    title_box = (50, 40, 380, 108)
    keepouts = [title_box] + [(x - 22, y - 26, x + 22, y + 4) for x, y in summits if HZ - y > 8]
    placed = place_fleet(months, keepouts)
    fleet_svg, micro = [], []
    for i, (m, v, t, k) in enumerate(months):
        cap = f'{data.MON[m.month]} {m.year} · {v:,}'
        if not k:                                                      # parked on the far shore
            pw, ph = fleet.PARKED; px_, py_ = slot_x(i), HZ - ph / 2 - 1
            img, b = kit.raster(lambda x, y, px_=px_, py_=py_: fleet.parked(x - px_, y - py_, light), px_ - pw / 2 - 1, py_ - ph / 2 - 1, px_ + pw / 2 + 1, py_ + ph / 2 + 1)
            fleet_svg.append(img); micro.append((px_, HZ + 5, cap + ' · PARKED')); continue
        x, y, bx = placed[i]; w, h = fleet.SIZE[k]
        img, b = kit.raster(lambda xx, yy, k=k, x=x, y=y: fleet.shade(k, xx - x, yy - y, light), bx[0] - 1, bx[1] - 1, bx[2] + 1, bx[3] + 1)
        sizes[f'fleet{i}'] = len(b); parts = []
        for p in fleet.parts(k):
            u0, v0, u1, v1 = p['box']
            pimg, pb = kit.raster(lambda xx, yy, p=p, x=x, y=y: p['shade'](xx - x, yy - y, light), x + u0, y + v0, x + u1, y + v1)
            parts.append(f'<g class="{p["motion"]}" style="transform-origin:{x + p["pivot"][0]:.1f}px {y + p["pivot"][1]:.1f}px">{pimg}</g>')
        mot = fleet.MOTION.get(k)
        delay = f'animation-delay:-{(i * 1.9) % 11:.1f}s'
        fleet_svg.append(f'<g class="{mot or ""}" style="{delay}">{img}{"".join(parts)}</g>')
        micro.append((x, bx[3] + 4.5, cap))
    # 7. the cloud, in the emptiest sky
    boxes = [p[2] for p in placed.values() if p] + [(sx - sr, sy - sr, sx + sr, sy + sr)]
    cx, cy = place_cloud(boxes, title_box); s = CLOUD_SCALE
    img, b = kit.raster(lambda x, y: cloud_at((x - cx) / s, (y - cy) / s, light), cx - 122 * s, cy - 118 * s, cx + 124 * s, cy + 3 * s); sizes['cloud'] = len(b)
    cloud_svg = f'<g class="cloud">{img}</g>'
    if night:
        cloud_svg += ''.join(f'<text x="{cx + 70 * s + 12 * j:.1f}" y="{cy - 92 * s - 14 * j:.1f}" font-family="Geist Mono" font-size="{16 + 3 * j}" fill="{text_ink}" data-bg="{hexc(tint[0])}">z</text>' for j in range(3))
    # 8. night sky details
    stars = ''
    if night:
        for k2 in range(220):
            x = (k2 * 7919 + 13) % 1187 + 6.5; y = (k2 * 104729 + 7) % 997 / 997 * (HZ - 24) + 8
            if any(overlaps((x - 4, y - 4, x + 4, y + 4), o, 6) for o in boxes + [title_box]) or math.hypot(x - sx, y - sy) < sr + 60: continue
            r = .7 + (k2 * 31) % 9 / 9; tw = f' class="star" style="animation-delay:-{(k2 * .53) % 4:.2f}s"' if k2 % 3 == 0 else ''
            stars += (f'<path d="M{x:.1f} {y - 2.4 * r:.1f}L{x + .55 * r:.1f} {y - .55 * r:.1f}L{x + 2.4 * r:.1f} {y:.1f}L{x + .55 * r:.1f} {y + .55 * r:.1f}'
                      f'L{x:.1f} {y + 2.4 * r:.1f}L{x - .55 * r:.1f} {y + .55 * r:.1f}L{x - 2.4 * r:.1f} {y:.1f}L{x - .55 * r:.1f} {y - .55 * r:.1f}Z" fill="#e8eefb" fill-opacity="{.4 + .6 * ((k2 * 17) % 10) / 10:.2f}"{tw}/>')
            if stars.count('<path') >= 34: break
    # 9. text
    mono = 'font-family="Geist Mono" letter-spacing="1.6"'
    words = (f'<text x="64" y="76" font-family="Geist" font-size="34" letter-spacing="-.4" fill="{text_ink}" data-bg="{hexc(tint[0])}">Jake Parker</text>'
             f'<text x="65" y="102" {mono} font-size="16.5" fill="{text_ink}" data-bg="{hexc(mix(tint[0], tint[1], .3))}">{clock.LABEL[moment]} · LOS ANGELES</text>')
    for (yr, tot), (x, y) in zip(years, summits):
        words += f'<text x="{x:.1f}" y="{HZ + 19}" text-anchor="middle" {mono} font-size="16.5" fill="{text_ink}" data-bg="{hexc(tint[2])}">{yr}</text>'
    words += ''.join(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="Geist Mono" font-size="3.2" fill="{text_ink}" fill-opacity=".7" '
                     f'data-micro="1" aria-hidden="true">{c}</text>' for x, y, c in micro)
    title = f'Jake Parker: a lake engraved from GitHub contributions at {clock.LABEL[moment].lower()} in Los Angeles. Mountains are years, aircraft are months, the shore is days.'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}" role="img"><title>{title}</title>'
           f'<style>{kit.fonts()}</style><style>{MOTION_CSS}</style><defs>{defs}</defs>'
           f'<g clip-path="url(#{P}card)">{"".join(out)}{stars}{"".join(out_cast)}{days_svg}{"".join(fleet_svg)}{cloud_svg}</g>{words}</svg>')
    meta = dict(moment=moment, last=last.isoformat(), years=[dict(year=y, total=t, summit=[sx_, sy_]) for (y, t), (sx_, sy_) in zip(years, summits)],
                mountains=mountains.BAND, fleet=[dict(month=m.isoformat()[:7], total=v, tier=t, kind=k) for m, v, t, k in months],
                record_month=data.record_month(days_), days=dict(band=daysmod.BAND, counts=[c for _, c in recent], heights=daysmod.heights(recent)),
                sizes=sizes)
    return svg, meta

WHEN = datetime.datetime.now(clock.TZ)

def main():
    global WHEN
    ap = argparse.ArgumentParser()
    ap.add_argument('--moment', choices=clock.MOMENTS); ap.add_argument('--when'); ap.add_argument('--all', action='store_true')
    ap.add_argument('--data'); ap.add_argument('--out')
    a = ap.parse_args()
    if a.when: WHEN = datetime.datetime.fromisoformat(a.when).replace(tzinfo=clock.TZ)
    days_, last = data.load(a.data)
    moments = clock.MOMENTS if a.all else [a.moment or clock.moment(WHEN)]
    for m in moments:
        svg, meta = build(m, days_, last)
        if a.all: path = os.path.join(a.out or os.path.join(kit.ROOT, 'previews', 'world'), f'{m}.svg')
        else: path = a.out or os.path.join(kit.ROOT, 'assets', 'art.svg')
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        open(path, 'w').write(svg); json.dump(meta, open(os.path.splitext(path)[0] + '.json', 'w'))
        print(f'{m:8} {len(svg) // 1024:4} KB  -> {path}')

if __name__ == '__main__':
    main()
