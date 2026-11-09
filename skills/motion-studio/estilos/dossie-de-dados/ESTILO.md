# Dossiê de dados ("A conta")
id: dossie-de-dados
Melhor para: uma conta que muda como a pessoa enxerga algo (tempo, dinheiro, saúde, trânsito), dado público que emociona, campanha que as pessoas compartilham, explicação de número para leigo, vídeo-manifesto de marca com narração
Formato: 1080×1920 (9:16), 85 s, narração natural (ElevenLabs) + piano em código + efeitos de papel
Vídeo na galeria: galeria/videos/m-dossie-de-dados.mp4 (filme "A conta", Orbe, 05/11/2026)
Peça de partida: projeto/ (filme.js + narracao.js + dados.js; texturas geradas por projeto/scripts/preparar.py)

## Como usar esta referência
1. Leia esta ficha inteira antes de abrir `projeto/`.
2. A peça nova nasce de UMA conta verificável (fonte guardada no LEIA-ME do projeto, nunca na tela) e do roteiro falado.
3. Mantenha o mecanismo, a paleta e o ritmo medidos aqui; troque o assunto, os números e as fotos.
4. O `filme.js` é apoio: rótulos de papel rasgado, polaroide com fita, caneta vermelha, persiana, mosaico de dias.

## Mecanismo em uma frase
A narração faz uma conta em voz alta e a mesa de trabalho prova cada passo: tabela real com marca-texto, a conta à mão no
caderno, quadradinhos amarelos que viram dias, fotos com fita — e a luz da persiana atravessa o dia até a noite enquanto o
número vira emoção.

## Estrutura
- **Mesa**: papelão (kraft), caderno quadriculado e ardósia, sempre com a sombra da persiana em diagonal (−50°) deslizando.
- **Rótulos de papel rasgado**: tarja preta (pergunta/contexto), etiqueta amarela (número/conclusão), serifa itálica em papel claro (fala da mãe, nota). Batem na mesa com amasso e mola; a tarja preta risca da esquerda.
- **Provas**: tabela do documento oficial com marca-texto e círculo de caneta vermelha; conta escrita à mão (Caveat) aparecendo como quem escreve.
- **Quadradinhos**: cada um é uma unidade (visita, dia); marcados um a um em amarelo; viram mosaico do rosto e desmoronam.
- **Gancho e fecho em tela de celular**: chamada de "Mãe" vibrando; no fim, a conversa sem resposta — o vídeo emenda no começo.
- **Faixa vermelha** com a ordem em letra gigante ("liga pra ela") no clímax.

## Paleta (hex)
- papel: `#EFE9DC` · papelão: `#A88862` · tinta: `#17140B` · tarja: `#121210`
- **acento (único): amarelo etiqueta `#F0CA35`** · caneta: `#C5202C` (só no círculo e no "liga") · azul de tela `#A9D6FF` (só na cena "internet")
- luz: dia `#F6F3EA` → pôr do sol `#FFC484` → noite `#22212F`

## Tipografia
- Rótulos: Inter Tight 800–900, caixa alta, tracking −0,03 em no número
- Serifa: Instrument Serif itálico 400 (falas, notas, manchetes)
- Mão: Caveat 700 (a conta escrita) · Faixa: Archivo Black / Anton

## Batidas (como o filme anda)
| Tempo | O que acontece | Curva |
|---|---|---|
| 0–4,6 s | Gancho: chamada vibrando, "sua mãe?" bate em vermelho, celular recua | bate 5 qd + mola; recuo E.move 1,0 s |
| 4,6–10 s | Prova: tabela real, marca-texto varre, círculo de caneta, "60 + 24 = 84" | marca-texto 0,25 s; caneta 0,45 s |
| 10–26 s | A conta no caderno: 48 → 288 quadradinhos; "não dá um ano" | um quadradinho a cada ~2 qd |
| 26–49 s | Mergulho na foto + rosto feito de dias; luz dourada em "pra sempre" | câmera 1,2 s inOut |
| 49–57 s | Soco: no "93%" os dias caem como papel, sobram os olhos no escuro | queda física fechada |
| 57–75 s | Um ano em 365 quadradinhos; 116 azuis (internet) × 12 dourados (com ela); faixa "liga pra ela" | |
| 75–85 s | Noite: a conversa no celular; volta a chamada (loop) | |

## Movimento (medido com pericia_movimento.py, cópia 720p)
| Medida | Valor |
|---|---|
| Amplitude (pico ÷ mediana) | **58,2x** |
| Em quase-parada | **81 %** |
| Cortes duros | 1 (o resto é câmera e papel batendo) |

**Metas para a nossa versão:** amplitude ≥ 40x · quase-parada ≥ 70 % · ≥ 3 picos (os socos: gancho, número-chave, faixa final).
É um filme de muita calma e poucos socos: a voz carrega, o papel pontua.

## Permitido e proibido
- Sempre: número com fonte verificada (no LEIA-ME, não na tela, salvo pedido); a conta conferida em `window.CHECKS`.
- Sempre: persiana e grão; sombra projetada nos papéis; tudo "bate" na mesa, nada aparece com fade.
- Proibido: gradiente, glow, ícone genérico, texto centralizado flutuando sem papel, mais de um acento, trilha de banco "inspiracional".
