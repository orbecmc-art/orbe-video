# Câmera virtual — reenquadrar, zoom e punch-in

`rosto.py` acha o rosto (YuNet; Haar sem o modelo) a cada 3 quadros; `camera.py` gera o recorte quadro a quadro.

## Reenquadrar 16:9 → 9:16
- Recorte = maior janela com o aspecto da saída. 1080p → 608×1080 (upscale 1,78×). Peça 4K quando der: zoom de
  verdade sem amolecer. Com upscale > 1,4× entra nitidez leve; > 2,2× o camera.md avisa.
- Olhos a 36% da altura do recorte (30–38%). Zona morta de 10% da largura (1 pessoa) — o quadro NÃO persegue
  micro-movimento; mola criticamente amortecida (suavidade 0,35–0,8 s). Pan ≤ 5–8% da largura por segundo.
- Corte = câmera pode SALTAR (o corte esconde); dentro do trecho, só desliza. Nunca inverte direção num corte.
- Sem rosto (produto, carro, tela): mantém o último enquadramento bom ou o centro; para planos sem pessoa, use
  `--sem-reenquadrar` (encaixe inteiro) ou mande como B-roll.

## Zoom por corte (disfarça o jump cut)
- Corte "pulo" (mesmo clipe, tempo pulou): alterna zoom_alterna (100% ↔ 110–114%). Mudança < 5% não conta.
- Push lento dentro do trecho: +2–4% (ease out). Luxo 4%, dinâmico 2% (o punch faz o trabalho).
- Punch-in de ênfase: +4,5–8% em 0,18 s, segura até o próximo corte. Palavra = número, "nunca/sempre/primeiro…",
  pico de energia da voz, ou pedida (`--punch-palavras 12,40` / `enfase_palavras` no mapa). ≥ punch_intervalo
  entre punches (dinâmico 3 s, educativo 4 s, clínica 8 s, luxo nenhum); nunca nos 0,5 s depois de um corte.
- Zoom total ≤ max_zoom (1,22 em fonte 1080p; 1,5–2,0 em 4K).

## Pedidos comuns → comando
| Pedido | Faça |
|---|---|
| "menos zoom" | `camera.py . --zoom-max 1.12` ou ajustes.camera.zoom_alterna [1.0, 1.06] |
| "tira o punch" | `camera.py . --sem-punch` |
| "zoom no 'nunca'" | ache o #índice em FRASES.md → `--punch-palavras 57` |
| "cam07 mais fechado" | ajuste zoom_alterna ou punch daquele trecho (camera.json plano cam07) |
Revisão: docs/CAMERA.md (cam01… com zoom, pulo e punch por trecho).

## J-cut (opcional)
`cortes.jcut` = 2–4 quadros: o som do trecho novo entra antes e a imagem do anterior segura esses quadros. Suaviza o
pulo do jump cut em estilo calmo/cinematográfico; em dinâmico o corte seco é a linguagem (deixe 0). Liga com
`briefing.py . ajuste.cortes.jcut=3`; `compor.py --sem-jcut` desliga numa rodada. O kit de NLE vai sem J-cut (o editor
faz no programa dele).
