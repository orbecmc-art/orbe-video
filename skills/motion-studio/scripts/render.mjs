#!/usr/bin/env node
/* render.mjs — renderiza um filme `window.seek(t)` em MP4, frame a frame, de forma determinística.
 *
 * Uso:
 *   node render.mjs [index.html] [--out out/silent.mp4] [--fps 60] [--dur <s>] [--sub 4] [--shutter 0.5]
 *                   [--w 1080 --h 1920 | --format 9x16|1x1|16x9|4x5] [--from 0 --to <s>] [--workers 4]
 *                   [--crf 16] [--scale 1] [--jpeg] [--keep] [--hook <id> --cta <id>] [--linear 0]
 *                   [--ss 2] [--deband] [--alpha] [--master]   (--ss 2 = supersample 2× + Lanczos: o master final)
 *                     (banding em gradiente · ProRes 4444 transparente · ProRes 422 HQ 10 bits)
 *
 * Modos:
 *   CANVAS (padrão quando existe <canvas id="c">): motion blur feito DENTRO da página acumulando
 *     `sub` subframes espalhados pelo obturador (shutter 0.5 = 180°). Só 1 imagem por frame trafega → rápido.
 *     Adaptativo: frame parado = 1 amostra; window.SUB_AT(t) pode pedir 16–32 num whip; nenhum subframe cruza
 *     um corte (window.CUTS, ou os fins de window.SHOTS com out 'cut').
 *   DOM (sem #c, ou --dom): screenshot da página por subframe; blur via ffmpeg tmix.
 *
 * Contrato da página:
 *   - window.seek(t) ou window.renderAt(t) pinta o instante t (segundos). Pura: nada de timers, Math.random.
 *     Animações CSS @keyframes / Web Animations também funcionam: são pausadas e posicionadas em t a cada frame.
 *   - campaign.json ao lado do html → sincronizado em campaign.js antes do render. --hook/--cta escolhem a variante.
 *   - opcional window.DURATION / window.FPS. Lê ?w=&h=&format= da URL para trocar o formato.
 *   - opcional window.ready (Promise) — aguardada antes do primeiro frame (fontes, imagens).
 */
import { chromium, syncCampaign, filmURL, installSeek } from './pw.mjs';
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync, existsSync, renameSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import os from 'node:os';

const argv = process.argv.slice(2);
const flag = (k) => argv.includes('--' + k);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const num = (k, d) => { const v = opt(k); if (v === undefined) return d; const m = String(v).match(/^(\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)$/); return m ? Number(m[1]) / Number(m[2]) : Number(v); };   // aceita 30000/1001
const input = resolve(argv.find((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--'))) || 'index.html');

const FORMATS = { '9x16': [1080, 1920], '1x1': [1080, 1080], '16x9': [1920, 1080], '4x5': [1080, 1350], '4k': [3840, 2160] };
const fmt = opt('format');
let [W, H] = fmt ? FORMATS[fmt] : [num('w', 0), num('h', 0)];
const SUB_AUTO = opt('sub') === 'auto';   // --sub auto: amostras pela quantidade de movimento no obturador (1 · 4 · 8 · 16 · 32)
const SUB = SUB_AUTO ? 0 : Math.max(1, num('sub', 4));
const SHUTTER = num('shutter', 0.5);
const CRF = num('crf', 16);
const SCALE = num('scale', 1);
const WORKERS = Math.max(1, num('workers', Math.min(6, Math.max(1, os.cpus().length - 1))));
let OUT = resolve(opt('out', fmt ? `out/silent_${fmt}.mp4` : 'out/silent.mp4'));
if ((flag('alpha') || flag('master')) && OUT.endsWith('.mp4')) OUT = OUT.replace(/\.mp4$/, flag('alpha') ? '_alpha.mov' : '_master.mov');

syncCampaign(input);
// SUPERSAMPLE (--ss 2): o canvas pinta em 2× e o ffmpeg reduz com Lanczos → traço fino e borda girada sem serrilhado ("barato").
// Custa ~4× de tempo: use no master final, não no rascunho. O layout em L/u escala sozinho com ?w=&h=.
const SS = Math.max(1, num('ss', 1));
const LINEAR = num('linear', 1) !== 0;   // motion blur em luz LINEAR (como um obturador de cinema de 180°)
if (SS > 1 && (!W || !H)) {   // descobre o tamanho nativo do canvas antes de dobrar
  const b0 = await chromium.launch(); const p0 = await b0.newPage(); await p0.goto(filmURL(input, { hook: opt('hook'), cta: opt('cta') }));
  [W, H] = await p0.evaluate(() => { const c = document.getElementById('c'); return c ? [c.width, c.height] : [1080, 1920]; }); await b0.close();
}
const OUTW = W, OUTH = H;
const url = filmURL(input, { w: W * SS || undefined, h: H * SS || undefined, format: SS > 1 ? undefined : fmt, hook: opt('hook'), cta: opt('cta') });
if (SS > 1) { W *= SS; H *= SS; }

// flags determinísticas: o compositor termina tudo antes de desenhar, nada de animação em thread paralela
const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-gpu-vsync', '--force-color-profile=srgb', '--font-render-hinting=none',
  '--run-all-compositor-stages-before-draw', '--disable-threaded-animation', '--disable-checker-imaging', '--disable-renderer-backgrounding'] });

async function openPage() {
  const page = await browser.newPage({ viewport: { width: W || 1080, height: H || 1920 }, deviceScaleFactor: SCALE });
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  page.on('console', (m) => { if (m.type() === 'error') console.error('[console]', m.text()); });
  await page.goto(url);
  await page.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
  const sk = await installSeek(page);
  const info = await page.evaluate(() => {
    const c = document.getElementById('c');
    return { canvas: !!c, cw: c?.width, ch: c?.height, dur: window.DURATION, fps: window.FPS };
  });
  if (!sk.seek && !sk.anims) throw new Error('A página não define window.seek(t)/renderAt(t) nem tem animações CSS.');
  if (!W || !H) { W = info.canvas ? info.cw : 1080; H = info.canvas ? info.ch : 1920; await page.setViewportSize({ width: W, height: H }); }
  if (info.canvas && !flag('dom')) {
    // acumulador de motion blur dentro da página
    await page.evaluate((linear) => {
      const c = document.getElementById('c');
      // sRGB ↔ linear: a média de subframes em luz linear é como o filme registra movimento (sem "escurecer" bordas)
      const toLin = new Float32Array(256), N2 = 4096, toS = new Uint8ClampedArray(N2 + 1);
      for (let i = 0; i < 256; i++) { const v = i / 255; toLin[i] = linear ? (v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)) : v; }
      for (let i = 0; i <= N2; i++) { const v = i / N2; toS[i] = Math.round(255 * (linear ? (v <= 0.0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - 0.055) : v)); }
      window.__acc = null;
      // CORTES: nenhum subframe atravessa um corte seco (senão o 1º frame do plano novo carrega um fantasma do anterior).
      // window.CUTS = [t,...] ou, na falta, os fins de window.SHOTS com out 'cut'.
      const CUTS = (window.CUTS || (window.SHOTS || []).filter((s) => !s.out || s.out === 'cut').map((s) => s.to)).filter((x) => x > 0);
      const side = (t, ts) => { for (const k of CUTS) { if (t < k && ts >= k) return k - 1e-4; if (t >= k && ts < k) return k; } return ts; };
      const sample = (g) => { const d = g.getImageData(0, 0, c.width, c.height).data, o = new Uint8Array(4096), st = Math.max(4, Math.floor(d.length / 4 / 4096) * 4); for (let i = 0, j = 0; j < 4096 && i < d.length; i += st, j++) o[j] = d[i + 1]; return o; };
      window.__frame = async (t, sub, dt, mime, q) => {
        window.__frameT = t; // tempo central → contadores/textos discretos não borram
        if (window.SUB_AT) sub = Math.max(1, Math.min(64, window.SUB_AT(t) | 0 || sub));   // a cena pode pedir mais amostras num whip
        if (sub === 1) { window.__seek(t); return c.toDataURL(mime, q); }
        const g = c.getContext('2d', { willReadFrequently: true });
        const auto = sub === 0; if (auto) sub = 32;
        // BLUR ADAPTATIVO: se as pontas do obturador são iguais, o frame está parado → 1 amostra (rápido e sem fantasma)
        window.__seek(side(t, t - dt / 2)); const a = sample(g); window.__seek(side(t, t + dt / 2)); const b = sample(g);
        let diff = 0; for (let i = 0; i < a.length; i++) if (Math.abs(a[i] - b[i]) > 2) diff++;
        if (diff / a.length < 0.0005) { window.__seek(t); return c.toDataURL(mime, q); }
        if (auto) { const f = diff / a.length; sub = f < 0.03 ? 4 : f < 0.12 ? 8 : f < 0.3 ? 16 : 32; }   // whip/tela inteira andando → mais amostras (sem 'cópias' separadas)
        const n = c.width * c.height * 4;
        if (!window.__acc || window.__acc.length !== n) window.__acc = new Float32Array(n);
        const acc = window.__acc; acc.fill(0);
        for (let s = 0; s < sub; s++) {
          window.__seek(side(t, t + (s / sub - 0.5 + 0.5 / sub) * dt)); // centrado no instante t, do lado certo do corte
          const d = g.getImageData(0, 0, c.width, c.height).data;
          // alfa PRÉ-MULTIPLICADO: com fundo transparente (--alpha) a média direta escurece as bordas (franja preta)
          for (let i = 0; i < n; i += 4) { const a = d[i + 3] / 255; acc[i] += toLin[d[i]] * a; acc[i + 1] += toLin[d[i + 1]] * a; acc[i + 2] += toLin[d[i + 2]] * a; acc[i + 3] += d[i + 3]; }
        }
        const out = g.createImageData(c.width, c.height), o = out.data, k = 1 / sub;
        for (let i = 0; i < n; i += 4) {
          const un = acc[i + 3] > 0 ? 255 / acc[i + 3] : 0;   // desfaz a pré-multiplicação (opaco: = 1/sub, igual a antes)
          o[i] = toS[Math.min(N2, Math.round(acc[i] * un * N2))]; o[i + 1] = toS[Math.min(N2, Math.round(acc[i + 1] * un * N2))]; o[i + 2] = toS[Math.min(N2, Math.round(acc[i + 2] * un * N2))];
          o[i + 3] = acc[i + 3] * k + 0.5;
        }
        g.putImageData(out, 0, 0);
        return c.toDataURL(mime, q);
      };
    }, LINEAR);
  }
  return { page, info };
}

const first = await openPage();
const FPS = num('fps', first.info.fps || 60);
const DUR = num('dur', first.info.dur || 10);
const FROM = num('from', 0), TO = num('to', DUR);
const f0 = Math.round(FROM * FPS), f1 = Math.round(TO * FPS);
const total = f1 - f0;
const canvasMode = first.info.canvas && !flag('dom');
const ext = flag('jpeg') ? 'jpg' : 'png';
const mime = flag('jpeg') ? 'image/jpeg' : 'image/png';
const frameDir = join(dirname(OUT), '.frames_' + Date.now());
mkdirSync(frameDir, { recursive: true });

console.log(`▶ ${input}\n  ${W}x${H} @${FPS}fps · ${FROM}s→${TO}s (${total} frames) · sub ${SUB_AUTO ? 'auto' : SUB} · ${canvasMode ? 'canvas' : 'dom'} · ${WORKERS} workers`);
const t0 = Date.now();
let done = 0;
const dtShutter = SHUTTER / FPS;

async function worker(w) {
  const { page } = w === 0 ? first : await openPage();
  for (let f = f0 + w; f < f1; f += WORKERS) {
    const t = f / FPS, idx = f - f0;
    if (canvasMode) {
      const dataUrl = await page.evaluate(([t, s, dt, m]) => window.__frame(t, s, dt, m, 0.95), [t, SUB, dtShutter, mime]);
      writeFileSync(join(frameDir, `${String(idx).padStart(6, '0')}.${ext}`), Buffer.from(dataUrl.split(',')[1], 'base64'));
    } else {
      await page.evaluate((x) => { window.__frameT = x; }, t);
      for (let s = 0; s < SUB; s++) {
        const ts = SUB === 1 ? t : t + (s / SUB - 0.5 + 0.5 / SUB) * dtShutter;
        await page.evaluate((x) => window.__seek(x), ts);
        await page.screenshot({ path: join(frameDir, `${String(idx * SUB + s).padStart(7, '0')}.${ext}`), type: flag('jpeg') ? 'jpeg' : 'png', quality: flag('jpeg') ? 95 : undefined });
      }
    }
    done++;
    if (done % Math.max(1, Math.round(FPS)) === 0) {
      const el = (Date.now() - t0) / 1000;
      process.stdout.write(`\r  ${done}/${total} frames · ${(done / el).toFixed(1)} fps · ETA ${((total - done) / (done / el)).toFixed(0)}s   `);
    }
  }
}
await Promise.all(Array.from({ length: WORKERS }, (_, w) => worker(w)));
await browser.close();
console.log(`\n  frames em ${((Date.now() - t0) / 1000).toFixed(1)}s — codificando…`);

mkdirSync(dirname(OUT), { recursive: true });
const tmp = OUT.replace(/\.(mp4|mov)$/, '.tmp.$1');
const pattern = join(frameDir, canvasMode ? `%06d.${ext}` : `%07d.${ext}`);
// JPEG entra em faixa cheia: sem converter, o MP4 sai yuvj420p, que players e redes tratam mal
const saida = flag('jpeg') ? 'scale=in_range=pc:out_range=tv,format=yuv420p' : 'format=yuv420p';
const vf = canvasMode || SUB === 1
  ? saida
  : `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB,${saida}`;
// --deband: gradiente grande em 8 bits "escadinha" (banding) — bitrate não resolve; gradfun + grão fino resolve.
// --alpha: ProRes 4444 com transparência (.mov) para o editor do cliente pôr por cima do vídeo dele (fundo da página transparente).
// --master: ProRes 422 HQ 10 bits (.mov) para quem vai editar/colorir depois. O MP4 H.264 continua sendo a entrega de redes.
const band = flag('deband') ? 'gradfun=strength=1.2:radius=16,noise=alls=3:allf=t,' : '';
const down = SS > 1 ? `scale=${OUTW}:${OUTH}:flags=lanczos,` : '';
const vfFinal = vf.replace(/format=yuv420p$/, `${down}${band}format=yuv420p`);
const COLOR = ['-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709'];
const args = flag('alpha') || flag('master')
  ? ['-y', '-loglevel', 'error', '-framerate', String(canvasMode ? FPS : FPS * SUB), '-i', pattern, '-vf', (down + vf.replace(/,?(scale=[^,]*,)?format=yuv420p$/, '')).replace(/,$/, '') || 'null',
     '-r', String(FPS), '-c:v', 'prores_ks', '-profile:v', flag('alpha') ? '4444' : '3', '-pix_fmt', flag('alpha') ? 'yuva444p10le' : 'yuv422p10le',
     ...(flag('alpha') ? ['-alpha_bits', '16'] : []), ...COLOR, tmp]
  : ['-y', '-loglevel', 'error', '-framerate', String(canvasMode ? FPS : FPS * SUB), '-i', pattern,
     '-vf', vfFinal, '-r', String(FPS), '-c:v', 'libx264', '-preset', opt('preset', 'medium'), '-crf', String(CRF),
     '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-color_range', 'tv', ...COLOR, tmp];
const code = await new Promise((r) => spawn('ffmpeg', args, { stdio: 'inherit' }).on('close', r));
if (code !== 0) { console.error('ffmpeg falhou; frames mantidos em', frameDir); process.exit(1); }
renameSync(tmp, OUT);
if (!flag('keep')) rmSync(frameDir, { recursive: true, force: true });
console.log(`✔ ${OUT} (${((Date.now() - t0) / 1000).toFixed(1)}s total)`);
