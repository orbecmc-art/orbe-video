#!/usr/bin/env python3
"""pedidos.py — aplica os pedidos da página de revisão (ou de qualquer lista no mesmo formato) e diz o que re-renderizar.

    python3 pedidos.py <projeto> [_edit/pedidos.json]

Formato: lista de {id?, tipo, alvo, ...} com status "novo":
  legenda   {alvo:"L012", palavras:[#…], texto:"…"}      → correções por palavra (tempo intacto)
  sfx       {alvo:"sfx07", valor:"-3"|"+3"|"off"}          → eventos.py --ajuste
  item      {alvo:"mo04", acao:"antes"|"depois"|"remover"|"texto", valor?} → mapa.json
  corte     {acao:"manter"|"remover", de:#, ate:#}          → cortes.py (destrava se preciso, com registro)
  comentario {alvo, em, texto}                              → docs/PEDIDOS.md (o Claude interpreta e aplica à mão)
  aprovacao {alvo:"v03"}                                    → estado.py aprovar
Escreve _edit/pedidos_aplicados.json (ids aplicados) para o Claude marcar status "aplicado" na página.
"""
import sys, os, json, subprocess, datetime
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0]); F = Path(A[1]) if len(A) > 1 else P / '_edit/pedidos.json'
peds = [p for p in (E.jload(F, []) or []) if p.get('status', 'novo') == 'novo']
if not peds: print('nenhum pedido novo'); sys.exit()
S = E.SKILL / 'scripts'; py = lambda *a: subprocess.run([sys.executable, str(S / a[0]), str(P), *a[1:]])
tl = E.jload(P / '_edit/timeline.json'); W = {w['i']: w for w in tl['palavras']}
mapa = E.jload(P / '_edit/mapa.json', {}) or {}; leg = {b['id']: b for b in (E.jload(P / '_edit/legendas.json', {}) or {}).get('blocos', [])}
refazer = set(); aplic = []; diario = []
corr = E.jload(P / '_edit/correcoes.json', {}) or {}; ajs = []
for p in sorted(peds, key=lambda x: x.get('criado', '')):
    t = p.get('tipo'); pid = p.get('id') or f"{t}:{p.get('alvo')}"
    if t == 'legenda':
        idx = p.get('palavras') or leg.get(p['alvo'], {}).get('palavras', []); novo = p['texto'].split()
        for k, i in enumerate(idx):
            corr[f'#{i}'] = (novo[k] if k < len(novo) else '') + ((' ' + ' '.join(novo[len(idx):])) if k == len(idx) - 1 and len(novo) > len(idx) else '')
        refazer |= {'legendas', 'final'}; aplic.append(pid); diario.append(f"{p['alvo']}: legenda → “{p['texto']}”")
    elif t == 'sfx':
        ajs.append(f"{p['alvo']}={p['valor']}"); refazer |= {'som', 'final'}; aplic.append(pid); diario.append(f"{p['alvo']}: som {p['valor']}")
    elif t == 'item':
        it = next((x for x in mapa.get('itens', []) if x['id'] == p['alvo']), None)
        if not it: diario.append(f"⚠ {p['alvo']} não existe mais no mapa"); continue
        if p['acao'] == 'remover': mapa['itens'] = [x for x in mapa['itens'] if x['id'] != p['alvo']]
        elif p['acao'] in ('antes', 'depois'):
            d = -0.5 if p['acao'] == 'antes' else 0.5; dur = it['t_fim'] - it['t_ini']
            it['de'] = round(max(0, it['t_ini'] + d), 3); it['ate'] = None; it['dur'] = round(dur, 3); it.pop('ate', None)
        elif p['acao'] == 'texto': it['texto'] = p.get('valor', it.get('texto'))
        refazer |= {'mapa', 'motion', 'legendas', 'som', 'final'}; aplic.append(pid); diario.append(f"{p['alvo']}: {p['acao']}")
    elif t == 'corte':
        flag = '--manter' if p['acao'] == 'manter' else '--remover'
        r = subprocess.run([sys.executable, str(S / 'cortes.py'), str(P), flag, f"{p['de']}-{p['ate']}", '--forcar'], capture_output=True, text=True)
        refazer |= {'mapa', 'camera', 'motion', 'legendas', 'som', 'final'}; aplic.append(pid); diario.append(f"corte {p['acao']} #{p['de']}–#{p['ate']} (destravado e refeito)")
    elif t == 'comentario':
        diario.append(f"PEDIDO LIVRE {p.get('alvo')} @{p.get('em', 0):.2f}s: {p.get('texto')}  ← interpretar e aplicar à mão")
    elif t == 'aprovacao':
        py('estado.py', 'aprovar', p.get('alvo', 'versao')); aplic.append(pid); diario.append(f"✔ cliente aprovou {p.get('alvo')}")
E.jsave(P / '_edit/correcoes.json', corr); E.jsave(P / '_edit/mapa.json', mapa)
if ajs: py('eventos.py', '--ajuste', *ajs)
hoje = datetime.date.today().isoformat()
with open(P / 'docs/PEDIDOS.md', 'a', encoding='utf-8') as fh:
    fh.write(f'\n## {hoje}\n' + '\n'.join(f'- {d}' for d in diario) + '\n')
E.jsave(P / '_edit/pedidos_aplicados.json', aplic)
ordem = ['mapa', 'motion', 'camera', 'legendas', 'som', 'final']
cmd = {'mapa': 'mapa.py .', 'motion': 'motion_ponte.py . render', 'camera': 'camera.py .', 'legendas': 'legendas.py .', 'som': 'eventos.py . && audio.py .', 'final': 'final.py .'}
print('\n'.join(f'- {d}' for d in diario))
print('→ refazer, nesta ordem: ' + ' → '.join(cmd[k] for k in ordem if k in refazer))
print(f'→ {len(aplic)} pedido(s) aplicados: marque status "aplicado" na página (ArtifactData update) — ids em _edit/pedidos_aplicados.json')
