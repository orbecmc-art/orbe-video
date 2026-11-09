#!/usr/bin/env node
/* pecas.mjs — lê CUES/VALIDATE de cada peça de motion e tira stills (PNG com alfa) para revisão.
 *   node pecas.mjs --ms <motion-studio> --page motion/pecas.html --ids mo01,mo02 [--w 1080 --h 1920] [--stills motion/stills]
 * Saída (stdout): JSON { mo01: { dur, cues:[…], validate:[…], stills:[{t, arquivo}] } }
 * Para páginas próprias (peça custom = projeto motion-studio), passe --page <projeto>/index.html --ids _ (sem ?peca).
 */
import { resolve, join } from 'node:path';
import { mkdirSync } from 'node:fs';
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const MS = resolve(opt('ms'));
const { chromium, filmURL, installSeek } = await import(join(MS, 'scripts/pw.mjs'));
const page = resolve(opt('page')), ids = opt('ids', '_').split(','), W = +opt('w', 1080), H = +opt('h', 1920);
const dirStills = opt('stills'); if (dirStills) mkdirSync(dirStills, { recursive: true });
const b = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none'] });
const out = {};
for (const id of ids) {
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto(filmURL(page, { w: W, h: H, extra: id === '_' ? {} : { peca: id, ...(opt('alpha-ids', '').split(',').includes(id) ? { alpha: '1' } : {}) } }));
  await p.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
  await installSeek(p);
  const info = await p.evaluate(() => ({
    dur: window.DURATION, fps: window.FPS,
    cues: (typeof window.CUES === 'function' ? window.CUES() : window.CUES) || [],
    validate: typeof window.VALIDATE === 'function' ? window.VALIDATE() : [],
  }));
  info.erros = errs; info.stills = [];
  if (dirStills) {
    const ts = [0.18, Math.min(info.dur * 0.55, 1.3), Math.max(0, info.dur - 0.12)];
    for (const t of ts) {
      await p.evaluate((x) => window.__seek(x), t);
      const f = join(dirStills, `${id}_${t.toFixed(2)}.png`);
      const el = await p.$('canvas#c');
      if (el) await el.screenshot({ path: f, omitBackground: true }); else await p.screenshot({ path: f, omitBackground: true });
      info.stills.push({ t, arquivo: f });
    }
  }
  out[id] = info; await p.close();
}
await b.close();
process.stdout.write(JSON.stringify(out));
