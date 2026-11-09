# Look — fugir do "vídeo de IA" e direcionar a estética

## 1. A lei principal

> Deixado sozinho, o mesmo brief sai com o mesmo look, rodada após rodada. Banir esse look só empurra para o próximo padrão.

O que quebra o padrão é **input de fora**, nesta ordem de força:
1. **Spec do projeto** (SPEC.md com números — ver §4)
2. **A marca real** (logo, cores, fontes, screenshots reais do produto)
3. **Uma referência** (um frame, um vídeo, uma pasta de imagens do próprio usuário)
4. **O mundo do assunto** (os materiais, objetos e linguagem do tema)

**Nomear um estilo funciona melhor que descrever um.** Uma referência dá ritmo, tipografia e transições para copiar. A sua própria biblioteca é uma referência que ninguém mais tem.

Fontes de referência: whatships.com (vídeos de lançamento), Dribbble motion, filmes de lançamento de concorrentes, o portfólio do próprio cliente.

## 2. Proibido por padrão (só se a marca/referência pedir)

**Regra Orbe — fontes fora da tela**: nenhum filme leva fonte/crédito no quadro — nada de tarja vertical "Fonte: …"
no canto, rodapé de tabela com a origem do dado, crédito de foto ou @ de banco de imagem. A fonte de cada número
fica no `campaign.json` (claim.source), no `LEIA-ME.md`/recibos e, quando a licença pedir (CC BY), na legenda do post.
Só entra no quadro se o pedido disser explicitamente ("com fonte na tela").

**Composição e cor**
- Título centralizado sobre gradiente. Tudo centralizado. Tudo entrando com fade. Todo elemento com fade + slide-up.
- Vazio preto/azul-marinho com elementos pequenos flutuando no meio. Herói minúsculo em quadro vazio.
- Glow, bloom, neon, lens flare, orbes/anéis brilhantes, partículas decorativas, explosões de partículas, shockwave, RGB split, grid floor, fundo piscando.
- Gradientes roxo/azul, mesh gradient, glass cards, gradiente em UI chrome.
- O look "papel creme + serif display + palavras em itálico de acento + rótulos 01/02 + caps monoespaçadas pequenas + pill chips".
- Rótulos de canto, bordas de quadro, colchetes de canto, HUD decorativo — os sinais clássicos de vídeo feito por IA.

**Movimento**
- Easing com quique em UI. Texto que se move enquanto é lido. Título que continua derivando depois de pousar.
- Respirar/flutuar/pulsar no lugar de movimento de verdade; escala lenta rastejando num título; push lento no fim da cena; anéis de clique.
- Toda cena entrando do mesmo jeito; mundos em crossfade; o mesmo whoosh em todo corte.
- Tempo morto.

**Layout e conteúdo**
- Três cards em linha; grade de KPIs; título sobre screenshot escurecido; logo ancorado no canto.
- Abrir digitando num campo de prompt. Abrir com "Apresentando…" ou com o logo.
- Dashboard inventado em vez da UI real; UI do produto inclinada em 3D fake.
- Barras de espectro/forma de onda como imagem principal de clipe.
- Bullet slides, ícones em círculos, diagrama inteiro mostrado de uma vez, legenda que repete o que a ação já mostra.
- Formas planas ou gradientes digitais misturados num meio pintado. Rotação 3D fake.

**Copy proibida**: "desbloqueie", "sem esforço", "revolucione", "turbine", "game-changer", "em segundos" (sem medir), pontos finais em texto de tela.

**Fontes que denunciam design gerado** (use só se a marca usar): Inter, Space Grotesk, Instrument Serif, Geist, JetBrains Mono. *O template usa Inter apenas como placeholder — troque pela fonte da marca.*

**Depois de cada primeiro render**: liste todo padrão que ele usou e adicione à linha BANNED do SPEC.md desse filme. A lista cresce a cada filme.

## 3. Construir um look a partir das regras de um MEIO, não de uma paleta

Exemplo risografia: papel (cor chapada + ruído de fibra), tinta A (tudo que se lê), tinta B (um foco fluorescente por quadro), overprint (terceira cor onde sobrepõem, chapa B 3 px fora de registro), meio-tom (todo gradiente vira pontos). **O movimento segue o meio**: imprime chapa por chapa, não faz fade.

Outros meios prontos para pedir: recorte de papel/colagem · carimbo/xilogravura · blueprint técnico · tela de terminal fósforo · aquarela com pincel (p5.brush) · claymation · pixel art com grade lógica fixa (128×96, upscale inteiro, sem AA) · editorial suíço (grid de 12 colunas) · brutalismo de internet · K-pop/clipe (troca de layout por compasso).

## 4. Adjetivo → número (SPEC.md)

| Adjetivo | Vira |
|---|---|
| premium | papel acetinado com 2% de grão, sombra de contato 0,55, springs ζ 0,8–0,9 |
| moderno | push de 30 frames num único ease, display a 9% da altura com tracking −2% |
| limpo | 12 colunas, margens de 96 px, acento em uma palavra por plano |
| brincalhão | springs ζ 0,45–0,6, poses exageradas 10–30% |
| cinematográfico | enquadramento 35 mm, luz principal sup. esquerda, contraluz, vinheta 6% |
| enérgico | 0,4–0,6 mudanças fortes/s, layout novo a cada compasso, 120–128 BPM |
| luxo | muito respiro, movimento lento (0,7×), uma fonte serifada fina, sem quique |

Especifique sempre: **brilho do fundo, cores principais e acento**. Dados do dataset: "motion graphics" sem isso cai em escuro-neutro genérico.

## 5. Tipografia e composição (pisos)

- Texto para ler ≥ 2,6% do lado curto (28 px em 1080) só para rótulo auxiliar; **legenda e texto principal ≥ 5,2% do lado curto (≥ 56 px em 1080)**. Headline ≥ 84 px, apoio ≥ 44 px (em 1080 de largura). Meça a altura efetiva (com escala do pai e perspectiva) e leia no phone.png de 390 px.
- Títulos 4–9% da altura do quadro. Palavras-herói ocupam 60–90% da largura.
- ≤ 6 palavras por linha (≤ 10 em explainer), uma linha por vez. Muitas palavras: **corte palavras, nunca encolha a fonte**.
- Uma fonte display + uma de UI. Só os pesos que a fonte realmente tem (senão vira negrito falso).
- Paleta: ≤ 6 cores + tinta. Sem preto/branco puros (#141413 e #F1EEE7 em vez de #000/#FFF). Um acento, racionado: uma palavra, o payoff e o card final.
- Arco de cor ao longo do filme (frio → quente) dá sensação de história.
- Herói ≥ 40% do quadro. "Um objeto pequeno no meio de um quadro vazio nunca é um plano."
- Contraste do texto ≥ 4,5:1 em todo frame, inclusive sobre fundo em movimento. Nada piscando mais de 3×/s.
- "Evite cara de IA" genérico só troca um padrão por outro (a própria Anthropic diz isso no guia do Opus 5.5): **nomeie** os padrões, confira quais o 1º resultado usou e aumente a lista.

## 6. Formatos e zonas seguras

| Formato | Tamanho | Uso |
|---|---|---|
| 9:16 | 1080×1920 | Reels, TikTok, Shorts, Stories. Topo ~14% e base ~22% ficam sob a UI do app (`L.safe`). Legendas a 600–700 px da base. |
| 4:5 | 1080×1350 | Feed do Instagram/Facebook (ocupa mais tela que 1:1) |
| 1:1 | 1080×1080 | Feed, LinkedIn, carrossel |
| 16:9 | 1920×1080 | YouTube, site, apresentações, X |

Escreva contra `M.layout(W,H)` e renderize todos os formatos do mesmo timeline; re-enquadre (tipografia maior no vertical, mais respiro no horizontal), nunca recorte.

## 7. Produto/marca — regras duras

- **UI real apenas.** Screenshots reais (Playwright no site ou anexos do usuário), logo real, cores e fontes reais. Recorte e anime a coisa real; nunca redesenhe telas de imaginação.
- Liste os assets encontrados antes de animar (`./assets` + inventário).
- Dados reais em cada estado (números, nomes, métricas que o usuário confirmou). Nunca invente feature, número ou depoimento.
- Para componentes de UI de alta qualidade quando não há produto: biblioteca de componentes de verdade (ex.: 21st.dev, shadcn) em vez de botão inventado.
