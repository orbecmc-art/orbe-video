#!/usr/bin/env python3
"""ativos.py — ETAPA 5: busca, escolha e conformação de B-roll e fotos (bancos gratuitos + material do cliente).

    python3 ativos.py <projeto> buscar [--n 6] [--item br01]   # opções por item → folha de contato numerada
    python3 ativos.py <projeto> escolher br01=a3 ft01=a1        # baixa em alta, conforma, grava crédito
    python3 ativos.py <projeto> auto                             # sem ninguém olhando: escolhe pela heurística
    python3 ativos.py <projeto> conformar                        # só conforma arquivos próprios (broll/…)

Fontes, em ordem (chaves grátis no .env — PEXELS_API_KEY, PIXABAY_API_KEY; procura no ambiente, em <projeto>/.env,
~/.config/orbe/.env e <skill>/.env):
  Pexels (vídeo+foto, licença Pexels, sem atribuição obrigatória) · Pixabay (vídeo+foto, licença Pixabay) ·
  Openverse (foto, só licenças comerciais) · Wikimedia Commons (vídeo+foto; só CC0/domínio público/CC BY — sem BY-SA/NC).
`busca` em INGLÊS acha muito mais ("woman washing face at sink"); `busca_pt` opcional.
REGRAS: créditos vão para docs/CREDITOS.md, NUNCA na tela (regra Orbe). Clínica/saúde: pessoa de banco nunca é
apresentada como paciente real nem como "antes/depois". Imagem sem licença clara não entra.
Conformação: CFR no fps do projeto, SDR BT.709 (tonemap se HDR), sem áudio, H.264 CRF 16, -g fps; fotos JPG ≤ 3000 px.
"""
import sys, os, json, re, ssl, subprocess, urllib.request, urllib.parse, shutil
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
P = E.proj(A[0] if A and not A[0].startswith('--') and A[0] not in ('buscar', 'escolher', 'auto', 'conformar') else None)
CMD = next((a for a in A if a in ('buscar', 'escolher', 'auto', 'conformar')), 'buscar')
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
B, EST, _ = E.config(P); OW, OH = E.formato(B)
inv = E.jload(P / '_edit/inventario.json') or {}; FPS = inv.get('fps', 30)
FPS_STR = inv.get('fps_str', str(FPS))
mapa = E.jload(P / '_edit/mapa.json') or E.die('rode mapa.py antes (o mapa diz o que buscar)')
AT = E.jload(P / '_edit/ativos.json', {}) or {}
UA = 'edita-video/1.0 (video editing skill)'
CTX = ssl.create_default_context()
for ca in (os.environ.get('SSL_CERT_FILE'), '/root/.ccr/ca-bundle.crt'):
    if ca and Path(ca).exists():
        try: CTX.load_verify_locations(ca)
        except Exception: pass

def chaves():
    k = {}
    for f in [P / '.env', Path.home() / '.config/orbe/.env', E.SKILL / '.env']:
        if f.exists():
            for ln in f.read_text().splitlines():
                m = re.match(r'\s*([A-Z_]+)\s*=\s*"?([^"#\s]+)', ln)
                if m: k.setdefault(m.group(1), m.group(2))
    for n in ('PEXELS_API_KEY', 'PIXABAY_API_KEY'):
        if os.environ.get(n): k[n] = os.environ[n]
    return k
K = chaves()

def get(url, headers=None, binary=False, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        d = r.read()
    return d if binary else json.loads(d)

def baixar(url, dest, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)
    return dest

# ───────────── buscadores (cada um devolve lista de candidatos normalizados) ─────────────
VERT = OH > OW
def pexels(q, video, n):
    if 'PEXELS_API_KEY' not in K: return []
    h = {'Authorization': K['PEXELS_API_KEY']}
    qs = urllib.parse.urlencode({'query': q, 'per_page': n, 'orientation': 'portrait' if VERT else 'landscape', 'size': 'medium'})
    if video:
        d = get(f'https://api.pexels.com/videos/search?{qs}', h); out = []
        for v in d.get('videos', []):
            fs = sorted([f for f in v['video_files'] if f.get('file_type') == 'video/mp4' and f.get('width')], key=lambda f: f['width'] * f['height'])
            alvo = next((f for f in fs if min(f['width'], f['height']) >= 1080), fs[-1] if fs else None)
            if not alvo: continue
            out.append({'fonte': 'Pexels', 'tipo': 'video', 'thumb': v['image'], 'hd': alvo['link'], 'w': alvo['width'], 'h': alvo['height'], 'dur': v['duration'],
                        'autor': v['user']['name'], 'pagina': v['url'], 'licenca': 'Pexels License (uso livre, sem atribuição obrigatória)'})
        return out
    d = get(f'https://api.pexels.com/v1/search?{qs}', h)
    return [{'fonte': 'Pexels', 'tipo': 'foto', 'thumb': p['src']['medium'], 'hd': p['src']['original'], 'w': p['width'], 'h': p['height'], 'dur': 0,
             'autor': p['photographer'], 'pagina': p['url'], 'licenca': 'Pexels License (uso livre, sem atribuição obrigatória)', 'alt': p.get('alt', '')} for p in d.get('photos', [])]

def pixabay(q, video, n):
    if 'PIXABAY_API_KEY' not in K: return []
    base = 'https://pixabay.com/api/videos/' if video else 'https://pixabay.com/api/'
    par = {'key': K['PIXABAY_API_KEY'], 'q': q[:100], 'per_page': max(3, n), 'safesearch': 'true'}
    if video: par['video_type'] = 'film'
    else: par.update(image_type='photo', orientation='vertical' if VERT else 'horizontal')
    d = get(base + '?' + urllib.parse.urlencode(par)); out = []
    for h in d.get('hits', []):
        if video:
            v = h['videos'].get('large') or h['videos'].get('medium')
            if not v or not v.get('url'): continue
            out.append({'fonte': 'Pixabay', 'tipo': 'video', 'thumb': v.get('thumbnail') or h['videos'].get('tiny', {}).get('thumbnail'), 'hd': v['url'], 'w': v['width'], 'h': v['height'],
                        'dur': h.get('duration', 0), 'autor': h.get('user', ''), 'pagina': h['pageURL'], 'licenca': 'Pixabay Content License (uso livre)'})
        else:
            out.append({'fonte': 'Pixabay', 'tipo': 'foto', 'thumb': h['webformatURL'], 'hd': h.get('largeImageURL') or h['webformatURL'], 'w': h['imageWidth'], 'h': h['imageHeight'],
                        'dur': 0, 'autor': h.get('user', ''), 'pagina': h['pageURL'], 'licenca': 'Pixabay Content License (uso livre)'})
    return out

def openverse(q, video, n):
    if video: return []
    d = get('https://api.openverse.org/v1/images/?' + urllib.parse.urlencode({'q': q, 'license_type': 'commercial,modification', 'page_size': n, 'mature': 'false'}))
    out = []
    for r in d.get('results', []):
        lic = (r.get('license') or '').lower()
        if lic in ('by-sa', 'by-nc', 'by-nc-sa', 'by-nd', 'by-nc-nd', 'nc'): continue
        out.append({'fonte': f"Openverse/{r.get('source', '')}", 'tipo': 'foto', 'thumb': r.get('thumbnail') or r['url'], 'hd': r['url'], 'w': r.get('width') or 0, 'h': r.get('height') or 0,
                    'dur': 0, 'autor': r.get('creator') or '?', 'pagina': r.get('foreign_landing_url', ''), 'licenca': f"CC {lic.upper()} {r.get('license_version', '')}".strip(),
                    'credito_obrigatorio': lic.startswith('by')})
    return out

def commons(q, video, n):
    s = ('filetype:video ' if video else 'filetype:bitmap ') + q
    d = get('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'query', 'generator': 'search', 'gsrsearch': s, 'gsrnamespace': 6, 'gsrlimit': n * 2, 'prop': 'imageinfo',
        'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 480, 'format': 'json'}))
    out = []
    for pg in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = (pg.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata', {})
        lic = (md.get('LicenseShortName', {}).get('value') or '')
        L = lic.lower()
        if not (('cc0' in L) or ('public domain' in L) or L.startswith('pd') or (L.startswith('cc by') and 'sa' not in L and 'nc' not in L)): continue
        autor = re.sub('<[^>]+>', '', md.get('Artist', {}).get('value', '?'))[:80]
        out.append({'fonte': 'Wikimedia Commons', 'tipo': 'video' if video else 'foto', 'thumb': ii.get('thumburl') or ii.get('url'), 'hd': ii.get('url'), 'w': ii.get('width', 0), 'h': ii.get('height', 0),
                    'dur': float(ii.get('duration') or 0), 'autor': autor, 'pagina': ii.get('descriptionurl', ''), 'licenca': lic,
                    'credito_obrigatorio': L.startswith('cc by')})
    return out[:n]

def buscar(it, n):
    video = it['tipo'] == 'broll'; q = it.get('busca') or it.get('busca_pt') or it.get('descricao', '')
    cands = []; erros = []
    for fn in (pexels, pixabay, openverse, commons):
        if len(cands) >= n: break
        try: cands += fn(q, video, n - len(cands) + 2)
        except Exception as e: erros.append(f'{fn.__name__}: {str(e)[:80]}')
    # ordena: orientação do formato, resolução, duração suficiente
    need = it['t_fim'] - it['t_ini']
    def nota(c):
        o = 1 if ((c['h'] >= c['w']) == VERT) else 0
        res = min(1, min(c['w'], c['h']) / 1080) if c['w'] else 0.3
        du = 1 if (not video or c['dur'] >= need + 0.5) else 0.3
        return o * 2 + res + du + (0.3 if c['fonte'] in ('Pexels', 'Pixabay') else 0)
    cands.sort(key=nota, reverse=True)
    for i, c in enumerate(cands[:n]): c['id'] = f'a{i + 1}'
    return cands[:n], erros

def folha(item_id, cands):
    from PIL import Image, ImageDraw, ImageFont
    tw, th = 300, 300 if not VERT else 420; cols = 3; rows = (len(cands) + cols - 1) // cols
    img = Image.new('RGB', (cols * tw, rows * (th + 46)), (18, 18, 18)); dr = ImageDraw.Draw(img)
    try: fnt = ImageFont.truetype('DejaVuSans-Bold.ttf', 18); fs = ImageFont.truetype('DejaVuSans.ttf', 13)
    except Exception: fnt = fs = ImageFont.load_default()
    tmp = P / '_edit/thumbs'; tmp.mkdir(exist_ok=True)
    for k, c in enumerate(cands):
        x, y = (k % cols) * tw, (k // cols) * (th + 46)
        try:
            f = tmp / f"{item_id}_{c['id']}.jpg"
            try: baixar(c['thumb'], f)
            except Exception: baixar(c['hd'], f)          # miniatura falhou (rate limit) → original
            im = Image.open(f).convert('RGB'); im.thumbnail((tw - 8, th - 8)); img.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        except Exception: dr.text((x + 10, y + th // 2), 'sem miniatura', fill=(200, 80, 80), font=fs)
        dr.text((x + 8, y + th + 2), f"{c['id']}", fill=(255, 212, 59), font=fnt)
        dr.text((x + 48, y + th + 4), f"{c['fonte'][:18]} · {c['w']}×{c['h']}" + (f" · {c['dur']:.0f}s" if c['dur'] else ''), fill=(230, 230, 230), font=fs)
        dr.text((x + 8, y + th + 24), c['licenca'][:44], fill=(150, 150, 150), font=fs)
    out = P / 'docs/folhas' / f'{item_id}_opcoes.jpg'; img.save(out, quality=88); return out

def conformar(src, dest, video, hdr=None):
    if not video:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB'); im.thumbnail((3000, 3000)); im.save(dest, quality=93); return dest
    pr = E.ffprobe(src); vs = next(s for s in pr['streams'] if s['codec_type'] == 'video')
    tr = vs.get('color_transfer', ''); vf = []
    if tr in ('smpte2084', 'arib-std-b67'):
        vf.append('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv')
    vf += [f'fps={FPS_STR}', "scale='if(gt(iw,ih),min(iw,3840),-2)':'if(gt(iw,ih),-2,min(ih,3840))'", 'format=yuv420p']
    E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-an', '-vf', ','.join(vf), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16',
           '-g', str(round(FPS)), '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', str(dest)])
    return dest

def creditos():
    L = ['# Créditos e licenças', '', '> **Não vão na tela** (regra Orbe: nenhum vídeo leva fonte/crédito no quadro, salvo pedido).',
         '> Use esta lista para a legenda do post quando a licença pedir crédito (CC BY) e para guardar a prova de licença.', '',
         '| item | fonte | autor | licença | página | crédito obrigatório? |', '|---|---|---|---|---|---|']
    for iid, a in sorted(AT.items()):
        c = a.get('escolhido')
        if c: L.append(f"| {iid} | {c['fonte']} | {c['autor']} | {c['licenca']} | {c['pagina']} | {'SIM — na legenda do post' if c.get('credito_obrigatorio') else 'não'} |")
    for it in mapa['itens']:
        if it.get('arquivo', '').startswith('broll/') or it.get('origem') == 'cliente':
            L.append(f"| {it['id']} | material do cliente | — | do cliente | — | não |")
    (P / 'docs/CREDITOS.md').write_text('\n'.join(L) + '\n', encoding='utf-8')

alvo_itens = [it for it in mapa['itens'] if it['tipo'] in ('broll', 'foto') and (not opt('item') or it['id'] == opt('item'))]
if CMD == 'buscar' or CMD == 'auto':
    n = int(opt('n', 6)); fontes_ok = [f for f, k in (('Pexels', 'PEXELS_API_KEY'), ('Pixabay', 'PIXABAY_API_KEY')) if k in K]
    print(f"Fontes: {', '.join(fontes_ok + ['Openverse (foto)', 'Commons'])}" + ('' if fontes_ok else ' · ⚠ sem chave Pexels/Pixabay: resultados fracos — crie as chaves grátis e ponha no .env'))
    for it in alvo_itens:
        if it.get('arquivo') and CMD == 'buscar' and not opt('item'): continue
        if not (it.get('busca') or it.get('busca_pt')): continue
        cands, erros = buscar(it, n)
        ws = (it.get('busca') or '').split()
        while not cands and len(ws) > 2:      # busca longa demais nos bancos sem chave: encurta (tira palavras do fim) e tenta de novo
            ws = ws[:-1]; it2 = dict(it, busca=' '.join(ws)); cands, erros = buscar(it2, n)
            if cands: print(f"  · {it['id']}: achei com «{it2['busca']}» (busca encurtada)")
        AT[it['id']] = {'busca': it.get('busca'), 'candidatos': cands, 'erros': erros}
        if not cands: print(f"✗ {it['id']}: nada para «{it.get('busca')}» {'; '.join(erros)}"); continue
        f = folha(it['id'], cands); print(f"✔ {it['id']}: {len(cands)} opções → {f.relative_to(P)}  (olhe e escolha: ativos.py . escolher {it['id']}=a1)")
        if CMD == 'auto': A.append(f"{it['id']}=a1")
    E.jsave(P / '_edit/ativos.json', AT)
if CMD in ('escolher', 'auto'):
    for esc in [a for a in A if re.match(r'^[a-z]+\d+=a\d+$', a)]:
        iid, aid = esc.split('='); it = next(x for x in mapa['itens'] if x['id'] == iid)
        c = next((c for c in AT.get(iid, {}).get('candidatos', []) if c['id'] == aid), None)
        if not c: print(f'✗ {esc}: candidato não existe (rode buscar)'); continue
        video = c['tipo'] == 'video'; ext = Path(urllib.parse.urlparse(c['hd']).path).suffix.lower() or ('.mp4' if video else '.jpg')
        orig = P / 'assets/originais'; orig.mkdir(parents=True, exist_ok=True); src = orig / f'{iid}_{aid}{ext}'
        h = {'Authorization': K['PEXELS_API_KEY']} if c['fonte'] == 'Pexels' and 'PEXELS_API_KEY' in K else None
        try: baixar(c['hd'], src, h)
        except Exception as e: print(f'✗ {iid}: download falhou ({e}) — tente outra opção ou baixe no Mac'); continue
        dest = P / 'assets' / (f'{iid}.mp4' if video else f'{iid}.jpg'); conformar(src, dest, video)
        it['arquivo'] = str(dest.relative_to(P)); it['status'] = 'ok'; it['tipo'] = 'broll' if video else 'foto'
        AT[iid]['escolhido'] = c; print(f'✔ {iid} ← {aid} ({c["fonte"]}, {c["licenca"]}) → {it["arquivo"]}')
    E.jsave(P / '_edit/ativos.json', AT); E.jsave(P / '_edit/mapa.json', mapa); creditos()
if CMD == 'conformar':
    for it in alvo_itens:
        a = it.get('arquivo')
        if not a or a.startswith('assets/'): continue
        video = it['tipo'] == 'broll'; dest = P / 'assets' / (f"{it['id']}.mp4" if video else f"{it['id']}.jpg")
        conformar(P / a, dest, video); it['origem'] = 'cliente'; it['arquivo_original'] = a; it['arquivo'] = str(dest.relative_to(P))
        print(f"✔ {it['id']}: {a} conformado → {it['arquivo']}")
    E.jsave(P / '_edit/mapa.json', mapa); creditos()
E.log_estado(P, 'assets', 'feito' if all(x.get('arquivo') for x in alvo_itens) else 'parcial')
