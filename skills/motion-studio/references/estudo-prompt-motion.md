# Estudo da galeria Prompt Motion, para aprimorar a skill motion-studio

Fonte: https://prompt-motion.com/?tag=product-ui, lida em 03/11/2026. 105 entradas de Product UI: 15 com direção detalhada e o resto com pedido curto. Os três filmes medidos estão na seção 1.

**Sobre os prompts:** a galeria credita os vídeos e prompts aos criadores e sinaliza `use=reference`, por isso este arquivo não os reproduz. A seção 6 tem o link de cada um; as seções 2 e 5 estão escritas com nossas palavras.

## 1. O que os números dizem

| Filme | Tamanho | BPM medido | Toques por segundo | Cortes |
|---|---|---|---|---|
| [White ball UI motion loop](https://prompt-motion.com/rossaxbt-94583b) | 10 s, 16:9 | 120 | 4,35 | 0 |
| [Food craving launch film](https://prompt-motion.com/ultimaxbt-2ddf1e) | 16 s, 16:9 | 119 | 4,43 | 1 |
| [Photo print app launch film](https://prompt-motion.com/twoclipping-221cab) | 29 s, 1:1 | 120 | 4,23 | 0 |

"Toques" é o que `beats.py` detecta como hit, cerca de um por colcheia. A leitura prática: **os filmes fortes quase não cortam e têm um evento sonoro a cada 230 ms.** O `qa.sh` da skill sugere de 0,3 a 0,6 corte por segundo para reel, e isso penaliza justamente esse estilo.

## 2. As lições mais valiosas, em ordem de impacto

### Conceito
1. **Um objeto físico conduz o filme.** Uma bola, um ponto ou um pill atravessa a interface e causa cada mudança. Ele nunca teletransporta, e o caminho de cada passagem aparece. Valor: dá causa a tudo o que muda, tira a cara de slide e entrega o roteiro de som de graça. [White ball](https://prompt-motion.com/rossaxbt-94583b)
2. **Poucos momentos extraordinários batem muitos medianos.** Um plano, uma ideia. O produto é o herói, com pouquíssimo texto, e o arco é um pensamento contínuo, como caos, controle, clareza e marca. [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)
3. **Cada cena nasce da anterior.** Sem fade, blur ou corte: o objeto muda de forma, o botão vira página, a cor inunda a partir de um objeto e contrai no próximo. O teste é o espectador achar óbvio que a cena veio dali. [Photo print](https://prompt-motion.com/twoclipping-221cab), [Food craving](https://prompt-motion.com/ultimaxbt-2ddf1e), [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)
4. **Use as peças do produto, não o print.** Quebrar a tela em componentes animáveis, ou usar os componentes reais do repositório. Não inventar tela nem número; valor de exemplo tem de parecer exemplo. [Voice agent SaaS](https://prompt-motion.com/fractadev-149adc), [mdfor.dev](https://prompt-motion.com/ho-ba-f3f0e9), [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)

### Câmera
5. **Um mundo só, uma câmera só.** Todos os componentes num mesmo plano; cada close é um movimento por esse mundo. Zoom interpolado em espaço logarítmico e um movimento por cena; não fazer zoom in e out em seguida. Ao passar de cena, começar no zoom em que a anterior terminou, ou a câmera dá um salto. [Food craving](https://prompt-motion.com/ultimaxbt-2ddf1e), [Ora 2](https://prompt-motion.com/rossaxbt-3085b7), [Prompt Motion promo](https://prompt-motion.com/antonio-kodheli-490109)
6. **Dirigir por curva de velocidade, não por chave a cada meio segundo.** Em voo contínuo, integrar a velocidade em posição evita surtos. Conferir numa prévia com fluxo óptico que a velocidade nunca cai. [Landing page 3D scroll](https://prompt-motion.com/twoclipping-d89be5)
7. **O plano entra já em movimento e sai acelerando,** com o desfoque acompanhando velocidade e direção. Corte seco só de propósito, cerca de 2 frames antes da batida. [Frame by Frame](https://prompt-motion.com/notdwd-7de38a)
8. **Tudo com alvo calculado em tempo de execução.** Cursor mira a posição viva do botão, porque a câmera segue andando durante os holds. [Prompt Motion promo](https://prompt-motion.com/antonio-kodheli-490109), [UGC ad](https://prompt-motion.com/twoclipping-6dd14e)

### Som
9. **Som é coreografia, não cama.** Todo contato faz som, e cada som é posicionado pelo pico medido. Sem SFX que não tenha causa. [White ball](https://prompt-motion.com/rossaxbt-94583b), [Photo print](https://prompt-motion.com/twoclipping-221cab)
10. **O drop é o evento central do roteiro.** Conformar a faixa para o drop cair no movimento principal, e usar o breakdown numa cena calma. Reverso de sopro nas quebras da faixa levando aos hits. [Photo print](https://prompt-motion.com/twoclipping-221cab), [Prompt Motion promo](https://prompt-motion.com/antonio-kodheli-490109)
11. **Voz com sidechain em três bandas.** Abaixar pouco os graves, bastante os médios, e ajustar frase a frase até a voz ficar cerca de 9 dB acima da música entre 300 Hz e 4 kHz. Encurtar pausas longas e nivelar frases mexendo no ganho só durante as pausas. [Ora 2](https://prompt-motion.com/rossaxbt-3085b7)
12. **Tempo de palavra confiável.** Whisper em uma passada pode errar a palavra em até meio segundo: dividir nas pausas, transcrever cada trecho e alinhar ao início medido. [Ora 2](https://prompt-motion.com/rossaxbt-3085b7)
13. **Efeitos de campo curto.** Riser de catálogo costuma ter 4 s: cortar em volta do pico. Evitar boom de trailer e riser de EDM em produto sóbrio. [Ora 2](https://prompt-motion.com/rossaxbt-3085b7), [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)

### Conferência
14. **Varredura de pops:** frames cuja diferença para o anterior é 3 vezes a dos vizinhos. É barata e pega o erro que o olho perde na contact sheet. [Photo print](https://prompt-motion.com/twoclipping-221cab), [Ora 2](https://prompt-motion.com/rossaxbt-3085b7)
15. **Um still por batida** antes do render, e quadros do MP4 decodificado depois, não só capturas do navegador. [Morphing UI](https://prompt-motion.com/demonugc-4c5753), [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)
16. **Crítico novo:** quem não construiu revê o render, e isso entra no fluxo. [Prompt Motion promo](https://prompt-motion.com/antonio-kodheli-490109)
17. **Antes de mostrar, perguntar:** toda frame poderia ser anúncio parado? Há cara de template? Há demais na tela? [Taxtello](https://prompt-motion.com/daniel-haida-8691d4)

### Forma do prompt
18. **Os melhores têm a mesma espinha:** entradas (com padrões, se a pessoa pular), direção, estrutura na grade de batidas, build, armadilhas e início (perguntar, depois mostrar o mapa de batidas e stills). Nossa skill já é parecida; falta o bloco de armadilhas e o de padrões.
19. **Nomear o que é proibido, para este filme.** Inclui o que parece técnica boa: fade em tudo, glass em tudo, zoom constante, 20 estilos de animação.
20. **Os pedidos curtos funcionam com três acréscimos:** URL ou repositório, ativos reais e música sincronizada. Sem isso, o "go all out" sozinho gera variações do mesmo reel.

## 3. Armadilhas técnicas que vale colar na skill

- Inundação de cor precisa ultrapassar o canto mais distante e levar cerca de 0,3 s; menos que isso vira flash.
- Com 4 subframes, movimento rápido deixa cópias fantasmas: subir para 8 ou desacelerar.
- `backdrop-filter: url()` lê mal mapas de deslocamento no Chromium: para vidro líquido, clonar a cena atrás do elemento.
- `opacity` ou `filter` em elemento `preserve-3d` achata e mostra as duas faces: aplicar no invólucro.
- Filho com `visibility: visible` aparece mesmo com o pai escondido: usar `inherit`.
- `will-change` em algo que a câmera escala deixa o texto borrado.
- Texto que troca dentro de forma em morph precisa de máscara e tempo próprios, senão sobrepõe.
- Texto digitado em linhas fixas: a câmera não precisa seguir um cursor que quebra linha.
- Medir texto só depois de carregar a fonte. Nome de produto longo pede escalar o conjunto, não encolher só o nome.
- Item branco em página branca precisa de borda de 1 px e sombra leve; tile da cor do fundo some.
- Vídeo dentro do filme: recodificar só com keyframes (`-g 1`) e carregar como blob, porque `http.server` não faz range; esperar o `seeked` antes de desenhar.
- Clipes reais têm cortes próprios: rodar `scdet` e fazer loop só em janelas sem corte.
- Definir `z-index` em toda camada, ou os cards flutuam sobre a inundação.
- Desfoque forte pode apagar a forma: se o frame parece vazio, baixar o desfoque.
- Vidro some em branco puro: colocar uma aura leve de cor atrás dele.

## 4. O que mudou na skill (aplicado em 03/11/2026)

| Arquivo | O quê |
|---|---|
| `scripts/qa.sh`, `audit-audio.py` | Vírgula do ffprobe 9 tratada |
| `scripts/qa.sh` | Varredura de pops e toques por segundo; filme sem corte deixou de ser tratado como defeito |
| `scripts/mix.sh` | Ganho medido + limitador em laço até o alvo; sidechain com teto perto de 8 dB; mistura intermediária em float, que evita clip antes do limitador |
| `scripts/render.mjs` | `--jpeg` sai `yuv420p` em faixa `tv` |
| `lib/motion.js` | `M.rota` (parábola fechada entre contatos) e `M.camSeg` (zoom em log) |
| `template/audio/compor.py`, `medir.py`, `scripts/exporta-rota.mjs` | Compositor em que cada contato é nota; o arranjo tem batidas fixas de "A bola" e precisa de ajuste a cada filme |
| `references/motion.md` §11–12, `sound.md` §6–7, `prompts.md` §4c, `pipeline.md`, `critique.md`, `SKILL.md` | Lições, armadilhas e modelos deste estudo |

Ficou de fora: um exemplo DOM completo em `template/`, porque "A bola" tem marca e dados de cliente. O `pipeline.md` explica a rota e o compositor traz o som.

## 5. Modelos nossos para colar na skill

### Objeto que guia (produto real)
```xml
<inputs>
Produto e URL ou repositório. Uma frase de dor. Um objeto da marca que possa virar físico (ponto, pill, forma do logo).
3 a 6 telas reais. Claims com fonte. Padrões se faltar algo: objeto = o ponto da logo; 128 BPM; vertical.
</inputs>
<direction>
Um objeto físico atravessa um único mundo e causa cada mudança: quando ele toca, a tela muda e soa.
Sem corte. Uma câmera, zoom em log. Uma ideia por tela, um movimento herói por vez.
Proibido: [nomeie aqui], objeto que teletransporta, contato sem som, som sem contato.
</direction>
<structure>
Grade em batidas. Para cada contato: batida, alvo, nota, timbre, o que muda.
Problema em tom menor e pouco movimento; silêncio; drop no maior junto da marca; uma tela por 2 compassos.
</structure>
<build>
seek(t) puro. Objeto em parábola fechada entre contatos, alvos medidos do layout, achatar no contato.
Rota única para imagem e som. Pico do som em evento + 1 frame. Panorama pela posição.
</build>
<gotchas>Cole a seção de armadilhas. Contato em elemento que ainda não entrou: entre no contato, com pop.</gotchas>
<start>Mostre roteiro em batidas e um esboço de som antes de animar. Depois um still por batida e varredura de pops.</start>
```

### Som como melodia
```text
Cada contato da rota tem nota escrita à mão. Timbre por superfície, nunca um som só. Tom menor antes do drop, maior depois.
Camadas entram por seção. Uma batida de silêncio antes do maior impacto. Contato de 5 a 11 dB acima da trilha na banda de 300 Hz a 6 kHz.
Bumbo com "knock" perto de 200 Hz e banda de celular a menos de 5 dB da cheia. Tudo sintetizado; meça, não invente que ouviu.
```

### Pedido curto que funciona
```text
Filme de [N] s para [produto] ([URL ou repositório]). Use ativos e componentes reais, quebre as telas em peças animáveis.
Três momentos extraordinários, não dez medianos. Cada cena nasce da anterior. Música com drop no momento principal.
Roteiro em batidas primeiro. Depois confira frame a frame, inclusive no MP4 decodificado.
```

## 6. Todos os prompts lidos, com link

Mais longos primeiro. "Sim" na coluna Música indica a etiqueta Music da galeria.

| Título | Tamanho do prompt | Música | Etiquetas | Link |
|---|---|---|---|---|
| Taxtello bookkeeping app film | 14.877 car. |  | Charts | [abrir](https://prompt-motion.com/daniel-haida-8691d4) |
| Launch video remake comparison | 10.414 car. | Sim | Photos | [abrir](https://prompt-motion.com/notdwd-c2037d) |
| Frame by Frame launch video | 10.306 car. | Sim |  | [abrir](https://prompt-motion.com/notdwd-7de38a) |
| Spotify product film | 8.131 car. | Sim |  | [abrir](https://prompt-motion.com/brainextends-e19ac3) |
| Landing page 3D scroll | 6.633 car. |  | Kinetic type | [abrir](https://prompt-motion.com/twoclipping-d89be5) |
| Ora 2 image model launch film | 5.790 car. | Sim | Photos | [abrir](https://prompt-motion.com/rossaxbt-3085b7) |
| Photo print app launch film | 5.217 car. | Sim | Phone, Photos | [abrir](https://prompt-motion.com/twoclipping-221cab) |
| Food craving launch film | 4.654 car. | Sim | Kinetic type, Photos | [abrir](https://prompt-motion.com/ultimaxbt-2ddf1e) |
| Prompt Motion site promo | 3.976 car. | Sim |  | [abrir](https://prompt-motion.com/antonio-kodheli-490109) |
| White ball UI motion loop | 3.672 car. | Sim |  | [abrir](https://prompt-motion.com/rossaxbt-94583b) |
| Morphing UI states loop | 2.706 car. | Sim |  | [abrir](https://prompt-motion.com/demonugc-4c5753) |
| Shape morphing through UI states | 2.706 car. | Sim | Charts | [abrir](https://prompt-motion.com/twoclipping-5cba86) |
| UGC ad generator promo | 2.509 car. | Sim | Phone, Photos | [abrir](https://prompt-motion.com/twoclipping-6dd14e) |
| Voice agent landing page | 2.487 car. | Sim |  | [abrir](https://prompt-motion.com/pankajstwt-49978ed) |
| Developer portfolio site showreel | 1.005 car. | Sim |  | [abrir](https://prompt-motion.com/wani-shola-16ca7a) |
| SaaS launch video | 996 car. | Sim |  | [abrir](https://prompt-motion.com/aschapmann-131210) |
| Sahi trading terminal reveal | 631 car. |  | Phone, Charts, Particles | [abrir](https://prompt-motion.com/dale-vaz-cc612a) |
| mdfor.dev product intro video | 597 car. |  | Code | [abrir](https://prompt-motion.com/ho-ba-f3f0e9) |
| Visual guides library launch | 519 car. |  | Diagrams, Code | [abrir](https://prompt-motion.com/techyoutbe-945b56) |
| Badge unlock screen animation | 416 car. |  | Phone, Particles | [abrir](https://prompt-motion.com/bthreeagency-b9b8d9) |
| Supademo launch video | 409 car. | Sim | Kinetic type | [abrir](https://prompt-motion.com/jhylee95-e1152f) |
| org2html product showreel | 339 car. |  | Code | [abrir](https://prompt-motion.com/kyonax-on-tech-aabc1d) |
| DistilBook product explainer | 339 car. |  | Diagrams | [abrir](https://prompt-motion.com/sudo-kiran-6609ed) |
| Datagran ChatGPT ads explainer | 332 car. |  | Phone, Charts | [abrir](https://prompt-motion.com/charlesmendez-73b6e4) |
| Portfolio motion reel | 331 car. |  | Kinetic type, Particles | [abrir](https://prompt-motion.com/heyiammallik-e72d17) |
| Muse connector tracker promo | 315 car. |  |  | [abrir](https://prompt-motion.com/elliot-garreffa-f334bc) |
| ViralGrow product promo | 300 car. |  | Phone, Photos | [abrir](https://prompt-motion.com/samuel-yostt-891f87) |
| Motion designer showreel | 276 car. |  | Charts, Kinetic type | [abrir](https://prompt-motion.com/danilowm-d3720d) |
| Stock analysis app promo | 272 car. |  | Charts | [abrir](https://prompt-motion.com/aistocksavvy-3fb9f5) |
| Lidlezz app promo | 268 car. |  |  | [abrir](https://prompt-motion.com/cansincengiz-me-cf68dd) |
| Email verification tool promo | 254 car. |  |  | [abrir](https://prompt-motion.com/kmasiff-cc72cb) |
| Commotion app showreel | 252 car. |  | Phone, Code | [abrir](https://prompt-motion.com/amol909s-27533e) |
| Reddit marketing tool launch video | 227 car. |  | Characters | [abrir](https://prompt-motion.com/anthonyriera-9b1b2a) |
| SaaS product launch video | 226 car. |  |  | [abrir](https://prompt-motion.com/xelandre-363f00) |
| Jev engineering showreel | 222 car. | Sim | Kinetic type | [abrir](https://prompt-motion.com/polydao-7a572b) |
| Database client launch video | 221 car. |  | Code | [abrir](https://prompt-motion.com/iammxfschr-d68f90) |
| Sherwood agentic hedge fund explainer | 212 car. |  | Kinetic type, Photos | [abrir](https://prompt-motion.com/imthatcarlos-e04bfe) |
| Voice agent SaaS launch | 206 car. |  | Charts | [abrir](https://prompt-motion.com/fractadev-149adc) |
| Dub promo video | 203 car. |  | Charts | [abrir](https://prompt-motion.com/steventey-0d20e4) |
| Product intro synced to music | 201 car. | Sim | Particles | [abrir](https://prompt-motion.com/bogdandragomir-35e024) |
| Browser automation skill launch | 201 car. | Sim | Code | [abrir](https://prompt-motion.com/hqmank-7c61f1) |
| HTML app demo skill | 201 car. |  |  | [abrir](https://prompt-motion.com/mengto-a7f4679) |
| Tennis game launch video | 197 car. |  | Phone | [abrir](https://prompt-motion.com/deifosv-04e4d3) |
| Website analyzer product promo | 194 car. |  |  | [abrir](https://prompt-motion.com/en-ra-81c6dd) |
| TasteSkill dashboard showcase | 189 car. |  | Charts | [abrir](https://prompt-motion.com/lexnlin-f9b3bd8) |
| Cinetic skill launch film | 188 car. |  | Code | [abrir](https://prompt-motion.com/lexnlin-6161a6) |
| Fitters Bible app promo | 181 car. |  | Phone, Diagrams | [abrir](https://prompt-motion.com/adamdesgns-478d6d) |
| Chunku product promo | 179 car. |  | Kinetic type | [abrir](https://prompt-motion.com/reyzostyle-b55864) |
| Amazon wholesale pitch video | 176 car. |  | Kinetic type | [abrir](https://prompt-motion.com/ceowinkz-7c776b) |
| sweetRegret app update reel | 176 car. |  | Phone, Characters | [abrir](https://prompt-motion.com/thilina-a-891c09) |
| Bento.surf product video | 174 car. |  | Phone | [abrir](https://prompt-motion.com/bizibeast-10f264) |
| Distilbook product video | 173 car. |  |  | [abrir](https://prompt-motion.com/ajith-io-c52e09) |
| Distilbook motion showreel | 173 car. | Sim | Kinetic type, Particles | [abrir](https://prompt-motion.com/itisrazak-3ad902) |
| Motion designer showreel | 169 car. |  | Phone, Charts, Kinetic type | [abrir](https://prompt-motion.com/kangaroohere-b10f8d) |
| Whiteboard skill tutorial | 169 car. |  | Diagrams | [abrir](https://prompt-motion.com/lemomo-ai-0d9cff) |
| Bold Pilot SEO promo | 166 car. |  | Charts, Kinetic type | [abrir](https://prompt-motion.com/utopyaszx-1b2f94) |
| Trezio app motion reel | 162 car. |  | Kinetic type | [abrir](https://prompt-motion.com/agonaliu-466a8f) |
| Dubz Up motion showreel | 160 car. |  | Phone, Kinetic type, Characters | [abrir](https://prompt-motion.com/devius-maximus-beab45) |
| FundMyCompute platform overview | 156 car. |  | Diagrams | [abrir](https://prompt-motion.com/jayscambler-3f8889) |
| Second brain service promo | 156 car. |  | Code | [abrir](https://prompt-motion.com/theviableedge-9065be) |
| QuickDesign brand promo | 152 car. | Sim | Kinetic type | [abrir](https://prompt-motion.com/quickdesignio-dd93d0) |
| Enxovaly baby app promo | 151 car. |  | Phone | [abrir](https://prompt-motion.com/gabrielbuzziv-4ff0c6) |
| Crux motion design showreel | 151 car. | Sim | Charts, Kinetic type | [abrir](https://prompt-motion.com/marouanegazouzi-6071d5) |
| Quetzal social app reel | 151 car. |  | Photos | [abrir](https://prompt-motion.com/miskinho-443898) |
| AjustaCV Pro pricing promo | 151 car. |  |  | [abrir](https://prompt-motion.com/thayto-dev-44b911) |
| Travel visa service promo | 151 car. |  | Kinetic type, Photos | [abrir](https://prompt-motion.com/thismacapital-dfba20) |
| SuperX feature release teaser | 148 car. |  |  | [abrir](https://prompt-motion.com/robj3d3-b18fad) |
| DistilBook product explainer | 142 car. |  |  | [abrir](https://prompt-motion.com/sudo-kiran-4f8b59) |
| DistilBook motion explainer | 142 car. |  | Diagrams | [abrir](https://prompt-motion.com/sudo-kiran-b055de) |
| Ondefica app motion reel | 140 car. |  | Phone, Charts, Kinetic type | [abrir](https://prompt-motion.com/jesscaroline7-1ff7cb) |
| Gene Spectra promo | 138 car. |  |  | [abrir](https://prompt-motion.com/madebyjmayala-b9204d) |
| GenVizu product launch | 136 car. |  | Photos | [abrir](https://prompt-motion.com/listudio-820c7b) |
| Ren app launch video | 135 car. |  | Phone, Charts | [abrir](https://prompt-motion.com/macrohou-33959d) |
| Alan agent platform promo | 129 car. |  | Diagrams | [abrir](https://prompt-motion.com/prasad-pilla-2c0cba) |
| Photo retouch app promo | 127 car. |  | Photos | [abrir](https://prompt-motion.com/oliahmed205-3e31c4) |
| Tented image gen product video | 124 car. |  | Photos | [abrir](https://prompt-motion.com/justincooperman-e7bbc4) |
| founder.page launch video | 123 car. |  | Charts | [abrir](https://prompt-motion.com/ratheejaisal-1f4538) |
| Email tool promo reel | 118 car. |  | Kinetic type | [abrir](https://prompt-motion.com/melvynx-6cde6c) |
| Lism CSS 1.0 release video | 112 car. |  | Code | [abrir](https://prompt-motion.com/ddryo-loos-300829) |
| Personal skills showreel | 108 car. |  | Particles, Characters | [abrir](https://prompt-motion.com/ibrahimwasim240-809370) |
| MotionSites one million visitors | 106 car. |  | Charts, Code | [abrir](https://prompt-motion.com/viktoroddy-98c1d8) |
| AllInvestView product promo | 105 car. |  | Phone, Charts | [abrir](https://prompt-motion.com/rammanq-f5a90f) |
| Pixelup Labs studio showreel | 102 car. |  | Photos | [abrir](https://prompt-motion.com/arjunsh1607-93005d) |
| Norilu product launch video | 102 car. |  |  | [abrir](https://prompt-motion.com/sachaarbonel-8f14f4) |
| Supasito launch video | 99 car. |  |  | [abrir](https://prompt-motion.com/wozu-co-242285) |
| Sotto reading app explainer | 96 car. |  | Phone | [abrir](https://prompt-motion.com/1stnoel-c20a89) |
| Design portfolio video reel | 96 car. |  | Phone | [abrir](https://prompt-motion.com/kikelopezdesign-7cc9e8) |
| CloudJoi search showcase | 95 car. |  | Photos | [abrir](https://prompt-motion.com/lester-tyy-f897f7) |
| Tally product demo | 93 car. |  | Kinetic type | [abrir](https://prompt-motion.com/visheshbaghell-3aba37) |
| Five scroll-based sections | 89 car. |  | Photos | [abrir](https://prompt-motion.com/ercankeskinx-ec2568) |
| YouTube transcript product ad | 83 car. |  | Kinetic type | [abrir](https://prompt-motion.com/tstfully-0aa6b4) |
| Mascot referral program promo | 81 car. |  | Characters | [abrir](https://prompt-motion.com/paulo-kombucha-96431c) |
| AIsa API key promo | 68 car. |  |  | [abrir](https://prompt-motion.com/0xfemyn-e114d3) |
| AgentHud project motion video | 63 car. |  | Code | [abrir](https://prompt-motion.com/jazzen-chen-4542ae) |
| Step race app promo | 59 car. |  |  | [abrir](https://prompt-motion.com/marklaunches-3b9492) |
| Studio website showreel | 55 car. |  | Photos | [abrir](https://prompt-motion.com/andginja-333d32) |
| Brieform product presentation | 55 car. |  |  | [abrir](https://prompt-motion.com/majorbaguette-fb11d7) |
| FigPad product promo | 54 car. |  |  | [abrir](https://prompt-motion.com/ai-baymax-0ef9dd) |
| PicTwin AI app ad | 52 car. |  | Photos | [abrir](https://prompt-motion.com/l3d1c-0e35a3) |
| ocrX app launch video | 51 car. |  |  | [abrir](https://prompt-motion.com/mehul4795-4a7007) |
| AI Arena product promo | 48 car. |  | Code | [abrir](https://prompt-motion.com/ezshine-c90d73) |
| Parenting app hype video | 44 car. |  | Phone, Kinetic type | [abrir](https://prompt-motion.com/francoxavier33-d2dfd2) |
| Three.js Skyraider aircraft model | 42 car. |  |  | [abrir](https://prompt-motion.com/buildfastwithai-ed9447) |
| Claude self-promo spot | 35 car. |  | Phone, Kinetic type | [abrir](https://prompt-motion.com/slvdev-64c45a) |
| Matra caption app promo | 34 car. |  | Phone, Photos | [abrir](https://prompt-motion.com/gautam-mer1-2ae354) |
