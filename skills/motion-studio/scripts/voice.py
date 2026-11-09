#!/usr/bin/env python3
"""voice.py — VOZ PRIMEIRO, depois o tempo, depois a animação. Gera a narração, mede, e escreve os relógios do filme.

    python3 scripts/voice.py                       # lê scenes.json, sintetiza cada fala, ajusta as durações das cenas
    python3 scripts/voice.py --voice audio/voice.wav --no-tts   # voz gravada por você (celular): só mede/sincroniza
    Opções: --model <voz piper .onnx> · --whisper small|base|medium · --breath 0.3 · --fps 30 · --rate 1.0
    VoiceStudio / qualquer servidor compatível com OpenAI (/v1/audio/speech):
      python3 scripts/voice.py --api http://localhost:3900/v1 --api-model cosyvoice3 --api-voice minha-voz
      (ou em scenes.json: "voice": {"api": "...", "api_model": "...", "api_voice": "..."}; chave opcional em VOICE_API_KEY no .env)

Saídas (todas ancoradas no mesmo relógio do filme):
  audio/voice.wav      narração montada na linha do tempo (cena a cena, com respiro)
  audio/words.json     cada palavra com início/fim (faster-whisper, guiado pelo texto conhecido) → legendas palavra a palavra
  audio/mouth.json     formato de boca por frame (A..H, X — padrão Rhubarb) → sincronia labial de verdade, não boca em loop
  audio/loud.json      envelope de volume por frame + picos de ênfase → sobrancelha desce, pulo nas palavras fortes
  scenes.json          duration_sec/start de cada cena ajustados à fala real (+ respiro); o filme lê daqui

TTS, nesta ordem: (1) o que já existe em audio/lines/NN.wav (gravado, ElevenLabs, exportado do VoiceStudio) ·
(2) --api: VoiceStudio/servidor OpenAI-compatível local (voz clonada, motores atuais) · (3) Piper (offline, pt_BR) se instalado — voz em models/*.onnx ou ~/.local/share/piper. ElevenLabs: gere os WAVs por cena
fora daqui (chave só no .env) e salve em audio/lines/NN.wav — o script usa o que existir e só sintetiza o que faltar.
Lip sync: usa `rhubarb` (Rhubarb Lip Sync, --recognizer phonetic) se estiver no PATH; senão, o analisador próprio:
texto da fala → visemas por grafema (português) distribuídos no tempo de cada palavra e fechados onde o volume cai.
"""
import json, os, re, subprocess, sys, glob, shutil
import numpy as np

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
FPS = int(opt('fps', 30)); BREATH = float(opt('breath', 0.3)); SR = 48000
os.makedirs('audio/lines', exist_ok=True)
S = json.load(open('scenes.json'))
scenes = S['scenes']

def load(p, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

def find_voice():
    m = opt('model') or S.get('voice', {}).get('model')
    if m and os.path.exists(m): return m
    for g in ['models/*.onnx', os.path.expanduser('~/.local/share/piper/*.onnx'), '/usr/share/piper-voices/*.onnx']:
        f = sorted(glob.glob(g))
        if f: return f[0]
    return None

# ── 1. uma fala por cena (TTS só do que faltar) ──
VC = S.get('voice', {})
API = opt('api') or VC.get('api')
def api_tts(text, out):
    """POST /audio/speech (padrão OpenAI) → WAV. VoiceStudio expõe isso em http://localhost:3900/v1."""
    import urllib.request
    body = json.dumps({'model': opt('api-model') or VC.get('api_model') or 'tts-1', 'input': text,
                       'voice': opt('api-voice') or VC.get('api_voice') or 'default', 'response_format': 'wav',
                       'speed': float(opt('rate', VC.get('rate', 1.0)))}).encode()
    key = os.environ.get('VOICE_API_KEY') or ''
    if not key and os.path.exists('.env'):
        for ln in open('.env'):
            if ln.startswith('VOICE_API_KEY='): key = ln.split('=', 1)[1].strip()
    req = urllib.request.Request(API.rstrip('/') + '/audio/speech', data=body, headers={'Content-Type': 'application/json', **({'Authorization': 'Bearer ' + key} if key else {})})
    with urllib.request.urlopen(req, timeout=300) as r: data = r.read()
    tmp = out + '.src'; open(tmp, 'wb').write(data)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ac', '1', '-ar', str(SR), out], check=True); os.remove(tmp)
if '--no-tts' not in A and API:
    for sc in scenes:
        out = f"audio/lines/{sc['id']}.wav"
        if not sc.get('voiceover') or os.path.exists(out): continue
        try: api_tts(sc['voiceover'], out)
        except Exception as e: sys.exit(f"✗ servidor de voz em {API} falhou na cena {sc['id']}: {str(e)[:200]} — o VoiceStudio está aberto? (a API dele só existe com o app rodando)")
    print(f'✔ falas em audio/lines/ (servidor {API})')
if '--no-tts' not in A and not API:
    model = find_voice()
    for sc in scenes:
        out = f"audio/lines/{sc['id']}.wav"
        if not sc.get('voiceover') or os.path.exists(out): continue
        if not model: sys.exit('✗ sem voz: use --api (VoiceStudio), grave/exporte audio/lines/NN.wav, ou instale piper-tts + uma voz pt_BR em models/')
        r = subprocess.run([sys.executable, '-m', 'piper', '-m', model, '-f', out, '--length-scale', str(1 / float(opt('rate', S.get('voice', {}).get('rate', 1.0))))],
                           input=sc['voiceover'].encode(), capture_output=True)
        if r.returncode: sys.exit(f"✗ piper falhou na cena {sc['id']}: {r.stderr.decode()[-300:]}")
    print(f'✔ falas em audio/lines/ ({os.path.basename(model) if model else "gravadas"})')

def trim(x, thr=0.012, pad=0.03):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx): return x
    a, b = max(0, idx[0] - int(pad * SR)), min(len(x), idx[-1] + int(pad * 3 * SR))
    return x[a:b]

# ── 2. linha do tempo a partir da fala real: cena = fala + respiro (mínimo = duration_sec do roteiro) ──
t = 0.0; lines = {}
for sc in scenes:
    p = f"audio/lines/{sc['id']}.wav"
    x = trim(load(p)) if os.path.exists(p) else np.zeros(0)
    lead = float(sc.get('voice_at', 0.25))                      # a fala começa um pouco depois do corte
    need = lead + len(x) / SR + BREATH
    sc['start'] = round(t, 3); sc['duration_sec'] = round(max(float(sc.get('min_sec', sc.get('duration_sec', 0)) or 0), need), 3)
    lines[sc['id']] = (x, t + lead)
    t += sc['duration_sec']
S['duration'] = round(t, 3)
voice = np.zeros(int((t + 0.5) * SR))
for sid, (x, at) in lines.items():
    i = int(at * SR); voice[i:i + len(x)] += x
peak = np.abs(voice).max() or 1; voice = voice / peak * 0.89
def wav(path, y):
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
wav('audio/voice.wav', voice)
json.dump(S, open('scenes.json', 'w'), ensure_ascii=False, indent=2)
print(f'✔ audio/voice.wav · {t:.2f}s · {len(scenes)} cenas com duração da fala real (+{BREATH}s de respiro)')

# ── 3. palavras com tempo (faster-whisper guiado pelo texto) ──
words = []
try:
    from faster_whisper import WhisperModel
    wm = WhisperModel(opt('whisper', 'small'), device='cpu', compute_type='int8')
    for sc in scenes:
        x, at = lines[sc['id']]
        if not len(x): continue
        x16 = load(f"audio/lines/{sc['id']}.wav", 16000)
        x16 = trim(x16, pad=0.03) if len(x16) else x16
        segs, _ = wm.transcribe(x16.astype(np.float32), language=S.get('lang', 'pt'), word_timestamps=True, initial_prompt=sc['voiceover'])
        ws = [w for s in segs for w in s.words]
        # alinha ao texto do roteiro (a grafia certa vem do roteiro; o tempo, do whisper)
        script = re.findall(r"[\wÀ-ÿ%+'-]+[.,!?…]*", sc['voiceover'])
        for i, tok in enumerate(script):
            w = ws[min(i, len(ws) - 1)] if ws else None
            if w and len(ws) == len(script): s0, s1 = w.start, w.end
            else:   # contagens diferentes: distribui pelo tamanho no intervalo da fala
                tot = sum(len(z) for z in script); acc = sum(len(z) for z in script[:i]); dur = len(x) / SR
                s0, s1 = dur * acc / tot, dur * (acc + len(tok)) / tot
            words.append({'scene': sc['id'], 'w': tok, 's': round(at + s0, 3), 'e': round(at + s1, 3)})
    print(f'✔ audio/words.json · {len(words)} palavras com tempo (faster-whisper)')
except Exception as e:
    print(f'⚠ faster-whisper indisponível ({str(e)[:80]}): tempo das palavras estimado pelo tamanho')
    for sc in scenes:
        x, at = lines[sc['id']]; script = re.findall(r"[\wÀ-ÿ%+'-]+[.,!?…]*", sc.get('voiceover', '')); tot = sum(len(z) for z in script) or 1; acc = 0; dur = len(x) / SR
        for tok in script:
            words.append({'scene': sc['id'], 'w': tok, 's': round(at + dur * acc / tot, 3), 'e': round(at + dur * (acc + len(tok)) / tot, 3)}); acc += len(tok)
json.dump(words, open('audio/words.json', 'w'), ensure_ascii=False, indent=1)

# ── 4. volume por frame + ênfases (palavras fortes) ──
hop = SR // FPS
env = np.array([np.sqrt(np.mean(voice[i:i + hop] ** 2) + 1e-12) for i in range(0, len(voice), hop)])
env = env / (env.max() or 1)
sm = np.convolve(env, np.ones(3) / 3, mode='same')
for wd in words:
    a, b = int(wd['s'] * FPS), max(int(wd['s'] * FPS) + 1, int(wd['e'] * FPS))
    wd['loud'] = round(float(sm[a:b].max()) if b > a else 0, 3)
lv = np.array([w['loud'] for w in words]) if words else np.zeros(1)
thr = max(0.75, float(np.percentile(lv, 85))) if len(lv) else 1
for wd in words: wd['stress'] = bool(wd['loud'] >= thr)
json.dump(words, open('audio/words.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'fps': FPS, 'env': [round(float(v), 3) for v in sm], 'stress': [w['s'] for w in words if w['stress']]}, open('audio/loud.json', 'w'))
print(f"✔ audio/loud.json · {sum(w['stress'] for w in words)} palavra(s) de ênfase (pulo/sobrancelha)")

# ── 5. bocas (A..H, X) ──
# A=M/B/P fechada · B=consoantes, dentes · C=E/I · D=A aberta · E=O · F=U/bico · G=F/V · H=L · X=repouso
def visemes_from_text(tok):
    t_ = tok.lower(); out = []; i = 0
    while i < len(t_):
        c = t_[i]; nx = t_[i + 1] if i + 1 < len(t_) else ''
        if c in 'mbp': out.append(('A', 1))
        elif c in 'fv': out.append(('G', 1))
        elif c == 'l' and nx != 'h': out.append(('H', 1))
        elif c in 'aáàâã': out.append(('D', 2))
        elif c in 'eéêií': out.append(('C', 2))
        elif c in 'oóôõ': out.append(('E', 2))
        elif c in 'uú': out.append(('F', 2))
        elif c.isalpha(): out.append(('B', 1))
        i += 2 if (c in 'lnc' and nx == 'h') or (c == 'q' and nx == 'u') else 1
    return out or [('B', 1)]

n = int(S['duration'] * FPS) + 1
mouth = ['X'] * n
rh = shutil.which('rhubarb')
if rh:
    for sc in scenes:
        x, at = lines[sc['id']]
        if not len(x): continue
        r = subprocess.run([rh, '-f', 'json', '--recognizer', 'phonetic', '-q', f"audio/lines/{sc['id']}.wav"], capture_output=True, text=True)
        if r.returncode: rh = None; break
        for c in json.loads(r.stdout)['mouthCues']:
            for f in range(int((at + c['start']) * FPS), int((at + c['end']) * FPS)):
                if 0 <= f < n: mouth[f] = c['value']
src = 'Rhubarb (phonetic)' if rh else 'texto + volume'
if not rh:
    for wd in words:
        vs = visemes_from_text(re.sub(r'[^\wÀ-ÿ]', '', wd['w']))
        tot = sum(w for _, w in vs); f0, f1 = wd['s'] * FPS, wd['e'] * FPS; acc = 0
        for v, w in vs:
            a, b = int(round(f0 + (f1 - f0) * acc / tot)), int(round(f0 + (f1 - f0) * (acc + w) / tot)); acc += w
            for f in range(a, max(a + 1, b)):
                if 0 <= f < n: mouth[f] = v
    # volume manda: onde a voz cai, a boca fecha; vogal fraca vira meia-boca
    for f in range(n):
        e = sm[f] if f < len(sm) else 0
        if e < 0.06: mouth[f] = 'X'
        elif e < 0.16 and mouth[f] in 'DE': mouth[f] = 'C' if mouth[f] == 'D' else 'F'
# segura cada forma ≥ 2 frames (boca que troca a cada frame treme)
for f in range(1, n - 1):
    if mouth[f] != mouth[f - 1] and mouth[f] != mouth[f + 1]: mouth[f] = mouth[f - 1]
json.dump({'fps': FPS, 'source': src, 'shapes': ''.join(mouth)}, open('audio/mouth.json', 'w'))
print(f'✔ audio/mouth.json · {n} frames · bocas por {src}')
