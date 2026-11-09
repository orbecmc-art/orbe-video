# Laboratório — prompt dirigido, números, follow-ups com frame e recibos

> Adjetivo é onde mora o look padrão. **Cada adjetivo trocado por um número é uma decisão que você toma de volta do modelo.**

Teste controlado (mesmo modelo, mesmo produto, mesma linha técnica, só a direção muda):
- **Prompt vago** (27 palavras, "legal, premium, moderno"): saiu fundo azul-marinho, anel brilhante, bloom, partículas, produto girando e uma tagline inventada. Quase toda a lista proibida.
- **Prompt dirigido** (448 palavras de números): saiu filme de estúdio. Depois foram 15 follow-ups em 4 rodadas, todos com frame e número.
Ninguém posta o meio: o 2º prompt, o 3º, a nota "o frame 84 pica atrasado". Esse meio é o trabalho.

## 1. Template de prompt dirigido (preencha TODAS as linhas antes de enviar)

```
OBJETIVO: o que o espectador deve sentir ou fazer, numa frase
SAÍDA: um index.html autocontido, window.seek(t) [ou Remotion/HyperFrames/three.js — com versão fixa], L × A
TEMPO: segundos × fps = total de frames · BPM (1 batida = N frames) · loop: sim/não (frame N-1 flui para o 0)
LOOK: paleta em hex, UM acento (onde aparece), fonte + peso + tamanho + tracking, fundo, textura (grão %, vinheta %)
MOVIMENTO: easing como cubic-bezier, springs como ζ (razão de amortecimento) + Hz, durações em FRAMES, stagger
PLANOS: faixas de frame · UM movimento herói por plano · como cada plano passa para o próximo (corte na batida, match cut, máscara)
PROIBIDO: os padrões que você nunca quer ver (pelo nome)
QA: stills em frames nomeados, contact sheet, consertar, só então o render completo
[3D] MODELO: medidas (1 unidade = 1 cm), materiais (cor, roughness, clearcoat, metalness), o que NÃO pode mudar
[3D] CÂMERA: fov, distância, órbita em graus, push-in com curva e frame, elevação; câmera nunca estacionada
```
- Escreva **OBJETIVO primeiro**. Se não cabe numa frase, nenhum easing salva a peça. Depois **TEMPO**: todo o resto pendura no total de frames.
- **PLANOS** é onde mora a história. Padrão = corte na batida; transição tem que ser uma decisão.
- A linha **QA** obriga o Claude a olhar stills antes do render inteiro — é onde o loop de laboratório começa.
- Cole o **contrato de render** (pipeline.md §2) embaixo de qualquer prompt.

### Adjetivo → número (o que mudou entre o vago e o dirigido)
| Disseram | Virou |
|---|---|
| "premium" | materiais: cerâmica acetinada roughness 0,38 + clearcoat 0,35; cromo roughness 0,05; acento só numa peça |
| "legal" | um estúdio: key / fill / rim com cor (hex ou K) e intensidade, reflexo de softbox, sombra de contato 0,55. Zero glow |
| "moderno" | uma câmera: fov 30°, nunca parada, órbita 34°→10°, UM push-in com ease-out-expo no frame da batida |
| "animação" | batidas e springs: 120 BPM, antecipação de 3 frames, abertura com ζ 0,6, segundo elemento ζ 0,7 com follow-through ζ 0,5 |
| (nada) | os padrões NOMEADOS e banidos: bloom, orbes, neon, partículas, turntable girando, fundo escuro, texto |

## 2. Números de referência (cola)

**Easing** (`M.EASE`, valores de easings.net)
| Nome | cubic-bezier | Uso |
|---|---|---|
| ease-out-expo `enter` | 0.16, 1, 0.3, 1 | revelar texto e logo |
| ease-out-quint `premium` | 0.22, 1, 0.36, 1 | entradas premium |
| ease-in-out-quart `move` | 0.76, 0, 0.24, 1 | atravessar a tela, câmera |
| ease-in-expo `exit` | 0.7, 0, 0.84, 0 | saídas rápidas |
| ease-out-back `pop` | 0.34, 1.56, 0.64, 1 | pop brincalhão (nunca texto) |
Entra com *out*, sai com *in* e 40–50% mais curto (400 ms entra / 200 ms sai), atravessa com *in-out*. Linear só em rotação, barra de progresso e fase de loop.

**Springs** (`M.springZ(t, ζ, Hz)`, `M.dampingRatio(k, d, m)`): ζ 1 sem quique · 0,7–0,85 premium · 0,4–0,6 brincalhão · < 0,3 cartoon. Remotion padrão (100, 10, 1) = ζ 0,5; react-spring padrão (170, 26) = ζ 1,0. Posição e tamanho podem quicar; **opacidade e cor nunca**.

**Durações** (em frames: a 60 fps, 1 frame ≈ 16,7 ms; a 24 fps ≈ 42 ms)
| O quê | ms | frames @60 | frames @24 |
|---|---|---|---|
| feedback de UI | 100–200 | 6–12 | 2–5 |
| movimento de UI | 200–500 | 12–30 | 5–12 |
| revelação herói | 600–900 | 36–54 | 14–22 |
| letra / palavra / item | 30 / 60–120 / 40–80 | 2 / 4–7 / 2–5 | 1 / 2–3 / 1–2 |
Próximo elemento começa com o anterior 30–50% feito. Tudo sequencial = robótico; tudo junto = barato.

**Batida**: frames por batida = fps × 60 / BPM. Calcule cada batida a partir do tempo e arredonde UMA vez (somar 14 arredondado deriva 2 frames em 32 batidas). Corte na batida, mude o layout no compasso (a cada 4) — mudar tudo em toda batida cansa.

**Leitura**: texto fica ≥ 0,5 s + 0,3 s por palavra (2 palavras = 1,1 s). Durante o hold, push lento de 2% mantém vivo sem atrapalhar a leitura.

**Hierarquia**: um herói por plano. Secundários andam 50–70% da distância e começam 100–200 ms depois. Ambiente < 5% do curso do herói, seno lento, nunca para. Parallax: frente 1,0 · meio 0,5 · fundo 0,2.

**Acessibilidade**: contraste do texto ≥ 4,5:1 em todo frame (inclusive sobre fundo em movimento). No máximo 3 flashes por segundo (o `qa.sh` mede).

## 3. Princípios de animação escritos como números (para mascote/personagem/objeto)

| Princípio | O que faz | Escreva no prompt assim |
|---|---|---|
| Antecipação | carrega antes do movimento | "agacha 11 frames (escala 1,2 × 0,75)" |
| Squash & stretch | peso e velocidade | "estica 0,85 × 1,28 na decolagem, achata 1,25 × 0,7 no pouso" |
| Ação sobreposta | partes começam depois do corpo | "braços atrasam 4 frames, pernas 6" |
| Follow-through | partes continuam depois que o corpo para | "braços assentam a 2,2 Hz, ζ 0,22" |
| Arcos | movimento natural | "salto em arco pontilhado de 3,5 de altura" |
| Slow in / out | acelera e assenta macio | "volta com spring ζ 0,55" |
| Timing | contagem de frames = peso | "25 frames no ar por pulo" |
Exagero: no celular tudo encolhe — empurre poses-chave 10–30% além do que parece certo. E diga o que **não** pode mudar (proporções do personagem, logo): é a trava que mantém a identidade em qualquer estilo.

Truque de set: enquanto itera, peça **playhead e rótulos de frame na própria cena** (cada rótulo acende no frame em que o princípio acontece → um movimento atrasado aparece como rótulo acendendo antes). Desligue no render final. No template: `?debug=1`.

## 4. Biblioteca de follow-ups (apontam para FRAMES, não para sensações)

Use 1–2 por rodada. Colar todos de uma vez transforma conserto em reescrita.
```
Gere stills nos frames 0, 24, 48, 72 e 96. Descreva cada um numa frase, como um espectador. Bate com a lista de planos? Conserte o que não bate.
Contact sheet de 1 a cada 12 frames. Marque todo frame em que duas coisas se mexem ao mesmo tempo e conserte a hierarquia.
Onion skin dos frames 24 a 47 (stills.mjs --onion). O espaçamento deve apertar perto das chaves. Ajuste o easing até apertar.
Gráfico de x e escala do herói por frame (stills.mjs --graph). Mostre onde é linear ou para seco e conserte com os tokens.
Revise como um motion designer sênior: 10 notas por impacto, cada uma com número de frame e a mudança exata no código. Aplique as 5 primeiras.
Está ocupado demais. Remova 30% do movimento e mantenha só o que guia o olho.
O final é abrupto. Hold de 36 frames com push de 2% e assentamento em spring ζ 0,8.
O conserto no frame 84 não pegou. Gere 83 e 85 lado a lado, liste toda diferença, ache a linha que causa, mude só ela e gere de novo.
```
**Traduza sensação em número antes de mandar:**
| Nota que chega | Mande isto |
|---|---|
| "dá um pop" | escala 1,0 → 1,08 → 1,0 em 6 frames, pico na batida |
| "mais premium" | ease-out-quint nas entradas, springs ζ 0,8, nenhum overshoot em texto |
| "está arrastado" | encurte cada hold em 12 frames (1 batida a 120 BPM/24 fps) — cortes continuam na grade |
| "está ocupado" | um movimento herói por vez; o resto começa 150 ms depois com 60% do curso |
| "parece IA" | liste pelo nome os padrões usados, bana cada um, renderize de novo |

Quando um conserto funciona, **adicione a regra ao contrato** (CLAUDE.md do projeto): o contrato é a memória do estúdio.

## 5. Recibos (prompts e follow-ups registrados)

Registre em `docs/PROMPTS.md`: o prompt exato, cada follow-up criativo (muda como a peça parece ou se move) e, separado, os técnicos (fonte, captura). Conte.
Referências honestas da trend: loop de cromo líquido = 416 palavras + 10 follow-ups + 5 de som (~2 h + 45 min) · filme de produto dirigido = 448 + 15 + 12 de som (~3 h) · mascote 3D = 399 + 4 + 0 de som · vídeo de lançamento de estúdio de design = 3 prompts · explainer interativo = 1 prompt + 3 rodadas noturnas (5 h 28 min, ~US$ 90 de API).
**3 prompts é um bom número.** "Um prompt" deixa as pessoas desconfiadas; recibo convence (e vende).

## 6. Esforço e velocidade

- A Anthropic diz que o Opus 5.5 em **medium** iguala ou supera o Opus 5 em high, e recomenda guardar xhigh/max para onde você **mediu** ganho. Regra do laboratório: medium para tudo; suba só quando uma peça do zero errar duas vezes. Peças de lançamento grandes da trend usaram xhigh/max — vale para o primeiro build de algo ambicioso, não para iterar.
- Iteração: medium (ou /fast quando velocidade importa mais que custo).

## 7. 3D (three.js)

- Fixe a versão via importmap (ex.: three 0.160.0). Sem rede externa (workspace na nuvem), `npm i three@0.160.0` e importe de `./node_modules/three/build/three.module.js`.
- `window.renderAt(t)` define TUDO a partir de t; nada de `clock.getDelta()`; ruído periódico na duração do loop; `window.ready` depois de fonte e pré-cálculos.
- Armadilha real: no r160 o `TextGeometry` lê `height` para a profundidade; `depth` é ignorado e vira 50 → letras 400× mais fundas. Fixe a versão e nomeie o parâmetro certo.
- Materiais e luz por número (key/fill/rim, softbox, reflexo de estúdio construído em código); câmera com fov 30–50° e nunca estacionada.
- GPU real renderiza muito mais rápido; sem GPU: `--use-angle=swiftshader --enable-unsafe-swiftshader` e imprima `UNMASKED_RENDERER_WEBGL` para saber o que está rodando.
- Motion blur: média de subframes em luz LINEAR (o `render.mjs` já faz: obturador de 180°).
- Pós: bloom só com limiar alto e só em emissivos, curva de tom, vinheta 6–10%, grão 1,5–2% semeado pelo frame.

### 7b. Receita three.js "estúdio" (v4 — dos repos claude-motion, motion-video-kit, whaleyxbt)
- Ambiente: `RoomEnvironment` ou `Sky` → `PMREMGenerator.fromScene(env, 0.03)`; tone mapping ACES (ou AgX) e **compense o desvio de cor do ACES** no acento da marca; render target HalfFloat com MSAA 4.
- Bloom: força 0,85 · raio 0,55 · limiar 0,62; emissivos < 1 fora do momento-herói (senão tudo brilha).
- Metal grande: roughness ≥ 0,45, envMapIntensity ≈ 0,5. Presets de material: clay, chrome, glass, toon.
- Cutaway por `clippingPlanes`; volume (fumaça, aura) como casca `LatheGeometry` com shader aditivo.
- Câmera em CatmullRom centrípeto; **voar através** do objeto vale mais que orbitar; pitch 35–55° em produto.
- Recorte nítido: `camera.setViewOffset` renderiza o sub-retângulo em vez de ampliar a imagem.
- Trave `devicePixelRatio` no load; sem `will-change`; varra o render atrás de frame preto isolado (NaN no shader) — o `qa.sh` acusa como "frame intruso".
- Exploded view: smootherstep por camada, camadas registradas (alinhadas) na ida e na volta.
- Antes de tudo isso: `M.cam3` (2.5D em canvas) resolve parallax, dolly zoom e rack focus sem WebGL. Use 3D só quando a forma precisa de luz real.
