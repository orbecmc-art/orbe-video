---
name: variacoes
description: "Comando /variacoes — cria VARIAÇÕES DE TESTE de um vídeo já editado (trial reels do Instagram, criativos A/B do Meta Ads): abertura nova, sem setup, versão curta, versão para ver sem som, abertura em P&B com cor revelada — cada uma com hipótese, métrica e prévia lado a lado com o master. Use quando digitarem /variacoes ou pedirem \"faz versões para testar\", \"trial reels\", \"variações do criativo\", \"teste A/B desse vídeo\"."
---

# /variacoes — variações de teste com hipótese e métrica

Use a skill **edita-video** (`S=../edita-video/scripts`), em um projeto já editado e aprovado (tem `renders/*_vNN.mp4`).
Leia `../edita-video/references/variacoes-e-formatos.md`.

1. Pergunte (uma rodada de `AskUserQuestion`): **onde vai rodar** (trial reels · anúncio Meta · os dois) · **quais
   variações** (multiSelect: direto — corta o setup · abertura — gancho novo · mudo — para quem vê sem som · pb-cor —
   gancho visual · micro — só a demonstração) · **texto do gancho novo** (opcional; senão sai da 1ª frase) · para
   micro, **quais linhas** (F### de docs/FRASES.md).
2. `python3 $S/variacoes.py <projeto> --receitas <lista> [--gancho "..."] [--linhas F004-F009] [--setup F002-F003]`
3. **Abra** cada `entregas/variacoes/previa-<receita>.mp4` (lado a lado com o master): a variação tem que parecer
   OUTRO vídeo nos 3 s iniciais — se parece repost, mude mais (abertura, gráfico ou estrutura).
4. Entregue os MP4 + `VARIACOES.md` (hipótese, métrica, regra do vencedor: ≥ 5 pontos de skip rate ou 1,5× por mil;
   no máximo 5 trial reels por dia; empurrar o vencedor em 48 h). Quando os números voltarem, registre o aprendizado:
   `python3 $S/estado.py <projeto> aprendizado "<o que venceu e por quê>"`.
