# Ferramentas: o que usar, quando, e o que instalar

Regra de ouro (consenso de todas as fontes, sem benchmark que diga o contrário): **o motor não é o que dá qualidade**. Remotion e HyperFrames empataram em teste lado a lado; o salto vem de proibições, números, referência, 2º passe de crítica. Por isso a rota padrão continua a nossa (index.html + `seek(t)` + Playwright + ffmpeg). As outras entram quando ganham em algo específico.

## Mapa: quem ganha em quê

| Precisa de… | Use | Por quê |
|---|---|---|
| Tipografia, UI, dados, marca, explainer, campanha, série de personagem 2D | **Rota pura (padrão)** | determinística, blur em luz linear, som com pico no frame, auditorias; zero dependência pesada |
| Produto 3D, vidro/metal, voo de câmera por dentro do objeto | **Three.js** dentro da rota pura (`lab.md` §7 + `oficio.md` §5) | `seek(t)` continua valendo; PMREM + ACES/AgX + bloom com limiar. Regra: se CSS `preserve-3d`/`M.cam3` resolve, não use 3D (agentes exageram em Three.js) |
| Animação que o cliente já tem em After Effects | **Lottie** (`goToAndStop(t*1000, false)` dentro do `seek`) | importa a animação de marca sem refazer |
| GSAP já existente / MorphSVG / SplitText | **GSAP** pausado: `tl.totalTime(t+0.001,true); tl.totalTime(t,true)` | grátis (inclusive plugins), seek determinístico |
| Pessoas reais, filmagem, ambientes fotográficos, personagem orgânico complexo | **Modelo de vídeo** (Higgsfield está conectado nesta conta; Veo, Kling, Runway) — rota **híbrida** | código perde em fotorrealismo. A IA faz só a mudança semântica (material, estrutura); o código faz texto, UI, marca, tempo e som por cima. Segmentos de 3–6 s com UMA mudança cada; o seguinte começa no último frame real do anterior |
| Cena 3D fotográfica com rig | **Blender + MCP + BlenderKit** (máquina do usuário) | puxe asset pronto e arranje — não modele do zero; preview 480p; 1080p leva 1–2 h |
| Explainer de matemática | Manim | estilo reconhecível; precisa de LaTeX |
| Mascote interativo com estados | Rive | runtime MIT; o .riv sai do editor deles |

## O que NÃO usar por padrão

- **Remotion**: grátis só para empresas com até 3 pessoas. **A Orbe tem 4 → licença de empresa paga** (confira os termos atuais em remotion.dev/license antes de usar). ~950 MB + Chrome de 283 MB por projeto.
- **HyperFrames** (HeyGen, Apache 2.0): bom e grátis, mas não supera a rota pura em qualidade; render local lento, banding em 8 bits, sem análise de áudio. Vale minerar ideias (lint de composição, catálogo de transições shader, `animation-map`). Use se o usuário pedir.
- **Kenney / sons de jogo**: clientes rejeitaram como "game demais". **Mixkit**: proíbe redistribuir dentro de ferramenta/template — baixe só no projeto do cliente, nunca guarde na skill.
- **madmom** (modelos CC BY-NC-SA) e **Essentia** (AGPL): licença incompatível com trabalho de cliente.
- **Claude Motion** (aba de artifacts do claude.ai): hoje só em planos Team/Enterprise; esta conta não lista o tipo. Se aparecer, é ótimo para edição colaborativa (comentário preso ao elemento, edição de texto direto); a skill continua sendo o caminho para render determinístico, som medido e campanha.

## O que instalar (por nível)

**Nível 0 — já basta para 90% dos trabalhos** (o `new.sh` confere): Node 20+, ffmpeg, Python 3 + numpy, Playwright (Chromium).

**Nível 1 — série com personagem / narração** (`new.sh --kind cartoon` confere):
```bash
pip install piper-tts faster-whisper          # voz offline + palavra a palavra
# voz pt_BR: baixe pt_BR-faber-medium.onnx + .json do repositório de vozes do Piper (Hugging Face rhasspy/piper-voices) para models/
```
- **Rhubarb Lip Sync** (MIT): baixe o binário do GitHub (DanielSWolf/rhubarb-lip-sync, releases) na SUA máquina e coloque no PATH. O `voice.py` usa sozinho quando existir; sem ele, o analisador próprio dá um lip sync bom.
- **ElevenLabs** (opcional, melhor voz PT-BR): chave no `.env` do projeto; gere as falas em `audio/lines/NN.wav`.

**Voz local de qualidade — VoiceStudio (já instalado no Mac do Gabriel)**: app local com 17 motores atuais e clonagem a partir de 5–15 s de áudio limpo. API compatível com OpenAI em `http://localhost:3900/v1`:
```bash
python3 scripts/voice.py --api http://localhost:3900/v1 --api-model cosyvoice3 --api-voice <voz-clonada>
```
(rodando a skill no Claude Code do próprio Mac, com o app aberto; na nuvem, exporte os WAV em `audio/lines/NN.wav` e rode `voice.py --no-tts`). **Licença**: o motor padrão (OmniVoice) é **não comercial** — para cliente use CosyVoice 3, VoxCPM2 ou MOSS-TTS (Apache-2.0) e teste o pt-BR do motor escolhido. Clone só a sua voz ou a de quem autorizou por escrito.

**Nível 2 — som de estúdio** (o maior salto de percepção depois da imagem):
- Biblioteca própria de SFX **gravados** (Freesound CC0/CC-BY — nunca BY-NC; Mixkit só por projeto) em `estudio/sfx/` com nome por função (`whoosh_soft_01.wav`, `click_mech_02.wav`). Ver `sound.md` §7 para triagem, filtro e ganho por banda. Os SFX sintetizados continuam como reserva.
- Trilhas licenciadas (Artlist, Epidemic, Musicbed) quando o cliente pagar: com faixa, use `beats.py` e **back-timing** (o hit final da faixa cai no corte do cartão final).

**Nível 3 — 3D e híbrido**:
- Three.js (MIT) — fixe a versão no projeto.
- Blender 5.x + servidor MCP do Blender + BlenderKit, na máquina do usuário, só para planos fotográficos.
- Conector do Higgsfield (já ligado) para plates de vídeo/imagem na rota híbrida. Sempre com claims e marca por cima em código.

**Nível 4 — skills de apoio (claude.ai / Claude Code)**:
- **Impeccable** (pbakaus) — design system e detector de "slop" com 62 regras: `npx impeccable install` ou `/plugin marketplace add pbakaus/impeccable`. Use antes do filme para fechar a direção de arte do cliente.
- **frontend-design** (já disponível) — direção visual de páginas/telas que o filme mostra.
- Skills de transcrição/SRT: o `voice.py` já faz palavra a palavra com faster-whisper; para vídeo do cliente, extraia o áudio e rode o mesmo.

## Rota híbrida (quando o código perde)

1. Trave os keyframes antes de gerar vídeo (stills aprovados).
2. Gere planos de 3–6 s, cada um com UMA mudança; o próximo começa no último frame real do anterior (confira a emenda).
3. Traga o MP4 para a rota pura como `<video>` com `currentTime = t` dentro do `seek` (ou frames extraídos), e faça por cima: tipografia, UI, marca, contador, legendas, som.
4. Nada de texto/logo gerado pelo modelo de vídeo: sempre em código.
5. Rastreie o objeto do plate quando o texto precisar "grudar" nele (pontos marcados em 3 frames + `M.monotone`).

## Skills de terceiros já instaladas no Mac (~/.agents/skills)
HyperFrames (hyperframes, -animation, -audio, -cli, -core, -creative, -keyframes, -registry, -studio), Remotion (studio, etc.) e Higgsfield. A skill motion-studio continua sendo a rota padrão; chame HyperFrames/Remotion só por pedido explícito (Remotion = licença de empresa para a Orbe). Os padrões úteis deles já estão em `receitas.md` e `oficio.md`.
