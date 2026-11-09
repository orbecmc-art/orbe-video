# Loop de crítica — fazer o Claude assistir aos próprios frames

O Opus lê imagens. Este hábito, sozinho, separa os vídeos que viralizaram dos postados com "ficou meio mid".
Iteração é o método, não uma falha: o curta em aquarela mais honesto da trend levou 163 chamadas e ~7 horas.

> Você sabe o que acontece porque escreveu o código. O espectador vê **uma vez, em velocidade real, pela primeira vez.**

## 1. Quando olhar (gates)

| Gate | O que gerar | Custo |
|---|---|---|
| **G1 — Storyboard** | `docs/STORYBOARD.md` com leituras (reads) e estado final de cada batida | texto |
| **G1b — Board de aprovação** | `stills.mjs --board` → `out/board.html`: um frame por estado de `window.SHOTS` + aviso de texto curto demais. Mostre ao usuário/cliente | segundos |
| **G2 — Quadros-chave** | `stills.mjs --times <poses-chave>` em tamanho real | segundos |
| **G3 — Um frame por batida** | `stills.mjs --beats audio/beats.json` (ou `--every 0.5`) | segundos |
| **G4 — Trecho mais difícil** | `stills.mjs --strip <t> --n 12` nos 2–4 s mais complexos + em toda emenda (−0,2 s a +0,2 s) | segundos |
| **G5 — Animatic** | `render.mjs --fps 30 --sub 1 --jpeg` (rascunho) | ~1 min |
| **G6 — Master** | render final + mix + `qa.sh out/final.mp4 --loop` | minutos |

**Nunca pule do código direto ao render final.** Corrigir storyboard é barato; corrigir render é caro. "Um render que sai com código 0 não prova nada" — confira o **master**, não a fonte.

### As 5 passadas que ninguém pode pular
| Passada | Pergunta | Ferramenta |
|---|---|---|
| 1. Storyboard | a história se entende com alguns frames por cena? | `stills.mjs --board` |
| 2. Timing | antes, durante e depois de CADA transição: texto pisado, salto, algo sumindo sem motivo? (a contact sheet pode cair entre dois frames de uma transição quebrada) | `--strip <t>`, `--onion a,b`, `--graph`, varredura de pops do `qa.sh` |
| 3. Tamanho de celular | lê a 360 px de largura? | `--thumb 360`, `qa.sh` → phone.png |
| 4. Marca e dados | logo, fonte, cores, capturas e **claims aprovados** batem? | `campaign.mjs validate`, `--checks` |
| 5. Vídeo final com áudio | arquivo codificado: sincronia, duração, formato, loudness | `qa.sh`, `audit-audio.py` |

### Ferramentas de laboratório
- `index.html?t=2.5` congela o frame exato (para olhar, printar ou descrever). `?debug=1` desenha frame/tempo/batida/plano no canto (para anotar "frame 84"); nunca no render final.
- `stills.mjs --frames 83,84,85` · `--strip 4.2 --n 12` · `--onion 1.2,1.8` (espaçamento igual = robótico; apertando perto das chaves = easing certo) · `--graph` (valor e velocidade por frame das `window.PROBES`: linha reta = linear, quina = parada/arranque seco) · `--checks` (auditoria numérica de `window.CHECKS`: cada número do brief vira um teste).
- No teste desta skill, `--checks` pegou o cursor ainda andando no clique (161 u/s) e a aba que não chegava a tempo; `--onion` mostrou o texto do gancho saindo por cima do botão. Nenhum dos três aparecia na contact sheet.

## 2. Como olhar (procedimento)

1. **Descreva cada frame de batida em uma frase, como um estranho**, nomeando cada objeto. Qualquer objeto que você precisaria explicar ("aquelas barras são espelhos") é **P0**.
2. Leia a sheet em ordem e **conte os frames que cada leitura recebe** (60 fps: 60 = 1 s). Leitura de texto: `0,5 s + 0,3 s/palavra`. Se não cabe, alongue o plano ou corte a leitura. Leituras nunca se sobrepõem.
3. Cubra as palavras mentalmente: as imagens sozinhas contam a história? Cada frame causa o próximo?
4. Abra `phone.png` (360 px de largura): tudo que importa ainda se lê?
5. Pontue **por dimensão (e por plano)**, nunca o filme inteiro numa nota só — uma nota geral não encontra nada para consertar.

### Rubrica (1–10 cada; meta: todas ≥ 8)

| Dimensão | Pergunta |
|---|---|
| Gancho | Os primeiros 2 s (e o frame 0, que é a thumbnail) seguram o dedo? |
| Leitura no celular | Tudo legível a 360 px? Texto ≥ 2,6% do lado curto? |
| Qualidade do movimento | Springs com massa, sem frames mortos, sem coisas deslizando linearmente? |
| Variedade | Algo novo a cada 2–4 s? Entradas variadas? |
| Composição | Herói ≥ 40% do quadro, hierarquia clara, zonas seguras respeitadas? |
| Fidelidade à marca | Cores/fontes/UI/dados reais? |
| Sincronia com o som | Mudanças nas batidas, SFX nos eventos, nada atrasado? |
| Anti-slop | Nenhum item da lista proibida (look.md §2)? |

### Formato das notas (obrigatório)

```
P0 · t=4.20s · card de métricas · número sobrepõe a aba durante a troca → atrasar entrada das abas para B(10.4) · manter a cascata das barras
P1 · t=7.50s · transição toast→grade · quadro vazio por 0,25 s → grade nasce do ponto onde o toast colapsa · manter impacto em B(15.2)
P2 · t=11.0s · logo · rotação de entrada lê como gratuita → reduzir de −0,6 para −0,2 rad
```
`P0` quebra a leitura ou o contrato · `P1` enfraquece · `P2` polimento.
Corrija **texto primeiro, depois timing, depois detalhe**. Re-gere só o que mudou. Segunda rodada só se ainda restar P0.
Quando um conserto não pega: tire still dos dois lados, liste toda diferença, mude só a linha causadora.

## 3. O que caçar especificamente

- Avisos ⚠ do board (estado curto demais para o texto que mostra) — alongue o estado ou corte palavras.
- Cursor clicando em movimento ou mirando no lugar errado (confira com `--times` no instante do clique).
- Texto sobrepondo durante trocas; dígitos borrados em contadores (use `M.count`).
- Algo **deslizando** em vez de assentar; movimento em velocidade constante; partes se movendo todas juntas (twinning).
- Rótulos de canto, bordas de quadro, título centralizado sobre gradiente, tudo com fade-in.
- Texto escalado borrado (will-change / escala de câmera sobre bitmap).
- Uma batida morta sem nada acontecendo (o `qa.sh` aponta trechos > 0,6 s "quase sem mudança").
- Engasgo na emenda do loop (último frame ≠ primeiro).
- Frame 0 vazio, preto ou só logo.
- Leituras empilhadas: 7 leituras em 1,3 s (o final da demo do ClaudeAnimationBase precisou de 4 s).
- Filme "ocupado": remova 1/3 do movimento, mantenha o que guia o olho.
- **Pops de 1 frame** (`qa.sh`: diferença 3x a dos vizinhos): confira quadro a quadro. Contato e corte proposital passam; o resto é bug.
- Toda frame importante poderia ser anúncio parado? Há cara de template? Há demais na tela? A UI é a real?
- Confira quadros do **MP4 decodificado**, não só capturas do navegador: faixa de cor, compressão e subframes só aparecem ali.

### Relatório obrigatório do agente
Se um agente diz "a animação ficou ótima" sem ter olhado o render, não acredite. Todo fim de rodada traz:
**segundos/frames revisados · problemas encontrados · o que foi consertado · o que ainda preocupa** — e uma pessoa aprova.

## 4. Comandos

```bash
node scripts/stills.mjs index.html --beats audio/beats.json --out out/contact.png      # 1 por batida, com timestamp
node scripts/stills.mjs index.html --strip 4.2 --n 12 --out out/strip.png              # frames consecutivos
node scripts/stills.mjs index.html --every 1 --thumb 360 --out out/phone.png           # teste de celular
bash scripts/qa.sh out/final.mp4 --strip 4.2 --loop                                     # master: contact, phone, poster, loop, métricas
```

## 5. Prompt do diretor crítico (use em si mesmo ou num subagente revisor)

```
Abra out/contact.png, out/strip.png e out/phone.png e olhe de verdade.
Seja um diretor de motion exigente, não um autor orgulhoso.
1) Descreva cada frame de batida em uma frase, como um estranho veria.
2) Pontue 1–10: gancho · leitura no celular · qualidade do movimento · variedade · composição · marca · sincronia · anti-slop.
3) Liste os 3 maiores problemas no formato "P0/P1/P2 · t=… · onde · problema → mudança exata · o que fica".
Cace: texto sobrepondo, algo deslizando, rótulos de canto, centralizado-sobre-gradiente, texto borrado,
batida morta, engasgo no loop, frame 0 vazio.
4) Corrija, re-renderize só os segundos afetados, mostre a nova sheet e as novas notas. Repita até tudo ≥ 8.
```
Revisor em subagente: passe **só** o STORYBOARD.md e as sheets (não o código) e peça linhas P0/P1. A edição fica com você. Num filme importante, um crítico novo, que não construiu, revê o render final antes da entrega.

## 6. Notas de diretor (vocabulário que funciona na iteração)

Notas vagas ("melhora isso") geram mudanças aleatórias. Notas de câmera geram exatamente a mudança:
- "desacelera todo zoom para 0,7×" · "corte seco aqui" · "push in no botão" · "segura 0,4 s a mais no número"
- "entra pela ação: corta no frame mais rápido do movimento" · "a palavra 'receita' no acento, o resto em tinta"
- "tira o tremor de câmera, só no impacto" · "o card nasce do botão, não aparece" · "menos coisas se mexendo ao mesmo tempo"
- "mais papel, luz mais escura, texto por cima da imagem, fade lento no final" (deltas curtos de direção de arte funcionam)

Depois do primeiro render: escreva no SPEC.md, linha **BANNED**, todo padrão que apareceu e você não quer de novo.


## 7. Revisão adversarial (o que separa "eu acho que ficou bom" de "passou no crítico")

- **Crítico novo, contexto limpo**: um subagente recebe só o MP4 (ou contact sheet + strips), o brief, as palavras do cliente e o relatório anterior — **nunca o seu raciocínio**. Ele rejeita por padrão e puxa janelas densas de frames (1/30 s) em toda transição.
- **Resumo cego**: outro agente vê só os frames, sem som, e reconta a mensagem em uma frase. Se a frase não for a do brief, o filme não comunica.
- **Rodadas de verificação**: cada item vira FIXED / PARTLY / STILL PRESENT; o veredito é SHIP ou ONE MORE PASS. Mantenha um livro de rodadas em `docs/REVIEW.md` (achado → mudança → medida).
- **A v2 só substitui a v1 se ganhar lado a lado** (um juiz vê as duas, sem saber qual é a nova).
- **Passe só de áudio**: ouça (meça) sem imagem — a narrativa sonora tem começo, meio e fim? E o passe mudo: a imagem conta a história sem som?
- **Legibilidade no celular**: leia as legendas no `phone.png` (390 px). Se você precisa dar zoom, o público não lê.
- **O que cliente pegou e crítico não pegou** (cace de propósito): texto sobre texto no meio de um crossfade; rótulo que contradiz o próprio valor (barra de 30% com "80%"); título que sumiu porque ninguém mandou manter.
- **Varreduras automáticas** (`qa.sh`): mudança visual por janela de 2 s (Deck Trap: < 12% = slide), frame intruso (n ≠ vizinhos com n−1 ≈ n+1), pops, velocidade na emenda do loop, mono, flashes.
- **Determinismo**: renderize o mesmo frame duas vezes e compare o hash; diferente = estado escondido.

## 8. Engenharia de prova
Rótulos OBSERVADO/INFERIDO/DESCONHECIDO, registro de defeito com escopo, golden frames contra regressão, defeitos plantados para testar os instrumentos, gates G1–G6 com `docs/MANIFEST.json` e **teto de 5 rodadas de conserto** (depois disso, reporte o que falta): `references/prova.md`.
