#!/usr/bin/env python3
"""legendas.py — legendas queimadas (ASS/libass) a partir das palavras da timeline, no estilo do briefing.

    python3 legendas.py <projeto> [--corrigir "#12=Rafael" "bril=brilho" …] [--sem] [--y 0.62]

Regras (references/legendas.md):
  · Blocos de `palavras` (2–4) e ≤ max_car caracteres; quebra em pausa > 0,35 s, pontuação forte, vírgula e corte.
    Nunca termina bloco em palavra funcional ("de", "o", "que", "pra"…) — ela desce para o próximo bloco.
    "Dr./Dra./Sr." e número + unidade ("30 dias", "R$ 99") ficam juntos.
  · Entra 2 quadros ANTES da voz (o olho lê antes do ouvido) e fica até o próximo bloco (sem piscar em pausa < 0,6 s).
  · Palavra ativa no `destaque` (cor) sem mudar de tamanho (layout estável); palavra de ÊNFASE (mapa/camera) em
    destaque o bloco inteiro, 8% maior. Caixa alta tira vírgula/ponto final; mantém ? e !.
  · Posição: centro em y (fração da altura), fora da zona da interface do Reels (y ≤ 0,72 no 9:16). Se um item do mapa
    ocupa a faixa da legenda, ela sobe para cima dele; em tela cheia com texto próprio, some (dois textos brigam).
  · Correções de transcrição NÃO mexem em tempo: _edit/correcoes.json {"#12": "Rafael", "bril": "brilho"}.
  · layout "cinema" (estilo minimal premium): bloco de até 5 palavras; a(s) palavra(s)-chave (número, ênfase, termo
    do briefing, palavra longa/alongada) ficam GRANDES no centro em serifa itálica (fonte2) ou sans pesada (números);
    as demais, pequenas, nos vãos acima/abaixo. Cada palavra aparece quando é dita (fade + leve subida), halo escuro
    suave em vez de contorno. Uma cor de acento só, e só na ênfase.
  · animacao "monta" (podcast P&B): a frase se MONTA — cada palavra aparece quando é dita e fica até o bloco acabar;
    chave_serifa: a palavra-chave em serifa itálica (fonte2) 18% maior; halo: borda suave desfocada no lugar do contorno.
  · animacao "blur" (Joseph): o bloco entra com pop + desfoque + fade de baixa opacidade.
  · chave_caixa (dinâmico/varejo, Style Studio): no máximo UMA palavra-chave por bloco (número, ênfase, termo, palavra
    longa) numa caixa na cor de destaque, inclinada chave_inclina° (−2,5), texto em chave_tinta; a caixa salta quando a
    palavra é dita. Blocos sem palavra forte ficam sem caixa (nem toda linha precisa).
  · layout "micro" (lifestyle, R1): UMA palavra por vez, pequena, em serifa, sem caixa nem destaque — o vídeo respira;
    "30 dias"/"Dr. Rafael" ficam juntos. Fica no peito (y), desvia das peças.
  · layout "escada" (entrevista, R2): grotesca de tracking negativo, cada palavra entra com fade; a palavra-chave do
    bloco fica GRANDE e o resto do bloco PEQUENO, deslocado (embaixo à direita se vem depois, em cima à esquerda se
    vem antes) — hierarquia tipográfica sem cor. Durante uma cartela (peça "cartela") a própria peça escreve a fala.
Saídas: _edit/legendas.ass · _edit/legendas.json (L001… com palavras) · docs/LEGENDAS.md (para revisar por número)
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P); LG = dict(EST['legendas'])
if opt('y'): LG['y'] = float(opt('y'))
W, H = E.formato(B); S = min(W, H)
_slug = lambda f: f.lower().replace(' ', '-')
if not list((P / 'fonts').glob(_slug(LG['fonte']) + '-*.ttf')) and not list((P / 'fonts').glob('*.otf')) or (LG.get('fonte2') and not list((P / 'fonts').glob(_slug(LG['fonte2']) + '-*.ttf'))):
    import subprocess; subprocess.run([sys.executable, str(E.SKILL / 'scripts/fontes.py'), str(P)])      # legenda precisa de TTF/OTF (libass não lê woff2)
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes'); FPS = tl['fps']

# ── correções (persistentes) ──
corr = E.jload(P / '_edit/correcoes.json', {}) or {}
if '--corrigir' in A:
    for x in A[A.index('--corrigir') + 1:]:
        if x.startswith('--'): break
        k, _, v = x.partition('='); corr[k.strip()] = v.strip()
    E.jsave(P / '_edit/correcoes.json', corr)
if '--sem' in A or not LG.get('ativo', True):
    (P / '_edit/legendas.ass').unlink(missing_ok=True); E.jsave(P / '_edit/legendas.json', {'blocos': []})
    print('legendas desligadas'); E.log_estado(P, 'legendas', 'feito', 'sem legenda'); sys.exit()

def texto(w):
    t = corr.get(f"#{w['i']}")
    if t is None:
        nk = E.norm(w['w']); t = w['w']
        for k, v in corr.items():
            if not k.startswith('#') and E.norm(k) == nk:
                t = re.sub(re.escape(re.sub(r'[^\wÀ-ÿ]', '', w['w'])), v, w['w']) if re.sub(r'[^\wÀ-ÿ]', '', w['w']) else v
    return t
pal = [dict(w, t=texto(w)) for w in tl['palavras'] if texto(w).strip()]

# ênfase: pedida no mapa + punch-ins da câmera
mapa = E.jload(P / '_edit/mapa.json', {}) or {}
cam = E.jload(P / '_edit/camera.json', {}) or {}
ENF = {int(i) for i in mapa.get('enfase_palavras', [])} | ({p['i'] for p in cam.get('punch', [])} if EST['camera'].get('punch_modo', 'enfase') != 'linha' else set())   # punch por linha cai no começo da linha: não é ênfase

# ── blocos ──
ABREV = {'dr', 'dra', 'sr', 'sra', 'prof', 'profa', 'r$', 'nº', 'n°'}
UNID = {'dias', 'dia', 'anos', 'ano', 'meses', 'mês', 'horas', 'hora', 'minutos', 'reais', 'mil', 'milhões', 'por', '%', 'x', 'kg', 'ml', 'mg', 'cm', 'semanas', 'sessões', 'vezes'}
NMAX, CMAX = int(LG['palavras']), int(LG['max_car'])
# Quebra ótima por programação dinâmica: cada bloco cabe em max_car e em `palavras` palavras de CONTEÚDO (funcionais
# não contam); custo baixo para quebrar em pontuação/pausa, alto para terminar em palavra funcional, separar
# "Dr. Rafael"/"30 dias", juntar duas frases ou deixar bloco-relâmpago (< 6 caracteres ou < 0,45 s).
NUMS = set('um uma dois duas tres quatro cinco seis sete oito nove dez onze doze quinze vinte trinta quarenta cinquenta cem cento duzentos mil'.split())
def forte(t): return bool(re.search(r'[.!?:;…]$', t)) and E.norm(t) not in ABREV
def cola(a, b): return E.norm(a['t']) in ABREV or ((bool(re.search(r'\d', a['t'])) or E.norm(a['t']) in NUMS) and E.norm(b['t']) in UNID)
def conta(x): k = E.norm(x['t']); return k not in E.FUNC and k not in ABREV and len(k) > 2
_zonas = [(it['t_ini'], it['t_fim']) for it in mapa.get('itens', []) if it.get('t_ini') is not None and (it.get('modo') in ('tela_cheia', 'split') or it.get('esconde_legenda'))]
def zona(t): return next((k for k, (a, b) in enumerate(_zonas) if a - 0.04 <= t < b), -1)
corridas = []; cur = []
for w in pal:      # quebras obrigatórias: corte de cena, pausa longa e entrada/saída de tela cheia/split (a legenda muda de lugar)
    if cur and (w['seg'] != cur[-1]['seg'] or w['s'] - cur[-1]['e'] > 0.6 or zona(w['s']) != zona(cur[-1]['s'])): corridas.append(cur); cur = []
    cur.append(w)
if cur: corridas.append(cur)
blocos = []
for R in corridas:
    n = len(R); best = [0.0] + [1e9] * n; prev = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(max(0, i - 3 * NMAX), i):
            b = R[j:i]; ch = len(' '.join(x['t'] for x in b)); cont = sum(1 for x in b if conta(x))
            if (ch > CMAX or cont > NMAX) and i - j > 1: continue
            c = 0.8
            if i < n:
                a, z = R[i - 1], R[i]; gap = z['s'] - a['e']
                c += 0 if forte(a['t']) else 0.2 if a['t'].endswith(',') else 0.3 if gap > 0.25 else 6 if E.norm(a['t']) in E.FUNC else 8 if cola(a, z) else 1.0
            c += sum(4 if forte(x['t']) else 0.7 if x['t'].endswith(',') else 0 for x in b[:-1])
            c += 1.5 if ch < 6 else 0; c += 1.0 if b[-1]['e'] - b[0]['s'] < 0.45 else 0
            if best[j] + c < best[i]: best[i] = best[j] + c; prev[i] = j
    i = n; parts = []
    while i > 0: parts.append(R[prev[i]:i]); i = prev[i]
    blocos += parts[::-1]

MICRO = LG.get('layout') == 'micro'
if MICRO:      # uma palavra por vez; junta "30 dias", "Dr. Rafael", palavra funcional e fala rápida (< 0,3 s) — nunca atrasa
    blocos = []
    for R in corridas:
        i = 0
        while i < len(R):
            b = [R[i]]; i += 1
            while (i < len(R) and len(b) < 3 and len(' '.join(x['t'] for x in b + [R[i]])) <= 16
                   and (R[i]['s'] - b[0]['s'] < 0.30 or cola(b[-1], R[i]) or E.norm(b[-1]['t']) in ABREV or E.norm(b[-1]['t']) in E.FUNC)):
                b.append(R[i]); i += 1
            blocos.append(b)

# ── zonas do mapa: esconder / subir ──
def faixa(it):
    if it.get('caixa'): return it['caixa']
    return {'baixo': [0.70, 0.90], 'topo': [0.08, 0.28], 'centro': [0.36, 0.64], 'meio-baixo': [0.55, 0.75], 'esquerda': [0.30, 0.70], 'direita': [0.30, 0.70]}.get(it.get('posicao', 'baixo'), [0.70, 0.90])
DIZ_A_FRASE = ('frase', 'aspas', 'texto', 'cta', 'linha', 'grafico', 'etiqueta', 'empilha', 'cartela')     # peças que já são o texto do trecho: legenda some
itens = [it for it in mapa.get('itens', []) if it.get('t_ini') is not None]
_ros = {}
def queixo(t0, t1):
    """altura do queixo (fração do quadro final) no trecho — rosto.py através da câmera; None sem dados."""
    qs = cam.get('quadros') or []; fps_ = cam.get('fps') or FPS; ys = []
    for n in range(int(t0 * fps_), max(int(t0 * fps_) + 1, int(t1 * fps_)), 4):
        if n >= len(qs): break
        q = qs[n]
        if q['clip'] not in _ros: _ros[q['clip']] = [a for a in (E.jload(P / f"_edit/rosto/{q['clip']}.json") or {}).get('amostras', []) if a[6] > 0]
        am = _ros[q['clip']]
        if not am: continue
        a = min(am, key=lambda x: abs(x[0] - q['ts']))
        if abs(a[0] - q['ts']) < 1.0: ys.append((a[2] + a[4] / 2 - (q['cy'] - q['ch'] / 2)) / q['ch'])
    return sorted(ys)[len(ys) // 2] if ys else None

def y_para(t0, t1):
    y = LG['y']; esconde = False
    if LG.get('desvia_rosto'):          # legenda nunca na boca/queixo: desce para o peito se o rosto está baixo no quadro
        qx = queixo(t0, t1); h2 = 0.05
        if qx is not None and y - h2 < qx + 0.015: y = round(min(0.73, qx + 0.015 + h2), 3)      # 0,73: acima da UI do Reels
    for it in itens:
        if it['t_fim'] <= t0 or it['t_ini'] >= t1: continue
        modo = it.get('modo', 'tela_cheia')
        if modo == 'tela_cheia' and it.get('esconde_legenda', it.get('tipo') in ('motion', 'texto')): esconde = True
        elif it.get('esconde_legenda', it.get('peca') in DIZ_A_FRASE): esconde = True   # peça que já diz a frase — dois textos brigam
        elif modo == 'split': y = 0.5
        elif modo == 'sobreposto':
            a, b = faixa(it); h2 = 0.085 if LG.get('layout') == 'cinema' else 0.06
            if not (y + h2 < a or y - h2 > b): y = a - h2 - 0.02 if a > 0.45 else b + h2 + 0.02
    return y, esconde

# ── ASS ──
def ass_cor(hx, a=0):
    hx = hx.lstrip('#'); r, g, b = hx[0:2], hx[2:4], hx[4:6]
    return f'&H{a:02X}{b}{g}{r}'.upper()
def tcs(t):
    t = max(0, t); cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
def limpa(t, alta):
    t = t.replace('{', '(').replace('}', ')')
    if alta:
        t = (t if E.norm(t) in ABREV else re.sub(r'[,.;:…]+$', '', t)).upper()
    else:
        t = t if E.norm(t) in ABREV else re.sub(r'[,;:.…]+$', '', t)     # legenda não termina em ponto; mantém ? e !
    return t
alta = LG.get('caixa', 'alta') == 'alta'
fs = LG['tamanho'] * S / 0.80          # libass: Fontsize ≈ altura da linha; em ≈ 0,8 × isso → tamanho = em / lado curto
ol, sh = LG.get('contorno', 0.0075) * S, LG.get('sombra', 0.003) * S
cor, dest = ass_cor(LG['cor']), ass_cor(LG['destaque'])
fundo = LG.get('fundo', 'nenhum')
bstyle = 3 if fundo == 'caixa' else 1
outc = ass_cor('#000000', 0x60) if fundo == 'caixa' else ass_cor('#000000', 0x00)
L = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 0', 'ScaledBorderAndShadow: yes', 'YCbCr Matrix: TV.709', '',
     '[V4+ Styles]', 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
     f"Style: Leg,{LG['fonte']},{fs:.1f},{cor},{dest},{outc},{ass_cor('#000000', 0x80)},0,{-1 if LG.get('italico') else 0},0,0,100,100,{-0.01 * fs:.1f},0,{bstyle},{(ol if bstyle == 1 else 0.25 * fs):.1f},{sh:.1f},5,{int(0.08 * W)},{int(0.08 * W)},0,1",
     '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
snap = lambda t: round(t * FPS) / FPS
lead = 2 / FPS
TERMOS = {E.norm(x) for x in re.split(r'[,;\s]+', str(B.get('termos', ''))) if len(E.norm(x)) > 2}

def chave(b):
    """índices (no bloco) da palavra-chave: número > ênfase > termo do briefing > palavra longa/alongada no fim."""
    sc = []
    for j, x in enumerate(b):
        k = E.norm(x['t'])
        v = -9 if ((k in E.FUNC or len(k) <= 2) and not re.search(r'\d', x['t'])) else 0.22 * len(k)      # "38", "45" são chave, não palavra curta
        if re.search(r'\d', x['t']) or k in NUMS: v += 4
        if x['i'] in ENF: v += 5
        if k in TERMOS: v += 2.5
        v += 0.6 if j == len(b) - 1 else 0
        v += min(1.0, 2 * (x['e'] - x['s']))
        sc.append(v)
    j = max(range(len(b)), key=lambda q: sc[q]); J = [j]
    if j + 1 < len(b) and cola(b[j], b[j + 1]): J.append(j + 1)
    elif j > 0 and cola(b[j - 1], b[j]): J.insert(0, j - 1)
    return J

def cinema(blocos):
    """legenda cinematográfica de dois tamanhos (references/legendas.md · estilo minimal)."""
    f1, f2 = LG['fonte'], LG.get('fonte2') or LG['fonte']
    fs = LG['tamanho'] * S / 0.80; fk = fs * float(LG.get('escala_chave', 1.9))
    halo = max(2.0, 0.0045 * S)
    hdr = L[:L.index('[V4+ Styles]') + 2]
    LL = hdr + [f"Style: Peq,{f1},{fs:.1f},{ass_cor(LG['cor'], 0x18)},{dest},{ass_cor('#000000', 0x88)},{ass_cor('#000000', 0xFF)},0,0,0,0,100,100,{0.01 * fs:.1f},0,1,{halo:.1f},0,5,{int(0.07 * W)},{int(0.07 * W)},0,1",
                f"Style: Chave,{f2},{fk:.1f},{cor},{dest},{ass_cor('#000000', 0x80)},{ass_cor('#000000', 0xFF)},0,-1,0,0,100,100,{-0.005 * fk:.1f},0,1,{halo * 1.4:.1f},0,5,{int(0.06 * W)},{int(0.06 * W)},0,1",
                '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    RV = []; prev_end = 0; blur = max(1.5, 0.004 * S)
    for bi, b in enumerate(blocos):
        t0 = snap(max(prev_end, b[0]['s'] - lead))
        nxt = blocos[bi + 1][0]['s'] - lead if bi + 1 < len(blocos) else None
        t1 = snap(nxt) if nxt is not None and nxt - b[-1]['e'] < 0.6 else snap(b[-1]['e'] + 0.3)
        t1 = max(t1, t0 + 0.45); prev_end = t1
        y, esconde = y_para(t0, t1)
        lid = f'L{bi + 1:03d}'; J = chave(b)
        RV.append({'id': lid, 't0': round(t0, 3), 't1': round(t1, 3), 'texto': ' '.join(limpa(x['t'], False) for x in b), 'palavras': [x['i'] for x in b],
                   'chave': [b[j]['i'] for j in J], 'y': y, 'oculta': esconde})
        if esconde: continue
        pre, key, pos = b[:J[0]], b[J[0]:J[-1] + 1], b[J[-1] + 1:]
        num = any(re.search(r'\d', x['t']) or E.norm(x['t']) in NUMS for x in key)
        enf = any(x['i'] in ENF for x in key)
        def palavras(ws, on='00'):
            out = []
            for x in ws:
                a = int(max(0, (x['s'] - lead - t0)) * 1000)
                tx = limpa(x['t'], False)
                if a < 40: out.append(f"{{\\alpha&H{on}&}}{tx}")
                else: out.append(f"{{\\alpha&HFF&\\t({a},{a + 160},\\alpha&H{on}&)}}{tx}")
            return ' '.join(out)
        yk = int(y * H); up = int(0.46 * fk + 0.50 * fs + 0.10 * fs); dn = int(0.42 * fk + 0.56 * fs + 0.10 * fs)
        ka = int(max(0, (key[0]['s'] - lead - t0)) * 1000)
        kfont = f"\\fn{f1}\\b{LG.get('peso_chave', 800)}\\i0" if num else f"\\b{LG.get('peso_chave2', 700)}\\i1"
        kcol = f"\\c{dest}" if (enf and LG.get('enfase_cor', True)) else ''
        mv = f"\\move({W // 2},{yk + int(0.012 * H)},{W // 2},{yk},{ka},{ka + 220})"
        LL.append(f"Dialogue: 1,{tcs(t0)},{tcs(t1)},Chave,,0,0,0,,{{\\an5{mv}\\blur{blur:.1f}{kfont}{kcol}}}{palavras(key)}")
        if pre: LL.append(f"Dialogue: 0,{tcs(t0)},{tcs(t1)},Peq,,0,0,0,,{{\\an5\\pos({W // 2},{yk - up})\\blur{blur:.1f}\\b{LG.get('peso', 500)}}}{palavras(pre, '22')}")
        if pos: LL.append(f"Dialogue: 0,{tcs(t0)},{tcs(t1)},Peq,,0,0,0,,{{\\an5\\pos({W // 2},{yk + dn})\\blur{blur:.1f}\\b{LG.get('peso', 500)}}}{palavras(pos, '22')}")
    return LL, RV

# ── caixa da palavra-chave (Style Studio): mede as palavras com a fonte real para pôr a caixa embaixo da certa ──
_pil = {}
def _fonte_pil(peso, em):
    try:
        from PIL import ImageFont
        cands = sorted((P / 'fonts').glob(_slug(LG['fonte']) + '-*.ttf'))
        if not cands: return None
        alvo = min(cands, key=lambda f: abs(int(re.sub(r'\D', '', f.stem.split('-')[-1]) or 400) - int(peso)))
        k = (str(alvo), int(em))
        if k not in _pil: _pil[k] = ImageFont.truetype(str(alvo), max(8, int(em)))
        return _pil[k]
    except Exception: return None
def _larg(font, t): return font.getlength(t) if font else len(t) * 0.6 * fs * 0.8
_ult_caixa = [-9.0]
def chave_forte(b):
    """UMA palavra-chave forte por bloco (número, ênfase, termo, palavra longa) e no máx. 1 caixa a cada 2 s."""
    if len(b) < 2 or b[0]['s'] - _ult_caixa[0] < 2.0: return []
    cand = []
    for j, x in enumerate(b):
        k = E.norm(x['t']); dig = bool(re.search(r'\d', x['t']))
        sc = 4 if dig or k in NUMS else 3 if x['i'] in ENF else 2.5 if k in TERMOS else 1 if len(k) >= 8 else 0
        if sc: cand.append((sc, len(k), j))
    if not cand: return []
    j = max(cand)[2]; _ult_caixa[0] = b[0]['s']
    return [j]
def _em_px():
    """libass: Fontsize = usWinAscent + usWinDescent da fonte (OS/2), não o em — converte para o em em px (medido:
    Montserrat 99,9 → em 64). Sem fontTools, usa 0,64."""
    try:
        from fontTools.ttLib import TTFont
        cands = sorted((P / 'fonts').glob(_slug(LG['fonte']) + '-*.ttf'))
        f = TTFont(str(cands[0])); o = f['OS/2']
        return fs * f['head'].unitsPerEm / max(1, o.usWinAscent + o.usWinDescent)
    except Exception: return fs * 0.64
def caixa_chave(b, t0, t1, y, J):
    em = _em_px(); font = _fonte_pil(LG.get('peso', 800), em)
    txs = [limpa(x['t'], alta) for x in b]; sp = _larg(font, ' ') + (-0.01 * fs)
    ws_ = [_larg(font, t) for t in txs]; tot = sum(ws_) + sp * (len(b) - 1)
    x0 = W / 2 - tot / 2 + sum(ws_[:J[0]]) + sp * J[0]; wk = sum(ws_[J[0]:J[-1] + 1]) + sp * (len(J) - 1)
    padx, pady = 0.20 * em, 0.10 * em; bw, bh = wk + 2 * padx, em * 0.92 + 2 * pady
    cx, cy = x0 + wk / 2, y * H + 0.02 * em
    a = int(max(0, (b[J[0]]['s'] - lead - t0)) * 1000)
    acc = ass_cor(LG.get('chave_cor') or LG['destaque'])
    return (f"Dialogue: 0,{tcs(t0)},{tcs(t1)},Leg,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f})\\p1\\bord0\\shad0\\1c{acc}\\frz{-float(LG.get('chave_inclina', -2.5)):.1f}"
            f"\\fscx40\\fscy40\\alpha&HFF&\\t({a},{a + 90},\\alpha&H00&\\fscx108\\fscy108)\\t({a + 90},{a + 170},\\fscx100\\fscy100)}}"
            f"m 0 0 l {bw:.0f} 0 l {bw:.0f} {bh:.0f} l 0 {bh:.0f}{{\\p0}}")

def escada(blocos):
    """legenda em escada (R2): chave grande + resto pequeno deslocado; cada palavra entra com fade quando é dita."""
    em = _em_px(); peso = LG.get('peso', 500); kp = float(LG.get('escala_pequena', 0.6))
    fb = _fonte_pil(peso, em); fsm = _fonte_pil(peso, em * kp); spc = -0.01 * fs * float(LG.get('tracking', 2.5))
    halo = f"\\3c&H000000&\\bord{max(1.5, 0.004 * S):.1f}\\blur{max(2.0, 0.007 * S):.1f}\\shad0" if LG.get('halo') else ''
    def larg(f, tx, k=1.0): return _larg(f, tx) + spc * k * max(0, len(tx) - 1)
    def fades(ws, t0):
        out = []
        for x in ws:
            a = int(max(0, (x['s'] - lead - t0)) * 1000); tx = limpa(x['t'], alta)
            oa = '&H50&' if LG.get('halo') else '&H00&'
            out.append((f"{{\\1a&H00&\\3a{oa}}}" if a < 40 else f"{{\\1a&HFF&\\3a&HFF&\\t({a},{a + 180},\\1a&H00&\\3a{oa})}}") + tx)
        return ' '.join(out)
    LL = L[:L.index('[Events]') + 2]; RV = []; prev_end = 0      # cabeçalho + estilo Leg (sem os eventos do caminho padrão)
    for bi, b in enumerate(blocos):
        t0 = snap(max(prev_end, b[0]['s'] - lead))
        nxt = blocos[bi + 1][0]['s'] - lead if bi + 1 < len(blocos) else None
        t1 = snap(nxt) if nxt is not None and nxt - b[-1]['e'] < 0.6 else snap(b[-1]['e'] + 0.25)
        t1 = max(t1, t0 + 0.30); prev_end = t1
        y, esconde = y_para(t0, t1)
        RV.append({'id': f'L{bi + 1:03d}', 't0': round(t0, 3), 't1': round(t1, 3), 'texto': ' '.join(limpa(x['t'], alta) for x in b), 'palavras': [x['i'] for x in b], 'y': y, 'oculta': esconde})
        if esconde: continue
        J = chave(b) if len(b) > 1 else [0]
        if len(b) >= 3 and J[-1] < len(b) - 1: grande, peq, lado = b[:J[-1] + 1], b[J[-1] + 1:], 'depois'
        elif len(b) >= 3 and J[0] > 0: grande, peq, lado = b[J[0]:], b[:J[0]], 'antes'
        else: grande, peq, lado = b, [], ''
        yc = int(y * H); wg = larg(fb, ' '.join(limpa(x['t'], alta) for x in grande))
        LL.append(f"Dialogue: 1,{tcs(t0)},{tcs(t1)},Leg,,0,0,0,,{{\\an5\\pos({W // 2},{yc})\\b{peso}\\fsp{spc:.1f}{halo}}}{fades(grande, t0)}")
        if peq:
            fz = fs * kp; wp = larg(fsm, ' '.join(limpa(x['t'], alta) for x in peq), kp)
            if lado == 'depois':      # embaixo, alinhada pela direita da linha grande (sai para a direita se for maior)
                xr = W // 2 + wg / 2 + max(0, (wp - wg) * 0.5) + 0.04 * em
                LL.append(f"Dialogue: 1,{tcs(t0)},{tcs(t1)},Leg,,0,0,0,,{{\\an9\\pos({xr:.0f},{yc + int(0.40 * em)})\\fs{fz:.1f}\\b{peso}\\fsp{spc * kp:.1f}{halo}}}{fades(peq, t0)}")
            else:                     # em cima, alinhada pela esquerda
                xl = W // 2 - wg / 2 - max(0, (wp - wg) * 0.5) - 0.04 * em
                LL.append(f"Dialogue: 1,{tcs(t0)},{tcs(t1)},Leg,,0,0,0,,{{\\an1\\pos({xl:.0f},{yc - int(0.42 * em)})\\fs{fz:.1f}\\b{peso}\\fsp{spc * kp:.1f}{halo}}}{fades(peq, t0)}")
    return LL, RV

rev = []; prev_end = 0
for bi, b in enumerate(blocos):
    t0 = snap(max(prev_end, b[0]['s'] - lead))
    nxt = blocos[bi + 1][0]['s'] - lead if bi + 1 < len(blocos) else None
    t1 = snap(nxt) if nxt is not None and nxt - b[-1]['e'] < 0.6 else snap(b[-1]['e'] + 0.25)
    t1 = max(t1, t0 + (0.18 if MICRO else 0.30)); prev_end = t1
    y, esconde = y_para(t0, t1)
    lid = f'L{bi + 1:03d}'
    rev.append({'id': lid, 't0': round(t0, 3), 't1': round(t1, 3), 'texto': ' '.join(limpa(x['t'], alta) for x in b), 'palavras': [x['i'] for x in b], 'y': y, 'oculta': esconde})
    if esconde: continue
    if LG.get('animacao') == 'monta':      # a frase se monta palavra a palavra
        J = chave(b) if LG.get('chave_serifa') else []
        peso = LG.get('peso', 600); parts = []
        for j, x in enumerate(b):
            a = int(max(0, (x['s'] - lead - t0)) * 1000); tx = limpa(x['t'], alta)
            if j in J: tx = f"{{\\fn{LG.get('fonte2') or LG['fonte']}\\i1\\b0\\fscx118\\fscy118}}{tx}{{\\fn{LG['fonte']}\\i0\\b{peso}\\fscx100\\fscy100}}"
            on = '&H00&'; oa = '&H38&' if LG.get('halo') else '&H00&'
            parts.append((f"{{\\1a{on}\\3a{oa}}}" if a < 40 else f"{{\\1a&HFF&\\3a&HFF&\\t({a},{a + 150},\\1a{on}\\3a{oa})}}") + tx)
        halo = f"\\3c&H000000&\\bord{max(2.0, 0.006 * S):.1f}\\blur{max(2.0, 0.008 * S):.1f}\\shad0" if LG.get('halo') else ''
        L.append(f"Dialogue: 0,{tcs(t0)},{tcs(t1)},Leg,,0,0,0,,{{\\an5\\pos({W // 2},{int(y * H)})\\b{peso}{halo}}}{' '.join(parts)}")
        continue
    JK = chave_forte(b) if LG.get('chave_caixa') else []
    if JK: L.append(caixa_chave(b, t0, t1, y, JK))
    tinta = ass_cor(LG.get('chave_tinta', '#111111'))
    enf_bloco = any(x['i'] in ENF for x in b)
    for k, w in enumerate(b):
        e0 = t0 if k == 0 else snap(w['s'] - lead)
        e1 = snap(b[k + 1]['s'] - lead) if k + 1 < len(b) else t1
        if e1 <= e0: continue
        parts = []
        for j, x in enumerate(b):
            tx = limpa(x['t'], alta)
            if JK and j in JK:
                tx = f"{{\\c{tinta}\\3a&HFF&\\4a&HFF&}}{tx}{{\\c{cor}\\3a&H00&\\4a&H80&}}" if k >= JK[0] else tx
            elif x['i'] in ENF and not JK: tx = f"{{\\c{dest}\\fscx108\\fscy108}}{tx}{{\\c{cor}\\fscx100\\fscy100}}"
            elif j == k and LG.get('animacao') != 'nenhuma' and len(b) > 1 and not JK: tx = f"{{\\c{dest}}}{tx}{{\\c{cor}}}"
            parts.append(tx)
        anim = ''
        if k == 0:
            anim = {'pop': '\\fscx82\\fscy82\\t(0,70,\\fscx104\\fscy104)\\t(70,140,\\fscx100\\fscy100)',
                    'blur': '\\blur12\\fscx92\\fscy92\\fad(160,0)\\t(0,200,\\blur%.1f\\fscx100\\fscy100)' % max(0.6, 0.0012 * S),
                    'fade': '\\fad(120,0)', 'subir': '\\fad(80,0)\\move(%d,%d,%d,%d,0,140)' % (W // 2, int(y * H) + int(0.012 * H), W // 2, int(y * H))}.get(LG.get('animacao'), '')
        pos = '' if 'move' in anim else f'\\pos({W // 2},{int(y * H)})'
        hl = f"\\3c&H000000&\\3a&H40&\\bord{max(1.5, 0.0045 * S):.1f}\\blur{max(2.0, 0.007 * S):.1f}\\shad0" if LG.get('halo') else ''     # halo suave: lê em roupa clara sem contorno duro
        L.append(f"Dialogue: 1,{tcs(e0)},{tcs(e1)},Leg,,0,0,0,,{{\\an5{pos}\\b{LG.get('peso', 800)}{hl}{anim}}}{' '.join(parts)}")
if LG.get('layout') == 'cinema':
    L, rev = cinema(blocos)
elif LG.get('layout') == 'escada':
    L, rev = escada(blocos)
(P / '_edit/legendas.ass').write_text('\n'.join(L) + '\n', encoding='utf-8')
E.jsave(P / '_edit/legendas.json', {'blocos': rev, 'fonte': LG['fonte'], 'y': LG['y']})
D = [f'# Legendas — {len(rev)} blocos · {LG["fonte"]} {LG.get("peso")} · {"CAIXA ALTA" if alta else "frase"} · y={LG["y"]}', '',
     'Corrigir palavra sem mexer em tempo: `legendas.py . --corrigir "#12=Rafael"` (índice da palavra) ou `"bril=brilho"` (todas).', '']
for r in rev:
    D.append(f"- {r['id']} [{E.tc(r['t0'])}] {r['texto']}" + (' _(oculta: a peça já diz o texto)_' if r['oculta'] else '') + (f" _(y={r['y']:.2f})_" if abs(r['y'] - LG['y']) > 0.01 and not r['oculta'] else ''))
(P / 'docs/LEGENDAS.md').write_text('\n'.join(D) + '\n', encoding='utf-8')
print(f"✔ {len(rev)} blocos de legenda → _edit/legendas.ass · docs/LEGENDAS.md")
for r in rev[:8]: print(f"  {r['id']} {E.tc(r['t0'])} {r['texto']}")
E.log_estado(P, 'legendas', 'feito', f'{len(rev)} blocos')
