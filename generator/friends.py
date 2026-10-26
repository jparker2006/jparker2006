"""Engraved lake friends: a turtle and a leaping koi (shapes from design round 3, variant B).

Each function takes local coordinates (units, waterline at y = 0) and returns an RGB colour or None.
"""
import math

NAVY, PAPER, WATER_INK = (25, 47, 88), (243, 238, 226), (24, 66, 104)
SHELL_INK, SHELL_PAPER = (118, 84, 34), (238, 216, 164); SKIN_INK, SKIN_PAPER = (78, 112, 70), (220, 230, 186)
KOI_INK, KOI_PAPER = (212, 116, 46), (252, 228, 194); FIN_PAPER = (247, 245, 238)
EYE_PAPER, BLUSH = (251, 249, 240), (236, 150, 130)
OUTLINE = .8                                        # fine navy outline (units), as on the cloud
BBOX = {'turtle': (-19, -15, 30, 2), 'koi': (-26, -40, 34, 5)}   # local bounding boxes (x0, y0, x1, y1)

def clamp(v, a=0., b=1.): return a if v < a else b if v > b else v
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
def line(phase, width, aa):
    d = abs(phase - math.floor(phase + .5))
    return clamp((width * .5 - d) / aa + .5)

def ell(x, y, cx, cy, a, b):
    """Approximate signed distance to an ellipse (negative inside)."""
    u, v = (x - cx) / a, (y - cy) / b
    k0 = math.hypot(u, v); k1 = math.hypot(u / a, v / b)
    return k0 * (k0 - 1) / k1 if k1 > 1e-9 else -min(a, b)
def cap(x, y, x1, y1, x2, y2, r):
    """Signed distance to a capsule (a stroke from x1,y1 to x2,y2 with radius r)."""
    dx, dy = x2 - x1, y2 - y1
    h = clamp(((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy))
    return math.hypot(x - x1 - dx * h, y - y1 - dy * h) - r
def smin(a, b, k):
    h = clamp(.5 + .5 * (b - a) / k); return b + (a - b) * h - k * h * (1 - h)
def lit(x, y, cx, cy, a, b):
    """Engraver's light from the upper left: 0 = lit, 1 = deep shade, for a rounded form."""
    nx, ny = (x - cx) / a, (y - cy) / b
    nz = math.sqrt(max(0., 1 - nx * nx - ny * ny))
    return clamp(.55 + .42 * nx + .62 * ny - .45 * nz)
def etch(d, t, ph, paper, ink, sp=1.6):
    """One engraved part: fine navy outline at its edge, line-halftone shading inside (line width = tone)."""
    if d > -OUTLINE: return mix(paper, NAVY, .85)
    c = line(ph / sp, clamp(t), .5 / sp)
    if t > .62: c = max(c, line((ph * .7 + 9) / (sp * 1.4), (t - .62) * 1.6, .5 / sp))   # cross-hatch in shade
    return mix(paper, ink, c)
def oval(x, y, cx, cy, rx, ry): return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
def arc(x, y, cx, cy, r, w, a0, a1):
    """Thin stroke along a circle between angles a0..a1 (radians, screen space, y down)."""
    a = math.atan2(y - cy, x - cx)
    return abs(math.hypot(x - cx, y - cy) - r) < w * .5 and a0 <= a <= a1

def hex_edge(x, y, r=5.4):
    """Distance to the nearest edge of a flat-top hexagon tiling (the turtle's scutes)."""
    w, h = 1.5 * r, math.sqrt(3) * r
    i0 = round(x / w); best = [9e9, 9e9]
    for i in (i0 - 1, i0, i0 + 1):
        off = h / 2 if i % 2 else 0; j0 = round((y - off) / h)
        for j in (j0 - 1, j0, j0 + 1):
            dd = math.hypot(x - i * w, y - off - j * h)
            if dd < best[0]: best = [dd, best[0]]
            elif dd < best[1]: best[1] = dd
    return (best[1] - best[0]) / 2

def turtle(x, y):
    x = -x                                                                  # mirrored: swims right, toward the summit
    hx, hy = -21, -6.5
    d = math.hypot(x - hx, y - hy) - 6
    if d < 0:                                                               # head, turned to face us
        if oval(x, y, hx - 2.3, hy - 1.1, 1.15, 1.6) or oval(x, y, hx + 2.1, hy - 1.1, 1.15, 1.6): return NAVY
        if abs(math.hypot(x - hx, y - hy + .2) - 2.5) < .5 and y > hy + 1.2: return NAVY
        if oval(x, y, hx - 4, hy + 2, 1.3, .75) or oval(x, y, hx + 3.9, hy + 2, 1.3, .75): return mix(SKIN_PAPER, BLUSH, .75)
        return etch(d, .14 + .4 * lit(x, y, hx, hy, 6, 6), -d, SKIN_PAPER, SKIN_INK, 1.3)
    if y > .6: return None                                                  # the rest is under water
    d = cap(x, y, -12, -.5, -18.5, -4.5, 3.3)
    if d < 0: return etch(d, .3 + .3 * lit(x, y, -15, -2, 5, 4), (x - y) * .7, SKIN_PAPER, SKIN_INK, 1.3)
    d = ell(x, y, 0, 1.5, 16, 12)
    if d < 0:                                                               # domed shell with scutes
        u, v = x / 16, (y - 1.5) / 12
        if d > -OUTLINE: return mix(SHELL_PAPER, NAVY, .85)
        seam = (abs(v + .28) * 12 < .5 or v < -.28 and hex_edge(x * (1 + .35 * u * u), y + 9.6) < .5
                or v > -.28 and min(abs(u - c) for c in (-.8, -.4, 0, .4, .8)) * 16 < .5)
        if seam: return mix(SHELL_PAPER, NAVY, .8)
        t = .2 + .5 * lit(x, y, 0, -4, 16, 9) + (.12 if v > -.3 else 0)
        return etch(d, t, -d, SHELL_PAPER, SHELL_INK, 1.4)
    return None

KOI_C, KOI_R, KOI_H, KOI_T = (14, 14), 40, math.radians(92), math.radians(140)
KOI_L = (KOI_T - KOI_H) * KOI_R
DROPS = [(-28, -6, 1.3), (-31.5, -1.5, 1), (-14, -4, 1.1), (-24, -11.5, .9), (-11, -9, .8), (-18, -1, .8)]
def koi(x, y):
    x = -x                                                                  # mirrored: faces left, toward the summit
    for dx, dy, r in DROPS:                                                 # splash droplets
        d = math.hypot(x - dx, y - dy) - r
        if d < 0: return mix(PAPER, WATER_INK, .8) if d > -.55 else EYE_PAPER
    rx, ry = x - KOI_C[0], y - KOI_C[1]
    L = (math.atan2(-ry, rx) - KOI_H) * KOI_R; n = math.hypot(rx, ry) - KOI_R     # along the spine, across it
    if L < -1 or L > KOI_L + 10: return None
    if L <= 7: w = 6.2 * math.sqrt(max(0., 1 - ((7 - L) / 7.2) ** 2))
    else: w = 6.2 * (1 - .78 * min(1., (L - 7) / (KOI_L - 7)) ** 1.4)
    if 0 <= L <= KOI_L and abs(n) < w:                                      # body
        d = abs(n) - w
        if L < .6: d = max(d, -L * 2)
        if oval(L, n, 4.2, 1.5, 1.25, 1.7): return NAVY                     # eye
        if abs(math.hypot(L - 3.4, n + .2) - 2.6) < .5 and n < -1.3 and L < 3.6: return NAVY   # smile
        if oval(L, n, 7, -2.3, 1.6, .9): return mix(EYE_PAPER, BLUSH, .75)
        if d > -OUTLINE: return mix(KOI_PAPER, NAVY, .85)
        t = .1 + .45 * clamp(.5 - n / w * .6)
        wob = .8 * math.sin(L * 1.3) + .5 * math.sin(n * 1.7 + L * .4)
        patch = (L > 1.4 and L < 6.8 and n > 2.2 + .12 * (L - 4) ** 2 + .4 * wob
                 or ((L - 14) / 5.2) ** 2 + ((n - 1.4) / 5.2) ** 2 + .18 * wob < 1
                 or ((L - 25) / 3.6) ** 2 + ((n - .6) / 3.2) ** 2 + .18 * wob < 1)
        if patch: return etch(d, t + .25, n, KOI_PAPER, KOI_INK, 1.4)
        return etch(d, t * .55, n, EYE_PAPER, NAVY, 1.4)
    if 9 <= L <= 21 and 0 < n - w < 4.6 * math.sin(math.pi * (L - 9) / 12):    # dorsal fin
        d = max(n - w - 4.6 * math.sin(math.pi * (L - 9) / 12), -(n - w)) * .7
        return etch(d, .32, L + .6 * (n - w), FIN_PAPER, KOI_INK, 1.5)
    if 6 <= L <= 11 and 0 < -n - w < 3.6 * math.sin(math.pi * (L - 6) / 5):    # pectoral fin
        d = (-n - w - 3.6 * math.sin(math.pi * (L - 6) / 5)) * .7
        return etch(d, .3, L - .6 * (n + w), FIN_PAPER, KOI_INK, 1.5)
    u = L - KOI_L                                                           # forked tail fan
    if 0 <= u <= 9.5 and abs(n) < 1.3 + u * .8 and not (u > 4.6 and abs(n) < (u - 4.6) * 1.05):
        d = max(abs(n) - 1.3 - u * .8, u - 9.5, -(abs(n) - (u - 4.6) * 1.05) if u > 4.6 else -9) * .8
        return etch(d, .3, math.atan2(n, u + 3) * 14, FIN_PAPER, KOI_INK, 1.5)
    return None
