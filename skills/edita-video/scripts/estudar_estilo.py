#!/usr/bin/env python3
"""estudar_estilo.py — TREINA um estilo a partir de uma PASTA de edições de referência (método Joseph / LABS / Stockton).

    python3 estudar_estilo.py <pasta com vídeos> --nome <estilo> [--base minimal] [--kit <pasta do cliente>] [--saida <pasta>]

Para cada vídeo (mp4/mov/webm/m4v): cortes (scdet) e duração de plano, mudanças na tela (corte + pico de movimento),
trechos ANIMADOS (movimento alto e contínuo 0,25–2,5 s, que não é corte) com uma TIRA de 6 quadros de cada, presença de
rosto e linha dos olhos, paleta (k-means), saturação e luz. Junta tudo num PACOTE DE ESTILO:
  <saída>/REGRAS.md      livro de regras: números medidos + as 5 chaves para o Claude preencher olhando as folhas
                         (legenda · capítulos/listas · pops de UI e contadores · gancho · telas cheias), tipografia,
                         cantos, sombra, curvas e velocidades; e o TESTE DE FIDELIDADE (recriar 5–10 s lado a lado)
  <saída>/LOOKBOOK.jpg   paleta + quadros representativos      <saída>/planos/*.jpg   1 quadro por plano de cada vídeo
  <saída>/animacoes/*.jpg  tiras de quadros das animações + ANIMACOES.md (o que é, entrada, curva, onde no roteiro)
  <saída>/preset.json    rascunho do preset (herda de --base): ritmo medido, cor, punch — use com estilo=<nome>
Saída padrão: <kit do cliente>/estilos/<nome>/ (com --kit) ou ~/.config/orbe/estilos/<nome>/. O edita-video acha o
estilo pelo nome (evlib.estilo_proprio). Referência é para APRENDER A GRAMÁTICA — nunca copiar texto, marca ou peça.
"""
import sys, os, json, re, subprocess, shutil, math
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np
import cv2
from pathlib import Path

A = sys.argv[1:]
if not A or A[0].startswith('--'): E.die(__doc__)
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
SRC = Path(A[0]).expanduser().resolve(); NOME = opt('nome') or E.die('--nome <estilo> é obrigatório')
BASE = opt('base', 'minimal')
OUT = Path(opt('saida') or (Path(opt('kit')) / 'estilos' / NOME if opt('kit') else Path.home() / '.config/orbe/estilos' / NOME)).expanduser()
(OUT / 'planos').mkdir(parents=True, exist_ok=True); (OUT / 'animacoes').mkdir(exist_ok=True)
vids = sorted([f for f in SRC.iterdir() if f.suffix.lower() in ('.mp4', '.mov', '.webm', '.m4v', '.mkv')]) if SRC.is_dir() else [SRC]
if not vids: E.die(f'nenhum vídeo em {SRC}')
YU = E.models_dir() / 'yunet.onnx'
_hf = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
CASC = cv2.CascadeClassifier(_hf) if os.path.exists(_hf) else None
_yn = {}
def rostos(f):
    """[(x,y,w,h)] — YuNet (modelos.py baixa) ou Haar; sem nenhum, [] (as medidas de rosto ficam vazias)."""
    h, w = f.shape[:2]
    if YU.exists() and hasattr(cv2, 'FaceDetectorYN'):
        if (w, h) not in _yn: _yn[(w, h)] = cv2.FaceDetectorYN.create(str(YU), '', (w, h), 0.6, 0.3, 5000)
        _, fa = _yn[(w, h)].detect(f); return [tuple(int(v) for v in r[:4]) for r in (fa if fa is not None else [])]
    if CASC is not None and not CASC.empty():
        return list(CASC.detectMultiScale(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 1.1, 4, minSize=(int(w * 0.12),) * 2))
    return []

def frames(path, fps, w=200):
    """quadros pequenos em cinza + cor (para paleta), a `fps`."""
    cap = cv2.VideoCapture(str(path)); src_fps = cap.get(cv2.CAP_PROP_FPS) or 30; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, round(src_fps / fps)); out = []; i = 0
    while True:
        ok = cap.grab()
        if not ok: break
        if i % step == 0:
            ok, fr = cap.retrieve()
            if ok:
                h, w0 = fr.shape[:2]; sm = cv2.resize(fr, (w, int(h * w / w0)), interpolation=cv2.INTER_AREA)
                out.append((i / src_fps, sm))
        i += 1
    cap.release(); return out, src_fps

def grab(path, t, w=360):
    cap = cv2.VideoCapture(str(path)); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read(); cap.release()
    if not ok: return None
    h, w0 = fr.shape[:2]; return cv2.resize(fr, (w, int(h * w / w0)), interpolation=cv2.INTER_AREA)

def folha(imgs, cols, out, rotulos=None):
    imgs = [i for i in imgs if i is not None]
    if not imgs: return
    h, w = imgs[0].shape[:2]; rows = math.ceil(len(imgs) / cols); sh = np.full((rows * h, cols * w, 3), 18, np.uint8)
    for k, im in enumerate(imgs):
        im = cv2.resize(im, (w, h)); r, c = divmod(k, cols); sh[r * h:(r + 1) * h, c * w:(c + 1) * w] = im
        if rotulos: cv2.putText(sh, rotulos[k], (c * w + 8, r * h + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(str(out), sh, [cv2.IMWRITE_JPEG_QUALITY, 82])

TOT = {'dur': 0, 'cortes': [], 'planos': [], 'gaps': [], 'rosto': [], 'olhos': [], 'sat': [], 'luz': [], 'px': [], 'anim': []}
por_video = []
for vi, v in enumerate(vids):
    print(f'── {v.name}', flush=True)
    fr, sfps = frames(v, 10)
    if len(fr) < 5: print('  (curto demais)'); continue
    dur = fr[-1][0] + 0.1; TOT['dur'] += dur
    g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for _, f in fr]
    dif = np.array([0] + [float(np.mean(np.abs(g[k] - g[k - 1]))) for k in range(1, len(g))])
    ts = np.array([t for t, _ in fr])
    cut_thr = max(28.0, np.percentile(dif, 99) * 0.8)
    cortes = [ts[k] for k in range(1, len(dif)) if dif[k] > cut_thr and dif[k] > 3 * np.median(dif[max(0, k - 5):k + 5] + 1e-3)]
    cortes = [c for k, c in enumerate(cortes) if k == 0 or c - cortes[k - 1] > 0.25]
    bordas = [0.0] + cortes + [dur]; planos = [b - a for a, b in zip(bordas, bordas[1:]) if b - a > 0.05]
    # animação/evento: pico de movimento bem acima do "normal" daquele trecho (fala e gesto viram a linha de base) e que não é corte
    rm = np.array([np.median(dif[max(0, k - 7):k + 8]) for k in range(len(dif))]); sc = dif / (rm + 1.0)
    cand = [k for k in range(1, len(dif)) if sc[k] > 1.6 and dif[k] < cut_thr and dif[k] > 4]
    segs = []
    for k in sorted(cand, key=lambda k: -sc[k]):
        if all(abs(ts[k] - (a + 0.3)) > 1.0 for a, _, _ in segs) and all(abs(ts[k] - c) > 0.3 for c in cortes):
            segs.append((max(0.0, ts[k] - 0.3), min(dur, ts[k] + 0.6), float(sc[k])))
        if len(segs) >= 12: break
    segs.sort()
    mud = sorted(set([round(c, 2) for c in cortes] + [round(a, 2) for a, _, _ in segs]))
    gaps = [b - a for a, b in zip([0.0] + mud, mud + [dur]) if b - a > 0.05]
    # rosto e olhos (2 fps)
    ros = 0; olhos = []
    for t, f in fr[::5]:
        fa = rostos(f)
        if len(fa):
            ros += 1; x, y, w, h = max(fa, key=lambda r: r[2] * r[3]); olhos.append((y + 0.42 * h) / f.shape[0])
    hsv = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for _, f in fr[::10]]
    TOT['sat'] += [float(h_[..., 1].mean()) / 255 for h_ in hsv]; TOT['luz'] += [float(h_[..., 2].mean()) / 255 for h_ in hsv]
    for _, f in fr[::10]: TOT['px'].append(f.reshape(-1, 3)[::37])
    TOT['cortes'].append(len(cortes) / max(dur / 60, 1e-3)); TOT['planos'] += planos; TOT['gaps'] += gaps
    TOT['rosto'].append(ros / max(1, len(fr[::5]))); TOT['olhos'] += olhos
    # folhas
    folha([grab(v, (a + b) / 2, 240) for a, b in list(zip(bordas, bordas[1:]))[:30]], 6, OUT / 'planos' / f'{vi + 1:02d}_{v.stem[:30]}.jpg',
          [E.tc(a) for a, b in list(zip(bordas, bordas[1:]))[:30]])
    for si, (a, b, en) in enumerate(sorted(segs, key=lambda x: -x[2])[:8]):
        tira = [grab(v, a - 0.04 + (b - a + 0.12) * q / 5, 220) for q in range(6)]
        arq = OUT / 'animacoes' / f'{vi + 1:02d}_{si + 1:02d}.jpg'; folha(tira, 6, arq, [f'{a - 0.04 + (b - a + 0.12) * q / 5:.2f}s' for q in range(6)])
        TOT['anim'].append({'arquivo': arq.name, 'video': v.name, 'de': round(a, 2), 'dur': round(b - a, 2), 'intensidade': round(en, 1)})
    por_video.append({'video': v.name, 'dur': round(dur, 1), 'cortes_min': round(len(cortes) / max(dur / 60, 1e-3), 1), 'plano_med': round(float(np.median(planos)), 2) if planos else None,
                      'mudanca_med': round(float(np.median(gaps)), 2) if gaps else None, 'rosto': round(ros / max(1, len(fr[::5])), 2), 'animacoes': len(segs)})
    print(f"  {por_video[-1]}")

if not por_video: E.die('nenhum vídeo analisável')
px = np.concatenate(TOT['px']).astype(np.float32)
_, lab, cen = cv2.kmeans(px, 7, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
cnt = np.bincount(lab.ravel(), minlength=7); ordem = np.argsort(-cnt)
paleta = [('#%02X%02X%02X' % tuple(int(c) for c in cen[i][::-1]), round(float(cnt[i] / cnt.sum()), 3)) for i in ordem]
G = np.array(TOT['gaps']); PL = np.array(TOT['planos'])
sat, luz = float(np.mean(TOT['sat'])), float(np.mean(TOT['luz']))
med = {'videos': len(por_video), 'minutos': round(TOT['dur'] / 60, 1), 'cortes_por_min': round(float(np.median(TOT['cortes'])), 1),
       'plano_p50': round(float(np.median(PL)), 2), 'mudanca_p25': round(float(np.percentile(G, 25)), 2), 'mudanca_p75': round(float(np.percentile(G, 75)), 2),
       'parado_p95': round(float(np.percentile(G, 95)), 2), 'rosto_na_tela': round(float(np.mean(TOT['rosto'])), 2),
       'olhos_y': round(float(np.median(TOT['olhos'])), 2) if TOT['olhos'] else None, 'saturacao': round(sat, 2), 'luz': round(luz, 2), 'animacoes': len(TOT['anim'])}
cor = 'pb' if sat < 0.06 else 'fosco' if sat < 0.22 else 'punch' if sat > 0.42 else 'natural'
punch = 'linha' if med['mudanca_p25'] < 1.2 else 'tonicas' if med['mudanca_p25'] < 2.2 else 'viradas'
preset = {'base': BASE, 'nome': NOME,
          'ritmo': {'mudanca': [max(0.8, med['mudanca_p25']), max(1.5, med['mudanca_p75'])], 'parado_max': round(max(2.5, med['parado_p95']), 1), 'plano_min': 0.75, 'fim_max': 2.0},
          'cor': {'preset': cor}, 'camera': {'punch_modo': punch, **({'olhos_y': med['olhos_y']} if med['olhos_y'] and 0.25 < med['olhos_y'] < 0.5 else {})},
          '_medido': med, '_paleta': [c for c, _ in paleta]}
E.jsave(OUT / 'preset.json', preset)
# lookbook
sw = np.zeros((90, 1260, 3), np.uint8); x = 0
for c, p in paleta:
    w = max(40, int(1260 * p)) if c != paleta[-1][0] else 1260 - x
    sw[:, x:x + w] = tuple(int(c[i:i + 2], 16) for i in (5, 3, 1)); cv2.putText(sw, c, (x + 6, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255) if np.mean(sw[0, x]) < 128 else (0, 0, 0), 1, cv2.LINE_AA); x += w
    if x >= 1260: break
reps = [grab(v, 1.2, 210) for v in vids[:6]] + [grab(v, max(0.5, por_video[min(k, len(por_video) - 1)]['dur'] * 0.6), 210) for k, v in enumerate(vids[:6])]
reps = [r for r in reps if r is not None][:12]
if reps:
    hh = reps[0].shape[0]; linha = np.full((hh * 2, 1260, 3), 18, np.uint8)
    for k, r in enumerate(reps): r = cv2.resize(r, (210, hh)); linha[(k // 6) * hh:(k // 6 + 1) * hh, (k % 6) * 210:(k % 6 + 1) * 210] = r
    cv2.imwrite(str(OUT / 'LOOKBOOK.jpg'), np.concatenate([sw, linha], 0), [cv2.IMWRITE_JPEG_QUALITY, 85])
# documentos
R = [f'# Livro de regras — estilo "{NOME}"', '', f'Treinado em {med["videos"]} edição(ões) de referência ({med["minutos"]} min) · herda de `{BASE}` · preset: `preset.json`', '',
     '## Números medidos (não opinião)', '', '| medida | valor | vira no preset |', '|---|---|---|',
     f"| cortes por minuto (mediana) | {med['cortes_por_min']} | — |", f"| duração do plano (mediana) | {med['plano_p50']} s | cortes.pausa_max / ritmo |",
     f"| mudança na tela a cada | {med['mudanca_p25']}–{med['mudanca_p75']} s (p25–p75) | ritmo.mudanca |", f"| maior trecho parado (p95) | {med['parado_p95']} s | ritmo.parado_max |",
     f"| rosto na tela | {int(100 * med['rosto_na_tela'])}% do tempo | motion.por_minuto / tela cheia |", f"| linha dos olhos | {med['olhos_y'] or '—'} da altura | camera.olhos_y |",
     f"| saturação · luz | {med['saturacao']} · {med['luz']} | cor.preset = {cor} |", f"| trechos animados | {med['animacoes']} (tiras em animacoes/) | peças |", '',
     '| vídeo | dur | cortes/min | plano | mudança | rosto | animações |', '|---|---|---|---|---|---|---|',
     *[f"| {p['video'][:40]} | {p['dur']}s | {p['cortes_min']} | {p['plano_med']}s | {p['mudanca_med']}s | {int(100 * p['rosto'])}% | {p['animacoes']} |" for p in por_video], '',
     '## Paleta', '', ' · '.join(f'`{c}` {int(100 * p)}%' for c, p in paleta), '',
     '## As 5 chaves (preencha OLHANDO planos/ e animacoes/ — a gramática, nunca o conteúdo)', '',
     '1. **Legenda** — fontes (sans + destaque?), tamanho, caixa, palavras por linha, posição (terço?), fundo/faixa, entrada (pop, blur, máscara), palavra-chave (cor, caixa, serifa).',
     '2. **Capítulos e listas** — forma (losango, círculo, número), quando aparece (cedo, repetido ao citar), entrada.',
     '3. **Pops de UI e contadores** — notificação, anel, antes/depois, lista em vidro, pílula, slam: desenho, sombra, raio, duração no ar.',
     '4. **Gancho** — falante + texto + visual: onde ficam os olhos, que texto, que visual nos 2 s iniciais.',
     '5. **Telas cheias** — listicle com linha do tempo, cena única, texto com fundo contrastante, zoom para fora (janela), mapa/mesa.',
     '', '## Tipografia, cantos, sombra, curvas e velocidades', '', '- fontes:', '- raio dos cantos:', '- sombra:', '- entrada típica (quadros, curva):', '- saída típica:', '- junções (corte, zoom, flash, deslize…):',
     '', '## Teste de fidelidade (antes de usar em cliente)', '',
     '1. Escolha 5–10 s de UMA referência; recrie com o edita-video/motion-studio usando este estilo.',
     '2. Gere a prévia lado a lado (referência | recriação) e compare quadro a quadro: tamanhos, tempos, curvas, cor.',
     '3. Ajuste preset.json/REGRAS.md até ficar indistinguível na gramática. Só então o estilo vai para vídeo de cliente.']
(OUT / 'REGRAS.md').write_text('\n'.join(R) + '\n', encoding='utf-8')
AN = ['# Animações das referências', '', 'Cada tira = 6 quadros do trecho animado. Preencha: o que é · entrada (como chega) · curva/quadros · onde no roteiro (que batida).', '',
      '| tira | vídeo | em | dur | intensidade | o que é | entrada | curva | batida |', '|---|---|---|---|---|---|---|---|---|']
AN += [f"| animacoes/{a['arquivo']} | {a['video'][:30]} | {a['de']}s | {a['dur']}s | {a['intensidade']} |  |  |  |  |" for a in TOT['anim']]
(OUT / 'ANIMACOES.md').write_text('\n'.join(AN) + '\n', encoding='utf-8')
print(f"✔ pacote do estilo \"{NOME}\" em {OUT}\n  {json.dumps(med, ensure_ascii=False)}\n→ OLHE planos/*.jpg, animacoes/*.jpg e LOOKBOOK.jpg; preencha REGRAS.md e ANIMACOES.md; ajuste preset.json; faça o teste de fidelidade. Uso: briefing.py . estilo={NOME}")
