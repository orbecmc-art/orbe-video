#!/usr/bin/env node
/* music.mjs — trilha original sintetizada em código, já com a grade rítmica exata (beats.json).
 * Nada de "pad genérico": percussão física, baixo com sidechain, pluck Karplus-Strong, piano aditivo.
 *
 *   node music.mjs --bpm 120 --structure "intro:2,build:2,drop:4,outro:1" --style tech --key A --scale minor
 *   node music.mjs --dur 15 --style piano                     # calcula compassos pela duração
 *   Saída: --out audio/music.wav (estéreo 48k) e --beats audio/beats.json
 *
 * Estilos: tech (pulsante, UI/produto) · warm (pop orgânico) · piano (emocional, story) ·
 *          minimal (clicks + sub, para UI morph) · cinematic (hits, braams, riser — trailers)
 * Seções:  intro (leve) · build (sobe, riser no fim) · drop (tudo) · break (só harmonia) · outro (resolve, impacto final)
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const SR = 48000;
// percussão com PICO em batida + 1 frame (mesma regra do sfx.mjs: luz antes do som). beats.json guarda o tempo da IMAGEM.
const LAG = Number(opt('lag-frames', 1)) / Number(opt('fps', 60));
const BPM = Number(opt('bpm', 120));
const SPB = 60 / BPM, BAR = SPB * 4;
const STYLE = opt('style', 'tech');
const KEY = opt('key', 'A'), SCALE = opt('scale', STYLE === 'warm' ? 'major' : 'minor');
let structure = opt('structure');
if (!structure) {
  const bars = Math.max(2, Math.round(Number(opt('dur', 15)) / BAR));
  const intro = Math.max(1, Math.round(bars * 0.15)), outro = 1, build = Math.max(1, Math.round(bars * 0.2));
  structure = `intro:${intro},build:${build},drop:${Math.max(1, bars - intro - build - outro)},outro:${outro}`;
}
const sections = structure.split(',').map((s) => { const [name, n] = s.split(':'); return { name, bars: Number(n) }; });
const totalBars = sections.reduce((a, s) => a + s.bars, 0);
const DUR = totalBars * BAR + 2.5; // cauda para reverb/impacto
const N = Math.ceil(DUR * SR);
const L = new Float32Array(N), R = new Float32Array(N), SEND = new Float32Array(N), DUCK = new Float32Array(N).fill(1);

let seed = Number(opt('seed', 7));
const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
const noise = () => rnd() * 2 - 1;
const NOTE = { C: 0, 'C#': 1, D: 2, 'D#': 3, E: 4, F: 5, 'F#': 6, G: 7, 'G#': 8, A: 9, 'A#': 10, B: 11 };
const midi = (m) => 440 * Math.pow(2, (m - 69) / 12);
const root = 57 + ((NOTE[KEY] ?? 9) - 9); // A3 = 57
const SCALES = { minor: [0, 2, 3, 5, 7, 8, 10], major: [0, 2, 4, 5, 7, 9, 11] };
const sc = SCALES[SCALE] || SCALES.minor;
// progressões em graus (0 = tônica)
const PROG = SCALE === 'major' ? [0, 4, 5, 3] : [0, 5, 2, 6]; // I-V-vi-IV | i-VI-III-VII
const chordAt = (bar) => { const d = PROG[bar % PROG.length]; return [0, 2, 4].map((k) => { const s = d + k; return root + sc[s % 7] + 12 * Math.floor(s / 7); }); };

const peakIdx = (buf) => { let p = 0, v = 0; const n = Math.min(buf.length, Math.round(0.08 * SR)); for (let i = 0; i < n; i++) { const a = Math.abs(buf[i]); if (a > v) { v = a; p = i; } } return p; };
const hit = (t, buf, ...rest) => add(t + LAG - peakIdx(buf) / SR, buf, ...rest);   // alinha o pico, não o início
function add(t, buf, gain = 1, pan = 0, send = 0) { // buf: Float32Array mono
  const s0 = Math.floor(t * SR), gl = gain * Math.cos((pan + 1) * Math.PI / 4), gr = gain * Math.sin((pan + 1) * Math.PI / 4);
  for (let i = 0; i < buf.length; i++) { const j = s0 + i; if (j < 0 || j >= N) continue; L[j] += buf[i] * gl; R[j] += buf[i] * gr; SEND[j] += buf[i] * send * gain; }
}
const synth = (len, fn) => { const b = new Float32Array(Math.floor(len * SR)); for (let i = 0; i < b.length; i++) b[i] = fn(i / SR, i); return b; };

// ── instrumentos ──
// kick curto + "knock" em ~190 Hz: o sub some no celular, o knock é o que se ouve no telefone
const kick = () => { let ph = 0; return synth(0.3, (t) => { ph += 2 * Math.PI * (52 + 100 * Math.exp(-t * 30)) / SR; return Math.sin(ph) * Math.exp(-t * 14) * 0.85 + Math.cos(2 * Math.PI * 190 * t) * Math.exp(-t * 45) * 0.55 + (t < 0.003 ? noise() * 0.35 : 0); }); };
const snare = () => { let lp = 0; return synth(0.25, (t) => { const n = noise(); lp += (n - lp) * 0.35; return ((n - lp) * Math.exp(-t * 18) * 0.55 + Math.sin(2 * Math.PI * 190 * t) * Math.exp(-t * 30) * 0.4); }); };
const clap = () => { let lp = 0; return synth(0.3, (t) => { const n = noise(); lp += (n - lp) * 0.25; const env = [0, 0.011, 0.022].reduce((a, o) => a + (t >= o ? Math.exp(-(t - o) * 90) : 0), 0) * 0.5 + (t > 0.022 ? Math.exp(-(t - 0.022) * 14) : 0); return (n - lp) * env * 0.5; }); };
const hat = (open = false) => { let p = 0; return synth(open ? 0.22 : 0.05, (t) => { const n = noise(); const h = n - p; p = n; return h * Math.exp(-t * (open ? 16 : 70)) * 0.22; }); };
// baixo: senoide reduzida, saw mais aberto (~1,2 kHz) → harmônicos que aparecem no alto-falante pequeno
const bass = (f, len) => { let lp = 0; return synth(len, (t) => { const ph = (f * t) % 1; const saw = 2 * ph - 1; lp += (saw - lp) * (0.12 + 0.18 * Math.exp(-t * 6)); const env = Math.min(1, t * 200) * Math.exp(-t * 1.2) * Math.min(1, (len - t) * 30); return (Math.sin(2 * Math.PI * f * t) * 0.3 + lp * 0.7) * env * 0.5; }); };
const pluck = (f, len = 0.6, bright = 0.5) => { // Karplus–Strong
  const P = Math.max(2, Math.round(SR / f)), line = new Float32Array(P); for (let i = 0; i < P; i++) line[i] = noise();
  let idx = 0; const damp = 0.494 + bright * 0.005;
  return synth(len, (t) => { const a = line[idx], b = line[(idx + 1) % P]; line[idx] = (a + b) * damp; idx = (idx + 1) % P; return a * 0.35 * Math.min(1, (len - t) * 20); });
};
const piano = (f, len = 1.6, vel = 0.5) => synth(len, (t) => { let s = 0; for (let h = 1; h <= 6; h++) { const fh = f * h * Math.sqrt(1 + 0.0004 * h * h); s += Math.sin(2 * Math.PI * fh * t) * Math.exp(-t * (1.2 + h * 0.9)) / h; } return s * vel * 0.32 * Math.min(1, t * 400) * Math.min(1, (len - t) * 10); });
const riser = (len) => { let lp = 0, hp = 0; return synth(len, (t) => { const p = t / len, n = noise(); lp += (n - lp) * (0.02 + 0.5 * p * p); const v = lp - hp; hp += (lp - hp) * 0.01; return v * p * p * 0.5; }); };
const impact = () => { let ph = 0, lp = 0; return synth(2.2, (t) => { ph += 2 * Math.PI * (38 + 60 * Math.exp(-t * 6)) / SR; const n = noise(); lp += (n - lp) * 0.08; return Math.sin(ph) * Math.exp(-t * 2.2) * 0.9 + lp * Math.exp(-t * 4) * 0.5; }); };
const braam = (f, len) => synth(len, (t) => { let s = 0; for (const d of [-0.07, 0, 0.06]) s += 2 * (((f * (1 + d / 100)) * t) % 1) - 1; return Math.tanh(s * 0.6) * Math.min(1, t * 8) * Math.exp(-t * 0.9) * 0.25; });
const sidechain = (t, depth = 0.6, rel = 0.18) => { const s0 = Math.floor(t * SR), n = Math.floor(rel * 1.5 * SR); for (let i = 0; i < n && s0 + i < N; i++) DUCK[s0 + i] = Math.min(DUCK[s0 + i], 1 - depth * Math.exp(-(i / SR) / (rel / 3))); };

// ── composição ──
const beats = [], downbeats = [], secOut = [];
let bar0 = 0;
const S = STYLE;
for (const sec of sections) {
  const tSec = bar0 * BAR;
  secOut.push({ name: sec.name, start: +tSec.toFixed(3), end: +((bar0 + sec.bars) * BAR).toFixed(3) });
  for (let b = 0; b < sec.bars; b++) {
    const bar = bar0 + b, tb = bar * BAR, ch = chordAt(bar), last = b === sec.bars - 1;
    const energy = { intro: 0.3, build: 0.3 + 0.5 * (b / Math.max(1, sec.bars)), drop: 1, break: 0.25, outro: 0.35 }[sec.name] ?? 0.6;
    downbeats.push(+tb.toFixed(3));
    for (let q = 0; q < 4; q++) {
      const t = tb + q * SPB; beats.push(+t.toFixed(3));
      // KICK
      const kickOn = (sec.name === 'drop') || (sec.name === 'build' && b >= sec.bars / 2) || (S === 'minimal' && sec.name !== 'intro' && q % 2 === 0);
      if (kickOn && S !== 'piano') { hit(t, kick(), 0.9); sidechain(t + LAG); }
      if (S === 'piano' && sec.name === 'drop' && q === 0) { hit(t, kick(), 0.55); sidechain(t + LAG, 0.3); }
      // CLAP/SNARE no 2 e 4
      if ((q === 1 || q === 3) && energy > 0.5 && S !== 'minimal') hit(t, S === 'warm' ? snare() : clap(), 0.55, 0, 0.25);
      // HATS
      if (S !== 'piano' && energy >= 0.3) {
        hit(t + SPB / 2, hat(sec.name === 'drop' && S !== 'minimal'), 0.6, 0.3);
        if (energy > 0.7 && S === 'tech') { hit(t + SPB / 4, hat(), 0.35, -0.3); hit(t + 3 * SPB / 4, hat(), 0.35, -0.3); }
      }
    }
    // BAIXO (oitavas abaixo da tônica do acorde)
    if (sec.name !== 'intro' && sec.name !== 'break' && S !== 'piano') {
      const f = midi(ch[0] - 12);   // oitava acima (A2 = 110 Hz em vez de 55 Hz)
      for (let e = 0; e < (S === 'tech' ? 8 : 4); e++) { const step = S === 'tech' ? SPB / 2 : SPB; if (S === 'tech' && e % 2 === 0 && sec.name === 'drop') continue; add(tb + e * step, bass(f, step * 0.95), 0.8); }
    }
    // HARMONIA
    if (S === 'piano' || S === 'warm' || S === 'cinematic' || sec.name === 'break' || sec.name === 'intro' || sec.name === 'outro') {
      const vel = S === 'piano' ? 0.55 : 0.35;
      ch.forEach((m, i) => add(tb + i * 0.012, piano(midi(m), BAR * 1.1, vel), 0.9, (i - 1) * 0.25, 0.45));
      if (S === 'piano') { const mel = [4, 2, 1, 2]; add(tb + 2 * SPB, piano(midi(ch[0] + 12 + sc[mel[bar % 4]]), BAR * 0.6, 0.4), 0.8, 0.15, 0.5); }
    }
    // ARPEJO PLUCK (16 avos) — assinatura rítmica do vídeo
    if ((S === 'tech' || S === 'warm' || S === 'minimal') && energy >= 0.3) {
      const pat = [0, 1, 2, 1, 0, 2, 1, 2, 0, 1, 2, 3, 2, 1, 0, 2];
      for (let s = 0; s < 16; s++) {
        if (S === 'minimal' && s % 2) continue;
        const k = pat[s], m = ch[k % 3] + 12 * (1 + Math.floor(k / 3));
        add(tb + s * SPB / 4, pluck(midi(m), 0.5, energy), 0.55 * (s % 4 === 0 ? 1 : 0.7), (s % 2 ? 0.35 : -0.35), 0.35);
      }
    }
    if (S === 'cinematic' && b % 2 === 0 && sec.name !== 'intro') add(tb, braam(midi(ch[0] - 24), BAR * 1.8), 0.8, 0, 0.3);
    // TRANSIÇÕES
    if (sec.name === 'build' && last) { add(tb, riser(BAR), 0.8, 0, 0.2); for (let s = 0; s < 8; s++) hit(tb + BAR / 2 + s * SPB / 4, snare(), 0.18 + s * 0.04); }
  }
  if (sec.name === 'drop' || sec.name === 'outro') hit(tSec, impact(), sec.name === 'drop' ? 0.8 : 0.6, 0, 0.3);
  bar0 += sec.bars;
}
hit(totalBars * BAR, impact(), 0.7, 0, 0.4); // golpe final no fim
add(totalBars * BAR, piano(midi(root - 12), 2.4, 0.6), 0.9, 0, 0.5);

// ── reverb Schroeder no bus de send ──
function reverb(inp) {
  const out = new Float32Array(N);
  const combs = [1557, 1617, 1491, 1422].map((d) => ({ b: new Float32Array(Math.round(d * SR / 44100)), i: 0, lp: 0 }));
  const aps = [225, 556].map((d) => ({ b: new Float32Array(Math.round(d * SR / 44100)), i: 0 }));
  for (let n = 0; n < N; n++) {
    let s = 0;
    for (const c of combs) { const y = c.b[c.i]; c.lp = y * 0.7 + c.lp * 0.3; c.b[c.i] = inp[n] + c.lp * 0.82; c.i = (c.i + 1) % c.b.length; s += y; }
    s *= 0.25;
    for (const a of aps) { const y = a.b[a.i]; const v = s + y * -0.5; a.b[a.i] = v; s = y + v * 0.5; a.i = (a.i + 1) % a.b.length; }
    out[n] = s;
  }
  return out;
}
const wet = reverb(SEND);
// aplica sidechain ao que não é bumbo (aproximação: ducka a mix toda levemente, exceto transientes)
// remove DC por canal antes do ganho final
{ let a = 0, b = 0; for (let n = 0; n < N; n++) { a += L[n]; b += R[n]; } a /= N; b /= N; for (let n = 0; n < N; n++) { L[n] -= a; R[n] -= b; } }
let peak = 0;
for (let n = 0; n < N; n++) {
  const d = 0.35 + 0.65 * DUCK[n];
  L[n] = L[n] * d + wet[n] * 0.35; R[n] = R[n] * d + wet[(n + 240) % N] * 0.35;
  peak = Math.max(peak, Math.abs(L[n]), Math.abs(R[n]));
}
// soft-clip + normalização de pico a -1 dBFS (loudness final é feito no mix.sh)
// passa-altas suave em 35 Hz no master (sub abaixo disso é só headroom gasto)
{ const a = Math.exp(-2 * Math.PI * 35 / SR); let pl = 0, pr = 0, ol = 0, or = 0;
  for (let n = 0; n < N; n++) { const l = L[n], r = R[n]; ol = a * (ol + l - pl); or = a * (or + r - pr); pl = l; pr = r; L[n] = ol; R[n] = or; }
  peak = 0; for (let n = 0; n < N; n++) peak = Math.max(peak, Math.abs(L[n]), Math.abs(R[n])); }
const g = 0.89 / Math.max(peak, 1e-6);
const fadeOut = Math.floor(0.5 * SR);
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let n = 0; n < N; n++) {
  const f = n > N - fadeOut ? (N - n) / fadeOut : 1;
  buf.writeInt16LE(Math.round(Math.tanh(L[n] * g * 1.1) * f * 32767), 44 + n * 4);
  buf.writeInt16LE(Math.round(Math.tanh(R[n] * g * 1.1) * f * 32767), 46 + n * 4);
}
const out = resolve(opt('out', 'audio/music.wav')), bj = resolve(opt('beats', 'audio/beats.json'));
mkdirSync(dirname(out), { recursive: true }); mkdirSync(dirname(bj), { recursive: true });
writeFileSync(out, buf);
writeFileSync(bj, JSON.stringify({ bpm: BPM, duration: +(totalBars * BAR).toFixed(3), beats, downbeats, hits: [], sections: secOut, style: STYLE, key: KEY, scale: SCALE }, null, 1));
console.log(`✔ ${out} · ${BPM} BPM · ${totalBars} compassos (${(totalBars * BAR).toFixed(2)}s + cauda) · ${STYLE} · ${KEY} ${SCALE}\n✔ ${bj}`);
