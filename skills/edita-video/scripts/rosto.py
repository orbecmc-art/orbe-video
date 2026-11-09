#!/usr/bin/env python3
"""rosto.py — rastreia o rosto em cada clipe (para reenquadrar 16:9 → 9:16 e travar a câmera no rosto).

    python3 rosto.py <projeto> [--passo 3] [--largura 640]

Detector: YuNet (OpenCV Zoo, ~/.cache/edita-video/yunet.onnx; baixe com modelos.py). Sem o modelo, Haar cascade
(frontal + perfil) que vem no OpenCV. Amostra 1 a cada --passo quadros numa cópia de --largura px (rápido e suficiente:
a câmera suaviza depois). Guarda o rosto PRINCIPAL (maior e mais central, com continuidade) por amostra:
  _edit/rosto/<clip>.json = {fps, w, h, amostras: [[t, cx, cy, fw, fh, olhos_y, score], …]}  (coordenadas do mezanino)
Sem rosto na amostra → linha com score 0 (a câmera mantém o último enquadramento bom).
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np, cv2

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
inv = E.jload(P / '_edit/inventario.json'); FPS = inv['fps']
PASSO = int(opt('passo', 3)); LW = int(opt('largura', 640))
OUT = P / '_edit/rosto'; OUT.mkdir(exist_ok=True)
model = E.models_dir() / 'yunet.onnx'
cv2.setLogLevel(2) if hasattr(cv2, 'setLogLevel') else None
usa_yunet = model.exists() and hasattr(cv2, 'FaceDetectorYN')
if not usa_yunet:
    haar_f = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    haar_p = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

for c in inv['clips']:
    W, H = c['w'], c['h']; lh = int(round(H * LW / W / 2) * 2); s = W / LW
    det = cv2.FaceDetectorYN.create(str(model), '', (LW, lh), 0.6, 0.3, 5000) if usa_yunet else None
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(P / c['mez']), '-vf', f"select='not(mod(n\\,{PASSO}))',scale={LW}:{lh}",
                             '-fps_mode', 'vfr', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    n = 0; prev = None; am = []; fb = LW * lh * 3
    while True:
        buf = proc.stdout.read(fb)
        if len(buf) < fb: break
        img = np.frombuffer(buf, np.uint8).reshape(lh, LW, 3)
        t = n * PASSO / FPS; n += 1
        cand = []
        if usa_yunet:
            _, faces = det.detect(img)
            for f in (faces if faces is not None else []):
                x, y, w, h = f[:4]; ey = (f[5] + f[7]) / 2; cand.append((x + w / 2, y + h / 2, w, h, ey, float(f[14])))
        else:
            g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); mn = int(0.04 * lh)
            for (x, y, w, h) in list(haar_f.detectMultiScale(g, 1.1, 4, minSize=(mn, mn))) + list(haar_p.detectMultiScale(g, 1.1, 4, minSize=(mn, mn))):
                cand.append((x + w / 2, y + h / 2, w, h, y + 0.40 * h, 0.7))
        if not cand:
            am.append([round(t, 3), 0, 0, 0, 0, 0, 0]); continue
        def nota(f):      # maior, mais central, e perto do rosto anterior (continuidade)
            area = f[2] * f[3] / (LW * lh); centro = 1 - abs(f[0] / LW - 0.5)
            cont = 1 - min(1, abs(f[0] - prev[0]) / (0.3 * LW)) if prev else 0.5
            return area * 4 + centro * 0.5 + cont + f[5] * 0.3
        b = max(cand, key=nota); prev = b
        am.append([round(t, 3)] + [round(float(v) * s, 1) for v in b[:5]] + [round(float(b[5]), 2)])
    proc.wait()
    ok = sum(1 for a in am if a[6] > 0)
    E.jsave(OUT / f"{c['id']}.json", {'fps': FPS, 'w': W, 'h': H, 'passo': PASSO, 'detector': 'yunet' if usa_yunet else 'haar', 'amostras': am})
    print(f"✔ {c['id']}: rosto em {ok}/{len(am)} amostras ({100 * ok / max(1, len(am)):.0f}%) · detector {'YuNet' if usa_yunet else 'Haar'}"
          + ('' if ok / max(1, len(am)) > 0.6 else ' ⚠ pouco rosto: reenquadramento vai usar o centro/saliência — confira'))
