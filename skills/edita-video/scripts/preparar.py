#!/usr/bin/env python3
"""preparar.py — ETAPA 2: inventário, mezanino CFR/SDR, áudio, transcrição por palavra, frases com pausas, mapa de silêncio.

    python3 preparar.py <projeto> [--fps 30] [--modelo small|medium] [--termos "Dr. Rafael, Botox, Orbe"] [--sem-transcrever]

Faz, para cada vídeo em brutos/ (ordem: data de gravação, depois nome):
  1. ffprobe → _edit/inventario.json + docs/INVENTARIO.md (duração, fps, VFR, HDR, rotação, áudio, resolução).
  2. MEZANINO em _edit/mez/<id>.mp4: CFR no fps do projeto, SDR Rec.709 (HDR do iPhone vira SDR com tonemap), rotação
     aplicada, keyframe a cada 1 s (seek exato). Todo o resto do fluxo usa o mezanino; brutos/ nunca muda.
  3. Áudio: _edit/audio/<id>.wav (48 kHz mono, para montar a voz) e <id>_16k.wav (transcrição).
  4. Transcrição por palavra (faster-whisper, pt, VAD) com prompt de hesitação (o Whisper apaga "é…", "hum" se não
     for semeado) e termos do cliente. Guarda contra alucinação: palavra dentro de silêncio real é descartada; trecho com
     energia de fala e sem palavra é retranscrito SEM prompt ("trecho engolido").
  5. _edit/words.json (todas as palavras: clip, w, s, e, p) · docs/FRASES.md (o que o Claude LÊ: uma frase por linha
     com tempo e pausas) · _edit/silencios.json · docs/folhas/<id>_contato.jpg (1 quadro/s: confere legenda já
     queimada, cortes de câmera e enquadramento).
"""
import sys, os, re, json, subprocess, datetime
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, _ = E.config(P)
FPS = float(opt('fps', B.get('fps', 30)))
FPS_STR = {29.97: '30000/1001', 23.976: '24000/1001', 59.94: '60000/1001'}.get(round(FPS, 3), str(int(FPS)) if FPS == int(FPS) else str(FPS))
MEZ = P / '_edit' / 'mez'; AUD = P / '_edit' / 'audio'; FOL = P / 'docs' / 'folhas'
for d in (MEZ, AUD, FOL): d.mkdir(parents=True, exist_ok=True)

VIDEXT = ('.mp4', '.mov', '.m4v', '.mkv', '.mts', '.avi', '.webm', '.hevc')
brutos = sorted([f for f in (P / 'brutos').iterdir() if f.suffix.lower() in VIDEXT])
if not brutos:
    E.die('nenhum vídeo em brutos/')

# ── 1. inventário ──
inv = []
for f in brutos:
    pr = E.ffprobe(f)
    v = next((s for s in pr['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in pr['streams'] if s['codec_type'] == 'audio'), None)
    if not v:
        print(f'⚠ {f.name}: sem vídeo, ignorado'); continue
    rot = 0
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd: rot = int(sd['rotation'])
    rot = rot or int((v.get('tags') or {}).get('rotate', 0) or 0)
    w, h = int(v['width']), int(v['height'])
    if abs(rot) in (90, 270): w, h = h, w
    rfr, afr = E.frac(v.get('r_frame_rate')), E.frac(v.get('avg_frame_rate'))
    vfr = abs(rfr - afr) > 0.05 * max(rfr, 1)
    trc = v.get('color_transfer', '')
    hdr = trc in ('smpte2084', 'arib-std-b67')
    criado = (pr['format'].get('tags') or {}).get('creation_time') or datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat()
    inv.append({'arquivo': f.name, 'dur': float(pr['format']['duration']), 'w': w, 'h': h, 'fps': round(afr or rfr, 3), 'vfr': vfr,
                'hdr': hdr, 'transfer': trc, 'rot': rot, 'audio': bool(a), 'codec': v['codec_name'], 'criado': criado,
                'bits': v.get('bits_per_raw_sample') or v.get('pix_fmt')})
inv.sort(key=lambda x: (x['criado'], x['arquivo']))
for i, it in enumerate(inv):
    it['id'] = f'c{i + 1}'
if not opt('fps') and not B.get('fps'):
    # fps do projeto = o do A-roll principal, num valor padrão; 50/60 viram 25/30 (entrega de redes)
    PADR = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
    princ = max(inv, key=lambda it: it['dur'])['fps'] or 30
    f = min(PADR, key=lambda x: abs(x - princ))
    FPS = {50: 25, 59.94: 29.97, 60: 30}.get(f, f)
    FPS_STR = {29.97: '30000/1001', 23.976: '24000/1001', 59.94: '60000/1001'}.get(round(FPS, 3), str(int(FPS)) if FPS == int(FPS) else str(FPS))
    FPS = {29.97: 30000 / 1001, 23.976: 24000 / 1001}.get(FPS, float(FPS))
E.jsave(P / '_edit' / 'inventario.json', {'fps': FPS, 'fps_str': FPS_STR, 'clips': inv})
linhas = ['# Inventário dos brutos', '', f'fps do projeto: **{FPS_STR}** (tudo vira CFR nesse fps)', '',
          '| id | arquivo | dur | resolução | fps | VFR | HDR | rot | áudio |', '|---|---|---|---|---|---|---|---|---|']
alertas = []
for it in inv:
    linhas.append(f"| {it['id']} | {it['arquivo']} | {it['dur']:.1f}s | {it['w']}×{it['h']} | {it['fps']} | {'sim' if it['vfr'] else '-'} | {'sim' if it['hdr'] else '-'} | {it['rot']} | {'sim' if it['audio'] else 'NÃO'} |")
    if not it['audio']: alertas.append(f"{it['id']}: sem áudio (precisa de voz separada ou é B-roll)")
    if it['hdr']: alertas.append(f"{it['id']}: HDR ({it['transfer']}) → convertido para SDR com tonemap")
    if it['vfr']: alertas.append(f"{it['id']}: VFR → mezanino CFR (sem isso o tempo deriva)")
    if min(it['w'], it['h']) < 1080 and EST['camera'].get('reenquadrar'): alertas.append(f"{it['id']}: {it['w']}×{it['h']} — zoom/recorte vai amolecer; limite o zoom")
if alertas:
    linhas += ['', '## Alertas', ''] + [f'- {a}' for a in alertas]
(P / 'docs' / 'INVENTARIO.md').write_text('\n'.join(linhas) + '\n', encoding='utf-8')
print('\n'.join(linhas[4:]))

# ── 2. mezanino + 3. áudio ──
for it in inv:
    src = P / 'brutos' / it['arquivo']; out = MEZ / f"{it['id']}.mov"
    if not out.exists():
        vf = []
        if it['hdr']:
            vf.append('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv')
        vf.append(f'fps={FPS_STR}')
        vf.append('format=yuv420p')
        g = str(max(1, round(FPS)))
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-vf', ','.join(vf), '-fps_mode', 'cfr', '-c:v', 'libx264', '-preset', 'veryfast',
               '-crf', '14', '-g', g, '-keyint_min', g, '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
               *(['-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '1'] if it['audio'] else ['-an']), str(out)]
        E.run(cmd)
    mov = MEZ / f"{it['id']}.mov"
    it['mez'] = str(mov.relative_to(P))
    if it['audio']:
        for sr, suf in ((48000, ''), (16000, '_16k')):
            w = AUD / f"{it['id']}{suf}.wav"
            if not w.exists():
                E.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mov), '-vn', '-ac', '1', '-ar', str(sr), '-c:a', 'pcm_s16le', str(w)])
    # folha de contato 1 quadro/s (legenda já queimada? tarja? cortes?)
    folha = FOL / f"{it['id']}_contato.jpg"
    if not folha.exists():
        n = max(1, int(it['dur']))
        cols = 10; rows = min(6, -(-n // cols))
        E.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mov), '-vf', f'fps=1,scale=192:-1,tile={cols}x{rows}', '-frames:v', '1', str(folha)])
E.jsave(P / '_edit' / 'inventario.json', {'fps': FPS, 'fps_str': FPS_STR, 'clips': inv})
print(f'✔ mezanino CFR {FPS_STR} (H.264 intra-1s + PCM .mov) em _edit/mez/ · áudio em _edit/audio/ · folhas em docs/folhas/')

if '--sem-transcrever' in A:
    E.log_estado(P, 'preparar', 'feito', 'sem transcrição'); sys.exit(0)

# ── 4. transcrição ──
from faster_whisper import WhisperModel
modelo = opt('modelo', B.get('modelo_whisper', 'small'))
wm = WhisperModel(modelo, device='cpu', compute_type='int8')
termos = opt('termos', B.get('termos', ''))
PROMPT = 'Ééé… então, tipo, hã, né? Ahn… hum, assim. ' + (f'{termos}.' if termos else '')

def transcrever(x16, prompt):
    segs, _ = wm.transcribe(x16.astype(np.float32), language='pt', word_timestamps=True, vad_filter=True,
                            vad_parameters={'min_silence_duration_ms': 300, 'speech_pad_ms': 60},
                            initial_prompt=prompt, condition_on_previous_text=False, beam_size=5)
    return [(w.word.strip(), float(w.start), float(w.end), float(w.probability)) for s in segs for w in (s.words or []) if w.word.strip()]

todas, sil_all = [], {}
for it in inv:
    if not it['audio']: continue
    x16 = E.load_wav(AUD / f"{it['id']}_16k.wav", 16000)
    env = E.rms_env(x16, 16000, 0.01); envdb = 20 * np.log10(env + 1e-9)
    # limiar adaptativo: piso de ruído (p10) + 12 dB, entre −50 e −30 dB
    piso = float(np.percentile(envdb, 10)); fala_db = float(np.percentile(envdb, 90))
    thr = min(-30.0, max(-50.0, piso + 12)); thr = min(thr, fala_db - 18)
    falando = envdb > thr
    ws = transcrever(x16, PROMPT)
    # guarda contra alucinação: palavra cuja janela não tem energia de fala
    boas = []
    for w, s, e, p in ws:
        a, b = int(s * 100), max(int(s * 100) + 1, int(e * 100))
        cobertura = float(falando[a:b].mean()) if b > a else 0.0
        if cobertura > 0.15 or p > 0.6:
            boas.append((w, s, e, p))
    descartadas = len(ws) - len(boas)
    # trechos engolidos: fala (≥0,6 s) sem nenhuma palavra → retranscreve sem prompt
    cobre = np.zeros(len(falando), bool)
    for w, s, e, p in boas: cobre[int(s * 100):int(e * 100) + 1] = True
    buracos, i = [], 0
    while i < len(falando):
        if falando[i] and not cobre[i]:
            j = i
            while j < len(falando) and falando[j] and not cobre[j]: j += 1
            if j - i >= 60: buracos.append((i / 100, j / 100))
            i = j
        else: i += 1
    for a, b in buracos:
        a0, b0 = max(0, a - 0.3), min(len(x16) / 16000, b + 0.3)
        extra = transcrever(x16[int(a0 * 16000):int(b0 * 16000)], None)
        boas += [(w, s + a0, e + a0, p) for w, s, e, p in extra if a - 0.1 <= s + a0 <= b + 0.1]
    boas.sort(key=lambda z: z[1])
    for w, s, e, p in boas:
        todas.append({'clip': it['id'], 'w': w, 's': round(s, 3), 'e': round(e, 3), 'p': round(p, 3), 'filler': E.is_filler(w)})
    # silêncios (para o corte e para a revisão)
    sils, i = [], 0
    while i < len(falando):
        if not falando[i]:
            j = i
            while j < len(falando) and not falando[j]: j += 1
            if j - i >= 15: sils.append([round(i / 100, 2), round(j / 100, 2)])
            i = j
        else: i += 1
    sil_all[it['id']] = {'limiar_db': round(thr, 1), 'piso_db': round(piso, 1), 'silencios': sils}
    print(f"✔ {it['id']}: {len([t for t in todas if t['clip'] == it['id']])} palavras · {descartadas} descartada(s) por alucinação · "
          f"{len(buracos)} trecho(s) engolido(s) retranscrito(s) · limiar de silêncio {thr:.0f} dB")

# índice global estável
for i, w in enumerate(todas): w['i'] = i
E.jsave(P / '_edit' / 'words.json', todas)
E.jsave(P / '_edit' / 'silencios.json', sil_all)

# ── 5. FRASES.md: a visão que o Claude lê (não assiste; lê) ──
def frases(words):
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nx = words[k + 1] if k + 1 < len(words) else None
        gap = (nx['s'] - w['e']) if nx and nx['clip'] == w['clip'] else 99
        if re.search(r'[.!?…]$', w['w']) or gap >= 0.5 or not nx:
            out.append((cur, gap)); cur = []
    return out
fr = frases(todas)
L = ['# Frases (leia isto, não o vídeo)', '', 'Formato: `[clip início–fim] texto` · `(pausa X s)` depois da frase · *itálico* = hesitação · ~prob baixa~',
     'Use os números `#` das palavras para pedir cortes finos (ex.: remover #12–#15).', '']
for k, (ws, gap) in enumerate(fr):
    txt = ' '.join((f"*{w['w']}*" if w['filler'] else (f"~{w['w']}~" if w['p'] < 0.45 else w['w'])) for w in ws)
    L.append(f"F{k + 1:03d} [{ws[0]['clip']} {ws[0]['s']:.2f}–{ws[-1]['e']:.2f}] #{ws[0]['i']}–#{ws[-1]['i']} {txt}" + (f"  (pausa {gap:.1f} s)" if 0.3 <= gap < 99 else ''))
(P / 'docs' / 'FRASES.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
dur_fala = sum(w['e'] - w['s'] for w in todas)
print(f'✔ docs/FRASES.md · {len(fr)} frases · {len(todas)} palavras · {dur_fala:.0f} s de fala em {sum(it["dur"] for it in inv):.0f} s de bruto')
E.log_estado(P, 'preparar', 'feito', f'{len(inv)} clipe(s), {len(todas)} palavras')
