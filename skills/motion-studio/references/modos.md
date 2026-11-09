# Modos de produção além do filme único e da campanha

## A. Motion sobre talking head (B-roll guiado por SRT)

> **Vídeo gravado de verdade (cortes, legendas, reenquadramento, B-roll, som) → use a skill edita-video.** Ela faz o
> mapa de motion ancorado nas palavras e chama ESTA skill para renderizar cada peça: `render.mjs pecas.html
> --query peca=mo03 --alpha` (ProRes 4444; a página recebe `?alpha=1` e não pinta fundo; o blur de movimento soma em
> alfa pré-multiplicado, sem franja preta) e lê `window.CUES` de cada peça para o som. `--fps 30000/1001` é aceito.
> Uma peça fora do catálogo vira um projeto desta skill (`new.sh`) referenciado no mapa como `"peca": "custom"`.
> O que segue abaixo é o caminho manual (só motion por cima de um vídeo pronto, sem editar).

Para quem grava vídeo de rosto (médico, advogado, consultor, o próprio Gabriel) e quer motion graphics que **acompanham o que a pessoa fala**.

1. **Transcrição com tempo**: `ffmpeg -i video.mp4 -ac 1 -ar 16000 audio/fala.wav` e rode faster-whisper com `word_timestamps=True` (o mesmo código do `voice.py`, passo 3) → `audio/words.json`. Para vídeos longos, SRT por frase basta.
2. **Decida por frase** (densidade 2–4, 4–7 ou mais inserções por minuto, combinada com o cliente):
   - **cutaway cheio** (3–10 s, a tela inteira vira motion; ≥ 2 s de rosto entre dois cutaways);
   - **painel transparente** por cima do rosto (render `--alpha` → ProRes 4444), ocupando o terço livre — **reserve o terço do rosto** (topo/lateral onde a cabeça está) e nunca cubra olhos/boca;
   - **nada** (a fala carrega sozinha).
3. Cada inserção é um `window.SHOTS` com `from/to` vindo do tempo das palavras; o que a pessoa diz aparece no frame em que ela diz (número, lista, nome de produto).
4. Texto mínimo: 1–4 palavras por inserção. O rosto é o herói.
5. Arquivos nomeados pelo ponto de entrada (`0m32s40_lista.mov`) + `compare.html` (antes/depois lado a lado) para o editor do cliente.
6. Quando o rosto precisa aparecer dentro do motion (moldura, recorte), use o vídeo como `<video>` com `currentTime = t` dentro do `seek`.

Texto atrás da pessoa (efeito "título atrás da cabeça"): exige máscara por frame (SAM 2, Apache 2.0, ~5 s/frame na CPU). Ofereça como extra.

## B. Explainer de dados (planilha → gráfico animado)

1. O dado vem do arquivo do cliente; cada número dito vira claim com fonte (regra dura 5).
2. **Confira a frase contra o dado**: se o roteiro diz "vazio às 8h" e a planilha mostra 6 bicicletas às 8h, escreva "quase vazio" e avise o cliente por quê. Nunca anime uma afirmação que os próprios dados contradizem.
3. O gráfico se desenha a partir de TODAS as linhas da planilha (não de uma amostra bonita); destaque alto/baixo; termine numa conclusão de uma frase.
4. Rótulo que contradiz o valor é o erro que o cliente mais pega: CHECK automático por barra (`window.CHECKS`).

## C. Estilo por referência (prints de um filme que o cliente ama)

O modelo não assiste vídeo: ele vê prints. Por isso:
- `bash scripts/ref.sh <arquivo|url>` → frames, duração dos planos, paleta, BPM. Mande **vários prints** (um por plano), não um.
- Escreva a **lista do que deixar de fora** (o que é marca registrada do filme de referência) antes de construir.
- A referência dá a gramática (ritmo, transições, composição); a marca do cliente dá a identidade.
- Melhor ainda que prints: um exemplo **em código** do estilo (um filme anterior aprovado, ou um template do estúdio). Com o código como base, até modelo menor fica consistente.

### C2. Medir a referência (não "parecido com": números)
Método do sub-level/marketing-videos (MIT):
1. Extraia **todos** os frames do trecho que importa (`ffmpeg -i ref.mp4 -vsync 0 refs/f/%05d.png`), não amostras.
2. Meça 4 coisas por bounding box de tinta (numpy/Pillow): **altura de caixa-alta ÷ altura do quadro** · **frame de chegada** de cada letra/elemento (diferença entre frames consecutivos) · **mecânica da saída** (bordas esquerda/direita da tinta por frame) · **holds** (sequências de bbox idêntica; referências enxutas seguram só 5–15 f).
3. Escreva a gramática em prosa, com números, antes do código. Monte a **tabela de casting** (batida da referência → função → seu conteúdo), na mesma ordem; corte a batida que não tem equivalente.
4. Guarde cada token com a medida no comentário (`// cap 0,057 — medido f0142`).
5. Compare lado a lado na mesma batida (`ffmpeg ... hstack`): tamanho, depois posição, depois peso. Se o seu corte dura o dobro do da referência, o problema são os holds.
6. Partículas: junte 3 frames com 1 s de intervalo nos canais R/G/B — rastros paralelos = você fez campo de estrelas, não poeira viva.

## D. Remake 1:1 (estudo de um filme)

Para aprender ou para o cliente aprovar uma direção: detecção de cortes (`ref.sh`), um subagente por grupo de planos + um para o áudio, split-screen comparando. Sem música, voz ou rosto da referência na entrega. Nunca publique o remake como peça do cliente.

## E. Página interativa a partir do filme

Como tudo é `seek(t)` puro, o mesmo filme vira landing com scroll: `t = progresso do scroll × DURATION`. Nada a reescrever.
