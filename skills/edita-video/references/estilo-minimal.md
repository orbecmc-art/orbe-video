# Estilo minimal premium (o "look Arthur Brooks")

Talking head educativo com cara de alto valor: papel, serifa itálica, uma cor fosca, cenas de linha, gráfico,
pintura e aspas alternando com o rosto. Calmo e artístico, mas com mudança visual constante. Serve para médico,
advogado, mentor, consultor, marca pessoal premium. Preset: `estilo=minimal` (assets/estilos.json).

## Os 10 princípios → como a skill faz

| # | Princípio | Na skill |
|---|---|---|
| 1 | **Legenda cinematográfica**: 2 fontes (sans média + serifa itálica); linha ≤ 5 palavras; a(s) palavra(s) importante(s) GRANDE(S) no centro, as outras pequenas nos vãos acima/abaixo | `legendas.layout = "cinema"` (automático no minimal): chave = número > ênfase > termo do briefing > palavra longa/alongada; cada palavra aparece quando é dita |
| 2 | **B-roll com texto**: papel leve, bordas escuras e levemente desfocadas (o olho vai ao centro), texto cinematográfico por cima | `broll.tratamento = "papel"` (padrão no minimal) + peça `frase` sobreposta no mesmo trecho |
| 3 | **Pintura**: pintura que mostra a fala + textura de tinta/papel + texto em volta do sujeito + câmera desliza para revelar | `foto` tela cheia (pintura de domínio público: Wikimedia Commons/Openverse, `busca` em inglês "… painting public domain") + `"transicao": "deslize"` + `frase` |
| 4 | **Linha + texto**: linha de acento se desenha, é interrompida pela palavra e segue até a próxima; câmera acompanha | peça `linha` (`params.textos`, `forma: reta|zigue`, `tempos` opcionais) |
| 5 | **Linha + ilustração** (progressão em fases, zigue-zague com pan) | `linha` com `forma: "zigue"`; ilustração própria → peça `custom` no motion-studio |
| 6 | **Só texto com aspas** em papel claro/azul — fecha a ideia | peça `aspas` (`fundo: claro|azul|escuro`) |
| 7–8 | **Ilustração central / lateral** com textura pintada e texto em volta | `custom` (motion-studio) ou imagem gerada (Higgsfield/Canva) como `foto` + `frase`; saúde: nunca paciente |
| 9 | **Objeto + texto** (callout de um elemento) | peça `callout` (`ponto: [x, y]`, `texto`, `sub`) sobre B-roll ou rosto |
| 10 | **Gráfico**: fundo escuro texturizado, grade fina com brilho leve, bola de acento traçando a linha, câmera segue | peça `grafico` (`forma: degraus|sobe|plano|cai`, `degraus`, `rotulo`) |
| + | **Legenda + UI** (animação pequena na metade de baixo, vídeo atrás escurece e desfoca) | qualquer peça `sobreposto` com `"posicao": "meio-baixo", "fundo": "escurece"` — ex.: `capitulos` (1·2·3 que preenchem) |

## Como planejar (o passo que mais pesa)
- **Abra no rosto** com legenda: conexão antes de animação. O 1º visual forte vem cedo (≤ 4 s) para prender.
- **Anuncia item novo → rosto. Descreve → mostra.** ("Existem os lineares…" = rosto; "…que sobem, sobem, sobem" =
  gráfico em degraus, um degrau por "sobe".)
- Série (1, 2, 3) = a MESMA UI (`capitulos`) que preenche a cada item e volta no fim com todos preenchidos.
- Pessoa citada → `callout`/foto; história → pintura ou B-roll com texto; número/ritmo → gráfico; virtudes/ideias em
  sequência → `linha`; conclusão → `aspas`.
- Uma tela cheia nunca colada na outra (≥ 2 s de rosto); fora do rosto ≤ 45% do vídeo.
- Use a **página de plano** (`plano.py`): roteiro linha a linha, a pessoa escolhe Legenda · Legenda + UI · Meia tela ·
  Tela cheia e o design; 15 min de plano humano valem mais que qualquer prompt. A 1ª versão chega a 60–70%; o resto
  são revisões numeradas.

## Look e números
- Cores foscas: acento azul dessaturado `#6E8FC6` (ou a cor da marca, UMA só), papel `#EEEAE2`, escuro `#121315`.
  Nada de preto/branco/vermelho puros. Cor do vídeo: preset `fosco` (pretos levantados, saturação 0,80).
- Fontes: Inter (pequenas, peso 500) + Playfair Display itálico 700 (chave). Troque por Fraunces/Instrument Serif/DM
  Serif Display mantendo o par sans + serifa itálica.
- Elementos ~25% menores que o primeiro impulso; efeito raro = efeito especial; papel e grão sempre sutis.
- Câmera: zoom alternado 100↔105%, punch raro (+3,5% a cada ≥ 9 s), transição seca entre rosto e cena; `deslize`
  para revelar pintura/B-roll.

## Som (3 famílias, sempre seguindo o movimento)
- **Movimento** (whoosh/paper): câmera desliza, cena entra, papel passa.
- **Texturas** (click/tick/pop/marker): algo aparece — texto (click suave), círculo preenche (pop), linha/gráfico
  riscando (marker).
- **Antecipação** (riser + hit): só na grande virada, no máximo 1–2 por vídeo.
- Trilha cinematográfica suave (piano) a −20 dB sob a voz; densidade discreta (≈ 6 / 30 s); visual pronto antes do som.

## Fonte
Princípios do vídeo "How to Edit VIRAL Talking Head Videos Using ONLY Claude (New Minimal Style)" (Joseph, Ultimate
Editors, out/2026) e do "How to Edit VIRAL Instagram Reels Using Opus 5.5" (mesmo canal) — estudados e reescritos;
nenhum arquivo deles foi copiado.
