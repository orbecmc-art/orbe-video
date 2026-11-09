#!/usr/bin/env python3
"""fontes.py — põe as fontes das legendas em <projeto>/fonts/ como TTF (o libass não lê woff2).

    python3 fontes.py <projeto> [montserrat:700,800,900 inter:600,800 playfair-display:700i …]

Sem argumentos: baixa a família do estilo ativo (legendas.fonte) nos pesos 400–900 e, se o estilo usa segunda fonte
(legendas.fonte2, layout cinematográfico), ela em itálico 600–800. Peso com "i" = itálico. Fonte: pacotes @fontsource no
registry do npm (funciona mesmo sem Google Fonts), convertidos com fontTools. Fontes do kit do cliente (TTF/OTF já
em fonts/) têm prioridade e não são tocadas. Cache em ~/.cache/edita-video/fonts.
"""
import sys, os, subprocess, tarfile, tempfile, shutil, re, json
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') and ':' not in A[0] else None)
specs = [a for a in A if ':' in a or (a and not a.startswith('--') and Path(a).resolve() != P)]
B, EST, _ = E.config(P)
fam = EST['legendas']['fonte']
if not specs:
    specs = [f"{fam.lower().replace(' ', '-')}:400,500,600,700,800,900" + (',400i,700i' if EST['legendas'].get('italico') else '')]
    if EST['legendas'].get('fonte2'): specs.append(f"{EST['legendas']['fonte2'].lower().replace(' ', '-')}:600i,700i,800i,700")
CACHE = E.models_dir() / 'fonts'; CACHE.mkdir(exist_ok=True)
FD = P / 'fonts'; FD.mkdir(exist_ok=True)

def tem_local(family):
    for f in list(FD.glob('*.ttf')) + list(FD.glob('*.otf')):
        try:
            from fontTools.ttLib import TTFont
            n = TTFont(f, lazy=True)['name']
            if (n.getDebugName(16) or n.getDebugName(1) or '').lower() == family.lower(): return True
        except Exception: pass
    return False

for spec in specs:
    slug, _, ws = spec.partition(':'); ws = [w for w in (ws or '400,700').split(',') if w]
    pronto = [CACHE / f'{slug}-{w}.ttf' for w in ws]
    if not all(p.exists() for p in pronto):
        tmp = Path(tempfile.mkdtemp())
        r = subprocess.run(['npm', 'pack', f'@fontsource/{slug}', '--silent'], cwd=tmp, capture_output=True, text=True)
        tgz = next(iter(tmp.glob('*.tgz')), None)
        if r.returncode or not tgz:
            print(f'✗ @fontsource/{slug} não encontrado (rede?) — legendas usam a fonte padrão do sistema'); continue
        with tarfile.open(tgz) as t: t.extractall(tmp, filter='data')
        meta = json.loads((tmp / 'package/metadata.json').read_text()) if (tmp / 'package/metadata.json').exists() else {}
        family = meta.get('family', slug)
        from fontTools.ttLib import TTFont
        from fontTools import merge as _m  # noqa
        for w in ws:
            it = w.endswith('i'); wn = w.rstrip('i'); st = 'italic' if it else 'normal'
            base = tmp / f'package/files/{slug}-latin-{wn}-{st}.woff2'
            ext = tmp / f'package/files/{slug}-latin-ext-{wn}-{st}.woff2'
            if not base.exists(): print(f'  · {slug} sem peso {w}'); continue
            fnt = TTFont(base); fnt.flavor = None
            if ext.exists():     # junta latin + latin-ext (acentos raros, ç maiúsculo em algumas fontes vêm no ext)
                try:
                    from fontTools.merge import Merger
                    a, b = tmp / f'a{w}.ttf', tmp / f'b{w}.ttf'
                    fnt.save(a); e2 = TTFont(ext); e2.flavor = None; e2.save(b)
                    fnt = Merger().merge([str(a), str(b)])
                except Exception: pass
            name = fnt['name']
            sub = {600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black', 500: 'Medium', 400: 'Regular', 300: 'Light'}.get(int(wn), wn)
            if it: sub = (sub + ' Italic').replace('Regular Italic', 'Italic')
            for rec in list(name.names):
                if rec.nameID in (1, 16): rec.string = family
                elif rec.nameID in (2, 17): rec.string = sub
                elif rec.nameID == 4: rec.string = f'{family} {sub}'
                elif rec.nameID == 6: rec.string = f'{family.replace(" ", "")}-{sub}'
            fnt['OS/2'].usWeightClass = int(wn)
            if it:      # libass escolhe a face pelo par (negrito, itálico): marque o itálico nas duas tabelas
                fnt['OS/2'].fsSelection = (fnt['OS/2'].fsSelection | 1) & ~(1 << 6)
                fnt['head'].macStyle |= 2
            fnt.save(CACHE / f'{slug}-{w}.ttf')
        shutil.rmtree(tmp, ignore_errors=True)
    for p in pronto:
        if p.exists(): shutil.copy(p, FD / p.name)
    print(f"✔ {slug}: {', '.join(w for w, p in zip(ws, pronto) if p.exists())} → {FD}")
