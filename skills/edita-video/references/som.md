# Som — voz, trilha e efeitos que combinam com o que se vê

O Claude não ouve: MEDE. Toda afirmação sobre áudio vem de número (LUFS, dBTP, pico em ms, dB entre camadas).

## Voz (audio.py)
Ordem: subtrair → nivelar → caráter → teto.
| Sintoma | Filtro |
|---|---|
| ronco/grave de ambiente | passa-alta 80 Hz (voz feminina 90–120) |
| ruído constante (ar, rua) | RNNoise (`arnndn`, modelo sh) mix 0,85 se o piso > −60 dBFS; sem modelo `afftdn nr=10` |
| "caixa"/sala | −2 a −3 dB em 250–400 Hz, Q 1–1,4 |
| abafado/sem clareza | +2 a +2,5 dB em 3 kHz, Q 1–1,2 |
| sibilância | de-esser 5–9 kHz |
| dinâmica irregular | compressor 3:1, −20 dB, ataque 5 ms, soltura 120 ms |
Ruído ANTES de comprimir. Eco forte / vento / clip: limpeza tem limite — avise e sugira regravar o trecho.
Emendas: fade 20–30 ms em toda borda (sem clique; o QA confere cada emenda).

## Trilha
- Gerada em código no motion-studio (`music.mjs`, estilos tech · warm · piano · minimal · cinematic) = original, sem
  licença. Arquivo do cliente: `briefing trilha=audio/x.mp3` (licença é do cliente: registre).
- Nível: sob a fala, 19–23 LU abaixo da voz (voz −14 → trilha −33…−37 LUFS); fora da fala (vão ≥ 0,6 s, abertura,
  final) sobe até 6 dB. Ataque 0,15 s ANTES da sílaba, soltura 0,4 s. Fade in 0,4 s, out 1,5 s.
- Estilo × trilha (`som.trilha_estilo`): clínica warm · dinâmico tech · luxo cinematic · educativo minimal · varejo
  warm · minimal premium piano a −20 LU.
- Nunca MusicGen/IA de licença não comercial; nunca música "conhecida" sem licença (derruba o post).

## Efeitos (eventos.py → sfx.mjs)
- Cada som nasce de um evento VISÍVEL: peça entra (pop/whoosh), marcador varre (swish), número assenta (ding),
  item de lista (pop + tick), corte para B-roll (swish/whoosh), punch-in (swish curto), CTA (pop + bloop + chime).
- Densidade (`som.sfx_por_30s`): discreto 4–5 · moderado 7 · intenso 10–12. Desenhado ≈ 8 em 18 s; 20 = genérico.
- ≥ 0,25 s entre sons; ~0,5 s de respiro antes de impacto; mesmo tipo 3× seguidas → parente; não repetir a mesma
  amostra em ~20 s (o sfx.mjs alterna).
- Pico no evento + 1 quadro (a luz chega antes do som). Nível: 5–10 dB ABAIXO de voz+trilha (`over` −5 intenso,
  −7 moderado, −10 discreto). SFX mais alto que a voz = bug.
- Sem timbre de game/meme (moeda, buzina, "vine boom") salvo pedido.
- **Gravados soam melhor que síntese**: uma pasta com WAVs nomeados pelo tipo (`whoosh_01.wav`, `pop_soft.wav`,
  `swish_02.wav`, `ding_01.wav`, `impact_01.wav`…) em `--lib` ou `ORBE_SFX_LIB` — o sfx.mjs usa a gravação e
  sintetiza só o que faltar. Fontes: assinatura Epidemic/Artlist da Orbe, Sonniss GDC (royalty-free), freesound CC0.
- **Três famílias** (o som segue o MOVIMENTO): movimento = whoosh/paper (câmera, cena entra, transição) · texturas =
  click/tick/pop/marker (algo aparece: texto, círculo, linha riscando) · antecipação = riser + impact (só na virada,
  1–2 por vídeo). Minimal (`som.familias = minimal`): cortes viram `paper`, gráfico/linha usam `marker`.
- **Biblioteca mínima** (para gravar/comprar uma vez e pôr em `ORBE_SFX_LIB`): 5 whooshes (`whoosh_longo`,
  `whoosh_curto`, `whoosh_textura`…), 2–3 cliques (`click_curto`, `click_metal`, `click_retro`), 2–3 UI (`ui_clique`,
  `ui_sucesso`, `ui_falha`), 2 risers (`riser_grave`, `riser_metal`), 2 hits (`impact_grave`, `impact_pesado`),
  `paper_01` (folha), `marker_01` (marca-texto). Apelidos aceitos: hit→impact, ui→tick, marcador→marker, papel→paper.
- Ordem: **visual aprovado primeiro, som por último** — mexer na animação depois do som quebra a sonoplastia.
- Ajuste por número: `eventos.py . --ajuste sfx07=-3 sfx09=off sfx12=whoosh`.

## Mix e entrega
−14 LUFS integrado (redes; calmo −16), pico real ≤ −1,5 dBTP antes do AAC e ≤ −1 depois (o final.py mede o MP4).
Banda de celular (200 Hz–6 kHz) no máximo 4 dB abaixo da banda cheia. Stems em `audio/` (voz, trilha, sfx) — o
cliente troca a trilha sem pedir render.
