#!/usr/bin/env bash
# qa.sh — inspeção objetiva de um vídeo renderizado. Gera imagens para você OLHAR e um relatório com métricas.
#
#   bash qa.sh out/final.mp4 [--strip 4.2] [--loop]
# Saídas em out/qa/: contact.png (2 fps) · phone.png (390px = largura real de um celular; LEIA as legendas nele, 1 fps) · poster.png · strip.png · loop_check.mp4 · qa.md
# Métricas: tempo morto (freezedetect), frames pretos, cortes e toques por segundo, varredura de pops, loudness, specs.
set -euo pipefail
V="$1"; shift
STRIP=""; LOOP=0
while [[ $# -gt 0 ]]; do case "$1" in --strip) STRIP="$2"; shift 2;; --loop) LOOP=1; shift;; *) shift;; esac; done
D="$(dirname "$V")/qa"; mkdir -p "$D"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
WH=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$V" | sed 's/,$//')
ROWS=$(python3 -c "import math;print(math.ceil($DUR*2/6))")

ffmpeg -v error -y -i "$V" -vf "fps=2,scale=270:-1,tile=6x${ROWS}:padding=4:color=0x1b1b1b" -frames:v 1 "$D/contact.png"
PR=$(python3 -c "import math;print(math.ceil($DUR/5))")
ffmpeg -v error -y -i "$V" -vf "fps=1,scale=390:-1,tile=5x${PR}:padding=6:color=0x1b1b1b" -frames:v 1 "$D/phone.png"
ffmpeg -v error -y -ss "$(python3 -c "print(round($DUR*0.3,2))")" -i "$V" -frames:v 1 "$D/poster.png"
if [[ -n "$STRIP" ]]; then
  ffmpeg -v error -y -ss "$(python3 -c "print(max(0,$STRIP-0.1))")" -i "$V" -vf "scale=320:-1,tile=12x1:padding=4" -frames:v 1 "$D/strip.png"
fi
if [[ $LOOP -eq 1 ]]; then ffmpeg -v error -y -stream_loop 1 -i "$V" -c copy "$D/loop_check.mp4"; fi

# tempo morto: trechos > 0.6s sem mudança visível
FREEZE=$(ffmpeg -hide_banner -i "$V" -vf "freezedetect=n=0.003:d=0.6" -map 0:v -f null - 2>&1 | python3 -c "
import sys,re
ev=re.findall(r'freeze_(start|end): ([0-9.]+)',sys.stdin.read()); out=[];st=None
for k,v in ev:
    if k=='start': st=float(v)
    elif st is not None: out.append((st,float(v))); st=None
if st is not None: out.append((st,$DUR))
print('\\n'.join((f'  - ⚠ {a:.2f}s → {b:.2f}s ({b-a:.2f}s) TEMPO MORTO: nada novo por mais de 2 s' if b-a>2 else f'  - {a:.2f}s → {b:.2f}s ({b-a:.2f}s) segurando (ok se for leitura de texto ou pausa intencional)') for a,b in out))" || true)
BLACK=$(ffmpeg -hide_banner -i "$V" -vf "blackdetect=d=0.1:pix_th=0.05" -an -f null - 2>&1 | grep -oE "black_start:[0-9.]+ black_end:[0-9.]+" | sed 's/^/  - /' || true)
CUTS=$(ffmpeg -hide_banner -i "$V" -vf "select='gt(scene,0.25)',showinfo" -an -f null - 2>&1 | grep -c "pts_time" || true)
HASAUD=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$V" | head -1)
LUF="(sem áudio)"; if [[ -n "$HASAUD" ]]; then LUF=$(ffmpeg -hide_banner -i "$V" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2" LUFS"}'); fi
MONO=""; if [[ -n "$HASAUD" ]]; then
  LM=$(ffmpeg -hide_banner -i "$V" -af "pan=mono|c0=0.5*c0+0.5*c1,ebur128" -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
  MONO=$(python3 -c "s='$LUF'.split()[0]; m='$LM'; d=float(m)-float(s)+3.01 if s not in ('(sem','') and m else None; print('' if d is None else f'- Mono (alto-falante de celular): {d:+.1f} dB vs estéreo ' + ('✔' if d > -3 else '⚠ some no mono — fase invertida/largura demais na trilha'))" 2>/dev/null || true)
fi
RATE=$(python3 -c "print(round($CUTS/$DUR,2) if $DUR>0 else 0)")

# flashes (WCAG 2.3.1: no máx. 3 por segundo) e emenda do loop — por luminância de quadros reduzidos
FPSV=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$V" | python3 -c "import sys;n,d=sys.stdin.read().strip().rstrip(',').split('/');print(float(n)/float(d))")
FLASH=$(python3 - "$V" "$FPSV" "$LOOP" <<'PY'
import sys, subprocess, numpy as np
v, fps, loop = sys.argv[1], float(sys.argv[2]), sys.argv[3] == '1'
p = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',v],capture_output=True,text=True).stdout.strip().split(',')
w, h = 96, int(round(96 * int(p[1]) / int(p[0]) / 2) * 2)
raw = subprocess.run(['ffmpeg','-v','error','-i',v,'-vf',f'scale={w}:{h},format=gray','-f','rawvideo','-'],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(float) / 255
lum = fr.mean((1, 2)) ** 2.2                      # luminância relativa aproximada (tela inteira)
d = np.diff(lum); ev = []                          # transições ≥ 10% com a parte escura < 0,8
for i, x in enumerate(d):
    if abs(x) >= 0.1 and min(lum[i], lum[i + 1]) < 0.8: ev.append((i, np.sign(x)))
flashes = [ev[k][0] for k in range(1, len(ev)) if ev[k][1] != ev[k - 1][1]]   # par de mudanças opostas = 1 flash
worst = max([sum(1 for f in flashes if a <= f < a + fps) for a in range(len(lum))] or [0])
out = [f'- Flashes: pior janela de 1 s = {worst} ' + ('⚠ acima de 3/s (WCAG) — reduza piscadas/inversões de tela cheia' if worst > 3 else '✔ (≤ 3/s, WCAG)')]
if loop:
    md = np.abs(np.diff(fr, axis=0)).mean((1, 2)); seam = np.abs(fr[-1] - fr[0]).mean(); med = np.median(md[md > 0]) if (md > 0).any() else 0
    ok = seam <= max(3 * med, 0.004)
    out.append(f'- Emenda do loop: último→primeiro = {seam:.4f} · mediana entre frames = {med:.4f} ' + ('✔' if ok else '⚠ salto na emenda — o último frame (N-1) precisa fluir para o frame 0; renderize 0..N-1 com ciclos inteiros'))
# varredura de pops: quadro cuja diferença para o anterior é 3x a dos vizinhos. Pega o salto de 1 frame que a contact sheet perde.
md = np.abs(np.diff(fr, axis=0)).mean((1, 2))
viz = np.array([np.median(np.r_[md[max(0, i - 6):i], md[i + 1:i + 7]]) for i in range(len(md))])
pops = [(i + 1) / fps for i in range(len(md)) if md[i] > 3 * viz[i] and md[i] > 0.005]
out.append(f'- Pops de 1 frame: {len(pops)} ' + ('✔' if not pops else '⚠ confira quadro a quadro (contato e corte proposital passam): ' + ', '.join(f'{t:.2f}s' for t in pops[:12])))
# flash de 1 frame: n difere dos DOIS vizinhos, mas n-1 ≈ n+1 (a varredura de pops deixa passar quando dois diffs grandes ficam lado a lado)
fl1 = [i / fps for i in range(1, len(fr) - 1) if md[i - 1] > 0.02 and md[i] > 0.02 and np.abs(fr[i + 1] - fr[i - 1]).mean() < 0.35 * min(md[i - 1], md[i])]
out.append(f'- Frame intruso (n ≠ vizinhos, n−1 ≈ n+1): {len(fl1)} ' + ('✔' if not fl1 else '⚠ um frame "pisca" algo que não devia: ' + ', '.join(f'{t:.2f}s' for t in fl1[:10])))
# DECK TRAP: % de pixels que mudam em janelas de 2 s. Filmes fortes ficam em 14–30%; slide parado animado fica em 9–12%.
k2 = int(round(2 * fps)); hold = int(round(1.5 * fps))
if len(fr) > k2 + hold:
    ch = np.array([(np.abs(fr[i + k2] - fr[i]) > 0.04).mean() for i in range(0, len(fr) - k2 - hold, max(1, int(fps // 2)))])
    low = [i * max(1, int(fps // 2)) / fps for i, c in enumerate(ch) if c < 0.12]
    out.append(f'- Mudança visual por janela de 2 s (Deck Trap): mediana {100*np.median(ch):.0f}% · mínima {100*ch.min():.0f}% ' + ('✔ (alvo 14–30%)' if np.median(ch) >= 0.14 and not low else '⚠ trechos com cara de slide (<12%): ' + ', '.join(f'{t:.1f}s' for t in low[:8]) + ' — algo novo precisa acontecer (câmera, objeto, corte), não só texto'))
if loop and len(fr) > 3:
    vin, vout = np.abs(fr[1] - fr[0]).mean(), np.abs(fr[-1] - fr[-2]).mean()
    out.append(f'- Velocidade na emenda: saída {vout:.4f} · entrada {vin:.4f} ' + ('✔' if abs(vin - vout) <= max(0.002, 0.5 * max(vin, vout)) else '⚠ o movimento muda de velocidade na volta — some as caudas de mola dos ciclos anteriores no frame 0'))
print(chr(10).join(out))
PY
)

# toques por segundo: filme sem corte é legítimo; o ritmo aparece nos eventos sonoros
TOQUES="(sem áudio)"; if [[ -n "$HASAUD" ]]; then
  TMPW="$D/.qa_audio.wav"; ffmpeg -v error -y -i "$V" -map 0:a -ac 1 -ar 22050 "$TMPW"
  TOQUES=$(python3 "$(cd "$(dirname "$0")" && pwd)/beats.py" "$TMPW" 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(round(len(d.get('hits',[]))/max(d.get('duration',1),0.1),2),'/s, BPM',d.get('bpm'))" || echo "(não medido)"); rm -f "$TMPW"
fi

cat > "$D/qa.md" <<EOF
# QA — $(basename "$V")
- Specs: ${WH} · ${DUR}s · áudio: ${HASAUD:-nenhum} · loudness: ${LUF} (alvo -14)
- Cortes/mudanças fortes detectados: ${CUTS} (${RATE}/s) — referência para filme com cortes, reel/ad: 0.3–0.6/s · story: 0.1–0.3/s. Filme de uma câmera só pode ter 0.
- Toques: ${TOQUES} — filmes de produto fortes medidos em 03/11/2026 ficam perto de 4,3/s (references/estudo-prompt-motion.md)
- Trechos parados (>0.6s; ⚠ = tempo morto >2s):
${FREEZE:-  - nenhum ✔}
- Frames pretos:
${BLACK:-  - nenhum ✔}
${FLASH}
${MONO}

Agora ABRA contact.png, phone.png e poster.png e faça a crítica (references/critique.md).
EOF
cat "$D/qa.md"
echo "imagens em $D/"
