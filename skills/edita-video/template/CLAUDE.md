# Projeto de edição (edita-video · plugin orbe-video)

Este projeto é editado com a skill **edita-video**. Ao abrir: `python3 <skill>/scripts/estado.py .` e diga em 1 frase
onde parou e o próximo passo. Decisões e porquês ficam em `docs/DIARIO.md` (`estado.py . nota "…"`).

## Pastas
- `brutos/` gravações originais (NUNCA alterar) · `broll/` planos do cliente · `referencias/` vídeos de referência
- `assets/` B-roll/fotos baixados e conformados (licenças em `docs/CREDITOS.md`) · `motion/` peças (motion-studio)
- `audio/` voz limpa, trilha, sfx, mix (stems) · `renders/` versões `_v01`, `_v02`… (nunca sobrescrever)
- `docs/` o que se lê: BRIEFING, FRASES, CORTES, MAPA, CAMERA, LEGENDAS, SOM, AUDIO, QA, CREDITOS, DIARIO, folhas/
- `_edit/` estado da máquina (JSON). Edite pelos scripts; à mão só `mapa.json`, `briefing.json` (ajustes) e
  `correcoes.json`.

## Regras deste projeto
1. Ler, não assistir: decida por `docs/FRASES.md` e pelos índices `#` de palavra; abra imagens só nas folhas.
2. Na dúvida não corta — marca. Corte aprovado TRAVA.
3. Pedidos por número: s003 (trecho) · mo04 (motion) · br02 (B-roll) · cam05 (câmera) · L012 (legenda) · sfx07 (som).
4. Nenhuma fonte/crédito na tela (regra Orbe), salvo pedido explícito.
5. Medir antes de mostrar: QA sem ✗ e as duas folhas abertas. Áudio é medido, não ouvido — diga isso.
6. Saúde: sem antes/depois, sem promessa, pessoa de banco nunca como paciente.

## Gosto deste cliente
(Copiado do kit em `estudio/brands/<cliente>/PERFIL_EDICAO.md` quando existir — leia antes de cortar.)
