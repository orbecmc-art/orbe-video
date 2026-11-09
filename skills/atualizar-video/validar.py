#!/usr/bin/env python3
"""validar.py — confere o plugin com as regras do APP (mais rígidas que o `claude plugin validate`) antes de empacotar.

    python3 skills/atualizar-video/validar.py [<raiz do plugin>]

Regras (aprendidas com erros reais de upload): plugin.json com name kebab, version semver e description ≤ 500
caracteres; cada skills/<pasta>/SKILL.md com frontmatter YAML válido, name = pasta (kebab ≤ 64), description entre
aspas, 1–1024 caracteres, sem < >; nada de __pycache__ nem arquivos > 50 MB; ≤ 5000 arquivos e ≤ 200 MB no total.
"""
import sys, re, json
from pathlib import Path
R = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
erros, avisos = [], []
pj = json.loads((R / '.claude-plugin/plugin.json').read_text())
if not re.fullmatch(r'[a-z0-9-]+', pj.get('name', '')): erros.append('plugin.json: name precisa ser kebab-case')
if not re.fullmatch(r'\d+\.\d+\.\d+', pj.get('version', '')): erros.append('plugin.json: version precisa ser semver (1.2.3)')
if len(pj.get('description', '')) > 500: erros.append(f"plugin.json: description com {len(pj['description'])} caracteres (máx. 500 no app)")
try: import yaml
except ImportError: yaml = None
for f in sorted(R.glob('skills/*/SKILL.md')):
    s = f.read_text(); m = re.match(r'^---\n(.*?)\n---\n', s, re.S)
    if not m: erros.append(f'{f.parent.name}: sem frontmatter'); continue
    if yaml:
        try: d = yaml.safe_load(m.group(1))
        except Exception as e: erros.append(f'{f.parent.name}: YAML inválido ({e})'); continue
    else: d = dict(re.findall(r'^(\w+):\s*"?(.*?)"?$', m.group(1), re.M))
    nm, ds = d.get('name', ''), d.get('description') or ''
    if nm != f.parent.name or not re.fullmatch(r'[a-z0-9-]{1,64}', nm): erros.append(f'{f.parent.name}: name "{nm}" ≠ pasta ou fora do padrão')
    if not 1 <= len(ds) <= 1024: erros.append(f'{f.parent.name}: description com {len(ds)} caracteres (1–1024)')
    if '<' in ds or '>' in ds: erros.append(f'{f.parent.name}: description com < ou >')
    if not re.search(r'^description: "', m.group(1), re.M): avisos.append(f'{f.parent.name}: description sem aspas (dois-pontos quebram o YAML)')
arqs = [p for p in R.rglob('*') if p.is_file()]
if any('__pycache__' in p.parts for p in arqs): avisos.append('há __pycache__ (exclua do pacote)')
tot = sum(p.stat().st_size for p in arqs)
for p in arqs:
    if p.stat().st_size > 50e6: erros.append(f'{p.relative_to(R)}: {p.stat().st_size / 1e6:.0f} MB')
if len(arqs) > 5000: erros.append(f'{len(arqs)} arquivos (máx. 5000)')
if tot > 200e6: erros.append(f'{tot / 1e6:.0f} MB (máx. 200)')
print(f"{pj.get('name')} {pj.get('version')} · {len(list(R.glob('skills/*/SKILL.md')))} skills · {len(arqs)} arquivos · {tot / 1e6:.1f} MB")
for a in avisos: print('⚠', a)
for e in erros: print('✗', e)
print('✔ pronto para empacotar' if not erros else f'✗ {len(erros)} erro(s)')
sys.exit(1 if erros else 0)
