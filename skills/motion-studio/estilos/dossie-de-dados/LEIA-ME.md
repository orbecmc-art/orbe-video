# Dossiê de dados — o que trocar e o que quebra

- **Troque**: o roteiro (`narracao.js` sai do alinhamento palavra a palavra da voz), os números (`window.CHECKS` em
  `filme.js`), as fotos (pasta `assets/originais`, Pexels/cliente) e as falas em serifa.
- **Rode `scripts/preparar.py`** para gerar papelão, caderno, persiana e os índices dos dias (`dados.js`) — semente fixa.
- **Quebra se**: a persiana ficar forte demais (passa de 0,4 de opacidade e suja o texto), um rótulo não sair antes da
  próxima cena, texto cair em cima da boca de quem aparece, o crepúsculo ficar escuro demais para ler.
- **Render pesado**: o mosaico de 6 mil dias é lento — sem filtro por ladrilho; renderize em JPEG, não PNG.
- **Na edição de vídeo gravado** a mesma gramática existe como estilo `dossie` (edita-video: etiquetas, faixa, grade,
  colagem, recorte, cartão cinza).
