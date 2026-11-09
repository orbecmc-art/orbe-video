# Galeria de estilos — escolher UM estilo antes de animar

A galeria (página com o vídeo real de cada estilo) está no link de `../../galeria.json` (`url`) e vai inteira no plugin
(`../../galeria/`). Mostre o link na pergunta de estilo; a pessoa aperta "Usar este estilo" e cola o **id**. Quem não
abre o link (privado da conta da Orbe): publique a cópia da pasta `galeria/`. Sem nada disso: liste a tabela abaixo.

Cada estilo em `estilos/<id>/` tem:
- `ESTILO.md` — a perícia pronta da referência: mecanismo em uma frase, batidas com tempo e curva, paleta em hex,
  traço, **metas de movimento medidas** (amplitude, quase-parada, picos, cortes) e o que é permitido/proibido. Vira lei.
- `LEIA-ME.md` — o que trocar e o que quebra.
- `projeto/` — o código da peça de referência (HTML + GSAP no contrato HyperFrames). O `render.mjs` já renderiza
  esses projetos: o `pw.mjs` liga a timeline pausada (`window.__timelines.main`) ao `seek(t)`. Arquivos pesados
  (fotos, trilhas) não vêm junto — a cena da pessoa usa a mídia DELA.

**Da referência se copia método e sensação (mecanismo, ritmo, paleta, traço). Nunca o conteúdo**: tema, textos e
marca são do cliente. O código é apoio para ver como um truque foi feito, não molde para preencher.

Origem: `dossie-de-dados` é o filme "A conta" da Orbe (05/11/2026); `documentario-continuo` é o motor de documentário da
Orbe (07/11/2026, método do prompt "continuous flowing" + Zane Hoyer, demo "Goiânia, a capital planejada"); os outros 21
vêm da biblioteca **claude-video** de
Felipe Borges (MIT; aviso em `../../LICENCAS-TERCEIROS.md`).

| id | estilo | melhor para | formato |
|---|---|---|---|
| `documentario-continuo` | Documentário contínuo (Orbe) | história, linha do tempo, "como nasceu", caso contado como documentário: UM plano-sequência sobre um mapa/mesa real, papéis caindo, ano gigante, rota, círculo e carimbo na palavra; tabela de batidas aprovada antes | 1080×1920 (ou 16:9/21:9), duração da voz, narração + piano |
| `dossie-de-dados` | Dossiê de dados ("A conta", Orbe) | uma conta que emociona e é compartilhada; dado público explicado com papel, etiquetas, quadradinhos e persiana | 1080×1920, 85 s, narração + piano |
| `app-de-design` | App de design com cursor de IA | demo de app ou produto de design, abertura sobre thumbnails ou identidade visual, teaser "a IA desenhou isso", vídeo sobre criar com IA, mock de feed  | 1920×1080, 15 s, sem som |
| `app-de-motion` | App de motion com cursor de IA | demo de ferramenta de animação, abertura sobre motion graphics com IA, vídeo em tema escuro sobre keyframes e curvas, teaser "do plano cru ao plano pr | 1920×1080, 16 s, sem som |
| `aviao-em-codigo` | Avião em código | objeto 3D feito só com código (produto, carro, avião, prédio) apresentado num painel de controles, "cada peça se move" e troca de pintura em um clique | 1920×1080 (16:9), 22 s, sem som |
| `barco-e-montanha` | Barco e montanha | fundo ambiente em loop (tela de espera, intervalo, live), abertura calma de marca, peça "um dia inteiro" sem texto, ilustração em papel recortado para | 1920×1080, 16 s em loop (quadro 0 s = quadro 16 s), sem som |
| `cartaz-gritado` | Cartaz gritado | gancho de Short ou Reel (uma palavra por batida), contagem regressiva, chamada para um lançamento, vinheta barulhenta com música | 1920×1080 (16:9), 12 s, em loop, sem som |
| `cartaz-risografia` | Cartazes em risografia | anúncio de live, evento ou lançamento em três cartazes, teaser percussivo para Reels, vinheta de abertura com música, qualquer coisa que precise de so | 1920×1080 (16:9), 12 s, em loop, sem som |
| `diagrama-azul-marinho` | Diagrama azul-marinho | explicar um fluxo ou pipeline (pedido → plano → código → teste → no ar), arquitetura de agente ou automação, etapas de um serviço, fundo técnico calmo | 1920×1080 (16:9), 12 s, em loop, sem som |
| `dirigivel-a-lapis` | Dirigível a lápis | história de mascote ou personagem, abertura de post quadrado (Instagram), peça "feita à mão" sobre um projeto ou jornada, cenário que se constrói traç | 1600×1600 (1:1), 28,6 s, sem som |
| `documento-vira-video` | Documento vira vídeo | aberturas e showreels de marca em que um documento, pedido ou roteiro vira filme; peças de 10 a 60 s com mergulhos de câmera e volta pelo mesmo ponto | 16:9 · 32 s · referência a 60 fps (a cópia da galeria roda a |
| `editor-ia` | Editor com cursor de IA | abertura de vídeo sobre edição com IA, demo de app ou produto de edição, teaser "a IA editou isso", vinheta de canal que fala de ferramentas, cena de  | 1920×1080, 18 s, sem som |
| `festival-da-lua` | Festival da lua | peça contemplativa de paisagem, "desenho que vira foto" com passagem de tempo (dia→noite), vinheta sem texto para abertura ou intervalo, tema oriental | 1920×1080, 28 s, sem som |
| `folha-de-projeto` | Folha de projeto | mostrar como um produto ou sistema é por dentro (vista explodida), destacar uma peça ou etapa de um conjunto, abertura de vídeo técnico, loop de fundo | 1920×1080 (16:9), 12 s, em loop, sem som |
| `giz-de-cera` | Giz de cera | aberturas e vinhetas curtas com clima infantil e divertido — anotação de professor, caderno de desenho, uma palavra ou nome escrito à mão com laço e s | 16:9 · 5 s em loop sem emenda · 30 fps (o render funciona ta |
| `grafico-de-jornal` | Gráfico de jornal | um número ou ranking que muda de figura (antes e depois), comparação de 3 a 6 itens em que um se destaca, dado de resultado num vídeo ou post, cartão  | 1920×1080 (16:9), 10 s, em loop, sem som |
| `interface-escura-3d` | Interface escura em 3D | filme de produto ou de funcionalidade de um app, demonstrar um fluxo de interface (clicar, concluir, publicar), abertura de vídeo sobre ferramenta, ma | 1920×1080 (16:9), 12 s, em loop, sem som |
| `livro-pop-up` | Livro pop-up de papel | frase ou promessa curta em serifa ("passo a passo"), abertura afetiva ou artesanal, cartão de boas-vindas, loop de fundo quente para falar por cima | 1920×1080 (16:9), 12 s, em loop, sem som |
| `porto-de-nova-york` | Porto de Nova York | cartão-postal de cidade ou lugar, passagem de tempo (pôr do sol→noite) com as luzes acendendo, abertura contemplativa sem texto, peça de viagem ou tur | 1920×1080, 30 s, com som (trilha sintetizada em código; a có |
| `poster-suico` | Pôster suíço em grade | título ou slogan de 3 linhas que troca uma palavra, cartão de abertura ou encerramento em loop, vinheta de marca com um só acento, tela de espera ante | 1920×1080 (16:9), 9 s, em loop, sem som |
| `rabisco-de-caneta` | Rabisco de caneta | aberturas e vinhetas com cara de caderno escolar — letras-balão de esferográfica, rabiscos na margem (espiral, estrela, cubo, raio, seta), um nome ou  | 16:9 · 5 s em loop sem emenda · 30 fps (o render funciona ta |
| `sessao-na-mesa` | Sessão na mesa | contar uma sessão real entre a pessoa e o agente dela (pedido, trabalho, resposta, correção, elogio) como desenho animado em aquarela; bastidores, bui | 16:9 · 58,7 s na peça de exemplo (loop de 5 s na parede: ped |
| `showreel` | Showreel em fundo claro | showreel ou portfólio de motion designer, abertura de canal em fundo claro, tipografia cinética em capítulos, vídeo "o que eu sei fazer" para currícul | 1920×1080, 16 s, com som (trilha gerada em código, −14,9 LUF |

## Como usar (encaixa no Fluxo da SKILL)
1. **Estilo** (passo 2): id da galeria → leia `estilos/<id>/ESTILO.md` inteiro. Referência própria → `ref.sh` +
   `python3 ../edita-video/scripts/pericia_movimento.py REF.mp4 --json docs/movimento_ref.json` e escreva o
   `ESTILO.md` do projeto no mesmo formato (mecanismo, batidas, paleta, metas). "Escolhe você" → escolha pelo assunto
   e diga por quê em uma linha.
2. **Brief em números** com a paleta da MARCA no lugar das cores do estilo (as regras do estilo ficam).
3. **Cards parados** (1 por cena, com texto/fonte/cor/mídia reais) aprovados antes de animar; depois 3 quadros
   ~0,6 s após cada virada, nota 1–10 em composição · movimento · tipografia · cor · ideia; conserte as 3 piores até
   tudo ≥ 8.
4. **Projeto**: `cp -r estilos/<id>/projeto <pasta>` (motor pronto) e troque a cena; ou `new.sh` e siga a ficha.
5. **Aceite de movimento**: `python3 ../edita-video/scripts/pericia_movimento.py out/final.mp4 --contra <ref>.mp4`.
   Reprovou → quase nunca é "acelerar tudo": escolha UMA batida para ser o soco e aprofunde as paradas vizinhas.

## Regras dos estúdios (vídeos de 2026: Felipe Borges, Rourke/GenHQ, Joseph/Ultimate Editors)
- **Cada plano se transforma no próximo** (linhas viram círculo, círculo vira quadrado, quadrado abre o player).
  Pergunte no storyboard: "como esta forma vira a próxima?". Crossfade entre planos = proibido.
- **Ação no centro do quadro**, efeitos em volta: o olho não pula pela tela.
- **Sempre algo em movimento** (no mínimo a câmera); nada parado > 1 s; nada na tela < 0,3 s.
- **Texto**: cada PALAVRA sobe por máscara e encaixa, uma após a outra; sem quicar, sem letra a letra em fade.
- **Menos é mais**: elementos ~25% menores do que o primeiro impulso; efeito raro é efeito especial.
- **Cores foscas** (azuis/verdes dessaturados) parecem caras; preto, branco e vermelho puros parecem amadores.
- **Profundidade de campo rasa** no fundo = cara de câmera.
- **Mídia real > desenho**: logo em alta (nunca recortado de print), telas reais, fotos/vídeos do cliente; sem
  mídia, gerar com Higgsfield (mostrar plano e custo antes) — saúde: nunca pessoa como paciente/resultado.
- **Visual primeiro, som por último**: mexer na animação depois do som quebra a sonoplastia.
- **Locução depois do vídeo pronto**: o Claude sabe a duração e escreve o texto que cabe (ElevenLabs/VoiceStudio);
  trilha gerada no tamanho exato.
- **3D com luz única de referência** (Blender por trás) e final no quadro exato que emenda com a filmagem real.
- **Confira contra o produto real** (detalhes, proporções) antes de entregar.
- Anti-IA-barata (a lista de sempre): degradê roxo, brilho/faísca, texto gigante no meio, fade em tudo.
