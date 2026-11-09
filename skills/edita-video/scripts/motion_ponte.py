#!/usr/bin/env python3
"""motion_ponte.py — ETAPA 6: a ponte edita-video → motion-studio. Renderiza cada item "motion" do mapa.

    python3 motion_ponte.py <projeto> preparar        # monta motion/ (pecas.html + lib + fontes + pecas.js) e valida
    python3 motion_ponte.py <projeto> board           # stills de cada peça SOBRE o quadro real do vídeo → docs/folhas/motion_board.jpg
    python3 motion_ponte.py <projeto> render [--item mo03] [--rascunho]

Como funciona (references/motion-e-broll.md §ponte):
  · Peças prontas (titulo · palavra · numero · lista · lower_third · check · cta · comparacao · texto) vivem em
    motion/pecas.html (cópia de assets/motion/pecas.html — ajuste o look ali para o cliente) e usam a lib do
    motion-studio (springs, easing, máscara). Cada item vira UM render do motion-studio: `render.mjs --query peca=moNN`.
  · sobreposto → ProRes 4444 com ALFA (`--alpha`, fundo transparente, blur pré-multiplicado); tela_cheia/split → MP4.
  · peça "custom" → "projeto": pasta motion-studio criada com new.sh (filme próprio); a ponte só renderiza no tamanho,
    fps e duração do item e lê os CUES dela.
  · Os CUES de cada peça (som com pico no evento) saem deslocados para o tempo da edição em _edit/motion_cues.json —
    o eventos.py junta com cortes, B-roll e punch-ins e o sfx.mjs do motion-studio sintetiza/gravações.
  · Marca: briefing.marca (ou kit do cliente marca.json) → cores/fontes das peças. Regra Orbe: nada de fonte na tela.
"""
import sys, os, json, shutil, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') and A[0] not in ('preparar', 'board', 'render') else None)
CMD = next((a for a in A if a in ('preparar', 'board', 'render')), 'preparar')
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
B, EST, ESTILO = E.config(P); OW, OH = E.formato(B)
MS = E.motion_studio() or E.die('motion-studio não encontrado (instale o plugin orbe-video ou defina MOTION_STUDIO)')
tl = E.jload(P / '_edit/timeline.json'); FPS = tl['fps']
inv = E.jload(P / '_edit/inventario.json') or {}; FPS_STR = inv.get('fps_str', str(FPS))
mapa = E.jload(P / '_edit/mapa.json') or E.die('rode mapa.py antes')
MD = P / 'motion'; MD.mkdir(exist_ok=True); (MD / 'out').mkdir(exist_ok=True)
itens = [it for it in mapa['itens'] if it['tipo'] in ('motion', 'texto') and it.get('t_ini') is not None]
if opt('item'): itens = [it for it in itens if it['id'] == opt('item')]

def marca():
    m = dict(EST.get('marca_padrao', {}))
    kit = B.get('cliente_kit') or (E.jload(P / '_edit/estado.json', {}) or {}).get('cliente_kit')
    if kit and (Path(kit) / 'marca.json').exists(): m.update(E.jload(Path(kit) / 'marca.json'))
    m.update(B.get('marca') or {})
    m.setdefault('accent', EST['legendas'].get('destaque', '#FFD43B')); m.setdefault('display', EST['legendas'].get('fonte', 'Montserrat'))
    m.setdefault('ui', 'Inter'); m.setdefault('ink', '#141413'); m.setdefault('paper', '#FFFFFF'); m.setdefault('bg', '#141413')
    # texto sobre o acento: escuro se o acento é claro
    h = m['accent'].lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    m.setdefault('onAccent', '#141413' if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else '#FFFFFF')
    return m

def imgs(itens):
    """fotos das peças (colagem, faixa): "fotos"/"foto" = arquivos do projeto → motion/img/; "quadros" = segundos da
    sequência → quadros do próprio vídeo (do mezanino, sem a câmera) — a pessoa vira a polaroide."""
    (MD / 'img').mkdir(exist_ok=True)
    inv_ = {c['id']: c for c in (inv.get('clips') or [])}
    for it in itens:
        pr = it.setdefault('params', {})
        def leva(f):
            src = (P / f) if not Path(f).is_absolute() else Path(f)
            if f.startswith('img/') and (MD / f).exists(): return f
            if not src.exists(): print(f"⚠ {it['id']}: foto {f} não existe"); return None
            dst = MD / 'img' / f"{it['id']}_{src.name}"; shutil.copy(src, dst); return f'img/{dst.name}'
        fs = [x for x in (leva(f) for f in pr.get('fotos', [])) if x]
        for k, tq in enumerate(pr.get('quadros', [])):
            seg = next((sg for sg in tl['segmentos'] if sg['seq_in'] <= tq < sg['seq_out']), tl['segmentos'][-1])
            c = inv_.get(seg['clip']); src_t = seg['src_in'] + (tq - seg['seq_in'])
            if not c: continue
            dst = MD / 'img' / f"q_{it['id']}_{k}.jpg"
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{src_t:.3f}', '-i', str(P / c['mez']), '-frames:v', '1', '-vf', 'scale=900:-2', '-q:v', '3', str(dst)])
            if dst.exists(): fs.append(f'img/{dst.name}')
        if fs: pr['fotos'] = fs
        if pr.get('foto'): pr['foto'] = leva(pr['foto']) or pr['foto']

def lugar_livre(t0, t1):
    """posicao "auto" (R1): a peça vai para o espaço LIVRE do quadro final — acima da cabeça se sobra ≥ 22% em cima,
    senão no peito. Mede o rosto (rosto.py) através da câmera (camera.py) no intervalo do item. Devolve (cy, vaga) em
    fração da altura: centro da peça e altura que ela pode ocupar."""
    cam = E.jload(P / '_edit/camera.json')
    if not cam:
        if not (P / '_edit/rosto').exists(): subprocess.run([sys.executable, str(E.SKILL / 'scripts/rosto.py'), str(P)], capture_output=True)
        subprocess.run([sys.executable, str(E.SKILL / 'scripts/camera.py'), str(P)], capture_output=True)
        cam = E.jload(P / '_edit/camera.json')
    if not cam: return 0.215, 0.26
    ros = {}; caixas = []
    for n in range(int(t0 * FPS), max(int(t0 * FPS) + 1, int(t1 * FPS)), 3):
        if n >= len(cam['quadros']): break
        q = cam['quadros'][n]
        if q['clip'] not in ros: ros[q['clip']] = (E.jload(P / f"_edit/rosto/{q['clip']}.json") or {}).get('amostras', [])
        am = [a for a in ros[q['clip']] if a[6] > 0]
        if not am: continue
        a = min(am, key=lambda x: abs(x[0] - q['ts']))
        if abs(a[0] - q['ts']) > 1.0: continue
        x0, y0 = q['cx'] - q['cw'] / 2, q['cy'] - q['ch'] / 2
        caixas.append(((a[2] - a[4] / 2 - y0) / q['ch'], (a[2] + a[4] / 2 - y0) / q['ch']))
    if not caixas: return 0.215, 0.26
    topo = sorted(c[0] for c in caixas)[len(caixas) // 2]; base = sorted(c[1] for c in caixas)[len(caixas) // 2]
    cima, baixo = (0.05, topo - 0.03), (base + 0.05, 0.78)      # cima pode encostar no cabelo (R1); baixo para antes da UI do Reels
    hc, hb = cima[1] - cima[0], baixo[1] - baixo[0]
    if hc >= 0.12 and hc >= 0.8 * hb: return round((cima[0] + cima[1]) / 2, 3), round(hc, 3)
    if hb >= 0.10: return round((baixo[0] + baixo[1]) / 2, 3), round(hb, 3)
    return 0.16, 0.2

def preparar():
    if not (MD / 'pecas.html').exists() or '--recopiar' in A: shutil.copy(E.SKILL / 'assets/motion/pecas.html', MD / 'pecas.html')
    (MD / 'lib').mkdir(exist_ok=True); shutil.copy(MS / 'template/lib/motion.js', MD / 'lib/motion.js')
    mk = marca()
    if any(it.get('peca') in ('rotulo', 'empilha', 'doc') for it in itens): mk.setdefault('script', 'Great Vibes'); mk.setdefault('serif', 'Instrument Serif')
    ff = MD / 'fonts/.familias'; atual = ff.read_text() if ff.exists() else ''
    fam = f"{mk['display']}|{mk['ui']}|{mk.get('serif', '')}|{mk.get('faixa', '')}|{mk.get('mao', '')}|{mk.get('script', '')}"
    if not (MD / 'fonts/fonts.css').exists() or atual != fam:
        slug = lambda f: f.lower().replace(' ', '-')
        extra = [f"{slug(mk[k])}:{w}" for k, w in (('serif', '400'), ('faixa', '400'), ('mao', '700'), ('script', '400')) if mk.get(k)]
        r = subprocess.run(['bash', str(MS / 'scripts/fonts.sh'), f"{slug(mk['display'])}:600,700,800,900", f"{slug(mk['ui'])}:500,600,700,800,900", *extra, '--dir', str(MD / 'fonts')], capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])
        (MD / 'fonts/.familias').write_text(fam)
    # texturas do look dossiê (papelão, papel quadriculado, persiana) — geradas em código no filme "A conta" (Orbe)
    if (E.SKILL / 'assets/motion/dossie').exists(): shutil.copytree(E.SKILL / 'assets/motion/dossie', MD / 'dossie', dirs_exist_ok=True)
    look = EST.get('motion', {}).get('look') or ('card' if ESTILO in ('clinica-premium', 'luxo') else 'bold')
    D = {'w': OW, 'h': OH, 'fps': FPS, 'marca': mk, 'look': B.get('motion_look', look), 'itens': {}}
    imgs(itens)
    auto = [it for it in itens if it.get('posicao') == 'auto' and it.get('modo', 'sobreposto') == 'sobreposto']
    if auto:
        for it in auto:
            cy, vaga = lugar_livre(it['t_ini'], it['t_fim'])
            it['_cy'], it['_vaga'] = cy, vaga; it['caixa'] = [round(cy - vaga / 2, 3), round(cy + vaga / 2, 3)]     # legendas.py desvia dessa faixa
        E.jsave(P / '_edit/mapa.json', mapa)
    for it in itens:
        D['itens'][it['id']] = {'peca': it.get('peca', 'texto' if it['tipo'] == 'texto' else 'titulo'), 'modo': it.get('modo', 'sobreposto'), 'posicao': it.get('posicao', 'centro'),
                                'texto': it.get('texto', ''), 'params': it.get('params', {}), 'dur': round(it['t_fim'] - it['t_ini'], 4), 'look': it.get('look'),
                                'sfx_saida': it.get('sfx_saida', False), 'cy': it.get('_cy'), 'vaga': it.get('_vaga')}
    (MD / 'pecas.js').write_text('// GERADO por motion_ponte.py a partir de _edit/mapa.json — edite o mapa, não este arquivo\nwindow.PECAS = ' + json.dumps(D, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')
    return D

def ler(ids, stills=None):
    alfa = ','.join(i for i in ids if D['itens'].get(i, {}).get('modo') == 'sobreposto')
    cmd = ['node', str(E.SKILL / 'scripts/pecas.mjs'), '--ms', str(MS), '--page', str(MD / 'pecas.html'), '--ids', ','.join(ids), '--w', str(OW), '--h', str(OH), '--alpha-ids', alfa]
    if stills: cmd += ['--stills', str(stills)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: E.die('pecas.mjs falhou: ' + r.stderr[-800:])
    return json.loads(r.stdout)

D = preparar()
std = [it for it in itens if it.get('peca') != 'custom']
custom = [it for it in itens if it.get('peca') == 'custom']
if CMD == 'preparar':
    info = ler([it['id'] for it in std]) if std else {}
    for it in std:
        i = info.get(it['id'], {})
        for v in i.get('validate', []) + i.get('erros', []): print(f"⚠ {it['id']}: {v}")
    print(f"✔ motion/ pronto: {len(std)} peça(s) padrão, {len(custom)} custom · marca accent {D['marca']['accent']} · look {D['look']}")
    print('→ próximo: motion_ponte.py . board (olhe as peças sobre o vídeo) → motion_ponte.py . render')

if CMD == 'board':
    import numpy as np, cv2
    st = MD / 'stills'; info = ler([it['id'] for it in std], st)
    if not (P / '_edit/camera.json').exists():      # o board mostra a peça sobre o quadro REAL (já reenquadrado)
        if not (P / '_edit/rosto').exists(): subprocess.run([sys.executable, str(E.SKILL / 'scripts/rosto.py'), str(P)])
        subprocess.run([sys.executable, str(E.SKILL / 'scripts/camera.py'), str(P)], capture_output=True)
    cam = E.jload(P / '_edit/camera.json'); invc = {c['id']: c for c in inv['clips']}
    tiles = []
    for it in std:
        i = info[it['id']]
        for s in i['stills']:
            tq = it['t_ini'] + s['t']; n = min(len(cam['quadros']) - 1, int(tq * FPS)); q = cam['quadros'][n]
            fr = E.run(['ffmpeg', '-v', 'error', '-ss', f"{q['ts']:.3f}", '-i', str(P / invc[q['clip']]['mez']), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture=True, text=False).stdout
            c = invc[q['clip']]; img = np.frombuffer(fr, np.uint8).reshape(c['h'], c['w'], 3)
            x0, y0 = q['cx'] - q['cw'] / 2, q['cy'] - q['ch'] / 2
            M = np.float32([[OW / q['cw'], 0, -x0 * OW / q['cw']], [0, OH / q['ch'], -y0 * OH / q['ch']]])
            base = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            ov = cv2.imread(s['arquivo'], cv2.IMREAD_UNCHANGED)
            if ov is not None and ov.shape[2] == 4:
                ov = cv2.resize(ov, (OW, OH)); a = ov[:, :, 3:4] / 255.0; base = (base * (1 - a) + ov[:, :, :3] * a).astype(np.uint8)
            elif ov is not None: base = cv2.resize(ov[:, :, :3], (OW, OH))
            sm = cv2.resize(base, (OW * 3 // 8, OH * 3 // 8), interpolation=cv2.INTER_AREA)
            cv2.putText(sm, f"{it['id']} {it.get('peca')} {s['t']:.2f}s", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (59, 212, 255), 2)
            tiles.append(sm)
    if tiles:
        cols = 6; h, w = tiles[0].shape[:2]; rows = (len(tiles) + cols - 1) // cols
        sheet = np.full((rows * h, cols * w, 3), 20, np.uint8)
        for k, tl_ in enumerate(tiles): sheet[(k // cols) * h:(k // cols + 1) * h, (k % cols) * w:(k % cols + 1) * w] = tl_
        out = P / 'docs/folhas/motion_board.jpg'; cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])
        print(f'✔ {out.relative_to(P)} — {len(tiles)} stills (entrada · meio · saída de cada peça) sobre o quadro real. ABRA e critique.')

if CMD == 'render':
    cues = []
    sub = '1' if '--rascunho' in A else '4'
    for it in std + custom:
        alfa = it.get('modo', 'sobreposto') == 'sobreposto'; dur = it['t_fim'] - it['t_ini']
        page = MD / 'pecas.html' if it in std else Path(it['projeto']).resolve() / 'index.html'
        out = MD / 'out' / f"{it['id']}.mp4"
        cmd = ['node', str(MS / 'scripts/render.mjs'), str(page), '--w', str(OW), '--h', str(OH), '--fps', str(FPS_STR), '--sub', sub, '--out', str(out)]
        if it in std: cmd += ['--query', f"peca={it['id']}"]
        else: cmd += ['--dur', f'{dur:.3f}']
        if alfa: cmd += ['--alpha']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: print(f"✗ {it['id']}: render falhou\n{r.stderr[-600:]}"); continue
        final = out.with_name(f"{it['id']}_alpha.mov") if alfa else out
        it['render'] = str(final.relative_to(P)); print(f"✔ {it['id']} ({it.get('peca')}, {dur:.1f}s{', alfa' if alfa else ''}) → {it['render']}")
    info = ler([it['id'] for it in std]) if std else {}
    for it in custom:
        try:
            r = subprocess.run(['node', str(E.SKILL / 'scripts/pecas.mjs'), '--ms', str(MS), '--page', str(Path(it['projeto']).resolve() / 'index.html'), '--ids', '_', '--w', str(OW), '--h', str(OH)], capture_output=True, text=True)
            info[it['id']] = json.loads(r.stdout)['_']
        except Exception: info[it['id']] = {'cues': []}
    for it in std + custom:
        for cu in info.get(it['id'], {}).get('cues', []):
            if it.get('sfx') == 'nenhum': continue
            cues.append({**cu, 't': round(it['t_ini'] + cu['t'], 4), 'origem': it['id']})
    if opt('item'):      # render parcial: mantém os cues das outras peças
        feitos = {it['id'] for it in std + custom}
        cues += [c for c in (E.jload(P / '_edit/motion_cues.json', []) or []) if c.get('origem') not in feitos]
    E.jsave(P / '_edit/motion_cues.json', sorted(cues, key=lambda c: c['t']))
    E.jsave(P / '_edit/mapa.json', mapa)
    print(f"✔ {len(cues)} cues de som das peças → _edit/motion_cues.json")
    E.log_estado(P, 'motion', 'feito', f'{len(std) + len(custom)} peças')
