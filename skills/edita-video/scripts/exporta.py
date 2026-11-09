#!/usr/bin/env python3
"""exporta.py — (legado: prefira nle.py, que gera o kit completo para todos os editores) leva a edição para o Premiere / DaVinci Resolve / Final Cut (FCP7 XML) + EDL de cortes.

    python3 exporta.py <projeto> [--nome x]

renders/<nome>_premiere.xml (Arquivo › Importar no Premiere; File › Import › Timeline no Resolve):
  V1 A-roll (trechos do mezanino CFR, nos tempos exatos do corte) · V2 B-roll/fotos · V3 peças de motion (ProRes com alfa)
  · V4 o render final (desligado, para comparar) · A1 voz do bruto · A2 voz limpa (desligada) · A3 trilha · A4 SFX.
  Reenquadramento/zoom da câmera virtual NÃO viaja (cada NLE guarda isso diferente): o V4 mostra o resultado.
renders/<nome>_cortes.edl (CMX3600, só V1) · legendas: use o .srt da versão.
Caminhos absolutos: mova a pasta do projeto inteira junto, ou reconecte (Link Media) apontando para _edit/mez/.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0]); B, EST, _ = E.config(P)
tl = E.jload(P / '_edit/timeline.json'); FPS = tl['fps']; inv = {c['id']: c for c in E.jload(P / '_edit/inventario.json')['clips']}
mapa = E.jload(P / '_edit/mapa.json', {}) or {}
OW, OH = E.formato(B)
nome = opt('nome') or B.get('nome') or P.name
ntsc = abs(FPS - round(FPS)) > 0.01; tb = round(FPS)
f = lambda t: int(round(t * FPS))
RATE = f'<rate><timebase>{tb}</timebase><ntsc>{"TRUE" if ntsc else "FALSE"}</ntsc></rate>'
def url(p): return 'file://localhost' + quote(str(Path(p).resolve()))
vistos = set()
def arquivo(fid, path, dur_s, w=None, h=None, audio=True, video=True, ch=2):
    if fid in vistos: return f'<file id="{fid}"/>'
    vistos.add(fid)
    med = ''
    if video: med += f'<video><samplecharacteristics>{RATE}<width>{w or OW}</width><height>{h or OH}</height></samplecharacteristics></video>'
    if audio: med += '<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>{ch}</channelcount></audio>'
    return f'<file id="{fid}"><name>{escape(Path(path).name)}</name><pathurl>{url(path)}</pathurl>{RATE}<duration>{f(dur_s)}</duration><media>{med}</media></file>'
def clip(cid, nm, fileel, start, end, cin, cout, dur_s, kind='video', enabled=True, track=1):
    st = f'<sourcetrack><mediatype>{kind}</mediatype><trackindex>{track}</trackindex></sourcetrack>' if kind == 'audio' else ''
    return (f'<clipitem id="{cid}"><name>{escape(nm)}</name><enabled>{"TRUE" if enabled else "FALSE"}</enabled><duration>{f(dur_s)}</duration>{RATE}'
            f'<start>{start}</start><end>{end}</end><in>{cin}</in><out>{cout}</out>{fileel}{st}</clipitem>')
def dur_of(p):
    try: return float(E.ffprobe(p)['format']['duration'])
    except Exception: return tl['duracao']
V1, A1 = [], []
for s in tl['segmentos']:
    c = inv[s['clip']]; mez = P / c['mez']; d = c['dur']
    a, b = f(s['seq_in']), f(s['seq_out']); i0 = f(s['src_in']); i1 = i0 + (b - a)
    V1.append(clip(f"v1-{s['id']}", s['id'], arquivo(f"f-{s['clip']}", mez, d, c['w'], c['h'], c['audio'], ch=1), a, b, i0, i1, d))
    if c['audio']: A1.append(clip(f"a1-{s['id']}", s['id'], f'<file id="f-{s["clip"]}"/>', a, b, i0, i1, d, 'audio'))
V2, V3 = [], []
for it in mapa.get('itens', []):
    if it.get('t_ini') is None: continue
    a, b = f(it['t_ini']), f(it['t_fim'])
    if it['tipo'] in ('broll', 'foto') and it.get('arquivo'):
        p = P / it['arquivo']; d = dur_of(p) if it['tipo'] == 'broll' else max(10, it['t_fim'] - it['t_ini'] + 1)
        V2.append(clip(f"v2-{it['id']}", it['id'], arquivo(f"f-{it['id']}", p, d, audio=False), a, b, 0, b - a, d))
    elif it.get('render'):
        p = P / it['render']; d = dur_of(p)
        V3.append(clip(f"v3-{it['id']}", f"{it['id']} {it.get('peca', '')}", arquivo(f"f-{it['id']}", p, d, audio=False), a, b, 0, b - a, d))
rend = sorted((P / 'renders').glob('*_v[0-9][0-9].mp4'))
V4 = [clip('v4-final', 'render final (comparar)', arquivo('f-final', rend[-1], tl['duracao']), 0, f(tl['duracao']), 0, f(tl['duracao']), tl['duracao'], enabled=False)] if rend else []
AUX = []
for k, (stem, en) in enumerate((('voz', False), ('trilha', True), ('sfx', True))):
    p = P / 'audio' / f'{stem}.wav'
    if p.exists(): AUX.append([clip(f'a-{stem}', stem, arquivo(f'f-{stem}', p, tl['duracao'], video=False), 0, f(tl['duracao']), 0, f(tl['duracao']), tl['duracao'], 'audio', en)])
tr = lambda items: f'<track>{"".join(items)}</track>'
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5"><sequence id="seq-1">'
       f'<name>{escape(nome)}</name><duration>{f(tl["duracao"])}</duration>{RATE}<media><video><format><samplecharacteristics>{RATE}'
       f'<width>{OW}</width><height>{OH}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>'
       + tr(V1) + tr(V2) + tr(V3) + (tr(V4) if V4 else '') + '</video><audio>' + tr(A1) + ''.join(tr(x) for x in AUX) + '</audio></media></sequence></xmeml>\n')
out = P / f'renders/{nome}_premiere.xml'; out.write_text(xml, encoding='utf-8')
# EDL CMX3600 (V1)
def tcf(n):
    fr = n % tb; s = n // tb; return f'{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{fr:02d}'
L = [f'TITLE: {nome}', 'FCM: NON-DROP FRAME', '']
for k, s in enumerate(tl['segmentos']):
    a, b = f(s['seq_in']), f(s['seq_out']); i0 = f(s['src_in']); i1 = i0 + (b - a)
    L += [f"{k + 1:03d}  {s['clip'].upper()[:8]:<8} AA/V  C        {tcf(i0)} {tcf(i1)} {tcf(a)} {tcf(b)}", f"* FROM CLIP NAME: {Path(inv[s['clip']]['mez']).name}", '']
(P / f'renders/{nome}_cortes.edl').write_text('\n'.join(L), encoding='utf-8')
print(f'✔ {out.relative_to(P)} (V1 {len(V1)} trechos · V2 {len(V2)} B-roll · V3 {len(V3)} motion · áudio {len(A1)}+{len(AUX)}) · renders/{nome}_cortes.edl')
print('  zoom/reenquadramento não viajam no XML — o V4 (desligado) mostra o render final para comparar.')
