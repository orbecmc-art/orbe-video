---
name: novo-motion
description: "Comando /novo-motion — cria um vídeo de motion graphics do zero (sem filmagem) pela skill motion-studio, com as perguntas de direção (objetivo, formato, duração, marca, referência, som) antes de animar. Use quando o usuário digitar /novo-motion ou pedir um motion/vídeo animado novo."
---

# /novo-motion

1. Carregue a skill **motion-studio** deste plugin (pasta irmã `../motion-studio`; leia o `SKILL.md` dela).
2. **Estilo primeiro**: mande o link da galeria (`../../galeria.json` → `url`) — a pessoa escolhe um estilo e cola o
   pedido ("/novo-motion no estilo poster-suico"), ou manda 1–3 referências, ou diz "escolhe você" (escolha pelo
   assunto e diga por quê). O `estilos/<id>/ESTILO.md` vira lei (motion-studio/references/galeria.md).
   **Documentário** (história, linha do tempo, "como nasceu", caso contado com lugar e data) → estilo
   `documentario-continuo`: pergunte a VOZ (gravar ou Piper), o MUNDO (mapa de onde? mesa? quadro?), o MATERIAL REAL
   (fotos e documentos que existem — peça a lista) e o formato (9:16, 16:9 ou 21:9); escreva roteiro.json, gere a
   voz e mostre docs/BATIDAS.md para aprovação ANTES de animar.
3. Perguntas antes de animar (`AskUserQuestion`, pule o que o pedido já disse): **objetivo** (lançamento · anúncio ·
   explicar · institucional · série com personagem) · **formato** (9:16 · 1:1 · 16:9 · vários) · **duração**
   (6–10 s · 15 s · 30 s · 60 s) · **REFERÊNCIA** (link/arquivo · kit do cliente · nenhuma) · **som** (trilha + SFX ·
   só trilha · mudo) · e em texto: marca/kit, texto/dados que o vídeo diz (com fonte do cliente), CTA.
4. Siga o fluxo da motion-studio (modo e nível → direção em números → projeto → som primeiro → storyboard → construir →
   olhar e medir → render + QA → entregar e registrar).
   Cards parados aprovados antes de animar; 3 quadros com nota 1–10 (≥ 8) antes do render; no fim
   `pericia_movimento.py final.mp4 --contra <referência>`.
5. Regra Orbe: fonte/crédito de dado NUNCA na tela (vai para o LEIA-ME e a legenda do post), salvo pedido.
