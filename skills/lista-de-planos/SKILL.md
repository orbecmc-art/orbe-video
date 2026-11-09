---
name: lista-de-planos
description: "Comando /lista-de-planos — monta a LISTA DE PLANOS (decupagem) para o cliente gravar sozinho com o celular antes da edição: cada plano com ação, função (estabelece, detalhe, reação, POV, transição), esquema de onde pôr o celular, dica e tempo de gravação, validado pela gramática de montagem (corte na ação, match cut, perspectiva forçada). Gera a página para mandar ao cliente. Use quando digitarem /lista-de-planos ou pedirem roteiro de gravação, decupagem, \"o que eu gravo?\", \"lista de takes\", B-roll do próprio cliente ou bastidores."
---

# /lista-de-planos — o que gravar, de onde e para quê

Use a skill **edita-video** (`S=../edita-video/scripts`). Leia `../edita-video/references/decupagem.md`.

1. Pergunte (uma rodada de `AskUserQuestion`): **o que o vídeo conta** (texto livre, 1 frase) · **onde grava**
   (clínica · loja · escritório · restaurante · imóvel · produto na mão · história livre) · **tem fala?** (talking head +
   cobertura · história sem fala) · **duração** (15 · 30 · 45 · 60 s). Quem aparece e se há paciente (só com autorização
   por escrito).
2. `python3 $S/planos.py <pasta do cliente ou projeto> modelo <contexto> --titulo "…" --alvo <s>`
3. Escreva em `_edit/planos.json` a AÇÃO concreta de cada plano contando uma história (lugar → trabalho/problema com
   detalhe e reação → resultado). Ajuste a ordem, as cenas e os tipos (catálogo em `../edita-video/assets/planos.json`).
4. `python3 $S/planos.py <pasta> --cliente "…"` — resolva os avisos (cena sem plano que estabelece, ação com um ângulo
   só, falta detalhe/reação, plano repetido).
5. Publique `docs/planos/index.html` como Artifact (página do cliente, com caixinhas "gravado") e dê o link. Mostre em
   3 linhas: quantos planos, quanto tempo de gravação, o que não pode faltar.
6. Quando os vídeos chegarem, siga com `/editar-video` usando a lista como roteiro do mapa (cada plano = um B-roll
   `"arquivo"` na ordem; bastidor/aula: `rotulo` `estilo: tecnico` com o nome da etapa).
