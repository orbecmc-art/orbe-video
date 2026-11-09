#!/usr/bin/env python3
"""briefing.py — grava as respostas da SEQUÊNCIA FIXA DE PERGUNTAS (references/perguntas.md) em _edit/briefing.json.

    python3 briefing.py <projeto> formato=9x16 duracao=30 estilo=dinamico|minimal|… referencia=https://… legendas=palavra|frase|cinema plano=pagina \\
        motion=alta broll=buscar sfx=sim trilha=gerar cliente=estudio/brands/x cta="Comenta PELE" termos="Dr. Rafael" \\
        objetivo="..." nome=clinica-pele-oleosa
    python3 briefing.py <projeto> ajuste.camera.punch=0 ajuste.legendas.y=0.6 sem_cortes=sim   # qualquer número do estilo
    python3 briefing.py <projeto> mostrar

Cada resposta vira estilo + ajustes concretos (os números de assets/estilos.json). Regras fixas da Orbe já entram:
fontes/créditos fora da tela (fontes_na_tela=nao, salvo pedido explícito) e conformidade do nicho (saúde: CFM).
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E

A = sys.argv[1:]
P = E.proj(A[0])
b = E.jload(P / '_edit/briefing.json', {}) or {}
kv = dict(re.match(r'^([a-z_.]+)=(.*)$', a, re.S).groups() for a in A[1:] if re.match(r'^[a-z_.]+=', a))
aj = b.setdefault('ajustes', {})
def sub(k): return aj.setdefault(k, {})
for k, v in kv.items():
    v = v.strip()
    if k == 'formato': b['formato'] = {'reels': '9x16', 'vertical': '9x16', 'feed': '4x5', 'quadrado': '1x1', 'youtube': '16x9', 'horizontal': '16x9'}.get(v.lower(), v.lower())
    elif k == 'duracao':
        n = re.findall(r'\d+', v); b['duracao_alvo'] = int(n[0]) if n else None     # "livre" = None (só tira o que é ruim)
    elif k == 'estilo': b['estilo'] = {'minimal-premium': 'minimal', 'premium': 'minimal', 'clean': 'minimal', 'minimalista': 'minimal', 'clinica': 'clinica-premium'}.get(v.lower(), v)
    elif k == 'referencia': b.setdefault('referencias', []).append(v) if v.lower() not in ('nao', 'não', 'nenhuma', '') else b.setdefault('referencias', [])
    elif k == 'legendas':
        if v in ('nenhuma', 'nao', 'não', 'sem'): sub('legendas')['ativo'] = False
        elif v == 'frase': sub('legendas').update(ativo=True, palavras=6, max_car=32, caixa='frase', animacao='fade', tamanho=0.054)
        elif v in ('cinema', 'cinematografica', 'cinematográfica'):      # 2 tamanhos: chave em serifa itálica (estilo minimal)
            sub('legendas').update(ativo=True, layout='cinema', fonte='Inter', peso=500, fonte2='Playfair Display', palavras=4, max_car=30, caixa='frase',
                                   tamanho=0.040, escala_chave=1.9, contorno=0.0, animacao='palavra')
        else: sub('legendas')['ativo'] = True
    elif k == 'motion':
        sub('motion').update({'alta': {'densidade': 'alta', 'por_minuto': [4, 7]}, 'pontual': {'densidade': 'pontual', 'por_minuto': [2, 4]},
                              'abertura_cta': {'densidade': 'abertura_cta', 'por_minuto': [0, 2]}, 'nenhum': {'densidade': 'nenhum', 'por_minuto': [0, 0]}}.get(v, {'densidade': v}))
    elif k == 'broll': b['broll'] = v                      # buscar · meu · ambos · nenhum
    elif k == 'sfx':
        if v in ('nao', 'não', 'sem', 'nenhum'): b['sfx'] = False
        else:
            b['sfx'] = True
            if v in ('discreto', 'moderado', 'intenso'): sub('som')['sfx'] = v
    elif k == 'trilha':
        b['musica'] = 'nenhuma' if v in ('nao', 'não', 'nenhuma', 'sem') else 'gerar' if v in ('sim', 'gerar') else ({'gerar': {'style': v.split(':', 1)[1]}} if v.startswith('gerar:') else v)
    elif k == 'cliente': b['cliente_kit'] = v
    elif k == 'fontes_na_tela': b['fontes_na_tela'] = v.lower() in ('sim', 'true', '1')
    elif k == 'cor': sub('cor')['preset'] = v
    elif k.startswith('ajuste.'):                         # ajuste.camera.punch=0 · ajuste.legendas.y=0.6 · ajuste.camera.zoom_alterna=[1,1]
        _, grupo, chave = k.split('.', 2)
        try: val = __import__('json').loads(v)
        except ValueError: val = v
        sub(grupo)[chave] = val
    elif k == 'sem_cortes': b['sem_cortes'] = v.lower() in ('sim', 'true', '1')
    else: b[k] = v                                       # cta, termos, objetivo, nome, publico, nicho…
b.setdefault('fontes_na_tela', False)
if (b.get('nicho') or '').lower() in ('saude', 'saúde', 'clinica', 'clínica', 'medico', 'médico', 'odonto', 'estetica', 'estética'): b['conformidade'] = 'saude-cfm'
E.jsave(P / '_edit/briefing.json', b)
B, EST, ESTILO = E.config(P)
LGs = 'não' if not EST['legendas'].get('ativo', True) else '%s palavras/bloco, %s, ativa em %s' % (EST['legendas']['palavras'], EST['legendas']['caixa'], EST['legendas']['destaque'])
L = ['# Briefing', '', f"- Objetivo: {b.get('objetivo', '—')}", f"- Formato: {b.get('formato', '9x16')} · duração alvo: {b.get('duracao_alvo') or 'livre (só tira o que é ruim)'}",
     f"- Estilo: **{ESTILO}** — {EST.get('_descricao', '')}", f"- Referência(s): {', '.join(b.get('referencias', [])) or 'nenhuma — segue o estilo'}",
     f"- Legendas: {LGs}",
     f"- Motion: {EST['motion'].get('densidade')} ({EST['motion']['por_minuto'][0]}–{EST['motion']['por_minuto'][1]}/min) · B-roll: {b.get('broll', 'buscar')}",
     f"- Plano de cenas: {({'pagina': 'página de plano (a pessoa aprova linha a linha)', 'claude': 'o Claude decide; revisão no vídeo', 'chat': 'mapa no chat'}).get(b.get('plano', ''), b.get('plano') or 'o Claude decide')}",
     f"- Som: SFX {'não' if b.get('sfx') is False else EST['som'].get('sfx')} · trilha {b.get('musica', 'gerar')} · {EST['som']['lufs']} LUFS",
     f"- Kit do cliente: {b.get('cliente_kit') or '—'} · CTA: {b.get('cta', '—')} · termos: {b.get('termos', '—')}",
     f"- Fontes/créditos na tela: {'SIM (pedido)' if b.get('fontes_na_tela') else 'não (regra Orbe)'}" + (' · conformidade: saúde/CFM' if b.get('conformidade') else '')]
(P / 'docs/BRIEFING.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); print('\n'.join(L))
E.log_estado(P, 'briefing', 'feito')
