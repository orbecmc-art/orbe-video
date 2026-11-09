# Campanha — um brief, muitas versões (sem começar do zero a cada cliente)

Um founder manda o site, o logo, as cores, umas capturas e duas linhas sobre o produto. O sistema devolve **uma** peça de 12–25 s em
**3 aberturas × 3 formatos × 2 CTAs = 18 arquivos** prontos para publicar. São 18 combinações da mesma peça, não 18 filmes.
O próximo cliente passa pela mesma cadeia: brief → dados → instruções de animação → renderer → controle de qualidade → variantes → pacote.

> Se você automatizar um vídeo medíocre, vai ter muitos vídeos medíocres. **Primeiro deixe UM vídeo bom de verdade**, depois transforme textos, imagens, cores e tempos em dados.

## 1. Separe dados de animação

`campaign.json` diz **o que** sai no vídeo; o `index.html` decide **como** aparece. Trocar texto, logo, cor ou CTA não toca no código.
```json
{
  "project": "nova-lancamento", "template": "ui-morph@3", "duration": 12, "fps": 60, "bpm": 120,
  "brand":  { "name": "Nova", "url": "nova.app", "colors": { "bg": "#F7F8FA", "ink": "#111827", "accent": "#2563EB", ... },
              "fonts": { "display": "...", "ui": "..." }, "logo": "assets/logo.svg" },
  "copy":   { "button": "Começar", "metricLabel": "...", "tabs": [...], "toast": "..." },
  "claims": [ { "id": "leads", "value": 1284, "text": "1.284 leads no mês", "approved": true, "source": "planilha do cliente, out/2026" } ],
  "scenes": [ { "id": "hook", "start": 0, "end": 2.5 }, ..., { "id": "cta", "start": 10, "end": 12 } ],
  "hooks":  [ { "id": "problema", "lines": ["Leads", "esfriando?"] }, { "id": "resultado", "lines": ["+38%", "de retenção"], "claim": "retencao", "style": "number" }, ... ],
  "ctas":   [ { "id": "teste", "text": "Teste grátis" }, { "id": "demo", "text": "Agende uma demo" } ],
  "formats": ["9x16", "1x1", "16x9"],
  "audio":  { "music": "audio/music.wav", "style": "tech", "musicDb": -4 },
  "approval": { "copy": false, "by": "", "date": "" }
}
```
Aberturas que funcionam: **o problema** · **o resultado** (número aprovado) · **a feature que surpreende**.
CTAs: um de baixo atrito ("Teste grátis") e um de alto valor ("Agende uma demo").

## 2. Contrato de variantes (o que torna o lote barato)

- O **gancho** só pode afetar `t < fim da cena "hook"` e precisa ter sumido 1 frame antes da fronteira.
- O **CTA** só pode afetar `t ≥ início da cena "cta"`.
- O miolo é idêntico em todas as variantes → renderizado **uma vez por formato**.
- `campaign.mjs validate` confere isso **por hash de pixels** em frames do miolo e das duas fronteiras, para cada gancho e CTA.

Resultado: por formato, 3 segmentos de gancho + 1 miolo + 2 segmentos de CTA, concatenados sem re-encode. 6 vídeos custam ~1,6 vídeo de render. Segmentos ficam em cache por hash (html + motion.js + fontes + campanha + ajustes): mudou só o CTA → só o CTA re-renderiza.

## 3. Validação antes de gastar render (`node scripts/campaign.mjs validate`)

Recusa o brief se:
1. Faltar asset (logo, trilha) ou a fonte não estiver em `fonts/fonts.css` (cai no fallback do sistema).
2. Um texto não couber no formato (`window.VALIDATE()` do filme mede cada gancho e CTA em 9:16, 1:1 e 16:9) ou ficar no ar menos que 0,5 s + 0,3 s/palavra.
3. Um `CHECK` numérico falhar (cursor parado no clique, indicador chegou na aba, contador terminou no valor...).
4. **Algum número na copy não vier de um claim aprovado com fonte.** "Aumenta a conversão em 240%" tem que vir do cliente, nunca do modelo. Melhor recusar o brief do que entregar um vídeo lindo com uma mentira dentro.
5. Claim de EXEMPLO ainda no arquivo, ou `approval.copy ≠ true` (o cliente aprova o que o vídeo **diz** antes do render final).
6. O contrato de variantes quebrar.
`--draft` rebaixa (5) a aviso para rascunho interno — nunca para entregar.

## 4. Render, auditoria e pacote

```bash
node scripts/campaign.mjs render --draft                 # rascunho: 30 fps, sem blur, jpeg (rápido) — para o board e o cliente aprovar
node scripts/campaign.mjs render                         # final: fps da campanha, motion blur 4 subframes
node scripts/campaign.mjs render --formats 9x16 --hooks problema --ctas demo   # só o que mudou
node scripts/campaign.mjs package                        # out/delivery/<projeto>_<data>/ + .zip
node scripts/campaign.mjs all                            # validate → render → package
```
Para cada variante: SFX nivelado contra a trilha (picos em frame+1), mix −14 LUFS, capa (.jpg). Por formato: `qa.sh` na 1ª variante. Auditoria de áudio da 1ª variante (`out/qa/audio.md`).

**Pacote de entrega**: `<formato>/<projeto>_<formato>_<gancho>_<cta>.mp4` + `_capa.jpg`, `manifest.json` (hash SHA-256 de cada arquivo, duração, resolução, LUFS, hash da campanha e do template, ajustes de render, versões das ferramentas, claims e aprovação), `LEIA-ME.md` para o cliente (onde usar cada formato), `campaign.json`, `validate.md`, `audio.md` e o `.zip`.
O manifesto evita entregar um vídeo com o logo velho e responde "qual versão é essa?" meses depois.

## 5. Biblioteca de cenas revisadas (a mudança para ir a sério)

Não deixe o modelo redesenhar componentes de marca a cada campanha. Monte uma coleção de **templates revisados** (`ui-morph@3`, `dashboard@1`, `kinetic-explainer@1`...) e deixe o Claude **escolher e configurar** via `campaign.json`. A qualidade de design continua dependendo do template, mas o processo sai igual toda vez.
Primeira versão séria: um vídeo de referência polido, a biblioteca de cenas, o `campaign.json` validado, um comando de render, contact sheet, 3 formatos e estrutura de entrega clara.

## 6. Prompt de partida (Claude Code)

```
Use a skill motion-studio no modo campanha. Projeto: [pasta]. Produto: [NOME] ([URL]).
1. Inspecione o site e os assets aprovados em ./assets; liste o que encontrou.
2. Preencha campaign.json: marca, copy, 3 aberturas (problema · resultado · feature), 2 CTAs, formatos 9x16/1x1/16x9.
   Todo número dito no vídeo vem de "claims" com fonte do cliente — se não houver, NÃO invente: deixe a abertura sem número.
   A fonte (`source`) é registro, não texto de tela: vai para o manifest/LEIA-ME e a legenda do post (regra Orbe).
3. Rode campaign.mjs validate --draft e o board (stills.mjs --board) para cada formato. Me mostre o board e a validação.
4. Depois do meu OK (approval.copy = true): campaign.mjs all. Não diga que terminou sem ter aberto o contact sheet,
   o audio.md e uma variante de cada formato. Me entregue um relatório: segundos revisados, problemas, o que consertou,
   o que ainda preocupa.
```
