#!/usr/bin/env bash
# mix.sh — junta vídeo mudo + trilha + SFX (+ voz opcional), normaliza para -14 LUFS / -1 dBTP e entrega o MP4 final.
#
#   bash mix.sh out/silent.mp4 out/final.mp4 [--music audio/music.wav] [--sfx audio/sfx.wav] [--voice audio/voice.wav]
#               [--music-db -3] [--sfx-db 0] [--voice-db 0] [--lufs -14] [--stems]
# --stems: entrega também <saída>_sem_musica.mp4 (voz+SFX) e <saída>_so_musica.mp4 — o cliente troca a trilha sem pedir render.
# Com voz: a música é abaixada automaticamente (sidechain) quando a voz fala.
set -euo pipefail
VIDEO="$1"; OUT="$2"; shift 2
MUSIC=""; SFX=""; VOICE=""; MDB=-3; SDB=0; VDB=0; LUFS=-14; STEMS=0
while [[ $# -gt 0 ]]; do case "$1" in
  --music) MUSIC="$2"; shift 2;; --sfx) SFX="$2"; shift 2;; --voice) VOICE="$2"; shift 2;;
  --music-db) MDB="$2"; shift 2;; --sfx-db) SDB="$2"; shift 2;; --voice-db) VDB="$2"; shift 2;; --lufs) LUFS="$2"; shift 2;; --stems) STEMS=1; shift;;
  *) echo "arg desconhecido: $1"; exit 1;; esac; done

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
IN=(-i "$VIDEO"); FC=""; n=1; LABELS=()
if [[ -n "$MUSIC" ]]; then IN+=(-i "$MUSIC"); FC+="[$n:a]volume=${MDB}dB,aformat=sample_rates=48000:channel_layouts=stereo[m];"; LABELS+=(m); n=$((n+1)); fi
if [[ -n "$SFX" ]];   then IN+=(-i "$SFX");   FC+="[$n:a]volume=${SDB}dB,aformat=sample_rates=48000:channel_layouts=stereo[s];"; LABELS+=(s); n=$((n+1)); fi
if [[ -n "$VOICE" ]]; then
  IN+=(-i "$VOICE"); FC+="[$n:a]volume=${VDB}dB,aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][vk];"; n=$((n+1))
  if [[ -n "$MUSIC" ]]; then FC+="[m][vk]sidechaincompress=threshold=0.02:ratio=20:attack=60:release=350:mix=0.6[md];"; LABELS=("${LABELS[@]/m/md}"); else FC+="[vk]anullsink;"; fi
  LABELS+=(v)
fi
[[ ${#LABELS[@]} -eq 0 ]] && { echo "nenhum áudio informado"; exit 1; }
MIXIN=""; for l in "${LABELS[@]}"; do MIXIN+="[$l]"; done
FC+="${MIXIN}amix=inputs=${#LABELS[@]}:normalize=0:duration=longest,atrim=0:${DUR},afade=t=out:st=$(python3 -c "print($DUR-0.25)"):d=0.25[pre]"

# passo 1: medir loudness
TMP=$(mktemp -d)
ffmpeg -v error -y "${IN[@]}" -filter_complex "$FC" -map "[pre]" -c:a pcm_f32le "$TMP/pre.wav"
STATS=$(ffmpeg -hide_banner -i "$TMP/pre.wav" -af loudnorm=I=$LUFS:TP=-2.2:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$STATS" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
# passo 2+3: ganho até o alvo, limitador oversampled, AAC e MEDIR o MP4 decodificado. O loudnorm linear corta o ganho quando
# um hit passaria do teto e o filme fica 2 dB abaixo; aqui quem segura o pico é o limitador, e o laço corrige pelo medido.
# O AAC sobe o pico de forma variável (medido: +0,9 a +1,6 dB): se passar de −1 dBTP, baixa o limitador.
LIM_DB=-2.2; TRY=0; GAIN=$(python3 -c "print(round($LUFS - ($(g input_i)), 2))")
while :; do
  LIM=$(python3 -c "print(round(10**($LIM_DB/20),4))")
  ffmpeg -v error -y -i "$TMP/pre.wav" -af "volume=${GAIN}dB,aresample=192000,alimiter=limit=$LIM:attack=1:release=50:level=false,aresample=48000" "$TMP/norm.wav"
  ffmpeg -v error -y -i "$VIDEO" -i "$TMP/norm.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT"
  MED=$(ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1)
  TP=$(echo "$MED" | grep -A1 "True peak" | grep -oE "\-?[0-9.]+ dBFS" | tail -1 | awk '{print $1}')
  FINAL=$(echo "$MED" | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
  TRY=$((TRY+1))
  python3 -c "import sys; sys.exit(0 if float('${TP:--99}') <= -1.0 and abs(${FINAL:-0} - ($LUFS)) <= 0.3 else 1)" && break
  [[ $TRY -ge 4 ]] && break
  GAIN=$(python3 -c "print(round($GAIN + ($LUFS) - (${FINAL:-0}), 2))")
  python3 -c "import sys; sys.exit(0 if float('${TP:--99}') > -1.0 else 1)" && LIM_DB=$(python3 -c "print(round($LIM_DB - (${TP} + 1.0) - 0.3, 2))")
done
rm -rf "$TMP"
echo "✔ $OUT · ${DUR}s · loudness integrado ${FINAL} LUFS (alvo $LUFS) · true peak decodificado ${TP} dBTP (limitador ${LIM_DB} dBTP, ${TRY} passada(s))"
if [[ $STEMS -eq 1 ]]; then
  SELF="$(cd "$(dirname "$0")" && pwd)/mix.sh"; B="${OUT%.mp4}"
  if [[ -n "$SFX$VOICE" ]]; then A=(); [[ -n "$SFX" ]] && A+=(--sfx "$SFX" --sfx-db "$SDB"); [[ -n "$VOICE" ]] && A+=(--voice "$VOICE" --voice-db "$VDB")
    bash "$SELF" "$VIDEO" "${B}_sem_musica.mp4" "${A[@]}" --lufs "$LUFS" | tail -1; fi
  [[ -n "$MUSIC" ]] && bash "$SELF" "$VIDEO" "${B}_so_musica.mp4" --music "$MUSIC" --music-db "$MDB" --lufs "$LUFS" | tail -1
fi
