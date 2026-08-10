"""
Sistema de diseño del Expediente — tokens y primitivas de página.

Todo el PDF se compone con el canvas de bajo nivel de reportlab (no platypus),
así que este módulo concentra lo que de otra forma se repetiría en cada página:
la paleta, las fuentes, la retícula y los bloques que se dibujan una y otra vez.

Los valores vienen del manual de producción §1. No inventar intermedios.
"""

import random

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Retícula ────────────────────────────────────────────────────────────────

PAGESIZE = letter
W, H = PAGESIZE  # 612 × 792 pt
MARGEN = 44.0  # todo el contenido se alinea a este margen lateral
ANCHO_UTIL = W - 2 * MARGEN

BARRA_Y = H - 62  # barra superior oscura
BARRA_ALTO = 34
FRANJA_Y = H - 148  # franja de identificación (fichas y evidencias)
FRANJA_ALTO = 86
PIE_FILETE_Y = 44
PIE_TEXTO_Y = 30

# ─── Paleta ──────────────────────────────────────────────────────────────────

KRAFT = HexColor("#cdbfa2")  # fondo de portada, cartulina de folder
PAPER = HexColor("#e7e1d3")  # fondo de páginas interiores
PAPER2 = HexColor("#ddd6c5")  # bloques secundarios
BAND = HexColor("#c0b193")  # franja de identificación y títulos de sección
DATA = HexColor("#ded7c6")  # cajas de datos y citas
DARK = HexColor("#26241f")  # barra superior, fondos oscuros
INK = HexColor("#1d1b19")  # texto de cuerpo
SOFT = HexColor("#5f584d")  # etiquetas, texto secundario
RED = HexColor("#8f2a22")  # sellos, acentos, numeración de página
RED_L = HexColor("#b8564a")  # acento sobre fondo oscuro
FRAME = HexColor("#6f6552")  # marcos de fotografía
RULE = HexColor("#8a7d64")  # filetes finos
FIBRA = HexColor("#cfc6b0")  # textura de papel

# ─── Tipografía ──────────────────────────────────────────────────────────────

MONO, MONOB, MONOI = "Mono", "MonoB", "MonoI"
SANS, SANSB = "Sans", "SansB"

_DIR_FUENTES = "/usr/share/fonts/truetype/liberation"
_FUENTES = {
    MONO: "LiberationMono-Regular.ttf",
    MONOB: "LiberationMono-Bold.ttf",
    MONOI: "LiberationMono-Italic.ttf",
    SANS: "LiberationSans-Regular.ttf",
    SANSB: "LiberationSans-Bold.ttf",
}


def registrar_fuentes(dir_fuentes=_DIR_FUENTES):
    """Registra los TTF de Liberation. Sin esto los acentos y la ñ salen rotos."""
    for alias, archivo in _FUENTES.items():
        pdfmetrics.registerFont(TTFont(alias, f"{dir_fuentes}/{archivo}"))


# ─── Texto ───────────────────────────────────────────────────────────────────


def ancho(texto, fuente, tam):
    return pdfmetrics.stringWidth(texto, fuente, tam)


def partir(texto, fuente, tam, ancho_max):
    """Parte un texto en líneas que quepan en ancho_max. Respeta los \n."""
    lineas = []
    for parrafo in texto.split("\n"):
        palabras, actual = parrafo.split(), ""
        for palabra in palabras:
            tentativa = f"{actual} {palabra}".strip()
            if ancho(tentativa, fuente, tam) <= ancho_max:
                actual = tentativa
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def bloque(c, x, y, texto, ancho_max, fuente=MONO, tam=9.0, inter=13.2,
           color=INK, justificado=True):
    """
    Dibuja un párrafo y devuelve la y donde quedó el cursor.

    La justificación reparte el sobrante entre los espacios de la línea. La
    última línea de cada párrafo nunca se justifica, para que no quede rala.
    """
    c.setFillColor(color)
    c.setFont(fuente, tam)
    lineas = partir(texto, fuente, tam, ancho_max)
    for i, linea in enumerate(lineas):
        ultima = i == len(lineas) - 1
        palabras = linea.split()
        if justificado and not ultima and len(palabras) > 1:
            sobra = ancho_max - ancho("".join(palabras), fuente, tam)
            hueco = sobra / (len(palabras) - 1)
            cursor = x
            for palabra in palabras:
                c.drawString(cursor, y, palabra)
                cursor += ancho(palabra, fuente, tam) + hueco
        else:
            c.drawString(x, y, linea)
        y -= inter
    return y


def alto_bloque(texto, ancho_max, fuente=MONO, tam=9.0, inter=13.2):
    """Cuánto va a medir un bloque, para reservar espacio antes de dibujarlo."""
    return len(partir(texto, fuente, tam, ancho_max)) * inter


# ─── Fondo y textura ─────────────────────────────────────────────────────────


def fondo(c, color=PAPER, fibras=170, semilla=None):
    """
    Pinta el fondo y le tira fibras de papel encima.

    Las fibras son segmentos cortos en distintos ángulos. Con semilla fija el
    resultado es reproducible, que es lo que uno quiere al regenerar el PDF.
    """
    c.setFillColor(color)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    rnd = random.Random(semilla) if semilla is not None else random
    c.setStrokeColor(FIBRA)
    c.setLineWidth(0.35)
    for _ in range(fibras):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        largo, ang = rnd.uniform(2, 9), rnd.uniform(0, 3.14159)
        c.line(x, y, x + largo * (1 if rnd.random() > 0.5 else -1), y + largo * ang / 3)


# ─── Bloques recurrentes ─────────────────────────────────────────────────────


def barra_superior(c, izq, der, fondo_color=DARK, texto_color=PAPER):
    """Barra oscura del encabezado: expediente a la izquierda, sección a la derecha."""
    c.setFillColor(fondo_color)
    c.rect(0, BARRA_Y, W, BARRA_ALTO, stroke=0, fill=1)
    c.setFillColor(texto_color)
    c.setFont(MONOB, 10)
    c.drawString(MARGEN, BARRA_Y + 12, izq)
    if der:
        c.setFont(MONO, 8.6)
        c.drawRightString(W - MARGEN, BARRA_Y + 12.5, der)


def franja_identificacion(c, titulo, subtitulo="", numero="", color_numero=None):
    """
    Franja clara bajo la barra: alias grande a la izquierda, número a la derecha.
    Es lo que le da a cada ficha su golpe de vista.
    """
    c.setFillColor(BAND)
    c.rect(0, FRANJA_Y, W, FRANJA_ALTO, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont(MONOB, 40)
    c.drawString(MARGEN, FRANJA_Y + 38, titulo)
    if subtitulo:
        c.setFillColor(SOFT)
        c.setFont(MONO, 8.4)
        c.drawString(MARGEN, FRANJA_Y + 20, subtitulo)
    if numero:
        c.setFillColor(color_numero or HexColor("#a8946f"))
        c.setFont(MONOB, 52)
        c.drawRightString(W - MARGEN, FRANJA_Y + 30, numero)


def titular(c, y, texto, sub=""):
    """Titular de página con filete rojo debajo. Para páginas sin franja."""
    c.setFillColor(INK)
    c.setFont(MONOB, 20)
    c.drawString(MARGEN, y, texto)
    c.setStrokeColor(RED)
    c.setLineWidth(2.5)
    ancho_filete = min(ancho(texto, MONOB, 20) + 20, ANCHO_UTIL)
    c.line(MARGEN, y - 9, MARGEN + ancho_filete, y - 9)
    if sub:
        c.setFillColor(SOFT)
        c.setFont(MONO, 8.6)
        c.drawString(MARGEN, y - 24, sub)
        return y - 40
    return y - 26


def banda_seccion(c, y, texto, x=MARGEN, ancho_banda=None, color=BAND):
    """Título de sección sobre franja clara. Devuelve la y del contenido."""
    ancho_banda = ancho_banda or ANCHO_UTIL
    c.setFillColor(color)
    c.rect(x, y, ancho_banda, 18, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(MONOB, 9.5)
    c.drawString(x + 8, y + 5.5, texto)
    return y - 14


def caja(c, x, y, ancho_caja, alto_caja, relleno=DATA, borde=None, grosor=0.6):
    c.setFillColor(relleno)
    if borde:
        c.setStrokeColor(borde)
        c.setLineWidth(grosor)
    c.rect(x, y, ancho_caja, alto_caja, stroke=1 if borde else 0, fill=1)


def renglones(c, x, y, ancho_r, cantidad=3, paso=17, color=RULE):
    """Renglones en blanco para que el equipo escriba encima."""
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    for i in range(cantidad):
        c.line(x, y - i * paso, x + ancho_r, y - i * paso)
    return y - cantidad * paso


def burbuja(c, x, y, r=6, color=INK, grosor=1.1):
    c.setStrokeColor(color)
    c.setLineWidth(grosor)
    c.circle(x, y, r, stroke=1, fill=0)


def sello(c, x, y, texto, sub="", angulo=-13, color=RED, tam=19, tam_sub=8.5):
    """
    Sello rotado con doble marco. El ángulo torcido es lo que lo hace ver
    estampado a mano y no impreso con la página.
    """
    c.saveState()
    c.translate(x, y)
    c.rotate(angulo)

    ancho_texto = ancho(texto, MONOB, tam)
    pad_x, pad_y = 14, 10
    ancho_marco = ancho_texto + 2 * pad_x
    alto_marco = tam + 2 * pad_y + (tam_sub + 4 if sub else 0)

    c.setStrokeColor(color)
    c.setLineWidth(2.6)
    c.rect(-ancho_marco / 2, -alto_marco / 2, ancho_marco, alto_marco, stroke=1, fill=0)
    c.setLineWidth(0.8)
    c.rect(-ancho_marco / 2 + 3.5, -alto_marco / 2 + 3.5,
           ancho_marco - 7, alto_marco - 7, stroke=1, fill=0)

    c.setFillColor(color)
    c.setFont(MONOB, tam)
    base = -alto_marco / 2 + pad_y + (tam_sub + 2 if sub else 0)
    c.drawCentredString(0, base, texto)
    if sub:
        c.setFont(MONOB, tam_sub)
        c.drawCentredString(0, -alto_marco / 2 + pad_y - 3, sub)
    c.restoreState()


def pie(c, izq, etiqueta="", numero=None, color_numero=RED, color_texto=SOFT,
        color_filete=RULE):
    c.setStrokeColor(color_filete)
    c.setLineWidth(0.6)
    c.line(MARGEN, PIE_FILETE_Y, W - MARGEN, PIE_FILETE_Y)
    c.setFillColor(color_texto)
    c.setFont(MONO, 8.5)
    c.drawString(MARGEN, PIE_TEXTO_Y, izq)
    if etiqueta:
        c.setFillColor(color_numero)
        c.setFont(MONOB, 8.5)
        c.drawRightString(W - MARGEN, PIE_TEXTO_Y, etiqueta)
    if numero is not None:
        c.setFillColor(color_texto)
        c.setFont(MONO, 8.5)
        c.drawCentredString(W / 2, PIE_TEXTO_Y, str(numero))


def tachado(c, x, y, ancho_t, alto_t=9.5, color=INK):
    """Barra negra sobre un nombre legal. El expediente nunca los muestra."""
    c.setFillColor(color)
    c.rect(x, y, ancho_t, alto_t, stroke=0, fill=1)


def par_dato(c, x, y, etiqueta, valor, ancho_valor, ancho_etiqueta=92,
             tam=9.2, inter=12.6, color_valor=INK):
    """Fila etiqueta/valor de las cajas de datos. Devuelve la y siguiente."""
    c.setFillColor(SOFT)
    c.setFont(MONOB, tam)
    c.drawString(x, y, etiqueta)
    c.setFillColor(color_valor)
    c.setFont(MONO, tam)
    lineas = partir(valor, MONO, tam, ancho_valor)
    for linea in lineas:
        c.drawString(x + ancho_etiqueta, y, linea)
        y -= inter
    return y
