# Documentário contínuo — um plano-sequência sobre um mundo só

Referência: o "documentário nível Netflix feito pelo Claude" (Zane Hoyer) e o prompt de direção que o Gabriel guardou
(docs/PROMPTS.md). Serve para história, linha do tempo, "como nasceu", caso de cliente contado como documentário, origem
de uma marca/cidade/empresa, explicação de mercado com lugar e data. Tudo desenhado em código: sem gerador de vídeo de IA,
sem banco de imagem — fotos e documentos REAIS entram como objetos no mundo.

## A gramática
- **Um mundo só**: mapa (contornos reais), mesa, quadro de cortiça. Nada corta, nenhum slide troca: a câmera desliza,
  aproxima nos detalhes, recua para viajar e mergulha de novo.
- **Câmera filmada**: toda partida e chegada com ease; na espera ela NUNCA para — deriva devagar (≥ 24 px/s) na direção
  em que vai sair e empurra 3,5% de zoom; viagem com velocidade contínua (Hermite); recuo de zoom em viagem longa com
  sen² (sem tranco); handheld sutil; motion blur adaptativo à velocidade (SUB_AT); grão, brilho e vinheta.
- **Objetos físicos**: documento (título datilografado, um campo grande, corpo em linhas cinza), recorte de jornal (borda
  rasgada, cabeçalho, manchete), planta/blueprint (o traçado se desenha), cidade (ponto + rótulo mono espaçado), estado
  aceso, rota tracejada com ponto viajando, número grande + carimbo. Caem na mesa com mola e sombra que encolhe.
- **Tela**: ano gigante em serifa espaçada com fios vermelhos (herói de virada de época), título final, régua do tempo no
  rodapé com o ano marcando.

## As regras (as mais importantes — vêm do prompt)
1. **Uma ideia por fala → UM herói** (objeto, ano ou título). Todo o resto escurece.
2. **Cada frase aparece UMA vez**: ou num documento real, ou digitada — nunca as duas (rótulo de mapa não conta).
3. **Sem texto de enchimento**: corpo de documento = linhas cinza, não palavras que a pessoa tenta ler.
4. **Tipo grande**: herói muito grande, rótulo nunca miúdo — se não lê no celular em 1 s, está pequeno ou tem coisa demais.
5. **Menos é mais**: nada de fita, carimbo, memo ou etiqueta decorativa que não seja parte da história.
6. **O gesto cai na palavra**: o círculo se desenha quando a palavra é dita; o carimbo bate na batida.

## Processo (não pule)
1. Roteiro em `roteiro.json` (falas + objetos) → `python3 scripts/narrar.py` (voz primeiro: gravada > Piper pt-BR).
2. `python3 scripts/tabela.py` → **docs/BATIDAS.md**: tempo → narração → o herói → texto na tela → gesto. MOSTRE ao
   usuário e pergunte o que estiver vago ANTES de animar. Peça a lista do que falta (fotos reais, documentos) e use o
   material real — é isso que tira a cara de "PowerPoint".
3. Stills de cada batida + `VALIDATE()` na página: câmera parada, tranco, herói duplo, texto repetido, tipo pequeno.
4. Render (`render.mjs`, motion blur adaptativo) → SFX dos `CUES` (papel na queda, caneta no círculo, impacto no
   carimbo, boom no ano, whoosh nas viagens) → trilha (piano/drone, −16 dB sob a voz) → `mix.sh` em −14 LUFS.
Feedback que funciona: "está rápido demais, não dá pra ler" → segure mais cada herói; "frase aparece em vários lugares" →
corte a repetição; "parece PowerPoint" → material real e câmera contínua.

## Formatos
9:16 (Reels/TikTok, padrão), 16:9 e 21:9 (3840×1646, cinema) — troque `formato` no roteiro; a duração é a da voz.

## Licenças
Mapa: Natural Earth (domínio público) via world-atlas (ISC) e estados via datamaps (MIT). Fontes: Cormorant Garamond,
IBM Plex Mono, Courier Prime, Inter Tight (OFL, via @fontsource). Fotos de pessoas reais: só do cliente ou com licença —
nunca baixar foto de pessoa pública da web para pôr no vídeo. Documento/notícia: só reais (nunca inventar manchete).
