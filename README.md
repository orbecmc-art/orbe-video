# Orbe Vídeo · Plugin (v1.6.0)

Duas skills que conversam + dez comandos:

| Skill | O que faz |
|---|---|
| `edita-video` | Edita vídeo GRAVADO: perguntas fixas (inclui referência) → transcrição por palavra → cortes (silêncio, vícios, falso começo, regravação) → mapa de motion/B-roll ancorado nas palavras → B-roll e fotos com licença → câmera virtual (9:16 no rosto, zoom alternado, punch-in) → legendas palavra a palavra → SFX por evento + trilha com ducking + voz limpa a −14 LUFS → QA medido (voz no mix, loudness, cliques, zonas da UI, sincronia) → MP4 + SRT + capa. **Multiplataforma:** kit aberto para Premiere, Final Cut, DaVinci, CapCut e celular; Claude ao vivo no editor (MCP); revisão do cliente no navegador. |
| `motion-studio` | Motion graphics do zero em código (seek(t) + Playwright + ffmpeg): springs, tipografia cinética, 2.5D, campanha, série com personagem, trilha/SFX com pico no quadro. Também renderiza as peças de motion da edição (ProRes com alfa). |

| Comando | Para quê |
|---|---|
| `/editar-video` | Edição completa, começando pelas perguntas fixas (com a galeria de estilos e o plano de cenas) |
| `/legendar` | Só legenda (com ou sem limpar pausas), MP4 + .srt |
| `/novo-motion` | Motion do zero com as perguntas de direção |
| `/exportar-video` | Leva a edição para Premiere, Final Cut, DaVinci, CapCut, celular ou para a página de revisão do cliente |
| `/atualizar-video` | Junta os aprendizados e as mudanças de plataforma e propõe a atualização das skills |
| `/variacoes` | Variações de teste de um vídeo editado (trial reels, criativos A/B) com hipótese, métrica e prévia lado a lado |
| `/treinar-estilo` | Estilo próprio a partir de uma pasta de referências: livro de regras, lookbook, preset e teste de fidelidade |
| `/documentario` | Documentário em plano-sequência sobre mapa/mesa real, voz guiando o tempo, tabela de batidas aprovada antes |
| `/lista-de-planos` | Decupagem para o cliente gravar sozinho: cada plano com ação, função, esquema do celular e dica; página para mandar |
| `/edit-cinema` | Edit cinematográfico sem fala (carro, produto, evento, imóvel): takes e fotos montados na batida, 5 receitas estudadas em referências |

## Regras fixas da Orbe (já embutidas)
- **Nenhuma fonte/crédito na tela** (sem tarja de fonte, rodapé "Fonte:", crédito de foto), salvo pedido explícito.
  Fontes e licenças vão para `docs/CREDITOS.md` / LEIA-ME e para a legenda do post quando a licença exigir.
- Todo vídeo editado tem motion e som desenhados (salvo pedido): gancho nos 2 s iniciais, mudança visual a cada ≤ 5 s,
  CTA no fim, cada efeito nascido de um evento visível, efeitos abaixo da voz.
- Licença clara ou não entra. Saúde: sem antes/depois, sem promessa, pessoa de banco nunca como paciente.
- Versões `_v01`, `_v02`… nunca sobrescrevem; brutos intocados. Áudio é medido, não ouvido (e o relatório diz isso).

## Edits de carro e cinema (1.6)
Quatro referências do Instagram analisadas (cortes, batidas e cor medidos): @h.vzls (911 no outono), @shotbykinetic
(M3 E92 girado), @loris.cataldo (ritual nos Alpes) e @f1rstmotors (ASMR 288 GTO). Na 3ª aba da galeria, cada
referência tem o link do Instagram e o botão "Usar este estilo" (copia `/edit-cinema receita …`), mais um aftermovie com
takes da Rivoli Concept. Regra: foto não substitui take — só fotos, o comando para e avisa.
- **Motor de montagem** (`montagem.py`): `takes` (folhas e tabela do material: qps, som, movimento) → `_edit/montagem.json`
  → render. Corte encaixado na batida medida (`"2b"`, `"1c"`), movimento de câmera em foto (push, pull, pan, tilt,
  órbita), câmera lenta e rampa com mistura de quadros, transições flash/whip/zoom/fade/preto/luz com SFX, 6 cores de
  cinema (showroom, outono, filme, alpino, dourado, noite), grão, vinheta, halo, faixas de cinema, cartela preta com
  máquina de escrever, fim com modelo + marca, "vire o celular" (16:9 girado), −14 LUFS medido.
- **Receitas** (`edit-cinema.md`): cinema lento, ritual de detalhes com crescendo, vire o celular, aftermovie e ASMR
  (só som real), com o que o cliente precisa gravar para cada uma.
- **/edit-cinema**: perguntas (receita, duração, trilha, texto) → folhas → montagem → rascunho → final.

## Lifestyle, entrevista e lista de planos (1.5)
Três referências do Instagram analisadas quadro a quadro (com o som medido): @daniirramoss (lifestyle), @nicomonteiroo
(entrevista) e @bryanhynes ("how to film yourself").
- **Estilo Lifestyle** (`lifestyle`): edição quieta — gancho gigante que se empilha uma palavra por linha (`empilha`),
  legenda de UMA palavra pequena em serifa (`micro`), rótulos creme em sans + manuscrita (`rotulo`), card de documento
  como prova (`doc`), sem efeitos sonoros.
- **Estilo Entrevista** (`entrevista`): legenda pequena em escada (chave grande, resto pequeno deslocado), CARTELAS de
  respiro (tela lisa com a fala escrita, `cartela`), 2 ângulos alternando, cama grave contínua, fim em fade para o preto.
- **Espaço livre** (`"posicao": "auto"`): a peça vai para onde não há rosto (acima da cabeça ou no peito), medido no
  quadro final; a legenda desvia sozinha.
- **/lista-de-planos** (`planos.py`, `decupagem.md`): o que gravar, de onde e para quê — 17 tipos de plano, 7 contextos,
  gramática validada (estabelece, 2 ângulos por ação, detalhe e reação) e página com esquema do celular por plano.

## Ritmo medido, documentário, variações de teste e estilo treinado (1.4)
Estudo de 9 vídeos (Joseph, Zane Hoyer, LABS, Stockton Walbeck, Grow with Alex, Mateus Dias, Rourke, Enrique Marq) + o
prompt "continuous flowing" + o Style Studio (videoeditskill.synteq.app — método, não código).
- **Ritmo, batidas e junções por estilo** (`ritmo.py`): cada frase vira uma batida (gancho, virada, item, número,
  ponto, prova, fim) e o estilo diz que peça a carrega e com que junção entra; algo muda na tela a cada X s (medido por
  estilo), nunca parado além do limite, fim curto, junções fora do estilo recusadas, slam no máx. 2. Punch por linha de
  legenda (dinâmico/varejo, vai-e-volta), nas tônicas ou só nas viradas. Cor de destaque em rodízio por vídeo.
- **Peças novas**: slam (número que cai, antigo riscado), notificação de app, anel contador, pílula, capítulos em losango
  (e a etiqueta do capítulo citado). **Layout janela** (a pessoa vira cartão e a câmera recua — o "zoom para fora"),
  **split com fio** na cor de destaque, **quebra de padrão** (close no nariz, P&B, reverb, trilha abafada) e **P&B → cor**.
- **Legendas**: monta (a frase se forma palavra a palavra), entrada com desfoque, palavra-chave em caixa inclinada (medida
  com a fonte real), faixa desfocada sob a legenda.
- **Estilo podcast P&B** (grão, legenda que se monta, serifa itálica na chave, palavras atrás da cabeça) — na galeria.
- **Notas faladas**: "abre nota … fecha nota" gravado no vídeo sai do corte e vira direção da edição.
- **Variações de teste** (`variacoes.py`, `/variacoes`): direto, micro, abertura, mudo, P&B → cor — hipótese, métrica,
  prévia lado a lado com o master e a regra do vencedor.
- **Formatos repetíveis** (`formato.py`), **cortes de vídeo longo** (`momentos.py`), **estilo treinado em referências**
  (`estudar_estilo.py`, `/treinar-estilo`: livro de regras, lookbook, tiras das animações, preset e teste de fidelidade).
- **Documentário contínuo** (motion-studio, `/documentario`): um plano-sequência sobre um mapa real (Natural Earth),
  papéis que caem, ano gigante, rota, círculo e carimbo na palavra; voz primeiro (Piper ou gravada), tabela de batidas
  para aprovar, câmera que nunca para nem dá tranco (checada), motion blur adaptativo. Demo: "Goiânia, a capital planejada".

## Galeria no plugin, vitrine e estilo dossiê (1.3)
- **A galeria vai junto**: pasta `galeria/` (página + vídeos + `gerar.py`). O link de `galeria.json` é da conta da Orbe
  (privado até ser compartilhado); quem instalar o plugin publica a própria cópia a partir da pasta.
- **Vitrine** (`edita-video/scripts/vitrine.py`): o MESMO vídeo editado em todos os estilos, com mapa próprio por
  estilo, som e o bruto ao lado. Na galeria: botão Ouvir, Comparar lado a lado e o que muda em cada estilo. Serve para
  o cliente escolher o estilo vendo o vídeo DELE.
- **Estilo Dossiê** (`estilo=dossie`, gramática do @odossie.br e do filme "A conta"): tarjas pretas e etiquetas amarelas
  de papel rasgado, faixa vermelha, a conta em quadradinhos, colagem com fotos (inclusive quadros do próprio vídeo),
  manchete circulada, cartão cinza, papelão/papel com persiana, cor documental, legenda em serifa itálica.
- **Motion "Dossiê de dados"**: o filme "A conta" vira ficha + projeto de partida no motion-studio.

## Estilos com exemplos, minimal premium e plano de cenas (1.2)
- **Galeria de estilos** (página publicada; link em `galeria.json`): um vídeo real de cada estilo de edição (minimal
  premium, dinâmico, clínica premium, educativo, luxo, varejo) e 22 de motion. "Usar este estilo" copia o pedido.
  A pergunta de estilo do `/editar-video` e do `/novo-motion` leva esse link.
- **Minimal premium** (`estilo=minimal`, o "look Arthur Brooks"): legenda cinematográfica de 2 tamanhos (Inter +
  Playfair itálica, a palavra-chave grande), cor fosca, B-roll e pintura com papel e borda suave, câmera que desliza,
  e peças novas: `frase`, `aspas`, `linha`, `grafico`, `capitulos`, `callout`; "legenda + UI" com fundo que escurece.
  Som em 3 famílias (movimento · texturas · antecipação) com `paper` e `marker`, piano a −20 dB.
- **Página de plano** (`plano.py`): o roteiro cortado linha a linha com a sugestão do Claude; a pessoa escolhe
  Legenda · Legenda + UI · Meia tela · Tela cheia, o design e uma nota, salva e aprova; `plano.py . aplicar` leva
  para o mapa. "Copiar plano" funciona sem conta.
- **Perícia de movimento** (`pericia_movimento.py`): amplitude, quase-parada e picos do nosso vídeo × referência —
  o `final.py` roda quando o projeto tem referência.
- **motion-studio**: 22 estilos com ficha pronta (`estilos/<id>/ESTILO.md`, metas de movimento medidas) e o código
  da peça, que o render já lê (ponte GSAP/HyperFrames no `pw.mjs`); regras dos estúdios 2026 em
  `references/galeria.md`.

## Edite onde quiser (1.1)
| Onde | O que recebe | Como entra |
|---|---|---|
| Claude (padrão) | MP4 final + SRT + capa | pronto |
| Premiere Pro | `premiere/<nome>.xml` (FCP7) e `.otio` + kit | Arquivo › Importar · ou o Claude importa ao vivo pelo Edit Link / premiere-pro-mcp |
| Final Cut Pro | `finalcut/<nome>.fcpxml` 1.10 (validado na DTD da Apple) | Arquivo › Importar › XML · ou `open -a "Final Cut Pro"` com o Mac ligado |
| DaVinci Resolve | `.otio` · `.fcpxml` · `.xml` · `.edl` | Importar › Linha do tempo · ou MCP nativo do Resolve 21.1 Studio |
| CapCut desktop | rascunho (experimental) + roteiro de montagem | pasta de rascunhos do CapCut |
| Celular (Edits, CapCut mobile) | final, versão sem legenda, SRT | importar no app |
| Navegador | página de revisão com linha do tempo numerada | cliente pede por número e aprova; o Claude aplica |

O kit leva tudo no tamanho final (nenhum editor reenquadra): trechos com câmera e cor gravadas e alça de 1 s,
coberturas prontas (+ originais), motion e legendas com transparência, SRT editável, stems de voz/trilha/efeitos,
LUT do look, guias de zona do Reels/TikTok/Shorts e o render de referência. Marcadores com os mesmos números
(s003, br01, mo04, L012, sfx07) em todos os programas.

Recomendado: Premiere com **Edit Link** (já instalado na Orbe) ou `premiere-pro-mcp` do npm (cuidado com cópias no
GitHub); DaVinci **Studio 21.1** para controle nativo. O primeiro uso real em cada programa deve ser conferido
(importação testada por validação de formato, não dentro dos apps).

## Instalação
- **Claude / Cowork:** aceite o arquivo `.plugin` (botão na conversa).
- **Claude Code:** copie a pasta `orbe-video/` para o diretório de plugins, ou cada pasta de `skills/` para
  `~/.claude/skills/` (mantenha `edita-video` e `motion-studio` lado a lado — a edição acha o motion pela pasta irmã,
  ou defina `MOTION_STUDIO=<pasta>`).
- Se você já tem a skill `motion-studio` avulsa instalada, desinstale-a: a deste plugin é a v5 com a ponte e a regra
  de fontes.

## Requisitos (o `novo.sh` confere tudo e diz o que falta)
ffmpeg com libass · Python 3.10+ com `numpy opencv-python-headless faster-whisper pillow scipy fonttools brotli` ·
Node 20+ com Playwright (Chromium). Opcionais: `mediapipe` (texto atrás da pessoa), `opentimelineio` (kit .otio),
`pycapcut pymediainfo` (rascunho CapCut). Modelos pequenos (rosto YuNet, ruído RNNoise) e fontes das legendas são baixados
uma vez em `~/.cache/edita-video`.

## Chaves grátis recomendadas (B-roll e fotos muito melhores)
Crie e ponha no `~/.config/orbe/.env` (nunca no chat):
```
PEXELS_API_KEY=...      # pexels.com/api — grátis, vídeo e foto, sem atribuição obrigatória
PIXABAY_API_KEY=...     # pixabay.com/api/docs — grátis, vídeo e foto
```
Sem as chaves a busca usa Openverse e Wikimedia Commons (só licenças comerciais; resultados mais fracos).
Efeitos sonoros gravados (soam melhores que os sintetizados): uma pasta com WAVs nomeados pelo tipo
(`whoosh_01.wav`, `pop_soft.wav`, `swish_02.wav`, `ding_01.wav`, `impact_01.wav`…) e `ORBE_SFX_LIB=<pasta>` no `.env`.

## Onde ficam as coisas
- Projetos de edição: `estudio/edicoes/<data>-<cliente>-<nome>/` (brutos, docs, renders, _edit).
- Kit de cada cliente: `estudio/brands/<cliente>/` — `BRAND.md`, `marca.json` (cores/fontes), `fonts/`,
  `PERFIL_EDICAO.md` (gosto aprovado, lido antes de cada vídeo dele).
- Aprendizados de ofício (valem para todos): `~/.config/orbe/edita-video/APRENDIZADOS.md` → `/atualizar-video`.

## Manutenção
`/atualizar-video` junta os aprendizados das entregas e checa mudanças de plataforma, licenças e ferramentas;
propõe diffs; aprovado, sobe a versão e reempacota. Cadência sugerida: a cada 5 vídeos entregues ou mensal.

## Changelog
- **1.6.0 (08/11/2026):** edits de carro e cinema — motor `montagem.py` (takes/fotos na batida, câmera em foto, rampa,
  transições com SFX, 6 cores de cinema, girado 16:9, cartela de máquina de escrever), `references/edit-cinema.md` com
  as 4 referências e 5 receitas, comando /edit-cinema e 3ª aba na galeria ("Edits de carro e cinema"): as 4
  referências com link e "Usar este estilo" + aftermovie com takes da Rivoli Concept; sem vídeo (só fotos) o comando para e avisa.
- **1.5.0 (08/11/2026):** estilos lifestyle e entrevista (galeria com 11 edições), peças empilha, rotulo (creme e técnico),
  doc e cartela, legendas micro e escada, posição automática no espaço livre, 2º ângulo na câmera, fim em fade para o preto,
  comando /lista-de-planos com página para o cliente; descrição do plugin dentro do limite de 500 caracteres do app.
- **1.4.0 (07/11/2026):** ritmo/batidas/junções por estilo (`ritmo.py`), punch por linha/tônica/virada, peças slam,
  notificação, anel, pílula e capítulos em losango, layout janela com recuo, split com fio, quebra de padrão e P&B → cor,
  legendas monta/blur/caixa da palavra-chave/faixa desfocada, estilo podcast P&B, notas faladas, variações de teste,
  formatos repetíveis, cortes de vídeo longo, estilo treinado em referências, estilo documentário contínuo no
  motion-studio e três comandos novos (/variacoes, /treinar-estilo, /documentario). Estilos próprios no kit do cliente.
  Contador de número inteiro pequeno ("R$ 1 milhão") entra pronto em vez de passar por "R$ 0".
- **1.3.1 (06/11/2026):** corrige o erro de upload/instalação — o cabeçalho da skill edita-video tinha dois-pontos fora de aspas (YAML inválido para o validador do app); todas as descrições agora vão entre aspas e dentro do limite de 1.024 caracteres.
- **1.3.0 (06/11/2026):** galeria dentro do plugin (pasta `galeria/`), refeita com um vídeo real da Orbe editado em 8
  versões (bruto + 7 estilos), som, comparação lado a lado e ficha "o que muda"; `vitrine.py`; estilo de edição
  **dossiê** (6 peças novas: etiqueta, faixa, grade, colagem, recorte, cartão cinza; fotos por `quadros` do próprio
  vídeo; cor `documental`; legenda itálica); estilo de motion **dossiê de dados** ("A conta"); ajustes do minimal
  (linha, gráfico, legenda maior).
- **1.2.0 (06/11/2026):** galeria de estilos com vídeos (edição + motion), estilo **minimal premium** (legenda
  cinematográfica, cor `fosco`, tratamento `papel`, transição `deslize`, fundo `escurece`, 6 peças novas, SFX
  `paper`/`marker`), **página de plano** de cenas (`plano.py`), perícia de movimento × referência, 21 estilos de
  motion da biblioteca claude-video (Felipe Borges, MIT — `LICENCAS-TERCEIROS.md`) + série com personagem, pergunta
  do plano no `/editar-video`, estilo antes de tudo no `/novo-motion`.
- **1.1.0 (05/11/2026):** multiplataforma. `nle.py` (kit aberto + linhas do tempo para Premiere, Final Cut,
  DaVinci, CapCut e celular, legendas com alfa por difference matting, LUT 33³ do look, guias de zona),
  `revisao.py` + `pedidos.py` (página de revisão no navegador com pedidos por número e aprovação),
  `/exportar-video`, `references/multiplataforma.md` (MCPs ao vivo: Edit Link, premiere-pro-mcp, Resolve 21.1,
  fcp-mcp-server; CapCut sem API). Novos recursos de edição: texto atrás da pessoa (`"atras": true`, MediaPipe),
  J-cut opcional (`cortes.jcut`), correção automática de cor medida, cadeia de voz com RNNoise/de-esser,
  render parcial com legenda alinhada, SRT sem sobreposição.
- **1.0.0 (05/11/2026):** primeira versão. `edita-video` nova (fluxo de 8 etapas do LeiteZ com 4 portões, perguntas
  fixas com referência, 20 scripts). `motion-studio` v5 + ponte com a edição (`--query`, `--alpha` com fundo
  transparente e blur pré-multiplicado, fps 30000/1001) e regra "sem fonte na tela".
