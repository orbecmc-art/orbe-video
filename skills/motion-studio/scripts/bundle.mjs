#!/usr/bin/env node
/* bundle.mjs — o filme vira UMA página autocontida: código, dados, cenas, fontes, imagens e a trilha embutidos.
 *
 *   node scripts/bundle.mjs [index.html] [--audio out/final.mp4] [--out out/filme.html] [--title "Nome"]
 *
 * Para: publicar como Artifact/link privado para o cliente aprovar no celular, mandar por WhatsApp/Drive, ou entregar em
 * chat sem render. A página abre no PLAYER (lib/recorder.js): Play · Pausar · Reiniciar · Gravar (o cliente baixa um MP4/WebM
 * gravado no navegador dele, com som). O relógio é o áudio → sincronia mantida.
 * --audio: o MIX FINAL (mp4 ou wav). É recodificado em AAC 160k para a página ficar leve. Sem --audio, toca mudo.
 * Limite prático: ~15 MB. Avisa se passar.
 */
import { syncCampaign } from './pw.mjs';
import { readFileSync, writeFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { resolve, dirname, join, extname, basename } from 'node:path';
import { execFileSync } from 'node:child_process';
import os from 'node:os';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const input = resolve(argv.find((a, i) => a.endsWith('.html') && !(i > 0 && argv[i - 1].startsWith('--'))) || 'index.html');
const ROOT = dirname(input);
syncCampaign(input);
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.gif': 'image/gif', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const dataURI = (p) => `data:${MIME[extname(p).toLowerCase()] || 'application/octet-stream'};base64,${readFileSync(p).toString('base64')}`;
const esc = (js) => js.replace(/<\/script/gi, '<\\/script');
let inlinedAssets = 0;
// strings 'assets/x.png', "brand/logo.svg", `img/a.webp` dentro do código → data URI
const inlineAssets = (src) => src.replace(/(['"`])((?:\.\/)?(?:assets|brand|img|images|refs)\/[^'"`]+?\.(?:png|jpe?g|webp|svg|gif))\1/gi, (m, q, p) => {
  const f = join(ROOT, p); if (!existsSync(f)) return m; inlinedAssets++; return q + dataURI(f) + q; });

let html = readFileSync(input, 'utf8');
// scripts locais (data.js: os document.write das cenas viram as próprias cenas, em ordem)
html = html.replace(/<script src="([^"]+)"><\/script>/g, (m, src) => {
  if (/^https?:/.test(src)) return m;
  const f = join(ROOT, src); if (!existsSync(f)) { console.warn('⚠ script não encontrado:', src); return m; }
  let js = readFileSync(f, 'utf8');
  js = js.replace(/document\.write\('<script src="([^"]+)"><\\\/script>'\);/g, (mm, s2) => { const f2 = join(ROOT, s2); return existsSync(f2) ? `\n/* ${s2} */\n` + readFileSync(f2, 'utf8') : mm; });
  return `<script>/* ${src} */\n${esc(inlineAssets(js))}\n</script>`;
});
// fontes
html = html.replace(/<link rel="stylesheet" href="([^"]+\.css)">/g, (m, href) => {
  const f = join(ROOT, href); if (!existsSync(f)) return '';
  const css = readFileSync(f, 'utf8').replace(/url\((['"]?)([^)'"]+)\1\)/g, (mm, q, u) => { const ff = join(dirname(f), u); return existsSync(ff) ? `url(${dataURI(ff)})` : mm; });
  return `<style>${css}</style>`;
});
html = inlineAssets(html);
// trilha
let head = '<script>window.BUNDLED = true;</script>';
if (opt('audio')) {
  const tmp = join(os.tmpdir(), `bundle_${process.pid}.m4a`);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', resolve(opt('audio')), '-vn', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', tmp]);
  head = `<script>window.BUNDLED = true; window.SOUNDTRACK = "data:audio/mp4;base64,${readFileSync(tmp).toString('base64')}";</script>`;
}
if (opt('title')) html = html.replace(/<title>[^<]*<\/title>/, `<title>${opt('title')}</title>`);
html = html.replace(/<head>/, `<head>\n<meta name="viewport" content="width=device-width,initial-scale=1">\n${head}`);
// no player, o canvas cabe na tela (o CSS do template já limita fora do modo render)
const out = resolve(opt('out', join(ROOT, 'out', basename(ROOT) + '.html')));
mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, html);
const mb = statSync(out).size / 1e6;
console.log(`✔ ${out} · ${mb.toFixed(1)} MB · ${inlinedAssets} imagem(ns) embutida(s)${opt('audio') ? ' · trilha embutida (AAC 160k)' : ' · sem trilha'}${mb > 15 ? '  ⚠ > 15 MB: comprima imagens ou encurte' : ''}`);
console.log('  abra no navegador: Play / Gravar. Publicar como Artifact: a página já é autocontida.');
