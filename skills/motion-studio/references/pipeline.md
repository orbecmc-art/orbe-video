# Pipeline — motor de render, determinismo e rotas

> O Claude não emite MP4. Ele escreve um **programa** que pinta qualquer instante `t`; outra coisa vira esse programa em frames.
> O prompt é 10% do vídeo. Os outros 90% são esse harness.

## 1. As rotas

| Rota | Quando | Como |
|---|---|---|
| **A — `seek(t)` em canvas** (padrão) | Quase tudo: reels, UI morph, kinetic type, explainers, logo | `index.html` + `lib/motion.js` + `scripts/render.mjs`. Zero dependências. É o que o Opus escolhe sozinho. |
| **A' — `seek(t)` em DOM/SVG** | UI densa de produto: bolhas, cards, tabelas, texto com quebra. Sai com muito menos código que canvas e usa o CSS real do produto | Mesmo contrato; sem `<canvas id="c">` o `render.mjs` tira screenshot. Estilos calculados dentro de `seek(t)`, nunca transições CSS. Um canvas com outro id cuida de fundo, partículas e formas gigantes. Render a 60 fps com `--sub 4` levou de 3 a 11 min para 50 s. |
| **B1 — Remotion (React)** | Séries, templates reaproveitáveis, vídeo dirigido por dados, time que já usa React | Skill `remotion-video` (já instalada) ou `npx skills add remotion-dev/skills`. Diga explicitamente "use Remotion" — senão o Opus foge para a rota A. |
| **B2 — HyperFrames (HTML + GSAP)** | Pensa em páginas web; precisa de GSAP | `npx hyperframes init` + skills `/hyperframes`. Timeline GSAP **pausada**, `fromTo` (nunca `from`), sem `repeat:-1`. |
| **C — node-canvas / p5.brush** | Estética desenhada à mão (papel, aquarela, pincel) | Mesmo contrato `draw(t)`; boil re-semeado 10–12×/s por elemento. |
| **D — gerar-e-decalcar** | Personagens/físicas difíceis de codar (L4, longo) | Modelo de vídeo (Seedance etc.) gera a base; o JS redesenha tudo por cima e só a camada em código aparece. |

Na dúvida: **rota A**. Ela é a mais rápida de iterar (uma edição de 1 linha + re-render do trecho).

**Rota pura vence framework no Opus 5.5.** Remotion e HyperFrames ficaram famosos porque ajudavam modelos antigos; no Opus 5.5 o melhor resultado sai com ele escrevendo o código do jeito dele. Teste lado a lado (mesmo prompt de app de delivery): a versão pura saiu mais dinâmica e detalhada; a via HyperFrames, mais simples. E com framework instalado o Opus **pula direto para ele** — por isso o prompt precisa dizer "não use HyperFrames/Remotion/outra skill de vídeo" e esta skill **não** chama a skill `remotion-video` a menos que o usuário peça Remotion.
Use framework só quando o motivo é reaproveitamento (série/template/dados) e não qualidade.

## 2. O contrato de render (inegociável)

- `window.seek(t)` pinta o frame `t` (segundos). **Função pura**: qualquer frame, em qualquer ordem, sempre igual.
- Proibido em modo render: `setTimeout`/`setInterval`, `requestAnimationFrame` como relógio, transições/keyframes CSS, `Math.random`, `Date.now`, contadores/estado entre frames, física integrada passo a passo, GSAP `repeat:-1`.
- Simulações (partículas, físicas) → rode **uma vez no load** para arrays e consulte o estado em `t`.
- Aleatoriedade → `M.rng(seed)`, `M.hash1`, `M.noise1/2`. Semente vem do **nome do elemento**, nunca do índice do frame. Se um elemento usa quantidade variável de random, re-semeie por elemento (senão tudo depois dele "treme").
- Tempo de batida: `B(n) = offset + n * 60/BPM` calculado (nunca somando batidas arredondadas — deriva 2 frames em 32 batidas).
- Valores **discretos** (contadores, troca de texto, índice de lista, "on twos") → `M.frameT(t)` / `M.count(...)`. Os subframes do motion blur misturam dígitos ("4̶3̶2") se você usar `t` direto. *Bug real encontrado no teste desta skill.*
- `seek` deve aceitar `t < 0` e `t > DURATION` (os subframes do blur pedem): use `M.clamp(t, 0, DURATION-1e-4)`.
- Fontes: canvas **não** carrega fonte sozinho. Liste em `FONTS` e aguarde `window.ready = Promise.all(FONTS.map(f => document.fonts.load(f)))`.
- Formato: leia `?w=&h=` da URL; escreva cenas com `L = M.layout(W,H)` e unidades `u`. Um timeline → 9:16, 1:1, 16:9 (re-enquadre tipografia/UI por formato; nunca corte um 16:9).

### Contrato de render para colar embaixo de qualquer prompt
```
Um index.html autocontido. Só as bibliotecas que o prompt nomeia, com versão fixa. Nenhuma requisição de rede além de fontes e dessas bibliotecas.
Todo frame é função pura do tempo t, em segundos. Exponha window.seek(t) (ou window.renderAt(t)) que desenha exatamente aquele frame.
Anime com Canvas 2D, SVG, WebGL, CSS @keyframes ou Web Animations — o renderer pausa e posiciona as animações CSS/WAAPI em t.
Nada de Date.now, setTimeout/setInterval disparando, Math.random sem semente, estado carregado entre frames.
Loops: renderize os frames 0 a N-1, e o frame N-1 flui para o frame 0. Espere document.fonts.ready antes do primeiro frame.
```
Cada linha fecha um jeito de o render dar errado: relógio/timer → o frame 84 sai diferente a cada render; random sem semente → formas tremem; renderizar o frame N → soluço na emenda.

## 3. Render

```bash
node scripts/render.mjs index.html --fps 60 --sub 4 --out out/silent.mp4           # final
node scripts/render.mjs index.html --fps 30 --sub 1 --out out/preview.mp4          # rascunho rápido
node scripts/render.mjs index.html --from 4 --to 7 --out out/part.mp4              # re-render só do trecho
node scripts/render.mjs index.html --format 1x1 & node scripts/render.mjs index.html --format 16x9   # formatos em paralelo
```
- Motion blur: `--sub 4` subframes por frame, obturador `--shutter 0.5` (180°), média em **luz linear** (como o filme registra; `--linear 0` desliga). No modo canvas a média é feita **dentro da página** (só 1 PNG trafega por frame).
- Variantes de campanha: `--hook <id> --cta <id>`. O `campaign.json` ao lado do html é sincronizado em `campaign.js` antes de cada render.
- Páginas só com CSS `@keyframes`/Web Animations também renderizam: o renderer chama `seek/renderAt` e pausa cada animação em `t`.
- `--workers N` paraleliza (padrão = CPUs−1). `--jpeg` é cerca de 2x mais rápido; para o master, prefira PNG.
- Encode: H.264, `yuv420p`, CRF 16, `+faststart`, BT.709 — toca em qualquer lugar.
- Rascunho a 30 fps sem blur; final a 60 fps com `--sub 4` (ou 30 fps `--sub 4` para social pesado).
- Trechos: re-renderize só os segundos afetados e junte com concat demuxer `-c copy` (mesmo fps/size/encoder).

## 4. Verificações de determinismo

```bash
node scripts/stills.mjs --times 1.25,4.1,7.9 --out out/a.png && node scripts/stills.mjs --times 7.9,4.1,1.25 --out out/b.png
# os PNGs em out/stills/ precisam ter o mesmo hash nas duas ordens (md5sum out/stills/*)
```
Escolha instantes que **atravessem cada passagem de cena** — um filme passou na verificação só porque nenhuma amostra cruzou uma troca com cache.

## 5. Ambiente

| Onde | Situação |
|---|---|
| **Claude Code / desktop** | Ideal: renderiza, ouve (mede), olha os próprios frames. `npm i -D playwright && npx playwright install chromium`, ffmpeg, python3+numpy. |
| **App do Claude (workspace na nuvem)** | Funciona: Node, ffmpeg, Playwright e numpy já existem. Rede limitada: Google Fonts e sites externos costumam estar bloqueados → fontes via `scripts/fonts.sh` (usa o registry do npm) e assets que o usuário anexa ou que o navegador (Claude in Chrome) captura. |
| **Chat sem ferramentas** | Só dá para escrever o HTML; o usuário roda o render. Diga isso. |

Flags úteis do Chromium: sem GPU use `--use-angle=swiftshader --enable-unsafe-swiftshader` (WebGL); imprima `UNMASKED_RENDERER_WEBGL` para detectar fallback para software. Para 2D canvas o padrão já é determinístico.

## 6. Pegadinhas visuais conhecidas

- `will-change` em algo que a câmera escala → texto borrado.
- `opacity`/`filter` em elemento `preserve-3d` achata o 3D → aplique no wrapper.
- Um pixel `NaN` apaga o frame inteiro via bloom. Valide entradas de springs.
- Gradiente linear em tela inteira sobre fundo escuro faz *banding* no H.264 → use radial + grão.
- Acento abaixo de 15% de opacidade desaparece no encode.
- Texto que troca dentro de um container que se transforma precisa de entrada/saída próprias (`M.swapAlpha`) ou sobrepõe.
- Loop: último frame = primeiro, **incluindo posição e velocidade do cursor**.
- Primeiro frame é a thumbnail: nunca vazio, preto ou só logo (por isso o `t0: -0.3` no gancho do template).
- Vídeo dentro de `seek(t)`: extraia para sequência de JPEG e aguarde o decode de cada imagem.
- Remotion: `interpolate` não faz clamp por padrão; use `extrapolateRight:'clamp'`.
- Com 4 subframes, movimento rápido deixa cópias fantasmas: suba para 8 ou desacelere.
- `backdrop-filter: url()` lê mal mapas de deslocamento no Chromium: para vidro líquido, clone a cena atrás do elemento. Vidro some em branco puro: ponha uma aura leve atrás.
- Filho com `visibility: visible` aparece mesmo com o pai escondido: use `inherit`.
- Elemento visual sem classe de entrada aparece em todas as telas do mesmo card (erro real: uma caixa cinza vazou por todo o filme). Confira o board inteiro depois de cada tela nova.
- Texto digitado em linhas fixas: a câmera não precisa seguir um cursor que quebra linha.
- Meça texto só depois de carregar a fonte. Nome de produto longo pede escalar o conjunto, não encolher só o nome.
- Item branco em página branca precisa de borda de 1 px e sombra leve. `z-index` em toda camada, ou os cards flutuam sobre a inundação.
- Vídeo com seek: recodifique só com keyframes (`-g 1`), carregue como blob e espere `seeked`. Clipes reais têm cortes próprios: rode `scdet` e faça loop só em janelas sem corte.
- Desfoque forte pode apagar a forma: se o frame parece vazio, baixe o desfoque.
- ffprobe 9 devolve vírgula no fim da linha em stream de vídeo (`-of csv=p=0`): sempre `rstrip(',')` ao ler número.

## 7. Motores: qual escolher (e licenças)

> Mapa completo de ferramentas, licenças, rota híbrida e o que instalar por nível: `references/toolchain.md`.

| Peça | Motor |
|---|---|
| Uma ideia < 10 s, tipografia, formas, UI | HTML + Canvas/CSS puro (rota A) — zero instalação |
| Série, template, vídeo dirigido por dados | Remotion (React) — **ou** a rota A com `campaign.json` (ver campaign.md) |
| Você pensa em páginas e GSAP | HyperFrames (HTML + GSAP; Apache 2.0) |
| Qualquer coisa 3D | three.js (versão fixa; ver lab.md §7) |
| Movimento dentro de um produto vivo (não vídeo) | Motion (MIT) ou GSAP (100% grátis, inclusive SplitText/MorphSVG) |
Escreva o motor na linha SAÍDA do prompt com números ("composição Remotion, 1920×1080, 30 fps, 450 frames") ou o Opus escolhe por você.
**Licença Remotion**: grátis para pessoa física e empresas de até 3 funcionários; acima disso, licença de empresa. Confira os termos atuais antes de vender. Revise também direitos de logos, fontes, efeitos e música de cada cliente.

## 8. Exportar para cada destino

```bash
bash scripts/export.sh out/final.mp4 x            # H.264 High, yuv420p, AAC, faststart (X: ≤ 140 s sem Premium, até 60 fps)
bash scripts/export.sh out/final.mp4 reels        # confere 1080×1920
bash scripts/export.sh out/final.mp4 gif          # 1 paleta, loop infinito, 25 fps (atraso EXATO de 40 ms), ≤ 1280 px, avisa > 350 frames ou > 15 MB
bash scripts/export.sh out/final.mp4 x --loop-fade   # MP4 de loop: fade de 2 ms nas pontas do áudio (padding do AAC)
```
Armadilha do GIF: atraso guardado em centésimos — 24 fps (41,7 ms) vira 40 ms e o loop corre 4% rápido, fora da batida. Use 25 ou 20 fps. Para GIF, prefira cores chapadas (gradiente = banding + peso).

## 9. Novidades v5 do render e da entrega
- `--sub auto`: amostras de blur pela quantidade de movimento no obturador (parado 1 · leve 4 · médio 8 · whip 16–32). Frame parado nunca paga blur.
- `--ss 2`: supersample — pinta em 2× e reduz com Lanczos. Traço fino e borda girada sem serrilhado. ~4× o tempo: só no master final.
- `--deband`, `--alpha` (ProRes 4444 transparente), `--master` (ProRes 422 HQ 10 bits).
- **Entrega como página**: `node scripts/bundle.mjs --audio out/final.mp4 [--title "Cliente — Peça"]` → `out/<projeto>.html` autocontido (código, cenas, fontes, imagens e trilha AAC embutidos). Abre num **player com Play · Pausar · Reiniciar · Gravar** (`lib/recorder.js`; o relógio é o áudio). O cliente aprova no celular e, se quiser, grava o MP4/WebM no navegador dele. Pode ser publicado como Artifact (link privado). Qualquer projeto também abre o player com `index.html?player=1`.
- **Prova** (`references/prova.md`): `node scripts/prove.mjs determinism` · `golden save|check --scope a-b` · `color` · `gate` · `round`.
