#!/usr/bin/env python3
"""vitrine.py — o MESMO vídeo editado em vários estilos, para escolher olhando (galeria de estilos ou cliente).

    python3 vitrine.py <projeto> [--estilos minimal,dinamico,clinica-premium,educativo,luxo,varejo] [--mapas <pasta>]
                       [--saida <pasta>] [--so-exportar]

Pré-requisito: projeto com cortes aprovados e rosto.py rodado (a vitrine não refaz o corte — todos os estilos partem
do mesmo corte, para a comparação ser justa). Para cada estilo:
  · cria a pasta irmã <projeto>-<estilo> (arquivos grandes por link, sem duplicar disco), grava o estilo no briefing;
  · usa o mapa daquele estilo (<mapas>/<estilo>.json; padrão <projeto>/_edit/mapas/) — escreva um mapa POR ESTILO
    com as peças que são a assinatura dele (minimal: aspas/linha/gráfico; educativo: lista/número; luxo: pouco e lento…);
    sem mapa próprio, usa o mapa do projeto;
  · roda câmera → legendas → assets (auto) → motion → som → final.py (com QA);
  · exporta a prévia (540 px, H.264 + AAC) e a capa para <saida>/videos/e-<estilo>.mp4 e grava <saida>/vitrine.json
    (o que muda em cada estilo: legenda, câmera, cor, cenas, som) — a galeria (galeria/gerar.py) lê esse arquivo.
Também exporta o BRUTO (e-bruto.mp4) para comparar. Mostrar ao cliente: publique a galeria (Artifact) com a vitrine.
"""
import sys, os, json, shutil, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0])
S = Path(__file__).parent
TODOS = ['minimal', 'dossie', 'podcast-pb', 'lifestyle', 'entrevista', 'dinamico', 'clinica-premium', 'educativo', 'luxo', 'varejo']
estilos = (opt('estilos') or ','.join(TODOS)).split(',')
MAPAS = Path(opt('mapas') or P / '_edit/mapas')
OUT = Path(opt('saida') or P / 'entregas/vitrine'); (OUT / 'videos').mkdir(parents=True, exist_ok=True)
EJ = E.jload(E.SKILL / 'assets/estilos.json', {})
NOMES = {'minimal': 'Minimal premium', 'dossie': 'Dossiê', 'podcast-pb': 'Podcast P&B', 'lifestyle': 'Lifestyle editorial', 'entrevista': 'Entrevista cinematográfica', 'dinamico': 'Dinâmico', 'clinica-premium': 'Clínica premium', 'educativo': 'Educativo', 'luxo': 'Luxo', 'varejo': 'Varejo e oferta'}
CHAMADA = {'minimal': 'Papel, serifa itálica e uma cor fosca: aspas, linha e gráfico alternando com o rosto',
           'dossie': 'Tarjas pretas e etiquetas amarelas de papel rasgado, faixa vermelha, a conta em quadradinhos e colagem com fita',
           'podcast-pb': 'Preto e branco com grão, legenda que se monta palavra a palavra, palavras gigantes atrás da cabeça e quebra com reverb',
           'lifestyle': 'Gancho gigante que se empilha, legenda de uma palavra em serifa, rótulos creme em sans + manuscrita no espaço livre e card de documento',
           'entrevista': 'Luz de cinema, legenda pequena em escada, cartelas de respiro com a fala escrita e fim em fade para o preto',
           'dinamico': 'Caixa alta palavra a palavra, zoom alternado e punch-in, peça a cada poucos segundos',
           'clinica-premium': 'Sóbrio e confiável: placas claras, zoom discreto, som de cuidado',
           'educativo': 'Cards, números e listas que explicam enquanto a pessoa fala',
           'luxo': 'Lento e elegante, legenda mínima, placas claras e poucas peças, impacto só nas revelações',
           'varejo': 'Energia de oferta: números grandes, cor quente, chamada forte no fim'}
BOM = {'minimal': 'Médico, advogado, mentor, educativo de alto valor', 'dossie': 'Dados, mercado, resultado de cliente, opinião, "fizemos a conta"',
       'podcast-pb': 'Podcast, entrevista, opinião forte, bastidor', 'lifestyle': 'Educadoras, mentoras, estética, nutrição, bem-estar',
       'entrevista': 'Autoridade, opinião, negócios, advogados, consultores', 'dinamico': 'Retenção, opinião, dica rápida',
       'clinica-premium': 'Clínicas, médicos, saúde (CFM)', 'educativo': 'Aula curta, passo a passo, tutorial',
       'luxo': 'Concessionária premium, joalheria, imóveis', 'varejo': 'Loja, promoção, lançamento'}

def py(script, d, *a, check=True):
    r = subprocess.run([sys.executable, str(S / script), str(d), *a], capture_output=True, text=True)
    if r.returncode and check: print(f'  ✗ {script}: {(r.stderr or r.stdout)[-600:]}')
    return r

def copiar(dst):
    if dst.exists(): shutil.rmtree(dst)
    def lnk(a, b):      # só a mídia que ninguém reescreve vai por link (brutos e mezanino); o resto é cópia própria
        if ('/brutos/' in a or '/_edit/mez/' in a):
            try: os.link(a, b); return b
            except OSError: pass
        return shutil.copy2(a, b)
    shutil.copytree(P, dst, ignore=shutil.ignore_patterns('renders', 'entregas', 'motion'), copy_function=lnk)
    (dst / 'renders').mkdir(exist_ok=True)

def resumo(est):
    LG, CA, SO, MO = est['legendas'], est['camera'], est['som'], est['motion']
    leg = ('cinematográfica (chave grande em serifa)' if LG.get('layout') == 'cinema' else 'serifa itálica discreta; o soco vai nas etiquetas' if LG.get('italico') else
           'se monta palavra a palavra; chave em serifa itálica' if LG.get('animacao') == 'monta' else
           f"{LG['palavras']} palavras, {'CAIXA ALTA' if LG.get('caixa') == 'alta' else 'frase'}, {LG.get('animacao')}")
    z = CA.get('zoom_alterna', [1, 1])
    return {'Legenda': leg, 'Câmera': f"zoom {int(z[0] * 100)}↔{int(z[1] * 100)}%" + (f", punch +{CA['punch'] * 100:.1f}%" if CA.get('punch') else ', sem punch'),
            'Cor': (est.get('cor') or {}).get('preset', 'natural'), 'Cenas': f"{MO['por_minuto'][0]}–{MO['por_minuto'][1]} por minuto" + (f" · look {MO['look']}" if MO.get('look') else ''),
            'Som': f"{SO.get('sfx')} · trilha {SO.get('trilha_estilo', '')} {SO.get('musica_db', '')} dB".strip()}

def exportar(src, dst, capa_t=None):
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-vf', 'scale=540:-2,fps=30', '-c:v', 'libx264', '-preset', 'slow', '-crf', '26',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-ac', '2', '-movflags', '+faststart', str(dst)])
    if capa_t is not None:
        E.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{capa_t:.2f}', '-i', str(src), '-frames:v', '1', '-vf', 'scale=540:-2', '-q:v', '4', str(dst.with_suffix('.jpg'))])

itens = []
# bruto
bruto = next(iter(sorted((P / 'brutos').glob('*'))), None)
if bruto:
    exportar(bruto, OUT / 'videos/e-bruto.mp4', 1.0)
    itens.append({'id': 'bruto', 'nome': 'Bruto (sem edição)', 'chamada': 'O vídeo como chegou: é daqui que todos os estilos partem.', 'bom': '', 'video': 'videos/e-bruto.mp4',
                  'capa': 'videos/e-bruto.jpg', 'muda': {}, 'bruto': True})
for est in estilos:
    d = P.parent / f'{P.name}-{est}'
    print(f'── {est} → {d.name}', flush=True)
    if '--so-exportar' not in A:
        copiar(d)
        b = E.jload(d / '_edit/briefing.json', {}) or {}; b['estilo'] = est; b.pop('ajustes', None); E.jsave(d / '_edit/briefing.json', b)
        m = MAPAS / f'{est}.json'
        if m.exists(): shutil.copy(m, d / '_edit/mapa.json')
        py('mapa.py', d)
        mp = E.jload(d / '_edit/mapa.json', {}) or {}
        if any(it.get('tipo') in ('broll', 'foto') and not it.get('arquivo') for it in mp.get('itens', [])):
            py('ativos.py', d, 'buscar', check=False); py('ativos.py', d, 'auto', check=False); py('mapa.py', d)
        py('camera.py', d); py('legendas.py', d)
        if any(it.get('tipo') in ('motion', 'texto') for it in mp.get('itens', [])):
            py('motion_ponte.py', d, 'preparar', '--recopiar'); py('motion_ponte.py', d, 'render')
            falta = [it['id'] for it in (E.jload(d / '_edit/mapa.json', {}) or {}).get('itens', []) if it.get('tipo') in ('motion', 'texto') and not it.get('render')]
            if falta: print(f"  ✗ {est}: peças sem render {falta} — veja motion_ponte.py {d.name} render --item {falta[0]}")
        py('eventos.py', d); py('audio.py', d)
        r = py('final.py', d)
        print('\n'.join(l for l in r.stdout.splitlines() if l.startswith(('✔ renders', '- ✗', '- ⚠')))[:1500])
    rend = sorted([f for f in (d / 'renders').glob('*_v[0-9][0-9].mp4') if not f.name.startswith('_')], key=lambda f: f.stat().st_mtime)
    if not rend: print(f'  ✗ {est}: sem render'); continue
    mp = E.jload(d / '_edit/mapa.json', {}) or {}
    capa = next((it['t_ini'] + 0.8 for it in sorted(mp.get('itens', []), key=lambda x: x.get('t_ini', 99)) if it.get('t_ini', 99) > 1.5 and it.get('modo') != 'tela_cheia'), 3.0)   # capa com o rosto, não a cartela
    exportar(rend[-1], OUT / f'videos/e-{est}.mp4', capa)
    estj = dict(EJ.get('_base', {}))
    for k, v in (EJ.get(est) or {}).items(): estj[k] = {**estj[k], **v} if isinstance(v, dict) and isinstance(estj.get(k), dict) else v
    itens.append({'id': est, 'nome': NOMES.get(est, est), 'chamada': CHAMADA.get(est, ''), 'bom': BOM.get(est, ''), 'video': f'videos/e-{est}.mp4',
                  'capa': f'videos/e-{est}.jpg', 'muda': resumo(estj), 'cmd': f'/editar-video estilo={est}',
                  'pecas': sorted({it.get('peca') or it.get('tipo') for it in mp.get('itens', [])})})
E.jsave(OUT / 'vitrine.json', {'projeto': P.name, 'itens': itens})
print(f"✔ vitrine: {len(itens)} vídeos em {OUT}/videos · {OUT}/vitrine.json → galeria: python3 <plugin>/galeria/gerar.py --vitrine {OUT}")
