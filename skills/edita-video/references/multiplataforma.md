# Multiplataforma — o Claude edita; o editor continua onde quiser

Três caminhos, do mais automático ao mais manual. Escolha pelo que a pessoa tem e quer:

| Caminho | Quando | Como |
|---|---|---|
| **1. Claude entrega pronto** | quer o vídeo final | `final.py` → MP4 + SRT + capa (padrão) |
| **2. Kit aberto (qualquer editor)** | o editor/cliente quer mexer no Premiere, Final Cut, DaVinci, CapCut ou celular | `nle.py . [--para …] --base <pasta no Mac>` |
| **3. Claude dentro do editor (ao vivo)** | a pessoa edita no Premiere/DaVinci e quer o Claude operando lá | conector MCP do editor (abaixo) + o kit |
| **Navegador** | o cliente revisa/aprova sem instalar nada | página de revisão (`revisao.py`, Artifact) · Canva pelo conector |

## 2. O kit (`nle.py`) — o mesmo vídeo, editável
- Tudo no tamanho/fps finais: **nenhum editor precisa reenquadrar**. A câmera virtual (rosto, zoom alternado, punch)
  e a cor já estão nos trechos `s###.mov`, que têm alça de 1 s de cada lado (`--alca`). `--sem-zoom` entrega só o
  seguimento de rosto, para o editor animar o zoom.
- Faixas iguais em todos: V1 A-roll · V2 coberturas (B-roll/foto/split prontos; originais em `midia/originais/`) ·
  V3 motion com alfa · V4 legendas no estilo do vídeo com alfa (+ `legendas.srt` editável) · V5 referência
  (desligada) · A1 voz limpa dentro dos trechos · A2 trilha com ducking · A3 efeitos. Marcadores com os mesmos IDs.
- `cor_<preset>.cube` (look do estilo, LUT 33³) e `guias/zonas_*.png` (Reels/TikTok/Shorts).
- **Caminhos**: os XML apontam para arquivos. Gere com `--base` = caminho onde o kit vai morar no Mac do editor
  (ex.: `/Users/gabriel/estudio/edicoes/<proj>/entregas/<nome>_v01_kit`) e entregue a pasta nesse lugar (pasta
  conectada / `device_commit_files`). Gerado no próprio Mac, o padrão já está certo. Senão: reconectar mídia.

| Editor | Arquivo | Importar | Observações |
|---|---|---|---|
| Premiere Pro | `premiere/<nome>.xml` (FCP7) · `.otio` (25.6+) | Arquivo › Importar | legendas: importar `legendas.srt` → faixa de legendas editável; LUT no Lumetri › Look |
| Final Cut Pro | `finalcut/<nome>.fcpxml` (1.10, validado na DTD da Apple) | Arquivo › Importar › XML | papéis: dialogue/music/effects; legendas: Arquivo › Importar › Legendas; `--legendas-fcp` embute como legenda SRT |
| DaVinci Resolve | `resolve/<nome>.otio` · `.fcpxml` · `.xml` · `.edl` | Arquivo › Importar › Linha do tempo | 18.5+ lê OTIO; legendas: Importar › Legenda |
| CapCut desktop | `capcut/<nome>/` (rascunho via pyCapCut, **experimental**) + `capcut/ROTEIRO.md` | CapCut fechado → copiar para `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/` | sem API oficial; 8.4+ pode recusar rascunho "de caminho não convencional" (abrir um projeto vazio criado no app e usar como modelo); 10.x pode recusar; JianYing 6+ criptografa; legendas vão NATIVAS (editáveis) |
| Celular (Edits, CapCut mobile) | `celular/` | importar no app | Edits não importa projeto: final pronto + versão sem legenda (motion e som dentro) + SRT |

## 3. Claude ao vivo dentro do editor (MCP)
Antes de agir, confira quais ferramentas a sessão tem (ToolSearch). Regras: ponto de restauração/cópia do projeto
antes de mexer; confirmar antes de apagar clipe/faixa/sequência; nunca `execute_extendscript` livre sem pedido;
verificar o resultado olhando (frames/QA), não só pelo "ok" da ferramenta.

**Premiere Pro**
- **Edit Link (Brainstorm Academy)** — o Gabriel tem: painel CEP que conecta Claude/ChatGPT ao Premiere (arquivo
  `.mcpb` para o Claude Desktop). Ferramentas úteis: `import_fcp_xml` (importa o kit inteiro), `import_media`,
  `create_markers`/`add_marker`, `create_caption_track`, `apply_lut`, `see_frames`, `export_sequence`,
  `get_active_sequence`. Opções do painel: só leitura, confirmação antes de apagar, ponto de restauração.
  Fluxo: `nle.py` no Mac → `import_fcp_xml(<kit>/premiere/<nome>.xml)` → `see_frames` para conferir → ajustes.
  Os outros painéis do pacote (Auto Silence, Auto J-Cut, Auto Sound FX, Margens, LUT Library, Beat Marker) fazem
  em Premiere o que esta skill faz no render; use-os quando o editor preferir trabalhar só no Premiere.
- **premiere-pro-mcp** (open source, MIT, `npm i -g premiere-pro-mcp`, ponte CEP; Premiere 2020–2026, mesmo
  computador) — use o pacote do npm ou o repositório original (upstream `leancoderkavy/premiere-pro-mcp`).
  **Cuidado: o GitHub está cheio de cópias com o mesmo README** (contas aleatórias) — não instale de forks.
- Adobe AI Assistant (beta, dentro do Premiere) usa modelos da Adobe, não o Claude. O conector "Adobe for
  creativity" no Claude reformata vídeo e usa apps da Creative Cloud, mas não opera a timeline local.

**DaVinci Resolve**
- Resolve **21.1 Studio** tem servidor MCP nativo (Arquivo › Configurar assistentes de IA). A versão gratuita não.
- `davinci-resolve-mcp` (samuelgursky, MIT, ~2,2 mil estrelas): Studio direto; na gratuita via script-ponte
  (`install_resolve_bridge.py`, pode deixar de funcionar). Fluxo: importar `resolve/<nome>.otio`, conferir,
  renderizar. Não escolhe take nem julga qualidade — isso é desta skill.

**Final Cut Pro**
- Não tem API de controle. Abrir o kit: no Mac (shell do dispositivo) `open -a "Final Cut Pro" "<kit>/finalcut/<nome>.fcpxml"`
  importa direto. `fcp-mcp-server` (DareDev256, MIT, PyPI) lê/gera/edita FCPXML e envia ao FCP aberto
  (`push_to_fcp`, Apple Event); também tem cópias-spam no GitHub — use o PyPI/repo original.

**CapCut**
- Sem API/MCP oficial para o Claude (a ByteDance lançou um plugin só para o ChatGPT desktop). Projetos abertos
  (VectCutAPI, capcut-cli, pyCapCut) escrevem rascunhos; mudam a cada versão do CapCut.
  Com o computador ligado à sessão: feche o CapCut, copie `capcut/<nome>/` para a pasta de rascunhos, abra.

**Navegador**
- Página de revisão (`revisao.py` → Artifact): o cliente assiste, comenta por número (s003, mo04, L012, sfx07),
  corrige palavra da legenda e aprova; o Claude lê os pedidos e aplica (ver `references/cor-qa-entrega.md`).
- Canva: com o conector do Canva, o MP4 final e as camadas podem ir para a biblioteca do Canva
  (`create-upload-url` + POST dos bytes) para ajustes no editor de vídeo do navegador — só com pedido explícito.

## O que não viaja entre editores (e como o kit resolve)
| Coisa | Resolvido como |
|---|---|
| reenquadramento e zoom com rastreio de rosto | gravado nos trechos `s###` (ou `--sem-zoom`) |
| motion (springs, máscaras, texto cinético) | ProRes 4444 com alfa por peça |
| legenda estilizada palavra a palavra | camada com alfa + SRT editável |
| Ken Burns, split, tela cheia | cobertura pronta por item (original junto) |
| ducking e nivelamento | stems no nível final |
| cor | gravada + LUT do look |
Pedido de mudança no motion/legenda/câmera? Mais rápido pedir ao Claude (por número) e reexportar o kit.
