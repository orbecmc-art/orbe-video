/* DOCUMENTÁRIO CONTÍNUO — um plano-sequência sobre um mundo só (mapa, mesa, quadro). Tudo em código.
 *
 * Todo quadro é função pura do tempo: window.seek(t) pinta o instante t. O relógio é a VOZ (narracao.js).
 * O roteiro (roteiro.js ← roteiro.json) diz, por fala: UM herói (objeto, ano ou título), a câmera e os gestos
 * (círculo, troca, carimbo) presos à PALAVRA dita. O resto do mundo escurece.
 * Câmera: segura cada batida derivando devagar na direção do próximo movimento (nunca para morta), viaja com
 * velocidade contínua (Hermite), recua para viajar longe e mergulha de novo; handheld sutil; motion blur adaptativo.
 */
const Q = new URLSearchParams(location.search);
if (Q.has('render') || navigator.webdriver) document.body.classList.add('render');
const R = window.ROTEIRO, N = window.NARRACAO, MP = window.MAPA;
const W = +Q.get('w') || R.formato[0], H = +Q.get('h') || R.formato[1], FPS = R.fps || 30, DURATION = N.dur;
Object.assign(window, { DURATION, FPS });
const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const g = cv.getContext('2d', { willReadFrequently: true });
const { clamp, lerp, EASE: E } = M;
const u = Math.min(W, H) / 1080, C = R.paleta;
const F_SER = '"Cormorant Garamond"', F_MONO = '"IBM Plex Mono"', F_DOC = '"Courier Prime"', F_UI = '"Inter Tight"';
const norm = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
const sm = (p) => p * p * (3 - 2 * p);

// ── relógio da voz ──
const FAL = Object.fromEntries(N.falas.map((f) => [f.id, f]));
const tPal = (id, w) => { const f = FAL[id]; const k = f.palavras.findIndex((p) => norm(p.w).startsWith(norm(w))); return k >= 0 ? f.palavras[k].t0 : f.t0 + 0.3; };
const BT = R.falas.map((f, i) => ({ ...f, i, t0: FAL[f.id].t0, t1: FAL[f.id].t1 }));
BT.forEach((b, i) => { b.tn = i + 1 < BT.length ? BT[i + 1].t0 : DURATION; });
const beatAt = (t) => { let k = 0; for (let i = 0; i < BT.length; i++) if (t >= BT[i].t0 - 0.25) k = i; return BT[k]; };

// ── projeção (equiretangular corrigida pela latitude do centro) ──
const [LON0, LAT0] = R.mundo.centro, KX = Math.cos((LAT0 * Math.PI) / 180), S0 = (R.mundo.escala || 26) * u;
const PJ = (lon, lat) => [(lon - LON0) * KX * S0, -(lat - LAT0) * S0];
const caminho = (aneis) => { const p = new Path2D(); for (const a of aneis) { a.forEach(([lo, la], k) => { const [x, y] = PJ(lo, la); k ? p.lineTo(x, y) : p.moveTo(x, y); }); p.closePath(); } return p; };
const PAISES = (MP.paises || []).map((p) => ({ nome: p.nome, path: caminho(p.aneis) }));
const ESTADOS = (MP.estados || []).map((e) => {
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (const a of e.aneis) for (const [lo, la] of a) { const [x, y] = PJ(lo, la); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  return { nome: e.nome, path: caminho(e.aneis), cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
});

// ── objetos do mundo ──
const OB = Object.fromEntries(R.objetos.map((o) => [o.id, { ...o }]));
for (const o of Object.values(OB)) {
  if (o.lon != null) [o.x, o.y] = PJ(o.lon, o.lat);
  if (o.tipo === 'estado') { const e = ESTADOS.find((s) => norm(s.nome) === norm(o.nome)); Object.assign(o, { est: e, x: e ? e.cx : 0, y: e ? e.cy : 0 }); }
}
for (const o of Object.values(OB)) if (o.tipo === 'rota') { const a = OB[o.de], b = OB[o.ate]; Object.assign(o, { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }); }
// quando entra (1ª fala em que é herói ou acompanhante) e a que zoom foi desenhado (o tamanho em px vale nesse zoom)
for (const o of Object.values(OB)) {
  const b = BT.find((b) => b.heroi && (b.heroi.obj === o.id || (b.heroi.e || []).includes(o.id)));
  o.tin = b ? b.t0 + (b.heroi.obj === o.id ? 0.12 : 0.35) : 0; o.zh = b ? (b.camera.zoom || 1) : 2; o.beat = b;
  o.wd = ((o.larg || 300) * u) / o.zh;
}
// ── câmera: segura (com deriva) → viaja (Hermite, velocidade contínua) → mergulha ──
const alvo = (b) => (b.camera.obj ? [OB[b.camera.obj].x, OB[b.camera.obj].y + (['documento', 'recorte', 'planta'].includes(OB[b.camera.obj].tipo) ? OB[b.camera.obj].wd * 0.12 : 0)] : PJ(b.camera.lon, b.camera.lat));
const KF = BT.map((b) => { const [x, y] = alvo(b); return { t: b.t0 + 0.5, x, y, lz: Math.log(b.camera.zoom || 1) }; });
KF.unshift({ t: 0, x: KF[0].x + 30 * u, y: KF[0].y - 20 * u, lz: KF[0].lz - 0.22 });
KF.push({ t: DURATION + 0.2, x: KF[KF.length - 1].x, y: KF[KF.length - 1].y + 10 * u, lz: KF[KF.length - 1].lz - 0.25 });
const SEG = [];      // trechos: segura (deriva linear) e viaja (Hermite), costurados com a mesma velocidade
for (let i = 0; i < KF.length - 1; i++) {
  const a = KF[i], b = KF[i + 1], span = b.t - a.t;
  const zA = Math.exp(a.lz), dist = Math.hypot(b.x - a.x, b.y - a.y) * zA, viagem = clamp(0.85 + dist / (1900 * u), 0.9, 1.9);
  const tDep = Math.max(a.t + 0.15, b.t - Math.min(viagem, span * 0.8));
  // na espera a câmera NUNCA para: deriva na direção do próximo alvo (≥ 24 px/s na tela) e empurra 3,5% de zoom
  const hold = Math.max(0.15, tDep - a.t), dw0 = Math.hypot(b.x - a.x, b.y - a.y), dx = dw0 > 1e-6 ? (b.x - a.x) / dw0 : 0, dy = dw0 > 1e-6 ? (b.y - a.y) / dw0 : 1;
  const dw = Math.min(Math.max(dw0 * 0.25, (8 * u) / zA), Math.max(dw0 * 0.05, (24 * u * hold) / zA));
  const d = { x: a.x + dx * dw, y: a.y + dy * dw, lz: a.lz + (b.lz - a.lz) * 0.05 + 0.035 };
  SEG.push({ tipo: 'segura', t0: a.t, t1: tDep, A: a, B: d, dip: 0 });
  SEG.push({ tipo: 'viaja', t0: tDep, t1: b.t, A: d, B: b, dip: clamp(dist / (W * 1.4) - 0.25, 0, 0.75) });
}
for (let i = 0; i < SEG.length; i++) {      // velocidades: a da espera é constante; a viagem herda a da espera anterior e entrega a da próxima
  const s = SEG[i], h = Math.max(1e-3, s.t1 - s.t0);
  s.v = ['x', 'y', 'lz'].map((k) => (s.B[k] - s.A[k]) / h);
}
function camAt(t) {
  const s = SEG.find((s) => t >= s.t0 && t < s.t1) || (t < SEG[0].t0 ? SEG[0] : SEG[SEG.length - 1]);
  const h = Math.max(1e-3, s.t1 - s.t0), p = clamp((t - s.t0) / h), i = SEG.indexOf(s);
  if (s.tipo === 'segura') { const e = p; return { x: lerp(s.A.x, s.B.x, e), y: lerp(s.A.y, s.B.y, e), z: Math.exp(lerp(s.A.lz, s.B.lz, e)) }; }
  const v0 = SEG[i - 1] ? SEG[i - 1].v : [0, 0, 0], v1 = SEG[i + 1] ? SEG[i + 1].v : [0, 0, 0];
  const her = (a, b, m0, m1) => { const p2 = p * p, p3 = p2 * p; return (2 * p3 - 3 * p2 + 1) * a + (p3 - 2 * p2 + p) * m0 * h + (-2 * p3 + 3 * p2) * b + (p3 - p2) * m1 * h; };
  const x = her(s.A.x, s.B.x, v0[0], v1[0]), y = her(s.A.y, s.B.y, v0[1], v1[1]);
  const sn = Math.sin(Math.PI * p), lz = her(s.A.lz, s.B.lz, v0[2], v1[2]) - s.dip * sn * sn;      // recua para viajar, mergulha de novo (sen²: sem tranco nas pontas)
  return { x, y, z: Math.exp(lz) };
}
const velTela = (t) => { const a = camAt(t), b = camAt(t + 1 / FPS); return Math.hypot((b.x - a.x) * b.z, (b.y - a.y) * b.z) + Math.abs(Math.log(b.z / a.z)) * W * 0.5; };

// ── foco: o herói da fala acende, o resto escurece (transição de 0,45 s) ──
function heroisDe(b) { return b && b.heroi && b.heroi.obj ? [b.heroi.obj, ...(b.heroi.e || [])] : []; }
function foco(id, t) {
  const b = beatAt(t), pb = BT[b.i - 1], k = sm(clamp((t - (b.t0 - 0.25)) / 0.45));
  const on = (bb) => (bb ? (heroisDe(bb).includes(id) ? 1 : bb.heroi && (bb.heroi.ano || bb.heroi.titulo) ? 0.22 : 0.3) : 0.3);
  return lerp(on(pb), on(b), k);
}
const dimMapa = (t) => { const b = beatAt(t), pb = BT[b.i - 1], k = sm(clamp((t - (b.t0 - 0.25)) / 0.45)); const d = (bb) => (bb && bb.heroi && bb.heroi.ano ? 0.5 : bb && heroisDe(bb).some((id) => ['documento', 'recorte', 'planta', 'numero'].includes(OB[id].tipo)) ? 0.72 : 1); return lerp(d(pb), d(b), k); };

// ── texturas (semente fixa) ──
const texRuido = (() => { const S = 256, c2 = document.createElement('canvas'); c2.width = c2.height = S; const cg = c2.getContext('2d'), id = cg.createImageData(S, S), r = M.rng(19);
  for (let i = 0; i < S * S; i++) { const x = i % S, y = (i / S) | 0, v = 128 + 38 * (0.6 * M.noise2(x / 24, y / 24) + 0.4 * (r() * 2 - 1)); id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
  cg.putImageData(id, 0, 0); return c2; })();
let PAT = null;

// ── desenho: utilidades ──
const px = (v, z) => (v * u) / z;            // v px de TELA em unidades de mundo
const legivel = (o, z) => clamp((z / o.zh - 0.32) / 0.22);   // longe demais para ler → o texto do objeto some (não polui o recuo)
function texto(t, x, y, size, fam, w, cor, { al = 'center', tr = 0, base = 'alphabetic' } = {}) { g.font = `${w} ${size}px ${fam}`; g.textAlign = al; g.textBaseline = base; g.letterSpacing = `${tr * size}px`; g.fillStyle = cor; g.fillText(t, x, y); g.letterSpacing = '0px'; }
function linhasCinza(x, y, w, h, n, seed, cor) { const r = M.rng(seed); g.fillStyle = cor; for (let k = 0; k < n; k++) { const ww = w * (k === n - 1 ? 0.55 : 0.82 + 0.18 * r()); M.rrect(g, x, y + k * h, ww, h * 0.36, h * 0.18); g.fill(); } }
function queda(o, t) {    // o papel cai na mesa: grande e torto → assenta com mola; sombra encolhe
  const k = M.springZ(t - o.tin, 0.62, 2.6), a = clamp((t - o.tin) / 0.16);
  return { k, a, s: 1.16 - 0.16 * Math.min(1.05, k), r: ((o.rot || 0) + 5 * (1 - Math.min(1, k))) * Math.PI / 180 };
}
function circulo(cx, cy, rx, ry, p, z, seed = 3) {   // caneta vermelha desenhando uma elipse à mão
  if (p <= 0) return; g.save(); g.strokeStyle = C.acento; g.lineWidth = px(5, z); g.lineCap = 'round'; g.shadowColor = C.acento; g.shadowBlur = 10 * u; g.beginPath();
  const n = 64, fim = p * 1.12 * n;
  for (let k = 0; k <= fim; k++) { const a = -2.2 + (k / n) * 2 * Math.PI, w = 1 + 0.05 * M.noise1(k * 0.3 + seed); const x = cx + Math.cos(a) * rx * w, y = cy + Math.sin(a) * ry * w; k ? g.lineTo(x, y) : g.moveTo(x, y); }
  g.stroke(); g.restore();
}

// ── objetos ──
const DES = {};
DES.cidade = (o, t, f, z) => {
  const a = clamp((t - o.tin) / 0.3) * (o.discreto ? 0.6 : 1); if (a <= 0) return;
  g.save(); g.globalAlpha = a * lerp(0.35, 1, f); const r = px(o.chave ? 8 : 6, z), cor = o.chave ? C.acento : C.suave;
  if (f > 0.6) { const pu = (t * 0.8) % 1; g.strokeStyle = cor; g.globalAlpha *= (1 - pu) * 0.7; g.lineWidth = px(2, z); g.beginPath(); g.arc(o.x, o.y, r * (1 + 3 * pu), 0, 2 * Math.PI); g.stroke(); g.globalAlpha = a * lerp(0.35, 1, f); }
  g.shadowColor = cor; g.shadowBlur = 14 * u; g.fillStyle = cor; g.beginPath(); g.arc(o.x, o.y, r, 0, 2 * Math.PI); g.fill(); g.shadowBlur = 0;
  texto(o.rotulo, o.x + px(18, z), o.y + px(9, z), px(o.discreto ? 22 : 27, z), F_MONO, 600, o.chave ? C.acento : C.texto, { al: 'left', tr: 0.14 });
  g.restore();
};
DES.estado = (o, t, f, z) => {
  if (!o.est) return; const a = clamp((t - o.tin) / 0.6); if (a <= 0) return;
  g.save(); g.globalAlpha = a * f; g.fillStyle = C.acento; g.globalAlpha *= 0.13; g.fill(o.est.path); g.globalAlpha = a * f;
  g.strokeStyle = C.acento; g.lineWidth = px(2.2, z); g.shadowColor = C.acento; g.shadowBlur = 16 * u; g.stroke(o.est.path); g.shadowBlur = 0;
  if (o.rotulo) texto(o.rotulo, o.x, o.y - px(80, z), px(40, z), F_MONO, 600, C.texto, { tr: 0.32 });
  g.restore();
};
DES.documento = (o, t, f, z) => {
  if (t < o.tin) return; const q = queda(o, t), w = o.wd, h = w * 1.3;
  g.save(); g.globalAlpha = q.a * lerp(0.42, 1, f); g.translate(o.x, o.y); g.rotate(q.r); g.scale(q.s, q.s);
  g.shadowColor = 'rgba(0,0,0,.55)'; g.shadowBlur = (26 + 30 * (1 - Math.min(1, q.k))) * u; g.shadowOffsetY = (8 + 20 * (1 - Math.min(1, q.k))) * u;
  const gr = g.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2); gr.addColorStop(0, C.papel); gr.addColorStop(1, M.mixHex(C.papel, '#B9AE93', 0.35));
  g.fillStyle = gr; g.fillRect(-w / 2, -h / 2, w, h); g.shadowColor = 'transparent';
  g.globalAlpha *= 0.18; g.fillStyle = g.createPattern(texRuido, 'repeat'); g.globalCompositeOperation = 'multiply'; g.fillRect(-w / 2, -h / 2, w, h); g.globalCompositeOperation = 'source-over'; g.globalAlpha = q.a * lerp(0.42, 1, f);
  texto(o.titulo, 0, -h / 2 + w * 0.17, w * 0.068, F_DOC, 700, C.tinta, { tr: 0.08 });
  g.fillStyle = C.tinta; g.fillRect(-w * 0.36, -h / 2 + w * 0.22, w * 0.72, w * 0.006);
  if (o.campo) texto(o.campo, 0, -h * 0.06, w * 0.105, F_DOC, 700, C.tinta, { tr: 0.03 });
  linhasCinza(-w * 0.36, h * 0.06, w * 0.72, w * 0.062, o.linhas || 5, o.id.length * 7, 'rgba(29,27,24,.20)');
  const hc = o.beat && o.beat.heroi.circulo;
  if (hc) { const tw = tPal(o.beat.id, hc.palavra); circulo(0, -h * 0.09, w * 0.42, w * 0.11, E.premium(clamp((t - tw) / 0.5)), z, 5); }
  g.restore();
};
DES.recorte = (o, t, f, z) => {
  if (t < o.tin) return; const q = queda(o, t), w = o.wd, h = w * 0.92, r = M.rng(o.id.length * 13);
  g.save(); g.globalAlpha = q.a * lerp(0.42, 1, f); g.translate(o.x, o.y); g.rotate(q.r); g.scale(q.s, q.s);
  g.shadowColor = 'rgba(0,0,0,.55)'; g.shadowBlur = (24 + 30 * (1 - Math.min(1, q.k))) * u; g.shadowOffsetY = (8 + 18 * (1 - Math.min(1, q.k))) * u;
  g.beginPath(); const n = 26;       // borda rasgada
  for (let k = 0; k <= n; k++) g.lineTo(-w / 2 + (w * k) / n, -h / 2 + (r() - 0.5) * w * 0.018);
  for (let k = 0; k <= n; k++) g.lineTo(w / 2 + (r() - 0.5) * w * 0.018, -h / 2 + (h * k) / n);
  for (let k = n; k >= 0; k--) g.lineTo(-w / 2 + (w * k) / n, h / 2 + (r() - 0.5) * w * 0.022);
  for (let k = n; k >= 0; k--) g.lineTo(-w / 2 + (r() - 0.5) * w * 0.018, -h / 2 + (h * k) / n);
  g.closePath(); g.fillStyle = M.mixHex(C.papel, '#D8CDB0', 0.3); g.fill(); g.shadowColor = 'transparent';
  texto(o.cabeca, 0, -h / 2 + w * 0.15, w * 0.11, F_SER, 700, C.tinta, { tr: 0.04 });
  g.fillStyle = C.tinta; g.fillRect(-w * 0.43, -h / 2 + w * 0.19, w * 0.86, w * 0.005); g.fillRect(-w * 0.43, -h / 2 + w * 0.205, w * 0.86, w * 0.002);
  texto(o.data || '', 0, -h / 2 + w * 0.245, w * 0.032, F_MONO, 500, 'rgba(29,27,24,.7)', { tr: 0.2 });
  const yM = -h / 2 + w * 0.42; texto(o.manchete, 0, yM, w * 0.15, F_SER, 700, C.tinta, { tr: 0.02 });
  linhasCinza(-w * 0.43, yM + w * 0.09, w * 0.4, w * 0.05, 5, 3, 'rgba(29,27,24,.2)'); linhasCinza(w * 0.03, yM + w * 0.09, w * 0.4, w * 0.05, 5, 9, 'rgba(29,27,24,.2)');
  const bs = BT.filter((b) => b.heroi && b.heroi.obj === o.id);
  for (const b of bs) {
    if (b.heroi.circulo) { const tw = tPal(b.id, b.heroi.circulo.palavra); const fade = b.heroi.circulo && bs.some((x) => x.heroi.troca && t > x.t0) ? 0.0 : 1; g.save(); g.globalAlpha *= fade; circulo(0, yM - w * 0.05, w * 0.44, w * 0.11, E.premium(clamp((t - tw) / 0.5)), z, 2); g.restore(); }
    if (b.heroi.troca) {
      const tw = tPal(b.id, b.heroi.troca.palavra), ps = E.premium(clamp((t - (tw - 0.3)) / 0.25));
      if (ps > 0) { g.save(); g.strokeStyle = C.acento; g.lineWidth = w * 0.014; g.lineCap = 'round'; g.beginPath(); g.moveTo(-w * 0.38, yM - w * 0.04); g.lineTo(-w * 0.38 + w * 0.76 * ps, yM - w * 0.06); g.stroke(); g.restore(); }
      const k = M.springZ(t - tw, 0.5, 3.2);
      if (t >= tw) { g.save(); g.translate(w * 0.06, yM + w * 0.2); g.rotate(-0.1); const sc = 1.5 - 0.5 * Math.min(1.05, k); g.scale(sc, sc); g.globalAlpha *= clamp((t - tw) / 0.08);
        g.strokeStyle = C.acento; g.lineWidth = w * 0.012; g.strokeRect(-w * 0.36, -w * 0.1, w * 0.72, w * 0.16); texto(o.troca, 0, w * 0.015, w * 0.11, F_UI, 800, C.acento, { tr: 0.06 }); g.restore(); }
    }
  }
  g.restore();
};
DES.planta = (o, t, f, z) => {
  if (t < o.tin) return; const q = queda(o, t), w = o.wd, h = w * 0.82;
  g.save(); g.globalAlpha = q.a * lerp(0.42, 1, f); g.translate(o.x, o.y); g.rotate(q.r); g.scale(q.s, q.s);
  g.shadowColor = 'rgba(0,0,0,.55)'; g.shadowBlur = 30 * u; g.shadowOffsetY = 12 * u; g.fillStyle = C.planta; g.fillRect(-w / 2, -h / 2, w, h); g.shadowColor = 'transparent';
  g.strokeStyle = 'rgba(255,255,255,.07)'; g.lineWidth = w * 0.002; for (let k = -10; k <= 10; k++) { g.beginPath(); g.moveTo((k * w) / 20, -h / 2); g.lineTo((k * w) / 20, h / 2); g.stroke(); g.beginPath(); g.moveTo(-w / 2, (k * h) / 20); g.lineTo(w / 2, (k * h) / 20); g.stroke(); }
  const d = E.move(clamp((t - o.tin - 0.35) / 1.5)), cx = 0, cy = -h * 0.08;
  g.strokeStyle = 'rgba(235,242,250,.85)'; g.lineWidth = w * 0.006; g.lineCap = 'round';
  g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx, cy + h * 0.46 * d); g.stroke();      // eixo
  for (const a of [-1.15, -0.62, 0, 0.62, 1.15]) { g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(a) * w * 0.42 * d, cy - Math.cos(a) * h * 0.4 * d); g.stroke(); }
  for (const rr of [0.12, 0.22, 0.32]) { g.beginPath(); g.arc(cx, cy, w * rr, Math.PI * (1.05), Math.PI * (1.05 + 0.9 * d)); g.stroke(); }
  g.fillStyle = 'rgba(235,242,250,.9)'; g.beginPath(); g.arc(cx, cy, w * 0.018, 0, 2 * Math.PI); g.fill();
  g.restore();
  if (o.rotulo && t > o.tin + 0.5) { g.save(); g.globalAlpha = clamp((t - o.tin - 0.5) / 0.3) * lerp(0.4, 1, f) * legivel(o, z); texto(o.rotulo, o.x, o.y + h * 0.5 + px(56, z), px(30, z), F_MONO, 600, C.texto, { tr: 0.12 }); g.restore(); }
};
DES.rota = (o, t, f, z) => {
  if (t < o.tin) return; const a = OB[o.de], b = OB[o.ate], p = E.move(clamp((t - o.tin) / 1.4));
  const mx = (a.x + b.x) / 2 - (b.y - a.y) * 0.18, my = (a.y + b.y) / 2 + (b.x - a.x) * 0.18;
  const pt = (s) => [(1 - s) * (1 - s) * a.x + 2 * (1 - s) * s * mx + s * s * b.x, (1 - s) * (1 - s) * a.y + 2 * (1 - s) * s * my + s * s * b.y];
  g.save(); g.globalAlpha = lerp(0.4, 1, f); g.strokeStyle = C.acento; g.lineWidth = px(3, z); g.setLineDash([px(14, z), px(10, z)]); g.lineDashOffset = -t * px(30, z);
  g.shadowColor = C.acento; g.shadowBlur = 12 * u; g.beginPath(); for (let k = 0; k <= 60 * p; k++) { const [x, y] = pt(k / 60); k ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); g.setLineDash([]);
  const [hx, hy] = pt(p); g.fillStyle = '#FFE9E2'; g.beginPath(); g.arc(hx, hy, px(7, z), 0, 2 * Math.PI); g.fill(); g.restore();
};
DES.numero = (o, t, f, z) => {
  if (t < o.tin) return; const k = M.springZ(t - o.tin, 0.7, 2.4), w = o.wd;
  g.save(); g.globalAlpha = clamp((t - o.tin) / 0.2) * lerp(0.35, 1, f); g.translate(o.x, o.y); g.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k);
  g.globalAlpha *= 0.25 + 0.75 * legivel(o, z);
  texto(o.valor, 0, 0, w * 0.62, F_SER, 700, C.texto); texto(o.rotulo, 0, w * 0.16, w * 0.052, F_MONO, 600, C.suave, { tr: 0.14 });
  const hc = o.beat && o.beat.heroi.carimbo;
  if (hc && o.carimbo) { const tw = tPal(o.beat.id, hc.palavra); if (t >= tw) { const kk = M.springZ(t - tw, 0.45, 3.4), sc = 1.7 - 0.7 * Math.min(1.06, kk);
    g.save(); g.translate(w * 0.05, w * 0.33); g.rotate(-0.12); g.scale(sc, sc); g.globalAlpha *= clamp((t - tw) / 0.06) * 0.92;
    g.strokeStyle = C.acento; g.lineWidth = w * 0.011; g.strokeRect(-w * 0.47, -w * 0.075, w * 0.94, w * 0.13); g.strokeRect(-w * 0.45, -w * 0.06, w * 0.9, w * 0.1);
    texto(o.carimbo, 0, w * 0.012, w * 0.052, F_UI, 800, C.acento, { tr: 0.08 }); g.restore(); } }
  g.restore();
};

// ── mapa ──
function mapa(t, z) {
  const d = dimMapa(t);
  g.fillStyle = C.mar; g.fillRect(-1e5, -1e5, 2e5, 2e5);
  g.save(); g.globalAlpha = 0.07 * d; g.strokeStyle = C.suave; g.lineWidth = px(1, z);
  for (let lo = -90; lo <= -20; lo += 5) { const [x0, y0] = PJ(lo, 15), [x1, y1] = PJ(lo, -60); g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); }
  for (let la = -60; la <= 15; la += 5) { const [x0, y0] = PJ(-95, la), [x1, y1] = PJ(-15, la); g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); }
  g.restore();
  g.save(); g.fillStyle = M.mixHex(C.terra, C.mar, 1 - d); for (const p of PAISES) g.fill(p.path);
  if (!PAT) PAT = g.createPattern(texRuido, 'repeat');
  g.globalAlpha = 0.10; g.globalCompositeOperation = 'overlay'; g.fillStyle = PAT; for (const p of PAISES) g.fill(p.path); g.globalCompositeOperation = 'source-over';
  g.globalAlpha = 0.9 * d; g.strokeStyle = C.borda; g.lineWidth = px(1.4, z); for (const p of PAISES) g.stroke(p.path);
  g.globalAlpha = 0.55 * d; g.strokeStyle = C.estado; g.lineWidth = px(1, z); for (const e of ESTADOS) g.stroke(e.path);
  g.restore();
}

// ── tela: ano, título, régua do tempo ──
function anoHeroi(t) {
  for (const b of BT) {
    if (!b.heroi.ano) continue; const a = clamp((t - b.t0 + 0.05) / 0.55), sai = clamp((t - (b.tn - 0.45)) / 0.4); if (a <= 0 || sai >= 1) continue;
    const e = E.premium(a), al = e * (1 - sai), y = H * 0.40;
    g.save(); g.globalAlpha = al; g.filter = a < 1 ? `blur(${((1 - e) * 10 * u).toFixed(1)}px)` : 'none';
    g.translate(W / 2, y); g.scale(1.06 - 0.06 * e, 1.06 - 0.06 * e);
    texto(b.heroi.ano.split('').join(' '), 0, 0, 200 * u, F_SER, 600, C.texto, { tr: 0.06, base: 'middle' });
    g.filter = 'none'; g.fillStyle = C.acento; const L = 150 * u * e; g.fillRect(-W * 0.5 + 40 * u, -2 * u, L, 3 * u); g.fillRect(W * 0.5 - 40 * u - L, -2 * u, L, 3 * u);
    g.restore();
  }
  for (const b of BT) {
    if (!b.heroi.titulo) continue; const a = clamp((t - b.t0 - 0.4) / 0.8); if (a <= 0) continue; const e = E.premium(a);
    g.save(); g.globalAlpha = e; g.filter = a < 1 ? `blur(${((1 - e) * 8 * u).toFixed(1)}px)` : 'none';
    const tt = b.heroi.titulo, tsz = Math.min(128 * u, M.fitSize(g, tt, W * 0.8, 128 * u, 600, F_SER, 40 * u) * 0.86);
    texto(tt, W / 2, H * 0.38, tsz, F_SER, 600, C.texto, { tr: 0.12, base: 'middle' });
    g.filter = 'none'; g.fillStyle = C.acento; g.fillRect(W / 2 - 110 * u * e, H * 0.38 + 92 * u, 220 * u * e, 3 * u); g.restore();
  }
}
const ANOS = BT.filter((b) => b.ano).map((b) => ({ t: b.t0, ano: b.ano }));
function regua(t) {
  const [a0, a1] = R.mundo.anos || [1930, 2010], y = H - 168 * u, x0 = 90 * u, x1 = W - 90 * u, X = (a) => x0 + ((a - a0) / (a1 - a0)) * (x1 - x0);
  let cur = ANOS.length ? ANOS[0].ano : a0; for (let k = 0; k < ANOS.length; k++) { const A = ANOS[k]; if (t >= A.t) { const prev = k ? ANOS[k - 1].ano : A.ano; cur = lerp(prev, A.ano, E.move(clamp((t - A.t) / 0.9))); } }
  const ap = clamp(t / 0.8); g.save(); g.globalAlpha = 0.85 * ap;
  for (let a = a0; a <= a1; a++) { const maj = a % 10 === 0; g.fillStyle = maj ? 'rgba(232,226,210,.5)' : 'rgba(232,226,210,.18)'; g.fillRect(X(a) - u, y - (maj ? 16 : 7) * u, 2 * u, (maj ? 16 : 7) * u);
    if (maj) texto(String(a), X(a), y + 30 * u, 19 * u, F_MONO, 500, 'rgba(232,226,210,.45)', { tr: 0.08 }); }
  g.fillStyle = C.acento; g.shadowColor = C.acento; g.shadowBlur = 12 * u; g.fillRect(X(cur) - 1.5 * u, y - 34 * u, 3 * u, 40 * u); g.shadowBlur = 0;
  texto(String(Math.round(cur)), X(cur), y - 46 * u, 24 * u, F_MONO, 600, C.acento, { tr: 0.1 });
  g.restore();
}

// ── quadro ──
function pinta(t) {
  const cm = camAt(t), [hx, hy, hr] = M.handheld(t, 5 * u, 0.33, 7), z = cm.z * S0 / S0;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none'; g.fillStyle = C.mar; g.fillRect(0, 0, W, H);
  g.setTransform(1, 0, 0, 1, 0, 0); g.translate(W / 2 + hx, H / 2 + hy); g.rotate(hr * 2); g.scale(z, z); g.translate(-cm.x, -cm.y);
  mapa(t, z);
  const ordem = ['estado', 'rota', 'cidade', 'planta', 'documento', 'recorte', 'numero'];
  for (const tp of ordem) for (const o of Object.values(OB)) if (o.tipo === tp && DES[tp]) DES[tp](o, t, foco(o.id, t), z);
  g.setTransform(1, 0, 0, 1, 0, 0);
  anoHeroi(t); regua(t);
  M.vignette(g, W, H, 0.62); M.grain(g, W, H, t, 0.05, 14);
}
window.seek = (t) => { pinta(clamp(Number.isFinite(t) ? t : 0, 0, DURATION - 1e-4)); return true; };
window.renderAt = window.seek;
window.SUB_AT = (t) => { const v = velTela(t); return v > 22 * u ? 12 : v > 10 * u ? 8 : v > 4 * u ? 4 : 2; };
window.CUTS = [];
window.SHOTS = BT.map((b) => ({ name: `${b.id} ${(b.heroi.obj || b.heroi.ano || b.heroi.titulo || '')}`, from: Math.max(0, b.t0 - 0.25), to: b.tn - 0.25, out: 'flow' }));
window.CUES = () => {
  const cs = [];
  for (const b of BT) {
    if (b.heroi.ano) cs.push({ t: b.t0 + 0.05, type: 'boom', gain: 0.45 });
    if (b.heroi.titulo) cs.push({ t: b.t0 + 0.45, type: 'chime', gain: 0.45 });
    const o = b.heroi.obj && OB[b.heroi.obj];
    if (o && o.tin >= b.t0 && ['documento', 'recorte', 'planta'].includes(o.tipo)) cs.push({ t: o.tin + 0.18, type: 'paper', gain: 0.7 });
    if (o && o.tipo === 'numero' && o.tin >= b.t0) cs.push({ t: o.tin + 0.05, type: 'thump', gain: 0.55 });
    if (o && o.tipo === 'rota') cs.push({ t: o.tin + 0.05, type: 'whoosh', gain: 0.45 }, { t: o.tin + 1.4, type: 'tick', gain: 0.5 });
    if (b.heroi.circulo) cs.push({ t: tPal(b.id, b.heroi.circulo.palavra) + 0.05, type: 'marker', gain: 0.6 });
    if (b.heroi.troca) { const tw = tPal(b.id, b.heroi.troca.palavra); cs.push({ t: tw - 0.3, type: 'swish', gain: 0.45 }, { t: tw, type: 'impact', gain: 0.75 }); }
    if (b.heroi.carimbo) cs.push({ t: tPal(b.id, b.heroi.carimbo.palavra), type: 'impact', gain: 0.85 });
  }
  for (const s of SEG) if (s.tipo === 'viaja' && s.dip > 0.15) cs.push({ t: (s.t0 + s.t1) / 2 - 0.25, type: 'whoosh', gain: 0.28 });
  return cs.sort((a, b) => a.t - b.t);
};
// ── checagens: câmera que para ou dá tranco, herói único, frase repetida, tipo pequeno ──
window.CAMERA = () => {
  const out = []; let parado = 0, ini = 0, vAnt = null;
  for (let t = 0; t < DURATION - 0.4; t += 1 / FPS) {
    const v = velTela(t);
    if (v < 0.35 * u) { if (!parado) ini = t; parado += 1 / FPS; } else { if (parado > 0.45) out.push(`câmera PARADA ${parado.toFixed(2)}s em ${ini.toFixed(2)}s`); parado = 0; }
    if (vAnt != null && Math.abs(v - vAnt) > 9 * u) out.push(`TRANCO em ${t.toFixed(2)}s (${vAnt.toFixed(1)} → ${v.toFixed(1)} px/quadro)`);
    vAnt = v;
  }
  return out;
};
window.VALIDATE = () => {
  const out = [...window.CAMERA()];
  for (const b of BT) { const n = ['obj', 'ano', 'titulo'].filter((k) => b.heroi && b.heroi[k]).length; if (n !== 1) out.push(`${b.id}: precisa de UM herói (tem ${n})`); }
  const vistos = {};
  for (const o of Object.values(OB)) for (const s of [o.titulo, o.campo, ['cidade', 'estado'].includes(o.tipo) ? null : o.rotulo, o.manchete, o.troca, o.valor, o.carimbo].filter(Boolean)) { const k = norm(s); if (vistos[k]) out.push(`texto repetido na tela: "${s}"`); vistos[k] = 1; }
  for (const o of Object.values(OB)) { if (['documento', 'recorte'].includes(o.tipo)) { const tela = o.wd * 0.068 * o.zh / u; if (tela < 18) out.push(`${o.id}: título do papel com ${tela.toFixed(0)}px na tela — aumente larg ou o zoom`); } }
  return out;
};
window.ready = document.fonts.ready.then(() => Promise.all([`700 60px ${F_SER}`, `600 60px ${F_SER}`, `600 60px ${F_MONO}`, `500 60px ${F_MONO}`, `700 60px ${F_DOC}`, `800 60px ${F_UI}`].map((f) => document.fonts.load(f, 'aãçéÂ0').catch(() => 0))));
window.ready.then(() => window.seek(+Q.get('t') || 3));
