#!/usr/bin/env bash
# brand.sh — guarda o kit de marca de um filme APROVADO para reutilizar nos próximos vídeos do mesmo cliente.
#
#   bash scripts/brand.sh save <projeto> <estudio/brands/cliente>
#       copia brand/BRAND.md, logos (assets/logo*, brand/logo*), fontes (fonts/), poster e contact do filme aprovado.
#       Depois: ATUALIZE <brands/cliente>/BRAND.md com o que foi aprovado (cores, tipos, springs, som, feedback).
#   bash scripts/brand.sh show <estudio/brands/cliente>      # lista o kit
#
# Para começar um filme novo com a marca: bash <skill>/scripts/new.sh <pasta> --brand <estudio/brands/cliente>
set -euo pipefail
CMD="${1:?uso: brand.sh save <projeto> <brand-dir> | show <brand-dir>}"
if [[ "$CMD" == "show" ]]; then
  B="${2:?}"; echo "Kit: $B"; find "$B" -maxdepth 2 -type f | sed "s#^$B/#  #" | sort; exit 0
fi
P="${2:?projeto}"; B="${3:?pasta da marca}"
mkdir -p "$B"/{fonts,approved,assets}
STAMP=$(date +%Y-%m-%d)
NAME=$(basename "$(cd "$P" && pwd)")
# BRAND.md: o do projeto (mais recente) vence; senão mantém o existente
if [[ -f "$P/brand/BRAND.md" ]]; then cp "$P/brand/BRAND.md" "$B/BRAND.md"; fi
[[ -f "$B/BRAND.md" ]] || cp "$(dirname "$0")/../template/BRAND.md" "$B/BRAND.md" 2>/dev/null || true
# logos e assets de marca
shopt -s nullglob nocaseglob
for f in "$P"/assets/logo* "$P"/brand/logo* "$P"/brand/assets/*; do cp "$f" "$B/assets/"; done
[[ -f "$B/assets/logo.svg" ]] && cp "$B/assets/logo.svg" "$B/logo.svg"
[[ -f "$B/assets/logo.png" ]] && cp "$B/assets/logo.png" "$B/logo.png"
# fontes
if [[ -d "$P/fonts" ]]; then cp "$P"/fonts/*.woff2 "$B/fonts/" 2>/dev/null || true; [[ -s "$P/fonts/fonts.css" ]] && cp "$P/fonts/fonts.css" "$B/fonts/fonts.css"; fi
# prova do que foi aprovado
[[ -f "$P/out/qa/poster.png" ]] && cp "$P/out/qa/poster.png" "$B/approved/${STAMP}_${NAME}_poster.png"
[[ -f "$P/out/qa/contact.png" ]] && cp "$P/out/qa/contact.png" "$B/approved/${STAMP}_${NAME}_contact.png"
[[ -f "$P/out/board.html" ]] && cp "$P/out/board.html" "$B/approved/${STAMP}_${NAME}_board.html"
[[ -f "$P/docs/SPEC.md" ]] && cp "$P/docs/SPEC.md" "$B/approved/${STAMP}_${NAME}_SPEC.md"
echo "✔ kit salvo em $B"
echo "→ agora atualize $B/BRAND.md: cores/tipos/springs/som aprovados + linha no Histórico com o feedback do cliente"
