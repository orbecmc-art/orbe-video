---
name: legendar
description: "Comando /legendar — só legenda (e, se pedir, limpa o áudio e reenquadra) um vídeo gravado, sem cortes, motion ou trilha. Legenda palavra a palavra com destaque ou por frase, no estilo da marca, queimada no MP4 + arquivo .srt. Use quando o usuário digitar /legendar ou pedir \"só coloca legenda nesse vídeo\"."
---

# /legendar — legenda rápida

Use a skill **edita-video** (pasta irmã `../edita-video`, `S=<ela>/scripts`) no modo enxuto.

1. Perguntas (uma rodada de `AskUserQuestion`): **estilo da legenda** (palavra a palavra com destaque · frase
   sóbria) · **formato** (manter o original · 9:16 com reenquadramento no rosto · 4:5) · **cortar silêncios?** (não,
   só legenda · sim, limpar pausas e vícios) · **cor de destaque/marca** (kit do cliente · amarelo · outra).
2. Projeto e briefing (sem motion, sem trilha, sem SFX, sem zoom):
   ```bash
   bash $S/novo.sh <pasta> [--cliente <kit>] --brutos <video>
   python3 $S/briefing.py <pasta> formato=<9x16|4x5|16x9> estilo=educativo legendas=<palavra|frase> motion=nenhum \
     broll=nenhum sfx=nao trilha=nenhuma sem_cortes=<sim|nao> ajuste.camera.zoom_alterna=[1,1] ajuste.camera.punch=0 \
     ajuste.camera.push=0 termos="<nomes>"
   ```
   Formato original horizontal mantido: `formato=16x9` (sem reenquadrar). Cor da palavra ativa:
   `ajuste.legendas.destaque="#FF5A4B"`.
3. `python3 $S/preparar.py <pasta>` → `python3 $S/cortes.py <pasta>` (com `sem_cortes=sim` mantém tudo) →
   `python3 $S/rosto.py <pasta>` → `python3 $S/camera.py <pasta>` → `python3 $S/legendas.py <pasta>` → leia
   `docs/LEGENDAS.md` e corrija grafias (`--corrigir "#12=Rafael"`) → `python3 $S/final.py <pasta>`.
4. Abra a folha do QA (legenda legível no celular, fora da zona da interface) e entregue o MP4 + .srt.
