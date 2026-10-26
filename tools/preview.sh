#!/usr/bin/env bash
# Render one variant SVG into review PNGs.
#   tools/preview.sh assets/art.svg previews
# Writes OUT_DIR/desktop.png (830 px, GitHub README width), phone.png (358 px),
# dark.png (on GitHub's dark background) and cb_protan/cb_deutan/cb_tritan/cb_gray.png.
# Only one headless Chromium runs at a time (flock), because the sandbox has limited memory.
set -euo pipefail
svg=$(readlink -f "$1"); mkdir -p "$2"; out=$(readlink -f "$2")
read -r VW VH < <(python3 -I -c 'import re,sys; v=re.search(r"viewBox=\"0 0 ([0-9.]+) ([0-9.]+)\"",open(sys.argv[1]).read(1000)); print(int(float(v[1])),int(float(v[2])))' "$svg")
h830=$(( (830*VH + VW - 1) / VW )); h358=$(( (358*VH + VW - 1) / VW ))
tmp=$(mktemp -d /tmp/pa-render.XXXXXX); trap 'rm -rf "$tmp"' EXIT
cp "$svg" "$tmp/v.svg"
page() { # name width height body-style img-style
  printf '<html><body style="margin:0;%s"><svg width="0" height="0" style="position:absolute"><defs>
<filter id="protan" color-interpolation-filters="linearRGB"><feColorMatrix type="matrix" values="0.152286 1.052583 -0.204868 0 0 0.114503 0.786281 0.099216 0 0 -0.003882 -0.048116 1.051998 0 0 0 0 0 1 0"/></filter>
<filter id="deutan" color-interpolation-filters="linearRGB"><feColorMatrix type="matrix" values="0.367322 0.860646 -0.227968 0 0 0.280085 0.672501 0.047413 0 0 -0.011820 0.042940 0.968881 0 0 0 0 0 1 0"/></filter>
<filter id="tritan" color-interpolation-filters="linearRGB"><feColorMatrix type="matrix" values="1.255528 -0.076749 -0.178779 0 0 -0.078411 0.930809 0.147602 0 0 0.004733 0.691367 0.303900 0 0 0 0 0 1 0"/></filter>
<filter id="gray"><feColorMatrix type="saturate" values="0"/></filter></defs></svg><img src="v.svg" style="display:block;width:%spx;%s"></body></html>' "$4" "$2" "$5" > "$tmp/$1.html"
  flock /tmp/profile-art-render.lock chromium --headless=new --no-sandbox --user-data-dir="$tmp/chrome" --hide-scrollbars \
    --window-size="$2,$3" --screenshot="$out/$1.png" "file://$tmp/$1.html" >/dev/null 2>&1
}
page desktop 830 "$h830" "background:#fff" ""
page phone 358 "$h358" "background:#fff" ""
for f in protan deutan tritan gray; do page "cb_$f" 830 "$h830" "background:#fff" "filter:url(#$f)"; done
# dark mode preview: GitHub dark page colour with a margin around the image
printf '<html><body style="margin:0;background:#0d1117;padding:24px"><img src="v.svg" style="display:block;width:830px"></body></html>' > "$tmp/dark.html"
flock /tmp/profile-art-render.lock chromium --headless=new --no-sandbox --user-data-dir="$tmp/chrome" --hide-scrollbars \
  --window-size="878,$((h830 + 48))" --screenshot="$out/dark.png" "file://$tmp/dark.html" >/dev/null 2>&1
ls "$out"/*.png | xargs -n1 basename | tr '\n' ' '; echo
