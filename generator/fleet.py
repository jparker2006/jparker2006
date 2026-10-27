"""The fleet: one aircraft per month, bigger for busier months (docs/WORLD.md). Engraved like the airmail stamps of
the 1920s and 30s: fine outlines, bare-paper highlights, lines that run along each form, cross-hatching only in deep
shade. Side view, seen a touch from below, nose to the right (the fleet flies toward "now"). Keep this interface;
world.py relies on it.

    SIZE[kind] = (w, h)          box in art units, nose pointing right. Visual mass grows strictly with tier.
    ALTITUDE[kind] = y           cruising height of the craft's centre (art units, y down; the horizon is y = 300).
    MOTION[kind]                 how the whole craft moves: 'bob' (slow float), 'hover' (small jitter) or None.
    shade(kind, u, v, light)     -> (r, g, b) or None. Local coords: (0, 0) = box centre, u to the right, v down.
    parts(kind)                  -> [dict(name, box=(u0, v0, u1, v1), pivot=(u, v), motion, shade=fn(u, v, light))]
                                    separately animated pieces drawn on top: 'spin-y' (propeller seen from the side,
                                    flickers by scaling along y), 'spin-x' (rotor seen from the side, scales along x)
                                    or 'spin' (tail rotor seen face on, turns about pivot).
    PARKED = (w, h); parked(u, v, light) -> colour or None   a month with no contributions: a shut hangar and a limp
                                    windsock on the far shore (box centre; the ground is v = h / 2).

Everything is drawn with tone (0 lit .. 1 shade) through ink() / kit.engrave(), so every moment works, and night
becomes a white-line print. Gold only for warm light: burner flame, lit windows at low sun and night, night nav lights.
Each craft wears a golden-age livery (LIVERY) printed under the lines from kit.PIGMENTS: decoration only, never data.
"""
import math
import kit
from kit import clamp, mix, line, q, S
from data import KINDS

SIZE = dict(paper_plane=(18, 8), drone=(24, 12), helicopter=(44, 20), prop_plane=(54, 23), private_jet=(70, 18),
            balloon=(40, 56), airliner=(120, 34), blimp=(140, 40), airship=(210, 56))
ALTITUDE = dict(paper_plane=274, drone=252, helicopter=230, prop_plane=210, balloon=196, blimp=150, private_jet=118,
                airliner=84, airship=60)
MOTION = dict(drone='hover', balloon='bob', blimp='bob', airship='bob')
PARKED = (22, 11)
OW = .8                                            # outline width (units)

# ------------------------------------------------------------------ ink
def cover(ph, w, sp):
    """Ink coverage of a pixel by lines of width w (fraction of the period sp) at integer phase: a box filter over the
    pixel, so thin lines on a slant stay even instead of breaking into dashes."""
    d = abs(ph / sp - math.floor(ph / sp + .5)); h = .5 / S / sp
    return clamp((min(d + h, w / 2) - max(d - h, -w / 2)) / (2 * h)) + clamp((min(1 - d + h, w / 2) - (1 - d - h)) / (2 * h))
def ink(t, ph, L, sp=2., ph2=None, base=None):
    """Engraved tone t along lines of phase ph; by day, cross-hatching along ph2 where the shade is deep. At night the
    print flips to pale lines on navy, like kit.engrave(). base = the livery colour printed under the lines."""
    t = clamp(t)
    if base: t *= PAINT_T                          # painted areas carry less ink, so the colour shows through the lines
    if L['night']:
        if base is None and NIGHT_BODY[0]:                          # after dark the whole body glows in its livery colour
            base = NIGHT_BODY[0]; t = (1 - t) * .56
        else: t = (1 - t) * (PAINT_N if base else .72)
    c = cover(ph, t, sp)
    if ph2 is not None and t > .62 and not L['night']: c = max(c, cover(ph2, (t - .62) * 1.7, sp))
    return mix(base or L['paper'], L['ink'], q(clamp(c)))
def edge(L): return kit.outline(L)
def faint(L): return mix(L['paper'], L['ink'], .5)
def low(L): return not L['night'] and abs(L['sun'][1]) < .45              # dawn, golden hour, dusk: warm light
def rim(L, nx, ny): return low(L) and nx * L['sun'][0] + ny * L['sun'][1] > .5
def glass(L, ph, t=.86, lit=True):
    """Window glass: dark with the sky in it by day; warm glints at low sun; lit cabins at night (lit=False for a
    cockpit canopy, which stays dark at night)."""
    if L['night']: return L['gold'] if lit else L['paper']
    if low(L): return mix(L['gold'], L['paper'], .25)
    return ink(t, ph, L, 1.4)
NAV = dict(red=(255, 96, 84), green=(96, 232, 150), white=(255, 248, 232))
def nav(L, colour='red'):
    """Navigation lights, night only, in real aircraft colours: red beacons, green on the starboard side we see."""
    return NAV[colour] if L['night'] else None
def nacelle(u0, u1, cy, R):
    """An engine pod: rounded intake lip at the front (right), tapering exhaust behind."""
    n = u1 - u0
    def r(u):
        s = clamp((u - u0) / n)
        return R * (.62 + .38 * s ** .45) * max(0., 1 - (2 * s - 1) ** 10) ** .35
    return Hull(u0, u1, r, lambda u: cy)

# ------------------------------------------------------------------ livery (decoration only: every kind reads by its shape)
# Golden-age liveries printed under the engraving, like the colour plate of a bicolour airmail stamp: cheatlines along
# the fuselage, coloured tails and fins, bold gores. Pigments come through kit.pigment(), which quiets them at night.
# Each livery pairs a mid pigment with a light one (or cream), so the parts stay distinct in grey too.
LIVERY = dict(paper_plane=('vermilion', 'sky'), drone=('marigold', 'vermilion'), helicopter=('coral', 'cream'),
              prop_plane=('sky', 'marigold', 'vermilion'), private_jet=('plum', 'rose'), balloon=('vermilion', 'marigold', 'sky'),
              airliner=('vermilion', 'marigold'), blimp=('leaf', 'marigold'), airship=('sky', 'marigold', 'vermilion'),
              hangar=('vermilion', 'sky'))
PAINT_T, PAINT_N = .8, .26      # ink on painted areas by day (x tone), and the pale lines on them at night (x tone)
def paint(kind, i, L, a=1.):
    if L['night']:                # lit after dark, like a night airshow: the liveries keep their colour on the navy sky
        return mix(L['paper'], mix(kit.PIGMENTS[LIVERY[kind][i]], L['paper'], .12), a)
    return kit.pigment(LIVERY[kind][i], L, a)
def cream(L): return kit.pigment('cream', L)
def band(sn, a, b): return a <= sn <= b
def warmish(L, base, tone, ph, sp=2.2):
    """Warm burner light on a painted surface (night): the gold engraving over the livery colour."""
    return kit.warm(tone, ph, L, sp, mix(base, L['gold'], .35))

# ------------------------------------------------------------------ shapes
class Hull:
    """A body of revolution seen from the side (fuselage, envelope, nacelle): radius r(u) about centre line c(u)."""
    def __init__(s, u0, u1, r, c=lambda u: 0.):
        s.u0, s.u1, s.r, s.c = u0, u1, r, c
        s.R = max(r(u0 + (u1 - u0) * i / 80) for i in range(81))
        s.box = (u0, min(c(u0 + (u1 - u0) * i / 40) - r(u0 + (u1 - u0) * i / 40) for i in range(41)),
                 u1, max(c(u0 + (u1 - u0) * i / 40) + r(u0 + (u1 - u0) * i / 40) for i in range(41)))
    def at(s, u, v):
        """-> (d, nx, ny, sn, r): signed distance, surface normal (x, y), sine of the angle around the axis, radius."""
        if not (s.u0 < u < s.u1 and s.box[1] - 1 < v < s.box[3] + 1): return 9., 0., 0., 0., 0.
        h = .06; a, b = max(u - h, s.u0), min(u + h, s.u1)
        r, c = s.r(u), s.c(u); dr = (s.r(b) - s.r(a)) / (b - a); dc = (s.c(b) - s.c(a)) / (b - a)
        dy = v - c
        d = (abs(dy) - r) / math.hypot(1, min(40, abs(dc + (dr if dy >= 0 else -dr))))
        d = max(d, s.u0 - u, u - s.u1)
        sn = clamp(dy / r, -1, 1) if r > 1e-6 else 0.
        n = math.hypot(1, dc * sn + dr)
        return d, -(dc * sn + dr) / n, sn / n, sn, r

def along(H, sn, r, k=.5):
    """Hatch phase for lines that run along a hull and gather toward its ends and its limbs, like meridians seen from
    the side; the gathering is capped so the lines never get finer than the raster can hold."""
    return (sn + .12 * sn * sn * sn) * min(H.R * k + r * (1 - k), r * 1.6)

def hull_ink(H, u, v, L, g, sp=2., dark=0., k=.5, rimw=1.2, base=None):
    d, nx, ny, sn, r = g
    if d > -OW: return edge(L)
    if d > -OW - rimw and rim(L, nx, ny): return kit.warm(.7, u, L)
    t = .04 + .9 * kit.form(nx, ny, L) + dark
    return ink(t, along(H, sn, r, k), L, sp, u * .6 + v * .8, base)

def poly_box(pts, m=1.): return (min(p[0] for p in pts) - m, min(p[1] for p in pts) - m, max(p[0] for p in pts) + m, max(p[1] for p in pts) + m)
def inb(b, u, v): return b[0] <= u <= b[2] and b[1] <= v <= b[3]
def plate(pts, t, ph_dir, sp=2., paint=None):
    """A flat part (wing, fin, strut): polygon, tone fn(u, v, L) or number, hatch direction (a, b) -> phase a*u + b*v.
    paint = livery colour under the lines: fn(u, v, L) -> colour or None."""
    bx = poly_box(pts); a, b = ph_dir
    def f(u, v, L):
        if not inb(bx, u, v): return None
        d = kit.poly(u, v, pts)
        if d > 0: return None
        if d > -OW: return edge(L)
        tt = t(u, v, L) if callable(t) else t
        base = paint(u, v, L) if paint else None
        return ink(tt, a * u + b * v, L, sp, a * v - b * u, base)
    return f
def wire(x1, y1, x2, y2, r=.42, col=edge):
    bx = (min(x1, x2) - r - 1, min(y1, y2) - r - 1, max(x1, x2) + r + 1, max(y1, y2) + r + 1)
    def f(u, v, L):
        if not inb(bx, u, v) or kit.cap(u, v, x1, y1, x2, y2, r) > 0: return None
        return col(L)
    return f
def first(layers, u, v, L):
    for f in layers:
        c = f(u, v, L)
        if c is not None: return c
    return None
def smooth(a, b, x): t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ 1. paper plane: a folded dart, nose up a touch
PP_WING = [(-8.7, -3.5), (8.6, .2), (-7.2, -.9)]
PP_KEEL = [(-7.2, -.9), (8.6, .2), (-5.6, 3.5)]
def paper_plane(u, v, L):
    ca, sa = math.cos(.07), math.sin(.07); u, v = u * ca - v * sa, u * sa + v * ca     # tilt nose up
    for pts, t, dirn in ((PP_WING, .02, (-.2, 1)), (PP_KEEL, .42, (.24, 1))):
        d = kit.poly(u, v, pts)
        if d <= 0:
            if d > -.65: return edge(L)
            if pts is PP_WING:                          # folded from airmail paper: red and blue chevrons along the edge
                base = paint('paper_plane', int((u + 1.6 * v + 40) / 2.4) % 2, L) if kit.cap(u, v, -8.7, -3.5, 8.6, .2, 0) < 1.9 else paint('paper_plane', 1, L, .3)
            else: base = paint('paper_plane', 0, L, .85)
            return ink(t + (.25 * clamp((-u - 2) / 6) if t > .1 else 0), dirn[0] * u + dirn[1] * v, L, 1.5, base=base)
    return None

# ------------------------------------------------------------------ 2. drone: quadcopter, two rotors in view
def drone(u, v, L):
    # gimbal camera
    d = math.hypot(u - 1.2, v - 2.5) - 1.5
    if d < 0:
        if d > -.6: return edge(L)
        if math.hypot(u - 1.7, v - 2.3) < .45: return L['paper'] if not L['night'] else edge(L)
        return ink(.7, v, L, 1.2)
    # legs and skids
    for x in (-1, 1):
        if kit.cap(u, v, 2.4 * x, .8, 3.4 * x, 4.9, .38) < 0 or kit.cap(u, v, 2.2 * x, 4.9, 4.6 * x, 4.9, .38) < 0: return edge(L)
    # body shell
    d = kit.box(u, v, 0, -.4, 4.6, 1.9, 1.6)
    if d < 0:
        if d > -.6: return edge(L)
        if 4.6 > u > 2.4 and -1.6 < v < -.4 and nav(L): return nav(L, 'green')
        base = paint('drone', 1 if abs(v + .1) < .55 else 0, L)              # a vermilion stripe round the shell
        return ink(.06 + .7 * kit.form(u / 5, (v + .4) / 2.2, L), v, L, 1.3, base=base)
    # arms and motors
    for x in (-1, 1):
        d = kit.box(u, v, 9 * x, -2.9, 1, 1.15, .4)
        if d < 0: return edge(L) if d > -.55 else ink(.4, v, L, 1.2, base=paint('drone', 1, L))
        if kit.cap(u, v, 1.5 * x, -1.1, 9 * x, -2.6, .62) < 0: return edge(L)
    return None

def rotor_part(cx, cy, half, thick=.42, disc=.0):
    """A rotor seen from the side: a long thin blade and a faint swept disc (motion spin-x)."""
    def f(u, v, L):
        if kit.cap(u, v, cx - half, cy, cx + half, cy, thick) < 0: return edge(L)
        if disc and kit.ell(u, v, cx, cy, half, disc) < 0 and line(u / 1.6, .35, .3) > .5: return faint(L)
        if math.hypot(u - cx, v - cy - .3) < .75: return edge(L)
        return None
    return f
def prop_part(cx, cy, half, thick=.55):
    """A propeller seen from the side: a blade across a faint disc, hub on the axis (motion spin-y)."""
    def f(u, v, L):
        if abs(v - cy) < half and abs(u - cx) < thick * (1 - .55 * ((v - cy) / half) ** 2): return edge(L)
        if kit.ell(u, v, cx, cy, thick * 1.6, half) < 0 and line(v / 1.4, .3, .3) > .5: return faint(L)
        return None
    return f
def disc_part(cx, cy, rad):
    """A tail rotor seen face on: two crossed blades and a faint rim (motion spin)."""
    def f(u, v, L):
        x, y = u - cx, v - cy; rr = math.hypot(x, y)
        if rr > rad: return None
        if rr < .7: return edge(L)
        if kit.cap(x, y, -rad * .92, -rad * .3, rad * .92, rad * .3, .32) < 0: return edge(L)
        if rr > rad - .45: return faint(L)
        return None
    return f

# ------------------------------------------------------------------ 3. helicopter: light helicopter, glazed cabin
def _heli_r(u):
    cab = 4.9 * math.sqrt(max(0., 1 - ((u - 2.6) / 8.4) ** 2)) if -5.8 < u < 11 else 0
    boom = .75 + 1.3 * clamp((u + 20) / 15) ** 1.4 if u < -2 else 0
    return max(cab, boom) if abs(cab - boom) > 1.2 else (cab + boom + math.sqrt((cab - boom) ** 2 + .3)) / 2
def _heli_c(u): return -2.9 * (1 - smooth(-12, -2.5, u)) - .2
HELI = Hull(-20.2, 11, _heli_r, _heli_c)
HELI_FIN = [(-16.6, -3.6), (-19.6, -8.6), (-21.4, -8.4), (-20.6, -3.0)]
HELI_STAB = [(-13.6, -2.4), (-12.4, -2.2), (-14.4, -.4), (-15.8, -.4)]
HELI_LAYERS = [
    plate(HELI_STAB, .4, (.4, 1), 1.5, lambda u, v, L: paint('helicopter', 0, L)),
    wire(-6.6, 7.7, 8.4, 7.7, .55), wire(8.4, 7.7, 10.4, 6.5, .5), wire(-3.4, 3.8, -4.4, 7.6, .4), wire(4.8, 4.2, 5.6, 7.6, .4),
]
HELI_BACK = [plate(HELI_FIN, lambda u, v, L: .18 + .3 * clamp((v + 3) / -6), (.1, 1), 1.5, lambda u, v, L: paint('helicopter', 0, L)),
             wire(.8, -5.4, .8, -8.2, .5)]
def helicopter(u, v, L):
    c = first(HELI_LAYERS, u, v, L)
    if c: return c
    g = HELI.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        # bubble canopy: front of the cabin above the skid line
        cw = u - 3.2 + .5 * (v + 1.2)
        if cw > 0 and v < 1.2:
            if cw < .6 or v > .6: return edge(L)
            if abs((u + v * .8) - 6.4) < .5: return L['paper'] if not L['night'] else faint(L)         # reflection
            return glass(L, v, .9, lit=False)
        db = kit.box(u, v, -.8, -1.8, 1.9, 1.6, .9)
        if db < 0: return edge(L) if db > -.55 else glass(L, v, .8, lit=False)
        if abs(v - 2.7) < .3 and -5 < u < 6: return faint(L)                  # belly panel line
        sn = g[3]
        base = paint('helicopter', 1, L) if band(sn, .1, .42) or -17 < u < -14.6 else paint('helicopter', 0, L)          # cheatline, boom band
        return hull_ink(HELI, u, v, L, g, 1.6, base=base)
    c = first(HELI_BACK, u, v, L)
    if c: return c
    d = kit.box(u, v, .4, -5.0, 3.6, 1.2, 1)                                 # engine fairing
    if d < 0: return edge(L) if d > -OW else ink(.1 + .5 * clamp((v + 5) / 2), v, L, 1.5, base=paint('helicopter', 0, L))
    if nav(L) and math.hypot(u + 21, v + 8.5) < .8: return nav(L, 'red')
    return None

# ------------------------------------------------------------------ 4. prop plane: an airmail biplane
def _bi_r(u):
    if u > 13: return 3.7 * math.sqrt(max(0., 1 - ((u - 13) / 6.4) ** 4))
    return .8 + 2.9 * clamp((u + 25) / 38) ** .7
def _bi_c(u): return -1.3 * (1 - clamp((u + 25) / 38)) ** 1.5
BI = Hull(-25, 19.4, _bi_r, _bi_c)
BI_TOP = Hull(-3.6, 12, lambda u: 1.05 * math.sqrt(max(0., 1 - ((u - 8.4) / 3.6) ** 2)) if u > 8.4 else 1.05 * (.35 + .65 * (1 - ((8.4 - u) / 12) ** 2)), lambda u: -8.6)
BI_LOW = Hull(-4.6, 10.6, lambda u: 1. * math.sqrt(max(0., 1 - ((u - 7.4) / 3.2) ** 2)) if u > 7.4 else (.35 + .65 * (1 - ((7.4 - u) / 12) ** 2)), lambda u: 3.6)
BI_FIN = [(-18.6, -2.2), (-22.2, -7.6), (-25.4, -7.8), (-26.4, -6.4), (-26.4, -1.2)]
BI_STAB = [(-17.6, -1.4), (-25.4, -1.6), (-26.6, .2), (-21, .3)]
BI_STRUTS = [wire(-1.2, -7.6, -.6, 2.8, .5), wire(8.2, -7.6, 7.6, 2.8, .5), wire(1.8, -7.7, 3.4, -3.4, .38), wire(6.4, -7.7, 5, -3.6, .38),
             wire(-.9, -7.2, 7.8, 2.4, .22), wire(7.9, -7.2, -.9, 2.4, .22)]
BI_STAB_P = plate(BI_STAB, .4, (.1, 1), 1.5, lambda u, v, L: paint('prop_plane', 1, L))
BI_GEAR = [wire(9.4, 3.2, 10.6, 8.2, .42), wire(13.6, 2.4, 10.6, 8.2, .42), wire(-23, 1.2, -24.6, 2.8, .4)]
def wing_ink(H, u, v, L, g, sp=1.5, base=None):
    d, nx, ny, sn, r = g
    if d > -.6: return edge(L)
    t = .06 + .8 * kit.form(nx * .4, ny * .9, L)
    return ink(t, v * 1.6 + u * .02, L, sp, u, base)
def prop_plane(u, v, L):
    # wheel
    dw = math.hypot(u - 10.6, v - 8.4) - 2.6
    if dw < 0:
        if dw > -.65 or math.hypot(u - 10.6, v - 8.4) < .7: return edge(L)
        if dw > -1.3: return ink(.75, math.atan2(v - 8.4, u - 10.6) * 4, L, 1.2)          # tyre
        return ink(.12 + .5 * clamp((v - 7) / 3), v, L, 1.3)
    c = first(BI_GEAR, u, v, L)
    if c: return c
    g = BI_LOW.at(u, v)
    if g[0] < 0: return wing_ink(BI_LOW, u, v, L, g, base=paint('prop_plane', 1, L))
    c = first(BI_STRUTS, u, v, L)
    if c: return c
    g = BI.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        if u > 13.6:                                                            # engine cowling, ribbed
            if abs(u - 13.6 - .5) < .45: return edge(L)
            return ink(.12 + .8 * kit.form(0, g[2], L), v * 1.3 + 2 * math.sin(u), L, 1.4, u * 2)
        if -4.4 < u < .4 and v < -2.2: return edge(L) if v > -2.75 else ink(.85, u, L, 1.2)            # cockpit opening
        if abs(u + 6.8) < .22 and v > -2.4 or abs(u - 12.7) < .22: return faint(L)                    # panel lines
        return hull_ink(BI, u, v, L, g, 1.6, base=paint('prop_plane', 0, L))
    c = first([BI_STAB_P], u, v, L)
    if c: return c
    d = kit.poly(u, v, BI_FIN)
    if d < 0:                                                                   # fin and striped rudder
        if d > -OW or abs(u + 22.3 + .1 * v) < .3: return edge(L)
        stripe = u < -22.3 - .1 * v and int((u + 26.6) / 1.35) % 2 == 0
        return ink(.12, u * .1 + v, L, 1.4, u, paint('prop_plane', 2, L) if stripe else cream(L))
    g = BI_TOP.at(u, v)
    if g[0] < 0: return wing_ink(BI_TOP, u, v, L, g, base=paint('prop_plane', 1, L))
    if math.hypot(u - 20.3, v) < 1.4: return edge(L) if math.hypot(u - 20.3, v) > .7 else faint(L)  # spinner
    return None

# ------------------------------------------------------------------ 5. private jet: tip tanks, rear engines, T-tail
def _jet_r(u):
    if u > 22: return 3.3 * (1 - ((u - 22) / 12.6) ** 1.9) ** .55 if u < 34.6 else 0
    if u > -14: return 3.3
    t = (-14 - u) / 18; return .55 + 2.75 * (1 - t ** 1.6) ** .9
def _jet_c(u):
    if u > 22: return .9 * ((u - 22) / 12.6) ** 2
    if u > -14: return 0
    return -1.9 * ((-14 - u) / 18) ** 1.4
JET = Hull(-32, 34.6, _jet_r, _jet_c)
JET_ENG = nacelle(-22.6, -12.4, -2.7, 2.15)
JET_FIN = [(-18.8, -2.6), (-27.6, -9.4), (-31.8, -9.4), (-30.6, -1.4)]
JET_STAB = [(-26.6, -9.6), (-33.6, -8.6), (-33.4, -8.0), (-28.4, -8.2)]
JET_WING = [(11, 2.4), (-.6, 6.2), (-5, 6.2), (-3.4, 2.8)]
JET_TANK = Hull(-6.6, 3.6, lambda u: 1.1 * math.sqrt(max(0., 1 - ((u + 1.5) / 5.1) ** 2)), lambda u: 6.6)
def private_jet(u, v, L):
    g = JET_TANK.at(u, v)
    if g[0] < 0:
        if nav(L) and u > 2.6: return nav(L, 'green')
        return hull_ink(JET_TANK, u, v, L, g, 1.4, rimw=.6, base=paint('private_jet', 1, L))
    c = first([plate(JET_WING, lambda u, v, L: .3 + .3 * clamp((v - 2) / 4), (.33, 1), 1.5)], u, v, L)
    if c: return c
    g = JET_ENG.at(u, v)
    if g[0] < 0:
        if g[0] > -OW or abs(u + 19.4) < .22: return edge(L)
        if u > -13.6: return ink(.75, v, L, 1.2)                                # intake lip
        return hull_ink(JET_ENG, u, v, L, g, 1.5, base=paint('private_jet', 0, L))
    g = JET.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        if 25.4 < u < 29.6 and -3 + (u - 25.4) * .38 < v < -1:                                         # windscreen
            return edge(L) if v > -1.5 or u > 29.1 else glass(L, u - v)
        wx = (u + 7.6) % 3.6 - 1.8
        if -8 < u < 20 and (wx / 1.) ** 2 + ((v + .9) / .78) ** 2 < 1: return glass(L, u - v)          # cabin windows
        if abs(u - 22.6) < .2 and -2.6 < v < 1.6: return faint(L)                                        # door
        sn = g[3]                                                                                         # cheatline and pinstripe
        base = paint('private_jet', 0, L) if band(sn, .06, .46) else paint('private_jet', 1, L) if band(sn, .56, .72) else None
        return hull_ink(JET, u, v, L, g, 1.7, base=base)
    for pts, t in ((JET_STAB, .45), (JET_FIN, None)):
        dd = kit.poly(u, v, pts)
        if dd < 0:
            if dd > -OW or (t is None and abs(u + 29.4 + .1 * (v + 5)) < .22): return edge(L)
            if nav(L) and t is None and v < -8.2 and u < -30: return nav(L, 'red')
            return ink(t * .8 if t else .1 + .24 * clamp((-2 - v) / 7), v, L, 1.5, u, paint('private_jet', 1 if t else 0, L))
    return None

# ------------------------------------------------------------------ 6. hot air balloon: striped gores, gold burner
B_CY, B_R, B_TH = -11.5, 18.5, 12.6               # sphere centre and radius, the throat level
def _bal_w(v):
    """Half-width of the envelope at height v."""
    if v < B_CY + 6: return math.sqrt(max(0., B_R * B_R - (v - B_CY) ** 2))
    p0, m0 = math.sqrt(B_R * B_R - 36), -6 / math.sqrt(B_R * B_R - 36); p1, m1 = 4.6, -.18; Ln = B_TH - B_CY - 6
    s = clamp((v - B_CY - 6) / Ln); s2, s3 = s * s, s * s * s
    return (2 * s3 - 3 * s2 + 1) * p0 + (s3 - 2 * s2 + s) * Ln * m0 + (-2 * s3 + 3 * s2) * p1 + (s3 - s2) * Ln * m1
BAL_V0 = B_CY - B_R
def balloon(u, v, L):
    # basket
    d = kit.box(u, v, 0, 24.6, 3.5, 2.9, .7)
    if d < 0:
        if d > -.6: return edge(L)
        if abs(v - 22.6) < .55: return ink(.7, u, L, 1.2)                      # rim
        weave = line((v + .6 * (int((u + 9) / 1.2) % 2)) / 1.2, .45, .3); wick = kit.pigment('marigold', L, .45)
        return mix(ink(.3 + .4 * clamp((u + 3.5) / 7), v * 1.6, L, 1.2, base=wick), edge(L), .5 * weave) if not L['night'] else ink(.5 - .3 * weave, v * 1.6, L, 1.2, base=wick)
    # burner and flame (the warm light)
    fy = v - 16.6
    if abs(u) < 2 and 19.2 < v < 21.6: return edge(L) if abs(v - 19.4) < .4 or abs(u) > 1.3 or v > 21.2 else ink(.6, v, L, 1)
    fw = 1.7 * clamp((fy + 3.4) / 3.4) ** .6 * clamp((2.6 - fy) / 2.6) ** .9
    if abs(u) < fw and -3.4 < fy < 2.6:
        return mix(L['gold'], L['paper'], .55 * clamp(1 - abs(u) / fw * 1.4) * clamp(1 - abs(fy) / 2.5)) if not L['night'] else mix(L['gold'], (255, 246, 214), .5 * clamp(1 - abs(u) / fw))
    # cables
    for x in (-1, 1):
        if kit.cap(u, v, 4.4 * x, B_TH + .8, 3.2 * x, 22, .3) < 0 or kit.cap(u, v, 1.5 * x, B_TH + .9, 1.1 * x, 22, .22) < 0: return edge(L)
    # skirt (scoop under the throat)
    if B_TH - .2 < v < B_TH + 1.9 and abs(u) < 4.9 - .25 * (v - B_TH):
        if abs(u) > 4.2 - .25 * (v - B_TH) or v > B_TH + 1.4: return edge(L)
        return ink(.6, u * .3 + v, L, 1.2, base=paint('balloon', 2, L)) if not L['night'] else kit.warm(.5, v, L)
    # envelope
    if not BAL_V0 - 1 < v < B_TH + 1: return None
    w = _bal_w(v); d = max(abs(u) - w, BAL_V0 - v, v - B_TH)
    if d > 0: return None
    wn = _bal_w(v + .1); dw = (wn - w) / .1
    d = max((abs(u) - w) / math.hypot(1, dw), BAL_V0 - v, v - B_TH)
    if d > -OW: return edge(L)
    sn = clamp(u / max(w, 1e-6), -1, 1); psi = math.asin(sn)
    gore = psi / (math.pi / 10) + 5                                            # ten gores across the visible face
    seam = abs(gore - round(gore)) * w * math.cos(psi) * math.pi / 10
    if seam < .32 and v > BAL_V0 + 1.5: return faint(L) if v < B_TH - .6 else edge(L)
    n = math.hypot(1, dw); nx, ny = sn / n, -dw / n
    if rim(L, nx, ny) and d > -OW - 1.4: return kit.warm(.7, v, L)
    t = .03 + .7 * kit.form(nx * .95, ny * .95, L) + (.08 if int(gore) % 2 else 0)
    base = paint('balloon', int(gore) % 2, L)                                  # bold alternating gores
    if v < BAL_V0 + 4.2 or abs(v - (B_CY + 9.5)) < 1.3: base = paint('balloon', 2, L)   # crown panel, a band round the belly
    lat = v + .5 * w * (1 - math.cos(psi)) * (1 if v > B_CY else -.4)          # latitudes around the envelope
    if L['night'] and v > B_CY + 4:                                            # the burner lights the envelope from inside
        glow = clamp((v - B_CY - 4) / 18) * (1 - .5 * abs(sn))
        if glow > .15: return warmish(L, base, glow * .9, v + .4 * w * (1 - math.cos(psi)), 2)
    return ink(t, lat, L, 1.8, u * .7 - v * .7, base)

# ------------------------------------------------------------------ 7. jet airliner: four engines, cheatline, swept tail
def _al_r(u):
    if u > 46: return 5.4 * (1 - ((u - 46) / 12.4) ** 2.1) ** .5 if u < 58.4 else 0
    if u > -30: return 5.4
    t = (-30 - u) / 27.4; return .7 + 4.7 * (1 - min(1, t) ** 1.7) ** .8
def _al_c(u):
    if u > 46: return -.3 + 1.6 * ((u - 46) / 12.4) ** 2
    if u > -30: return -.3
    return -.3 - 3.5 * min(1, (-30 - u) / 27.4) ** 1.5
AL = Hull(-57.4, 58.4, _al_r, _al_c)
AL_ENG = [nacelle(-11.6, -1.8, 12.4, 2.), nacelle(2.6, 13.6, 8.0, 2.3)]
AL_PYL = [[(-7, 10.2), (-1.4, 9.6), (-2.6, 7.6), (-7.2, 9)], [(6, 5.6), (12.6, 5.4), (9.8, 3.8), (5.6, 4.6)]]
AL_WING = [(15, 3.4), (-13.4, 13.6), (-18.4, 13.8), (-17.6, 12.6), (-9, 4.2)]
AL_STAB = [(-41.4, -2.8), (-51, .8), (-55, .9), (-54, -3.4)]
AL_FIN = [(-37.6, -5.2), (-49.8, -16.6), (-55.2, -16.6), (-56.4, -4.0)]
def airliner(u, v, L):
    for H in AL_ENG:
        g = H.at(u, v)
        if g[0] < 0:
            if g[0] > -OW: return edge(L)
            if u > H.u1 - 1.2: return ink(.8, v, L, 1.3)                         # intake lip in shade
            if abs(u - H.u0 - 3.4) < .22: return faint(L)                          # fan cowl line
            return hull_ink(H, u, v, L, g, 1.6, rimw=.8)
    for pts in AL_PYL:
        d = kit.poly(u, v, pts)
        if d < 0: return edge(L) if d > -.6 else ink(.6, v, L, 1.4)
    d = kit.poly(u, v, AL_WING)
    if d < 0:
        if d > -OW: return edge(L)
        if nav(L) and u < -16 and v > 12: return nav(L, 'green')
        if abs(-.34 * u + v - 5.4 - (-.34 * -8.6)) < .25 and v > 5: return faint(L)   # flap line
        return ink(.42 + .32 * clamp((v - 4) / 9), .32 * u + v, L, 1.8, u - .3 * v)
    d = kit.poly(u, v, AL_STAB)
    if d < 0: return edge(L) if d > -OW else ink(.5, .3 * u + v, L, 1.6, u)
    g = AL.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        c = _al_c(u)
        if 51 < u < 55.4 and c - 2.9 + (u - 51) * .2 < v < c - 1.4: return edge(L) if v > c - 1.8 else glass(L, u - v)   # cockpit
        if -40 < u < 47 and abs(v - c + 1.5) < .55 and (u + 60) % 2.4 < .95: return glass(L, u - v, .8)                 # windows
        if any(abs(u - x) < .2 for x in (45, 25, -36)) and abs(v - c + .5) < 3.2: return faint(L)                       # doors
        if nav(L) and math.hypot(u - 2, v - c + 5.6) < .9: return nav(L, 'red')                                               # beacon
        sn = g[3]                                                                                                       # cheatline, pinstripe
        base = paint('airliner', 0, L) if band(sn, -.56, -.06) else paint('airliner', 1, L) if band(sn, .04, .2) else None
        return hull_ink(AL, u, v, L, g, 2., k=.6, base=base)
    d = kit.poly(u, v, AL_FIN)
    if d < 0:
        if d > -OW or abs(u + 52 + .2 * (v + 10)) < .22: return edge(L)                                                  # rudder hinge
        sweep = abs(v + 12.2 + .55 * (u + 47)) < 1.9                                                                      # livery sweep
        return ink(.1 + .24 * clamp((-5 - v) / 12), v, L, 1.7, u, paint('airliner', 1 if sweep else 0, L))
    return None

# ------------------------------------------------------------------ 8. blimp: soft envelope, cruciform tail, gondola
BL_C = -4.
def _bl_r(u):
    if u >= 16: return 15.2 * max(0., 1 - ((u - 16) / 52) ** 2.2) ** .5
    t = (16 - u) / 84; return 15.2 * max(0., 1 - t ** 1.9) ** .62
BLIMP = Hull(-68, 68, _bl_r, lambda u: BL_C)
def _top(H, u): return H.c(u) - H.r(u)
def _bot(H, u): return H.c(u) + H.r(u)
BL_UFIN = [(-40, _top(BLIMP, -40) + 1.4), (-55, -19.6), (-63.6, -19.6), (-65.6, _top(BLIMP, -65.6) + .8)]
BL_LFIN = [(-40, _bot(BLIMP, -40) - 1.4), (-55, 11.6), (-63.6, 11.6), (-65.6, _bot(BLIMP, -65.6) - .8)]
BL_SFIN = [(-42, BL_C + 1), (-56, BL_C + 7.4), (-65, BL_C + 7.2), (-66.4, BL_C + .6)]
BL_GON = Hull(4, 27, lambda u: 2.9 * (1 - clamp((8 - u) / 4) ** 2) ** .5 * (1 - clamp((u - 23) / 4) ** 2.4) ** .5, lambda u: 13.2)
BL_POD = Hull(-.6, 6.2, lambda u: 1.45 * math.sqrt(max(0., 1 - ((u - 3.6) / (2.6 if u > 3.6 else 4.2)) ** 2)), lambda u: 14.6)
def fin_ink(pts, hinge, u, v, L, base=.14, paint=None):
    """A fin with its rudder behind the hinge; paint(u, v, L, rudder) -> livery colour or None."""
    d = kit.poly(u, v, pts)
    if d >= 0: return None
    if d > -OW or abs(u - hinge) < .25: return edge(L)
    col = paint(u, v, L, u < hinge) if paint else None
    t = base + (.3 if u < hinge else 0)
    return ink(t, v * .2 + u * .05 if base < .3 else v, L, 1.8, u, col)
def bl_fin(u, v, L, rudder): return paint('blimp', 1 if rudder else 0, L)
def blimp(u, v, L):
    g = BL_POD.at(u, v)
    if g[0] < 0: return hull_ink(BL_POD, u, v, L, g, 1.4, rimw=.6, base=paint('blimp', 1, L))
    if kit.cap(u, v, 2, 12.4, 4, 13.6, .5) < 0: return edge(L)
    g = BL_GON.at(u, v)
    if g[0] < 0:
        if g[0] > -OW: return edge(L)
        if 8.4 < u < 24.6 and 11.6 < v < 13.6:
            if (u - 8.4) % 2.3 < .6 or v > 13.1: return edge(L)
            return glass(L, u - v)
        return hull_ink(BL_GON, u, v, L, g, 1.4, rimw=.6, base=paint('blimp', 0, L))
    c = fin_ink(BL_SFIN, -59, u, v, L, .45, bl_fin)
    if c: return c
    g = BLIMP.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        sn, r = g[3], g[4]
        if u > 57:                                                             # nose battens
            ph = math.asin(sn) / (math.pi / 12)
            if abs(ph - round(ph)) * r * math.pi / 12 < .3: return edge(L)
            if u > 66.4: return ink(.7, v, L, 1.4)
        if nav(L) and u > 66.6 and abs(v - BL_C) < 1: return nav(L, 'white')
        base = paint('blimp', 0, L) if band(sn, -.16, .2) else paint('blimp', 1, L) if band(sn, -.25, .29) else None   # gold-edged band
        return hull_ink(BLIMP, u, v, L, g, 2.1, k=.55, base=base)
    for pts, h in ((BL_UFIN, -58.6), (BL_LFIN, -58.6)):
        c = fin_ink(pts, h, u, v, L, paint=bl_fin)
        if c: return c
    return None

# ------------------------------------------------------------------ 9. cargo airship: rigid hull, girders, slung container
AS_C = -7.
def _as_r(u):
    if u > 70: return 19 * math.sqrt(max(0., 1 - ((u - 70) / 34) ** 2))
    if u > -30: return 19
    t = (-30 - u) / 74; return 19 * max(0., 1 - t ** 1.8) ** .72
SHIP = Hull(-104, 104, _as_r, lambda u: AS_C)
AS_UFIN = [(-60, _top(SHIP, -60) + 1.6), (-79, -27.4), (-95, -27.4), (-99, _top(SHIP, -99) + .6)]
AS_LFIN = [(-60, _bot(SHIP, -60) - 1.6), (-79, 13.4), (-95, 13.4), (-99, _bot(SHIP, -99) - .6)]
AS_SFIN = [(-62, AS_C + 1.2), (-80, AS_C + 8.6), (-96, AS_C + 8.4), (-100, AS_C + .8)]
AS_CAR = Hull(56, 79, lambda u: 2.9 * max(0., 1 - clamp((61 - u) / 5) ** 2) ** .5 * max(0., 1 - clamp((u - 74) / 5) ** 2) ** .5, lambda u: 13.6)
AS_PODS = [Hull(c0, c0 + 10, lambda u, c0=c0: 2.1 * math.sqrt(max(0., 1 - ((u - c0 - 6) / (4 if u > c0 + 6 else 6)) ** 2)), lambda u: 16.4) for c0 in (26, -46)]
AS_BOX = (0, 23.6, 17, 3.9)                         # slung container: centre, half sizes
AS_CABLES = [wire(-8, 11.4, -16, 19.7, .3), wire(8, 11.4, 16, 19.7, .3), wire(-3, 11.6, -6, 19.7, .26), wire(3, 11.6, 6, 19.7, .26)]
AS_STRUTS = [wire(c0 + 5, 11, c0 + 6.4, 14.6, .45) for c0 in (26, -46)] + [wire(c0 + 2, 11.2, c0 + 4.6, 14.8, .32) for c0 in (26, -46)]
AS_BANDS = (-91, -84, -79, -74)                     # the banded tail: sky, marigold, sky (u, rings follow the hull)
def as_band(u, L):
    for i in range(3):
        if AS_BANDS[i] <= u < AS_BANDS[i + 1]: return paint('airship', i % 2, L)
    return None
def as_fin(u, v, L, rudder): return as_band(u, L) or (paint('airship', 0, L) if rudder else cream(L))
def airship(u, v, L):
    # slung container: corrugated sides, corner castings
    d = kit.box(u, v, *AS_BOX)
    if d < 0:
        if d > -OW: return edge(L)
        x, y = u - AS_BOX[0], v - AS_BOX[1]
        if abs(x) > AS_BOX[2] - 1.6 and abs(y) > AS_BOX[3] - 1.4: return ink(.85, v, L, 1.2)
        if abs(y + AS_BOX[3] - 1.1) < .25 or abs(y - AS_BOX[3] + 1.1) < .25: return faint(L)
        rib = line(u / 1.5, .38, 1 / S / 1.5); box_ = paint('airship', 2, L)                  # a coloured container
        t = .14 + .4 * clamp((y + 2) / 6)
        if L['night']: return ink(t, u, L, 1.5, base=box_)
        return mix(box_, L['ink'], q(max(rib * .45, line(u / 1.5 + .5, t, 1 / S / 1.5))))
    c = first(AS_CABLES, u, v, L)
    if c: return c
    for H in AS_PODS:
        g = H.at(u, v)
        if g[0] < 0:
            if g[0] > -OW or abs(u - H.u0 - 3.2) < .2: return edge(L)
            return hull_ink(H, u, v, L, g, 1.5, rimw=.7, base=paint('airship', 0, L))
    c = first(AS_STRUTS, u, v, L)
    if c: return c
    g = AS_CAR.at(u, v)
    if g[0] < 0:
        if g[0] > -OW: return edge(L)
        if 61 < u < 76 and 12.2 < v < 14.2:
            if (u - 61) % 2.5 < .55 or v > 13.7: return edge(L)
            return glass(L, u - v)
        return hull_ink(AS_CAR, u, v, L, g, 1.4, rimw=.6, base=paint('airship', 1, L))
    c = fin_ink(AS_SFIN, -90, u, v, L, .45, as_fin)
    if c: return c
    g = SHIP.at(u, v); d = g[0]
    if d < 0:
        if d > -OW: return edge(L)
        sn, r = g[3], g[4]; phi = math.asin(sn); k = phi / (math.pi / 10)
        gap = r * math.cos(phi) * math.pi / 10                                                      # girder spacing on screen
        if nav(L) and u > 102.6: return nav(L, 'red')
        if u > 96:                                                                                  # nose cap battens
            if abs(k * 2 - round(k * 2)) * gap / 2 < .26: return edge(L)
            if u > 102.4: return ink(.5, v, L, 1.4, base=paint('airship', 0, L))
        if d > -OW - 1.4 and rim(L, g[1], g[2]): return kit.warm(.7, u, L)
        pk = (math.floor(k) + .5) * math.pi / 10                                                    # flat fabric panels
        nx = g[1]; ny = math.sin(pk) * math.sqrt(max(0., 1 - nx * nx))
        t = .05 + .88 * kit.form(nx, ny, L)
        base = as_band(u - 2.2 * math.cos(phi), L)                                                 # the banded tail
        if u > 96 or (-74 <= u - 2.2 * math.cos(phi) and band(sn, -.04, .16)): base = paint('airship', 0, L)   # nose cap, cheatline
        elif -74 <= u - 2.2 * math.cos(phi) and band(sn, .16, .22): base = paint('airship', 1, L)
        if base: return ink(t, along(SHIP, sn, r, .6), L, 2.2, u * .6 + v * .8, base)
        frame = clamp((kit.form(g[1], g[2], L) - .12) * 3)                   # the frame shows in the half-tones, not the highlights
        if frame > 0:
            if abs(k - round(k)) * gap < .2 and gap > 2.6 and abs(round(k)) < 5: return mix(L['paper'], L['ink'], q(.35 + .45 * frame))   # girders
            fr = (u - 2.2 * math.cos(phi)) / 11.5
            if abs(fr - round(fr)) * 11.5 < .22 and -95 < u < 92 and abs(sn) < .97: return mix(L['paper'], L['ink'], q(.3 + .4 * frame))  # rings
        return ink(t, along(SHIP, sn, r, .6), L, 2.2, u * .6 + v * .8)
    for pts, h in ((AS_UFIN, -90), (AS_LFIN, -90)):
        c = fin_ink(pts, h, u, v, L, paint=as_fin)
        if c: return c
    return None

# ------------------------------------------------------------------ moving parts
PARTS = dict(
    drone=[dict(name='rotor-aft', box=(-13, -6, -5, -3.6), pivot=(-9, -4.6), motion='spin-x', shade=rotor_part(-9, -4.6, 3.8, .36, .5)),
           dict(name='rotor-fore', box=(5, -6, 13, -3.6), pivot=(9, -4.6), motion='spin-x', shade=rotor_part(9, -4.6, 3.8, .36, .5))],
    helicopter=[dict(name='rotor', box=(-19, -10, 21, -7.4), pivot=(.8, -8.6), motion='spin-x', shade=rotor_part(.8, -8.6, 19.6, .45, .7)),
                dict(name='tail-rotor', box=(-22.8, -7.4, -16.8, -1.4), pivot=(-19.8, -4.4), motion='spin', shade=disc_part(-19.8, -4.4, 2.9))],
    prop_plane=[dict(name='propeller', box=(19.6, -8.2, 22.4, 8.2), pivot=(21, 0), motion='spin-y', shade=prop_part(21, 0, 7.6, .7))],
    blimp=[dict(name='propeller', box=(-2.6, 10, 0, 19.2), pivot=(-1.3, 14.6), motion='spin-y', shade=prop_part(-1.3, 14.6, 4.2, .5))],
    airship=[dict(name=f'propeller{i}', box=(c0 - 1.6, 11.6, c0 + 1, 21.2), pivot=(c0 - .3, 16.4), motion='spin-y', shade=prop_part(c0 - .3, 16.4, 4.6, .55))
             for i, c0 in enumerate((26, -46))],
)
DRAW = dict(paper_plane=paper_plane, drone=drone, helicopter=helicopter, prop_plane=prop_plane, private_jet=private_jet,
            balloon=balloon, airliner=airliner, blimp=blimp, airship=airship)

NIGHT_BODY = [None]
NIGHT_TINT = .66                 # how strongly a craft's body takes its livery colour at night (0 = plain white-line print)
def night_body(kind, L):
    """The colour a craft's body glows at night: its main livery pigment, deep enough for the pale lines to read on."""
    return mix(L['paper'], kit.PIGMENTS[LIVERY[kind][0]], NIGHT_TINT)

def shade(kind, u, v, light):
    w, h = SIZE[kind]
    if abs(u) > w / 2 + .5 or abs(v) > h / 2 + .5: return None
    NIGHT_BODY[0] = night_body(kind, light) if light['night'] else None
    try: return DRAW[kind](u, v, light)
    finally: NIGHT_BODY[0] = None

def parts(kind):
    return PARTS.get(kind, [])

# ------------------------------------------------------------------ parked: a shut hangar and a limp windsock
def parked(u, v, light):
    L = light
    if v > 5.5: return None
    if kit.cap(u, v, 7.6, 5.5, 7.6, -4.6, .3) < 0: return edge(L)                           # windsock pole
    d = kit.poly(u, v, [(7.8, -4.8), (9.8, -4.1), (9.2, -.9), (8.3, -1.2)])                  # the sock hangs limp
    if d < 0: return edge(L) if d > -.4 else paint('hangar', 0, L) if int((v + 4.8) / 1.25) % 2 else cream(L)
    # a barrel-roofed hangar facing us, its big doors shut
    x0, x1, eave, crown = -10.6, 5.6, -.6, -4.4; cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
    roof = eave + (crown - eave) * max(0., 1 - ((u - cx) / hw) ** 2) ** .6 if x0 <= u <= x1 else None
    if roof is None or v < roof: return None
    if v - roof < .7 or abs(u - x0) < .6 or abs(u - x1) < .6 or v > 4.9: return edge(L)
    if v < eave + .3:                                                                        # ribbed roof
        if abs(v - eave) < .45: return edge(L)
        return ink(.12 + .5 * kit.form((u - cx) / hw * .8, -.6, L), u, L, 1.4)
    if L['night'] and abs(u - cx) < 1.1 and 1 < v < 3.2: return L['gold']                   # someone working late
    if abs(u - cx) < .3: return edge(L)                                                      # the doors meet
    if abs(v - eave - 1) < .3: return faint(L)                                               # door track
    return ink(.2, u, L, 1.25, base=paint('hangar', 1, L, .8))
