# Engenharia de prova — não "prompte" o vídeo, prove o vídeo

Fazer o Opus renderizar a primeira versão já não é a parte difícil. O difícil é **saber quando o filme está certo** — e esse saber mora fora do modelo: nos arquivos que ele lê, nas regras sob as quais renderiza e nas medidas que julgam o resultado. (Base: "Motion Engineering", @0xg4tsby; adaptado às ferramentas desta skill.)

## 1. Três objetos, três donos

| Objeto | O que é | Dono | Onde mora aqui |
|---|---|---|---|
| **SPEC** | o que é verdade e o que foi decidido | você/cliente | `campaign.json` (fatos e claims com fonte) · `docs/SPEC.md` + `brand/BRAND.md` (tokens) · `docs/STORYBOARD.md` |
| **COMPOSIÇÃO** | como cada frame é desenhado a partir da spec | o modelo | `index.html`, `scenes/NN.js`, `lib/` |
| **EVIDÊNCIA** | o que o render provou | os instrumentos | `out/qa/`, `out/checks.md`, `golden/`, `docs/REVIEW.md`, `docs/MANIFEST.json` |

Quase toda falha vem de misturar os três: o modelo edita a spec para facilitar a composição; a composição inventa um fato que a spec não tinha; a "evidência" é a descrição do próprio modelo do que ele quis desenhar.

## 2. Fatos × escolhas

- **Fatos** (logo, telas reais, claims, copy aprovada, CTA) estão TRAVADOS e cada um tem fonte. **A composição lê fatos, nunca escreve.**
- **Escolhas** (paleta, ritmo, câmera, ideia de abertura) mudam muito e barato: são tokens.
- Cena que precisa de uma tela/fato que não existe na spec fica **BLOQUEADA** — não aproximada, não redesenhada de memória — com uma nota dizendo qual asset falta. Tela falsa convincente é o defeito mais caro de um filme de produto, porque passa em toda checagem visual.

## 3. Referência vira token, não adjetivo

"Premium", "clean", "dinâmico" são convites para o modelo usar os padrões dele. Antes de qualquer código de cena, produza e MOSTRE esta tabela:

| Referência | Observação | Token |
|---|---|---|
| frame 03 | fundo nunca preto puro | bg #0E0E0C |
| frame 03 | um acento só, < 5% da área | accent #D97757, teto 5% |
| clipe 01 | corta a cada 1,1–1,4 s | beat 1,25 s |
| clipe 01 | painéis assentam, nunca quicam | overshoot do painel 0 |
| clipe 02 | tipo entra rápido, segura longo | entra 240 ms, hold ≥ 900 ms |

Se a coluna "observação" estiver errada, o filme sai errado de um jeito consistente e profissional — mais difícil de pegar depois que um bug óbvio. Junte uma **lista do que NÃO copiar** (assuntos, logos, copy, composições reconhecíveis): a referência entrega um método, nunca um enredo.

## 4. O tempo é a única entrada

`frame = render(t, spec, tokens, assets, seed)`. Nunca do frame anterior, nunca de quanto tempo o navegador está aberto.

| Quebra o contrato | Substitua por |
|---|---|
| `Date.now()` na coreografia | `t` passado; relógio só no player de preview |
| `Math.random()` | `M.rng(semente)`, um fluxo por sistema |
| `x += v*dt`, estado entre frames | forma fechada (`p = p0 + v·a − g·a²`, a = t − t0) ou `M.bake` (física pré-calculada a passo fixo) |
| `setTimeout`, transição CSS | `seek(t)` |
| `frame += 1` num loop | `n = round(t·fps)` calculado uma vez |
| fonte ainda carregando na captura | `window.ready` aguarda fontes/imagens |

**Teste o contrato**: `node scripts/prove.mjs determinism` — frame frio (seek direto) × quente (depois de tocar 0→t) × ordem reversa, hash idêntico. Rode depois de toda mudança estrutural; leva segundos e é o que dá sentido a todas as outras checagens.

## 5. Tempo numa grade

Escolha fps e BPM para a batida ser número inteiro de frames quando der (120 BPM a 30/60 fps = 15/30 frames por batida, nunca deriva). Fracionário (128 BPM a 60 fps = 28,125) é ok **desde que nunca acumule**: `cue_frame = round((compasso·batidas + batida) · 60/BPM · fps)`. Nunca escreva "cue anterior + 28 frames": oito compassos depois você está 4 frames fora da música. Uma lista de eventos é a única fonte de tempo (`window.CUES` + `window.SHOTS`, lidos por imagem, som e revisão). Som no frame do contato visual, nunca antes.

## 6. Classes de movimento com números

| Classe | Duração | Curva | Overshoot |
|---|---|---|---|
| micro UI | 120–200 ms | saída rápida | 0–2% |
| painel | 320–480 ms | criticamente amortecida | 0% |
| manchete | 200–300 ms | saída forte, hold longo | 0–4% |
| câmera | 1,5–4 s | in-out muito suave | 0% |
| personagem | varia | antecipação + follow-through | permitido |

Cada objeto pertence a UMA classe. Um movimento-herói por batida; secundários seguem o herói com **80–150 ms** de atraso. Duas coisas começando no mesmo frame com o mesmo peso = o olho não escolhe nenhuma.

## 7. A escada da evidência (suba só quando o degrau de baixo passa)

| Degrau | Custo | Responde | Comando |
|---|---|---|---|
| still único | segundos | a batida está composta e na marca? | `stills.mjs --times` |
| contact sheet | segundos | a história lê batida a batida? | `stills.mjs --board` / `--every` |
| strip de transição (3–5 frames) | segundos | existe meio-estado feio? | `stills.mjs --strip` |
| render de trecho | minutos | o movimento funciona em movimento? | `render.mjs --from --to` / `clips.mjs --only` |
| render completo | mais | o filme se sustenta? | `render.mjs` |
| **export decodificado** | mais | o arquivo que eu entrego é o filme que eu revisei? | `qa.sh` + `audit-audio.py` + `prove.mjs golden check` |

## 8. Instrumentos (meça o que dá para medir)

| Checagem | Instrumento | Passa quando |
|---|---|---|
| cor de marca | `prove.mjs color` (`window.PROBE_COLORS`) | ΔE2000 ≤ 2–2,5 (≈ invisível lado a lado) |
| legibilidade | `phone.png` 390 px + `window.CHECKS` de tamanho | legenda ≥ 5,2% do lado curto |
| contraste | `window.VALIDATE`/CHECKS | ≥ 4,5:1 (3:1 texto grande) |
| zona segura | CHECKS de caixas vs retângulo seguro | sem sobreposição |
| continuidade | `qa.sh` (pops, frame intruso, Deck Trap) | picos só nos cortes planejados |
| emenda do loop | `qa.sh --loop` | dentro da variação normal + velocidade igual |
| sincronia | `audit-audio.py` no arquivo decodificado | ≤ 1 frame |
| loudness | `mix.sh` + `audit-audio.py` | −14 LUFS (ou o do gênero), ≤ −1 dBTP |
| determinismo | `prove.mjs determinism` | hash igual |
| regressão | `prove.mjs golden check --scope` | nada muda fora do escopo |

História, gosto e piada ainda pedem olho — mas tudo que tem token merece instrumento. "O laranja está meio estranho" vira um número com direção: dá para saber se o conserto passou do ponto.

## 9. Crítica com rótulos

O modelo produz explicações confiantes mais rápido que certezas. Todo achado leva um rótulo:
- **OBSERVADO** — visível num frame nomeado ou medido dos pixels.
- **INFERIDO** — várias observações apontam uma causa; nenhum frame prova ainda.
- **DESCONHECIDO** — não checado, ou a evidência conflita.

E uma regra acima dos rótulos: **o modelo não dá nota ao próprio trabalho.** O juiz é o render, a referência ou um instrumento. Registro de defeito acionável (vai em `docs/REVIEW.md`):

```
- id: D-07
  frames: 412-418
  classe: legibilidade        # verdade-do-produto | legibilidade | continuidade | tempo | sincronia | formato
  rótulo: OBSERVADO
  evidência: altura de maiúscula 19 px em 1080x1920, token mínimo 28 px
  causa: escala da manchete compartilhada com o layout 16:9   # INFERIDO
  conserto: escala de manchete por formato, só 9:16
  escopo: cena 04
  verificar: re-render 405-425 + golden set
```

Prompt de crítica: *"Julgue só os frames renderizados e as medidas anexadas. Não descreva o que o código queria fazer. Reporte os 3 defeitos de maior impacto: frames, classe, rótulo, evidência, causa provável, menor conserto local, escopo. Não proponha conserto fora do escopo."*

## 10. Cheque o checador (defeitos plantados)

Uma checagem verde é evidência sobre a checagem que rodou, nada mais. Ao montar o estúdio (e sempre que a revisão mudar), **plante defeitos de propósito** e rode a revisão normal:

| Defeito plantado | Tem de ser pego por |
|---|---|
| cor de acento deslocada 8% | `prove.mjs color` |
| um cue de som 3 frames atrasado | `audit-audio.py` |
| manchete 40 px fora da zona segura | CHECKS de zona segura |
| barra cinza de placeholder numa tela | revisão de verdade-do-produto |
| pop de 2 frames dentro de uma dissolução | strip de transição / `qa.sh` |
| mudança fora do escopo de um conserto | `prove.mjs golden check --scope` |

O que escapar diz exatamente qual instrumento falta. É teste de mutação para pipeline de vídeo. (Validado nesta skill: cor plantada pega com ΔE 8,8; mudança fora de escopo pega como REGRESSÃO.)

## 11. Proteja o que já funciona

Conserto quebra coisa fora do escopo mais do que falha dentro dele. Duas práticas:
- **Patch delimitado**: cada conserto nomeia o escopo e só mexe nele. Se precisar mexer num token compartilhado, diz — e a revisão se alarga para toda cena que usa o token.
- **Golden frames**: um conjunto fixo de frames aprovados (1 por estado + pôster) — `prove.mjs golden save` depois da aprovação. Depois de cada conserto: re-render do trecho + `golden check --scope a-b`. Mudou fora do escopo = PARE.

É isso que faz a 10ª rodada ser mais rápida que a 3ª, em vez de mais arriscada.

## 12. Formato é restrição, não recorte

9:16 é outra composição da mesma história: compartilha spec, eventos e tokens; NÃO compartilha layout.

| | 16:9 | 9:16 | 1:1 |
|---|---|---|---|
| elementos por batida | até 3 | 1–2 | 2 |
| escala da manchete | ×1,4 | ×1,2 | ×1,0 |
| câmera | lateral | vertical | mínima |
| holds | token | +15% | +10% |
| margem | title-safe 90% | margens da plataforma | title-safe 90% |

Cada variante ganha a própria contact sheet e as próprias medidas. Export correto = a composição sobreviveu à troca de formato, não "o encoder terminou".

## 13. Rodadas longas = máquina de estados

| Gate | Checagem | Artefato de saída |
|---|---|---|
| G1 | assets completos, fatos com fonte | `campaign.json`, BRAND/SPEC |
| G2 | cada batida tem propósito | `STORYBOARD.md`, CUES/SHOTS |
| G3 | determinismo passa | stills + contact sheet |
| G4 | transições, sincronia, movimento | renders de trecho |
| G5 | 3 piores corrigidos, golden limpo | `REVIEW.md` rN |
| G6 | cada formato medido no decodificado | `out/` + nota de entrega |

`node scripts/prove.mjs gate G3 pass "nota"` grava em `docs/MANIFEST.json`; uma rodada retomada lê o manifest, não o histórico do chat. **Bloqueios, não julgamento**: asset que falta, determinismo falhou, golden mudou fora do escopo → para e pergunta. **Teto de rodadas**: `prove.mjs round` conta; passou de 5, reporta o que falta em vez de ficar em loop. Novecentos frames polidos da coisa errada são piores que um still de teste e uma pergunta.

## 14. Prompt em gates (cole quando a tarefa for longa ou você for se ausentar)

```
Você está dirigindo e engenheirando um filme renderizado em código. Trabalhe em gates.
SPEC: leia campaign.json (fatos travados). Nunca acrescente, mude ou redesenhe um fato; se uma cena precisar de um fato
que não existe, PARE e liste. Das referências, escreva a tabela observação → token no SPEC.md + a lista do que não copiar.
Mostre antes de escrever código de cena.
PLANO: STORYBOARD.md com cada batida (tempo, estado de entrada, estado de saída, propósito, o que persiste).
CUES/SHOTS são a única fonte de tempo; fps e BPM escolhidos para cues serem calculados do tempo e arredondados uma vez.
BUILD: seek(t) puro. Sem relógio, sem random sem semente, sem estado entre frames, sem timers/transições CSS.
Aguarde fontes e assets. Rode prove.mjs determinism depois de toda mudança estrutural.
REVISÃO: stills por batida e strips de 3–5 frames em toda transição; rode os instrumentos. Rotule cada achado
OBSERVADO/INFERIDO/DESCONHECIDO. Você não dá nota à própria intenção: julgue só frames e medidas. Reporte os 3 defeitos de
maior impacto como registros com escopo e verificação. Conserte só no escopo; re-render do escopo + golden check.
Pare em qualquer mudança fora do escopo.
ENTREGA: composições separadas por formato, cada uma medida no arquivo decodificado. Atualize o MANIFEST a cada gate.
No máximo 5 rodadas de conserto. Termine com a nota de entrega: o que passou, o que foi medido, o que ainda pede olho/ouvido humano.
```
