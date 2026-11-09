#!/usr/bin/env node
/* stills.mjs — o laboratório: olhar o filme SEM renderizar o vídeo (segundos, não minutos).
 *
 *   node stills.mjs [index.html] --every 0.5            # contact sheet: 1 frame a cada 0,5 s
 *   node stills.mjs --beats audio/beats.json [--downbeats]   # 1 frame por batida (ou por compasso)
 *   node stills.mjs --times 0,1.2,3.5                    # instantes exatos (salva PNGs em tamanho real em out/stills/)
 *   node stills.mjs --frames 83,84,85                    # o mesmo, por número de frame
 *   node stills.mjs --strip 4.2 [--n 12]                 # frames consecutivos (pega "pulos", texto pisado, 1 frame a mais)
 *   node stills.mjs --board                              # BOARD de aprovação: 1 still por estado de window.SHOTS → out/board.html
 *   node stills.mjs --onion 1.2,1.8 [--step 2]           # ONION SKIN: frames empilhados → espaçamento igual = robótico
 *   node stills.mjs --graph [cursor.x,shape.w] [--from 0 --to 6]   # GRÁFICO DE VELOCIDADE de window.PROBES → out/graph.png
 *   node stills.mjs --checks                             # AUDITORIA NUMÉRICA de window.CHECKS (sai com erro se algo falhar)
 *   Comuns: --format 9x16|1x1|16x9|4x5  --hook <id> --cta <id>  --thumb 360  --cols 6  --out <arquivo>  --full
 */
import { chromium, syncCampaign, filmURL, installSeek, FORMATS } from './pw.mjs';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';

const argv = process.argv.slice(2);
const flag = (k) => argv.includes('--' + k);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : d; };
const input = resolve(argv.find((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--'))) || 'index.html');
const fmt = opt('format');
syncCampaign(input);

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none'] });
const [vw, vh] = fmt ? FORMATS[fmt] : [1080, 1920];
const page = await browser.newPage({ viewport: { width: vw, height: vh } });
page.on('pageerror', (e) => console.error('[page error]', e.message));
await page.goto(filmURL(input, { format: fmt, hook: opt('hook'), cta: opt('cta') }));
await page.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
await installSeek(page);
const info = await page.evaluate(() => { const c = document.getElementById('c'); return { canvas: !!c, w: c?.width || innerWidth, h: c?.height || innerHeight, dur: window.DURATION || 10, fps: window.FPS || 60, bpm: window.BPM }; });
if (!info.canvas) await page.setViewportSize({ width: info.w, height: info.h });
const OUTDIR = resolve(dirname(input), 'out'); mkdirSync(OUTDIR, { recursive: true });
const sheet = await browser.newPage({ viewport: { width: 400, height: 400 } });
const save = (p, dataUrl) => { mkdirSync(dirname(p), { recursive: true }); writeFileSync(p, Buffer.from(dataUrl.split(',')[1], 'base64')); };
async function grab(t) {
  await page.evaluate((x) => { window.__frameT = x; window.__seek(x); }, t);
  return info.canvas
    ? (await page.evaluate(() => document.getElementById('c').toDataURL('image/png'))).split(',')[1]
    : (await page.screenshot({ type: 'png' })).toString('base64');
}
const fr = (t) => Math.round(t * info.fps);

// ───────────────────────── CHECKS: auditoria numérica ─────────────────────────
if (flag('checks')) {
  const res = await page.evaluate(async () => {
    const out = [];
    for (const c of window.CHECKS || []) {
      window.__frameT = c.t; window.__seek(c.t);
      let r; try { r = c.test(c.t); } catch (e) { r = 'erro: ' + e.message; }
      out.push({ name: c.name, t: c.t, ok: r === true, msg: r === true ? '' : String(r) });
    }
    return out;
  });
  const fails = res.filter((r) => !r.ok);
  const lines = res.map((r) => `${r.ok ? '✔' : '✗'} f${String(fr(r.t)).padStart(4, '0')} ${r.t.toFixed(3)}s  ${r.name}${r.ok ? '' : '  → ' + r.msg}`);
  const md = `# CHECKS — ${res.length - fails.length}/${res.length} passaram\n\n` + lines.map((l) => '- ' + l).join('\n') + '\n';
  writeFileSync(resolve(opt('out', join(OUTDIR, 'checks.md'))), md);
  console.log(lines.join('\n') + `\n${fails.length ? '✗' : '✔'} ${res.length - fails.length}/${res.length} checagens · out/checks.md`);
  await browser.close(); process.exit(fails.length ? 1 : 0);
}

// ───────────────────────── GRAPH: posição e velocidade por frame ─────────────────────────
if (flag('graph')) {
  const want = opt('graph');
  const from = Number(opt('from', 0)), to = Number(opt('to', info.dur));
  const data = await page.evaluate(([want, from, to, fps]) => {
    const P = window.PROBES || {}, keys = want ? want.split(',') : Object.keys(P), res = {};
    for (const k of keys) { if (!P[k]) continue; const v = []; for (let f = Math.round(from * fps); f <= Math.round(to * fps); f++) v.push(P[k](f / fps)); res[k] = v; }
    return res;
  }, [want, from, to, info.fps]);
  const keys = Object.keys(data);
  if (!keys.length) { console.error('nenhuma sonda: declare window.PROBES = { nome: (t) => valor } no filme'); process.exit(1); }
  // diagnóstico: trechos lineares (velocidade constante ≠ 0 por ≥ 10 frames) e paradas mortas (velocidade cai a ~0 em 1 frame)
  const notes = [];
  for (const k of keys) {
    const v = data[k], d = v.map((x, i) => (i ? x - v[i - 1] : 0)), amp = Math.max(...v) - Math.min(...v) || 1;
    let run = 0;
    const still = (x) => Math.abs(x) < amp * 0.0005;
    const peakAround = (i, dir) => { let m = 0; for (let j = 1; j <= 15; j++) { const x = d[i + dir * j]; if (x !== undefined) m = Math.max(m, Math.abs(x)); } return m; };
    for (let i = 2; i < d.length; i++) {
      const moving = Math.abs(d[i]) > amp * 0.002, same = Math.abs(d[i] - d[i - 1]) < amp * 0.0004;
      run = moving && same ? run + 1 : 0;
      if (run === 10) notes.push(`${k}: LINEAR desde f${fr(from) + i - 10} (velocidade constante) → use spring/ease`);
      // seco = muda de parado para ≥60% da velocidade de pico (ou o inverso) em 1 frame. Spring a partir do repouso dá ~35%: ok.
      if (still(d[i]) && !still(d[i - 1]) && Math.abs(d[i - 1]) > 0.6 * peakAround(i - 1, -1) && Math.abs(d[i - 1]) > amp * 0.01) notes.push(`${k}: PARADA SECA em f${fr(from) + i} → assentar com spring`);
      if (still(d[i - 1]) && !still(d[i]) && Math.abs(d[i]) > 0.6 * peakAround(i, 1) && Math.abs(d[i]) > amp * 0.01) notes.push(`${k}: ARRANQUE SECO em f${fr(from) + i} → antecipação ou ease-in`);
    }
  }
  const png = await sheet.evaluate(([data, from, fps, notesN]) => {
    const keys = Object.keys(data), W = 1400, rowH = 260, c = document.createElement('canvas');
    c.width = W; c.height = keys.length * rowH + 40; const g = c.getContext('2d');
    g.fillStyle = '#141413'; g.fillRect(0, 0, c.width, c.height);
    keys.forEach((k, r) => {
      const v = data[k], d = v.map((x, i) => (i ? x - v[i - 1] : 0)), y0 = 30 + r * rowH, x0 = 70, w = W - 100, h = rowH - 60;
      const mn = Math.min(...v), mx = Math.max(...v), dm = Math.max(...d.map(Math.abs)) || 1;
      g.strokeStyle = '#333'; g.strokeRect(x0, y0, w, h);
      for (let s = 0; s * fps <= v.length; s++) { const x = x0 + (s * fps / (v.length - 1)) * w; g.fillStyle = '#666'; g.font = '12px monospace'; g.fillText(`${(from + s).toFixed(0)}s`, x - 8, y0 + h + 16); g.fillRect(x, y0, 1, h); }
      g.strokeStyle = '#F1EEE7'; g.lineWidth = 2; g.beginPath(); v.forEach((x, i) => { const px = x0 + (i / (v.length - 1)) * w, py = y0 + h - ((x - mn) / (mx - mn || 1)) * h; i ? g.lineTo(px, py) : g.moveTo(px, py); }); g.stroke();
      g.strokeStyle = '#FF5A1F'; g.lineWidth = 1.5; g.beginPath(); d.forEach((x, i) => { const px = x0 + (i / (v.length - 1)) * w, py = y0 + h / 2 - (x / dm) * (h / 2); i ? g.lineTo(px, py) : g.moveTo(px, py); }); g.stroke();
      g.fillStyle = '#ddd'; g.font = '600 15px monospace'; g.fillText(`${k}   (branco = valor ${mn.toFixed(1)}…${mx.toFixed(1)} · laranja = velocidade por frame)`, x0, y0 - 8);
    });
    g.fillStyle = '#aaa'; g.font = '13px monospace'; g.fillText(`${notesN} alerta(s) — linhas retas = movimento linear · quinas = parada/arranque seco`, 70, c.height - 10);
    return c.toDataURL('image/png');
  }, [data, from, info.fps, notes.length]);
  const out = resolve(opt('out', join(OUTDIR, 'graph.png'))); save(out, png);
  console.log((notes.length ? notes.slice(0, 30).join('\n') + '\n' : 'nenhum trecho linear ou parada seca detectado\n') + `✔ ${out}`);
  await browser.close(); process.exit(0);
}

// ───────────────────────── ONION SKIN ─────────────────────────
if (opt('onion')) {
  const [a, b] = opt('onion').split(',').map(Number), step = Number(opt('step', 2));
  const list = []; for (let f = fr(a); f <= fr(b); f += step) list.push(f / info.fps);
  const imgs = []; for (const t of list) imgs.push(await grab(t));
  const png = await sheet.evaluate(async ([imgs, alpha]) => {
    const els = await Promise.all(imgs.map(async (b) => { const i = new Image(); i.src = 'data:image/png;base64,' + b; await i.decode(); return i; }));
    const W = els[0].width, H = els[0].height, c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d', { willReadFrequently: true });
    const px = els.map((im) => { g.drawImage(im, 0, 0); return g.getImageData(0, 0, W, H).data; });
    const lightBg = (px[0][0] + px[0][1] + px[0][2]) / 3 > 128;   // fundo claro → empilha por "darken"; escuro → "lighten"
    const out = g.createImageData(W, H), o = out.data, n = els.length;
    for (let i = 0; i < o.length; i += 4) {
      for (let ch = 0; ch < 3; ch++) {
        let acc = lightBg ? 255 : 0;
        for (let k = 0; k < n; k++) {
          const w = k === n - 1 ? 1 : alpha + (1 - alpha) * 0.6 * (k / Math.max(1, n - 1));   // antigos mais fracos, atual sólido
          const v = lightBg ? 255 - (255 - px[k][i + ch]) * w : px[k][i + ch] * w;
          acc = lightBg ? Math.min(acc, v) : Math.max(acc, v);
        }
        o[i + ch] = acc;
      }
      o[i + 3] = 255;
    }
    g.putImageData(out, 0, 0);
    return c.toDataURL('image/png');
  }, [imgs, Number(opt('alpha', 0.3))]);
  const out = resolve(opt('out', join(OUTDIR, 'onion.png'))); save(out, png);
  console.log(`✔ ${out} — ${list.length} frames (f${fr(a)}→f${fr(b)}, passo ${step}). Espaçamento igual = robótico; apertando perto das chaves = easing certo.`);
  await browser.close(); process.exit(0);
}

// ───────────────────────── CONTACT SHEET / STRIP / BOARD ─────────────────────────
let times = [], shots = null;
if (flag('board')) {
  shots = await page.evaluate(() => (window.SHOTS || []).map((s) => ({ ...s })));
  if (!shots.length) { console.error('window.SHOTS vazio — declare a lista de estados no index.html'); process.exit(1); }
  times = shots.map((s) => +(s.key ?? (s.from + s.to) / 2).toFixed(4));
}
else if (opt('times')) times = opt('times').split(',').map(Number);
else if (opt('frames')) times = opt('frames').split(',').map((f) => Number(f) / info.fps);
else if (opt('beats')) { const b = JSON.parse(readFileSync(opt('beats'), 'utf8')); times = flag('downbeats') ? b.downbeats : b.beats; times = times.map((x) => x + 0.05).filter((x) => x < info.dur); }
else if (opt('strip')) { const c = Number(opt('strip')), n = Number(opt('n', 12)); for (let i = 0; i < n; i++) times.push(c + (i - n / 2) / info.fps); }
else { const e = Number(opt('every', 0.5)); for (let t = 0; t < info.dur - 1e-6; t += e) times.push(+t.toFixed(4)); }

const out = resolve(opt('out', join(OUTDIR, opt('strip') ? 'strip.png' : flag('board') ? 'board_contact.png' : 'contact.png')));
mkdirSync(dirname(out), { recursive: true });
const full = flag('full') || !!opt('times') || !!opt('frames');
if (full) mkdirSync(join(dirname(out), 'stills'), { recursive: true });

const captured = [];
for (const t of times) {
  const b64 = await grab(t);
  if (full) writeFileSync(join(dirname(out), 'stills', `f${String(fr(t)).padStart(4, '0')}_t${t.toFixed(2)}.png`), Buffer.from(b64, 'base64'));
  captured.push({ t, f: fr(t), b64 });
}

const thumb = Number(opt('thumb', opt('strip') ? 240 : 360));
const cols = Number(opt('cols', opt('strip') ? Math.min(12, captured.length) : 6));
const th = Math.round(thumb * info.h / info.w);
const rows = Math.ceil(captured.length / cols), pad = 8, lab = 26;
const dataUrl = await sheet.evaluate(async ({ shots, thumb, th, cols, rows, pad, lab }) => {
  const c = document.createElement('canvas');
  c.width = cols * (thumb + pad) + pad; c.height = rows * (th + pad + lab) + pad;
  const g = c.getContext('2d'); g.fillStyle = '#1b1b1b'; g.fillRect(0, 0, c.width, c.height);
  g.imageSmoothingQuality = 'high';
  for (let i = 0; i < shots.length; i++) {
    const img = new Image(); img.src = 'data:image/png;base64,' + shots[i].b64; await img.decode();
    const x = pad + (i % cols) * (thumb + pad), y = pad + Math.floor(i / cols) * (th + pad + lab);
    g.drawImage(img, x, y + lab, thumb, th);
    g.fillStyle = '#ddd'; g.font = '600 15px monospace'; g.fillText(`#${i} f${shots[i].f} ${shots[i].t.toFixed(2)}s`, x + 2, y + 18);
  }
  return c.toDataURL('image/png');
}, { shots: captured, thumb, th, cols, rows, pad, lab });
save(out, dataUrl);

if (shots) {
  const thumbs = await sheet.evaluate(async (list) => {
    const res = [];
    for (const b64 of list) {
      const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode();
      const c = document.createElement('canvas'); c.width = 540; c.height = Math.round(540 * img.height / img.width);
      const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(img, 0, 0, c.width, c.height);
      res.push(c.toDataURL('image/jpeg', 0.86));
    }
    return res;
  }, captured.map((c) => c.b64));
  const meta = await page.evaluate(() => ({ bpm: window.BPM, dur: window.DURATION, title: document.title, variant: window.VARIANT }));
  const spb = meta.bpm ? 60 / meta.bpm : null;
  const fmtT = (x) => `${x.toFixed(2)}s · f${fr(x)}` + (spb ? ` · B${+(x / spb).toFixed(1)}` : '');
  const esc = (v) => String(v ?? '—').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const colsK = ['name', 'read', 'text', 'sfx', 'out'];
  const head = { name: 'Estado', read: 'Leitura (o que o espectador entende)', text: 'Texto na tela', sfx: 'Som', out: 'Transição de saída' };
  const need = (s) => { const w = String(s.text || '').replace(/[—·/]/g, ' ').split(/\s+/).filter(Boolean).length; return w ? 0.5 + 0.3 * w : 0; };
  const warn = (s) => (s.to - s.from) + 1e-6 < need(s) ? `<div class=w8>⚠ texto pede ${need(s).toFixed(1)}s</div>` : '';
  const short = shots.filter((s) => warn(s)).length;
  const rowsH = shots.map((s, i) => `<tr><td class=n>${i + 1}</td><td class=t>${fmtT(s.from)}<br>→ ${fmtT(s.to)}<br><small>${(s.to - s.from).toFixed(2)}s</small>${warn(s)}</td>
    <td><img src="${thumbs[i]}"><div class=k>still @ ${fmtT(times[i])}</div></td>${colsK.map((k) => `<td>${esc(s[k])}</td>`).join('')}</tr>`).join('');
  const vinfo = meta.variant ? ` · variante: gancho <b>${esc(meta.variant.hook)}</b>, CTA <b>${esc(meta.variant.cta)}</b>` : '';
  const html = `<!doctype html><html lang=pt-BR><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Board — ${esc(meta.title)}</title><style>
:root{--bg:#f6f4ef;--ink:#1a1a18;--mute:#77746c;--line:#ddd8cd}@media(prefers-color-scheme:dark){:root{--bg:#161615;--ink:#eee;--mute:#9a978f;--line:#333}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}p.m{color:var(--mute);margin:0 0 20px}.w{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:900px}
td,th{border-top:1px solid var(--line);padding:10px 8px;vertical-align:top;text-align:left}th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mute)}
td.n{font-weight:700}td.t{white-space:nowrap;font-variant-numeric:tabular-nums}img{width:150px;border-radius:6px;display:block}.k{font-size:11px;color:var(--mute);margin-top:4px}.w8{color:#c2410c;font-size:12px;margin-top:6px;white-space:normal}
</style><main><h1>Board de aprovação</h1><p class=m>${shots.length} estados · ${meta.dur}s${meta.bpm ? ` · ${meta.bpm} BPM` : ''}${fmt ? ` · ${fmt}` : ''}${vinfo} · aprove ou anote por linha antes do render completo${short ? ` · <b style=color:#c2410c>${short} estado(s) curto(s) demais para ler</b>` : ''}</p>
<div class=w><table><tr><th>#</th><th>Tempo</th><th>Frame</th>${colsK.map((k) => `<th>${head[k]}</th>`).join('')}</tr>${rowsH}</table></div></main></html>`;
  const boardPath = resolve(dirname(out), opt('board-out', 'board.html'));
  writeFileSync(boardPath, html);
  console.log(`✔ ${boardPath} — ${shots.length} estados${short ? ` · ⚠ ${short} curto(s) demais para o texto` : ''}`);
}
await browser.close();
console.log(`✔ ${out} — ${captured.length} frames (${cols}×${rows}, miniatura ${thumb}px)`);
