# Documentário contínuo — o que trocar e o que quebra

- **Copie a pasta `projeto/`** para o projeto novo e troque `roteiro.json` (falas, objetos, câmera por fala, paleta).
- **Outro lugar do mundo**: `npm pack world-atlas@2.0.2 datamaps@0.5.9` numa pasta própria e
  `python3 scripts/preparar_mapa.py --world <countries-50m.json> --brasil <datamaps.bra.js> --bbox lon0,lat0,lon1,lat1`
  (Europa: `-12,34,32,60`; o `--brasil` só serve para estados do Brasil). Ajuste `mundo.centro` e `mundo.escala`.
- **Mundo que não é mapa** (mesa, quadro de cortiça): troque a função `mapa()` do filme.js por uma textura de mesa
  (kraft/madeira do estilo dossiê) — objetos, câmera e regras continuam iguais.
- **Voz**: grave você (audio/linhas/<id>.wav, melhor para cliente) ou deixe o Piper; `scripts/narrar.py` mede tudo.
- **Rode sempre**: `narrar.py` → `tabela.py` (aprovar docs/BATIDAS.md) → stills + VALIDATE → render → sfx → trilha → mix.
- **Quebra se**: dois papéis caem no mesmo lugar (espalhe lon/lat — a câmera precisa viajar entre eles); `larg` pequeno
  (título do papel < 18 px na tela — o VALIDATE avisa); uma fala tem dois heróis; a câmera de uma fala aponta para longe
  demais do herói (vira chicote); palavra do gesto não existe na fala (o gesto cai no começo dela).
- **Render**: ~35 s em 9:16 levam alguns minutos com motion blur adaptativo; `--sub 2` para rascunho.
