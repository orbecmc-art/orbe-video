#!/usr/bin/env python3
"""camera.py — ETAPA 7: enquadramento (16:9 → 9:16 seguindo o rosto), zoom alternado nos cortes, push lento e punch-in
na ênfase. Gera a "câmera virtual" quadro a quadro que o compor.py aplica.

    python3 camera.py <projeto> [--sem-punch] [--sem-reenquadrar] [--punch-palavras 12,40] [--zoom-max 1.2]

Regras (references/camera.md; números de LeiteZ, HyperFrames, pesquisa short-form):
  · Base: maior recorte com o aspecto do formato que cabe na fonte. Rosto seguido com ZONA MORTA (zona_morta × largura do
    recorte) e mola criticamente amortecida (suavidade s). Olhos a olhos_y da altura do recorte (~36%).
  · Em CADA corte a câmera pode saltar (o corte esconde) — dentro do trecho só desliza. Nunca inverte a direção num corte.
  · Corte "pulo" (mesmo clipe, tempo de origem pulou): alterna o zoom entre zoom_alterna (ex.: 100% ↔ 110%) — disfarça o
    jump cut. Mudança < 5% não conta como mudança de plano.
  · Push lento de `push` ao longo do trecho (ease out). Punch-in de `punch` na palavra de ênfase (pico de energia, número,
    ou palavra pedida), subindo em 0,18 s (ease out) e segurando até o próximo corte; no máximo 1 a cada punch_intervalo s,
    nunca nos 0,5 s depois de um corte.
  · Zoom total ≤ zoom_max (fonte 1080p já sofre 1,78× de upscale no 9:16 — mais que ~1,2 amolece). Nunca mostra borda.
  · punch_modo (por estilo, Style Studio/Synteq): enfase (padrão: palavras de ênfase, 1 a cada punch_intervalo s) ·
    linha (onde começa cada linha de legenda — fala em tela cheia sempre se mexe; dinâmico/varejo) · tonicas (palavras
    tônicas, intervalo curto) · viradas (só nas viradas/números do mapa e enfase_palavras; minimal/clínica/luxo).
    punch_alterna: cada punch VAI e o próximo VOLTA (aberto ↔ fechado em punch_rampa s, quase um corte).
  · Quebra de padrão (item do mapa com "efeito": "quebra"): close mais fechado com o nariz no centro (o compor tira a cor
    e o audio põe reverb) — o espectador sente a mudança de assunto.
Saídas: _edit/camera.json (por quadro: clip, t_origem, cx, cy, cw, ch) · docs/CAMERA.md (cam01… para revisão por número)
"""
import sys, os, math, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P); CAM = EST['camera']
OW, OH = E.formato(B); R = OW / OH
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes'); FPS = tl['fps']
inv = {c['id']: c for c in E.jload(P / '_edit/inventario.json')['clips']}
ZMAX = float(opt('zoom-max', CAM['max_zoom']))
reenq = CAM['reenquadrar'] and '--sem-reenquadrar' not in A
words = E.jload(P / '_edit/words.json'); widx = {w['i']: w for w in words}

def rosto(clip):
    d = E.jload(P / '_edit/rosto' / f'{clip}.json')
    if not d: return None
    a = np.array(d['amostras'], float)
    return a if len(a) else None
ROSTOS = {c: rosto(c) for c in inv}

def face_at(clip, t):
    a = ROSTOS.get(clip)
    if a is None: return None
    i = np.searchsorted(a[:, 0], t)
    # vizinhos com rosto válido
    for j in range(0, 12):
        for k in (i - j, i + j):
            if 0 <= k < len(a) and a[k, 6] > 0:
                return a[k]
    return None

# ── palavras de ênfase (punch) ──
MODO = CAM.get('punch_modo', 'enfase'); ALT = bool(CAM.get('punch_alterna')); RAMPA = float(CAM.get('punch_rampa', 0.18))
MAPA = E.jload(P / '_edit/mapa.json', {}) or {}
QUEBRAS = [(it['t_ini'], it['t_fim']) for it in MAPA.get('itens', []) if (it.get('efeito') == 'quebra' or it.get('quebra')) and it.get('t_ini') is not None]
def linhas_legenda():
    """início de cada linha de legenda (mesma quebra do legendas.py, aproximada): até `palavras` palavras, quebra em pausa
    > 0,35 s, pontuação forte ou corte."""
    n = int(EST['legendas'].get('palavras', 3)); out = []; cur = 0; prev = None
    for w in tl['palavras']:
        novo = prev is None or cur >= n or w['seg'] != prev['seg'] or w['s'] - prev['e'] > 0.35 or bool(re.search(r'[.!?…]$', prev['w']))
        if novo: out.append(w); cur = 0
        cur += 1; prev = w
    return out
def enfases():
    if '--sem-punch' in A or CAM['punch'] <= 0: return []
    segs = {s['id']: s for s in tl['segmentos']}
    if MODO == 'linha':
        out = []
        for w in linhas_legenda():
            s = segs[w['seg']]
            if w['s'] - s['seq_in'] < 0.35 or s['seq_out'] - w['s'] < 0.3: continue      # o corte já é a mudança
            if out and w['s'] - out[-1]['t'] < max(0.6, 0.8 * float((EST.get('ritmo') or {}).get('mudanca', [1.5])[0])): continue
            out.append({'t': round(w['s'] - 0.04, 3), 'palavra': w['w'], 'i': w['i'], 'seg': s['id']})
        return out
    if MODO == 'viradas':
        alvo = {int(i) for i in MAPA.get('enfase_palavras', [])}
        for it in MAPA.get('itens', []):
            if it.get('batida') in ('virada', 'numero') and it.get('modo', 'sobreposto') == 'sobreposto' and isinstance(it.get('de'), str) and it['de'].startswith('#'):
                alvo.add(int(it['de'][1:]))
        out = []
        for w in tl['palavras']:
            if w['i'] not in alvo: continue
            s = segs[w['seg']]
            if w['s'] - s['seq_in'] < 0.4: continue
            out.append({'t': round(w['s'] - 0.04, 3), 'palavra': w['w'], 'i': w['i'], 'seg': s['id']})
        return out
    pedidas = {int(x) for x in (opt('punch-palavras') or '').split(',') if x.strip()}
    mapa = E.jload(P / '_edit/mapa.json', {}) or {}
    pedidas |= {int(i) for i in mapa.get('enfase_palavras', [])}
    cand = []
    envs = {}
    for w in tl['palavras']:
        src = widx[w['i']]; clip = src['clip']
        if clip not in envs:
            x = E.load_wav(P / '_edit/audio' / f'{clip}.wav', 48000); envs[clip] = E.rms_env(x, 48000, 0.01)
        env = envs[clip]; a, b = int(src['s'] * 100), max(int(src['s'] * 100) + 1, int(src['e'] * 100))
        loud = float(env[a:b].max()) if b > a else 0
        num = any(ch.isdigit() for ch in w['w']) or E.norm(w['w']) in ('primeiro', 'segundo', 'terceiro', 'nunca', 'sempre', 'todo', 'todos', 'zero', 'gratis', 'agora')
        cand.append((w, loud, num))
    if not cand: return []
    louds = np.array([c[1] for c in cand]); thr = np.percentile(louds, 85)
    esc = []
    for w, loud, num in cand:
        score = (2 if w['i'] in pedidas else 0) + (1 if num else 0) + (1 if loud >= thr else 0) + (0.5 if len(E.norm(w['w'])) >= 6 else 0)
        if score >= 1.5 or w['i'] in pedidas:
            esc.append((score, w))
    esc.sort(key=lambda z: (-z[0], z[1]['s']))
    out = []
    gap = min(CAM['punch_intervalo'], 2.5) if MODO == 'tonicas' else CAM['punch_intervalo']
    for score, w in esc:
        s = segs[w['seg']]
        if w['s'] - s['seq_in'] < 0.5 or s['seq_out'] - w['s'] < 0.4: continue
        if any(abs(w['s'] - o['t']) < gap for o in out): continue
        out.append({'t': round(w['s'] - 0.04, 3), 'palavra': w['w'], 'i': w['i'], 'seg': s['id']})
    return sorted(out, key=lambda o: o['t'])
PUNCH = enfases()

# ── zoom por trecho ──
segs = tl['segmentos']; za = CAM['zoom_alterna']; plano = []
for k, s in enumerate(segs):
    pv = segs[k - 1] if k else None
    pulo = pv and pv['clip'] == s['clip'] and abs(s['src_in'] - pv['src_out']) > 0.05
    if k == 0: z = za[0]
    elif pulo:
        z = za[1] if abs(plano[-1]['z'] - za[0]) < 0.02 else za[0]     # alterna
    else: z = plano[-1]['z']
    plano.append({'seg': s['id'], 'z': z, 'pulo': bool(pulo)})

ease_out = lambda p: 1 - (1 - min(1, max(0, p))) ** 3
N = int(round(tl['duracao'] * FPS))
frames = []; cam_rev = []
pos = None; vel = np.zeros(2); alvo = None
w_ = 2 * math.pi / max(0.15, CAM['suavidade'] * 2.2)     # mola crítica: tempo de assentamento ≈ suavidade
for n in range(N):
    t = (n + 0.5) / FPS
    k = next(i for i, s in enumerate(segs) if t < segs[i]['seq_out'] or i == len(segs) - 1)
    s = segs[k]; clip = s['clip']; c = inv[clip]; SW, SH = c['w'], c['h']
    ts = t - s['seq_in'] + s['src_in']
    # recorte base com o aspecto do formato
    if reenq or abs(SW / SH - R) < 0.01:
        bw, bh = (SH * R, SH) if SW / SH > R else (SW, SW / R)
    else:     # sem reenquadrar e aspectos diferentes: encaixa inteiro (letterbox resolvido no compor com fundo desfocado)
        bw, bh = SW, SH
    pr = (t - s['seq_in']) / max(0.001, s['dur'])
    z = plano[k]['z'] * (1 + CAM['push'] * ease_out(pr))
    pus = [pu for pu in PUNCH if pu['seg'] == s['id'] and t >= pu['t']]
    if ALT and pus:            # vai e volta: ímpar = fechado, par = aberto
        p_ = ease_out((t - pus[-1]['t']) / RAMPA); z *= 1 + CAM['punch'] * (p_ if len(pus) % 2 else 1 - p_)
    else:
        for pu in pus: z *= 1 + CAM['punch'] * ease_out((t - pu['t']) / RAMPA)
    qb = any(a <= t < b for a, b in QUEBRAS)
    z = min(z * (1.22 if qb else 1), ZMAX * (1.12 if qb else 1))
    cw, ch = bw / z, bh / z
    f = face_at(clip, ts) if reenq else None
    if f is not None:
        tx = f[1]; ty = f[5] + (0.5 - (0.44 if qb else CAM['olhos_y'])) * ch     # quebra: nariz no centro
        if CAM.get('alterna_x') and abs(plano[k]['z'] - za[0]) > 0.02: tx += float(CAM['alterna_x']) * cw   # "2º ângulo" (entrevista): no plano fechado o rosto vai para um terço
    else:
        tx, ty = (alvo if alvo is not None and k == (frames[-1]['k'] if frames else -1) else (SW / 2, SH / 2))
    corte = not frames or frames[-1]['k'] != k
    if corte or alvo is None:
        alvo = np.array([tx, ty], float)
        pos = alvo.copy() if (corte or pos is None) else pos; vel[:] = 0
    else:
        dz = CAM['zona_morta'] * cw
        if abs(tx - alvo[0]) > dz: alvo[0] = tx - math.copysign(dz * 0.5, tx - alvo[0])
        if abs(ty - alvo[1]) > dz * 0.6: alvo[1] = ty - math.copysign(dz * 0.3, ty - alvo[1])
        dt = 1 / FPS; acc = w_ * w_ * (alvo - pos) - 2 * w_ * vel; vel += acc * dt; pos = pos + vel * dt
    cx = min(max(pos[0], cw / 2), SW - cw / 2); cy = min(max(pos[1], ch / 2), SH - ch / 2)
    frames.append({'k': k, 'clip': clip, 'ts': round(ts, 4), 'cx': round(float(cx), 2), 'cy': round(float(cy), 2), 'cw': round(cw, 2), 'ch': round(ch, 2), 'z': round(z, 4)})

for k, s in enumerate(segs):
    pu = [p for p in PUNCH if p['seg'] == s['id']]
    cam_rev.append({'id': f'cam{k + 1:02d}', 'seg': s['id'], 'zoom': plano[k]['z'], 'pulo': plano[k]['pulo'],
                    'punch': [f"{p['palavra']}@{p['t']:.2f}s" for p in pu]})
E.jsave(P / '_edit/camera.json', {'fps': FPS, 'w': OW, 'h': OH, 'quadros': frames, 'plano': cam_rev, 'punch': PUNCH, 'reenquadrar': reenq})
# upscale efetivo (aviso de nitidez)
up = max(OH / f['ch'] for f in frames) if frames else 1
L = [f'# Câmera virtual — {OW}×{OH}', '', f'Reenquadrar: {"sim (rosto)" if reenq else "não"} · upscale máximo {up:.2f}×' + (' ⚠ acima de 2,2× amolece: limite o zoom ou peça material 4K' if up > 2.2 else ''), '',
     '| id | trecho | zoom | corte-pulo | punch-in |', '|---|---|---|---|---|']
for c in cam_rev:
    L.append(f"| {c['id']} | {c['seg']} | {c['zoom'] * 100:.0f}% | {'sim' if c['pulo'] else '-'} | {', '.join(c['punch']) or '-'} |")
L += ['', 'Ajuste: `camera.py . --punch-palavras 12,40` (índices de FRASES.md), `--sem-punch`, `--zoom-max 1.15`.']
(P / 'docs/CAMERA.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L[2:]))
E.log_estado(P, 'camera', 'feito', f'{len(PUNCH)} punch-in(s)')
