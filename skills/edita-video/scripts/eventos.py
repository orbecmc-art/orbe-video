#!/usr/bin/env python3
"""eventos.py — ETAPA 8: decide QUAL efeito sonoro em CADA momento (cada som nasce de um evento que se VÊ).

    python3 eventos.py <projeto> [--sem] [--ajuste sfx07=-3 sfx09=0ff sfx12=whoosh]

Fontes de evento (em ordem de prioridade):
  1. peças de motion (motion_cues.json: o som que a própria peça pede — pop no selo, ding no número, swish no marcador)
  2. entrada/saída de B-roll, foto e tela cheia (whip/zoom → whoosh; corte → swish leve; fade → nada; flash → impact)
  3. punch-in de ênfase (swish curto e baixo)
Regras (references/som.md; LeiteZ, video-use, pesquisa): densidade do estilo (som.sfx_por_30s; discreto/moderado/intenso),
≥ 0,25 s entre sons (fica o mais forte), ~0,5 s de respiro antes de impacto, nunca o mesmo tipo 3× seguidas (troca por
parente), pico no evento + 1 quadro (o sfx.mjs mede e posiciona), SFX abaixo da voz (over negativo contra voz+trilha).
Sem SFX de meme/game. Saídas: _edit/eventos_sfx.json (sfx01…) · docs/SOM.md (para pedir "sfx07 mais baixo" = −3 dB).
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P); SOM = EST['som']
tl = E.jload(P / '_edit/timeline.json'); DUR = tl['duracao']
mapa = E.jload(P / '_edit/mapa.json', {}) or {}; cam = E.jload(P / '_edit/camera.json', {}) or {}
nivel = 'nenhum' if ('--sem' in A or B.get('sfx') is False) else SOM.get('sfx', 'moderado')
AJ = E.jload(P / '_edit/sfx_ajustes.json', {}) or {}
if '--ajuste' in A:
    for x in A[A.index('--ajuste') + 1:]:
        if x.startswith('--'): break
        k, _, v = x.partition('='); AJ[k] = v
    E.jsave(P / '_edit/sfx_ajustes.json', AJ)
OVER = {'discreto': -10, 'moderado': -7, 'intenso': -5}.get(nivel, -7)
ev = []
if nivel != 'nenhum':
    for c in E.jload(P / '_edit/motion_cues.json', []) or []:
        pri = 3 if c.get('gain', 1) >= 0.6 else 1.5
        ev.append({'t': c['t'], 'type': c['type'], 'gain': c.get('gain', 0.8), 'pan': c.get('pan', 0), 'prio': pri, 'origem': f"{c['origem']} (peça)"})
    trans = {'whip': 'whoosh', 'zoom': 'whoosh', 'corte': 'swish', 'flash': 'impact', 'fade': None, 'deslize': 'whoosh', 'recuo': 'whoosh'}
    if SOM.get('familias') == 'minimal': trans.update({'corte': 'paper', 'deslize': 'whoosh', 'zoom': 'paper'})
    padrao = {'corte': 'corte', 'suave': 'fade', 'dinamica': 'zoom'}.get(EST.get('transicao', 'corte'), 'corte')
    for it in mapa.get('itens', []):
        if it.get('t_ini') is None or it.get('sfx') == 'nenhum': continue
        if it.get('tipo') == 'efeito':
            if it.get('efeito') == 'quebra': ev.append({'t': it['t_ini'], 'type': it.get('sfx') if it.get('sfx') not in (None, 'auto') else 'thump', 'gain': 0.55, 'prio': 2.6, 'origem': f"{it['id']} quebra"})
            if it.get('efeito') == 'pb': ev.append({'t': max(0, it['t_fim'] - 0.4), 'type': it.get('sfx') if it.get('sfx') not in (None, 'auto') else 'riser', 'gain': 0.5, 'prio': 2.6, 'origem': f"{it['id']} cor"})
            continue
        if it.get('modo') not in ('tela_cheia', 'split', 'janela'): continue
        tp = trans.get('recuo' if it.get('modo') == 'janela' else it.get('transicao', padrao))
        if it.get('sfx') not in (None, 'auto'): tp = it['sfx']
        if tp:
            ev.append({'t': it['t_ini'], 'type': tp, 'gain': 0.7, 'prio': 2.5, 'origem': f"{it['id']} entra"})
            if nivel == 'intenso' and it['t_fim'] < DUR - 0.3:
                ev.append({'t': it['t_fim'], 'type': 'swish', 'gain': 0.35, 'prio': 1, 'origem': f"{it['id']} sai", 'pan': -0.2})
    if nivel != 'discreto':
        for p in cam.get('punch', []):
            ev.append({'t': p['t'], 'type': 'swish', 'gain': 0.35, 'prio': 1.2, 'origem': f"punch-in «{p['palavra']}»"})
for e in ev:
    if e['t'] < 2.0: e['prio'] += 1.5          # o gancho (2 s iniciais) sempre tem som
ev.sort(key=lambda e: e['t'])
# ≥ 0,25 s entre sons: fica o de maior prioridade
fil = []
for e in ev:
    if fil and e['t'] - fil[-1]['t'] < 0.25:
        if e['prio'] > fil[-1]['prio']: fil[-1] = e
        continue
    fil.append(e)
# densidade: corta os de menor prioridade até caber em sfx_por_30s
cap = max(1, round(SOM.get('sfx_por_30s', 6) * DUR / 30)) if nivel != 'nenhum' else 0
if len(fil) > cap:
    # 1º o som PRINCIPAL de cada item (cada peça/B-roll ganha o seu), depois os secundários — espalhado no vídeo todo,
    # nunca 4 sons no gancho e silêncio depois
    grupo = lambda e: e['origem'].split(' ')[0]
    princ = {}
    for e in fil:
        g_ = grupo(e)
        if g_ not in princ or (e.get('gain', 0), -e['t']) > (princ[g_].get('gain', 0), -princ[g_]['t']): princ[g_] = e
    P1 = sorted(princ.values(), key=lambda e: -e['prio']); resto = sorted([e for e in fil if e not in P1], key=lambda e: -e['prio'])
    cap = max(cap, min(len(P1), round(DUR / 4)))      # todo item visível tem som, até 1 a cada ~4 s mesmo no discreto
    if len(P1) > cap:      # mais itens que sons: escolhe espalhando (maior distância ao já escolhido)
        esc = [P1[0]]
        while len(esc) < cap:
            esc.append(max([e for e in P1 if e not in esc], key=lambda e: (min(abs(e['t'] - x['t']) for x in esc), e['prio'])))
        P1 = esc
    fil = sorted((P1 + resto)[:cap], key=lambda e: e['t'])
# variedade: o mesmo tipo 3× seguidas vira parente
PARENTE = {'swish': 'swipe', 'whoosh': 'swish', 'pop': 'bloop', 'tick': 'click', 'click': 'tick', 'ding': 'chime', 'thump': 'impact', 'paper': 'swish', 'marker': 'tick'}
for k in range(2, len(fil)):
    if fil[k]['type'] == fil[k - 1]['type'] == fil[k - 2]['type'] and fil[k]['type'] in PARENTE: fil[k]['type'] = PARENTE[fil[k]['type']]
# respiro antes de impacto: rebaixa o som que vem < 0,5 s antes
for k in range(1, len(fil)):
    if fil[k]['type'] in ('impact', 'boom', 'thump') and fil[k]['t'] - fil[k - 1]['t'] < 0.5: fil[k - 1]['gain'] *= 0.6
out = []
for k, e in enumerate(fil):
    sid = f'sfx{k + 1:02d}'; aj = str(AJ.get(sid, ''))
    if aj.lower() in ('off', '0ff', 'remover', 'x'): continue
    c = {'id': sid, 't': round(e['t'], 4), 'type': e['type'], 'gain': round(e['gain'], 3), 'pan': e.get('pan', 0), 'over': OVER + (0 if e['prio'] >= 2 else -3), 'origem': e['origem']}
    if re.match(r'^[+-]?\d+(\.\d+)?$', aj): c['over'] += float(aj)
    elif aj: c['type'] = aj
    out.append(c)
E.jsave(P / '_edit/eventos_sfx.json', {'nivel': nivel, 'cues': out})
L = [f'# Som — {len(out)} efeitos · nível {nivel} · teto {cap} em {DUR:.0f}s · SFX {abs(OVER)} dB abaixo de voz+trilha', '',
     'Ajuste por número: `eventos.py . --ajuste sfx07=-3` (mais baixo) · `sfx09=off` (remove) · `sfx12=whoosh` (troca).', '',
     '| id | quando | som | nasce de | nível |', '|---|---|---|---|---|']
for c in out: L.append(f"| {c['id']} | {E.tc(c['t'])} | {c['type']} | {c['origem']} | {c['over']:+.0f} dB |")
mus = B.get('musica', EST.get('musica', 'gerar'))
L += ['', f"Trilha: {mus if isinstance(mus, str) else mus}", 'Lembre: o Claude não ouve — o audit mede (pico no evento +1 quadro, SFX abaixo da voz, voz presente no mix).']
(P / 'docs/SOM.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L[:1] + L[4:4 + len(out) + 2]))
