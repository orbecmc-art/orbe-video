# Fluxo — as 8 etapas (base LeiteZ) com 4 portões de aprovação

Edição como DADO: tudo o que a edição decide vive em `_edit/*.json` com IDs estáveis (`s001` trecho, `mo04` motion,
`br02` B-roll, `cam07` câmera, `L012` legenda, `sfx12` som, `#123` palavra). O render é determinístico: mudar uma
decisão = editar um JSON/um comando + re-render. Pedido do cliente por número ("mo04 entra antes", "sfx07 mais baixo").

| Etapa | O que acontece | Comando | Portão |
|---|---|---|---|
| 0. Briefing | perguntas fixas + referência | `briefing.py`, `referencia.py` | — |
| 1. Iniciar | pasta do projeto, ambiente, modelos | `novo.sh` | — |
| 2. Preparar | inventário (VFR/HDR/rotação), mezanino CFR, transcrição por palavra, FRASES.md | `preparar.py` | — |
| 3. Cortes | vícios, falsos começos, regravações, pausas; bordas por energia | `cortes.py` → `final.py --rascunho` | **① cortes** (TRAVA) |
| 4. Mapa | motion, B-roll, fotos, ênfases ancorados em palavras | `mapa.py rascunho` → `mapa.json` → `mapa.py` | **② mapa** |
| 5. Assets | busca com licença, folhas numeradas, escolha, conformação | `ativos.py buscar/escolher/conformar` | (escolha das folhas) |
| 6. Motion | peças no motion-studio (alfa), board sobre o vídeo real | `motion_ponte.py preparar/board/render` | (board) |
| 7. Câmera | rosto (YuNet), reenquadrar 9:16, zoom alternado, punch, push | `rosto.py`, `camera.py` | — |
| 8. Som | SFX por evento, trilha com ducking, voz limpa, −14 LUFS | `eventos.py`, `audio.py` | — |
| Final | legendas + composição + mix + SRT + capa + QA + folhas | `legendas.py`, `final.py` | **③ v01** |
| Entrega | ajustes por número → v02…; revisão no navegador; kit para qualquer editor; aprendizados | `revisao.py`, `pedidos.py`, `nle.py`, `estado.py aprendizado` | **④ aprovado** |

## Portões (o que mostrar e esperar)

① **Cortes** — `docs/CORTES.md` (antes → depois em segundos, cada remoção com motivo) + o rascunho (`final.py --rascunho`,
   2–3 min). Pergunta única: "Os cortes estão ok? Algo que saiu e devia ficar?" Aprovado → `estado.py aprovar cortes`
   (trava: daqui pra frente nada mexe nos tempos sem `--forcar`).
② **Plano / mapa** — a proposta do Claude vira a **página de plano** (`plano.py .` → Artifact): roteiro linha a linha,
   tipo de cena (Legenda · Legenda + UI · Meia tela · Tela cheia), design e nota; a pessoa ajusta e aprova
   (`plano.py . ler` / `aplicar`). Sem tempo para página: `docs/MAPA.md` + `docs/folhas/motion_board.jpg` no chat.
   Para cliente exigente, ofereça 2 direções de motion. Aprovado → assets e render.
③ **v01** — o MP4 + 3–4 linhas: o que foi feito, o que preocupa, o que foi medido (áudio medido, não ouvido).
④ **Aprovado** — export, entrega e o que aprendemos (gosto → kit do cliente; ofício → APRENDIZADOS de ofício).

Pessoa ausente / tarefa agendada: siga sem os portões ①②, registre "assumi: …" no DIARIO e pare na v01.

## Continuidade entre sessões

- Ao abrir um projeto: `python3 <skill>/scripts/estado.py .` → diga em 1 frase onde parou e o próximo passo.
- Decisões e porquês: `estado.py . nota "…"` (docs/DIARIO.md). O projeto lembra; a conversa não precisa.
- Contexto pesado: termine a etapa, salve o estado, pode limpar o contexto — o próximo passo está no `estado.py`.

## Princípios (valem em toda etapa)

1. **Ler, não assistir**: decida pelo texto (`docs/FRASES.md`, índices de palavra); olhe imagens só nos pontos de
   decisão (folhas de contato, board, folhas do QA). Nunca descreva um quadro que não abriu.
2. **Na dúvida, não corta — marca.** Remoção duvidosa vira item em CORTES.md para o humano decidir.
3. **Nunca troca o que foi dito pelo roteiro.** A transcrição é a verdade; correção de grafia não mexe no tempo.
4. **Versão nova nunca sobrescreve** (`_v01`, `_v02`); brutos nunca são alterados.
5. **Adjetivo vira número** ("mais dinâmico" → pausa_max 0,30, punch a cada 3 s, legenda 2 palavras).
6. **O conteúdo decide o motion**: a peça nasce da fala ("serviria para qualquer vídeo?" → então não é boa).
7. **Medir antes de mostrar**: QA com zero ✗, folhas abertas, áudio medido. Máximo 3 rodadas de conserto por versão;
   depois, reporte o que falta.
8. **Fontes fora da tela** (regra Orbe), licenças registradas, nada de pessoa de banco como paciente.
