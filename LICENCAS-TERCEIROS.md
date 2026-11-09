# Licenças de terceiros

## claude-video (Felipe Borges) — usado em motion-studio/estilos/, motion-studio/references/galeria.md e edita-video/scripts/pericia_movimento.py

Origem: https://github.com/Felpborges/claude-video (fichas de estilo, código das peças de referência e a perícia de movimento; adaptados). Os vídeos de motion da galeria (`galeria/videos/m-*.mp4`, exceto `m-dossie-de-dados` e `m-serie-personagem`, que são da Orbe) também vêm dessa biblioteca.

```
MIT License

Copyright (c) 2026 Felipe Borges (claude-video)
Copyright (c) 2026 Claude Video Studio contributors (estrutura e scripts da skill original "Claude Video 2.0", MIT; ver LICENSE-original.txt)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```
MIT License

Copyright (c) 2026 Claude Video Studio contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Dados de mapa e fontes do estilo documentário (motion-studio/estilos/documentario-continuo/projeto)
- `mapa.js` é derivado de **Natural Earth** 1:50m (domínio público) via o pacote npm **world-atlas** 2.0.2
  (ISC, © 2013-2019 Michael Bostock) e de **datamaps** 0.5.9 (MIT, © Mark DiMarco) para os estados do Brasil —
  contornos decodificados, recortados e simplificados por `scripts/preparar_mapa.py`. O código desses pacotes não vem junto.
- Fontes em `projeto/fonts/`: Cormorant Garamond, IBM Plex Mono, Courier Prime e Inter Tight — SIL Open Font License 1.1
  (via @fontsource). Podem ser usadas, embutidas e redistribuídas com o software; não podem ser vendidas sozinhas.
- Voz da demonstração: Piper (MIT) com a voz pt_BR "faber" (modelo do projeto Piper/rhasspy). Para cliente, prefira voz
  gravada ou contratada.

## Métodos estudados (sem código copiado)
O método de ritmo, batidas, junções e packs de estilo foi aprendido no Style Studio (videoeditskill.synteq.app) e nos
vídeos de Joseph (Video Editing), Zane Hoyer, LABS, Stockton Walbeck, Grow with Alex, Mateus Dias, Rourke e Enrique
Marq. Nenhum arquivo, texto ou peça deles foi incluído: as regras foram reescritas e reimplementadas pela Orbe.

## Fontes novas (1.5) — todas SIL Open Font License 1.1, via @fontsource (npm)
- Great Vibes (TypeSETit) — manuscrita dos rótulos do estilo lifestyle.
- EB Garamond (Georg Duffner, Octavio Pardo) — legenda micro.
- Manrope (Mikhail Sharanda) — sans do estilo lifestyle.
- Inter Tight (Rasmus Andersson) — legenda em escada do estilo entrevista.

## Referências estudadas em 1.5 (sem código, imagem ou texto copiados)
Reels públicos de @daniirramoss, @nicomonteiroo e @bryanhynes, vistos no navegador para medir ritmo, tipografia,
posição e som. Nenhum quadro, áudio ou texto deles está no plugin; a galeria só aponta o link do original.

## Edits de carro e cinema (1.6)
- Fontes do `montagem.py` (baixadas no projeto por `fontes.py`, SIL Open Font License 1.1 via @fontsource): Courier Prime
  (máquina de escrever), Cormorant Garamond (cartela em serifa) e Inter Tight (títulos e fim).
- Referências estudadas (sem código, quadro, áudio ou texto copiados): posts públicos de @h.vzls, @shotbykinetic,
  @loris.cataldo e @f1rstmotors, vistos no navegador para medir cortes, batidas, cor e som. A galeria só aponta o link.
- Exemplos da galeria: fotos e takes da Rivoli Concept (cliente da Orbe), usados com o material cedido pelo cliente.
  Trilhas dos exemplos geradas pelo `music.mjs` (livres).
