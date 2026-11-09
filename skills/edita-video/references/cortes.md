# Cortes — o ofício em números

Fontes: LeiteZ (fluxo-de-edicao), video-use, HyperFrames media-use, auto-editor/vcut, pesquisa short-form 2025–26.

## Ler antes de cortar
- `docs/FRASES.md` é o vídeo em texto: `F005 [c1 6.93–10.25] #13–#27 texto (pausa 1.5 s)`. *itálico* = hesitação,
  `~palavra~` = transcrição incerta (confira na folha/ouvido do cliente). Decida por aqui; não assista o bruto inteiro.
- Notas faladas de edição ("corta isso", "de novo", "vou repetir", "pera") são instruções, não conteúdo.

## O que sai sozinho (cortes.py)
| Caso | Regra |
|---|---|
| Hesitação inequívoca (éé, ãh, hum, ahn) | sai sempre |
| "é", "um", "tipo", "né", "então", "assim", "aí", "sabe", "bom", "enfim" | só se ISOLADO por pausa ≥ 0,15 s dos dois lados; senão fica (é palavra) |
| Regravação (retake) | frase parecida (≥ 0,85, ≥ 4 palavras) com uma das 3 seguintes → fica a ÚLTIMA (a pessoa refez porque errou). Se a última tropeça e a anterior está limpa, a anterior (marque) |
| Falso começo | frase curta/sem fechamento cujas 2–3 primeiras palavras abrem a seguinte → sai |
| Pista falada | "de novo", "vou repetir", "pera", "corta", "não, não" → sai e marca dúvida |
| **Nota falada** | "abre nota … fecha nota" / "nota pro editor … fim da nota" / "Claude, coloca…" no começo da frase → sai do vídeo e vira instrução (docs/NOTAS_FALADAS.md, âncora = palavra seguinte). Sem "fecha", vai até o fim da frase e marca dúvida. Ensine o cliente a gravar assim: "abre nota: aqui entra o print do Pix, fecha nota" |
| Similaridade 0,60–0,85 | NÃO corta: vira dúvida em CORTES.md |
| Silêncio | encurta para pausa_max; folga 60–100 ms antes da 1ª sílaba e 100–150 ms depois da última (não come s/t finais) |
| Bordas | refinadas no mínimo de energia ±40 ms e encaixadas no quadro; fade 20–30 ms em toda borda interna |
| Trecho < 0,2 s | some (vira clique visual) |

## Pausa por estilo (pausa_max)
dinâmico 0,30 · podcast P&B 0,32 · educativo 0,35 · base 0,40 · clínica 0,45 · luxo 0,50. **Picotado** (estilo
Autocut, pedido "corta todo respiro"): `ajuste.cortes.pausa_max=0.10` — corta todo vão > 100 ms entre falas; use só em
fala rápida e decidida (em fala pausada vira gagueira). Estalos de boca (ou "possível clique" no QA):
`ajuste.som.estalos=true` (adeclick na voz). Entre ideias (fim de frase) deixe ar de
0,08–0,20 s (ar_frases) — sem ar o vídeo fica "metralhadora" e a legenda não respira.

## Condensar para a duração alvo
Limpeza raramente chega no alvo quando o bruto é 2× maior. Aí é EDIÇÃO de conteúdo:
1. Liste as ideias (frases F###) e marque: gancho · promessa · prova · exemplo · CTA.
2. Proponha 2 opções ("A: tira F009 e F012 → 29 s; B: tira F007 e o exemplo F014 → 31 s").
3. Aplique: `cortes.py . --remover F009,F012`. Nunca corte no meio da frase; nunca reordene sem pedir
   (reordenar é possível: peça e faça por trecho, mas confirme — muda o sentido).
4. Gancho nos 3 s iniciais: se a melhor frase está no meio, pergunte se pode abrir com ela (cold open).

## Depois de aprovado
`estado.py . aprovar cortes` → TRAVA. Motion, câmera, legenda e som dependem dos tempos; mudar corte depois
obriga refazer mapa/motion (avise antes de aceitar "só mais um corte").
Ajustes finos sempre por índice: `--remover 41-43` / `--manter 42` (persistem em `_edit/cortes_ajustes.json`).
