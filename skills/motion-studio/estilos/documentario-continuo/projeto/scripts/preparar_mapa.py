#!/usr/bin/env python3
"""preparar_mapa.py — gera mapa.js (o "mundo" do documentário) a partir de contornos REAIS de domínio público.

    python3 scripts/preparar_mapa.py --world <countries-50m.json> [--brasil <datamaps.bra.js>]
                                    [--bbox -82,-56,-30,13] [--tol 0.04] [--saida mapa.js]

Fontes (baixe com `npm pack world-atlas@2.0.2 datamaps@0.5.9` numa pasta própria e passe os caminhos):
  · world-atlas (ISC) = Natural Earth 1:50m (domínio público) → países
  · datamaps (MIT) → estados do Brasil (dist/datamaps.bra.js, objeto braTopo)
Decodifica TopoJSON (arcos quantizados com delta), recorta pelo bbox (lon0,lat0,lon1,lat1), simplifica
(Douglas-Peucker, tolerância em graus) e grava window.MAPA = {bbox, paises:[{nome, aneis}], estados:[{sigla,nome,aneis}]}.
Outro lugar do mundo: mude o bbox (Europa: -12,34,32,60). Os dados são lidos como dados (JSON), nunca executados.
"""
import sys, json, re, math
A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
BB = [float(x) for x in (opt('bbox', '-82,-56,-30,13')).split(',')]; TOL = float(opt('tol', 0.04))

def decode(topo, obj):
    tr = topo.get('transform'); arcs = []
    for arc in topo['arcs']:
        x = y = 0; pts = []
        for p in arc:
            if tr: x += p[0]; y += p[1]; pts.append((x * tr['scale'][0] + tr['translate'][0], y * tr['scale'][1] + tr['translate'][1]))
            else: pts.append((p[0], p[1]))
        arcs.append(pts)
    def ring(idx):
        out = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a[1:] if out else a)
        return out
    feats = []
    for gm in topo['objects'][obj]['geometries']:
        polys = [gm['arcs']] if gm['type'] == 'Polygon' else gm.get('arcs', []) if gm['type'] == 'MultiPolygon' else []
        rings = [ring(r) for poly in polys for r in poly]
        feats.append({'props': gm.get('properties', {}), 'id': gm.get('id'), 'rings': rings})
    return feats

def dp(pts, tol):
    if len(pts) < 4: return pts
    if pts[0] == pts[-1]:     # anel fechado: divide no ponto mais longe do início (senão a base tem comprimento zero)
        k = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
        if 0 < k < len(pts) - 1: return dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); ax, ay = pts[a]; bx, by = pts[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-9
        best, bi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / L
            if d > best: best, bi = d, i
        if best > tol and bi > 0: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]

def dentro(r):
    xs = [p[0] for p in r]; ys = [p[1] for p in r]
    return not (max(xs) < BB[0] or min(xs) > BB[2] or max(ys) < BB[1] or min(ys) > BB[3])

def limpa(feats, tol):
    out = []
    for f in feats:
        rs = [[[round(x, 3), round(y, 3)] for x, y in dp(r, tol)] for r in f['rings'] if r and dentro(r)]
        rs = [r for r in rs if len(r) >= 4]
        if rs: out.append({**f, 'rings': rs})
    return out

W = json.load(open(opt('world') or sys.exit(__doc__)))
paises = limpa(decode(W, 'countries'), TOL)
M = {'bbox': BB, 'fonte': 'Natural Earth 1:50m via world-atlas (ISC); estados do Brasil via datamaps (MIT)',
     'paises': [{'nome': f['props'].get('name', ''), 'aneis': f['rings']} for f in paises]}
if opt('brasil'):
    s = open(opt('brasil'), encoding='utf-8').read(); i = s.find('braTopo')
    m = re.search(r'braTopo\s*=\s*(\{.*?\})\s*;?\s*\n', s[i - 5:], re.S)
    T = json.loads(m.group(1)); obj = list(T['objects'].keys())[0]
    est = limpa(decode(T, obj), TOL * 0.6)
    M['estados'] = [{'sigla': (f['props'].get('postal') or f['props'].get('code_hasc', '')[-2:] or f['id'] or ''), 'nome': f['props'].get('name', ''), 'aneis': f['rings']} for f in est]
out = opt('saida', 'mapa.js')
open(out, 'w', encoding='utf-8').write('// GERADO por scripts/preparar_mapa.py — contornos reais (Natural Earth / datamaps). Não edite à mão.\nwindow.MAPA = ' + json.dumps(M, ensure_ascii=False, separators=(',', ':')) + ';\n')
n = sum(len(r) for p in M['paises'] for a in p['aneis'] for r in [a]) + sum(len(a) for e in M.get('estados', []) for a in e['aneis'])
print(f"✔ {out}: {len(M['paises'])} países, {len(M.get('estados', []))} estados, {n} pontos")
