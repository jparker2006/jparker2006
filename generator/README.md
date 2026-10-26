# Profile art generator

`art.py` turns `data/contributions.json` into `assets/art.svg` (day) and `assets/art-night.svg` (night, shown in dark
mode through `<picture>`), and fills `README.md` from `README.template.md`.
`fetch.py` refreshes the data from GitHub's contribution calendar. The workflow in `.github/workflows/art.yml`
runs both every day and commits the result.

```sh
python3 generator/art.py            # render (standard library only, ~8 s)
python3 tools/check.py assets       # honesty + readability gates
tools/preview.sh assets/art.svg previews   # desktop, phone, dark mode and colour-vision previews (needs Chromium)
```

## How it is drawn
- One mountain range for the last 52 weeks; each peak is one week, all on one linear scale.
- A line-halftone "engraving" shader: every surface is ink lines whose width follows the tone (crossing wave mesh in
  the sky, contour lines and rock ribs on the mountains, perspective lines on the water, a guilloché sun or moon).
- Night is a white-line engraving: pale lines on navy, glowing balloons, sleeping cloud and ducks, stars, fireflies.
- Motion is CSS inside the SVG (cloud, balloons, gulls, a leaping koi, twinkling glints and stars) and switches off
  for people who ask their system for reduced motion.
- A microprint line above the horizon only reads when you zoom in.

## Rules the art keeps
- One ridge per month, oldest at the back. Height is linear in contributions with one shared scale; every
  day's crest is exact (`tools/check.py` verifies it against the data).
- Only real numbers are printed. Meaning never depends on colour alone.
- The SVG is self-contained (embedded PNG and fonts), because GitHub shows README SVGs as images.

## Credits
Typefaces: [Geist and Geist Mono](https://github.com/vercel/geist-font) by Vercel, SIL Open Font License 1.1
(`fonts/*-OFL.txt`), embedded as subsets.
