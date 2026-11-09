#!/usr/bin/env python3
"""nle.py — EDITE ONDE QUISER: transforma a edição do Claude num kit aberto para Premiere, Final Cut, DaVinci Resolve,
CapCut e celular (Edits/CapCut mobile). O mesmo corte, a mesma câmera, o mesmo motion e o mesmo som — editáveis.

    python3 nle.py <projeto> [--para todos|premiere|finalcut|resolve|capcut|celular] [--alca 1.0] [--base <pasta no Mac>]
                   [--sem-zoom] [--legendas-fcp] [--versao 2]

O kit (entregas/<nome>_vNN_kit/) — tudo no tamanho e fps do projeto, então nenhum editor precisa reenquadrar nada:
  midia/s001.mov…   A-roll de cada trecho JÁ reenquadrado (câmera virtual: rosto, zoom alternado, punch) e com a cor do
                    estilo, voz limpa embutida, com ALÇA de --alca s de cada lado (dá para estender/aparar o corte).
                    --sem-zoom: só segue o rosto (zoom/punch ficam para o editor animar).
  midia/br01.mov…   cada cobertura (B-roll, foto com Ken Burns, split, cartela) pronta, 1 arquivo por item do mapa;
                    os originais ficam em midia/originais/ para quem quiser trocar.
  midia/mo01_alpha.mov…  peças de motion com transparência (ProRes 4444).
  midia/legendas_alpha.mov  as legendas no estilo do vídeo, com transparência (QuickTime Animation) + legendas.srt editável.
  midia/audio/      trilha.wav (ducking já feito) · sfx.wav · voz.wav · mix.wav (stems no nível final).
  midia/cor_<preset>.cube  o look do estilo como LUT · midia/guias/zonas_*.png  zonas da interface (Reels/TikTok/Shorts).
  midia/referencia_final.mp4  o render aprovado (faixa desligada no topo, para comparar).
Linhas do tempo: premiere/<nome>.xml (FCP7 XML: Premiere e Resolve) · <nome>.otio (Premiere 25.6+, Resolve 18.5+) ·
finalcut/<nome>.fcpxml (FCPXML 1.10, validado na DTD quando disponível) · resolve/ (OTIO + FCPXML + EDL) ·
capcut/<nome>/ (rascunho experimental via pyCapCut + roteiro de montagem) · celular/ (MP4 final, sem legenda, SRT).
Marcadores em todas as linhas do tempo: s001…, mo03…, br01…, sfx07… (o editor e o cliente falam pelo mesmo número).
--base: caminho ABSOLUTO onde o kit vai morar no computador do editor (ex.: /Users/gabriel/estudio/edicoes/x/entregas/
x_v01_kit). Sem ele, usa o caminho atual — certo quando o kit é gerado no próprio Mac. No outro caso o editor reconecta
a mídia (Premiere: Link Media · Final Cut: Relink Files · Resolve: Relink) apontando para midia/.
"""
import sys, os, re, json, shutil, subprocess, math
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np, cv2

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P)
PARA = set((opt('para') or 'todos').split(','))
if 'todos' in PARA: PARA = {'premiere', 'finalcut', 'resolve', 'capcut', 'celular'}
tl = E.jload(P / '_edit/timeline.json') or E.die('rode cortes.py antes')
cam = E.jload(P / '_edit/camera.json') or E.die('rode camera.py antes')
inv = E.jload(P / '_edit/inventario.json'); INV = {c['id']: c for c in inv['clips']}
mapa = E.jload(P / '_edit/mapa.json', {}) or {}
FPS = tl['fps']; FPS_STR = inv.get('fps_str', str(FPS))
FR = Fraction(FPS_STR) if '/' in FPS_STR else Fraction(FPS).limit_denominator(1001)
FD = 1 / FR                                  # duração de 1 quadro (racional)
OW, OH = cam['w'], cam['h']; DUR = tl['duracao']; NQ = len(cam['quadros'])
est = E.jload(P / '_edit/estado.json', {}) or {}
ver = int(opt('versao', est.get('versao', 1) or 1))
nome = B.get('nome') or re.sub(r'[^a-z0-9-]+', '-', P.name.lower()).strip('-') or 'video'
KIT = P / 'entregas' / f'{nome}_v{ver:02d}_kit'; MID = KIT / 'midia'
for d in (MID / 'audio', MID / 'originais', MID / 'guias'): d.mkdir(parents=True, exist_ok=True)
BASE = Path(opt('base') or KIT.resolve())
ALCA = float(opt('alca', 1.0)); SEM_ZOOM = '--sem-zoom' in A
nf = lambda t: int(round(t * FPS))
def caminho(p):                                         # caminho que o editor vai ver (no Mac dele)
    return BASE / Path(p).resolve().relative_to(KIT.resolve())
def url(p): return 'file://' + quote(str(caminho(p)))
log = []

# ───────────────────────── 1. MÍDIA ─────────────────────────
class Dec:
    def __init__(self, path, start, vf, w, h):
        self.w, self.h = w, h
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{max(0, start):.4f}', '-i', str(path), '-vf', (vf + ',' if vf else '') + f'fps={FPS_STR}',
                                   '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL); self.last = None
    def read(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3: self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass

R = OW / OH
def recorte_base(f, c):
    """--sem-zoom: o mesmo centro (segue o rosto), sem zoom/punch/push."""
    SW, SH = c['w'], c['h']; bw, bh = (SH * R, SH) if SW / SH > R else (SW, SW / R)
    cx = min(max(f['cx'], bw / 2), SW - bw / 2); cy = min(max(f['cy'], bh / 2), SH - bh / 2)
    return dict(f, cx=cx, cy=cy, cw=bw, ch=bh)

PISO = {}
def piso(clip):
    if clip not in PISO:
        x = E.load_wav(P / '_edit/audio' / f'{clip}.wav', 48000); env = E.rms_env(x, 48000, 0.05)
        PISO[clip] = E.db(float(np.percentile(env[env > 1e-6], 5))) if (env > 1e-6).any() else -90
    return PISO[clip]

SEGS = []
def midia_trechos():
    quadros = cam['quadros']
    for k, s in enumerate(tl['segmentos']):
        c = INV[s['clip']]; ns = [n for n in range(NQ) if quadros[n]['k'] == k]
        if not ns: continue
        pre = min(nf(ALCA), int(s['src_in'] * FPS)); post = min(nf(ALCA), max(0, int((c['dur'] - s['src_out']) * FPS) - 1))
        total = pre + len(ns) + post; t0 = s['src_in'] - pre / FPS
        out = MID / f"{s['id']}.mov"; SEGS.append({'id': s['id'], 'arq': out, 'pre': pre, 'n': len(ns), 'post': post, 'seq0': ns[0], 'clip': s['clip'], 'texto': s.get('texto', '')})
        if out.exists() and '--refazer' not in A: continue
        dec = Dec(P / c['mez'], t0, E.cadeia_cor(P, EST, P / c['mez'], c['dur']), c['w'], c['h'])
        af = E.cadeia_voz(EST, piso(s['clip'])) if c['audio'] else ''
        cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', FPS_STR, '-i', '-']
        if c['audio']:
            cmd += ['-ss', f'{t0:.4f}', '-t', f'{total / FPS:.4f}', '-i', str(P / '_edit/audio' / f"{s['clip']}.wav")]
        cmd += ['-map', '0:v'] + (['-map', '1:a', '-af', (af + ',' if af else '') + 'aresample=48000', '-c:a', 'pcm_s16le', '-ar', '48000'] if c['audio'] else [])
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-g', str(round(FPS)), '-color_primaries', 'bt709',
                '-color_trc', 'bt709', '-colorspace', 'bt709', '-t', f'{total / FPS:.4f}', str(out)]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for j in range(total):
            n = ns[0] if j < pre else ns[-1] if j >= pre + len(ns) else ns[j - pre]
            f = quadros[n]; f = recorte_base(f, c) if SEM_ZOOM else f
            img = dec.read()
            sx, sy = OW / f['cw'], OH / f['ch']; x0, y0 = f['cx'] - f['cw'] / 2, f['cy'] - f['ch'] / 2
            M = np.float32([[sx, 0, -x0 * sx], [0, sy, -y0 * sy]])
            fr = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
            if OH / f['ch'] > 1.4: bl = cv2.GaussianBlur(fr, (0, 0), 1.2); fr = cv2.addWeighted(fr, 1.35, bl, -0.35, 0)
            enc.stdin.write(fr.tobytes())
        enc.stdin.close(); enc.wait(); dec.close()
        print(f"  ✔ {out.name} ({len(ns) / FPS:.2f}s + alças {pre / FPS:.1f}/{post / FPS:.1f}s)", flush=True)

COB = []
def midia_coberturas():
    itens = [it for it in mapa.get('itens', []) if it.get('t_ini') is not None and it.get('modo') in ('tela_cheia', 'split')
             and (it.get('arquivo') or it.get('render'))]
    if not itens: return
    base = MID / '_base.mp4'
    if all((MID / f"{it['id']}.mov").exists() for it in itens) and '--refazer' not in A:      # já recortadas
        for it in itens: COB.append({'id': it['id'], 'arq': MID / f"{it['id']}.mov", 'a': nf(it['t_ini']), 'b': nf(it['t_fim']), 'desc': it['tipo']})
        return
    if not base.exists() or '--refazer' in A:
        print('  · render de base (sem legenda e sem peças sobrepostas) para recortar as coberturas…', flush=True)
        r = subprocess.run([sys.executable, str(E.SKILL / 'scripts/compor.py'), str(P), '--sem-legenda', '--sem-sobrepostos', '--saida', str(base)], capture_output=True, text=True)
        if r.returncode: print(r.stderr[-600:]); return
    for it in itens:
        a, b = nf(it['t_ini']), nf(it['t_fim']); out = MID / f"{it['id']}.mov"
        E.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{a / FPS:.4f}', '-i', str(base), '-frames:v', str(b - a), '-an', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
               '-pix_fmt', 'yuv420p', '-g', str(round(FPS)), str(out)])
        COB.append({'id': it['id'], 'arq': out, 'a': a, 'b': b, 'desc': f"{it['tipo']} {it.get('modo')} {it.get('busca') or it.get('texto') or ''}".strip()})
        orig = it.get('arquivo')
        if orig and (P / orig).exists(): shutil.copy(P / orig, MID / 'originais' / Path(orig).name)
    print(f'  ✔ {len(COB)} cobertura(s) recortadas do render de base (originais em midia/originais/)', flush=True)

MOT = []
def midia_motion():
    for it in mapa.get('itens', []):
        if it.get('modo') != 'sobreposto' or not it.get('render') or it.get('t_ini') is None: continue
        src = P / it['render']
        if not src.exists(): continue
        out = MID / src.name; shutil.copy(src, out)
        MOT.append({'id': it['id'], 'arq': out, 'a': nf(it['t_ini']), 'b': nf(it['t_fim']), 'desc': f"{it.get('peca', '')} {it.get('texto') or ''}".strip()})
    if MOT: print(f'  ✔ {len(MOT)} peça(s) de motion com alfa', flush=True)

LEG = {}
def midia_legendas():
    ass = P / '_edit/legendas.ass'
    if not ass.exists(): return
    out = MID / 'legendas_alpha.mov'; fd = P / 'fonts'
    if not out.exists() or '--refazer' in A:
        # o libass não escreve alfa: renderiza sobre preto e sobre branco e tira a transparência da diferença (exato)
        def src(cor):
            vf = f"ass='{ass.as_posix()}'" + (f":fontsdir='{fd.as_posix()}'" if fd.exists() else '')
            return subprocess.Popen(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=c={cor}:s={OW}x{OH}:r={FPS_STR}:d={DUR:.4f}', '-vf', vf,
                                     '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        pb, pw = src('black'), src('white'); fb = OW * OH * 3
        enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{OW}x{OH}', '-r', FPS_STR, '-i', '-',
                                '-c:v', 'qtrle', '-pix_fmt', 'argb', str(out)], stdin=subprocess.PIPE)
        vazio = np.zeros((OH, OW, 4), np.uint8).tobytes()
        while True:
            a, b = pb.stdout.read(fb), pw.stdout.read(fb)
            if len(a) < fb or len(b) < fb: break
            k = np.frombuffer(a, np.uint8).reshape(OH, OW, 3); w = np.frombuffer(b, np.uint8).reshape(OH, OW, 3)
            if not k.any(): enc.stdin.write(vazio); continue
            al = 255 - (w.astype(np.int16) - k.astype(np.int16)).max(2).clip(0, 255)
            rgb = np.where(al[..., None] > 0, (k.astype(np.float32) * 255 / np.maximum(al[..., None], 1)).clip(0, 255), 0).astype(np.uint8)
            enc.stdin.write(np.dstack([rgb, al.astype(np.uint8)]).tobytes())
        enc.stdin.close(); enc.wait(); pb.kill(); pw.kill()
    LEG['alpha'] = out
    srt = sorted((P / 'renders').glob(f'*_v{ver:02d}.srt')) or sorted((P / 'renders').glob('*_v[0-9][0-9].srt'))
    if srt: shutil.copy(srt[-1], MID / 'legendas.srt'); LEG['srt'] = MID / 'legendas.srt'
    print('  ✔ legendas_alpha.mov (estilo do vídeo, transparente) + legendas.srt (editável)', flush=True)

AUD = {}
def midia_audio():
    for nm in ('trilha', 'sfx', 'voz', 'mix'):
        f = P / 'audio' / f'{nm}.wav'
        if f.exists() and (nm != 'trilha' or np.abs(E.load_wav(f, 8000)).max() > 1e-4) and (nm != 'sfx' or np.abs(E.load_wav(f, 8000)).max() > 1e-4):
            shutil.copy(f, MID / 'audio' / f.name); AUD[nm] = MID / 'audio' / f.name
    if (P / 'audio/sfx_cues.json').exists(): shutil.copy(P / 'audio/sfx_cues.json', MID / 'audio/sfx_cues.json')
    print(f"  ✔ stems: {', '.join(AUD)}", flush=True)

def midia_lut():
    """o look do estilo como LUT 33³ (.cube) — os filtros de cor são pontuais, então aplicar no cubo identidade é exato."""
    preset = (EST.get('cor') or {}).get('preset', 'natural'); g = E.GRADES.get(preset, '')
    if not g: return None
    N = 33; v = np.round(np.arange(N) * 255 / (N - 1)).astype(np.uint8)
    r_, g_, b_ = np.meshgrid(v, v, v, indexing='ij')            # índice [r, g, b]
    cubo = np.stack([r_.transpose(2, 1, 0).ravel(), g_.transpose(2, 1, 0).ravel(), b_.transpose(2, 1, 0).ravel()], 1)   # r mais rápido (padrão .cube)
    img = cubo.reshape(N * N, N, 3); src = MID / '_id.png'; dst = MID / '_lut.png'
    cv2.imwrite(str(src), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-vf', g + ',format=rgb24', '-frames:v', '1', str(dst)])
    out_ = cv2.cvtColor(cv2.imread(str(dst)), cv2.COLOR_BGR2RGB).reshape(-1, 3) / 255.0
    out = MID / f'cor_{preset}.cube'
    with open(out, 'w') as fh:
        fh.write(f'TITLE "Orbe {preset}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for x in out_: fh.write(f'{x[0]:.6f} {x[1]:.6f} {x[2]:.6f}\n')
    src.unlink(); dst.unlink(); print(f'  ✔ {out.name} (o look "{preset}" como LUT 33³ para clipes novos)', flush=True)
    return out

def midia_guias():
    if OH <= OW: return
    plat = {'reels': (0.14, 0.22, 0.12), 'tiktok': (0.12, 0.25, 0.16), 'shorts': (0.12, 0.20, 0.14)}
    for nm, (topo, base, dir_) in plat.items():
        im = np.zeros((OH, OW, 4), np.uint8); cor = (60, 60, 255, 90)
        im[:int(topo * OH)] = cor; im[int((1 - base) * OH):] = cor; im[int(0.45 * OH):, int((1 - dir_) * OW):] = cor
        cv2.putText(im, f'{nm.upper()} - zona da interface (fora daqui: legenda, texto, rosto)', (30, int(topo * OH) - 24), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255, 230), 2, cv2.LINE_AA)
        cv2.imwrite(str(MID / 'guias' / f'zonas_{nm}.png'), im)
    print('  ✔ guias de zona segura (Reels, TikTok, Shorts) em PNG transparente', flush=True)

REF = {}
def midia_referencia():
    r = sorted((P / 'renders').glob(f'*_v{ver:02d}.mp4')) or sorted((P / 'renders').glob('*_v[0-9][0-9].mp4'))
    if r: shutil.copy(r[-1], MID / 'referencia_final.mp4'); REF['arq'] = MID / 'referencia_final.mp4'

# ───────────────────────── 2. LINHA DO TEMPO (modelo comum) ─────────────────────────
def marcadores():
    m = [(SEGS[0]['seq0'] if SEGS else 0, 'início', 'gancho: 2 s iniciais')] if SEGS else []
    for s in SEGS[1:]: m.append((s['seq0'], s['id'], (s['texto'] or '')[:60]))
    for it in mapa.get('itens', []):
        if it.get('t_ini') is None: continue
        pr = it.get('params', {}); txt = it.get('texto') or pr.get('nome') or pr.get('palavra') or ' / '.join(pr.get('itens', [])) or it.get('busca') or ''
        m.append((nf(it['t_ini']), it['id'], f"{it.get('peca') or it['tipo']} {it.get('modo', '')} {txt}".strip()[:80]))
    for c in (E.jload(P / '_edit/eventos_sfx.json', {}) or {}).get('cues', []): m.append((nf(c['t']), c['id'], f"som {c['type']} ← {c['origem']}"))
    for p in cam.get('punch', []): m.append((nf(p['t']), 'punch', f"punch-in «{p['palavra']}»"))
    return sorted(m, key=lambda x: x[0])
def faixas():
    """V1 A-roll · V2 cobertura · V3 motion · V4 legendas · V5 referência (desligada) · A1 voz (nos trechos) · A2 trilha · A3 sfx"""
    v1 = [{'arq': s['arq'], 'em': s['seq0'], 'ini': s['pre'], 'n': s['n'], 'nome': s['id'], 'audio': True} for s in SEGS]
    v2 = [{'arq': c['arq'], 'em': c['a'], 'ini': 0, 'n': c['b'] - c['a'], 'nome': c['id']} for c in COB]
    v3 = [{'arq': m['arq'], 'em': m['a'], 'ini': 0, 'n': m['b'] - m['a'], 'nome': m['id']} for m in MOT]
    v4 = [{'arq': LEG['alpha'], 'em': 0, 'ini': 0, 'n': NQ, 'nome': 'legendas'}] if LEG.get('alpha') else []
    v5 = [{'arq': REF['arq'], 'em': 0, 'ini': 0, 'n': NQ, 'nome': 'referência final', 'off': True}] if REF.get('arq') else []
    a2 = [{'arq': AUD['trilha'], 'em': 0, 'ini': 0, 'n': NQ, 'nome': 'trilha'}] if AUD.get('trilha') else []
    a3 = [{'arq': AUD['sfx'], 'em': 0, 'ini': 0, 'n': NQ, 'nome': 'sfx'}] if AUD.get('sfx') else []
    return {'V1': v1, 'V2': v2, 'V3': v3, 'V4': v4, 'V5': v5, 'A2': a2, 'A3': a3}

PROBE = {}
def probe(p):
    if p not in PROBE:
        pr = E.ffprobe(p); v = next((s for s in pr['streams'] if s['codec_type'] == 'video'), None); a = next((s for s in pr['streams'] if s['codec_type'] == 'audio'), None)
        PROBE[p] = {'dur': float(pr['format']['duration']), 'w': int(v['width']) if v else 0, 'h': int(v['height']) if v else 0,
                    'video': bool(v), 'audio': bool(a), 'ch': int(a.get('channels', 2)) if a else 0, 'nq': int(round(float(pr['format']['duration']) * FPS))}
    return PROBE[p]

# ───────────────────────── 3. FORMATOS ─────────────────────────
def t(nq):          # quadros → tempo racional FCPXML
    x = nq * FD
    return '0s' if x == 0 else (f'{x.numerator}s' if x.denominator == 1 else f'{x.numerator}/{x.denominator}s')

def escreve_fcpxml(dest, versao='1.10'):
    F = faixas(); res = []; ids = {}
    def rid(): return f'r{len(res) + 2}'
    res.append(f'<format id="r1" frameDuration="{t(1)}" width="{OW}" height="{OH}" colorSpace="1-1-1 (Rec. 709)"/>')
    def asset(p, audio_only=False):
        p = Path(p)
        if p in ids: return ids[p]
        i = probe(p); a = rid(); ids[p] = a
        attrs = f'id="{a}" name="{escape(p.stem)}" start="0s" duration="{t(i["nq"])}" hasVideo="{1 if i["video"] and not audio_only else 0}" hasAudio="{1 if i["audio"] else 0}"'
        if i['video'] and not audio_only: attrs += ' format="r1" videoSources="1"'
        if i['audio']: attrs += f' audioSources="1" audioChannels="{i["ch"]}" audioRate="48000"'
        res.append(f'<asset {attrs}><media-rep kind="original-media" src="{escape(url(p))}"/></asset>')
        return a
    spine = []; marks = marcadores(); filhos = {k: [] for k in range(len(F['V1']))}; mk = {k: [] for k in range(len(F['V1']))}
    def pai(nq):
        for k, c in enumerate(F['V1']):
            if c['em'] <= nq < c['em'] + c['n']: return k
        return len(F['V1']) - 1
    def local(k, nq): c = F['V1'][k]; return c['ini'] + (nq - c['em'])
    for lane, nomef, role in ((1, 'V2', None), (2, 'V3', None), (3, 'V4', None), (4, 'V5', None), (-1, 'A2', 'music'), (-2, 'A3', 'effects')):
        for c in F[nomef]:
            k = pai(c['em']); a = asset(c['arq'], audio_only=nomef.startswith('A'))
            attr = f'ref="{a}" lane="{lane}" offset="{t(local(k, c["em"]))}" name="{escape(c["nome"])}" start="{t(c["ini"])}" duration="{t(c["n"])}"'
            if role: attr += f' audioRole="{role}"'
            elif nomef in ('V2', 'V3', 'V4', 'V5'): attr += ' srcEnable="video"' if probe(c['arq'])['audio'] else ''
            if c.get('off'): attr += ' enabled="0"'
            filhos[k].append(f'<asset-clip {attr}/>')
    if '--legendas-fcp' in A and LEG.get('srt'):
        for i, (a_, b_, txt) in enumerate(_srt(LEG['srt'])):
            k = pai(nf(a_)); filhos[k].append(f'<caption lane="5" offset="{t(local(k, nf(a_)))}" name="L{i + 1:03d}" duration="{t(max(1, nf(b_) - nf(a_)))}" role="SRT?captionFormat=SRT.pt-BR"><text placement="bottom"><text-style ref="ts1">{escape(txt)}</text-style></text>' + ('<text-style-def id="ts1"><text-style font=".AppleSystemUIFont" fontSize="13" fontFace="Regular" fontColor="1 1 1 1" backgroundColor="0 0 0 1"/></text-style-def>' if i == 0 else '') + '</caption>')
    for nq, iid, txt in marks:
        k = pai(nq); mk[k].append(f'<marker start="{t(local(k, nq))}" duration="{t(1)}" value="{escape(iid + " · " + txt)}"/>')
    for k, c in enumerate(F['V1']):
        a = asset(c['arq'])
        spine.append(f'<asset-clip ref="{a}" offset="{t(c["em"])}" name="{escape(c["nome"])}" start="{t(c["ini"])}" duration="{t(c["n"])}" tcFormat="NDF" audioRole="dialogue">'
                     + ''.join(filhos[k]) + ''.join(mk[k]) + '</asset-clip>')
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="{versao}">\n<resources>\n' + '\n'.join(res) + '\n</resources>\n'
           f'<library>\n<event name="Orbe · {escape(nome)}">\n<project name="{escape(nome)} v{ver:02d}">\n'
           f'<sequence format="r1" duration="{t(NQ)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">\n<spine>\n'
           + '\n'.join(spine) + '\n</spine>\n</sequence>\n</project>\n</event>\n</library>\n</fcpxml>\n')
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(xml, encoding='utf-8')
    dtd = E.models_dir() / f"FCPXMLv{versao.replace('.', '_')}.dtd"
    if dtd.exists() and shutil.which('xmllint'):
        r = subprocess.run(['xmllint', '--noout', '--dtdvalid', str(dtd), str(dest)], capture_output=True, text=True)
        log.append(f"FCPXML {versao}: {'✔ válido na DTD da Apple' if r.returncode == 0 else '✗ DTD: ' + r.stderr.strip()[:300]}")
    else: log.append(f'FCPXML {versao}: gerado (sem DTD local para validar — rode modelos.py)')

def _srt(p):
    out = []; txt = Path(p).read_text(encoding='utf-8').strip().split('\n\n')
    for bl in txt:
        ls = bl.strip().splitlines()
        if len(ls) < 3: continue
        m = re.findall(r'(\d+):(\d+):(\d+),(\d+)', ls[1])
        if len(m) < 2: continue
        sec = lambda g: int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        out.append((sec(m[0]), sec(m[1]), ' '.join(ls[2:])))
    return out

def escreve_xmeml(dest):
    F = faixas(); ntsc = abs(FPS - round(FPS)) > 0.01; tb = round(FPS)
    RATE = f'<rate><timebase>{tb}</timebase><ntsc>{"TRUE" if ntsc else "FALSE"}</ntsc></rate>'
    vistos = set()
    def arq(p, fid):
        i = probe(p)
        if fid in vistos: return f'<file id="{fid}"/>'
        vistos.add(fid); med = ''
        if i['video']: med += f'<video><samplecharacteristics>{RATE}<width>{i["w"]}</width><height>{i["h"]}</height></samplecharacteristics></video>'
        if i['audio']: med += f'<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>{i["ch"]}</channelcount></audio>'
        return f'<file id="{fid}"><name>{escape(Path(p).name)}</name><pathurl>{escape("file://localhost" + quote(str(caminho(p))))}</pathurl>{RATE}<duration>{i["nq"]}</duration><media>{med}</media></file>'
    def item(c, cid, kind='video', on=True):
        p = c['arq']; fid = 'f-' + Path(p).stem; i = probe(p)
        st = f'<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>' if kind == 'audio' else ''
        return (f'<clipitem id="{cid}"><name>{escape(c["nome"])}</name><enabled>{"TRUE" if on and not c.get("off") else "FALSE"}</enabled><duration>{i["nq"]}</duration>{RATE}'
                f'<start>{c["em"]}</start><end>{c["em"] + c["n"]}</end><in>{c["ini"]}</in><out>{c["ini"] + c["n"]}</out>{arq(p, fid)}{st}</clipitem>')
    tr = lambda xs: f'<track>{"".join(xs)}</track>'
    V = [tr([item(c, f'{k}-{j}') for j, c in enumerate(F[k])]) for k in ('V1', 'V2', 'V3', 'V4', 'V5') if F[k]]
    Au = [tr([item(c, f'A1-{j}', 'audio') for j, c in enumerate(F['V1'])])] + [tr([item(c, f'{k}-{j}', 'audio') for j, c in enumerate(F[k])]) for k in ('A2', 'A3') if F[k]]
    MK = ''.join(f'<marker><name>{escape(i)}</name><comment>{escape(x)}</comment><in>{n}</in><out>-1</out></marker>' for n, i, x in marcadores())
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5"><sequence id="seq-1">'
           f'<name>{escape(nome)} v{ver:02d}</name><duration>{NQ}</duration>{RATE}<media><video><format><samplecharacteristics>{RATE}'
           f'<width>{OW}</width><height>{OH}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>'
           + ''.join(V) + '</video><audio>' + ''.join(Au) + '</audio></media>' + MK + '</sequence></xmeml>\n')
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(xml, encoding='utf-8')
    import xml.dom.minidom as mdm; mdm.parse(str(dest)); log.append(f'XML Premiere/Resolve (FCP7): ✔ {dest.relative_to(KIT)}')

def escreve_otio(dest):
    try: import opentimelineio as otio
    except ImportError: log.append('OTIO: pule (pip install opentimelineio)'); return
    F = faixas(); rate = float(FR)
    tlo = otio.schema.Timeline(name=f'{nome} v{ver:02d}'); tlo.global_start_time = otio.opentime.RationalTime(0, rate)
    def faixa(itens, kind, nm):
        trk = otio.schema.Track(name=nm, kind=kind); cur = 0
        for c in sorted(itens, key=lambda c: c['em']):
            if c['em'] > cur: trk.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(duration=otio.opentime.RationalTime(c['em'] - cur, rate))))
            ref = otio.schema.ExternalReference(target_url=url(c['arq']), available_range=otio.opentime.TimeRange(otio.opentime.RationalTime(0, rate), otio.opentime.RationalTime(probe(c['arq'])['nq'], rate)))
            cl = otio.schema.Clip(name=c['nome'], media_reference=ref, source_range=otio.opentime.TimeRange(otio.opentime.RationalTime(c['ini'], rate), otio.opentime.RationalTime(c['n'], rate)))
            if c.get('off'): cl.enabled = False
            trk.append(cl); cur = c['em'] + c['n']
        return trk
    for k, nm in (('V1', 'V1 A-roll'), ('V2', 'V2 cobertura'), ('V3', 'V3 motion'), ('V4', 'V4 legendas'), ('V5', 'V5 referência')):
        if F[k]: tlo.tracks.append(faixa(F[k], otio.schema.TrackKind.Video, nm))
    tlo.tracks.append(faixa(F['V1'], otio.schema.TrackKind.Audio, 'A1 voz'))
    for k, nm in (('A2', 'A2 trilha'), ('A3', 'A3 sfx')):
        if F[k]: tlo.tracks.append(faixa(F[k], otio.schema.TrackKind.Audio, nm))
    for n, i, x in marcadores():
        tlo.tracks[0].markers.append(otio.schema.Marker(name=f'{i} · {x}', marked_range=otio.opentime.TimeRange(otio.opentime.RationalTime(n, rate), otio.opentime.RationalTime(1, rate)), color=otio.schema.MarkerColor.YELLOW))
    dest.parent.mkdir(parents=True, exist_ok=True); otio.adapters.write_to_file(tlo, str(dest)); log.append(f'OTIO: ✔ {dest.relative_to(KIT)}')

def escreve_edl(dest):
    tb = round(FPS)
    def tcf(n): fr = n % tb; s = n // tb; return f'{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{fr:02d}'
    L = [f'TITLE: {nome} v{ver:02d}', 'FCM: NON-DROP FRAME', '']
    for k, c in enumerate(faixas()['V1']):
        L += [f"{k + 1:03d}  {c['nome'].upper()[:8]:<8} AA/V  C        {tcf(c['ini'])} {tcf(c['ini'] + c['n'])} {tcf(c['em'])} {tcf(c['em'] + c['n'])}", f"* FROM CLIP NAME: {Path(c['arq']).name}", '']
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text('\n'.join(L), encoding='utf-8')

def escreve_capcut(pasta):
    """Rascunho do CapCut desktop via pyCapCut (experimental — o formato muda a cada versão). Legenda vai NATIVA
    (importada do SRT, editável no CapCut) em vez da camada transparente."""
    pasta.mkdir(parents=True, exist_ok=True)
    try: import pycapcut as cc
    except ImportError: log.append('CapCut: rascunho pulado (pip install pycapcut pymediainfo) — use o roteiro de montagem'); return
    F = faixas(); df = cc.DraftFolder(str(pasta)); nomed = f'{nome}_v{ver:02d}'
    sc = df.create_draft(nomed, OW, OH, fps=round(FPS), allow_replace=True)
    us = lambda nq: int(round(nq / FPS * 1_000_000))
    tr_ = lambda em, n: cc.Timerange(us(em), us(em + n) - us(em))      # fim arredondado uma vez só: sem sobreposição de 1 µs
    sc.add_track(cc.TrackType.video, 'A-roll')
    for c in F['V1']: sc.add_segment(cc.VideoSegment(str(c['arq']), tr_(c['em'], c['n']), source_timerange=cc.Timerange(us(c['ini']), us(c['em'] + c['n']) - us(c['em']))), 'A-roll')
    for k, nm in (('V2', 'cobertura'), ('V3', 'motion')):
        if F[k]:
            sc.add_track(cc.TrackType.video, nm, relative_index=1 if k == 'V2' else 2)
            for c in F[k]: sc.add_segment(cc.VideoSegment(str(c['arq']), tr_(c['em'], c['n']), source_timerange=cc.Timerange(0, us(c['em'] + c['n']) - us(c['em']))), nm)
    for k, nm in (('A2', 'trilha'), ('A3', 'sfx')):
        if F[k]:
            sc.add_track(cc.TrackType.audio, nm)
            for c in F[k]: sc.add_segment(cc.AudioSegment(str(c['arq']), cc.Timerange(0, us(c['n']))), nm)
    if LEG.get('srt'):
        LG = EST['legendas']; h = LG.get('destaque', '#FFD43B').lstrip('#')
        sc.add_track(cc.TrackType.text, 'legendas')
        cues_ = _srt(LEG['srt']); fixo = pasta / '_legendas_capcut.srt'; L_ = []
        for i, (a_, b_, x_) in enumerate(cues_):        # CapCut recusa legendas sobrepostas: fim ≤ início da próxima
            b_ = min(b_, cues_[i + 1][0] - 0.002) if i + 1 < len(cues_) else b_
            st_ = lambda v: f'{int(v // 3600):02d}:{int(v % 3600 // 60):02d}:{int(v % 60):02d},{int(round((v % 1) * 1000)) % 1000:03d}'
            L_ += [str(i + 1), f'{st_(a_)} --> {st_(b_)}', x_, '']
        fixo.write_text('\n'.join(L_), encoding='utf-8')
        sc.import_srt(str(fixo), 'legendas', text_style=cc.TextStyle(size=9 if LG.get('caixa') == 'alta' else 7, bold=True, align=1, auto_wrapping=True, max_line_width=0.8),
                      clip_settings=cc.ClipSettings(transform_y=1 - 2 * float(LG.get('y', 0.66))))
    sc.save(); (pasta / '_legendas_capcut.srt').unlink(missing_ok=True)
    dc = pasta / nomed / 'draft_content.json'; s = dc.read_text(encoding='utf-8')
    s = s.replace(str(KIT.resolve()), str(BASE)); dc.write_text(s, encoding='utf-8')     # caminhos do Mac do editor
    log.append(f'CapCut: rascunho experimental em capcut/{nomed}/ (copie para a pasta de rascunhos com o CapCut FECHADO)')

def roteiro_capcut(dest):
    F = faixas(); tc = lambda n: f'{n / FPS:06.2f}s'
    L = [f'# Roteiro de montagem — CapCut / celular ({nome} v{ver:02d})', '', 'Se o rascunho automático não abrir, monte assim (5 min):', '',
         '1. Projeto novo no formato do vídeo (9:16). Importe toda a pasta `midia/`.', '2. Trilha principal, em ordem, sem espaço:']
    L += [f"   - {Path(c['arq']).name}: corte de {tc(c['ini'])} até {tc(c['ini'] + c['n'])} (o resto é alça)" for c in F['V1']]
    L += ['3. Camada acima (sobreposição), nos tempos da TIMELINE:'] + [f"   - {Path(c['arq']).name} em {tc(c['em'])} ({c['n'] / FPS:.2f}s)" for c in F['V2'] + F['V3']]
    L += ['4. Legendas: Texto › Legendas locais/Importar › `midia/legendas.srt` (ficam editáveis) — ou use `legendas_alpha.mov` como sobreposição (estilo idêntico ao vídeo).',
          '5. Áudio: `audio/trilha.wav` e `audio/sfx.wav` a partir de 0 s (já nivelados; a voz está dentro dos trechos s###).',
          '6. Exporte 1080×1920, 30 fps, taxa alta. Confira com `referencia_final.mp4`.', '', 'Marcadores (o que acontece em cada tempo):']
    L += [f'- {tc(n)} {i} · {x}' for n, i, x in marcadores()]
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text('\n'.join(L) + '\n', encoding='utf-8')

def pacote_celular(pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    if REF.get('arq'): shutil.copy(REF['arq'], pasta / f'{nome}_final.mp4')
    sem = pasta / f'{nome}_sem_legenda.mp4'
    if not sem.exists():
        r = subprocess.run([sys.executable, str(E.SKILL / 'scripts/compor.py'), str(P), '--sem-legenda', '--saida', str(pasta / '_v.mp4')], capture_output=True, text=True)
        if r.returncode == 0 and (P / 'audio/mix.wav').exists():
            E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(pasta / '_v.mp4'), '-i', str(P / 'audio/mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-t', f'{DUR:.4f}', '-movflags', '+faststart', str(sem)])
        (pasta / '_v.mp4').unlink(missing_ok=True)
    if LEG.get('srt'): shutil.copy(LEG['srt'], pasta / f'{nome}.srt')
    (pasta / 'LEIA-ME.md').write_text(f"""# Celular (Edits, CapCut mobile, InShot)

- `{nome}_final.mp4` — pronto para postar.
- `{nome}_sem_legenda.mp4` — com motion e som, SEM legenda: use as legendas automáticas do Edits/CapCut ou importe `{nome}.srt`.
- Edits (Instagram) não importa projeto de outro editor: ajuste fino = abra o `_sem_legenda`, gere legendas no app e mude o que quiser.
- Precisa mexer em corte, peça ou som? Peça ao Claude pelo número (s003, mo04, sfx07) — ele refaz em minutos.
""", encoding='utf-8')
    log.append('Celular/Edits: ✔ final, sem legenda e SRT')

def leia_me():
    F = faixas()
    txt = f"""# Kit de edição — {nome} v{ver:02d} (Orbe · edita-video)

O mesmo vídeo que o Claude montou, aberto para qualquer editor. Tudo já está no tamanho final ({OW}×{OH}, {FPS_STR} fps):
nenhum editor precisa reenquadrar. Os trechos do A-roll têm {ALCA:g} s de alça de cada lado (dá para estender o corte).

## Faixas (iguais em todos os editores)
| faixa | conteúdo |
|---|---|
| V1 | A-roll: {len(F['V1'])} trechos (s001…) já reenquadrados{' (sem zoom)' if SEM_ZOOM else ', com zoom/punch'}, cor do estilo, voz limpa |
| V2 | coberturas (B-roll, fotos, split): {len(F['V2'])} · originais em `midia/originais/` |
| V3 | motion com transparência: {len(F['V3'])} |
| V4 | legendas no estilo do vídeo (transparente) — ou importe `midia/legendas.srt` (editável) |
| V5 | referência final (desligada — ligue para comparar) |
| A1/A2/A3 | voz (dentro dos trechos) · trilha (ducking pronto) · efeitos |
Marcadores: s###, mo##, br##, sfx##, punch — os mesmos números que o Claude usa.

## Premiere Pro
1. Arquivo › Importar › `premiere/{nome}.xml` (Premiere 25.6+ também abre `premiere/{nome}.otio`).
2. Mídia offline? Clique com o direito › Vincular mídia › aponte para `midia/`.
3. Legenda editável: Arquivo › Importar › `midia/legendas.srt` › arraste para a sequência (vira faixa de legendas) e desligue a V4.
4. Look para clipes novos: Lumetri › Criativo › Look › `midia/{('cor_' + (EST.get('cor') or {}).get('preset', 'natural') + '.cube')}`.
5. Zonas seguras: arraste `midia/guias/zonas_reels.png` para a faixa mais alta (desligue antes de exportar).
Com o painel **Edit Link** (Brainstorm) ou o **premiere-pro-mcp** conectado, o Claude importa isto sozinho (references/multiplataforma.md).

## Final Cut Pro
1. Arquivo › Importar › XML… › `finalcut/{nome}.fcpxml` (cria o evento e o projeto).
2. Legenda editável: Arquivo › Importar › Legendas… › `midia/legendas.srt` (e desative a camada V4).
3. Look: efeito "LUT Personalizado" › `midia/cor_*.cube`.

## DaVinci Resolve
1. Arquivo › Importar › Linha do tempo › `resolve/{nome}.otio` (ou `.fcpxml` / `.xml`).
2. Legendas: Arquivo › Importar › Legenda › `midia/legendas.srt`.
Resolve 21.1 Studio tem servidor MCP nativo (Arquivo › Configurar assistentes de IA): o Claude pode importar e renderizar.

## CapCut (computador)
Rascunho automático (experimental) em `capcut/` — feche o CapCut, copie a pasta para
`~/Movies/CapCut/User Data/Projects/com.lveditor.draft/` (Windows: `%LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\`) e abra.
Não abriu? Siga `capcut/ROTEIRO.md` (montagem guiada em 5 minutos, com os tempos).

## Celular (Edits, CapCut mobile)
`celular/`: final pronto, versão sem legenda (com motion e som) e o SRT.

## No navegador
Peça ao Claude a página de revisão: o cliente assiste, comenta por número e aprova; o Claude aplica e renderiza.
"""
    (KIT / 'LEIA-ME.md').write_text(txt, encoding='utf-8')

# ───────────────────────── execução ─────────────────────────
print(f'Kit multiplataforma → {KIT.relative_to(P)}  (caminhos para o editor: {BASE})', flush=True)
midia_trechos(); midia_coberturas(); midia_motion(); midia_legendas(); midia_audio(); midia_lut(); midia_guias(); midia_referencia()
if 'premiere' in PARA or 'resolve' in PARA:
    escreve_xmeml(KIT / 'premiere' / f'{nome}.xml'); escreve_otio(KIT / 'premiere' / f'{nome}.otio')
if 'finalcut' in PARA: escreve_fcpxml(KIT / 'finalcut' / f'{nome}.fcpxml', opt('fcpxml', '1.10'))
if 'resolve' in PARA:
    (KIT / 'resolve').mkdir(exist_ok=True)
    for f in ('xml', 'otio'):
        if (KIT / 'premiere' / f'{nome}.{f}').exists(): shutil.copy(KIT / 'premiere' / f'{nome}.{f}', KIT / 'resolve' / f'{nome}.{f}')
    escreve_fcpxml(KIT / 'resolve' / f'{nome}.fcpxml', '1.10'); escreve_edl(KIT / 'resolve' / f'{nome}.edl')
if 'capcut' in PARA:
    roteiro_capcut(KIT / 'capcut' / 'ROTEIRO.md')
    try: escreve_capcut(KIT / 'capcut')
    except Exception as e: log.append(f'CapCut: rascunho falhou ({str(e)[:120]}) — use capcut/ROTEIRO.md')
if 'celular' in PARA: pacote_celular(KIT / 'celular')
(MID / '_base.mp4').unlink(missing_ok=True)
leia_me()
tam = sum(f.stat().st_size for f in KIT.rglob('*') if f.is_file()) / 1e6
print('\n'.join(['', *log, f'✔ kit em {KIT.relative_to(P)} ({tam:.0f} MB) · LEIA-ME.md com o passo a passo de cada editor']))
E.log_estado(P, 'entrega', 'kit', f"{', '.join(sorted(PARA))}")
