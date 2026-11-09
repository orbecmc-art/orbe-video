#!/usr/bin/env python3
"""momentos.py — CORTES DE VÍDEO LONGO (podcast, live, aula, entrevista): acha os melhores trechos e vira projetos curtos.

    python3 momentos.py <projeto> [--min 20] [--max 60] [--n 10]     # candidatos → docs/MOMENTOS.md + _edit/momentos.json
    python3 momentos.py <projeto> extrair 1,3,4                       # cada escolhido vira o projeto <projeto>-c01, -c03…

Pré-requisito: preparar.py rodado no vídeo longo (transcrição por palavra). Candidatos começam e terminam em frase
inteira e são pontuados por: gancho na 1ª frase (pergunta, número, palavra forte), começar sem depender do antes ("e",
"mas", "isso", "ele"… no começo perdem ponto), fechar com conclusão, número/lista no meio, fala viva (palavras por
segundo) e poucas hesitações. É a triagem — quem escolhe é o Claude lendo os 10 melhores (assunto, emoção, cliente) e
o usuário aprovando. Cada projeto extraído já vem com o corte só daquele trecho; siga o fluxo normal (rosto → câmera
9:16 → legendas → motion → som → final). Nunca tirar frase do contexto para mudar o sentido do que a pessoa disse.
"""
import sys, os, re, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
if not A: E.die(__doc__)
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0]); CMD = A[1] if len(A) > 1 and not A[1].startswith('--') else 'listar'
words = E.jload(P / '_edit/words.json') or E.die('rode preparar.py antes (falta _edit/words.json)')

def frases(ws):
    out, cur = [], []
    for k, w in enumerate(ws):
        cur.append(w); nx = ws[k + 1] if k + 1 < len(ws) else None
        gap = (nx['s'] - w['e']) if nx and nx['clip'] == w['clip'] else 99
        if re.search(r'[.!?…]$', w['w']) or gap >= 0.6 or not nx: out.append(cur); cur = []
    return [f for f in out if f]
FR = frases(words)
FORTE = re.compile(r'\b(ningu[ée]m|nunca|sempre|segredo|erro|errado|verdade|mentira|dinheiro|milh[ãa]o|mil|resultado|problema|pior|melhor|maior|simples|r[áa]pido|cuidado|proibido|ningu[ée]m te conta|pare|para de)\b', re.I)
DEPENDE = re.compile(r'^(e|mas|ent[ãa]o|porque|isso|esse|essa|ele|ela|eles|a[ií]|tipo|tamb[ée]m|da[ií])\b', re.I)
FECHO = re.compile(r'\b(por isso|ent[ãa]o|resumindo|no fim|a li[çc][ãa]o|o ponto [ée]|[ée] isso|entendeu|faz sentido)\b', re.I)
NUM = re.compile(r'\d|\b(um|dois|tr[êe]s|quatro|cinco|dez|cem|mil|primeiro|segundo|terceiro)\b', re.I)

if CMD == 'extrair':
    esc = [int(x) for x in A[2].split(',')]
    cand = E.jload(P / '_edit/momentos.json') or E.die('rode momentos.py . primeiro')
    for k in esc:
        c = next((x for x in cand if x['rank'] == k), None)
        if not c: print(f'✗ #{k} não está na lista'); continue
        d = P.parent / f'{P.name}-c{k:02d}'
        if d.exists(): shutil.rmtree(d)
        def lnk(a, b):
            if '/brutos/' in a or '/_edit/mez/' in a:
                try: os.link(a, b); return b
                except OSError: pass
            return shutil.copy2(a, b)
        shutil.copytree(P, d, ignore=shutil.ignore_patterns('renders', 'entregas', 'motion', 'timeline.json', 'cortes.json', 'mapa.json', 'camera.json', 'legendas.*'), copy_function=lnk)
        fora = [[w['i'], w['i']] for w in words if not (c['de'] <= w['i'] <= c['ate'])]
        E.jsave(d / '_edit/cortes_ajustes.json', {'remover': fora, 'manter': []})
        b = E.jload(d / '_edit/briefing.json', {}) or {}; b['nome'] = f"{b.get('nome', P.name)}-c{k:02d}"; b['corte_de'] = {'origem': P.name, 'de': c['de'], 'ate': c['ate'], 'gancho': c['gancho']}
        E.jsave(d / '_edit/briefing.json', b)
        print(f"✔ #{k} → {d.name} ({c['dur']:.0f}s: \"{c['gancho'][:70]}\") — siga: cortes.py {d.name} → rosto.py → câmera…")
    sys.exit()

MN, MX, N = float(opt('min', 20)), float(opt('max', 60)), int(opt('n', 10))
cands = []
for i in range(len(FR)):
    if DEPENDE.match(FR[i][0]['w']) and i > 0: pen0 = 1.2
    else: pen0 = 0
    for j in range(i, len(FR)):
        if FR[j][0]['clip'] != FR[i][0]['clip']: break
        t0, t1 = FR[i][0]['s'], FR[j][-1]['e']; d = t1 - t0
        if d > MX: break
        if d < MN: continue
        ws = [w for f in FR[i:j + 1] for w in f]; txt0 = ' '.join(w['w'] for w in FR[i]); txt1 = ' '.join(w['w'] for w in FR[j])
        tx = ' '.join(w['w'] for w in ws)
        sc = 0.0; why = []
        if '?' in txt0: sc += 1.5; why.append('abre com pergunta')
        if NUM.search(txt0) and re.search(r'\d', txt0): sc += 1.2; why.append('número no gancho')
        if FORTE.search(txt0): sc += 1.0; why.append('palavra forte no gancho')
        if pen0: sc -= pen0; why.append('começa dependendo do antes')
        if re.search(r'[.!]$', FR[j][-1]['w']): sc += 0.6
        if FECHO.search(txt1): sc += 0.8; why.append('fecha com conclusão')
        if len(re.findall(r'\d', tx)) >= 2: sc += 0.6; why.append('tem números')
        pps = len(ws) / max(1e-3, sum(w['e'] - w['s'] for w in ws) + 1e-3)
        fala = len(ws) / d
        if 2.2 <= fala <= 3.6: sc += 0.5
        fill = sum(1 for w in ws if w.get('filler')) / max(1, len(ws))
        sc -= 3 * fill
        sc += 0.3 * min(1.0, len(FORTE.findall(tx)) / 3)
        if 25 <= d <= 45: sc += 0.4
        cands.append({'i': i, 'j': j, 'de': ws[0]['i'], 'ate': ws[-1]['i'], 't0': round(t0, 2), 'dur': round(d, 1), 'score': round(sc, 2),
                      'porque': ', '.join(why) or 'fala contínua', 'gancho': txt0[:140], 'fecho': txt1[:140]})
cands.sort(key=lambda c: -c['score']); esc = []
for c in cands:
    if all(c['j'] < e['i'] or c['i'] > e['j'] for e in esc): esc.append(c)
    if len(esc) >= N: break
for k, c in enumerate(esc): c['rank'] = k + 1
E.jsave(P / '_edit/momentos.json', esc)
L = [f'# Momentos — {P.name}', '', f'{len(FR)} frases · candidatos de {MN:.0f}–{MX:.0f} s · os {len(esc)} melhores (sem sobreposição).', '',
     '| # | quando | dur | nota | por quê | começa com | termina com |', '|---|---|---|---|---|---|---|']
L += [f"| {c['rank']} | {E.tc(c['t0'])} | {c['dur']:.0f}s | {c['score']} | {c['porque']} | {c['gancho'][:80]} | {c['fecho'][:60]} |" for c in esc]
L += ['', 'Leia os candidatos (assunto, emoção, o que o público do cliente quer), proponha 3–5 ao usuário e extraia: `momentos.py . extrair 1,3,4`.']
(P / 'docs').mkdir(exist_ok=True); (P / 'docs/MOMENTOS.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L))
