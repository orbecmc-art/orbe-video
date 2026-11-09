#!/usr/bin/env python3
"""modelos.py — baixa (uma vez) os modelos pequenos usados pela edição, em ~/.cache/edita-video:
  yunet.onnx   detector de rosto YuNet (OpenCV Zoo, MIT) — reenquadramento e trava no rosto
  sh.rnnn      modelo RNNoise para o filtro arnndn do ffmpeg (redução de ruído de fundo na voz)
  selfie_segmenter.tflite  recorte da pessoa (MediaPipe, Apache-2.0) — texto ATRÁS da pessoa
  FCPXMLv1_10/1_11.dtd  validação do kit do Final Cut
Sem rede: o rosto cai para Haar cascade (vem com o OpenCV) e o ruído para afftdn. Nada quebra.
"""
import sys, urllib.request
sys.path.insert(0, __import__('os').path.dirname(__file__))
import evlib

# DTDs do FCPXML (validação do kit do Final Cut; espelho público do CommandPost)
DTD = 'https://raw.githubusercontent.com/CommandPost/CommandPost/develop/src/extensions/cp/apple/fcpxml/dtd/'
URLS = {
    'selfie_segmenter.tflite': 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite',
    'FCPXMLv1_10.dtd': DTD + 'FCPXMLv1_10.dtd',
    'FCPXMLv1_11.dtd': DTD + 'FCPXMLv1_11.dtd',
    'yunet.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
    'sh.rnnn': 'https://raw.githubusercontent.com/GregorR/rnnoise-models/master/somnolent-hogwash-2018-09-01/sh.rnnn',
}
quiet = '--silencioso' in sys.argv
d = evlib.models_dir(); falhou = False
for nome, url in URLS.items():
    f = d / nome
    if f.exists() and f.stat().st_size > 10000:
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'edita-video/1.0'})
        data = urllib.request.urlopen(req, timeout=60).read()
        if len(data) < 10000:
            raise RuntimeError('arquivo pequeno demais (LFS?)')
        f.write_bytes(data)
        quiet or print(f'✔ {nome} ({len(data)//1024} KB)')
    except Exception as e:
        falhou = True
        quiet or print(f'⚠ {nome}: {e}')
sys.exit(1 if falhou else 0)
