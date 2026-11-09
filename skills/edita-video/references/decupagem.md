# Decupagem: a lista de planos para o cliente gravar sozinho

Use quando o cliente AINDA vai gravar (bastidores, rotina da clínica, produto, loja, história sem fala) ou quando o
talking head precisa de cobertura que nenhum banco de imagem resolve (o consultório DELE, as mãos DELE). Estudado do
"how to film yourself" (@bryanhynes): 25 planos num vídeo de 35 s, cada um com nome e função, montados em 1–2 s.

## Fluxo
1. Pergunte (1 rodada de `AskUserQuestion`): o que o vídeo conta (1 frase), onde grava (contexto), quem aparece,
   se tem fala (talking head + cobertura) ou é história muda, duração alvo.
2. `python3 $S/planos.py <pasta> modelo <contexto> --titulo "…" --alvo 30` → `_edit/planos.json` com a sequência do
   contexto (historia · clinica · loja · escritorio · restaurante · imovel · produto).
3. ESCREVA a ação de cada plano (o que acontece, com que objeto, onde) contando UMA história: começo (o lugar), meio
   (o trabalho/o problema, com detalhe e reação) e fim (resultado, fechamento). Agrupe em cenas (`"cena": 2`), corte o que
   não serve, repita um tipo de plano se a história pedir. Nunca invente o que o cliente não tem (equipamento, paciente).
4. `python3 $S/planos.py <pasta> --cliente "…"` → valida a gramática e gera `docs/PLANOS.md` + `docs/planos/index.html`.
   Publique a página como Artifact e mande o link: o cliente marca "gravado" plano a plano no celular.
5. Quando os brutos chegarem: `novo.sh … --brutos` normal; a lista vira o roteiro do mapa (cada plano = um item de
   B-roll `"arquivo"` na ordem da lista). Para conteúdo de bastidor/aula, o rótulo técnico (`rotulo` `estilo: tecnico`)
   escreve o nome do plano/etapa embaixo de cada um, como na referência.

## Gramática (o que o planos.py confere)
| regra | por quê |
|---|---|
| cada cena abre com um plano que ESTABELECE (geral de cima, geral de baixo, geral reto) | quem assiste precisa saber onde está antes do detalhe |
| ≥ 2 ângulos da mesma ação por cena | é o que permite o **corte na ação** (a mão começa o gesto num plano e termina no outro) |
| pelo menos um DETALHE e uma REAÇÃO no vídeo | detalhe mostra o que a fala cita; reação dá emoção (sem reação não há história) |
| nunca o mesmo plano duas vezes seguidas | mesma altura + mesma distância = pulo (jump cut) sem querer |
| 1–2 s por plano na montagem; grave 3–5 s com 1 s de folga | folga para cortar no movimento, não no começo do gesto |

## Truques de montagem que a lista prepara
- **Estabelece → aproxima → detalhe → reação → payoff**: a ordem natural; quebre de propósito, não por acaso.
- **Match cut**: dois planos ligados pela forma ou pelo movimento (a mão sobe com o avião de brinquedo → o avião no céu).
- **Perspectiva forçada**: objeto perto da lente parece enorme (`mesa`, `chao-ceu`) — barato e mágico.
- **POV ↔ contra-POV**: o que a pessoa vê e, logo depois, a pessoa vista pelo objeto. Prende o olhar.
- **Passagem**: algo cobre a lente e abre a cena seguinte — transição sem efeito de edição.
- **Linha guia**: corredor, mesa, prateleira levam o olho até o assunto; ótimo para entrar num ambiente.

## Celular sozinho (sem equipe)
Tripé simples + apoio (livro, caixa, prateleira). Lente 0,5× para os gerais, 1× para médios, 2×/modo retrato para
perfil e detalhe. Trava foco/exposição (toque e segure). Vertical 4K 30 qps ou 1080p 60 qps (60 permite câmera lenta).
Luz da janela de lado. Mesma roupa por cena. Sem música ambiente (atrapalha o corte).

## Saúde e Orbe
Paciente só com autorização por escrito (e nunca como "antes/depois"); prontuário, tela de sistema e documento com dado
pessoal ficam fora do quadro. Marca de terceiros (logo de equipamento) só se o cliente puder usar.
