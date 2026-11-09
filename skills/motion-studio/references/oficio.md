# Ofício de estúdio — os números que separam "feito por IA" de "pagaram caro"

Destilado de ~35 fontes (repos de motion em código, guias de Opus 5.5/Claude Motion/HyperFrames, 124 fichas de plano do video-shotcraft, 192 movimentos do motion-prompt, 28 filmes de lançamento analisados quadro a quadro pelo motion-video-kit, feedback real de clientes). Use junto de `motion.md` (fundamentos) e `look.md` (proibidos). Funções citadas estão em `lib/motion.js`.

## 1. Regras de caso (número · regra · por quê · autoteste)

Formato herdado das regras de estúdio que vieram de reclamação de cliente. Ao revisar, audite pelo número ("R3 falhou no plano 4").

| # | Regra | Por quê | Autoteste |
|---|---|---|---|
| R1 | **O 1º corte sai um degrau mais lento** do que parece certo | todo feedback de cliente registrado pedia "mais devagar", nunca "mais rápido" | alguém que nunca viu lê cada texto até o fim? |
| R2 | Uma técnica é estrela **uma vez** por filme; lotes de entrada **aceleram** como cartas sendo dadas (`M.stag`, i^0,8) | repetir o truque mata o truque; stagger linear parece robô | qual é o momento "como fizeram isso"? há só um? |
| R3 | **Holds reservados antes de animar**: wordmark assentado ≥ 30 f, lote de entradas termina com 15 f de quietude, manchete ≥ 1,2 s, hold final ≥ 1,5 s, 300–600 ms de pausa antes de uma revelação | sem respiro não há leitura | pause em cada hold: dá para ler? |
| R4 | **≤ 3 batidas de tela cheia** (pump de escala, shake, flash) por filme, cada uma num dos bumbos mais fortes, ≥ 16 batidas de distância; pump de batida ≤ 4 batidas, uma vez | bumbo detectado é candidato, não gatilho | conte os hits de tela cheia |
| R5 | **Nada congela fora do hold final**; hold vive com push ≤ 2% ou um elemento pequeno vivo. Tempo congelado ≤ 1 s a cada 30 s | frame parado = slide | `qa.sh` → trechos parados |
| R6 | **Curva por propriedade**: opacidade chega em ~⅓ do tempo do transform (`M.enterProps`). Nunca a mesma curva para os dois | o fade longo "lava" o movimento | onion skin: o objeto já está opaco quando acelera? |
| R7 | **Pré-roll de 12–20 frames**: nenhuma cena chega com palco vazio; o plano seguinte já entra se movendo na direção da saída | palco vazio = tempo morto | primeiro frame de cada plano tem algo em movimento? |
| R8 | **Salto de tom** (fundo claro ↔ escuro): nada de slide ou crossfade (gera ~6 frames de cinza de ninguém). Use "settle" com 1 frame de gap ou inundação a partir de um objeto | crossfade de tons opostos = cinza lamacento | `stills --strip` no corte |
| R9 | **2–3 famílias de transição por filme**, uma transição por emenda; o título que sai sai ANTES do wipe, o que entra entra DEPOIS | variedade demais = vitrine de efeitos | liste as transições: cabem em 3 famílias? |
| R10 | **O que não é dito, o modelo remove**: o STORYBOARD tem a coluna "persiste na tela" (o título, o logo, a barra) | um título sumiu num caso real porque o prompt não mandava manter | cada plano diz o que fica? |
| R11 | **Legibilidade medida em pixels efetivos**: legenda ≥ 5,2% do lado curto (≥ 56 px em 1080), texto auxiliar ≥ 2,6–3%, incluindo escala do pai/perspectiva. Texto é legível de verdade OU textura deliberada — nada no meio. Leia no `phone.png` (390 px) | o celular é o padrão | `qa.sh` → phone.png |
| R12 | **Brilho/glint**: uma vez por plano, só no herói, recortado no raio da borda; conserte flash de reflexo **alargando a luz**, não apagando | glint em tudo = plástico barato | conte glints |
| R13 | Herói/assunto principal ocupa **60–85% do quadro** em filmes premium de 30 s (12–15 composições, batidas de 1,4–3,5 s) | assunto pequeno = filme de "slide" | meça na contact sheet |
| R14 | **Fly-ins pousam em slots reais** (o card voa para o lugar em que vai viver); elemento compartilhado viaja, nunca é duplicado; conteúdo de container espera ele abrir > 50% | objeto que pousa "em lugar nenhum" denuncia o template | onion skin do pouso |
| R15 | **Sem shake de câmera na mão em UI clara**; nada de tilt-shift, lens flare ou íris de estrela | lê como filtro | — |

## 2. Esqueleto de energia (promo com várias features)

Abertura de marca 8–12% (energia baixa) → plano herói 12–15% → escalada de features 55–65% com um cartão de "respiro" de 50–55 f a cada 1–2 planos → final "foto de grupo" no pico 13–16%.
Dentro de cada cena: constrói 0–30%, respira 30–70%, resolve 70–100%. A cena mais lenta é ~3× mais lenta que a mais rápida. No máximo 2 tweens dividem o mesmo easing.

Moldes curtos:
- **15 s**: 0–2 gancho · 2–5 problema · 5–9 transformação · 9–13 prova · 13–15 resolução.
- **5 batidas** (Meaghan Choi): pergunta · gancho · prova · virada · recompensa.
- **Logo reveal 10 s**: 0–2 tensão · 2–5 construção · 5–8 revelação · 8–10 hold com assinatura.

**Vocabulário semântico** (declare no SPEC): horizontal = progresso/tempo; escala = importância; rotação = mudança de estado; descer = peso/problema; subir = solução. Não use um eixo com dois sentidos no mesmo filme.

## 3. Voz de movimento da marca (presets a 30 fps)

Dois eixos — energia e tom — dão 6 presets. Escolha um por cliente e grave no BRAND.md.

| Preset | Duração típica | Curva | Overshoot | Bom para |
|---|---|---|---|---|
| Luxo | ~48 f | bezier(.4,0,.6,1) | ≤ 1,02 | concessionária premium, joalheria |
| Calmo/cuidado | ~42 f | simétrica, quase sem squash | ≈ 1,00 | clínica, saúde, advocacia |
| Confiável | ~30 f | bezier(.2,0,0,1) | ≤ 1,04 | SaaS B2B, financeiro |
| Amigável | ~24 f | mola ζ 0,6 | 1,08 | varejo, educação |
| Enérgico | ~16 f | expo out | 1,10 | fitness, lançamento, reels |
| Brincalhão | ~14 f | mola ζ 0,45 + squash | 1,15 | série de personagem, infantil |

Peça em linguagem humana com `M.springVD(t, visualDuration, bounce)`: "chega em 0,3 s, quica 0,2" = ζ 0,8, Hz 1/(1,2·0,3).

## 4. Catálogo de transições com números

| Transição | Receita |
|---|---|
| **Corte invisível** | placa desfocada cruza a lente (núcleo 2600 px + bordas suaves 340 px, 14 f, bezier(.3,0,.7,1), ~530 px/f); corte num frame que o núcleo cobre por inteiro; o conteúdo deriva +40→−40 px atravessando o corte (lê como um plano só) |
| **Light leak / queima** | 3 elipses radiais (#c2311a, #ff5a1f, #ffb347; 3000/2300/1700 px; −34°; screen); intensidade t² por 28 f, corte no pico, sai em 43 f; no pico: brilho +85%, contraste −50%, saturação −25% |
| **Versus slam** (antes/depois) | duas metades com costura diagonal de 78° entram de ±1240 px, ease-in 10 f; no frame do impacto: flash branco 0,85→0 em 3 f + shake 16 px·e^(−t/1,7) + carimbo com mola (1,9→1) |
| **Whip pan com freio** | hold ≥ 20 f; 70% da distância em 30% do tempo, pico ≥ 300 px/f, cauda ease-out de 48 f; dirija por UMA curva de velocidade integrada (`M.speedRamp`); blur ≈ 0,085×velocidade (≤ 64 px) ou `window.SUB_AT` com 16–32 amostras |
| **Portal num card** | a janela cresce 40 f, bezier(.7,0,.3,1); a cena de dentro escala 0,42→1 no mesmo relógio; 2 camadas de parallax (0,08 e 0,3); depois ≥ 30 f parado |
| **Crash zoom** | 6 f até 2,4–2,8×, rebote 3–6%, shake 14 px·e^(−t/1,8) (acima de 20 px vira glitch) |
| **Zoom-through** | atravesse o buraco da letra/objeto: escala = max^p, p = 0,8·easeIn + 0,2·easeOut (`M.zoomThrough`); a cena seguinte mora dentro do buraco a 1/max |
| **Sakuga** | movimento "em 3s" (≥ 30 px por passo, pose nova a cada passo) e então troca para fluido num frame (~3:2) |
| **Plano-sequência** (6 paradigmas) | penetração de escala · oclusor que cruza a lente · forma que casa · passagem de tempo · atravessar um reflexo · cutaway pela parede |
| **Crossfade de elemento compartilhado** | entra circOut 0–50%, sai linear 50–95% (`M.handoff`) — sem o "buraco" do crossfade simétrico |
| **Shader** (domain-warp 0,5–0,8 s, chromatic split 0,3–0,5 s…) | no máximo 1–2 emendas-herói por filme |

Emenda de corte: corte no **pico de velocidade**, mesma direção e velocidade dos dois lados, blur ~10 px em texto e 18–20 px em quadro inteiro. O render não deixa subframe atravessar corte (`window.CUTS`).

## 5. Câmera

- **2,5D de verdade** (`M.cam3`): mundo em metros, lente em px. `proj(x,y,z)` → posição, escala e blur de profundidade. Dá parallax real, **dolly ≠ zoom**, **dolly zoom** (`M.dollyZoomF`: f ∝ distância; 3,2→8 m com 132→330 px, o fundo cresce ~2,2×), órbita, grua, **rack focus** (frente 0→7 px, fundo 6→0 px em 1,6 s, bezier(.65,0,.35,1)), **bullet time** (tempo a 0,1× enquanto orbita ±0,6 rad). Camadas de parallax de trás para frente: 0,05 / 0,1 / 0,28 / 0,6 / 1,25 / 2,1.
- **Câmera que segue o objeto que guia** (`M.followCam`, pré-calculada): alvo = objeto + 0,15 s × velocidade, misturado com uma âncora fixa (peso 0,7 na interação, 0,15 em voo, 0,85 no payoff), mola crítica ω≈6. Objeto com 50–70 px em 1080p durante o voo. Reveal: para de seguir e abre ~0,3× com tilt 15–25°. Slow-mo no lançamento: `M.heroSlow` (1 − 0,9·sin(πu)^0,6). "Slot vazio": quando o objeto sai da estação fica um contorno que se enche na volta.
- **Tour 3D de cards**: câmera = inversa da pose de cada card (ordem de rotação invertida); voos de 28–32 f com recuo de 30% no meio; perspectiva ≈ 3× a maior profundidade; cards fora de foco ≥ 0,22 de opacidade.
- **Spotlight no card herói**: o resto escurece (multiply 0,90–0,94), luz suave no formato do card (nunca círculo), feixe volumétrico (screen 0,34→0,06); sobe → paira → assenta em ~108 f com sombra que cresce.
- **Impacto**: `M.impactShake` (x 15·e^(−5t)·sin(2π·5t), y 11·e^(−5t)·cos(2π·6,5t)) + squash de 22% ancorado na base.
- **Handheld que fecha loop**: `M.handheldLoop(phase)` (senos com múltiplos inteiros do ciclo).
- **Director na batida** (reels/clipes): corte a cada 4 batidas antes do drop e a cada 2 depois; punch-in 3%/7% no bumbo decaindo em e^(−Δt/0,11); drift 3,5% por compasso; drop a ~40% do clipe; o momento-herói é puxado para cair no drop.
- **Texto nítido sob zoom**: desenhe a linha uma vez num canvas 2× e escale a imagem (re-rasterizar a cada frame dá degraus visíveis num push lento). Capture UI a 2×, recortes-herói a 4×. Profundidade de campo não conserta falta de nitidez.

## 6. Polish (o acabamento)

- `M.surface(g, x,y,w,h,r,{elev})`: sombra de contato + ambiente tingida, borda de 1 px e highlight interno no topo. É o que faz um card parecer objeto.
- Grão: 0,04–0,08 em fundo claro, 0,06–0,12 em escuro (`M.grain`). Vinheta tingida, não preta. Palco com luz-chave radial + tinta do acento.
- Tracking por tamanho: −0,04 em em ≥ 96 px até +0,01 em em texto pequeno. Escala tipográfica 1080p: 260/180/120/84/60/40/32/22.
- Papéis de cor: bg ×3, superfície ×2, linha, tinta ×3, acento, acento2 (≤ 5% do quadro), sobre-acento, sombra.
- Cor entre tons: `M.mixHexQ` (espaço quadrático; o lerp sRGB enlameia o meio).
- Banding em gradiente grande: `render.mjs --deband` (gradfun + grão fino). Bitrate não resolve.
- Movimento "premium" = **um objeto mudando de forma** (não três aparecendo); deixe um fantasma leve do estado inicial; algo pequeno continua vivo no hold.
- Curva medida de referência (produto girando, braço de máquina): marque os pontos quadro a quadro e use `M.monotone` (Fritsch–Carlson); smoothstep entre chaves dá soluço no meio do giro. Trave a câmera durante o movimento-herói. Blur: obturador sobe de 180° a 300° em 6 f no giro mais rápido.

## 7. Mecanismos que vendem (dos 28 filmes de lançamento)

Fly-through de primeiro plano · logo como portal · resultado que se materializa · trilhos persistentes (a barra que atravessa o filme todo) · decomposição registrada (o produto explode em camadas alinhadas e volta) · pedido → seletor → confirmação (UI que conta a história sozinha) · "signature visual": UM momento por filme escolhido pela metáfora do produto (blocos → campo de cubos; dados → partículas que viram anel; flexibilidade → blob líquido).

## 8. Moldes de prompt/follow-up que funcionam

- Prompt único: termine com **"assuma que a v1 não é final: critique-se e faça a v2 antes de me mostrar"**.
- Follow-up de variante: **"mude X e Y; mantenha todo o resto igual"** (1–2 parâmetros por vez).
- Edição em 3 escopos: global ("tudo 10% mais lento"), capítulo nomeado ("na cena PROVA…"), elemento ("o número 98%…"). Nomeie os capítulos no STORYBOARD para isso funcionar.
- Entrevista inicial em 3 profundidades, no máximo 5 perguntas; teste de pipeline de 2 s antes do build longo.
- Estilo por **código de exemplo**, não por vídeo: modelo não "assiste" vídeo, só vê prints. Um exemplo em código do estilo (ou a nossa referência por frames do `ref.sh`) dá consistência até em modelo menor.
- Referência de estilo por **vários prints** do filme que você quer imitar + o seu roteiro com timestamps (SRT) — o maior salto de qualidade nos testes do Claude Motion.

## 9. Linguagem de movimento do filme (escreva no SPEC antes de animar; audite plano a plano)

Uma escolha por linha: **curva assinatura** (~90% dos movimentos; no máximo 2 curvas no filme) · **unidade base** (todas as durações são múltiplos dela) · família de transição · ritmo de stagger · **orçamento de intensidade** (quantos momentos fortes) · hold mínimo · 3 adjetivos de humor (desempatam decisões).

| Preset | Base | Deslocamento | Escala | Overshoot | Stagger | Hold |
|---|---|---|---|---|---|---|
| Calmo + suave | 0,6 s | ≤ 16 px | 0,98→1 | 0 | 120 ms | ≥ 0,6 s |
| Calmo + preciso | 0,4 s | ≤ 24 px | 0,96→1 | ≤ 2% | 60 ms | ≥ 0,3 s |
| Cinético + preciso | 0,25 s | livre | 1,18→1 no impacto | — | 40 ms | ≥ 0,2 s |

Curva "snappy premium" (influência assimétrica: saída 15–25%, chegada 80–90%) ≈ `cubic-bezier(.18,0,.15,1)`. Base de layout comum: `cubic-bezier(.22,1,.36,1)` 500 ms para layout, 300 ms para cor.

| # | Regra | Autoteste |
|---|---|---|
| R16 | **Duração pela distância e material** (`M.durFor`): 50 px 0,8× · 100 px 1× · 200 px 1,3× · 300 px 1,5× · 400 px 1,6× · tela cheia 1,8–2×. Rígido 1,2× sem overshoot · elástico 0,8× 15–25% · fluido 1,5× 5% · papel 1× 3–5% · gás 2× · vidro 0,9× | o objeto que anda o quadro inteiro demora o mesmo que o que anda 50 px? errado |
| R17 | **Regras de 1/3**: nada percorre > 1/3 do quadro sem chave intermediária ou troca de escala/opacidade; com ≥ 3 elementos, no máximo 1/3 se move ao mesmo tempo | conte quem se mexe no frame mais cheio |
| R18 | **Teto de stagger**: o lote inteiro em < 0,5 s (grupos grandes 0,6–0,8 s; reveal de texto ~0,8 s no total) — `M.stagCap` | o último item chega depois que o primeiro já foi lido? |
| R19 | **Contra-movimento**: herói vai à esquerda → fundo à direita a 20–30% da velocidade; herói cresce → sombra encolhe 10–20%; herói gira horário → ambiente anti-horário a 15–25% | o mundo reage ao herói? |
| R20 | **Gatilho compartilhado**: todas as reações começam até 50 ms do gatilho e POUSAM escalonadas | o clique "puxa" tudo junto? |
| R21 | **Arco**: deslocamento perpendicular no meio do caminho de 10–20 px (5 corporativo, 20+ brincalhão) | trajetória reta = robô |
| R22 | **4 atos por duração** (antecipação/ação/reação/resolução): 200–400 ms → 10–15/40–50/10–15/25–30%; > 800 ms → 20/30–35/15–20/25–30% | o movimento tem preparo e assentamento? |
| R23 | **Personagem para seguir**: um personagem pequeno dá ao olho alguém para acompanhar; **a câmera move a atenção ANTES da cena mudar**; palavras enormes interrompem a história no momento certo (kozh) | o olho sabe onde ir 0,3 s antes do corte? |
| R24 | Sem travessão (—) em texto de tela: lê como IA | — |

Composição: hierarquia = tamanho > contraste > cor > posição; foco nos pontos de força dos terços; herói em movimento a 1/3 da borda de trás com espaço à frente; secundários escurecidos 40–60% + blur 2–4 px quando o herói fala. Grade 9:16: 6 colunas, margem 48, calha 16, base 8 px; no vertical a tipografia sobe 15–25% e o layout é **reempilhado**, nunca recortado.

## 10. Pacote short-form (Reels/TikTok/Shorts)

- **Arquétipos de gancho** (uma lacuna por vídeo): loop aberto · promessa direta · negação ("Pare de…") · interrupção de padrão · prejuízo ("isso me custou R$…") · lista com referência à frente ("o 3º é o que…").
- **Orçamento de 20 s**: gancho 0–1 s · setup 1–4 · corpo 4–17 · payoff 17–20. Vídeo mais longo cresce o corpo, nunca o gancho.
- **Cortes irregulares** (ex.: 0 · 1,2 · 3,0 · 5,4 · 8,0 · 11,2 · 14,0 s): intervalo de metrônomo lê como tédio.
- **Punch-in como interrupção**: escala 1→1,10–1,12, mola ζ ≈ 0,43 (rigidez 200–220, amortecimento 12–13), origem 50%/45%.
- **Loop de frase**: a última fala emenda no frame 0 ("…e é por isso que eu nunca —"). Duração ideal para reassistir: 7–15 s.
- **Ritmo por personalidade**: premium corta a cada 8–16 batidas · corporativo 8 · brincalhão 4 sincopado · enérgico 1–2 no clímax; o arco encurta 8→4→1–2 e fecha com hold longo. Ancore a grade no offset da batida 1.
- **J-cut**: o som do plano seguinte entra 4–12 f antes; **L-cut**: o som do atual continua 12–24 f depois.
- **Zonas**: topo ~120 px, base 320 px (370 em TikTok Ads), **trilho direito 120 px** (botões); caixa universal 900×1400 no centro.
- **Ler a curva de retenção** depois de publicar: queda em 0–2 s → troque o gancho · planalto e queda no meio → interrupção a cada 2–4 s · subida no fim → estão reassistindo: encurte · pico num instante → leve esse momento para o gancho.
- Estatísticas de "x% decidem em 3 s" que circulam em repos **não têm fonte**: nunca use como claim para cliente.

## 11. O que o vídeo tem que fazer (kozh, 59 s em código)

"Fazer as coisas se moverem" não é o difícil; o difícil é fazer alguém ficar para o próximo frame. Fluxo: **referência → storyboard → animar → trilha → render → inspecionar → cortar de novo.** A vantagem do diretor é saber qual frame faz alguém assistir ao próximo — isso entra no STORYBOARD como "por que a pessoa fica" em cada batida.
