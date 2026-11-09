#!/usr/bin/env python3
"""compor.py — o compositor: A-roll com câmera virtual + B-roll/fotos (Ken Burns) + peças de motion + cor + legendas.

    python3 compor.py <projeto> [--rascunho] [--saida renders/x.mp4] [--de 0 --ate 10] [--sem-legenda] [--sem-sobrepostos]

Ordem das camadas (de baixo para cima), quadro a quadro, em Python (numpy/OpenCV) com o ffmpeg nas duas pontas:
  1. BASE: A-roll do mezanino com a cor do estilo (ffmpeg) → recorte da câmera (camera.json) com interpolação Lanczos
     sub-pixel (zoom/push sem tremor) + nitidez leve quando o upscale passa de 1,4×.
     Ou, se um item de tela cheia cobre o quadro: B-roll/foto (cover + Ken Burns) ou peça de motion opaca.
     split: item na metade de cima, rosto (recorte em volta dos olhos) na de baixo; "split_fio" no estilo (hex ou
     "accent") desenha a borda dura com fio na cor de destaque (half band do Style Studio).
     janela: o item toma a tela e a câmera vira um CARTÃO quadrado (olhos no terço superior, cantos redondos, anel e
     sombra) — entra e sai com "recuo" (o quadro inteiro encolhe até o cartão: o zoom para fora do Joseph).
     Tratamento "papel" (estilo minimal ou "tratamento": "papel" no item): textura de papel, vinheta e bordas
     levemente desfocadas — o olho vai ao centro (pinturas, B-roll com texto por cima).
  2. TRANSIÇÃO do item (corte · fade · zoom · whip · flash · deslize = câmera desliza para revelar) na entrada e na saída.
  3. PEÇAS sobrepostas (ProRes 4444 com alfa do motion-studio). "fundo": "escurece" na peça → o vídeo atrás escurece
     e desfoca enquanto ela está no ar (animação "legenda + UI" na metade de baixo).
  4. LEGENDAS por último (libass no encoder) — nada cobre a legenda. legendas.faixa_desfoque: o terço da legenda
     escurece e desfoca de leve sob o texto (premium: o texto respira sem caixa).
  Efeitos: item "efeito": "quebra" → o rosto fica P&B (contraste alto) no intervalo; cor.grao → grão de filme no quadro.
Saída: vídeo SEM áudio em renders/_video_vNN.mp4 (o final.py junta a mixagem). --rascunho = metade da resolução, rápido.
"""
import sys, os, math, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np, cv2

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P)
RASC = '--rascunho' in A
cam = E.jload(P / '_edit/camera.json') or E.die('rode camera.py antes')
tl = E.jload(P / '_edit/timeline.json'); FPS = tl['fps']
inv = E.jload(P / '_edit/inventario.json'); INV = {c['id']: c for c in inv['clips']}; FPS_STR = inv.get('fps_str', str(FPS))
mapa = E.jload(P / '_edit/mapa.json', {}) or {}
OW, OH = cam['w'], cam['h']
if RASC: OW, OH = OW // 2 // 2 * 2, OH // 2 // 2 * 2
FR = cam['quadros']; N = len(FR)
n0 = int(float(opt('de', 0)) * FPS); n1 = min(N, int(float(opt('ate', 1e9)) * FPS))

# ── cor (references/cor.md) ──
GRADES = E.GRADES
preset = (EST.get('cor') or {}).get('preset', 'natural')
LUT = (EST.get('cor') or {}).get('lut')
def cadeia(path, dur): return E.cadeia_cor(P, EST, path, dur)

# ── decodificadores ──
class Dec:
    def __init__(self, path, start, vf, w, h, alpha=False):
        self.w, self.h, self.c = w, h, 4 if alpha else 3
        args = ['ffmpeg', '-v', 'error', '-ss', f'{max(0, start):.4f}', '-i', str(path), '-vf', (vf + ',' if vf else '') + f'fps={FPS_STR}',
                '-f', 'rawvideo', '-pix_fmt', 'bgra' if alpha else 'bgr24', '-']
        self.p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL); self.last = None
    def read(self):
        b = self.p.stdout.read(self.w * self.h * self.c)
        if len(b) == self.w * self.h * self.c: self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, self.c)
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass

# ── A-roll: um decodificador por trecho, consumido em ordem ──
segs = tl['segmentos']; GRADE_A = {c: cadeia(P / INV[c]['mez'], INV[c]['dur']) for c in INV}
up_max = max(cam['h'] / f['ch'] for f in FR) if FR else 1
nitidez = up_max > 1.4
aroll = {'k': None, 'dec': None}
# J-CUT (cortes.jcut quadros, 0 = desligado): o som do trecho novo entra antes da imagem — a imagem do trecho anterior
# continua J quadros depois do corte do áudio. Suaviza o "pulo" do jump cut (o painel Auto J-Cut faz o mesmo no Premiere).
J = 0 if '--sem-jcut' in A else int(EST['cortes'].get('jcut', 0) or 0)
SEG0 = {}
for i_, f_ in enumerate(FR): SEG0.setdefault(f_['k'], i_)
def aroll_frame(n):
    f = FR[n]; k = f['k']; off = n - SEG0[k]
    if J and k > 0 and off < J and segs[k]['seq_in'] - segs[k - 1]['seq_in'] > 0.4:
        if aroll['k'] != ('j', k):
            if aroll['k'] != k - 1:      # chegou aqui sem ter lido o anterior (render parcial): abre no fim dele
                if aroll['dec']: aroll['dec'].close()
                sp = segs[k - 1]; cp = INV[sp['clip']]
                aroll['dec'] = Dec(P / cp['mez'], sp['src_out'], GRADE_A[sp['clip']], cp['w'], cp['h'])
            aroll['k'] = ('j', k)
        f = FR[SEG0[k] - 1]              # mesmo enquadramento do último quadro do trecho anterior
    elif aroll['k'] != k:
        if aroll['dec']: aroll['dec'].close()
        s = segs[k]; c = INV[s['clip']]
        aroll['dec'] = Dec(P / c['mez'], f['ts'], GRADE_A[s['clip']], c['w'], c['h']); aroll['k'] = k
    img = aroll['dec'].read()
    sx, sy = OW / f['cw'], OH / f['ch']; x0, y0 = f['cx'] - f['cw'] / 2, f['cy'] - f['ch'] / 2
    M = np.float32([[sx, 0, -x0 * sx], [0, sy, -y0 * sy]])
    out = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if nitidez and not RASC:
        bl = cv2.GaussianBlur(out, (0, 0), 1.2); out = cv2.addWeighted(out, 1.35, bl, -0.35, 0)
    return out

# ── itens do mapa ──
def nf(t): return int(round(t * FPS))
ITENS = []
for it in mapa.get('itens', []):
    if it.get('t_ini') is None or it.get('tipo') == 'efeito': continue
    d = dict(it); d['n0'], d['n1'] = nf(it['t_ini']), nf(it['t_fim'])
    if it['tipo'] in ('broll', 'foto') and not it.get('arquivo'): print(f"⚠ {it['id']}: sem arquivo — fica o rosto (rode ativos.py)"); continue
    if it['tipo'] in ('motion', 'texto') and not it.get('render'): print(f"⚠ {it['id']}: peça não renderizada — rode motion_ponte.py render"); continue
    ITENS.append(d)
transp_padrao = {'corte': 'corte', 'suave': 'fade', 'dinamica': 'zoom'}.get(EST.get('transicao', 'corte'), 'corte')
ease = lambda p: 1 - (1 - min(1, max(0, p))) ** 3
ease_io = lambda p: 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, p)))

class Fonte:
    """B-roll (vídeo), foto ou motion opaco → quadro OW×OH (ou metade no split), com Ken Burns."""
    def __init__(self, it, area):
        self.it, self.aw, self.ah = it, area[0], area[1]; self.dec = None; self.img = None
        path = P / (it.get('render') or it['arquivo'])
        if it['tipo'] == 'foto':
            self.img = cv2.imread(str(path)); self.sw, self.sh = self.img.shape[1], self.img.shape[0]
            g = cadeia(path, 1) if False else ''
        elif it['tipo'] in ('motion', 'texto'):
            self.dec = Dec(path, 0, f'scale={OW}:{OH}', OW, OH); self.sw, self.sh = OW, OH
        else:
            pr = E.ffprobe(path); vs = next(s for s in pr['streams'] if s['codec_type'] == 'video')
            self.sw, self.sh = int(vs['width']), int(vs['height']); dur = float(pr['format'].get('duration', 0))
            need = (it['n1'] - it['n0']) / FPS
            ini = float(it.get('inicio', min(max(0.0, (dur - need) * 0.35), max(0.0, dur - need))))
            self.dec = Dec(path, ini, cadeia(path, dur), self.sw, self.sh)
    def frame(self, n):
        it = self.it
        if it['tipo'] in ('motion', 'texto'):
            fr = self.dec.read()
            return fr if self.ah == OH else fr[:self.ah]
        src = self.img if self.img is not None else self.dec.read()
        p = (n - it['n0']) / max(1, it['n1'] - it['n0']); kb = float(EST['broll'].get('kenburns', 0.06)) if it.get('kenburns', 'in') != 'nenhum' else 0
        mode = it.get('kenburns', 'in'); z = 1 + kb * (ease_io(p) if mode in ('in', 'esq', 'dir', 'sobe', 'desce') else 1 - ease_io(p))
        s = max(self.aw / self.sw, self.ah / self.sh) * z
        fx, fy = it.get('foco', [0.5, 0.5])
        cx, cy = self.sw * fx, self.sh * fy
        mx, my = (self.sw - self.aw / s) / 2, (self.sh - self.ah / s) / 2      # folga sem mostrar borda
        pan = (ease_io(p) * 2 - 1) * 0.6
        if mode == 'esq': cx = self.sw / 2 + pan * mx
        elif mode == 'dir': cx = self.sw / 2 - pan * mx
        elif mode == 'sobe': cy = self.sh / 2 - pan * my
        elif mode == 'desce': cy = self.sh / 2 + pan * my
        cx = min(max(cx, self.aw / s / 2), self.sw - self.aw / s / 2); cy = min(max(cy, self.ah / s / 2), self.sh - self.ah / s / 2)
        M = np.float32([[s, 0, self.aw / 2 - s * cx], [0, s, self.ah / 2 - s * cy]])
        return cv2.warpAffine(src, M, (self.aw, self.ah), flags=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
    def close(self):
        if self.dec: self.dec.close()

class Overlay:
    def __init__(self, it):
        self.it = it; self.dec = Dec(P / it['render'], 0, f'scale={OW}:{OH}', OW, OH, alpha=True)
    def comp(self, base):
        fr = self.dec.read()
        if fr is None: return base
        a = fr[:, :, 3:4].astype(np.float32) * (1 / 255.0)
        if not a.any(): return base
        ys = np.where(a[:, :, 0].max(1) > 0)[0]; y0, y1 = ys[0], ys[-1] + 1   # só a faixa com conteúdo (rápido)
        b = base[y0:y1].astype(np.float32); f = fr[y0:y1, :, :3].astype(np.float32); aa = a[y0:y1]
        base[y0:y1] = (f * aa + b * (1 - aa) + 0.5).astype(np.uint8)
        return base
    def close(self): self.dec.close()

class Pessoa:
    """máscara da pessoa (MediaPipe selfie_segmenter, ~12 ms/quadro em 256 px) com suavização no tempo."""
    def __init__(self): self.seg = None; self.prev = None; self.falhou = False
    def ok(self):
        if self.seg or self.falhou: return not self.falhou
        try:
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core.base_options import BaseOptions
            mdl = E.models_dir() / 'selfie_segmenter.tflite'
            if not mdl.exists(): raise FileNotFoundError('rode modelos.py')
            self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=str(mdl)), output_confidence_masks=True, output_category_mask=False))
        except Exception as e:
            print(f"\n⚠ texto atrás da pessoa indisponível ({str(e)[:80]}) — pip install mediapipe; peças 'atras' vão por cima"); self.falhou = True
        return not self.falhou
    def mascara(self, bgr):
        import mediapipe as mp
        h = int(round(256 * bgr.shape[0] / bgr.shape[1])); sm = cv2.cvtColor(cv2.resize(bgr, (256, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        m = self.seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(sm))).confidence_masks[0].numpy_view().reshape(h, 256)
        m = cv2.GaussianBlur(cv2.resize(m, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR), (0, 0), 2.5)
        m = np.clip((m - 0.35) / 0.3, 0, 1).astype(np.float32)
        if self.prev is not None: m = 0.65 * m + 0.35 * self.prev
        self.prev = m; return m[..., None]
    def reset(self): self.prev = None
pessoa = Pessoa()

def face_half(full):
    """rosto para a metade de baixo do split: janela de OH/2 em volta dos olhos (camera põe os olhos em olhos_y)."""
    oy = EST['camera'].get('olhos_y', 0.36) * OH; y0 = int(min(max(0, oy - 0.38 * OH / 2), OH / 2))
    return full[y0:y0 + OH // 2]

class Papel:
    """textura de papel (fibras + grão), vinheta e borda desfocada — calculada uma vez por tamanho."""
    _c = {}
    def __new__(cls, w, h, forca=1.0):
        k = (w, h, forca)
        if k in cls._c: return cls._c[k]
        o = super().__new__(cls); cls._c[k] = o
        rng = np.random.default_rng(7)
        n1 = cv2.resize(rng.normal(0, 1, (h // 8 + 1, w // 8 + 1)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        fib = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sigmaX=5, sigmaY=0.7)
        gr = rng.normal(0, 1, (h, w)).astype(np.float32)
        tex = 1 + forca * (0.030 * n1 / (n1.std() + 1e-6) + 0.028 * fib / (fib.std() + 1e-6) + 0.018 * gr)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.4142
        vig = 1 - 0.50 * forca * np.clip((r - 0.30) / 0.70, 0, 1) ** 1.5
        o.mul = (tex * vig)[..., None] * np.array([0.975, 0.995, 1.02], np.float32)       # BGR: leve calor de papel
        o.edge = (np.clip((r - 0.42) / 0.50, 0, 1) ** 1.2 * 0.85)[..., None]
        o.w, o.h = w, h
        return o
    def aplica(self, fr):
        h, w = fr.shape[:2]
        sm = cv2.resize(fr, (max(2, w // 4), max(2, h // 4)), interpolation=cv2.INTER_AREA)
        bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 2.5), (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        f = fr.astype(np.float32); f = f * (1 - self.edge) + bl * self.edge
        g_ = f.mean(2, keepdims=True); f = f * 0.78 + g_ * 0.22                              # mais fosco: papel não combina com cor gritada
        return np.clip(f * self.mul + 3, 0, 255).astype(np.uint8)

def _hex_bgr(h):
    h = h.lstrip('#'); return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))
def _accent():
    return (B.get('marca') or {}).get('accent') or (EST.get('marca_padrao') or {}).get('accent') or '#FFD43B'
SPLIT_FIO = EST.get('split_fio')
if SPLIT_FIO == 'accent': SPLIT_FIO = _accent()
JAN = dict({'lado': 0.74, 'y': 0.57, 'raio': 0.045, 'anel': '#FFFFFF', 'anel_px': 6, 'quadros': 10}, **(EST.get('janela') or {}))
if JAN['anel'] == 'accent': JAN['anel'] = _accent()
_mask_c = {}
def _rmask(w, h, r):
    k = (w, h, int(r))
    if k not in _mask_c:
        m = np.zeros((h * 2, w * 2), np.uint8); rr = max(1, int(r * 2))
        cv2.rectangle(m, (rr, 0), (w * 2 - rr, h * 2), 255, -1); cv2.rectangle(m, (0, rr), (w * 2, h * 2 - rr), 255, -1)
        for cx_, cy_ in ((rr, rr), (w * 2 - rr, rr), (rr, h * 2 - rr), (w * 2 - rr, h * 2 - rr)): cv2.circle(m, (cx_, cy_), rr, 255, -1)
        _mask_c[k] = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255.0
    return _mask_c[k]
def _clip(x, y, w, h):
    """recorte seguro de um retângulo (x,y,w,h) na tela: (fatia destino, fatia origem) ou None."""
    x0, y0, x1, y1 = max(0, x), max(0, y), min(OW, x + w), min(OH, y + h)
    if x1 <= x0 or y1 <= y0: return None
    return (slice(y0, y1), slice(x0, x1)), (slice(y0 - y, y1 - y), slice(x0 - x, x1 - x))
def janela(bg, full, p):
    """câmera num cartão quadrado sobre o item (p 0 = quadro inteiro, 1 = cartão)."""
    e = ease_io(p); lado = JAN['lado'] * OW; ty = JAN['y'] * OH - lado / 2
    x0 = (OW - lado) / 2 * e; y0 = ty * e; w_ = int(round(OW + (lado - OW) * e)); h_ = int(round(OH + (lado - OH) * e))
    w_, h_ = max(8, w_), max(8, h_)
    oy = EST['camera'].get('olhos_y', 0.36) * OH; ch_ = min(OH, OW * h_ / w_)
    cy0 = min(max(0, oy - ch_ / 3), OH - ch_) if e > 0.02 else 0
    src = full[int(cy0):int(cy0) + max(1, int(ch_))] if e > 0.02 else full
    tile = cv2.resize(src, (w_, h_), interpolation=cv2.INTER_AREA).astype(np.float32)
    out = bg.copy().astype(np.float32); r = JAN['raio'] * OW * e
    m = _rmask(w_, h_, r); xi, yi = int(round(x0)), int(round(y0))
    if e > 0.02:     # sombra
        sh = np.zeros(out.shape[:2], np.float32); dy = int(18 * OW / 1080); c_ = _clip(xi, yi + dy, w_, h_)
        if c_: sh[c_[0]] = m[c_[1]][..., 0]
        sh = cv2.GaussianBlur(sh, (0, 0), 18 * OW / 1080) * 0.55 * e
        out *= (1 - sh[..., None])
    c_ = _clip(xi, yi, w_, h_)
    if c_: out[c_[0]] = tile[c_[1]] * m[c_[1]] + out[c_[0]] * (1 - m[c_[1]])
    if e > 0.02 and JAN['anel_px']:
        t_ = max(2, int(JAN['anel_px'] * OW / 1080)); ring = _rmask(w_ + 2 * t_, h_ + 2 * t_, r + t_).copy()
        ring[t_:t_ + h_, t_:t_ + w_] -= m; ring = np.clip(ring, 0, 1) * e
        c_ = _clip(xi - t_, yi - t_, w_ + 2 * t_, h_ + 2 * t_)
        if c_:
            col = np.array(_hex_bgr(JAN['anel']), np.float32); rg = ring[c_[1]]
            out[c_[0]] = col * rg + out[c_[0]] * (1 - rg)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)
QUEBRAS = [(nf(it['t_ini']), nf(it['t_fim'])) for it in mapa.get('itens', []) if (it.get('efeito') == 'quebra' or it.get('quebra')) and it.get('t_ini') is not None]
PBS = [(nf(it['t_ini']), nf(it['t_fim'])) for it in mapa.get('itens', []) if it.get('efeito') == 'pb' and it.get('t_ini') is not None]
_pour = None
def pb_cor(fr, n):
    """efeito "pb": o quadro inteiro em P&B; nos últimos 12 quadros a cor ESCORRE de cima para baixo (borda orgânica)."""
    global _pour
    for a, b in PBS:
        if a <= n < b:
            g_ = cv2.cvtColor(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR); k = b - n
            if k > 12: return g_
            if _pour is None:
                xs = np.linspace(0, 6 * np.pi, OW); _pour = (np.sin(xs * 1.3) * 0.5 + np.sin(xs * 0.45 + 1) * 0.35) * 0.06 * OH
            p_ = 1 - k / 12; frente = p_ * (OH * 1.15) + _pour - 0.08 * OH
            yy = np.arange(OH, dtype=np.float32)[:, None]; m = np.clip((frente[None, :] - yy) / (0.03 * OH), 0, 1)[..., None]
            return (fr.astype(np.float32) * m + g_.astype(np.float32) * (1 - m) + 0.5).astype(np.uint8)
    return fr
def quebra(fr):
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32); g = np.clip((g - 128) * 1.18 + 122, 0, 255)
    return cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR)
GRAO = float((EST.get('cor') or {}).get('grao', 0) or 0)
_grao = []
if GRAO > 0:
    rng_ = np.random.default_rng(11)
    for _ in range(6):
        z_ = rng_.normal(0, 1, (OH // 2, OW // 2)).astype(np.float32)
        _grao.append(cv2.resize(z_, (OW, OH), interpolation=cv2.INTER_LINEAR) * (GRAO * 255))
LGc = EST.get('legendas') or {}
FAIXA = bool(LGc.get('faixa_desfoque'))
if FAIXA:
    yc = float(LGc.get('y', 0.66)) * OH; hb = 0.26 * OH; yy = np.arange(OH, dtype=np.float32)
    d_ = np.clip(1 - np.abs(yy - yc) / (hb / 2), 0, 1); FMASK = (d_ * d_ * (3 - 2 * d_))[:, None, None]; FY0, FY1 = int(max(0, yc - hb / 2)), int(min(OH, yc + hb / 2))
def faixa_desfoque(fr):
    reg = fr[FY0:FY1]; sm = cv2.resize(reg, (max(2, reg.shape[1] // 4), max(2, reg.shape[0] // 4)), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3), (reg.shape[1], reg.shape[0]), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.62
    m = FMASK[FY0:FY1]; out = fr.copy(); out[FY0:FY1] = (bl * m + reg.astype(np.float32) * (1 - m) + 0.5).astype(np.uint8)
    return out

def escurece(fr, k):
    """fundo de 'legenda + UI': o vídeo atrás escurece (55%) e desfoca, com rampa k 0→1."""
    if k <= 0: return fr
    h, w = fr.shape[:2]
    sm = cv2.resize(fr, (max(2, w // 6), max(2, h // 6)), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3.0), (w, h), interpolation=cv2.INTER_LINEAR)
    d = cv2.addWeighted(bl, 0.45, np.zeros_like(bl), 0, 0)
    return cv2.addWeighted(fr, 1 - k, d, k, 0)

def transicao(tipo, a, b, p):
    """mistura do quadro que sai (a) para o que entra (b), p 0→1 ao longo da janela."""
    if tipo == 'fade': return cv2.addWeighted(a, 1 - ease_io(p), b, ease_io(p), 0)
    if tipo == 'flash':
        w = 1 - abs(p * 2 - 1); x = b if p >= 0.5 else a
        return cv2.addWeighted(x, 1 - 0.85 * w, np.full_like(x, 255), 0.85 * w, 0)
    if tipo == 'zoom':      # entra com zoom 1,12→1 e leve desfoque de movimento
        z = 1 + 0.12 * (1 - ease(p)); h, w = b.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, z); bb = cv2.warpAffine(b, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if p < 0.6: bb = cv2.addWeighted(bb, 0.6, cv2.warpAffine(b, cv2.getRotationMatrix2D((w / 2, h / 2), 0, z * 1.03), (w, h), borderMode=cv2.BORDER_REFLECT), 0.4, 0)
        return bb
    if tipo == 'whip':      # empurrão horizontal com borrão direcional
        h, w = a.shape[:2]; e = ease_io(p); off = int(e * w)
        cat = np.concatenate([a, b], 1)[:, off:off + w]
        k = int(6 + 60 * (1 - abs(p * 2 - 1))) | 1
        return cv2.blur(cat, (k, 1))
    if tipo == 'deslize':   # câmera desliza para baixo e revela o item (pinturas, B-roll com texto): empurrão vertical
        h, w = a.shape[:2]; e = ease_io(p); off = int(e * h)
        cat = np.concatenate([a, b], 0)[off:off + h]
        k = int(4 + 40 * (1 - abs(p * 2 - 1))) | 1
        return cv2.blur(cat, (1, k))
    return b
TRANS_N = {'fade': 6, 'flash': 4, 'zoom': 6, 'whip': 6, 'deslize': 9, 'corte': 0, 'recuo': 0}
TRAT = (EST.get('broll') or {}).get('tratamento')

# ── saída ──
estado = E.jload(P / '_edit/estado.json', {}) or {}
ver = int(opt('versao', estado.get('versao', 0) + (0 if RASC else 1)))
out = P / (opt('saida') or f"renders/_video_{'rascunho' if RASC else f'v{ver:02d}'}.mp4"); out.parent.mkdir(exist_ok=True)
vf = []
ass = P / '_edit/legendas.ass'
if ass.exists() and '--sem-legenda' not in A:
    fd = P / 'fonts'
    vf.append(f"ass='{ass.as_posix()}'" + (f":fontsdir='{fd.as_posix()}'" if fd.exists() else '') + (f":original_size={cam['w']}x{cam['h']}" if RASC else ''))
if n0 and vf and vf[0].startswith('ass='):      # render parcial (--de): a legenda precisa do tempo real da sequência
    vf[0] = f'setpts=PTS+{n0 / FPS:.6f}/TB,' + vf[0] + ',setpts=PTS-STARTPTS'
FIMF = float((EST.get('fim') or {}).get('fade_preto', 0) or 0)
if FIMF and not n0 and n1 >= N: vf.append(f"fade=t=out:st={max(0, n1 / FPS - FIMF):.3f}:d={FIMF:.3f}")   # entrevista: fecha no preto, legenda some junto
vf.append('format=yuv420p')
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', FPS_STR, '-i', '-',
                        '-vf', ','.join(vf), '-c:v', 'libx264', '-preset', 'ultrafast' if RASC else 'medium', '-crf', '23' if RASC else '17',
                        '-g', str(round(FPS) * 2), '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
                        '-movflags', '+faststart', '-an', str(out)], stdin=subprocess.PIPE)
ativos_f, ativos_o = {}, {}
import time; t0 = time.time()
# pula até n0 consumindo o A-roll (mantém o sincronismo dos decodificadores)
for n in range(n0, n1):
    full = aroll_frame(n); base = full
    # itens de tela cheia/split
    cobre = [it for it in ITENS if it['modo'] in ('tela_cheia', 'split', 'janela') and it['tipo'] in ('broll', 'foto', 'motion', 'texto') and it['n0'] <= n < it['n1']]
    for it in [x for x in ITENS if x['modo'] in ('tela_cheia', 'split', 'janela') and x['n0'] <= n < x['n1'] + TRANS_N.get(x.get('transicao', transp_padrao), 0)]:
        if it['id'] not in ativos_f: ativos_f[it['id']] = Fonte(it, (OW, OH // 2 if it['modo'] == 'split' else OH))
    for iid in [k for k, f in ativos_f.items() if n >= f.it['n1'] + TRANS_N.get(f.it.get('transicao', transp_padrao), 0)]:
        ativos_f.pop(iid).close()
    if cobre:
        it = cobre[0]; fr = ativos_f[it['id']].frame(n)
        if it.get('tratamento', TRAT if it['tipo'] in ('broll', 'foto') else None) == 'papel':
            fr = Papel(fr.shape[1], fr.shape[0], float(it.get('papel', 1.0))).aplica(fr)
        if it['modo'] == 'split':
            base = np.concatenate([fr, face_half(full)], 0)
            if SPLIT_FIO: cv2.line(base, (0, OH // 2), (OW, OH // 2), _hex_bgr(SPLIT_FIO), max(4, int(10 * OW / 1080)))
            else: cv2.line(base, (0, OH // 2), (OW, OH // 2), (20, 20, 20), max(2, OW // 360))
        elif it['modo'] == 'janela':
            qn = JAN['quadros']; base = janela(fr, full, min(1.0, (n - it['n0'] + 1) / qn, (it['n1'] - n) / qn))
        else: base = fr
        tp = it.get('transicao', transp_padrao); tn = 0 if it['modo'] == 'janela' else TRANS_N.get(tp, 0)
        if tn and n - it['n0'] < tn: base = transicao(tp, full, base, (n - it['n0'] + 1) / (tn + 1))
    else:
        # saída de um item: transição de volta ao rosto
        for it in ITENS:
            tp = it.get('transicao', transp_padrao); tn = TRANS_N.get(tp, 0)
            if it['modo'] in ('tela_cheia', 'split') and tn and it['n1'] <= n < it['n1'] + tn and it['id'] in ativos_f:
                fr = ativos_f[it['id']].frame(n)
                if it.get('tratamento', TRAT if it['tipo'] in ('broll', 'foto') else None) == 'papel':
                    fr = Papel(fr.shape[1], fr.shape[0], float(it.get('papel', 1.0))).aplica(fr)
                if it['modo'] == 'split': fr = np.concatenate([fr, face_half(full)], 0)
                base = transicao(tp, fr, full, (n - it['n1'] + 1) / (tn + 1)); break
    base = np.ascontiguousarray(base)
    if not cobre and any(a <= n < b for a, b in QUEBRAS): base = quebra(base)
    if FAIXA and not cobre: base = faixa_desfoque(base)
    # sobrepostos: primeiro os que vão ATRÁS da pessoa ("atras": true — texto atrás da cabeça), depois a pessoa volta
    # por cima (máscara MediaPipe), depois os normais. Só sobre o rosto (em tela cheia de B-roll não há pessoa).
    vivos = [x for x in ITENS if x['modo'] == 'sobreposto' and x['n0'] <= n < x['n1'] and '--sem-sobrepostos' not in A]
    for it in vivos:
        if it['id'] not in ativos_o: ativos_o[it['id']] = Overlay(it)
    for it in [x for x in vivos if x.get('fundo') == 'escurece']:
        rk = min(1.0, (n - it['n0'] + 1) / 6, (it['n1'] - n) / 6); base = escurece(base, max(0.0, rk))
    atras = [x for x in vivos if x.get('atras')]
    if atras and not cobre and pessoa.ok():
        pes = base.copy(); m = pessoa.mascara(pes)
        for it in atras: base = ativos_o[it['id']].comp(base)
        base = (pes.astype(np.float32) * m + base.astype(np.float32) * (1 - m) + 0.5).astype(np.uint8)
    else:
        for it in atras: base = ativos_o[it['id']].comp(base)
        if not atras: pessoa.reset()
    for it in [x for x in vivos if not x.get('atras')]:
        base = ativos_o[it['id']].comp(base)
    for iid in [k for k, o in ativos_o.items() if n >= o.it['n1']]: ativos_o.pop(iid).close()
    if PBS: base = pb_cor(base, n)
    if _grao: base = np.clip(base.astype(np.float32) + _grao[n % 6][..., None], 0, 255).astype(np.uint8)
    enc.stdin.write(base.tobytes())
    if (n - n0) % (round(FPS) * 2) == 0:
        el = time.time() - t0; print(f"\r  {n - n0}/{n1 - n0} quadros · {(n - n0 + 1) / max(el, 1e-3):.1f} q/s", end='', flush=True)
enc.stdin.close(); enc.wait()
for d in list(ativos_f.values()) + list(ativos_o.values()): d.close()
if aroll['dec']: aroll['dec'].close()
print(f"\n✔ {os.path.relpath(out, P)} · {OW}×{OH} · {(n1 - n0) / FPS:.1f}s · {time.time() - t0:.0f}s · cor {preset}{' + LUT' if LUT else ''}{' · nitidez (upscale %.2f×)' % up_max if nitidez else ''}")
