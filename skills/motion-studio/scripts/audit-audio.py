#!/usr/bin/env python3
"""audit-audio.py — o Claude não ouve: MEDE. Confere o som do MP4 final contra a imagem, hit por hit.

    python3 scripts/audit-audio.py out/final.mp4 --sfx audio/sfx.wav --music audio/music.wav [--music-db -4 --sfx-db 0] [--loop]

Lê audio/sfx_cues.json (gerado pelo sfx.mjs) para saber onde cada pico DEVERIA cair (evento + 1 frame).
Relata (e grava out/qa/audio.md):
  • offset do áudio decodificado vs stems (encoder/AAC) e sobra de áudio além do vídeo (padding do codec)
  • por hit: erro de sincronia em ms e frames (meta: 0 a +1 frame; nunca antes da imagem)
  • por hit: quanto o hit fica ACIMA da trilha (K-weighted, 60 ms) — meta 3 a 6 dB
  • loudness integrado: banda cheia vs banda de CELULAR (200 Hz–6 kHz) — grave demais some no alto-falante do telefone
  • distribuição de energia (<60 Hz, <150 Hz, 150 Hz–6 kHz), DC por canal, true peak do arquivo decodificado
  • --loop: degrau na emenda (último→primeiro sample)
"""
import sys, json, subprocess, re, os
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, correlate

a = sys.argv[1:]
VIDEO = a[0]
def opt(k, d=None):
    return a[a.index('--' + k) + 1] if '--' + k in a else d
SFX, MUSIC = opt('sfx', 'audio/sfx.wav'), opt('music')
MDB, SDB = float(opt('music-db', -3)), float(opt('sfx-db', 0))
CUES = opt('cues', (SFX[:-4] + '_cues.json') if SFX else None)
SR = 48000
OUT = os.path.join(os.path.dirname(VIDEO) or '.', 'qa', 'audio.md')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def load(p, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)

def kweight(x):  # ITU-R BS.1770 K-weighting @48 kHz
    x = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585], x)
    return lfilter([1, -2, 1], [1, -1.99004745483398, 0.99007225036621], x)

def ebur(p, af=''):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', (af + ',' if af else '') + 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = re.findall(r'^\s+I:\s+(-?[\d.]+) LUFS', r, re.M); TP = re.findall(r'^\s+Peak:\s+(-?[\d.inf]+) dBFS', r, re.M)
    return (float(I[-1]) if I else None), (float(TP[-1]) if TP and TP[-1] != '-inf' else None)

lines, warn = [], []
def say(s): lines.append(s); print(s)

vdur = float(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', VIDEO], capture_output=True, text=True).stdout.strip().rstrip(',') or 0)
dec = load(VIDEO); mono = dec.mean(1)
adur = len(dec) / SR
say(f'# Auditoria de áudio — {os.path.basename(VIDEO)}')
say(f'- duração: vídeo {vdur:.3f}s · áudio decodificado {adur:.3f}s · sobra {1000*(adur-vdur):+.1f} ms' + (' (padding do codec)' if adur - vdur > 0.005 else ''))

# ── offset decodificado vs stems ──
stems = None
if SFX and os.path.exists(SFX):
    sfx = load(SFX).mean(1) * 10 ** (SDB / 20)
    mus = load(MUSIC).mean(1) * 10 ** (MDB / 20) if MUSIC and os.path.exists(MUSIC) else np.zeros_like(sfx)
    n = min(len(sfx), len(mus)); stems = sfx[:n] + mus[:n]
    w = min(len(stems), len(mono), SR * 4)
    cc = correlate(mono[:w], stems[:w], mode='full', method='fft'); lag = int(np.argmax(cc)) - (w - 1)
    lim = int(0.05 * SR)
    seg = cc[(w - 1) - lim:(w - 1) + lim + 1]; lag = int(np.argmax(seg)) - lim
    say(f'- offset decodificado vs stems: {1000*lag/SR:+.2f} ms ' + ('✔' if abs(lag) < SR * 0.002 else '⚠'))
    if abs(lag) >= SR * 0.002: warn.append(f'áudio do MP4 deslocado {1000*lag/SR:+.1f} ms em relação aos stems')

    # ── sincronia e nível por hit ──
    if CUES and os.path.exists(CUES):
        cj = json.load(open(CUES)); fps = cj.get('fps', 60)
        ks, km = kweight(sfx), kweight(mus[:len(sfx)] if len(mus) >= len(sfx) else np.pad(mus, (0, len(sfx) - len(mus))))
        say(f'\n## Hits ({len(cj["cues"])}) — meta: pico em evento+1 frame (0 a +{1000/fps:.0f} ms depois da imagem), 3–6 dB acima da trilha')
        say('| t evento | tipo | pico medido | erro vs evento | hit/trilha |')
        say('|---|---|---|---|---|')
        early = late = loud = soft = 0
        tgs = [c['target'] for c in cj['cues']]
        for c in cj['cues']:
            tg = c['target']; i0, i1 = int((tg - 0.03) * SR), int((tg + 0.06) * SR)
            ov = any(o != tg and abs(o - tg) < 0.045 for o in tgs)
            win = np.abs(sfx[max(0, i0):i1]); pk = (max(0, i0) + int(np.argmax(win))) / SR + lag / SR if len(win) else tg
            err = pk - c['t']                                    # vs EVENTO visual
            j0, j1 = int((pk - 0.005) * SR), int((pk + 0.06) * SR)
            eh = np.mean(ks[max(0, j0):j1] ** 2) + 1e-12; eb = np.mean(km[max(0, j0):j1] ** 2) + 1e-12
            over = 10 * np.log10(eh / eb) if MUSIC else float('nan')
            flag = ' (sobreposto: medido junto com o vizinho)' if ov else ''
            if not ov and err < -0.0005: early += 1; flag = ' ⚠ ANTES da imagem'
            elif not ov and err > 2.5 / fps: late += 1; flag = ' ⚠ atrasado'
            if MUSIC and not ov and over < 2.5: soft += 1; flag += ' ⚠ baixo'
            if MUSIC and not ov and over > 9: loud += 1; flag += ' ⚠ alto'
            say(f"| {c['t']:.3f}s f{round(c['t']*fps)} | {c['type']} | {pk:.4f}s | {1000*err:+.1f} ms ({err*fps:+.2f} fr) | {over:+.1f} dB{flag} |")
        if early: warn.append(f'{early} hit(s) soam ANTES da imagem')
        if late: warn.append(f'{late} hit(s) atrasados mais de 2 frames')
        if soft: warn.append(f'{soft} hit(s) abaixo de 3 dB sobre a trilha (somem no celular) — rode sfx.mjs com --bed (nivelamento automático)')
        if loud: warn.append(f'{loud} hit(s) mais de 9 dB acima da trilha (pulam) — abaixe')

# ── loudness: cheia vs celular ──
I, TP = ebur(VIDEO)
Ip, _ = ebur(VIDEO, 'highpass=f=200:poles=2,lowpass=f=6000:poles=2')
say(f'\n## Loudness')
say(f'- integrado: {I} LUFS (meta −14) · true peak decodificado: {TP} dBTP (meta ≤ −1)')
say(f'- banda de celular 200 Hz–6 kHz: {Ip} LUFS · diferença {(Ip - I) if (I is not None and Ip is not None) else float("nan"):+.1f} dB')
if TP is not None and TP > -1.0: warn.append(f'true peak {TP} dBTP no MP4 decodificado — limite o WAV mais baixo (ex.: −2,2 dBTP) porque o AAC sobe o pico')
if I is not None and abs(I + 14) > 1: warn.append(f'loudness {I} LUFS fora de −14 ±1')
if I is not None and Ip is not None and Ip - I < -5: warn.append(f'banda de celular {Ip - I:+.1f} dB abaixo da cheia: energia demais no grave — suba médios (pad/pluck), oitava acima no baixo, kick com "knock" ~190 Hz')

# ── espectro e DC ──
F = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2; fq = np.fft.rfftfreq(len(mono), 1 / SR); tot = F.sum() + 1e-12
p60, p150, pmid = F[fq < 60].sum() / tot, F[fq < 150].sum() / tot, F[(fq >= 150) & (fq <= 6000)].sum() / tot
say(f'- energia: {100*p60:.1f}% < 60 Hz · {100*p150:.1f}% < 150 Hz · {100*pmid:.1f}% em 150 Hz–6 kHz')
if p60 > 0.4: warn.append(f'{100*p60:.0f}% da energia abaixo de 60 Hz (celular não toca isso)')
dc = dec.mean(0); say(f'- DC: L {dc[0]:+.5f} · R {dc[1]:+.5f}')
if np.max(np.abs(dc)) > 0.002: warn.append('DC no áudio — subtraia a média de cada canal')

if '--loop' in a:
    step = np.abs(dec[0] - dec[-1]).max(); say(f'- emenda do loop: degrau {step:.4f} (último→primeiro sample)')
    if step > 0.02: warn.append('degrau na emenda do loop: no MP4 de loop use fade raised-cosine de 2 ms nos 96 primeiros/últimos samples (export.sh --loop-fade); mantenha o WAV mestre sem fade')

say('\n## Veredito')
if warn:
    for w_ in warn: say(f'- ⚠ {w_}')
else:
    say('- ✔ sincronia, níveis e loudness dentro das metas')
say('\n> Áudio MEDIDO (picos, níveis, LUFS no arquivo decodificado), não ouvido. Vale uma escuta humana final.')
open(OUT, 'w').write('\n'.join(lines) + '\n')
print(f'→ {OUT}')
