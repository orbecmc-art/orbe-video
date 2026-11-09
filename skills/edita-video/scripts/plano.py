#!/usr/bin/env python3
"""plano.py — o PLANO DE CENAS antes de animar (portão ②): cada linha do roteiro com o tipo de cena e o design.

O passo que mais muda o resultado (Joseph/Ultimate Editors, 2026): a IA constrói bem, mas o plano bom vem do gosto de
quem edita. A página mostra o roteiro já cortado, linha a linha, com a sugestão do Claude; a pessoa escolhe:
    Legenda (só rosto + legenda) · Legenda + UI (animação pequena na metade de baixo, fundo escurece) ·
    Meia tela (animação/B-roll em cima, rosto embaixo) · Tela cheia (a cena toma a tela)
e o design de cada uma (gráfico, linha, aspas, pintura com texto, B-roll, capítulos…), mais uma nota livre.

    python3 plano.py <projeto>                 # página entregas/plano/index.html (+ proxy.mp4 do corte, se houver)
    python3 plano.py <projeto> ler [arquivo]   # _edit/plano.json (do banco da página) → docs/PLANO.md por linha
    python3 plano.py <projeto> aplicar         # escolhas → _edit/mapa.json (itens novos "pendente": o Claude preenche)

Publicar (Claude): Artifact file_path=index.html, files={"proxy.mp4": …}, capabilities={"db": {}, "user": {"scopes":
["profile"]}}, icon "video". Ler: ArtifactData list collection "plano" → salve em _edit/plano.json. Sem página (pessoa
com pressa): o botão "Copiar plano" dá o texto para colar no chat — mesmo formato.
Regras de plano (references/estilo-minimal.md): abre no rosto (conexão); ANUNCIA item novo → rosto; DESCREVE → mostra;
uma tela cheia nunca colada na outra (≥ 2 s de rosto); série (1/2/3) = mesma UI; fecha em aspas ou CTA.
"""
import sys, os, re, json, html
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') and A[0] not in ('ler', 'aplicar') else None)
cmd = next((a for a in A if a in ('ler', 'aplicar')), 'pagina')
B, EST, ESTILO = E.config(P)
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes')
mapa = E.jload(P / '_edit/mapa.json', {}) or {'itens': []}
PAL = tl['palavras']; FPS = tl['fps']; DUR = tl['duracao']

# ── linhas do roteiro (sequência já cortada): quebra em pontuação forte, pausa > 0,45 s ou 14 palavras ──
linhas = []; cur = []
for k, w in enumerate(PAL):
    cur.append(w)
    nxt = PAL[k + 1] if k + 1 < len(PAL) else None
    if nxt is None or re.search(r'[.!?…]$', w['w']) or nxt['s'] - w['e'] > 0.45 or len(cur) >= 14:
        linhas.append(cur); cur = []
LIN = [{'id': f'P{n + 1:02d}', 'i0': c[0]['i'], 'i1': c[-1]['i'], 'a': round(c[0]['s'], 3), 'b': round(c[-1]['e'], 3),
        'txt': ' '.join(x['w'] for x in c)} for n, c in enumerate(linhas)]

CENAS = {'legenda': 'Legenda', 'legenda_ui': 'Legenda + UI', 'meia_tela': 'Meia tela', 'tela_cheia': 'Tela cheia'}
DESIGNS = {
    'legenda': [('rosto', 'Só o rosto e a legenda — conexão com quem fala')],
    'legenda_ui': [('capitulos', 'Capítulos: círculos 1·2·3 que preenchem'), ('numero', 'Número que conta e assenta'),
                   ('callout', 'Ponto + linha + rótulo num detalhe'), ('check', 'Itens com ✓ / ✗'), ('lista', 'Selo numerado'),
                   ('lower_third', 'Nome e cargo'), ('palavra', 'Uma palavra grande'), ('rotulo', 'Rótulo: sans + manuscrita no espaço livre'),
                   ('empilha', 'Gancho gigante que se empilha'), ('doc', 'Card de documento (prova)'), ('custom', 'UI própria (descreva na nota)')],
    'meia_tela': [('broll', 'Vídeo de apoio em cima'), ('foto', 'Foto em cima'), ('grafico', 'Gráfico com bola e grade'),
                  ('linha', 'Linha que leva às palavras'), ('custom', 'Animação própria (descreva)')],
    'tela_cheia': [('aspas', 'Só texto, com aspas, em papel'), ('pintura', 'Pintura/foto com papel + texto em volta'),
                   ('broll_texto', 'B-roll com papel + texto por cima'), ('broll', 'B-roll limpo'), ('grafico', 'Gráfico (sobe, degraus, plano, cai)'),
                   ('linha', 'Linha + palavras (câmera segue)'), ('texto', 'Cartela de texto'), ('cartela', 'Respiro: tela lisa com a fala escrita'), ('cta', 'Chamada final'), ('custom', 'Cena própria (descreva)')],
}

def cena_de(it):
    m = it.get('modo', 'sobreposto')
    return 'tela_cheia' if m == 'tela_cheia' else 'meia_tela' if m == 'split' else 'legenda_ui'
def design_de(it):
    if it.get('tipo') in ('broll',): return 'broll'
    if it.get('tipo') == 'foto': return 'pintura' if it.get('modo') == 'tela_cheia' else 'foto'
    return it.get('peca') or 'custom'

def sugestao(L):
    """o que o mapa atual (proposta do Claude) faz nesta linha."""
    its = [it for it in mapa.get('itens', []) if it.get('t_ini') is not None and it['t_ini'] < L['b'] - 0.05 and it['t_fim'] > L['a'] + 0.05]
    if not its: return {'cena': 'legenda', 'design': 'rosto', 'itens': []}
    fora = [it for it in its if it.get('modo') in ('tela_cheia', 'split')]
    it = fora[0] if fora else its[0]
    d = design_de(it)
    if d == 'broll' and any(x.get('peca') == 'frase' for x in its): d = 'broll_texto'
    return {'cena': cena_de(it), 'design': d, 'itens': [x['id'] for x in its]}

# ════════════════════════════ página ════════════════════════════
if cmd == 'pagina':
    nome = B.get('nome') or re.sub(r'[^a-z0-9-]+', '-', P.name.lower()).strip('-') or 'video'
    OUT = P / 'entregas' / 'plano'; OUT.mkdir(parents=True, exist_ok=True)
    rend = sorted((P / 'renders').glob('*.mp4'), key=lambda f: f.stat().st_mtime)
    tem_video = False
    if rend:
        kbps = max(600, min(2600, int(12 * 8 * 1000 / max(DUR, 1)) - 160))
        r = E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(rend[-1]), '-vf', 'scale=720:-2', '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{kbps}k',
                   '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(OUT / 'proxy.mp4')], check=False)
        tem_video = (OUT / 'proxy.mp4').exists()
    mk = dict(EST.get('marca_padrao', {})); mk.update(B.get('marca') or {})
    dados = {'nome': nome, 'estilo': ESTILO, 'dur': round(DUR, 2), 'fps': FPS, 'video': tem_video,
             'linhas': [{**L, 'sug': sugestao(L)} for L in LIN], 'cenas': CENAS, 'designs': DESIGNS,
             'marca': {'accent': mk.get('accent') or EST['legendas'].get('destaque', '#6E8FC6'), 'fonte': EST['legendas'].get('fonte', 'Inter'),
                       'fonte2': EST['legendas'].get('fonte2') or mk.get('display') or ''}}
    TPL = (E.SKILL / 'assets/plano.html').read_text(encoding='utf-8')
    out = TPL.replace('__NOME__', html.escape(nome)).replace('__DADOS__', json.dumps(dados, ensure_ascii=False).replace('</', '<\\/'))
    (OUT / 'index.html').write_text(out, encoding='utf-8')
    print(f"✔ {OUT.relative_to(P)}/index.html · {len(LIN)} linhas do roteiro" + (' + proxy.mp4' if tem_video else ' (sem vídeo: rode um rascunho para a página tocar o corte)'))
    print('→ publique: Artifact file_path=index.html' + (', files={"proxy.mp4": "<pasta>/proxy.mp4"}' if tem_video else '') + ', capabilities={"db": {}, "user": {"scopes": ["profile"]}}, icon="video"')
    print('→ a pessoa escolhe cena + design por linha e aperta "Salvar"/"Aprovar"; leia (ArtifactData list "plano") → _edit/plano.json → plano.py . ler')
    sys.exit()

# ════════════════════════════ ler / aplicar ════════════════════════════
src = next((a for a in A[1:] if a not in ('ler', 'aplicar') and not a.startswith('--')), None)
raw = E.jload(P / (src or '_edit/plano.json'), None)
if raw is None: E.die('salve as escolhas da página em _edit/plano.json (ArtifactData list "plano") ou cole o plano copiado')
docs = raw if isinstance(raw, list) else raw.get('docs', raw.get('linhas', []))
esc = {d.get('linha') or d.get('id'): d for d in docs if isinstance(d, dict)}
cfg = esc.pop('config', None) or {}; status = esc.pop('status', None) or {}
if cfg:
    aj = {}
    if cfg.get('accent'): B.setdefault('marca', {})['accent'] = cfg['accent']; aj.setdefault('legendas', {})['destaque'] = cfg['accent']
    if cfg.get('fonte'): aj.setdefault('legendas', {})['fonte'] = cfg['fonte']
    if cfg.get('fonte2') is not None: aj.setdefault('legendas', {})['fonte2'] = cfg['fonte2'] or None; B.setdefault('marca', {})['display'] = cfg['fonte2'] or B.get('marca', {}).get('display')
    for k, v in aj.items(): B.setdefault('ajustes', {}).setdefault(k, {}).update(v)
    E.jsave(P / '_edit/briefing.json', B)
D = [f'# Plano de cenas — {len(LIN)} linhas · {"APROVADO" if status.get("aprovado") else "rascunho"}', '',
     '| linha | quando | fala | cena | design | nota |', '|---|---|---|---|---|---|']
for L in LIN:
    c = esc.get(L['id']) or {}; s = sugestao(L)
    cena = c.get('cena') or s['cena']; dz = c.get('design') or s['design']
    D.append(f"| {L['id']} #{L['i0']}–#{L['i1']} | {E.tc(L['a'])} | {L['txt'][:70]} | {CENAS.get(cena, cena)} | {dz} | {(c.get('nota') or '').replace('|', '/')[:90]} |")
if cfg: D += ['', f"Marca escolhida: acento {cfg.get('accent')} · fonte {cfg.get('fonte')} · destaque {cfg.get('fonte2') or '—'} (gravado no briefing)"]
(P / 'docs/PLANO.md').write_text('\n'.join(D) + '\n', encoding='utf-8')
print('\n'.join(D))
if cmd == 'ler':
    print('\n→ leia as notas, ajuste o mapa à mão ou rode `plano.py . aplicar` (gera os itens que faltam como "pendente")'); sys.exit()

# aplicar: legenda → tira itens da linha; outras → garante um item com a cena/design pedidos (stub "pendente")
itens = mapa.setdefault('itens', [])
def nid(pref):
    k = 1
    while any(it['id'] == f'{pref}{k:02d}' for it in itens): k += 1
    return f'{pref}{k:02d}'
def na_linha(it, L):
    m = re.match(r'#(\d+)', str(it.get('de', '')))
    if m: return L['i0'] <= int(m.group(1)) <= L['i1']
    return it.get('t_ini') is not None and L['a'] - 0.05 <= it['t_ini'] < L['b']
feitos = []
for L in LIN:
    c = esc.get(L['id'])
    if not c: continue
    cena, dz, nota = c.get('cena'), c.get('design'), (c.get('nota') or '').strip()
    atuais = [it for it in itens if na_linha(it, L)]
    if cena == 'legenda':
        for it in atuais:
            if not it.get('manter'): itens.remove(it); feitos.append(f"{L['id']}: tirei {it['id']} (fica só a legenda)")
        continue
    alvo_modo = {'legenda_ui': 'sobreposto', 'meia_tela': 'split', 'tela_cheia': 'tela_cheia'}[cena]
    ok = [it for it in atuais if it.get('modo', 'sobreposto') == alvo_modo and design_de(it) in (dz, 'broll' if dz == 'broll_texto' else dz)]
    if ok: feitos.append(f"{L['id']}: {ok[0]['id']} já é {CENAS[cena]} / {dz}"); continue
    for it in atuais:
        if not it.get('manter'): itens.remove(it)
    base = {'de': f"#{L['i0']}", 'ate': f"#{L['i1']}", '_plano': L['id'], 'pendente': True, 'nota_plano': nota}
    fala = L['txt']
    if dz in ('broll', 'foto', 'pintura', 'broll_texto'):
        tipo = 'foto' if dz in ('foto', 'pintura') else 'broll'
        novo = {**base, 'id': nid('ft' if tipo == 'foto' else 'br'), 'tipo': tipo, 'modo': alvo_modo, 'busca': nota or fala, 'descricao': f'{dz}: {fala}'}
        if dz in ('pintura', 'broll_texto'): novo.update({'tratamento': 'papel', 'transicao': 'deslize'})
        if dz == 'pintura': novo['busca'] = nota or f'public domain painting — {fala}'
        itens.append(novo); feitos.append(f"{L['id']}: {novo['id']} {tipo} {alvo_modo} (pendente: escolher {('a pintura' if dz == 'pintura' else 'o vídeo')})")
        if dz in ('pintura', 'broll_texto'):
            fr = {**base, 'id': nid('mo'), 'tipo': 'motion', 'peca': 'frase', 'modo': 'sobreposto', 'posicao': 'centro', 'params': {}, 'texto': fala}
            itens.append(fr); feitos.append(f"{L['id']}: {fr['id']} frase por cima (pendente: antes/chave/depois)")
        continue
    peca = 'texto' if dz == 'custom' and cena == 'tela_cheia' else dz
    novo = {**base, 'id': nid('mo'), 'tipo': 'motion', 'peca': 'custom' if dz == 'custom' else peca, 'modo': alvo_modo, 'texto': fala, 'params': {}}
    if cena == 'legenda_ui': novo.update({'posicao': 'meio-baixo', 'fundo': 'escurece'})
    itens.append(novo); feitos.append(f"{L['id']}: {novo['id']} {novo['peca']} {alvo_modo} (pendente: params)")
itens.sort(key=lambda it: int(re.match(r'#(\d+)', str(it.get('de', '#0'))).group(1)) if re.match(r'#(\d+)', str(it.get('de', ''))) else 0)
E.jsave(P / '_edit/mapa.json', mapa)
print('\n' + '\n'.join(f'- {f}' for f in feitos))
print('→ preencha os itens "pendente" (params / busca), tire a marca e rode `mapa.py .`')
E.log_estado(P, 'plano', 'feito', f'{len(esc)} linhas escolhidas')
