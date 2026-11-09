/* recorder.js — PLAYER QUE GRAVA A SI MESMO (para entregar o filme como página: Artifact, link pro cliente, chat sem render).
 *
 * Ativa com ?player=1 ou quando o bundle (scripts/bundle.mjs) define window.BUNDLED. Mostra Play · Pause · Reiniciar · Gravar
 * FORA da arte. O RELÓGIO é o áudio (audio.currentTime) → imagem e som nunca escorregam. Gravar: volta a 0, grava UM ciclo
 * completo com a trilha (canvas.captureStream + Web Audio → MediaRecorder), para sozinho e baixa o arquivo.
 * Formato: MP4 se o navegador suportar (Safari/Chrome recentes), senão WebM — a extensão do arquivo é a real.
 * Não captura microfone nem áudio do sistema. O áudio só começa no clique (regra dos navegadores).
 * Trilha: window.SOUNDTRACK (URL ou data URI). Sem trilha, o relógio é performance.now().
 * O render oficial continua sendo scripts/render.mjs (frame exato + blur); a gravação ao vivo é para conveniência.
 */
(function () {
  const Q = new URLSearchParams(location.search);
  if (!(Q.has('player') || window.BUNDLED) || Q.has('render')) return;
  window.__PLAYER = true;
  addEventListener('load', async () => {
    if (window.ready) await window.ready;
    const c = document.getElementById('c'), DUR = window.DURATION || 10, FPS = window.FPS || 30;
    const hud = document.getElementById('hud'); if (hud) hud.style.display = 'none';
    // o quadro inteiro cabe na tela e os controles ficam FORA da arte (embaixo)
    document.body.classList.remove('render'); document.body.style.cssText += ';margin:0;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;overflow:hidden';
    c.style.cssText = 'display:block;max-width:100vw;max-height:calc(100vh - 72px);width:auto;height:auto;margin:0';
    const bar = document.createElement('div');
    bar.style.cssText = 'position:relative;display:flex;gap:8px;align-items:center;padding:8px 10px;border-radius:12px;background:rgba(15,15,15,.82);color:#eee;font:13px system-ui;z-index:9;backdrop-filter:blur(6px)';
    const btn = (label, fn) => { const b = document.createElement('button'); b.textContent = label; b.style.cssText = 'background:#2a2a2a;color:#eee;border:0;border-radius:8px;padding:7px 12px;cursor:pointer;font:inherit'; b.onclick = fn; bar.appendChild(b); return b; };
    const time = document.createElement('span'); time.style.cssText = 'min-width:92px;text-align:right;font-variant-numeric:tabular-nums';
    document.body.appendChild(bar);
    let audio = null, actx = null, dest = null, playing = false, t0 = 0, paused = 0, rec = null;
    if (window.SOUNDTRACK) { audio = new Audio(window.SOUNDTRACK); audio.preload = 'auto'; audio.loop = false; }
    const now = () => (audio ? audio.currentTime : playing ? (performance.now() - t0) / 1000 : paused);
    function ensureAudioGraph() {
      if (!audio || actx) return;
      actx = new (window.AudioContext || window.webkitAudioContext)();
      const src = actx.createMediaElementSource(audio); dest = actx.createMediaStreamDestination();
      src.connect(actx.destination); src.connect(dest);
    }
    const play = async () => { ensureAudioGraph(); if (actx) await actx.resume(); if (audio) await audio.play(); else t0 = performance.now() - paused * 1000; playing = true; pb.textContent = '❚❚ Pausar'; };
    const pause = () => { if (audio) audio.pause(); else paused = now(); playing = false; pb.textContent = '▶ Play'; };
    const restart = async () => { if (audio) audio.currentTime = 0; paused = 0; t0 = performance.now(); if (!playing) await play(); };
    const pb = btn('▶ Play', () => (playing ? pause() : play()));
    btn('⟲ Reiniciar', restart);
    const rb = btn('● Gravar', async () => {
      if (rec) return;
      const types = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
      const mime = types.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m));
      if (!mime) { alert('Este navegador não grava vídeo (MediaRecorder). Use o Chrome.'); return; }
      ensureAudioGraph(); if (actx) await actx.resume();
      const stream = c.captureStream(FPS);
      if (dest) for (const tr of dest.stream.getAudioTracks()) stream.addTrack(tr);
      const chunks = []; rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 16e6 });
      rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      rec.onstop = () => { const ext = mime.startsWith('video/mp4') ? 'mp4' : 'webm', a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob(chunks, { type: mime.split(';')[0] })); a.download = (document.title || 'filme').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\W+/g, '-').replace(/^-|-$/g, '') + '.' + ext; a.click();
        rec = null; rb.textContent = '● Gravar'; rb.style.background = '#2a2a2a'; };
      if (audio) audio.currentTime = 0; paused = 0; t0 = performance.now();
      rec.start(250); rb.textContent = '● gravando…'; rb.style.background = '#a12';
      if (!playing) await play();
    });
    bar.appendChild(time);
    (function loop() {
      let t = now();
      const end = audio && isFinite(audio.duration) && audio.duration > 0 ? Math.min(DUR, audio.duration) : DUR;   // AAC pode ser ms mais curto
      if (t >= end - 0.03 || (audio && audio.ended)) {
        if (rec) { rec.stop(); pause(); t = DUR - 1e-3; }
        else if (playing) { if (audio) audio.currentTime = 0; else t0 = performance.now(); t = 0; }
      }
      window.__frameT = t; (window.seek || window.renderAt)(Math.min(t, DUR - 1e-3));
      time.textContent = `${t.toFixed(2)} / ${DUR.toFixed(2)}s`;
      requestAnimationFrame(loop);
    })();
    addEventListener('keydown', (e) => { if (e.code === 'Space') { e.preventDefault(); playing ? pause() : play(); } });
  });
})();
