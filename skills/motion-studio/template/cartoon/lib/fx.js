/* fx.js — efeitos em camadas e legendas palavra a palavra. Tudo determinístico (função de t, ruído com semente).
 * Impacto "de cinema" = várias camadas no MESMO frame: flash → ondas de choque → bola de fogo → fumaça/cogumelo → detritos
 * → tremor de câmera decaindo (+ o mundo reage: árvores dobram). Em filme de PRODUTO esses efeitos seguem proibidos como
 * decoração; aqui servem a uma história (o meteoro, a explosão, o "carimbo" da virada).
 *
 *   FX.flash(g, t, t0, W, H, cor, dur)              FX.shockwave(g, t, t0, x, y, rMax, cor, n)
 *   FX.fireball(g, t, t0, x, y, r)                  FX.smoke(g, t, t0, x, y, n, seed, r)   (cogumelo: FX.mushroom)
 *   FX.debris(g, t, t0, x, y, n, seed, {v, grav, cores, size})       FX.shake(t, t0, amp, decaimento) → [dx, dy]
 *   FX.bend(t, t0, x, xImpacto, força) → ângulo (rad) para árvores/postes dobrarem na onda de choque
 *   FX.speedLines(g, t, cx, cy, n, seed, cor, W, H) FX.sparkles(g, t, t0, x, y, n, seed, cor)
 *   FX.stamp(g, t, t0, texto, x, y, size, cor, font) carimbo com squash (a virada da história)
 *   FX.captions(g, t, words, opts)                  legendas palavra a palavra (2–3 por vez, palavra atual no acento, escala 1,1)
 */
(function (root) {
  'use strict';
  const M = root.M;
  const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const age = (t, t0) => t - t0;

  function flash(g, t, t0, W, H, cor = '#FFFFFF', dur = 0.14) {
    const a = age(t, t0); if (a < 0 || a > dur) return;
    g.save(); g.globalAlpha = Math.min(0.6, 0.6 * (1 - a / dur)); g.fillStyle = cor; g.fillRect(0, 0, W, H); g.restore();   // ≤ 0,6: nunca "buraco branco"
  }
  function shockwave(g, t, t0, x, y, rMax, cor = '#FFFFFF', n = 2) {
    for (let k = 0; k < n; k++) {
      const a = age(t, t0 + k * 0.09); if (a < 0 || a > 0.7) continue;
      const p = M.EASE.enter(cl(a / 0.7)), r = rMax * p;
      g.save(); g.globalAlpha = (1 - p) * 0.9; g.strokeStyle = cor; g.lineWidth = Math.max(2, rMax * 0.05 * (1 - p));
      g.beginPath(); g.ellipse(x, y, r, r * 0.35, 0, 0, 7); g.stroke(); g.restore();
    }
  }
  function fireball(g, t, t0, x, y, r) {
    const a = age(t, t0); if (a < 0 || a > 1.6) return;
    const grow = M.spring(a, 120, 14), rr = r * grow * (1 + 0.15 * a), heat = cl(1 - a / 1.2);
    const gr = g.createRadialGradient(x, y - rr * 0.2, rr * 0.05, x, y, rr);
    gr.addColorStop(0, `rgba(255,250,220,${heat})`); gr.addColorStop(0.35, `rgba(255,190,70,${0.95 * heat + 0.05})`);
    gr.addColorStop(0.7, `rgba(235,90,40,${0.85 * heat + 0.1})`); gr.addColorStop(1, 'rgba(80,30,30,0)');
    g.save(); g.fillStyle = gr; g.beginPath(); g.arc(x, y, rr, 0, 7); g.fill(); g.restore();
  }
  function smoke(g, t, t0, x, y, n, seed, r, cor = [70, 62, 72]) {
    const a = age(t, t0); if (a < 0 || a > 4) return; const R = M.rng(seed);
    for (let i = 0; i < n; i++) {
      const ang = R() * Math.PI * 2, sp = 0.4 + R() * 0.8, rise = 0.6 + R() * 0.8, d = R() * 0.25;
      const aa = Math.max(0, a - d), p = 1 - Math.exp(-aa * 1.6);
      const px = x + Math.cos(ang) * r * sp * p, py = y - r * rise * p * 1.2 + Math.sin(ang) * r * 0.25 * p, pr = r * (0.25 + 0.5 * p) * (0.7 + R() * 0.6);
      g.save(); g.globalAlpha = cl(0.75 * (1 - aa / 4)); g.fillStyle = `rgb(${cor[0]},${cor[1]},${cor[2]})`; g.beginPath(); g.arc(px, py, pr, 0, 7); g.fill(); g.restore();
    }
  }
  function mushroom(g, t, t0, x, y, r, seed = 3) {   // coluna + chapéu que sobe e abre
    const a = age(t, t0); if (a < 0 || a > 5) return; const up = M.EASE.premium(cl(a / 2.2)) * r * 2.4;
    g.save(); g.globalAlpha = cl(1 - (a - 3) / 2); g.fillStyle = '#5A4A52';
    g.beginPath(); g.moveTo(x - r * 0.18, y); g.quadraticCurveTo(x - r * 0.12, y - up * 0.5, x - r * 0.2, y - up); g.lineTo(x + r * 0.2, y - up); g.quadraticCurveTo(x + r * 0.12, y - up * 0.5, x + r * 0.18, y); g.fill(); g.restore();
    smoke(g, t, t0 + 0.15, x, y - up, 14, seed, r * 0.9 * cl(a / 1.5 + 0.2), [92, 78, 86]);
  }
  function debris(g, t, t0, x, y, n, seed, o = {}) {
    const a = age(t, t0); if (a < 0 || a > (o.life || 2.2)) return; const R = M.rng(seed);
    const v = o.v || 900, grav = o.grav || 1800, cores = o.cores || ['#3A2E39', '#6B5B63', '#F2A65A'], size = o.size || 10;
    for (let i = 0; i < n; i++) {
      const ang = -Math.PI * (0.1 + R() * 0.8), sp = v * (0.35 + R() * 0.65), rot = (R() - 0.5) * 18, s = size * (0.5 + R());
      const px = x + Math.cos(ang) * sp * a, py = y + Math.sin(ang) * sp * a + 0.5 * grav * a * a;   // balística fechada
      g.save(); g.globalAlpha = cl(1.4 - a / (o.life || 2.2)); g.translate(px, py); g.rotate(rot * a); g.fillStyle = cores[i % cores.length];
      g.fillRect(-s / 2, -s / 2, s, s * 0.7); g.restore();
    }
  }
  const shake = (t, t0, amp = 24, dec = 7) => { const d = t - t0; if (d < 0) return [0, 0]; const e = amp * Math.exp(-dec * d); return [e * Math.sin(d * 97), e * Math.cos(d * 71)]; };
  const bend = (t, t0, x, xi, forca = 0.6) => { const dist = Math.abs(x - xi), chega = t0 + dist / 2400, d = t - chega; if (d < 0) return 0;
    return Math.sign(x - xi) * forca * Math.exp(-d * 3) * Math.cos(d * 9) * Math.min(1, 600 / (dist + 200)); };
  function speedLines(g, t, cx, cy, n, seed, cor, W, H) {
    const R = M.rng(seed + Math.floor(t * 12));   // troca 12×/s (on twos)
    g.save(); g.strokeStyle = cor; for (let i = 0; i < n; i++) { const a = R() * Math.PI * 2, r0 = Math.max(W, H) * (0.32 + R() * 0.2);
      g.globalAlpha = 0.25 + R() * 0.4; g.lineWidth = 2 + R() * 5; g.beginPath(); g.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); g.lineTo(cx + Math.cos(a) * Math.max(W, H), cy + Math.sin(a) * Math.max(W, H)); g.stroke(); }
    g.restore();
  }
  function sparkles(g, t, t0, x, y, n, seed, cor = '#FFD166') {
    const a = age(t, t0); if (a < 0 || a > 0.6) return; const R = M.rng(seed);
    for (let i = 0; i < n; i++) { const ang = (i / n) * Math.PI * 2 + R() * 0.4, d = M.EASE.enter(cl(a / 0.45)) * (60 + R() * 60), s = (1 - a / 0.6) * (8 + R() * 8);
      g.save(); g.translate(x + Math.cos(ang) * d, y + Math.sin(ang) * d); g.rotate(ang); g.fillStyle = cor; g.beginPath();
      for (let k = 0; k < 4; k++) { const q = (k * Math.PI) / 2; g.lineTo(Math.cos(q) * s, Math.sin(q) * s); g.lineTo(Math.cos(q + Math.PI / 4) * s * 0.35, Math.sin(q + Math.PI / 4) * s * 0.35); }
      g.closePath(); g.fill(); g.restore(); }
  }
  function stamp(g, t, t0, texto, x, y, size, cor, font) {
    const a = age(t, t0); if (a < 0) return;
    const p = M.springZ(a, 0.45, 3.2), sc = 2.4 - 1.4 * p, rot = -0.12 + 0.04 * Math.exp(-a * 6) * Math.sin(a * 30);
    g.save(); g.translate(x, y); g.rotate(rot); g.scale(sc, sc * (1 - 0.12 * Math.exp(-a * 9))); g.globalAlpha = cl(a / 0.06);
    g.font = font || `900 ${size}px system-ui`; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.lineWidth = size * 0.12; g.strokeStyle = cor; const w = g.measureText(texto).width;
    g.strokeRect(-w / 2 - size * 0.3, -size * 0.75, w + size * 0.6, size * 1.5); g.fillStyle = cor; g.fillText(texto, 0, size * 0.04); g.restore();
  }

  /* Legendas palavra a palavra: 70% assiste sem som.
   * words = [{w, s, e, stress}] (audio/words.json) · opts: {y, size, font, color, accent, outline, per (2–3), maxW}
   * Grupo de `per` palavras (quebra em pontuação), entra com pop; a palavra falada fica no acento e cresce 10%. */
  // Regras de bloco (PT-BR): ≤ 2 palavras e ≤ 13 caracteres, ou ≤ 3 e ≤ 18; quebra em pontuação e em troca de cena;
  // NUNCA termina bloco em palavra funcional ("de", "que", "o"…) — ela desce para o próximo bloco.
  const FUNC = new Set('a o as os um uma de da do das dos e é em no na nos nas que pra pro para por com sem se ao à mas ou meu minha seu sua te me lhe'.split(' '));
  function groups(words, per) {
    const out = []; let cur = [];
    const clean = (w) => w.w.toLowerCase().replace(/[^\wà-ÿ%]/g, '');
    const chars = (arr) => arr.reduce((a, w) => a + w.w.length, 0) + arr.length - 1;
    for (let i = 0; i < words.length; i++) {
      const w = words[i], nx = words[i + 1];
      cur.push(w);
      const full = cur.length >= Math.min(per, 3) || (cur.length >= 2 && chars(cur) >= 13) || chars(cur) >= 18;
      const brk = /[.,!?…:;]$/.test(w.w) || !nx || nx.scene !== w.scene || (nx.s - w.e) > 0.5;
      if (brk || full) {
        if (!brk) { const carry = []; while (cur.length > 1 && FUNC.has(clean(cur[cur.length - 1]))) carry.unshift(cur.pop()); if (carry.length) { out.push(cur); cur = carry; continue; } }   // função vai pro próximo
        out.push(cur); cur = [];
      }
    }
    if (cur.length) out.push(cur); return out;
  }
  const GCACHE = new WeakMap();
  function captions(g, t, words, o) {
    if (!words || !words.length) return;
    const per = o.per || 3; let gs = GCACHE.get(words); if (!gs || gs.per !== per) { gs = groups(words, per); gs.per = per; GCACHE.set(words, gs); }
    const grp = gs.find((gp, i) => t >= gp[0].s - 0.04 && t < (gs[i + 1] ? Math.min(gs[i + 1][0].s - 0.04, gp[gp.length - 1].e + 0.6) : gp[gp.length - 1].e + 0.6));
    if (!grp) return;
    const ft = M.frameT(t), size = o.size || 72, font = (w) => `${o.weight || 900} ${size}px ${o.font || 'system-ui'}`;
    g.save(); g.font = font(); g.textBaseline = 'alphabetic'; g.lineJoin = 'round';
    const txt = (w) => (o.upper === false ? w.w : w.w.toUpperCase()).replace(/[.,!?…:]+$/, (m) => (o.keepPunct ? m : m.replace(/[.,:…]/g, '')));
    // célula de cada palavra já reserva o crescimento de 1,1× da palavra atual + o contorno → nunca encosta na vizinha
    const ow = o.outlineW || 12, sp = size * 0.16;
    const ws = grp.map((w) => g.measureText(txt(w)).width), cells = ws.map((w) => w * 1.12 + ow), total = cells.reduce((a, b) => a + b, 0) + sp * (grp.length - 1);
    const fit = Math.min(1, (o.maxW || 900) / total), pop = M.springZ(t - grp[0].s + 0.04, 0.55, 4);
    let x = (o.x ?? 540) - (total * fit) / 2;
    g.translate(0, o.y); g.scale(1, 1);
    grp.forEach((w, i) => {
      const on = ft >= w.s && ft < w.e + 0.08, said = ft >= w.s, cw = cells[i] * fit;
      const s = fit * (0.85 + 0.15 * pop) * (on ? 1 + 0.1 * M.springZ(ft - w.s, 0.6, 5) : 1);
      g.save(); g.translate(x + cw / 2, 0); g.scale(s, s);
      g.lineWidth = ow; g.strokeStyle = o.outline || '#1E1B2E'; g.strokeText(txt(w), -ws[i] / 2, 0);
      g.fillStyle = on || (w.stress && said) ? o.accent || '#FFB547' : o.color || '#FFFFFF'; g.fillText(txt(w), -ws[i] / 2, 0);
      g.restore(); x += cw + sp * fit;
    });
    g.restore();
  }

  root.FX = { flash, shockwave, fireball, smoke, mushroom, debris, shake, bend, speedLines, sparkles, stamp, captions };
})(typeof window !== 'undefined' ? window : globalThis);
