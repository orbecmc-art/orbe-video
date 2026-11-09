# Biblioteca de prompts — do one-liner ao brief de diretor

Escada de níveis. Escolha pelo que está em jogo, não pelo que parece mais impressionante.

| Nível | Quando | Tempo típico | Template |
|---|---|---|---|
| L1 — One-liner | testar o setup, peça de portfólio | 5–15 min | §1 |
| L2 — Marca/produto | reel de lançamento, anúncio | 20–45 min | §2 |
| L2+ — Referência | quando o look importa | +10 min | §3 |
| L3 — Spec de estados | UI morph, loop de produto, "uma forma nunca corta" | 30–60 min | §4 |
| **L3 — Objeto que guia** | Filme de venda movimentado: objeto físico, um mundo, contato é nota | 2–4 h com recibos | §4c |
| **L3 — Spec de produto (recomendado p/ cliente)** | vídeo de produto/marca real com aprovação por tabela | 45–90 min | §0 + §4b |
| L4 — Brief de diretor | clipe, curta, filme longo, autônomo por horas | horas | §5 |
| Explainer | conteúdo educativo, história, "como funciona" | 30–90 min | §6 |
| **Laboratório** | loop curto, peça 3D, logo/produto em estúdio — tudo em números | 1–3 h com recibos | §8 + `lab.md` |
| **Campanha** | 1 brief → N aberturas × formatos × CTAs | 1 vídeo bom + lote | `campaign.md` §6 |

Esforço do modelo: **medium** por padrão (no Opus 5.5 iguala/supera o Opus 5 em high); suba para xhigh/max só quando uma peça do zero errar duas vezes ou num 1º build ambicioso de lançamento. Uma sessão por marca (renderer, síntese de áudio e pipeline já existem → o segundo vídeo sai mais rápido).

**Linha que vai em todo prompt quando houver Remotion/HyperFrames/outras skills de vídeo instaladas** (testado: com framework disponível o Opus pula para ele e o resultado sai mais simples):
```
Não use HyperFrames, Remotion nem outra skill de vídeo. Faça do seu jeito natural: um index.html com window.seek(t),
render quadro a quadro com Playwright e ffmpeg. Projeto novo: salve tudo em ./<pasta-nova>, não abra filmes anteriores.
```

---

## §0 · Antes do prompt: direção e história (conversa separada)

A parte que mais muda o resultado é a **direção**. Se ela não está clara, não escreva o prompt ainda — monte a direção primeiro (pode ser numa conversa à parte e depois colar). Perguntas que fecham a direção:

1. Qual a **emoção** no fim? (confiança, euforia, calma, urgência, nostalgia, orgulho)
2. **Energia**: lento/elegante, médio/claro, rápido/enérgico? → vira BPM (90 / 110 / 128) e spring (heavy / ui / snappy)
3. **Uma referência** de que gosta (vídeo, frame, marca) e o que pegar dela
4. A **única coisa** que o espectador precisa lembrar
5. Onde vai rodar (feed, stories, site, anúncio) → formato e duração
6. O que é **proibido** para esta marca

Prompt para co-criar a direção/história com o Claude:
```
Quero criar um vídeo de motion graphics de [DURAÇÃO]s para [PRODUTO/CLIENTE] ([URL]).
Ideia: [1-2 frases]. Emoção no fim: [ ]. Energia: [ ]. Referência: [link/arquivo + o que pegar].
Me ajude a escrever o bloco <direction> e a <structure> (lista de estados na grade de batidas) do prompt abaixo.
Proponha 3 direções bem diferentes (mundo, dispositivo visual, forma; os primeiros 2 s exatos de cada),
recomende uma e escreva os blocos prontos para colar.
[cole aqui o template do §4b]
```

---

## §1 · One-liner (testa o motor, nunca a ideia)

Por que o original funciona: "showreel para currículo" define um gênero com regras conhecidas (cortes rápidos, técnica nova a cada plano, o melhor primeiro); "que designer incrível você é" torna o modelo o assunto (mostra técnicas, nada de conteúdo para errar); 15 s cabe numa passada e comporta 6–8 planos; "vai com tudo" multiplica esforço.
Fraqueza: centenas de prompts idênticos geraram reels que rimam entre si. Use para testar o setup e siga em frente.

```
faça um vídeo de motion graphics dinâmico de 15 segundos que mostre o motion designer incrível que você é,
como se fosse seu showreel para um currículo. vai com tudo.
```
Variações:
```
# mais longo, com barra de som
showreel dinâmico 16:9 de 60 segundos mostrando seus limites criativos reais. Sound design nível S, nada de pad
de synth genérico. Componha uma trilha original de piano e sincronize cada corte com ela. Exporte MP4 1080p.

# guarda-corpo anti-slop
vídeo de motion de 10 s que apresente quem você é. Evite molduras e texto nos cantos, os sinais típicos de vídeo feito por IA.

# história em vez de técnicas
use a energia de showreel, mas conte uma história: a história de [TEMA] de [INÍCIO] até hoje.
Me surpreenda com o storyboard. 45 segundos, vertical 9:16.

# persona de agência
showreel de 30 s como se você fosse um estúdio de branding de nicho para [PÚBLICO]. Crie todo gráfico do zero.
Uma cor de acento. Cada plano é uma técnica diferente.
```

## §2 · Marca / produto

Três linhas extras transformam o one-liner num vídeo de lançamento: a URL, "use screenshot/logo/assets reais", "precisa ter música". Com estrutura, fica muito melhor:

```
Faça um vídeo de motion graphics dinâmico de [20] segundos para [PRODUTO] ([URL]), com a energia
de um showreel de motion designer. Vai com tudo.

Assets
- Visite o site. Use screenshots reais (Playwright), o logo real, as cores e fontes reais.
  Salve tudo em ./assets e LISTE o que encontrou antes de animar.
- Nunca redesenhe a UI do produto de imaginação. Recorte e anime a coisa real.

História (uma batida cada, 2 a 4 s)
1. Gancho: o problema em até 5 palavras de tipografia cinética enorme.
2. O produto aparece; a UI se monta peça por peça.
3. Três features, cada uma como um momento de UI com um cursor fazendo uma ação real.
4. Um número que prova que funciona: [MÉTRICA].
5. Logo + [CTA].

Som
- Trilha original ~120 BPM sintetizada em código. Cliques de UI e whooshes na batida.

Formato: 1080x1920 (9:16) primeiro, depois 1:1 e 16:9 do mesmo timeline.
Antes do render completo, me mostre uma contact sheet com um frame por batida.
```
Upgrade: mascote/personagem que explica o produto + voz (ElevenLabs via `.env`).

## §3 · Referência (nomeie um look, alimente um frame)

```
Referência: ./refs/launch.mp4 (e ./refs/frames/*.png)

1. Extraia um frame a cada 0,5 s com ffmpeg. Estude-os.
2. Escreva ./docs/style_guide.md: paleta (hex), tipografia (família, peso, tracking), duração dos planos,
   tipos de transição, movimentos de câmera, textura/grão, como o texto entra e sai.
3. Escreva ./docs/shotlist.md para um vídeo de [DURAÇÃO]s sobre [ASSUNTO] NESSE estilo.
   Pegue a gramática da referência, nunca o conteúdo, logos ou personagens.
4. Me mostre os dois arquivos. Espere meu OK antes de qualquer código.
```
- **Analise antes de escrever**: `bash scripts/ref.sh refs/launch.mp4` dá frames, duração de cada plano, paleta e BPM prontos.
- **Ache referências** em galerias de vídeos feitos com Opus 5.5 (cada um linka o post original no X) e no whatships.com. Achou um que gosta → "desmonte este vídeo, entenda a estrutura e o design, e crie com base nele para [marca]".
- **Um frame**: screenshot de um vídeo que você ama → diga o que pegar (paleta, tipo, grão) e o que não pegar (assunto).
- **Um vídeo**: extraia frames, descreva ritmo plano a plano antes de codar.
- **Uma biblioteca**: pasta de imagens/trabalhos do usuário → `style_guide.md` primeiro.
- Com referência, **deixe o modelo escolher a técnica**. Especifique look e restrições, não a biblioteca.
- Peça **3 variantes de storyboard** e escolha uma — você escolhe uma direção em vez de consertar a primeira ideia.

## §4 · Spec de estados (o prompt mais salvo da trend)

Conceito: **uma forma, nunca corta**. Um único elemento muda tamanho, raio e cor de estado em estado (botão, loader, player, slider, gráfico, paleta de comandos); um cursor dirige cada mudança com cliques reais; o último frame = o primeiro, então faz loop.

```xml
<inputs>
Me pergunte: meu produto + URL, 8 a 12 estados de UI que contam a história dele, os dados reais de cada
estado, cores + fontes da marca + um acento, uma faixa royalty-free perto de 120 BPM (ou "sintetize"), formatos.
</inputs>

<direction>
UI motion de filme de produto, nível Dribbble. Um container nunca corta: todo estado é o mesmo elemento
mudando tamanho, raio e preenchimento enquanto o conteúdo troca atrás de um blur curto. Um cursor dirige
cada mudança com cliques e arrastos reais. Canvas neutro quente, componentes [cores], uma fonte de UI limpa,
um acento. Springs em tudo, no máximo um overshoot mínimo. A câmera dá zoom para cada estado preencher o quadro.
Proibido: easing com quique, explosões de partículas, glows, gradientes em UI chrome, ícones com traço
inconsistente, tempo morto, qualquer coisa com cara de template.
</direction>

<structure>
[BPM] BPM, [N] compassos, algo acontece em toda batida.
logo → botão CTA → campo de e-mail (digitado) → loader → check → card de dashboard → gráfico se desenha
→ tooltip no hover → paleta ⌘K → digitar para filtrar → enter → toast → logo.
</structure>

<build>
1. Um HTML, um canvas, window.seek(t). Sem transições CSS, sem timers, sem estado entre frames.
2. Springs em forma fechada. Valor com vários alvos = soma de uma mola por mudança (lib/motion.js track()).
3. Texto dentro de container que se transforma entra depois do morph começar e sai antes do próximo.
4. Indicador de abas: bordas de ataque e fuga em molas diferentes, para esticar. Mesmo truque no knob do toggle.
5. Arrastos são manipulação direta: valor vem da posição do cursor; ao soltar, mola volta de onde estava.
6. Grade de batidas da faixa (scripts/beats.py). Começa num downbeat. Sons de UI nos picos medidos.
7. Render em Chrome headless a 60 fps, 4 subframes por frame (motion blur), todos os formatos em paralelo.
8. Um frame por batida como contact sheet ANTES do render completo; conserte o que estiver fora da grade,
   apertado ou ilegível.
</build>

<gotchas>
Nunca will-change em algo que a câmera escala (texto borra). Texto que troca dentro do container precisa
de entrada/saída próprias ou sobrepõe. Último frame = primeiro, incluindo posição e velocidade do cursor.
Nunca faça fade de preto direto para o acento: mova um elemento de acento entre os estados.
Contadores usam M.count (tempo do frame) ou o blur mistura os dígitos.
</gotchas>

<start>
Me pergunte os inputs, depois me mostre a lista de estados sobre a grade de batidas antes de escrever código.
</start>
```

## §4b · Spec de produto completo (o que deu os resultados mais estáveis nos testes)

O §4 adaptado para **qualquer produto real**. É o prompt recomendado para cliente: guia a direção sem precisar supervisionar o modelo a cada passo.

```xml
<inputs>
Produto: [NOME] ([URL]). Frase do produto: use o título principal do site.
Marca: logo real, cores e fontes reais — do site ou de brand/BRAND.md se existir (kit de marca tem prioridade).
Salve os assets em ./assets e liste o que encontrou antes de animar.
Música: [faixa em ./audio/track.wav | sintetize original ~120 BPM, estilo tech].
Formatos: [9:16 e 16:9] do mesmo timeline. Duração: [20] s.
</inputs>

<direction>
[COLE AQUI A DIREÇÃO DO §0: emoção, energia, referência, mundo visual, a única coisa a lembrar.]
Uma forma conduz o filme sem cortar; um cursor real dirige as mudanças. Fundo [claro/escuro], um acento.
Proibido: título centralizado sobre gradiente, tudo com fade, rótulos de canto, glow, quique em UI,
UI inventada, tempo morto.
</direction>

<structure>
[BPM] BPM, [N] compassos, algo acontece em toda batida.
[estado 1 → estado 2 → … → logo + CTA] — cada estado mostra uma feature REAL com dados reais.
</structure>

<build>
Não use HyperFrames, Remotion nem outra skill de vídeo: um index.html, window.seek(t), springs de forma fechada,
Playwright quadro a quadro + ffmpeg, motion blur por subframes. Siga o CLAUDE.md da pasta.
Declare window.SHOTS (estados) e window.CUES (sons) no mesmo timeline das animações.
</build>

<start>
Me mostre a lista de estados na grade de batidas EM TABELA (tempo, estado, leitura, texto, som, transição)
antes de escrever código. Quando eu aprovar: construa, gere o board com um frame por estado (stills.mjs --board),
critique, conserte, e só então renderize e salve em ./resultados.
</start>
```

## §4c · Objeto que guia (produto real, o mais forte da galeria Prompt Motion)

Os melhores prompts da galeria têm a mesma espinha: entradas com padrões, direção, estrutura na grade de batidas, build, armadilhas e início (perguntar, depois mostrar). Sem os padrões, o modelo trava; sem as armadilhas, repete os mesmos erros.

```xml
<inputs>
Produto e URL ou repositório. Uma frase de dor. Um objeto da marca que possa virar físico (ponto, pill, forma do logo).
3 a 6 telas reais. Claims com fonte. Padrões se faltar algo: objeto = o ponto da logo; 128 BPM; vertical.
</inputs>
<direction>
Um objeto físico atravessa um único mundo e causa cada mudança: quando ele toca, a tela muda e soa.
Sem corte. Uma câmera, zoom em log. Uma ideia por tela, um movimento herói por vez.
Três momentos extraordinários valem mais que dez medianos: diga quais são.
Proibido: [nomeie aqui], objeto que teletransporta, contato sem som, som sem contato.
</direction>
<structure>
Grade em batidas. Para cada contato: batida, alvo, nota, timbre, o que muda.
Problema em tom menor e pouco movimento; silêncio; drop no maior junto da marca; uma tela por 2 compassos.
</structure>
<build>
seek(t) puro. M.rota para o objeto, alvos medidos do layout, achatar no contato. M.camSeg para a câmera.
Rota única para imagem e som (campaign.json). Som pelo ataque em evento + 1 frame. Panorama pela posição.
</build>
<gotchas>
Com a câmera andando, trace o arco na tela. Elemento que nasce no contato entra com pop. Esconda por janela de tempo o que não está em cena.
Cole também references/pipeline.md §6.
</gotchas>
<start>Mostre roteiro em batidas e um esboço de som antes de animar. Depois um still por batida e varredura de pops.</start>
```

**Procure o idioma do produto.** "A bola" nasceu de "não deixar a bola cair": a expressão deu conceito, imagem, som e slogan de uma vez. Antes de desenhar, pergunte que frase feita da língua do cliente descreve o que o produto impede.

**Pedido curto que funciona** (o "go all out" sozinho gera variações do mesmo reel):
```text
Filme de [N] s para [produto] ([URL ou repositório]). Use ativos e componentes reais, quebre as telas em peças animáveis.
Três momentos extraordinários, não dez medianos. Cada cena nasce da anterior. Música com drop no momento principal.
Roteiro em batidas primeiro. Depois confira frame a frame, inclusive no MP4 decodificado.
```

## §5 · Brief de diretor (L4 — horas autônomas)

Os briefs que geraram os vídeos de 2 milhões de views (9.500 e 19.000 caracteres) não descrevem um vídeo: **contratam uma equipe**.
Esqueleto: filme em uma linha · referências · ferramentas e chaves · bíblia de personagem · beat sheet · texto na tela · gates de workflow · loop de crítica · entregáveis.

```
Você é diretor, animador, sound designer e engenheiro de render de um filme de [DURAÇÃO] feito em código.
Trate como produção em várias sessões. Não corra para um render final.

## O filme em uma linha
[LOGLINE. O que o espectador deve sentir no fim.]

## Referências e insumos
- ./refs/ : [vídeo / frames / biblioteca de imagens]. Pegue a gramática, nunca o conteúdo.
- ./audio/track.wav : use sem alterar. Meça as batidas com scripts/beats.py primeiro.
- Skill motion-studio carregada; siga references/.
- APIs no .env: [ELEVENLABS_API_KEY, FAL_KEY]. Orçamento: [R$X]. Seja econômico.

## Look
[3–5 linhas: paleta, tipo, textura, linguagem de câmera. Looks proibidos.]

## Bíblia de personagem (se houver)
Proporções, paleta amostrada de uma sheet, expressões, uma trava de identidade que sobrevive a toda troca de estilo.

## Beat sheet
0:00-0:02 gancho: [a imagem mais marcante]
0:02-0:10 [ato 1]
... um payoff visual novo a cada 3-5 segundos
[FIM] o último frame prepara o primeiro (loop)

## Texto na tela
Quando a letra/legenda fica enorme, quando fica como legenda. A composição deixa espaço para ela.

## Workflow, com gates
1. docs/SPEC.md (todo adjetivo vira número) e docs/STORYBOARD.md (cada plano: frames, câmera, texto, SFX, reads).
   Me mostre o storyboard. Continue sem esperar se eu não responder em 10 minutos.
2. Stills de cada plano. Contact sheet. Crítica.
3. Animatic a 960x540 com áudio provisório. Conserte o ritmo antes do polimento.
4. Animação completa, passe de polimento, passe de som, render final.
5. Divida por capítulos entre subagentes. Escreva docs/ANIMATION_GUIDE.md antes, para todos codarem no
   mesmo estilo. Cada subagente só edita o próprio arquivo de capítulo; bug em arquivo compartilhado → reporta.

## Loop de crítica (todo plano, pelo menos 3 rodadas)
Renderize 3-5 stills, pontue 1-10 por dimensão (references/critique.md). Registre notas P0/P1/P2 em
docs/REVIEW.md. Conserte. Repita até tudo ≥ 8.

## Entregáveis
out/final.mp4 · out/qa/loop_check.mp4 · out/qa/poster.png · out/qa/contact.png · README.md com como re-renderizar
```
Movimento-chave L4 — **gerar-e-decalcar**: um modelo de vídeo renderiza as bases com personagens e física; o Opus redesenha o vídeo inteiro em JS por cima, e o espectador só vê a camada em código. Movimento de modelo de vídeo + look consistente e proprietário do código.

## §6 · Explainer / educativo / história

```
Use JS para fazer um vídeo: [CONCEITO]. Profundo mas acessível, um aluno do ensino médio acompanha.
Não só alto nível: detalhes, incluindo [o mecanismo central] e um pouco da matemática.
Antes do código, liste as afirmações factuais + fontes + pontos disputados. Rotule física/ciência não
verificada como "ilustração".
5 cenas: o problema do cliente/pergunta · a ideia central · como funciona em 3 passos · uma prova · fechamento.
Pode usar qualquer ferramenta, instalar o que precisar, pesquisar na web. Me surpreenda.
```
Briefs abertos de história ("pesquise e decida como contar; use as pinturas anexas como inspiração de clima,
não como estilo; não pareça infográfico genérico; controle criativo total") produzem os filmes longos mais fortes.

## §8 · Prompt dirigido de laboratório (exemplo preenchido — 3D de produto)

O template está em `lab.md` §1. Exemplo próprio, para uma chave de carro premium (troque palavras, mantenha os números na 1ª rodada; na 2ª, mude UM número por vez para ver o que cada um faz):
```
OBJETIVO: a chave pousa na mão de quem assiste — sensação de "é seu" — e o logo da concessionária assina.
SAÍDA: um index.html, three.js 0.160.0 (importmap local), 1080x1350 (4:5), window.renderAt(t), window.ready após fontes e pré-cálculo.
TEMPO: 6 s em loop, 60 fps = 360 frames, 120 BPM (1 batida = 30 frames). Hits nas batidas. Frame 359 flui para o 0.
MODELO (1 unidade = 1 cm): chave 7,4 x 3,1 x 1,2, cantos raio 0,6, aro de cromo 0,08 na emenda, botão central em vidro escuro.
  O que não muda: proporção e o logo do botão.
LOOK: corpo em cerâmica preta acetinada (roughness 0,42, clearcoat 0,4), cromo (metalness 1, roughness 0,05), acento [HEX DA MARCA]
  só no anel do botão. Fundo F2EFEA no centro → DED9D0 nos cantos, com dither. Key 4500 K 3,0 sup. esquerda frontal, fill 0,5
  baixo direito, rim 6500 K 4,0 trás direita. Reflexos de um estúdio construído em código (softbox superior, faixa de rim).
  Sombra de contato 0,55. Tone mapping neutro, vinheta 8%, grão 2% semeado pelo frame.
MOVIMENTO: entradas ease-out-expo, câmera ease-in-out-quart, springs ζ 0,7 (chave) e ζ 0,5 (follow-through do chaveiro), durações em frames.
PLANOS:
  0–30: faixa de luz de 2,4 de largura varre o corpo da esquerda para a direita (brilho no frame 0 = gancho).
  42–57: antecipação — a chave afunda 2% e gira -3°, segura 3 frames.
  60: sobe até a câmera (spring ζ 0,7, assentada no frame 84); chaveiro atrasa 4 frames e balança (ζ 0,5).
  90: push-in ease-out-expo 0,8 s.  150: segundo brilho cruza o botão.  210–270: hold, flutua 0,05 num seno de 1 s.
  270–330: desce e pousa com mergulho de 0,05; 300: logo em maskReveal (texto pousado fica PARADO).  330–359: volta ao enquadre do frame 0.
CÂMERA: fov 30, nunca parada. Azimute 30°→12° e volta; distância 22→16 no push; elevação 12°→18°.
PROIBIDO: gradiente roxo/azul, orbes de brilho, bloom, neon, lens flare, partículas, turntable girando, fundo escuro, texto além do logo.
QA: renderAt(t) desenha exatamente t, ruído só com semente. Stills em 0, 57, 60, 84, 150, 300, 359 antes do render. Frame 359 → 0 sem salto.
```
Depois, som por números de frame (sound.md) e follow-ups por frame (lab.md §4). Registre tudo em `docs/PROMPTS.md`.

## §7 · Pedido para a skill (o atalho)

Com a skill instalada, o curso inteiro vira uma frase:
```
/motion-studio para [URL], 20s, vertical, referência ./refs/frame.png, trilha sintetizada tech 120 BPM
```

## Higiene

- Chaves de API no `.env`, nunca no prompt (prompts são printados e compartilhados).
- Prompt longo é bom; prompt vago não. Cada adjetivo deveria virar um número no SPEC.md.
- Diga o framework só se precisar dele para reaproveitar ("use Remotion"); senão deixe a rota A.

## §9 · Prompt em 6 categorias (estrutura mínima que funciona — @0xForce_)

```
INSUMOS: nome do produto + site + 3–5 imagens REAIS do produto (sem placeholder).
DIREÇÃO: high-end minimalista, uma ideia por plano, muito espaço vazio, um acento.
ESTRUTURA: 10 compassos a 120 BPM (2 s cada); algo acontece em toda batida.
BUILD: analise a música com ffmpeg + numpy (beats.py), gere o visual em seek(t), costure com o render da skill.
PEGADINHAS: só material real; nada de tela inventada, número inventado ou placeholder cinza.
COMEÇO: pergunte os insumos primeiro; entregue o storyboard completo ANTES de gerar qualquer coisa.
```

## §10 · Showreel de 5 s num prompt (studio-grade) — @0xWroomie, adaptado à skill

```
<direction>
Showreel de 5 s que prova um motion designer de primeira. Escolha UM conceito visual e nomeie-o em uma linha antes de começar.
Cada plano é feito do anterior: forma, tipo e cor se transformam na cena seguinte — sem corte, sem fade.
Uma fonte, no máximo 3 cores + preto e branco, uma linguagem de câmera.
Identidade: <cores hex da marca com papéis — fundo, acento dominante, acento secundário, preto, branco>; <traço/textura
(ex.: contorno escuro "à mão" com leve irregularidade, preenchimento chapado, sombra deslocada sutil, textura de papel longe do texto;
CONTORNOS E TEXTURA ESTÁVEIS — não podem tremer de um frame para o outro)>; <fonte única, pesos>.
Mostre alcance, tempos iguais: tipografia cinética, morph de forma, um momento 2D→3D, um momento de dado/UI, título final.
Proibido: partículas, glow, lens flare, camera shake, RGB split, crossfade, gradiente genérico, easing com quique,
hold maior que meio segundo, qualquer coisa com cara de template.
</direction>
<structure>120 BPM, algo em toda batida. 1º compasso: gancho. Depois uma técnica por compasso, uma saindo da outra.
Último compasso cheio: o momento mais forte. Meio compasso final: título; o último frame casa com o primeiro (loop).</structure>
<build>Use a skill motion-studio (seek(t) puro, molas e expo como funções do tempo, blur pela velocidade).
Som em código: bumbo em toda batida, riser para o último compasso, hit em cada troca de cena.
Antes de entregar: um frame por batida (stills --beats), legibilidade, sobreposição, sincronia.</build>
<start>Diga o conceito, mostre o storyboard batida a batida e então construa sem me perguntar mais nada.</start>
```
Sem ferramentas de render (chat comum)? Peça a entrega como **HTML com Play/Gravar** (`lib/recorder.js`; na skill: `node scripts/bundle.mjs --audio out/final.mp4`) — o cliente grava o MP4 no navegador dele.

## §11 · Explainer: devagar, para ser lido

Um reel de 5 s impressiona; um explainer precisa ser LIDO. Antes de qualquer animação, feche 5 coisas: objetivo, público, sequência, formato, estilo — e a lista exata de palavras e números que a animação pode mostrar (notícia: verificada antes). Descreva a mudança numa frase ("um pedido vira um resultado", "um filtro encurta uma lista"). Se precisar de várias ideias sem relação, faça a 1ª versão menor.

Exemplo planejado (15 s mudos, o cartão fica no mesmo lugar o tempo todo): 0–3 s notas originais · 3–6 s destaca as linhas relevantes, de cima para baixo · 6–9 s some o texto velho com o cartão parado · 9–12 s entra o resumo · 12–15 s segura o resultado para leitura. Antes do build completo: stills da abertura, da mudança principal e do frame final — a mensagem tem de ficar clara sem explicação ao lado.

## §12 · Notas específicas (o que funciona na iteração)

- Em vez de "deixa mais profissional": *"Mantenha layout, paleta e texto. Aumente o resumo, remova o selo extra, use só uma marca laranja de ênfase. Deixe o estado final visível por 3 segundos."*
- Rótulos sobrepostos: *"Mantenha a ordem das cenas. Termine o texto que sai ANTES de trazer o novo. Remova todo frame em que os dois rótulos se sobrepõem."*
- Estilo desenhado à mão: *"Mantenha o contorno FIXO; anime só posição e tamanho"* (borda irregular que muda de forma a cada frame = tremedeira). Compare o mesmo timestamp antes e depois de cada revisão; depois assista em velocidade normal.
- Confira o ARQUIVO gravado/renderizado, não o preview: texto certo e dentro do quadro, transformações legíveis em velocidade normal, rótulos curtos legíveis no celular, acentos do som nas mudanças visuais, loop sem pulo.
