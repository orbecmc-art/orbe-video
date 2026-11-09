---
name: motion-studio
description: "Estúdio de motion graphics 100% em código pelo Claude (window.seek(t) + Playwright + ffmpeg) com springs, tipografia cinética, câmera 2.5D, trilha e SFX com pico no frame, motion blur adaptativo, board de aprovação, auditorias de imagem e áudio, modo campanha (aberturas × formatos × CTAs), série com personagem que fala (voz → lip sync → legendas palavra a palavra), motion sobre talking head guiado por SRT e kit de marca por cliente. Use SEMPRE que pedirem vídeo animado, motion graphics/design, Reels/TikTok/Shorts animado, lançamento, anúncio animado, variações de vídeo, showreel, vinheta, intro/outro, logo animado, explainer, cartoon/personagem explicando, série de episódios animados, gráfico animado de planilha, UI animada, tipografia cinética, loop/GIF, 3D de produto, lyric video, \"zero After Effects\" ou recriar os virais de motion do Opus. Vídeo GRAVADO para editar (cortar, legendar, reenquadrar) é a skill edita-video, que chama esta na etapa de motion."
---

# Motion Studio

> A legenda diz "um prompt". O prompt real tem 10 mil caracteres, skills, exemplos e chaves — e o meio que ninguém posta: o 2º prompt, o 3º, a nota "o frame 84 pica atrasado".
> **O prompt é 10% do vídeo. Os outros 90% são o estúdio em volta dele** — regras, marca, referência, números, revisão. Esta skill é esse estúdio.

O Claude não gera MP4: escreve um programa em que `window.seek(t)` pinta o frame exato de qualquer instante. Um Chromium headless chama `seek` frame a frame, o ffmpeg costura. Determinístico: mudar um dado é uma linha + re-render. O que separa o "ficou mid" dos virais: dizer o que é **proibido**, de onde vem a **marca**, qual a **referência**, trocar **adjetivos por números** e **conferir** o resultado (o próprio Claude, olhando frames e medindo o som).

## Roteador

| Preciso de… | Vá para |
|---|---|
| Criar o projeto e renderizar | `scripts/new.sh` + §Fluxo |
| Template de prompt dirigido, números (easing, ζ, frames, batida), princípios de animação, follow-ups por frame, 3D, recibos | `references/lab.md` |
| **Campanha**: campaign.json, ganchos × formatos × CTAs, validação de claims, render por segmentos, pacote com manifesto | `references/campaign.md` |
| Contrato de render (pronto p/ colar), rotas e motores, licenças, export X/GIF/Reels | `references/pipeline.md` |
| Springs, timing, transições, câmera, loops perfeitos, hierarquia, acessibilidade | `references/motion.md` |
| Fugir do look de IA, marca, tipografia, formatos e zonas seguras | `references/look.md` |
| Trilha, regra do frame+1, nivelamento de hits, banda de celular, auditoria de áudio, loop/padding | `references/sound.md` |
| As 5 passadas de QA, ferramentas de laboratório, rubrica, notas P0/P1/P2, relatório | `references/critique.md` |
| Prompts prontos: direção (§0), one-liner, marca, referência, spec de produto (§4b), brief L4, laboratório 3D (§8) | `references/prompts.md` |
| Kit de marca, pastas de estúdio, minerar referências, fluxo com cliente, oferta e preço | `references/studio-ops.md` |
| Objeto físico que guia, um mundo e uma câmera | `references/motion.md` §11–12 + `references/prompts.md` §4c |
| Sonoplastia em que cada contato é nota (compositor pronto) | `references/sound.md` §6 + `audio/compor.py` do projeto |
| Estudo de 105 filmes de produto: lições, armadilhas e links | `references/estudo-prompt-motion.md` |
| **Os números do ofício**: regras de caso R1–R15, esqueleto de energia, voz de movimento por marca, catálogo de transições com números, câmera 2.5D, polish | `references/oficio.md` |
| **Série com personagem** (cartoon que fala: voz → tempo → boca → legendas, herói travado, cena por arquivo, "NN, mudança") | `references/cartoon.md` + `new.sh --kind cartoon` |
| Motion sobre talking head (SRT), explainer de dados, estilo por prints, remake, página interativa | `references/modos.md` |
| Qual ferramenta usar, licenças (Remotion × Orbe), rota híbrida, VoiceStudio, **o que instalar** | `references/toolchain.md` |
| **Ponte com o edita-video** (peças sobre vídeo gravado: `--query peca=moNN`, `--alpha` com fundo transparente e blur pré-multiplicado, fps racional `30000/1001`, CUES lidos pela edição) | `references/modos.md` §A + skill edita-video |
| **Engenharia de prova**: fatos × tokens, determinismo frio×quente, golden frames, sonda de cor ΔE, defeitos plantados, rótulos OBSERVADO/INFERIDO, gates G1–G6 com teto de rodadas | `references/prova.md` + `scripts/prove.mjs` |
| **Receitas prontas**: revelação de produto, vista explodida, rota no mapa, gráfico com contador na ponta, linha digitada, lower third, logo, física (`M.bake`), GSAP que respeita o seek | `references/receitas.md` |
| **Documentário contínuo** (um plano-sequência sobre mapa/mesa real, papéis caindo, ano gigante, rota, gesto na palavra; voz primeiro, tabela de batidas aprovada antes, câmera que nunca para nem dá tranco) | `estilos/documentario-continuo/` (ESTILO.md + projeto pronto) |
| **Galeria de 23 estilos** (ficha pronta com metas de movimento + código que o render lê), escolher estilo, perícia de movimento × referência, regras dos estúdios 2026 (transformar em vez de dissolver, centro, palavra que sobe) | `references/galeria.md` + `estilos/` |
| Exemplo funcional (dados de campanha, forma única, abas líquidas, contador, PROBES, CHECKS, VALIDATE, CUES, SHOTS) | `template/index.html` + `template/campaign.json` |

Leia o reference de cada etapa **quando chegar nela**, não tudo de uma vez.

## Fluxo (siga os gates — não pule do código ao render final)

**0. Modo e nível** (prompts.md): L1 one-liner · L2 marca/produto · L2+ referência · L3 spec de produto · **Laboratório** (loop curto, 3D, tudo em números) · L4 brief de diretor · **Campanha** (variações para publicar) · **Série** (personagem que fala, cartoon.md) · **Sobre talking head** / **dados** (modos.md). Pedido de "vídeo pro cliente X" = L3; "vários formatos/versões/testes A/B" = Campanha; "desenho/personagem explicando" = Série. Escolha a voz de movimento da marca (oficio.md §3).

**1. Marca, dados e insumos**
- Kit do cliente (`estudio/brands/<cliente>/BRAND.md`) existe? A marca vem dele, mesmo com referência nova.
- Senão, colete (look.md §1): logo, hex, fontes, UI/screenshots reais, duração, formatos, CTA, música. Com URL: capture assets reais e **liste antes de animar**.
- **Todo número que o vídeo vai dizer vira um claim com fonte do cliente** em `campaign.json`. Sem fonte → o vídeo não diz o número.
- Referência em vídeo? `bash scripts/ref.sh <arquivo|url>` → frames, duração dos planos, paleta, BPM.

**2. Estilo e direção em números** — UM estilo antes de tudo: da galeria (link em `galeria.json`; ficha `estilos/<id>/ESTILO.md` vira lei) ou da referência da pessoa (perícia → ficha no mesmo formato) — galeria.md. Depois feche OBJETIVO (uma frase), TEMPO (s × fps = frames, BPM), LOOK, MOVIMENTO, PLANOS e PROIBIDO (lab.md §1). Para cliente, ofereça 3 direções e recomende uma.

**3. Projeto — sempre numa pasta nova**
```bash
bash <skill>/scripts/new.sh estudio/filmes/<data>-<cliente>-<nome> [--brand estudio/brands/<cliente>] [--fonts "<display>:400,800" "<ui>:500,600"]
```
Edite `campaign.json` (o QUE o vídeo diz) e o `index.html` (COMO aparece; o look do template é placeholder).

**4. Som primeiro** (sound.md): faixa → `python3 scripts/beats.py audio/track.wav > audio/beats.json` · sem faixa → `node scripts/music.mjs --bpm 120 --dur 12 --style tech` · objeto que guia → rota em `campaign.json` + `python3 audio/compor.py`, e mande o esboço de som junto do roteiro: é a parte que o usuário consegue julgar antes de existir imagem.

**5. Tabela de estados** (G1) — `docs/SPEC.md` (adjetivos → números + BANNED + vocabulário semântico) e `docs/STORYBOARD.md` (tempo · capítulo nomeado · estado · leitura · texto · **persiste na tela** · som · transição). Mostre e espere OK em L2+/L3/L4/Campanha. **Still primeiro**: 1 frame-chave por capítulo aprovado antes de animar.

**6. Construir** — receita pronta? (`receitas.md`) · `M.track`/`M.springZ`/`M.EASE` (tokens, nada solto), `B(n)` para tempos, `L`/`u` para layout, e no mesmo timeline: `window.CUES` (som), `window.SHOTS` (board), `window.PROBES` (gráficos), `window.CHECKS` (cada número do brief vira teste), `window.VALIDATE` (texto cabe/fonte carregou).

**7. Olhar e medir antes de renderizar** (critique.md — as 5 passadas; prova.md — os instrumentos):
```bash
node scripts/prove.mjs determinism                 # frame frio = frame quente (senão nada do que você olhar vale)
node scripts/stills.mjs --board                    # 1 frame por estado + ⚠ texto curto demais → out/board.html
node scripts/stills.mjs --checks                   # auditoria numérica (sai com erro se algo falhar)
node scripts/stills.mjs --strip <t> | --onion a,b | --graph | --frames 83,84,85
node scripts/campaign.mjs validate [--draft]       # claims, fontes, texto em cada formato, contrato de variantes
```
**Abra as imagens com Read e critique de verdade.** Notas `P0/P1/P2 · frame · onde · problema → mudança exata`, citando as regras de caso (oficio.md R1–R15). 1–2 follow-ups por rodada. Repita até tudo ≥ 8. Em peça de cliente, rode a revisão adversarial (critique.md §7): crítico em contexto limpo + resumo cego; a v2 só entra se ganhar lado a lado.

**8. Render + som + QA**
```bash
# filme único
node scripts/render.mjs --fps 60 --sub 4 --out out/silent.mp4      # blur adaptativo em luz linear, sem cruzar cortes; --fps 30 --sub 1 --jpeg = animatic
#   --deband (gradiente grande) · --alpha (ProRes 4444 transparente p/ pôr sobre vídeo) · --master (ProRes 422 HQ 10 bits)
node scripts/sfx.mjs --page index.html --bed audio/music.wav --bed-db -4
bash scripts/mix.sh out/silent.mp4 out/final.mp4 --music audio/music.wav --sfx audio/sfx.wav --music-db -4
bash scripts/qa.sh out/final.mp4 [--loop]  &&  python3 scripts/audit-audio.py out/final.mp4 --sfx audio/sfx.wav --music audio/music.wav --music-db -4
# campanha (todas as variantes, cache por segmento, pacote com manifesto)
node scripts/campaign.mjs all [--draft]
```
Olhe `out/qa/contact.png`, `phone.png` (390 px: leia as legendas), e no `qa.md`: Deck Trap (mudança por 2 s ≥ 14%), pops, frame intruso, mono; e o `audio.md` do **master**. Export: `bash scripts/export.sh out/final.mp4 x|reels|gif [--loop-fade]`. Aprovado: `node scripts/prove.mjs golden save` (todo conserto depois passa por `golden check --scope`).
**Para o cliente ver/aprovar**: `node scripts/bundle.mjs --audio out/final.mp4` → uma página com Play/Gravar (pode virar Artifact com link privado).

**9. Entregar, registrar e guardar** — envie os MP4/capas (ou o `.zip` da campanha). Relatório em 3–4 linhas: **frames revisados · problemas · o que consertou · o que ainda preocupa**; diga que o áudio foi **medido, não ouvido**. Registre prompts e follow-ups em `docs/PROMPTS.md` (recibos). Aprovado: `bash scripts/brand.sh save . estudio/brands/<cliente>` e atualize o BRAND.md.

## Regras duras

1. **Rota pura por padrão**: `index.html` + `seek(t)` + Playwright + ffmpeg (os projetos da galeria, em GSAP, entram pela ponte do `pw.mjs` — mesma rota). Não chame a skill `remotion-video`, HyperFrames ou outra skill de vídeo salvo pedido explícito (o motor não muda a qualidade; Remotion exige licença de empresa acima de 3 funcionários — a Orbe tem 4). Pessoas/filmagem/fotorrealismo: rota híbrida (toolchain.md), com texto e marca sempre em código.
2. **Contrato**: `seek(t)` puro; sem timers, rAF no render, `Math.random`, estado entre frames; discretos via `M.frameT`/`M.count`; loops = frames 0..N−1 com ciclos inteiros.
3. **Adjetivo → número.** Easing em cubic-bezier, springs em ζ + Hz, durações em frames, padrões proibidos pelo nome.
4. **Olhe e meça antes de mostrar.** Nunca diga que terminou sem ter aberto o render e o relatório de áudio.
5. **UI, marca e dados reais.** Nunca invente telas, números, depoimentos ou features; número sem claim aprovado = brief recusado. **Fonte/crédito nunca na tela** (regra Orbe: sem tarja de fonte, rodapé "Fonte:", crédito de foto) — fica no campaign.json/LEIA-ME/legenda do post, salvo pedido explícito.
6. **Proibidos por padrão**: título centralizado sobre gradiente, tudo com fade-in, rótulos de canto, glow/neon/partículas, quique em UI, tempo morto, frame 0 vazio, cursor clicando em movimento, mesmo whoosh em todo corte (look.md §2), > 3 batidas de tela cheia, crossfade entre fundos de tom oposto, tilt-shift/lens flare, SFX com timbre de jogo.
7. **Uma display + uma UI + um acento**, salvo marca. Legenda/texto principal ≥ 5,2% do lado curto (auxiliar ≥ 2,6%), no ar ≥ 0,5 s + 0,3 s/palavra, contraste ≥ 4,5:1. Herói ≥ 40% do quadro. ≤ 3 flashes/s.
8. **Som**: pico em evento + 1 frame; hits 3–6 dB sobre a trilha; −14 LUFS; MP4 decodificado ≤ −1 dBTP; banda de celular viva. A imagem funciona no mudo.
9. **Uma pasta por filme**; kit de marca separado das regras; campanha só com `approval.copy = true`.
10. **Chaves** só no `.env`. **Ambiente**: `new.sh` checa node, ffmpeg, Playwright e numpy. Em chat sem ferramentas, entregue o HTML com o player que grava (`lib/recorder.js`, prompts.md §10).
11. **Fatos são lidos, nunca escritos** pela composição; asset que falta BLOQUEIA a cena (não se aproxima). O modelo não dá nota à própria intenção: juiz = frame, referência ou instrumento. Máximo 5 rodadas de conserto, depois reporte o que falta (prova.md).

## Escala e esforço

- Esforço: **medium** por padrão; suba para xhigh/max só quando uma peça do zero errar duas vezes ou num 1º build ambicioso.
- Até ~6 cenas: construa num só contexto. Acima: `docs/ANIMATION_GUIDE.md` + 2–3 cenas por subagente em arquivos próprios; um subagente **revisor** recebe só STORYBOARD + sheets e devolve P0/P1.
- Campanha: não deixe o modelo redesenhar componentes de marca a cada cliente — templates revisados que ele **escolhe e configura**.
