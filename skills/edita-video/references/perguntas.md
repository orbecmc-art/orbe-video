# Perguntas fixas — antes de editar QUALQUER vídeo

> Regra: o resultado é decidido antes do primeiro corte. Toda edição começa por esta sequência, **sempre na mesma
> ordem**. Pule só o que o pedido já respondeu (diga "entendi X" em vez de perguntar). A pergunta de REFERÊNCIA nunca é
> pulada: muita gente esquece de mandar o link.

## Como perguntar (2 rodadas + 1 texto)

Use `AskUserQuestion` (até 4 perguntas por chamada). Opção recomendada primeiro, com "(Recomendado)".
Sem ninguém respondendo (tarefa agendada, pessoa ausente): use os padrões da última coluna, escreva no topo do
BRIEFING "assumi: …" e siga.

### Rodada 1 — o vídeo

| # | Pergunta | Opções | Por que é decisiva | Padrão |
|---|---|---|---|---|
| 1 | **Onde vai ser postado?** | Reels/TikTok/Shorts (9:16) · Feed (4:5) · YouTube (16:9) · Vários formatos | Decide enquadramento, zonas seguras, tamanho de legenda e duração | 9:16 |
| 2 | **Quanto tempo no final?** | Até 30 s · 30–60 s · 60–90 s · Livre (só tira o que é ruim) | Decide se é limpeza ou CONDENSAÇÃO (escolher trechos) — muda o corte inteiro | Livre |
| 3 | **Qual estilo de edição?** (com o link da **galeria de estilos** na pergunta) | Minimal premium (papel, serifa, linha azul) · Dossiê (tarjas, etiquetas, "fizemos a conta") · Dinâmico (retenção) · Podcast P&B (cinematográfico) · Lifestyle (quieto, rótulos creme) · Entrevista (cartelas, autoridade) · Clínica premium (sóbrio) · Educativo (cards e números) · Luxo (lento, elegante) · Varejo/oferta · estilo treinado do cliente (kit) · formato salvo | Puxa ~40 números de uma vez (pausa, zoom, legenda, cenas, SFX, cor) | pelo nicho do cliente |
| 4 | **Tem vídeo de REFERÊNCIA?** | Sim, vou mandar o link/arquivo · Use a referência do kit do cliente · Não, siga o estilo | A referência vira números (cortes/min, pausa, legenda, paleta) — o "parece com isso" | Não |

Se "Sim": peça o link na hora ("cola aqui o link ou anexa o arquivo") e rode `referencia.py`. Instagram/TikTok com
login → peça o arquivo.

**Galeria de estilos**: o link está em `galeria.json` (`url`) na raiz do plugin — o mesmo vídeo bruto editado em cada
estilo (com som, o bruto e comparação lado a lado) e os estilos de motion; a pessoa aperta "Usar este estilo" e cola o
pedido. Ponha o link no texto da pergunta 3. O link é privado da conta da Orbe: para outra pessoa, compartilhe a página
ou publique a cópia da pasta `galeria/` do plugin. **Cliente indeciso**: `vitrine.py` faz a vitrine com o vídeo DELE.
`AskUserQuestion` aceita 4 opções: mostre as 3 que mais servem ao nicho + "Minimal premium" (a recomendada para
educativo de alto valor: médico, advogado, mentor) ou "Dossiê" (dados, mercado, resultado, opinião); o "Outro" cobre
o resto. Saúde → Clínica premium ou Minimal. **Sem fala** (carro, produto, evento, imóvel: só takes e fotos) não passa
por estas perguntas: é `/edit-cinema` (aba "Edits de carro e cinema" da galeria, `#cinema` no link).

### Rodada 2 — as camadas

| # | Pergunta | Opções | Padrão |
|---|---|---|---|
| 5 | **Legendas?** | Palavra a palavra com destaque (Recomendado p/ Reels) · Frase (2 linhas, sóbria) · Sem legenda | palavra |
| 6 | **Motion graphics?** | Bastante (títulos, números, listas, CTA) · Pontual (gancho, números, CTA) · Só abertura e CTA · Sem motion | pelo estilo |
| 7 | **Imagens de apoio (B-roll)?** | Buscar na internet (bancos gratuitos com licença) · Só o meu material · Os dois · Nenhuma | os dois |
| 8 | **Som?** | Trilha + efeitos sonoros · Só trilha · Só efeitos · Só a voz | trilha + efeitos |

### Rodada 2b — o plano (uma pergunta)

| # | Pergunta | Opções | Padrão |
|---|---|---|---|
| 8b | **Como decidir as cenas?** | Eu aprovo o plano numa página, linha a linha (Recomendado p/ premium) · O Claude decide e eu reviso no vídeo · Só me mostre o mapa no chat | página para minimal/cliente exigente; Claude decide em dinâmico rápido |

A página de plano (`plano.py`) mostra o roteiro já cortado com a sugestão do Claude por linha (Legenda · Legenda + UI ·
Meia tela · Tela cheia + design + nota). É o passo que mais muda o resultado — references/estilo-minimal.md.

### Rodada 3 — texto livre (uma mensagem)

9. **Cliente / marca** — qual kit (`estudio/brands/<cliente>`) ou cores/fonte/logo? (sem kit: neutro do estilo)
10. **CTA** — o que a pessoa deve fazer no fim? ("comenta X", "agenda no link", "chama no WhatsApp")
11. **Nomes e termos difíceis** — nome do profissional, procedimentos, marcas (vão para a transcrição acertar)
12. **O que NÃO pode** — algo para tirar, evitar ou não mostrar (paciente, preço, concorrente)

## Grave as respostas

```bash
python3 <skill>/scripts/briefing.py . formato=9x16 duracao=30 estilo=dinamico referencia=<link> legendas=palavra plano=pagina \
  motion=pontual broll=ambos sfx=sim trilha=gerar cliente=estudio/brands/dr-rafael cta="Comenta PELE" \
  termos="Dr. Rafael, melasma" objetivo="gerar comentários e leads" nicho=saude nome=pele-oleosa
```
`docs/BRIEFING.md` sai pronto — mostre em 4–6 linhas e siga (não peça "posso começar?").

## Regras que NÃO viram pergunta (já decididas pela Orbe)

- **Fontes/créditos nunca aparecem na tela** (nada de tarja de fonte, rodapé "Fonte: IBGE", crédito de foto).
  Vão para `docs/CREDITOS.md` e para a legenda do post quando a licença exigir. Só entram no quadro se pedirem.
- Saúde/estética: conformidade CFM automática (`conformidade.md`).
- Música e imagem só com licença clara; trilha gerada em código é a opção segura.
- Versões nunca sobrescrevem (`_v01`, `_v02`).

## Perguntas que só aparecem se fizer sentido

- O cliente AINDA vai gravar (ou só tem o talking head e quer cobertura dele) → "Monto a lista de planos para você
  gravar?" → `/lista-de-planos` (decupagem.md): página com o que gravar, de onde e para quê.
- Vários takes do mesmo trecho e nenhuma nota → "Prefere o take mais enérgico ou o mais limpo?"
- O bruto tem NOTAS FALADAS ("abre nota … fecha nota") → não pergunte o que já foi dito: siga a nota; pergunte só o que
  ela deixou vago. Cliente que grava sempre: ensine a gravar assim (é a direção mais barata que existe).
- Vídeo LONGO (podcast, live, aula) → "Quantos cortes e de que tamanho?" (3–5 de 20–60 s) → `momentos.py`.
- Vai rodar em anúncio/trial reels → "Quer variações de teste?" (direto · abertura · mudo · pb-cor · micro) → `variacoes.py`.
- O cliente tem edições que ama (dele ou de alguém) e quer "o estilo dele" → `estudar_estilo.py` + teste de fidelidade.
- Cliente recorrente com um vídeo que deu certo → "Usamos o formato salvo «…»?" → `formato.py . usar`.
- Duração alvo menor que o conteúdo bom → mostre 2 opções de condensação (o que sai em cada uma).
- Rosto saindo do quadro / material 720p → avise antes de prometer zoom.
- Áudio ruim (piso de ruído > −45 dBFS, eco) → avise que a limpeza tem limite; sugira regravar o trecho.
