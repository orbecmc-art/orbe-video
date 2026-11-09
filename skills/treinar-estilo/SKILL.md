---
name: treinar-estilo
description: "Comando /treinar-estilo — treina um ESTILO DE EDIÇÃO a partir de uma pasta de vídeos de referência (as melhores edições do cliente, da Orbe ou que o cliente admira): mede ritmo, cortes, rosto, paleta e animações, monta livro de regras, lookbook e preset, e faz o teste de fidelidade antes de usar em cliente. Use quando digitarem /treinar-estilo ou pedirem \"aprende o estilo desses vídeos\", \"edita igual a esses\", \"cria um estilo nosso\"."
---

# /treinar-estilo — estilo próprio a partir de referências

Use a skill **edita-video** (`S=../edita-video/scripts`); leia `references/variacoes-e-formatos.md` (seção estilo
treinado) e `references/ritmo-e-batidas.md`.

1. Junte as referências numa pasta (5–15 vídeos; Instagram/TikTok com login → peça os arquivos). Pergunte: **nome do
   estilo**, **de qual cliente** (kit) e **de qual preset ele herda** (minimal · dinâmico · dossiê · educativo ·
   podcast-pb · clínica · luxo · varejo).
2. `python3 $S/estudar_estilo.py <pasta> --nome <estilo> --base <preset> [--kit <kit do cliente>]`
3. **Abra** `planos/*.jpg`, `animacoes/*.jpg` e `LOOKBOOK.jpg`. Preencha `REGRAS.md` (as 5 chaves: legenda,
   capítulos/listas, pops e contadores, gancho, telas cheias; tipografia, cantos, sombra, curvas, velocidades) e
   `ANIMACOES.md` (o que é, entrada, curva, batida). Traduza em `preset.json` (legendas, câmera, cor, ritmo, batidas,
   junções) — números, não adjetivos.
4. **Teste de fidelidade**: escolha 5–10 s de uma referência, recrie com um vídeo do cliente no estilo novo e gere a
   prévia lado a lado (ffmpeg hstack). Ajuste até a gramática ficar indistinguível. Só então use em cliente
   (`briefing.py <projeto> estilo=<estilo>`).
5. Referência ensina gramática; nunca copiar texto, marca, foto ou peça de alguém.
