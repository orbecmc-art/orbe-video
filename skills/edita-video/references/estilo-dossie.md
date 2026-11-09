# Estilo dossiê ("fizemos a conta")

Gramática do perfil @odossie.br (referência: https://vt.tiktok.com/ZSpM7xHKF/) e do filme "A conta" da Orbe
(motion-studio, estilo `dossie-de-dados`). Jornalístico e investigativo: a fala de quem aparece é provada na mesa de
trabalho — papelão, papel com sombra de persiana, tarjas, etiquetas, fotos com fita, números que batem.
Serve para dados, mercado, denúncia/opinião, "a conta que ninguém fez", resultado de cliente, educação financeira.
Preset: `estilo=dossie` (assets/estilos.json, look de motion `dossie`).

## As peças (pecas.html, look dossiê)
| Peça | O que é | Params |
|---|---|---|
| `etiqueta` | tarjas pretas + etiquetas amarelas de papel rasgado empilhadas ("QUASE MIL / VÍTIMAS"; "Nº 1 / 300 / DEMISSÕES DIRETAS") — sobre o rosto, o B-roll ou o papel | `linhas: [{txt, tipo: pre|ama|num|ser|ver}]`, `alinha` |
| `numero` | vira etiqueta: número grande em amarelo + rótulo em tarja | `valor`, `prefixo`, `sufixo`, `rotulo` |
| `faixa` | palavra gigante em faixa vermelha + faixa branca que batem dos lados ("VAI FECHAR / UMA FÁBRICA") | `linhas: [2]`, `foto` opcional |
| `grade` | a conta em quadradinhos amarelos marcados um a um no caderno; número em etiqueta, nota à mão | `total`, `colunas`, `marcados`, `rotulo`, `nota` |
| `colagem` | título em tarja, fotos com fita que batem na mesa, etiquetas nelas | `titulo`, `fotos: []` ou `quadros: [s]` (quadros do próprio vídeo), `etiquetas` |
| `recorte` | manchete em serifa no papel; caneta vermelha circula a palavra | `manchete`, `circula`, `sub` — **só manchete REAL** com fonte guardada (nunca inventar notícia) |
| `aspas`/`frase` | cartão cinza com vinheta: serifa itálica pequena + etiqueta amarela ("o que a economia faz com o seu emprego / SEGUE O DOSSIÊ") | `antes`, `chave`, `depois` |
| `titulo`, `palavra`, `cta` | viram pilhas de etiquetas na mesma gramática | os de sempre |
Fundo das telas cheias: `fundo: kraft | papel | cinza | escuro` (texturas geradas em código, `assets/motion/dossie/`),
sempre com persiana em diagonal deslizando e grão.

## Como montar
- **Abre no rosto** com a pergunta/contexto numa tarja preta e o número/gancho numa etiqueta amarela (topo).
- Cada número dito vira **etiqueta** no momento da palavra; dado que precisa de prova vira **grade** ou **recorte**.
- Lista de motivos/fatores = **colagem** (fotos com fita + etiquetas que entram uma a uma, como "3 FATORES").
- Frase de impacto/ordem = **faixa** (no máximo 1–2 por vídeo). Fecho = **cartão cinza** com a chamada.
- Ritmo: algo novo a cada 2–4 s; cenas de papel ≤ 4 s; ≥ 1,2 s de rosto entre telas cheias.
- Legenda: serifa itálica pequena (Instrument Serif), branca com halo, sem cor de palavra ativa — o destaque é das etiquetas.
- Cor `documental` (contraste firme, saturação contida); B-roll com `tratamento: papel`.
- Som: papel batendo (`paper`/`thump`), marcador na grade/caneta (`marker`), piano em notas soltas a −21 dB.

## Regras
- Número na tela = número dito e verificável (fonte no LEIA-ME/legenda do post; na tela só se pedirem).
- Pessoa real em foto/vídeo de terceiros: só com licença e sem sugerir o que ela não disse. Saúde: sem antes/depois.
- O estilo é a gramática, não o conteúdo do @odossie.br: nunca copiar texto, marca ou peça deles.
