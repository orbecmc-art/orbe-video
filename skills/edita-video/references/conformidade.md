# Conformidade e regras da Orbe

## Regras fixas da Orbe (sempre)
1. **Nenhuma fonte/crédito na tela** — nada de tarja vertical de fonte, rodapé "Fonte: …", crédito de foto, @ do
   banco de imagem. Fontes de dados e licenças vão para `docs/CREDITOS.md`, para o LEIA-ME do projeto e, quando a
   licença exigir (CC BY), para a legenda do post. Só entra no quadro se o pedido disser explicitamente
   (`briefing fontes_na_tela=sim`). O `mapa.py` e as peças avisam se aparecer "Fonte:" no texto.
2. Número dito no vídeo precisa de fonte do cliente (anotada no CREDITOS/briefing) — o número aparece, a fonte não.
3. Licença clara ou não entra (imagem, vídeo, música, fonte tipográfica). Trilha gerada em código é a opção segura.
4. Chaves de API só no `.env` (projeto, `~/.config/orbe/.env` ou da skill) — nunca no código, nunca no chat.
5. Brutos intocados, versões nunca sobrescritas.

## Saúde, estética, odonto (CFM 2.336/2023, CFO, Anvisa) — nicho=saude liga isto
- Sem "antes e depois" de paciente; sem promessa de resultado ("acaba com", "garantido", "100%").
- Pessoa de banco de imagem nunca apresentada como paciente real nem como resultado.
- Paciente real só com autorização de imagem por escrito (pergunte); nunca identificar paciente sem ela.
- Profissional identificado (nome + CRM/RQE quando for anúncio de especialidade: peça o número; vai no lower third
  SÓ se o cliente pedir — é dado, não fonte).
- Sem preço de procedimento como chamariz em saúde; sem "o melhor/único" sem prova.
- Linguagem: "pode ajudar", "avaliação individual", "procure um especialista".
Na dúvida: marque no DIARIO e pergunte antes de publicar.

## Plataformas
- Reels/TikTok: legenda e peças fora das zonas da UI (topo 14%, base 22%, trilho direito na metade de baixo).
- Música comercial conhecida sem licença derruba/silencia o post — não use.
- Anúncio (Meta Ads): sem texto excessivo cobrindo o rosto; capa sem texto pequeno.

## Remotion / HyperFrames / outras skills de vídeo
Esta skill não depende delas. Remotion exige licença de empresa acima de 3 pessoas (a Orbe tem 4): não usar sem
licença. HyperFrames é Apache-2.0, mas o motor não muda a qualidade — o motion-studio cobre o motion.
