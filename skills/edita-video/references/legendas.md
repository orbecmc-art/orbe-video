# Legendas queimadas — legíveis no celular, no ritmo da fala

`legendas.py` gera ASS (libass) a partir das palavras da timeline. Fonte: TTF em `fonts/` (`fontes.py` baixa a
família do estilo; kit do cliente tem prioridade).

## Números
| Item | Valor |
|---|---|
| Palavras por bloco | dinâmico/varejo 2 · base/educativo 3 · clínica/luxo 4 · "frase" 6 (2 linhas) — palavras curtas/funcionais não contam |
| Caracteres por bloco | 15 (dinâmico) · 18 · 22 (calmo) · 32 (frase) |
| Tamanho (em) | 6,6–7,6% do lado curto (71–82 px em 1080) · frase 5,4% · nunca < 4,4% (48 px) |
| Peso | 800–900 caixa alta · 600–700 frase |
| Contorno / sombra | 0,75% / 0,3% do lado curto (legível em qualquer fundo sem caixa) · ou caixa 60% opaca (`fundo: caixa`) |
| Posição | centro do bloco em y = 0,66 da altura (9:16) — dentro de 16–74%; acima da UI do Reels (base 22%) |
| Entrada | 2 quadros ANTES da voz · pop 82→104→100% em 140 ms (dinâmico) · fade 120 ms (calmo) |
| Saída | no início do próximo bloco (sem piscar em pausa < 0,6 s); senão fim da palavra + 0,25 s |
| Palavra ativa | cor `destaque` (amarelo #FFD43B, coral #FF5A4B, verde-água #9FE3E0…) SEM mudar tamanho |
| Ênfase | palavra de punch/ênfase em destaque o bloco inteiro e 8% maior |

## Quebra (programação dinâmica)
Barato quebrar: pontuação forte, vírgula, pausa > 0,25 s. Caro: terminar em palavra funcional ("de", "que", "o",
"pra") ou separar "Dr. Rafael", "30 dias", "duas horas". Proibido: atravessar corte de cena, pausa > 0,6 s ou entrada de
tela cheia/split (a legenda muda de lugar). Nunca juntar duas frases no mesmo bloco.

## Convivência com motion
- Peça sobreposta na faixa da legenda → a legenda sobe/desce para fora dela automaticamente.
- Split → legenda na emenda (y = 0,5). Tela cheia de motion com texto → legenda some (dois textos brigam).
- Peça que já diz a frase (CTA "comenta PELE") → `"esconde_legenda": true` no item.

## Correções sem mexer em tempo
`legendas.py . --corrigir "#18=três" "bril=brilho" "Rafel=Rafael"` (salvo em `_edit/correcoes.json`; vale para SRT
também). Nomes próprios: ponha em `termos` no briefing ANTES de transcrever.

## Entregáveis
Queimada no MP4 + `.srt` por frase (≤ 42 car/linha, 2 linhas) para a plataforma (acessibilidade e SEO).

## Serifa itálica (estilo dossiê)
`legendas.italico = true` + `fonte = "Instrument Serif"`, peso 400, sem cor de palavra ativa (destaque = cor): a
legenda fica discreta e as etiquetas carregam o soco. O `fontes.py` baixa o itálico sozinho.

## Layout cinematográfico (estilo minimal)
`legendas.layout = "cinema"` (+ `fonte2`, `escala_chave`, `peso_chave2`): bloco de até 5 palavras; a palavra-chave
(número > ênfase do mapa > termo do briefing > palavra longa/alongada no fim) fica 1,9× maior, no centro, em serifa
itálica (números em sans pesada); as outras, pequenas, nos vãos acima (o que vem antes) e abaixo (o que vem depois).
Cada palavra aparece quando é dita (fade 160 ms + leve subida da chave); halo escuro desfocado no lugar de contorno;
acento só na ênfase. A legenda some quando uma peça que já diz o texto está no ar (frase, aspas, linha, gráfico, CTA).


## Animações e destaques novos (v1.4)
- **`animacao: "monta"`** (podcast P&B): a frase se MONTA — cada palavra aparece quando é dita e fica até o bloco
  acabar. `chave_serifa: true` põe a palavra-chave em serifa itálica (fonte2) 18% maior; `halo: true` troca o contorno
  por uma borda suave desfocada (cinema, sem cara de Reels).
- **`animacao: "blur"`** (Joseph): o bloco entra com pop + desfoque + fade de baixa opacidade.
- **`chave_caixa: true`** (dinâmico/varejo, Style Studio): no máximo UMA palavra forte por bloco (número, ênfase, termo,
  palavra longa) numa caixa na cor de destaque, inclinada `chave_inclina` (−2,5°), texto em `chave_tinta`; a caixa salta
  quando a palavra é dita; no máximo 1 caixa a cada 2 s (nem toda linha precisa). A caixa é medida com a fonte real.
- **`faixa_desfoque: true`** (minimal): o terço da legenda escurece e desfoca de leve sob o texto (o texto respira sem caixa).
- Contraste: palavra direto sobre o vídeo → branco em roupa escura, tinta com borda em roupa clara; na dúvida, pílula.

## Micro e escada (v1.5)
- **`layout: "micro"`** (lifestyle): UMA palavra por vez, pequena (3% do lado), em serifa (EB Garamond), branca, sem caixa
  e sem destaque — quase decorativa; o protagonista é o rótulo creme. Junta palavra funcional, número + unidade e fala
  rápida (< 0,3 s) para nunca atrasar da voz. Fica no peito (`y` 0,68) e desvia das peças.
- **`layout: "escada"`** (entrevista): grotesca de tracking negativo (Inter Tight 500, `tracking` 2,5), pequena (4%),
  cada palavra entra com fade quando é dita; a palavra-chave do bloco fica GRANDE e o resto PEQUENO (`escala_pequena`
  0,62), deslocado — embaixo à direita se vem depois, em cima à esquerda se vem antes. Hierarquia sem cor nem caixa.
- **`desvia_rosto: true`** (lifestyle, entrevista; vale para qualquer estilo): mede o queixo no quadro final (rosto.py
  através da câmera) em cada bloco e desce a legenda para o peito quando o rosto está baixo — nunca texto na boca.
- Número curto ("38", "45") agora conta como palavra-chave (antes perdia para palavra longa) — vale para cinema e escada.
