#!/usr/bin/env python3
"""tabela.py — roteiro.json → roteiro.js (o filme lê) + docs/BATIDAS.md (a TABELA DE BATIDAS para aprovar ANTES de animar).

    python3 scripts/tabela.py

Tabela: tempo → narração → o ÚNICO herói na tela → texto na tela → gesto na palavra. Mostre ao usuário e pergunte o que
estiver vago antes de renderizar (regra do prompt de documentário). Rode de novo a cada mudança no roteiro.
"""
import json, os
R = json.load(open('roteiro.json', encoding='utf-8'))
open('roteiro.js', 'w', encoding='utf-8').write('// GERADO por scripts/tabela.py a partir de roteiro.json — edite o JSON\nwindow.ROTEIRO = ' + json.dumps(R, ensure_ascii=False) + ';\n')
N = None
if os.path.exists('narracao.js'):
    s = open('narracao.js', encoding='utf-8').read(); N = json.loads(s[s.index('=') + 1:].strip().rstrip(';'))
T = {f['id']: f for f in (N or {}).get('falas', [])}
OB = {o['id']: o for o in R['objetos']}
def txt(o):
    return ' · '.join(str(o[k]) for k in ('rotulo', 'titulo', 'campo', 'cabeca', 'manchete', 'valor', 'carimbo') if o.get(k))
L = [f"# Tabela de batidas — {R.get('titulo', '')}", '', 'Uma fala = UM herói. O resto escurece. Cada frase aparece UMA vez (documento OU texto).', '',
     '| quando | narração | herói | texto na tela | gesto na palavra | câmera |', '|---|---|---|---|---|---|']
for f in R['falas']:
    h = f.get('heroi', {}); t = T.get(f['id'])
    quando = f"{t['t0']:.1f}–{t['t1']:.1f}s" if t else '(rode narrar.py)'
    if h.get('ano'): her, tx = f"ano {h['ano']}", h['ano']
    elif h.get('titulo'): her, tx = 'título final', h['titulo']
    else: o = OB.get(h.get('obj'), {}); her = f"{o.get('tipo', '?')} «{o.get('id')}»" + (f" + {', '.join(h.get('e', []))}" if h.get('e') else ''); tx = txt(o)
    gesto = ' · '.join(f"{k} em «{v['palavra']}»" for k, v in h.items() if isinstance(v, dict) and v.get('palavra')) or '—'
    cam = f.get('camera', {}); cam_s = (f"em {cam['obj']}" if cam.get('obj') else f"{cam.get('lon')},{cam.get('lat')}") + f" ×{cam.get('zoom', 1)}"
    L.append(f"| {quando} | {f['texto']} | {her} | {tx} | {gesto} | {cam_s} |")
os.makedirs('docs', exist_ok=True); open('docs/BATIDAS.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))
