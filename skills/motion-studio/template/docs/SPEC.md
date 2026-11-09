# SPEC — [nome do filme]

## Filme em uma linha
[O que é + o que o espectador deve sentir no fim.]

## Entrega
- Duração: [15] s · Formatos: [9:16 → 1:1, 16:9] · FPS: 60 · Plataforma: [Reels/TikTok/YouTube/site]
- Público: [quem] · Objetivo: [lançamento / anúncio / explicar / portfólio] · CTA: [texto exato]

## Insumos (input de fora — o que quebra o look padrão)
- Marca: logo [arquivo], cores [hex], fontes [famílias + pesos]
- UI/produto real: [screenshots em ./assets]
- Referência: [arquivo/link] — pegar: [paleta / tipografia / ritmo / transições] · NÃO pegar: [assunto, logos]
- Dados reais por estado: [números, nomes, métricas confirmados]

## Look (todo adjetivo vira número)
| Adjetivo | Número |
|---|---|
| fundo | [#hex, claro/escuro] |
| acento | [#hex] — usado em: [palavra-chave, payoff, card final] |
| display | [família, peso, tamanho em % da altura, tracking] |
| UI | [família, peso, tamanhos] |
| movimento | [presets de spring; overshoot permitido onde] |
| textura | [grão %, vinheta %, papel?] |
| câmera | [push %/plano, zoom por estado] |

## Linguagem de movimento (oficio.md §9 — audite cada plano contra isto)
- Curva assinatura (~90%): [ex.: cubic-bezier(.18,0,.15,1)] · 2ª curva (máx.): [ ]
- Unidade base: [0,4 s] — durações em múltiplos · voz da marca (oficio.md §3): [calmo/confiável/…]
- Família de transição (2–3 no filme): [ ] · stagger: [60 ms, teto 0,5 s] · hold mínimo: [0,3 s]
- Orçamento de intensidade: [≤ 3 batidas de tela cheia] · 3 adjetivos de humor: [ , , ]
- Vocabulário semântico: horizontal = [progresso] · escala = [importância] · rotação = [mudança de estado]

## Referência → token (prova.md §3) — mostre ANTES de escrever cena
| Referência | Observação | Token |
|---|---|---|
| | | |
- NÃO copiar: [assuntos, logos, copy, composições reconhecíveis]

## Som
- [faixa fornecida → beats.py] ou [music.mjs --style ... --bpm ...]
- SFX: [lista de tipos e quando] · Voz: [sim/não, fonte]

## BANNED (padrões deste filme)
- título centralizado sobre gradiente · tudo com fade-in · rótulos de canto · glow · quique em UI
- [adicione aqui todo padrão que aparecer no 1º render e você não quiser]
