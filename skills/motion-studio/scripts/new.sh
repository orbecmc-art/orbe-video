#!/usr/bin/env bash
# new.sh — cria um projeto de filme autocontido, SEMPRE numa pasta nova (o modelo não deve ver nem alterar filmes anteriores).
#
#   bash <skill>/scripts/new.sh <pasta> [--kind film|cartoon] [--brand <estudio/brands/cliente>] [--fonts "slug:pesos" ...]
#   --kind cartoon → SÉRIE COM PERSONAGEM (references/cartoon.md): scenes.json + hero/ + scenes/NN.js + voz→tempo→animação
#
# Estrutura de estúdio recomendada (agência com vários clientes):
#   estudio/brands/<cliente>/   BRAND.md, logo.svg, fonts/, assets/, approved/   ← kit reutilizável
#   estudio/filmes/<AAAA-MM-DD>-<cliente>-<nome>/                                ← um projeto por filme (este script)
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?uso: new.sh <pasta> [--brand <dir>] [--fonts spec...]}"; shift || true
BRAND=""; FONTS=(); KIND=film
while [[ $# -gt 0 ]]; do case "$1" in
  --brand) BRAND="$2"; shift 2;;
  --kind) KIND="$2"; shift 2;;
  --fonts) shift; while [[ $# -gt 0 && "$1" != --* ]]; do FONTS+=("$1"); shift; done;;
  *) echo "arg desconhecido: $1"; exit 1;; esac; done
[[ -e "$DEST/index.html" ]] && { echo "✗ $DEST já tem um filme — use uma pasta NOVA para cada filme."; exit 1; }
mkdir -p "$DEST"/{lib,scripts,docs,audio,assets,refs,out,fonts,brand}
if [[ "$KIND" == cartoon ]]; then
  mkdir -p "$DEST"/{scenes,hero,models,audio/lines}
  cp "$SKILL/template/cartoon/index.html" "$SKILL/template/cartoon/scenes.json" "$SKILL/template/CLAUDE.md" "$DEST/"
  cp "$SKILL"/template/cartoon/lib/*.js "$DEST/lib/"; cp "$SKILL"/template/cartoon/scenes/*.js "$DEST/scenes/"; cp "$SKILL"/template/cartoon/hero/*.json "$DEST/hero/"
  cp "$SKILL/template/campaign.json" "$DEST/campaign.json"
  cp "$SKILL"/scripts/{voice.py,clips.mjs} "$DEST/scripts/"
  cat >> "$DEST/CLAUDE.md" <<'EOF'

## Este projeto é uma SÉRIE COM PERSONAGEM (references/cartoon.md da skill)
- Ordem: roteiro em `scenes.json` → `python3 scripts/voice.py` (voz, tempo de cada cena, palavras, bocas, ênfases) → animação.
  Nunca anime antes da voz existir: a duração de cada cena é a duração da FALA + respiro.
- O herói está TRAVADO em `hero/hero.json` (cores, proporções, assinatura). Episódio novo não redesenha o personagem.
- Cada cena vive em `scenes/NN.js`. Pedido "3, câmera mais perto" mexe só na 03; `node scripts/clips.mjs --only 03` re-renderiza só ela.
- Pés do herói em `FLOOR`; legendas abaixo do chão (`CAPTION_Y`), nunca sobre o corpo. Topo 120 px e base 320 px são do app.
- Rascunho: `node scripts/clips.mjs` (30 fps, cache por cena) · final: render + music + sfx + mix com `--voice audio/voice.wav`.
EOF
else
  cp "$SKILL/template/index.html" "$SKILL/template/CLAUDE.md" "$SKILL/template/campaign.json" "$DEST/"
fi
cp "$SKILL"/template/lib/{motion.js,recorder.js} "$DEST/lib/"
cp "$SKILL"/template/docs/*.md "$DEST/docs/"
cp "$SKILL"/scripts/{render.mjs,stills.mjs,pw.mjs,sfx.mjs,music.mjs,beats.py,mix.sh,qa.sh,fonts.sh,ref.sh,brand.sh,campaign.mjs,audit-audio.py,export.sh,exporta-rota.mjs,prove.mjs,bundle.mjs} "$DEST/scripts/"
cp "$SKILL"/template/audio/{compor.py,medir.py} "$DEST/audio/"
: > "$DEST/fonts/fonts.css"

if [[ -n "$BRAND" ]]; then
  [[ -d "$BRAND" ]] || { echo "✗ kit de marca não encontrado: $BRAND"; exit 1; }
  cp -R "$BRAND"/. "$DEST/brand/"
  if [[ -d "$BRAND/fonts" ]]; then cp "$BRAND"/fonts/*.woff2 "$DEST/fonts/" 2>/dev/null || true; [[ -s "$BRAND/fonts/fonts.css" ]] && cp "$BRAND/fonts/fonts.css" "$DEST/fonts/fonts.css"; fi
  cat >> "$DEST/CLAUDE.md" <<EOF

## Marca deste filme
Leia \`brand/BRAND.md\` ANTES de qualquer decisão de look. Logo, cores, fontes, personalidade de movimento e som vêm de lá,
mesmo que uma referência nova seja usada (a referência dá a gramática; a marca dá a identidade).
Os itens "Proibido para este cliente" entram na linha BANNED do docs/SPEC.md.
EOF
  echo "✔ marca carregada de $BRAND"
else
  cp "$SKILL/template/BRAND.md" "$DEST/brand/BRAND.md"
fi
cat > "$DEST/.gitignore" <<'EOF'
out/
node_modules/
.env
EOF
printf '# Chaves opcionais (nunca cole chaves em prompts)\nELEVENLABS_API_KEY=\nFAL_KEY=\n' > "$DEST/.env.example"
[[ ${#FONTS[@]} -gt 0 ]] && ( cd "$DEST" && bash scripts/fonts.sh "${FONTS[@]}" )

ok() { printf "  ✔ %s\n" "$1"; }; no() { printf "  ✗ %s — %s\n" "$1" "$2"; }
# campanha: nome do projeto = nome da pasta; campaign.js para o preview abrir direto
python3 - "$DEST" <<'PY'
import json, sys, os
d = sys.argv[1]; p = os.path.join(d, 'campaign.json'); c = json.load(open(p))
c['project'] = os.path.basename(os.path.abspath(d)); json.dump(c, open(p, 'w'), ensure_ascii=False, indent=2)
PY
( cd "$DEST" && node scripts/campaign.mjs sync >/dev/null 2>&1 ) || true
echo "✔ projeto criado em $DEST"
command -v node >/dev/null && ok "node $(node -v)" || no node "instale Node 20+"
command -v ffmpeg >/dev/null && ok "ffmpeg" || no ffmpeg "brew install ffmpeg / apt install ffmpeg"
python3 -c "import numpy" 2>/dev/null && ok "python3 + numpy" || no numpy "pip install numpy"
if [[ "$KIND" == cartoon ]]; then
  python3 -c "import piper" 2>/dev/null && ok "piper-tts (voz offline)" || no piper-tts "pip install piper-tts + voz pt_BR em models/ (references/cartoon.md §Voz) — ou grave audio/lines/NN.wav"
  python3 -c "import faster_whisper" 2>/dev/null && ok "faster-whisper (palavra a palavra)" || no faster-whisper "pip install faster-whisper (sem ele, legendas por estimativa)"
  command -v rhubarb >/dev/null && ok "rhubarb (lip sync fonético)" || echo "  · rhubarb ausente — boca por texto+volume (bom); instale o Rhubarb Lip Sync para o melhor"
fi
( cd "$DEST" && node -e "import('./scripts/pw.mjs').then(()=>process.exit(0))" >/dev/null 2>&1 ) && ok "playwright" || no playwright "npm i -D playwright && npx playwright install chromium"
[[ "$KIND" == cartoon ]] && echo "→ roteiro em scenes.json; depois: cd $DEST && python3 scripts/voice.py && node scripts/clips.mjs"
echo "→ preview: abra $DEST/index.html no navegador (espaço = play/pause, ←/→ = frame, Shift = batida)"
