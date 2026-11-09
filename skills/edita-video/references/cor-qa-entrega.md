# Cor · QA · Entrega

## Cor (compor.py)
1. **Correção antes de estilo**, automática por clipe (10 quadros, signalstats): contraste 1,00–1,08 se a faixa de luma
   < 0,65; gama 1,08/1,04 se escuro (< 0,36/0,42), 0,97 se claro (> 0,62); saturação 1,04 se < 0,18, 0,96 se > 0,40.
2. **Preset do estilo** (`cor.preset`): `natural` (clínica, educativo) · `punch` (dinâmico) · `cinema` (luxo) ·
   `produto` (varejo) · `quente` · `frio` · `nenhum`. LUT do cliente: `ajustes.cor.lut = "assets/marca.cube"`.
3. HDR do iPhone (HLG/PQ) vira SDR com tonemap no preparar; Apple Log → LUT oficial da Apple como `lut`.
Pele é a referência: nunca laranja/magenta; na dúvida, menos. B-roll recebe a mesma correção (combina com o A-roll).

## QA (qa_edicao.py — final.py roda sozinho)
✗ bloqueia: duração · loudness/pico · **voz no mix** (retranscrição ≥ 88%) · arquivo sem áudio.
⚠ relata: clique nas emendas · preto/congelado · legenda na zona da UI ou sobre peça · rosto fora do recorte ·
> 5 s sem mudança visual · sincronia dos SFX (pico medido no MP4) · banda de celular.
Depois do relatório, **ABRA as duas folhas** (`docs/folhas/<versão>_folha.jpg` e `_cortes.jpg`) e faça a revisão:
`P0/P1/P2 · tempo · onde · problema → mudança exata`. P0 = errado (palavra errada, legenda cobrindo peça, flash,
rosto cortado, fonte na tela) · P1 = fraco · P2 = polimento. Corrija P0/P1, até 3 rodadas por versão.
Peça de cliente importante: revisor em contexto limpo (subagente recebe só o MP4/folhas + briefing e devolve P0/P1).

## Entrega
- `renders/<nome>_vNN.mp4` (H.264 High, AAC 256k, BT.709, faststart) · `.srt` · capa 9:16 + recorte 3:4 do grid ·
  stems em `audio/` · `docs/CREDITOS.md` (licenças; CC BY → crédito na legenda do post).
- Mensagem ao cliente/Gabriel em 3–4 linhas: o que foi feito · o que foi medido (áudio medido, não ouvido) · o que
  ainda preocupa · como pedir ajuste ("mo04 entra antes", "sfx07 mais baixo", "L012 é 'três', não 'tais'").
- Página para aprovação (opcional): publique o MP4 numa página de player (Artifact) com os IDs listados.
- Outro editor (Premiere, Final Cut, DaVinci, CapCut, celular): `nle.py .` → kit aberto (references/multiplataforma.md).
- Cliente revisa no navegador: `revisao.py .` → Artifact com pedidos por número → `pedidos.py .` aplica.
- Com referência no projeto, o `final.py` roda a **perícia de movimento** (`pericia_movimento.py .` → docs/MOVIMENTO.md):
  amplitude (pico ÷ mediana), % em quase-parada e picos do nosso vídeo × metas tiradas da referência. É alvo, não
  bloqueio; reprovado = uniforme demais → escolha UMA batida para socar e deixe as vizinhas respirarem.
- Aprovado: `estado.py . aprovar v0N` e registre o que aprendemos:
  `estado.py . aprendizado "cliente prefere legenda frase" --gosto` (vai para o kit dele) ·
  `estado.py . aprendizado "punch a cada 3 s cansa em vídeo > 60 s" --oficio` (vale para todos; com 3+ de ofício,
  proponha atualizar esta skill — ela melhora a cada entrega).
