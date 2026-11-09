#!/usr/bin/env bash
# novo.sh — cria um projeto de EDIÇÃO (material gravado → vídeo editado) e confere o ambiente.
#
#   bash <skill>/scripts/novo.sh <pasta> [--cliente <estudio/brands/cliente>] [--brutos arquivo1 arquivo2 ...]
#
# Estrutura (nunca altere brutos/; tudo que é gerado é versionado _v01, _v02…):
#   brutos/       vídeos gravados (A-roll). Os originais ficam intactos.
#   broll/        planos de apoio do cliente (B-roll próprio).
#   referencias/  vídeos/links de referência de estilo (o "parece com isso").
#   assets/       imagens, vídeos, logos e sons baixados (com licença registrada em docs/CREDITOS.md).
#   motion/       projetos motion-studio de cada item de motion (mo01, mo02…).
#   audio/        voz limpa, trilha, SFX, stems.
#   renders/      saídas versionadas.
#   docs/         BRIEFING, CORTES, MAPA, REVIEW, CREDITOS, ENTREGA (o que o cliente/editor lê).
#   _edit/        estado da máquina: estado.json, briefing.json, words.json, cortes.json, timeline.json, camera.json…
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?uso: novo.sh <pasta> [--cliente <kit>] [--brutos arquivos…]}"; shift
CLIENTE=""; BRUTOS=()
while [[ $# -gt 0 ]]; do case "$1" in
  --cliente) CLIENTE="$2"; shift 2;;
  --brutos) shift; while [[ $# -gt 0 && "$1" != --* ]]; do BRUTOS+=("$1"); shift; done;;
  *) echo "arg desconhecido: $1"; exit 1;; esac; done
[[ -e "$DEST/_edit" ]] && { echo "✗ $DEST já é um projeto (tem _edit/). Use: python3 $SKILL/scripts/estado.py $DEST status"; exit 1; }
mkdir -p "$DEST"/{brutos,broll,referencias,assets,motion,audio,renders,docs/folhas,_edit,fonts}
cp "$SKILL/template/CLAUDE.md" "$DEST/"
cp "$SKILL"/template/docs/*.md "$DEST/docs/"
for f in "${BRUTOS[@]:-}"; do [[ -n "$f" ]] && cp "$f" "$DEST/brutos/"; done
python3 - "$DEST" "$CLIENTE" <<'EOF'
import json, sys, datetime, pathlib
d, cliente = pathlib.Path(sys.argv[1]), sys.argv[2]
json.dump({'criado': datetime.date.today().isoformat(), 'cliente_kit': cliente or None, 'versao': 0,
           'etapas': {k: {'status': 'pendente'} for k in ['briefing', 'preparar', 'cortes', 'mapa', 'assets', 'motion', 'camera', 'legendas', 'som', 'final', 'entrega']}},
          open(d / '_edit/estado.json', 'w'), ensure_ascii=False, indent=1)
EOF
# kit do cliente: fontes (legendas usam TTF/OTF de fonts/), gosto aprovado (PERFIL_EDICAO.md) e marca.json
if [[ -n "$CLIENTE" ]]; then
  [[ -d "$CLIENTE/fonts" ]] && { cp "$CLIENTE"/fonts/*.ttf "$CLIENTE"/fonts/*.otf "$DEST/fonts/" 2>/dev/null || true; }
  [[ -f "$CLIENTE/PERFIL_EDICAO.md" ]] && { echo; cat "$CLIENTE/PERFIL_EDICAO.md"; } >> "$DEST/CLAUDE.md"
  python3 - "$DEST" "$CLIENTE" <<'PY'
import json, sys, pathlib
d, k = pathlib.Path(sys.argv[1]), sys.argv[2]
b = {'cliente_kit': k}
m = pathlib.Path(k) / 'marca.json'
if m.exists(): b['marca'] = json.load(open(m))
json.dump(b, open(d / '_edit/briefing.json', 'w'), ensure_ascii=False, indent=1)
PY
fi
OF="$HOME/.config/orbe/edita-video/APRENDIZADOS.md"
[[ -f "$OF" ]] && echo "  · aprendizados de ofício em $OF — leia antes de editar" 

ok(){ echo "  ✔ $1"; }; no(){ echo "  ✗ $1 — $2"; MISS=1; }; MISS=0
echo "Ambiente:"
command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || no ffmpeg "instale o ffmpeg"
ffmpeg -hide_banner -filters 2>/dev/null | grep -c " ass " >/dev/null && ok "libass (legendas queimadas)" || no libass "ffmpeg sem libass: legendas viram overlay"
python3 -c "import numpy, cv2" 2>/dev/null && ok "python3 + numpy + opencv" || no opencv "pip install numpy opencv-python-headless"
python3 -c "import faster_whisper" 2>/dev/null && ok "faster-whisper (transcrição local por palavra)" || no faster-whisper "pip install faster-whisper"
python3 -c "import fontTools, brotli" 2>/dev/null && ok "fonttools + brotli (fontes das legendas)" || no fonttools "pip install fonttools brotli"
python3 -c "import scipy, PIL" 2>/dev/null && ok "scipy + pillow" || no scipy "pip install scipy pillow"
python3 -c "import mediapipe" 2>/dev/null && ok "mediapipe (texto atrás da pessoa)" || echo "  · opcional: pip install mediapipe (texto atrás da pessoa)"
python3 -c "import opentimelineio" 2>/dev/null && ok "opentimelineio (kit .otio p/ Premiere/Resolve)" || echo "  · opcional: pip install opentimelineio (kit .otio)"
python3 -c "import pycapcut" 2>/dev/null && ok "pycapcut (rascunho CapCut)" || echo "  · opcional: pip install pycapcut pymediainfo (rascunho CapCut)"
command -v node >/dev/null && ok "node (SFX e motion via motion-studio)" || no node "instale Node 20+"
MS=$(python3 -c "import sys; sys.path.insert(0,'$SKILL/scripts'); import evlib; m=evlib.motion_studio(); print(m or '')")
[[ -n "$MS" ]] && ok "motion-studio em $MS (etapa de motion)" || echo "  · motion-studio não encontrado — instale o plugin orbe-video completo ou defina MOTION_STUDIO=<pasta da skill>"
python3 "$SKILL/scripts/modelos.py" --silencioso && ok "modelos (rosto YuNet, ruído RNNoise) em ~/.cache/edita-video" || echo "  · modelos não baixados (rede?) — rosto cai para Haar, ruído para afftdn"
echo "✔ projeto em $DEST"
echo "→ próximo: briefing (references/perguntas.md) → python3 $SKILL/scripts/preparar.py $DEST"
