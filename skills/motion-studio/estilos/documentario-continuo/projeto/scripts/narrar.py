#!/usr/bin/env python3
"""narrar.py — VOZ PRIMEIRO: monta a locução do roteiro e escreve o relógio do filme (narracao.js).

    python3 scripts/narrar.py [--modelo <voz piper .onnx>] [--voz audio/voz_gravada.wav] [--whisper small]

Ordem da voz (igual ao voice.py do motion-studio): (1) audio/linhas/<id>.wav que já existirem (gravado no celular,
ElevenLabs, VoiceStudio — o melhor para cliente); (2) Piper offline pt-BR (--modelo ou roteiro.voz.modelo, procurado
em models/, ~/.local/share/piper e na pasta do projeto) para o que faltar. --voz: uma locução inteira gravada (o
roteiro é só o texto) → mede com o Whisper e corta por fala.
Cada fala entra depois de "respiro" s. As palavras recebem início/fim pelo faster-whisper (guiado pelo texto); sem
ele, por proporção de sílabas. Saídas: audio/voice.wav · narracao.js (window.NARRACAO = {dur, falas:[{id,t0,t1,palavras}]}).
"""
import sys, os, json, re, subprocess, shutil, wave, glob
import numpy as np
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
R = json.load(open('roteiro.json', encoding='utf-8')); V = R.get('voz', {})
SR = 22050; RESP = float(V.get('respiro', 0.4)); RITMO = float(V.get('ritmo', 1.0))
Path('audio/linhas').mkdir(parents=True, exist_ok=True)

def ler(f):
    with wave.open(str(f)) as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth(); x = np.frombuffer(w.readframes(n), np.int16 if sw == 2 else np.int32).astype(np.float32)
    x = x.reshape(-1, ch).mean(1) / (32768 if sw == 2 else 2 ** 31)
    if sr != SR: x = np.interp(np.arange(0, len(x) * SR / sr) * sr / SR, np.arange(len(x)), x).astype(np.float32)
    return x

def apara(x, lim=0.012):
    i = np.where(np.abs(x) > lim)[0]
    return x[max(0, i[0] - int(0.03 * SR)):min(len(x), i[-1] + int(0.08 * SR))] if len(i) else x

def modelo():
    nome = opt('modelo') or V.get('modelo', 'pt_BR-faber-medium.onnx')
    for c in [nome, f'models/{nome}', os.path.expanduser(f'~/.local/share/piper/{nome}'), *glob.glob(os.path.expanduser(f'~/**/{Path(nome).name}'), recursive=True)[:3]]:
        if c and os.path.exists(c): return c
    return None

if opt('voz'):
    sys.exit('--voz (locução inteira): rode o Whisper nela e corte por fala — use o voice.py do motion-studio com --voice e --no-tts e copie os tempos para narracao.js')

linhas = []
for f in R['falas']:
    arq = Path(f'audio/linhas/{f["id"]}.wav')
    if not arq.exists():
        m = modelo()
        if not m or not shutil.which('piper'): sys.exit(f'falta a voz de {f["id"]}: grave audio/linhas/{f["id"]}.wav ou instale o Piper + uma voz pt_BR (.onnx)')
        subprocess.run(['piper', '-m', m, '-f', str(arq), '--length-scale', str(round(1 / RITMO, 3)), '--sentence-silence', '0.1'], input=f['texto'], text=True, capture_output=True, check=True)
    linhas.append((f, apara(ler(arq))))

pos = 0.45; trilha = []; falas = []
for f, x in linhas:
    t0 = pos; trilha.append((int(t0 * SR), x)); t1 = t0 + len(x) / SR
    falas.append({'id': f['id'], 't0': round(t0, 3), 't1': round(t1, 3), 'texto': f['texto'], '_x': x}); pos = t1 + RESP
dur = pos - RESP + float(R.get('cauda', 1.2))
out = np.zeros(int(dur * SR) + 1, np.float32)
for i0, x in trilha: out[i0:i0 + len(x)] += x
pk = np.abs(out).max() or 1; out = out / pk * 0.89
with wave.open('audio/voice.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())

def silabas(w): return max(1, len(re.findall(r'[aeiouáéíóúâêôãõà]+', w.lower())))
try:
    from faster_whisper import WhisperModel
    WM = WhisperModel(opt('whisper', 'small'), device='cpu', compute_type='int8')
except Exception: WM = None
for f in falas:
    x = f.pop('_x'); ws = f['texto'].split(); pal = []
    if WM is not None:
        try:     # array em 16 kHz direto (não depende do decodificador de áudio da versão instalada)
            x16 = np.interp(np.arange(0, len(x) * 16000 / SR) * SR / 16000, np.arange(len(x)), x).astype(np.float32)
            segs, _ = WM.transcribe(x16, language='pt', word_timestamps=True, initial_prompt=f['texto'], vad_filter=False)
            wh = [(w_.start, w_.end) for s in segs for w_ in (s.words or [])]
            if len(wh) == len(ws): pal = [{'w': w, 't0': round(f['t0'] + a, 3), 't1': round(f['t0'] + b, 3)} for w, (a, b) in zip(ws, wh)]
        except Exception as e: print('  (whisper falhou nesta fala:', str(e)[:80], ')')
    if not pal:      # proporcional às sílabas
        tot = sum(silabas(w) for w in ws); acc = 0; d = f['t1'] - f['t0']
        for w in ws:
            a = f['t0'] + d * acc / tot; acc += silabas(w); pal.append({'w': w, 't0': round(a, 3), 't1': round(f['t0'] + d * acc / tot, 3)})
    f['palavras'] = pal
N = {'dur': round(dur, 3), 'falas': falas}
open('narracao.js', 'w', encoding='utf-8').write('// GERADO por scripts/narrar.py — o relógio do filme é a voz\nwindow.NARRACAO = ' + json.dumps(N, ensure_ascii=False) + ';\n')
print(f"✔ audio/voice.wav · {dur:.1f}s · {len(falas)} falas · palavras por {'whisper' if WM else 'sílabas'} → narracao.js")
for f in falas: print(f"  {f['id']} {f['t0']:6.2f}–{f['t1']:6.2f}  {f['texto']}")
