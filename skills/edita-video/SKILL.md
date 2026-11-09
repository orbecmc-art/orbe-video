---
name: edita-video
description: "Editor de vídeo GRAVADO pelo Claude com cara de programa profissional — talking head, Reels/TikTok/Shorts, depoimento, aula, médico/clínica, podcast e cortes de vídeo longo. Perguntas fixas (formato, estilo com galeria, REFERÊNCIA, legendas, motion, B-roll, som, plano), corte de silêncios e regravações, notas faladas viram direção, 9:16 no rosto com punch-in, legendas animadas, B-roll com licença, motion via motion-studio, SFX por evento, trilha com ducking, −14 LUFS, QA medido. Estilos de dinâmico a minimal premium, dossiê, podcast P&B, lifestyle e entrevista com ritmo e batidas medidos; edit de carro/produto/evento na batida; lista de planos para o cliente gravar; variações de teste (trial reels/A-B), formatos repetíveis, estilo treinado. Multiplataforma (Premiere, Final Cut, DaVinci, CapCut, celular). Use SEMPRE que pedirem editar, cortar, legendar, “tirar os silêncios”, “deixar dinâmico/premium”, reels de vídeo gravado, cortes de podcast ou mandarem brutos. Motion do zero é a skill motion-studio."
---

# Edita Vídeo

> Edição como DADO: tudo que a edição decide vive em `_edit/*.json` com IDs estáveis; o render é determinístico.
> O Claude **lê** o vídeo (transcrição por palavra), **decide** (cortes, mapa, câmera, som), **mede e olha** (QA +
> folhas) — e só então mostra. Base: fluxo de 8 etapas do LeiteZ + o melhor de video-use, HyperFrames, Remotion e da
> skill motion-studio (que esta chama na etapa de motion).

## Roteador

| Preciso de… | Vá para |
|---|---|
| As perguntas fixas antes de editar (inclui REFERÊNCIA) | `references/perguntas.md` |
| O fluxo, os 4 portões, IDs, continuidade entre sessões | `references/fluxo.md` |
| Regras de corte, retake, vícios, condensar para a duração | `references/cortes.md` |
| Mapa de motion/B-roll, catálogo de peças, busca com licença, ponte motion-studio | `references/motion-e-broll.md` |
| Reenquadrar, zoom alternado, punch-in | `references/camera.md` |
| Legendas (tamanho, quebra, posição, correções) | `references/legendas.md` |
| Voz, trilha, SFX, loudness | `references/som.md` |
| Cor, QA (o que bloqueia), entrega, export Premiere, aprendizados | `references/cor-qa-entrega.md` |
| Presets de estilo, pedido → número, referência → número | `references/estilos.md` |
| **Minimal premium** (look Arthur Brooks: 10 princípios → peças, legenda cinematográfica, plano, som em 3 famílias) | `references/estilo-minimal.md` |
| **Dossiê** ("fizemos a conta": tarjas, etiquetas, faixa, grade, colagem, recorte, papel com persiana) | `references/estilo-dossie.md` |
| **Vitrine**: o mesmo vídeo em todos os estilos (galeria ou para o cliente escolher) | `scripts/vitrine.py` + `../../galeria/` |
| **Ritmo, batidas e junções do estilo** (gancho/virada/item/número/prova/fim → peça; mudança a cada X s; slam, caixa da palavra-chave, janela, fio no split, cor em rodízio) | `references/ritmo-e-batidas.md` + `scripts/ritmo.py` |
| **Variações de teste** (trial reels/criativos A-B), **formatos repetíveis**, **cortes de vídeo longo**, **estilo treinado em referências** | `references/variacoes-e-formatos.md` |
| **Podcast P&B** (cinematográfico: legenda que se monta, palavra-chave em serifa itálica, palavras atrás da cabeça, quebra com reverb) | `references/estilos.md` (preset `podcast-pb`) |
| **Lifestyle** (gancho empilhado, legenda micro, rótulo sans + manuscrita no espaço livre, card de documento) e **Entrevista** (legenda em escada, cartelas de respiro, 2 ângulos, fim no preto) | `references/estilos.md` + `motion-e-broll.md` (v1.5) |
| **Lista de planos** (decupagem para o cliente gravar sozinho: o que, de onde, para quê) | `references/decupagem.md` + `scripts/planos.py` |
| **Edit cinematográfico sem fala** (carro, concessionária, produto, aftermovie, imóvel: takes e fotos na batida, cinema lento, ritual, vire o celular, ASMR) | `references/edit-cinema.md` + `scripts/montagem.py` (comando `/edit-cinema`) |
| Regras Orbe (sem fonte na tela), saúde/CFM, licenças | `references/conformidade.md` |
| **Editar no Premiere, Final Cut, DaVinci, CapCut, celular ou navegador**; Claude ao vivo no editor (Edit Link, MCPs) | `references/multiplataforma.md` |

Leia o reference de cada etapa quando chegar nela.

## Fluxo (S = `<esta skill>/scripts`, rode dentro da pasta do projeto)

**0. Perguntas fixas** (`perguntas.md`) — 2 rodadas de `AskUserQuestion` + plano + 1 texto livre. A pergunta de
**referência** nunca é pulada; a de estilo leva o link da **galeria** (`galeria.json` na raiz do plugin). Grave: `python3 $S/briefing.py . formato=9x16 duracao=30 estilo=dinamico …`.
Referência: `python3 $S/referencia.py . <link|arquivo>` → abra as folhas → preencha "O que eu vi" → ajustes.

Cliente ainda vai gravar (ou quer cobertura própria): `python3 $S/planos.py <pasta> modelo <contexto>` → ações → `planos.py <pasta>`
→ página da lista de planos para o cliente (decupagem.md).

**1. Iniciar** — `bash $S/novo.sh estudio/edicoes/<data>-<cliente>-<nome> [--cliente estudio/brands/<cliente>] --brutos <arquivos>`
(confere ffmpeg/libass/opencv/faster-whisper/node/motion-studio e baixa os modelos).

**2. Preparar** — `python3 $S/preparar.py . [--termos "Dr. Rafael, melasma"]` → inventário (VFR/HDR/rotação),
mezanino CFR, transcrição por palavra (faster-whisper pt, vícios preservados), `docs/FRASES.md`. **Leia FRASES.md.**

**3. Cortes** — `python3 $S/cortes.py .` → `docs/CORTES.md`. Ajuste por índice (`--remover 8-12,F009 --manter 42`).
**Notas faladas**: "abre nota … fecha nota" (ou "Claude, coloca…") gravado no vídeo sai do corte e vira instrução em
`docs/NOTAS_FALADAS.md`, ancorada na palavra seguinte — o plano/mapa começa por elas. Vídeo LONGO (podcast, live):
`momentos.py .` lista os melhores cortes → `momentos.py . extrair 1,3` (variacoes-e-formatos.md).
Rascunho para o cliente ver o ritmo: rode câmera+legenda (passos 7) e `python3 $S/final.py . --rascunho --sem-qa`.
**Portão ①**: aprovado → `python3 $S/estado.py . aprovar cortes` (trava).

**4. Plano e mapa** — `python3 $S/mapa.py . rascunho` → escreva `_edit/mapa.json` (âncoras `#palavra`; anuncia → rosto,
descreve → mostra) → `python3 $S/mapa.py .` → `docs/MAPA.md`. **Portão ②**: `python3 $S/plano.py .` → publique a página
(Artifact, `db` + `user`); a pessoa escolhe por linha Legenda · Legenda + UI · Meia tela · Tela cheia + design + nota →
leia (ArtifactData "plano" → `_edit/plano.json`) → `plano.py . aplicar` → preencha os itens "pendente" → `mapa.py .`.
`ritmo.py . batidas` sugere a batida de cada frase (gancho, virada, item, número, prova, fim) com a peça do estilo;
marque `"batida"` nos itens e rode `ritmo.py .` — ritmo, junções recusadas, slam, fim curto (ritmo-e-batidas.md).
Formato salvo de um vídeo que deu certo: `formato.py . usar <nome>` antes do mapa.

**5. Assets** — `python3 $S/ativos.py . buscar` → **abra** `docs/folhas/<id>_opcoes.jpg` → `ativos.py . escolher br01=a3`
· material próprio: `ativos.py . conformar`.

**6. Motion (motion-studio)** — `python3 $S/motion_ponte.py . preparar` → `board` (**abra** `motion_board.jpg`, critique)
→ `render`. Peça fora do catálogo: projeto motion-studio próprio com `"peca": "custom"`.

**7. Câmera e legendas** — `python3 $S/rosto.py .` · `python3 $S/camera.py .` · `python3 $S/legendas.py . [--corrigir "#18=três"]`
(J-cut opcional: `briefing.py . ajuste.cortes.jcut=3`; texto atrás da pessoa: `"atras": true` na peça do mapa.)

**8. Som** — `python3 $S/eventos.py .` (`docs/SOM.md`) · `python3 $S/audio.py . [--lib <SFX gravados>]`

**Final** — `python3 $S/final.py .` → `renders/<nome>_vNN.mp4` + `.srt` + capa + QA (+ perícia de movimento × referência). **Abra** as duas folhas do QA,
revise P0/P1/P2, conserte (máx. 3 rodadas). **Portão ③**: mostre a v01 em 3–4 linhas (`docs/ENTREGA.md`).
Ajustes por número → nova versão. Aprovado e vai rodar em teste/anúncio: `variacoes.py .` (direto, micro, abertura, mudo,
pb-cor — cada uma com hipótese e métrica, prévia lado a lado com o master). Deu certo: `formato.py . salvar <nome>`.
Estilo do cliente a partir das edições que ele ama: `estudar_estilo.py <pasta> --nome <estilo>` (variacoes-e-formatos.md).

**Edite onde quiser** (`multiplataforma.md`) — `python3 $S/nle.py . [--para premiere,finalcut,resolve,capcut,celular] --base <pasta no Mac>`
→ kit com trechos já reenquadrados (alça de 1 s), coberturas, motion e legendas com alfa, stems, LUT, guias e as linhas do
tempo (XML, OTIO, FCPXML validado, EDL, rascunho CapCut, pacote celular). Premiere com **Edit Link**/premiere-pro-mcp ou
DaVinci 21.1 Studio conectados: o Claude importa o kit e confere ao vivo.
**Revisão no navegador** — `python3 $S/revisao.py .` → publique como Artifact (`db` + `user`); o cliente assiste, pede
por número e aprova; leia os pedidos (ArtifactData) → `python3 $S/pedidos.py .` → refaça o que ele indicar.
**Aprendizado**: `estado.py . aprendizado "…" --gosto|--oficio` (gosto vai para o kit do cliente; ofício para todos).

Ao reabrir um projeto: `python3 $S/estado.py .` (onde parou + próximo comando).

## Regras duras

1. **Perguntas fixas primeiro**; referência sempre perguntada. Sem resposta possível: padrões + "assumi: …" no DIARIO.
2. **Ler, não assistir**: decida pelo texto; olhe imagens nas folhas. Nunca descreva quadro que não abriu.
3. **Na dúvida não corta — marca.** Nunca troca o que foi dito pelo roteiro. Corte aprovado trava.
4. **Nenhuma fonte/crédito na tela** (regra Orbe) salvo pedido explícito — vão para `docs/CREDITOS.md`.
5. **Todo vídeo tem motion e som desenhados** (salvo o briefing dizer não): gancho visual nos 2 s iniciais, mudança
   visual a cada ≤ 5 s, CTA no fim, cada SFX nascido de um evento visível, SFX abaixo da voz, sem som de meme.
6. **Licença clara ou não entra**; pessoa de banco nunca como paciente; saúde sem antes/depois nem promessa.
7. **Medir antes de mostrar**: QA sem ✗, folhas abertas, "áudio medido, não ouvido". Versões `_vNN`, brutos intactos.
8. **Motion via motion-studio** (rota pura). Não chamar Remotion (licença de empresa > 3 pessoas) nem HyperFrames sem
   pedido; o motor não muda a qualidade, o ofício sim.
9. Chaves de API só no `.env` (PEXELS_API_KEY, PIXABAY_API_KEY). Nunca e-mail/dado do usuário em User-Agent ou URL.

## Ambiente e escala

- Precisa: ffmpeg com libass, Python 3.10+ (numpy, opencv-python-headless, faster-whisper, pillow, fonttools, brotli,
  scipy), Node 20+ com Playwright (motion-studio). `novo.sh` confere tudo.
- Vídeo > 3 min ou 4K: rode no Mac (pasta conectada) — o container tem disco e CPU limitados. Compositor ≈ 6 q/s em 1080×1920.
- Vários vídeos do mesmo cliente: mesmo kit (`--cliente`), mesmo estilo, `PERFIL_EDICAO.md` lido antes de cortar.
