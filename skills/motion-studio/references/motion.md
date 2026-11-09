# Ofício do movimento — o que faz parecer caro

Movimento barato vai de A a B numa curva fixa. Movimento caro tem **massa**: acelera, passa um fio do alvo, assenta.
A assinatura de filme gerado: o mesmo `easeOut` de 0,5 s em tudo.

## 1. Springs (padrão para objetos)

`M.spring(t, k, d)` é a resposta ao degrau em forma fechada — pura em `t`. Presets em `M.SPRING`:

| Preset | k, d | ζ | Lê como | Use em |
|---|---|---|---|---|
| `snappy` | 320, 30 | 0,84 | premium, firme | botões, toggles, borda de ataque, letras |
| `ui` | 260, 28 | 0,87 | premium | morph de containers, tamanhos |
| `smooth` | 170, 26 | 1,0 | sem quique | cards, posição, câmera |
| `heavy` | 90, 20 | 1,05 | peso | tipografia grande, logo, número, 3D |
| `playful` | 220, 14 | 0,47 | brincalhão | mascotes, stickers, badges |
| `wobbly` | 180, 9 | 0,34 | cartoon | gag pontual |

- **Opacidade e cor nunca quicam.** Posição e tamanho podem.
- Linguagem universal: `M.springZ(t, ζ, Hz)` — ζ 1 sem quique · 0,7–0,85 premium · 0,4–0,6 brincalhão · < 0,3 cartoon. Converta números de qualquer biblioteca com `M.dampingRatio(k, d, m)` (Remotion padrão = ζ 0,5). Em prompt, escreva sempre ζ e Hz.
- UI: overshoot mínimo. Tipografia: nenhum.
- **Valor que muda de alvo várias vezes = soma de uma mola por mudança** → `M.track(t, [[t0,v0],[t1,v1],...], preset)`. Nunca reinicie a mola. Continua contínuo e você renderiza o frame 812 sem simular 0–811.
- **Indicador líquido**: bordas em molas diferentes (`M.stretch`) → estica no movimento. Mesmo truque no knob do toggle.
- **Em `M.track` a chave marca quando o movimento COMEÇA**, não quando chega. Cursor: comece a mover ~0,5 s antes e faça chegar ~0,3 s antes do clique — clicar em movimento parece bug. *Erro real pego no board do teste desta skill.*
- **Mire pelo layout, não no chute**: o alvo do cursor = posição do elemento × zoom da câmera, calculada das mesmas variáveis que desenham o elemento.
- **Clique só com cursor visível**; mudança de estado sem causa na tela (e som de clique sem cursor) quebra a leitura.
- **Arrasto**: enquanto o cursor segura, valor = f(posição do cursor). Ao soltar, mola volta de onde estava.
- Prompt de refactor que funciona: *"Troque toda curva de easing por springs de forma fechada de lib/motion.js. Overshoot mínimo em UI, nenhum em tipografia. Todo valor com mais de um alvo usa track()."*

## 2. Easing por papel (câmera, cor, opacidade)

Tokens prontos em `M.EASE` (cubic-bezier reais): `enter` (out-expo 0.16,1,0.3,1) · `premium` (out-quint) · `move` (in-out-quart 0.76,0,0.24,1) · `exit` (in-expo 0.7,0,0.84,0) · `pop` (out-back). Um arquivo de tokens, **nenhum número solto nas cenas** ("use só os tokens" é uma linha que funciona no prompt). Tabela completa e durações em frames: `lab.md` §2.

| Papel | Curva |
|---|---|
| Chegada | `outExpo` / `outQuint` (cauda longa; pousar demora mais que sair) |
| Movimento de câmera, inundação de cor | `inOutCubic` / `inOutSine` |
| Saída, zoom-through | `inCubic` (acelera para fora) |
| Linear | só rotação contínua, barra de progresso |

## 3. Tempo

- Movimento rápido: 0,3–0,6 s. Blur máximo no frame mais rápido.
- **Saída 40–50% mais curta que a entrada.**
- **Sobreposição**: o próximo elemento começa quando o anterior está 30–50% feito.
- **Stagger**: letras ~1 frame (16–30 ms), palavras 60–120 ms, itens de lista 40–80 ms. `M.stagger(i, n, spread, 'center'|'random'|...)`.
- **"Snap, then hold"**: mudança em 1–2 frames + assentamento com ease. Uma mudança de 0,5 s com ease lê como slide de apresentação. **O ease vai no assentamento, não na mudança.**
- Movimento que precisa cair num hit começa **40–190 ms antes**. O hit em si é instantâneo (easing mata o impacto).
- Uma ideia por vez. Um movimento herói por plano; secundários andam 50–70% da distância e começam 100–200 ms depois. O resto fica parado.
- **Algo novo a cada 2–4 s** (e com música: um layout novo por compasso; UI morph: algo em toda batida).
- Leitura: um texto fica `0,5 s + 0,3 s/palavra`. Última linha do filme ≥ 2 s. Contagem numérica 1,2–1,6 s e pousa num downbeat.
- Se "parece rápido demais": desacelere zooms e pans para 0,7× e nada mais.

## 4. Transições com causa (3–5 tipos por filme)

Cada emenda tem uma transição causada por algo na tela — inclusive a entrada do primeiro plano e a saída do último. No máximo 1/3 de cortes secos. **Mundos nunca fazem crossfade.**

| Transição | Receita |
|---|---|
| **Forma única (never cut)** | o mesmo elemento muda tamanho/raio/cor de estado em estado; conteúdo troca com blur curto (template) |
| **Objeto vira o mundo** | elemento cresce além do quadro em ~0,65 s enquanto o entorno borra 15 px; ou colapsa num ponto e o próximo mundo nasce dali |
| **Zoom pelo botão** | câmera mira o botão com blur (0,6 s), botão escala 8% → 250% em 0,35 s, ease-in forte |
| **Morph** | ~110 → 880 px em 0,2 s `outCubic`, blur horizontal 12 → 0 |
| **Carregar através** | encolhe 1 → 0,6, blur pico 6 px, atravessa o corte |
| **Inundação de cor** | 0,4 s, a partir de um elemento (nunca preto → acento direto: mova um elemento de acento) |
| **Whip** | 0,13–0,3 s de borrão; o que chega nitidiza em 0,13 s |
| **Íris** | círculo (ou forma do objeto) em 0,15 s |
| **Dip cut** | escurece 40% por 3 frames antes do corte |
| **Match cut / cut on action** | corte no frame mais rápido, mesma direção e velocidade dos dois lados; espelhe o ease (in de um lado, out do outro) |
| **Pincel (papel)** | 5 traços irregulares com atrasos [0, .14, .06, .18, .1]; cobre em p=0,5, corta sob cobertura total |

"Parece slide": entre na próxima cena através de um objeto na tela, ou corte um movimento no meio do voo.

## 5. Câmera

- Sempre viva, nunca nervosa: push lento de +5–10% por plano, ou pan ±30 px com escala ≥105% (bordas nunca aparecem).
- Zoom para cada estado preencher o quadro (o herói ocupa ≥ 40% do quadro).
- `M.camera(g, L, {x,y,zoom,rot})` centraliza um ponto do mundo. UI/legendas ficam **fora** da transformação da câmera.
- Tremor determinístico: `M.handheld(t, amp, hz)` (sutil) ou impacto decaindo `sin(d*97)·e^(-9d)`. Tremor de câmera em tudo é clichê — use em impacto.
- **Título pousado fica parado.** O movimento passa para o próximo elemento, a câmera ou o mundo. Nada de "respirar/pulsar" no lugar de movimento.

## 6. Tipografia cinética

- Varie as entradas dentro do filme (nunca fade+slide-up em tudo):
  - por palavra: blur 6px → 0 com opacidade, 0,13 s cada, 67 ms entre palavras, sem translate
  - por palavra: cinza claro → tinta, 70–100 ms entre
  - linha inteira: blur 8 → 0 em 0,13–0,2 s
  - por letra (nomes): 0,1 s entre, opacidade 0,3 → 1
  - máscara (texto sobe de dentro da linha): `M.maskReveal`
  - roleta de palavras (slot machine): ~0,1 s por giro
  - texto atrás do objeto: lê melhor 30–55% coberto
- Saída: blur + fade 0,13–0,25 s, palavra por palavra.
- `M.kinetic(g, t, text, {by:'char'|'word', from:{y,rot,blur,scale}, exit:{t}})` cobre os casos comuns.
- Uma palavra destacada no acento, e ela carrega sentido.

## 7. Personagens (quando houver)

- Antecipação, squash/stretch com volume preservado, arcos, overlap/follow-through, exagero, poses-chave fortes.
- **Evite "twinning"**: código copia valores → braços simétricos, multidão pulando em uníssono. Defase fases e sementes.
- Rosto nunca troca seco: aperta → troca sob o aperto → reação → overshoot.
- Desenho "on twos" (`M.onTwos(t)` = 12 fps), **câmera sempre "on ones"**. Objetos rápidos rastreados ficam em ones ou estroboscopam.
- Holds precisam de vida: respiração ±2%, piscar a cada ~3,3 s.
- Escala: herói em close ≈ 45% da largura; plano de trabalho 15–25%; plano geral 5–9% (e precisa de companhia).

## 8. Game feel (impactos)

- Hit-stop: congela o tempo do jogo 2–3 frames no contato (0,3 s no golpe final) enquanto os efeitos seguem.
- Todo hit = 5 coisas no mesmo frame: flash (≤ 0,6), faíscas, anel, palavra/número, tremor + par de sons (thump + crack).
- Zoom de mundo ≈ 1,3: em 1× um herói de 130 px num quadro de 1920 lê como ícone.

## 9. Loops perfeitos

- Renderize os frames **0 a N−1, nunca N**: o frame N é o 0 de novo, e mostrá-lo duas vezes é o soluço na emenda (o `render.mjs` já faz 0..N−1).
- Dirija tudo por `phase = t / DURAÇÃO` com **ciclos inteiros**: um quadrado que gira exatamente 90° por loop, uma onda que completa exatamente 2 ciclos.
- Ruído orgânico que volta ao começo: `M.loopNoise(phase)` (amostra o ruído num círculo).
- O movimento final atravessa o frame 0 (ex.: um "wobble" que começa no fim e termina no início) — a emenda some.
- Frame 0 é uma composição pronta (é o que aparece enquanto o GIF carrega). Confira: `qa.sh --loop` mede o salto último→primeiro.

## 10. Hierarquia, câmera e acessibilidade (números)

- Um herói por plano; o resto espera, escurece para 40% ou fica parado. Secundários: 50–70% do curso, 100–200 ms depois. Ambiente: < 5% do curso do herói, seno lento.
- Câmera ganha as curvas mais macias (in-out-quart); objetos, as mais firmes. Parallax: 1,0 / 0,5 / 0,2.
- Contraste de texto ≥ 4,5:1 em todo frame; ≤ 3 flashes/s (WCAG; `qa.sh` mede).
- Texto parado: alinhe a pixels inteiros (ou renderize a 2× e reduza) — texto em subpixel cintila. Em DOM, anime só `transform` e `opacity`.
- Princípios de animação escritos como números (antecipação, squash & stretch, ação sobreposta, follow-through, arcos): `lab.md` §3.

## 11. Objeto físico que guia (o que mais rendeu na galeria Prompt Motion)

Um ponto, bola ou pill atravessa a interface e **causa** cada mudança: quando toca, a tela muda e soa. Dá causa a tudo, tira a cara de slide e entrega o roteiro de som de graça.
- `M.rota(contatos)`: parábola fechada entre contatos `{t,x,y,g?}`. O contato cai exatamente em `t`, sem simular nada. `pos.achata(t)` dá o achatamento.
- **Nunca teletransporta**: o caminho de toda passagem aparece. Alvos medidos do layout (`offsetLeft/Top`), nunca chutados.
- **Com a câmera andando, trace o arco em coordenadas de tela** e converta para o mundo: em coordenadas de mundo a bola saiu do quadro num mergulho de zoom (erro real, pego por sonda em "A bola").
- Altura do pulo por gravidade: `g·T²/8`. A 128 BPM e g = 3200, uma batida dá 88 px e duas, 352. Para um voo lento antes do impacto, baixe `g`.
- Elemento que nasce no contato entra com pop curto (ζ ≈ 0,72, 5,5 Hz) no mesmo frame, nunca antes.
- Só o objeto se move muito; a UI responde pouco (reação de 9 px, decai a 16/s).
- CHECKS que valem: objeto em cada contato (distância < 2 px), objeto no quadro o tempo todo, nenhum salto entre frames.

## 12. Um mundo, uma câmera

Todos os componentes num único plano; cada close é um movimento por esse mundo. `M.camSeg(inicio, segs)` faz segmentos com zoom em espaço logarítmico.
- Um movimento por vez. Não fazer zoom in e out em seguida. Ao passar de cena, comece no zoom em que a anterior terminou, ou há salto.
- Voo longo e contínuo: dirija por **curva de velocidade** integrada em posição, não por chave a cada meio segundo.
- O plano entra já em movimento e sai acelerando; o desfoque acompanha velocidade e direção.
- Elementos fora da vez ficam escondidos por janela de tempo: num recuo de zoom, tudo o que existe no mundo aparece miniatura.
- Zoom muito grande em SVG/DOM estoura a textura: desenhe a forma gigante em canvas, em coordenadas de tela (o L de "A bola" tem 5.000 px de mundo).
- Cada cena nasce da anterior: botão vira página, cor inunda a partir de um objeto e contrai no próximo. A inundação precisa passar do canto mais distante e levar cerca de 0,3 s.
