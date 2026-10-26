# Profile art generator

`art.py` turns `data/contributions.json` into `assets/art.svg` and fills `README.md` from `README.template.md`.
`fetch.py` refreshes the data from GitHub's contribution calendar. The workflow in `.github/workflows/art.yml`
runs both every day and commits the result.

```sh
python3 generator/art.py            # render (standard library only, ~8 s)
python3 tools/check.py assets       # honesty + readability gates
tools/preview.sh assets/art.svg previews   # desktop, phone, dark mode and colour-vision previews (needs Chromium)
```

## Rules the art keeps
- One ridge per month, oldest at the back. Height is linear in contributions with one shared scale; every
  day's crest is exact (`tools/check.py` verifies it against the data).
- Only real numbers are printed. Meaning never depends on colour alone.
- The SVG is self-contained (embedded PNG and fonts), because GitHub shows README SVGs as images.

## Credits
Typefaces: [Geist and Geist Mono](https://github.com/vercel/geist-font) by Vercel, SIL Open Font License 1.1
(`fonts/*-OFL.txt`), embedded as subsets.
