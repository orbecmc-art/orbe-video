# Ritmo, batidas e junções — o estilo em números (método Style Studio / Synteq, adaptado)

Um estilo não é só fonte e cor: é **que cena carrega cada batida do roteiro**, **de quanto em quanto tempo algo muda
na tela** e **que junções ele aceita**. Isso mora em `assets/estilos.json` → `ritmo`, `batidas`, `juncoes`, e o
`ritmo.py` confere o mapa contra o estilo antes do render.

## Batidas (o que a frase FAZ)
| batida | o que é | exemplo |
|---|---|---|
| gancho | a 1ª frase, o motivo para ficar | "Se você fatura mais de 1 milhão…" |
| virada | a revelação, o payoff, o "mas" | "O problema é que 90% desistem" |
| item | um de uma lista/passo/capítulo | "Passo 1: …" |
| numero | quantidade, preço, prazo, % | "45% a mais em 45 dias" |
| ponto | argumento comum | — fica no rosto na maioria dos estilos |
| prova | caso, depoimento, print, notícia, estudo | "a gente fez isso com…" |
| fim | fecho/CTA | "Comenta CONVITE" |
`ritmo.py . batidas` sugere a batida de cada frase (docs/BATIDAS.md) com a peça e a junção do estilo. Marque no mapa
(`"batida": "numero"`); o `ritmo.py .` avisa quando a peça não é a do estilo (ex.: dinâmico carrega número com
`slam`/`numero`/`anel` entrando em `flash`; minimal com `grafico`/`numero`).

## Ritmo medido por estilo
| estilo | algo muda a cada | nunca parado > | fim após a última palavra | punch |
|---|---|---|---|---|
| dinâmico / varejo | 1,5–2,5 s | 3 s | ≤ 1–1,5 s | **linha**: cada linha de legenda, vai-e-volta |
| dossiê | 2–3 s | 4 s | ≤ 2 s | tônicas |
| educativo / podcast P&B | 2,5–3,5 s | 4,5 s | ≤ 2 s | tônicas |
| clínica premium / minimal / luxo | 3–4 s | 5–5,5 s | ≤ 2,5–3 s | só nas viradas |
"Mudança" = corte, punch-in, peça que entra, B-roll, quebra. Legenda trocando NÃO conta. Plano < 0,75 s não registra.
Medido nas referências do Style Studio (Volt 1,5–2 s com punch em toda linha; Ledger 3–4 s com punch só nas viradas).

## Junções
Cada estilo aceita uma lista (`juncoes`); as outras são RECUSADAS pelo `ritmo.py` (✗). Zoom e flash só na 1ª e na que
mais importa de uma série — usados em toda entrada, viram ruído. `recuo` = a câmera vira cartão (modo `janela`).

## Peças de assinatura (v1.4)
- **slam** — o número que o vídeo existe para dizer cai na palavra, largo como a tela; o valor antigo espera em cima e é
  riscado. No máximo 2 por vídeo, nunca dois seguidos (o `ritmo.py` bloqueia).
- **caixa da palavra-chave** (dinâmico/varejo) — no máx. 1 palavra forte por bloco numa caixa inclinada na cor de destaque.
- **janela** — a pessoa num cartão quadrado (olhos no terço superior, anel, sombra) sobre a cena; entra recuando.
- **split com fio** — a borda do split vira um fio grosso na cor de destaque (`split_fio`).
- **cor de destaque em rodízio** — `ritmo.py . cor` escolhe a próxima cor do `rodizio` do cliente (marca.json) e nunca
  repete a do último vídeo (histórico no kit). Só quando a marca permite variar.

## Revisão
- Stills de cada plano quando assentou + o meio de cada junção (board do motion_ponte e qa_edicao).
- Palavra direto sobre o vídeo: contraste pelo tom da roupa sob o rosto — branco em camisa escura, tinta (com borda) em
  camisa clara; na dúvida, pílula/caixa.
- Regra de ouro (Joseph, Stockton): **você decide o que cada cena mostra (plano); a skill decide como ela fica.**
