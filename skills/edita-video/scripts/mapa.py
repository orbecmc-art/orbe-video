#!/usr/bin/env python3
"""mapa.py — ETAPA 4 (a mais importante): o MAPA de motion, B-roll, fotos e ênfases ancorado nas palavras.

    python3 mapa.py <projeto> rascunho     # sugere encaixes (você, Claude, decide e escreve _edit/mapa.json)
    python3 mapa.py <projeto>              # valida o mapa.json, resolve âncoras → tempos, escreve docs/MAPA.md

Formato de _edit/mapa.json (references/motion-e-broll.md):
{ "itens": [
   {"id":"mo01","tipo":"motion","peca":"numero","de":"#24","ate":"#29","modo":"sobreposto","posicao":"baixo",
    "texto":"2 horas","params":{"valor":2,"sufixo":"h","rotulo":"e a oleosidade volta"},"sfx":"auto"},
   {"id":"br01","tipo":"broll","busca":"mulher lavando o rosto pia","de":"#30","dur":2.2,"modo":"tela_cheia","kenburns":"in"},
   {"id":"ft01","tipo":"foto","arquivo":"assets/ft01.jpg","de":12.4,"dur":1.6,"modo":"split"} ],
  "enfase_palavras":[24,57], "musica":{"gerar":{"style":"warm","bpm":92}} }
  · de/ate: "#<índice da palavra>" (FRASES.md) — prefira; ou segundos da sequência. "dur" no lugar de "ate".
  · tipo: motion (peça do motion-studio: titulo · palavra · numero · lista · lower_third · check · comparacao · cta ·
    minimal: frase · aspas · linha · grafico · capitulos · callout · lifestyle: empilha · rotulo · doc · entrevista:
    cartela (tela_cheia) · custom→projeto motion-studio próprio em "projeto"). posicao "auto" = espaço livre (rosto medido). · broll (vídeo: "arquivo" ou "busca") · foto · texto (cartela).
  · modo: sobreposto (por cima do rosto, fundo transparente) · tela_cheia (corta para o item) · split (item em cima,
    rosto embaixo) · janela (item toma a tela, a câmera vira cartão quadrado com anel — entra e sai com recuo).
  · tipo "efeito" (sem peça): {"tipo":"efeito","efeito":"quebra","de":"#40","ate":"#52"} = quebra de padrão (close no
    nariz, P&B, reverb na voz, trilha abafada) — 1 por vídeo, na virada de assunto. "efeito": "pb" = o quadro inteiro
    em P&B e a cor ESCORRE nos últimos 12 quadros (abertura que segura até a revelação; receita pb-cor das variações).
  · "batida" (opcional, ritmo.py): gancho · virada · item · numero · ponto · prova · fim — o ritmo.py confere se o estilo
    carrega essa batida com essa peça e essa junção.
Validação: duração mínima (motion 0,8 s · B-roll 1,2 s) e máxima (B-roll 4 s), sem sobreposição de tela cheia,
≥ rosto_entre s de rosto entre cortes para fora, densidade por minuto do estilo, gancho nos 2 s iniciais,
arquivos existentes, CTA no fim. Nunca FONTES/créditos na tela (regra Orbe) — vão para docs/CREDITOS.md.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') and A[0] != 'rascunho' else None)
B, EST, ESTILO = E.config(P); MO, BR = EST['motion'], EST['broll']
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes'); FPS = tl['fps']; DUR = tl['duracao']
PAL = {w['i']: w for w in tl['palavras']}
snap = lambda t: round(t * FPS) / FPS
SYNC = ('empilha', 'cartela')                       # peças que recebem as palavras ditas com tempo (params._palavras)
CORR = {k: v for k, v in (E.jload(P / '_edit/correcoes.json', {}) or {}).items() if k.startswith('#')}

def ancora(v, fim=False):
    if v is None: return None
    if isinstance(v, str) and v.startswith('#'):
        i = int(v[1:])
        if i not in PAL:      # palavra cortada: usa a mais próxima que ficou
            vivos = sorted(PAL); i = min(vivos, key=lambda k: abs(k - i))
        return PAL[i]['e'] if fim else PAL[i]['s']
    return float(v)

# ───────────────────────── rascunho ─────────────────────────
if 'rascunho' in A:
    ws = tl['palavras']; sug = []
    ORD = {'primeiro': 1, 'primeira': 1, 'segundo': 2, 'segunda': 2, 'terceiro': 3, 'terceira': 3, 'quarto': 4, 'quinto': 5}
    CTA = {'comenta', 'comente', 'link', 'agenda', 'agende', 'chama', 'manda', 'mensagem', 'segue', 'siga', 'salva', 'salve', 'compartilha', 'clica', 'clique', 'bio', 'whatsapp', 'direct'}
    NUM = re.compile(r'\d')
    for k, w in enumerate(ws):
        n = E.norm(w['w'])
        if n in ORD: sug.append(('lista', w, f'item {ORD[n]} de uma lista → motion "lista" ou "titulo" numerado'))
        elif NUM.search(w['w']) or n in ('dois', 'duas', 'tres', 'quatro', 'cinco', 'dez', 'cem', 'mil', 'metade', 'dobro'):
            sug.append(('numero', w, 'número dito → motion "numero" (contador) — só com fonte/claim do cliente'))
        elif n in CTA and w['s'] > DUR * 0.6: sug.append(('cta', w, 'chamada para ação → motion "cta" no fim'))
    # janelas de B-roll: fins de frase a cada cada_s
    alvo = BR['cada_s'][0]; ult = 1.5
    frases = []; cur = []
    for w in ws:
        cur.append(w)
        if re.search(r'[.!?,]$', w['w']): frases.append(cur); cur = []
    if cur: frases.append(cur)
    for f in frases:
        if f[0]['s'] - ult >= alvo and f[-1]['e'] - f[0]['s'] >= 1.2:
            txt = ' '.join(x['w'] for x in f)
            sug.append(('broll', f[0], f'B-roll cobrindo "{txt[:60]}" ({f[-1]["e"] - f[0]["s"]:.1f}s) — o que a frase MOSTRA?')); ult = f[-1]['e']
    sug.sort(key=lambda z: z[1]['s'])
    L = [f'# Rascunho do mapa — estilo {ESTILO} · {DUR:.1f}s', '',
         f"Densidade do estilo: motion {MO['por_minuto'][0]}–{MO['por_minuto'][1]}/min (≈ {MO['por_minuto'][0] * DUR / 60:.0f}–{MO['por_minuto'][1] * DUR / 60:.0f} aqui) · B-roll a cada {BR['cada_s'][0]}–{BR['cada_s'][1]} s · rosto ≥ {MO['rosto_entre']} s entre cortes para fora.", '',
         'Encaixes sugeridos (decida o que entra; escreva _edit/mapa.json e rode `mapa.py .`):', '']
    for tipo, w, why in sug: L.append(f"- [{E.tc(w['s'])}] #{w['i']} «{w['w']}» → {tipo}: {why}")
    L += ['', 'Lembre: gancho visual nos 2 s iniciais (título/palavra/zoom), CTA no fim, nada de fonte/crédito na tela.']
    (P / 'docs/MAPA_RASCUNHO.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L)); sys.exit()

# ───────────────────────── validar ─────────────────────────
mapa = E.jload(P / '_edit/mapa.json') or E.die('escreva _edit/mapa.json (veja `mapa.py . rascunho` e references/motion-e-broll.md)')
itens = mapa.get('itens', []); err = []; warn = []
for it in itens:
    it.setdefault('modo', 'efeito' if it.get('tipo') == 'efeito' else 'sobreposto' if it.get('tipo') == 'motion' else 'tela_cheia')
    t0 = ancora(it.get('de'))
    if t0 is None: err.append(f"{it['id']}: falta 'de'"); continue
    t1 = ancora(it.get('ate'), fim=True) if it.get('ate') is not None else t0 + float(it.get('dur', 2.0))
    t0, t1 = snap(max(0, t0 - (0.04 if it['tipo'] != 'motion' else 0))), snap(min(DUR, t1))
    it['t_ini'], it['t_fim'] = round(t0, 3), round(t1, 3); d = t1 - t0
    if it.get('tipo') == 'motion' and (it.get('peca') in SYNC or (it.get('params') or {}).get('sync')):     # a peça escreve a FALA no tempo dela
        it.setdefault('params', {})['_palavras'] = [{'w': CORR.get(f"#{w['i']}", w['w']), 'i': w['i'], 't': round(w['s'] - t0, 3), 'e': round(w['e'] - t0, 3)}
                                                   for w in tl['palavras'] if t0 - 0.05 <= w['s'] < t1 - 0.05]
        if it.get('peca') == 'empilha' and it['params']['_palavras']:      # a última linha precisa de ≥ 0,8 s no ar antes de sair
            t1 = snap(min(DUR, max(t1, t0 + it['params']['_palavras'][-1]['e'] + 0.8))); it['t_fim'] = round(t1, 3); d = t1 - t0
    mn = 0.8 if it['tipo'] in ('motion', 'efeito') else 1.2
    if it['tipo'] == 'efeito' and it.get('efeito') == 'quebra' and d > 8: warn.append(f"{it['id']}: quebra de {d:.1f}s — acima de ~8 s deixa de ser quebra (vira o vídeo)")
    if d < mn: warn.append(f"{it['id']}: {d:.2f}s é curto (mín. {mn}s para ler/registrar)")
    if it['tipo'] in ('broll', 'foto') and d > 4.0: warn.append(f"{it['id']}: {d:.1f}s de B-roll — acima de 4 s a pessoa some; divida ou volte ao rosto")
    if it['tipo'] in ('broll', 'foto'):
        if it.get('arquivo') and not (P / it['arquivo']).exists(): err.append(f"{it['id']}: arquivo {it['arquivo']} não existe")
        if not it.get('arquivo'): it['status'] = 'buscar' if it.get('busca') else 'falta'
    if it['tipo'] in ('motion', 'texto'):
        pr = it.get('params', {}); ls = [x if isinstance(x, str) else (x or {}).get('txt', '') for x in pr.get('linhas', [])]
        txt = ' '.join(str(x) for x in [it.get('texto') or '', *(ls if it.get('peca') == 'etiqueta' else ls[1:]), pr.get('nome', ''), pr.get('cargo', ''), pr.get('rotulo', ''), pr.get('sub', ''),
                                        pr.get('antes', ''), pr.get('chave', ''), pr.get('depois', ''), pr.get('titulo', ''), *pr.get('textos', []), *[e if isinstance(e, str) else e.get('txt', '') for e in pr.get('etiquetas', [])]])
        nw = len(txt.split()); need = 0.5 + 0.3 * nw
        if nw and d < need: warn.append(f"{it['id']}: {nw} palavra(s) pedem {need:.1f}s no ar para ler; tem {d:.1f}s (estique 'ate' ou corte texto)")
    if it['tipo'] == 'motion':
        if it.get('peca', 'custom') == 'custom' and not it.get('projeto'): err.append(f"{it['id']}: peça custom precisa de 'projeto' (pasta motion-studio)")
        if re.search(r'\b(fonte|source|via|segundo o|dados de)\b', txt, re.I):      # só o TEXTO que vai para a tela (não as chaves dos params)
            warn.append(f"{it['id']}: parece citar FONTE na tela — regra Orbe: fontes ficam fora do vídeo (docs/CREDITOS.md), salvo pedido")
for it in itens:
    if it.get('pendente'): warn.append(f"{it['id']}: veio do plano ({it.get('_plano')}) e está PENDENTE — preencha {('params' if it['tipo'] == 'motion' else 'busca/arquivo')} e tire \"pendente\"")
fora = sorted([it for it in itens if it.get('t_ini') is not None and it['modo'] in ('tela_cheia', 'split', 'janela')], key=lambda x: x['t_ini'])
for a, b in zip(fora, fora[1:]):
    if b['t_ini'] < a['t_fim'] - 1e-3: err.append(f"{a['id']} e {b['id']} se sobrepõem em tela cheia")
    elif 0 < b['t_ini'] - a['t_fim'] < MO['rosto_entre']: warn.append(f"{a['id']}→{b['id']}: só {b['t_ini'] - a['t_fim']:.1f}s de rosto entre eles (estilo pede ≥ {MO['rosto_entre']}s) — ou emende os dois")
for it in itens:     # peça sobreposta atravessando a entrada/saída de um corte para fora: some/aparece no meio do B-roll
    if it.get('modo') != 'sobreposto' or it.get('t_ini') is None: continue
    for f in fora:
        for b in (f['t_ini'], f['t_fim']):
            if it['t_ini'] + 0.05 < b < it['t_fim'] - 0.05: warn.append(f"{it['id']} atravessa a {'entrada' if b == f['t_ini'] else 'saída'} de {f['id']} ({b:.2f}s) — termine antes ou comece depois (ou ponha a peça dentro do item)")
nmo = sum((1 / max(1, it.get('params', {}).get('total', 1))) if it.get('peca') == 'lista' else 1 for it in itens if it['tipo'] == 'motion'); pm = nmo / max(DUR / 60, 0.25)   # uma série de lista conta como 1
lo, hi = MO['por_minuto']
if DUR >= 20 and not (lo * 0.7 <= pm <= hi * 1.3): warn.append(f"{nmo:.0f} motion em {DUR:.0f}s = {pm:.1f}/min; estilo {ESTILO} pede {lo}–{hi}/min")
if not any(it.get('t_ini', 99) < 2.0 for it in itens) and not mapa.get('gancho_sem_item'):
    warn.append('nada nos 2 s iniciais: gancho visual (título, palavra-chave grande, zoom) segura a retenção — ou marque "gancho_sem_item": true')
if B.get('cta') and not any(it.get('peca') == 'cta' for it in itens): warn.append('briefing tem CTA mas o mapa não tem peça "cta"')
cob = sum(it['t_fim'] - it['t_ini'] for it in fora)
if DUR and cob / DUR > 0.55: warn.append(f"{100 * cob / DUR:.0f}% do vídeo fora do rosto — talking head perde a pessoa; alvo ≤ 45%")
E.jsave(P / '_edit/mapa.json', mapa)
L = [f'# Mapa de motion e B-roll — {len(itens)} itens · {DUR:.1f}s · estilo {ESTILO}', '',
     '| id | tipo | quando | dur | modo | o quê | status |', '|---|---|---|---|---|---|---|']
for it in sorted(itens, key=lambda x: x.get('t_ini', 0)):
    pr = it.get('params', {}); ls = [x if isinstance(x, str) else (x or {}).get('txt', '') for x in pr.get('linhas', [])]
    oq = it.get('peca', '') + (': ' if it.get('peca') else '') + (it.get('texto') or pr.get('nome') or pr.get('palavra') or pr.get('chave') or ' / '.join(ls) or ' / '.join(pr.get('itens', [])) or ' / '.join(pr.get('textos', [])) or pr.get('titulo') or pr.get('rotulo') or it.get('busca') or it.get('arquivo') or it.get('descricao') or '')
    L.append(f"| {it['id']} | {it['tipo']} | {E.tc(it.get('t_ini', 0))} | {it.get('t_fim', 0) - it.get('t_ini', 0):.1f}s | {it['modo']} | {oq[:70]} | {it.get('status', 'ok')} |")
if mapa.get('enfase_palavras'): L += ['', 'Ênfase (punch-in + legenda em destaque): ' + ', '.join(f"#{i} «{PAL[i]['w']}»" for i in mapa['enfase_palavras'] if i in PAL)]
L += ['', *(f'- ✗ {e}' for e in err), *(f'- ⚠ {w}' for w in warn)]
(P / 'docs/MAPA.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L))
if err: sys.exit(1)
E.log_estado(P, 'mapa', 'feito', f'{len(itens)} itens, {len(warn)} avisos')
