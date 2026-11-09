# Operação de estúdio — constância entre vídeos e clientes

Um vídeo bom é fácil de repetir quando o que foi aprovado fica salvo. Esta é a camada que transforma "um prompt que deu certo" em **padrão de entrega**.

## 1. Estrutura de pastas

```
estudio/
  brands/<cliente>/          ← kit de marca (BRAND.md, logo.svg, fonts/, assets/, approved/)
  filmes/2026-10-30-<cliente>-<nome>/   ← UM projeto por filme (new.sh), nunca reaproveitar a pasta
  refs/                      ← referências estudadas (ref.sh), reaproveitáveis entre clientes
```
- **Cada filme numa pasta nova.** Se o projeto anterior estiver na mesma pasta, o modelo olha para ele e acaba alterando ou copiando. Nos testes, avisar "projeto novo, salve em outra pasta" foi necessário.
- `CLAUDE.md` (regras do estúdio, iguais para todos) ≠ `BRAND.md` (identidade de UM cliente). Não misture.

## 2. Kit de marca (o que garante constância)

```bash
bash <skill>/scripts/new.sh estudio/filmes/2026-11-02-acme-lancamento --brand estudio/brands/acme   # começa com a marca
bash scripts/brand.sh save . ../../brands/acme                                                      # depois da aprovação
```
- Primeiro filme de um cliente: preencha `brand/BRAND.md` durante o trabalho (logo real, hex, fontes, tom).
- **Ao terminar e o cliente aprovar**: `brand.sh save` + atualize o BRAND.md com o que foi aprovado (springs, velocidade, transição assinatura, trilha, CTAs) e uma linha no Histórico com o feedback do cliente.
- Próximo filme: mesmo com uma referência nova, a marca vem do kit — a referência dá a **gramática** (ritmo, transições), a marca dá a **identidade** (cores, fontes, logo).
- "Proibido para este cliente" cresce a cada rodada e entra na linha BANNED do SPEC.

## 3. Minerar referências

- Galerias: **awesome-opus-5-5-videos** (vídeos feitos com o Opus 5.5, cada um com link para o post original no X — também revela perfis para seguir), whatships.com (lançamentos), Dribbble motion, filmes de lançamento de concorrentes.
- Escolheu uma? `bash scripts/ref.sh <arquivo-ou-url> --name <nome>` → frames, cortes/duração dos planos, paleta, BPM, ANALYSIS.md.
- Depois: "desmonte esta referência, entenda a estrutura e crie com base nela para [marca/produto]" (prompts.md §3).
- O X é o melhor lugar para achar quem produz esse tipo de vídeo; siga os autores dos que você mais gostar.

## 4. Fluxo com o cliente

| Etapa | O que o cliente vê | Arquivo |
|---|---|---|
| Direção | 3 variantes de direção (1 parágrafo cada) ou a direção já fechada | conversa / `docs/STORYBOARD.md` |
| Storyboard | **tabela de estados na grade de batidas** (sem imagens ainda) | `docs/STORYBOARD.md` |
| Board | a mesma tabela **com um frame por estado** + aviso de texto curto demais | `out/board.html` (`stills.mjs --board`) |
| Corte | MP4 com som, nos formatos combinados | `out/final.mp4` |
| Ajustes | até 3 rodadas de notas de diretor | `docs/REVIEW.md` |

Aprovar no board é muito mais barato que aprovar no render: cada mudança no board custa segundos; no vídeo, minutos.

## 5. Campanha: 18 arquivos de um brief
Detalhes em `campaign.md`. Resumo: `campaign.json` (dados) + template revisado (animação) → `campaign.mjs validate` (assets, fontes, texto cabe, CHECKS, **claims aprovados**, contrato de variantes) → `render` por segmentos com cache → `package` (manifest com hash de cada arquivo + LEIA-ME para o cliente + zip).
Comece por UM tipo de vídeo (ex.: dashboard animado de 25 s com 4 cenas: título forte, interface com cursor, dado/feature animado, identidade + CTA). Deixe esse bom de verdade; só então parametrize, adicione formatos e aberturas, e por último o lote.

## 6. Oferta e preço (referência de mercado)

- Um reel de lançamento que custava ~US$ 1.000 numa agência sai em ~30–60 min com este pipeline (relato de Tony Dinh no X).
- Pacote que vende: trilha original, mascote/personagem no estilo da marca (com voz, se quiser), features reais do produto, oferta no final, qualquer idioma, até 3 rodadas, 9:16 + 1:1 + 16:9 do mesmo timeline.
- Recorrência: kit de marca salvo → cada vídeo novo do mesmo cliente parte do zero só na história, não no look.
- **Venda um pacote de lançamento, não "IA"**: um produto, uma narrativa aprovada, 3 aberturas, 3 formatos, 2 CTAs, os MP4s, capas e um número fechado de revisões. O cliente não quer saber o que é `seek(t)`; quer a campanha no prazo.
- **Cobre por entregável, nunca por prompt.** (Exemplo ilustrativo de um autor, não tabela de mercado: pacote de US$ 750 — antes de impostos, software, computação, licença de áudio, tempo de venda e revisões.)
- Meça para saber se compensa: horas do 1º design · horas por variante extra · custo de render e de API · revisões pedidas · erros de entrega · clientes que voltam.
- **Recibos vendem**: registre prompts e follow-ups em `docs/PROMPTS.md` e mostre o processo ("3 prompts, 2 rodadas de revisão") em vez de "um prompt só".
