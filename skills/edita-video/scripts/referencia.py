#!/usr/bin/env python3
"""referencia.py — desmonta um vídeo de REFERÊNCIA em números + folhas para o Claude estudar a gramática (nunca copiar).

    python3 referencia.py <projeto> <url|arquivo> [--nome ref1]

URL: baixa com yt-dlp (instala com pip se faltar). Se a rede bloquear (Instagram/TikTok costumam exigir login), peça
o arquivo ao usuário (baixar no celular/Mac e anexar) ou abra no navegador e capture quadros — nunca invente a referência.
Mede: duração · cortes/min e duração média de plano (scdet) · fala (palavras/min, pausas p50/p90, maior pausa) ·
loudness · gancho (o que muda nos 3 s iniciais) · paleta. Folhas: 1 quadro a cada 0,5 s nos 3 s iniciais e 1/s depois,
mais 1 quadro em cada corte → referencias/<nome>/folha.jpg e cortes.jpg.
Depois de OLHAR as folhas, preencha a seção "O que eu vi" de docs/REFERENCIA.md (legenda: palavras/bloco, caixa, cor
da palavra ativa, posição; zooms; B-roll; motion; transições; cor; trilha/SFX) e traduza em ajustes no briefing.
"""
import sys, os, re, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0]); SRC = A[1]
nome = opt('nome') or f"ref{len(list((P / 'referencias').glob('ref*/'))) + 1}"
D = P / 'referencias' / nome; D.mkdir(parents=True, exist_ok=True)
if re.match(r'^https?://', SRC):
    if not shutil.which('yt-dlp'):
        try: import yt_dlp  # noqa
        except ImportError: subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--break-system-packages', 'yt-dlp'], capture_output=True)
    cmd = (['yt-dlp'] if shutil.which('yt-dlp') else [sys.executable, '-m', 'yt_dlp']) + ['-q', '-f', 'mp4/bestvideo[height<=1920]+bestaudio/best', '--merge-output-format', 'mp4', '-o', str(D / 'source.%(ext)s'), SRC]
    r = subprocess.run(cmd, capture_output=True, text=True)
    vid = next(iter(D.glob('source.*')), None)
    if r.returncode or not vid:
        (D / 'LINK.txt').write_text(SRC + '\n')
        E.die(f"não consegui baixar ({(r.stderr or '').strip()[-160:]}).\n→ Peça o ARQUIVO ao usuário (baixar e anexar) ou abra o link no navegador e capture quadros. Link salvo em {D / 'LINK.txt'}")
else:
    vid = D / ('source' + Path(SRC).suffix.lower()); shutil.copy(SRC, vid)
pr = E.ffprobe(vid); vs = next(s for s in pr['streams'] if s['codec_type'] == 'video'); dur = float(pr['format']['duration'])
w, h = int(vs['width']), int(vs['height']); tem_audio = any(s['codec_type'] == 'audio' for s in pr['streams'])
# cortes (scdet)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(vid), '-vf', 'scale=320:-2,scdet=threshold=12', '-an', '-f', 'null', '-'], capture_output=True, text=True)
cortes = sorted({round(float(x), 2) for x in re.findall(r'lavfi\.scd\.time:\s*([\d.]+)', r.stderr)})
planos = np.diff([0] + cortes + [dur]) if dur else np.array([dur])
# fala
fala = {}
if tem_audio:
    wav = D / 'a16k.wav'; E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(vid), '-ac', '1', '-ar', '16000', str(wav)])
    try:
        from faster_whisper import WhisperModel
        wm = WhisperModel('small', device='cpu', compute_type='int8')
        segs, _ = wm.transcribe(E.load_wav(wav, 16000), language='pt', word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
        ws = [x for s in segs for x in (s.words or [])]
        if ws:
            gaps = np.array([b.start - a.end for a, b in zip(ws, ws[1:])]); gaps = gaps[gaps > 0.02]
            fala = {'palavras': len(ws), 'ppm': len(ws) / max(1e-6, (ws[-1].end - ws[0].start) / 60), 'p50': float(np.percentile(gaps, 50)) if len(gaps) else 0,
                    'p90': float(np.percentile(gaps, 90)) if len(gaps) else 0, 'max': float(gaps.max()) if len(gaps) else 0, 'texto': ' '.join(x.word.strip() for x in ws)[:600]}
    except Exception as e: fala = {'erro': str(e)[:80]}
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(vid), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True)
    lufs = (re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr) or ['?'])[-1]
else: lufs = '—'
# folhas
S = E.SKILL / 'scripts'
ts = [round(x, 2) for x in np.arange(0, min(3, dur), 0.5)] + [round(x, 2) for x in np.arange(3, dur, 1.0)]
subprocess.run([sys.executable, str(S / 'folha.py'), str(vid), '--tempos', ','.join(map(str, ts)), '--largura', '200', '--colunas', '8', '--saida', str(D / 'folha.jpg')], capture_output=True)
if cortes: subprocess.run([sys.executable, str(S / 'folha.py'), str(vid), '--tempos', ','.join(f'{c + 0.12:.2f}' for c in cortes[:48]), '--largura', '200', '--colunas', '8', '--saida', str(D / 'cortes.jpg')], capture_output=True)
# paleta (k-means em quadros espaçados)
try:
    import cv2
    fr = []
    for t in np.linspace(0.5, max(0.6, dur - 0.5), 8):
        o = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', str(vid), '-frames:v', '1', '-vf', 'scale=96:-2', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        if o: fr.append(np.frombuffer(o, np.uint8).reshape(-1, 3))
    X = np.concatenate(fr).astype(np.float32); _, lab, cen = cv2.kmeans(X, 6, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.ravel(), minlength=6); pal = [('#%02X%02X%02X' % tuple(int(v) for v in cen[i]), cnt[i] / cnt.sum()) for i in np.argsort(-cnt)]
except Exception: pal = []
cpm = len(cortes) / max(dur / 60, 1e-6)
sug = []
if fala.get('p90'): sug.append(f"pausa_max ≈ {min(0.5, max(0.2, fala['p90'])):.2f} s (p90 das pausas da referência)")
if len(planos): sug.append(f"plano médio {planos.mean():.1f} s → {'dinamico (punch a cada ~3 s, B-roll a cada 4–6 s)' if planos.mean() < 2.5 else 'educativo/clinica (punch a cada 4–8 s)' if planos.mean() < 5 else 'luxo/calmo'}")
L = [f'# Referência — {nome}', '', f'Fonte: {SRC}', f'- {w}×{h} · {dur:.1f}s · {"vertical" if h > w else "horizontal"} · {lufs} LUFS',
     f'- cortes: {len(cortes)} ({cpm:.0f}/min) · plano médio {planos.mean():.2f}s · mais longo {planos.max():.1f}s' if len(planos) else '- cortes: —']
if fala.get('palavras'): L.append(f"- fala: {fala['ppm']:.0f} palavras/min · pausas p50 {fala['p50']:.2f}s · p90 {fala['p90']:.2f}s · maior {fala['max']:.2f}s")
if pal: L.append('- paleta: ' + ' · '.join(f'{h_} {100 * p:.0f}%' for h_, p in pal))
L += ['', '## Sugestões numéricas', *(f'- {s}' for s in sug), '', '## O que eu vi (preencha OLHANDO folha.jpg e cortes.jpg)', '',
      '- Gancho (0–3 s): ', '- Legenda: palavras por bloco · caixa · fonte (peso) · cor da palavra ativa · posição (y) · animação: ',
      '- Câmera: zoom alternado? punch-in em quê? ', '- B-roll / fotos: frequência, duração, tela cheia × split: ', '- Motion: tipos de peça, cores, entrada/saída: ',
      '- Transições: ', '- Cor: ', '- Trilha / SFX: ', '- O que NÃO copiar (marca/conteúdo do outro): ', '',
      f"Folhas: referencias/{nome}/folha.jpg · referencias/{nome}/cortes.jpg"]
if fala.get('texto'): L += ['', '## Fala (para entender a estrutura, não para copiar)', '', fala['texto']]
out = P / 'docs' / f'REFERENCIA_{nome}.md'; out.write_text('\n'.join(L) + '\n', encoding='utf-8')
E.jsave(D / 'medidas.json', {'dur': dur, 'w': w, 'h': h, 'cortes': cortes, 'fala': {k: v for k, v in fala.items() if k != 'texto'}, 'lufs': lufs, 'paleta': pal})
print('\n'.join(L[:10] + L[11:14])); print(f'→ ABRA referencias/{nome}/folha.jpg e cortes.jpg e preencha "O que eu vi" em {out.relative_to(P)}')
