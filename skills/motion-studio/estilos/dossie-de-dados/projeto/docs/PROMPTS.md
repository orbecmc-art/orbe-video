# Recibos

## Pedido do dono (05/11/2026)
Motion vertical com a referência do TikTok @odossie.br, surreal de bom, para o público compartilhar. Voz no ElevenLabs, natural e suave.

## Roteiro falado
Quantas vezes você ainda vai ver a sua mãe? / A gente fez a conta. / Mulher de sessenta, no Brasil, vive em média até os oitenta e quatro. Faltam vinte e quatro. / Se você mora longe, e vai lá duas vezes por ano, são quarenta e oito visitas. / Quarenta e oito. Cabe numa folha de caderno. / Se você vai todo mês, duzentas e oitenta e oito. / Parece bastante. Não dá um ano. / Agora olha o que já passou. / Cada quadradinho desse é um dia com ela. / Até você sair de casa, foram quase seis mil. / Seis mil "já comeu?". Seis mil "leva um casaco". Seis mil "me avisa quando chegar". / E a gente achava que ia ser assim pra sempre. / Aos dezoito anos, você já tinha vivido noventa e três por cento do seu tempo com ela. / Hoje, o que sobrou é isso aqui. / Esse ano, você vai passar cento e dezesseis dias inteiros na internet. / Inclusive agora. / Com ela, doze. / A última vez nunca avisa que é a última. / Então não manda esse vídeo pra ninguém. / Liga pra ela. / Melhor: vai lá. / E me avisa quando chegar.

## Voz
ElevenLabs, Eleven v4, voz Juliana Katrein, estabilidade 50%, similaridade 75%. Usada a take2. `audio/voz/montar.py` reabre os respiros. A fala dos 24 anos foi regravada a pedido do dono ("mais 24" soava como viver 24 anos): `audio/voz/trocar_p03.py` roda depois do montar, com a take novo1.

## Fontes dos números
- IBGE, Tábuas Completas de Mortalidade 2024, Tabela 3: mulher aos 60 anos, mais 24,2 anos (lido no PDF oficial).
- We Are Social e Meltwater, Digital 2026 Brasil: 53h30 por semana online. Lido em matéria do Olhar Direto de 08/07/2026, não no relatório original. 53,5 h x 365/7 / 24 = 116 dias.
- Simulação do filme: mãe de 60 anos, filho de 32, saiu de casa aos 18. Até os 18: 18 x 365 x 90% = 5.913 dias. Depois, uma visita por mês: 168 já feitas e 288 por fazer. Total 6.369. 5.913 / 6.369 = 92,8%.
- Ideia da conta: Tim Urban, The Tail End, Wait But Why, 2015.

## Imagens e som
Fotos e vídeos do Pexels (ids nos nomes de assets/originais e em scripts/preparar.py). Clipes: 8817764, 4863747, 5101554, 10397853, 7516762, 6624519. Efeitos: ElevenLabs Sound Effects. Trilha: composta em audio/musica.py, sem sample.
