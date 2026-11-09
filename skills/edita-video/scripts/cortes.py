#!/usr/bin/env python3
"""cortes.py — ETAPA 3: propõe o corte (silêncios, hesitações, retakes, falsos começos) e monta a linha do tempo.

    python3 cortes.py <projeto> [--remover 8-12,42,F009] [--manter 13-27] [--pausa 0.35] [--sem-vicios] [--sem-cortes] [--travar]

Regras (references/cortes.md):
  · Escolhe e descarta ENTRE frases/takes, nunca no meio de uma frase. Retake: frase parecida com uma das 3 seguintes
    (≥ retake_sim, ≥ 4 palavras) → fica a ÚLTIMA. Falso começo: frase curta/sem fechamento cujas 2–3 primeiras palavras
    abrem a seguinte → sai. Pista falada ("de novo", "vou repetir", "pera", "corta") → sai e marca dúvida.
  · NOTAS FALADAS (Mateus Dias): quem grava fala "abre nota … fecha nota" (ou "nota pro editor … fim da nota") e dá a
    direção daquele trecho ("coloca a foto do produto na minha mão", "aqui entra o gráfico"). A nota SAI do vídeo e vira
    instrução: _edit/notas_faladas.json + docs/NOTAS_FALADAS.md, ancorada na palavra seguinte — o mapa/plano começa por
    elas. "Claude, coloca/bota/mostra…" no começo de frase também vira nota (marcada como dúvida). Nota sem "fecha" vai
    até o fim da frase.
  · Hesitação inequívoca (éé, ãh, hum) sai. Palavra que também é palavra ("é", "um", "tipo", "né") só sai ISOLADA por
    pausa ≥ pausa_vicio dos dois lados. Na dúvida, não corta e marca.
  · Silêncio > pausa_max dentro do trecho é encurtado, deixando folga_antes antes da 1ª sílaba e folga_depois depois da
    última (não come "s" e "t" finais). Bordas refinadas pela ENERGIA do áudio (±40 ms) e encaixadas no frame.
  · Trecho mantido < min_trecho some. Fade de fade_ms nas bordas internas (feito na montagem do áudio).
  · Ajustes manuais por ÍNDICE de palavra (estáveis, vêm de docs/FRASES.md): --remover 8-12 --manter 42. Ficam salvos em
    _edit/cortes_ajustes.json e valem nas próximas rodadas. --travar marca o corte como aprovado (motion/câmera dependem dele).
Saídas: _edit/cortes.json · _edit/timeline.json (tempo da sequência ↔ origem, palavras no tempo final) · docs/CORTES.md
"""
import sys, os, re, difflib
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P)
C = EST['cortes']
if opt('pausa'): C['pausa_max'] = float(opt('pausa'))
inv = E.jload(P / '_edit/inventario.json'); FPS = inv['fps']
words = E.jload(P / '_edit/words.json') or E.die('rode preparar.py antes')
est = E.jload(P / '_edit/estado.json', {})
if (est.get('etapas', {}).get('cortes', {}).get('status') == 'travado') and '--forcar' not in A:
    E.die('o corte está TRAVADO (aprovado). Mudar agora exige refazer câmera/motion/som. Rode com --forcar se for isso mesmo.')

# ── ajustes manuais persistentes ── (por palavra #12-15 ou por frase F005; condensar para a duração alvo = remover frases)
def _frases(ws):
    out, cur = [], []
    for k, w in enumerate(ws):
        cur.append(w); nx = ws[k + 1] if k + 1 < len(ws) else None
        gap = (nx['s'] - w['e']) if nx and nx['clip'] == w['clip'] else 99
        if re.search(r'[.!?…]$', w['w']) or gap >= 0.5 or not nx: out.append(cur); cur = []
    return out
_FR = _frases(words)
aj = E.jload(P / '_edit/cortes_ajustes.json', {'remover': [], 'manter': []})
def faixas(s):
    out = []
    for p in (s or '').split(','):
        p = p.strip()
        if not p: continue
        a, _, b = p.partition('-')
        if a.upper().startswith('F'):      # frase inteira (docs/FRASES.md): F005 ou F005-F007 → faixa de palavras
            fa = _FR[int(a[1:]) - 1]; fb = _FR[int((b or a)[1:]) - 1]; out.append([fa[0]['i'], fb[-1]['i']])
        else: out.append([int(a.lstrip('#')), int((b or a).lstrip('#'))])
    return out
aj['remover'] += faixas(opt('remover')); aj['manter'] += faixas(opt('manter'))
E.jsave(P / '_edit/cortes_ajustes.json', aj)
forca_rem = {i for a, b in aj['remover'] for i in range(a, b + 1)}
forca_man = {i for a, b in aj['manter'] for i in range(a, b + 1)}

# ── frases ──
def frases(ws):
    out, cur = [], []
    for k, w in enumerate(ws):
        cur.append(w); nx = ws[k + 1] if k + 1 < len(ws) else None
        gap = (nx['s'] - w['e']) if nx and nx['clip'] == w['clip'] else 99
        if re.search(r'[.!?…]$', w['w']) or gap >= 0.5 or not nx:
            out.append(cur); cur = []
    return out
FR = frases(words)
toks = lambda f: [E.norm(w['w']) for w in f if not w['filler'] and not E.talvez_vicio(w['w'])] or [E.norm(w['w']) for w in f]
remove = {}     # índice → motivo
duvidas = []
PISTAS = re.compile(r'\b(de novo|vou repetir|deixa eu (falar|come[cç]ar) de novo|pera|perai|corta|n[aã]o, n[aã]o|errei)\b', re.I)

# ── notas faladas: "abre nota … fecha nota" saem do vídeo e viram direção ──
NN = [E.norm(w['w']) for w in words]
ABRE = [('abre', 'nota'), ('abrir', 'nota'), ('abro', 'nota'), ('abre', 'a', 'nota'), ('abrindo', 'nota'), ('nota', 'pro', 'editor'),
        ('nota', 'para', 'o', 'editor'), ('nota', 'pra', 'edicao'), ('nota', 'para', 'a', 'edicao'), ('nota', 'pra', 'edicao')]
FECHA = [('fecha', 'nota'), ('fecha', 'a', 'nota'), ('fechar', 'nota'), ('fecho', 'nota'), ('fechando', 'nota'), ('fim', 'da', 'nota')]
def _casa(k, pads):
    for pd in pads:
        if tuple(NN[k:k + len(pd)]) == pd: return len(pd)
    return 0
NOTAS = []; k = 0
fim_frase = {}
for f in FR:
    for w in f: fim_frase[w['i']] = f[-1]['i']
pos = {w['i']: n for n, w in enumerate(words)}
VERBOS = ('coloca', 'bota', 'poe', 'mostra', 'adiciona', 'tira', 'faz', 'aqui', 'nesse', 'neste', 'entra', 'corta', 'usa')
while k < len(words):
    la = _casa(k, ABRE)
    claude = (NN[k] in ('claude', 'claudio') and k + 1 < len(words) and NN[k + 1] in VERBOS
              and (k == 0 or re.search(r'[.!?…]$', words[k - 1]['w']) or words[k]['s'] - words[k - 1]['e'] > 0.4))
    if not la and not claude: k += 1; continue
    fechou = False
    if claude:
        fim = pos[fim_frase[words[k]['i']]]; corpo = words[k + 1:fim + 1]; rem = words[k:fim + 1]; nxt = fim + 1; fechou = True
    else:
        j = k + la
        while j < len(words) and j - k < 80:
            lf = _casa(j, FECHA)
            if lf: fechou = True; break
            j += 1
        if fechou: corpo = words[k + la:j]; rem = words[k:j + lf]; nxt = j + lf
        else:
            fim = pos[fim_frase[words[k]['i']]]
            if fim <= k + la - 1 and k + la < len(words): fim = pos[fim_frase[words[k + la]['i']]]   # "Abre nota." → vale a próxima frase
            corpo = words[k + la:fim + 1]; rem = words[k:fim + 1]; nxt = fim + 1
    texto = ' '.join(w['w'] for w in corpo).strip(' ,.')
    for w in rem: remove[w['i']] = 'nota falada'
    prox = next((w for w in words[nxt:] if w['i'] not in remove), None)
    NOTAS.append({'de': rem[0]['i'], 'ate': rem[-1]['i'], 'texto': texto, 'ancora': f"#{prox['i']}" if prox else None,
                  'quando_bruto': round(rem[0]['s'], 2), 'fechada': fechou, 'tipo': 'claude' if claude else 'nota'})
    if not fechou or claude: duvidas.append(f"nota falada em #{rem[0]['i']}{' (\"Claude, …\")' if claude else ' sem \"fecha nota\"'} — saiu até o fim da frase: \"{texto[:80]}\" (confira)")
    k = max(nxt, k + 1)
for n_ in NOTAS:
    for w in words:
        if n_['de'] <= w['i'] <= n_['ate']: remove[w['i']] = 'nota falada'

for k, f in enumerate(FR):
    tk = toks(f); txt = ' '.join(w['w'] for w in f)
    # frase só de hesitação/vício isolado
    if all(w['filler'] or E.talvez_vicio(w['w']) for w in f) and C['vicios'] != 'nenhum':
        prev_gap = f[0]['s'] - (FR[k - 1][-1]['e'] if k and FR[k - 1][-1]['clip'] == f[0]['clip'] else -9)
        next_gap = (FR[k + 1][0]['s'] - f[-1]['e']) if k + 1 < len(FR) and FR[k + 1][0]['clip'] == f[-1]['clip'] else 9
        if all(w['filler'] for w in f) or (prev_gap >= C['pausa_vicio'] and next_gap >= C['pausa_vicio']):
            for w in f: remove[w['i']] = 'hesitação'
            continue
    if PISTAS.search(txt):
        for w in f: remove[w['i']] = 'pista de regravação'
        duvidas.append(f"F{k + 1:03d} tem pista de regravação (\"{txt}\"): conferir se a frase anterior também sai")
        continue
    # retake / falso começo: compara com as 3 próximas frases do mesmo clipe, até 60 s
    for j in range(k + 1, min(len(FR), k + 4)):
        g = FR[j]
        if g[0]['clip'] != f[0]['clip'] or g[0]['s'] - f[-1]['e'] > 60: break
        tg = toks(g)
        if not tk or not tg: continue
        n = min(3, len(tk))
        aberto = not re.search(r'[.!?…]$', f[-1]['w']) or len(tk) <= 6
        if len(tk) <= max(6, len(tg)) and tk[:n] == tg[:n] and aberto and len(tk) < len(tg):
            for w in f: remove.setdefault(w['i'], f'falso começo (refeito em F{j + 1:03d})')
            break
        sim = difflib.SequenceMatcher(None, tk, tg).ratio()
        if sim >= C['retake_sim'] and len(tk) >= C['retake_min_palavras']:
            for w in f: remove.setdefault(w['i'], f'retake (fica a última: F{j + 1:03d}, {sim:.0%} igual)')
            break
        if 0.6 <= sim < C['retake_sim'] and len(tk) >= C['retake_min_palavras']:
            duvidas.append(f'F{k + 1:03d} parece retake de F{j + 1:03d} ({sim:.0%}) — mantive as duas; decida')
    # hesitação inequívoca no meio da frase (com pausa em volta) também sai
    for m, w in enumerate(f):
        if w['filler'] and C['vicios'] != 'nenhum':
            remove.setdefault(w['i'], 'hesitação')
        elif E.talvez_vicio(w['w']) and C['vicios'] == 'isolados' and 0 < m < len(f) - 1:
            a = w['s'] - f[m - 1]['e']; b = f[m + 1]['s'] - w['e']
            if a >= C['pausa_vicio'] and b >= C['pausa_vicio'] and E.norm(w['w']) in ('e', 'eh', 'ah', 'a', 'um', 'tipo', 'ne', 'assim', 'enfim', 'entao'):
                duvidas.append(f"#{w['i']} \"{w['w']}\" isolado por pausa em F{k + 1:03d} — parece vício; mantive")
if '--sem-vicios' in A:
    remove = {i: m for i, m in remove.items() if m != 'hesitação'}
for i in forca_rem: remove[i] = 'pedido'
for i in forca_man: remove.pop(i, None)

# ── trechos mantidos ──
aud = {}
def energia(clip):
    if clip not in aud:
        x = E.load_wav(P / '_edit/audio' / f'{clip}.wav', 48000)
        aud[clip] = (E.rms_env(x, 48000, 0.005), len(x) / 48000)
    return aud[clip]

def refina(t, lado, w0, clip):
    """move a borda para o vale de energia mais próximo (±40 ms), sem invadir a palavra; depois encaixa no frame."""
    env, dur = energia(clip); hop = 0.005
    a, b = (t - 0.04, min(t + 0.04, w0 - 0.025)) if lado == 'in' else (max(t - 0.04, w0 + 0.03), t + 0.04)
    ia, ib = max(0, int(a / hop)), min(len(env) - 1, int(b / hop))
    if ib > ia: t = (ia + int(np.argmin(env[ia:ib + 1]))) * hop
    t = min(max(0.0, t), dur)
    f = (np.floor if lado == 'in' else np.ceil)(t * FPS + 1e-6) / FPS
    return round(float(f), 4)

keep = [w for w in words if w['i'] not in remove]
segs, cur = [], []
for k, w in enumerate(keep):
    if cur and (w['clip'] != cur[-1]['clip'] or w['s'] - cur[-1]['e'] > C['pausa_max'] or w['i'] != cur[-1]['i'] + 1 and w['s'] - cur[-1]['e'] > 0.12):
        segs.append(cur); cur = []
    cur.append(w)
if cur: segs.append(cur)

out = []
for ws in segs:
    clip = ws[0]['clip']
    tin = refina(ws[0]['s'] - C['folga_antes'], 'in', ws[0]['s'], clip)
    tout = refina(ws[-1]['e'] + C['folga_depois'], 'out', ws[-1]['e'], clip)
    if out and out[-1]['clip'] == clip and tin < out[-1]['src_out']:     # folgas se tocam: emenda contínua
        out[-1]['src_out'] = tout; out[-1]['palavras'] += [w['i'] for w in ws]; out[-1]['texto'] += ' ' + ' '.join(w['w'] for w in ws)
        continue
    out.append({'clip': clip, 'src_in': tin, 'src_out': tout, 'palavras': [w['i'] for w in ws], 'texto': ' '.join(w['w'] for w in ws)})
out = [s for s in out if s['src_out'] - s['src_in'] >= C['min_trecho']]
if '--sem-cortes' in A or B.get('sem_cortes'):      # /legendar: mantém cada clipe inteiro (só legenda/som/cor), na ordem
    remove = {}; out = []
    for c in inv['clips']:
        ws_c = [w for w in words if w['clip'] == c['id']]
        out.append({'clip': c['id'], 'src_in': 0.0, 'src_out': round(np.floor(c['dur'] * FPS) / FPS, 4), 'palavras': [w['i'] for w in ws_c], 'texto': ' '.join(w['w'] for w in ws_c)})
t = 0.0
for n, s in enumerate(out):
    s['id'] = f's{n + 1:03d}'; s['dur'] = round(s['src_out'] - s['src_in'], 4)
    s['seq_in'] = round(t, 4); t += s['dur']; s['seq_out'] = round(t, 4)
total = round(t, 4)

removidos, cur = [], None
for w in words:
    m = remove.get(w['i'])
    if m and cur and cur['motivo'] == m and w['i'] == cur['ate'] + 1:
        cur['ate'] = w['i']; cur['texto'] += ' ' + w['w']; cur['e'] = w['e']
    elif m:
        cur = {'de': w['i'], 'ate': w['i'], 'motivo': m, 'texto': w['w'], 'clip': w['clip'], 's': w['s'], 'e': w['e']}; removidos.append(cur)
    else:
        cur = None

E.jsave(P / '_edit/notas_faladas.json', NOTAS)
if NOTAS:
    NL = ['# Notas faladas — direção dada na gravação', '', 'Saíram do vídeo. Cada uma vale para o trecho logo depois dela (âncora = palavra de docs/FRASES.md).', '',
          '| # | âncora | nota | fechada |', '|---|---|---|---|'] + [f"| {n + 1} | {x['ancora'] or '—'} | {x['texto']} | {'sim' if x['fechada'] else 'NÃO (até o fim da frase)'} |" for n, x in enumerate(NOTAS)]
    NL += ['', 'Próximo: leve cada nota para o plano/mapa (o item começa na âncora). Nota é ordem de quem gravou — só não cumpre se ferir regra (CFM, licença, fonte na tela).']
    (P / 'docs/NOTAS_FALADAS.md').write_text('\n'.join(NL) + '\n', encoding='utf-8')
E.jsave(P / '_edit/cortes.json', {'fps': FPS, 'estilo': ESTILO, 'parametros': C, 'segmentos': out, 'removidos': removidos, 'duvidas': duvidas, 'duracao': total})

# ── linha do tempo: palavras no tempo final ──
idx = {w['i']: w for w in words}
tl_words = []
for s in out:
    off = s['seq_in'] - s['src_in']
    for i in s['palavras']:
        w = idx[i]
        tl_words.append({'i': i, 'w': w['w'], 's': round(max(s['seq_in'], w['s'] + off), 4), 'e': round(min(s['seq_out'], w['e'] + off), 4), 'seg': s['id'], 'p': w['p']})
E.jsave(P / '_edit/timeline.json', {'fps': FPS, 'duracao': total, 'segmentos': out, 'palavras': tl_words})

# ── docs/CORTES.md ──
bruto = sum(c['dur'] for c in inv['clips'])
alvo = B.get('duracao_alvo')
L = [f'# Corte proposto — estilo {ESTILO}', '',
     f'**{bruto:.1f} s de bruto → {total:.1f} s** ({len(out)} trechos, {len(removidos)} remoções)' + (f' · alvo {alvo} s' if alvo else ''), '']
if alvo and total > float(alvo) * 1.1:
    L += [f'> ⚠ {total - float(alvo):.0f} s acima do alvo. Condense por ideia inteira (frase), nunca no meio: monte 2 opções (quais F### saem e quanto fica) e aplique com `cortes.py . --remover F009,F012`.', '']
L += ['## Trechos que ficam', '', '| id | origem | seq | dur | texto |', '|---|---|---|---|---|']
for s in out:
    L.append(f"| {s['id']} | {s['clip']} {E.tc(s['src_in'])}–{E.tc(s['src_out'])} | {E.tc(s['seq_in'])} | {s['dur']:.2f} | {s['texto']} |")
L += ['', '## O que saiu', '', '| palavras | motivo | texto |', '|---|---|---|']
for r in removidos:
    L.append(f"| #{r['de']}–#{r['ate']} | {r['motivo']} | ~~{r['texto']}~~ |")
if duvidas:
    L += ['', '## Dúvidas (não cortei — decida)', ''] + [f'- {d}' for d in duvidas]
L += ['', 'Ajuste: `cortes.py . --remover 8-12` / `--manter 42` (índices de docs/FRASES.md). Aprovou? `cortes.py . --travar`.']
(P / 'docs/CORTES.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L[:3]))
for r in removidos: print(f"  − #{r['de']}–#{r['ate']} {r['motivo']}: {r['texto']}")
for x in NOTAS: print(f"  ✎ nota falada → {x['ancora']}: {x['texto']}")
for d in duvidas: print(f'  ? {d}')
if '--travar' in A:
    E.log_estado(P, 'cortes', 'travado', f'{total:.1f} s'); print('🔒 corte travado (aprovado)')
else:
    E.log_estado(P, 'cortes', 'aguardando_aprovacao', f'{total:.1f} s')
