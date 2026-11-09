---
name: exportar-video
description: "Comando /exportar-video — leva um vídeo editado pelo Claude para onde a pessoa quiser continuar - Premiere Pro, Final Cut Pro, DaVinci Resolve, CapCut, celular (Edits, CapCut mobile), Canva ou uma página de revisão no navegador onde o cliente comenta e aprova. Gera o kit aberto (trechos reenquadrados, coberturas, motion e legendas com alfa, stems, LUT, linhas do tempo XML/OTIO/FCPXML/EDL/rascunho CapCut) e, com o editor conectado, opera ao vivo (Edit Link, premiere-pro-mcp, DaVinci MCP). Use quando digitarem /exportar-video ou pedirem \"manda para o Premiere/Final Cut/CapCut\", \"quero editar no meu programa\", \"projeto aberto\", \"XML\", \"o cliente quer revisar\"."
---

# /exportar-video — o mesmo vídeo, em qualquer editor

Use a skill **edita-video** (pasta irmã `../edita-video`, `S=<ela>/scripts`). Leia antes
`../edita-video/references/multiplataforma.md`. Pré-requisito: projeto com versão renderizada (`final.py`); se não
tiver, rode a edição antes (`/editar-video`).

## 1. Uma pergunta (AskUserQuestion, multiSelect)
**Onde vai continuar?** Premiere · Final Cut · DaVinci Resolve · CapCut · Celular (Edits/CapCut mobile) ·
Revisão do cliente no navegador. Se ainda não disse: **o kit vai para qual computador?** (o Mac do editor → caminho
absoluto da pasta, para `--base`). Zoom gravado ou o editor anima? (padrão: gravado).

## 2. Kit
```bash
python3 $S/nle.py <proj> --para <premiere,finalcut,resolve,capcut,celular> --base "<caminho no Mac>" [--sem-zoom] [--legendas-fcp]
```
- Confira a saída: FCPXML validado (✓ DTD), contagem de trechos/coberturas/motion, avisos. Abra 2–3 quadros de
  `midia/s###.mov` e de `legendas_alpha.mov` sobre fundo xadrez para ver alfa e enquadramento.
- Leve o kit para o computador: pasta conectada → `device_commit_files` para o `--base` exato (os XML apontam
  para lá); sem pasta conectada → zip com `SendUserFile` e avise que o editor reconecta a mídia apontando `midia/`.
- Entregue o `LEIA-ME.md` do kit (passo a passo por editor) junto.

## 3. Ao vivo (se o editor estiver conectado à sessão)
Procure as ferramentas (ToolSearch: "premiere", "edit link", "resolve", "fcp"). Regras: ponto de restauração antes;
confirmar antes de apagar; conferir olhando quadros, não só pelo "ok".
- **Premiere + Edit Link / premiere-pro-mcp:** `import_fcp_xml(<kit>/premiere/<nome>.xml)` → importar
  `legendas.srt` como faixa de legenda → LUT `cor_<preset>.cube` se o editor quiser o look editável → `see_frames`
  em 3 pontos (gancho, meio, CTA) → reporte.
- **DaVinci Resolve 21.1 Studio (MCP nativo) / davinci-resolve-mcp:** importar `resolve/<nome>.otio` → conferir →
  render se pedirem.
- **Final Cut Pro (Mac ligado à sessão):** `open -a "Final Cut Pro" "<kit>/finalcut/<nome>.fcpxml"`; com
  `fcp-mcp-server` instalado, `push_to_fcp`.
- **CapCut:** sem API; com o computador ligado: fechar o CapCut, copiar `capcut/<nome>/` para a pasta de rascunhos
  (ver multiplataforma.md), abrir. Recusou → `capcut/ROTEIRO.md` (montagem manual em ~10 min).
- **Canva (conector):** só com pedido explícito — subir MP4 final e camadas para a biblioteca.

## 4. Revisão no navegador (cliente)
```bash
python3 $S/revisao.py <proj>        # → entregas/revisao_vNN/index.html + proxy.mp4
```
Publique com Artifact: `file_path` = index.html, `files` = {"proxy.mp4": <caminho>}, `capabilities` =
{"db": {}, "user": {"scopes": ["profile"]}}, `icon` "video". Diga para compartilhar com o cliente como
**Colaborador** (só leitura não grava pedido). Depois:
1. `ArtifactData list` na coleção `pedidos` → salve os de status "novo" em `<proj>/_edit/pedidos.json`.
2. `python3 $S/pedidos.py <proj>` → aplica legenda/som/peça/corte; comentários livres vão para `docs/PEDIDOS.md`
   (interprete e aplique à mão); aprovação marca o estado.
3. Rode o que ele mandar refazer (ordem impressa) → `final.py` → nova versão → `revisao.py` de novo
   (mesma página: republique no mesmo arquivo ou passe `url`).
4. `ArtifactData batch` marcando os ids de `_edit/pedidos_aplicados.json` com `status: "aplicado"`.

## 5. Fechar
Uma linha por destino: o que foi entregue e onde (caminho no Mac / link da página), o que não viaja (J-cut fica com o
editor; CapCut é experimental) e o próximo passo.
