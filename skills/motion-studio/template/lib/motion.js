/* motion.js — biblioteca de movimento determinístico para filmes em código.
 * Tudo aqui é FUNÇÃO PURA DO TEMPO: mesma entrada → mesmo pixel, em qualquer ordem de frames.
 * Script clássico (não ES module) para funcionar via file:// no Chromium headless.
 * Expõe window.M.
 */
(function (root) {
  'use strict';

  // ───────────────────────── básicos ─────────────────────────
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const invLerp = (a, b, x) => clamp((x - a) / (b - a));
  const remap = (x, a, b, c, d) => lerp(c, d, invLerp(a, b, x));
  const smooth = (p) => p * p * (3 - 2 * p);
  const mix = (a, b, p) => (typeof a === 'number' ? lerp(a, b, p) : a.map((v, i) => lerp(v, b[i], p)));

  // Easings — use para CÂMERA e opacidade. Para objetos com massa, use springs.
  const ease = {
    linear: (p) => p,
    inCubic: (p) => p * p * p,
    outCubic: (p) => 1 - Math.pow(1 - p, 3),
    outQuad: (p) => 1 - (1 - p) * (1 - p),
    inOutCubic: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    outQuint: (p) => 1 - Math.pow(1 - p, 5),
    outExpo: (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
    inOutExpo: (p) => (p <= 0 ? 0 : p >= 1 ? 1 : p < 0.5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2),
    inOutSine: (p) => -(Math.cos(Math.PI * p) - 1) / 2,
  };
  // tween(t, t0, dur, easing) → 0..1
  const tween = (t, t0, dur, e = ease.inOutCubic) => e(clamp((t - t0) / dur));

  // cubic-bezier igual ao CSS (resolve x→t por Newton + bisseção). Pura e determinística.
  function cubicBezier(x1, y1, x2, y2) {
    const A = (a, b) => 1 - 3 * b + 3 * a, Bc = (a, b) => 3 * b - 6 * a, Cc = (a) => 3 * a;
    const f = (t, a, b) => ((A(a, b) * t + Bc(a, b)) * t + Cc(a)) * t;
    const df = (t, a, b) => 3 * A(a, b) * t * t + 2 * Bc(a, b) * t + Cc(a);
    return (x) => {
      if (x <= 0) return 0; if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) { const d = df(t, x1, x2); if (Math.abs(d) < 1e-6) break; const e = f(t, x1, x2) - x; if (Math.abs(e) < 1e-6) return f(t, y1, y2); t -= e / d; }
      let lo = 0, hi = 1; t = x;
      for (let i = 0; i < 30; i++) { const v = f(t, x1, x2); if (Math.abs(v - x) < 1e-6) break; if (v < x) lo = t; else hi = t; t = (lo + hi) / 2; }
      return f(t, y1, y2);
    };
  }
  // TOKENS de movimento — um arquivo, nada de número solto no código das cenas.
  // Easings (referência easings.net). Entra com out, sai com in (40–50% mais curto), atravessa com inOut.
  const EASE = {
    enter: cubicBezier(0.16, 1, 0.3, 1),     // ease-out-expo — texto e logo
    premium: cubicBezier(0.22, 1, 0.36, 1),  // ease-out-quint — entradas premium
    move: cubicBezier(0.76, 0, 0.24, 1),     // ease-in-out-quart — movimentos e câmera
    exit: cubicBezier(0.7, 0, 0.84, 0),      // ease-in-expo — saídas rápidas
    pop: cubicBezier(0.34, 1.56, 0.64, 1),   // ease-out-back — pop com overshoot (nunca em texto)
    linear: (p) => p,                        // só rotação, progresso, fase de loop
  };
  const MS = { feedback: 0.15, move: 0.4, hero: 0.75, exit: 0.24 };          // segundos
  const STAGGER = { letter: 0.03, word: 0.09, item: 0.06 };                  // segundos

  // ───────────────────────── springs (forma fechada) ─────────────────────────
  // Resposta ao degrau 0→1 de um oscilador massa-mola amortecido (massa = 1).
  // k = rigidez, d = amortecimento. ζ = d / (2√k).
  function spring(t, k = 170, d = 26) {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z < 1) {
      const wd = w0 * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + ((z * w0) / wd) * Math.sin(wd * t));
    }
    if (z === 1) return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
    // superamortecido (ζ > 1): duas raízes reais
    const s = w0 * Math.sqrt(z * z - 1);
    const r1 = -z * w0 + s, r2 = -z * w0 - s;
    return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
  }

  // Presets calibrados. Overshoot aproximado entre parênteses.
  const SPRING = {
    snappy: [320, 30],  // UI: botões, toggles, bordas de ataque (~1%)
    ui: [260, 28],      // padrão de UI (~0.5%)
    smooth: [170, 26],  // cards, containers, câmera (crítico, 0%)
    heavy: [90, 20],    // tipografia grande, logo, objetos 3D (0%)
    playful: [220, 14], // mascotes, stickers (overshoot visível ~20%)
    wobbly: [180, 9],   // gag/cômico (~40%) — use com parcimônia
  };
  const sp = (t, preset = 'smooth') => spring(t, ...SPRING[preset]);
  // Spring pela linguagem universal: ζ (razão de amortecimento) e frequência em Hz.
  // ζ 1 = sem quique · 0,7–0,85 premium · 0,4–0,6 brincalhão · <0,3 cartoon. Posição/tamanho podem quicar; opacidade/cor nunca.
  const springZ = (t, zeta = 0.75, hz = 2) => { const w = 2 * Math.PI * hz; return spring(t, w * w, 2 * zeta * w); };
  // Converte números de qualquer biblioteca (stiffness k, damping d, mass m) para ζ — Remotion padrão (100,10,1) = 0,5
  const dampingRatio = (k, d, m = 1) => d / (2 * Math.sqrt(k * m));

  // Valor com vários alvos ao longo do tempo: soma de uma mola por mudança.
  // keys: [[tempo, valor], ...] ordenado. Contínuo e sem simular frames anteriores.
  function track(t, keys, preset = 'smooth') {
    const [k, d] = typeof preset === 'string' ? SPRING[preset] : preset;
    let v = keys[0][1];
    for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
    return v;
  }
  // track para vetores/cores: keys: [[tempo, [a,b,c]], ...]
  function trackV(t, keys, preset = 'smooth') {
    return keys[0][1].map((_, j) => track(t, keys.map(([tt, v]) => [tt, v[j]]), preset));
  }

  // Indicador líquido: borda de ataque mais rígida que a de fuga → estica no movimento.
  function stretch(t, stops, width) {
    const lead = track(t, stops, [320, 30]);
    const trail = track(t, stops, [140, 22]);
    return { left: Math.min(lead, trail), right: Math.max(lead, trail) + width };
  }

  // Conteúdo dentro de container que se transforma: entra depois do morph começar, sai antes do próximo.
  const swapAlpha = (t, tIn, tOut, fadeIn = 0.12, fadeOut = 0.1, delay = 0.08) =>
    Math.min(clamp((t - tIn - delay) / fadeIn), clamp((tOut - fadeOut - t) / fadeOut));

  // Atraso em cascata: índice i de n, espalhado em `spread` segundos, com ordem opcional ('center' | 'random' | 'linear' | 'reverse')
  function stagger(i, n, spread, order = 'linear', seed = 1) {
    if (n <= 1) return 0;
    let p = i / (n - 1);
    if (order === 'reverse') p = 1 - p;
    if (order === 'center') p = Math.abs(p - 0.5) * 2;
    if (order === 'random') p = hash1(i * 13.37 + seed);
    return p * spread;
  }

  const loopT = (t, dur) => ((t % dur) + dur) % dur;
  // LOOPS: tudo dirigido por phase = t/DUR com ciclos INTEIROS. Ruído orgânico que volta ao início: amostre num círculo.
  const loopNoise = (phase, radius = 1, seed = 0) => noise2(Math.cos(phase * 2 * Math.PI) * radius + seed * 17.3, Math.sin(phase * 2 * Math.PI) * radius + seed * 31.7);

  // Tempo CENTRAL do frame (ignora os subframes do motion blur). Use para tudo que é DISCRETO:
  // contadores, troca de texto, índice de lista, frames "on twos". Senão o blur mistura dígitos ("4̶3̶2").
  const frameT = (t) => (typeof window !== 'undefined' && window.__frameT != null ? window.__frameT : t);
  // Contador inteiro sem borrão: valor final × progresso calculado no tempo do frame
  const count = (t, to, t0, preset = 'heavy', from = 0) => Math.round(from + (to - from) * sp(frameT(t) - t0, preset));
  // Animação em "twos" (12 fps) para personagens/traço desenhado — câmera continua em "ones"
  const onTwos = (t, fps = 12) => Math.floor(frameT(t) * fps) / fps;

  // ───────────────────────── aleatoriedade determinística ─────────────────────────
  function rng(seed) { // mulberry32
    return () => {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash1(x) { const s = Math.sin(x * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
  // value noise 1D/2D suave, determinístico
  function noise1(x) { const i = Math.floor(x), f = x - i; return lerp(hash1(i), hash1(i + 1), smooth(f)) * 2 - 1; }
  function noise2(x, y) {
    const h = (a, b) => hash1(a * 157.31 + b * 113.97);
    const ix = Math.floor(x), iy = Math.floor(y), fx = smooth(x - ix), fy = smooth(y - iy);
    return lerp(lerp(h(ix, iy), h(ix + 1, iy), fx), lerp(h(ix, iy + 1), h(ix + 1, iy + 1), fx), fy) * 2 - 1;
  }
  const fbm = (x, y = 0, oct = 4) => { let a = 0.5, s = 0; for (let o = 0; o < oct; o++) { s += a * noise2(x, y); x *= 2; y *= 2; a *= 0.5; } return s; };
  // tremor de câmera de mão: amplitude em px, freq em Hz
  const handheld = (t, amp = 6, hz = 0.7, seed = 0) => [amp * noise1(t * hz + seed), amp * noise1(t * hz + seed + 91.3), amp * 0.002 * noise1(t * hz * 0.7 + seed + 47)];

  // ───────────────────────── batida / música ─────────────────────────
  // BEATS = { bpm, beats:[], downbeats:[], hits:[] } (de beats.json). Sem arquivo, gere uma grade.
  const grid = (bpm, bars, beatsPerBar = 4, offset = 0) => {
    const spb = 60 / bpm, beats = [];
    for (let i = 0; i < bars * beatsPerBar; i++) beats.push(+(offset + i * spb).toFixed(4));
    return { bpm, beats, downbeats: beats.filter((_, i) => i % beatsPerBar === 0), hits: [] };
  };
  // Pulso que decai após cada tempo em `times` (para "bater" escala/brilho no ritmo).
  function pulse(t, times, decay = 8) {
    let v = 0;
    for (const bt of times) { if (bt > t) break; v = Math.max(v, Math.exp(-(t - bt) * decay)); }
    return v;
  }
  // Índice do último tempo ≤ t
  const beatIndex = (t, times) => { let i = -1; for (let j = 0; j < times.length && times[j] <= t; j++) i = j; return i; };

  // ───────────────────────── layout responsivo ─────────────────────────
  // Escreva cenas em unidades relativas, nunca em pixels fixos. Um timeline → 9:16, 1:1, 16:9.
  function layout(W, H) {
    const u = Math.min(W, H) / 1080; // 1u = 1px em 1080 de lado curto
    const portrait = H > W * 1.2, landscape = W > H * 1.2;
    // Zonas seguras (Reels/TikTok/Shorts): topo ~14%, base ~22% ocupadas pela UI do app
    const safe = portrait ? { top: H * 0.14, bottom: H * 0.78, left: W * 0.07, right: W * 0.93 }
                          : { top: H * 0.08, bottom: H * 0.92, left: W * 0.06, right: W * 0.94 };
    return { W, H, u, cx: W / 2, cy: H / 2, portrait, landscape, square: !portrait && !landscape, safe,
      // tamanho de tipografia por papel, já ajustado ao formato
      type: { hero: (portrait ? 150 : landscape ? 170 : 160) * u, title: 96 * u, body: 44 * u, label: 30 * u } };
  }

  // ───────────────────────── tipografia ─────────────────────────
  function setFont(g, weight, size, family) { g.font = `${weight} ${Math.round(size)}px ${family}`; }
  // Reduz o tamanho até caber em maxW
  function fitSize(g, text, maxW, size, weight, family, min = 8) {
    let s = size; setFont(g, weight, s, family);
    while (s > min && g.measureText(text).width > maxW) { s *= 0.95; setFont(g, weight, s, family); }
    return s;
  }
  // Quebra em linhas por largura
  function wrap(g, text, maxW) {
    const words = text.split(/\s+/), lines = []; let line = '';
    for (const w of words) { const test = line ? line + ' ' + w : w; if (g.measureText(test).width > maxW && line) { lines.push(line); line = w; } else line = test; }
    if (line) lines.push(line); return lines;
  }
  /* Tipografia cinética por caractere/palavra.
   * opts: { x, y, size, weight, family, color, align:'center'|'left', tracking (em), by:'char'|'word',
   *         t0, spread (s), preset, from:{y, scale, rot, blur}, exit:{t, spread} }
   */
  function kinetic(g, t, text, o) {
    const by = o.by || 'char', units = by === 'char' ? [...text] : text.split(' ');
    setFont(g, o.weight || 700, o.size, o.family);
    g.letterSpacing = ((o.tracking || 0) * o.size).toFixed(2) + 'px';
    const sepW = by === 'word' ? g.measureText(' ').width : 0;
    const widths = units.map((u) => g.measureText(u).width);
    const total = widths.reduce((a, b) => a + b, 0) + sepW * (units.length - 1);
    let x = o.align === 'left' ? o.x : o.x - total / 2;
    const from = Object.assign({ y: 0.6, scale: 1, rot: 0, blur: 0 }, o.from || {});
    g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    units.forEach((ch, i) => {
      const d = stagger(i, units.length, o.spread ?? 0.35, o.order || 'linear');
      const p = sp(t - (o.t0 || 0) - d, o.preset || 'snappy');
      let a = clamp(p * 1.6);
      let exitP = 0;
      if (o.exit) { exitP = tween(t, o.exit.t + stagger(i, units.length, o.exit.spread ?? 0.2), 0.35, ease.inCubic); a *= 1 - exitP; }
      if (a > 0.001) {
        g.save();
        g.globalAlpha *= a;
        const cx = x + widths[i] / 2;
        g.translate(cx, o.y + (1 - p) * from.y * o.size - exitP * 0.4 * o.size);
        g.rotate((1 - p) * from.rot);
        const s = lerp(from.scale, 1, p); g.scale(s, s);
        if (from.blur) g.filter = `blur(${((1 - p) * from.blur).toFixed(2)}px)`;
        g.fillStyle = o.color || '#fff';
        g.fillText(ch, -widths[i] / 2, 0);
        g.restore();
      }
      x += widths[i] + sepW;
    });
    g.letterSpacing = '0px';
    return total;
  }
  // Revelação por máscara (texto sobe de dentro de uma linha) — clássico de motion
  function maskReveal(g, t, text, o) {
    setFont(g, o.weight || 800, o.size, o.family);
    g.textAlign = o.align || 'center'; g.textBaseline = 'alphabetic';
    const w = g.measureText(text).width, x0 = g.textAlign === 'center' ? o.x - w / 2 : o.x;
    const p = sp(t - (o.t0 || 0), o.preset || 'heavy');
    g.save(); g.beginPath(); g.rect(x0 - o.size, o.y - o.size * 1.05, w + o.size * 2, o.size * 1.35); g.clip();
    g.fillStyle = o.color || '#fff'; g.fillText(text, o.x, o.y + (1 - p) * o.size * 1.2); g.restore();
    return w;
  }

  // ───────────────────────── formas ─────────────────────────
  function rrect(g, x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
  }
  // Desenha path parcialmente (0..1) — linhas que se "desenham"
  function drawPartial(g, pts, p) {
    if (pts.length < 2 || p <= 0) return;
    const segs = []; let L = 0;
    for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); segs.push(l); L += l; }
    let rem = L * clamp(p); g.beginPath(); g.moveTo(...pts[0]);
    for (let i = 1; i < pts.length && rem > 0; i++) {
      const f = Math.min(1, rem / segs[i - 1]);
      g.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)); rem -= segs[i - 1];
    }
    g.stroke();
  }
  // Cursor de sistema (seta) com clique (escala) — p.ex. cursor(g, x, y, pressAmount)
  function cursor(g, x, y, press = 0, s = 1, fill = '#111', stroke = '#fff') {
    g.save(); g.translate(x, y); g.scale(s * (1 - 0.12 * press), s * (1 - 0.12 * press));
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 34); g.lineTo(9, 26); g.lineTo(15, 40); g.lineTo(21, 37); g.lineTo(15, 24); g.lineTo(26, 24); g.closePath();
    g.lineJoin = 'round'; g.lineWidth = 3; g.strokeStyle = stroke; g.stroke(); g.fillStyle = fill; g.fill(); g.restore();
  }
  // Clique: press 0→1→0 em ~0.18s a partir de tClick
  const press = (t, tClick) => { const x = t - tClick; return x < 0 || x > 0.22 ? 0 : Math.sin((x / 0.22) * Math.PI); };

  // ───────────────────────── câmera ─────────────────────────
  // cam = {x, y, zoom, rot} em coords do mundo; centraliza o ponto (x,y) no frame
  function camera(g, L, cam) {
    g.translate(L.cx, L.cy); g.rotate(cam.rot || 0); g.scale(cam.zoom || 1, cam.zoom || 1); g.translate(-(cam.x ?? L.cx), -(cam.y ?? L.cy));
  }

  // ───────────────────────── cor ─────────────────────────
  const hex = (h) => { h = h.replace('#', ''); if (h.length === 3) h = [...h].map((c) => c + c).join(''); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); };
  const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const mixHex = (a, b, p) => rgb(mix(hex(a), hex(b), p));

  // ───────────────────────── textura: grão de filme determinístico ─────────────────────────
  const grainCache = {};
  function grain(g, W, H, t, amount = 0.06, fps = 24) {
    const key = W + 'x' + H;
    if (!grainCache[key]) {
      grainCache[key] = [];
      for (let k = 0; k < 6; k++) {
        const c = document.createElement('canvas'); c.width = 256; c.height = 256;
        const cg = c.getContext('2d'), id = cg.createImageData(256, 256), r = rng(1000 + k);
        for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
        cg.putImageData(id, 0, 0); grainCache[key].push(c);
      }
    }
    const tile = grainCache[key][((Math.floor(t * fps) % 6) + 6) % 6];
    g.save(); g.globalAlpha = amount; g.globalCompositeOperation = 'overlay';
    g.fillStyle = g.createPattern(tile, 'repeat'); g.fillRect(0, 0, W, H); g.restore();
  }
  function vignette(g, W, H, amount = 0.35, color = '0,0,0') {
    const r = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.hypot(W, H) * 0.6);
    r.addColorStop(0, `rgba(${color},0)`); r.addColorStop(1, `rgba(${color},${amount})`);
    g.fillStyle = r; g.fillRect(0, 0, W, H);
  }

  // ───────────────────────── timeline de cenas com transições ─────────────────────────
  /* scenes: [{ from, to, draw(g, lt, ctx), name }] — lt = tempo local da cena.
   * Cenas podem se sobrepor: durante a sobreposição ambas desenham (use ctx.inP / ctx.outP para transições).
   */
  function runScenes(g, t, scenes, extra = {}) {
    for (const s of scenes) {
      if (t < s.from || t >= s.to) continue;
      const lt = t - s.from, dur = s.to - s.from;
      const next = scenes.find((n) => n !== s && n.from > s.from && n.from < s.to);
      const prev = scenes.find((n) => n !== s && n.to > s.from && n.to < s.to && n.from < s.from);
      const inP = prev ? clamp((t - s.from) / (prev.to - s.from)) : 1;
      const outP = next ? clamp((t - next.from) / (s.to - next.from)) : 0;
      g.save(); s.draw(g, lt, Object.assign({ dur, inP, outP, t }, extra)); g.restore();
    }
  }

  // ───────────────────────── objeto físico e câmera ─────────────────────────
  // Parábola fechada entre contatos [{t,x,y,g?}]: nunca teletransporta e o contato cai exatamente em t.
  // Com a câmera andando, passe coordenadas de tela e converta depois, ou o objeto sai do quadro no meio do voo.
  function rota(contatos, gPadrao = 3200) {
    const pos = (t) => {
      let i = 0;
      while (i < contatos.length - 2 && t >= contatos[i + 1].t) i++;
      const a = contatos[i], b = contatos[i + 1] || a, T = Math.max(b.t - a.t, 1e-6), d = clamp(t - a.t, 0, T), g = a.g ?? gPadrao;
      const v0 = (b.y - a.y - 0.5 * g * T * T) / T;
      return [lerp(a.x, b.x, d / T), a.y + v0 * d + 0.5 * g * d * d];
    };
    // achatamento no contato, 0..forca: scaleY(1-a) scaleX(1+a), ancorado na base
    pos.achata = (t, forca = 0.24, queda = 26) => { let a = 0; for (const c of contatos) { if (c.t > t) break; a = Math.max(a, forca * Math.exp(-(t - c.t) * queda)); } return a; };
    return pos;
  }
  // Um mundo, uma câmera: segmentos [{t0,t1,para:{x,y,z}}]. Zoom em espaço logarítmico; entre segmentos a câmera segura o último alvo.
  function camSeg(inicio, segs, e = EASE.move) {
    return (t) => {
      let de = inicio;
      for (const s of segs) {
        if (t < s.t0) break;
        if (t < s.t1) { const p = e(clamp((t - s.t0) / (s.t1 - s.t0))); return { x: lerp(de.x, s.para.x, p), y: lerp(de.y, s.para.y, p), z: Math.exp(lerp(Math.log(de.z), Math.log(s.para.z), p)) }; }
        de = s.para;
      }
      return { ...de };
    };
  }

  // ═══════════════════ v4 — ofício de estúdio (números em references/oficio.md) ═══════════════════
  // Mola por "chega em X s, quica Y" (forma humana de pedir): ζ = 1 − bounce, Hz = 1/(1,2·visualDuration)
  const springVD = (t, visualDuration = 0.4, bounce = 0.15) => springZ(t, clamp(1 - bounce, 0.05, 1), 1 / (1.2 * visualDuration));
  // Stagger orgânico: base·i^0,8 (o lote ACELERA, como cartas sendo dadas) + jitter determinístico de ±1–2 frames
  const stag = (i, base = 0.06, { pow = 0.8, jitter = 1.5, fps = 30, seed = 3 } = {}) => base * Math.pow(i, pow) + ((hash1(i * 7.13 + seed) - 0.5) * 2 * jitter) / fps * (i > 0);
  // Stagger 2D: atraso pela distância até uma origem (grade, mosaico, cards)
  const stag2D = (x, y, ox, oy, perUnit = 0.04) => Math.hypot(x - ox, y - oy) * perUnit;
  // CURVA POR PROPRIEDADE: opacidade chega em ~1/3 do tempo do transform (nunca a mesma curva nos dois)
  const enterProps = (t, t0, dur = 0.6, zeta = 0.8, hz) => ({ a: ease.outQuad(clamp((t - t0) / (dur / 3))), p: springZ(t - t0, zeta, hz || 1 / (1.2 * dur)) });
  // Crossfade de elemento compartilhado SEM "buraco": entra circOut em 0–50%, sai linear em 50–95%
  const handoff = (p) => { const x = clamp(p / 0.5); return { inA: Math.sqrt(1 - (1 - x) * (1 - x)), outA: 1 - clamp((p - 0.5) / 0.45) }; };
  // Inércia (scroll de feed em demo de app): para sozinho, em forma fechada. v em px/s.
  const inertia = (t, from, v, tau = 0.325, power = 0.8) => { const amp = power * v * tau; return t <= 0 ? from : from + amp - amp * Math.exp(-t / tau); };
  // Cor em espaço quadrático (meios-tons sem lama — o mixHex linear em sRGB escurece o meio)
  const mixHexQ = (a, b, p) => { const A = hex(a), B = hex(b); return rgb(A.map((x, i) => Math.sqrt(x * x + p * (B[i] * B[i] - x * x)))); };
  // Tremor de impacto (x e y em frequências diferentes, decaimento e^-5t) e squash ancorado na base
  const impactShake = (t, t0, amp = 15) => { const d = t - t0; if (d < 0 || d > 1.2) return [0, 0]; const e = Math.exp(-5 * d); return [amp * e * Math.sin(2 * Math.PI * 5 * d), amp * 0.73 * e * Math.cos(2 * Math.PI * 6.5 * d)]; };
  // Handheld que FECHA o loop: senos com multiplicadores inteiros do ciclo
  const handheldLoop = (phase, amp = 1) => { const T = 2 * Math.PI * phase; return { yaw: amp * (0.016 * Math.sin(3 * T) + 0.008 * Math.sin(7 * T) + 0.004 * Math.sin(13 * T)), pitch: amp * (0.012 * Math.sin(5 * T + 1) + 0.006 * Math.sin(11 * T + 2)), roll: amp * 0.004 * Math.sin(2 * T + 0.5) }; };
  // Speed ramp: integra a VELOCIDADE (não remapeia a posição). vel(u) ∈ (0..1]; devolve o tempo "de filme" acumulado.
  function speedRamp(t, vel, step = 1 / 240) { let acc = 0; for (let x = 0; x < t; x += step) acc += vel(x) * Math.min(step, t - x); return acc; }
  // Slow-mo no momento-herói (lançamento/impacto): velocidade 1 − 0,9·sin(πu)^0,6
  const heroSlow = (u) => 1 - 0.9 * Math.pow(Math.sin(Math.PI * clamp(u)), 0.6);
  // Zoom-through (atravessar a letra/o buraco): escala = max^p, p = 0,8·easeIn + 0,2·easeOut
  const zoomThrough = (p, max = 40) => Math.pow(max, 0.8 * ease.inCubic(clamp(p)) + 0.2 * ease.outCubic(clamp(p)));
  // Monotone cubic (Fritsch–Carlson): curva MEDIDA de uma referência (pontos [t,v]) sem o soluço do smoothstep
  function monotone(pts) {
    const n = pts.length, xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]), d = [], m = [];
    for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (3 * (d[i - 1] + d[i])) / ((2 * d[i] + d[i - 1]) / d[i - 1] + (d[i] + 2 * d[i - 1]) / d[i]);
    return (x) => { if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1]; let i = 0; while (x > xs[i + 1]) i++;
      const h = xs[i + 1] - xs[i], u = (x - xs[i]) / h, u2 = u * u, u3 = u2 * u;
      return (2 * u3 - 3 * u2 + 1) * ys[i] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * ys[i + 1] + (u3 - u2) * h * m[i + 1]; };
  }
  // Sombra macia de "superfície" (contato + ambiente) e borda fina — o polish que separa card premium de retângulo
  function surface(g, x, y, w, h, r, { fill = '#fff', elev = 1, line = 'rgba(0,0,0,.08)', tint = '0,0,0' } = {}) {
    g.save(); g.fillStyle = fill;
    g.shadowColor = `rgba(${tint},${0.10 + 0.04 * elev})`; g.shadowBlur = 2 + 2 * elev; g.shadowOffsetY = 1 + elev; rrect(g, x, y, w, h, r); g.fill();
    g.shadowColor = `rgba(${tint},${0.08 + 0.03 * elev})`; g.shadowBlur = 18 * elev + 10; g.shadowOffsetY = 8 * elev + 4; rrect(g, x, y, w, h, r); g.fill();
    g.shadowColor = 'transparent'; g.lineWidth = 1; g.strokeStyle = line; rrect(g, x + 0.5, y + 0.5, w - 1, h - 1, r); g.stroke();
    g.strokeStyle = 'rgba(255,255,255,.55)'; g.beginPath(); g.moveTo(x + r, y + 1.5); g.lineTo(x + w - r, y + 1.5); g.stroke(); g.restore();
  }
  // ── CÂMERA 2.5D (ideia do kit camera.js de showheyohtaki/motion-prompt, MIT): mundo em metros, lente em px ──
  // cam = { x,y,z (posição), yaw, pitch, roll, f (distância focal px), focus (dist. de foco m), aperture (blur px por m fora de foco) }
  // M.cam3(cam, W, H).proj(x,y,z) → { x, y, s (escala), z (profundidade), blur } · .layers(lista,{draw}) ordena de trás p/ frente
  // Grátis daqui: parallax real, dolly ≠ zoom, DOLLY ZOOM (f ∝ distância), órbita, grua, rack focus, bullet time.
  function cam3(cam, W, H) {
    const cy = Math.cos(cam.yaw || 0), sy = Math.sin(cam.yaw || 0), cp = Math.cos(cam.pitch || 0), spp = Math.sin(cam.pitch || 0), f = cam.f || W * 0.9;
    const proj = (x, y, z) => {
      let dx = x - (cam.x || 0), dy = y - (cam.y || 0), dz = z - (cam.z ?? -6);
      const x1 = cy * dx - sy * dz, z1 = sy * dx + cy * dz;            // yaw
      const y2 = cp * dy - spp * z1, z2 = spp * dy + cp * z1;           // pitch
      const r = cam.roll || 0, xr = Math.cos(r) * x1 - Math.sin(r) * y2, yr = Math.sin(r) * x1 + Math.cos(r) * y2;
      if (z2 <= 0.05) return null;                                       // atrás da lente (near clip)
      const blur = cam.focus != null ? Math.min(40, Math.abs(z2 - cam.focus) * (cam.aperture || 0)) : 0;
      return { x: W / 2 + (f * xr) / z2, y: H / 2 - (f * yr) / z2, s: f / z2, z: z2, blur };
    };
    const layers = (items, draw) => items.map((it) => ({ it, p: proj(it.x, it.y, it.z) })).filter((o) => o.p).sort((a, b) => b.p.z - a.p.z).forEach(({ it, p }) => draw(it, p));
    return { proj, layers, f };
  }
  // Dolly zoom: mantém o assunto do mesmo tamanho (f ∝ distância) enquanto o fundo cresce/encolhe
  const dollyZoomF = (dist, ref = { dist: 3.2, f: 132 }) => (ref.f * dist) / ref.dist;
  // Câmera que SEGUE o objeto que guia (pré-calcule por frame): alvo = obj + lead·vel, misturado com âncora; mola crítica ω≈6
  function followCam(objAt, anchorAt, weightAt, { fps = 60, dur = 10, lead = 0.15, omega = 6 } = {}) {
    const N = Math.ceil(dur * fps) + 2, xs = new Float32Array(N), ys = new Float32Array(N); let x = null, y = null, vx = 0, vy = 0; const dt = 1 / fps;
    for (let i = 0; i < N; i++) { const t = i * dt, o = objAt(t), o2 = objAt(t + dt), a = anchorAt(t), w = weightAt(t);
      const tx = (1 - w) * (o.x + lead * (o2.x - o.x) / dt) + w * a.x, ty = (1 - w) * (o.y + lead * (o2.y - o.y) / dt) + w * a.y;
      if (x === null) { x = tx; y = ty; }
      const ax = omega * omega * (tx - x) - 2 * omega * vx, ay = omega * omega * (ty - y) - 2 * omega * vy; vx += ax * dt; vy += ay * dt; x += vx * dt; y += vy * dt; xs[i] = x; ys[i] = y; }
    return (t) => { const i = clamp(t * fps, 0, N - 2), k = Math.floor(i), f = i - k; return { x: lerp(xs[k], xs[k + 1], f), y: lerp(ys[k], ys[k + 1], f) }; };
  }

  // ═══════════════════ v5 ═══════════════════
  // FÍSICA PRÉ-CALCULADA (determinística): simula UMA vez a passo fixo desde t=0 e guarda cada amostra; seek(t) só lê.
  // step(state, dt, t) muta e devolve o estado; snapshot(state) → objeto plano. Mesmo t = mesmo frame, frio ou quente.
  // Ex.: const sim = M.bake({ dur: 6, hz: 240, init: () => ({ bolas }), step: verlet, snapshot: (s) => s.bolas.map(b => [b.x, b.y]) }); sim(t)
  function bake({ dur, hz = 240, init, step, snapshot }) {
    const N = Math.ceil(dur * hz) + 1, dt = 1 / hz, frames = new Array(N); let st = init();
    for (let i = 0; i < N; i++) { frames[i] = snapshot(st); st = step(st, dt, i * dt) || st; }
    return (t) => frames[Math.max(0, Math.min(N - 1, Math.round(t * hz)))];
  }
  // Verlet com gravidade, chão e colisão círculo-círculo (o "motor de física" do filme, sem estado no render)
  function verletStep({ g = 2400, floor = Infinity, walls = null, bounce = 0.35, iters = 4, friction = 0.25 } = {}) {
    return (s, dt) => {
      for (const b of s.bodies) { const vx = (b.x - b.px) * 0.999, vy = (b.y - b.py) * 0.999; b.px = b.x; b.py = b.y; b.x += vx; b.y += vy + g * dt * dt; }
      for (let k = 0; k < iters; k++) for (let i = 0; i < s.bodies.length; i++) {
        const a = s.bodies[i];
        if (a.y + a.r > floor) { const vy = a.y - a.py, vx = a.x - a.px; a.y = floor - a.r; a.py = a.y + vy * bounce; a.px = a.x - vx * (1 - friction); }
        if (walls) { if (a.x - a.r < walls[0]) a.x = walls[0] + a.r; if (a.x + a.r > walls[1]) a.x = walls[1] - a.r; }
        for (let j = i + 1; j < s.bodies.length; j++) { const b = s.bodies[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1e-6, m = a.r + b.r;
          if (d < m) { const o = Math.min(m - d, a.r * 0.5) / 2 / d; a.x -= dx * o; a.y -= dy * o; b.x += dx * o; b.y += dy * o; } }
      }
      return s;
    };
  }
  // Duração pela DISTÂNCIA e pelo MATERIAL (LottieFiles): 50 px 0,8× · 100 1× · 200 1,3× · 300 1,5× · 400 1,6× · tela cheia 1,8–2×
  const MATERIAL = { rigid: [1.2, 0], elastic: [0.8, 0.2], fluid: [1.5, 0.05], paper: [1.0, 0.04], gas: [2.0, 0], glass: [0.9, 0] };
  function durFor(px, base = 0.4, material = 'paper', W = 1080) {
    const k = px <= 50 ? 0.8 : px <= 100 ? remap(px, 50, 100, 0.8, 1) : px <= 200 ? remap(px, 100, 200, 1, 1.3) : px <= 300 ? remap(px, 200, 300, 1.3, 1.5) : px <= 400 ? remap(px, 300, 400, 1.5, 1.6) : remap(Math.min(px, W), 400, W, 1.6, 1.9);
    const [m, overshoot] = MATERIAL[material] || MATERIAL.paper; return { dur: base * k * m, overshoot };
  }
  // DIGITAÇÃO medida (sub-level/TypedLine): 1 letra/frame, +2 f depois de espaço, +1 f de "tropeço" a cada ~7 letras, sem cursor.
  // Centralize pela largura FINAL (a linha não "anda" enquanto digita). Devolve quantos caracteres mostrar no instante t.
  function typed(t, t0, text, fps = 30) { let f = 0; const at = []; for (let i = 0; i < text.length; i++) { at.push(f); f += 1 + (text[i] === ' ' ? 2 : 0) + (i % 7 === 6 ? 1 : 0); } const n = (t - t0) * fps; let k = 0; while (k < at.length && at[k] <= n) k++; return k; }
  // SAÍDA "VARRIDA": em 13 f a borda esquerda da tinta corre p/ direita até ~70% sumir (borda suave de 8 letras), a linha desce 0,5 cap em p², depois CORTE SECO
  const sweepOut = (t, t0, fps = 30) => { const p = clamp((t - t0) * fps / 13); return { p, edge: 0.7 * ease.outCubic(p), drop: 0.5 * p * p, alpha: p >= 1 ? 0 : 1 - 0.15 * p }; };
  // DÍGITOS EM CÉLULA FIXA: contador que não "treme" (largura tabular). Desenha string centrada em x com células iguais ao '0'.
  function digits(g, str, x, y, { align = 'center' } = {}) { const cw = g.measureText('0').width, tot = [...str].reduce((a, ch) => a + (/\d/.test(ch) ? cw : g.measureText(ch).width), 0); let cx = align === 'center' ? x - tot / 2 : align === 'right' ? x - tot : x;
    const ta = g.textAlign; g.textAlign = 'center'; for (const ch of str) { const w = /\d/.test(ch) ? cw : g.measureText(ch).width; g.fillText(ch, cx + w / 2, y); cx += w; } g.textAlign = ta; }
  // Teto de stagger: o lote inteiro cabe em `total` s (Lottie < 0,5 s; grupo grande 0,6–0,8 s), mantendo a aceleração i^0,8
  const stagCap = (i, n, total = 0.5, pow = 0.8) => (n <= 1 ? 0 : total * Math.pow(i / (n - 1), pow));

  root.M = { rota, camSeg, clamp, lerp, invLerp, remap, smooth, mix, ease, tween, cubicBezier, EASE, MS, STAGGER, spring, SPRING, sp, springZ, dampingRatio, track, trackV, stretch, swapAlpha,
    stagger, loopT, loopNoise, frameT, count, onTwos, rng, hash1, noise1, noise2, fbm, handheld, grid, pulse, beatIndex, layout, setFont, fitSize, wrap,
    kinetic, maskReveal, rrect, drawPartial, cursor, press, camera, hex, rgb, mixHex, grain, vignette, runScenes,
    springVD, stag, stag2D, enterProps, handoff, inertia, mixHexQ, impactShake, handheldLoop, speedRamp, heroSlow, zoomThrough, monotone, surface, cam3, dollyZoomF, followCam,
    bake, verletStep, durFor, MATERIAL, typed, sweepOut, digits, stagCap };
})(typeof window !== 'undefined' ? window : globalThis);
