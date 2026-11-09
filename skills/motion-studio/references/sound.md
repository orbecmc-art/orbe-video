# Som — onde "vídeo de IA" começa a parecer filme

O Claude **não ouve**. Ele mede. Tudo aqui existe para que o som fique certo sem ser escutado — e a entrega deve dizer: *"áudio medido (BPM, picos, LUFS), não auditado de ouvido"*.

**A imagem tem que funcionar no mudo primeiro**: o feed toca sem som até alguém tocar na tela. O som é a camada que faz parecer filme — não a que explica.

### A regra de sincronia: pico do som em evento + 1 frame
A luz chega antes do som. Som **antes** da imagem parece errado mais cedo do que um pouco depois. Por isso todo hit tem o **pico medido** (não o início do arquivo) em `t_evento + 1 frame` — `sfx.mjs` e `music.mjs` já posicionam assim (`--lag-frames 1`), medindo o pico de cada som sintetizado. Um seno que começa na fase 0 pica alguns ms depois do início; um waveshaper atrasa mais ainda — medir o pico resolve os dois.
*(Isto substitui a recomendação antiga de "0–30 ms adiantado": medições frame a frame em arquivo decodificado mostraram que +1 frame é o ponto certo.)*

## 1. Dois caminhos

**A. O usuário mandou uma faixa** → meça antes de animar:
```bash
python3 scripts/beats.py audio/track.wav > audio/beats.json          # BPM, beats, downbeats, hits, energy, sections
python3 scripts/beats.py audio/track.wav --bpm 128 --downbeat 0      # force quando já souber / se a detecção errar
```
- `beats` → mudanças de estado · `downbeats` → cortes e revelações grandes · `hits` → SFX · `sections` → intensidade (intro/build/drop) · `energy` → reatividade.
- Calibre a grade nos bumbos reais (gere stills nos primeiros downbeats e confira). Em música calma, o tracker inventa metrônomo (às vezes em dobro) → corte em mudanças de frase/energia.
- Música de biblioteca: entre no compasso mais forte, não na intro calma; termine em fim de compasso; fade-in 0,4 s, fade-out 1,5 s.

**B. Sem faixa** → sintetize no mesmo timeline da imagem:
```bash
node scripts/music.mjs --bpm 120 --structure "intro:1,build:1,drop:4,outro:1" --style tech --key A --out audio/music.wav --beats audio/beats.json
node scripts/music.mjs --dur 20 --style piano                       # calcula compassos pela duração
```
Estilos: `tech` (produto/UI, pulsante) · `warm` (pop orgânico, maior) · `piano` (história, emoção) · `minimal` (clicks + sub, UI morph) · `cinematic` (braams, impacto, trailer).
A trilha já sai com `beats.json` exato — **as batidas no filme e no áudio são a mesma conta**. Use o mesmo BPM no `index.html`.

Truque: comece o gancho só com SFX e deixe a trilha entrar no primeiro corte (`intro` curta ou mixar música com atraso) — "bate mais forte".

## 2. SFX — fonte única da verdade

O filme declara `window.CUES = [{t, type, gain, pan, pitch}]` usando os **mesmos tempos** das animações (`B(n)`, `CLICKS`, `stagger`). Depois:
```bash
node scripts/sfx.mjs --page index.html --bed audio/music.wav --bed-db -4 --out audio/sfx.wav   # --bed = nivelar contra a trilha
```
- `t` do cue = instante do **evento visual**; o pico vai para t + 1 frame. `align:'start'` para o raro som que deve começar no evento.
- `--bed` mede a trilha (ponderação K, 60 ms a partir do pico) e ajusta cada hit para **3–6 dB acima dela**: `gain ≥ 0,5` → +4,5 dB; `gain < 0,5` (secundário) → +3 dB; `over` no cue força outro valor. Sem isso, os níveis saem desiguais (medido: de −15 a +19 dB sobre a trilha).
- O WAV de SFX sai em float 32-bit (não clipa nem é normalizado → relação hit/trilha intacta) + `sfx_cues.json` com onde cada pico caiu.
Tipos: `click tick key type(n) pop bloop snap thump whoosh swish swipe riser impact boom glitch chime ding shutter`.

Regras:
- **SFX só com causa visível**: click = clique real do cursor · whoosh = corte ou card grande e rápido · tick/key = texto chegando · pop = badge/número pousando · riser → impact = **uma vez por filme** (o payoff).
- **Pico em evento + 1 frame** (medido no arquivo decodificado pelo `audit-audio.py`). Nunca antes da imagem; mais de 2 frames depois lê como atrasado.
- Varie `pitch` 0,9–1,3 e alterne 2–3 tipos para sons repetidos. O mesmo whoosh em todo corte é o sinal nº 1 de amadorismo.
- Desenho surgindo é silencioso; **contatos** fazem som.
- No máximo ~1 cue forte por batida. Hit principal 3–6 dB sobre a trilha; ticks e secundários ~3 dB, e 4–8 dB abaixo do hit principal vizinho.
- Abafe a trilha 3–4 dB por 1–2 batidas no hit mais importante (o "fecha" do filme) para ele respirar.

## 3. Voz (opcional)

- ElevenLabs/TTS: chave no `.env` (`ELEVENLABS_API_KEY`) — **nunca cole a chave no prompt** nem em arquivos que serão compartilhados.
- **Narração como relógio**: gere cada frase separada, meça a duração (`ffprobe`), e monte o timeline a partir dessas durações (cada plano = `[início, fim]` da frase). Nunca estique o movimento para caber numa narração longa: corte o texto.
- TTS lê ~2,2 palavras/s → ≤ 19 palavras por cena de 9 s; 30–90 s de filme ≤ 155 palavras.
- Revele cada elemento quando a voz o nomeia, na segunda metade da cena.
- Personagem/mascote que fala + voz = upgrade que vende como serviço.

## 4. Mix e loudness

```bash
bash scripts/mix.sh out/silent.mp4 out/final.mp4 --music audio/music.wav --sfx audio/sfx.wav [--voice audio/voice.wav] [--music-db -4]
```
- Ganho medido + limitador, em laço, até **−14 LUFS** (social) / −16 (YouTube/podcast). O WAV é limitado em **−2,2 dBTP** (oversampled) porque o encode AAC sobe o pico ~1 dB: medido, um mix a −1,3 virou −0,4 dBTP no MP4. Assim o arquivo decodificado fica ≤ −1.
- Com voz: sidechain automático abaixa a música de 6 a 8 dB quando a voz fala (§7).
- Níveis: sem narração, trilha ~0 dB e SFX 3–6 dB acima da trilha nos hits. Com narração, trilha ≈ −20 dB relativa.
- **Banda de celular (200 Hz–6 kHz)**: medido, um primeiro mix tinha 80% da energia abaixo de 60 Hz, que o telefone não toca. O `music.mjs` agora usa kick curto com "knock" em ~190 Hz, baixo uma oitava acima com saw aberto e passa-altas de 35 Hz no master. Meta: a loudness da banda de celular fica a ≤ 4–5 dB da loudness cheia.
- Tire o **DC** (média de cada canal) — os scripts já fazem.

### Auditoria: o som conferido no arquivo final
```bash
python3 scripts/audit-audio.py out/final.mp4 --sfx audio/sfx.wav --music audio/music.wav --music-db -4 [--loop]
```
Decodifica o MP4 e relata (→ `out/qa/audio.md`): offset do áudio vs stems, sobra de padding do codec, **erro de sincronia por hit** (ms e frames), **hit acima da trilha** (K-weighted, 60 ms), loudness cheia vs banda de celular, % de energia < 60 Hz, DC e true peak do arquivo decodificado. Hits colados (< 45 ms) são marcados "sobreposto" (medidos juntos). Nenhuma nota de som é "achismo": cada follow-up de áudio aponta um número desse relatório.
No teste desta skill, a 1ª passada acusou: 42% da energia < 60 Hz, banda de celular −6,2 dB, true peak −0,8 dBTP, hits de −15 a +19 dB. Depois dos ajustes acima: todos os hits em +1,06 frame e +3 a +4,6 dB, banda de celular −2,7 dB, true peak −1,3, −14 LUFS.

### Loops e o padding do codec
O AAC acrescenta ~10–20 ms de silêncio ao fim. Num MP4 que o player repete, o som corta seco na emenda. Guarde o **WAV mestre sem fade** (posts com 2 loops emendados) e, no MP4 de loop único, aplique fade raised-cosine de 2 ms nas pontas: `bash scripts/export.sh out/final.mp4 x --loop-fade`.

### Prompt de som por números de frame (quando o Claude escreve o som de uma peça pronta)
```
Trilha deste loop de 6 s (360 frames, 60 fps). Tudo sintetizado em código, sem samples. Cada hit com PICO 1 frame depois do evento visual.
Base: 120 BPM, compassos começando nos frames 67, 157, 247, 337; kick em 67, 247, 337; shaker no contratempo só onde não há hit; pad em Bm G A D.
Eventos: inspiração no frame 84 · deslize 84→112 · bloops 112, 113, 114, 120 · ting metálico 200 (parciais < 8 kHz) · swell de 288 com pico em 303 ·
gotas 309 · "glup" final 337 ondulando a 2,4 Hz.
WAV 48 kHz estéreo, −14 LUFS, pico −2,2 dBTP (MP4 decodificado ≤ −1), hits 3–6 dB acima da base, sem clique na emenda. Confira cada hit no áudio decodificado.
```

## 5. Estrutura de clipe musical

- Seções da música = capítulos. Densidade de corte segue a energia: verso = planos lentos; refrão = uma imagem por batida forte; breakdown = imagem segurada.
- O refrão volta a um "palco" e escala a cada vez. O final rima com a abertura.
- Sinais de clipe gerado: o mesmo tratamento por > 6 s, forma de onda como imagem principal, corte em toda batida.
- Letras: grandes e presentes no gancho; em outros trechos como legenda. Componha o plano deixando espaço para elas (personagem à direita, letra à esquerda).

## 6. Contato é nota (o som que faz o filme parecer composto)

Quando um objeto físico guia o filme, a rota vira a partitura. `template/audio/compor.py` faz isso sem sample nem licença.
- Cada contato tem nota escrita à mão em `campaign.json` (`rota`). Timbre por superfície (corda, madeira, vidro, marimba, xilofone, kalimba, clique com nota), nunca um som só.
- A melodia precisa caber na harmonia da batida. Tom menor no problema, maior depois do drop: a virada se ouve.
- O panorama segue a posição do objeto (`scripts/exporta-rota.mjs`, depois `compor.py`). O sopro de voo acompanha a velocidade.
- Camadas entram por seção. Uma batida de silêncio antes do maior impacto.
- **Alinhe pelo ataque, não pelo pico global:** num sino o máximo vem depois do transiente, e alinhar por ele adianta o som em relação à imagem. O `audit-audio.py` acusa "atrasado" nesses casos; confira o ataque antes de "corrigir".
- A meta de 3 a 6 dB é para SFX sobre trilha. Contato-melodia fica melhor em 5 a 11 dB na banda de 300 Hz a 6 kHz (`audio/medir.py`), porque é o instrumento principal; sem trilha, o número sobe e não é defeito.
- Bumbo com "knock" perto de 200 Hz e baixo com harmônicos: 54% de energia abaixo de 150 Hz caiu para 33% e a banda de celular ficou a −0,9 dB da cheia.

## 7. Voz sobre trilha

- Receita aprovada: voz a −15 LUFS, trilha a −17, trilha abaixa 8 dB sob a voz (ataque 60 ms, soltura 350 ms), sons de UI abaixam 3 dB. O `mix.sh --voice` agora limita o sidechain a 8 dB; medido, de 6 a 7 dB (antes passava de 15 dB e a trilha sumia a cada palavra).
- Mais fino, em três bandas: abaixa pouco os graves, bastante os médios, e ajusta frase a frase até a voz ficar cerca de 9 dB acima da música entre 300 Hz e 4 kHz.
- Confira a inteligibilidade transcrevendo o **filme mixado** com Whisper.
- Tempo de palavra: uma passada de Whisper erra até meio segundo; divida nas pausas e alinhe ao início medido.
- Voz que acelera soa falsa: troque o tempo da entrada ou encurte o texto em vez de subir a velocidade (`0,95` a `1,05`).
- Corte riser em volta do pico (de catálogo costuma ter 4 s) e use sopro reverso nas quebras da faixa.

## 8. Som de estúdio: SFX gravados, contabilidade de sincronia, entrega em 3 versões

Aprendido com rejeições reais de cliente (motion-video-kit, video-shotcraft): **varredura de seno e "tick" sintetizado foram recusados** como baratos; sons de jogo (Kenney) soaram "game demais". O que passou: gravações reais e limpas (foley de obturador, interruptor mecânico, papel, tecido, vidro). A regra veta **timbre de UI de jogo**, não a ação.

**Biblioteca** (`estudio/sfx/`, nunca dentro da skill se a licença proíbe redistribuir): Freesound CC0/CC-BY (nunca BY-NC), Mixkit baixado por projeto. Triagem automática do candidato: rejeite se > 50% da energia < 150 Hz ou > 40% > 6 kHz. Filtre: passa-alta 150–220 Hz, passa-baixa 9–11 kHz, fade de 10 ms.
**Ganho por evento, na banda do próprio efeito**, medido contra a trilha sozinha: +3–4 dB na banda do efeito (2–8 kHz no máximo +4 dB); pico ≤ 6 dB acima do pico local da música (8 dB num hit-assinatura); movimento mecânico herói pode ir a +8–10 dB na banda.
**Repetição**: alterne 2 amostras, desça o volume 0,40→0,25 e deixe o intervalo acelerar 8→3 f. Frase de fechamento de plano: riser → impacto → brilho. Whoosh começa 2 frames antes do corte; o riser termina NO hit. Cliente não gostou de um som: **troque, não apague**.

**Sincronia — separe as duas contas**:
1. Regra artística: pico em evento + 1 frame (luz antes do som).
2. Atraso do codec: o AAC empurra o áudio decodificado para depois (~1024 amostras no aac do ffmpeg, ~2048 no fdk ≈ 1,3 f a 30 fps). Meça uma vez por pipeline cruzando 2–3 SFX secos com a faixa decodificada e guarde como constante (`from = pico_alvo − atraso_do_pico_na_amostra − offset_saída`). O `audit-audio.py` mede o resultado final: ≤ 1,5 f ideal, ≤ 3 f aceitável.

**Grade de batida conferida**: ajuste a grade por mínimos quadrados sobre as batidas detectadas (o BPM do detector erra até 2%); aceite resíduos de ±15 ms. Teste 0,5×/1×/2× e fique com o que casa ≥ 98% dos bumbos com erro médio < 10 ms. Bumbo 40–160 Hz, caixa 150–500 Hz + 1–3 kHz, chimbal 6–14 kHz (na parte percussiva). Acentos esparsos vão no transiente real, não na grade.

**Back-timing** (faixa licenciada sob imagem travada): alinhe o hit final da faixa com o corte do cartão final e toque a faixa contínua desde o frame 0; mova os cortes para a grade da faixa (varispeed ≤ 1,7% se precisar). Cliente rejeita emenda e parada seca. Ofereça 5–7 faixas back-timed sob a mesma imagem, no mesmo loudness.

**Loudness por gênero**: −14 LUFS para peças socadas; −16 a −19 para peças calmas (clínica, luxo); LRA ≥ 3 LU em trilha enérgica. Grave abaixo de 120 Hz em mono. Confira o mix em mono (o `qa.sh` mede).

**Entrega**: master · só música · sem música (SFX + voz). E liste os **5 timestamps de risco** para o cliente ouvir de fone.

### Na prática (v5)
- **Biblioteca gravada**: `node scripts/sfx.mjs --page index.html --lib estudio/sfx --bed audio/music.wav --bed-db -4`. Arquivos nomeados pelo tipo (`whoosh_soft.wav`, `click_mech_02.wav`, `impact_01.wav`); o script filtra (180 Hz–10 kHz, fade 10 ms), rejeita amostra grave/aguda demais, alterna amostras do mesmo tipo e desce o volume em sequências rápidas. O que não tiver gravação é sintetizado. Cue pode pedir arquivo: `{ t, type: 'whoosh', file: 'whoosh_soft' }`.
- **3 versões de entrega**: `bash scripts/mix.sh ... --stems` → `final.mp4`, `final_sem_musica.mp4`, `final_so_musica.mp4`.
- **Contenção**: linha digitada, toque visível e corte dentro da tela ficam MUDOS por padrão; no máximo 1 "ding" por filme; um som real gravado com a trilha baixada à metade vale mais que dez sintetizados. Corte o começo do whoosh para o pico cair ~6 f depois do corte quando ele "puxa" a cena.
- **J/L-cut** (voz, talking head, cartoon): som do próximo plano entra 4–12 f antes (J); som do atual continua 12–24 f depois (L).
