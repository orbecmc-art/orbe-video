#!/usr/bin/env bash
# fonts.sh — baixa fontes open source (Fontsource via registry do npm, que funciona mesmo sem acesso ao Google Fonts)
# e gera fonts/fonts.css com @font-face locais. O filme fica 100% offline e determinístico.
#
#   bash fonts.sh "inter-tight:400,600,800" "instrument-serif:400" "jetbrains-mono:500" [--dir fonts]
# Slug = nome do pacote @fontsource/<slug> (minúsculas, hífen). Pesos separados por vírgula.
# Pares que funcionam: inter-tight + instrument-serif · geist + geist-mono · space-grotesk + jetbrains-mono ·
#   manrope + fraunces · archivo + ibm-plex-mono · syne + inter · bricolage-grotesque + dm-mono · unbounded + inter
set -euo pipefail
DIR="fonts"; SPECS=()
while [[ $# -gt 0 ]]; do case "$1" in --dir) DIR="$2"; shift 2;; *) SPECS+=("$1"); shift;; esac; done
mkdir -p "$DIR"; TMP=$(mktemp -d); CSS="$DIR/fonts.css"; : > "$CSS"
for spec in "${SPECS[@]}"; do
  slug="${spec%%:*}"; weights="${spec#*:}"; [[ "$slug" == "$spec" ]] && weights="400,700"
  ( cd "$TMP" && npm pack "@fontsource/$slug" --silent >/dev/null 2>&1 ) || { echo "✗ @fontsource/$slug não encontrado"; continue; }
  tgz=$(ls "$TMP"/fontsource-"$slug"-*.tgz | head -1); mkdir -p "$TMP/$slug"; tar -xzf "$tgz" -C "$TMP/$slug"
  fam=$(python3 -c "import json;print(json.load(open('$TMP/$slug/package/metadata.json'))['family'])" 2>/dev/null || echo "$slug")
  for w in ${weights//,/ }; do
    for style in normal italic; do
      f="$TMP/$slug/package/files/$slug-latin-$w-$style.woff2"
      [[ -f "$f" ]] || continue
      cp "$f" "$DIR/"; ext="$TMP/$slug/package/files/$slug-latin-ext-$w-$style.woff2"; [[ -f "$ext" ]] && cp "$ext" "$DIR/"
      echo "@font-face{font-family:'$fam';font-style:$style;font-weight:$w;font-display:block;src:url('./$(basename "$f")') format('woff2');}" >> "$CSS"
      [[ -f "$ext" ]] && echo "@font-face{font-family:'$fam';font-style:$style;font-weight:$w;font-display:block;src:url('./$(basename "$ext")') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}" >> "$CSS"
    done
  done
  echo "✔ $fam ($weights)"
done
rm -rf "$TMP"
echo "→ $CSS  (no index.html: <link rel=\"stylesheet\" href=\"fonts/fonts.css\"> e liste as fontes em FONTS para pré-carregar)"
