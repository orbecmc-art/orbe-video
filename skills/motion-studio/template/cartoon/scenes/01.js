// CENA 01 — GANCHO: pergunta que dói. Frame 0 já "alto": texto na tela, Léo surpreso, celular vibrando.
SCENE['01'] = {
  keys: [{ at: 0, pose: 'surprised', emotion: 'surprised', look: [0.5, -0.7] }, { at: 1.6, pose: 'shrug', emotion: 'worried', look: [-0.2, 0] }],
  cues: [{ at: 0.3, type: 'glitch', gain: 0.25 }, { at: 1.1, type: 'glitch', gain: 0.25 }],
  draw(g, lt, { W, H, u, L, P, t, FLOOR, drawHero, DISPLAY }) {
    g.fillStyle = P.bg2; g.beginPath(); g.arc(L.cx, FLOOR - 560 * u, 520 * u, 0, 7); g.fill();          // "palco" atrás do herói
    if (lt < 0.45) FX.speedLines(g, t, L.cx, FLOOR - 580 * u, 26, 5, P.light, W, H);
    // celular gigante vibrando em pulsos (rotação em 30 Hz só durante o pulso)
    const pulse = [0.15, 0.95, 1.75].reduce((a, p0) => a + (lt > p0 && lt < p0 + 0.35 ? 1 : 0), 0);
    const rot = pulse ? 0.035 * Math.sin(lt * 2 * Math.PI * 30) : 0;
    g.save(); g.translate(L.cx + 250 * u, FLOOR - 470 * u); g.rotate(-0.12 + rot); g.scale(0.82, 0.82);
    g.fillStyle = P.ink; M.rrect(g, -190 * u, -340 * u, 380 * u, 680 * u, 56 * u); g.fill();
    g.fillStyle = P.light; M.rrect(g, -168 * u, -312 * u, 336 * u, 624 * u, 40 * u); g.fill();
    for (let k = 0; k < 6; k++) { const w = (180 + ((k * 53) % 110)) * u; g.fillStyle = k % 2 ? '#CFE9D9' : '#E7E1EF';
      M.rrect(g, (k % 2 ? 150 * u - w : -150 * u), -270 * u + k * 92 * u, w, 66 * u, 22 * u); g.fill(); }
    const n = M.count(t, 99, 0.1, 'heavy', 12);
    const bs = 1 + 0.12 * M.pulse(lt, [0.15, 0.95, 1.75], 10);
    g.save(); g.translate(150 * u, -320 * u); g.scale(bs, bs); g.fillStyle = P.danger; g.beginPath(); g.arc(0, 0, 70 * u, 0, 7); g.fill();
    g.fillStyle = '#fff'; g.font = `900 ${58 * u}px ${DISPLAY}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(n >= 99 ? '99+' : String(n), 0, 4 * u); g.restore();
    g.restore();
    drawHero(t, L.cx - 140 * u, FLOOR, 800 * u);
  },
};
