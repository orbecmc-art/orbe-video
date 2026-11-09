# Regras da casa — estúdio de motion em código

Este projeto foi criado pela skill **motion-studio**. Estas regras valem para todo filme feito aqui.

## Contrato de render
- Rota pura: um index.html, `window.seek(t)`, Playwright + ffmpeg. Não use HyperFrames, Remotion ou outra skill de vídeo, salvo pedido explícito.
- Este é um projeto NOVO: não abra nem copie filmes de outras pastas.
- Todo filme é função pura do tempo: `window.seek(t)` pinta o frame t. `lib/motion.js` tem springs, tracks, ruído, tipografia.
- Sem transições CSS, setTimeout, requestAnimationFrame no render, estado entre frames. Ruído com semente (`M.rng`), nunca Math.random.
- Valores discretos (contadores, troca de texto) usam `M.frameT`/`M.count`.
- DADOS ≠ ANIMAÇÃO: marca, copy, claims, ganchos e CTAs vêm de `campaign.json`. O gancho some antes do fim da cena "hook"; o CTA só aparece a partir da cena "cta".
- Tokens de movimento (`M.EASE`, `M.springZ`, `M.MS`, `M.STAGGER`): nenhum número de easing solto nas cenas.
- Render: `node scripts/render.mjs` → H.264 yuv420p CRF 16. Formatos pelo `--format`.

## Look
- Proibido por padrão: título centralizado sobre gradiente, tudo entrando com fade, rótulos de canto e bordas de quadro,
  glow em UI, explosões de partículas genéricas, easing com quique em UI (lista completa: references/look.md da skill).
- Uma fonte display, uma de UI, um acento (a menos que a marca diga outra coisa). Fontes locais via `scripts/fonts.sh`.
- Algo novo a cada 2–4 segundos. Herói ≥ 40% do quadro. Legenda/texto principal ≥ 5,2% do lado curto (auxiliar ≥ 2,6%). O 1º corte sai um degrau mais lento (oficio.md R1).
- UI e dados reais apenas. Nunca invente telas, números ou depoimentos. Todo número dito no vídeo vem de um claim aprovado com fonte.
- **Fonte/crédito NUNCA na tela** (regra Orbe): nada de tarja de fonte no canto, rodapé "Fonte: …" ou crédito de foto. A fonte fica no campaign.json, no LEIA-ME e na legenda do post. Só na tela se pedirem.
- Texto ≥ 0,5 s + 0,3 s/palavra no ar · contraste ≥ 4,5:1 · ≤ 3 flashes/s.

## Som
- Trilha e SFX sintetizados em código (`scripts/music.mjs`, `scripts/sfx.mjs --page index.html --bed audio/music.wav`) a menos que uma faixa seja fornecida.
- Pico de cada som em evento + 1 frame (luz antes do som). Hits 3–6 dB acima da trilha. Banda de celular a ≤ 5 dB da cheia.
- Com faixa: `scripts/beats.py` → `audio/beats.json`; mudanças nas batidas, cortes nos downbeats, SFX nos picos.
- Mix em −14 LUFS (`scripts/mix.sh`), MP4 decodificado ≤ −1 dBTP. Confira com `python3 scripts/audit-audio.py`. A entrega diz: áudio medido, não ouvido.

## Antes de me mostrar qualquer coisa
0. Tabela de estados na grade de batidas (docs/STORYBOARD.md) aprovada; `window.SHOTS` e `window.CUES` no mesmo timeline.
1. `node scripts/stills.mjs --board` → out/board.html (um frame por estado; resolva todo ⚠ de texto curto).
2. `node scripts/stills.mjs --beats audio/beats.json` (ou `--every 0.5`) e OLHE a contact sheet.
3. Pontue 1–10: gancho nos 2 primeiros s · leitura no celular · qualidade do movimento · variedade · composição · marca · sincronia · anti-slop.
4. Conserte os 3 piores problemas (notas P0/P1/P2 em docs/REVIEW.md). Repita até tudo ≥ 8.
5. `node scripts/stills.mjs --checks` (auditoria numérica) e, em transições, `--strip`/`--onion`/`--graph`.
6. Só então o render completo, mix, `scripts/qa.sh out/final.mp4` (inclui a varredura de pops) e `scripts/audit-audio.py`.
7. Relatório: frames revisados · problemas · o que consertei · o que ainda preocupa. Registre prompts e follow-ups em docs/PROMPTS.md.

## Campanha (variantes)
- `node scripts/campaign.mjs validate` → `render` (`--draft` para rascunho) → `package`. Nunca entregue com claim de EXEMPLO ou `approval.copy` falso.

## Depois da aprovação
- `bash scripts/brand.sh save . <estudio/brands/cliente>` e atualize o BRAND.md com o que foi aprovado + feedback do cliente.

## BANNED deste projeto (cresce a cada filme)
- 
