// CENA 04 — VIRADA + CTA: carimbo "FECHOU!" em camadas (flash ≤ 0,6, ondas, faíscas, tremor). Fecha rimando com a abertura.
SCENE['04'] = {
  keys: [{ at: 0, pose: 'thumbs_up', emotion: 'happy', look: [0, 0] }, { at: 1.4, pose: 'wave', emotion: 'happy', look: [0, 0] }],
  cues: [{ at: 0.05, type: 'thump', gain: 0.7 }],
  draw(g, lt, { W, H, u, L, P, t, FLOOR, drawHero, DISPLAY }) {
    const [sx, sy] = FX.shake(lt, 0.05, 22 * u, 8);
    g.save(); g.translate(sx, sy);
    g.fillStyle = P.bg2; g.beginPath(); g.arc(L.cx, FLOOR - 640 * u, 560 * u, 0, 7); g.fill();
    FX.shockwave(g, lt, 0.05, L.cx + 190 * u, FLOOR - 930 * u, 620 * u, P.accent, 2);
    // o celular volta pequeno e calmo — o último frame rima com o primeiro
    const ph = M.springZ(lt - 0.5, 0.7, 2.5);
    g.save(); g.translate(L.cx + 300 * u, FLOOR - 380 * u); g.rotate(0.12); g.scale(0.32 * ph, 0.32 * ph);
    g.fillStyle = P.ink; M.rrect(g, -190 * u, -340 * u, 380 * u, 680 * u, 56 * u); g.fill(); g.fillStyle = P.light; M.rrect(g, -168 * u, -312 * u, 336 * u, 624 * u, 40 * u); g.fill();
    g.fillStyle = P.second; g.beginPath(); g.arc(0, 0, 90 * u, 0, 7); g.fill(); g.restore();
    drawHero(t, L.cx - 100 * u, FLOOR, 780 * u);
    FX.stamp(g, lt, 0.05, 'FECHOU!', L.cx + 190 * u, FLOOR - 930 * u, 104 * u, P.accent, `900 ${104 * u}px ${DISPLAY}`);
    FX.sparkles(g, lt, 0.1, L.cx + 190 * u, FLOOR - 930 * u, 12, 9, P.light);
    g.restore();
    FX.flash(g, lt, 0.05, W, H, '#FFFFFF', 0.12);
  },
};
