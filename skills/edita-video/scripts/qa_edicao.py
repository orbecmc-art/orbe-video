#!/usr/bin/env python3
"""qa_edicao.py — o Claude não assiste: MEDE e OLHA. Roda depois de cada versão (final.py chama sozinho).

    python3 qa_edicao.py <projeto> <renders/x_v01.mp4> [--rapido]

Checagens (✗ bloqueia a entrega, ⚠ vai no relatório):
  ✗ duração vídeo × áudio × timeline (±1 quadro) · ✗ loudness fora do alvo ±1 LU ou pico > −1 dBTP depois do AAC
  ✗ VOZ NO MIX: retranscreve o MP4 final e compara com a timeline (palavras faltando = trecho mudo/cortado)
  ✗ clique nas emendas da voz (salto de amostra > 8× o local) · ⚠ quadro preto/congelado não planejado
  ⚠ legenda na zona da interface (topo 14%, base 22%) ou embaixo de peça · ⚠ rosto fora do recorte
  ⚠ "Deck Trap": > 5 s sem mudança visual (corte, item, punch) · ⚠ sincronia dos SFX (audit-audio do motion-studio)
Gera docs/QA.md e as folhas docs/folhas/<versão>_folha.jpg (12 quadros + zonas da UI) e _cortes.jpg (±0,15 s de
cada corte/item). ABRA AS DUAS FOLHAS com Read antes de mostrar ao cliente.
"""
import sys, os, re, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0]); V = Path(A[1]) if len(A) > 1 and not A[1].startswith('--') else sorted((P / 'renders').glob('*_v[0-9][0-9].mp4'))[-1]
V = V if V.is_absolute() else (P / V if (P / V).exists() else V.resolve())
B, EST, ESTILO = E.config(P); tl = E.jload(P / '_edit/timeline.json'); FPS = tl['fps']; DUR = tl['duracao']
mapa = E.jload(P / '_edit/mapa.json', {}) or {}; leg = E.jload(P / '_edit/legendas.json', {}) or {}; cam = E.jload(P / '_edit/camera.json', {}) or {}
OK, AV, ER = [], [], []
pr = E.ffprobe(V); vs = next(s for s in pr['streams'] if s['codec_type'] == 'video'); au = next((s for s in pr['streams'] if s['codec_type'] == 'audio'), None)
dv = float(vs.get('duration') or pr['format']['duration']); da = float(au.get('duration', 0)) if au else 0
(ER if abs(dv - DUR) > 1.5 / FPS else OK).append(f'duração vídeo {dv:.3f}s × timeline {DUR:.3f}s')
if not au: ER.append('SEM ÁUDIO no arquivo final')
elif abs(da - dv) > 0.1: AV.append(f'áudio {da:.2f}s × vídeo {dv:.2f}s')
# loudness do decodificado
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(V), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
I = float((re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr) or ['-99'])[-1]); TP = float((re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr) or ['0'])[-1])
alvo = EST['som'].get('lufs', -14)
(ER if abs(I - alvo) > 1 or TP > -1.0 else OK).append(f'loudness {I:.1f} LUFS (alvo {alvo}) · pico real {TP:.1f} dBTP')
# voz no mix: retranscrever
if '--rapido' not in A:
    try:
        from faster_whisper import WhisperModel
        wav = P / '_edit/audio_tmp/qa_16k.wav'
        E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(V), '-ac', '1', '-ar', '16000', str(wav)])
        wm = WhisperModel(B.get('modelo_whisper', 'small'), device='cpu', compute_type='int8')
        segs, _ = wm.transcribe(E.load_wav(wav, 16000), language='pt', beam_size=3, vad_filter=False, condition_on_previous_text=False)
        ouvido = [E.norm(w) for s in segs for w in s.text.split() if E.norm(w)]
        esperado = [E.norm(w['w']) for w in tl['palavras'] if E.norm(w['w'])]
        import difflib
        sm = difflib.SequenceMatcher(a=esperado, b=ouvido, autojunk=False); cob = sum(b.size for b in sm.get_matching_blocks()) / max(1, len(esperado))
        faltas = []
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op in ('delete', 'replace') and a1 - a0 >= 3: faltas.append(' '.join(esperado[a0:a1]))
        (ER if cob < 0.75 else AV if cob < 0.88 else OK).append(f'voz no mix: {100 * cob:.0f}% das palavras reconhecidas na retranscrição' + (f" · trechos a conferir: {' | '.join(faltas[:4])}" if faltas else ''))
    except Exception as e: AV.append(f'retranscrição não rodou ({str(e)[:60]})')
# cliques nas emendas da voz
vz = P / 'audio/voz.wav'
if vz.exists():
    x = E.load_wav(vz, 48000); d = np.abs(np.diff(x)); bad = []
    for s in tl['segmentos'][1:]:
        i = int(s['seq_in'] * 48000); w = d[max(0, i - 480):i + 480]
        if len(w) and w.max() > 8 * (np.median(d[max(0, i - 4800):i + 4800]) + 1e-5) and w.max() > 0.05: bad.append(f"{s['id']}@{s['seq_in']:.2f}s")
    (AV if bad else OK).append('emendas da voz sem clique' if not bad else f"possível clique em {', '.join(bad[:6])}")
# preto / congelado
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(V), '-vf', 'blackdetect=d=0.08:pix_th=0.08,freezedetect=n=-60dB:d=0.6', '-an', '-f', 'null', '-'], capture_output=True, text=True)
pretos = re.findall(r'black_start:([\d.]+)', r.stderr); cong = re.findall(r'freeze_start: ([\d.]+)', r.stderr)
fotos = [(it['t_ini'], it['t_fim']) for it in mapa.get('itens', []) if it.get('tipo') == 'foto' and it.get('t_ini') is not None]
cong = [c for c in cong if not any(a - 0.1 <= float(c) <= b for a, b in fotos)]
cenas = [(it['t_ini'], it['t_fim']) for it in mapa.get('itens', []) if it.get('tipo') in ('motion', 'texto') and it.get('modo') in ('tela_cheia', 'split') and it.get('t_ini') is not None]
pretos = [p_ for p_ in pretos if not any(a - 0.1 <= float(p_) <= b for a, b in cenas)]      # fundo escuro desenhado (gráfico, linha) não é quadro preto
(AV if pretos or cong else OK).append('sem quadro preto/congelado' if not (pretos or cong) else f"preto em {pretos[:4]} · congelado em {cong[:4]}")
# legendas: zona da UI e colisão com peças
OW, OH = E.formato(B)
if OH > OW and leg.get('blocos'):
    fora = [b['id'] for b in leg['blocos'] if not b.get('oculta') and not (0.16 <= b['y'] <= 0.74)]
    (AV if fora else OK).append('legendas dentro da área segura (16–74% da altura)' if not fora else f'legenda na zona da interface: {fora[:6]}')
    col = []
    for b in leg['blocos']:
        if b.get('oculta'): continue
        for it in mapa.get('itens', []):
            if it.get('modo') != 'sobreposto' or it.get('t_ini') is None or it['t_fim'] <= b['t0'] or it['t_ini'] >= b['t1']: continue
            y = {'topo': 0.215, 'centro': 0.46, 'baixo': 0.745, 'meio-baixo': 0.62}.get(it.get('posicao', 'centro'), 0.46)
            if abs(y - b['y']) < 0.09 and not it.get('esconde_legenda'): col.append(f"{b['id']}×{it['id']}")
    (AV if col else OK).append('legenda não colide com peças' if not col else f'legenda encostando em peça: {col[:6]}')
# rosto no recorte
rost = {}
for f in (P / '_edit/rosto').glob('*.json'): rost[f.stem] = np.array(E.jload(f)['amostras'], float)
if cam.get('quadros') and rost:
    bad = 0; tot = 0
    for q in cam['quadros'][::max(1, int(FPS // 2))]:
        a = rost.get(q['clip'])
        if a is None or not len(a): continue
        i = min(len(a) - 1, np.searchsorted(a[:, 0], q['ts'])); fa = a[i]
        if fa[6] <= 0: continue
        tot += 1; ey = (fa[5] - (q['cy'] - q['ch'] / 2)) / q['ch']; ex = (fa[1] - (q['cx'] - q['cw'] / 2)) / q['cw']
        if not (0.2 <= ey <= 0.55 and 0.15 <= ex <= 0.85): bad += 1
    (AV if tot and bad / tot > 0.1 else OK).append(f'rosto no recorte em {100 * (1 - bad / max(1, tot)):.0f}% das amostras (olhos entre 20–55% da altura)')
# Deck Trap: mudança visual a cada ≤ 5 s
marcas = sorted({0.0, DUR} | {s['seq_in'] for s in tl['segmentos']} | {x for it in mapa.get('itens', []) if it.get('t_ini') is not None for x in (it['t_ini'], it['t_fim'])} | {p['t'] for p in cam.get('punch', [])})
gaps = [(a, b) for a, b in zip(marcas, marcas[1:]) if b - a > 5.0]
(AV if gaps else OK).append('mudança visual a cada ≤ 5 s' if not gaps else 'trechos > 5 s sem mudança: ' + ', '.join(f'{a:.1f}–{b:.1f}s' for a, b in gaps[:5]))
# sincronia dos SFX (motion-studio audit-audio.py)
MS = E.motion_studio()
if MS and (P / 'audio/sfx.wav').exists() and (P / 'audio/sfx_cues.json').exists():
    r = subprocess.run([sys.executable, str(MS / 'scripts/audit-audio.py'), str(V), '--sfx', str(P / 'audio/sfx.wav'), '--cues', str(P / 'audio/sfx_cues.json'),
                        '--music', str(P / 'audio/trilha.wav'), '--music-db', '0', '--sfx-db', '0'], capture_output=True, text=True, cwd=str(P))
    errs = [float(x) for x in re.findall(r'\|\s*[\d.]+s f\d+\s*\|\s*\w+\s*\|\s*[\d.]+s\s*\|\s*([+-][\d.]+) ms', r.stdout)]
    cel = re.search(r'banda de celular[^:]*:\s*(-?[\d.]+) LUFS · diferença (-?[\d.]+) dB', r.stdout)
    if errs:
        ruim = [e for e in errs if e < -5 or e > 45]
        (AV if ruim else OK).append(f'SFX: {len(errs)} picos medidos no MP4, erro {min(errs):+.0f}…{max(errs):+.0f} ms (meta: evento + 0–1 quadro)' + (f' · {len(ruim)} fora' if ruim else ''))
    if cel: (AV if float(cel.group(2)) < -4 else OK).append(f'banda de celular {cel.group(1)} LUFS ({cel.group(2)} dB vs banda cheia — grave demais some no alto-falante se < −4)')
# folhas
S = E.SKILL / 'scripts'; base = V.stem
subprocess.run([sys.executable, str(S / 'folha.py'), str(V), '--n', '12', '--ui', '--saida', str(P / f'docs/folhas/{base}_folha.jpg')], capture_output=True)
subprocess.run([sys.executable, str(S / 'folha.py'), str(V), '--cortes', str(P), '--largura', '220', '--saida', str(P / f'docs/folhas/{base}_cortes.jpg')], capture_output=True)
L = [f'# QA — {V.name}', '', *(f'- ✗ {x}' for x in ER), *(f'- ⚠ {x}' for x in AV), *(f'- ✔ {x}' for x in OK), '',
     f'Folhas para OLHAR: docs/folhas/{base}_folha.jpg (12 quadros + zonas da UI) · docs/folhas/{base}_cortes.jpg (±0,15 s de cada corte/item)',
     'O áudio foi MEDIDO, não ouvido. Revisão visual: P0/P1/P2 · tempo · onde · problema → mudança exata.']
(P / 'docs/QA.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L))
sys.exit(1 if ER else 0)
