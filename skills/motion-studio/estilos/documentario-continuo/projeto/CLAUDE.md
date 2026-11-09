# Projeto: documentário contínuo (motion-studio)

Leia `../ESTILO.md` antes de mexer. O filme é `filme.js` (motor) + `roteiro.json` (o que contar) + `narracao.js` (o
relógio = a voz) + `mapa.js` (o mundo). Nunca escreva texto de cena no filme.js — tudo vem do roteiro.

## Ordem
1. `roteiro.json`: falas (texto falado, `heroi`, `camera`, `ano`) e objetos (cidade, estado, documento, recorte,
   planta, rota, numero). Gestos na palavra: `heroi.circulo.palavra`, `heroi.troca.palavra`, `heroi.carimbo.palavra`.
2. `python3 scripts/narrar.py [--modelo voz.onnx]` → audio/voice.wav + narracao.js.
3. `python3 scripts/tabela.py` → roteiro.js + docs/BATIDAS.md → **aprovação do usuário**.
4. Stills (uma por fala) + `window.VALIDATE()` vazio.
5. `node ../../../scripts/render.mjs index.html --out out/silent.mp4 --sub 4` (o caminho do motion-studio pode variar:
   use o scripts/ da skill) → `sfx.mjs --page index.html` → `music.mjs --style piano` → `mix.sh` com `--voice`.

## Regras do estilo (resumo)
Um herói por fala · cada frase uma vez · corpo de papel em linhas cinza · tipo grande (herói ≥ 60 px, rótulo ≥ 22 px na
tela) · menos é mais · gesto na palavra · câmera nunca para e nunca dá tranco · material real (fotos/documentos do
cliente; nada de foto de pessoa pública baixada da web; nada de manchete inventada).
