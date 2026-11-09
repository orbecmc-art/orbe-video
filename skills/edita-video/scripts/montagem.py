#!/usr/bin/env python3
"""montagem.py — EDIT CINEMATOGRÁFICO sem fala (carros, produto, evento, imóvel): takes e fotos montados na batida.

    python3 montagem.py <pasta> takes [<pasta de mídia>]     # folhas de contato + docs/TAKES.md (o que cada take tem)
    python3 montagem.py <pasta> musica                      # gera/mede a trilha → audio/beats.json (grade de batidas)
    python3 montagem.py <pasta> [--rascunho] [--de 3 --ate 9]  # renderiza _edit/montagem.json → renders/montagem_vNN.mp4
    python3 montagem.py <pasta> som                         # refaz só a mixagem (trilha/SFX/volumes) sobre o último vídeo

<pasta> é qualquer pasta (cria _edit/, audio/, renders/, docs/). Mídia: vídeos (MOV/MP4) e fotos (JPG/PNG/HEIC→JPG).
O Claude LÊ as folhas (docs/folhas/takes_*.jpg), escreve _edit/montagem.json e renderiza (references/edit-cinema.md).

_edit/montagem.json
{ "estilo": "cinema-lento", "formato": "9x16", "fps": 30,
  "musica": {"gerar": {"style": "piano", "bpm": 64, "structure": "intro:1,drop:3,outro:1"}} | {"arquivo": "trilha.mp3", "inicio": 12.0},
  "cor": "showroom" | "outono" | "filme" | "alpino" | "dourado" | "noite", "grao": 0.03, "vinheta": 0.25, "halo": 0.1,
  "barras": 0.0 (fração da altura, cada lado) · "girado": false (monta em 16:9 e gira 90° — "vire o celular"),
  "planos": [ {"src": "fotos/x.jpg" | "brutos/IMG_1.MOV", "dur": 2.1 | "2b" (batidas) | "1c" (compassos),
               "in": 0.0 (vídeo), "vel": 1.0 | "rampa": [[0,1],[0.35,0.35],[1,1]] (fração do plano → velocidade),
               "mov": "push|pull|pan-e|pan-d|tilt-c|tilt-b|deriva|parado|orbita", "foco": [0.5,0.5], "zoom": [1.0,1.1], "dist": 0.08,
               "trans": "corte|flash|whip|zoom|fade|preto|luz" (como ENTRA), "tremor": 0, "som": true (som do take no mix),
               "texto": {"tipo": "legenda|titulo|cartela", "txt": "…", "maquina": true} } ],
  "cartelas": [{"depois": 3, "dur": 1.2, "txt": "fuck it", "fonte": "maquina"}]   # tela preta entre planos (índice)
  "fim": {"txt": "911 CARRERA T", "sub": "Rivoli Concept", "dur": 2.2},
  "som": {"trilha_db": -3, "takes_db": -8, "sfx": "auto|nenhum", "lufs": -14}, "corte_na_batida": true }
Regras (references/edit-cinema.md): corte cai na batida (downbeat nos momentos grandes); cada plano é UMA ideia; foto
ganha movimento de câmera (nunca parada); rampa só em take ≥ 50 qps ou com mistura de quadros; sem fonte/crédito na tela.
"""
import sys, os, re, json, math, subprocess, shutil, time
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path
import numpy as np, cv2

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = Path(A[0]).resolve() if A and not A[0].startswith('--') else Path.cwd()
CMD = next((a for a in A[1:2] if a in ('takes', 'musica', 'som')), 'render')
for d in ('_edit', 'audio', 'renders', 'docs/folhas', 'fonts'): (P / d).mkdir(parents=True, exist_ok=True)
MS = E.motion_studio()
VID = ('.mov', '.mp4', '.m4v', '.mkv', '.webm'); FOT = ('.jpg', '.jpeg', '.png', '.webp')

def probe(f):
    r = json.loads(E.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(f)]).stdout)
    v = next((s for s in r['streams'] if s['codec_type'] == 'video'), {}); a = any(s['codec_type'] == 'audio' for s in r['streams'])
    rot = 0
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd: rot = int(sd['rotation'])
    w, h = int(v.get('width', 0)), int(v.get('height', 0))
    if abs(rot) in (90, 270): w, h = h, w
    fr = v.get('avg_frame_rate', '30/1'); n, dd = (fr.split('/') + ['1'])[:2]; fps = float(n) / max(1e-9, float(dd or 1))
    return {'w': w, 'h': h, 'fps': round(fps, 3), 'dur': float(r['format'].get('duration', 0)), 'audio': a,
            'hdr': v.get('color_transfer') in ('arib-std-b67', 'smpte2084')}

# ───────────────────────── takes: o que tem em cada arquivo ─────────────────────────
if CMD == 'takes':
    src = Path(A[2]).resolve() if len(A) > 2 and not A[2].startswith('--') else P
    fs = sorted([f for f in src.rglob('*') if f.suffix.lower() in VID + FOT and not f.name.startswith('._')])
    L = [f'# Takes — {len(fs)} arquivos em {src}', '', '| # | arquivo | tipo | tamanho | qps | dur | som | movimento (0 parado · 30+ muito) | nota |', '|---|---|---|---|---|---|---|---|---|']
    tiles = []
    for k, f in enumerate(fs, 1):
        if f.suffix.lower() in FOT:
            im = cv2.imread(str(f)); h, w = im.shape[:2]
            th = cv2.resize(im, (int(240 * w / h), 240)); tiles.append((k, f.name, [th]))
            L.append(f'| {k} | {f.name} | foto | {w}×{h} | — | — | — | — | {"deitada" if w > h else "em pé"} |'); continue
        m = probe(f); n = 6; fr = []
        for i in range(n):
            t = m['dur'] * (i + 0.5) / n
            raw = E.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(f), '-frames:v', '1', '-vf', 'scale=-2:240', '-f', 'image2pipe', '-vcodec', 'png', '-'], text=False).stdout
            im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if im is not None: fr.append(im)
        mov = np.mean([cv2.absdiff(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)).mean() for a, b in zip(fr, fr[1:])]) if len(fr) > 1 else 0
        pk = ''
        if m['audio']:
            st = E.run(['ffmpeg', '-hide_banner', '-i', str(f), '-af', 'astats=metadata=0', '-f', 'null', '-'], check=False).stderr
            v = re.findall(r'Peak level dB:\s*(-?[\d.]+)', st); pk = f'pico {float(v[-1]):.1f} dB' if v else ''
        tiles.append((k, f.name, fr))
        L.append(f"| {k} | {f.name} | vídeo | {m['w']}×{m['h']} | {m['fps']:g} | {m['dur']:.1f}s | {pk or '—'} | {mov:.0f} | {'câmera lenta ok' if m['fps'] >= 50 else ''}{' HDR→SDR' if m['hdr'] else ''} |")
    # folhas: 1 linha por take (6 quadros), 12 takes por folha
    for g in range(0, len(tiles), 12):
        rows = []
        for k, nome, fr in tiles[g:g + 12]:
            row = np.full((250, 1440, 3), 18, np.uint8); x = 0
            for im in fr:
                if x + im.shape[1] > 1440: break
                row[5:5 + im.shape[0], x:x + im.shape[1]] = im; x += im.shape[1] + 4
            cv2.rectangle(row, (0, 0), (300, 30), (0, 0, 0), -1); cv2.putText(row, f'{k} {nome}'[:28], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            rows.append(row)
        cv2.imwrite(str(P / f'docs/folhas/takes_{g // 12 + 1:02d}.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    (P / 'docs/TAKES.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L))
    print(f"✔ {len(fs)} takes · folhas em docs/folhas/takes_*.jpg — ABRA as folhas antes de escrever o _edit/montagem.json")
    sys.exit()

M = E.jload(P / '_edit/montagem.json') or E.die('escreva _edit/montagem.json (veja o topo deste script e references/edit-cinema.md)')
FPS = int(M.get('fps', 30)); FMT = M.get('formato', '9x16')
OW, OH = {'9x16': (1080, 1920), '4x5': (1080, 1350), '1x1': (1080, 1080), '16x9': (1920, 1080)}[FMT]
GIR = bool(M.get('girado'))
CW, CH = (OH, OW) if GIR else (OW, OH)        # tela de montagem (girado: 16:9 dentro do 9:16)
SOM = {'trilha_db': -3, 'takes_db': -9, 'sfx': 'auto', 'lufs': -14, **(M.get('som') or {})}

# ───────────────────────── música e grade de batidas ─────────────────────────
def musica(dur_alvo):
    mu = M.get('musica', {}) or {}
    if mu.get('arquivo'):
        f = (P / mu['arquivo']); ini = float(mu.get('inicio', 0))
        E.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{ini:.3f}', '-i', str(f), '-t', f'{dur_alvo + 3:.2f}', '-ac', '2', '-ar', '48000', str(P / 'audio/music.wav')])
        bj = subprocess.run([sys.executable, str(MS / 'scripts/beats.py'), str(P / 'audio/music.wav')] + (['--bpm', str(mu['bpm'])] if mu.get('bpm') else []), capture_output=True, text=True)
        b = json.loads(bj.stdout) if bj.returncode == 0 else {'bpm': 0, 'beats': [], 'downbeats': []}
    elif mu.get('gerar') or not mu:
        g = mu.get('gerar') or {'style': 'cinematic', 'bpm': 90}
        cmd = ['node', str(MS / 'scripts/music.mjs'), '--style', g.get('style', 'cinematic'), '--bpm', str(g.get('bpm', 90)), '--fps', str(FPS),
               '--out', str(P / 'audio/music.wav'), '--beats', str(P / 'audio/beats.json'), '--seed', str(g.get('seed', 7))]
        cmd += ['--structure', g['structure']] if g.get('structure') else ['--dur', f'{dur_alvo:.2f}']
        if g.get('key'): cmd += ['--key', g['key']]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: E.die('music.mjs falhou: ' + r.stderr[-400:])
        b = E.jload(P / 'audio/beats.json')
    else:
        return None
    E.jsave(P / 'audio/beats.json', b); return b

def beats_de(b):
    return sorted(set(float(x) for x in (b or {}).get('beats', []))), sorted(set(float(x) for x in (b or {}).get('downbeats', [])))

if CMD == 'musica':
    b = musica(float(opt('dur', 20)))
    bt, db_ = beats_de(b); print(f"✔ audio/music.wav · {b.get('bpm')} bpm · {len(bt)} batidas · {len(db_)} tempos fortes · seções {[s.get('name') for s in b.get('sections', [])]}")
    sys.exit()

# ───────────────────────── linha do tempo ─────────────────────────
PL = M['planos']
mu = M.get('musica', {}); SEM_MUSICA = mu is False; mu = mu or {}
bpm_hint = (mu.get('gerar') or {}).get('bpm') or mu.get('bpm') or 90
def dur_s(d, bpm):
    if isinstance(d, str) and d.endswith('b'): return float(d[:-1]) * 60 / bpm
    if isinstance(d, str) and d.endswith('c'): return float(d[:-1]) * 4 * 60 / bpm
    return float(d)
est = sum(dur_s(p.get('dur', 2), bpm_hint) for p in PL) + sum(dur_s(c.get('dur', 1.2), bpm_hint) for c in M.get('cartelas', [])) + float((M.get('fim') or {}).get('dur', 0))
B = None if SEM_MUSICA else musica(est)
BPM = float((B or {}).get('bpm') or bpm_hint)
BT, DBT = beats_de(B)
def encaixa(t):
    """corte cai na batida mais próxima (± meia batida) — a grade manda, o plano se ajusta."""
    if not BT or not M.get('corte_na_batida', True): return t
    k = min(BT, key=lambda x: abs(x - t)); return k if abs(k - t) <= 30 / BPM + 1e-6 else t
seq = []; t = float(M.get('inicio', 0)); cart = {int(c['depois']): c for c in M.get('cartelas', [])}
for i, p in enumerate(PL):
    d = dur_s(p.get('dur', 2), BPM); t1 = encaixa(t + d)
    if t1 - t < 0.25: t1 = t + d
    seq.append({'k': 'plano', 'i': i, 'p': p, 't0': t, 't1': t1}); t = t1
    if i in cart:
        c = cart[i]; t1 = encaixa(t + dur_s(c.get('dur', 1.2), BPM)); seq.append({'k': 'cartela', 'c': c, 't0': t, 't1': t1}); t = t1
if M.get('fim'):
    f = M['fim']; t1 = t + float(f.get('dur', 2.2)); seq.append({'k': 'fim', 'f': f, 't0': t, 't1': t1}); t = t1
DUR = t; NF = int(round(DUR * FPS))

# ───────────────────────── fontes (texto desenhado no quadro) ─────────────────────────
from PIL import Image, ImageDraw, ImageFont
FONTES = {'maquina': ('courier-prime', '400'), 'serifa': ('cormorant-garamond', '500'), 'serifa_i': ('cormorant-garamond', '500i'),
          'sans': ('inter-tight', '500'), 'sans_forte': ('inter-tight', '700'), 'titulo': ('inter-tight', '300')}
def fonte(nome, px):
    slug, w = FONTES.get(nome, FONTES['sans']); f = P / f'fonts/{slug}-{w}.ttf'
    if not f.exists():
        subprocess.run([sys.executable, str(E.SKILL / 'scripts/fontes.py'), str(P), f'{slug}:{w}'], capture_output=True)
    try: return ImageFont.truetype(str(f), int(px))
    except Exception: return ImageFont.load_default()

def texto_rgba(txt, nome, px, cor=(242, 236, 224), track=0.0, n_chars=None, sombra=True):
    """renderiza texto (com tracking e revelação letra a letra) numa camada RGBA justa."""
    f = fonte(nome, px); vis = txt if n_chars is None else txt[:n_chars]
    ws = [f.getlength(c) + track * px for c in txt]; W = int(sum(ws) + px); H = int(px * 1.6)
    im = Image.new('RGBA', (max(W, 4), H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = px * 0.3
    for c, w in zip(vis, ws):
        d.text((x, px * 0.2), c, font=f, fill=tuple(cor) + (255,)); x += w
    if sombra:        # sombra macia (texto legível sobre qualquer imagem, sem caixa)
        from PIL import ImageFilter
        a = im.split()[3].filter(ImageFilter.GaussianBlur(max(2, px * 0.12))).point(lambda v: int(v * 0.65))
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(a); im = Image.alpha_composite(sh, im)
    return np.array(im), sum(ws)

def cola(base, rgba, cx, cy, alpha=1.0):
    h, w = rgba.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(base.shape[1], x0 + w), min(base.shape[0], y0 + h)
    if xb <= xa or yb <= ya: return
    s = rgba[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); a = s[..., 3:4] / 255 * alpha
    base[ya:yb, xa:xb] = (base[ya:yb, xa:xb] * (1 - a) + s[..., [2, 1, 0]] * a).astype(np.uint8)

# ───────────────────────── fontes de imagem (fotos e takes) ─────────────────────────
HEAD = 1.22        # folga de zoom/pan acima da cobertura
_fotos = {}
def foto(path):
    if path in _fotos: return _fotos[path]
    im = Image.open(P / path); im = __import__('PIL.ImageOps', fromlist=['x']).exif_transpose(im).convert('RGB')
    w, h = im.size; s = max(CW / w, CH / h) * HEAD
    im = im.resize((int(w * s), int(h * s)), Image.LANCZOS); a = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    _fotos[path] = a; return a

class Take:
    """lê um vídeo em ordem, escalado para cobrir a tela com folga; entrega o quadro no tempo pedido (mistura entre
    quadros vizinhos quando a câmera lenta passa da taxa de quadros do take)."""
    def __init__(s, path, t_in):
        s.m = probe(P / path); s.fps = s.m['fps'] or 30
        sc = max(CW / s.m['w'], CH / s.m['h']) * 1.12; s.w, s.h = int(s.m['w'] * sc) // 2 * 2, int(s.m['h'] * sc) // 2 * 2
        vf = f"scale={s.w}:{s.h}:flags=lanczos" + (",zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" if s.m['hdr'] else '')
        s.pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t_in:.3f}', '-i', str(P / path), '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
        s.idx = -1; s.cur = None; s.prev = None
    def ler(s):
        raw = s.pr.stdout.read(s.w * s.h * 3)
        if len(raw) < s.w * s.h * 3: return False
        s.prev = s.cur; s.cur = np.frombuffer(raw, np.uint8).reshape(s.h, s.w, 3); s.idx += 1; return True
    def quadro(s, t_rel):
        alvo = t_rel * s.fps; n = int(alvo)
        while s.idx < n + 1 and s.ler(): pass
        if s.cur is None: return np.zeros((s.h, s.w, 3), np.uint8)
        fr = alvo - n
        if s.prev is not None and s.idx == n + 1 and 0.15 < fr < 0.85:      # mistura de quadros na câmera lenta
            return cv2.addWeighted(s.prev, 1 - fr, s.cur, fr, 0)
        return s.prev if (s.idx == n + 1 and s.prev is not None and fr < 0.5) else s.cur
    def fecha(s):
        try: s.pr.kill()
        except Exception: pass

def tempo_fonte(p, u, d):
    """tempo dentro do take para a fração u do plano (integra a velocidade/rampa)."""
    if p.get('rampa'):
        pts = sorted(p['rampa']); us = np.linspace(0, u, 40); vs = np.interp(us, [x[0] for x in pts], [x[1] for x in pts])
        return float((getattr(np, 'trapezoid', None) or np.trapz)(vs, us) * d)
    return float(p.get('vel', 1.0)) * u * d

ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, x)))
def camera(p, u, sw, sh):
    """(cx, cy, z) no espaço da fonte para a fração u do plano. z multiplica a escala de cobertura."""
    mv = p.get('mov', 'deriva'); fx, fy = p.get('foco', [0.5, 0.5]); z0, z1 = p.get('zoom', {'push': [1.0, 1.12], 'pull': [1.12, 1.0], 'orbita': [1.06, 1.12]}.get(mv, [1.04, 1.04]))
    e = ease(u) if p.get('curva', 'suave') == 'suave' else u; dd = float(p.get('dist', 0.08))
    if mv == 'parado': z0 = z1 = z0
    if mv == 'deriva': z0, z1 = 1.0, 1.03
    z = z0 + (z1 - z0) * e; cx, cy = fx, fy
    if mv == 'pan-e': cx = fx + dd * (0.5 - e) * 2
    if mv == 'pan-d': cx = fx - dd * (0.5 - e) * 2
    if mv == 'tilt-c': cy = fy + dd * (0.5 - e) * 2
    if mv == 'tilt-b': cy = fy - dd * (0.5 - e) * 2
    if mv == 'orbita': cx = fx + dd * (0.5 - e) * 2
    return cx * sw, cy * sh, z

def enquadra(src, cx, cy, z, rot=0.0, dx=0.0):
    sh, sw = src.shape[:2]; s = max(CW / sw, CH / sh) * z
    hw, hh = CW / 2 / s, CH / 2 / s                       # meia janela na fonte
    cx = min(max(cx, hw), sw - hw); cy = min(max(cy, hh), sh - hh)
    Mx = cv2.getRotationMatrix2D((cx, cy), rot, s); Mx[0, 2] += CW / 2 - cx + dx; Mx[1, 2] += CH / 2 - cy
    return cv2.warpAffine(src, Mx, (CW, CH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ───────────────────────── cor, grão, vinheta, halo ─────────────────────────
def curva(pts, sombra=0.0, luz=0.0):
    """curva de um canal + tom nas sombras/luzes (split-tone dobrado na própria curva: custo zero por quadro)."""
    x = np.arange(256) / 255; y = np.interp(x, [a for a, b in pts], [b for a, b in pts]) * 255
    return np.clip(y + sombra * (1 - x) ** 2 + luz * x ** 2, 0, 255).astype(np.uint8)
GRADES = {   # curvas R, G, B · saturação · tom das sombras (B, G, R) · tom das luzes (B, G, R)
    'showroom': ([(0, .02), (.5, .5), (1, .98)], [(0, .02), (.5, .5), (1, .99)], [(0, .03), (.5, .52), (1, 1)], 0.92, (6, 2, -2), (-4, 0, 2)),
    'outono':   ([(0, .04), (.4, .42), (1, 1)], [(0, .03), (.5, .48), (1, .96)], [(0, .03), (.5, .44), (1, .88)], 1.12, (-2, 2, 6), (-8, 2, 8)),
    'filme':    ([(0, .06), (.25, .22), (.75, .8), (1, .95)], [(0, .06), (.25, .23), (.75, .78), (1, .94)], [(0, .08), (.25, .25), (.75, .74), (1, .86)], 0.80, (12, 7, -6), (-12, 2, 10)),
    'alpino':   ([(0, .04), (.5, .5), (1, .95)], [(0, .04), (.5, .5), (1, .95)], [(0, .05), (.5, .5), (1, .93)], 0.86, (6, 2, 0), (-4, 2, 4)),
    'dourado':  ([(0, .03), (.5, .52), (1, 1)], [(0, .03), (.5, .5), (1, .98)], [(0, .03), (.5, .47), (1, .93)], 1.0, (2, 2, 4), (-7, 2, 7)),
    'noite':    ([(0, .0), (.3, .26), (1, .96)], [(0, .01), (.3, .28), (1, .97)], [(0, .03), (.3, .32), (1, 1)], 0.9, (12, 4, -4), (-2, 0, 4)),
}
G = GRADES.get(M.get('cor', 'filme'), GRADES['filme'])
LUT = np.stack([curva(G[2], G[4][0], G[5][0]), curva(G[1], G[4][1], G[5][1]), curva(G[0], G[4][2], G[5][2])], 1).reshape(256, 1, 3)   # BGR
SAT = G[3] * float(M.get('saturacao', 1.0))
GR = float(M.get('grao', 0.03)); VIG = float(M.get('vinheta', 0.22)); HALO = float(M.get('halo', 0.0))
_vig = None; _grao = []
def acabamento(fr, n):
    """cor (LUT por canal), saturação, halo das luzes, vinheta e grão — tudo em uint8/cv2 (~25 ms por quadro)."""
    global _vig
    h, w = fr.shape[:2]
    fr = cv2.LUT(fr, LUT)
    if abs(SAT - 1) > 0.01:
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY); fr = cv2.addWeighted(fr, SAT, cv2.merge([gray] * 3), 1 - SAT, 0)
    if HALO:      # halation: só o que passa de ~70% de brilho, borrado em 1/4 da resolução, puxado para o quente
        br = cv2.subtract(cv2.resize(fr, (w // 4, h // 4), interpolation=cv2.INTER_AREA), (180, 180, 180, 0))
        br = cv2.resize(cv2.GaussianBlur(br, (0, 0), 6), (w, h)); fr = cv2.add(fr, cv2.multiply(br, (2.5 * HALO * 0.7, 2.5 * HALO * 0.9, 2.5 * HALO * 1.25, 0)))
    if VIG:
        if _vig is None or _vig.shape[:2] != (h, w):
            yy, xx = np.mgrid[0:h, 0:w]; r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.42
            v = ((1 - VIG * np.clip(r, 0, 1) ** 2.2) * 255).astype(np.uint8); _vig = cv2.merge([v] * 3)
        fr = cv2.multiply(fr, _vig, scale=1 / 255)
    if GR:
        if not _grao or _grao[0].shape[:2] != (h, w):
            _grao.clear(); rng = np.random.default_rng(3)
            for _ in range(6):
                z = rng.normal(0, GR * 255, (h // 2, w // 2)).astype(np.float32)
                _grao.append(cv2.resize(z, (w, h)).astype(np.int16)[..., None])
        fr = np.clip(fr.astype(np.int16) + _grao[n % 6], 0, 255).astype(np.uint8)
    return fr

# ───────────────────────── render ─────────────────────────
RASC = '--rascunho' in A
n0 = int(float(opt('de', 0)) * FPS); n1 = min(NF, int(float(opt('ate', 1e9)) * FPS))
ver = 1 + max([int(m.group(1)) for f in (P / 'renders').glob('montagem_v*.mp4') for m in [re.search(r'_v(\d+)', f.name)] if m] or [0])
out = P / (f'renders/_montagem_rascunho.mp4' if RASC else f'renders/montagem_v{ver:02d}.mp4')
SO_SOM = CMD == 'som' and (P / 'renders/_video.mp4').exists()     # 'som': refaz só a mixagem sobre o vídeo já renderizado
if not SO_SOM:
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                            '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast' if RASC else 'medium', '-crf', '24' if RASC else '17',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', '-an', str(P / 'renders/_video.mp4')], stdin=subprocess.PIPE)
    from collections import OrderedDict
    takes = OrderedDict()       # no máximo 2 takes abertos (o atual e o anterior, para a fusão)
    def bloco_de(n):
        t = (n + 0.5) / FPS
        return next((k for k, b in enumerate(seq) if b['t0'] <= t < b['t1']), len(seq) - 1), t
    TRN = {'flash': 3, 'whip': 7, 'zoom': 6, 'fade': 10, 'preto': 7, 'luz': 12}
    def quadro_plano(b, t):
        p = b['p']; d = b['t1'] - b['t0']; u = (t - b['t0']) / d
        src = p['src']
        if Path(src).suffix.lower() in FOT:
            img = foto(src)
        else:
            key = id(b)
            if key not in takes:
                while len(takes) >= 2: takes.popitem(last=False)[1].fecha()
                takes[key] = Take(src, float(p.get('in', 0)))
            img = takes[key].quadro(max(0.0, tempo_fonte(p, u, d)))
        sh, sw = img.shape[:2]; cx, cy, z = camera(p, u, sw, sh)
        rot = float(p.get('rot', 0)) * (u - 0.5) * 2 if p.get('mov') == 'orbita' else 0.0
        dx = 0.0
        if p.get('tremor'):
            k = max(0.0, 1 - (t - b['t0']) / 0.35); dx = float(p['tremor']) * k * math.sin(t * 90) * 18
        return enquadra(img, cx, cy, z, rot, dx)

    def cartela(c, t, b):
        fr = np.zeros((CH, CW, 3), np.uint8); fr[:] = c.get('fundo', (8, 8, 8))
        txt = c.get('txt', ''); u = (t - b['t0']) / max(0.01, b['t1'] - b['t0'])
        dig = min(len(txt) * 0.055, 0.6 * (b['t1'] - b['t0']))         # a digitação termina com folga antes do corte
        nch = len(txt) if not c.get('maquina', c.get('fonte') == 'maquina') else int(min(1, (t - b['t0']) / max(0.2, dig)) * len(txt))
        lay, w = texto_rgba(txt, c.get('fonte', 'serifa_i'), (c.get('tamanho', 0.028)) * max(CW, CH), n_chars=nch, sombra=False)
        a = min(1, (t - b['t0']) / 0.25) * min(1, (b['t1'] - t) / 0.2)
        cola(fr, lay, CW / 2, CH * c.get('y', 0.5), a); return fr

    def fim(f, t, b):
        fr = np.zeros((CH, CW, 3), np.uint8); fr[:] = f.get('fundo', (6, 6, 6)); e = t - b['t0']
        a1 = min(1, e / 0.6); a2 = min(1, max(0, (e - 0.45) / 0.6)); out_ = min(1, (b['t1'] - t) / 0.4)
        l1, _ = texto_rgba(f.get('txt', ''), f.get('fonte', 'titulo'), f.get('tamanho', 0.072) * min(CW, CH), track=0.22, sombra=False)
        cola(fr, l1, CW / 2, CH * 0.48 - (1 - a1) * 10, a1 * out_)
        if f.get('sub'):
            l2, _ = texto_rgba(f['sub'].upper(), 'sans', 0.026 * min(CW, CH), cor=(200, 196, 188), track=0.35, sombra=False)
            cola(fr, l2, CW / 2, CH * 0.48 + f.get('tamanho', 0.072) * min(CW, CH) * 1.05, a2 * out_)
        return fr

    def legenda(fr, p, t, b):
        tx = p.get('texto');
        if not tx: return
        txt = tx.get('txt', ''); e = t - b['t0'] - float(tx.get('atraso', 0.2))
        if e < 0: return
        dig = min(len(txt) * 0.045, 0.6 * max(0.3, b['t1'] - b['t0'] - float(tx.get('atraso', 0.2))))
        nch = int(min(1, e / max(0.2, dig)) * len(txt)) if tx.get('maquina', True) else len(txt)
        tipo = tx.get('tipo', 'legenda'); px = {'legenda': 0.022, 'titulo': 0.06}.get(tipo, 0.022) * max(CW, CH) * (tx.get('escala', 1))
        na_faixa = BAR and tipo == 'legenda' and 'y' not in tx        # com faixas de cinema, a legenda mora na faixa de baixo
        if na_faixa: px = min(px, 0.5 * BAR * CH)
        lay, w = texto_rgba(txt, tx.get('fonte', 'maquina' if tipo == 'legenda' else 'sans'), px, cor=tuple(tx.get('cor', (236, 228, 205))),
                            track=0.18 if tipo == 'titulo' else 0.0, n_chars=nch, sombra=not na_faixa)
        a = min(1, (b['t1'] - t) / 0.25) * (min(1, e / 0.3) if not tx.get('maquina', True) else 1)
        x = CW * tx.get('x', 0.5); y = CH * (1 - BAR / 2) if na_faixa else CH * tx.get('y', 0.8)
        if tx.get('alinha') == 'esquerda': x += w / 2 - CW * 0.0
        cola(fr, lay, x, y, a)

    def transicao(fr, n, k):
        """efeito na ENTRADA do bloco k (primeiros quadros) e na saída do anterior (últimos quadros)."""
        b = seq[k]; tr = (b.get('p') or {}).get('trans', 'corte'); t = (n + 0.5) / FPS
        nb = (n + 0.5) - b['t0'] * FPS                               # quadros desde o corte
        if tr == 'flash' and nb < 3:
            a = [0.85, 0.45, 0.15][int(nb)]; fr = cv2.addWeighted(fr, 1 - a, np.full_like(fr, 255), a, 0)
        elif tr == 'luz' and nb < 12:
            a = math.sin(math.pi * nb / 12) * 0.55; h, w = fr.shape[:2]; yy, xx = np.mgrid[0:h:4, 0:w:4]
            g = np.exp(-(((xx - w * 0.85) / (w * 0.6)) ** 2 + ((yy - h * 0.2) / (h * 0.5)) ** 2))
            g = cv2.resize(g.astype(np.float32), (w, h))[..., None]
            fr = np.clip(fr + g * a * np.array([60, 140, 255], np.float32), 0, 255).astype(np.uint8)
        elif tr == 'zoom' and nb < 6:
            s = 1 + 0.25 * (1 - nb / 6) ** 2; Mx = cv2.getRotationMatrix2D((CW / 2, CH / 2), 0, s); fr = cv2.warpAffine(fr, Mx, (CW, CH), borderMode=cv2.BORDER_REFLECT)
            fr = cv2.blur(fr, (1 + int(14 * (1 - nb / 6)), 1 + int(14 * (1 - nb / 6))))
        elif tr == 'whip' and nb < 4:
            off = int(CW * 0.5 * (1 - nb / 4) ** 2); fr = np.roll(fr, off, 1); kz = 1 + int(60 * (1 - nb / 4)); fr = cv2.blur(fr, (kz, 1))
        elif tr == 'preto' and nb < 7:
            fr = (fr * (nb / 7)).astype(np.uint8)
        elif tr == 'fade' and nb < 10 and k > 0 and seq[k - 1]['k'] == 'plano':
            prev = quadro_plano(seq[k - 1], t); fr = cv2.addWeighted(prev, 1 - nb / 10, fr, nb / 10, 0)
        # saída do bloco: preto/whip antecipam o próximo
        if k + 1 < len(seq):
            nx = (seq[k + 1].get('p') or {}).get('trans', 'corte'); falta = b['t1'] * FPS - (n + 0.5)
            if nx == 'preto' and falta < 7: fr = (fr * (falta / 7)).astype(np.uint8)
            if nx == 'whip' and falta < 4:
                off = -int(CW * 0.5 * (1 - falta / 4) ** 2); fr = np.roll(fr, off, 1); kz = 1 + int(60 * (1 - falta / 4)); fr = cv2.blur(fr, (kz, 1))
            if (seq[k + 1]['k'] in ('cartela', 'fim')) and falta < 6 and nx == 'corte' and M.get('cartela_fade', True): fr = (fr * (0.35 + 0.65 * falta / 6)).astype(np.uint8)
        return fr

    BAR = float(M.get('barras', 0))
    t_ini = time.time()
    for n in range(n0, n1):
        k, t = bloco_de(n); b = seq[k]
        if b['k'] == 'plano': fr = quadro_plano(b, t)
        elif b['k'] == 'cartela': fr = cartela(b['c'], t, b)
        else: fr = fim(b['f'], t, b)
        fr = transicao(fr, n, k)
        if b['k'] == 'plano': fr = acabamento(fr, n)
        if BAR: hb = int(CH * BAR); fr[:hb] = 0; fr[CH - hb:] = 0      # faixas de cinema na composição (giradas viram laterais)
        if b['k'] == 'plano': legenda(fr, b['p'], t, b)                   # texto por cima de tudo (sem grão/cor)
        if GIR: fr = cv2.rotate(fr, cv2.ROTATE_90_CLOCKWISE)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    for k_ in list(takes): takes.pop(k_).fecha()
    enc.stdin.close(); enc.wait()
    print(f"✔ vídeo {OW}×{OH} · {(n1 - n0) / FPS:.1f}s · {len(seq)} blocos · {time.time() - t_ini:.0f}s de render")

# ───────────────────────── som: trilha + som dos takes + SFX na transição ─────────────────────────
SR = 48000; N = int(round(DUR * SR)) + SR
mix = np.zeros((N, 2), np.float32)
if (P / 'audio/music.wav').exists() and M.get('musica') is not False:
    y = E.load_wav(P / 'audio/music.wav', mono=False).astype(np.float32)[:N]; mix[:len(y)] += y * 10 ** (SOM['trilha_db'] / 20)
for b in seq:
    p = b.get('p') or {}
    if b['k'] != 'plano' or not p.get('som') or Path(p['src']).suffix.lower() in FOT: continue
    vel = float(p.get('vel', 1)); d = b['t1'] - b['t0']
    if p.get('rampa'): continue                     # som de take em rampa vira ruído: deixe a trilha/SFX
    raw = E.run(['ffmpeg', '-v', 'error', '-ss', f"{float(p.get('in', 0)):.3f}", '-i', str(P / p['src']), '-t', f'{d * vel:.3f}', '-ac', '2', '-ar', str(SR)]
                + (['-af', f'atempo={max(0.5, min(2, vel)):.3f}'] if abs(vel - 1) > 0.01 else []) + ['-f', 'f32le', '-'], check=False, text=False).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2) if raw else np.zeros((0, 2), np.float32)
    if not len(a): continue
    fd = min(len(a) // 4, int(0.03 * SR)); env = np.ones(len(a), np.float32); env[:fd] = np.linspace(0, 1, fd); env[-fd:] = np.linspace(1, 0, fd)
    i0 = int(b['t0'] * SR); a = a[:N - i0] * env[:N - i0, None] * 10 ** (float(p.get('som_db', SOM['takes_db'])) / 20); mix[i0:i0 + len(a)] += a
cues = []
if SOM['sfx'] != 'nenhum':
    TIPO = {'whip': ('whoosh', 0.55), 'zoom': ('whoosh', 0.5), 'flash': ('impact', 0.6), 'luz': ('swish', 0.35)}
    for b in seq:
        tr = (b.get('p') or {}).get('trans', 'corte')
        if tr in TIPO: cues.append({'t': round(b['t0'], 3), 'type': TIPO[tr][0], 'gain': TIPO[tr][1]})
        if b['k'] == 'cartela' and b['c'].get('maquina', b['c'].get('fonte') == 'maquina'): cues.append({'t': round(b['t0'] + 0.25, 3), 'type': 'type', 'gain': 0.35, 'n': len(b['c'].get('txt', ''))})
        if b['k'] == 'fim': cues.append({'t': round(b['t0'] + 0.05, 3), 'type': 'impact', 'gain': 0.45})
    for c in M.get('sfx', []): cues.append(c)
    if cues and MS:
        cj = P / 'audio/cues.json'; E.jsave(cj, cues)
        r = subprocess.run(['node', str(MS / 'scripts/sfx.mjs'), str(cj), '--dur', f'{DUR:.3f}', '--fps', str(FPS), '--out', str(P / 'audio/sfx.wav')]
                           + (['--bed', str(P / 'audio/music.wav'), '--bed-db', str(SOM['trilha_db'])] if (P / 'audio/music.wav').exists() else []), capture_output=True, text=True)
        if r.returncode == 0 and (P / 'audio/sfx.wav').exists():
            y = E.load_wav(P / 'audio/sfx.wav', mono=False).astype(np.float32)[:N]; mix[:len(y)] += y
mix = mix[:int(DUR * SR)]
fo = int(min(1.2, DUR * 0.1) * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
E.save_wav(P / 'audio/pre.wav', mix, SR)
def loud(path):
    r = E.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], check=False).stderr
    try: return {k: float(v) for k, v in json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}', r, re.S)[-1]).items() if k.startswith('input')}
    except Exception: return {}
alvo = float(SOM['lufs']); ganho = alvo - loud(P / 'audio/pre.wav').get('input_i', -20); lim = -1.8
def mixa(ganho, lim):     # ganho até o alvo + limitador com oversampling; ataque de 5 ms (1 ms distorce e o AAC estoura o pico)
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(P / 'audio/pre.wav'), '-af', f'volume={ganho:.2f}dB,aresample=192000,alimiter=limit={10 ** (lim / 20):.4f}:attack=5:release=120:level=false,aresample=48000',
           '-c:a', 'pcm_s24le', str(P / 'audio/mix.wav')])
    return loud(P / 'audio/mix.wav')
def junta():
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(P / 'renders/_video.mp4'), '-ss', f'{n0 / FPS:.3f}', '-t', f'{(n1 - n0) / FPS:.3f}', '-i', str(P / 'audio/mix.wav'),
           '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', str(out)])
    return loud(out)
for _ in range(4):
    m = mixa(ganho, lim)
    if abs(m.get('input_i', alvo) - alvo) <= 0.5 and m.get('input_tp', -9) <= -1.5: break
    ganho += alvo - m.get('input_i', alvo); lim -= 0.4 if m.get('input_tp', -9) > -1.5 else 0
for _ in range(3):        # confere o pico REAL no MP4 (depois do AAC); passou de −1 dBTP, baixa o teto e refaz
    mf = junta()
    if mf.get('input_tp', -9) <= -1.0: break
    lim -= mf['input_tp'] + 1.3; mixa(ganho, lim)
med = E.run(['ffmpeg', '-hide_banner', '-i', str(out), '-af', 'ebur128=peak=true', '-f', 'null', '-'], check=False).stderr
I = re.findall(r'I:\s+(-?[\d.]+) LUFS', med); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', med)

# ── QA e docs ──
cortes = [round(b['t0'], 2) for b in seq[1:]]
fora = [c for c in cortes if BT and c <= BT[-1] + 0.05 and min(abs(c - x) for x in BT) > 0.05] if M.get('corte_na_batida', True) else []
ts = [(b['t0'] + b['t1']) / 2 for b in seq][:24]
subprocess.run([sys.executable, str(E.SKILL / 'scripts/folha.py'), str(out), '--tempos', ','.join(f'{x:.2f}' for x in ts), '--saida', str(P / 'docs/folhas/montagem.jpg'), '--largura', '220'], capture_output=True)
L = [f"# Montagem — {M.get('estilo', '')} · {DUR:.1f}s · {BPM:.0f} bpm · {len(seq)} blocos", '',
     '| # | quando | dur | o quê | movimento | entra |', '|---|---|---|---|---|---|']
for i, b in enumerate(seq, 1):
    p = b.get('p') or {}
    oq = Path(p['src']).name if b['k'] == 'plano' else ('cartela: ' + b['c'].get('txt', '')) if b['k'] == 'cartela' else ('fim: ' + b['f'].get('txt', ''))
    L.append(f"| {i} | {b['t0']:.2f}s | {b['t1'] - b['t0']:.2f}s | {oq} | {p.get('mov', '') if p else ''}{' · rampa' if p.get('rampa') else ''} | {p.get('trans', 'corte') if p else ''} |")
L += ['', f"- Som: {I[-1] if I else '?'} LUFS · pico {TP[-1] if TP else '?'} dBTP (medido, não ouvido) · {len(cues)} efeitos",
      f"- Cortes fora da batida: {fora if fora else 'nenhum'}", f"- Folha: docs/folhas/montagem.jpg (ABRA antes de mostrar)"]
(P / 'docs/MONTAGEM.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L[-3:])); print(f'✔ {out.relative_to(P)}')
