#!/usr/bin/env python3
"""estado.py — onde o projeto está, o que vem depois, aprovações e aprendizados (o projeto lembra entre sessões).

    python3 estado.py <projeto>                         # status de cada etapa + próximo comando
    python3 estado.py <projeto> aprovar cortes|mapa|v01 # registra aprovação (cortes aprovados TRAVAM)
    python3 estado.py <projeto> nota "decisão ou motivo" # diário de decisões (docs/DIARIO.md)
    python3 estado.py <projeto> aprendizado "legenda menor no 4:5" --gosto|--oficio [--etapa legendas]

Aprendizado de GOSTO (deste cliente/pessoa) → <kit do cliente>/PERFIL_EDICAO.md (e docs/APRENDIZADOS.md).
Aprendizado de OFÍCIO (vale para todo vídeo) → ~/.config/orbe/edita-video/APRENDIZADOS.md: lido no início de cada
projeto; quando acumular, proponha a atualização da skill (propose_skills) — a skill melhora a cada entrega.
"""
import sys, os, datetime, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0] if A else None); CMD = A[1] if len(A) > 1 else 'status'
est = E.jload(P / '_edit/estado.json', {}) or {}; hoje = datetime.date.today().isoformat()
OFICIO = Path.home() / '.config/orbe/edita-video/APRENDIZADOS.md'
PROX = {
    'briefing': 'perguntas fixas (references/perguntas.md) → briefing.py . chave=valor …',
    'preparar': 'preparar.py .  (inventário, mezanino CFR, transcrição) → leia docs/FRASES.md',
    'cortes': 'cortes.py . → mostre docs/CORTES.md + rascunho (final.py . --rascunho) → aprovar cortes',
    'mapa': 'mapa.py . rascunho → escreva _edit/mapa.json → mapa.py . → plano.py . (página de plano; ou docs/MAPA.md no chat) → plano.py . ler/aplicar → aprovar mapa',
    'assets': 'ativos.py . buscar → ABRA as folhas → ativos.py . escolher br01=a2 …',
    'motion': 'motion_ponte.py . preparar → board (ABRA) → render',
    'camera': 'rosto.py . && camera.py .',
    'legendas': 'legendas.py .  (correções: --corrigir "#12=Rafael")',
    'som': 'eventos.py . && audio.py .',
    'final': 'final.py .  → ABRA as folhas do QA → mostre a v01',
    'entrega': 'revisao.py . (cliente no navegador) · nle.py . (Premiere/Final Cut/DaVinci/CapCut/celular) · docs/ENTREGA.md · aprendizados',
}
if CMD == 'status':
    print(f"# {P.name} — versão atual v{est.get('versao', 0):02d}" + (f" · kit {est.get('cliente_kit')}" if est.get('cliente_kit') else ''))
    prox = None
    for k, v in est.get('etapas', {}).items():
        st = v.get('status', 'pendente'); mark = {'feito': '✔', 'travado': '🔒', 'aprovado': '✔✔', 'parcial': '◐'}.get(st, '·')
        print(f"  {mark} {k:<9} {st}{(' — ' + v['nota']) if v.get('nota') else ''}")
        if st in ('pendente', 'parcial') and not prox: prox = k
    if prox: print(f"\n→ próximo: {prox}: {PROX.get(prox, '')}")
    if OFICIO.exists(): print(f"\nAprendizados de ofício ativos: {OFICIO} (leia antes de editar)")
    d = P / 'docs/DIARIO.md'
    if d.exists(): print('\nÚltimas decisões:\n' + '\n'.join(d.read_text().strip().splitlines()[-3:]))
elif CMD == 'aprovar':
    et = A[2]
    if et == 'cortes': subprocess.run([sys.executable, str(E.SKILL / 'scripts/cortes.py'), str(P), '--travar'])
    est.setdefault('aprovacoes', {})[et] = hoje; E.jsave(P / '_edit/estado.json', est)
    if et in est.get('etapas', {}) and et != 'cortes': E.log_estado(P, et, 'aprovado', hoje)
    print(f'✔ {et} aprovado em {hoje}')
elif CMD == 'nota':
    d = P / 'docs/DIARIO.md'; d.parent.mkdir(exist_ok=True)
    with open(d, 'a', encoding='utf-8') as fh: fh.write(f"- {hoje} · {A[2]}\n")
    print('✔ anotado em docs/DIARIO.md')
elif CMD == 'aprendizado':
    txt = A[2]; etapa = A[A.index('--etapa') + 1] if '--etapa' in A else 'geral'
    linha = f"- [ ] {etapa} · {txt} · {hoje} · ({P.name})\n"
    with open(P / 'docs/APRENDIZADOS.md', 'a', encoding='utf-8') as fh: fh.write(linha)
    if '--oficio' in A:
        OFICIO.parent.mkdir(parents=True, exist_ok=True)
        with open(OFICIO, 'a', encoding='utf-8') as fh: fh.write(linha)
        print(f'✔ ofício → {OFICIO} (vale para todos os projetos; ao juntar 3+, proponha atualizar a skill)')
    else:
        kit = est.get('cliente_kit') or (E.jload(P / '_edit/briefing.json', {}) or {}).get('cliente_kit')
        if kit:
            pf = Path(kit) / 'PERFIL_EDICAO.md'; pf.parent.mkdir(parents=True, exist_ok=True)
            novo = not pf.exists()
            with open(pf, 'a', encoding='utf-8') as fh:
                if novo: fh.write('# Perfil de edição — gosto deste cliente (lido antes de cada vídeo dele)\n\n')
                fh.write(linha)
            print(f'✔ gosto → {pf}')
        else: print('✔ gosto anotado no projeto (sem kit de cliente: defina cliente=… no briefing para levar adiante)')
