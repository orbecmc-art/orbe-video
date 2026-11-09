#!/usr/bin/env python3
"""beats.py — mede a grade rítmica de uma faixa e grava beats.json para a animação ler.

    python3 beats.py musica.wav > beats.json
    python3 beats.py musica.mp3 --bpm 120   # força o BPM se você já sabe (mais preciso)
    python3 beats.py musica.mp3 --downbeat 0   # qual batida (0-3) é o 'um' do compasso, se a detecção errar

Saída: {bpm, beats[], downbeats[], hits[], sections[], energy[]}
  beats      → mudanças de estado vão aqui
  downbeats  → momentos grandes (cortes, revelações) vão aqui
  hits       → picos de transiente medidos (SFX/UI sounds vão aqui)
  energy     → RMS normalizado a cada 0,1s (para reagir à intensidade)
  sections   → trechos de energia parecida (intro / build / drop)

Usa librosa se instalado; senão cai num detector só com numpy (decodifica via ffmpeg).
"""
import sys, json, subprocess
import numpy as np

args = sys.argv[1:]
path = next(a for a in args if not a.startswith('--'))
force_bpm = float(args[args.index('--bpm') + 1]) if '--bpm' in args else None
SR = 22050


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


y = load(path)
dur = len(y) / SR
HOP, NFFT = 256, 1024
y_pad = np.concatenate([np.zeros(NFFT // 2, np.float32), y, np.zeros(NFFT // 2, np.float32)])  # frames centrados (frame i ↔ i*HOP)

# ── fluxo espectral (onset strength) ──
win = np.hanning(NFFT).astype(np.float32)
nfr = 1 + max(0, (len(y_pad) - NFFT) // HOP)
frames = np.lib.stride_tricks.as_strided(y_pad, shape=(nfr, NFFT), strides=(y_pad.strides[0] * HOP, y_pad.strides[0]))
mag = np.log1p(np.abs(np.fft.rfft(frames * win, axis=1)) * 10)
flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
flux = np.concatenate([[0], flux])
flux = (flux - flux.mean()) / (flux.std() + 1e-9)
fps_on = SR / HOP
times = np.arange(len(flux)) / fps_on

try:
    import librosa  # caminho preferido
    tempo, bf = librosa.beat.beat_track(y=y, sr=SR, hop_length=HOP, units='frames', start_bpm=force_bpm or 120)
    bpm = force_bpm or float(np.atleast_1d(tempo)[0])
    beats = librosa.frames_to_time(bf, sr=SR, hop_length=HOP)
except Exception:
    # ── tempo por autocorrelação do fluxo (60–200 BPM) ──
    def interp(arr, t):  # fluxo interpolado linearmente em tempos arbitrários
        x = np.asarray(t) * fps_on
        i = np.clip(x.astype(int), 0, len(arr) - 2); f = x - i
        return arr[i] * (1 - f) + arr[i + 1] * f
    if force_bpm:
        cands = [force_bpm]
    else:
        ac = np.correlate(flux, flux, mode='full')[len(flux) - 1:]
        lags = np.arange(1, len(ac) - 1)
        bpms = 60 * fps_on / lags
        mask = (bpms >= 70) & (bpms <= 180)
        weight = np.exp(-0.5 * (np.log2(bpms[mask] / 120) / 0.9) ** 2)
        k = lags[mask][np.argmax(ac[lags[mask]] * weight)]
        # interpolação parabólica do pico → BPM sub-lag
        a_, b_, c_ = ac[k - 1], ac[k], ac[k + 1]
        kf = k + 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_ + 1e-12)
        b0 = 60 * fps_on / kf
        cands = np.arange(b0 - 3, b0 + 3, 0.05)
        # BPMs "redondos" ganham leve preferência (trilhas de stock quase sempre são inteiras)
    smoothed = np.convolve(flux, np.hanning(5) / np.hanning(5).sum(), mode='same')
    best, bpm, phase = -1e9, cands[0], 0.0
    for cb in cands:
        per = 60 / cb
        for ph in np.linspace(0, per, 48, endpoint=False):
            sc_ = interp(smoothed, np.arange(ph, dur, per)).mean()
            if abs(cb - round(cb)) < 0.03: sc_ *= 1.02
            if sc_ > best: best, bpm, phase = sc_, cb, ph
    bpm = round(bpm) if abs(bpm - round(bpm)) < 0.15 else bpm
    period = 60 / bpm
    for ph in np.linspace(0, period, 200, endpoint=False):  # refina a fase com o BPM final
        sc_ = interp(smoothed, np.arange(ph, dur, period)).mean()
        if ph == 0 or sc_ > best2: best2, phase = sc_, ph
    if phase > period - 0.04: phase -= period  # fase 'quase um período' = batida em ~0s
    beats = np.maximum(0, np.arange(phase, dur, period))

beats = np.round(np.asarray(beats), 3)

# ── downbeats: fase de compasso (4/4) com mais energia de grave ──
low = mag[:, : max(2, int(150 / (SR / NFFT)))].sum(axis=1)
low = np.concatenate([[low[0]], low])
def at(arr, t):
    return arr[np.clip((np.asarray(t) * fps_on).astype(int), 0, len(arr) - 1)]
scores = [at(low, beats[o::4]).mean() if len(beats[o::4]) else 0 for o in range(4)]
off = int(args[args.index('--downbeat') + 1]) if '--downbeat' in args else int(np.argmax(scores))  # ambíguo em 4x4 reto: confira e force com --downbeat 0..3
downbeats = beats[off::4]

# ── hits: picos locais do fluxo ──
k = 3
peaks = [i for i in range(k, len(flux) - k)
         if flux[i] > 1.2 and flux[i] == flux[i - k:i + k + 1].max()]
hits, last = [], -1
for i in peaks:
    if times[i] - last >= 0.09:
        hits.append(round(float(times[i]), 3)); last = times[i]

# ── energia (RMS a cada 0,1s) e seções ──
step = int(SR * 0.1)
rms = np.array([np.sqrt(np.mean(y[i:i + step] ** 2) + 1e-12) for i in range(0, len(y), step)])
rms = rms / (rms.max() + 1e-9)
bar = 4 * 60 / bpm
sections, cur = [], None
for b in downbeats:
    e = float(rms[int(b / 0.1): int((b + bar) / 0.1) + 1].mean()) if int(b / 0.1) < len(rms) else 0
    lvl = 'low' if e < 0.35 else 'mid' if e < 0.65 else 'high'
    if not cur or cur['level'] != lvl:
        cur = {'start': round(float(b), 3), 'level': lvl}; sections.append(cur)
for i, s in enumerate(sections):
    s['end'] = sections[i + 1]['start'] if i + 1 < len(sections) else round(dur, 3)

json.dump({
    'bpm': round(float(bpm), 2), 'duration': round(dur, 3),
    'beats': beats.tolist(), 'downbeats': downbeats.tolist(), 'hits': hits,
    'sections': sections, 'energy': [round(float(v), 3) for v in rms],
}, sys.stdout, indent=1)
print(file=sys.stderr)
print(f"✔ {bpm:.1f} BPM · {len(beats)} batidas · {len(downbeats)} compassos · {len(hits)} hits · {len(sections)} seções", file=sys.stderr)
