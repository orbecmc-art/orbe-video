#!/usr/bin/env bash
# ref.sh — desmonta um vídeo de referência em números para o Claude estudar (a GRAMÁTICA, nunca o conteúdo).
#
#   bash scripts/ref.sh refs/launch.mp4 [--name launch] [--every 0.5]
#   bash scripts/ref.sh "https://x.com/.../status/..."      # baixa com yt-dlp se instalado e se a rede permitir
#
# Saída em refs/<nome>/:
#   frames/      1 frame a cada 0,5 s (540 px)       → abra e descreva o ritmo plano a plano
#   contact.png  todos os frames numa folha          → visão geral do look
#   cuts.txt     tempos de corte detectados + duração de cada plano
#   palette.txt  cores dominantes (hex + %)          → paleta da referência
#   beats.json   BPM/batidas da trilha (se houver áudio)
#   ANALYSIS.md  números prontos + roteiro do que escrever em docs/style_guide.md
# Onde achar referências: whatships.com · galerias de vídeos feitos com Opus 5.5 (awesome-opus-5-5-videos) · Dribbble motion · X
set -euo pipefail
SRC="${1:?uso: ref.sh <video|url> [--name nome] [--every 0.5]}"; shift
NAME=""; EVERY=0.5
while [[ $# -gt 0 ]]; do case "$1" in --name) NAME="$2"; shift 2;; --every) EVERY="$2"; shift 2;; *) shift;; esac; done
HERE="$(cd "$(dirname "$0")" && pwd)"
if [[ "$SRC" =~ ^https?:// ]]; then
  command -v yt-dlp >/dev/null || { echo "✗ yt-dlp não instalado (pip install yt-dlp) — ou baixe o vídeo e passe o arquivo"; exit 1; }
  NAME="${NAME:-ref_$(date +%H%M%S)}"; mkdir -p "refs/$NAME"
  yt-dlp -q -f "mp4/bestvideo+bestaudio/best" --merge-output-format mp4 -o "refs/$NAME/source.%(ext)s" "$SRC" || { echo "✗ download falhou (rede bloqueada?) — baixe manualmente e passe o arquivo"; exit 1; }
  SRC="refs/$NAME/source.mp4"
fi
[[ -f "$SRC" ]] || { echo "✗ arquivo não encontrado: $SRC"; exit 1; }
NAME="${NAME:-$(basename "${SRC%.*}")}"; D="refs/$NAME"; mkdir -p "$D/frames"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC")
INFO=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$SRC")
HASA=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$SRC" | head -1)

# frames + folha
ffmpeg -v error -y -i "$SRC" -vf "fps=1/$EVERY,scale=540:-2" -q:v 3 "$D/frames/f_%03d.jpg"
N=$(ls "$D/frames" | wc -l); ROWS=$(( (N + 7) / 8 ))
ffmpeg -v error -y -i "$SRC" -vf "fps=1/$EVERY,scale=240:-2,tile=8x${ROWS}:padding=4:color=0x1b1b1b" -frames:v 1 "$D/contact.png"

# cortes e duração dos planos
ffmpeg -hide_banner -i "$SRC" -vf "select='gt(scene,0.3)',showinfo" -an -f null - 2>&1 | grep -oE "pts_time:[0-9.]+" | cut -d: -f2 > "$D/.cuts" || true
python3 - "$D" "$DUR" <<'EOF' > "$D/cuts.txt"
import sys
d, dur = sys.argv[1], float(sys.argv[2])
cuts = [float(x) for x in open(f"{d}/.cuts").read().split()]
edges = [0.0] + cuts + [dur]
shots = [round(b - a, 2) for a, b in zip(edges, edges[1:]) if b - a > 0.04]
print(f"cortes: {len(cuts)} · planos: {len(shots)} · duração média {sum(shots)/len(shots):.2f}s · min {min(shots):.2f}s · max {max(shots):.2f}s · {len(cuts)/dur:.2f} cortes/s")
for i, (a, s) in enumerate(zip(edges, shots)): print(f"  plano {i+1:2d}  {a:6.2f}s  dura {s:.2f}s")
EOF
rm -f "$D/.cuts"

# paleta dominante
ffmpeg -v error -y -i "$SRC" -vf "fps=2,scale=160:-2,palettegen=max_colors=10:stats_mode=full" "$D/palette.png"
python3 - "$SRC" > "$D/palette.txt" <<'EOF'
import sys, subprocess, numpy as np
raw = subprocess.run(['ffmpeg','-v','error','-i',sys.argv[1],'-vf','fps=2,scale=96:-2','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
px = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(int)
q = px // 20
key = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
keys, inv, counts = np.unique(key, return_inverse=True, return_counts=True)
tot = counts.sum()
for idx in np.argsort(-counts)[:10]:
    r, g, b = px[inv == idx].mean(axis=0).round().astype(int)   # cor média do grupo, não o centro do balde
    print(f"#{r:02X}{g:02X}{b:02X}  {100*counts[idx]/tot:5.1f}%")
EOF

# trilha
BEATS="(sem áudio)"
if [[ -n "$HASA" ]]; then
  ffmpeg -v error -y -i "$SRC" -vn -ac 1 -ar 22050 "$D/audio.wav"
  python3 "$HERE/beats.py" "$D/audio.wav" > "$D/beats.json" 2>/dev/null && BEATS=$(python3 -c "import json;b=json.load(open('$D/beats.json'));print(f\"{b['bpm']} BPM · {len(b['beats'])} batidas\")")
fi

cat > "$D/ANALYSIS.md" <<EOF
# Referência: $NAME
- Fonte: $SRC
- Specs: ${INFO} · ${DUR}s · áudio: ${HASA:-nenhum} · trilha: ${BEATS}
- Ritmo de edição: $(head -1 "$D/cuts.txt")
- Paleta dominante: $(head -5 "$D/palette.txt" | awk '{printf "%s (%s) ", $1, $2}')

## O que o Claude faz agora (antes de qualquer código)
1. Abrir contact.png e os frames em sequência; descrever o filme plano a plano (o que entra, como, por quanto tempo).
2. Escrever docs/style_guide.md com: paleta (hex), tipografia (família provável, peso, tracking, caixa),
   duração dos planos (use cuts.txt), tipos de transição, movimentos de câmera, textura/grão,
   como o texto entra e sai, relação som × corte.
3. Separar: GRAMÁTICA (pegar) × CONTEÚDO (nunca pegar: logos, personagens, textos, marca do autor).
4. Se houver kit de marca (brand/BRAND.md): a referência dá o ritmo e as transições; a marca dá cores, fontes e logo.
5. Mostrar style_guide.md + shotlist ao usuário e esperar OK.
EOF
echo "✔ $D — $N frames · $(head -1 "$D/cuts.txt")"
echo "  abra $D/contact.png e $D/ANALYSIS.md"
