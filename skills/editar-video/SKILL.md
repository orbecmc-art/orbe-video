---
name: editar-video
description: "Comando /editar-video — começa a edição completa de um vídeo gravado pela sequência fixa de perguntas (onde vai postar, duração, estilo, REFERÊNCIA, legendas, motion, B-roll, som, marca, CTA) e conduz o fluxo da skill edita-video até a v01 medida. Use quando o usuário digitar /editar-video ou pedir para \"editar com as perguntas\"."
---

# /editar-video

1. Carregue a skill **edita-video** deste plugin (pasta irmã `../edita-video`; leia o `SKILL.md` dela e, agora,
   `references/perguntas.md` e `references/fluxo.md`). Todos os comandos usam `S=<pasta da edita-video>/scripts`.
2. Ache os brutos: anexos da conversa, pasta conectada do computador (prefira trabalhar lá se o vídeo for > 3 min ou 4K)
   ou peça os arquivos. Sem vídeo, não comece.
3. Faça as **perguntas fixas** na ordem do `perguntas.md`: rodada 1 (formato · duração · estilo — com o link da
   galeria de `../../galeria.json` — · REFERÊNCIA), rodada 2 (legendas · motion · B-roll · som) e a do plano (página
   linha a linha · Claude decide · mapa no chat) com `AskUserQuestion`, depois um texto livre (marca/kit · CTA · nomes e termos ·
   o que não pode). Pule só o que o pedido já respondeu — a referência é sempre perguntada. Ninguém respondendo:
   padrões do `perguntas.md` + "assumi: …".
4. `bash $S/novo.sh <pasta> [--cliente <kit>] --brutos <arquivos>` → `python3 $S/briefing.py <pasta> chave=valor …`
   → referência, se houver: `python3 $S/referencia.py <pasta> <link|arquivo>` (abra as folhas, preencha "O que eu vi").
5. Siga o fluxo do `SKILL.md` da edita-video com os portões: ① cortes (com rascunho) ② plano/mapa (página de plano
   quando escolhida: `plano.py`) ③ v01. Motion via
   motion-studio (a ponte já chama). Abra todas as folhas antes de mostrar. Notas faladas no bruto ("abre nota …
   fecha nota") viram direção do plano (docs/NOTAS_FALADAS.md). Antes do render, `ritmo.py .` (batidas, ritmo e
   junções do estilo) sem ✗.
6. Entregue em 3–4 linhas (`docs/ENTREGA.md`) com o MP4 (e .srt/capa) e explique como pedir ajuste por número.
   Ofereça numa linha: revisão do cliente no navegador e/ou kit aberto para Premiere, Final Cut, DaVinci, CapCut ou
   celular (`/exportar-video`). Vai para anúncio ou trial reel: ofereça `/variacoes`. Deu certo: `formato.py . salvar`.
