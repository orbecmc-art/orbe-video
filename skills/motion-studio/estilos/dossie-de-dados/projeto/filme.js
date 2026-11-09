/* A CONTA — quantas vezes você ainda vai ver a sua mãe?
 *
 * Todo quadro é função pura do tempo: window.seek(t) pinta o instante t.
 * O relógio é a narração (narracao.js): cada entrada nasce na palavra que a voz diz.
 * Os números moram em CONTA e são conferidos em window.CHECKS.
 */
const Q = new URLSearchParams(location.search);
if (Q.has('render') || navigator.webdriver) document.body.classList.add('render');
const N = window.NARRACAO, D = window.DIAS;
const W = 1080, H = 1920, FPS = 30, DURATION = N.dur;
Object.assign(window, { DURATION, FPS });
const c = document.getElementById('c'); c.width = W; c.height = H;
const g = c.getContext('2d', { willReadFrequently: true });
const { clamp, lerp, EASE: E } = M;
const qd = (n) => n / FPS;   // duração em quadros

// A conta do filme: cada número vem daqui.
const CONTA = {
  anosAMais: 24,          // IBGE, Tábuas 2024, Tabela 3: mulher aos 60 anos, 24,2 anos a mais, ou seja, até os 84
  visitasPorAno: 2,
  visitasLonge: 48,       // 2 x 24
  visitasMes: 288,        // 12 x 24
  ateSair: 5913,          // 18 anos x 365 dias x 90% dos dias
  jaFeitas: 168,          // dos 18 aos 32 anos, uma visita por mês
  total: 6369,            // 5913 + 168 + 288
  pct18: 93,              // 5913 / 6369 = 92,8%
  horasPorSemana: 53.5,   // We Are Social/Meltwater, Digital 2026 Brasil
  diasInternet: 116,      // 53,5 x 52,14 / 24
};

// ── relógio da voz ──
const FAL = Object.fromEntries(N.falas.map((f) => [f.id, f]));
const P = (id, i = 0) => FAL[id].palavras[i].t0;
const PF = (id, i) => FAL[id].palavras[i ?? FAL[id].palavras.length - 1].t1;

// ── fontes e imagens ──
const F_UI = '"Inter Tight"', F_SER = '"Instrument Serif"', F_MAO = 'Caveat', F_BLACK = '"Archivo Black"';
const IMG = {};
const carrega = (nome, src) => new Promise((ok, erro) => { const i = new Image(); i.onload = () => { IMG[nome] = i; ok(); }; i.onerror = () => erro(new Error('falta ' + src)); i.src = src; });
const CLIPES = { mae: 84, cozinha: 72, campo: 72, janela: 84, espera: 84, maos: 72 };
const QUADROS = {};
window.ready = Promise.all([
  ...[`800 60px ${F_UI}`, `900 60px ${F_UI}`, `700 60px ${F_UI}`, `600 60px ${F_UI}`, `italic 400 60px ${F_SER}`, `400 60px ${F_SER}`, `700 60px ${F_MAO}`, `400 60px ${F_BLACK}`].map((f) => document.fonts.load(f, 'aãçé0')),
  ...['kraft', 'papel', 'ardosia', 'madeira', 'rosto', 'mergulho', 'persiana', 'folha-fotos'].map((n) => carrega(n, `assets/${n}.jpg`)),
  ...Object.entries(CLIPES).flatMap(([nome, n]) => {
    QUADROS[nome] = [];
    return Array.from({ length: n }, (_, i) => new Promise((ok) => {
      const im = new Image(); im.onload = ok; im.onerror = ok; im.src = `assets/clipes/${nome}/${String(i + 1).padStart(3, '0')}.jpg`; QUADROS[nome][i] = im;
    }));
  }),
]).then(() => { prepararSprites(); });

// Vídeo em 12 quadros por segundo, indo e voltando: nunca dá salto na emenda.
function quadro(nome, t) {
  const q = QUADROS[nome], n = q.length, f = Math.floor(Math.max(0, t) * 12) % (2 * n - 2);
  return q[f < n ? f : 2 * n - 2 - f];
}

// ── utilidades de desenho ──
function cobre(img, x, y, w, h, fx = 0.5, fy = 0.5) {
  const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height, s = Math.max(w / iw, h / ih), sw = w / s, sh = h / s;
  g.drawImage(img, (iw - sw) * fx, (ih - sh) * fy, sw, sh, x, y, w, h);
}
const novoCanvas = (w, h) => { const cv = document.createElement('canvas'); cv.width = Math.ceil(w); cv.height = Math.ceil(h); return cv; };

let GRAO = null;
function grao() {
  if (GRAO) return GRAO;
  GRAO = novoCanvas(180, 180); const x = GRAO.getContext('2d'), id = x.createImageData(180, 180), r = M.rng(77);
  for (let i = 0; i < id.data.length; i += 4) { const v = 150 + r() * 105; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  x.putImageData(id, 0, 0); return GRAO;
}

// Borda de papel rasgado: ondulação lenta mais dente fino.
function rasgado(w, h, seed, amp, passo = 13) {
  const r = M.rng(seed), pts = [], j = (k = 1) => (r() - 0.5) * 2 * amp * k, baixa = (v, k) => M.noise1(v * 0.013 + k) * amp * 1.7;
  for (let x = 0; x < w; x += passo * (0.5 + r())) pts.push([x, baixa(x, seed) + j(0.6)]);
  for (let y = 0; y < h; y += passo * (0.4 + r() * 0.7)) pts.push([w + baixa(y, seed + 9) + j(1.1), y]);
  for (let x = w; x > 0; x -= passo * (0.5 + r())) pts.push([x, h + baixa(x, seed + 21) + j(0.6)]);
  for (let y = h; y > 0; y -= passo * (0.4 + r() * 0.7)) pts.push([baixa(y, seed + 33) + j(1.1), y]);
  return pts;
}
function caminho(x, pts) { x.beginPath(); pts.forEach(([a, b], i) => (i ? x.lineTo(a, b) : x.moveTo(a, b))); x.closePath(); }

// Rótulos: papel rasgado com tinta, como na gramática do dossiê.
const ESTILO = {
  ama: { papel: '#f0ca35', borda: '#fbf0c0', tinta: '#17140b', peso: 800, fam: F_UI, cx: 0.42, cy: 0.20, caixa: true },
  num: { papel: '#f0ca35', borda: '#fbf0c0', tinta: '#17140b', peso: 900, fam: F_UI, cx: 0.30, cy: 0.06, caixa: true, trk: -0.03 },
  pre: { papel: '#121210', borda: '#3a3936', tinta: '#f5f2e8', peso: 800, fam: F_UI, cx: 0.40, cy: 0.22, caixa: true },
  ser: { papel: '#efe9dc', borda: '#fffaf0', tinta: '#1b1a17', peso: 400, fam: F_SER, cx: 0.42, cy: 0.20, it: true },
};
const CACHE = new Map();
function rotulo(txt, tipo, px, seed = 1) {
  const chave = `${tipo}|${txt}|${px}|${seed}`;
  if (CACHE.has(chave)) return CACHE.get(chave);
  const e = ESTILO[tipo], fonte = `${e.it ? 'italic ' : ''}${e.peso} ${px}px ${e.fam}`, m0 = novoCanvas(4, 4).getContext('2d');
  m0.font = fonte; if (e.trk) m0.letterSpacing = `${e.trk * px}px`;
  const t = e.caixa ? txt.toUpperCase() : txt, tw = m0.measureText(t).width;
  const w = Math.round(tw + px * e.cx * 2), h = Math.round(px * (e.it ? 1.18 : 1.0) + px * e.cy * 2), amp = Math.max(2.2, px * 0.045), m = 34, ES = 2;
  const cv = novoCanvas((w + 2 * m) * ES, (h + 2 * m) * ES), x = cv.getContext('2d');
  x.scale(ES, ES); x.translate(m, m);
  const pts = rasgado(w, h, seed * 17 + txt.length, amp);
  x.save(); x.shadowColor = 'rgba(0,0,0,.42)'; x.shadowBlur = 16; x.shadowOffsetY = 7; x.fillStyle = e.borda; caminho(x, pts); x.fill(); x.restore();
  const interno = pts.map(([a, b]) => [lerp(a, w / 2, 3 / w) + (M.hash1(a + b) - 0.5) * 1.5, lerp(b, h / 2, 3.4 / h)]);
  x.fillStyle = e.papel; caminho(x, interno); x.fill();
  x.save(); caminho(x, interno); x.clip(); x.globalCompositeOperation = 'multiply'; x.globalAlpha = tipo === 'pre' ? 0.5 : 0.22; x.fillStyle = x.createPattern(grao(), 'repeat'); x.fillRect(-m, -m, w + 2 * m, h + 2 * m); x.restore();
  x.font = fonte; if (e.trk) x.letterSpacing = `${e.trk * px}px`; x.fillStyle = e.tinta; x.textAlign = 'left'; x.textBaseline = 'alphabetic';
  x.fillText(t, px * e.cx, h / 2 + px * (e.it ? 0.27 : 0.355));
  const s = { cv, w, h, m };
  CACHE.set(chave, s); return s;
}

// Entradas. Rótulo amarelo bate na mesa, tarja preta risca, serifa entra em foco.
function bate(t, t0, dur = qd(5)) {
  const d = t - t0; if (d < 0) return null;
  const p = clamp(d / dur), ei = p * p * p;
  let s = 1.36 - 0.36 * ei;
  if (p >= 1) { const q = d - dur; s = 1 - 0.024 * Math.exp(-9 * q) * Math.cos(21 * q); }
  return { s, a: clamp(d / qd(2)), r: (1 - ei) * 0.05, blur: (1 - ei) * 3 };
}
function risca(t, t0) { const d = t - t0; if (d < 0) return null; return { clipX: E.enter(clamp(d / qd(7))), a: 1, dx: (1 - E.enter(clamp(d / qd(9)))) * -26 }; }
function foca(t, t0) { const d = t - t0; if (d < 0) return null; const p = clamp(d / qd(13)); return { a: E.premium(clamp(d / qd(5))), blur: (1 - E.premium(p)) * 15, s: 1.02 - 0.02 * E.premium(p) }; }
function poe(sp, x, y, o, rot = 0) {
  if (!o) return;
  g.save(); g.translate(x + (o.dx || 0), y + (o.dy || 0)); g.rotate(rot + (o.r || 0)); g.scale(o.s || 1, o.s || 1); g.globalAlpha *= o.a ?? 1;
  if (o.blur > 0.3) g.filter = `blur(${o.blur.toFixed(2)}px)`;
  if (o.clipX !== undefined && o.clipX < 1) { g.beginPath(); g.rect(-sp.w / 2 - 34, -sp.h / 2 - 34, (sp.w + 68) * o.clipX, sp.h + 68); g.clip(); }
  g.drawImage(sp.cv, -sp.w / 2 - sp.m, -sp.h / 2 - sp.m, sp.w + 2 * sp.m, sp.h + 2 * sp.m);
  g.restore();
}
// Queda de um papel solto: fórmula fechada, sem estado.
function queda(t, t0, seed = 1) {
  const d = t - t0; if (d <= 0) return { dy: 0, dx: 0, r: 0 };
  return { dy: 0.5 * 2700 * d * d, dx: (M.hash1(seed) - 0.5) * 240 * d, r: (M.hash1(seed + 3) - 0.5) * 2.4 * d };
}
function junta(a, b) { if (!a) return null; const al = (a.a ?? 1) * (b.a ?? 1); if (al <= 0) return null; return { ...a, a: al, dy: (a.dy || 0) + (b.dy || 0), dx: (a.dx || 0) + (b.dx || 0), r: (a.r || 0) + (b.r || 0) }; }

// Polaroide: moldura com fita, foto (ou vídeo) dentro.
const MOLDURAS = new Map();
function moldura(w, h, seed) {
  const ch = `${w}|${h}|${seed}`; if (MOLDURAS.has(ch)) return MOLDURAS.get(ch);
  const m = 44, ES = 1.6, cv = novoCanvas((w + 2 * m) * ES, (h + 2 * m) * ES), x = cv.getContext('2d');
  x.scale(ES, ES); x.translate(m, m);
  const pts = rasgado(w, h, seed * 11, 1.6, 24);
  x.save(); x.shadowColor = 'rgba(0,0,0,.5)'; x.shadowBlur = 26; x.shadowOffsetY = 12; x.fillStyle = '#eee9dd'; caminho(x, pts); x.fill(); x.restore();
  x.save(); caminho(x, pts); x.clip(); x.globalCompositeOperation = 'multiply'; x.globalAlpha = 0.16; x.fillStyle = x.createPattern(grao(), 'repeat'); x.fillRect(0, 0, w, h); x.restore();
  const s = { cv, w, h, m, b: Math.round(w * 0.042) };
  MOLDURAS.set(ch, s); return s;
}
function fita(x, y, w, rot, seed) {
  const r = M.rng(seed), h = w * 0.3;
  g.save(); g.translate(x, y); g.rotate(rot); g.beginPath(); g.moveTo(-w / 2, -h / 2);
  for (let i = 0; i <= 6; i++) g.lineTo(-w / 2 + (w * i) / 6, -h / 2 + (r() - 0.5) * 2);
  for (let i = 0; i <= 5; i++) g.lineTo(w / 2 + (i % 2 ? 5 : -3), -h / 2 + (h * i) / 5);
  for (let i = 6; i >= 0; i--) g.lineTo(-w / 2 + (w * i) / 6, h / 2 + (r() - 0.5) * 2);
  for (let i = 5; i >= 0; i--) g.lineTo(-w / 2 + (i % 2 ? -5 : 3), -h / 2 + (h * i) / 5);
  g.closePath(); g.fillStyle = 'rgba(222,210,172,.72)'; g.fill(); g.restore();
}
function polaroide(x, y, w, h, rot, o, foto, seed = 1) {
  if (!o) return;
  const f = moldura(w, h, seed);
  g.save(); g.translate(x + (o.dx || 0), y + (o.dy || 0)); g.rotate(rot + (o.r || 0)); g.scale(o.s || 1, o.s || 1); g.globalAlpha *= o.a ?? 1;
  g.drawImage(f.cv, -w / 2 - f.m, -h / 2 - f.m, w + 2 * f.m, h + 2 * f.m);
  const b = f.b;
  g.save(); g.beginPath(); g.rect(-w / 2 + b, -h / 2 + b, w - 2 * b, h - 2 * b); g.clip();
  cobre(foto, -w / 2 + b, -h / 2 + b, w - 2 * b, h - 2 * b);
  const dentro = g.createLinearGradient(0, -h / 2, 0, h / 2); dentro.addColorStop(0, 'rgba(0,0,0,.20)'); dentro.addColorStop(0.08, 'rgba(0,0,0,0)'); dentro.addColorStop(0.92, 'rgba(0,0,0,0)'); dentro.addColorStop(1, 'rgba(0,0,0,.18)');
  g.fillStyle = dentro; g.fillRect(-w / 2, -h / 2, w, h); g.restore();
  fita(0, -h / 2 + 2, w * 0.34, -0.03 * seed, seed + 40);
  g.restore();
}

// Texto à mão: aparece da esquerda para a direita, como quem escreve.
function aMao(txt, x, y, px, t, t0, dur, cor = '#20304e', alinha = 'center') {
  const d = t - t0; if (d < 0) return;
  g.save(); g.font = `700 ${px}px ${F_MAO}`; const w = g.measureText(txt).width;
  const x0 = alinha === 'center' ? x - w / 2 : x;
  g.beginPath(); g.rect(x0 - 16, y - px, (w + 32) * clamp(d / dur), px * 1.5); g.clip();
  g.fillStyle = cor; g.textAlign = 'left'; g.fillText(txt, x0, y); g.restore();
}
// Traço de caneta vermelha: desenha o caminho aos poucos.
function caneta(pts, t, t0, dur, cor = '#c5202c', larg = 8) {
  const d = t - t0; if (d < 0) return;
  let tot = 0; for (let i = 1; i < pts.length; i++) tot += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  g.save(); g.strokeStyle = cor; g.lineWidth = larg; g.lineCap = 'round'; g.lineJoin = 'round';
  g.setLineDash([tot * clamp(d / dur), tot + 10]);
  g.beginPath(); pts.forEach(([a, b], i) => (i ? g.lineTo(a, b) : g.moveTo(a, b))); g.stroke(); g.restore();
}
function elipseMao(cx, cy, rx, ry, voltas = 1.18, seed = 3) {
  const pts = [], n = 90;
  for (let i = 0; i <= n; i++) {
    const a = -2.4 + (i / n) * voltas * Math.PI * 2, k = 1 + (i / n) * 0.09 + M.noise1(i * 0.09 + seed) * 0.03;
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return pts;
}

// ── sprites prontos ──
let QUAD_AMA = [], FUNDO_CHAMADA = null, TABELA = null, AVATAR = null, QUAD_AZUL = null, QUAD_APAGADO = null, QUAD_OURO = null;
function prepararSprites() {
  // quadradinho marcado com caneta-texto: três variações, para não parecer carimbo
  for (let k = 0; k < 4; k++) {
    const cv = novoCanvas(120, 120), x = cv.getContext('2d'), r = M.rng(900 + k);
    const pts = rasgado(96, 96, 300 + k, 2.4, 16).map(([a, b]) => [a + 12, b + 12]);
    x.fillStyle = '#f0ca35'; caminho(x, pts); x.fill();
    x.globalCompositeOperation = 'multiply'; x.globalAlpha = 0.28; x.fillStyle = x.createPattern(grao(), 'repeat'); x.fillRect(0, 0, 120, 120);
    x.globalCompositeOperation = 'source-over'; x.globalAlpha = 0.85; x.strokeStyle = '#2a2415'; x.lineWidth = 2.6; caminho(x, pts.map(([a, b]) => [a + (r() - 0.5) * 2, b + (r() - 0.5) * 2])); x.stroke();
    QUAD_AMA.push(cv);
  }
  // fundo da tela de chamada: o rosto dela, desfocado e escuro
  FUNDO_CHAMADA = novoCanvas(W, H);
  { const x = FUNDO_CHAMADA.getContext('2d'); x.filter = 'blur(48px) brightness(.55) saturate(.8)'; x.drawImage(IMG.rosto, -140, -160, W + 280, H + 320); x.filter = 'none'; const v = x.createLinearGradient(0, 0, 0, H); v.addColorStop(0, 'rgba(6,7,10,.35)'); v.addColorStop(0.55, 'rgba(6,7,10,.12)'); v.addColorStop(1, 'rgba(6,7,10,.72)'); x.fillStyle = v; x.fillRect(0, 0, W, H); }
  AVATAR = novoCanvas(480, 480);
  { const x = AVATAR.getContext('2d'); x.beginPath(); x.arc(240, 240, 240, 0, Math.PI * 2); x.clip(); x.drawImage(IMG.rosto, 90, 300, 880, 880, 0, 0, 480, 480); }
  // a Tabela 3 do IBGE, com os valores do documento
  TABELA = novoCanvas(1800, 1560);
  { const x = TABELA.getContext('2d'); x.scale(2, 2);
    x.shadowColor = 'rgba(0,0,0,.42)'; x.shadowBlur = 22; x.shadowOffsetY = 10; x.fillStyle = '#f7f4ec'; x.fillRect(20, 20, 860, 730); x.shadowColor = 'transparent';
    x.globalCompositeOperation = 'multiply'; x.globalAlpha = 0.13; x.fillStyle = x.createPattern(grao(), 'repeat'); x.fillRect(20, 20, 860, 730); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
    x.fillStyle = '#17160f'; x.font = `400 66px ${F_SER}`; x.fillText('Expectativa de vida', 70, 112);
    x.font = `600 27px ${F_UI}`; x.fillStyle = '#4c4a41'; x.fillText('Brasil, 2024. Anos que ainda faltam, em média.', 72, 156);
    x.fillStyle = '#17160f'; x.fillRect(70, 186, 760, 3);
    const lin = [['Idade', 'Homens', 'Mulheres'], ['50 anos', '28,7', '32,9'], ['55 anos', '24,6', '28,4'], ['60 anos', '20,8', '24,2'], ['65 anos', '17,2', '20,1'], ['70 anos', '14,0', '16,3']];
    lin.forEach((l, i) => {
      const y = 248 + i * 76;
      x.fillStyle = i === 0 ? '#5a574c' : '#17160f'; x.font = `${i === 0 ? 700 : 600} ${i === 0 ? 30 : 46}px ${F_UI}`;
      x.textAlign = 'left'; x.fillText(l[0], 74, y); x.textAlign = 'right'; x.fillText(l[1], 590, y); x.fillText(l[2], 824, y); x.textAlign = 'left';
      if (i) { x.fillStyle = 'rgba(23,22,15,.18)'; x.fillRect(70, y + 22, 760, 2); }
    });
    x.font = `600 22px ${F_UI}`; x.fillStyle = '#5a574c'; x.fillText('Fonte: IBGE, Tábuas Completas de Mortalidade 2024, Tabela 3', 72, 712);
  }
  const quad = (cor, brilho) => { const cv = novoCanvas(80, 80), x = cv.getContext('2d'); x.shadowColor = brilho || 'transparent'; x.shadowBlur = brilho ? 16 : 0; x.fillStyle = cor; M.rrect(x, 18, 18, 44, 44, 6); x.fill(); return cv; };
  QUAD_AZUL = quad('#a9d6ff', 'rgba(110,180,255,.9)');
  QUAD_OURO = quad('#ffd23f', 'rgba(255,200,60,.95)');
  QUAD_APAGADO = quad('#2a2b30', null);
}

// ── o dia passando: cor do sol e sombra da persiana ──
const LUZ = [
  [0, [246, 243, 234], 0.36, -58, 0],
  [24, [255, 253, 246], 0.38, -55, 0],
  [38, [255, 226, 178], 0.44, -49, 0.35],
  [46, [255, 196, 132], 0.52, -44, 0.75],
  [53, [206, 146, 122], 0.42, -40, 0.25],
  [60, [146, 130, 160], 0.3, -36, 0],
  [70, [122, 108, 138], 0.24, -34, 0],
  [75, [58, 54, 78], 0.14, -34, 0],
  [78, [34, 33, 48], 0.08, -34, 0],
  [90, [34, 33, 48], 0.08, -34, 0],
];
function luzEm(t) {
  let i = 0; while (i < LUZ.length - 2 && t >= LUZ[i + 1][0]) i++;
  const a = LUZ[i], b = LUZ[i + 1], p = M.smooth(clamp((t - a[0]) / (b[0] - a[0])));
  return { cor: a[1].map((v, k) => lerp(v, b[1][k], p)), forca: lerp(a[2], b[2], p), ang: lerp(a[3], b[3], p), calor: lerp(a[4], b[4], p) };
}
function luz(t) {
  const l = luzEm(t);
  g.save();
  g.globalCompositeOperation = 'multiply';
  g.save(); g.translate(W / 2, H / 2); g.rotate((l.ang * Math.PI) / 180); g.globalAlpha = l.forca;
  const esc = 1.05 + t * 0.003, S = 2600 * esc, des = ((t * 7) % (S * 0.17));
  g.drawImage(IMG.persiana, -S / 2, -S / 2 + des, S, S); g.drawImage(IMG.persiana, -S / 2, -S / 2 + des - S, S, S);
  g.restore();
  g.globalAlpha = 1; g.fillStyle = `rgb(${l.cor.map(Math.round).join(',')})`; g.fillRect(0, 0, W, H);
  if (l.calor > 0.01) {
    g.globalCompositeOperation = 'soft-light'; g.globalAlpha = l.calor * 0.7;
    const r = g.createRadialGradient(W * 0.9, H * 0.12, 60, W * 0.7, H * 0.4, H * 0.95); r.addColorStop(0, '#ffcf7a'); r.addColorStop(1, '#6a3010'); g.fillStyle = r; g.fillRect(0, 0, W, H);
  }
  g.restore();
}

// ── telefone ──
const ICONE_FONE = new Path2D('M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z');
const ICONE_ENVIA = new Path2D('M10 9V5l-7 7 7 7v-4.1c5 0 8.5 1.6 11 5.1-1-5-4-10-11-11z');
function celular(cx, cy, k, rot, tela) {
  g.save(); g.translate(cx, cy); g.rotate(rot); g.scale(k, k);
  const r = 96 * clamp((1 - k) / 0.1);
  g.fillStyle = '#060608'; M.rrect(g, -W / 2 - 24, -H / 2 - 24, W + 48, H + 48, r + 24); g.fill();
  g.strokeStyle = 'rgba(255,255,255,.16)'; g.lineWidth = 3; g.stroke();
  g.save(); M.rrect(g, -W / 2, -H / 2, W, H, r); g.clip(); g.translate(-W / 2, -H / 2); tela(); g.restore();
  g.restore();
}
function vibra(t) {
  // duas rajadas por ciclo; o ciclo cabe certo no filme, para a emenda do loop não pular
  const ciclo = DURATION / 34, f = ((t % ciclo) + ciclo) % ciclo / ciclo;
  return f < 0.42 ? 1 : 0;
}
function chamadaLigada(t) { return t < 3.0 || t > 81.7; }
function telaChamada(t, perdida) {
  g.drawImage(FUNDO_CHAMADA, 0, 0);
  g.drawImage(AVATAR, W / 2 - 170, 300, 340, 340);
  g.textAlign = 'center'; g.fillStyle = '#fff'; g.font = `700 128px ${F_UI}`; g.fillText('Mãe', W / 2, 800);
  g.font = `600 46px ${F_UI}`;
  g.fillStyle = perdida > 0.5 ? '#ff8d8d' : 'rgba(255,255,255,.78)';
  g.fillText(perdida > 0.5 ? 'Chamada perdida' : 'chamando', W / 2, 872);
  const a = 1 - clamp(perdida * 2);
  if (a > 0) {
    g.save(); g.globalAlpha = a;
    const onda = ((t * 85) / DURATION) % 1;
    const botao = (x, cor, gira) => {
      if (!gira) { g.save(); g.globalAlpha = a * (1 - onda) * 0.55; g.strokeStyle = cor; g.lineWidth = 5; g.beginPath(); g.arc(x, 1640, 92 + onda * 62, 0, 7); g.stroke(); g.restore(); }
      g.fillStyle = cor; g.beginPath(); g.arc(x, 1640, 92, 0, 7); g.fill();
      g.save(); g.translate(x, 1640); if (gira) g.rotate(2.36); g.scale(4.6, 4.6); g.translate(-12, -12); g.fillStyle = '#fff'; g.fill(ICONE_FONE); g.restore();
    };
    botao(270, '#e5484d', true); botao(810, '#2fb568', false);
    g.restore();
  }
  g.textAlign = 'left';
}
// A conversa: as mensagens dela, sem resposta. A última chega quando a voz diz.
function balao(txt, y, hora, t, t0) {
  const d = t - t0; if (d < 0) return;
  const px = 74; g.font = `600 ${px}px ${F_UI}`; const w = g.measureText(txt).width, bw = w + 110, bh = 178;
  const s = t0 < 0 ? 1 : M.springZ(d, 0.72, 3.2);
  g.save(); g.translate(56, y + bh); g.scale(s, s); g.translate(0, -bh);
  g.fillStyle = '#262f34'; M.rrect(g, 0, 0, bw, bh, 40); g.fill();
  g.fillStyle = '#f6f8f8'; g.textAlign = 'left'; g.fillText(txt, 52, 96);
  g.font = `600 32px ${F_UI}`; g.fillStyle = 'rgba(255,255,255,.55)'; g.textAlign = 'right'; g.fillText(hora, bw - 34, 150); g.restore(); g.textAlign = 'left';
}
function telaConversa(t) {
  g.fillStyle = '#0d1215'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#171e22'; g.fillRect(0, 0, W, 340);
  g.drawImage(AVATAR, 150, 164, 140, 140);
  g.fillStyle = '#fff'; g.font = `700 76px ${F_UI}`; g.fillText('Mãe', 322, 232);
  g.fillStyle = 'rgba(255,255,255,.6)'; g.font = `600 38px ${F_UI}`; g.fillText('online', 322, 288);
  g.strokeStyle = '#fff'; g.lineWidth = 9; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); g.moveTo(96, 196); g.lineTo(60, 234); g.lineTo(96, 272); g.stroke();
  const faixa = (txt, y) => { g.font = `600 36px ${F_UI}`; const w = g.measureText(txt).width + 60; g.fillStyle = '#1b2327'; M.rrect(g, W / 2 - w / 2, y, w, 66, 20); g.fill(); g.fillStyle = 'rgba(255,255,255,.66)'; g.textAlign = 'center'; g.fillText(txt, W / 2, y + 46); g.textAlign = 'left'; };
  faixa('terça', 430); balao('já comeu?', 524, '12:04', t, -1);
  faixa('ontem', 746); balao('leva um casaco', 840, '07:12', t, -1);
  faixa('hoje', 1062);
  const fala = P('p26', 1) - 0.04;
  if (t > fala - 0.85 && t < fala) { // digitando
    g.fillStyle = '#262f34'; M.rrect(g, 56, 1156, 240, 126, 40); g.fill();
    for (let i = 0; i < 3; i++) { const f = 0.5 + 0.5 * Math.sin(t * 9 - i * 0.9); g.fillStyle = `rgba(255,255,255,${0.35 + f * 0.5})`; g.beginPath(); g.arc(120 + i * 56, 1219 - f * 8, 15, 0, 7); g.fill(); }
  }
  balao('me avisa quando chegar', 1156, 'agora', t, fala);
  g.fillStyle = '#171e22'; M.rrect(g, 44, 1730, 800, 110, 55); g.fill();
  g.fillStyle = 'rgba(255,255,255,.45)'; g.font = `600 40px ${F_UI}`; g.fillText('Mensagem', 96, 1800);
  g.fillStyle = '#2fb568'; g.beginPath(); g.arc(950, 1785, 62, 0, 7); g.fill();
  g.fillStyle = '#fff'; g.beginPath(); g.moveTo(926, 1752); g.lineTo(986, 1785); g.lineTo(926, 1818); g.lineTo(934, 1785); g.closePath(); g.fill();
}

// ── cenas ──
const FOLHA = (nome, t, a, zoom = 0.02) => { const s = 1 + zoom * clamp((t - a) / 10); g.save(); g.translate(W / 2, H / 2); g.scale(s, s); g.drawImage(IMG[nome], -600, -1067); g.restore(); };

const CENAS = {
  chamada: {
    a: 0, b: 5.1,
    base(t) {
      g.drawImage(IMG.madeira, -60, -107);
      const k = kChamada(t), [x, y] = [540, lerp(960, 1000, 1 - k)];
      if (k < 0.97) { g.save(); g.filter = 'blur(26px)'; g.fillStyle = 'rgba(0,0,0,.62)'; g.translate(x + 22, y + 30); g.rotate(rotChamada(t)); g.fillRect((-W / 2) * k, (-H / 2) * k, W * k, H * k); g.restore(); }
    },
    brilho(t) {
      const k = kChamada(t), per = clamp((t - 2.9) / 0.4), z = vibra(t) && chamadaLigada(t) ? Math.sin(t * 2 * Math.PI * 34) * 4 * (t < 3 ? 1 : 0.6) : 0;
      celular(540 + z, lerp(960, 1000, 1 - k), k, rotChamada(t), () => telaChamada(t, per));
      poe(rotulo('Quantas vezes', 'ama', 74, 3), 540, 1010, junta(bate(t, -1), { dy: fuga(t) }), -0.02);
      poe(rotulo('você ainda vai ver', 'pre', 62, 4), 540, 1118, junta(risca(t, P('p01', 2) - 0.03), { dy: fuga(t) }), 0.012);
      const ent = bate(t, P('p02', 0));
      poe(rotulo('A gente fez a conta', 'pre', 60, 5), 540, 260, ent, -0.012);
      poe(rotulo('ou quem te criou', 'ser', 56, 6), 540, 1745 - 130, foca(t, P('p02', 2)), 0.018);
    },
  },
  tabela: {
    a: 4.6, b: 10.9,
    base(t) {
      FOLHA('papel', t, 4.6);
      const zoom = 1 + 0.10 * E.move(clamp((t - P('p03', 2)) / 2.2)), linha = P('p03', 2);
      g.save(); g.translate(540, 900); g.scale(zoom, zoom); g.rotate(-0.012); g.translate(-450, -390);
      g.drawImage(TABELA, 0, 0, 900, 780);
      fita(450, 22, 240, 0.02, 7);
      // marca-texto na linha dos 60 anos
      const m = clamp((t - linha) / qd(9));
      if (m > 0) { g.save(); g.globalCompositeOperation = 'multiply'; g.fillStyle = '#f5d84c'; g.fillRect(62, 448, 776 * E.enter(m), 72); g.restore(); }
      caneta(elipseMao(752, 486, 112, 56), t, P('p03', 11), 0.5);
      g.restore();
      poe(rotulo('Mulher de 60 anos', 'pre', 62, 8), 540, 250, risca(t, P('p03', 2)), -0.012);
      poe(rotulo('60 + 24 = 84 anos', 'num', 84, 9), 540, 1400, bate(t, P('p03', 10)), -0.018);
      poe(rotulo('Faltam 24 anos', 'pre', 66, 10), 540, 1530, risca(t, P('p03', 11)), 0.012);
    },
  },
  conta: {
    a: 10.34, b: 27.74,
    base(t) {
      const u = clamp((t - 26.0) / (27.72 - 26.0)), z = Math.exp(Math.log(1080 / GRADE.lado) * u * u * u);
      FOLHA('papel', t, 9.36);
      g.save();
      const alvo = celula(ALVO, GRADE); g.translate(540, 960); g.scale(z, z); g.translate(-lerp(540, alvo[0], M.smooth(clamp(u * 3))), -lerp(960, alvo[1], M.smooth(clamp(u * 3))));
      contaConteudo(t);
      g.restore();
    },
  },
  mosaico: {
    a: 27.72, b: 57.25,
    base(t) {
      g.drawImage(IMG.ardosia, -60, -107);
      const cam = camMosaico(t);
      desenhaMosaico(t, cam, false);
      rotulosMosaico(t, false);
    },
    brilho(t) {
      const cam = camMosaico(t), f = clamp((t - 50) / 4);
      if (f > 0) desenhaMosaico(t, cam, true, f);
      rotulosMosaico(t, true);
    },
  },
  ano: {
    a: 56.75, b: 67.12,
    base(t) { g.drawImage(IMG.ardosia, -60, -107); },
    brilho(t) { anoConteudo(t); },
  },
  janela: {
    a: 66.62, b: 71.12,
    base(t) {
      FOLHA('kraft', t, 66.6, 0.1);
    },
    brilho(t) {
      const s = 1 + 0.05 * clamp((t - 66.6) / 4.5);
      polaroide(540, 790, 940, 750, -0.018, { s }, quadro('janela', t - 66.6), 2);
      poe(rotulo('a última vez', 'ser', 92, 11), 540, 1305, foca(t, P('p22', 1)), -0.014);
      poe(rotulo('nunca avisa', 'ser', 92, 12), 540, 1430, foca(t, P('p22', 3)), 0.012);
    },
  },
  naomanda: {
    a: 70.72, b: 75.6,
    base(t) { g.drawImage(IMG.ardosia, -60, -107); },
    brilho(t) {
      g.save(); g.translate(540, 700); const a = M.springZ(t - 70.86, 0.8, 2.2); g.scale(-22 * a, 22 * a); g.translate(-12, -12); g.fillStyle = '#f5f2e8'; g.fill(ICONE_ENVIA); g.restore();
      const n = P('p23', 6) - 0.1;
      caneta([[250, 450], [830, 960]], t, n, 0.22, '#d8222f', 26);
      caneta([[840, 440], [240, 970]], t, n + 0.2, 0.22, '#d8222f', 26);
      poe(rotulo('Não manda esse vídeo', 'pre', 70, 14), 540, 1180, risca(t, P('p23', 1)), -0.012);
      poe(rotulo('pra ninguém', 'ser', 96, 15), 540, 1320, foca(t, P('p23', 5)), 0.014);
    },
  },
  noite: {
    a: 74.9, b: 90,
    base(t) {
      g.drawImage(IMG.madeira, -60, -107);
      const k = kNoite(t);
      if (k < 0.97) { g.save(); g.filter = 'blur(26px)'; g.fillStyle = 'rgba(0,0,0,.7)'; g.translate(562, 985); g.fillRect((-W / 2) * k, (-H / 2) * k, W * k, H * k); g.restore(); }
    },
    brilho(t) {
      const k = kNoite(t);
      if (k < 0.99) { // a luz da tela no tampo da mesa
        g.save(); g.globalCompositeOperation = 'screen'; const r = g.createRadialGradient(540, 960, 200, 540, 960, 980); r.addColorStop(0, 'rgba(120,150,170,.42)'); r.addColorStop(1, 'rgba(120,150,170,0)'); g.fillStyle = r; g.fillRect(0, 0, W, H); g.restore();
      }
      const e = E.move(clamp((t - 81.7) / qd(13))), z = t > 81.9 && vibra(t) ? Math.sin(t * 2 * Math.PI * 34) * 4 : 0;
      celular(540 + z, 960, k, 0, () => {
        telaConversa(t);
        if (e > 0) { g.save(); g.translate(0, (e - 1) * H); telaChamada(t, 0); g.restore(); }
      });
      poe(rotulo('melhor: vai lá', 'ser', 92, 18), 540, 170 + 40, junta(foca(t, P('p25', 1)), { a: 1 - clamp((t - (P('p26', 0) - 0.3)) / 0.3) }), -0.012);
      if (t > 84.3) poe(rotulo('Quantas vezes', 'ama', 74, 3), 540, 1010, bate(t, DURATION - qd(14)), -0.02);
    },
  },
};
const kChamada = (t) => lerp(1, 0.56, E.move(clamp((t - 2.72) / 1.0))) + 0.02 * clamp((t - 3.7) / 1.4);
const rotChamada = (t) => -0.07 * E.move(clamp((t - 2.72) / 1.0));
const fuga = (t) => { const d = t - 2.72; return d > 0 ? d * d * 3800 : 0; };   // os rótulos do gancho caem para fora quando o telefone recua
const kNoite = (t) => lerp(0.6, 1, E.move(clamp((t - 75.6) / 3.6)));

// Conta: a folha do caderno.
const GRADE = { x0: 172, y0: 520, cel: 46, lado: 40, col: 16 };
const GRADE48 = { x0: 288, y0: 500, cel: 84, lado: 74, col: 6 };
const celula = (i, gr) => [gr.x0 + ((i % gr.col) + 0.5) * gr.cel, gr.y0 + (Math.floor(i / gr.col) + 0.5) * gr.cel];
const ALVO = 8 * 16 + 8;   // o quadradinho em que a câmera mergulha
function quadradinho(i, x, y, lado, a = 1) {
  g.save(); g.globalAlpha *= a; g.drawImage(QUAD_AMA[(i * 7 + (i >> 2)) % 4], x - lado * 0.625, y - lado * 0.625, lado * 1.25, lado * 1.25); g.restore();
}
function contaConteudo(t) {
  const t48 = P('p04', 12), tv = P('p04', 13), sobe = P('p06', 0) - 0.55, t288 = P('p07', 5), mesT = P('p07', 3), lim = 26.05;
  const saiMao = clamp((t - sobe) / 0.35);
  // a voz já está falando: a folha nunca fica vazia
  poe(rotulo('Se você mora longe', 'pre', 66, 20), 540, 250, junta(risca(t, P('p04', 0) - 0.05), { a: 1 - saiMao }), -0.012);
  // a conta escrita à mão
  if (saiMao < 1) {
    g.save(); g.globalAlpha = 1 - saiMao; g.translate(0, -saiMao * 60);
    aMao('2 visitas por ano', 540, 420, 118, t, P('p04', 7), 0.75);
    aMao('x 24 anos', 540, 545, 118, t, P('p04', 11) - 0.2, 0.5);
    caneta([[250, 586], [440, 592], [660, 582], [830, 590]], t, t48 - 0.28, 0.24, '#c5202c', 7);
    g.restore();
  }
  // 48 sobe para o canto e cede a folha aos quadradinhos
  const m48 = E.move(clamp((t - sobe) / 0.55)), sai48 = clamp((t - (P('p07', 3) - 0.1)) / 0.3);
  if (sai48 < 1) {
    const pulso = t > P('p05', 0) ? 1 + 0.06 * Math.exp(-7 * (t - P('p05', 0))) : 1;
    const o = bate(t, t48);
    if (o) { o.s *= pulso * lerp(1, 0.56, m48); o.a = (o.a ?? 1) * (1 - sai48); }
    poe(rotulo('48', 'num', 270, 21), lerp(540, 330, m48), lerp(795, 290, m48), o, -0.02);
    const o2 = risca(t, tv); if (o2) o2.a = 1 - sai48;
    poe(rotulo('visitas', 'pre', 66, 22), lerp(540, 690, m48), lerp(1000, 300, m48), o2, 0.015);
  }
  // os 48 quadradinhos cabem numa folha
  const iniQ = P('p06', 0) - 0.35, durQ = P('p06', 2) - iniQ + 0.4, iniM = mesT - 0.2, durM = 0.62, iniR = t288 - 0.55, durR = 1.75;
  for (let i = 0; i < 288; i++) {
    let x, y, lado, a = 1;
    if (i < 48) {
      const t0 = iniQ + M.stagCap(i, 48, durQ, 0.92); if (t < t0) continue;
      const e = E.premium(clamp((t - t0) / qd(5)));
      const [ax, ay] = celula(i, GRADE48), [bx, by] = celula(i, GRADE), m = E.move(clamp((t - iniM - i * 0.004) / durM));
      x = lerp(ax, bx, m); y = lerp(ay, by, m); lado = lerp(GRADE48.lado, GRADE.lado, m) * (1.25 - 0.25 * e); a = clamp((t - t0) / qd(2));
    } else {
      const t0 = iniR + M.stagCap(i - 48, 240, durR, 0.88); if (t < t0) continue;
      [x, y] = celula(i, GRADE); lado = GRADE.lado * (1.3 - 0.3 * E.premium(clamp((t - t0) / qd(4)))); a = clamp((t - t0) / qd(2));
    }
    quadradinho(i, x, y, lado, a);
    if (i === ALVO && t > 26) { // dentro do quadradinho do mergulho já se vê a foto
      const f = clamp((t - 26.4) / 0.9);
      if (f > 0) { g.save(); g.globalAlpha = f; g.drawImage(IMG.mergulho, x - lado / 2, y - lado / 2, lado, lado); g.restore(); }
    }
  }
  poe(rotulo('cabe numa folha de caderno', 'ser', 70, 23), 540, 1295, junta(foca(t, P('p06', 2) - 0.1), { a: 1 - clamp((t - iniM + 0.2) / 0.25) }), -0.012);
  // 288: todo mês
  poe(rotulo('Todo mês', 'pre', 60, 24), 540, 170, risca(t, mesT), -0.01);
  poe(rotulo('288', 'num', 190, 25), 540, 345, bate(t, t288), -0.02);
  const barra = P('p09', 0);
  poe(rotulo('parece bastante', 'ser', 72, 26), 540, 1432, junta(foca(t, P('p08', 0)), { a: 1 - clamp((t - barra + 0.05) / 0.2) }), 0.012);
  poe(rotulo('Não dá um ano', 'pre', 66, 27), 540, 1432, risca(t, barra), -0.01);
  // a régua de um ano: 288 de 365 dias
  const e = E.move(clamp((t - barra) / 0.65));
  if (e > 0) {
    g.save(); g.fillStyle = 'rgba(25,25,28,.2)'; g.fillRect(140, 1505, 800, 30);
    g.fillStyle = '#f0ca35'; g.fillRect(140, 1505, 800 * (288 / 365) * e, 30);
    g.strokeStyle = '#1b1a14'; g.lineWidth = 3; g.strokeRect(140, 1505, 800, 30);
    g.font = `700 34px ${F_UI}`; g.fillStyle = '#1b1a14'; g.textAlign = 'right'; g.fillText('365 dias', 940, 1582); g.textAlign = 'left'; g.fillText('288', 140, 1582); g.restore();
  }
}

// Mosaico: 6.369 ladrilhos, um por dia.
const T = 1080 / D.colunas;
const HOJE = new Set(D.hoje), AOS18 = new Set(D.aos18);
const FALL0 = P('p17', 8) + 0.5, FALL1 = P('p18', 5) - 0.06, G_QUEDA = 2300, ONDA = 3.4;
const TL = D.tiles.map(([lin, col], i) => {
  const r = M.rng(i * 13 + 5), j = r(), vx = (r() - 0.5) * 170, rv = (r() - 0.5) * 7, fv = 2 + r() * 8, foto = Math.floor(r() * 24);
  let t0 = FALL0 + (lin / D.linhas) * ONDA + j * 0.42;
  if (HOJE.has(i)) t0 = Infinity; else if (AOS18.has(i)) t0 = FALL1 + j * 0.6;
  return { lin, col, x: col * T, y: lin * T, t0, vx, rv, fv, foto, resta: HOJE.has(i) || AOS18.has(i) };
});
const OLHOS = D.meio_olhos, CENTRO = [540, 844], LADRILHO = (() => { const i = TL.findIndex((l) => l.lin === 50 && l.col === 32); return i; })();
function camMosaico(t) {
  // recua do ladrilho até o rosto inteiro: escala em log, para o recuo ter o mesmo ritmo do começo ao fim
  const u = clamp((t - 28.1) / (34.2 - 28.1)), e = M.smooth(u);
  const S0 = 1080 / T, S1 = 1.14, lt = TL[LADRILHO], foco0 = [lt.x + T / 2, lt.y + T / 2];
  let S = Math.exp(lerp(Math.log(S0), Math.log(S1), e)), f = [lerp(foco0[0], CENTRO[0], e), lerp(foco0[1], CENTRO[1], e)];
  S *= 1 + 0.045 * clamp((t - 34.2) / 16);   // fica chegando perto dela, sem parar
  const o = E.move(clamp((t - 51.6) / 5));
  S *= 1 + 0.3 * o; f = [lerp(f[0], OLHOS[0], o), lerp(f[1], OLHOS[1], o)];
  return { S, f };
}
function desenhaMosaico(t, cam, soResta, forca = 1) {
  const { S, f } = cam, ts = T * S, lado = ts - Math.max(0.9, ts * 0.06), k = M.smooth(clamp((ts - 34) / 170));
  const amarelo = 1 - clamp((t - 27.72) / 0.35), fol = IMG['folha-fotos'], ros = IMG.rosto;
  const ox = 540 - S * f[0], oy = 960 - S * f[1];
  if (!soResta && k < 1) { // por baixo, o rosto apagado: a fresta entre os dias fica discreta. A onda da queda leva junto.
    const lin = (t - FALL0) / ONDA * D.linhas, corte = Math.max(oy, oy + lin * ts);
    if (corte < H) { g.save(); g.beginPath(); g.rect(-100, corte, W + 200, H - corte + 200); g.clip(); g.globalAlpha = 0.6 * (1 - k); g.drawImage(ros, ox, oy, 1080 * S, 1688 * S); g.restore(); }
  }
  g.save(); if (soResta) g.globalAlpha = forca;   // sem filter aqui: aplicado ladrilho a ladrilho, ele derruba o render
  for (let i = 0; i < TL.length; i++) {
    const l = TL[i];
    if (soResta && !l.resta) continue;
    const X = ox + l.x * S, Y = oy + l.y * S, d = t - l.t0;
    if (d <= 0) {
      if (X > W || Y > H || X + ts < 0 || Y + ts < 0) continue;
      if (k < 1) g.drawImage(ros, l.x, l.y, T, T, X, Y, lado, lado);
      if (k > 0) {
        g.save(); g.globalAlpha = k;
        if (i === LADRILHO && ts > 240) g.drawImage(IMG.mergulho, X, Y, lado, lado);
        else g.drawImage(fol, (l.foto % 6) * 256, Math.floor(l.foto / 6) * 256, 256, 256, X, Y, lado, lado);
        g.restore();
      }
      if (amarelo > 0 && i !== LADRILHO) { g.save(); g.globalAlpha = amarelo * 0.85; g.fillStyle = '#f0ca35'; g.fillRect(X, Y, lado, lado); g.restore(); }
    } else {
      const yq = Y + 0.5 * G_QUEDA * d * d; if (yq > H + 60) continue;
      g.save(); g.translate(X + lado / 2 + l.vx * d, yq + lado / 2); g.rotate(l.rv * d); g.scale(Math.cos(l.fv * d), 1);
      g.drawImage(ros, l.x, l.y, T, T, -lado / 2, -lado / 2, lado, lado); g.restore();
    }
  }
  g.restore();
}
function rotulosMosaico(t, brilho) {
  if (!brilho) {
    const t12 = P('p11', 0), fim11 = P('p12', 0) - 0.05;
    poe(rotulo('1 quadradinho', 'pre', 62, 31), 540, 1430, junta(risca(t, t12 + 0.15), { a: 1 - clamp((t - fim11) / 0.2) }), -0.012);
    poe(rotulo('= 1 dia', 'ama', 78, 32), 540, 1535, junta(bate(t, P('p11', 5)), { a: 1 - clamp((t - fim11) / 0.2) }), 0.015);
    // contador: os dias até sair de casa
    const iC = P('p12', 0), fC = P('p12', 8), sC = P('p13', 0) - 0.3;
    if (t >= iC && t < sC + 0.3) {
      const v = Math.round(CONTA.ateSair * E.premium(clamp((M.frameT(t) - iC) / (fC - iC + 0.2))));
      const o = junta(bate(t, iC), { dy: Math.max(0, t - sC) ** 2 * 7000 });
      poe(rotulo(v.toLocaleString('pt-BR').padStart(5, ' '), 'num', 150, 33), 540, 1440, o, -0.015);
      poe(rotulo('Dias até sair de casa', 'pre', 58, 34), 540, 1570, junta(risca(t, iC + 0.25), { dy: Math.max(0, t - sC) ** 2 * 7000 }), 0.01);
    }
    // o que ela dizia: as fotos em cima, a frase embaixo; os olhos e o sorriso ficam livres
    const cai = (n) => queda(t, FALL0 + 0.02 + n * 0.1, n + 50);
    polaroide(236, 400, 350, 438, -0.09, junta(bate(t, P('p13', 2) - 0.04, qd(6)), cai(1)), quadro('cozinha', t - P('p13', 0)), 3);
    polaroide(846, 430, 350, 438, 0.08, junta(bate(t, P('p14', 2) - 0.04, qd(6)), cai(2)), quadro('campo', t - P('p14', 0)), 4);
    polaroide(540, 340, 310, 388, 0.02, junta(bate(t, P('p15', 2) - 0.04, qd(6)), cai(3)), quadro('espera', t - P('p15', 0)), 5);
    const pulsa = (id) => (t > P(id, 0) ? 0.07 * Math.exp(-8 * (t - P(id, 0))) : 0);
    const seis = bate(t, P('p13', 0));
    if (seis) { seis.s *= 1 + pulsa('p14') + pulsa('p15'); poe(rotulo('6 mil', 'pre', 66, 35), 540, 1392, junta(seis, { a: 1 - clamp((t - (P('p16', 0) - 0.12)) / 0.14) }), -0.014); }
    const frase = (txt, id, fim, seed, rot) => poe(rotulo(txt, 'ser', 92, seed), 540, 1512, junta(foca(t, P(id, 2) - 0.08), { a: 1 - clamp((t - fim) / 0.12) }), rot);
    frase('“já comeu?”', 'p13', P('p14', 0) - 0.08, 36, -0.012);
    frase('“leva um casaco”', 'p14', P('p15', 0) - 0.08, 37, 0.012);
    frase('“me avisa quando chegar”', 'p15', P('p16', 0) - 0.12, 38, -0.01);
    const fimSempre = 1 - clamp((t - (P('p17', 0) - 0.2)) / 0.2);
    poe(rotulo('A gente achava', 'pre', 60, 39), 540, 1392, junta(risca(t, P('p16', 3)), { a: fimSempre }), 0.012);
    poe(rotulo('pra sempre', 'ser', 126, 40), 540, 1525, junta(foca(t, P('p16', 8) - 0.05), { a: fimSempre }), -0.014);
    poe(rotulo('Aos 18 anos', 'pre', 70, 41), 540, 1135, junta(risca(t, P('p17', 1)), queda(t, FALL0 + 1.5, 70)), -0.012);
    poe(rotulo('93%', 'num', 250, 42), 540, 1350, junta(bate(t, P('p17', 7)), queda(t, FALL0 + 1.95, 71)), -0.024);
    poe(rotulo('Do seu tempo com ela', 'pre', 60, 43), 540, 1545, junta(risca(t, P('p17', 9)), queda(t, FALL0 + 2.1, 72)), 0.012);
  } else {
    poe(rotulo('o que sobrou', 'ser', 84, 44), 540, 1300, foca(t, P('p18', 3) - 0.05), -0.012);
    poe(rotulo('288', 'num', 190, 45), 540, 1480, bate(t, P('p18', 5)), 0.02);
  }
}

// Um ano em quadradinhos: 365 dias.
const ANO = { col: 19, cel: 50, x0: 65, y0: 480 };
const DIAS_COM_ELA = Array.from({ length: 12 }, (_, i) => Math.round(18 + (i * 365) / 12));
function anoConteudo(t) {
  const a = clamp((t - 56.9) / 0.5), i0 = P('p19', 5) - 0.1, dur = P('p19', 9) - i0 + 0.3, apaga = clamp((t - P('p21', 0)) / 0.45);
  const nEla = P('p21', 2) - 0.35;
  for (let i = 0; i < 365; i++) {
    const x = ANO.x0 + (i % ANO.col) * ANO.cel, y = ANO.y0 + Math.floor(i / ANO.col) * ANO.cel;
    g.save(); g.globalAlpha = a; g.drawImage(QUAD_APAGADO, x - 15, y - 15, 80, 80);
    if (i < CONTA.diasInternet) {
      const t0 = i0 + M.stagCap(i, CONTA.diasInternet, dur, 0.95);
      if (t >= t0) { g.globalAlpha = lerp(clamp((t - t0) / qd(2)), 0.14, apaga); g.drawImage(QUAD_AZUL, x - 15, y - 15, 80, 80); }
    }
    const k = DIAS_COM_ELA.indexOf(i);
    if (k >= 0) {
      const t0 = nEla + k * 0.07;
      if (t >= t0) { const s = 1.7 - 0.7 * E.premium(clamp((t - t0) / qd(6))); g.globalAlpha = clamp((t - t0) / qd(2)); g.translate(x + 25, y + 25); g.scale(s, s); g.drawImage(QUAD_OURO, -40, -40, 80, 80); }
    }
    g.restore();
  }
  const sai = 1 - apaga, v = Math.round(CONTA.diasInternet * clamp((M.frameT(t) - i0) / dur));
  poe(rotulo('Esse ano', 'pre', 60, 51), 540, 165, junta(risca(t, P('p19', 1) - 0.05), { a: sai }), -0.012);
  if (t >= i0) poe(rotulo(`${v} dias`, 'num', 150, 52), 540, 318, junta(bate(t, i0), { a: sai }), -0.018);
  poe(rotulo('Na internet', 'pre', 62, 53), 540, 1565, junta(risca(t, P('p19', 8)), { a: sai }), 0.01);
  // você está aqui
  const tA = P('p20', 0) - 0.05, xA = ANO.x0 + ((CONTA.diasInternet - 1) % ANO.col) * ANO.cel + 25, yA = ANO.y0 + Math.floor((CONTA.diasInternet - 1) / ANO.col) * ANO.cel + 25;
  if (t > tA && apaga < 1) {
    g.save(); g.globalAlpha = sai;
    const p = 0.5 + 0.5 * Math.sin((t - tA) * 11);
    g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = sai * p; g.drawImage(QUAD_AZUL, xA - 40, yA - 40, 80, 80); g.restore();
    caneta([[470, 1105], [340, 1050], [210, 960], [xA + 12, yA + 38]], t, tA, 0.3, '#ff4a4a', 10);
    caneta([[xA + 44, yA + 72], [xA + 12, yA + 38], [xA + 2, yA + 86]], t, tA + 0.27, 0.1, '#ff4a4a', 10);
    aMao('inclusive agora', 690, 1148, 104, t, tA + 0.1, 0.42, '#ff5c5c');
    g.restore();
  }
  poe(rotulo('Com ela', 'pre', 60, 54), 540, 165, risca(t, P('p21', 0)), -0.012);
  poe(rotulo('12', 'num', 190, 55), 540, 326, bate(t, P('p21', 2)), -0.02);
}

// Fichas de corte com os painéis que batem: vermelho em cima, papel embaixo.
function painel(y, h, cor, txt, tinta, seed) {
  g.save(); g.beginPath(); g.rect(0, y, W, h); g.clip();
  g.fillStyle = cor; g.fillRect(0, y, W, h);
  g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.25; g.fillStyle = g.createPattern(grao(), 'repeat'); g.fillRect(0, y, W, h);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 0.14; g.fillStyle = '#000'; g.fillRect(W * 0.5 - 1, y, 2, h); g.globalAlpha = 1;
  let px = 300; g.font = `400 ${px}px ${F_BLACK}`; px = Math.min(330, px * (W * 0.98) / g.measureText(txt).width); g.font = `400 ${px}px ${F_BLACK}`;
  g.fillStyle = tinta; g.textAlign = 'center'; g.fillText(txt, W / 2, y + h / 2 + px * 0.34); g.textAlign = 'left';
  g.restore();
}
function batePainel(t) {
  const t1 = P('p01', 7) - 0.06, e1 = E.exit(clamp((t - t1) / qd(5))), s1 = E.exit(clamp((t - (PF('p01') + 0.18)) / qd(6)));
  if (t >= t1 && s1 < 1) painel(H - 620 * e1 + 620 * s1, 620, '#b4152b', 'sua mãe?', '#f6f1e7', 1);
  const t2 = P('p24', 0) - 0.05, a2 = E.exit(clamp((t - t2) / qd(5))), s2 = E.move(clamp((t - (PF('p24') + 0.34)) / qd(13)));
  if (t >= t2 && s2 < 1) {
    painel(-960 + 960 * a2 - 980 * s2, 960, '#b4152b', 'liga', '#f6f1e7', 2);
    painel(H - 960 * a2 + 980 * s2, 960, '#ece7da', 'pra ela', '#16140e', 3);
  }
}

// Linha de fonte na lateral, como nas matérias: quem quer conferir acha.
const CREDITOS = [
  [0, 4.8, 'IMAGEM ILUSTRATIVA'],
  [5, 10.4, 'FONTE: IBGE, TÁBUAS COMPLETAS DE MORTALIDADE 2024, TABELA 3'],
  [10.8, 27.7, 'SIMULAÇÃO COM A MÉDIA DO IBGE: MÃE DE 60 ANOS, VIVE ATÉ OS 84'],
  [27.7, 49.0, 'SIMULAÇÃO: SAIU DE CASA AOS 18, UMA VISITA POR MÊS DEPOIS. IDEIA DA CONTA: TIM URBAN, WAIT BUT WHY, 2015. FOTOS: PEXELS'],
  [56.9, 66.6, 'FONTE: WE ARE SOCIAL E MELTWATER, DIGITAL 2026 BRASIL: 53H30 POR SEMANA ONLINE'],
  [66.7, 70.7, 'VÍDEO: PEXELS. IMAGEM ILUSTRATIVA'],
];
function creditos(t) {
  const c = CREDITOS.find((x) => t >= x[0] && t < x[1]); if (!c) return;
  g.save(); g.translate(30, H - 360); g.rotate(-Math.PI / 2); g.font = `600 19px ${F_UI}`; g.letterSpacing = '1px'; g.globalAlpha = 0.72;
  g.fillStyle = 'rgba(0,0,0,.55)'; g.fillText(c[2], 1, 1); g.fillStyle = t > 56 || t < 4.8 ? '#e8e4d8' : '#2d2a22'; if (t >= 27.7 && t < 56.8) g.fillStyle = '#efe9dc';
  g.fillText(c[2], 0, 0); g.restore();
}

// ── transições: empurrão de câmera pela mesa ──
const PASSA = [
  { de: 'chamada', para: 'tabela', t: 4.62, d: qd(14), dx: 1, dy: 0 },
  { de: 'tabela', para: 'conta', t: 10.38, d: qd(14), dx: 0, dy: 1 },
  { de: 'mosaico', para: 'ano', t: 56.78, d: qd(14), dx: 1, dy: 0 },
  { de: 'ano', para: 'janela', t: 66.64, d: qd(14), dx: 0, dy: 1 },
  { de: 'janela', para: 'naomanda', t: 70.74, d: qd(12), dx: 1, dy: 0 },
];
function deslocamento(id, t) {
  for (const p of PASSA) {
    const u = clamp((t - p.t) / p.d), e = E.move(u), L = p.dx ? W + 70 : H + 70;
    if (p.de === id && t >= p.t) return [-p.dx * e * L, -p.dy * e * L];
    if (p.para === id && t < p.t + p.d) return [p.dx * (1 - e) * L, p.dy * (1 - e) * L];
  }
  return [0, 0];
}

function pinta(t) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  g.textBaseline = 'alphabetic'; g.textAlign = 'left';
  g.drawImage(IMG.madeira, -60, -107);
  const vis = Object.entries(CENAS).filter(([, c]) => t >= c.a && t < c.b);
  for (const [id, cena] of vis) { const [x, y] = deslocamento(id, t); g.save(); g.translate(x, y); cena.base(t); g.restore(); }
  luz(t);
  for (const [id, cena] of vis) { if (!cena.brilho) continue; const [x, y] = deslocamento(id, t); g.save(); g.translate(x, y); cena.brilho(t); g.restore(); }
  batePainel(t);
  creditos(t);
  M.vignette(g, W, H, 0.26);
  M.grain(g, W, H, t, 0.09, 24);
}
window.seek = (t) => { pinta(clamp(Number.isFinite(t) ? t : 0, 0, DURATION - 1e-4)); return true; };
window.renderAt = window.seek;
window.SUB_AT = (t) => (PASSA.some((p) => t >= p.t && t < p.t + p.d) || (t > 26.6 && t < 27.74) ? 12 : 4);
window.CUTS = [27.72];

window.SHOTS = [
  { name: 'chamada', from: 0, to: 2.7 }, { name: 'recua', from: 2.7, to: 4.62 }, { name: 'tabela', from: 4.62, to: 10.38 },
  { name: 'dois por ano', from: 10.38, to: 16.41 }, { name: '48 na folha', from: 16.41, to: 19.74 }, { name: '288', from: 19.74, to: 25.97 },
  { name: 'mergulho', from: 25.97, to: 27.72 }, { name: 'um dia', from: 27.72, to: 31.57 }, { name: 'o rosto', from: 31.57, to: 34.97 },
  { name: 'o que ela dizia', from: 34.97, to: 42.12 }, { name: 'pra sempre', from: 42.12, to: 46.02 }, { name: '93', from: 46.02, to: 49.3 },
  { name: 'a queda', from: 49.3, to: 54.1 }, { name: 'o que sobrou', from: 54.1, to: 56.78 }, { name: 'na internet', from: 56.78, to: 64.44 },
  { name: 'com ela, 12', from: 64.44, to: 66.64 }, { name: 'a última vez', from: 66.64, to: 70.74 }, { name: 'não manda', from: 70.74, to: 74.1 },
  { name: 'liga', from: 74.1, to: 75.6 }, { name: 'vai lá', from: 75.6, to: 78.15 }, { name: 'me avisa', from: 78.15, to: 81.7 }, { name: 'chamando', from: 81.7, to: DURATION },
];
window.CHECKS = [
  { t: 0, name: '60 + 24 = 84 anos', test: () => 60 + CONTA.anosAMais === 84 },
  { t: 0, name: 'dois por ano x 24 anos = 48', test: () => CONTA.visitasPorAno * CONTA.anosAMais === CONTA.visitasLonge },
  { t: 0, name: 'doze por ano x 24 anos = 288', test: () => 12 * CONTA.anosAMais === CONTA.visitasMes },
  { t: 0, name: '18 anos x 365 x 90% = 5.913', test: () => Math.round(18 * 365 * 0.9) === CONTA.ateSair },
  { t: 0, name: 'ladrilhos = soma dos dias', test: () => TL.length === CONTA.total && CONTA.ateSair + CONTA.jaFeitas + CONTA.visitasMes === CONTA.total },
  { t: 0, name: '93% aos 18', test: () => Math.round((100 * CONTA.ateSair) / CONTA.total) === CONTA.pct18 },
  { t: 0, name: 'sobram 288 ladrilhos', test: () => TL.filter((l) => l.t0 === Infinity).length === CONTA.visitasMes },
  { t: 0, name: '53h30 por semana = 116 dias por ano', test: () => Math.round((CONTA.horasPorSemana * 365 / 7) / 24) === CONTA.diasInternet },
];
