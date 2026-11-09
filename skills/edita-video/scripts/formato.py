#!/usr/bin/env python3
"""formato.py — FORMATOS REPETÍVEIS: a edição que deu certo vira molde para os próximos vídeos (do cliente ou da Orbe).

    python3 formato.py <projeto> salvar <nome> [--nota "por que funcionou"]   # guarda o formato do projeto aprovado
    python3 formato.py <projeto> usar <nome>                                   # aplica num projeto novo (antes do mapa)
    python3 formato.py <projeto> listar

Guarda: estilo + ajustes do briefing (legenda, câmera, cor, som, ritmo), formato/duração, e o PADRÃO do mapa — a
sequência de batidas com a peça, o modo, a junção, a posição e os parâmetros de forma (sem o texto), mais em que
fração do vídeo cada uma cai. Onde: <kit do cliente>/formatos/<nome>.json (com cliente_kit no briefing) ou
~/.config/orbe/formatos/<nome>.json. "usar" grava estilo/ajustes no briefing e escreve docs/FORMATO.md com o padrão
para o Claude montar o mapa do vídeo novo em cima da transcrição nova (mesmas batidas, palavras novas).
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
if len(A) < 2: E.die(__doc__)
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0]); CMD = A[1]
B, EST, ESTILO = E.config(P)
DIR = (Path(B['cliente_kit']) / 'formatos') if B.get('cliente_kit') else Path.home() / '.config/orbe/formatos'
FORMA = ('forma', 'tag', 'total', 'look', 'fundo', 'icone', 'alinha', 'lado', 'tamanho', 'em', 'raio')

if CMD == 'listar':
    fs = sorted(DIR.glob('*.json'))
    print('\n'.join(f"- {f.stem}: {(E.jload(f, {}) or {}).get('nota', '')}" for f in fs) or f'nenhum formato em {DIR}'); sys.exit()

if CMD == 'salvar':
    nome = A[2] if len(A) > 2 else E.die('formato.py . salvar <nome>')
    tl = E.jload(P / '_edit/timeline.json') or E.die('projeto sem timeline'); DUR = tl['duracao']
    mapa = E.jload(P / '_edit/mapa.json', {}) or {}
    padrao = []
    for it in sorted([i for i in mapa.get('itens', []) if i.get('t_ini') is not None], key=lambda x: x['t_ini']):
        pr = it.get('params', {}) or {}
        padrao.append({'batida': it.get('batida'), 'tipo': it['tipo'], 'peca': it.get('peca'), 'efeito': it.get('efeito'), 'modo': it.get('modo'),
                       'transicao': it.get('transicao'), 'posicao': it.get('posicao'), 'fundo': it.get('fundo'),
                       'forma': {k: pr[k] for k in FORMA if k in pr}, 'em': round(it['t_ini'] / DUR, 3), 'dur': round(it['t_fim'] - it['t_ini'], 2),
                       'exemplo': (it.get('texto') or pr.get('texto') or ' / '.join(str(x) for x in (pr.get('linhas') or [])[:2]) or pr.get('valor') or pr.get('titulo') or '')[:60]})
    d = {'nome': nome, 'nota': opt('nota', ''), 'criado': datetime.date.today().isoformat(), 'origem': P.name,
         'estilo': ESTILO, 'ajustes': B.get('ajustes', {}), 'formato': B.get('formato'), 'duracao_alvo': B.get('duracao') or round(DUR),
         'padrao': padrao, 'gancho_sem_item': mapa.get('gancho_sem_item', False)}
    DIR.mkdir(parents=True, exist_ok=True); E.jsave(DIR / f'{nome}.json', d)
    print(f"✔ formato \"{nome}\" salvo em {DIR / (nome + '.json')} · {len(padrao)} passos · estilo {ESTILO}"); sys.exit()

if CMD == 'usar':
    nome = A[2] if len(A) > 2 else E.die('formato.py . usar <nome>')
    f = DIR / f'{nome}.json'
    if not f.exists(): E.die(f'formato {nome} não existe em {DIR} (formato.py . listar)')
    d = E.jload(f)
    B['estilo'] = d['estilo']; B['ajustes'] = {**(d.get('ajustes') or {}), **(B.get('ajustes') or {})}
    if d.get('formato') and not B.get('formato'): B['formato'] = d['formato']
    B['formato_molde'] = nome; E.jsave(P / '_edit/briefing.json', B)
    L = [f"# Formato \"{nome}\" (de {d['origem']}, {d['criado']})", '', d.get('nota') or '', '',
         f"Estilo {d['estilo']} · duração alvo ~{d['duracao_alvo']} s · ajustes do briefing aplicados.", '',
         'Monte o mapa do vídeo NOVO com a mesma sequência de batidas (palavras novas, tempos novos — a fração é só guia):', '',
         '| # | ~em | batida | peça/efeito | modo | junção | posição | forma | exemplo no original |', '|---|---|---|---|---|---|---|---|---|']
    L += [f"| {k + 1} | {int(100 * x['em'])}% | {x.get('batida') or '—'} | {x.get('peca') or x.get('efeito') or x['tipo']} | {x.get('modo') or '—'} | {x.get('transicao') or '—'} | "
          f"{x.get('posicao') or '—'} | {json.dumps(x.get('forma') or {}, ensure_ascii=False)} | {x.get('exemplo', '')} |" for k, x in enumerate(d['padrao'])]
    L += ['', 'Depois: `mapa.py .` → `ritmo.py .` (confere batidas/ritmo do estilo) → motion → som → final.']
    (P / 'docs').mkdir(exist_ok=True); (P / 'docs/FORMATO.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L)); sys.exit()
E.die(__doc__)
