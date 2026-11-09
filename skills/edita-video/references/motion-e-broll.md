# Mapa de motion e B-roll — a etapa mais importante

O mapa decide o que o espectador VÊ além do rosto. Lei: **o conteúdo decide a animação** — cada item nasce de uma
fala específica. Teste: "esta peça serviria para qualquer vídeo?" → então troque.

## Fluxo
1. `mapa.py . rascunho` → `docs/MAPA_RASCUNHO.md` (listas "primeiro/segundo", números ditos, CTA, janelas de B-roll).
2. Leia `docs/FRASES.md` e escreva `_edit/mapa.json` (formato no topo do `mapa.py`). Âncora SEMPRE por palavra
   (`"de": "#24", "ate": "#29"`): se o corte mudar, o item acompanha.
3. `mapa.py .` valida e escreve `docs/MAPA.md` → portão ② (mostre a tabela).
4. `ativos.py . buscar` → ABRA `docs/folhas/<id>_opcoes.jpg` → `ativos.py . escolher br01=a3 …`
5. `motion_ponte.py . preparar` → `board` (ABRA `docs/folhas/motion_board.jpg`: entrada · meio · saída de cada peça
   sobre o quadro real) → critique P0/P1/P2 → `render`.

## Densidade e ritmo (por estilo)
| | dinâmico | educativo | clínica | luxo | varejo |
|---|---|---|---|---|---|
| motion/min | 4–7 | 4–6 | 2–3 | 1–3 | 4–7 |
| B-roll | 1,5–3 s a cada 4–8 s | em substantivo concreto | pontual | planos longos de produto | produto/preço |
| rosto entre cortes p/ fora | ≥ 2 s | ≥ 2 s | ≥ 3 s | ≥ 3 s | ≥ 2 s |
Regras: mudança visual a cada ≤ 5 s (corte, item, punch) · tela fora do rosto ≤ 45% do vídeo · gancho visual nos
2 s iniciais · CTA no fim · série (lista 1/2/3) = mesmo componente, mesma posição · nunca 2 revelações juntas.

## Peças prontas (assets/motion/pecas.html → motion-studio)
| peça | quando | params | duração mín. |
|---|---|---|---|
| `titulo` | gancho/tema ("3 SINAIS") | `linhas: [forte, apoio]`, `destaque` | 1,6 s |
| `palavra` | uma palavra que é o soco ("NUNCA") | `texto`, `sub` | 0,9 s |
| `numero` | número dito COM fonte do cliente (inteiro < 10 entra pronto, sem contar de 0; `contar: true` força) | `valor`, `prefixo`, `sufixo`, `rotulo`, `decimais`, `contar` | 1,6 s |
| `lista` | "primeiro… segundo…" | `n`, `total`, texto | 1,2 s |
| `lower_third` | nome/cargo na 1ª aparição | `nome`, `cargo`, `placa` | 2,0 s |
| `check` | benefícios / ✗ mitos | `itens: []`, `icone: check|x` | 0,4 s/item + 0,8 |
| `cta` | chamada final | `acao`, `palavra`, `sub` | 2,0 s |
| `comparacao` | isto × aquilo (nunca antes/depois de paciente) | `esq`, `dir` | 2,5 s |
| `texto` | cartela de tela cheia | `linhas`, `destaque` | 1,5 s |
| `frase` | texto cinematográfico (pequenas + chave em serifa) sobre rosto, B-roll ou pintura | `antes`, `chave`, `depois`, `aspas` | 1,6 s |
| `aspas` | só texto com aspas em papel (fecha a ideia) | `antes`, `chave`, `depois`, `fundo: claro|azul|escuro` | 2,0 s |
| `linha` | linha de acento que leva às palavras; câmera segue | `textos: []`, `forma: reta|zigue`, `tempos` | 0,8 s/palavra |
| `grafico` | grade fina + bola de acento traçando | `forma: degraus|sobe|plano|cai`, `degraus`, `rotulo` | 2,0 s |
| `capitulos` | UI recorrente 1·2·3 que preenche (séries) | `n`, `total`, `titulo`, `todos` | 1,0 s |
| `callout` | ponto + linha-guia + rótulo num detalhe | `ponto: [x, y]`, `texto`, `sub`, `lado` | 1,4 s |
| `etiqueta` | dossiê: tarjas pretas + etiquetas amarelas de papel rasgado empilhadas | `linhas: [{txt, tipo}]` | 1,2 s |
| `faixa` | dossiê: palavra gigante em faixa vermelha + branca | `linhas: [2]`, `foto` | 1,2 s |
| `grade` | dossiê: a conta em quadradinhos marcados | `total`, `colunas`, `rotulo`, `nota` | 2,5 s |
| `colagem` | dossiê: fotos com fita + etiquetas | `titulo`, `fotos` ou `quadros`, `etiquetas` | 2,5 s |
| `recorte` | dossiê: manchete REAL circulada de caneta | `manchete`, `circula`, `sub` | 2,0 s |
| `slam` | o número do vídeo CAI na palavra, largo como a tela; o antigo espera em cima e é riscado; onda de choque | `valor` (≤ 7 car.), `antes`, `rotulo`, `em` (s do item) | 1,6 s |
| `notificacao` | card de app que desce do topo (venda, agenda, mensagem): ícone, app, título, texto, valor, selo | `app`, `icone`, `titulo`, `texto`, `valor`, `selo`, `hora` (+ `"fundo": "escurece"`) | 1,4 s |
| `anel` | contador circular: trilho, arco na cor de destaque, número contando no meio | `valor`+`total` ou `texto`+`fracao`, `sufixo`, `rotulo`, `raio` | 1,5 s |
| `pilula` | selo de vidro com ícone + texto curto ("⏱ 1h 30m") — ancora o gancho sem tomar a tela | `texto`, `icone`: relogio·check·raio·nenhum | 1,0 s |
| `capitulos` `forma: losango` | Joseph: losangos com gradiente e traço fino, mostrados cedo; `tag: true` = o capítulo citado volta pequeno com o nome | `total`, `n`, `nomes: []`, `tag` | 1,0 s |
| `empilha` | lifestyle: GANCHO gigante que se empilha uma linha por palavra no ritmo da fala, creme, terço de cima | `linhas` (ou a fala do trecho), `{txt, em: "#3"}` amarra a linha à palavra, `tamanho`, `peso`, `cor`, `caixa` | 1,5 s |
| `rotulo` | lifestyle: a ideia-chave em dupla sans + manuscrita ("5 Ganchos / *diferentes*") no espaço livre; `estilo: tecnico` = nome + "- função -" pequenos em amarelo (passo, plano, etapa) | `linhas: ["…", {txt, fonte: script·sans·serif, tam}]` ou `titulo`+`script`+`sub` | 1,6 s |
| `doc` | card de documento/print como PROVA ou recurso (lista numerada, termo em negrito) — conteúdo REAL do cliente | `titulo`, `itens: ["Termo: texto"]`, `numerado`, `largura`, `x` | 1,8 s |
| `cartela` | entrevista: respiro — corta para tela LISA (cinza claro ou quase preto) e a fala aparece escrita, trecho a trecho, com fade (modo `tela_cheia`) | `fundo: claro·escuro·#hex`, `tamanho`, `palavras_por_trecho`, `y` | 1,2 s |
| `custom` | ideia própria | `projeto`: pasta motion-studio (`new.sh`) | — |
Leitura: no ar ≥ 0,5 s + 0,3 s por palavra. Saída em 8 quadros. Posição: `topo` (21%), `centro` (46%),
`meio-baixo` (62%), `baixo` (74,5%). Look: `card` (placa clara — clínica/luxo), `bold` (texto forte com sombra) ou
`papel` (minimal: fundo de papel claro/escuro/azul com fibra, cores foscas, serifa itálica — `estilo-minimal.md`) ou
`dossie` (papelão/papel com persiana, tarjas e etiquetas rasgadas — `estilo-dossie.md`). Fotos nas peças: `fotos`
(arquivos do projeto) ou `quadros` (segundos da sequência → quadros do próprio vídeo), copiadas pela ponte.
Peças minimal funcionam em qualquer estilo (com a fonte display da marca).
Marca: `briefing.marca` {accent, ink, paper, bg, display, ui} ou `<kit>/marca.json`.
Para peça que o catálogo não cobre (gráfico animado, UI, mapa, produto 3D): crie projeto no motion-studio
(`bash <motion-studio>/scripts/new.sh motion/mo07`), siga a skill motion-studio, e no mapa `"peca": "custom",
"projeto": "motion/mo07"` — a ponte renderiza no tamanho/fps/duração do item e lê os CUES de som dele.

## Espaço livre (`"posicao": "auto"`) e fala sincronizada (v1.5)
- `"posicao": "auto"` (lifestyle): o motion_ponte mede o rosto no quadro FINAL (rosto.py + camera.py) no intervalo da
  peça e põe a peça no maior espaço livre — acima da cabeça (pode encostar no cabelo) ou no peito, antes da UI do Reels —
  e a encolhe para caber (`vaga`). A legenda desvia sozinha (o item ganha `caixa`). Nunca texto sobre boca e olhos.
- `empilha` e `cartela` recebem as palavras ditas com tempo (`params._palavras`, o mapa.py preenche): cada linha/palavra
  entra quando é dita. A legenda some enquanto elas escrevem a fala (dois textos brigam).
- Cartela: use em 2–4 frases que importam (abertura, virada, fecho), 1–2 s cada, alternando claro e escuro; o som de
  acento é só na VOLTA para o rosto. Mais que isso vira slide.

## Cobertura do próprio cliente (montagem de planos)
Quando o cliente gravou planos (lista de planos, `references/decupagem.md`): monte na ordem estabelece → aproxima →
detalhe → reação → payoff, 1–2 s por plano, corte NA ação (o gesto começa num plano e termina no outro), match cut por
forma/movimento, POV seguido de contra-POV. Bastidor/aula: `rotulo` `estilo: tecnico` com o nome do plano/etapa.

## Texto atrás da pessoa
`"atras": true` numa peça sobreposta (palavra/título grande em `topo` ou `centro`): o compositor recorta a pessoa
(MediaPipe, ~12 ms/quadro) e a devolve por cima da peça — o texto passa por trás da cabeça. Funciona em plano médio
com fundo livre acima/ao lado da cabeça; em close fechado o texto some (escolha outra peça). Use 1–2 vezes no vídeo
(gancho, palavra-chave), nunca em lista ou CTA.

## Imagem gerada (quando o banco não tem)
Com o conector Higgsfield/Canva, gere a imagem que a frase pede (cena, objeto, conceito) e use como `foto` com
`arquivo`. Registre em CREDITOS como "gerada por IA". Saúde: nunca gerar pessoa como paciente, resultado ou antes/depois.

## Modos
- `sobreposto`: sobre o rosto, fundo transparente (ProRes 4444). Não cubra a boca por mais de 1 s; topo é o lugar
  natural de títulos/listas.
- `tela_cheia`: corta para o item (B-roll, foto, cartela). A voz continua (J/L natural).
- `split`: item em cima, rosto embaixo; legenda na emenda. Ótimo para demonstrar algo enquanto fala. Com
  `"split_fio": "accent"` no estilo, a borda vira fio grosso na cor de destaque (dinâmico/varejo).
- `janela`: o item toma a tela inteira e a pessoa vira um CARTÃO quadrado (olhos no terço superior, cantos redondos, anel,
  sombra) — entra e sai com **recuo** (o quadro inteiro encolhe até o cartão: o "zoom para fora" do Joseph). O texto da
  peça fica no terço de cima. Ótimo para CTA, comparação, "olha isso".
- Efeitos (`"tipo": "efeito"`, sem peça): `"efeito": "quebra"` = quebra de padrão (close com o nariz no centro, P&B,
  reverb na voz, trilha abafada — 1 por vídeo, na virada de assunto, ≤ 8 s) · `"efeito": "pb"` = quadro inteiro em P&B e
  a cor escorre de cima para baixo no fim do intervalo (abertura que segura até a revelação).
- Transição (`transicao`): `corte` (padrão) · `fade` (calmo) · `zoom` (dinâmico) · `whip` (troca de assunto) · `flash`
  (revelação) · `deslize` (a câmera desce e revela — pinturas e B-roll com texto).
- `"tratamento": "papel"` (B-roll/foto): papel, vinheta e borda desfocada (padrão do minimal; `"papel": 0.6` = mais leve).
- `"fundo": "escurece"` (peça sobreposta): o vídeo atrás escurece 55% e desfoca enquanto ela está no ar — a cena
  "legenda + UI" (animação pequena na metade de baixo, `posicao: meio-baixo`). Use 3–5 tipos no máximo por vídeo; ≥ 1/3 dos cortes secos.
- Ken Burns (`kenburns`): `in` · `out` · `esq` · `dir` · `sobe` · `desce` · `nenhum` (6% do estilo); `foco: [x, y]` (0–1)
  para centrar no que importa da foto; `inicio` (s) para escolher o trecho do B-roll.

## Busca de B-roll e fotos
- `busca` em inglês e CONCRETA ("woman washing face at bathroom sink", não "skincare"). O que a frase MOSTRA.
- Fontes (licença): Pexels e Pixabay (chaves grátis no `.env`: PEXELS_API_KEY, PIXABAY_API_KEY — sem elas os
  resultados são fracos), Openverse (fotos comerciais), Wikimedia Commons (CC0/PD/CC BY; nunca BY-SA/NC em anúncio).
- Escolha olhando a folha: orientação do formato, sem marca/logo de terceiro, sem texto na imagem, luz parecida com
  o A-roll, pessoa compatível com o público. Sem opção boa → nova busca, ou marque `ASSET FALTANDO` e siga (o
  compositor mantém o rosto).
- **Créditos nunca na tela** (regra Orbe): `docs/CREDITOS.md`; CC BY → crédito na legenda do post.
- Saúde: pessoa de banco de imagem nunca como paciente real, nunca "antes/depois", nunca resultado.
- Material do cliente (`broll/`): `ativos.py . conformar` (CFR, SDR, sem áudio).

## Critique do board (antes do render)
P0 = errado (texto ilegível, cobre o rosto, palavra errada, fonte na tela) · P1 = fraco (entra tarde, sai cedo,
compete com legenda, cor fora da marca) · P2 = polimento. Corrija P0/P1, no máximo 3 rodadas.
