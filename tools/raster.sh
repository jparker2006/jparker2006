#!/usr/bin/env bash
# Rasterise an SVG to a JPEG (or PNG, by extension) with headless Chrome, at 1.5 px per unit.
#   tools/raster.sh in.svg out.jpg WIDTH HEIGHT
# Used for the phone picture: the GitHub app is safest with a plain JPEG.
set -euo pipefail
svg=$(readlink -f "$1"); out=$(readlink -f "$2" 2>/dev/null || echo "$PWD/$2"); w=$3; h=$4
chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
[ -n "$chrome" ] || { echo "no Chrome or Chromium found" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp "$svg" "$tmp/art.svg"
printf '<html><body style="margin:0"><img src="art.svg" style="display:block;width:%spx;height:%spx"></body></html>' "$w" "$h" > "$tmp/page.html"
"$chrome" --headless=new --no-sandbox --user-data-dir="$tmp/profile" --hide-scrollbars --force-device-scale-factor=1.5 \
  --virtual-time-budget=1500 --window-size="$w,$h" --screenshot="$out" "file://$tmp/page.html" >/dev/null 2>&1
test -s "$out" && echo "$out $(wc -c < "$out") bytes"
