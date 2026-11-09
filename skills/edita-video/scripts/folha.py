#!/usr/bin/env python3
"""folha.py — folha de contato rotulada de qualquer vídeo (para o Claude OLHAR o resultado, não imaginar).

    python3 folha.py <video> [--n 12] [--tempos 0.5,3.2,7] [--cortes <projeto>] [--saida folha.jpg] [--largura 300] [--ui]

--cortes <projeto>: um quadro 0,15 s antes e 0,15 s depois de cada corte e de cada entrada/saída de item do mapa
(é onde mora flash, pulo de legenda, overlay errado). --ui desenha a zona da interface do Reels (topo 14%, base 22%,
trilho direito) por cima, para conferir legenda/peças fora dela.
"""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np, cv2
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
V = Path(A[0]); pr = E.ffprobe(V); vs = next(s for s in pr['streams'] if s['codec_type'] == 'video')
W, H = int(vs['width']), int(vs['height']); dur = float(pr['format']['duration'])
LW = int(opt('largura', 300)); LH = int(LW * H / W)
if opt('tempos'): ts = [float(x) for x in opt('tempos').split(',')]
elif opt('cortes'):
    P = Path(opt('cortes')); tl = E.jload(P / '_edit/timeline.json'); mp = E.jload(P / '_edit/mapa.json', {}) or {}
    marcas = [s['seq_in'] for s in tl['segmentos'][1:]] + [x for it in mp.get('itens', []) if it.get('t_ini') is not None for x in (it['t_ini'], it['t_fim'])]
    ts = sorted({round(m + d, 2) for m in marcas for d in (-0.15, 0.15) if 0 <= m + d < dur})
else:
    n = int(opt('n', 12)); ts = [dur * (i + 0.5) / n for i in range(n)]
tiles = []
for t in ts:
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(V), '-frames:v', '1', '-vf', f'scale={LW}:{LH}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    if len(r.stdout) != LW * LH * 3: continue
    im = np.frombuffer(r.stdout, np.uint8).reshape(LH, LW, 3).copy()
    if '--ui' in A and H > W:
        ov = im.copy(); cv2.rectangle(ov, (0, 0), (LW, int(0.14 * LH)), (0, 0, 255), -1); cv2.rectangle(ov, (0, int(0.78 * LH)), (LW, LH), (0, 0, 255), -1)
        cv2.rectangle(ov, (int(0.86 * LW), int(0.45 * LH)), (LW, LH), (0, 0, 255), -1); im = cv2.addWeighted(ov, 0.25, im, 0.75, 0)
    cv2.rectangle(im, (0, 0), (LW, 26), (0, 0, 0), -1)
    cv2.putText(im, f'{int(t // 60)}:{t % 60:05.2f}', (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (59, 212, 255), 1, cv2.LINE_AA)
    tiles.append(im)
cols = int(opt('colunas', 6 if H > W else 4)); rows = (len(tiles) + cols - 1) // cols
sheet = np.full((rows * (LH + 4), cols * (LW + 4), 3), 15, np.uint8)
for k, im in enumerate(tiles): y, x = (k // cols) * (LH + 4), (k % cols) * (LW + 4); sheet[y:y + LH, x:x + LW] = im
out = Path(opt('saida') or V.with_name(V.stem + '_folha.jpg')); cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
print(f'✔ {out} ({len(tiles)} quadros)')
