"""
Utilidades de dibujo para las imágenes de evidencia.

Las evidencias se dibujan con Pillow, no se fotografían. Todas comparten la
misma receta de envejecido para que el expediente se vea como un solo archivo
y no como diez piezas sueltas.

Convención de color: acá se trabaja en RGB de Pillow (tuplas), no en HexColor
de reportlab. Los valores son los mismos tokens del manual §1.
"""

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─── Paleta (RGB) ────────────────────────────────────────────────────────────

KRAFT = (205, 191, 162)
PAPER = (231, 225, 211)
PAPER2 = (221, 214, 197)
BAND = (192, 177, 147)
DATA = (222, 215, 198)
DARK = (38, 36, 31)
INK = (29, 27, 25)
SOFT = (95, 88, 77)
RED = (143, 42, 34)
RED_L = (184, 86, 74)
FRAME = (111, 101, 82)
RULE = (138, 125, 100)
AMBAR = (176, 132, 44)
TINTA_AZUL = (38, 52, 96)

# ─── Fuentes ─────────────────────────────────────────────────────────────────

_DIR = "/usr/share/fonts/truetype/liberation"

# URW Chancery (paquete fonts-urw-base35) es caligráfica y sirve para las
# anotaciones a mano. Si no está instalada se cae a la serif itálica, que con
# el jitter de `manuscrito` da el pego a tamaño chico.
_CHANCERY = "/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf"

_ARCHIVOS = {
    "mono": f"{_DIR}/LiberationMono-Regular.ttf",
    "monob": f"{_DIR}/LiberationMono-Bold.ttf",
    "monoi": f"{_DIR}/LiberationMono-Italic.ttf",
    "sans": f"{_DIR}/LiberationSans-Regular.ttf",
    "sansb": f"{_DIR}/LiberationSans-Bold.ttf",
    "serif": f"{_DIR}/LiberationSerif-Regular.ttf",
    "serifi": f"{_DIR}/LiberationSerif-Italic.ttf",
    "manu": _CHANCERY if os.path.exists(_CHANCERY)
    else f"{_DIR}/LiberationSerif-Italic.ttf",
}

_CACHE = {}


def fuente(nombre, tam):
    """Carga y cachea una fuente. `nombre` es la clave lógica, no el archivo."""
    clave = (nombre, tam)
    if clave not in _CACHE:
        _CACHE[clave] = ImageFont.truetype(_ARCHIVOS[nombre], tam)
    return _CACHE[clave]


def medir(draw, texto, fnt):
    caja = draw.textbbox((0, 0), texto, font=fnt)
    return caja[2] - caja[0], caja[3] - caja[1]


# ─── Texto ───────────────────────────────────────────────────────────────────


def partir(draw, texto, fnt, ancho_max):
    lineas = []
    for parrafo in texto.split("\n"):
        actual = ""
        for palabra in parrafo.split():
            tentativa = f"{actual} {palabra}".strip()
            if medir(draw, tentativa, fnt)[0] <= ancho_max:
                actual = tentativa
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def parrafo(draw, xy, texto, fnt, ancho_max, fill=INK, inter=None):
    """Dibuja texto con salto de línea automático. Devuelve la y final."""
    x, y = xy
    inter = inter or fnt.size + 6
    for linea in partir(draw, texto, fnt, ancho_max):
        draw.text((x, y), linea, font=fnt, fill=fill)
        y += inter
    return y


def manuscrito(img, xy, texto, tam=26, fill=TINTA_AZUL, angulo=0, jitter=1.6,
               semilla=3, ancho_max=None, interlinea=None):
    """
    Escritura a mano: cada carácter va rotado y desplazado un poco.

    La fuente caligráfica sola se ve demasiado regular para pasar por letra
    manuscrita; lo que da el pego es romperle la alineación glifo a glifo.

    Respeta los \\n y, si se le pasa `ancho_max`, parte las líneas solo.
    Devuelve la y siguiente a la última línea.
    """
    rnd = random.Random(semilla)
    fnt = fuente("manu", tam)
    interlinea = interlinea or int(tam * 1.35)
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)

    lineas = []
    for parrafo in texto.split("\n"):
        lineas.extend(partir(draw, parrafo, fnt, ancho_max) if ancho_max
                      else [parrafo])

    x0, y = xy
    for linea in lineas:
        x = x0
        for caracter in linea:
            if caracter == " ":
                x += tam * 0.34
                continue
            glifo = Image.new("RGBA", (tam * 3, tam * 3), (0, 0, 0, 0))
            ImageDraw.Draw(glifo).text((tam // 2, tam // 2), caracter, font=fnt,
                                       fill=fill + (238,))
            glifo = glifo.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC)
            capa.alpha_composite(
                glifo,
                (int(x - tam // 2), int(y - tam // 2 + rnd.uniform(-jitter, jitter))),
            )
            # La chancery deja mucho aire lateral; sin apretar el avance la
            # frase se lee como letras sueltas y no como palabras.
            x += medir(draw, caracter, fnt)[0] * 0.82 + rnd.uniform(0.3, 1.4)
        y += interlinea

    if angulo:
        capa = capa.rotate(angulo, resample=Image.BICUBIC, center=xy)
    img.alpha_composite(capa)
    return y


# ─── Superficies ─────────────────────────────────────────────────────────────


def papel(ancho, alto, color=PAPER, fibras=900, semilla=11):
    """Hoja de papel con fibra. Base de casi todas las evidencias."""
    img = Image.new("RGBA", (ancho, alto), color + (255,))
    draw = ImageDraw.Draw(img)
    rnd = random.Random(semilla)
    for _ in range(fibras):
        x, y = rnd.uniform(0, ancho), rnd.uniform(0, alto)
        largo = rnd.uniform(3, 14)
        ang = rnd.uniform(0, math.pi)
        tono = rnd.randint(-14, 8)
        draw.line(
            [x, y, x + largo * math.cos(ang), y + largo * math.sin(ang)],
            fill=tuple(max(0, min(255, c + tono)) for c in color) + (150,),
            width=1,
        )
    return img


def corcho(ancho, alto, semilla=5):
    """Textura de corcho para el tablero y para la ficha de persona externa."""
    rnd = np.random.default_rng(semilla)
    base = rnd.normal(0.0, 1.0, (alto // 3, ancho // 3))
    base = np.array(
        Image.fromarray(((base - base.min()) / np.ptp(base) * 255).astype(np.uint8))
        .resize((ancho, alto), Image.BICUBIC)
        .filter(ImageFilter.GaussianBlur(1.4))
    ).astype(np.float32) / 255.0

    grumo = rnd.random((alto, ancho))
    manchas = (grumo > 0.986).astype(np.float32)

    r = 168 + base * 46 - manchas * 60
    g = 128 + base * 44 - manchas * 55
    b = 82 + base * 36 - manchas * 40
    arr = np.clip(np.dstack([r, g, b]), 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def cinta(img, xy, ancho=150, alto=42, angulo=-6, tono=(226, 214, 176), alpha=150):
    """Tira de cinta adhesiva translúcida. Lo que hace que algo se vea pegado."""
    tira = Image.new("RGBA", (ancho, alto), tono + (alpha,))
    draw = ImageDraw.Draw(tira)
    # Bordes rasgados y brillo longitudinal.
    for i in range(0, ancho, 7):
        draw.line([i, 0, i + 4, 2], fill=tono + (alpha - 40,), width=2)
        draw.line([i, alto - 1, i + 4, alto - 3], fill=tono + (alpha - 40,), width=2)
    draw.line([0, alto * 0.35, ancho, alto * 0.35],
              fill=(255, 255, 255, 55), width=max(2, alto // 6))
    tira = tira.rotate(angulo, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(tira, (int(xy[0] - tira.width / 2),
                               int(xy[1] - tira.height / 2)))


def chincheta(img, xy, color=(150, 38, 32), radio=13):
    """Chincheta con brillo y sombra, para el corcho."""
    capa = Image.new("RGBA", (radio * 4, radio * 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)
    cx = cy = radio * 2
    draw.ellipse([cx - radio + 3, cy - radio + 4, cx + radio + 3, cy + radio + 4],
                 fill=(0, 0, 0, 90))
    draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio], fill=color + (255,))
    draw.ellipse([cx - radio * 0.45, cy - radio * 0.55,
                  cx - radio * 0.05, cy - radio * 0.15],
                 fill=(255, 255, 255, 120))
    img.alpha_composite(capa, (int(xy[0] - cx), int(xy[1] - cy)))


def sombra(img, caja, desenfoque=9, opacidad=95, desplazamiento=(6, 8)):
    """Sombra proyectada bajo un rectángulo. Se dibuja ANTES que el objeto."""
    x0, y0, x1, y1 = caja
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).rectangle(
        [x0 + desplazamiento[0], y0 + desplazamiento[1],
         x1 + desplazamiento[0], y1 + desplazamiento[1]],
        fill=(0, 0, 0, opacidad),
    )
    img.alpha_composite(capa.filter(ImageFilter.GaussianBlur(desenfoque)))


def pegar_rotado(fondo, pieza, centro, angulo, con_sombra=True):
    """Pega una pieza rotada sobre el fondo, con su sombra."""
    girada = pieza.rotate(angulo, expand=True, resample=Image.BICUBIC)
    x = int(centro[0] - girada.width / 2)
    y = int(centro[1] - girada.height / 2)
    if con_sombra:
        capa = Image.new("RGBA", fondo.size, (0, 0, 0, 0))
        silueta = Image.new("RGBA", girada.size, (0, 0, 0, 110))
        silueta.putalpha(girada.split()[3].point(lambda v: min(v, 110)))
        capa.alpha_composite(silueta, (x + 7, y + 9))
        fondo.alpha_composite(capa.filter(ImageFilter.GaussianBlur(8)))
    fondo.alpha_composite(girada, (x, y))


def polaroid(interior, pie_texto="", ancho=430, borde=22, borde_inferior=86,
             tam_pie=27, semilla=4):
    """
    Marco de polaroid con la foto adentro y el pie escrito a mano.

    `interior` es una imagen cuadrada; se reescala al hueco disponible.
    """
    hueco = ancho - 2 * borde
    alto = hueco + borde + borde_inferior
    marco = Image.new("RGBA", (ancho, alto), (243, 239, 228, 255))
    draw = ImageDraw.Draw(marco)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(206, 198, 180, 255), width=2)

    foto = interior.convert("RGBA").resize((hueco, hueco), Image.LANCZOS)
    marco.alpha_composite(foto, (borde, borde))
    draw.rectangle([borde - 1, borde - 1, borde + hueco, borde + hueco],
                   outline=(70, 64, 54, 255), width=2)

    if pie_texto:
        fnt = fuente("manu", tam_pie)
        ancho_pie = medir(draw, pie_texto, fnt)[0]
        manuscrito(marco, ((ancho - ancho_pie) / 2, borde + hueco + 24),
                   pie_texto, tam=tam_pie, fill=(32, 30, 40), semilla=semilla)
    return marco


def silueta(lado=520, fondo=(58, 54, 48), figura=(16, 15, 14)):
    """
    Retrato en silueta, para la víctima y para la persona de interés externa.

    Cabeza, cuello y hombros. Sin rasgos: es exactamente lo que comunica un
    archivo sin fotografía disponible.
    """
    img = Image.new("RGBA", (lado, lado), fondo + (255,))
    draw = ImageDraw.Draw(img)

    # Degradado de estudio detrás de la figura.
    for i in range(lado):
        t = i / lado
        tono = tuple(int(c * (0.72 + 0.5 * (1 - abs(t - 0.42) * 1.7))) for c in fondo)
        draw.line([0, i, lado, i], fill=tuple(max(0, min(255, v)) for v in tono))

    cx = lado / 2
    hombro_y = lado * 0.99
    draw.polygon(
        [(cx - lado * 0.40, hombro_y), (cx - lado * 0.31, lado * 0.70),
         (cx - lado * 0.13, lado * 0.60), (cx + lado * 0.13, lado * 0.60),
         (cx + lado * 0.31, lado * 0.70), (cx + lado * 0.40, hombro_y)],
        fill=figura + (255,),
    )
    draw.rectangle([cx - lado * 0.085, lado * 0.50, cx + lado * 0.085, lado * 0.64],
                   fill=figura + (255,))
    draw.ellipse([cx - lado * 0.165, lado * 0.20, cx + lado * 0.165, lado * 0.56],
                 fill=figura + (255,))
    return img.filter(ImageFilter.GaussianBlur(0.8))


# ─── Sellos y marcas ─────────────────────────────────────────────────────────


def sello(img, xy, texto, sub="", angulo=-11, color=RED, tam=44, tam_sub=20,
          grosor=6):
    """Sello de tinta rotado, con doble marco y desgaste."""
    fnt = fuente("monob", tam)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    ancho_txt, alto_txt = medir(tmp, texto, fnt)
    pad_x, pad_y = 34, 22
    ancho = ancho_txt + 2 * pad_x
    alto = alto_txt + 2 * pad_y + (tam_sub + 12 if sub else 0)

    capa = Image.new("RGBA", (ancho + 40, alto + 40), (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)
    draw.rectangle([20, 20, ancho + 20, alto + 20], outline=color + (245,),
                   width=grosor)
    draw.rectangle([20 + grosor + 4, 20 + grosor + 4,
                    ancho + 16 - grosor, alto + 16 - grosor],
                   outline=color + (205,), width=2)
    draw.text((20 + pad_x, 20 + pad_y - 4), texto, font=fnt, fill=color + (245,))
    if sub:
        fnt_sub = fuente("monob", tam_sub)
        ancho_sub = medir(draw, sub, fnt_sub)[0]
        draw.text((20 + (ancho - ancho_sub) / 2, 20 + pad_y + alto_txt + 8),
                  sub, font=fnt_sub, fill=color + (235,))

    # Desgaste: se comen píxeles al azar para que no parezca vectorial.
    rnd = np.random.default_rng(9)
    alfa = np.array(capa.split()[3]).astype(np.float32)
    ruido = rnd.random(alfa.shape)
    alfa *= np.clip(0.55 + ruido * 0.75, 0, 1)
    capa.putalpha(Image.fromarray(alfa.astype(np.uint8)))

    capa = capa.rotate(angulo, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(capa, (int(xy[0] - capa.width / 2),
                               int(xy[1] - capa.height / 2)))


def recuadro_rojo(img, caja, etiqueta="", grosor=5, color=RED):
    """Marco rojo de analista sobre una zona de interés."""
    draw = ImageDraw.Draw(img)
    draw.rectangle(list(caja), outline=color + (255,), width=grosor)
    if etiqueta:
        fnt = fuente("monob", 22)
        ancho_txt, alto_txt = medir(draw, etiqueta, fnt)
        x0, y0 = caja[0], caja[1] - alto_txt - 16
        draw.rectangle([x0, y0, x0 + ancho_txt + 18, caja[1] - 2],
                       fill=color + (255,))
        draw.text((x0 + 9, y0 + 3), etiqueta, font=fnt, fill=(245, 238, 226, 255))


# ─── Envejecido final ────────────────────────────────────────────────────────


def envejecer(img, sigma=2.8, vineta=0.30, semilla=7):
    """
    Receta común de envejecido: grano gaussiano + viñeta suave.

    Se aplica al final, sobre la imagen ya compuesta, para que todas las
    evidencias compartan la misma piel.
    """
    arr = np.array(img.convert("RGB")).astype(np.float32)
    alto, ancho = arr.shape[:2]

    rnd = np.random.default_rng(semilla)
    arr += rnd.normal(0.0, sigma, arr.shape)

    ys, xs = np.mgrid[0:alto, 0:ancho]
    nx = (xs / ancho - 0.5) * 2
    ny = (ys / alto - 0.5) * 2
    radio = np.sqrt(nx ** 2 + ny ** 2) / math.sqrt(2)
    factor = 1 - vineta * np.clip(radio - 0.45, 0, None) ** 1.5 * 2.4
    arr *= np.clip(factor, 0.55, 1.0)[:, :, None]

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def guardar(img, ruta, calidad=93):
    envejecer(img).save(ruta, "JPEG", quality=calidad, subsampling=0)
    return ruta
