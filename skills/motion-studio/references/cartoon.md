# Série com personagem (cartoon explicativo para Reels/TikTok/Shorts)

Modo para **episódios curtos com um herói fixo que fala**: "um CRM é um caderno que nunca esquece", "tráfego pago é uma torneira", "o pixel é o porteiro do seu site". Cada episódio tem 12–40 s, 3–8 cenas, voz, legendas palavra a palavra, boca sincronizada e uma ideia só. Projeto: `bash scripts/new.sh <pasta> --kind cartoon`.

O que faz parecer caro **não é o desenho**. É: (1) a fala manda no tempo, (2) a boca bate com a voz, (3) cada palavra forte tem um evento visual, (4) o personagem é o MESMO em todo episódio, (5) uma metáfora visual por episódio que a pessoa entende sem som.

## 1. Fórmula do episódio

**"X é Y."** O episódio inteiro é uma metáfora que transforma o abstrato (X) em uma coisa física (Y) que o herói segura, chuta, abre, enche.

| Batida | Tempo | O que acontece | Regra |
|---|---|---|---|
| Gancho | 0–2,5 s | pergunta ou dor dita em ≤ 8 palavras, texto de tela grande, herói já em pose no frame 0 | frame 0 nunca vazio; texto do gancho já assentado no frame 0 |
| Dor | 2,5–6 s | a dor vira objeto (mensagens caindo e empilhando, dinheiro vazando) | um evento por palavra forte |
| Metáfora | 6–11 s | "X é Y": o objeto Y aparece e resolve a dor na frente do público | o que o herói FALA marca na tela no mesmo frame (checklist que ticka quando ele diz "anota") |
| Prova/virada | opcional | um número real (claim com fonte) ou um antes/depois | sem número inventado |
| CTA | últimos 2–3 s | "Comenta X que eu te mostro" + assinatura do herói | CTA de comentário rende mais que "segue" em série |

Roteiro: 1 frase por cena, 6–14 palavras, verbo forte. Leia em voz alta: se tropeçar, reescreva. Português falado, não escrito ("cê" não; "você" sim, mas curto).

## 2. Contrato do projeto

```
scenes.json      roteiro: id, voiceover, hero_pose, emotion, camera, on_screen_text, sfx, transition, min_sec
hero/hero.json   o herói TRAVADO: cores, proporções, assinatura, nota "não redesenhar"
scenes/NN.js     SCENE['NN'] = { keys: [...], cues: [...], draw(g, lt, ctx) } — uma cena por arquivo
audio/lines/NN.wav  a fala de cada cena (Piper, ElevenLabs ou gravada no celular)
lib/rig.js       o boneco: poses, emoções, piscada, respiração, boca A–H/X, gesto por volume
lib/fx.js        flash, shockwave, fumaça, cogumelo, destroços, shake, speed lines, sparkles, carimbo, legendas
```

`scripts/pw.mjs` junta tudo em `data.js` sozinho (`window.SCENES, HERO, WORDS, VOICE, SCENE`). O `index.html` só LÊ.

`ctx` de cada cena: `W H u L P SAFE FLOOR sc lt t words wordTime(re) drawHero(t,x,y,altura) heroState DISPLAY`.
- `wordTime(/^anota/i)` → o instante em que o herói FALA a palavra. Use para tudo que precisa bater com a fala.
- `keys: [{ at: 1.2, pose: 'point', emotion: 'happy', look: [0.9, 0] }]` → muda a pose no tempo local da cena.
- `cues: [{ word: /^cobra/i, type: 'ding', pitch: 1.26 }]` → som na palavra (ou `at:` em segundos).

## 3. Voz primeiro, depois o tempo, depois a animação

```bash
python3 scripts/voice.py              # sintetiza o que faltar, mede, escreve tudo
python3 scripts/voice.py --no-tts     # você gravou audio/lines/NN.wav (celular serve): só mede e sincroniza
```
Saídas: `audio/voice.wav` (narração montada), `scenes.json` com `start`/`duration_sec` = **fala real + 0,3 s de respiro** (mínimo `min_sec`), `audio/words.json` (cada palavra com início/fim — faster-whisper guiado pelo texto do roteiro), `audio/mouth.json` (boca por frame), `audio/loud.json` (volume por frame + palavras de ênfase).

**Voz** (do melhor para o mais simples):
1. **Voz do próprio cliente/Gabriel gravada** (celular, ambiente quieto, uma fala por arquivo). É o que mais converte: rosto/voz da marca.
2. **VoiceStudio** (local, voz clonada, grátis): `python3 scripts/voice.py --api http://localhost:3900/v1 --api-model cosyvoice3 --api-voice <voz>` com o app aberto, ou exporte os WAV em `audio/lines/NN.wav` e rode `--no-tts`. Motor padrão OmniVoice é **não comercial**: para cliente, CosyVoice 3 / VoxCPM2 / MOSS-TTS (toolchain.md).
3. **ElevenLabs** (chave só no `.env`): gere cada fala fora, salve em `audio/lines/NN.wav`. Melhor entonação em PT-BR.
4. **Piper** offline (padrão da skill): `pip install piper-tts` e baixe uma voz pt_BR (`pt_BR-faber-medium.onnx` + `.json`) do repositório de vozes do Piper para `models/`. Ajuste `voice.rate` (1,05 = mais ágil).

**Lip sync**: com `rhubarb` (Rhubarb Lip Sync, MIT) no PATH, o `voice.py` usa o reconhecimento fonético. Sem ele, o analisador próprio: grafema → visema em português (m/b/p fecha, f/v morde, o/u bico, a abre) distribuído no tempo de cada palavra e **fechado onde o volume cai**. Cada forma fica ≥ 2 frames (boca trocando a cada frame treme).

Formas (padrão Rhubarb): `A` M/B/P fechada · `B` consoantes, dentes · `C` E/I · `D` A aberta · `E` O · `F` U/bico · `G` F/V · `H` L · `X` repouso.

## 4. O herói (rig em código)

- **Travado**: `hero/hero.json` define pele, cabelo, camisa, calça, sapato, acento, assinatura. Episódio novo nunca redesenha; só troca pose, emoção, objeto na mão. Gere a **folha do personagem** com `index.html?sheet=1` e aprove com o cliente uma vez.
- **Poses** (`idle talk point shrug surprised thumbs_up wave think panic`): ombro/cotovelo/inclinação/cabeça como alvos; o rig chega por mola (`M.track`). Nunca teleporta.
- **Emoções como código** (`neutral happy sad angry surprised worried`): sobrancelha (ângulo, altura), olho (abertura), suor, bochecha, sorriso. Uma emoção por fala; troca na palavra que a justifica.
- **Vida em repouso**: respiração (1 ciclo/3 s), piscada semeada a cada 2–5 s, gesto de fala puxado pelo volume (`env`), **pulo + sobrancelha descendo nas palavras de ênfase** (`stress`).
- **Escala**: herói ≥ 40% da altura útil. Pés em `FLOOR`. Olhar (`look`) aponta para o objeto da metáfora.

## 5. Layout vertical (9:16)

- Topo ~120 px, base ~320 px e o **trilho direito ~120 px** (curtir/comentar/compartilhar) pertencem ao app. `SAFE` já desconta os três; gancho e legendas centralizam na coluna segura.
- **Palco**: pés do herói em `FLOOR` (SAFE.bottom − 80u); **legendas abaixo do chão** em `CAPTION_Y`, nunca sobre o corpo. Texto de gancho/CTA no topo da zona segura.
- Objeto da metáfora no terço oposto ao herói; nada importante atrás da cabeça.

## 6. Legendas palavra a palavra

`FX.captions` (no `index.html`): blocos de ≤ 2 palavras/13 caracteres ou ≤ 3/18, quebra em pontuação e em pausa > 0,5 s, **nunca termina em palavra funcional** (de, que, o, pra… descem para o bloco seguinte), sem travessão, palavra atual no acento e 1,1×, palavras de ênfase ficam no acento depois de ditas, contorno grosso, maiúsculas. Altura ≥ 5,2% do lado curto (≥ 56 px em 1080; o padrão é 76 px) e confira lendo o `phone.png` (390 px). Cada palavra acende no frame em que começa.

## 7. FX em camadas (impacto que parece caro)

Um impacto bom tem **4 camadas no mesmo frame**: flash (≤ 0,6, 1–2 frames), shockwave (anel que expande e afina), objeto físico (carimbo com mola ζ 0,45, destroços balísticos, fumaça) e câmera (shake que decai). Som com pico em evento + 1 frame. **No máximo 3 impactos de tela cheia por episódio**, nunca dois em menos de 2 s. Explosão/cogumelo é para piada, não para todo corte.

## 8. Câmera e transições

`camera` por cena: `static`, `zoom_in` (1 → 1,15), `pan_left`, `shake` (só nas palavras de ênfase). Transição de saída: `whip` (chicote 0,22 s com blur) ou `cut`. Máximo 2 famílias de transição por episódio. Corte seco no fim de frase; whip quando a ideia muda.

## 9. Fluxo de produção e edição

0. `bash scripts/new.sh <pasta> --kind cartoon [--brand ...]` e `bash scripts/fonts.sh "Inter:600,800,900"` (ou a fonte da marca). Folha do herói: abra `index.html?sheet=1`.
1. Roteiro (`scenes.json`) → mostre ao cliente **o texto e a voz** antes de qualquer desenho (é o que ele consegue julgar).
2. `voice.py` → `node scripts/stills.mjs --every 0.7` → OLHE → corrija.
3. `node scripts/clips.mjs` → um MP4 por cena (30 fps, cache: só re-renderiza a cena que mudou) + `out/clips.png`.
4. **Protocolo de edição**: o cliente responde "**NN, mudança**" ("03, caderno maior", "04, CTA mais cedo"). Você mexe só em `scenes/NN.js` e roda `node scripts/clips.mjs --only NN`.
5. Final: `node scripts/render.mjs --fps 30 --sub 4` → `music.mjs` (−19 dB sob a voz) → `sfx.mjs` → `mix.sh ... --voice audio/voice.wav` → `qa.sh` + `audit-audio.py`.

Checks embutidos (`stills.mjs --checks`): gancho no frame 0, cena de 2,5–6,5 s, boca aberta no meio das palavras, boca fechada no fim.

## 10. Checklist viral (antes de entregar)

- [ ] Frame 0 já tem texto de gancho assentado + herói em pose (não "entrando").
- [ ] Entende-se sem som (metáfora visível) e entende-se só com som (passe só de áudio).
- [ ] Toda palavra forte tem um evento visual no mesmo frame.
- [ ] Nada importante sob a UI do app; legenda legível a 390 px.
- [ ] Algo muda a cada ≤ 2 s (o `qa.sh` mede: mudança visual por janela de 2 s ≥ 14%).
- [ ] Última cena com CTA de comentário e a assinatura do herói.
- [ ] Entrega junto: **capa** (frame do gancho com o texto), **legenda do post** (2 linhas + pergunta), **3–5 hashtags** do nicho, **comentário fixado** respondendo o CTA.

## 11. Série

Mantenha um `docs/SERIE.md` no kit do cliente: herói, bordão/assinatura, paleta, episódios publicados (título, metáfora, CTA, resultado). Episódio novo = copiar o projeto anterior com `new.sh --kind cartoon --brand`, trocar `scenes.json` e as cenas. O herói, o rig e o som de marca não mudam.

Bônus interativo (landing/stories): a mesma cena vira página com `?t=` controlado por scroll — o `seek(t)` puro permite isso sem reescrever nada.
