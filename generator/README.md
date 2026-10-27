# The world generator

Draws the lake on the profile README from Jake's public GitHub contributions, at his current moment in California.
The art bible is `docs/WORLD.md`: what lives where, the look, and the rules.

```sh
python3 generator/world.py                          # the current moment -> assets/art.svg (+ art.json)
python3 generator/world.py --all --out previews/world   # all six moments
python3 generator/world.py --layout phone --out previews/phone.svg   # the phone cut (720 x 900)
tools/raster.sh previews/phone.svg previews/phone.jpg 720 900        # phone cut -> JPEG (needs Chrome)
python3 generator/world.py --moment golden --when 2026-10-26T17:30 --out previews/golden.svg
python3 tools/check.py assets/art.svg               # honesty and readability gates
python3 generator/readme.py                         # README.md from README.template.md
python3 generator/data.py                           # what the data says (years, fleet tiers, days)
python3 generator/clock.py                          # today's moments in California
```

| File | What |
|---|---|
| `world.py` | composition: tint plate, sky and water, sun or moon, cast, placement, text, motion |
| `kit.py` | engraving toolkit: light per moment, `engrave()`, shapes, PNG and sprite rasters |
| `data.py` | the data rules: years, the rolling 12-month fleet (each size up = twice the work), 365 days |
| `clock.py` | the real sun over California, the six moments, the moon's phase |
| `mountains.py`, `fleet.py`, `days.py`, `friends.py` | the pieces: years, months, days, and the turtle and koi |
| `fetch.py` | refreshes `data/contributions.json` from GitHub's contribution calendar |
| `readme.py` | fills the README numbers |

The workflow `.github/workflows/world.yml` runs every 15 minutes: it fetches the data, draws the current moment (the
wide SVG, and when it changed, the phone cut as a JPEG), checks both, and publishes them to the `output` branch (one
commit, replaced each time). Data and README numbers are saved
to `main` once a day. Standard library Python only; output is deterministic for the same data and moment.

Typefaces: [Geist and Geist Mono](https://github.com/vercel/geist-font) by Vercel, SIL Open Font License 1.1
(`fonts/*-OFL.txt`), embedded as subsets.
