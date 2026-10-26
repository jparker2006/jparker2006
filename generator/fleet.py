"""The fleet: one aircraft per month, bigger for busier months (docs/WORLD.md). PLACEHOLDER DRAWINGS: the fleet
artist replaces them. Keep this interface; world.py relies on it.

    SIZE[kind] = (w, h)          box in art units, nose pointing right (the fleet flies toward "now"). Must grow with tier.
    ALTITUDE[kind] = y           cruising height of the craft's centre (art units, y down; the horizon is y = 300).
    MOTION[kind]                 how the whole craft moves: 'bob' (slow float), 'hover' (small jitter) or None.
    shade(kind, u, v, light)     -> (r, g, b) or None. Local coords: (0, 0) = box centre, u to the right, v down.
    parts(kind)                  -> [dict(name, box=(u0, v0, u1, v1), pivot=(u, v), motion, shade=fn(u, v, light))]
                                    separately animated pieces drawn on top: motion 'spin' (rotor turning, rotate about
                                    pivot) or 'spin-x' (propeller seen from the side, flickers by scaling across pivot).
    PARKED = (w, h); parked(u, v, light) -> colour or None   what a month with no contributions leaves on the shore.

Draw with kit.engrave(tone, phase, light) and kit.outline(light) so every moment (and night) works.
"""
import kit
from data import KINDS

SIZE = dict(paper_plane=(20, 9), drone=(26, 12), helicopter=(52, 22), prop_plane=(62, 22), private_jet=(84, 24),
            balloon=(52, 74), airliner=(150, 44), blimp=(176, 52), airship=(270, 70))
ALTITUDE = dict(paper_plane=272, drone=248, helicopter=224, prop_plane=200, private_jet=118, balloon=176,
                airliner=96, blimp=150, airship=70)
MOTION = dict(drone='hover', balloon='bob', blimp='bob', airship='bob')
PARKED = (18, 8)

def shade(kind, u, v, light):
    w, h = SIZE[kind]
    d = kit.ell(u, v, 0, 0, w / 2, h / 2)
    if d > 0: return None
    if d > -.9: return kit.outline(light)
    return kit.engrave(kit.form(u / (w / 2), v / (h / 2), light), v, light)

def parts(kind):
    return []

def parked(u, v, light):
    d = kit.poly(u, v, [(-9, 3), (9, 0), (-9, -3)])
    if d > 0: return None
    return kit.outline(light) if d > -.7 else light['paper']
