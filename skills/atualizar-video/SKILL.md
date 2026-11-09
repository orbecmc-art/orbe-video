---
name: atualizar-video
description: "Rotina de atualização do plugin orbe-video (edita-video + motion-studio). Use quando o usuário pedir para atualizar as skills de vídeo, juntar os aprendizados das últimas edições, checar mudanças de plataforma (zonas seguras do Reels/TikTok, specs), licenças de bancos de imagem e música, versões das ferramentas, ou digitar /atualizar-video. Propõe as mudanças com diff para aprovação."
---

# /atualizar-video — a skill melhora a cada entrega

Nada é aplicado sem aprovação: o produto é um **diff proposto** por arquivo.

## 1. Aprendizados (o principal)
- Leia `~/.config/orbe/edita-video/APRENDIZADOS.md` (ofício, gravado por `estado.py aprendizado --oficio`) e os
  `docs/APRENDIZADOS.md`/`docs/DIARIO.md` dos projetos recentes (pasta conectada `estudio/edicoes/`).
- Agrupe por etapa (cortes, mapa, câmera, legendas, som, cor, QA). Repetiu em 2+ projetos → vira regra/número no
  reference da etapa. Gosto de um cliente só → fica no `PERFIL_EDICAO.md` do kit dele, não na skill.
- Marque como `[x]` os aprendizados incorporados.

## 2. O que muda no mundo (fonte primária, com data)
| Item | Onde checar | Arquivo |
|---|---|---|
| Zonas seguras e specs de Reels/TikTok/Shorts | central de ajuda/guia de criadores das plataformas | `edita-video/references/legendas.md`, `motion-studio/references/look.md` |
| Termos das APIs Pexels/Pixabay/Openverse/Commons | páginas de licença e API | `edita-video/references/motion-e-broll.md` |
| Publicidade médica (CFM/CFO/Anvisa) | resoluções oficiais | `edita-video/references/conformidade.md` |
| Licença Remotion / HyperFrames | sites oficiais | `conformidade.md`, `motion-studio/references/toolchain.md` |
| faster-whisper, OpenCV (YuNet), ffmpeg, Playwright | changelogs/PyPI/npm | `novo.sh`, scripts |

## 2b. Galeria de estilos
Estilo de EDIÇÃO novo: preset em `edita-video/assets/estilos.json` + mapa do estilo em `<projeto>/_edit/mapas/<estilo>.json`
→ `python3 edita-video/scripts/vitrine.py <projeto> --estilos <novo>` (o MESMO vídeo da vitrine atual) →
`python3 galeria/gerar.py --vitrine <projeto>/entregas/vitrine`. Estilo de MOTION novo: exemplo curto em
`galeria/videos/m-<id>.mp4` (≤ 16 s, 640 px) + entrada em `galeria/motion.json`. Republique no MESMO link de
`galeria.json` (Artifact publish com `url`) e reempacote o plugin (a pasta `galeria/` vai junto).
Ficha de motion nova: `motion-studio/estilos/<id>/ESTILO.md` no formato das outras (mecanismo, batidas, paleta,
metas de movimento medidas com `pericia_movimento.py`).

## 3. Teste de regressão
Rode um projeto curto do início ao fim (preparar → cortes → mapa com 2 peças → final) e confira o `docs/QA.md` sem ✗
e as folhas. Algo quebrou com versão nova de ferramenta → conserte o script antes de propor.

## 4. Propor e aplicar
Mostre por arquivo: trecho atual → trecho novo → motivo/fonte. Aprovado: edite os arquivos do plugin, suba a versão em
`.claude-plugin/plugin.json` (1.x.y), registre no Changelog do README e reempacote o plugin (skill cowork-plugin) para
reinstalar.

## Antes de empacotar (sempre)
`python3 skills/atualizar-video/validar.py` — regras do app (descrição do plugin ≤ 500 caracteres, descrição de skill
entre aspas e ≤ 1024, name = pasta, tamanho e nº de arquivos). Só empacote com "✔ pronto para empacotar"; depois
`zip -qr /tmp/orbe-video.plugin . -x "*/__pycache__/*" -x "*.DS_Store"`.
