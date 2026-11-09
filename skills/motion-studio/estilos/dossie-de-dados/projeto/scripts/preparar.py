#!/usr/bin/env python3
"""Gera os materiais do filme: papéis, persiana, o rosto do mosaico, a folha de fotos e os índices dos dias.

Tudo sai em assets/ e dados.js. Semente fixa: rodar de novo dá os mesmos arquivos.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "assets" / "originais"
SAIDA = RAIZ / "assets"
rng = np.random.default_rng(7)

W, H = 1200, 2134  # um pouco maior que o quadro: a câmera anda sem mostrar a borda


def ruido(w, h, escala, seed):
    """Ruído suave: sorteia pequeno e amplia com bicúbica."""
    r = np.random.default_rng(seed)
    pequeno = r.random((max(2, h // escala), max(2, w // escala)))
    im = Image.fromarray((pequeno * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255 - 0.5


def salvar(arr, nome, q=88):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(SAIDA / nome, quality=q)


def kraft():
    # papelão: base marrom, ondas finas na horizontal (como na referência), fibras e manchas
    y = np.arange(H, dtype=np.float32)[:, None]
    x = np.arange(W, dtype=np.float32)[None, :]
    onda = np.sin(y * 0.62 + 7 * np.sin(x * 0.006) + 3 * ruido(W, H, 90, 1) * 8) * 5.5
    fibras = ruido(W, H, 1, 2) * 16 + ruido(W, H, 3, 3) * 12
    mancha = ruido(W, H, 220, 4) * 26
    base = np.array([168, 136, 98], dtype=np.float32)
    l = onda + fibras + mancha
    return base[None, None, :] + l[:, :, None] * np.array([1.0, 0.92, 0.78])


def papel():
    # papel de caderno quadriculado, levemente amarelado
    base = np.array([222, 218, 206], dtype=np.float32)
    fibras = ruido(W, H, 1, 5) * 9 + ruido(W, H, 4, 6) * 7 + ruido(W, H, 260, 7) * 14
    arr = base[None, None, :] + fibras[:, :, None]
    passo = 54
    linha = np.zeros((H, W), dtype=np.float32)
    linha[:, ::passo] = 1
    linha[::passo, :] = 1
    linha = np.asarray(Image.fromarray((linha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32) / 255
    cor = np.array([120, 134, 150], dtype=np.float32)
    return arr * (1 - 0.32 * linha[:, :, None]) + cor * 0.32 * linha[:, :, None]


def ardosia():
    # cartolina preta: quase lisa, com poeira
    base = np.array([28, 28, 30], dtype=np.float32)
    g = ruido(W, H, 1, 8) * 7 + ruido(W, H, 5, 9) * 5 + ruido(W, H, 300, 10) * 9
    return base[None, None, :] + g[:, :, None]


def persiana():
    # máscara de sombra para multiplicar: branco = luz, cinza = sombra das lâminas
    n = 2600
    v = np.linspace(0, 1, n)
    passo = 0.17
    fase = (v % passo) / passo
    lamina = np.clip((np.abs(fase - 0.5) - 0.16) / 0.10, 0, 1)
    img = np.tile((lamina * 255)[:, None], (1, n)).astype(np.uint8)
    im = Image.fromarray(img).filter(ImageFilter.GaussianBlur(26))
    im.save(SAIDA / "persiana.jpg", quality=86)


def madeira():
    im = Image.open(ORIG / "12932247.jpg").convert("RGB")
    if im.width > im.height:
        im = im.rotate(90, expand=True)
    alvo = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    if alvo.height < H:
        alvo = alvo.resize((int(alvo.width * H / alvo.height), H), Image.LANCZOS)
    alvo.crop((0, 0, W, H)).save(SAIDA / "madeira.jpg", quality=86)


def rosto():
    # o retrato do mosaico: 64 x 100 ladrilhos de 16,875 px, ou seja 1080 x 1688
    im = Image.open(ORIG / "31735289.jpg").convert("RGB")
    a = 1688 / im.height
    im = im.resize((round(im.width * a), 1688), Image.LANCZOS)
    dx = (im.width - 1080) // 2
    im = im.crop((dx, 0, dx + 1080, 1688))
    arr = np.asarray(im, dtype=np.float32)
    cinza = arr.mean(axis=2, keepdims=True)
    arr = cinza + (arr - cinza) * 0.62  # meio caminho para o preto e branco: a pele continua quente
    arr = (arr - 128) * 1.06 + 124
    salvar(arr, "rosto.jpg", 90)
    return dx


def dias():
    """Sorteia a ordem de queda dos 6.369 ladrilhos e guarda quais sobram.

    O total é a conta do filme: 5.913 dias até os 18 + 168 visitas já feitas + 288 que faltam.
    """
    colunas, linhas = 64, 100
    total = 5913 + 168 + 288
    assert total == 6369
    # olhos no retrato, medidos no original em 1600 x 2400 (esquerdo 540,1170 e direito 990,1092)
    a = 1688 / 2400
    dx = (1600 * a - 1080) / 2
    olho_e = np.array([540 * a - dx, 1170 * a])
    olho_d = np.array([990 * a - dx, 1092 * a])
    meio = (olho_e + olho_d) / 2
    eixo = (olho_d - olho_e) / np.linalg.norm(olho_d - olho_e)
    normal = np.array([-eixo[1], eixo[0]])
    ids, peso = [], []
    t = 1080 / colunas
    fora = colunas * linhas - total  # os 31 que faltam ficam no canto de baixo
    for lin in range(linhas):
        for col in range(colunas):
            if lin == linhas - 1 and col >= colunas - fora:
                continue
            c = np.array([(col + 0.5) * t, (lin + 0.5) * t])
            d = c - meio
            # elipse deitada sobre os dois olhos, com a borda levemente irregular
            m = ((d @ eixo) / 1.0) ** 2 + ((d @ normal) * 3.0) ** 2
            m *= 1 + 0.10 * rng.random()
            ids.append((lin, col))
            peso.append(m)
    ordem = np.argsort(peso)
    sobra_hoje = set(int(i) for i in ordem[:288])
    sobra_18 = set(int(i) for i in ordem[:288 + 168])
    assert len(ids) == total
    return {
        "colunas": colunas,
        "linhas": linhas,
        "total": total,
        "tiles": [[int(a), int(b)] for a, b in ids],
        "hoje": sorted(sobra_hoje),
        "aos18": sorted(sobra_18 - sobra_hoje),
        "meio_olhos": [float(meio[0]), float(meio[1])],
    }


def folha_de_fotos():
    # 24 fotos, 256 px cada, em preto e branco quente: o que cada ladrilho mostra de perto
    nomes = [
        "18251000", "15003426", "35525672", "40226070", "31559971", "11887257",
        "20685790", "17066527", "17066585", "17066576", "36527109", "3171155",
        "3171137", "36500348", "28253015", "6218024", "8653860", "12842473",
        "36477303", "40427764", "7204149", "20729679", "31735291", "31735289",
    ]
    lado = 256
    folha = Image.new("RGB", (lado * 6, lado * 4))
    for i, n in enumerate(nomes):
        im = Image.open(ORIG / f"{n}.jpg").convert("L")
        m = min(im.size)
        x = (im.width - m) // 2
        y = max(0, (im.height - m) // 3)
        im = im.crop((x, y, x + m, y + m)).resize((lado, lado), Image.LANCZOS)
        cor = Image.merge("RGB", (im.point(lambda v: min(255, v * 1.03)), im, im.point(lambda v: v * 0.92)))
        folha.paste(cor, ((i % 6) * lado, (i // 6) * lado))
    folha.save(SAIDA / "folha-fotos.jpg", quality=84)
    # a foto do mergulho: mãe e filha, testa com testa, em tamanho grande
    im = Image.open(ORIG / "18251000.jpg").convert("L")
    m = min(im.size)
    x = (im.width - m) // 2
    im = im.crop((x, 0, x + m, m)).resize((1080, 1080), Image.LANCZOS)
    im.convert("RGB").save(SAIDA / "mergulho.jpg", quality=88)


def fotos_soltas():
    # as fotos que entram nas polaroides, já em preto e branco
    for n, nome, cortes in [
        ("6218024", "maos-fotos", None),
        ("28253015", "maos", None),
    ]:
        im = Image.open(ORIG / f"{n}.jpg").convert("L")
        im.thumbnail((900, 900), Image.LANCZOS)
        Image.merge("RGB", (im, im, im.point(lambda v: v * 0.95))).save(SAIDA / f"{nome}.jpg", quality=86)


salvar(kraft(), "kraft.jpg")
salvar(papel(), "papel.jpg")
salvar(ardosia(), "ardosia.jpg")
persiana()
madeira()
rosto()
folha_de_fotos()
fotos_soltas()
d = dias()
(RAIZ / "dados.js").write_text("window.DIAS = " + json.dumps(d, separators=(",", ":")) + ";\n")
print("ok", d["total"], "ladrilhos;", len(d["hoje"]), "hoje;", len(d["aos18"]), "entre os 18 e hoje")
