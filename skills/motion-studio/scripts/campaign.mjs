#!/usr/bin/env node
/* campaign.mjs — um brief, muitas versões. Dados (campaign.json) separados da animação (index.html).
 *
 *   node scripts/campaign.mjs sync                       # campaign.json → campaign.js (o preview no navegador lê isto)
 *   node scripts/campaign.mjs validate [--draft]         # trava o brief antes de gastar render (ver abaixo)
 *   node scripts/campaign.mjs render [--draft] [--formats 9x16,1x1] [--hooks a,b] [--ctas x] [--fps 60 --sub 4]
 *   node scripts/campaign.mjs package                    # pasta de entrega + manifest.json + LEIA-ME.md + .zip
 *   node scripts/campaign.mjs all [--draft]              # validate → render → package
 *
 * VALIDATE recusa o brief se: faltar asset/fonte · texto não couber (VALIDATE() do filme, em cada formato) ·
 *   CHECKS numéricos falharem · algum NÚMERO na copy não vier de um claim aprovado com fonte · claim de EXEMPLO ·
 *   approval.copy ≠ true (o cliente aprova o que o vídeo DIZ) · o CONTRATO DE VARIANTES quebrar
 *   (gancho mexendo depois da cena "hook" ou CTA mexendo antes da cena "cta" — conferido por hash de pixels).
 *   --draft transforma claim de exemplo e aprovação pendente em avisos (para rascunho interno, nunca para o cliente).
 *
 * RENDER por segmentos com cache: por formato renderiza [gancho × N] + [miolo × 1] + [CTA × M] e concatena
 *   (3 ganchos × 2 CTAs = 6 vídeos custam ~1,6 vídeo de render). Segmento só re-renderiza se html/motion/campanha/
 *   fontes/ajustes mudarem (hash). Áudio por variante: sfx nivelado contra a trilha, mix −14 LUFS, auditoria.
 */
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync, mkdirSync, copyFileSync, readdirSync, statSync } from 'node:fs';
import { resolve, dirname, join, relative, basename } from 'node:path';
import { chromium, syncCampaign, filmURL, installSeek, FORMATS } from './pw.mjs';

const argv = process.argv.slice(2), CMD = argv[0] || 'validate';
const flag = (k) => argv.includes('--' + k);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : d; };
const ROOT = resolve(opt('dir', '.')), HTML = join(ROOT, 'index.html'), HERE = dirname(new URL(import.meta.url).pathname);
const OUT = join(ROOT, 'out'), DRAFT = flag('draft');
const sh = (cmd, args, o = {}) => { const r = spawnSync(cmd, args, { stdio: o.quiet ? 'pipe' : 'inherit', cwd: ROOT, encoding: 'utf8' }); if (r.status !== 0 && !o.allowFail) { console.error(`✗ falhou: ${cmd} ${args.join(' ')}\n${r.stderr || ''}`); process.exit(1); } return r; };
const sha = (buf) => createHash('sha256').update(buf).digest('hex');
const fileSha = (p) => (existsSync(p) ? sha(readFileSync(p)) : 'missing');
if (!existsSync(join(ROOT, 'campaign.json'))) { console.error('✗ campaign.json não encontrado em ' + ROOT); process.exit(1); }
const C = syncCampaign(HTML);
const scene = (id) => C.scenes.find((s) => s.id === id);
const pickList = (list, sel) => (sel ? list.filter((x) => sel.split(',').includes(x.id)) : list);

// ═════════════════════════════════════ VALIDATE ═════════════════════════════════════
async function validate() {
  const E = [], Wn = [], ok = [];
  const err = (m) => (DRAFT && m.startsWith('[draft]') ? Wn.push(m.slice(8)) : E.push(m.replace(/^\[draft\] /, '')));
  // 1. estrutura
  for (const k of ['bg', 'ink', 'accent']) if (!C.brand?.colors?.[k]) E.push(`brand.colors.${k} ausente`);
  if (!C.hooks?.length) E.push('nenhum gancho em hooks'); if (!C.ctas?.length) E.push('nenhum CTA em ctas');
  for (const f of C.formats || []) if (!FORMATS[f]) E.push(`formato desconhecido: ${f}`);
  const H = scene('hook'), K = scene('cta');
  if (!H || !K) E.push('scenes precisa de uma cena "hook" e uma "cta" (fronteiras das variantes)');
  else if (H.end > K.start) E.push('a cena hook termina depois do início da cena cta');
  // 2. assets e fontes
  if (C.brand.logo && !existsSync(join(ROOT, C.brand.logo))) E.push(`logo não encontrado: ${C.brand.logo}`);
  if (C.audio?.music && !existsSync(join(ROOT, C.audio.music))) Wn.push(`trilha ${C.audio.music} não existe — o render vai sintetizar (music.mjs --style ${C.audio.style || 'tech'})`);
  const css = existsSync(join(ROOT, 'fonts/fonts.css')) ? readFileSync(join(ROOT, 'fonts/fonts.css'), 'utf8') : '';
  const sys = spawnSync('fc-list', [':', 'family'], { encoding: 'utf8' }).stdout || '';
  for (const fam of new Set(Object.values(C.brand.fonts || {}))) {
    if (!css.includes(`'${fam}'`) && !sys.includes(fam)) E.push(`fonte "${fam}" não está em fonts/fonts.css nem no sistema → cairia no fallback (rode scripts/fonts.sh)`);
    else if (!css.includes(`'${fam}'`)) Wn.push(`fonte "${fam}" só existe no SISTEMA desta máquina — para entregar/reproduzir, baixe com scripts/fonts.sh`);
  }
  // 3. claims: todo número dito no vídeo vem de um claim aprovado, com fonte
  const claims = Object.fromEntries((C.claims || []).map((c) => [c.id, c]));
  for (const c of C.claims || []) {
    if (!c.approved) E.push(`claim "${c.id}" não aprovado pelo cliente`);
    if (!c.source) E.push(`claim "${c.id}" sem fonte (de onde veio o número?)`);
    else if (/EXEMPLO/i.test(c.source)) err(`[draft] claim "${c.id}" ainda é de EXEMPLO — troque pelo dado real do cliente`);
  }
  const texts = [];
  const walk = (o, path) => { if (typeof o === 'string') texts.push([path, o]); else if (Array.isArray(o)) o.forEach((x, i) => walk(x, `${path}[${i}]`)); else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) walk(v, `${path}.${k}`); };
  walk(C.copy, 'copy'); C.hooks.forEach((h) => walk(h.lines, `hooks.${h.id}`)); C.ctas.forEach((c) => walk(c.text, `ctas.${c.id}`));
  const approvedNums = (C.claims || []).filter((c) => c.approved).flatMap((c) => [String(c.value), (c.text.match(/\d[\d.,]*/g) || [])].flat().map((x) => x.replace(/[.,]/g, '')));
  for (const [p, s] of texts) for (const m of s.match(/\d[\d.,]*/g) || []) if (!approvedNums.includes(m.replace(/[.,]/g, ''))) E.push(`número "${m}" em ${p} não vem de nenhum claim aprovado — o modelo nunca inventa dado`);
  for (const h of C.hooks) if (h.claim && !claims[h.claim]?.approved) E.push(`gancho "${h.id}" usa claim "${h.claim}" não aprovado`);
  if (C.approval?.copy !== true) err('[draft] approval.copy ≠ true — o cliente ainda não aprovou o que o vídeo diz');
  // 4. no navegador, por formato: VALIDATE(), CHECKS e contrato de variantes por hash de pixels
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  const open = async (format, hook, cta) => {
    const [w, h] = FORMATS[format]; const p = await browser.newPage({ viewport: { width: w, height: h } });
    p.on('pageerror', (e) => E.push(`[${format}] erro na página: ${e.message}`));
    await p.goto(filmURL(HTML, { format, hook, cta })); await p.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
    await installSeek(p); return p;
  };
  const hash = async (p, t) => sha(await p.evaluate((t) => { window.__frameT = t; window.__seek(t); return document.getElementById('c').toDataURL('image/png'); }, t));
  const fps = C.fps || 60, h0 = C.hooks[0].id, c0 = C.ctas[0].id;
  for (const f of C.formats) {
    const p = await open(f, h0, c0);
    const v = await p.evaluate(() => (window.VALIDATE ? window.VALIDATE() : []));
    v.forEach((m) => E.push(`[${f}] ${m}`));
    const chk = await p.evaluate(() => (window.CHECKS || []).map((c) => { window.__frameT = c.t; window.__seek(c.t); let r; try { r = c.test(c.t); } catch (e) { r = e.message; } return { n: c.name, t: c.t, r: r === true ? true : String(r) }; }));
    chk.filter((c) => c.r !== true).forEach((c) => E.push(`[${f}] CHECK "${c.n}" @${c.t.toFixed(2)}s: ${c.r}`));
    if (H && K) {
      const mid = [H.end + 2 / fps, (H.end + K.start) / 2, K.start - 1 / fps], ref = {};
      for (const t of [...mid, H.end - 1 / fps, K.start]) ref[t] = await hash(p, t);
      for (const hk of C.hooks.slice(1)) {
        const q = await open(f, hk.id, c0);
        for (const t of [...mid, H.end - 1 / fps]) if ((await hash(q, t)) !== ref[t]) E.push(`[${f}] contrato quebrado: gancho "${hk.id}" muda o frame ${Math.round(t * fps)} (${t.toFixed(2)}s) — o gancho precisa sumir antes de ${H.end}s`);
        await q.close();
      }
      for (const ct of C.ctas.slice(1)) {
        const q = await open(f, h0, ct.id);
        for (const t of [...mid, K.start]) if ((await hash(q, t)) !== ref[t]) E.push(`[${f}] contrato quebrado: CTA "${ct.id}" muda o frame ${Math.round(t * fps)} (${t.toFixed(2)}s) — o CTA só pode aparecer depois de ${K.start}s`);
        await q.close();
      }
    }
    ok.push(`${f}: ${v.length ? v.length + ' problema(s) de texto' : 'textos cabem'} · ${chk.filter((c) => c.r === true).length}/${chk.length} checks`);
    await p.close();
  }
  await browser.close();
  const md = `# Validação — ${C.project}${DRAFT ? ' (RASCUNHO)' : ''}\n\n` +
    `${E.length ? '## ✗ Erros (bloqueiam o render)\n' + E.map((x) => '- ' + x).join('\n') + '\n\n' : '## ✔ Sem erros\n\n'}` +
    `${Wn.length ? '## ⚠ Avisos\n' + Wn.map((x) => '- ' + x).join('\n') + '\n\n' : ''}## Formatos\n${ok.map((x) => '- ' + x).join('\n')}\n`;
  mkdirSync(OUT, { recursive: true }); writeFileSync(join(OUT, 'validate.md'), md);
  console.log(md);
  return E.length === 0;
}

// ═════════════════════════════════════ RENDER ═════════════════════════════════════
async function render() {
  if (!flag('skip-validate') && !(await validate())) { console.error('✗ validação falhou — veja out/validate.md (use --draft para rascunho interno)'); process.exit(1); }
  const H = scene('hook'), K = scene('cta'), DUR = C.duration;
  const formats = (opt('formats') ? opt('formats').split(',') : C.formats), hooks = pickList(C.hooks, opt('hooks')), ctas = pickList(C.ctas, opt('ctas'));
  const fps = Number(opt('fps', DRAFT ? 30 : C.fps || 60)), sub = Number(opt('sub', DRAFT ? 1 : 4));
  const settings = { fps, sub, crf: Number(opt('crf', 16)), jpeg: DRAFT || flag('jpeg') };
  const codeKey = sha([HTML, join(ROOT, 'lib/motion.js'), join(ROOT, 'fonts/fonts.css'), join(ROOT, 'campaign.json')].map(fileSha).join('|') + JSON.stringify(settings)).slice(0, 12);
  const musicDb = C.audio?.musicDb ?? -4, music = join(ROOT, C.audio?.music || 'audio/music.wav');
  if (!existsSync(music)) sh('node', [join(HERE, 'music.mjs'), '--bpm', String(C.bpm || 120), '--dur', String(DUR), '--style', C.audio?.style || 'tech', '--fps', String(fps), '--out', music, '--beats', join(ROOT, 'audio/beats.json')]);
  const t0 = Date.now(); let renderedSec = 0, cached = 0;
  const seg = (fmt, name, from, to, hook, cta) => {
    const dir = join(OUT, 'cache', fmt); mkdirSync(dir, { recursive: true });
    const file = join(dir, `${name}_${codeKey}.mp4`);
    if (existsSync(file)) { cached++; return file; }
    console.log(`▶ ${fmt} · ${name} (${from}s→${to}s)`);
    sh('node', [join(HERE, 'render.mjs'), HTML, '--format', fmt, '--from', String(from), '--to', String(to), '--hook', hook, '--cta', cta,
      '--fps', String(fps), '--sub', String(sub), '--crf', String(settings.crf), '--out', file, ...(settings.jpeg ? ['--jpeg'] : [])], { quiet: true });
    renderedSec += to - from; return file;
  };
  // áudio por variante (independe do formato)
  const audioFor = {};
  for (const h of hooks) for (const c of ctas) {
    const sfx = join(OUT, 'cache', 'audio', `sfx_${h.id}_${c.id}_${codeKey}.wav`); mkdirSync(dirname(sfx), { recursive: true });
    if (!existsSync(sfx)) sh('node', [join(HERE, 'sfx.mjs'), '--page', HTML, '--hook', h.id, '--cta', c.id, '--bed', music, '--bed-db', String(musicDb), '--fps', String(fps), '--out', sfx], { quiet: true });
    audioFor[`${h.id}_${c.id}`] = sfx;
  }
  const results = [];
  for (const fmt of formats) {
    const mid = seg(fmt, 'mid', H.end, K.start, hooks[0].id, ctas[0].id);
    const hs = Object.fromEntries(hooks.map((h) => [h.id, seg(fmt, `hook-${h.id}`, 0, H.end, h.id, ctas[0].id)]));
    const cs = Object.fromEntries(ctas.map((c) => [c.id, seg(fmt, `cta-${c.id}`, K.start, DUR, hooks[0].id, c.id)]));
    const dir = join(OUT, 'campaign', fmt); mkdirSync(dir, { recursive: true });
    for (const h of hooks) for (const c of ctas) {
      const base = `${C.project}_${fmt}_${h.id}_${c.id}`, silent = join(dir, `.${base}_silent.mp4`), final = join(dir, `${base}.mp4`);
      const list = join(dir, `.${base}.txt`); writeFileSync(list, [hs[h.id], mid, cs[c.id]].map((f) => `file '${f}'`).join('\n') + '\n');
      sh('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', silent]);
      sh('bash', [join(HERE, 'mix.sh'), silent, final, '--music', music, '--sfx', audioFor[`${h.id}_${c.id}`], '--music-db', String(musicDb)], { quiet: true });
      sh('ffmpeg', ['-v', 'error', '-y', '-ss', String(Math.min(DUR - 0.1, (H.end + K.start) / 2)), '-i', final, '-frames:v', '1', '-q:v', '3', join(dir, `${base}.jpg`)]);
      results.push({ fmt, hook: h.id, cta: c.id, file: final });
      console.log(`✔ ${relative(ROOT, final)}`);
    }
    // QA visual do formato (1ª variante) + auditoria de áudio da 1ª variante
    const first = join(dir, `${C.project}_${fmt}_${hooks[0].id}_${ctas[0].id}.mp4`);
    sh('bash', [join(HERE, 'qa.sh'), first], { quiet: true, allowFail: true });
  }
  const f0 = results[0].file;
  sh('python3', [join(HERE, 'audit-audio.py'), f0, '--sfx', audioFor[`${hooks[0].id}_${ctas[0].id}`], '--music', music, '--music-db', String(musicDb)], { quiet: true, allowFail: true });
  const total = results.length * DUR;
  console.log(`\n✔ ${results.length} vídeos (${formats.length} formatos × ${hooks.length} ganchos × ${ctas.length} CTAs) · ${renderedSec ? `renderizados ${renderedSec.toFixed(1)}s de vídeo para entregar ${total}s (${(total / renderedSec).toFixed(1)}× mais barato)` : `imagem 100% do cache (só concatenação e mix)`} · ${cached} segmento(s) do cache · ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  writeFileSync(join(OUT, 'campaign', 'render.json'), JSON.stringify({ settings, codeKey, results: results.map((r) => ({ ...r, file: relative(ROOT, r.file) })), draft: DRAFT, date: new Date().toISOString() }, null, 1));
}

// ═════════════════════════════════════ PACKAGE ═════════════════════════════════════
async function pack() {
  const rj = join(OUT, 'campaign', 'render.json'); if (!existsSync(rj)) { console.error('✗ rode render antes'); process.exit(1); }
  const R = JSON.parse(readFileSync(rj, 'utf8')), date = new Date().toISOString().slice(0, 10);
  const dest = join(OUT, 'delivery', `${C.project}_${date}${R.draft ? '_RASCUNHO' : ''}`); mkdirSync(dest, { recursive: true });
  const probe = (f) => { const r = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate:format=duration', '-of', 'json', f], { encoding: 'utf8' }); return JSON.parse(r.stdout); };
  const lufs = (f) => { const r = spawnSync('ffmpeg', ['-hide_banner', '-i', f, '-af', 'ebur128', '-f', 'null', '-'], { encoding: 'utf8' }).stderr; const m = r.match(/^\s+I:\s+(-?[\d.]+) LUFS/m); return m ? +m[1] : null; };
  const files = [];
  for (const r of R.results) {
    const src = join(ROOT, r.file), d = join(dest, r.fmt); mkdirSync(d, { recursive: true });
    const to = join(d, basename(src)); copyFileSync(src, to); copyFileSync(src.replace(/\.mp4$/, '.jpg'), to.replace(/\.mp4$/, '_capa.jpg'));
    const p = probe(to), v = p.streams.find((s) => s.width);
    files.push({ path: relative(dest, to), sha256: fileSha(to), bytes: statSync(to).size, duration: +(+p.format.duration).toFixed(3), width: v.width, height: v.height, fps: v.r_frame_rate, format: r.fmt, hook: r.hook, cta: r.cta, lufs: lufs(to) });
  }
  for (const f of ['campaign.json', 'out/validate.md']) if (existsSync(join(ROOT, f))) copyFileSync(join(ROOT, f), join(dest, basename(f)));
  // relatórios de QA por formato (qa.sh e audit-audio.py escrevem ao lado do vídeo, em out/campaign/<fmt>/qa/)
  for (const fm of [...new Set(R.results.map((r) => r.fmt))]) {
    const qd = join(OUT, 'campaign', fm, 'qa'); if (!existsSync(qd)) continue;
    const to = join(dest, 'qa', fm); mkdirSync(to, { recursive: true });
    for (const f of ['contact.png', 'phone.png', 'qa.md', 'audio.md']) if (existsSync(join(qd, f))) copyFileSync(join(qd, f), join(to, f));
  }
  const ff = spawnSync('ffmpeg', ['-version'], { encoding: 'utf8' }).stdout.split('\n')[0];
  const manifest = { project: C.project, template: C.template, generated: new Date().toISOString(), draft: R.draft, campaignSha256: fileSha(join(ROOT, 'campaign.json')),
    templateSha256: sha(fileSha(HTML) + fileSha(join(ROOT, 'lib/motion.js'))), render: R.settings, tools: { node: process.version, ffmpeg: ff }, approval: C.approval, claims: C.claims, files };
  writeFileSync(join(dest, 'manifest.json'), JSON.stringify(manifest, null, 1));
  const use = { '9x16': 'Reels, TikTok, Shorts, Stories', '1x1': 'feed (Instagram, LinkedIn, Facebook)', '16x9': 'YouTube, site, apresentações, X', '4x5': 'feed do Instagram/Facebook' };
  const byFmt = [...new Set(files.map((f) => f.format))];
  const readme = `# ${C.brand.name} — ${C.project}\n\nEntrega de ${date}${R.draft ? ' · **RASCUNHO interno, não enviar ao cliente**' : ''}\n\n` +
    `${files.length} vídeos de ${C.duration}s: ${byFmt.length} formato(s) × ${C.hooks.length} abertura(s) × ${C.ctas.length} chamada(s) para ação.\n\n` +
    `## Aberturas\n${C.hooks.map((h) => `- **${h.id}**: "${h.lines.join(' ')}"`).join('\n')}\n\n## Chamadas para ação\n${C.ctas.map((c) => `- **${c.id}**: "${c.text}"`).join('\n')}\n\n` +
    byFmt.map((fm) => `## ${fm} — ${use[fm] || ''}\n${files.filter((f) => f.format === fm).map((f) => `- \`${f.path}\` · abertura ${f.hook} · CTA ${f.cta} · ${f.width}×${f.height} · ${f.lufs} LUFS`).join('\n')}`).join('\n\n') +
    `\n\n## Especificações\n- Vídeo H.264 (yuv420p, faststart), áudio AAC 48 kHz, loudness −14 LUFS, pico ≤ −1 dBTP\n- Cada vídeo tem uma capa (\`_capa.jpg\`)\n- Números exibidos vêm dos dados aprovados (ver \`manifest.json\` → claims)\n- \`manifest.json\` traz o hash de cada arquivo para conferência\n`;
  writeFileSync(join(dest, 'LEIA-ME.md'), readme);
  const zip = dest + '.zip';
  spawnSync('python3', ['-c', `import shutil;shutil.make_archive(${JSON.stringify(dest)},'zip',${JSON.stringify(dirname(dest))},${JSON.stringify(basename(dest))})`]);
  console.log(`✔ ${relative(ROOT, dest)}/ — ${files.length} vídeos + capas + manifest.json + LEIA-ME.md\n✔ ${relative(ROOT, zip)} (${(statSync(zip).size / 1e6).toFixed(1)} MB)`);
}

if (CMD === 'sync') console.log('✔ campaign.js sincronizado');
else if (CMD === 'validate') process.exit((await validate()) ? 0 : 1);
else if (CMD === 'render') await render();
else if (CMD === 'package') await pack();
else if (CMD === 'all') { await render(); await pack(); }
else { console.error('comandos: sync | validate | render | package | all'); process.exit(1); }
