# Receitas prontas (com números) — peças que clientes pedem toda semana

Cada receita é um plano/cena completo com tempos medidos de repos e filmes que funcionaram. Adapte os tokens da marca; mantenha os números até ter motivo para mudar. Tempos a 30 fps salvo indicação.

## 1. Revelação de produto ("deriva → whip → hold", 10 s, um plano contínuo)
Fonte: anatomy-reveal (MIT). Ótimo para concessionária (peça, roda, painel), varejo, gadget.

| Tempo | Batida |
|---|---|
| 0–1,62 s | entra rolando: yaw ~180°, roll −30°→0, ocupa 60% da largura |
| 1,72–1,96 s | **whip** até macro 4–8× (0,24 s, quíntica in-out `16x⁵`) |
| 1,96–2,76 s | deslize lento na macro (o hold continua derivando) |
| ~2,8–6,9 s | 2º whip e hold com algo **funcionando** (ponteiro sobe, luz acende); o recurso acontece e volta |
| 6,93–7,33 s | **explode** (ease-out) |
| 7,33–8,25 s | hold explodido: yaw 10–15° + leve zoom out |
| 8,25–8,9 s | junta de novo girando para a câmera |
| 8,9–10 s | herói a 75% da largura (só o último segundo fica parado) |

- Canal `focus` no espaço do OBJETO, projetado com a rotação atual: o close não escapa do assunto enquanto ele gira.
- **Mudar a duração**: segmentos que terminam num whip mantêm o tamanho; os outros escalam pelo mesmo fator → filme mais longo "respira", não fica em câmera lenta.
- **Mudar o formato**: escreva as chaves em 9:16; planos abertos (zoom < 2,6) × `min(1, W/540, H/760)`; macros (> 4,6) ficam; entre os dois, mistura.
- **Nunca chute um ângulo**: renderize uma folha de 6–12 poses candidatas (`{yaw, pitch, zoom, focus}`) com `stills.mjs --times` e escolha olhando.
- Blur: o render com `--sub auto` sobe as amostras no whip (sem "cópias" separadas).

## 2. Vista explodida com linhas-guia (sem colisão)
Fonte: claude-animation-skills/breakdown (MIT) + /anatomy.
- Camadas: inOut³ em 1,25 s, intervalo 0,07 s, a de cima sai primeiro. Giratório −33°→−23° em 4,2 s; flutua 2°·sin(1,3t) e 0,05·sin(1,7t). Câmera amarrada à explosão (distância 46→55, elevação 34°→26°, fov 26).
- Composição: `camera.setViewOffset(W,H,150,0,W,H)` empurra o objeto para a esquerda e libera a coluna de rótulos.
- Linha-guia: ponto na âncora 3D projetada a cada frame → cotovelo em `max(ax+40, LX−90)` → horizontal até o rótulo; desenhada por comprimento de arco (`M.drawPartial`); rótulo entra 0,13 s depois deslizando 18 px.
- Sem colisão: projete as âncoras no frame explodido, ordene por y, espaço mínimo 150 px, suba tudo se passar do limite, numere 01–06 na ordem da tela.
- Vidro: `MeshPhysical` opacidade 0,15, clearcoat 1 + `EdgesGeometry`(30°) a 0,55 — o vidro lê pelas bordas.
- Look isométrico (/anatomy): 4 tons com ~3% de luminância entre eles + UM acento iluminado; azimute 45°, elevação 30°; linhas finas; toda linha termina numa borda; textura "some aos poucos".

## 3. Rota no mapa ("como chegar": clínica, loja, delivery)
Fonte: claude-animation-skills/map-route (MIT, three.js).
- Cidade: ruas a cada 4 unidades, quarteirões 3×3 (1/2/4 lotes), prédios em `InstancedMesh` branco (cinza 0,955–1), 7% altos, 5% parques, névoa 90–160.
- Trajeto: waypoints na grade, cantos arredondados (r 1,6), reamostrado a cada 0,06, fita com `setDrawRange(0, k·6)` (desenho exato por frame): borda branca 0,5 sob o acento 0,34. Cabeça: disco + anel de pulso (0,8→1,7, α 0,35→0).
- Progresso quad in-out de 0,25 a 2,75 s. Câmera mira 2% atrás da cabeça; azimute 28°→10°; fov 30.
- Pino: cai de 9 unidades em 0,28 s, um quique de 1,1 em 0,22 s, achata 18% preservando volume (1/√s); sombra muda com a altura.
- Textos: ETA = `round(min·(1−p))` → "Chegou"; a pé 12 min/km, bike 4, carro na cidade 2. Endereço e tempo reais do cliente (fato com fonte).
- Sem three.js: a mesma receita em 2D com `M.cam3` (mapa como plano inclinado) resolve 80% dos casos.

## 4. Gráfico de linha com contador amarrado à ponta
Fonte: claude-animation-skills/graph (MIT).
- Curva Catmull-Rom → Bézier (tensão 0,5/3), revelada por comprimento (`M.drawPartial`).
- **O número é a linha**: o contador lê o y da ponta (`valor = y_ponta × final/último`), não é um tween separado; em p = 1 cai exato no valor final.
- Tempos: eixos 0,45 s (power3.out, 0,06 s entre eles); linha 2,7 s (power1.inOut); pouso: halo r 13→60 em 0,7 s + pontilhado até a base em 0,45 s.
- Gosto: um número, uma linha, sem selos tipo "83×". Pontos intermediários nunca inventados: sem dados, a curva é rotulada "ilustrativa".
- Contagem: a legenda entra DEPOIS que o número termina; hold ≥ 0,5 s + 0,7 s de quietude; sem overshoot em quantidade; dígitos em célula fixa (`M.digits`).

## 5. Linha digitada (TypedLine medida)
- Entrada: `M.typed(t, t0, texto)` — 1 letra/frame, +2 f depois de espaço, +1 f de tropeço a cada ~7. Sem cursor. Centralize pela largura FINAL. Tracking pousa de +X em a 0 em 24 f. Silenciosa por padrão (som de tecla em tudo = barato).
- Saída: `M.sweepOut` — em 13 f a borda esquerda da tinta corre para a direita até ~70% sumir (borda suave de 8 letras), a linha desce 0,5 cap em p², o resto escurece a 0,85 e **corta seco**.

## 6. Legenda cinética (sobre vídeo/foto)
- Stagger 2,1 f, entrada 9 f (sobe 16 px, blur 7→0); ênfase em peso 800 contra 600 e no acento.
- **Scrim radial só sob o texto vivo**: elipse 80%×100%, preto 0,62 → transparente em 72% (não uma barra preta inteira).
- Tamanho pela altura de caixa-alta medida (62 px num quadro de 1080 de altura = 0,057; fonte ≈ altura/0,72).
- Blocos (PT-BR): ≤ 2 palavras e ≤ 13 caracteres, ou ≤ 3 e ≤ 18; nunca terminar em palavra funcional; sem travessão (lê como IA); números por extenso viram dígitos ("vinte e cinco" → "25").

## 7. Lower third (nome e cargo do médico/advogado/vendedor)
Barra → nome → cargo com 3–6 f entre eles. Entrada 12–18 f, hold 90–150 f ("dá para ler duas vezes"), saída 8–12 f. Cargo a 45–60% do tamanho do nome; painel 70–85% de opacidade. Fica no terço oposto ao rosto.

## 8. Logo reveal
Uma técnica só; 0,8–2,5 s; nunca skew/squash na geometria da marca. Assentamento 1,04→1,00 em 0,15 s no pico do som de marca. Wordmark animado por subpath (contornos internos das letras preservados). SVG do logo, nunca PNG.

## 9. Geometria contínua (palavra gigante que vira composição)
Palavra gigante em contorno fino dentro de um círculo tracejado maior que o quadro colapsa em 44 f (ease-out); no fim é **preenchida num corte, sem fade**; trilhos saem até as bordas, tracejados se fecham, o círculo gera irmãos em Venn. Frames por palavra: 70/36/36/36/40. **Crossfade espelhado**: letras antigas somem da esquerda para a direita enquanto as novas chegam da direita para a esquerda apagadas e depois acendem da esquerda para a direita. Regra: nunca uma geometria nova por card — a mesma forma se transforma.

## 10. Fotos/prints/B-roll misturados (unificar o look)
- Grade unificadora: cor-herói em soft-light 0,10–0,15 (tema claro) ou 0,18–0,25 (escuro) + gradiente escurecendo topo e base (0,10 e 0,20).
- Ken Burns em toda foto: 1→1,08–1,10 com pan de −25 px, **alternando** zoom in e zoom out entre planos seguidos.

## 11. Personagem palito (série barata e consistente)
Proporções normalizadas pela altura `s`: cabeça r 0,19 em y −0,765; torso "feijão" 0,25×0,35; braço 0,14+0,13; perna 0,155+0,155; membro 0,028; contorno 0,017; sombra de contato elipse 0,2×0,035 α 0,22; sombreamento chapado num lado (18% escuro sobre 38% da largura). Olhos: squint, happy, spiral (gira t·9), x, wide 1,3×, smug. **IK de 2 ossos** (lei dos cossenos) para a mão agarrar um ponto; objeto na mão desenhado com a posição/ângulo da mão (na frente ou atrás do braço).

## 12. Cartoon 3D (three.js) — cadeia de pós
Render 720×1280 → Lanczos para 1080×1920. Composer HalfFloat MSAA 4 → Bokeh (foco = distância ao assunto; abertura 0,004 normal, 0,06 macro) → bloom (0,25/0,4/1,6 ×0,6) → grade (vinheta 0,28, grão 0,018). Cada plano devolve `{dof, bloom, exposure}` por frame. Reflexo de estúdio: PMREM de cena própria com softboxes (key 8×4 a 3,2; rim 4×10 a 1,6; fundo 10×3 a 1,0) — é o que faz metal parecer metal. Impacto em câmera lenta: posição = `impacto − dir·max(0, TI−t)·v` (contato exato no frame). Virada "Mas…": corte para preto 0,18 s / volta 0,16 s. Roteiro ~2,5 palavras/s.

## 13. Física de verdade sem quebrar o seek
`M.bake` simula uma vez a passo fixo (240 Hz) desde t=0 e guarda as amostras; `seek(t)` só lê. `M.verletStep({floor, walls, bounce, friction})` dá pilha de objetos caindo, colisões e quique. Para cenas com dezenas de corpos: bake no load, não no frame.

## 14. GSAP sem quebrar o seek
`gsap.timeline({ paused: true })`; `tl.set({}, {}, DUR)` fixa a duração; labels = capítulos do STORYBOARD; no `seek(t)`: `tl.totalTime(t + 0.001, true); tl.totalTime(t, true)`. Armadilhas: vários `from`/`fromTo` na mesma propriedade pedem `immediateRender:false`; `"random(...)"` e `stagger:{from:"random"}` usam Math.random (semeie ou pré-calcule); `onComplete` não dispara com `totalTime(t,true)` — nada de estado ali. Plugins (todos grátis): MorphSVG (`type:"rotational"`, `shapeIndex` fixo depois do 1º ajuste; `render(rawPath)` + `updateTarget:false` para desenhar no canvas), DrawSVG `"20% 80%"` (traço que viaja), CustomEase a partir de path (importa curva do After Effects), SplitText (`mask:"lines"`, depois das fontes, `font-kerning:none`).
