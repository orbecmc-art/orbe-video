#!/usr/bin/env python3
"""variacoes.py — VARIAÇÕES DE TESTE (trial reels / criativos A-B) a partir de um vídeo já editado e aprovado.

    python3 variacoes.py <projeto> [--receitas direto,micro,abertura,mudo,pb-cor] [--setup F002-F003]
                         [--linhas F004-F009] [--gancho "texto da nova abertura"] [--saida <pasta>] [--so-previa]

O Instagram (e o Meta Ads) reconhece repost: zoom de 1,02, espelhar ou trocar uma linha NÃO basta. Cada variação muda
ABERTURA, GRÁFICOS ou ESTRUTURA — e testa UMA hipótese com UMA métrica (método Grow with Alex):
  direto    corta o setup (--setup, padrão: as frases entre o gancho e a 1ª virada/número) → payoff mais cedo · skip rate
  micro     só as linhas da demonstração (--linhas) + manchete nova no 1º quadro, fim que volta ao começo · tempo médio + envios
  abertura  abertura NOVA nos 2,5 s iniciais (--gancho; peça diferente da do master) · skip rate
  mudo      para quem vê SEM SOM: a frase-gancho escrita grande nos 3 s iniciais + legenda 15% maior · skip + % assistido
  pb-cor    abre em P&B e a cor escorre na 1ª virada/número (gancho visual) · skip rate + tempo médio
Cada variação vira um projeto irmão <projeto>-v-<receita> (brutos e mezanino por link), roda o pipeline inteiro (motion,
câmera, legendas, som, final com QA) e sai com: o MP4, uma PRÉVIA lado a lado com o master (≤ 10 s, 540 px por lado) e
docs/VARIACOES.md (cartão de teste: hipótese, métrica, o que mudou, regra do vencedor).
Regras do teste: no máximo 5 trial reels por dia; compare trial com trial (nunca com o post normal — público diferente);
vencedor só com ≥ 5 pontos de skip rate ou 1,5× por mil views; empurre o vencedor em até 48 h. Anúncio: mesma lógica,
um conjunto com as variações e orçamento igual.
"""
import sys, os, json, shutil, subprocess, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
if not A: E.die(__doc__)
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0]); S = Path(__file__).parent
RECEITAS = (opt('receitas') or 'direto,abertura,mudo,pb-cor').split(',')
OUT = Path(opt('saida') or P / 'entregas/variacoes'); OUT.mkdir(parents=True, exist_ok=True)
B, EST, ESTILO = E.config(P)
tl = E.jload(P / '_edit/timeline.json') or E.die('o projeto precisa estar editado (falta timeline)')
mapa0 = E.jload(P / '_edit/mapa.json', {}) or {}
words = E.jload(P / '_edit/words.json') or []
rend0 = sorted([f for f in (P / 'renders').glob('*_v[0-9][0-9].mp4') if not f.name.startswith('_')], key=lambda f: f.stat().st_mtime)
if not rend0: E.die('rode final.py no master antes (as variações são comparadas com ele)')
MASTER = rend0[-1]

INFO = {
 'direto': ('Pular o setup segura mais gente?', 'skip rate (3 s)', 'estrutura: começa no payoff'),
 'micro': ('A demonstração sozinha rende mais replays e envios que a aula inteira?', 'tempo médio + envios', 'estrutura: só a demo, fim que emenda no começo'),
 'abertura': ('Uma abertura nova para mais gente nos 2 s iniciais?', 'skip rate (3 s)', 'abertura: peça e texto novos'),
 'mudo': ('Escrever o gancho na tela segura quem vê sem som?', 'skip rate + % assistido', 'gráficos: gancho escrito grande, legenda maior'),
 'pb-cor': ('Abrir sem cor e revelar a cor na virada segura o olhar?', 'skip rate + tempo médio', 'abertura: P&B → cor escorrendo na virada'),
}

def frases_tl():
    out, cur = [], []
    P_ = tl['palavras']
    for k, w in enumerate(P_):
        cur.append(w); nx = P_[k + 1] if k + 1 < len(P_) else None
        if nx is None or re.search(r'[.!?…]$', w['w']) or nx['s'] - w['e'] > 0.5: out.append(cur); cur = []
    return out
FR = frases_tl()
def faixa_fr(s):     # "F002-F004" → índices de palavra (origem) dessas frases da timeline
    m = re.match(r'F?(\d+)(?:-F?(\d+))?', s or '')
    if not m: return []
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    return [w['i'] for f in FR[a - 1:b] for w in f]

def py(script, d, *a, check=True):
    r = subprocess.run([sys.executable, str(S / script), str(d), *a], capture_output=True, text=True)
    if r.returncode and check: print(f'  ✗ {script}: {(r.stderr or r.stdout)[-500:]}')
    return r

def copiar(dst):
    if dst.exists(): shutil.rmtree(dst)
    def lnk(a, b):
        if '/brutos/' in a or '/_edit/mez/' in a:
            try: os.link(a, b); return b
            except OSError: pass
        return shutil.copy2(a, b)
    shutil.copytree(P, dst, ignore=shutil.ignore_patterns('renders', 'entregas', 'motion'), copy_function=lnk)
    (dst / 'renders').mkdir(exist_ok=True)

def payoff_t():
    for it in sorted(mapa0.get('itens', []), key=lambda x: x.get('t_ini', 99)):
        if it.get('batida') in ('virada', 'numero') or it.get('peca') in ('numero', 'slam', 'grafico', 'anel'): return it.get('t_ini')
    return min(4.0, tl['duracao'] * 0.3)

ABREV = {'mil': 'MIL', 'milhao': 'MI', 'milhoes': 'MI', 'bilhao': 'BI', 'bilhoes': 'BI'}
def slam_de(g):
    """'R$ 1 milhão por ano' → valor 'R$ 1 MI' (≤ 7 caracteres) + rótulo 'por ano'; '38 a 45%' → '45%' com o 38 riscado."""
    ms = list(re.finditer(r'(R\$ ?)?(\d[\d.,]*)\s*(%|milh[ãa]o\b|milh[õo]es\b|bilh[ãa]o\b|bilh[õo]es\b|mil\b)?', g, re.I))
    if not ms: return {'valor': g[:6], 'em': 0.3}
    m = next((x for x in reversed(ms) if x.group(3)), ms[-1])
    un = ABREV.get(E.norm(m.group(3) or ''), m.group(3) or '')
    val = f"{m.group(1) or ''}{m.group(2)}{'' if un in ('', '%') else ' '}{un}".strip()
    out = {'valor': val, 'rotulo': re.sub(r'\s+', ' ', g[:m.start()] + g[m.end():]).strip(' ,.-')[:32], 'em': 0.3}
    if len(ms) > 1 and ms[0] is not m:
        out['antes'] = (ms[0].group(1) or '') + ms[0].group(2) + ('%' if (m.group(3) or '') == '%' else ''); out['em'] = 0.5
        out['rotulo'] = re.sub(r'^\S*\s*\ba\b\s*', '', g[m.end():].strip(' ,.-'))[:32] or out['rotulo'].replace(ms[0].group(0).strip(), '').strip(' a')
    return out

def receita(nome, d):
    mp = json.loads(json.dumps(mapa0)); bri = E.jload(d / '_edit/briefing.json', {}) or {}; aj = bri.setdefault('ajustes', {})
    itens = mp.setdefault('itens', []); mudou = []
    if nome == 'direto':
        setup = faixa_fr(opt('setup')) if opt('setup') else []
        if not setup:     # frases entre a 1ª e a 1ª com virada/número
            t_p = payoff_t() or 0
            setup = [w['i'] for f in FR[1:] if f[-1]['e'] <= t_p for w in f]
        if not setup: return None, 'não achei setup para cortar (use --setup F002-F003)'
        txt = ' '.join(w['w'] for w in tl['palavras'] if w['i'] in setup)
        r = py('cortes.py', d, '--forcar', '--remover', ','.join(str(i) for i in setup), check=True)
        mp['itens'] = [it for it in itens if not (isinstance(it.get('de'), str) and it['de'].startswith('#') and int(it['de'][1:]) in setup)]
        mudou.append(f'saiu o setup: "{txt[:120]}"')
    elif nome == 'micro':
        manter = faixa_fr(opt('linhas'))
        if not manter: return None, 'micro precisa de --linhas F004-F009 (as linhas da demonstração)'
        fora = [w['i'] for w in tl['palavras'] if w['i'] not in manter]
        py('cortes.py', d, '--forcar', '--remover', ','.join(str(i) for i in fora))
        mp['itens'] = [it for it in itens if isinstance(it.get('de'), str) and it['de'].startswith('#') and int(it['de'][1:]) in manter and it.get('peca') != 'cta']
        g = opt('gancho') or 'Olha isso'
        mp['itens'].insert(0, {'id': 'vm01', 'tipo': 'motion', 'peca': 'titulo', 'de': f'#{manter[0]}', 'dur': 1.6, 'modo': 'sobreposto', 'posicao': 'topo', 'batida': 'gancho', 'params': {'linhas': [g.upper()]}})
        mudou.append(f'só as linhas {opt("linhas")}; manchete nova no 1º quadro: "{g}"')
    elif nome == 'abertura':
        g = opt('gancho') or ' '.join(w['w'] for w in FR[0])[:40]
        usado = {it.get('peca') for it in itens if it.get('t_ini', 99) < 2.5}
        peca = next((p for p in ('slam', 'pilula', 'palavra', 'titulo') if p not in usado and (p != 'slam' or re.search(r'\d', g))), 'titulo')
        mp['itens'] = [it for it in itens if it.get('t_ini', 99) >= 2.5]
        params = slam_de(g) if peca == 'slam' else {'texto': g} if peca in ('pilula', 'palavra') else {'linhas': [g.upper()]}
        mp['itens'].insert(0, {'id': 'va01', 'tipo': 'motion', 'peca': peca, 'de': f"#{tl['palavras'][0]['i']}", 'dur': 2.2, 'modo': 'sobreposto' if peca != 'slam' else 'tela_cheia',
                               'transicao': 'flash' if peca == 'slam' else None, 'posicao': 'topo', 'batida': 'gancho', 'params': params, **({'texto': g} if peca == 'palavra' else {})})
        mp['itens'][0] = {k: v for k, v in mp['itens'][0].items() if v is not None}
        aj.setdefault('camera', {})['punch_modo'] = 'linha' if EST['camera'].get('punch_modo') != 'linha' else 'tonicas'
        mudou.append(f'abertura nova: {peca} "{g}" (no lugar de {", ".join(sorted(x for x in usado if x)) or "rosto puro"}); punch mudou para {aj["camera"]["punch_modo"]}')
    elif nome == 'mudo':
        g = opt('gancho') or ' '.join(w['w'] for w in FR[0])
        g = ' '.join(g.split()[:9])
        mp['itens'] = [it for it in itens if it.get('t_ini', 99) >= 3.2]
        mp['itens'].insert(0, {'id': 'vs01', 'tipo': 'motion', 'peca': 'titulo', 'de': f"#{tl['palavras'][0]['i']}", 'dur': 3.0, 'modo': 'sobreposto', 'posicao': 'topo', 'batida': 'gancho',
                               'params': {'linhas': [g.upper()], 'tamanho': 96}})
        lg = aj.setdefault('legendas', {}); lg['tamanho'] = round(float(EST['legendas'].get('tamanho', 0.06)) * 1.15, 4)
        mudou.append(f'gancho escrito nos 3 s iniciais: "{g}"; legenda 15% maior')
    elif nome == 'pb-cor':
        t_p = payoff_t() or 2.5
        w_alvo = min(tl['palavras'], key=lambda w: abs(w['s'] - t_p))
        mp['itens'].append({'id': 'vp01', 'tipo': 'efeito', 'efeito': 'pb', 'de': f"#{tl['palavras'][0]['i']}", 'ate': f"#{w_alvo['i']}"})
        mudou.append(f'abre em P&B; a cor escorre em {E.tc(w_alvo["s"])} («{w_alvo["w"]}»)')
    else: return None, f'receita desconhecida: {nome}'
    E.jsave(d / '_edit/mapa.json', mp); E.jsave(d / '_edit/briefing.json', bri)
    return mudou, None

cartoes = []
for nome in RECEITAS:
    d = P.parent / f'{P.name}-v-{nome}'; print(f'── {nome} → {d.name}', flush=True)
    if '--so-previa' not in A:
        copiar(d); mudou, erro = receita(nome, d)
        if erro: print(f'  ✗ {erro}'); continue
        py('mapa.py', d); py('camera.py', d); py('legendas.py', d)
        mp = E.jload(d / '_edit/mapa.json', {}) or {}
        if any(it.get('tipo') in ('motion', 'texto') for it in mp.get('itens', [])):
            py('motion_ponte.py', d, 'preparar', '--recopiar'); py('motion_ponte.py', d, 'render')
        py('eventos.py', d); py('audio.py', d)
        r = py('final.py', d); print('\n'.join(l for l in r.stdout.splitlines() if l.startswith(('✔ renders', '- ✗')))[:800])
    else: mudou = ['(prévia refeita)']
    rv = sorted([f for f in (d / 'renders').glob('*_v[0-9][0-9].mp4') if not f.name.startswith('_')], key=lambda f: f.stat().st_mtime)
    if not rv: print(f'  ✗ {nome}: sem render'); continue
    final = OUT / f'{P.name}-{nome}.mp4'; shutil.copy(rv[-1], final)
    prev = OUT / f'previa-{nome}.mp4'
    E.run(['ffmpeg', '-y', '-v', 'error', '-t', '10', '-i', str(MASTER), '-t', '10', '-i', str(rv[-1]), '-filter_complex',
           "[0:v]scale=540:-2,drawtext=text='MASTER':x=24:y=24:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10[a];"
           f"[1:v]scale=540:-2,drawtext=text='{nome.upper()}':x=24:y=24:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10[b];[a][b]hstack=2[v]",
           '-map', '[v]', '-map', '1:a?', '-c:v', 'libx264', '-crf', '24', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-shortest', str(prev)])
    h, m_, o = INFO[nome]
    cartoes.append({'receita': nome, 'arquivo': final.name, 'previa': prev.name, 'hipotese': h, 'metrica': m_, 'muda': o, 'detalhe': mudou})
    print(f'  ✔ {final.name} · prévia {prev.name}')

L = [f'# Variações de teste — {P.name}', '', f'Master: `{MASTER.name}` · estilo {ESTILO}', '',
     '| variação | hipótese | métrica | o que muda (não é repost) |', '|---|---|---|---|']
L += [f"| **{c['receita']}** ({c['arquivo']}) | {c['hipotese']} | {c['metrica']} | {c['muda']}: {'; '.join(c['detalhe'])} |" for c in cartoes]
L += ['', '## Como rodar o teste', '',
      '- Instagram: publique como **trial reel** (não vai para os seguidores; 72 h para julgar). No máximo 5 por dia.',
      '- Compare trial com trial — nunca com o post normal (público diferente).',
      '- Vencedor só com diferença clara: **≥ 5 pontos de skip rate** ou **1,5× por mil views** na métrica da variação. Diferença pequena é ruído.',
      '- Achou o vencedor: empurre (post normal ou anúncio) em até **48 h**; leve o aprendizado para o perfil do cliente (`estado.py . aprendizado`).',
      '- Anúncio (Meta Ads): as variações viram anúncios do mesmo conjunto, orçamento igual, mesma janela; a métrica é a da variação (hook rate / ThruPlay / CTR).',
      '- Mexa em UMA coisa por variação: abertura, comprimento/estrutura, visual ou fim — se mudar tudo, não dá para saber o que funcionou.']
(OUT / 'VARIACOES.md').write_text('\n'.join(L) + '\n', encoding='utf-8'); (P / 'docs').mkdir(exist_ok=True); (P / 'docs/VARIACOES.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
E.jsave(OUT / 'variacoes.json', cartoes)
print(f"✔ {len(cartoes)} variação(ões) em {OUT} · cartão de teste em docs/VARIACOES.md")
