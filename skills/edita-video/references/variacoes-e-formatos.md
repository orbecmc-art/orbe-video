# Variações de teste, formatos repetíveis, cortes de vídeo longo e estilo treinado

## Variações de teste (trial reels / criativos A-B) — `variacoes.py`
O Instagram e o Meta Ads reconhecem repost: zoom de 1,02, espelhar ou trocar uma linha não passa. Cada variação muda
**abertura, gráficos ou estrutura** e testa **uma hipótese com uma métrica** (método Grow with Alex):
| receita | muda | testa | métrica |
|---|---|---|---|
| direto | corta o setup (payoff mais cedo) | pular o setup segura mais? | skip rate (3 s) |
| micro | só as linhas da demonstração + manchete nova, fim que emenda no começo | demo sozinha rende mais replay? | tempo médio + envios |
| abertura | peça e texto novos nos 2,5 s iniciais, punch diferente | abertura nova segura mais? | skip rate |
| mudo | gancho escrito grande nos 3 s iniciais, legenda 15% maior | quem vê sem som fica? | skip + % assistido |
| pb-cor | abre em P&B, a cor escorre na 1ª virada | o gancho visual segura? | skip + tempo médio |
`python3 variacoes.py <projeto> --receitas direto,abertura,mudo,pb-cor --gancho "R$ 1 milhão por ano"` → um projeto
irmão por receita, render completo com QA, **prévia lado a lado com o master (≤ 10 s)** e o cartão de teste
(docs/VARIACOES.md). Regras: no máximo 5 trial reels por dia; compare trial com trial; vencedor só com ≥ 5 pontos de
skip rate ou 1,5× por mil; empurre o vencedor em 48 h; registre o aprendizado no perfil do cliente. Anúncio: mesmo
conjunto, orçamento igual, mesma janela.

## Formatos repetíveis — `formato.py`
A edição que deu certo vira molde: `formato.py . salvar convite-b2b --nota "slam no número, janela no CTA"` guarda
estilo, ajustes e a sequência de batidas (peça, modo, junção, posição, forma, em que fração do vídeo). No vídeo novo:
`formato.py . usar convite-b2b` → briefing ajustado + docs/FORMATO.md para montar o mapa em cima da transcrição nova.
Fica no kit do cliente (`formatos/`) ou em ~/.config/orbe/formatos.

## Cortes de vídeo longo — `momentos.py`
Podcast, live, aula, entrevista: `momentos.py . --min 20 --max 60 --n 10` lista os melhores trechos (começa e termina em
frase inteira; pontua gancho, autonomia, fecho, números, fala viva, poucas hesitações) em docs/MOMENTOS.md. O Claude lê,
propõe 3–5, o usuário aprova, `momentos.py . extrair 1,3,4` cria um projeto por corte já cortado. Nunca tirar frase do
contexto para mudar o sentido do que a pessoa disse.

## Estilo treinado em referências — `estudar_estilo.py`
Pasta com as melhores edições (do cliente, da Orbe ou que o cliente admira) → `estudar_estilo.py <pasta> --nome
estilo-cliente --base minimal --kit <kit>` mede cortes/min, plano, mudança na tela, trecho parado, rosto, linha dos
olhos, paleta, saturação e acha os trechos animados (tiras de 6 quadros). Monta o pacote: REGRAS.md (números + as 5
chaves para preencher olhando: legenda, capítulos/listas, pops e contadores, gancho, telas cheias), LOOKBOOK.jpg,
ANIMACOES.md e preset.json (herda do --base). Antes de usar em cliente: **teste de fidelidade** — recriar 5–10 s da
referência e comparar lado a lado. O edita-video acha o estilo pelo nome (`estilo=estilo-cliente`).
Referência ensina gramática; nunca copiar texto, marca ou peça de alguém.
