#!/usr/bin/env node
/* prove.mjs — ENGENHARIA DE PROVA: o render prova o filme; a descrição do modelo não prova nada.
 *
 *   node scripts/prove.mjs determinism [--n 6]           frame FRIO (seek direto) = frame QUENTE (depois de tocar 0→t)? hash igual ou é estado escondido
 *   node scripts/prove.mjs golden save [--format 9x16]   salva os GOLDEN FRAMES aprovados (1 por estado de window.SHOTS + pôster) em golden/<fmt>/
 *   node scripts/prove.mjs golden check [--scope 4.0-6.5] re-renderiza e compara: mudou DENTRO do escopo = esperado; FORA = REGRESSÃO (sai com erro)
 *   node scripts/prove.mjs color                          sonda de cor: window.PROBE_COLORS → ΔE2000 da região vs token da marca
 *   node scripts/prove.mjs gate G3 pass "nota"            registra o gate em docs/MANIFEST.json (G1..G6) · gate status · round (conta rodadas de conserto; teto 5)
 *
 * window.PROBE_COLORS = [{ t: 2.0, x: 100, y: 200, w: 40, h: 40, token: '#D97757', name: 'acento no botão', max: 2 }]
 *   (coordenadas em px do quadro; ΔE2000 < ~2 é invisível lado a lado; max padrão 2,5)
 * Comuns: [index.html] --format 9x16 --hook id --cta id
 */
import { chromium, syncCampaign, filmURL, installSeek, FORMATS } from './pw.mjs';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const pos = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--')));
const cmd = pos[0], sub = pos[1];
const input = resolve(pos.find((a) => a.endsWith('.html')) || 'index.html');
const ROOT = dirname(input), FMT = opt('format');
const MAN = join(ROOT, 'docs/MANIFEST.json');

// ───────────────────────── gates (não precisa de navegador) ─────────────────────────
const GATES = { G1: 'assets completos, fatos com fonte (campaign.json/claims)', G2: 'cada batida tem propósito (STORYBOARD + CUES)', G3: 'determinismo passa + stills/contact sheet',
  G4: 'transições, sincronia e movimento (strips, render de trecho)', G5: '3 piores corrigidos, golden set limpo', G6: 'cada formato medido no arquivo DECODIFICADO + nota de entrega' };
function man() { return existsSync(MAN) ? JSON.parse(readFileSync(MAN, 'utf8')) : { max_rounds: 5, rounds: 0, gates: Object.fromEntries(Object.keys(GATES).map((g) => [g, { status: 'pendente', what: GATES[g] }])) }; }
function saveMan(m) { mkdirSync(dirname(MAN), { recursive: true }); writeFileSync(MAN, JSON.stringify(m, null, 2)); }
if (cmd === 'gate') {
  const m = man();
  if (sub && sub !== 'status') { const st = pos[2] || 'pass'; m.gates[sub] = { ...(m.gates[sub] || {}), status: st, note: pos[3] || '', at: new Date().toISOString() }; saveMan(m); }
  for (const [g, v] of Object.entries(m.gates)) console.log(`${v.status === 'pass' ? '✔' : v.status === 'fail' ? '✗' : '·'} ${g} ${v.status.padEnd(8)} ${v.what}${v.note ? ' — ' + v.note : ''}`);
  console.log(`  rodadas de conserto: ${m.rounds}/${m.max_rounds}`);
  process.exit(0);
}
if (cmd === 'round') {
  const m = man(); m.rounds++; saveMan(m);
  if (m.rounds > m.max_rounds) { console.log(`✗ ${m.rounds} rodadas > teto ${m.max_rounds}: PARE e entregue o relatório do que falta (critique.md §8). Não fique em loop.`); process.exit(1); }
  console.log(`✔ rodada ${m.rounds}/${m.max_rounds}`); process.exit(0);
}

// ───────────────────────── navegador ─────────────────────────
syncCampaign(input);
const [W, H] = FMT ? FORMATS[FMT] : [0, 0];
const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none', '--run-all-compositor-stages-before-draw', '--disable-threaded-animation'] });
async function open() {
  const page = await browser.newPage({ viewport: { width: W || 1080, height: H || 1920 } });
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  await page.goto(filmURL(input, { format: FMT, hook: opt('hook'), cta: opt('cta') }));
  await page.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
  await installSeek(page);
  return page;
}
// impressão digital: imagem reduzida a 270 px de largura (cinza+cor) para diff, e hash do quadro inteiro para determinismo
async function grab(page, t, full = false) {
  return page.evaluate(([t, full]) => {
    window.__frameT = t; window.__seek(t);
    const c = document.getElementById('c');
    if (!c) return null;
    const w = 270, h = Math.round(c.height * w / c.width), o = document.createElement('canvas'); o.width = w; o.height = h;
    const g = o.getContext('2d'); g.drawImage(c, 0, 0, w, h); const d = g.getImageData(0, 0, w, h).data;
    let s = ''; for (let i = 0; i < d.length; i += 4) s += String.fromCharCode(d[i], d[i + 1], d[i + 2]);
    return { w, h, fp: btoa(s), full: full ? c.toDataURL('image/png') : null, hash: c.getContext('2d').getImageData(0, 0, c.width, c.height).data.reduce((a, v, i) => (a * 31 + v * (i % 7 + 1)) >>> 0, 7) };
  }, [t, full]);
}
const meta = async (page) => page.evaluate(() => ({ dur: window.DURATION, fps: window.FPS || 30, shots: (window.SHOTS || []).map((s) => ({ t: s.key ?? (s.from + s.to) / 2, name: s.name })), probes: window.PROBE_COLORS || [] }));
const diff = (a, b) => { const A = Buffer.from(a, 'base64'), B = Buffer.from(b, 'base64'); let sum = 0, big = 0; for (let i = 0; i < A.length; i++) { const d = Math.abs(A[i] - B[i]); sum += d; if (d > 8) big++; } return { mean: sum / A.length, frac: big / A.length }; };

if (cmd === 'determinism') {
  const p1 = await open(), M = await meta(p1), n = Number(opt('n', 6));
  const ts = Array.from({ length: n }, (_, i) => +(((i + 0.5) / n) * M.dur).toFixed(3));
  let bad = 0;
  // ordem 1: frio (cada t numa página recém-aberta, sem passado)
  const cold = []; for (const t of ts) { const p = await open(); cold.push((await grab(p, t)).hash); await p.close(); }
  // ordem 2: quente (toca 0→t frame a frame, como o player) e em ordem REVERSA
  const warm = {}; const step = 1 / M.fps;
  for (let t = 0; t <= M.dur; t += step) await p1.evaluate((x) => window.__seek(x), t);
  for (const t of [...ts].reverse()) warm[t] = (await grab(p1, t)).hash;
  ts.forEach((t, i) => { const ok = cold[i] === warm[t]; if (!ok) bad++; console.log(`${ok ? '✔' : '✗'} t=${t}s  frio ${cold[i]} · quente ${warm[t]}${ok ? '' : '  ← o frame depende do HISTÓRICO (estado entre frames, Date.now, random sem semente, acumulador)'}`); });
  await browser.close();
  console.log(bad ? `✗ ${bad}/${ts.length} frames dependem do passado — conserte antes de qualquer revisão (o frame que você olhou não é o que vai sair)` : `✔ determinismo: ${ts.length}/${ts.length} frames idênticos frio × quente × ordem reversa`);
  process.exit(bad ? 1 : 0);
}

if (cmd === 'golden') {
  const dir = join(ROOT, 'golden', FMT || 'default'); mkdirSync(dir, { recursive: true });
  const idx = join(dir, 'index.json'), p = await open(), M = await meta(p);
  if (sub === 'save') {
    const ts = [...M.shots.map((s) => ({ t: +s.t.toFixed(3), name: s.name })), { t: +(M.dur * 0.3).toFixed(3), name: 'pôster' }];
    const out = [];
    for (const s of ts) { const g = await grab(p, s.t, true); const f = `${String(Math.round(s.t * M.fps)).padStart(5, '0')}.png`; writeFileSync(join(dir, f), Buffer.from(g.full.split(',')[1], 'base64')); out.push({ ...s, file: f, fp: g.fp }); }
    writeFileSync(idx, JSON.stringify(out)); await browser.close();
    console.log(`✔ ${out.length} golden frames aprovados em ${dir} (re-salve só depois de aprovação do cliente/diretor)`); process.exit(0);
  }
  if (!existsSync(idx)) { console.error('✗ sem golden set: rode `prove.mjs golden save` depois da aprovação'); process.exit(1); }
  const gold = JSON.parse(readFileSync(idx, 'utf8')); const [a, b] = (opt('scope', '') || '').split('-').map(Number);
  let reg = 0;
  for (const s of gold) {
    const g = await grab(p, s.t), d = diff(g.fp, s.fp), changed = d.mean > 0.6 || d.frac > 0.002, inScope = opt('scope') && s.t >= a && s.t <= b;
    if (changed && !inScope) reg++;
    console.log(`${!changed ? '✔ igual  ' : inScope ? '~ mudou (no escopo)' : '✗ REGRESSÃO'}  ${s.t}s ${s.name}  · Δmédio ${d.mean.toFixed(2)} · ${(100 * d.frac).toFixed(2)}% px`);
  }
  await browser.close();
  console.log(reg ? `✗ ${reg} golden frame(s) mudaram FORA do escopo — o conserto vazou. Pare, ache o token/componente compartilhado.` : '✔ golden set limpo');
  process.exit(reg ? 1 : 0);
}

if (cmd === 'color') {
  const p = await open(), M = await meta(p);
  if (!M.probes.length) { console.log('· sem window.PROBE_COLORS — declare as regiões de cor de marca que importam (logo, botão, acento)'); await browser.close(); process.exit(0); }
  const hex = (h) => { h = h.replace('#', ''); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); };
  const lab = ([r, g, b]) => { const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; }; const [R, G, B] = [f(r), f(g), f(b)];
    const X = (0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047, Y = 0.2126 * R + 0.7152 * G + 0.0722 * B, Z = (0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883;
    const t = (v) => (v > 0.008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116); return [116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z))]; };
  const de2000 = ([L1, a1, b1], [L2, a2, b2]) => { const d = Math.PI / 180, C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cb = (C1 + C2) / 2, G = 0.5 * (1 - Math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)));
    const A1 = (1 + G) * a1, A2 = (1 + G) * a2, c1 = Math.hypot(A1, b1), c2 = Math.hypot(A2, b2); let h1 = Math.atan2(b1, A1) / d, h2 = Math.atan2(b2, A2) / d; if (h1 < 0) h1 += 360; if (h2 < 0) h2 += 360;
    const dL = L2 - L1, dC = c2 - c1; let dh = h2 - h1; if (c1 * c2 === 0) dh = 0; else if (dh > 180) dh -= 360; else if (dh < -180) dh += 360; const dH = 2 * Math.sqrt(c1 * c2) * Math.sin((dh / 2) * d);
    const Lb = (L1 + L2) / 2, cb = (c1 + c2) / 2; let hb = h1 + h2; if (c1 * c2 !== 0) hb = Math.abs(h1 - h2) > 180 ? (h1 + h2 + (h1 + h2 < 360 ? 360 : -360)) / 2 : (h1 + h2) / 2;
    const T = 1 - 0.17 * Math.cos((hb - 30) * d) + 0.24 * Math.cos(2 * hb * d) + 0.32 * Math.cos((3 * hb + 6) * d) - 0.2 * Math.cos((4 * hb - 63) * d);
    const SL = 1 + (0.015 * (Lb - 50) ** 2) / Math.sqrt(20 + (Lb - 50) ** 2), SC = 1 + 0.045 * cb, SH = 1 + 0.015 * cb * T, RT = -2 * Math.sqrt(cb ** 7 / (cb ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hb - 275) / 25) ** 2)) * d);
    return Math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH)); };
  let bad = 0;
  for (const pr of M.probes) {
    const rgb = await p.evaluate((pr) => { window.__frameT = pr.t; window.__seek(pr.t); const d = document.getElementById('c').getContext('2d').getImageData(pr.x, pr.y, pr.w || 8, pr.h || 8).data; let r = 0, g = 0, b = 0, n = d.length / 4; for (let i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; b += d[i + 2]; } return [r / n, g / n, b / n]; }, pr);
    const de = de2000(lab(hex(pr.token)), lab(rgb)), ok = de <= (pr.max ?? 2.5); if (!ok) bad++;
    console.log(`${ok ? '✔' : '✗'} ${pr.name || pr.token} @${pr.t}s · medido rgb(${rgb.map((v) => v.toFixed(0)).join(',')}) vs ${pr.token} · ΔE2000 ${de.toFixed(2)}${ok ? '' : ' ← a cor da marca derivou (grão, vinheta, blend, tone mapping?)'}`);
  }
  await browser.close(); process.exit(bad ? 1 : 0);
}
console.log('uso: prove.mjs determinism | golden save|check [--scope a-b] | color | gate <G1..G6> pass|fail "nota" | gate status | round');
process.exit(1);
