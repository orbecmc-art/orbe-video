# Estilos e referências — de adjetivo para número

`assets/estilos.json` tem 10 presets sobre uma base (o **minimal premium** está em `estilo-minimal.md`; o **dossiê** em `estilo-dossie.md`; o **podcast P&B** abaixo). Cada preset também tem `ritmo`, `batidas` e `juncoes` (ritmo-e-batidas.md). Estilos treinados para um cliente ficam no kit dele (`estilos/<nome>/preset.json`, estudar_estilo.py) e herdam de um preset. O briefing escolhe o estilo e sobrescreve qualquer número em
`ajustes` (persistente no projeto). Kit do cliente pode trazer `ajustes` próprios (gosto aprovado).

| | dinâmico | clínica premium | educativo | luxo | varejo | minimal premium |
|---|---|---|---|---|---|---|
| pausa_max | 0,30 | 0,45 | 0,35 | 0,50 | 0,30 | 0,36 |
| legenda | 2 pal. CAIXA ALTA 900, pop, amarelo | 4 pal. frase 700, fade, verde-água | 3 pal. caixa alta, pop | 4 pal. frase 600, fade, champanhe | 2 pal. 900, coral | cinematográfica: chave grande em serifa itálica + pequenas em Inter |
| zoom alternado | 100↔114% | 100↔108% | 100↔110% | 100↔106% | 100↔114% | 100↔105% |
| punch | +7% / 3 s | +4,5% / 8 s | +6% / 4 s | não | +8% / 3 s | +3,5% / 9 s |
| motion/min | 4–7 | 2–3 | 4–6 | 1–3 | 4–7 | 4–7 (cenas de papel, linha, gráfico, aspas) |
| SFX | intenso (12/30 s) | discreto (5) | moderado (7) | discreto (4) | intenso (10) | discreto (6): papel, clique, marcador |
| trilha | tech, −19 LU | warm, −23 LU | minimal, −22 LU | cinematic, −17 LU | warm, −18 LU | piano, −20 LU |
| cor | punch | natural | natural | cinema | produto | fosco |
| LUFS | −14 | −16 | −14 | −14 | −14 | −14 |

## Pedidos → ajustes
| Cliente diz | Mude |
|---|---|
| "mais dinâmico" | pausa_max −0,05; punch_intervalo −1 s; legendas.palavras 2; motion por_minuto +2 |
| "mais calmo/elegante" | pausa_max +0,08; legenda fade, 4 palavras; punch 0; transição suave |
| "legenda maior" | legendas.tamanho +0,008 (até 0,082) |
| "legenda mais pra cima" | legendas.y 0,60 (nunca > 0,74 nem < 0,16) |
| "zoom demais" | camera.zoom_alterna [1.0, 1.06]; punch 0,04 |
| "música alta" | som.musica_db −3 |
| "efeito demais" | som.sfx discreto ou sfx_por_30s −3 |
| "cor mais quente" | cor.preset quente |
| "jornalístico", "dossiê", "fizemos a conta", "com dados" | `estilo=dossie` (etiquetas, faixa, grade, colagem; `estilo-dossie.md`) |
| "mais premium/clean/minimalista" | `estilo=minimal` (ou só `legendas.layout=cinema` + `cor.preset=fosco` + `broll.tratamento=papel`) |
| "delicado", "feminino", "lifestyle", "menos poluído", "só o essencial na tela" | `estilo=lifestyle` (ou só `legendas.layout=micro` + peças `rotulo` com `posicao: auto`) |
| "cara de entrevista/documentário", "autoridade", "sério", "cinema" | `estilo=entrevista` (ou só `legendas.layout=escada` + 2–4 `cartela` + `fim.fade_preto`) |
Grave em `_edit/briefing.json → ajustes` (ex.: `{"legendas": {"tamanho": 0.074}}`) e re-rode a etapa.

## Referência → números
`referencia.py . <link|arquivo>` mede cortes/min, plano médio, palavras/min, pausas p50/p90, loudness e paleta e
monta as folhas. **Abra as folhas** e preencha "O que eu vi". Traduza:
- plano médio < 2,5 s → dinâmico; 2,5–5 s → educativo/clínica; > 5 s → luxo.
- pausa p90 da referência → `cortes.pausa_max` (entre 0,2 e 0,5).
- legenda (palavras por bloco, caixa, cor da ativa, y) → `legendas.*`.
- paleta → `marca.accent` só se o cliente não tiver kit (a marca do cliente sempre vence a da referência).
- Inspire-se na gramática (ritmo, hierarquia, tipo de peça), nunca copie conteúdo, marca ou layout idêntico.


## Podcast P&B (`podcast-pb`)
Corte de podcast/conversa cinematográfico (referência: os cortes P&B de podcast que viralizam; vídeo do Rourke).
Preto e branco moody (`cor: pb`, pretos fundos) com grão de filme (`cor.grao`); legenda que se MONTA palavra a palavra até
formar a frase (`animacao: monta`), palavra-chave em serifa itálica (`chave_serifa`), halo em vez de contorno; palavras
grandes ATRÁS da cabeça nos picos (`"atras": true` numa peça `palavra`, motion-e-broll.md); quebra de padrão com reverb
em 1 virada; punch nas tônicas; trilha cinematic −22 dB; ritmo 2,5–3,5 s. Use em: podcast, entrevista, opinião forte,
bastidor de médico/advogado/empresário. Evite em: varejo, oferta.

## Lifestyle editorial (`lifestyle`)
Edição QUIETA e elegante (referência: reels de educadoras/mentoras de lifestyle). Gancho gigante que se empilha uma
palavra por linha no terço de cima (`empilha`, creme, sans média); legenda de uma palavra pequena em serifa (`micro`);
rótulos creme em dupla sans + manuscrita (`rotulo`, Great Vibes) no espaço livre — 2–4 s cada, depois somem; card de
documento como prova (`doc`); jump cuts com reenquadre sutil (100↔108%, sem punch); cor quente natural; voz quase
sozinha (trilha −30 dB) e SEM efeitos sonoros; 5–10 rótulos por minuto. Use em: educadoras, mentoras, estética, nutrição,
bem-estar, médicas com público feminino. Evite em: varejo, oferta, dados densos.

## Entrevista cinematográfica (`entrevista`)
Autoridade com cara de documentário (referência: entrevistas de luz lateral quente, fundo cinza). Legenda pequena em
escada (`escada`); CARTELAS de respiro (`cartela`) — tela lisa cinza claro ou quase preto com a fala escrita — em 2–4
frases-chave; 2 ângulos alternando (`zoom_alterna` 100↔120% + `alterna_x` 0,07: no fechado o rosto vai para um terço);
cor `cinema` com grão leve; cama de trilha grave contínua (−24 dB, ducking de 6 dB), acento só na volta da cartela;
fecha em fade para o preto (`fim.fade_preto` 1,2 s, legenda e trilha juntas). Use em: opinião, negócios, advogados,
consultores, médicos em tom de autoridade. Evite em: oferta, dica rápida de 15 s.

## O que o Style Studio (Synteq) ensinou e virou número aqui
- Ritmo medido por estilo + punch por linha/tônica/virada (camera.punch_modo) — ritmo-e-batidas.md.
- Batidas → peça → junção por estilo; junções fora da lista são recusadas.
- Palavra-chave em caixa inclinada (1 por bloco), slam, janela (pessoa em cartão), fio na borda do split.
- Cor de destaque em rodízio por vídeo (nunca a do último) quando a marca permite.
