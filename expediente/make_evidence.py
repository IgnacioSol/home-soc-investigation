#!/usr/bin/env python3
"""
Genera las imágenes de evidencia del EXPEDIENTE 002.

    python3 make_evidence.py            # todas
    python3 make_evidence.py E J        # solo algunas

Cada función `ev_X` devuelve una imagen RGBA ya compuesta; el guardado y el
envejecido común los hace `evidencia_lib.guardar`, para que las diez piezas
compartan exactamente la misma piel.
"""

import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import evidencia_lib as ev
from evidencia_lib import INK, RED, SOFT, fuente, medir

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")

# Las piezas «a sangre» ocupan la página entera, así que se dibujan con la
# proporción de la hoja carta. Las documentales van enmarcadas y pueden tener
# cualquier proporción.
RATIO_PAGINA = 792 / 612


# ─── Piezas compartidas ──────────────────────────────────────────────────────


def _mesa(ancho, alto, tono=(104, 99, 88)):
    """
    Superficie sobre la que se fotografían las piezas físicas.

    Va en gris medio a propósito: sobre fondo oscuro las anotaciones rojas del
    analista no se leen, y esas anotaciones son parte de la evidencia.
    """
    rnd = np.random.default_rng(3)
    base = rnd.normal(0, 1, (alto // 6, ancho // 6))
    base = np.array(
        Image.fromarray(((base - base.min()) / np.ptp(base) * 255).astype(np.uint8))
        .resize((ancho, alto), Image.BICUBIC)
        .filter(ImageFilter.GaussianBlur(3))
    ).astype(np.float32) / 255.0

    # Caída de luz suave desde arriba-izquierda. Va acotada: sin el clip los
    # valores se van a negativo en las esquinas y la mesa sale negra.
    ys = np.linspace(-1, 1, alto)[:, None]
    xs = np.linspace(-1, 1, ancho)[None, :]
    luz = np.clip(1.10 - 0.17 * ((xs - 0.25) ** 2 + (ys + 0.15) ** 2), 0.74, 1.14)

    capas = [np.clip((c * 0.86 + c * 0.26 * base) * luz, 0, 255) for c in tono]
    arr = np.clip(np.dstack(capas), 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def _encabezado(img, letra, etiqueta_der, color_texto=(226, 219, 203)):
    """Franja superior con el identificador de la pieza."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, img.width, 66], fill=(24, 22, 19, 240))
    draw.text((34, 20), f"EVIDENCIA  {letra}", font=fuente("monob", 30),
              fill=color_texto + (255,))
    fnt = fuente("mono", 20)
    ancho_txt = medir(draw, etiqueta_der, fnt)[0]
    draw.text((img.width - 34 - ancho_txt, 27), etiqueta_der, font=fnt,
              fill=(150, 140, 122, 255))


def _pie_pieza(img, texto):
    draw = ImageDraw.Draw(img)
    fnt = fuente("mono", 18)
    ancho_txt = medir(draw, texto, fnt)[0]
    draw.text((img.width - 30 - ancho_txt, img.height - 34), texto, font=fnt,
              fill=(132, 122, 105, 255))


def _bolsa(ancho, alto, titulo, campos, semilla=2):
    """
    Bolsa de evidencia con cierre: plástico translúcido y etiqueta impresa.

    Lo que hace que el plástico se lea como plástico y no como un rectángulo
    gris son tres cosas: el borde brillante, las arrugas suaves y los reflejos
    diagonales. Sin las arrugas parece un recuadro dibujado.

    Devuelve (imagen, caja_interior) para que quien la llame dibuje adentro.
    """
    rnd = random.Random(semilla)
    bolsa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bolsa)

    # Cuerpo translúcido, un punto más claro y azulado que el fondo.
    draw.rounded_rectangle([0, 0, ancho - 1, alto - 1], radius=18,
                           fill=(228, 231, 230, 104))
    draw.rounded_rectangle([0, 0, ancho - 1, alto - 1], radius=18,
                           outline=(250, 251, 248, 215), width=4)
    draw.rounded_rectangle([5, 5, ancho - 6, alto - 6], radius=14,
                           outline=(176, 180, 178, 90), width=2)

    # Cierre zip: dos rieles con dentado.
    zip_y = 48
    draw.line([16, zip_y, ancho - 16, zip_y], fill=(250, 250, 245, 205), width=8)
    draw.line([16, zip_y + 12, ancho - 16, zip_y + 12],
              fill=(240, 240, 234, 150), width=5)
    for x in range(24, ancho - 24, 11):
        draw.line([x, zip_y - 5, x + 5, zip_y + 5], fill=(255, 255, 255, 135),
                  width=2)

    # Etiqueta impresa de cadena de custodia.
    et_y = zip_y + 30
    et_alto = 32 + 27 * len(campos)
    draw.rectangle([20, et_y, ancho - 20, et_y + et_alto],
                   fill=(240, 235, 221, 246), outline=(118, 108, 90, 230), width=2)
    draw.rectangle([20, et_y, ancho - 20, et_y + 32], fill=RED + (240,))
    draw.text((32, et_y + 7), titulo, font=fuente("monob", 19),
              fill=(246, 240, 228, 255))

    y = et_y + 43
    for etiqueta, valor in campos:
        draw.text((32, y), etiqueta, font=fuente("monob", 15), fill=SOFT + (255,))
        draw.text((196, y), valor, font=fuente("mono", 15), fill=INK + (255,))
        y += 27

    interior = (28, et_y + et_alto + 18, ancho - 28, alto - 26)

    # Arrugas y reflejos: se componen aparte y se desenfocan para que no se
    # vean como trazos dibujados sino como luz sobre una superficie.
    brillo = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    bd = ImageDraw.Draw(brillo)
    for _ in range(9):
        x0 = rnd.uniform(0, ancho)
        y0 = rnd.uniform(interior[1], alto)
        largo = rnd.uniform(60, 210)
        pend = rnd.uniform(-0.8, 0.8)
        bd.line([x0, y0, x0 + largo, y0 + largo * pend],
                fill=(255, 255, 255, rnd.randint(22, 46)), width=rnd.randint(3, 9))
    bd.polygon([(ancho * 0.10, alto), (ancho * 0.32, alto),
                (ancho * 0.64, interior[1]), (ancho * 0.44, interior[1])],
               fill=(255, 255, 255, 26))
    bd.polygon([(ancho * 0.68, alto), (ancho * 0.78, alto),
                (ancho * 0.96, interior[1]), (ancho * 0.88, interior[1])],
               fill=(255, 255, 255, 18))
    bolsa.alpha_composite(brillo.filter(ImageFilter.GaussianBlur(7)))

    return bolsa, interior


# ─── EVIDENCIA E — Pastillero y caja de repuesto ─────────────────────────────


def _pastillero(ancho, alto, faltantes=()):
    """
    Pastillero semanal de siete casillas vistas desde arriba.

    `faltantes` son los índices de casilla vacía. Para esta evidencia van todas
    llenas: el pastillero intacto es justo lo que descarta al Sujeto n.º 08.
    """
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, ancho - 1, alto - 1], radius=13,
                           fill=(206, 202, 194, 255), outline=(96, 92, 84, 255),
                           width=3)

    dias = ["L", "M", "X", "J", "V", "S", "D"]
    pad, hueco = 14, 7
    ancho_casilla = (ancho - 2 * pad - hueco * 6) / 7
    for i, dia in enumerate(dias):
        x0 = pad + i * (ancho_casilla + hueco)
        x1 = x0 + ancho_casilla
        y0, y1 = pad + 26, alto - pad
        draw.rounded_rectangle([x0, y0, x1, y1], radius=7,
                               fill=(178, 190, 196, 205),
                               outline=(88, 86, 80, 255), width=2)
        draw.text((x0 + ancho_casilla / 2 - 6, pad - 1), dia,
                  font=fuente("monob", 21), fill=(58, 55, 50, 255))
        if i in faltantes:
            continue
        # Dos pastillas por casilla, insinuadas a través de la tapa.
        cx = (x0 + x1) / 2
        for dy, r in ((0.34, 12), (0.60, 11)):
            cy = y0 + (y1 - y0) * dy
            draw.ellipse([cx - r - 4, cy - r, cx + r - 4, cy + r],
                         fill=(243, 241, 234, 232), outline=(150, 146, 138, 255))
            draw.ellipse([cx - r + 5, cy - r + 6, cx + r + 5, cy + r + 6],
                         fill=(238, 235, 226, 210), outline=(150, 146, 138, 220))
    return img


def _blister(ancho, alto, total=20, vacias=(), cols=5):
    """
    Blíster de aluminio con burbujas; las vacías van hundidas y reventadas.

    Devuelve (imagen, filas_vacias) para que quien lo llame pueda enmarcar el
    faltante sin tener que recalcular la retícula a mano.
    """
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, ancho - 1, alto - 1], radius=9,
                           fill=(203, 205, 208, 255), outline=(120, 120, 122, 255),
                           width=2)
    filas = total // cols
    pad, cabecera = 18, 26
    paso_x = (ancho - 2 * pad) / cols
    paso_y = (alto - 2 * pad - cabecera) / filas
    radio = min(paso_x, paso_y) * 0.33

    def centro(indice):
        f, col = divmod(indice, cols)
        return (pad + paso_x * (col + 0.5), pad + cabecera + paso_y * (f + 0.5))

    for i in range(total):
        cx, cy = centro(i)
        if i in vacias:
            draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio],
                         fill=(146, 146, 148, 255), outline=(92, 92, 94, 255),
                         width=2)
            draw.line([cx - radio * .7, cy - radio * .5, cx + radio * .6,
                       cy + radio * .7], fill=(80, 80, 82, 255), width=3)
            draw.line([cx - radio * .2, cy - radio * .8, cx + radio * .3,
                       cy + radio * .8], fill=(80, 80, 82, 255), width=2)
        else:
            draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio],
                         fill=(230, 232, 235, 255), outline=(148, 150, 154, 255),
                         width=2)
            draw.ellipse([cx - radio * .5, cy - radio * .62, cx - radio * .05,
                          cy - radio * .18], fill=(255, 255, 255, 180))

    if vacias:
        xs = [centro(i)[0] for i in vacias]
        ys = [centro(i)[1] for i in vacias]
        marco = (min(xs) - radio - 10, min(ys) - radio - 10,
                 max(xs) + radio + 10, max(ys) + radio + 10)
    else:
        marco = None
    return img, marco


def ev_E():
    ancho = 1100
    alto = round(ancho * RATIO_PAGINA)  # va a sangre: proporción de la hoja
    # Sin encabezado propio: en las piezas a sangre lo aporta la barra
    # superior de la página, y duplicarlo se ve como un error de montaje.
    img = _mesa(ancho, alto)

    ancho_bolsa, x_bolsa = 960, 70

    # E-1 — el pastillero semanal. Intacto: esto es lo que descarta al 08.
    y1, alto1 = 110, 440
    bolsa1, interior1 = _bolsa(
        ancho_bolsa, alto1,
        "E-1  ·  PASTILLERO SEMANAL  ·  CADENA DE CUSTODIA",
        [("RECOLECTADO:", "Domicilio del occiso, mesa de noche"),
         ("APORTADO POR:", "Sujeto n.º 08"),
         ("ESTADO:", "COMPLETO — 7 de 7 casillas cerradas")],
        semilla=2,
    )
    pastillero = _pastillero(interior1[2] - interior1[0] - 20, 190)
    bolsa1.alpha_composite(pastillero, (interior1[0] + 10, interior1[1] + 26))
    ev.sombra(img, (x_bolsa, y1, x_bolsa + ancho_bolsa, y1 + alto1))
    img.alpha_composite(bolsa1, (x_bolsa, y1))

    ev.manuscrito(img, (x_bolsa + 44, y1 + alto1 + 18),
                  "ninguna casilla abierta", tam=31, fill=(216, 78, 62),
                  semilla=12, angulo=-1.5)

    # E-2 — la caja de repuesto de la gaveta. Acá está el faltante.
    y2, alto2 = 620, 580
    bolsa2, interior2 = _bolsa(
        ancho_bolsa, alto2,
        "E-2  ·  CAJA DE REPUESTO  ·  CADENA DE CUSTODIA",
        [("RECOLECTADO:", "Gaveta de la cocina — domicilio del Sujeto n.º 01"),
         ("APORTADO POR:", "Registro de sitio"),
         ("ESTADO:", "ABIERTA — faltante no justificado")],
        semilla=6,
    )
    blister, marco = _blister(interior2[2] - interior2[0] - 40, 300,
                              total=20, vacias=tuple(range(9)))
    # El blíster baja lo suficiente para que la etiqueta roja del faltante,
    # que se dibuja por encima del marco, caiga sobre plástico y no sobre
    # la cabecera impresa del propio blíster.
    off = (interior2[0] + 20, interior2[1] + 54)
    bolsa2.alpha_composite(blister, off)
    ev.sombra(img, (x_bolsa, y2, x_bolsa + ancho_bolsa, y2 + alto2))
    img.alpha_composite(bolsa2, (x_bolsa, y2))

    # El marco rojo se calcula desde la retícula del blíster, no a ojo.
    ev.recuadro_rojo(
        img,
        (x_bolsa + off[0] + marco[0], y2 + off[1] + marco[1],
         x_bolsa + off[0] + marco[2], y2 + off[1] + marco[3]),
        "FALTANTE: 9 COMPRIMIDOS",
    )
    ev.manuscrito(img, (x_bolsa + 44, y2 + alto2 + 14),
                  "el occiso dejaba esta caja acá para cuando se quedaba a dormir",
                  tam=29, fill=(216, 78, 62), semilla=21, ancho_max=940,
                  angulo=-0.8)

    return img


# ─── EVIDENCIA J — Persona de interés externa ────────────────────────────────


def _nota(ancho, alto, titulo, lineas, color_titulo=RED, fondo=(233, 226, 208),
          tam_titulo=20, tam_linea=17, interlinea=25):
    """Papelito de nota, de los que se pegan al corcho."""
    img = ev.papel(ancho, alto, color=fondo, fibras=int(ancho * alto / 320),
                   semilla=ancho + alto)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(176, 166, 145, 255),
                   width=2)
    y = 18
    if titulo:
        draw.text((18, y), titulo, font=fuente("monob", tam_titulo),
                  fill=color_titulo + (255,))
        y += tam_titulo + 16
    fnt = fuente("mono", tam_linea)
    for linea in lineas:
        for trozo in ev.partir(draw, linea, fnt, ancho - 36):
            draw.text((18, y), trozo, font=fnt, fill=INK + (255,))
            y += interlinea
    return img


def _libreta(ancho, alto, titulo, lineas):
    """Hoja de libreta con espiral, como la de ACTIVIDADES de la referencia."""
    img = ev.papel(ancho, alto, color=(236, 231, 216), fibras=400, semilla=77)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(178, 168, 148, 255),
                   width=2)
    # Perforaciones y espiral del lado izquierdo.
    for y in range(30, alto - 20, 34):
        draw.ellipse([13, y, 29, y + 16], fill=(120, 112, 96, 255))
        draw.arc([9, y - 7, 40, y + 20], start=200, end=340,
                 fill=(96, 92, 84, 255), width=4)

    x = 52
    draw.text((x, 18), titulo, font=fuente("monob", 19), fill=RED + (255,))
    y = 54
    for linea in lineas:
        draw.ellipse([x + 2, y + 7, x + 9, y + 14], fill=INK + (255,))
        draw.text((x + 20, y), linea, font=fuente("mono", 17), fill=INK + (255,))
        y += 30
    return img


def _mapa(ancho, alto):
    """
    Recorte de plano urbano en sepia, con la zona de cobro marcada.

    Las manzanas se rellenan un tono más oscuro que las calles: sin ese
    contraste el plano se lee como una cuadrícula y no como un mapa.
    """
    img = Image.new("RGBA", (ancho, alto), (188, 172, 142, 255))
    draw = ImageDraw.Draw(img)
    rnd = random.Random(31)

    verticales = list(range(-20, ancho + 60, 46))
    horizontales = list(range(-20, alto + 60, 52))

    # Manzanas.
    for i in range(len(verticales) - 1):
        for j in range(len(horizontales) - 1):
            tono = rnd.randint(-9, 9)
            draw.rectangle(
                [verticales[i] + 5, horizontales[j] + 5,
                 verticales[i + 1] - 5, horizontales[j + 1] - 5],
                fill=(163 + tono, 148 + tono, 120 + tono, 255),
            )
    # Calles.
    for x in verticales:
        draw.line([x, 0, x + rnd.randint(-5, 5), alto],
                  fill=(206, 196, 174, 255), width=rnd.choice([5, 5, 9]))
    for y in horizontales:
        draw.line([0, y, ancho, y + rnd.randint(-5, 5)],
                  fill=(206, 196, 174, 255), width=rnd.choice([5, 5, 10]))
    # Avenida principal.
    draw.line([0, alto * 0.64, ancho, alto * 0.46], fill=(216, 206, 182, 255),
              width=15)
    draw.line([0, alto * 0.64, ancho, alto * 0.46], fill=(150, 138, 116, 255),
              width=2)

    img = img.filter(ImageFilter.GaussianBlur(0.6))
    draw = ImageDraw.Draw(img)
    cx, cy = ancho * 0.62, alto * 0.38
    draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], outline=RED + (235,),
                 width=5)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(112, 102, 86, 255),
                   width=2)
    return img


def ev_J():
    """
    Ficha de persona de interés externa, montada en corcho.

    Va a sangre en su página: a tamaño reducido el texto de los papelitos se
    vuelve ilegible, y la pieza deja de funcionar como evidencia. Las zonas de
    y<110 y de y>1100 quedan bajo la barra superior y la franja de nota de la
    página, así que no se compone nada ahí.
    """
    ancho = 1000
    alto = round(ancho * RATIO_PAGINA)
    img = ev.corcho(ancho, alto)

    # Cabecera del expediente externo.
    cab = _nota(430, 76, "", ["EXPEDIENTE EXTERNO"], tam_linea=25)
    ev.pegar_rotado(img, cab, (256, 152), -1.2)
    codigo = _nota(300, 76, "", ["#E-0227"], tam_linea=25)
    ev.pegar_rotado(img, codigo, (792, 148), 1.4)

    # Polaroid con la silueta — sin fotografía disponible.
    pol = ev.polaroid(ev.silueta(520, fondo=(74, 62, 48)), "«EL PELÓN»",
                      ancho=400, semilla=8)
    ev.pegar_rotado(img, pol, (295, 445), -2.4)
    ev.cinta(img, (295, 236), ancho=170, alto=44, angulo=-5)

    # Bloque de vinculación.
    vinc = _nota(
        356, 250, "ASOCIADO CON",
        ["MESA DE APUESTAS", "SAN JOSÉ CENTRO", "", "Último contacto:",
         "03/07 — 09:40"],
    )
    ev.pegar_rotado(img, vinc, (768, 336), 2.6)
    ev.cinta(img, (676, 224), ancho=110, alto=36, angulo=42)
    ev.cinta(img, (862, 224), ancho=110, alto=36, angulo=-42)

    # Actividades registradas.
    act = _libreta(330, 300, "ACTIVIDADES",
                   ["Apuestas deportivas", "Préstamo con interés",
                    "Cobro casa por casa", "Compra de deuda"])
    ev.pegar_rotado(img, act, (768, 640), -1.8)

    # Declaración de fuente reservada.
    testigo = _nota(
        410, 236, "DECLARACIÓN DE TESTIGO",
        ["«Cobra los sábados por la", "mañana, casa por casa.",
         "Nunca entra: espera afuera.»", "", "— Fuente de identidad reservada"],
    )
    ev.pegar_rotado(img, testigo, (268, 812), 1.9)
    ev.chincheta(img, (268, 706))

    # Recorte de plano de la zona de cobro.
    mapa = _mapa(356, 240)
    ev.pegar_rotado(img, mapa, (760, 906), -2.2)
    ev.chincheta(img, (760, 796), color=(58, 74, 132))

    # Nivel de riesgo.
    riesgo = Image.new("RGBA", (430, 120), (0, 0, 0, 0))
    rd = ImageDraw.Draw(riesgo)
    rd.rectangle([0, 0, 429, 119], fill=(233, 226, 208, 250),
                 outline=(176, 166, 145, 255), width=2)
    rd.text((18, 14), "NIVEL DE RIESGO", font=fuente("monob", 20), fill=INK + (255,))
    for i in range(5):
        x0 = 18 + i * 78
        activo = i == 3
        rd.rectangle([x0, 52, x0 + 66, 104],
                     fill=(RED + (255,)) if activo else (246, 242, 232, 255),
                     outline=(120, 110, 92, 255), width=2)
        rd.text((x0 + 26, 66), str(i + 1), font=fuente("monob", 26),
                fill=(246, 240, 228, 255) if activo else (110, 102, 88, 255))
    ev.pegar_rotado(img, riesgo, (268, 1024), -1.4)

    # El sello va en el corcho libre de abajo, pisando apenas el borde del
    # bloque de riesgo. Arriba tapaba el titular de la nota de vinculación.
    ev.sello(img, (616, 1074), "NO DIVULGAR", angulo=-7, tam=44)
    return img


# ─── Formularios impresos ────────────────────────────────────────────────────


def _formulario(ancho, alto, entidad, titulo, referencia, semilla=17):
    """Hoja membretada con cabecera institucional. Base de A, D y H."""
    img = ev.papel(ancho, alto, color=(236, 231, 217),
                   fibras=ancho * alto // 260, semilla=semilla)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, ancho - 1, 96], fill=(32, 30, 26, 255))
    draw.text((38, 24), entidad, font=fuente("monob", 24),
              fill=(232, 226, 210, 255))
    draw.text((38, 58), titulo, font=fuente("mono", 18), fill=(158, 148, 128, 255))

    fnt = fuente("mono", 17)
    ancho_ref = medir(draw, referencia, fnt)[0]
    draw.text((ancho - 38 - ancho_ref, 60), referencia, font=fnt,
              fill=(158, 148, 128, 255))

    draw.line([0, 100, ancho, 100], fill=RED + (255,), width=5)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(150, 140, 120, 255),
                   width=2)
    return img


def _tabla(draw, x, y, columnas, filas, ancho_total, alto_fila=34,
           tam=16, destacar=()):
    """
    Tabla con cabecera oscura. `columnas` es [(titulo, peso), ...].

    Devuelve la y siguiente al último renglón.
    """
    pesos = [c[1] for c in columnas]
    total = sum(pesos)
    anchos = [ancho_total * p / total for p in pesos]

    draw.rectangle([x, y, x + ancho_total, y + alto_fila], fill=(58, 54, 46, 255))
    cx = x
    for (titulo, _), ancho_col in zip(columnas, anchos):
        draw.text((cx + 10, y + alto_fila / 2 - tam * 0.62), titulo,
                  font=fuente("monob", tam - 1), fill=(228, 222, 206, 255))
        cx += ancho_col
    y += alto_fila

    for i, fila in enumerate(filas):
        fondo = (222, 215, 197, 255) if i % 2 else (233, 228, 213, 255)
        if i in destacar:
            fondo = (232, 205, 197, 255)
        draw.rectangle([x, y, x + ancho_total, y + alto_fila], fill=fondo)
        draw.line([x, y + alto_fila, x + ancho_total, y + alto_fila],
                  fill=(186, 176, 154, 255), width=1)
        cx = x
        for valor, ancho_col in zip(fila, anchos):
            color = RED if i in destacar else INK
            estilo = "monob" if i in destacar else "mono"
            draw.text((cx + 10, y + alto_fila / 2 - tam * 0.62), str(valor),
                      font=fuente(estilo, tam), fill=color + (255,))
            cx += ancho_col
        y += alto_fila

    draw.rectangle([x, y - alto_fila * len(filas) - alto_fila, x + ancho_total, y],
                   outline=(120, 110, 92, 255), width=2)
    return y


def _firma(img, xy, ancho=300, alto=64, color=(38, 52, 96), semilla=44):
    """
    Rúbrica manuscrita.

    Escribir el nombre tachado con bloques negros queda raro en una firma; una
    rúbrica ilegible comunica lo mismo y se ve como una firma de verdad.
    """
    rnd = random.Random(semilla)
    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)

    # Trazo inicial alto, como la mayúscula con la que arranca una firma.
    inicial = [(10 + t * 46, alto * 0.92 - t * alto * 0.80 + math.sin(t * 3) * 9)
               for t in [i / 11 for i in range(12)]]
    draw.line(inicial, fill=color + (240,), width=5, joint="curve")

    puntos = []
    for i in range(52):
        t = i / 51
        x = 54 + t * (ancho - 66)
        # Amplitud decreciente: las firmas empiezan grandes y se apagan.
        amplitud = alto * 0.34 * (1 - 0.45 * t)
        # El armónico rápido rompe la onda regular: sin él parece un
        # electrocardiograma y no una firma.
        onda = (math.sin(t * 15 + 0.6) * amplitud
                + math.sin(t * 41 + 2.1) * amplitud * 0.30)
        deriva = math.sin(t * 3.1 + 1.2) * (alto * 0.14)
        puntos.append((x, alto * 0.50 + onda + deriva + rnd.uniform(-1.5, 1.5)))
    draw.line(puntos, fill=color + (240,), width=4, joint="curve")

    # Trazo de cierre, el subrayado que casi todo el mundo le pone a su firma.
    draw.line([(ancho * 0.12, alto * 0.86), (ancho * 0.88, alto * 0.74)],
              fill=color + (215,), width=3)
    img.alpha_composite(capa, (int(xy[0]), int(xy[1])))


def _cromatograma(ancho, alto, pico_principal=0.42):
    """
    Traza cromatográfica con un pico dominante.

    Es lo que convierte el informe de toxicología en algo que parece salido de
    un laboratorio y no de una plantilla de texto.
    """
    img = Image.new("RGBA", (ancho, alto), (246, 243, 233, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, ancho - 1, alto - 1], outline=(150, 140, 120, 255),
                   width=2)

    base_y = alto - 34
    draw.line([44, base_y, ancho - 20, base_y], fill=(120, 112, 96, 255), width=2)
    draw.line([44, 18, 44, base_y], fill=(120, 112, 96, 255), width=2)

    rnd = random.Random(88)
    # (posición relativa, altura relativa, ancho del pico)
    picos = [(0.10, 0.11, 0.016), (0.19, 0.07, 0.013), (0.28, 0.16, 0.018),
             (pico_principal, 0.94, 0.022), (0.55, 0.09, 0.014),
             (0.68, 0.13, 0.016), (0.81, 0.06, 0.012), (0.90, 0.10, 0.015)]

    puntos = []
    for i in range(ancho - 64):
        t = i / (ancho - 64)
        valor = sum(a * math.exp(-((t - p) ** 2) / (2 * w ** 2))
                    for p, a, w in picos)
        valor += rnd.uniform(-0.006, 0.006)
        puntos.append((44 + i, base_y - valor * (base_y - 30)))
    draw.line(puntos, fill=(58, 54, 46, 255), width=2)

    # El pico que importa, marcado.
    x_pico = 44 + pico_principal * (ancho - 64)
    draw.line([x_pico, 34, x_pico, base_y], fill=RED + (140,), width=2)
    draw.text((x_pico + 10, 30), "9,4 ng/mL", font=fuente("monob", 16),
              fill=RED + (255,))
    draw.text((x_pico + 10, 52), "glucósido cardíaco", font=fuente("mono", 13),
              fill=RED + (255,))

    draw.text((50, base_y + 10), "tiempo de retención (min)",
              font=fuente("mono", 12), fill=SOFT + (255,))
    return img


def _conclusion(draw, x, y, ancho, titulo, texto, alto=None, tam=17):
    """Caja de conclusión enmarcada en rojo. Devuelve la y siguiente."""
    fnt = fuente("mono", tam)
    lineas = ev.partir(draw, texto, fnt, ancho - 32)
    alto = alto or (44 + len(lineas) * (tam + 8) + 16)
    draw.rectangle([x, y, x + ancho, y + alto], fill=(238, 232, 218, 255),
                   outline=RED + (255,), width=4)
    draw.text((x + 16, y + 14), titulo, font=fuente("monob", tam),
              fill=RED + (255,))
    yy = y + 48
    for linea in lineas:
        draw.text((x + 16, yy), linea, font=fnt, fill=INK + (255,))
        yy += tam + 8
    return y + alto


# ─── EVIDENCIA A — Informe de toxicología ────────────────────────────────────


def ev_A():
    ancho, alto = 1120, 1330
    img = _formulario(ancho, alto, "LABORATORIO DE CIENCIAS FORENSES",
                      "SECCIÓN DE TOXICOLOGÍA ANALÍTICA",
                      "INFORME TOX-2211/26", semilla=17)
    draw = ImageDraw.Draw(img)
    margen = 44
    util = ancho - 2 * margen

    y = 132
    for etiqueta, valor in (
        ("EXPEDIENTE:", "002 — muerte de adulto mayor, 74 años"),
        ("MUESTRA:", "Sangre periférica y humor vítreo"),
        ("TOMA:", "12 de julio, 04:10 — hospital"),
        ("RECEPCIÓN:", "13 de julio  ·  INFORME: 21 de julio"),
    ):
        draw.text((margen, y), etiqueta, font=fuente("monob", 17),
                  fill=SOFT + (255,))
        draw.text((margen + 200, y), valor, font=fuente("mono", 17),
                  fill=INK + (255,))
        y += 30

    y += 22
    draw.text((margen, y), "RESULTADOS CUANTITATIVOS", font=fuente("monob", 19),
              fill=INK + (255,))
    y += 32

    y = _tabla(
        draw, margen, y,
        [("SUSTANCIA", 46), ("HALLADO", 18), ("REFERENCIA", 22), ("VALOR", 14)],
        [
            ("Etanol", "0,4 g/L", "—", "bajo"),
            ("Glucósido cardíaco (digitálico)", "9,4 ng/mL", "0,5 – 2,0 ng/mL",
             "×  8"),
            ("Antihipertensivo habitual", "en rango", "terapéutico", "normal"),
            ("Cribado de otras sustancias", "negativo", "—", "—"),
        ],
        util, destacar=(1,),
    )

    y += 30
    y = _conclusion(
        draw, margen, y, util, "VENTANA DE INGESTA ESTIMADA",
        "Entre las 21:30 y las 22:15 del sábado 11 de julio. La estimación se "
        "apoya en la curva de absorción y en la hora del colapso presenciado "
        "(22:40). La toma habitual de las 21:00, presenciada por varios "
        "asistentes, queda fuera de la ventana y no explica la concentración.",
    )

    y += 24
    y = _conclusion(
        draw, margen, y, util, "OBSERVACIÓN DEL PERITO",
        "La concentración hallada no es compatible con un error de dosificación "
        "ni con una toma doble accidental. Corresponde a una cantidad muy "
        "superior a la de cualquier presentación individual del tratamiento.",
    )

    y += 34
    draw.text((margen, y), "PERFIL CROMATOGRÁFICO", font=fuente("monob", 19),
              fill=INK + (255,))
    y += 30
    img.alpha_composite(_cromatograma(util, 260), (margen, y))

    draw.text((margen, alto - 148), "PERITO RESPONSABLE", font=fuente("monob", 15),
              fill=SOFT + (255,))
    _firma(img, (margen + 20, alto - 138), ancho=320, alto=62)
    draw.line([margen, alto - 74, margen + 380, alto - 74],
              fill=(120, 110, 92, 255), width=2)
    ev.sello(img, (ancho - 250, alto - 128), "VERIFICADO", angulo=-9, tam=36)
    return img


# ─── EVIDENCIA D — Control de acceso del condominio ──────────────────────────


def ev_D():
    ancho, alto = 1120, 1010
    img = _formulario(ancho, alto, "CONDOMINIO TERUMA",
                      "CASETA DE SEGURIDAD — BITÁCORA DE ACCESO",
                      "SÁBADO 11 DE JULIO", semilla=23)
    draw = ImageDraw.Draw(img)
    margen = 44
    util = ancho - 2 * margen

    y = 136
    draw.text((margen, y), "MOVIMIENTOS REGISTRADOS  ·  18:00 – 00:00",
              font=fuente("monob", 19), fill=INK + (255,))
    y += 34

    filas = [
        ("18:12", "INGRESO", "Vehicular", "Residente filial 14", "—"),
        ("18:40", "INGRESO", "Vehicular", "Residente filial 14", "—"),
        ("19:05", "INGRESO", "Vehicular", "Visita autorizada", "filial 14"),
        ("19:22", "INGRESO", "Vehicular", "Visita autorizada", "filial 14"),
        ("19:38", "INGRESO", "Peatonal", "Adulto mayor — a pie", "filial 14"),
        ("19:44", "INGRESO", "Vehicular", "Visita autorizada", "filial 14"),
        ("20:16", "INGRESO", "Vehicular", "Visita autorizada", "filial 14"),
        ("21:35", "SALIDA", "Peatonal", "Visita — filial 14", "sin vehículo"),
        ("21:50", "INGRESO", "Peatonal", "Visita — filial 14", "reingreso"),
        ("22:55", "INGRESO", "Vehicular", "AMBULANCIA", "emergencia"),
        ("23:10", "SALIDA", "Vehicular", "AMBULANCIA", "traslado"),
    ]
    y = _tabla(
        draw, margen, y,
        [("HORA", 12), ("TIPO", 16), ("MODO", 16), ("REGISTRO", 38),
         ("OBS.", 18)],
        filas, util, alto_fila=32, tam=15, destacar=(7, 8),
    )

    y += 28
    y = _conclusion(
        draw, margen, y, util, "CERTIFICACIÓN DE LA CASETA",
        "No se registra el ingreso de ninguna persona ajena al listado de "
        "residentes y visitas autorizadas de la filial 14 entre las 18:00 y las "
        "22:55. El portón peatonal y el vehicular cuentan con registro "
        "independiente y ambos coinciden.",
    )

    y += 22
    ev.manuscrito(img, (margen + 8, y + 6),
                  "los dos movimientos peatonales de las 21:35 y 21:50 "
                  "corresponden a la misma persona",
                  tam=27, fill=(196, 62, 50), semilla=31, ancho_max=util - 20)

    ev.sello(img, (ancho - 236, alto - 92), "SIN INGRESO", sub="EXTERNO",
             angulo=-8, tam=32, tam_sub=18)
    return img


# ─── EVIDENCIA F — Libreta de préstamos ──────────────────────────────────────

# Las cuotas están puestas para que la suma dé una cifra redonda: es la
# respuesta de la pregunta bonus B2 y tiene que poder verificarse a mano.
CUOTAS = [
    ("14/07/24", "250 000"),
    ("22/09/24", "400 000"),
    ("03/12/24", "180 000"),
    ("18/02/25", "750 000"),
    ("29/04/25", "320 000"),
    ("11/07/25", "1 200 000"),
    ("06/10/25", "560 000"),
    ("30/01/26", "900 000"),
    ("19/05/26", "300 000"),
]


def ev_F():
    """Foto de celular de una libreta manuscrita, tomada por el propio occiso."""
    ancho = 1000
    alto = round(ancho * RATIO_PAGINA)
    img = _mesa(ancho, alto, tono=(78, 72, 62))

    # La hoja de libreta, ligeramente rotada como en una foto de mano.
    hoja_a, hoja_h = 800, 1010
    hoja = ev.papel(hoja_a, hoja_h, color=(238, 233, 214), fibras=2400, semilla=61)
    hd = ImageDraw.Draw(hoja)

    for y in range(96, hoja_h - 30, 46):
        hd.line([54, y, hoja_a - 40, y], fill=(168, 178, 196, 255), width=2)
    hd.line([96, 40, 96, hoja_h - 30], fill=(206, 148, 140, 255), width=2)
    for y in range(46, hoja_h - 20, 42):
        hd.ellipse([16, y, 34, y + 18], fill=(96, 90, 78, 255))

    ev.manuscrito(hoja, (120, 56), "M.  —  cuentas", tam=40, fill=(34, 42, 78),
                  semilla=5)
    ev.manuscrito(hoja, (500, 62), "«queda debiendo»", tam=26,
                  fill=(34, 42, 78), semilla=9)

    y = 148
    for fecha, monto in CUOTAS:
        ev.manuscrito(hoja, (120, y), fecha, tam=30, fill=(34, 42, 78),
                      semilla=hash(fecha) % 500)
        ev.manuscrito(hoja, (430, y), monto, tam=30, fill=(34, 42, 78),
                      semilla=hash(monto) % 500)
        y += 46

    hd.line([120, y + 8, hoja_a - 60, y + 8], fill=(34, 42, 78, 255), width=3)
    ev.manuscrito(hoja, (120, y + 26), "total", tam=34, fill=(34, 42, 78),
                  semilla=77)
    hd.line([250, y + 66, 660, y + 66], fill=(34, 42, 78, 255), width=2)

    ev.pegar_rotado(img, hoja, (ancho / 2, alto / 2 + 56), -1.8)

    # Marca de que es una foto tomada con teléfono, no un escaneo.
    draw = ImageDraw.Draw(img)
    draw.text((44, 112), "ARCHIVO DE IMAGEN — CÁMARA DEL OCCISO",
              font=fuente("mono", 20), fill=(206, 198, 180, 255))
    draw.text((44, 142), "capturada 19/06/26 · 3 semanas antes del hecho",
              font=fuente("mono", 17), fill=(168, 158, 138, 255))
    return img


# ─── EVIDENCIA G — Mensaje de las 20:05 ──────────────────────────────────────


def _burbuja_chat(draw, x, y, ancho, texto, hora, propia=False, autor=""):
    """Burbuja de mensajería en modo oscuro. Devuelve la y siguiente."""
    fnt = fuente("sans", 21)
    lineas = ev.partir(draw, texto, fnt, ancho - 40)
    # +22 al final: sin ese aire la hora se monta sobre el último renglón.
    alto = 30 + len(lineas) * 29 + 22 + (26 if autor else 0)
    color = (46, 74, 60, 255) if propia else (48, 48, 52, 255)
    draw.rounded_rectangle([x, y, x + ancho, y + alto], radius=16, fill=color)

    yy = y + 14
    if autor:
        draw.text((x + 20, yy), autor, font=fuente("sansb", 18),
                  fill=(122, 176, 214, 255))
        yy += 26
    for linea in lineas:
        draw.text((x + 20, yy), linea, font=fnt, fill=(232, 230, 226, 255))
        yy += 29
    ancho_h = medir(draw, hora, fuente("sans", 15))[0]
    draw.text((x + ancho - 16 - ancho_h, y + alto - 22), hora,
              font=fuente("sans", 15), fill=(150, 150, 152, 255))
    return y + alto + 16


def ev_G():
    ancho, alto = 900, 1120
    img = Image.new("RGBA", (ancho, alto), (24, 24, 26, 255))
    draw = ImageDraw.Draw(img)

    # Cabecera de la aplicación.
    draw.rectangle([0, 0, ancho, 116], fill=(38, 38, 42, 255))
    draw.ellipse([28, 30, 84, 86], fill=(86, 92, 104, 255))
    draw.text((104, 38), "FAMILIA", font=fuente("sansb", 26),
              fill=(238, 236, 232, 255))
    draw.text((104, 72), "14 participantes", font=fuente("sans", 17),
              fill=(150, 150, 152, 255))
    draw.text((ancho - 120, 48), "· · ·", font=fuente("sansb", 26),
              fill=(150, 150, 152, 255))

    draw.rounded_rectangle([ancho / 2 - 110, 140, ancho / 2 + 110, 178],
                           radius=14, fill=(44, 44, 48, 255))
    draw.text((ancho / 2 - 78, 148), "SÁBADO 11 JUL", font=fuente("sans", 17),
              fill=(160, 160, 162, 255))

    y = 206
    y = _burbuja_chat(draw, 40, y, 560,
                      "Ya vamos saliendo, llevamos el hielo", "19:12",
                      autor="████████")
    y = _burbuja_chat(draw, 300, y, 560,
                      "Perfecto, aquí ya está todo listo", "19:20", propia=True)
    y = _burbuja_chat(draw, 40, y, 560,
                      "Abuelo ya va llegando caminando, lo vi en la entrada",
                      "19:36", autor="████")
    y = _burbuja_chat(draw, 40, y, 600,
                      "Alguien me explica por qué hay que esperar hasta el "
                      "brindis para todo en esta familia", "19:58",
                      autor="██████")

    # El mensaje que importa. El aire extra es para que la etiqueta roja del
    # recuadro, que se dibuja por encima, no caiga sobre la burbuja anterior.
    y += 26
    y_clave = y
    y = _burbuja_chat(draw, 40, y, 520, "hoy lo digo", "20:05",
                      autor="ABUELO")
    ev.recuadro_rojo(img, (28, y_clave - 10, 572, y - 6), "SIN RESPUESTAS")

    y += 26
    y = _burbuja_chat(draw, 40, y, 600,
                      "Ya casi servimos, vengan todos a la mesa", "21:44",
                      autor="████")
    y = _burbuja_chat(draw, 300, y, 560, "LLAMEN UNA AMBULANCIA", "22:41",
                      propia=True)

    draw.rectangle([0, alto - 96, ancho, alto], fill=(38, 38, 42, 255))
    draw.rounded_rectangle([28, alto - 76, ancho - 120, alto - 20], radius=28,
                           fill=(52, 52, 56, 255))
    draw.text((52, alto - 62), "Mensaje", font=fuente("sans", 20),
              fill=(120, 120, 124, 255))
    return img


# ─── EVIDENCIA H — Transcripción de audio ────────────────────────────────────


def ev_H():
    ancho, alto = 1120, 960
    img = _formulario(ancho, alto, "UNIDAD DE ANÁLISIS DE AUDIO",
                      "TRANSCRIPCIÓN DE REGISTRO INCIDENTAL",
                      "PISTA 07 — 21:19 a 21:24", semilla=29)
    draw = ImageDraw.Draw(img)
    margen = 44
    util = ancho - 2 * margen

    y = 132
    for etiqueta, valor in (
        ("ORIGEN:", "Audio de fondo de una videollamada — Sujeto n.º 04"),
        ("CAPTURA:", "No intencional. La cámara apuntaba al interior."),
        ("CALIDAD:", "Baja. Se recupera cerca del 20 % del intercambio."),
        ("VOCES:", "Dos. Ningún hablante se identifica por su nombre."),
    ):
        draw.text((margen, y), etiqueta, font=fuente("monob", 17),
                  fill=SOFT + (255,))
        draw.text((margen + 168, y), valor, font=fuente("mono", 16),
                  fill=INK + (255,))
        y += 30

    y += 20
    draw.text((margen, y), "TRANSCRIPCIÓN LITERAL", font=fuente("monob", 19),
              fill=INK + (255,))
    y += 34

    fragmentos = [
        ("21:19:48", "VOZ A", "[ininteligible] ...dos años. Dos años, ██████."),
        ("21:20:15", "VOZ B", "[ininteligible]"),
        ("21:20:31", "VOZ A", "...no me interesa cómo lo arreglemos ahora..."),
        ("21:21:02", "VOZ B", "...bajá la voz, te van a [ininteligible]..."),
        ("21:21:40", "VOZ A", "...hoy en el brindis lo digo. Delante de todos."),
        ("21:22:09", "VOZ B", "[ininteligible] ...eso me arruina, ██████..."),
        ("21:22:55", "VOZ A", "[ininteligible]"),
        ("21:23:30", "—", "Ruido de puerta. Fin del registro útil."),
    ]
    for hora, voz, texto in fragmentos:
        clave = "lo digo" in texto or "arruina" in texto
        draw.rectangle([margen, y, margen + util, y + 52],
                       fill=(232, 205, 197, 255) if clave else (232, 227, 212, 255))
        draw.line([margen, y + 52, margen + util, y + 52],
                  fill=(190, 180, 158, 255), width=1)
        draw.text((margen + 12, y + 8), hora, font=fuente("mono", 15),
                  fill=SOFT + (255,))
        draw.text((margen + 12, y + 28), voz, font=fuente("monob", 15),
                  fill=(RED if clave else INK) + (255,))
        draw.text((margen + 130, y + 16), texto,
                  font=fuente("monoi" if not clave else "monob", 17),
                  fill=(RED if clave else INK) + (255,))
        y += 52

    draw.rectangle([margen, y - 52 * len(fragmentos), margen + util, y],
                   outline=(120, 110, 92, 255), width=2)

    y += 28
    _conclusion(
        draw, margen, y, util, "NOTA DEL ANALISTA",
        "La VOZ A presenta rasgos compatibles con los de un hablante de edad "
        "avanzada. La VOZ B es masculina y no se identifica. El registro "
        "confirma que hubo un intercambio en el exterior dentro del intervalo "
        "señalado, pero no permite atribuirlo a ninguna persona concreta.",
    )
    return img


# ─── Fotografías del carrete ─────────────────────────────────────────────────


def _grano_fotografico(img, sigma=9.0, semilla=5):
    """
    Ruido de sensor de poca luz.

    Es mucho más fuerte que el envejecido general de las evidencias: una foto
    de celular tomada de noche tiene grano visible, y ese grano es justamente
    lo que justifica que no se distingan las caras.
    """
    arr = np.array(img.convert("RGB")).astype(np.float32)
    rnd = np.random.default_rng(semilla)
    # El ruido crece en las sombras, como en un sensor real.
    luminancia = arr.mean(axis=2, keepdims=True) / 255.0
    arr += rnd.normal(0, 1, arr.shape) * sigma * (1.6 - luminancia)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def _marca_horaria(img, texto, esquina=(None, None)):
    """Marca de fecha y hora de la cámara, en el ámbar de siempre."""
    draw = ImageDraw.Draw(img)
    fnt = fuente("mono", 30)
    ancho_txt, alto_txt = medir(draw, texto, fnt)
    x = esquina[0] if esquina[0] is not None else img.width - 40 - ancho_txt
    y = esquina[1] if esquina[1] is not None else img.height - 150
    # Sombra dura: así se imprimían las marcas de las cámaras.
    draw.text((x + 2, y + 2), texto, font=fnt, fill=(20, 16, 8, 200))
    draw.text((x, y), texto, font=fnt, fill=(232, 186, 62, 255))


def _ampliacion(img, origen, destino, etiqueta):
    """
    Recorta una zona de la propia foto y la pega ampliada con marco rojo.

    Usa los píxeles reales, no un dibujo aparte: es lo que hace creíble que la
    ampliación salga de esa toma y no de otra.
    """
    recorte = img.crop(tuple(int(v) for v in origen))
    ancho_d = int(destino[2] - destino[0])
    alto_d = int(destino[3] - destino[1])
    recorte = recorte.resize((ancho_d, alto_d), Image.LANCZOS)
    recorte = recorte.filter(ImageFilter.UnsharpMask(radius=3, percent=140,
                                                     threshold=2))
    img.alpha_composite(recorte.convert("RGBA"),
                        (int(destino[0]), int(destino[1])))

    draw = ImageDraw.Draw(img)
    draw.rectangle(list(destino), outline=RED + (255,), width=5)
    draw.rectangle(list(origen), outline=RED + (255,), width=4)
    # Línea que une el origen con la ampliación.
    draw.line([origen[2], origen[1], destino[0], destino[3]],
              fill=RED + (180,), width=3)

    fnt = fuente("monob", 22)
    ancho_txt = medir(draw, etiqueta, fnt)[0]
    draw.rectangle([destino[0], destino[1] - 34, destino[0] + ancho_txt + 20,
                    destino[1]], fill=RED + (255,))
    draw.text((destino[0] + 10, destino[1] - 30), etiqueta, font=fnt,
              fill=(246, 240, 228, 255))


def _capa_difusa(tamano, pintar, desenfoque):
    """
    Dibuja en una capa aparte y la difumina antes de componerla.

    Es la única forma de que unas primitivas pasen por fotografía: con el
    contorno nítido se leen como dibujo. La forma tiene que perderse.
    """
    capa = Image.new("RGBA", tamano, (0, 0, 0, 0))
    pintar(ImageDraw.Draw(capa))
    return capa.filter(ImageFilter.GaussianBlur(desenfoque))


def ev_B():
    """
    Parqueo, 21:22. Dos figuras junto al vehículo.

    La toma es deliberadamente mala: de noche, a contraluz y desde lejos. Lo
    único que la imagen sostiene es que había dos personas y que una vestía
    algo claro. Cualquier cosa más definida sería una evidencia que el caso no
    tiene — y delataría al culpable demasiado pronto.
    """
    ancho = 1000
    alto = round(ancho * RATIO_PAGINA)

    # Cielo nocturno y suelo, con una farola cálida al fondo.
    ys = np.linspace(0, 1, alto)[:, None]
    xs = np.linspace(0, 1, ancho)[None, :]
    cielo = np.clip(14 + 20 * (1 - ys), 0, 255)
    suelo = np.where(ys > 0.64, 22 + 12 * (ys - 0.64), 0)
    farola = 62 * np.exp(-(((xs - 0.82) ** 2) / 0.008 + ((ys - 0.26) ** 2) / 0.012))

    r = cielo + suelo + farola * 1.34
    g = cielo * 0.97 + suelo + farola * 1.02
    b = cielo * 1.22 + suelo * 1.06 + farola * 0.50
    base = np.clip(np.dstack([r, g, b]) * np.ones((alto, ancho, 3)), 0, 255)
    img = Image.fromarray(base.astype(np.uint8), "RGB").convert("RGBA")

    # El vehículo: una masa oscura y poco más. De noche un carro es eso.
    def coche(dr):
        dr.polygon([(150, 790), (200, 706), (330, 662), (560, 656), (700, 696),
                    (792, 748), (808, 806), (786, 848), (172, 852), (146, 818)],
                   fill=(21, 22, 26, 255))
        dr.line([(200, 706), (330, 662), (560, 656), (700, 696)],
                fill=(120, 128, 142, 215), width=6)   # brillo del techo
        dr.polygon([(306, 670), (536, 666), (606, 704), (292, 708)],
                   fill=(44, 50, 62, 210))            # parabrisas
        dr.ellipse([740, 746, 796, 780], fill=(188, 74, 52, 235))  # piloto
    img.alpha_composite(_capa_difusa((ancho, alto), coche, 7))

    # Las dos figuras, como manchas. Sin cabeza recortada ni torso geométrico:
    # a esa distancia y con esa luz una persona es un borrón vertical.
    def figuras(dr):
        # Izquierda, ropa oscura: apenas se despega del fondo.
        dr.ellipse([392, 508, 476, 604], fill=(34, 33, 36, 255))
        dr.ellipse([374, 576, 496, 812], fill=(30, 29, 33, 255))
        # Derecha, ropa clara: es lo único que la foto realmente aporta.
        dr.ellipse([520, 504, 600, 596], fill=(50, 48, 50, 255))
        dr.ellipse([502, 570, 618, 806], fill=(96, 96, 98, 255))
        dr.ellipse([524, 600, 604, 742], fill=(114, 113, 112, 255))
    img.alpha_composite(_capa_difusa((ancho, alto), figuras, 13))

    img = img.filter(ImageFilter.GaussianBlur(3.2))
    img = _grano_fotografico(img, sigma=13.0, semilla=15)

    _marca_horaria(img, "2026-07-11  21:22:14")
    _ampliacion(img, (486, 486, 640, 700), (628, 226, 944, 666),
                "AMPLIACIÓN — PRENDA CLARA")

    draw = ImageDraw.Draw(img)
    draw.text((44, 118), "CARRETE DEL SUJETO N.º 03 — TOMA 41 DE 62",
              font=fuente("mono", 20), fill=(206, 198, 180, 255))
    draw.text((44, 146), "sin rostros identificables",
              font=fuente("mono", 17), fill=(168, 160, 144, 255))
    return img


def ev_C():
    """Brindis, 21:51. La entrega del vaso. El rostro queda fuera de cuadro."""
    ancho = 1000
    alto = round(ancho * RATIO_PAGINA)

    # Interior cálido, muy poca luz, con bokeh al fondo.
    ys = np.linspace(0, 1, alto)[:, None]
    xs = np.linspace(0, 1, ancho)[None, :]
    calido = 44 + 70 * np.exp(-(((xs - 0.42) ** 2) / 0.10 + ((ys - 0.34) ** 2) / 0.13))
    r = np.clip(calido * 1.32, 0, 255)
    g = np.clip(calido * 1.02, 0, 255)
    b = np.clip(calido * 0.66, 0, 255)
    base = np.clip(np.dstack([r, g, b]) * np.ones((alto, ancho, 3)), 0, 255)
    img = Image.fromarray(base.astype(np.uint8), "RGB").convert("RGBA")

    # Luces desenfocadas del fondo.
    bokeh = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    rnd = random.Random(19)
    for _ in range(22):
        cx, cy = rnd.uniform(60, ancho - 60), rnd.uniform(150, 700)
        r_luz = rnd.uniform(24, 62)
        bd.ellipse([cx - r_luz, cy - r_luz, cx + r_luz, cy + r_luz],
                   fill=(238, 196, 122, rnd.randint(30, 70)))
    img.alpha_composite(bokeh.filter(ImageFilter.GaussianBlur(22)))

    # Los presentes, de espaldas y desenfocados: son el primer plano fuera de
    # foco que encuadra la escena, no figuras que haya que distinguir.
    def presentes(dr):
        dr.rectangle([0, 880, ancho, alto], fill=(28, 20, 13, 255))
        for cx, altura in ((110, 300), (880, 360)):
            dr.ellipse([cx - 78, 880 - altura, cx + 78, 880 - altura + 168],
                       fill=(22, 16, 11, 255))
            dr.ellipse([cx - 118, 880 - altura + 108, cx + 118, 960],
                       fill=(22, 16, 11, 255))
    img.alpha_composite(_capa_difusa((ancho, alto), presentes, 16))

    # El gesto que importa: el brazo entrando por la izquierda con el vaso.
    def gesto(dr):
        dr.polygon([(0, 430), (250, 470), (300, 530), (0, 570)],
                   fill=(58, 44, 32, 255))                      # manga
        dr.polygon([(250, 466), (334, 480), (356, 538), (296, 534)],
                   fill=(146, 108, 78, 255))                    # antebrazo
        dr.ellipse([236, 458, 288, 496], fill=(92, 88, 92, 255))    # reloj
        dr.ellipse([243, 464, 281, 490], fill=(174, 172, 176, 255))
        # La mano que lo recibe, del otro lado.
        dr.polygon([(474, 506), (550, 490), (570, 546), (490, 562)],
                   fill=(150, 116, 86, 255))
    img.alpha_composite(_capa_difusa((ancho, alto), gesto, 5))

    # El vaso va menos difuso: es lo único enfocado de la toma.
    def vaso(dr):
        dr.polygon([(352, 460), (434, 460), (422, 570), (364, 570)],
                   fill=(206, 176, 120, 140))
        dr.ellipse([350, 448, 436, 474], fill=(228, 204, 156, 160))
        dr.line([(354, 462), (366, 566)], fill=(246, 232, 200, 200), width=4)
    img.alpha_composite(_capa_difusa((ancho, alto), vaso, 2))

    img = img.filter(ImageFilter.GaussianBlur(2.4))
    img = _grano_fotografico(img, sigma=8.0, semilla=23)

    _marca_horaria(img, "2026-07-11  21:51:07")
    _ampliacion(img, (214, 436, 454, 586), (556, 700, 950, 946),
                "AMPLIACIÓN — MANGA Y RELOJ")

    draw = ImageDraw.Draw(img)
    draw.text((44, 118), "CARRETE DEL SUJETO N.º 03 — TOMA 58 DE 62",
              font=fuente("mono", 20), fill=(226, 214, 190, 255))
    draw.text((44, 146), "el rostro de quien entrega el vaso queda fuera de cuadro",
              font=fuente("mono", 17), fill=(198, 184, 158, 255))
    return img


# ─── Registro y CLI ──────────────────────────────────────────────────────────

GENERADORES = {
    "A": ev_A,
    "B": ev_B,
    "C": ev_C,
    "D": ev_D,
    "E": ev_E,
    "F": ev_F,
    "G": ev_G,
    "H": ev_H,
    "J": ev_J,
}


def main(letras=None):
    os.makedirs(SALIDA, exist_ok=True)
    letras = [x.upper() for x in (letras or GENERADORES)]
    for letra in letras:
        if letra not in GENERADORES:
            print(f"  ·  {letra}: sin generador todavía, se omite")
            continue
        ruta = os.path.join(SALIDA, f"EV_{letra}.jpg")
        ev.guardar(GENERADORES[letra](), ruta)
        with Image.open(ruta) as im:
            print(f"  ✓  EV_{letra}.jpg   {im.width}×{im.height}")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
