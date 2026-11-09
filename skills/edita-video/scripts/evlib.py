"""evlib — utilidades comuns da skill edita-video (estado, caminhos, ffprobe, tempo, áudio).

Tudo que um script precisa saber do projeto passa por aqui. Os arquivos de estado ficam em <projeto>/_edit/.
Regra: o estado é a fonte da verdade; scripts leem e escrevem JSON, nunca "lembram" nada.
"""
import json, os, re, subprocess, sys, unicodedata, math, shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

def die(msg, code=1):
    print('✗ ' + msg, file=sys.stderr); sys.exit(code)

def proj(arg=None):
    """Raiz do projeto: argumento, variável EV_PROJETO ou cwd (precisa ter _edit/)."""
    p = Path(arg or os.environ.get('EV_PROJETO') or '.').resolve()
    if not (p / '_edit').is_dir():
        die(f'{p} não é um projeto do edita-video (falta _edit/). Crie com scripts/novo.sh')
    return p

def jload(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))

def jsave(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8'); tmp.replace(path)

def run(cmd, check=True, capture=True, text=True, **kw):
    r = subprocess.run(cmd, capture_output=capture, text=text, **kw)
    if check and r.returncode:
        err = r.stderr.decode('utf-8', 'replace') if isinstance(r.stderr, bytes) else (r.stderr or '')
        die(f"comando falhou: {' '.join(map(str, cmd))[:300]}\n{err[-1500:]}")
    return r

def ffprobe(path):
    r = run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', str(path)])
    return json.loads(r.stdout)

def frac(s, default=0.0):
    if not s or s in ('0/0', 'N/A'):
        return default
    if '/' in str(s):
        a, b = str(s).split('/'); return float(a) / float(b) if float(b) else default
    return float(s)

def estilo_proprio(b, nome):
    """procura um estilo que não está no plugin: <kit do cliente>/estilos/<nome>/preset.json, $ORBE_ESTILOS/<nome>/preset.json
    ou ~/.config/orbe/estilos/<nome>/preset.json (feitos por estudar_estilo.py ou formato.py)."""
    for base in (b.get('cliente_kit') and Path(b['cliente_kit']) / 'estilos', os.environ.get('ORBE_ESTILOS'), Path.home() / '.config/orbe/estilos'):
        if not base: continue
        for f in (Path(base) / nome / 'preset.json', Path(base) / f'{nome}.json'):
            if f.exists():
                d = jload(f, {}) or {}; d['_fonte'] = str(f); return d
    return None

def config(p):
    """Briefing + estilo resolvidos (briefing.json sobrescreve o preset do estilo)."""
    b = jload(p / '_edit' / 'briefing.json', {}) or {}
    estilos = jload(SKILL / 'assets' / 'estilos.json', {})
    nome = b.get('estilo', 'clinica-premium')
    est = dict(estilos.get('_base', {}))
    def _mescla(src):
        for k, v in (src or {}).items():
            if isinstance(v, dict) and isinstance(est.get(k), dict): est[k] = {**est[k], **v}
            else: est[k] = v
    custom = None if nome in estilos else estilo_proprio(b, nome)
    if custom:       # estilo treinado/salvo fora do plugin (kit do cliente ou ~/.config/orbe/estilos): herda do "base"
        _mescla(estilos.get(custom.get('base', 'minimal')))
        _mescla({k: v for k, v in custom.items() if k not in ('base', 'nome', '_fonte')})
    else:
        _mescla(estilos.get(nome))
    for k, v in (b.get('ajustes') or {}).items():          # ajustes finos pedidos pelo cliente
        if isinstance(v, dict) and isinstance(est.get(k), dict):
            est[k] = {**est[k], **v}
        else:
            est[k] = v
    return b, est, nome

def formato(b):
    f = (b.get('formato') or '9x16').lower()
    return {'9x16': (1080, 1920), '4x5': (1080, 1350), '1x1': (1080, 1080), '16x9': (1920, 1080)}.get(f, (1080, 1920))

# ── texto ──
FILLERS = {'éé', 'ééé', 'ehh', 'ãh', 'ãã', 'ahn', 'hum', 'hm', 'hmm', 'humm', 'uhm', 'uh', 'ãhn'}   # hesitação inequívoca
TALVEZ_VICIO = {'é', 'eh', 'e', 'ah', 'ã', 'a', 'um', 'tipo', 'né', 'então', 'assim', 'enfim', 'bom'}  # só é vício ISOLADO por pausa
FUNC = set('a o as os um uma uns umas de da do das dos e é em no na nos nas que pra pro pros pras para por com sem se ao à às aos mas ou meu minha seu sua te me lhe nem'.split())

def norm(w):
    w = unicodedata.normalize('NFKD', w.lower())
    w = ''.join(c for c in w if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9%]', '', w)

def norm_keep(w):
    return re.sub(r"[^\wÀ-ÿ%'-]", '', w.lower())

def is_filler(w):
    """Hesitação inequívoca (éé, ãh, hum). Palavras que TAMBÉM são palavras ('é', 'um', 'e', 'tipo', 'né') ficam em
    TALVEZ_VICIO e só saem quando isoladas por pausa dos dois lados (decidido em cortes.py com o tempo)."""
    t = norm_keep(w).strip("'-.")
    if t in FILLERS:
        return True
    return bool(re.fullmatch(r'(é|e|ã){2,}h*|h+u*m+|hu+m+|ãh+n*|a+h+n+', t))

def talvez_vicio(w):
    return norm_keep(w).strip("'-.") in TALVEZ_VICIO

# ── tempo ──
def snap(t, fps):
    return round(round(t * fps) / fps, 6)

def tc(t):
    m, s = divmod(max(0.0, t), 60)
    return f'{int(m)}:{s:05.2f}'

# ── áudio ──
def load_wav(path, sr=48000, mono=True):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1' if mono else '2', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).astype(np.float64)
    return a if mono else a.reshape(-1, 2)

def save_wav(path, y, sr=48000):
    import numpy as np, wave
    y = np.asarray(y)
    ch = 1 if y.ndim == 1 else y.shape[1]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())

def rms_env(x, sr, hop_s=0.01):
    import numpy as np
    hop = max(1, int(sr * hop_s)); n = len(x) // hop
    if n == 0:
        return np.zeros(1)
    return np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)

def db(x):
    return 20 * math.log10(max(x, 1e-9))

def motion_studio():
    """Acha a skill motion-studio (irmã no plugin orbe-video, ou instalada)."""
    cands = [os.environ.get('MOTION_STUDIO'), SKILL.parent / 'motion-studio', Path.home() / '.claude/skills/motion-studio',
             Path('/mnt/skills/organization/motion-studio')]
    for c in cands:
        if c and (Path(c) / 'scripts' / 'new.sh').exists():
            return Path(c)
    for c in Path('/').glob('mnt/skills/*/motion-studio'):
        if (c / 'scripts/new.sh').exists():
            return c
    return None

def models_dir():
    d = Path(os.environ.get('EV_MODELS') or Path.home() / '.cache' / 'edita-video')
    d.mkdir(parents=True, exist_ok=True); return d

def log_estado(p, etapa, status, nota=''):
    e = jload(p / '_edit' / 'estado.json', {}) or {}
    e.setdefault('etapas', {})[etapa] = {'status': status, 'nota': nota}
    jsave(p / '_edit' / 'estado.json', e)

# ── cor (compor e exportador NLE usam a mesma cadeia) ──
GRADES = {
    'nenhum': '',
    'natural': "eq=contrast=1.03:saturation=1.03",
    'punch': "eq=contrast=1.06:saturation=1.07,curves=master='0/0 0.25/0.23 0.75/0.77 1/1'",
    'cinema': "eq=contrast=1.08:brightness=-0.015:saturation=0.90,colorbalance=rs=0.02:bs=-0.03:rm=0.03:bm=-0.02:rh=0.06:bh=-0.04,curves=master='0/0 0.25/0.22 0.75/0.78 1/1'",
    'produto': "eq=contrast=1.05:saturation=1.05,curves=master='0/0.01 0.25/0.24 0.75/0.77 1/1'",
    'quente': "eq=contrast=1.04:saturation=1.04,colortemperature=temperature=5900",
    'frio': "eq=contrast=1.04:saturation=0.98,colortemperature=temperature=7200",
    # fosco (minimal premium): cor dessaturada, pretos levantados, altas suaves, leve calor — "cores foscas parecem caras"
    # documental (dossiê): contraste e pretos firmes, saturação contida, sombras levemente quentes — cara de reportagem
    'documental': "eq=contrast=1.07:saturation=0.86:brightness=-0.01,curves=master='0/0.02 0.25/0.22 0.75/0.77 1/0.97',colorbalance=rs=0.02:gs=0.005:bs=-0.02:rm=0.015:bm=-0.01",
    'fosco': "eq=contrast=0.97:saturation=0.80:brightness=0.005,curves=master='0/0.045 0.25/0.26 0.75/0.75 1/0.955',colorbalance=rs=0.015:bs=-0.01:rh=0.02:bh=-0.015",
    # pb (podcast cinematográfico): preto e branco moody — pretos fundos, meios-tons abertos, altas contidas (grão vem do compor)
    'pb': "hue=s=0,eq=contrast=1.16:brightness=-0.025,curves=master='0/0 0.16/0.10 0.5/0.49 0.84/0.86 1/0.96'",
}
_MEDIDAS = {}
def medir_cor(path, dur):
    """correção automática ANTES do estilo (video-use): luma média/faixa e saturação em ~10 quadros."""
    key = (str(path), round(dur, 2))
    if key in _MEDIDAS: return _MEDIDAS[key]
    import numpy as np
    r = run(['ffmpeg', '-v', 'error', '-i', str(path), '-vf', f"fps={10 / max(dur, 1):.4f},signalstats,metadata=print:file=-", '-f', 'null', '-'], check=False)
    vals = {}
    for ln in r.stdout.splitlines():
        if 'lavfi.signalstats.' in ln:
            k, _, v = ln.split('lavfi.signalstats.')[1].partition('=')
            try: vals.setdefault(k, []).append(float(v))
            except ValueError: pass
    out = ''
    if vals.get('YAVG'):
        mx = 255.0 if max(vals.get('YHIGH', [255])) > 1.5 else 1.0
        yavg = np.median(vals['YAVG']) / mx; rng = (np.median(vals.get('YHIGH', [235])) - np.median(vals.get('YLOW', [16]))) / mx
        sat = np.median(vals.get('SATAVG', [40])) / (128.0 if mx > 1 else 0.5)
        c = 1.0 + (min(0.08, (0.65 - rng) * 0.25) if rng < 0.65 else 0)
        gm = 1.08 if yavg < 0.36 else 1.04 if yavg < 0.42 else 0.97 if yavg > 0.62 else 1.0
        s = 1.04 if sat < 0.18 else 0.96 if sat > 0.40 else 1.0
        if not (abs(c - 1) < 0.005 and gm == 1 and s == 1): out = f"eq=contrast={c:.3f}:gamma={gm:.3f}:saturation={s:.3f}"
    _MEDIDAS[key] = out
    return out

def cadeia_cor(p, est, path, dur):
    preset = (est.get('cor') or {}).get('preset', 'natural'); lut = (est.get('cor') or {}).get('lut')
    parts = [x for x in (medir_cor(path, dur) if preset != 'nenhum' else '', GRADES.get(preset, ''),
                         f"lut3d=file='{(p / lut).as_posix()}'" if lut and (p / lut).exists() else '') if x]
    return ','.join(parts)

def cadeia_voz(est, piso_db):
    """limpeza da voz por sintoma (som.voz = limpar | leve | nenhum): subtrair → nivelar → caráter."""
    modo = (est.get('som') or {}).get('voz', 'limpar'); cad = []
    if modo == 'nenhum': return ''
    cad.append('highpass=f=80')
    modelo = models_dir() / 'sh.rnnn'
    if modo == 'limpar' and piso_db > -60:
        cad.append(f"arnndn=m='{modelo.as_posix()}':mix=0.85" if modelo.exists() else 'afftdn=nr=10:nf=-50:tn=1')
    if modo == 'limpar': cad += ['equalizer=f=250:t=q:w=1:g=-2', 'equalizer=f=3000:t=q:w=1.2:g=2', 'deesser=i=0.4']
    cad.append('acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2' if modo == 'limpar' else 'acompressor=threshold=-18dB:ratio=2:attack=10:release=150')
    return ','.join(cad)
