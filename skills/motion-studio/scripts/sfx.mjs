#!/usr/bin/env node
/* sfx.mjs — sintetiza os efeitos sonoros do filme a partir de uma lista de cues.
 *
 *   node sfx.mjs --page index.html [--hook id --cta id] --out audio/sfx.wav   # lê window.CUES do próprio filme
 *   node sfx.mjs cues.json --out audio/sfx.wav --dur 15 --fps 60
 *
 * SINCRONIA (medida, não ouvida): t = instante do EVENTO VISUAL. O PICO medido de cada som cai em t + 1 frame
 * (--lag-frames 1): a luz chega antes do som — som antes da imagem parece errado mais cedo que um pouco depois.
 * Grava também audio/cues_resolved.json (onde cada pico caiu) para o audit-audio.py conferir no MP4 decodificado.
 * NÍVEL: --bed audio/music.wav --bed-db <mesmo --music-db do mix> → cada hit sai 3–6 dB acima da trilha (K-weighted).
 * Cue: { t: segundos, type: 'click', gain?: 1 (acento), pan?: -1..1, pitch?: 1, align?: 'peak'|'start', over?: dB }
 * Tipos: click tick key pop bloop snap thump whoosh swish swipe riser impact boom glitch chime ding shutter paper marker type(n caracteres)
 * Apelidos: hit→impact · ui→tick · scifi→glitch · marcador/highlighter→marker · papel/page→paper (a biblioteca gravada com o nome original vence)
 * Regra: cada mudança visual relevante tem som; mas no máximo ~1 cue forte por batida.
 *
 * SONS GRAVADOS (recomendado para cliente — síntese pura soa "barata"; sound.md §8):
 *   --lib estudio/sfx   pasta com WAV/MP3/FLAC nomeados pelo TIPO: whoosh_01.wav, whoosh_soft.wav, click_mech.wav, impact_02.wav…
 *   Para cada cue, se existir arquivo do tipo (ou cue.file: 'nome'), usa a GRAVAÇÃO; senão, sintetiza (reserva).
 *   Cada amostra passa por: passa-alta 180 Hz · passa-baixa 10 kHz · fade 10 ms · triagem (rejeita > 50% da energia
 *   < 150 Hz ou > 40% > 6 kHz, com aviso). Repetição: alterna as amostras do tipo e desce o volume em sequências rápidas.
 *   Pico continua medido e posto em evento + 1 frame; nivelamento contra a trilha igual.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
let cues;
let pageDur, pageFps;
if (opt('page')) {
  const { chromium, syncCampaign, filmURL } = await import('./pw.mjs');
  syncCampaign(resolve(opt('page')));
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(filmURL(resolve(opt('page')), { hook: opt('hook'), cta: opt('cta') }));
  cues = await p.evaluate(() => (typeof window.CUES === 'function' ? window.CUES() : window.CUES) || []);
  [pageDur, pageFps] = await p.evaluate(() => [window.DURATION, window.FPS]);
  await b.close();
} else {
  cues = JSON.parse(readFileSync(argv.find((a) => a.endsWith('.json')), 'utf8'));
  if (!Array.isArray(cues)) cues = cues.cues;
}
const SR = 48000;
// ── biblioteca de amostras gravadas ──
const LIB = {};
if (opt('lib')) {
  const { readdirSync, existsSync } = await import('node:fs');
  const { execFileSync } = await import('node:child_process');
  const dir = resolve(opt('lib'));
  if (!existsSync(dir)) console.warn('⚠ --lib não encontrada:', dir);
  else for (const f of readdirSync(dir).filter((f) => /\.(wav|mp3|flac|ogg|aiff?)$/i.test(f)).sort()) {
    const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', resolve(dir, f), '-ac', '1', '-ar', String(SR),
      '-af', 'highpass=f=180,lowpass=f=10000,afade=t=in:d=0.004,areverse,afade=t=in:d=0.01,areverse', '-f', 'f32le', '-'], { maxBuffer: 1 << 28 });
    const buf = new Float32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.length));
    // triagem espectral grosseira (sem FFT): energia do passa-baixa 150 Hz e do passa-alta 6 kHz vs total
    const band = (fc, hp) => { const a = Math.exp(-2 * Math.PI * fc / SR); let y = 0, e = 0, tot = 0; for (const x of buf) { y = (1 - a) * x + a * y; const v = hp ? x - y : y; e += v * v; tot += x * x; } return e / (tot || 1); };
    const lo = band(150, false), hi = band(6000, true), name = f.replace(/\.[^.]+$/, ''), type = name.split(/[_-]/)[0].toLowerCase();
    if (lo > 0.5 || hi > 0.4) { console.warn(`⚠ ${f}: ${lo > 0.5 ? 'grave demais' : 'agudo demais'} (${(100 * Math.max(lo, hi)).toFixed(0)}%) — fora da biblioteca`); continue; }
    let pv = 0; for (const x of buf) pv = Math.max(pv, Math.abs(x)); for (let i = 0; i < buf.length; i++) buf[i] *= 0.5 / (pv || 1);
    (LIB[type] = LIB[type] || []).push({ name, buf }); LIB['@' + name.toLowerCase()] = [{ name, buf }];
  }
  console.log(`  biblioteca: ${Object.keys(LIB).filter((k) => k[0] !== '@').map((k) => `${k}×${LIB[k].length}`).join(' ') || '(vazia)'}`);
}
const used = {}, lastAt = {};
const FPS = (() => { const v = String(opt('fps', pageFps || 60)); const m = v.match(/^([\d.]+)\/([\d.]+)$/); return m ? m[1] / m[2] : Number(v); })(), LAG = Number(opt('lag-frames', 1)) / FPS;
const resolved = [];
const DUR = Number(opt('dur', pageDur || Math.max(...cues.map((c) => c.t)) + 2));
const N = Math.ceil(DUR * SR), L = new Float32Array(N), R = new Float32Array(N);
let s = 42; const noise = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2147483648) - 1;
const TAU = Math.PI * 2;

// cada voz: (pitch) => [duração, fn(t)] — fn mantém estado interno se precisar (filtros)
const V = {
  click: (p) => [0.04, (t) => Math.sin(TAU * 2400 * p * t) * Math.exp(-t * 160) * 0.5 + noise() * Math.exp(-t * 400) * 0.25],
  tick: (p) => [0.02, (t) => Math.sin(TAU * 4200 * p * t) * Math.exp(-t * 300) * 0.35],
  key: (p) => { let lp = 0; return [0.06, (t) => { const n = noise(); lp += (n - lp) * 0.4; return lp * Math.exp(-t * 120) * 0.5 + Math.sin(TAU * 900 * p * t) * Math.exp(-t * 200) * 0.15; }]; },
  pop: (p) => [0.14, (t) => Math.sin(TAU * (500 + 1100 * t) * p * t) * Math.exp(-t * 32) * 0.45],
  bloop: (p) => [0.22, (t) => Math.sin(TAU * (300 * p) * t * (1 + 2.2 * t)) * Math.exp(-t * 16) * 0.4],
  snap: (p) => { let hp = 0; return [0.08, (t) => { const n = noise(); const v = n - hp; hp = n; return v * Math.exp(-t * 90) * 0.5 + Math.sin(TAU * 1500 * p * t) * Math.exp(-t * 120) * 0.2; }]; },
  thump: (p) => { let ph = 0; return [0.5, (t) => { ph += TAU * (48 + 70 * Math.exp(-t * 25)) * p / SR; return Math.sin(ph) * Math.exp(-t * 10) * 0.8 + Math.cos(TAU * 180 * p * t) * Math.exp(-t * 40) * 0.45; }]; },
  whoosh: (p) => { let lp = 0; const len = 0.45 / p; return [len, (t) => { const x = t / len, n = noise(); lp += (n - lp) * (0.03 + 0.35 * Math.sin(Math.PI * x)); return lp * Math.sin(Math.PI * Math.min(1, x)) ** 2 * 0.55; }]; },
  swish: (p) => { let lp = 0, hp = 0; return [0.22, (t) => { const n = noise(); lp += (n - lp) * (0.15 + 0.5 * t / 0.22); const v = lp - hp; hp += (lp - hp) * 0.05; return v * Math.sin(Math.PI * t / 0.22) * 0.5; }]; },
  swipe: (p) => { let lp = 0; return [0.3, (t) => { const n = noise(); lp += (n - lp) * (0.5 - 1.4 * t); return lp * Math.exp(-t * 9) * Math.min(1, t * 80) * 0.45; }]; },
  riser: (p) => { let lp = 0; const len = 1.2 / p; return [len, (t) => { const x = t / len, n = noise(); lp += (n - lp) * (0.01 + 0.45 * x * x); return (lp * 0.6 + Math.sin(TAU * (200 + 900 * x * x) * t) * 0.08) * x * x * 0.6; }]; },
  impact: (p) => { let ph = 0, lp = 0; return [1.6, (t) => { ph += TAU * (42 + 80 * Math.exp(-t * 7)) * p / SR; const n = noise(); lp += (n - lp) * 0.12; return Math.sin(ph) * Math.exp(-t * 3.2) * 0.8 + Math.cos(TAU * 160 * p * t) * Math.exp(-t * 18) * 0.5 + lp * Math.exp(-t * 6) * 0.6; }]; },
  boom: (p) => { let ph = 0; return [2.5, (t) => { ph += TAU * (30 + 40 * Math.exp(-t * 3)) * p / SR; return Math.tanh(Math.sin(ph) * 2) * Math.exp(-t * 1.5) * 0.8; }]; },
  glitch: (p) => [0.18, (t) => { const k = Math.floor(t * 90); return (k % 3 ? Math.sign(Math.sin(TAU * (300 + (k * 137) % 900) * p * t)) : noise()) * 0.25 * (t < 0.17 ? 1 : 0); }],
  // paper: folha deslizando (ruído banda-média, ataque macio) — o "whoosh" do estilo minimal premium
  paper: (p) => { let lp = 0, hp = 0; const len = 0.34; return [len, (t) => { const x = t / len, n = noise(); lp += (n - lp) * (0.22 + 0.25 * Math.sin(Math.PI * x)); const v = lp - hp; hp += (lp - hp) * 0.08; return v * Math.sin(Math.PI * Math.min(1, x * 1.15)) ** 1.4 * 0.42; }]; },
  // marker: marca-texto riscando (ruído com ondulação rápida) — linha de gráfico, sublinhado, destaque
  marker: (p) => { let lp = 0; const len = 0.42; return [len, (t) => { const x = t / len, n = noise(); lp += (n - lp) * 0.35; return lp * (0.55 + 0.45 * Math.sin(TAU * 38 * p * t)) * Math.min(1, t * 40) * (1 - x) ** 0.6 * 0.38; }]; },
  chime: (p) => [1.2, (t) => [1, 2.76, 5.4].reduce((a, h, i) => a + Math.sin(TAU * 880 * p * h * t) * Math.exp(-t * (3 + i * 4)) / (i + 1), 0) * 0.3],
  ding: (p) => [0.6, (t) => (Math.sin(TAU * 1320 * p * t) + 0.4 * Math.sin(TAU * 1980 * p * t)) * Math.exp(-t * 7) * 0.3],
  shutter: (p) => [0.12, (t) => noise() * (Math.exp(-t * 120) + (t > 0.05 ? Math.exp(-(t - 0.05) * 140) : 0)) * 0.5],
};

// ── NIVELAMENTO AUTOMÁTICO (--bed audio/music.wav --bed-db -4): cada hit 3–6 dB acima da trilha, medido com
// ponderação K (BS.1770) nos 60 ms a partir do pico — o mesmo critério do audit-audio.py. Cue.gain vira "acento":
// gain ≥ 0.5 → +4,5 dB sobre a trilha; gain < 0.5 (secundário) → +3 dB; 'over' no cue força um valor.
let BED = null;
if (opt('bed')) {
  const { execFileSync } = await import('node:child_process');
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', resolve(opt('bed')), '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 });
  BED = new Float32Array(raw.buffer, raw.byteOffset, raw.length / 4).map((x) => x * Math.pow(10, Number(opt('bed-db', -3)) / 20));
}
function kw(x) { // K-weighting 48 kHz
  const out = new Float64Array(x.length); let a1 = 0, a2 = 0, b1 = 0, b2 = 0, c1 = 0, c2 = 0, d1 = 0, d2 = 0;
  for (let i = 0; i < x.length; i++) {
    const y = 1.53512485958697 * x[i] - 2.69169618940638 * a1 + 1.19839281085285 * a2 + 1.69065929318241 * b1 - 0.73248077421585 * b2;
    a2 = a1; a1 = x[i]; b2 = b1; b1 = y;
    const z = y - 2 * c1 + c2 + 1.99004745483398 * d1 - 0.99007225036621 * d2;
    c2 = c1; c1 = y; d2 = d1; d1 = z; out[i] = z;
  }
  return out;
}
const energy = (x, i0, i1) => { let e = 0; for (let i = Math.max(0, i0); i < Math.min(x.length, i1); i++) e += x[i] * x[i]; return e / Math.max(1, i1 - i0); };   // janela FIXA (som curto + silêncio), igual ao audit
let BEDK = null, BEDMED = 0;
if (BED) { BEDK = kw(BED); const seg = []; for (let i = 0; i + 2880 < BEDK.length; i += 2880) seg.push(energy(BEDK, i, i + 2880)); seg.sort((a, b) => a - b); BEDMED = seg[Math.floor(seg.length / 2)] || 1e-9; }

function place(c) {
  if (c.type === 'type') { // sequência de teclas: { t, type:'type', n: caracteres, cps: 14 }
    const n = c.n || 8, cps = c.cps || 14;
    for (let i = 0; i < n; i++) place({ t: c.t + i / cps + ((i * 7919) % 13) / 1000, type: 'key', gain: (c.gain || 1) * (0.7 + ((i * 31) % 7) / 20), pan: c.pan, pitch: 0.9 + ((i * 17) % 5) / 20 });
    return;
  }
  // apelidos (nomes de biblioteca comuns) → tipo sintetizável; a gravação com o nome original continua tendo prioridade
  const ALIAS = { hit: 'impact', ui: 'tick', scifi: 'glitch', marcador: 'marker', highlighter: 'marker', papel: 'paper', pagina: 'paper', page: 'paper', clique: 'click' };
  const pool = (c.file && LIB['@' + String(c.file).toLowerCase()]) || LIB[c.type] || LIB[ALIAS[c.type]];
  const v = V[c.type] || V[ALIAS[c.type]]; if (!v && !pool) { console.warn('tipo desconhecido:', c.type); return; }
  let gain = c.gain ?? 1; const pan = c.pan ?? 0;
  // repetição rápida do mesmo tipo (< 0,6 s): alterna amostra e desce o volume (0,40→0,25 relativo, como cartas caindo)
  const k = lastAt[c.type] != null && c.t - lastAt[c.type] < 0.6 ? (used[c.type + '#run'] || 0) + 1 : 0; used[c.type + '#run'] = k; lastAt[c.type] = c.t;
  if (k) gain *= Math.max(0.62, 1 - 0.1 * k);
  const gl = gain * Math.cos((pan + 1) * Math.PI / 4), gr = gain * Math.sin((pan + 1) * Math.PI / 4);
  // renderiza a voz num buffer (gravação ou síntese), MEDE onde está o pico e posiciona o buffer para o pico cair em t + 1 frame
  let buf, pk = 0, pv = 0;
  if (pool) {
    const n = used[c.type] = (used[c.type] ?? -1) + 1, src = pool[n % pool.length].buf, rate = c.pitch || 1;
    buf = new Float32Array(Math.ceil(src.length / rate));
    for (let i = 0; i < buf.length; i++) { const x = i * rate, j = Math.floor(x), f = x - j; buf[i] = (src[j] || 0) * (1 - f) + (src[j + 1] || 0) * f; }
    for (let i = 0; i < buf.length; i++) { const a = Math.abs(buf[i]); if (a > pv) { pv = a; pk = i; } }
  } else {
    const [len, fn] = v(c.pitch || 1);
    buf = new Float32Array(Math.ceil(len * SR));
    for (let i = 0; i < buf.length; i++) { buf[i] = fn(i / SR); const a = Math.abs(buf[i]); if (a > pv) { pv = a; pk = i; } }
  }
  const target = c.t + LAG, s0 = c.align === 'start' ? Math.round(target * SR) : Math.round(target * SR) - pk;
  let lev = 1, over = null;
  if (BEDK) {
    over = c.over ?? (gain >= 0.5 ? 4.5 : 3);
    const hk = kw(buf), eh = energy(hk, pk - 240, pk + 2880) * gain * gain;
    const p0 = s0 + pk, eb = Math.max(energy(BEDK, p0 - 240, p0 + 2880), BEDMED * 0.25);
    lev = Math.min(24, Math.sqrt(eb * Math.pow(10, over / 10) / Math.max(eh, 1e-12)));   // ganho extra para ficar `over` dB acima
  }
  for (let i = 0; i < buf.length; i++) { const j = s0 + i; if (j < 0 || j >= N) continue; L[j] += buf[i] * gl * lev; R[j] += buf[i] * gr * lev; }
  resolved.push({ t: c.t, type: c.type, src: pool ? 'gravado' : 'síntese', peak: +((s0 + pk) / SR).toFixed(5), target: +target.toFixed(5), gain: +(gain * lev).toFixed(4), over });
}
cues.forEach(place);

// remove DC (média do canal) — DC rouba headroom e dá "clique" no começo/fim
let mL = 0, mR = 0; for (let i = 0; i < N; i++) { mL += L[i]; mR += R[i]; } mL /= N; mR /= N;
for (let i = 0; i < N; i++) { L[i] -= mL; R[i] -= mR; }
let peak = 1e-6; for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
// WAV IEEE float 32-bit: picos acima de 1.0 não clipam aqui (o mix.sh normaliza e limita depois) e os níveis relativos ficam intactos
const b = Buffer.alloc(44 + N * 8);
b.write('RIFF', 0); b.writeUInt32LE(36 + N * 8, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(3, 20); b.writeUInt16LE(2, 22);
b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 8, 28); b.writeUInt16LE(8, 32); b.writeUInt16LE(32, 34); b.write('data', 36); b.writeUInt32LE(N * 8, 40);
for (let i = 0; i < N; i++) { b.writeFloatLE(L[i], 44 + i * 8); b.writeFloatLE(R[i], 48 + i * 8); }
const out = resolve(opt('out', 'audio/sfx.wav'));
mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, b);
writeFileSync(out.replace(/\.wav$/, '') + '_cues.json', JSON.stringify({ fps: FPS, lagFrames: LAG * FPS, cues: resolved }, null, 1));
console.log(`✔ ${out} · ${cues.length} cues · ${DUR.toFixed(2)}s · picos em frame+${(LAG * FPS).toFixed(0)}${BED ? ' · nivelado contra a trilha' : ''} · pico ${(20 * Math.log10(peak)).toFixed(1)} dBFS`);
