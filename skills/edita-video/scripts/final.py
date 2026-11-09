#!/usr/bin/env python3
"""final.py — monta a versão: (legendas → som → vídeo) → junta → SRT + capa → QA. Nunca sobrescreve: _v01, _v02…

    python3 final.py <projeto> [--rascunho] [--pular-video] [--pular-audio] [--sem-qa] [--nome clinica-pele]

--rascunho: metade da resolução, x264 ultrafast (para olhar ritmo/cortes rápido). Sem flag: master de entrega.
Saídas em renders/: <nome>_vNN.mp4 (H.264 High, AAC 48 kHz 256k, BT.709, faststart) · <nome>_vNN.srt (legenda para a
plataforma, por frase) · <nome>_vNN_capa.jpg (9:16) e _capa_3x4.jpg (recorte do grid) · stems em audio/.
Depois: python3 qa_edicao.py (roda sozinho aqui) e ABRA as folhas antes de dizer que terminou.
"""
import sys, os, subprocess, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
import evlib as E
from pathlib import Path

A = sys.argv[1:]
def opt(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
P = E.proj(A[0] if A and not A[0].startswith('--') else None)
B, EST, ESTILO = E.config(P); RASC = '--rascunho' in A
S = E.SKILL / 'scripts'
est = E.jload(P / '_edit/estado.json', {}) or {}
ver = est.get('versao', 0) + (0 if RASC else 1)
nome = opt('nome') or B.get('nome') or re.sub(r'[^a-z0-9-]+', '-', P.name.lower()).strip('-') or 'video'
tag = 'rascunho' if RASC else f'v{ver:02d}'
def py(script, *args):
    r = subprocess.run([sys.executable, str(S / script), str(P), *args])
    if r.returncode: E.die(f'{script} falhou')

def velho(alvo, *deps):     # refaz a etapa se algo de que ela depende mudou depois dela
    a = P / '_edit' / alvo
    return not a.exists() or any((P / '_edit' / d).exists() and (P / '_edit' / d).stat().st_mtime > a.stat().st_mtime for d in deps)
if not (P / '_edit/rosto').exists(): py('rosto.py')
if velho('camera.json', 'timeline.json', 'mapa.json', 'briefing.json'): py('camera.py')
if velho('legendas.json', 'timeline.json', 'mapa.json', 'camera.json', 'correcoes.json', 'briefing.json'): py('legendas.py')
if '--pular-audio' not in A:
    py('eventos.py'); py('audio.py')
video = P / f'renders/_video_{tag}.mp4'
if '--pular-video' in A and not video.exists():      # reaproveita o último vídeo composto (só o som mudou)
    prev = sorted((P / 'renders').glob('_video_v[0-9][0-9].mp4'))
    if prev: import shutil as _sh; _sh.copy(prev[-1], video)
if '--pular-video' not in A or not video.exists():
    py('compor.py', *(['--rascunho'] if RASC else ['--versao', str(ver)]))
out = P / f'renders/{nome}_{tag}.mp4'
tl0 = E.jload(P / '_edit/timeline.json')
E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(video), '-i', str(P / 'audio/mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
       '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', f"{tl0['duracao']:.4f}", '-movflags', '+faststart', str(out)])   # -shortest corta quadros (atraso do AAC)
# pico real depois do AAC (o codec sobe o pico de forma variável)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(out), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr); I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
print(f"✔ {out.relative_to(P)} · {I[-1] if I else '?'} LUFS · pico real {tp[-1] if tp else '?'} dBTP (depois do AAC)")

# SRT da plataforma: por frase, ≤ 42 caracteres/linha, ≤ 2 linhas, ≤ 6 s — com as correções de transcrição
tl = E.jload(P / '_edit/timeline.json'); corr = E.jload(P / '_edit/correcoes.json', {}) or {}
def txt(w):
    t = corr.get(f"#{w['i']}")
    if t is not None: return t
    for k, v in corr.items():
        if not k.startswith('#') and E.norm(k) == E.norm(w['w']): return re.sub(re.escape(re.sub(r'[^\wÀ-ÿ]', '', w['w'])), v, w['w'])
    return w['w']
cues = []; cur = []
for w in tl['palavras']:
    t = txt(w)
    if not t.strip(): continue
    if cur and (len(' '.join(x[0] for x in cur) + ' ' + t) > 84 or w['e'] - cur[0][1] > 6 or w['s'] - cur[-1][2] > 0.8): cues.append(cur); cur = []
    cur.append((t, w['s'], w['e']))
    if re.search(r'[.!?]$', t): cues.append(cur); cur = []
if cur: cues.append(cur)
def st(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f'{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'.replace(',1000', ',999')
L = []
for k, c in enumerate(cues):
    s = ' '.join(x[0] for x in c)
    if len(s) > 42:      # quebra em 2 linhas perto do meio, em espaço
        mid = len(s) // 2; i = min((j for j, ch in enumerate(s) if ch == ' '), key=lambda j: abs(j - mid)); s = s[:i] + '\n' + s[i + 1:]
    fim = c[-1][2] + 0.15
    if k + 1 < len(cues): fim = min(fim, cues[k + 1][0][1] - 0.002)      # nunca sobrepõe a próxima (CapCut/Premiere recusam)
    L += [str(k + 1), f'{st(c[0][1])} --> {st(fim)}', s, '']
(P / f'renders/{nome}_{tag}.srt').write_text('\n'.join(L), encoding='utf-8')
# capa: o quadro do gancho (meio da 1ª peça de título/palavra) ou 1,0 s
mapa = E.jload(P / '_edit/mapa.json', {}) or {}
gan = next((it for it in sorted(mapa.get('itens', []), key=lambda x: x.get('t_ini', 99)) if it.get('peca') in ('titulo', 'palavra', 'numero', 'frase', 'aspas', 'grafico', 'linha') and it.get('t_ini', 99) < 6), None)
tc = (gan['t_ini'] + min(1.2, 0.6 * (gan['t_fim'] - gan['t_ini']))) if gan else 1.0
capa = P / f'renders/{nome}_{tag}_capa.jpg'
E.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{tc:.2f}', '-i', str(out), '-frames:v', '1', '-q:v', '2', str(capa)])
E.run(['ffmpeg', '-y', '-v', 'error', '-i', str(capa), '-vf', 'crop=iw:iw*4/3:0:(ih-iw*4/3)/2', '-q:v', '2', str(capa.with_name(capa.stem + '_3x4.jpg'))])
if not RASC:
    est['versao'] = ver; E.jsave(P / '_edit/estado.json', est); E.log_estado(P, 'final', 'feito', out.name)
print(f'✔ legenda da plataforma {nome}_{tag}.srt · capa {capa.name} (+ recorte 3:4 do grid)')
if '--sem-qa' not in A:
    subprocess.run([sys.executable, str(S / 'qa_edicao.py'), str(P), str(out)])
    if not RASC and list(P.glob('referencias/*/source.mp4')):      # assinatura de movimento × referência (alvo, não bloqueia)
        subprocess.run([sys.executable, str(S / 'pericia_movimento.py'), str(P)])
