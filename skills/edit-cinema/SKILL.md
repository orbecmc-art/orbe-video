---
name: edit-cinema
description: "Comando /edit-cinema — monta EDIT CINEMATOGRÁFICO sem fala a partir de takes de VÍDEO (foto só de apoio): carro à venda, concessionária, produto, aftermovie de evento, imóvel. Receitas estudadas em referências reais (cinema lento, ritual de detalhes com crescendo, \"vire o celular\" em 16:9 girado com legenda de máquina de escrever, aftermovie e ASMR só com som real): corte na batida medida, câmera lenta em take de 60 qps, flash/whip/zoom, cor de cinema, grão, cartela preta antes da queda e fim com a marca. Use quando digitarem /edit-cinema ou pedirem \"edit de carro\", \"vídeo cinematográfico\", \"edit no beat\", \"aftermovie\", \"vídeo do carro para vender\"."
---

# /edit-cinema — takes de vídeo montados na batida

Use a skill **edita-video** (`S=../edita-video/scripts`). Leia `../edita-video/references/edit-cinema.md`.

1. Ache o material: anexos, pasta conectada ou Drive do cliente (vídeos ≤ ~6 MB passam pelo conector; maiores, peça a
   pasta do computador ou o arquivo — nunca troque os takes grandes pelos que couberam). Sem VÍDEO (só fotos), pare e
   avise: foto com zoom vira slide; ofereça `/lista-de-planos` (o que gravar). Sem material, idem.
2. Pergunte (uma rodada de `AskUserQuestion`): **receita** (cinema lento · ritual de detalhes · vire o celular ·
   aftermovie · ASMR) · **duração** (15 · 20 · 30 s) · **trilha** (gerada livre · a do cliente · sem trilha, para pôr no
   app) · **texto** (nenhum · legenda curta de máquina de escrever · título). Depois, em texto livre: modelo/produto e
   marca do fim, REFERÊNCIA (link), o que não pode aparecer (placa, pessoa, logo). Ninguém respondendo: a receita que
   o material permite (takes de um carro → cinema lento; takes de evento → aftermovie), 20 s, trilha gerada, sem texto — e diga
   "assumi: …".
3. `python3 $S/montagem.py <pasta do projeto> takes <pasta do material>` → ABRA as folhas `docs/folhas/takes_*.jpg`
   e leia `docs/TAKES.md` (qps, som, movimento). Escolha: o que estabelece, os detalhes, o herói. Descarte tremido,
   desfocado, placa de terceiros, gente sem autorização.
4. Escreva `_edit/montagem.json` pela receita (`edit-cinema.md`): durações em batidas, `foco` no assunto de cada
   plano, transições com motivo, cor, fim com modelo + marca. Texto só o que o cliente disse ou aprovou; nenhum dado
   técnico inventado; sem fonte/crédito na tela.
5. `python3 $S/montagem.py <pasta> --rascunho` → abra `docs/folhas/montagem.jpg` e o `docs/MONTAGEM.md` (cortes fora
   da batida, LUFS, pico). Corrija enquadramento (`foco`, `zoom`, `mov`) e ritmo até a folha contar a história.
6. `python3 $S/montagem.py <pasta>` → `renders/montagem_vNN.mp4`. Só mudou volume/SFX: `montagem.py <pasta> som`.
7. Entregue em 3 linhas: receita, duração, trilha (gerada livre ou a do cliente) e como pedir ajuste ("plano 4 mais
   curto", "troca a foto 7", "cor mais quente"). Para o cliente pôr música do app: mande também a versão sem trilha.
   Ofereça numa linha `/exportar-video` (kit para Premiere/CapCut) e `/variacoes` (abertura diferente para teste).
