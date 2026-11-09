#!/usr/bin/env python3
"""planos.py — LISTA DE PLANOS (decupagem) para o cliente gravar sozinho com o celular, ANTES da edição.

    python3 planos.py <pasta> modelo <contexto> [--titulo "…"] [--alvo 30]   # rascunho em _edit/planos.json
    python3 planos.py <pasta> [--cliente "Dra. Ana"]                          # valida + docs/PLANOS.md + docs/planos/index.html

Contextos do modelo: historia · clinica · loja · escritorio · restaurante · imovel · produto (assets/planos.json).
O rascunho traz a sequência de planos do contexto com a AÇÃO a preencher — o Claude escreve as ações da história do
cliente (cada plano = uma ação concreta, com objeto e lugar), agrupa em cenas e roda de novo para validar e gerar a página.

_edit/planos.json: {"titulo", "contexto", "alvo_s", "planos": [{"tipo": "geral-cima", "cena": 1, "acao": "…", "grave_s": 4,
                    "nota": "…", "rotulo": true}]}
Validação (gramática de references/decupagem.md, aprendida do "how to film yourself"):
  · cada cena abre com um plano que ESTABELECE (geral de cima/de baixo/reto) — senão quem assiste não sabe onde está;
  · a cena tem ≥ 2 ângulos da mesma ação (corte na ação) e pelo menos um DETALHE e uma REAÇÃO no vídeo;
  · dois planos seguidos com mesma altura E mesma distância viram "pulo" — mude um dos dois;
  · tempo de tela ≈ 1–2 s por plano na montagem; grave 3–5 s de cada (folga para cortar na ação).
Saída: docs/PLANOS.md (texto) e docs/planos/index.html (página pronta para publicar como Artifact e mandar ao cliente:
um cartão por plano com o esquema da câmera — altura, distância, direção — a ação, para que serve, a dica de celular e
uma caixinha para marcar). Regras Orbe/CFM: paciente só com consentimento por escrito; sem antes/depois.
"""
import sys, os, json, html, math
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = Path(A[0]).resolve() if A and not A[0].startswith('--') else Path.cwd()
(P / '_edit').mkdir(parents=True, exist_ok=True); (P / 'docs').mkdir(exist_ok=True)
CAT = E.jload(E.SKILL / 'assets/planos.json')
PL, CTX = CAT['planos'], CAT['contextos']
ARQ = P / '_edit/planos.json'

if 'modelo' in A:
    ctx = A[A.index('modelo') + 1] if len(A) > A.index('modelo') + 1 else 'historia'
    if ctx not in CTX: E.die(f"contexto '{ctx}' não existe — use: {', '.join(CTX)}")
    seq = CTX[ctx]['seq']; cena = 1; out = []
    for k, t in enumerate(seq):
        if k and PL[t]['familia'] == 'estabelece' and PL[seq[k - 1]]['familia'] != 'estabelece': cena += 1
        out.append({'tipo': t, 'cena': cena, 'acao': f"PREENCHER — {PL[t]['funcao']}", 'grave_s': 4})
    d = {'titulo': opt('titulo', CTX[ctx]['titulo']), 'contexto': ctx, 'alvo_s': float(opt('alvo', 30)), 'planos': out}
    if ARQ.exists() and '--sobrescrever' not in A: E.die(f'{ARQ} já existe (use --sobrescrever)')
    E.jsave(ARQ, d)
    print(f"✔ rascunho {ARQ} · {len(out)} planos ({ctx}) — escreva a AÇÃO de cada um (o que acontece, com que objeto, onde)\n"
          f"  e rode `planos.py {P}` para validar e gerar a página do cliente.")
    sys.exit()

D = E.jload(ARQ) or E.die(f'escreva {ARQ} (ou `planos.py {P} modelo <contexto>`)')
ps = D.get('planos', []); erros, avisos = [], []
for i, p in enumerate(ps, 1):
    p['n'] = i
    if p.get('tipo') not in PL: erros.append(f"plano {i}: tipo '{p.get('tipo')}' não existe — use {', '.join(PL)}"); continue
    if 'PREENCHER' in str(p.get('acao', '')): avisos.append(f"plano {i} ({PL[p['tipo']]['nome']}): ação ainda não escrita")
if erros: print('\n'.join('✗ ' + e for e in erros)); sys.exit(1)
cenas = {}
for p in ps: cenas.setdefault(p.get('cena', 1), []).append(p)
for c, xs in cenas.items():
    if PL[xs[0]['tipo']]['familia'] != 'estabelece': avisos.append(f"cena {c}: abre com {PL[xs[0]['tipo']]['nome']} — abra com um plano que estabelece (geral de cima/de baixo/reto)")
    if len(xs) < 2: avisos.append(f"cena {c}: um plano só — grave a mesma ação de 2 ângulos para poder cortar NA ação")
fams = {PL[p['tipo']]['familia'] for p in ps}
if 'detalhe' not in fams: avisos.append('nenhum DETALHE (inserto de cima, textura, objeto) — é o plano que mostra o que a fala cita')
if 'reacao' not in fams: avisos.append('nenhuma REAÇÃO (médio de baixo, perfil, contra-POV) — sem reação a história não tem emoção')
for a, b in zip(ps, ps[1:]):
    pa, pb = PL[a['tipo']], PL[b['tipo']]
    if pa['altura'] == pb['altura'] and pa['distancia'] == pb['distancia'] and a['tipo'] == b['tipo']:
        avisos.append(f"planos {a['n']}→{b['n']}: mesmo plano seguido ({pa['nome']}) vira pulo — troque altura ou distância de um")
tela = sum(1.5 for _ in ps); grav = sum(float(p.get('grave_s', 4)) for p in ps)
alvo = float(D.get('alvo_s', 30))
if tela < alvo * 0.6: avisos.append(f"{len(ps)} planos ≈ {tela:.0f} s de montagem para um vídeo de {alvo:.0f} s — faltam planos (ou a fala cobre o resto)")

# ── esquema da câmera (SVG): pessoa à direita, celular na altura/distância do plano, cone de visão ──
XD = {'detalhe': 70, 'close': 62, 'medio': 48, 'americano': 38, 'geral': 18}
YA = {'chao': 72, 'cintura': 52, 'peito': 44, 'olho': 33, 'alto': 9}
def esquema(t):
    c = PL[t]; ang = c['angulo']; px = 92
    x, y = XD[c['distancia']], YA[c['altura']]
    if ang == 'pov': x, y = px - 6, 31
    if ang == 'cima' and c['distancia'] in ('detalhe', 'close'): x = 76
    alvo = (78, 56) if c['familia'] == 'detalhe' or t == 'mesa' else (px, 46 if c['distancia'] in ('geral', 'americano') else 36)
    if ang == 'pov': alvo = (78, 54)
    dx, dy = alvo[0] - x, alvo[1] - y; n = max(1e-6, (dx * dx + dy * dy) ** 0.5); ux, uy = dx / n, dy / n
    L = min(n + 6, 46); sp = 0.42 if c['distancia'] in ('geral', 'americano') else 0.26
    a1 = (x + L * (ux * 1 - uy * sp), y + L * (uy * 1 + ux * sp)); a2 = (x + L * (ux * 1 + uy * sp), y + L * (uy * 1 - ux * sp))
    return (f'<svg viewBox="0 0 120 84" class="esq" aria-hidden="true">'
            f'<line x1="4" y1="78" x2="116" y2="78" class="chao"/>'
            f'<rect x="64" y="58" width="22" height="3" rx="1" class="mesa"/>'
            f'<circle cx="{px}" cy="30" r="6" class="pes"/><path d="M{px - 7} 76 L{px - 6} 42 Q{px} 37 {px + 6} 42 L{px + 7} 76 Z" class="pes"/>'
            f'<path d="M{x:.1f} {y:.1f} L{a1[0]:.1f} {a1[1]:.1f} L{a2[0]:.1f} {a2[1]:.1f} Z" class="cone"/>'
            f'<rect x="{x - 3:.1f}" y="{y - 5:.1f}" width="6" height="10" rx="1.6" class="cel" transform="rotate({math.degrees(math.atan2(uy, ux)) + 90:.0f} {x:.1f} {y:.1f})"/>'
            f'</svg>')

# ── MD ──
M = [f"# Lista de planos — {D.get('titulo', '')}", '',
     f"{len(ps)} planos · {len(cenas)} cena(s) · ~{tela:.0f} s de montagem · ~{grav / 60:.0f} min de gravação (com folgas) · contexto {D.get('contexto', '')}", '',
     '| # | cena | plano | ação | para quê | grave | dica |', '|---|---|---|---|---|---|---|']
for p in ps:
    c = PL[p['tipo']]
    M.append(f"| {p['n']} | {p.get('cena', 1)} | {c['nome']} ({c['en']}) | {p.get('acao', '')} | {c['funcao']} | {p.get('grave_s', 4)} s | {c['dica']} |")
M += ['', *[f'- ⚠ {a}' for a in avisos]]
(P / 'docs/PLANOS.md').write_text('\n'.join(M) + '\n', encoding='utf-8')

# ── página do cliente ──
h = html.escape
cards = []
for p in ps:
    c = PL[p['tipo']]
    cards.append(f'''<article class="card"><div class="topo"><span class="num">{p['n']:02d}</span><span class="cena">cena {p.get('cena', 1)}</span>
<label class="ok"><input type="checkbox"> gravado</label></div>{esquema(p['tipo'])}
<h3>{h(c['nome'])} <small>{h(c['en'])}</small></h3><p class="acao">{h(p.get('acao', ''))}</p>
<dl><dt>Para quê</dt><dd>{h(c['funcao'])}</dd><dt>Como</dt><dd>{h(c['dica'])}</dd>
<dt>Grave</dt><dd>{p.get('grave_s', 4)} s com 1 s de folga antes e depois{(' · ' + h(p['nota'])) if p.get('nota') else ''}</dd></dl></article>''')
cliente = opt('cliente', D.get('cliente', ''))
pagina = f'''<title>Lista de planos{(' · ' + h(cliente)) if cliente else ''}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap">
<style>
:root{{--bg:#F4F1EA;--surface:#FFFDF8;--ink:#1B1A17;--mute:#6F6A5F;--line:#E2DCCF;--accent:#C98A1B;--cone:rgba(201,138,27,.28);--pes:#B9B2A3}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141412;--surface:#1D1C19;--ink:#EDEAE2;--mute:#A39D90;--line:#33312C;--accent:#E8B04A;--cone:rgba(232,176,74,.28);--pes:#5E594F;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141412;--surface:#1D1C19;--ink:#EDEAE2;--mute:#A39D90;--line:#33312C;--accent:#E8B04A;--cone:rgba(232,176,74,.28);--pes:#5E594F;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 "Instrument Sans",system-ui,sans-serif;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
main{{max-width:1120px;margin:0 auto;padding-block:40px 64px;display:flex;flex-direction:column;gap:28px}}
header .claq{{font:700 12px/1 "JetBrains Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}}
h1{{font-size:clamp(28px,5vw,44px);line-height:1.05;margin:.3em 0 .2em;text-wrap:balance;letter-spacing:-.02em}}
.meta{{color:var(--mute);font-family:"JetBrains Mono",monospace;font-size:13px}}
.antes{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 22px}}
.antes h2{{font-size:15px;margin:0 0 8px;letter-spacing:.02em}} .antes ul{{margin:0;padding-left:18px;columns:2 280px;column-gap:28px}} .antes li{{margin:0 0 4px;break-inside:avoid}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px 16px;display:flex;flex-direction:column;gap:6px;min-width:0}}
.topo{{display:flex;align-items:center;gap:10px;font:500 12px "JetBrains Mono",monospace;color:var(--mute)}}
.num{{font:700 20px "JetBrains Mono",monospace;color:var(--ink)}} .ok{{margin-left:auto;display:flex;gap:6px;align-items:center;cursor:pointer}}
.esq{{width:100%;height:auto;background:var(--bg);border-radius:10px}} .esq .chao{{stroke:var(--line);stroke-width:1}} .esq .mesa{{fill:var(--pes);opacity:.6}}
.esq .pes{{fill:var(--pes)}} .esq .cone{{fill:var(--cone)}} .esq .cel{{fill:var(--accent)}}
h3{{margin:4px 0 0;font-size:17px;letter-spacing:-.01em}} h3 small{{font:500 11px "JetBrains Mono",monospace;color:var(--mute);letter-spacing:.04em;margin-left:4px}}
.acao{{margin:0;font-weight:600}} dl{{margin:4px 0 0;display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:13.5px}} dt{{color:var(--mute);font-family:"JetBrains Mono",monospace;font-size:11.5px;padding-top:2px}} dd{{margin:0}}
.avisos{{color:var(--mute);font-size:13px}}
</style>
<main><header><div class="claq">Orbe · lista de planos{(' · ' + h(cliente)) if cliente else ''}</div><h1>{h(D.get('titulo', 'Lista de planos'))}</h1>
<div class="meta">{len(ps)} planos · {len(cenas)} cena(s) · ~{grav / 60:.0f} min de gravação · montagem de ~{tela:.0f} s</div></header>
<section class="antes"><h2>Antes de gravar</h2><ul>
<li>Celular na horizontal só se pedirmos — o padrão é <b>vertical</b>, 4K 30 qps (ou 1080p 60 qps).</li>
<li>Limpe a lente. Toque e segure na tela para <b>travar foco e exposição</b> em cada plano.</li>
<li>Luz da janela de lado; nada de luz forte atrás da pessoa.</li>
<li>Grave cada plano com <b>1 s de folga</b> antes e depois da ação, e a ação 2 vezes.</li>
<li>Mesma roupa e mesma luz em todos os planos da mesma cena (continuidade).</li>
<li>Sem música ao fundo: o som entra na edição. Pessoas e pacientes só com autorização por escrito.</li></ul></section>
<section class="grade">{''.join(cards)}</section>
{('<p class="avisos">Notas para a edição: ' + ' · '.join(h(a) for a in avisos) + '</p>') if avisos else ''}</main>
'''
(P / 'docs/planos').mkdir(exist_ok=True); (P / 'docs/planos/index.html').write_text(pagina, encoding='utf-8')
print('\n'.join(M[:3]))
for a in avisos: print('⚠', a)
print(f"✔ docs/PLANOS.md · docs/planos/index.html (publique como Artifact e mande o link ao cliente)")
