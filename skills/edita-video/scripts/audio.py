#!/usr/bin/env python3
"""audio.py — o som da edição: voz montada e limpa, trilha com ducking, SFX do mapa, mixagem em loudness de entrega.

    python3 audio.py <projeto> [--sem-trilha] [--sem-sfx] [--lib <pasta de SFX gravados>] [--trilha audio/x.mp3]

1. VOZ: junta os trechos da timeline com fade de cortes.fade_ms (sem clique); limpeza por sintoma, na ordem
   subtrair → nivelar → caráter (references/som.md): passa-alta 80 Hz · ruído (arnndn/RNNoise se o piso > −60 dBFS,
   senão nada; afftdn sem o modelo) · −2 dB em 250 Hz (caixa) · +2 dB em 3 kHz (inteligibilidade) · de-esser ·
   compressor 3:1. som.voz = limpar | leve | nenhum. som.estalos = true → adeclick (estalos de boca, "clique" do QA).
   Quebra de padrão (item "efeito": "quebra" no mapa): a voz ganha reverb de sala e a trilha abafa (passa-baixa 700 Hz)
   só no intervalo, com rampas de 80 ms.
2. TRILHA: arquivo do cliente (loop com cruzamento) ou gerada no motion-studio (music.mjs, estilo pelo preset);
   sob a fala fica em voz + musica_db LU (−19 a −23); fora da fala (vão ≥ 0,6 s, abertura, final) sobe até 6 dB;
   ataque 0,15 s antes da 1ª sílaba, soltura 0,4 s. Fade in 0,4 s, fade out 1,5 s.
3. SFX: eventos_sfx.json → sfx.mjs do motion-studio (gravações de --lib/ORBE_SFX_LIB com prioridade; síntese de reserva),
   pico no evento + 1 quadro, nível relativo a voz+trilha (over negativo = abaixo da voz).
4. MIX: soma → ganho até som.lufs (−14 redes / −16 calmo) → limitador com oversampling a −1,5 dBTP; mede de novo.
Saídas: audio/voz.wav · audio/trilha.wav · audio/sfx.wav (stems já no nível do mix) · audio/mix.wav · docs/AUDIO.md
"""
import sys, os, json, subprocess, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
import numpy as np

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P); SOM = EST['som']; CORT = EST['cortes']
tl = E.jload(P / '_edit/timeline.json'); DUR = tl['duracao']; FPS = tl['fps']
inv = E.jload(P / '_edit/inventario.json'); FPS_STR = inv.get('fps_str', str(FPS))
SR = 48000; N = int(round(DUR * SR))
AD = P / 'audio'; AD.mkdir(exist_ok=True); TMP = P / '_edit/audio_tmp'; TMP.mkdir(exist_ok=True)
MS = E.motion_studio()
rel = []

def loud(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S)
    return {k: float(v) for k, v in json.loads(m.group(0)).items() if k.startswith('input_')} if m else {}
def ffaf(src, dst, af, stereo=False):
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-af', af, '-ar', str(SR), '-ac', '2' if stereo else '1', '-c:a', 'pcm_f32le', str(dst)])

# ── 1. VOZ ──
voz = np.zeros(N, np.float32); fade = int(CORT.get('fade_ms', 30) / 1000 * SR)
cache = {}
for s in tl['segmentos']:
    if s['clip'] not in cache: cache[s['clip']] = E.load_wav(P / '_edit/audio' / f"{s['clip']}.wav", SR)
    x = cache[s['clip']][int(round(s['src_in'] * SR)):int(round(s['src_out'] * SR))].copy()
    f = min(fade, len(x) // 4)
    if f > 1:
        r = np.sin(np.linspace(0, np.pi / 2, f)) ** 2; x[:f] *= r; x[-f:] *= r[::-1]
    a = int(round(s['seq_in'] * SR)); b = min(N, a + len(x)); voz[a:b] += x[:b - a]
E.save_wav(TMP / 'voz_montada.wav', voz, SR)
modo = SOM.get('voz', 'limpar')
env = E.rms_env(voz, SR, 0.05); piso = E.db(float(np.percentile(env[env > 1e-6], 5))) if (env > 1e-6).any() else -90
modelo = E.models_dir() / 'sh.rnnn'
cad = [x for x in E.cadeia_voz(EST, piso).split(',') if x]
if SOM.get('estalos'): cad = ['adeclick=w=55:o=75'] + cad
if cad: ffaf(TMP / 'voz_montada.wav', TMP / 'voz_limpa.wav', ','.join(cad))
else: shutil.copy(TMP / 'voz_montada.wav', TMP / 'voz_limpa.wav')
voz = E.load_wav(TMP / 'voz_limpa.wav', SR)[:N]; voz = np.pad(voz, (0, N - len(voz)))
LV = loud(TMP / 'voz_limpa.wav').get('input_i', -20)
MAPA = E.jload(P / '_edit/mapa.json', {}) or {}
QB = [(it['t_ini'], it['t_fim']) for it in MAPA.get('itens', []) if (it.get('efeito') == 'quebra' or it.get('quebra')) and it.get('t_ini') is not None]
QENV = np.zeros(N, np.float32)
for a, b in QB:
    i0, i1 = int(a * SR), min(N, int(b * SR)); r = int(0.08 * SR); QENV[i0:i1] = 1
    QENV[max(0, i0 - r):i0] = np.linspace(0, 1, i0 - max(0, i0 - r)); QENV[i1:min(N, i1 + r)] = np.linspace(1, 0, min(N, i1 + r) - i1)
if QB:
    ffaf(TMP / 'voz_limpa.wav', TMP / 'voz_rev.wav', 'aecho=0.8:0.82:47|89|163|251:0.30|0.22|0.15|0.09,highpass=f=120')
    rv = E.load_wav(TMP / 'voz_rev.wav', SR)[:N]; rv = np.pad(rv, (0, N - len(rv)))
    voz = voz * (1 - QENV) + rv * QENV
    rel.append(f"Quebra de padrão: {len(QB)} trecho(s) com reverb na voz e trilha abafada")
rel.append(f"Voz: {len(tl['segmentos'])} trechos, fade {CORT.get('fade_ms', 30)} ms · piso de ruído {piso:.0f} dBFS → {'RNNoise' if any('arnndn' in c for c in cad) else 'afftdn' if any('afftdn' in c for c in cad) else 'sem redução de ruído'} · cadeia: {modo} · {LV:.1f} LUFS antes do mix")

# máscara de fala (tempo da sequência)
fala = np.zeros(int(DUR * 100) + 2, bool)
ws = tl['palavras']; regs = []
for w in ws:
    a, b = max(0, w['s'] - 0.15), w['e'] + 0.30
    if regs and a - regs[-1][1] < 0.6: regs[-1][1] = max(regs[-1][1], b)
    else: regs.append([a, b])
for a, b in regs: fala[int(a * 100):int(b * 100) + 1] = True

# ── 2. TRILHA ──
mus = opt('trilha') or B.get('musica', 'gerar')
if '--sem-trilha' in A or mus in (False, 'nenhuma', 'nao', 'não'): mus = None
trilha = np.zeros((N, 2), np.float32)
if mus:
    src = None
    if isinstance(mus, str) and mus not in ('gerar',) and (P / mus).exists(): src = P / mus
    elif isinstance(mus, dict) and mus.get('arquivo') and (P / mus['arquivo']).exists(): src = P / mus['arquivo']
    else:
        g = mus.get('gerar', {}) if isinstance(mus, dict) else {}
        style = g.get('style') or SOM.get('trilha_estilo') or {'clinica-premium': 'warm', 'dinamico': 'tech', 'luxo': 'cinematic', 'educativo': 'minimal', 'varejo': 'warm', 'minimal': 'piano'}.get(ESTILO, 'warm')
        bpm = g.get('bpm') or {'tech': 118, 'warm': 96, 'cinematic': 84, 'minimal': 110, 'piano': 76}.get(style, 100)
        if MS:
            r = subprocess.run(['node', str(MS / 'scripts/music.mjs'), '--dur', f'{DUR + 1.5:.2f}', '--style', style, '--bpm', str(bpm), '--fps', str(FPS),
                                '--out', str(TMP / 'trilha_gerada.wav'), '--beats', str(TMP / 'beats.json')], capture_output=True, text=True)
            if r.returncode == 0: src = TMP / 'trilha_gerada.wav'; rel.append(f'Trilha: gerada no motion-studio ({style}, {bpm} BPM) — original, sem licença a pagar')
            else: rel.append('⚠ trilha: music.mjs falhou — sem trilha'); print(r.stderr[-400:])
        else: rel.append('⚠ trilha: motion-studio ausente — sem trilha')
    if src:
        y = E.run(['ffmpeg', '-v', 'error', '-i', str(src), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], text=False).stdout
        y = np.frombuffer(y, np.float32).reshape(-1, 2).copy()
        if len(y) < N:      # loop com cruzamento de 1 s
            cf = min(SR, len(y) // 4); out = y.copy()
            while len(out) < N:
                r = np.linspace(0, 1, cf)[:, None]; out[-cf:] = out[-cf:] * (1 - r) + y[:cf] * r; out = np.concatenate([out, y[cf:]])
            y = out
        y = y[:N]; fi, fo = int(0.4 * SR), int(1.5 * SR)
        y[:fi] *= np.linspace(0, 1, fi)[:, None]; y[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
        E.save_wav(TMP / 'trilha_base.wav', y, SR); LM = loud(TMP / 'trilha_base.wav').get('input_i', -20)
        alvo = LV + SOM.get('musica_db', -21); g0 = 10 ** ((alvo - LM) / 20)
        sobe = 10 ** (min(SOM.get('duck_db', 6), 6) / 20)
        tgt = np.where(fala, 1.0, sobe).astype(np.float64)
        sm = np.empty_like(tgt); v = tgt[0]; aa, rr = 1 - np.exp(-1 / (0.15 * 100)), 1 - np.exp(-1 / (0.40 * 100))
        for i, x in enumerate(tgt):     # desce rápido (ataque), sobe devagar (soltura)
            v += (x - v) * (aa if x < v else rr); sm[i] = v
        # antecipa a descida: a trilha já está baixa quando a sílaba começa
        sm = np.minimum(sm, np.concatenate([sm[15:], np.full(15, sm[-1])]))
        envs = np.interp(np.arange(N) / SR, np.arange(len(sm)) / 100, sm).astype(np.float32)
        trilha = y * (g0 * envs)[:, None]
        if QB:
            from scipy.signal import butter, sosfiltfilt
            ab = sosfiltfilt(butter(4, 700, 'low', fs=SR, output='sos'), trilha, axis=0).astype(np.float32)
            trilha = trilha * (1 - QENV[:, None]) + ab * QENV[:, None] * 1.25
        if not any('Trilha' in x for x in rel): rel.append(f'Trilha: {src.name}')
        rel.append(f"Trilha sob a fala: {alvo:.1f} LUFS ({SOM.get('musica_db', -21)} LU da voz) · sobe {20 * np.log10(sobe):.0f} dB fora da fala · ataque 0,15 s / soltura 0,4 s")

# ── 3. SFX ──
sfx = np.zeros((N, 2), np.float32)
evs = (E.jload(P / '_edit/eventos_sfx.json', {}) or {}).get('cues', [])
if evs and '--sem-sfx' not in A and MS:
    bed = np.stack([voz, voz], 1) + trilha; E.save_wav(TMP / 'bed.wav', bed, SR)
    cj = TMP / 'cues.json'; json.dump([{k: c[k] for k in ('t', 'type', 'gain', 'pan', 'over') if k in c} for c in evs], open(cj, 'w'))
    lib = opt('lib') or os.environ.get('ORBE_SFX_LIB') or B.get('sfx_lib')
    cmd = ['node', str(MS / 'scripts/sfx.mjs'), str(cj), '--dur', f'{DUR:.4f}', '--fps', str(FPS_STR), '--out', str(TMP / 'sfx.wav'), '--bed', str(TMP / 'bed.wav'), '--bed-db', '0']
    if lib and os.path.isdir(lib): cmd += ['--lib', lib]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: rel.append('⚠ SFX: sfx.mjs falhou'); print(r.stderr[-500:])
    else:
        y = E.run(['ffmpeg', '-v', 'error', '-i', str(TMP / 'sfx.wav'), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], text=False).stdout
        y = np.frombuffer(y, np.float32).reshape(-1, 2)[:N]; sfx[:len(y)] = y
        shutil.copy(TMP / 'sfx_cues.json', AD / 'sfx_cues.json') if (TMP / 'sfx_cues.json').exists() else None
        rel.append(f"SFX: {len(evs)} efeitos ({'gravados de ' + lib if lib and os.path.isdir(lib) else 'síntese do motion-studio — para cliente, prefira biblioteca gravada (--lib)'})")

FIMF = float((EST.get('fim') or {}).get('fade_preto', 0) or 0)
if FIMF and len(trilha):      # fecha no preto: a trilha desce junto com a imagem
    nf = min(len(trilha), int(FIMF * SR)); trilha[-nf:] *= np.linspace(1, 0, nf)[:, None] ** 1.5
# ── 4. MIX + loudness ──
pre = np.stack([voz, voz], 1) + trilha + sfx
E.save_wav(TMP / 'pre.wav', pre, SR)
alvo = SOM.get('lufs', -14); Li = loud(TMP / 'pre.wav').get('input_i', -20); ganho = alvo - Li; lim = -1.5
for _ in range(3):
    lv = 10 ** (lim / 20)
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(TMP / 'pre.wav'), '-af', f'volume={ganho:.2f}dB,aresample=192000,alimiter=limit={lv:.4f}:attack=1:release=50:level=false,aresample=48000',
           '-c:a', 'pcm_s24le', str(AD / 'mix.wav')])
    m = loud(AD / 'mix.wav')
    if abs(m.get('input_i', alvo) - alvo) <= 0.5 and m.get('input_tp', -9) <= -1.0: break
    ganho += alvo - m.get('input_i', alvo); lim -= 0.3 if m.get('input_tp', -9) > -1.0 else 0
gl = 10 ** (ganho / 20)
for nome, x in (('voz', np.stack([voz, voz], 1)), ('trilha', trilha), ('sfx', sfx)):
    E.save_wav(AD / f'{nome}.wav', x * gl, SR)
# voz × resto: a fala tem de mandar (SFX/trilha acima da voz = bug)
def pico_db(x): return E.db(float(np.max(np.abs(x))) + 1e-9)
k = int(SR * 0.4); fal = np.repeat(fala, SR // 100)[:N] if len(fala) * (SR // 100) >= N else np.pad(np.repeat(fala, SR // 100), (0, N))[:N]
rv = E.db(float(np.sqrt(np.mean(voz[fal[:len(voz)]] ** 2))) + 1e-9) if fal.any() else -90
rt = E.db(float(np.sqrt(np.mean(trilha[fal[:len(trilha)]] ** 2))) + 1e-9) if fal.any() else -90
rel.append(f"MIX: {m.get('input_i', 0):.1f} LUFS (alvo {alvo}) · pico real {m.get('input_tp', 0):.1f} dBTP · LRA {m.get('input_lra', 0):.1f} · trilha {rv - rt:.0f} dB abaixo da voz durante a fala")
if sfx.any():
    ps, pv = pico_db(sfx), pico_db(voz)
    rel.append(f"SFX pico {ps:.1f} dBFS vs voz {pv:.1f} dBFS" + (' ⚠ SFX mais alto que a voz — baixe (eventos.py --ajuste)' if ps > pv else ''))
(P / 'docs/AUDIO.md').write_text('# Áudio (medido, não ouvido)\n\n' + '\n'.join(f'- {x}' for x in rel) + '\n', encoding='utf-8')
print('\n'.join(rel)); E.log_estado(P, 'som', 'feito', f"{m.get('input_i', 0):.1f} LUFS")
