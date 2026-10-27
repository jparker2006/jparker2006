# The World: art bible

The profile art for github.com/jparker2006 is **one world**: a lake engraved in cobalt ink on cream paper, where every
time scale of Jake Parker's public GitHub contributions lives as something that belongs there. It follows Jake's real
clock in Los Angeles, so it is morning, golden hour or night when it is for him. It must read as **art first**.
The numbers live in plain text under it.

Everything below was decided with Jake in a grill on 2026-10-26. Changing any of it needs Jake.

## 1. What lives where (by speed, like nature)

| Scale | Thing | Rule |
|---|---|---|
| Years | **Mountains** on the far shore | One mountain per calendar year since the first contribution, oldest on the left. They never move. This year's grows a little every day. Summit height follows the square root of the year's total on one shared scale (Jake, 2026-10-26: small years must read as hills), and every year is labeled with its exact total. |
| Months | **A fleet of aircraft** in the sky | Rolling last 12 months, oldest on the left, the current month on the right. Each month flies one aircraft; bigger means busier. |
| Days | **Wildflowers** along the near shore | Rolling last 365 days, one per day, each under its own month's aircraft. Height follows the square root of the day's count (the tallest is labeled with its exact count); busier days bloom. A hand-coloured engraved meadow (daisies, round flowers, tulips, buds); only the busiest 10% of days get the cloud's smiling face, and they sleep at night. Flower colours are decoration only. |

**The fleet**, from quietest to busiest month: paper plane, drone, helicopter, prop plane, private jet, hot air balloon,
jet airliner, blimp, cargo airship. Each step up means **double the work**, measured against the record month (the
biggest month ever, currently Oct 2026 = 2,621): `tier = 9 + ceil(log2(month / record))`, clamped to 1..9. A month with no
contributions flies nothing; it stays parked on the ground. Big craft must *look* big: each type has its own natural size.
They fly **time across, at natural height**: x follows the month order, y follows the kind of craft (paper planes and
drones skim the water, helicopters and prop planes fly low, jets and airships cruise high). Big ones pass over small ones.

**Always there (the cast, not data):** the round smiling cloud (perfect geometric cloud shape, a cute face), rubber ducks
(a mother and ducklings), a turtle and a koi. Hot air balloons are no longer decoration, because a balloon now means a month.

## 2. Time of day

The art shows Jake's **real moment** in Los Angeles (`generator/clock.py`, from the real sun's elevation):
`dawn, morning, midday, golden, dusk, night`. Each moment is hand-composed, but the real sun decides when it starts.
For example, golden hour lands at the real sunset (6:06 pm on 2026-10-26, 4:43 pm on 2026-12-05). Night shows the
**real moon phase**. The hour decides what is lit; nothing is swapped out. Dark mode does not matter: everyone sees Jake's clock.

## 3. The look

- **One cobalt ink on cream paper**, plus **gold for warm light only** (the sun and its path on the water, the ducks,
  a balloon burner, warm rims). References: Praveen's textured shader (`/tmp/refs2/p*.jpg`), uisabor's engravings
  (`/tmp/refs3/s*.jpg`), unseen's lake paintings (`/tmp/refs4/u*.jpg`: hills built from rounded tree crowns, mirror-still
  water, a lone rower, one warm accent; `u4` is almost exactly our palette), and the engraved **airmail stamps of the 1920s
  and 30s** for the aircraft. Reference images are for technique only: never trace or copy them.
- **Light is bare paper.** Tone comes from line width. Concentrate detail where the eye should go; leave air elsewhere.
- **A tint plate** sits under the sky and the water, like a banknote's offset tint under the intaglio lines or a Hiroshige
  bokashi sky. It is baby blue at midday and changes with the moment. Land and cloud stay paper plus ink.
- **Colour accents** come from one shared palette, `kit.PIGMENTS` via `kit.pigment(name, light)`, which quiets them at
  night: the aircraft wear golden-age liveries printed under their engraving (1950s airline posters), the flowers are
  hand-coloured, and the turtle is green. Colour is decoration only; every meaning is carried by shape, size and labels.
- Night is a **white-line engraving**: pale lines on navy. `kit.engrave()` flips automatically, so draw with *tone*
  (0 = lit, 1 = shade), never with hard-coded colours.
- **Accessible to colourblind viewers:** meaning never by colour alone. Blue and gold is the safe pair; shapes must read in grey.
- Type: Geist (name) and Geist Mono (small caps). No ornate or classical fonts.

## 4. Canvas and composition (art units; the README shows it 830 px wide, so 1 unit = 0.69 px)

```
y   0 ┌──────────────────────────────────────────────────────────────┐ 1200
      │ Jake Parker                          (sun / moon by moment)  │
      │ GOLDEN HOUR · LOS ANGELES                                    │
      │      fleet: x = month order, y = natural height of the craft │
      │      (airship ~70, airliner ~95, ... drone ~245, paper ~270) │
 300  ├──── far shore: mountains (years), base y = 300 ─────────────┤
      │   water: reflections, sun path, ducks, turtle, koi           │
 430  │   near shore / shallows: the days (strip y 430..500)         │
 500  └──────────────────────────────────────────────────────────────┘
```

## 5. Motion (gentle life only)

Small loops, no travel: propellers and rotors spin, the drone hovers, the balloon and blimps bob, the cloud drifts, the
days sway in the wind, and the koi leaps now and then. Aircraft hold their places so the months still read left to right.
CSS animations inside the SVG only. Everything stops under `prefers-reduced-motion`.

## 6. Text (very little)

Inside the art: the name, the moment line ("GOLDEN HOUR · LOS ANGELES"), and a small year caption under each mountain.
Month captions are **microprint** (readable only when zoomed). Every number goes in the README text below the art.

## 7. Rules that never bend

- **Honest data:** mountain summits, fleet tiers and day sizes follow the rules above exactly. `tools/check.py` verifies them.
- **Original art:** draw it with code. Never copy reference images.
- **GitHub-safe SVG:** no scripts, no foreignObject, no external files. Embedded PNG and fonts only. Under about 500 KB.
- Readable: text at least 11 px at 830 px wide and at least 4.5:1 contrast (microprint excepted).
- Standard library Python only (fontTools is used once, offline, for fonts). Deterministic: the same input gives the same image.

## 8. Code map and ownership

| File | What | Owner |
|---|---|---|
| `generator/kit.py` | engraving toolkit: light presets, `engrave()`, signed distances, PNG, sprites, contact sheets | orchestrator |
| `generator/data.py` | the data rules above | orchestrator |
| `generator/clock.py` | LA sun, moments, moon | orchestrator |
| `generator/world.py` | composition, tint plate, sky, water, sun/moon, cast, text, motion, SVG | orchestrator |
| `generator/fleet.py` | the nine aircraft (sprites, moving parts, parked look) | fleet artist |
| `generator/days.py` | the days along the shore | days artist |
| `generator/mountains.py` | the year mountains | mountains artist |

Each piece's interface is documented at the top of its file. Pieces draw with `kit.engrave()` and `kit.LIGHTS[moment]`,
so they work at every moment, including night.
