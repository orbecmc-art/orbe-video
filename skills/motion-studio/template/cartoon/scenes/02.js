// CENA 02 — O PROBLEMA EM IMAGEM: balões caem e soterram; Léo em pânico (suor, sobrancelha, pulos nas palavras fortes).
SCENE['02'] = {
  keys: [{ at: 0, pose: 'panic', emotion: 'panic', look: [0.4, -0.8] }],
  cues: Array.from({ length: 7 }, (_, i) => ({ at: 0.2 + i * 0.32 + 0.42, type: 'pop', gain: 0.35, pitch: 0.85 + i * 0.07 })),
  draw(g, lt, { W, H, u, L, P, t, FLOOR, drawHero }) {
    const floor = FLOOR, R = M.rng(42);
    g.fillStyle = P.bg2; M.rrect(g, 60 * u, floor, W - 120 * u, 40 * u, 20 * u); g.fill();
    drawHero(t, L.cx - 230 * u, floor, 800 * u);
    // balões: queda balística fechada até a altura da pilha, depois assentam com spring (squash no pouso)
    const N = 14;
    for (let i = 0; i < N; i++) {
      const col = i % 3, row = Math.floor(i / 3), x = L.cx + 70 * u + col * 150 * u + (R() - 0.5) * 50 * u, rot = (R() - 0.5) * 0.35;
      const t0 = 0.05 + i * 0.11, yT = floor - 70 * u - row * 128 * u, y0 = -200 * u, gr = 5200 * u;
      const tf = Math.sqrt((2 * (yT - y0)) / gr), a = lt - t0; if (a < 0) continue;
      let y, sq = 0; if (a < tf) y = y0 + 0.5 * gr * a * a; else { y = yT; sq = 0.22 * Math.exp(-(a - tf) * 12) * Math.cos((a - tf) * 26); }
      g.save(); g.translate(x, y); g.rotate(rot * Math.min(1, a / tf)); g.scale(1 + sq, 1 - sq);
      g.fillStyle = i % 2 ? '#CFE9D9' : '#E7E1EF'; g.strokeStyle = P.ink; g.lineWidth = 5 * u;
      M.rrect(g, -120 * u, -52 * u, 240 * u, 104 * u, 34 * u); g.fill(); g.stroke();
      g.fillStyle = 'rgba(30,27,46,.35)'; M.rrect(g, -88 * u, -18 * u, 150 * u, 14 * u, 7 * u); g.fill(); M.rrect(g, -88 * u, 10 * u, 100 * u, 14 * u, 7 * u); g.fill();
      g.restore();
    }
  },
};
