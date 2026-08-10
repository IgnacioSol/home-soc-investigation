#!/usr/bin/env python3
"""
Genera las imágenes de evidencia del EXPEDIENTE 002.

    python3 make_evidence.py            # todas
    python3 make_evidence.py E J        # solo algunas

Cada función `ev_X` devuelve una imagen RGBA ya compuesta; el guardado y el
envejecido común los hace `evidencia_lib.guardar`, para que las diez piezas
compartan exactamente la misma piel.
"""

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


# ─── Registro y CLI ──────────────────────────────────────────────────────────

GENERADORES = {
    "E": ev_E,
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
