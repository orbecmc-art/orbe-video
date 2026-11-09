#!/usr/bin/env python3
"""Sonoplastia em que cada contato do objeto é uma nota, e a trilha nasce em volta deles. Veio do filme "A bola" da Ligare.

    python3 audio/compor.py

shortcut: o arranjo em main() tem batidas fixas daquele filme (drop em 24, groove até 88, pausa em 80, final em 92) e progressão em ré.
Ajuste a cada filme; os instrumentos, a mesa e a posição pelo ataque valem para qualquer um.
Precisa de "rota" em campaign.json: [{ "b": batida, "s": timbre, "n": nota ou lista, "g": ganho, "x": posição, "sala": envio }].
Timbres: pluck madeira chao vidro check xilo kalimba botao ding. A tabela SONS aceita novos.

Lê a rota de campaign.json (e audio/rota-xy.json, se existir, para o panorama seguir a bola).
Grava audio/trilha.wav (cama), audio/toques.wav (contatos e ar), audio/mix-previa.wav e audio/beats.json.
Tudo é sintetizado aqui: nenhum sample de terceiros, então não há licença a conferir.
"""
import json
import re
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

AQUI = Path(__file__).resolve().parent
PECA = AQUI.parent
CP = json.loads((PECA / 'campaign.json').read_text())
SR, BPM = 48000, CP['bpm']
B = 60 / BPM
DUR = CP['duration'] + 2.5
N = int(DUR * SR)
LAG = 1 / 60                         # o pico do som cai 1 frame depois da imagem
GANHO_TRILHA, GANHO_TOQUES = 0.36, 0.56
RNG = np.random.default_rng(23)
NOTAS = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(nome):
    m = re.fullmatch(r'([A-G][#b]?)(-?\d)', nome)
    return 440.0 * 2 ** ((NOTAS[m.group(1)] + 12 * (int(m.group(2)) + 1) - 69) / 12)


def tempo(d):
    return np.arange(int(d * SR)) / SR


def filtro(x, kind, fc, ordem=2):
    fc = np.clip(fc, 10, SR / 2 * 0.98)
    return sosfilt(butter(ordem, fc, kind, fs=SR, output='sos'), x)


def ruido(d):
    return RNG.standard_normal(int(d * SR))


def env(t, ataque, queda):
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / queda)


def serra(f, t, detune=0.0):
    fase = (f * (1 + detune) * t + RNG.random()) % 1
    return 2 * fase - 1


# ───────── instrumentos dos contatos: cada superfície tem o próprio timbre ─────────
def vidro(f, d=1.1):
    """Sino de vidro em FM: as bolhas de conversa."""
    t = tempo(d)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t / 0.09)
    x = np.sin(2 * np.pi * f * t + mod) * env(t, 0.001, 0.32) + 0.25 * np.sin(2 * np.pi * f * 2.003 * t) * env(t, 0.001, 0.16)
    return x + 0.25 * filtro(ruido(d), 'highpass', 6000) * np.exp(-t / 0.004)


def marimba(f, d=0.7):
    """Modos de uma tecla de madeira: as caixas de tarefa."""
    t = tempo(d)
    x = sum(a * np.sin(2 * np.pi * f * r * t) * env(t, 0.0008, q) for r, a, q in [(1, 1, 0.20), (3.93, 0.45, 0.06), (9.2, 0.16, 0.018)])
    return x + 0.2 * sosfilt(butter(2, [900, 4000], 'bandpass', fs=SR, output='sos'), ruido(d)) * np.exp(-t / 0.003)


def xilo(f, d=0.9):
    """Xilofone metálico: as barras do gráfico da Elisa."""
    t = tempo(d)
    return sum(a * np.sin(2 * np.pi * f * r * t) * env(t, 0.0005, q) for r, a, q in [(1, 1, 0.30), (3.0, 0.5, 0.14), (6.27, 0.28, 0.05), (9.4, 0.12, 0.02)])


def kalimba(f, d=1.4):
    """Lâmina dedilhada: os agentes do time."""
    t = tempo(d)
    x = sum(a * np.sin(2 * np.pi * f * r * t) * env(t, 0.0015, q) for r, a, q in [(1, 1, 0.42), (2.01, 0.28, 0.2), (5.43, 0.16, 0.035)])
    return x + 0.3 * sosfilt(butter(2, [1500, 7000], 'bandpass', fs=SR, output='sos'), ruido(d)) * np.exp(-t / 0.002)


def pluck(f, d=1.3, abafado=0.9965):
    """Corda de Karplus-Strong: as palavras do gancho."""
    n = int(d * SR)
    per = max(2, int(SR / f))
    buf = RNG.uniform(-1, 1, per)
    buf = filtro(np.tile(buf, 4), 'lowpass', 5000)[-per:]
    y = np.zeros(n)
    y[:per] = buf
    for i in range(per, n):
        y[i] = abafado * 0.5 * (y[i - per] + y[i - per - 1])
    return y


def madeira(f, d=0.5):
    """Bloco abafado: os cartões que falham no problema."""
    t = tempo(d)
    x = np.sin(2 * np.pi * f * t) * env(t, 0.001, 0.09) + 0.5 * np.sin(2 * np.pi * f * 2.4 * t) * env(t, 0.001, 0.03)
    return x + 0.35 * sosfilt(butter(2, [400, 2500], 'bandpass', fs=SR, output='sos'), ruido(d)) * np.exp(-t / 0.006)


def chao(f=55.0, d=0.7):
    """A bola batendo no chão: grave com corpo, porque o telefone precisa do 'knock'."""
    t = tempo(d)
    queda = f * (1 + 2.5 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(queda) / SR) * env(t, 0.001, 0.16) + 0.5 * np.sin(2 * np.pi * 210 * t) * env(t, 0.001, 0.035)
    return np.tanh(1.6 * x) + 0.3 * filtro(ruido(d), 'lowpass', 1800) * np.exp(-t / 0.008)


def botao(f, d=0.6):
    """Clique tátil com nota: botões e interruptores."""
    t = tempo(d)
    clique = filtro(ruido(d), 'highpass', 2500) * np.exp(-t / 0.0025)
    corpo = np.sin(2 * np.pi * 180 * t) * env(t, 0.0005, 0.018)
    return 0.7 * clique + 0.8 * corpo + 0.8 * vidro(f, d)


def acorde_vidro(notas, d=1.8):
    return sum(vidro(hz(n), d) * 0.7 for n in notas)


def ding(f, d=1.6):
    t = tempo(d)
    return sum(a * np.sin(2 * np.pi * f * r * t) * env(t, 0.001, q) for r, a, q in [(1, 1, 0.6), (2.0, 0.5, 0.35), (3.01, 0.3, 0.18), (5.4, 0.14, 0.06)])


def impacto(d=2.4):
    """Impacto do drop: sub que cai, corpo e ar."""
    t = tempo(d)
    f = 46 + 110 * np.exp(-t / 0.07)
    sub = np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(t, 0.001, 0.34)
    corpo = filtro(ruido(d), 'lowpass', 1400) * np.exp(-t / 0.07)
    knock = np.sin(2 * np.pi * 205 * t) * env(t, 0.001, 0.08) + 0.5 * np.sin(2 * np.pi * 410 * t) * env(t, 0.001, 0.05)
    return 0.8 * sub + 0.7 * corpo + 0.8 * knock


def prato(d=3.0, g=1.0):
    t = tempo(d)
    return g * filtro(ruido(d), 'highpass', 5200) * env(t, 0.002, 0.8)


def subida(d, ini=300.0, fim=8000.0, g=1.0):
    """Ruído que abre: a tensão antes do drop."""
    n = int(d * SR)
    x = ruido(d)
    saida = np.zeros(n)
    bloco = 512
    for i in range(0, n, bloco):
        p = i / n
        fc = ini * (fim / ini) ** (p ** 1.6)
        saida[i:i + bloco] = sosfilt(butter(2, [fc * 0.7, min(fc * 1.3, SR / 2 * 0.95)], 'bandpass', fs=SR, output='sos'), x[i:i + bloco])
    return g * saida * np.linspace(0, 1, n) ** 2.2


def tom(f, d=0.35):
    t = tempo(d)
    fq = f * (1 + 0.5 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(fq) / SR) * env(t, 0.001, 0.12) + 0.2 * filtro(ruido(d), 'lowpass', 3000) * np.exp(-t / 0.01)


def ar(d, g=1.0):
    """A bola cortando o ar: sopro com a frequência acompanhando a velocidade do voo (parábola)."""
    n = int(d * SR)
    x = ruido(d)
    p = np.linspace(0, 1, n)
    vel = np.abs(2 * p - 1)                # rápida nas pontas, lenta no topo do arco
    saida = np.zeros(n)
    bloco = 512
    for i in range(0, n, bloco):
        fc = 700 + 2600 * vel[i]
        saida[i:i + bloco] = sosfilt(butter(1, [fc * 0.6, fc * 1.5], 'bandpass', fs=SR, output='sos'), x[i:i + bloco])
    return g * saida * (0.25 + vel ** 2) * np.sin(np.pi * p) ** 0.5


SONS = {
    'pluck': lambda n: pluck(hz(n)), 'madeira': lambda n: madeira(hz(n)), 'chao': lambda n: chao(hz(n)),
    'vidro': lambda n: vidro(hz(n)), 'check': lambda n: marimba(hz(n)), 'xilo': lambda n: xilo(hz(n)),
    'kalimba': lambda n: kalimba(hz(n)), 'botao': lambda n: botao(hz(n)), 'ding': lambda n: ding(hz(n)),
}


# ───────── mesa ─────────
def coloca(buf, t, x, g=1.0, pan=0.0, pico=True):
    """Soma x em buf com o pico medido em t + 1 frame; panorama de igual potência."""
    # alinha pelo ataque (primeiros 8 ms): num sino o pico global vem depois e o som chegaria antes da imagem
    desloc = int(np.argmax(np.abs(x[: int(0.008 * SR)]))) if pico else 0
    a = int(round((t + LAG if pico else t) * SR)) - desloc
    if a < 0:
        x, a = x[-a:], 0
    b = min(N, a + len(x))
    if b <= a:
        return
    ang = (pan + 1) * np.pi / 4
    buf[a:b, 0] += g * np.cos(ang) * x[: b - a]
    buf[a:b, 1] += g * np.sin(ang) * x[: b - a]


def sala(d=1.9, cor=5200.0, semente=7):
    r = np.random.default_rng(semente)
    n = int(d * SR)
    t = np.arange(n) / SR
    ir = np.stack([r.standard_normal(n), r.standard_normal(n)], axis=1) * np.exp(-t / (d / 6.9))[:, None]
    ir = sosfilt(butter(1, cor, 'lowpass', fs=SR, output='sos'), ir, axis=0)
    ir = sosfilt(butter(1, 260, 'highpass', fs=SR, output='sos'), ir, axis=0)
    ir[: int(0.018 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(axis=0))


def com_sala(seco, envio, d=1.9, cor=5200.0):
    ir = sala(d, cor)
    molhado = np.stack([fftconvolve(envio[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
    return seco + molhado


def eco(buf, tempo_s, volta=0.42, vezes=4, cruzado=True):
    saida = np.zeros_like(buf)
    d = int(tempo_s * SR)
    for k in range(1, vezes + 1):
        g = volta ** k
        c = buf[:-d * k] * g
        if cruzado and k % 2:
            c = c[:, ::-1]
        saida[d * k:] += c
    return saida


# ───────── harmonia ─────────
MENOR = [('D3', 'F3', 'A3', 'C4'), ('Bb2', 'D3', 'F3', 'A3'), ('G2', 'Bb2', 'D3', 'F3'), ('A2', 'C#3', 'E3', 'G3')]
MAIOR = [('D3', 'F#3', 'A3', 'E4'), ('A2', 'C#3', 'E3', 'B3'), ('B2', 'D3', 'F#3', 'A3'), ('G2', 'B2', 'D3', 'F#3')]
BAIXO = ['D2', 'A1', 'B1', 'G1']


def acorde_em(b):
    return MAIOR[int((b - 24) // 4) % 4], BAIXO[int((b - 24) // 4) % 4]


def pad(notas, d, cor=1500.0, g=1.0):
    t = tempo(d)
    L, R = np.zeros(len(t)), np.zeros(len(t))
    for n in notas:
        f = hz(n)
        for det in (-0.004, 0.0, 0.0045):
            L += serra(f, t, det)
            R += serra(f, t, det * -1.1 + 0.0011)
    forma = np.minimum(1, t / 0.18) * np.minimum(1, (d - t) / 0.28)
    return np.stack([filtro(L, 'lowpass', cor), filtro(R, 'lowpass', cor)], axis=1) * (forma * g / (3 * len(notas)))[:, None]


def baixo(f, d):
    t = tempo(d)
    x = 0.42 * np.sin(2 * np.pi * f * t) + 0.62 * serra(f, t) + 0.34 * serra(f * 2, t, 0.002)
    corte = 420 + 1800 * np.exp(-t / 0.08)
    saida = np.zeros(len(t))
    for i in range(0, len(t), 256):
        saida[i:i + 256] = sosfilt(butter(2, corte[i], 'lowpass', fs=SR, output='sos'), x[i:i + 256])
    return np.tanh(1.5 * saida) * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.012)


def bumbo():
    d = 0.34
    t = tempo(d)
    f = 58 + 120 * np.exp(-t / 0.026)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(t, 0.0006, 0.095)
    knock = np.sin(2 * np.pi * 210 * t) * env(t, 0.0006, 0.03)
    return np.tanh(1.5 * (0.8 * x + 0.8 * knock)) + 0.34 * filtro(ruido(d), 'highpass', 3500) * np.exp(-t / 0.0025)


def palma():
    d = 0.32
    t = tempo(d)
    x = sum(np.where(t >= o, np.exp(-(t - o) / 0.006), 0) for o in (0, 0.011, 0.023)) + 0.8 * np.exp(-t / 0.075)
    return sosfilt(butter(2, [900, 4600], 'bandpass', fs=SR, output='sos'), ruido(d)) * x


def chimbal(queda=0.022, d=0.16):
    t = tempo(d)
    return filtro(ruido(d), 'highpass', 7600) * env(t, 0.0005, queda)


def main():
    if not CP.get('rota'):
        raise SystemExit('campaign.json sem "rota": escreva os contatos antes de compor')
    rota = CP['rota']
    xy = {}
    if (AQUI / 'rota-xy.json').exists():
        xy = {round(r['b'], 3): r for r in json.loads((AQUI / 'rota-xy.json').read_text())}

    cama, envio_cama, toques, envio_toques = (np.zeros((N, 2)) for _ in range(4))
    pads, grave = np.zeros((N, 2)), np.zeros((N, 2))
    kicks = []

    # 1) problema em ré menor: só um chão escuro embaixo dos toques
    for i in range(4):
        d = B * 4 + 0.3
        coloca(pads, i * 4 * B, pad(MENOR[i], d, cor=520, g=0.5)[:, 0], g=1, pan=-0.25, pico=False)
        coloca(pads, i * 4 * B, pad(MENOR[i], d, cor=520, g=0.5)[:, 1], g=1, pan=0.25, pico=False)
    for b in range(0, 16, 2):
        coloca(cama, b * B, tom(hz('D2'), 0.5), g=0.24 * (1 - b / 22))

    # 2) tensão de 4 batidas antes do drop de 24
    r = subida(B * 4)
    coloca(cama, 20 * B, r, g=0.42, pan=-0.15, pico=False)
    coloca(cama, 20 * B, subida(B * 4), g=0.42, pan=0.15, pico=False)
    for b, f in zip([20, 21, 22, 22.5, 23, 23.25, 23.5, 23.75], ['D2', 'D2', 'F2', 'F2', 'A2', 'A2', 'C3', 'D3']):
        coloca(cama, b * B, tom(hz(f)), g=0.55)
        coloca(envio_cama, b * B, tom(hz(f)), g=0.2)

    # 3) groove em ré maior, em camadas que entram ao longo do produto
    MUDO = [(80, 81)]
    def tocando(b, ini, fim=88):
        return ini <= b < fim and not any(a <= b < z for a, z in MUDO)

    for bq in np.arange(24, 88, 0.25):
        b = float(bq)
        (notas, raiz) = acorde_em(b)
        if b % 4 == 0 and tocando(b, 24):
            cor = 900 + 1500 * min(1, (b - 24) / 48) + (1500 if b >= 81 else 0)
            p = pad(notas, B * 4 + 0.25, cor=cor, g=0.72 if b >= 32 else 0.95)
            pads[int(b * B * SR): int(b * B * SR) + len(p)] += p[: max(0, N - int(b * B * SR))]
        if b % 1 == 0 and (tocando(b, 32) or (tocando(b, 24, 32) and b % 4 == 0)):
            coloca(cama, b * B, bumbo(), g=0.9)
            kicks.append(b * B)
        if tocando(b, 32) and b % 1 == 0.5:
            coloca(grave, b * B, baixo(hz(raiz), B * 0.44), g=0.62, pico=False)
        if tocando(b, 56) and b % 1 == 0.75:
            coloca(grave, b * B, baixo(hz(raiz) * 2, B * 0.2), g=0.36, pico=False)
        if tocando(b, 40) and b % 2 == 1:
            coloca(cama, b * B, palma(), g=0.45)
            coloca(envio_cama, b * B, palma(), g=0.22)
        if tocando(b, 32) and b % 1 == 0.5:
            coloca(cama, b * B, chimbal(0.075, 0.25), g=0.2, pan=0.15)
        if tocando(b, 40):
            coloca(cama, b * B, chimbal(0.014), g=0.12 if b % 0.5 else 0.17, pan=-0.2 + 0.4 * ((b * 4) % 2))
        if tocando(b, 48, 80) or tocando(b, 81):
            passo = int((b * 4) % 8)
            ordem = [0, 2, 1, 3, 2, 1, 3, 2]
            f = hz(notas[ordem[passo] % len(notas)]) * 4
            coloca(envio_cama, b * B, pluck(f, 0.42, 0.989), g=0.1, pan=-0.45 + 0.9 * ((b * 4) % 2))
            coloca(cama, b * B, pluck(f, 0.42, 0.989), g=0.085, pan=-0.45 + 0.9 * ((b * 4) % 2))
    coloca(cama, 24 * B, impacto(), g=0.85)
    coloca(cama, 24 * B, prato(3.2), g=0.2, pico=False)
    coloca(envio_cama, 24 * B, prato(3.2), g=0.12, pico=False)

    # 4) subida de 72 a 80, silêncio de uma batida, e a queda do preço em 81
    coloca(cama, 72 * B, subida(B * 8, 500, 9000), g=0.3, pan=-0.2, pico=False)
    coloca(cama, 72 * B, subida(B * 8, 500, 9000), g=0.3, pan=0.2, pico=False)
    for k, b in enumerate(np.arange(76, 80, 0.25)):
        coloca(cama, float(b) * B, palma(), g=0.1 + 0.3 * k / 16)
    coloca(cama, 81 * B, impacto(3.0), g=1.0)
    coloca(cama, 81 * B, prato(3.4), g=0.26, pico=False)
    coloca(envio_cama, 81 * B, prato(3.4), g=0.15, pico=False)

    # 5) respiro de 88 a 92 e acorde final em 92: a bola volta para a assinatura
    p = pad(('D3', 'A3', 'E4', 'F#4'), B * 4 + 0.3, cor=2400, g=0.85)
    a = int(88 * B * SR)
    pads[a: a + len(p)] += p
    coloca(cama, 88 * B, subida(B * 4, 400, 6000), g=0.26, pico=False)
    fim = pad(('D3', 'A3', 'D4', 'F#4', 'A4'), DUR - 92 * B, cor=2800, g=1.0)
    a = int(92 * B * SR)
    fim = fim * np.linspace(1, 0, len(fim))[:, None] ** 0.7
    pads[a: a + len(fim)] += fim[: N - a]
    coloca(cama, 92 * B, impacto(3.0), g=0.8)
    coloca(cama, 92 * B, prato(3.6), g=0.18, pico=False)
    coloca(envio_cama, 92 * B, prato(3.6), g=0.12, pico=False)
    for b in range(92, 100):
        coloca(cama, (b + 0.5) * B, chimbal(0.05, 0.2), g=0.1 * (1 - (b - 92) / 9), pan=0.15)
    coloca(grave, 92 * B, baixo(hz('D2'), B * 8), g=0.6, pico=False)

    # o bumbo empurra pad, baixo e arpejo: o "respirar" da trilha
    sc = np.ones(N)
    for k in kicks:
        a = int(k * SR)
        n = int(0.24 * SR)
        t = np.arange(n) / n
        sc[a: a + n] = np.minimum(sc[a: a + n], 0.42 + 0.58 * t ** 0.7)
    pads *= sc[:, None]
    grave *= (0.55 + 0.45 * sc)[:, None]
    envio_cama += pads * 0.25
    cama = com_sala(cama + pads + grave, envio_cama, 2.2, 4200)

    # ───────── os contatos: panorama pela posição da bola ─────────
    anterior = None
    for c in rota:
        b, som, nota = c['b'], c['s'], c.get('n')
        r = xy.get(round(b, 3), c)
        pan = float(np.clip((r.get('x', 540) - 540) / 620, -0.85, 0.85))
        g = c.get('g', 0.7)
        t = b * B
        notas = nota if isinstance(nota, list) else [nota]
        for n in notas:
            x = SONS[som](n)
            x = x / np.abs(x).max()
            coloca(toques, t, x, g=g / len(notas) ** 0.5, pan=pan)
            coloca(envio_toques, t, x, g=g * c.get('sala', 0.55) / len(notas) ** 0.5, pan=pan)
        if anterior is not None and b - anterior[0] >= 0.75:
            d = (b - anterior[0]) * B
            voo = ar(d)
            voo = voo / max(np.abs(voo).max(), 1e-6)
            coloca(toques, anterior[0] * B, voo, g=min(0.11, 0.05 + 0.03 * d * 2), pan=(pan + anterior[1]) / 2, pico=False)
        anterior = (b, pan)
    toques = com_sala(toques, envio_toques, 1.7, 6200) + eco(envio_toques, B * 0.75, 0.33, 3) * 0.3

    # master: tira o sub que o telefone não toca, equilibra e só encosta no limite nos impactos
    corte = butter(2, 38, 'highpass', fs=SR, output='sos')
    cama, toques = sosfilt(corte, cama, axis=0), sosfilt(corte, toques, axis=0)
    cama, toques = cama * GANHO_TRILHA, toques * GANHO_TOQUES
    for nome, x in [('trilha', cama), ('toques', toques)]:
        wavfile.write(str(AQUI / f'{nome}.wav'), SR, (x - x.mean(axis=0)).astype(np.float32))
    previa = cama + toques
    previa = np.tanh(previa * 1.15) / 1.15
    wavfile.write(str(AQUI / 'mix-previa.wav'), SR, (previa / np.abs(previa).max() * 0.89).astype(np.float32))
    cues = [{'t': round(c['b'] * B, 5), 'type': c['s'], 'target': round(c['b'] * B + LAG, 5)} for c in rota]
    (AQUI / 'toques_cues.json').write_text(json.dumps({'fps': 60, 'cues': cues}))
    batidas = [round(i * B, 5) for i in range(int(CP['duration'] / B))]
    (AQUI / 'beats.json').write_text(json.dumps({'bpm': BPM, 'duration': CP['duration'], 'beats': batidas, 'downbeats': batidas[::4], 'hits': []}))
    print(f'{len(rota)} contatos, {DUR:.1f} s, pico trilha {np.abs(cama).max():.2f}, toques {np.abs(toques).max():.2f}')


if __name__ == '__main__':
    main()
