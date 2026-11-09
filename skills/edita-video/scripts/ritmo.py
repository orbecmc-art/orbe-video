#!/usr/bin/env python3
"""ritmo.py — gramática de batidas, ritmo medido e junções do ESTILO (método do Style Studio, adaptado ao edita-video).

    python3 ritmo.py <projeto> batidas     # sugere a batida de cada frase (docs/BATIDAS.md) com a peça e a junção do estilo
    python3 ritmo.py <projeto> [checar]    # confere o mapa + câmera contra o estilo (docs/RITMO.md); sai 1 se houver ✗
    python3 ritmo.py <projeto> cor         # escolhe a cor de destaque do vídeo em rodízio (nunca a do último deste cliente)

Batidas (o que a frase FAZ no roteiro): gancho · virada (a revelação/payoff) · item (um de uma lista) · numero ·
ponto (argumento) · prova (depoimento, print, notícia, caso) · fim (fecho/CTA). Cada estilo diz, em estilos.json →
"batidas", que peça carrega cada batida (1ª escolha primeiro; "rosto", "rosto:split", "rosto:janela" = fica na pessoa
nesse layout) e com que junção entra ("entra"). Marque a batida no item do mapa ("batida": "numero"); o checar avisa
quando a peça ou a junção não é a do estilo.

Ritmo (estilos.json → "ritmo"): mudanca [curto, longo] = segundos entre mudanças NA TELA (corte, punch-in, peça que
entra, B-roll, quebra — legenda trocando NÃO conta); parado_max = nunca mais que isso sem mudança; plano_min = nenhum
plano menor que 0,75 s; fim_max = o vídeo acaba até X s depois da última palavra; ppm = fala por minuto (informativo).
Junções (estilos.json → "juncoes"): as que o estilo aceita — as outras são RECUSADAS (✗). Zoom/flash só na 1ª e na
que mais importa de uma série. Slam: no máximo 2 por vídeo e nunca dois seguidos.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
if not A: E.die(__doc__)
P = E.proj(A[0]); CMD = A[1] if len(A) > 1 else 'checar'
B, EST, ESTILO = E.config(P)
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes (falta _edit/timeline.json)')
PAL = tl['palavras']; DUR = tl['duracao']
RIT = dict({'mudanca': [3, 5], 'parado_max': 5.5, 'plano_min': 0.75, 'fim_max': 2.0, 'ppm': [150, 200]}, **(EST.get('ritmo') or {}))
JUN = EST.get('juncoes') or ['corte', 'fade', 'zoom', 'whip', 'flash', 'deslize', 'recuo']
BAT = EST.get('batidas') or {}
PADRAO_J = {'corte': 'corte', 'suave': 'fade', 'dinamica': 'zoom'}.get(EST.get('transicao', 'corte'), EST.get('transicao', 'corte'))

def frases():
    """frases faladas: quebra em pontuação forte, pausa > 0,5 s ou corte."""
    out, cur = [], []
    for k, w in enumerate(PAL):
        cur.append(w)
        nx = PAL[k + 1] if k + 1 < len(PAL) else None
        if nx is None or re.search(r'[.!?…]$', w['w']) or nx['s'] - w['e'] > 0.5 or (nx['seg'] != w['seg'] and re.search(r'[,;:]$', w['w'])):
            out.append(cur); cur = []
    return [f for f in out if f]

NUM = re.compile(r'\d|\b(mil|milh[ãa]o|milh[õo]es|bilh[ãa]o|dobro|metade|triplo|por ?cento|reais|dias|horas|anos)\b', re.I)
ENUM = re.compile(r'\b(primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]|passo|dica|motivo|erro|regra|etapa|n[úu]mero (um|dois|tr[êe]s))\b', re.I)
PROVA = re.compile(r'\b(disse|falou|segundo|estudo|pesquisa|cliente|caso|resultado|print|not[íi]cia|depoimento|aconteceu|a gente fez)\b', re.I)
VIRADA = re.compile(r'\b(mas|s[óo] que|o segredo|a verdade|na real|o problema|por isso|resultado|ent[ãa]o|descobri|o que ningu[ée]m)\b', re.I)
CTA = re.compile(r'\b(comenta|segue|salva|compartilha|link|clica|chama|manda|agende|marque|me (chama|segue))\b', re.I)

def batida_de(i, f, n):
    tx = ' '.join(w['w'] for w in f)
    if i == 0: return 'gancho', 'abre o vídeo'
    if i == n - 1 or CTA.search(tx): return 'fim', 'fecho/CTA'
    if NUM.search(tx): return 'numero', 'tem número/quantidade'
    if ENUM.search(tx): return 'item', 'enumera (primeiro, passo, motivo…)'
    if PROVA.search(tx): return 'prova', 'cita caso, estudo, resultado'
    if VIRADA.search(tx) and i <= 3: return 'virada', 'revela/vira o argumento'
    return 'ponto', 'argumento'

if CMD == 'batidas':
    fs = frases(); L = [f'# Batidas — {P.name} (estilo {ESTILO})', '',
                        'Sugestão automática (heurística): confira e marque no mapa com "batida". A peça é a 1ª escolha do estilo.', '',
                        '| # | quando | batida | por quê | o estilo carrega com | entra | frase |', '|---|---|---|---|---|---|---|']
    for i, f in enumerate(fs):
        b, why = batida_de(i, f, len(fs)); cfg = BAT.get(b, {})
        usa = ' / '.join(cfg.get('usa', [])[:3]) or '—'
        L.append(f"| {i + 1} | {E.tc(f[0]['s'])} (#{f[0]['i']}) | **{b}** | {why} | {usa} | {cfg.get('entra', PADRAO_J)} | {' '.join(w['w'] for w in f)[:90]} |")
    L += ['', f"Ritmo do estilo: algo muda na tela a cada {RIT['mudanca'][0]}–{RIT['mudanca'][1]} s · nunca parado > {RIT['parado_max']} s · "
          f"fim ≤ {RIT['fim_max']} s após a última palavra · junções aceitas: {', '.join(JUN)}.",
          'Regra de ouro (Joseph/Stockton): VOCÊ decide o que a cena mostra; a skill decide como ela fica.']
    (P / 'docs').mkdir(exist_ok=True); (P / 'docs/BATIDAS.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L)); sys.exit()

if CMD == 'cor':
    kit = B.get('cliente_kit'); marca = B.get('marca') or {}
    roda = marca.get('rodizio') or (E.jload(Path(kit) / 'marca.json', {}) or {}).get('rodizio') if kit else marca.get('rodizio')
    roda = roda or EST.get('rodizio')
    if not roda: print('sem rodízio: defina "rodizio": ["#hex", …] no marca.json do cliente (ou no estilo) — a cor de destaque fica a da marca'); sys.exit()
    hist_f = Path(kit) / 'historico.json' if kit else P / '_edit/historico_cor.json'
    hist = E.jload(hist_f, {}) or {}; ult = hist.get('ultima_cor')
    op = [c for c in roda if c.lower() != (ult or '').lower()] or roda
    idx = (roda.index(ult) + 1) % len(roda) if ult in roda else 0
    cor = roda[idx] if roda[idx] in op else op[0]
    aj = B.setdefault('ajustes', {}); aj.setdefault('marca', {})['accent'] = cor
    E.jsave(P / '_edit/briefing.json', B); hist['ultima_cor'] = cor; hist.setdefault('videos', []).append({'projeto': P.name, 'cor': cor})
    hist_f.parent.mkdir(parents=True, exist_ok=True); E.jsave(hist_f, hist)
    print(f'✔ cor de destaque deste vídeo: {cor} (a do último era {ult or "—"}) → briefing.ajustes.marca.accent'); sys.exit()

# ───────────────────────── checar ─────────────────────────
mapa = E.jload(P / '_edit/mapa.json', {}) or {}; cam = E.jload(P / '_edit/camera.json', {}) or {}
itens = [it for it in mapa.get('itens', []) if it.get('t_ini') is not None]
err, warn, info = [], [], []
mud = []      # (t, o quê, é corte?)
for s in tl['segmentos'][1:]: mud.append((s['seq_in'], f"corte {s['id']}", True))
for p in cam.get('punch', []): mud.append((p['t'], f"punch «{p.get('palavra', '')}»", False))
for it in itens:
    m = it.get('modo', 'sobreposto')
    if it.get('tipo') == 'efeito': mud.append((it['t_ini'], f"{it['id']} {it.get('efeito')}", False)); continue
    mud.append((it['t_ini'], f"{it['id']} entra ({it.get('peca') or it['tipo']})", m != 'sobreposto'))
    if m != 'sobreposto' and it['t_fim'] < DUR - 0.2: mud.append((it['t_fim'], f"{it['id']} volta ao rosto", True))
mud.sort()
fala_ini = PAL[0]['s'] if PAL else 0; fim_fala = PAL[-1]['e'] if PAL else DUR
marcos = [0.0] + [t for t, _, _ in mud] + [DUR]
gaps = [(a, b) for a, b in zip(marcos, marcos[1:]) if b - a > 0]
lo, hi = RIT['mudanca']
for a, b in gaps:
    g = b - a
    if g > RIT['parado_max'] and not (a >= fim_fala - 0.05): err.append(f"{E.tc(a)}–{E.tc(b)}: {g:.1f}s sem NADA mudar na tela (estilo: nunca > {RIT['parado_max']}s) — punch, peça, corte ou B-roll")
    elif g > hi * 1.3 and not (a >= fim_fala - 0.05): warn.append(f"{E.tc(a)}–{E.tc(b)}: {g:.1f}s sem mudança (estilo pede {lo}–{hi}s)")
media = (min(DUR, fim_fala) - fala_ini) / max(1, len([1 for t, _, _ in mud if fala_ini <= t <= fim_fala]))
info.append(f"mudança na tela a cada {media:.1f}s em média (estilo {ESTILO}: {lo}–{hi}s curto/longo)")
if media > hi * 1.15: warn.append(f"ritmo lento para o estilo: {media:.1f}s por mudança (alvo {lo}–{hi}s) — mais punch (camera.punch_modo) ou mais peças")
if media < lo * 0.6: warn.append(f"ritmo frenético para o estilo: {media:.1f}s por mudança (alvo {lo}–{hi}s) — o olho não descansa")
cortes = sorted(t for t, _, c in mud if c)
for a, b in zip([0.0] + cortes, cortes + [DUR]):
    if 0 < b - a < RIT['plano_min'] - 1e-3: warn.append(f"plano de {b - a:.2f}s em {E.tc(a)} (< {RIT['plano_min']}s não registra) — emende ou estique")
cauda = DUR - fim_fala
if cauda > RIT['fim_max'] + 0.05: warn.append(f"o vídeo segue {cauda:.1f}s depois da última palavra (estilo: ≤ {RIT['fim_max']}s) — corte o fim")
# junções
fz = []
for it in itens:
    if it.get('tipo') == 'efeito': continue
    m = it.get('modo', 'sobreposto')
    if m == 'sobreposto': continue
    j = 'recuo' if m == 'janela' else it.get('transicao', PADRAO_J)
    if j not in JUN: err.append(f"{it['id']}: junção '{j}' — o estilo {ESTILO} RECUSA (aceita {', '.join(JUN)})")
    if j in ('zoom', 'flash'): fz.append(it['id'])
if len(fz) > max(2, round(DUR / 20)): warn.append(f"zoom/flash em {len(fz)} entradas ({', '.join(fz)}) — guarde para a 1ª e a que mais importa de cada série")
# batidas
for it in itens:
    b = it.get('batida')
    if not b: continue
    if b not in ('gancho', 'virada', 'item', 'numero', 'ponto', 'prova', 'fim'): err.append(f"{it['id']}: batida '{b}' não existe"); continue
    cfg = BAT.get(b) or {}; usa = cfg.get('usa') or []
    if it.get('tipo') == 'efeito': continue
    peca = it.get('peca') or it['tipo']; m = it.get('modo', 'sobreposto')
    if usa and peca not in usa and f'rosto:{m}' not in usa:
        warn.append(f"{it['id']}: batida {b} com '{peca}' — o estilo {ESTILO} carrega {b} com {' / '.join(usa)}")
    if cfg.get('entra') and m != 'sobreposto' and it.get('transicao', PADRAO_J) != cfg['entra'] and m != 'janela':
        info.append(f"{it['id']}: batida {b} costuma entrar com '{cfg['entra']}' neste estilo (está '{it.get('transicao', PADRAO_J)}')")
# slam
sl = [it for it in sorted(itens, key=lambda x: x['t_ini']) if it.get('peca') == 'slam']
if len(sl) > 2: err.append(f"{len(sl)} slams — no máximo 2 por vídeo (perde o impacto)")
ordem = [it for it in sorted(itens, key=lambda x: x['t_ini']) if it.get('tipo') != 'efeito']
for a, b in zip(ordem, ordem[1:]):
    if a.get('peca') == 'slam' and b.get('peca') == 'slam': err.append(f"{a['id']} e {b['id']}: dois slams seguidos")
# fala por minuto
fala = sum(w['e'] - w['s'] for w in PAL); ppm = len(PAL) / max(1e-6, (fim_fala - fala_ini) / 60)
info.append(f"fala: {ppm:.0f} palavras/min (estilo {RIT['ppm'][0]}–{RIT['ppm'][1]})")
if ppm < RIT['ppm'][0] * 0.85: info.append('fala lenta para o estilo: aperte as pausas (cortes.pausa_max) ou escolha um estilo mais calmo')

L = [f'# Ritmo — {P.name} (estilo {ESTILO})', '', *[f'- ✗ {x}' for x in err], *[f'- ⚠ {x}' for x in warn], *[f'- · {x}' for x in info], '',
     '## Linha do tempo das mudanças', '', '| quando | o quê |', '|---|---|', *[f'| {E.tc(t)} | {o} |' for t, o, _ in mud]]
(P / 'docs').mkdir(exist_ok=True); (P / 'docs/RITMO.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L[:2 + len(err) + len(warn) + len(info)]))
print(f"✔ docs/RITMO.md · {len(err)} ✗ · {len(warn)} ⚠")
sys.exit(1 if err else 0)
