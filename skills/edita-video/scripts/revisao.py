#!/usr/bin/env python3
"""revisao.py — a REVISÃO NO NAVEGADOR: uma página (Artifact) em que o cliente assiste a versão, vê a linha do tempo
com os mesmos números da edição (s003, br01, mo04, L012, sfx07), pede mudanças em 1 clique e aprova. Os pedidos
ficam no banco da página; o Claude lê e aplica (pedidos.py).

    python3 revisao.py <projeto> [--versao 3]
    → entregas/revisao_vNN/index.html + proxy.mp4 (720p, ≤ 14 MB)

Publicar (Claude): Artifact publish com file_path=index.html, files={"proxy.mp4": "<…>/proxy.mp4"},
capabilities={"db": {}, "user": {"scopes": ["profile"]}}, icon "video". Compartilhe com o cliente no nível
"Colaborador/Contributor" (quem só vê não grava pedido). Ler pedidos: ArtifactData list collection "pedidos"
→ salve em _edit/pedidos.json → python3 pedidos.py <projeto> → marque cada pedido como aplicado (update status).
"""
import sys, os, re, json, subprocess, html
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P)
est = E.jload(P / '_edit/estado.json', {}) or {}
ver = int(opt('versao', est.get('versao', 1) or 1))
nome = B.get('nome') or re.sub(r'[^a-z0-9-]+', '-', P.name.lower()).strip('-') or 'video'
tl = E.jload(P / '_edit/timeline.json'); mapa = E.jload(P / '_edit/mapa.json', {}) or {}
leg = E.jload(P / '_edit/legendas.json', {}) or {}; sfx = (E.jload(P / '_edit/eventos_sfx.json', {}) or {}).get('cues', [])
cortes = E.jload(P / '_edit/cortes.json', {}) or {}
rend = sorted((P / 'renders').glob(f'*_v{ver:02d}.mp4')) or E.die(f'não achei renders/*_v{ver:02d}.mp4 — rode final.py')
OUT = P / 'entregas' / f'revisao_v{ver:02d}'; OUT.mkdir(parents=True, exist_ok=True)
DUR = tl['duracao']; FPS = tl['fps']
# proxy leve para a página (≤ 14 MB): 720 de largura, taxa pela duração
kbps = max(700, min(3000, int(14 * 8 * 1000 / max(DUR, 1)) - 160))
E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(rend[-1]), '-vf', 'scale=720:-2', '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{kbps}k',
       '-maxrate', f'{int(kbps * 1.3)}k', '-bufsize', f'{kbps * 2}k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(OUT / 'proxy.mp4')])
W = {w['i']: w for w in tl['palavras']}
dados = {
    'nome': nome, 'versao': ver, 'dur': round(DUR, 3), 'fps': FPS, 'estilo': ESTILO,
    'trechos': [{'id': s['id'], 'a': s['seq_in'], 'b': s['seq_out'], 'txt': s.get('texto', '')[:140], 'p0': s['palavras'][0] if s['palavras'] else None,
                 'p1': s['palavras'][-1] if s['palavras'] else None} for s in tl['segmentos']],
    'itens': [{'id': it['id'], 'tipo': it['tipo'], 'modo': it.get('modo'), 'a': it['t_ini'], 'b': it['t_fim'],
               'txt': (it.get('texto') or (it.get('params') or {}).get('nome') or (it.get('params') or {}).get('palavra') or ' / '.join((it.get('params') or {}).get('itens', [])) or it.get('busca') or '')[:100],
               'peca': it.get('peca')} for it in mapa.get('itens', []) if it.get('t_ini') is not None],
    'legendas': [{'id': b['id'], 'a': b['t0'], 'b': b['t1'], 'txt': b['texto'], 'pal': b['palavras'], 'oculta': b.get('oculta', False)} for b in leg.get('blocos', [])],
    'sfx': [{'id': c['id'], 'a': c['t'], 'tipo': c['type'], 'origem': c['origem']} for c in sfx],
    'cortados': [{'de': r['de'], 'ate': r['ate'], 'txt': r['texto'][:120], 'motivo': r['motivo']} for r in cortes.get('removidos', [])],
}
TPL = r'''<title>Revisão __NOME__ v__VER__</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Sala de corte: monitor à esquerda, inspetor à direita, timeline de faixas embaixo (como num NLE), números da edição em tudo. */
:root{
  --bg:#F3F2EE; --surface:#FFFFFF; --ink:#17181B; --mute:#6B6B70; --line:#DEDCD5;
  --accent:#1F6F66; --accent-ink:#FFFFFF; --rec:#C2412D; --ok:#2E7D4F;
  --l-corte:#8A8F98; --l-cob:#C08A2E; --l-mo:#1F6F66; --l-leg:#5B5FC7; --l-sfx:#B5487A;
  --f-disp:"Bricolage Grotesque",ui-sans-serif,system-ui,sans-serif; --f-body:"Instrument Sans",ui-sans-serif,system-ui,sans-serif; --f-mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#121315;--surface:#1B1C1F;--ink:#ECEBE7;--mute:#9A9AA0;--line:#2C2D31;--accent:#4FB3A6;--accent-ink:#0E1413;--rec:#E0664F;--ok:#5FBF86;--l-corte:#8E949E;--l-cob:#D9A447;--l-mo:#4FB3A6;--l-leg:#8E92F0;--l-sfx:#E07AAB;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121315;--surface:#1B1C1F;--ink:#ECEBE7;--mute:#9A9AA0;--line:#2C2D31;--accent:#4FB3A6;--accent-ink:#0E1413;--rec:#E0664F;--ok:#5FBF86;--l-corte:#8E949E;--l-cob:#D9A447;--l-mo:#4FB3A6;--l-leg:#8E92F0;--l-sfx:#E07AAB;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:15px/1.5 var(--f-body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 40px}
.wrap{max-width:1180px;margin:0 auto;display:grid;gap:18px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 16px}
h1{font:800 clamp(22px,3.4vw,32px)/1.1 var(--f-disp);margin:0;letter-spacing:-.01em;text-wrap:balance}
.meta{color:var(--mute);font-size:13px}
.tc{font:500 13px var(--f-mono);font-variant-numeric:tabular-nums}
.top{display:grid;grid-template-columns:minmax(0,360px) minmax(0,1fr);gap:18px;align-items:start}
@media (max-width:760px){.top{grid-template-columns:minmax(0,1fr)}}
.monitor{background:#000;border-radius:10px;overflow:hidden;max-width:100%}
.monitor video{display:block;width:100%;max-height:70vh;aspect-ratio:9/16;background:#000}
.bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 2px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px;display:grid;gap:12px;min-width:0}
.panel h2{font:600 18px/1.2 var(--f-disp);margin:0}
.chip{display:inline-flex;align-items:center;gap:6px;font:500 12px var(--f-mono);padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--mute)}
.chip i{width:8px;height:8px;border-radius:50%;display:inline-block}
.row{display:flex;flex-wrap:wrap;gap:8px}
button{font:600 14px var(--f-body);border-radius:8px;border:1px solid var(--line);background:var(--surface);color:var(--ink);padding:8px 12px;cursor:pointer}
button:hover{border-color:var(--accent)}
button:focus-visible,textarea:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
button.warn{color:var(--rec)}
button:disabled{opacity:.5;cursor:not-allowed}
textarea,input[type=text]{width:100%;font:15px var(--f-body);color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
textarea{min-height:76px;resize:vertical}
.hint{color:var(--mute);font-size:13px}
.tlbox{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 0 12px 12px;overflow-x:auto}
.tl{position:relative;min-width:760px;padding-right:12px}
.lane{display:grid;grid-template-columns:96px 1fr;align-items:center;height:30px}
.lane .lab{font:500 12px var(--f-mono);color:var(--mute);letter-spacing:.04em;text-transform:uppercase}
.track{position:relative;height:22px;border-radius:4px;background:color-mix(in srgb,var(--line) 45%,transparent)}
.blk{position:absolute;top:2px;bottom:2px;border-radius:3px;font:500 10px/18px var(--f-mono);color:var(--accent-ink);padding:0 4px;overflow:hidden;white-space:nowrap;cursor:pointer;border:0}
.blk.sel{outline:2px solid var(--ink);outline-offset:1px;z-index:2}
.blk.sfx{width:6px!important;padding:0;border-radius:2px}
.ruler{display:grid;grid-template-columns:96px 1fr;height:18px}
.ruler .ticks{position:relative;font:500 10px var(--f-mono);color:var(--mute)}
.ruler .ticks span{position:absolute;transform:translateX(-50%)}
.playhead{position:absolute;top:0;bottom:0;width:2px;background:var(--rec);pointer-events:none;left:96px}
.list{display:grid;gap:8px}
.ped{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:start;padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
.ped .what{min-width:0}
.ped .what b{font-family:var(--f-mono);font-size:13px}
.st{font:500 12px var(--f-mono);padding:2px 8px;border-radius:999px}
.st.novo{background:color-mix(in srgb,var(--rec) 15%,transparent);color:var(--rec)}
.st.aplicado{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}
.note{font-size:13px;color:var(--mute)}
section h3{font:600 15px var(--f-disp);margin:0 0 8px}
.cut{display:flex;gap:10px;align-items:baseline;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--line)}
.cut:last-child{border-bottom:0}
.cut span{min-width:0}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style>
<div class="wrap">
  <header>
    <h1>Revisão · __NOME__ <span style="color:var(--accent)">v__VER__</span></h1>
    <div class="meta"><span class="tc" id="durlab"></span> · estilo __ESTILO__ · peça mudanças pelo número</div>
  </header>
  <div class="top">
    <div>
      <div class="monitor"><video id="v" src="proxy.mp4" controls playsinline preload="metadata"></video></div>
      <div class="bar"><span class="tc" id="tcnow">00:00:00:00</span><span class="hint">Clique em qualquer bloco da linha do tempo</span></div>
    </div>
    <div class="panel" id="insp" aria-live="polite">
      <h2 id="i-tit">Selecione um bloco</h2>
      <div class="hint" id="i-sub">Cada bloco tem o número que a edição usa: s003 é um trecho, br01 uma imagem de apoio, mo04 uma animação, L012 uma legenda, sfx07 um efeito sonoro.</div>
      <div id="i-acoes" class="row"></div>
      <div id="i-leg" hidden><label class="hint" for="leg-txt">Texto da legenda (só corrige a escrita, o tempo continua igual)</label><input type="text" id="leg-txt"><div class="row" style="margin-top:8px"><button id="leg-ok">Corrigir legenda</button></div></div>
      <label class="hint" for="coment">Pedido livre sobre este ponto</label>
      <textarea id="coment" placeholder="Ex.: entra meio segundo antes · troca a imagem por uma de consultório · essa palavra merece destaque"></textarea>
      <div class="row"><button class="primary" id="enviar">Enviar pedido</button><span class="note" id="status"></span></div>
    </div>
  </div>
  <div class="tlbox"><div class="tl" id="tl"></div></div>
  <section>
    <h3>O que foi cortado do bruto</h3>
    <div class="hint" style="margin-bottom:6px">Hesitações, falsos começos e repetições saíram. Algo que devia ter ficado? Peça de volta.</div>
    <div id="cortados"></div>
  </section>
  <section>
    <h3>Pedidos</h3>
    <div class="row" style="margin-bottom:10px"><button class="primary" id="aprovar">Aprovar esta versão</button><span class="note" id="db-note">Conectando aos pedidos…</span></div>
    <div class="list" id="peds"><div class="note">Nenhum pedido ainda. Assista, clique num bloco e peça o que quiser mudar.</div></div>
  </section>
</div>
<script>
const D = __DADOS__;
const $ = (s) => document.querySelector(s);
const v = $('#v'), tlEl = $('#tl');
const tc = (t) => { const f = Math.round(t * D.fps); const fr = f % Math.round(D.fps), s = Math.floor(f / Math.round(D.fps)); return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60, fr].map((x) => String(x).padStart(2, '0')).join(':'); };
$('#durlab').textContent = tc(D.dur);
const LANES = [
  ['Cortes', 'corte', '--l-corte', D.trechos.map((x) => ({ ...x, k: 'corte' }))],
  ['Cobertura', 'cob', '--l-cob', D.itens.filter((x) => x.tipo !== 'motion' && x.tipo !== 'texto').map((x) => ({ ...x, k: 'item' }))],
  ['Motion', 'mo', '--l-mo', D.itens.filter((x) => x.tipo === 'motion' || x.tipo === 'texto').map((x) => ({ ...x, k: 'item' }))],
  ['Legendas', 'leg', '--l-leg', D.legendas.filter((x) => !x.oculta).map((x) => ({ ...x, k: 'leg' }))],
  ['Som', 'sfx', '--l-sfx', D.sfx.map((x) => ({ ...x, b: x.a + 0.2, k: 'sfx' }))],
];
const pct = (t) => (100 * t / D.dur);
const ruler = document.createElement('div'); ruler.className = 'ruler'; ruler.innerHTML = '<span></span><div class="ticks"></div>';
const step = D.dur > 60 ? 10 : D.dur > 20 ? 5 : 2;
for (let t = 0; t <= D.dur; t += step) { const s = document.createElement('span'); s.style.left = pct(t) + '%'; s.textContent = t + 's'; ruler.querySelector('.ticks').appendChild(s); }
tlEl.appendChild(ruler);
const blocks = [];
for (const [lab, cls, cor, arr] of LANES) {
  const lane = document.createElement('div'); lane.className = 'lane';
  const l = document.createElement('div'); l.className = 'lab'; l.textContent = lab; lane.appendChild(l);
  const tr = document.createElement('div'); tr.className = 'track';
  for (const x of arr) {
    const b = document.createElement('button'); b.className = 'blk' + (cls === 'sfx' ? ' sfx' : ''); b.type = 'button';
    b.style.left = pct(x.a) + '%'; b.style.width = Math.max(0.6, pct(x.b - x.a)) + '%'; b.style.background = `var(${cor})`;
    b.textContent = cls === 'sfx' ? '' : x.id; b.title = `${x.id} · ${tc(x.a)} · ${x.txt || x.tipo || ''}`;
    b.setAttribute('aria-label', b.title);
    b.addEventListener('click', () => selecionar(x, b)); tr.appendChild(b); blocks.push(b);
  }
  lane.appendChild(tr); tlEl.appendChild(lane);
}
const ph = document.createElement('div'); ph.className = 'playhead'; tlEl.appendChild(ph);
function moveHead() { const tr = tlEl.querySelector('.track'); if (!tr) return; const w = tr.getBoundingClientRect().width; ph.style.left = (96 + w * (v.currentTime / D.dur)) + 'px'; $('#tcnow').textContent = tc(v.currentTime); }
v.addEventListener('timeupdate', moveHead); window.addEventListener('resize', moveHead);
tlEl.querySelectorAll('.track').forEach((tr) => tr.addEventListener('click', (e) => { if (e.target !== tr) return; const r = tr.getBoundingClientRect(); v.currentTime = D.dur * (e.clientX - r.left) / r.width; }));

let sel = null;
function botao(txt, fn, cls) { const b = document.createElement('button'); b.type = 'button'; b.textContent = txt; if (cls) b.className = cls; b.addEventListener('click', fn); return b; }
function selecionar(x, el) {
  sel = x; blocks.forEach((b) => b.classList.remove('sel')); if (el) el.classList.add('sel');
  v.currentTime = Math.max(0, x.a - 0.3);
  const nomes = { corte: 'Trecho', item: x.tipo === 'motion' ? 'Animação' : 'Imagem de apoio', leg: 'Legenda', sfx: 'Efeito sonoro' };
  $('#i-tit').textContent = `${x.id} · ${nomes[x.k]}`;
  $('#i-sub').textContent = `${tc(x.a)}${x.b ? ' → ' + tc(x.b) : ''} · ${x.txt || x.tipo || ''}${x.origem ? ' · nasce de ' + x.origem : ''}`;
  const ac = $('#i-acoes'); ac.replaceChildren();
  $('#i-leg').hidden = x.k !== 'leg'; if (x.k === 'leg') $('#leg-txt').value = x.txt;
  if (x.k === 'sfx') { ac.append(botao('Mais baixo (−3 dB)', () => pedir({ tipo: 'sfx', alvo: x.id, valor: '-3' })), botao('Mais alto (+3 dB)', () => pedir({ tipo: 'sfx', alvo: x.id, valor: '+3' })), botao('Tirar este som', () => pedir({ tipo: 'sfx', alvo: x.id, valor: 'off' }), 'warn')); }
  if (x.k === 'item') { ac.append(botao('Entrar 0,5 s antes', () => pedir({ tipo: 'item', alvo: x.id, acao: 'antes' })), botao('Entrar 0,5 s depois', () => pedir({ tipo: 'item', alvo: x.id, acao: 'depois' })), botao('Tirar', () => pedir({ tipo: 'item', alvo: x.id, acao: 'remover' }), 'warn')); }
  if (x.k === 'corte') { ac.append(botao('Tirar este trecho', () => pedir({ tipo: 'corte', alvo: x.id, acao: 'remover', de: x.p0, ate: x.p1 }), 'warn')); }
}
$('#leg-ok').addEventListener('click', () => { if (sel && sel.k === 'leg') { const t = $('#leg-txt').value.trim(); if (t && t !== sel.txt) pedir({ tipo: 'legenda', alvo: sel.id, palavras: sel.pal, texto: t }); } });
$('#enviar').addEventListener('click', () => { const t = $('#coment').value.trim(); if (!t) { $('#status').textContent = 'Escreva o pedido antes de enviar.'; return; } pedir({ tipo: 'comentario', alvo: sel ? sel.id : 'geral', em: sel ? sel.a : v.currentTime, texto: t }).then((ok) => { if (ok) $('#coment').value = ''; }); });
$('#aprovar').addEventListener('click', () => pedir({ tipo: 'aprovacao', alvo: 'v' + D.versao }));

const cortEl = $('#cortados');
if (!D.cortados.length) cortEl.innerHTML = '<div class="note">Nada foi cortado além das pausas.</div>';
for (const c of D.cortados) { const r = document.createElement('div'); r.className = 'cut'; const s = document.createElement('span'); s.textContent = `#${c.de}–#${c.ate} · ${c.motivo}: “${c.txt}”`; r.append(s, botao('Voltar com isso', () => pedir({ tipo: 'corte', alvo: `#${c.de}-${c.ate}`, acao: 'manter', de: c.de, ate: c.ate }))); cortEl.appendChild(r); }

// ── pedidos no banco da página ──
let db = null, user = null, me = null; const pend = [];
const ROT = { sfx: 'Som', item: 'Item', corte: 'Corte', legenda: 'Legenda', comentario: 'Pedido', aprovacao: 'Aprovação' };
function descreve(p) {
  if (p.tipo === 'sfx') return p.valor === 'off' ? 'tirar o som' : `volume ${p.valor} dB`;
  if (p.tipo === 'item') return { antes: 'entrar 0,5 s antes', depois: 'entrar 0,5 s depois', remover: 'tirar' }[p.acao] || p.acao;
  if (p.tipo === 'corte') return p.acao === 'manter' ? 'voltar com o trecho cortado' : 'tirar o trecho';
  if (p.tipo === 'legenda') return `escrever “${p.texto}”`;
  if (p.tipo === 'aprovacao') return 'aprovou a versão';
  return p.texto || '';
}
async function pedir(p) {
  const corpo = { ...p, versao: D.versao, status: 'novo', criado: new Date().toISOString(), autor: me };
  if (!db) { $('#status').textContent = 'Os pedidos não estão conectados nesta visualização. Abra o link no claude.ai com sua conta.'; return false; }
  try { await db.collection('pedidos').add(corpo); $('#status').textContent = `Pedido enviado: ${p.alvo} · ${descreve(p)}`; return true; }
  catch (e) { $('#status').textContent = e && e.code === 'not_granted' ? 'Sua conta só pode assistir. Peça acesso de colaborador para enviar pedidos.' : 'Não deu para enviar agora. Tente de novo em instantes.'; return false; }
}
async function render(docs) {
  const el = $('#peds'); el.replaceChildren();
  if (!docs.length) { el.innerHTML = '<div class="note">Nenhum pedido ainda. Assista, clique num bloco e peça o que quiser mudar.</div>'; return; }
  const ids = [...new Set(docs.map((d) => d.autor).filter(Boolean))]; let perf = {};
  try { perf = user && ids.length ? await user.profiles(ids) : {}; } catch (e) { perf = {}; }
  for (const p of docs) {
    const r = document.createElement('div'); r.className = 'ped';
    const tag = document.createElement('span'); tag.className = 'chip'; tag.textContent = ROT[p.tipo] || p.tipo;
    const w = document.createElement('div'); w.className = 'what'; const b = document.createElement('b'); b.textContent = p.alvo + ' '; const s = document.createElement('span'); s.textContent = descreve(p);
    const n = document.createElement('div'); n.className = 'note'; n.textContent = `${(perf[p.autor] && perf[p.autor].name) || 'Alguém'} · v${p.versao} · ${new Date(p.criado).toLocaleString('pt-BR')}`;
    w.append(b, s, n); const st = document.createElement('span'); st.className = 'st ' + (p.status === 'aplicado' ? 'aplicado' : 'novo'); st.textContent = p.status === 'aplicado' ? 'aplicado' : 'novo';
    r.append(tag, w, st); el.appendChild(r);
  }
}
(async () => {
  if (!window.claude || !window.claude.use) { $('#db-note').textContent = 'Abra pelo link do claude.ai para enviar pedidos.'; return; }
  db = await window.claude.use('db'); user = await window.claude.use('user');
  if (!db) { $('#db-note').textContent = 'Pedidos indisponíveis aqui (entre com sua conta no claude.ai).'; return; }
  try { me = user ? await user.id() : null; } catch (e) { me = null; }
  const tm = setTimeout(() => { $('#db-note').textContent = 'Os pedidos ainda não carregaram; o que você enviar fica guardado.'; }, 10000);
  db.collection('pedidos').orderBy('criado', 'desc').onSnapshot((snap) => {
    if (!snap.metadata || !snap.metadata.fromCache) { clearTimeout(tm); $('#db-note').textContent = `${snap.docs.length} pedido(s)`; }
    render(snap.docs.map((d) => ({ id: d.id, ...d.data() })));
  }, () => { clearTimeout(tm); $('#db-note').textContent = 'Não deu para carregar os pedidos agora.'; });
})();
</script>
'''
out = TPL.replace('__NOME__', html.escape(nome)).replace('__VER__', f'{ver:02d}').replace('__ESTILO__', html.escape(ESTILO)).replace('__DADOS__', json.dumps(dados, ensure_ascii=False).replace('</', '<\\/'))
(OUT / 'index.html').write_text(out, encoding='utf-8')
mb = (OUT / 'proxy.mp4').stat().st_size / 1e6
print(f'✔ {OUT.relative_to(P)}/index.html + proxy.mp4 ({mb:.1f} MB)')
print('→ publique: Artifact file_path=index.html, files={"proxy.mp4": "<pasta>/proxy.mp4"}, capabilities={"db": {}, "user": {"scopes": ["profile"]}}, icon="video"')
print('→ compartilhe com o cliente como Colaborador; leia os pedidos (ArtifactData list "pedidos") → _edit/pedidos.json → pedidos.py')
