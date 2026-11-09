// CENA 03 — A METÁFORA: "um CRM é um caderno que nunca esquece". O checklist marca cada item quando o Léo FALA a palavra.
SCENE['03'] = {
  keys: [{ at: 0, pose: 'point', emotion: 'happy', look: [0.9, 0] }],
  cues: [{ word: /^anota/i, type: 'ding', gain: 0.5, pitch: 1.0 }, { word: /^lembra/i, type: 'ding', gain: 0.5, pitch: 1.12 }, { word: /^cobra/i, type: 'ding', gain: 0.55, pitch: 1.26 }],
  draw(g, lt, { W, H, u, L, P, t, FLOOR, sc, wordTime, drawHero, DISPLAY }) {
    drawHero(t, L.cx - 260 * u, FLOOR, 760 * u);
    // caderno abre: capa gira (escala X) e a página aparece
    const open = M.springZ(lt - 0.15, 0.75, 2.2), x0 = L.cx + 30 * u, y0 = FLOOR - 1100 * u, w = 420 * u, h = 560 * u;
    g.save(); g.translate(x0, y0); g.rotate(0.05);
    g.fillStyle = P.light; g.strokeStyle = P.ink; g.lineWidth = 6 * u; M.rrect(g, 0, 0, w, h, 26 * u); g.fill(); g.stroke();
    g.fillStyle = P.second; M.rrect(g, 0, 0, 34 * u, h, 14 * u); g.fill();
    g.fillStyle = P.ink; g.font = `900 ${44 * u}px ${DISPLAY}`; g.textBaseline = 'middle'; g.fillText('CRM', 70 * u, 70 * u);
    const itens = [['ANOTA', /^anota/i], ['LEMBRA', /^lembra/i], ['COBRA', /^cobra/i]];
    itens.forEach(([txt, re], k) => {
      const tw = wordTime(re), at = tw == null ? sc.start + 1 + k * 0.6 : tw, y = 170 * u + k * 120 * u;
      g.strokeStyle = P.ink; g.lineWidth = 6 * u; M.rrect(g, 60 * u, y - 34 * u, 68 * u, 68 * u, 14 * u); g.stroke();
      g.fillStyle = P.ink; g.font = `800 ${50 * u}px ${DISPLAY}`; g.fillText(txt, 160 * u, y + 2 * u);
      const p = M.springZ(t - at, 0.8, 4);                                   // tique desenha no instante da palavra
      if (p > 0.001) { g.strokeStyle = P.second; g.lineWidth = 12 * u; g.lineCap = g.lineJoin = 'round';
        M.drawPartial(g, [[72 * u, y], [92 * u, y + 22 * u], [134 * u, y - 30 * u]], p); FX.sparkles(g, t, at, 100 * u, y, 8, k + 3, P.accent); }
    });
    // capa por cima, abrindo para a esquerda
    if (open < 0.999) { g.save(); g.scale(Math.max(0, 1 - open), 1); g.fillStyle = P.second; g.strokeStyle = P.ink; M.rrect(g, 0, 0, w, h, 26 * u); g.fill(); g.stroke();
      // capa legível (sem isso o caderno fechado vira "retângulo vazio" no frame da transição)
      g.fillStyle = P.light; M.rrect(g, w * 0.2, h * 0.34, w * 0.6, h * 0.2, 16 * u); g.fill();
      g.fillStyle = P.ink; g.font = `900 ${64 * u}px ${DISPLAY}`; g.textAlign = 'center'; g.fillText('CRM', w / 2, h * 0.44); g.textAlign = 'left'; g.restore(); }
    g.restore();
  },
};
