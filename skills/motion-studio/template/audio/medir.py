#!/usr/bin/env python3
"""Mede a prévia: loudness, banda de celular, grave e quanto cada contato sobe sobre a trilha."""
import json, re, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
CP = json.load(open('campaign.json')); B = 60 / CP['bpm']
def lufs(p, af=''):
    f = (af + ',' if af else '') + 'ebur128=peak=true'
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', f, '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'\bI:\s+(-?[\d.]+) LUFS', r)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
i, tp = lufs('audio/mix-previa.wav'); fone, _ = lufs('audio/mix-previa.wav', 'highpass=f=200,lowpass=f=6000')
print(f'integrado {i:.1f} LUFS · pico {tp:.1f} dBFS · banda de celular {fone:.1f} LUFS (diferença {fone - i:.1f} dB)')
sr, c = wavfile.read('audio/trilha.wav'); _, t = wavfile.read('audio/toques.wav')
sos = butter(2, [300, 6000], 'bandpass', fs=sr, output='sos')
C = sosfilt(sos, c.mean(1)) ; T = sosfilt(sos, t.mean(1))
sec = {}
for r in CP['rota']:
    a = int((r['b'] * B + 1 / 60 - .005) * sr); e = a + int(.06 * sr)
    d = 10 * np.log10((T[a:e] ** 2).mean() / max((C[a:e] ** 2).mean(), 1e-12))
    k = int(r['b'] // 8) * 8
    sec.setdefault(k, []).append(d)
for k in sorted(sec): print(f'batidas {k:3d}-{k + 8:<3d} toque sobre a trilha: mediana {np.median(sec[k]):5.1f} dB  min {min(sec[k]):5.1f}  max {max(sec[k]):5.1f}')
