# Edit cinematográfico: carro, produto, evento, imóvel (sem fala)

Use quando o vídeo é feito de TAKES e FOTOS montados na música, sem ninguém falando: carro à venda, lançamento de
produto, aftermovie de evento, imóvel, bastidor. Motor: `scripts/montagem.py` (folhas → `_edit/montagem.json` →
render). Comando: `/edit-cinema`. Talking head continua no fluxo normal do edita-video.

**Regra nº 1 — foto não substitui take.** Edit de carro/produto é feito de VÍDEO (movimento real, reflexo andando,
roda girando, porta abrindo). Foto com zoom vira apresentação de slides e o cliente reprova. Só fotos? PARE antes de
montar e diga isso ao usuário; ofereça `/lista-de-planos` (o que gravar) ou um carrossel/motion com as fotos. Takes
grandes que o conector não traz (Drive baixa só até ~6 MB por arquivo): peça a pasta no computador ou o anexo — nunca
troque o material bom pelo que coube.

## As 4 referências estudadas (o que cada uma ensina)
| referência | receita | o que medir/copiar |
|---|---|---|
| [@h.vzls — 911 Turbo S no outono](https://www.instagram.com/p/DeMmOMFuJIK/) | **cinema-lento** | planos longos (~2 s) cortando nos tempos fortes; câmera lenta e contínua; o carro inteiro antes do detalhe; cor de outono (âmbar, sombras frias) |
| [@shotbykinetic — BMW M3 E92](https://www.instagram.com/p/DdGgrfNJiZ7/) | **vire-o-celular** | 16:9 girado 90° dentro do 9:16 (quem assiste deita o celular); grão de filme, creme nas luzes e azul-petróleo nas sombras; legenda de máquina de escrever; cartela preta antes da batida entrar; plano herói longo |
| [@loris.cataldo — restomod nos Alpes](https://www.instagram.com/p/Deo2Fc0KJbr/) | **ritual** | o ritual antes de sair (relógio, luva, câmbio, painel) em cortes de 0,5–0,8 s que ACELERAM; a estrada entra quando a batida cai; 16 s; cor alpina (fria, contida) |
| [@f1rstmotors — ASMR Ferrari 288 GTO](https://www.instagram.com/p/DfHwbPRMMqD/) | **asmr** | sem trilha: só o som real (passos, porta, chave, marcha lenta, acelerada) com o corte NO som; volta de detalhes de ~1 s; cor dourada; marca da loja no fim |

Mais uma receita da casa: **aftermovie** (evento) — a gramática do corte na batida aplicada a takes de evento:
estabelece (palco/fachada) → público → os carros/produto na queda da batida → pessoas → fecha no lugar.

## Gramática (o que o montagem.py faz e confere)
| regra | como |
|---|---|
| o corte cai na batida; momento grande no tempo forte | `dur` em batidas (`"2b"`) ou compassos (`"1c"`); o motor encaixa cada corte na batida mais próxima e lista os que ficaram fora em `docs/MONTAGEM.md` |
| ritmo conta a história | lento = 3–4 batidas por plano; crescendo = 2 → 1 batida; depois da queda, 2 batidas; o herói final dura 4 |
| uma ideia por plano | um detalhe, um ângulo, um gesto; nunca dois assuntos no mesmo plano |
| estabelece → detalhe → herói | primeiro o carro/lugar inteiro, depois os detalhes, termina no plano mais bonito |
| foto nunca fica parada | `mov`: push · pull · pan-e/pan-d · tilt-c/tilt-b · orbita · deriva (mínimo); `foco` = onde está o assunto (0–1) |
| câmera lenta só com material para isso | `vel`/`rampa` em take de 50–60 qps; em 30 qps o motor mistura quadros, mas não passe de 0,5× |
| transição tem motivo | `corte` (padrão) · `flash` na queda · `whip` entre ângulos do mesmo assunto · `zoom` para entrar em detalhe · `fade` só no lento · `preto` para abrir · `luz` (vazamento) no quente |
| respiro antes da queda | `cartelas`: tela preta com 3–5 palavras (máquina de escrever) logo antes do tempo forte |
| texto mínimo, sem fonte/crédito na tela | legenda curta (máquina de escrever, em minúsculas) ou título com espaçamento; fim com modelo + marca do cliente |
| som | trilha (gerada ou do cliente) + SFX só nas transições (whoosh no whip, impacto no flash e no fim, teclas na máquina de escrever); ASMR: `"musica": false` e `"som": true` nos takes |
| entrega | 9:16, −14 LUFS, pico ≤ −1 dBTP, folha `docs/folhas/montagem.jpg` aberta antes de mostrar |

## Receitas (ponto de partida do `_edit/montagem.json`)
| receita | trilha | planos | cor / acabamento |
|---|---|---|---|
| cinema-lento | piano 64–76 bpm, `intro:2,drop:4,outro:1` | 4b, 4b, depois 2b… e herói 4b; fusão só no começo e no fim | `showroom` (estúdio) ou `outono`; grão 0,02; halo 0,1 |
| ritual | cinematic 110–124 bpm, `intro:1,build:2,drop:4,outro:1` | 4b → 2b ×4 → 1b ×4 (crescendo) → `flash` na queda → 2b com `whip` | `alpino`; vinheta 0,3 |
| vire-o-celular | cinematic 84–96 bpm, `intro:2,drop:4,outro:1` | 4b com legenda → 2b → cartela 2b → `flash` → 2b ×6 → herói 4b | `"girado": true`, `"barras": 0.09`, `filme`, grão 0,035 |
| aftermovie | tech 120–128 bpm, `intro:1,build:1,drop:4,outro:1` | palco 4b com título → 2b, 1b, 1b → `flash` + rampa → 2b alternando carro/pessoas | `outono`; som do público baixo (−16 dB) |
| asmr | sem trilha | cada plano começa no som (porta, chave, ronco); 1–2 s; volta pelos detalhes | `dourado`; `"som": {"takes_db": 0}` |

## Material (diga ao cliente antes de gravar)
- Fotos de estúdio funcionam (o motor dá movimento de câmera), mas o melhor é vídeo: 4K 30 qps ou 1080p 60 qps
  (60 permite câmera lenta), 3–5 s por take, câmera andando devagar (gimbal ou estabilizador do celular).
- vire-o-celular: grave DEITADO (16:9). Os outros: em pé (9:16) ou deitado com folga para cortar.
- ASMR: celular perto da fonte do som, sem música ambiente, sem conversa; um take por som.
- Placa de carro de terceiros: enquadre fora (`foco`/`zoom`) ou desfoque. Pessoas em evento: só com autorização do
  evento/cliente. Logo do carro é o produto à venda; logo de outra marca, só com permissão.
- Não invente dado técnico, preço nem condição: só o que o cliente informou.

## Trilha
A gerada (`music.mjs`) é livre para uso. Trilha do cliente: `"musica": {"arquivo": "trilha.mp3", "inicio": 12}`
(o motor mede a grade com `beats.py`). Música comercial só se o cliente tiver licença; para Reels com música da
biblioteca do Instagram, entregue sem trilha e com o `beats.json` para o cliente escolher a música no app.
