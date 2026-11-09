#!/usr/bin/env node
/* clips.mjs — uma cena numerada = um clipe. Edição "como falar com um editor": "3, câmera mais perto" → mexe em scenes/03.js
 * e re-renderiza SÓ out/clip_03.mp4 (cache por hash da cena + libs + dados).
 *
 *   node scripts/clips.mjs                 # todos os clipes (rascunho: 30 fps, sem blur, jpeg) → out/clip_NN.mp4 + out/clips.png
 *   node scripts/clips.mjs --only 03,05    # só essas
 *   node scripts/clips.mjs --final         # qualidade final (fps do roteiro, motion blur 4 subframes)
 * Funciona com scenes.json (modo série) ou com window.SHOTS (qualquer filme: uma linha do board = um clipe).
 */
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { chromium, syncCampaign, filmURL } from './pw.mjs';
const argv = process.argv.slice(2), flag = (k) => argv.includes('--' + k);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const HTML = resolve('index.html'), HERE = dirname(new URL(import.meta.url).pathname), OUT = resolve('out');
syncCampaign(HTML);
const b = await chromium.launch(); const p = await b.newPage();
await p.goto(filmURL(HTML)); await p.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
const shots = await p.evaluate(() => (window.SCENES ? window.SCENES.scenes.map((s) => ({ id: s.id, from: s.start, to: s.start + s.duration_sec })) : (window.SHOTS || []).map((s, i) => ({ id: String(i + 1).padStart(2, '0'), from: s.from, to: s.to }))));
const fps0 = await p.evaluate(() => window.FPS); await b.close();
const only = opt('only') ? opt('only').split(',').map((x) => x.padStart(2, '0')) : null;
const fps = flag('final') ? fps0 : Number(opt('fps', 30)), sub = flag('final') ? 4 : 1;
const h = (f) => (existsSync(f) ? createHash('sha1').update(readFileSync(f)).digest('hex') : '-');
const libs = ['lib/motion.js', 'lib/rig.js', 'lib/fx.js', 'index.html', 'data.js', 'campaign.json'].map(h).join('');
mkdirSync(OUT, { recursive: true }); const made = [];
for (const s of shots) {
  if (only && !only.includes(s.id)) continue;
  const key = createHash('sha1').update(libs + h(`scenes/${s.id}.js`) + JSON.stringify(s) + fps + sub).digest('hex').slice(0, 10);
  const out = join(OUT, `clip_${s.id}.mp4`), stamp = out + '.key';
  if (existsSync(out) && existsSync(stamp) && readFileSync(stamp, 'utf8') === key) { console.log(`= clip_${s.id} (sem mudança)`); made.push(out); continue; }
  const r = spawnSync('node', [join(HERE, 'render.mjs'), HTML, '--from', String(s.from), '--to', String(s.to), '--fps', String(fps), '--sub', String(sub), '--out', out, ...(flag('final') ? [] : ['--jpeg'])], { stdio: 'pipe', encoding: 'utf8' });
  if (r.status) { console.error(r.stderr); process.exit(1); }
  writeFileSync(stamp, key); made.push(out); console.log(`✔ clip_${s.id} · ${s.from.toFixed(2)}→${s.to.toFixed(2)}s`);
}
// folha de revisão: o meio de cada clipe, numerado
const list = made.map((f) => `-ss 0.6 -i ${f}`).join(' ');
if (made.length) { spawnSync('bash', ['-c', `ffmpeg -v error -y ${made.map((f) => `-ss 0.8 -i '${f}'`).join(' ')} -filter_complex "${made.map((_, i) => `[${i}:v]scale=270:-2,drawtext=text='${String(i + 1).padStart(2, '0')}':x=10:y=10:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.6[v${i}]`).join(';')};${made.map((_, i) => `[v${i}]`).join('')}hstack=inputs=${made.length}" -frames:v 1 '${join(OUT, 'clips.png')}'`]); }
console.log(`→ ${made.length} clipe(s) · folha em out/clips.png · protocolo de edição: "NN, mudança" → só a cena NN muda`);
