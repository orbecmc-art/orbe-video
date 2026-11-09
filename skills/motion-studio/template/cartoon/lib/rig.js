/* rig.js — personagem com "rig" em canvas: partes separadas com pivô, 9 bocas (padrão Rhubarb), poses e emoções em código.
 * Tudo é função pura do tempo. O visual vem de hero/hero.json (elenco TRAVADO: mesmo boneco em todo episódio).
 *
 *   R.draw(g, hero, state, x, y, scale)          desenha o personagem com os pés em (x, y)
 *   R.state(t, hero, track, voice)               estado no instante t: ângulos (springs entre poses), emoção, boca, piscada, pulo
 *     track = [{ t, pose, emotion, look:[x,y], face:1|-1 }, ...]   (chaves ordenadas; poses/emoções trocam por spring)
 *     voice = { mouth: 'XXBBDDC…', fps, env:[…], stress:[t…], speaking:[[a,b],…] }   (de audio/mouth.json + loud.json)
 *   R.sheet(g, hero, W, H)                       folha de aprovação: todas as poses × todas as bocas (hero_sheet)
 * Poses: idle talk point shrug surprised thumbs_up wave think panic  ·  Emoções: neutral happy surprised angry worried panic sad
 * Bocas: A (M/B/P) B (consoantes) C (E/I) D (A aberta) E (O) F (U) G (F/V) H (L) X (repouso)
 */
(function (root) {
  'use strict';
  const M = root.M;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const rad = (d) => (d * Math.PI) / 180;

  // ângulos em graus: ombro (0 = braço para baixo, + = para fora/cima), cotovelo (+ dobra para cima)
  const POSES = {
    idle:      { sl: 8,   el: 10,  sr: 8,   er: 10,  lean: 0,  head: 0 },
    talk:      { sl: 10,  el: 15,  sr: 38,  er: 55,  lean: 2,  head: 3 },
    point:     { sl: 8,   el: 10,  sr: 95,  er: 0,   lean: 4,  head: 6 },
    shrug:     { sl: 55,  el: 95,  sr: 55,  er: 95,  lean: 0,  head: -4 },
    surprised: { sl: 120, el: 40,  sr: 120, er: 40,  lean: -3, head: -6 },
    thumbs_up: { sl: 8,   el: 10,  sr: 40,  er: 115, lean: 3,  head: 4 },
    wave:      { sl: 8,   el: 10,  sr: 150, er: 25,  lean: 0,  head: 5 },
    think:     { sl: 10,  el: 12,  sr: 30,  er: 140, lean: -2, head: -8 },
    panic:     { sl: 150, el: 70,  sr: 150, er: 70,  lean: 0,  head: 0 },
  };
  // emoção = números do rosto: sobrancelha (ângulo, altura), olho (escala), suor, rubor, inclinação da boca em repouso
  const EMO = {
    neutral:   { bA: 0,   bY: 0,    eye: 1,    sweat: 0, blush: 0,   smile: 0.2 },
    happy:     { bA: -6,  bY: -0.1, eye: 0.85, sweat: 0, blush: 0.6, smile: 1 },
    surprised: { bA: -4,  bY: -0.5, eye: 1.35, sweat: 0, blush: 0,   smile: 0 },
    angry:     { bA: 22,  bY: 0.25, eye: 0.9,  sweat: 0, blush: 0.3, smile: -0.8 },
    worried:   { bA: -18, bY: -0.2, eye: 1.05, sweat: 0.4, blush: 0, smile: -0.5 },
    panic:     { bA: -24, bY: -0.35, eye: 1.3, sweat: 1, blush: 0,   smile: -0.9 },
    sad:       { bA: -20, bY: 0.05, eye: 0.9,  sweat: 0, blush: 0,   smile: -1 },
  };
  const JOINTS = ['sl', 'el', 'sr', 'er', 'lean', 'head'], FACE = ['bA', 'bY', 'eye', 'sweat', 'blush', 'smile'];

  function state(t, hero, track, voice) {
    track = track && track.length ? track : [{ t: 0, pose: 'idle', emotion: 'neutral' }];
    const s = {};
    // poses e emoções: soma de springs (M.track) entre as chaves → contínuo, sem simular frames anteriores
    for (const j of JOINTS) s[j] = M.track(t, track.map((k) => [k.t, (POSES[k.pose] || POSES.idle)[j]]), [150, 20]);
    for (const f of FACE) s[f] = M.track(t, track.map((k) => [k.t, (EMO[k.emotion] || EMO.neutral)[f]]), [200, 26]);
    s.thumb = M.track(t, track.map((k) => [k.t, k.pose === 'thumbs_up' ? 1 : 0]), [260, 24]);
    s.lookX = M.track(t, track.map((k) => [k.t, (k.look || [0, 0])[0]]), 'smooth');
    s.lookY = M.track(t, track.map((k) => [k.t, (k.look || [0, 0])[1]]), 'smooth');
    s._t = t;
    s.face = track.filter((k) => k.t <= t).reduce((a, k) => (k.face != null ? k.face : a), track[0].face || 1);
    // respiração (escala 1 → 1,015 a cada 3 s) e piscada a cada 3–4 s com deslocamento semeado pelo nome
    const seed = (hero.name || 'h').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    s.breath = 1 + 0.015 * (0.5 - 0.5 * Math.cos((2 * Math.PI * t) / 3));
    let blink = 1;
    for (let k = 0, bt = 0.9 + M.hash1(seed) * 1.5; bt < t + 0.2 && k < 200; k++, bt += 3 + M.hash1(seed + k) * 1.2) {
      const d = t - bt; if (d >= 0 && d < 0.14) blink = Math.abs(d - 0.07) / 0.07;
    }
    s.blink = Math.max(0.08, blink);
    // boca: do mouth.json (por frame); fora da fala, repouso
    s.mouth = 'X';
    if (voice && voice.mouth) { const f = Math.floor(t * voice.fps); s.mouth = voice.mouth[f] || 'X'; }
    // falando → gesto sutil no braço do gesto + cabeça acompanha o volume
    const env = voice && voice.env ? voice.env[Math.floor(t * voice.fps)] || 0 : 0;
    s.talk = env;
    s.er += env * 18 * Math.sin(t * 7.3); s.head += env * 4 * Math.sin(t * 5.1 + 1);
    // palavra forte: pulinho (antecipação + salto + aterrissagem com squash) e sobrancelha desce
    s.jump = 0; s.squash = 0;
    for (const st of (voice && voice.stress) || []) {
      const d = t - st + 0.06;
      if (d > -0.08 && d < 0) s.squash = Math.max(s.squash, 0.06 * Math.sin((-d / 0.08) * Math.PI));             // agacha antes
      if (d >= 0 && d < 0.36) { s.jump = Math.max(s.jump, Math.sin((d / 0.36) * Math.PI)); }
      if (d >= 0.36 && d < 0.5) s.squash = Math.max(s.squash, 0.08 * Math.exp(-(d - 0.36) * 25) * Math.cos((d - 0.36) * 40));
      if (d >= 0 && d < 0.5) s.bY += 0.25 * Math.sin((clamp(d / 0.5)) * Math.PI);
    }
    return s;
  }

  function roundRect(g, x, y, w, h, r) { r = Math.min(r, w / 2, h / 2); g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  function limb(g, hero, x, y, a1, a2, len1, len2, w, side, thumb = 0) {
    // braço em dois segmentos com pivô no ombro e no cotovelo; mão redonda
    g.save(); g.translate(x, y); g.rotate(-side * rad(a1));   // + = para FORA (esquerdo gira horário, direito anti-horário)
    g.fillStyle = hero.shirt; roundRect(g, -w / 2, 0, w, len1, w / 2); g.fill(); g.stroke();
    g.translate(0, len1 - w * 0.2); g.rotate(-side * rad(a2));
    g.fillStyle = hero.skin; roundRect(g, -w * 0.42, 0, w * 0.84, len2, w * 0.42); g.fill(); g.stroke();
    g.beginPath(); g.arc(0, len2 + w * 0.15, w * 0.62, 0, 7); g.fill(); g.stroke();
    if (thumb > 0.05) {   // polegar para cima (joinha): aponta para o "alto" da mão, cresce com a pose
      g.save(); g.translate(side * w * 0.1, len2 + w * 0.15); g.rotate(Math.PI); g.scale(thumb, thumb);
      roundRect(g, -w * 0.2, w * 0.35, w * 0.4, w * 0.75, w * 0.2); g.fill(); g.stroke(); g.restore();
    }
    g.restore();
  }
  function mouthShape(g, hero, m, w, smile) {
    const d = hero.mouthColor || '#3B1F2B', teeth = '#FFFFFF', tongue = '#E8737A', r = w / 2;
    g.lineJoin = g.lineCap = 'round';
    const lip = (h) => { g.beginPath(); g.ellipse(0, 0, r, h, 0, 0, 7); g.fillStyle = d; g.fill(); g.stroke(); };
    switch (m) {
      case 'X': case 'A': {     // repouso / lábios fechados (M,B,P): linha com curva de humor
        const c = m === 'A' ? 0 : smile * r * 0.35;
        g.beginPath(); g.moveTo(-r * 0.75, 0); g.quadraticCurveTo(0, c * 2, r * 0.75, 0);
        g.lineWidth *= m === 'A' ? 1.6 : 1.2; g.stroke(); break; }
      case 'B': lip(r * 0.32); g.save(); g.clip(); g.fillStyle = teeth; g.fillRect(-r, -r * 0.32, 2 * r, r * 0.28); g.restore(); g.stroke(); break;
      case 'C': lip(r * 0.45); g.save(); g.clip(); g.fillStyle = teeth; g.fillRect(-r, -r * 0.45, 2 * r, r * 0.25); g.restore(); g.stroke(); break;
      case 'D': lip(r * 0.78); g.save(); g.clip(); g.fillStyle = teeth; g.fillRect(-r, -r * 0.78, 2 * r, r * 0.25);
        g.fillStyle = tongue; g.beginPath(); g.ellipse(0, r * 0.55, r * 0.55, r * 0.35, 0, 0, 7); g.fill(); g.restore(); g.stroke(); break;
      case 'E': g.beginPath(); g.ellipse(0, 0, r * 0.55, r * 0.6, 0, 0, 7); g.fillStyle = d; g.fill(); g.stroke(); break;
      case 'F': g.beginPath(); g.ellipse(0, 0, r * 0.3, r * 0.32, 0, 0, 7); g.fillStyle = d; g.fill(); g.stroke(); break;
      case 'G': lip(r * 0.28); g.save(); g.clip(); g.fillStyle = teeth; g.fillRect(-r, -r * 0.3, 2 * r, r * 0.36); g.restore(); g.stroke(); break;
      case 'H': lip(r * 0.5); g.save(); g.clip(); g.fillStyle = tongue; g.beginPath(); g.ellipse(0, -r * 0.05, r * 0.4, r * 0.28, 0, 0, 7); g.fill(); g.restore(); g.stroke(); break;
      default: lip(r * 0.3);
    }
  }

  // Desenha com os pés em (x, y). Unidade u = scale/10 (o boneco tem ~10 unidades de altura).
  function draw(g, hero, s, x, y, scale) {
    const u = scale / 10, ol = hero.outline || '#1E1B2E';
    g.save(); g.translate(x, y - s.jump * u * 1.6);
    g.scale(s.face * (1 + s.squash), 1 - s.squash);
    g.lineWidth = Math.max(1.5, u * 0.16); g.strokeStyle = ol;
    // sombra no chão (diminui no pulo)
    g.save(); g.scale(1, 0.25); g.fillStyle = 'rgba(0,0,0,.18)'; g.beginPath(); g.ellipse(0, (s.jump * u * 1.6) / 0.25 * 0.25 * 4, u * 2.4 * (1 - 0.35 * s.jump), u * 1.2, 0, 0, 7); g.fill(); g.restore();
    // pernas
    g.fillStyle = hero.pants; roundRect(g, -u * 1.35, -u * 2.7, u * 1.1, u * 2.5, u * 0.5); g.fill(); g.stroke();
    roundRect(g, u * 0.25, -u * 2.7, u * 1.1, u * 2.5, u * 0.5); g.fill(); g.stroke();
    g.fillStyle = hero.shoes; roundRect(g, -u * 1.6, -u * 0.45, u * 1.55, u * 0.6, u * 0.3); g.fill(); g.stroke();
    roundRect(g, u * 0.15, -u * 0.45, u * 1.55, u * 0.6, u * 0.3); g.fill(); g.stroke();
    // tronco (respira) com inclinação
    g.save(); g.translate(0, -u * 2.5); g.rotate(rad(s.lean)); g.scale(1, s.breath);
    const bw = u * 3.3, bh = u * 3.5;
    // braço de trás
    limb(g, hero, -bw * 0.42, -bh + u * 0.4, s.sl, s.el, u * 1.6, u * 1.5, u * 0.85, -1);
    g.fillStyle = hero.shirt; roundRect(g, -bw / 2, -bh, bw, bh, u * 1.1); g.fill(); g.stroke();
    if (hero.detail) { g.fillStyle = hero.accent; roundRect(g, -u * 0.5, -bh + u * 0.9, u * 1.0, u * 1.0, u * 0.3); g.fill(); }
    limb(g, hero, bw * 0.42, -bh + u * 0.4, s.sr, s.er, u * 1.6, u * 1.5, u * 0.85, 1, s.thumb || 0);
    // cabeça
    g.save(); g.translate(0, -bh - u * 0.1); g.rotate(rad(s.head));
    const hr = u * 2.25;
    g.fillStyle = hero.skin; g.beginPath(); g.ellipse(0, -hr, hr * 1.02, hr, 0, 0, 7); g.fill(); g.stroke();
    // cabelo
    g.fillStyle = hero.hair;
    if (hero.hairStyle === 'cap') { g.beginPath(); g.ellipse(0, -hr * 1.35, hr * 1.05, hr * 0.75, 0, Math.PI, 0); g.fill(); g.stroke(); roundRect(g, 0, -hr * 1.42, hr * 1.4, hr * 0.28, hr * 0.14); g.fill(); g.stroke(); }
    else if (hero.hairStyle === 'bob') { g.beginPath(); g.ellipse(0, -hr * 1.15, hr * 1.12, hr * 0.98, 0, Math.PI * 0.95, Math.PI * 2.05); g.fill(); g.stroke(); }
    else { g.beginPath(); g.moveTo(-hr * 0.95, -hr * 1.25); g.quadraticCurveTo(-hr * 0.4, -hr * 2.35, hr * 0.15, -hr * 1.95); g.quadraticCurveTo(hr * 0.55, -hr * 2.45, hr * 0.98, -hr * 1.3); g.quadraticCurveTo(0, -hr * 1.7, -hr * 0.95, -hr * 1.25); g.fill(); g.stroke(); }
    // rubor
    if (s.blush > 0.02) { g.fillStyle = `rgba(232,115,122,${0.45 * s.blush})`; for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(sx * hr * 0.55, -hr * 0.72, hr * 0.2, hr * 0.12, 0, 0, 7); g.fill(); } }
    // olhos (olhar + piscada) e sobrancelhas (emoção)
    const ey = -hr * 1.1, ex = hr * 0.38, er = hr * 0.2 * s.eye;
    for (const sx of [-1, 1]) {
      g.save(); g.translate(sx * ex, ey); g.scale(1, s.blink);
      g.fillStyle = '#fff'; g.beginPath(); g.ellipse(0, 0, er, er * 1.15, 0, 0, 7); g.fill(); g.stroke();
      g.fillStyle = ol; g.beginPath(); g.arc(s.lookX * er * 0.45, s.lookY * er * 0.45, er * 0.5, 0, 7); g.fill();
      g.restore();
      g.save(); g.translate(sx * ex, ey - er * 1.55 + s.bY * hr * 0.25); g.rotate(sx * rad(s.bA));
      g.lineWidth = u * 0.32; g.beginPath(); g.moveTo(-er * 0.95, 0); g.lineTo(er * 0.95, 0); g.stroke(); g.restore();
    }
    // boca
    g.save(); g.translate(hr * 0.02, -hr * 0.52); mouthShape(g, hero, s.mouth, hr * 0.62, s.smile); g.restore();
    // suor (pânico/preocupado): gotas que escorrem em loop determinístico
    if (s.sweat > 0.05) {
      for (let k = 0; k < 2; k++) {
        const ph = ((s._t || 0) * 0.9 + k * 0.5) % 1;   // função de t: escorre em loop
        const sx = (k ? -1 : 1) * hr * 0.95, sy = -hr * 1.5 + ph * hr * 0.9, a = s.sweat * (1 - ph);
        g.save(); g.globalAlpha *= a; g.fillStyle = '#7CC8F2'; g.beginPath(); g.moveTo(sx, sy - hr * 0.22);
        g.quadraticCurveTo(sx + hr * 0.13, sy, sx, sy + hr * 0.09); g.quadraticCurveTo(sx - hr * 0.13, sy, sx, sy - hr * 0.22); g.fill(); g.stroke(); g.restore();
      }
    }
    g.restore(); g.restore(); g.restore();
  }

  // Folha de aprovação do personagem: poses na 1ª linha, bocas na 2ª. Aprove UMA vez e trave hero/.
  function sheet(g, hero, W, H, bg) {
    g.fillStyle = bg || '#F4EDE4'; g.fillRect(0, 0, W, H);
    const poses = Object.keys(POSES), mouths = 'XABCDEFGH'.split(''), cw = W / poses.length;
    g.font = `600 ${Math.round(W / 60)}px ui-monospace,monospace`; g.textAlign = 'center'; g.fillStyle = '#333';
    poses.forEach((p, i) => {
      const s = state(0, hero, [{ t: -9, pose: p, emotion: p === 'panic' ? 'panic' : p === 'surprised' ? 'surprised' : p === 'thumbs_up' ? 'happy' : 'neutral' }], null);
      s._t = 0.3; draw(g, hero, s, cw * (i + 0.5), H * 0.5, H * 0.3); g.fillStyle = '#333'; g.fillText(p, cw * (i + 0.5), H * 0.57);
    });
    const mw = W / mouths.length;
    mouths.forEach((m, i) => {
      const s = state(0, hero, [{ t: -9, pose: 'idle', emotion: 'neutral' }], null); s.mouth = m;
      g.save(); g.beginPath(); g.rect(mw * i, H * 0.6, mw, H * 0.4); g.clip();
      draw(g, hero, s, mw * (i + 0.5), H * 1.55, H * 0.85); g.restore(); g.fillStyle = '#333'; g.fillText(m, mw * (i + 0.5), H * 0.98);
    });
  }

  root.R = { POSES, EMO, state, draw, sheet };
})(typeof window !== 'undefined' ? window : globalThis);
