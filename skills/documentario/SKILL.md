---
name: documentario
description: "Comando /documentario — vídeo DOCUMENTÁRIO em um plano-sequência sobre um mundo só (mapa real, mesa, quadro): a câmera desliza entre documentos, recortes, fotos reais, rotas e anos gigantes, com a voz guiando o tempo e cada gesto (círculo, carimbo) caindo na palavra. Tudo em código, sem gerador de vídeo. Use quando digitarem /documentario ou pedirem \"vídeo estilo documentário\", \"conta a história de…\", \"linha do tempo animada\", \"nível Netflix\"."
---

# /documentario — documentário contínuo (motion-studio)

Use a skill **motion-studio**, estilo `estilos/documentario-continuo/` (leia `ESTILO.md` e `LEIA-ME.md`; o prompt de
direção está em `projeto/docs/PROMPTS.md`).

1. Perguntas (uma rodada de `AskUserQuestion`): **a história** (o que aconteceu, em 5–10 frases curtas) · **a voz**
   (gravo eu · Piper pt-BR · ElevenLabs/VoiceStudio — chave só no .env) · **o mundo** (mapa de onde · mesa · quadro de
   cortiça) · **formato** (9:16 · 16:9 · 21:9 cinema). Depois peça o MATERIAL REAL: fotos e documentos que existem (do
   cliente). Datas e números: confira em fonte antes de escrever.
2. Copie `projeto/` para `estudio/motion/<data>-<nome>/`, escreva `roteiro.json` (uma fala = UM herói; objetos
   espalhados no mapa para a câmera viajar), gere o mapa da região se não for o Brasil (`scripts/preparar_mapa.py`).
3. `python3 scripts/narrar.py` → `python3 scripts/tabela.py` → mostre **docs/BATIDAS.md** e pergunte o que estiver
   vago. Só anime depois do "ok".
4. Stills de cada batida + `window.VALIDATE()` vazio (câmera sem parada nem tranco, herói único, nada repetido, tipo
   grande) → render (`render.mjs`, motion blur adaptativo) → `sfx.mjs --page` → `music.mjs --style piano` → `mix.sh`
   com `--voice` (−14 LUFS).
5. Entregue o MP4 + a tabela de batidas. Revisões por batida ("f5: segura mais", "f7: a rota mais lenta").
