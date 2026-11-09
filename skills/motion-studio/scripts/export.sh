#!/usr/bin/env bash
# export.sh — a última milha: arquivos prontos para cada destino, nos limites de cada plataforma.
#
#   bash scripts/export.sh out/final.mp4 x            # post no X: H.264 High, yuv420p, AAC, faststart (≤ 140 s sem Premium)
#   bash scripts/export.sh out/final.mp4 reels        # Reels/TikTok/Shorts: confere 9:16 e 1080×1920
#   bash scripts/export.sh out/final.mp4 gif [--width 1200] [--fps 25]   # GIF: 1 paleta, loop infinito, delays EXATOS
#   bash scripts/export.sh out/final.mp4 loop [--times 3]                # loop_check: toca N vezes seguidas p/ ver a emenda
#   Opções: --out <arquivo> · --loop-fade (fade raised-cosine de 2 ms nas pontas do áudio — só p/ MP4 de loop)
#
# Armadilhas cobertas:
#   • GIF guarda atraso em centésimos de segundo: 24 fps (41,7 ms) vira 40 ms e o loop corre 4% rápido, fora da batida.
#     Por isso o GIF sai em 25 fps (40 ms exatos) ou 20 fps (50 ms). X: GIF ≤ 15 MB, ≤ 1280×1080, ≤ 350 frames.
#   • AAC acrescenta ~10–20 ms de padding: num MP4 que toca em loop o som "corta seco" na emenda → --loop-fade.
#     O WAV mestre continua sem fade (para posts com 2 loops emendados).
set -euo pipefail
IN="${1:?uso: export.sh <video> x|reels|gif|loop [opções]}"; T="${2:?destino: x|reels|gif|loop}"; shift 2
OUT=""; WIDTH=1200; GFPS=25; FADE=0; TIMES=3
while [[ $# -gt 0 ]]; do case "$1" in
  --out) OUT="$2"; shift 2;; --width) WIDTH="$2"; shift 2;; --fps) GFPS="$2"; shift 2;;
  --loop-fade) FADE=1; shift;; --times) TIMES="$2"; shift 2;; *) echo "opção desconhecida: $1"; exit 1;; esac; done
BASE="${IN%.*}"; DIR="$(dirname "$IN")"
IFS=, read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$IN")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
HASA=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$IN" | head -1)
AF=(); if [[ $FADE -eq 1 && -n "$HASA" ]]; then AF=(-af "afade=t=in:d=0.002:curve=hsin,areverse,afade=t=in:d=0.002:curve=hsin,areverse"); fi
AUD=(); [[ -n "$HASA" ]] && AUD=(-c:a aac -b:a 192k -ar 48000 "${AF[@]}")

case "$T" in
x)
  OUT="${OUT:-${BASE}_x.mp4}"
  awk "BEGIN{exit !($DUR>140)}" && echo "⚠ ${DUR}s > 140 s: X sem Premium não aceita"
  ffmpeg -v error -y -i "$IN" -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart "${AUD[@]}" "$OUT"
  echo "✔ $OUT · ${W}×${H} · H.264 High · ${DUR}s";;
reels)
  OUT="${OUT:-${BASE}_reels.mp4}"
  [[ "$W" == 1080 && "$H" == 1920 ]] || echo "⚠ ${W}×${H}: Reels/TikTok/Shorts pedem 1080×1920 (9:16) — renderize com --format 9x16, não recorte"
  ffmpeg -v error -y -i "$IN" -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 17 -preset slow -r 30 -movflags +faststart "${AUD[@]}" "$OUT"
  echo "✔ $OUT · 30 fps (plataformas re-encodam 60→30; melhor você decidir) · lembre: topo ~14% e base ~22% ficam sob a UI do app";;
gif)
  OUT="${OUT:-${BASE}.gif}"
  case "$GFPS" in 25|20|50|10) ;; *) echo "⚠ ${GFPS} fps não tem atraso exato em centésimos — usando 25 fps (40 ms)"; GFPS=25;; esac
  [[ $WIDTH -gt 1280 ]] && { echo "⚠ largura limitada a 1280 (X)"; WIDTH=1280; }
  NF=$(python3 -c "print(int(round($DUR*$GFPS)))")
  [[ $NF -gt 350 ]] && echo "⚠ ${NF} frames > 350 (limite do X para GIF): encurte o loop ou use --fps 20"
  ffmpeg -v error -y -i "$IN" -vf "fps=${GFPS},scale=${WIDTH}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 "$OUT"
  SZ=$(python3 -c "import os;print(round(os.path.getsize('$OUT')/1e6,1))")
  awk "BEGIN{exit !($SZ>15)}" && echo "⚠ ${SZ} MB > 15 MB (limite do X): reduza largura, fps, duração ou use cores chapadas (gradiente = banding + peso)"
  echo "✔ $OUT · ${WIDTH}px · ${GFPS} fps (${NF} frames) · ${SZ} MB · 1 paleta · loop infinito";;
loop)
  OUT="${OUT:-${BASE}_loopcheck.mp4}"
  ffmpeg -v error -y -stream_loop $((TIMES-1)) -i "$IN" -c copy "$OUT"
  echo "✔ $OUT — $TIMES voltas seguidas: assista a emenda (e rode qa.sh --loop para medir)";;
*) echo "destino desconhecido: $T (x|reels|gif|loop)"; exit 1;;
esac
