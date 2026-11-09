// pw.mjs — utilitários compartilhados: Playwright (local OU global), campanha → campaign.js, URL de variante, "seek universal".
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

let pw;
try { pw = await import('playwright'); }
catch {
  try { pw = createRequire(execSync('npm root -g').toString().trim() + '/')('playwright'); }
  catch { console.error('Playwright não encontrado. Rode: npm i -D playwright && npx playwright install chromium'); process.exit(1); }
}
export const chromium = pw.chromium || pw.default.chromium;

export const FORMATS = { '9x16': [1080, 1920], '1x1': [1080, 1080], '16x9': [1920, 1080], '4x5': [1080, 1350], '4k': [3840, 2160] };

// campaign.json (fonte da verdade, editável) → campaign.js (window.CAMPAIGN, para o index.html abrir via file://)
// Série/personagem: scenes.json + hero/hero.json + audio/{words,mouth,loud}.json → data.js (window.SCENES, HERO, WORDS, VOICE)
// e carrega cada cena numerada scenes/NN.js (cenas isoladas: editar a 03 não quebra a 04).
export function syncData(htmlPath) {
  const dir = dirname(htmlPath), sj = join(dir, 'scenes.json');
  if (!existsSync(sj)) return null;
  const rd = (p, d = null) => (existsSync(join(dir, p)) ? JSON.parse(readFileSync(join(dir, p), 'utf8')) : d);
  const S = rd('scenes.json'), mouth = rd('audio/mouth.json'), loud = rd('audio/loud.json');
  const voice = mouth ? { fps: mouth.fps, mouth: mouth.shapes, env: loud?.env || [], stress: loud?.stress || [], source: mouth.source } : null;
  const files = S.scenes.map((sc) => `scenes/${sc.id}.js`).filter((f) => existsSync(join(dir, f)));
  const out = `// GERADO por scripts (syncData) de scenes.json, hero/hero.json e audio/*.json — NÃO edite aqui\n` +
    `window.SCENES = ${JSON.stringify(S)};\nwindow.HERO = ${JSON.stringify(rd('hero/hero.json', {}))};\nwindow.CAST = ${JSON.stringify(rd('hero/cast.json', {}))};\n` +
    `window.WORDS = ${JSON.stringify(rd('audio/words.json', []))};\nwindow.VOICE = ${JSON.stringify(voice)};\nwindow.SCENE = {};\n` +
    files.map((f) => `document.write('<script src="${f}"><\\/script>');`).join('\n') + '\n';
  const js = join(dir, 'data.js');
  if (!existsSync(js) || readFileSync(js, 'utf8') !== out) writeFileSync(js, out);
  return S;
}

export function syncCampaign(htmlPath) {
  syncData(htmlPath);
  const dir = dirname(htmlPath), json = join(dir, 'campaign.json'), js = join(dir, 'campaign.js');
  if (!existsSync(json)) return null;
  const data = JSON.parse(readFileSync(json, 'utf8'));
  const out = `// GERADO de campaign.json por scripts/campaign.mjs sync — NÃO edite aqui, edite o campaign.json\nwindow.CAMPAIGN = ${JSON.stringify(data, null, 1)};\n`;
  if (!existsSync(js) || readFileSync(js, 'utf8') !== out) writeFileSync(js, out);
  return data;
}

// URL do filme com formato/variante: ?render=1&w=&h=&format=&hook=&cta=
// --query "peca=mo03&t=1" e --alpha na linha de comando de QUALQUER script chegam à página (ponte com o edita-video:
// uma página de peças renderiza cada item do mapa por id; ?alpha=1 → a página não pinta fundo).
const _ARGV = process.argv.slice(2);
function argQuery() {
  const i = _ARGV.indexOf('--query'); const q = i >= 0 ? Object.fromEntries(new URLSearchParams(_ARGV[i + 1] || '')) : {};
  if (_ARGV.includes('--alpha')) q.alpha = '1';
  return q;
}
export function filmURL(htmlPath, { w, h, format, hook, cta, render = true, extra = {} } = {}) {
  const qs = new URLSearchParams(render ? { render: '1' } : {});
  extra = { ...argQuery(), ...extra };
  if (format && FORMATS[format]) { [w, h] = FORMATS[format]; qs.set('format', format); }
  if (w) qs.set('w', w); if (h) qs.set('h', h);
  if (hook != null) qs.set('hook', hook); if (cta != null) qs.set('cta', cta);
  for (const [k, v] of Object.entries(extra)) qs.set(k, v);
  return 'file://' + htmlPath + '?' + qs.toString();
}

// Instala window.__seek(t): chama seek/renderAt E congela animações CSS/WAAPI no mesmo t
// (assim filmes feitos só com @keyframes ou Web Animations também renderizam frame-exato).
export async function installSeek(page) {
  return page.evaluate(() => {
    // ponte HyperFrames/GSAP (estilos/ da galeria): timeline pausada em window.__timelines.main + data-duration no #root
    if (!window.seek && window.__timelines && Object.keys(window.__timelines).length) {
      const tl = window.__timelines.main || Object.values(window.__timelines)[0];
      window.seek = (t) => { tl.seek(t, false); if (window.STUDIO && window.STUDIO.__render) window.STUDIO.__render(t); };
      const root = document.querySelector('[data-composition-id]');
      if (!window.DURATION) window.DURATION = root ? +root.dataset.duration : tl.duration();
      if (!window.FPS) window.FPS = 30;
    }
    window.__seek = (t) => {
      const f = window.seek || window.renderAt; if (f) f(t);
      for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
    };
    return { seek: !!(window.seek || window.renderAt), anims: document.getAnimations().length };
  });
}
