#!/usr/bin/env python3
"""gerar.py — monta a Galeria de Estilos Orbe (index.html) nesta pasta.

    python3 galeria/gerar.py [--vitrine <pasta da vitrine>] [--saida <pasta>]

Edição de vídeo gravado: lê <vitrine>/vitrine.json (feito pelo edita-video/scripts/vitrine.py — o MESMO vídeo editado
em cada estilo, mais o bruto) e copia os vídeos/capas para videos/. Sem --vitrine, usa o vitrine.json já guardado aqui.
Motion: motion.json + videos/m-<id>.mp4 (≤ 16 s, 540–720 px). Referências externas (link do estilo) em REFERENCIAS.
Cinema: cinema.json (referências + exemplos) + videos/c-<id>.mp4/.jpg (feitos com edita-video/scripts/montagem.py).
Publicar: Artifact com file_path=index.html e files={"videos/<arquivo>": "<caminho>"} — no MESMO link de galeria.json.
Quem não abre o link da Orbe: publique a própria cópia a partir desta pasta (vai inteira no plugin).
"""
import json, shutil, sys
from pathlib import Path

G = Path(__file__).resolve().parent
A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
OUT = Path(opt('saida') or G); (OUT / 'videos').mkdir(parents=True, exist_ok=True)
REFERENCIAS = {'dossie': {'rotulo': 'Referência: @odossie.br (TikTok)', 'url': 'https://vt.tiktok.com/ZSpM7xHKF/'},
               'minimal': {'rotulo': 'Referência: o "look Arthur Brooks" (vídeo do Joseph)', 'url': 'https://www.youtube.com/watch?v=g9xoKm5DEeU'},
               'podcast-pb': {'rotulo': 'Referência: podcast cinematográfico P&B (vídeo do Rourke)', 'url': 'https://www.youtube.com/watch?v=M59zhPRXg1I'},
               'lifestyle': {'rotulo': 'Referência: @daniirramoss (Instagram)', 'url': 'https://www.instagram.com/reel/DeKQIjRxusy/'},
               'entrevista': {'rotulo': 'Referência: @nicomonteiroo (Instagram)', 'url': 'https://www.instagram.com/reel/DfDOL7Vgp4V/'},
               'documentario-continuo': {'rotulo': 'Referência: documentário contínuo (vídeo do Zane Hoyer)', 'url': 'https://www.youtube.com/watch?v=e2Fykz51Nxg'}}
vit = opt('vitrine')
if vit:
    V = Path(vit); vj = json.loads((V / 'vitrine.json').read_text())
    for it in vj['itens']:
        for k in ('video', 'capa'):
            if it.get(k) and (V / it[k]).exists(): shutil.copy(V / it[k], OUT / it[k])
    (G / 'vitrine.json').write_text(json.dumps(vj, ensure_ascii=False, indent=1), encoding='utf-8')
vj = json.loads((G / 'vitrine.json').read_text()) if (G / 'vitrine.json').exists() else {'itens': []}
ordem = ['bruto', 'minimal', 'dossie', 'podcast-pb', 'lifestyle', 'entrevista', 'dinamico', 'clinica-premium', 'educativo', 'luxo', 'varejo']
edicao = sorted([dict(e, ref=REFERENCIAS.get(e['id'])) for e in vj['itens'] if (OUT / e['video']).exists()], key=lambda e: ordem.index(e['id']) if e['id'] in ordem else 99)
motion = json.loads((G / 'motion.json').read_text())
for m in motion:
    m['video'] = f"videos/m-{m['id']}.mp4"; m['cmd'] = f"/novo-motion no estilo {m['id']}"
    m.setdefault('credito', 'claude-video · Felipe Borges'); m['ref'] = REFERENCIAS.get(m['id'])
if not any(m['id'] == 'serie-personagem' for m in motion):
    motion.insert(1, {'id': 'serie-personagem', 'nome': 'Série com personagem', 'familia': 'Personagem e série', 'som': True,
                      'chamada': 'Um personagem que fala com voz, boca sincronizada e legenda palavra a palavra; um episódio por arquivo',
                      'duracao': 13, 'formato': '9:16', 'video': 'videos/m-serie-personagem.mp4', 'cmd': '/novo-motion série com personagem', 'credito': 'Orbe · motion-studio'})
cin = json.loads((G / 'cinema.json').read_text()) if (G / 'cinema.json').exists() else {'referencias': [], 'itens': []}
refs = {r['handle']: r for r in cin['referencias']}
for c in cin['itens']:
    c['video'] = f"videos/c-{c['id']}.mp4"; c['capa'] = f"videos/c-{c['id']}.jpg"; c['cmd'] = f"/edit-cinema receita {c['id']}"
    r = refs.get(c.get('ref') or ''); c['ref'] = {'rotulo': f"Referência: {r['handle']} (Instagram)", 'url': r['url']} if r else None
D = {'projeto': vj.get('projeto', ''), 'edicao': edicao, 'motion': [m for m in motion if (OUT / m['video']).exists()],
     'cinema': [c for c in cin['itens'] if (OUT / c['video']).exists()], 'cinema_refs': cin['referencias']}
tpl = (G / 'tpl.html').read_text(encoding='utf-8')
(OUT / 'index.html').write_text(tpl.replace('__DADOS__', json.dumps(D, ensure_ascii=False).replace('</', '<\\/')), encoding='utf-8')
mb = sum(f.stat().st_size for f in (OUT / 'videos').glob('*')) / 1e6
print(f"✔ {OUT / 'index.html'} · {len(D['edicao'])} edição · {len(D['motion'])} motion · {len(D['cinema'])} cinema · vídeos {mb:.1f} MB")
