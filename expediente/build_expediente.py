#!/usr/bin/env python3
"""
Compone el EXPEDIENTE 002 — EL CONSTRUCTOR.

    python3 build_expediente.py             # el expediente completo
    python3 build_expediente.py --muestra   # solo las páginas de validación

Una función por tipo de página. Los datos vienen de caso.py; las imágenes de
evidencia, de evidence/; los retratos ya tratados, de photos_fbi/.
"""

import argparse
import os

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

import caso
import design as d
from design import (ANCHO_UTIL, BAND, DATA, FRAME, INK, MARGEN, MONO, MONOB,
                    MONOI, PAPER, PAPER2, RED, RULE, SOFT, W)

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_RETRATOS = os.path.join(BASE, "photos_fbi")
DIR_EVIDENCIA = os.path.join(BASE, "evidence")

PIE_IZQ = f"EXPEDIENTE {caso.CASO}"


# ─── Auxiliares de página ────────────────────────────────────────────────────


def seccion(c, y, titulo, x=MARGEN, ancho=ANCHO_UTIL):
    """Banda de sección con su borde superior en `y`. Devuelve la primera línea base."""
    d.banda_seccion(c, y - 18, titulo, x=x, ancho_banda=ancho)
    return y - 32


def retrato(c, alias, x, y, lado):
    """
    Retrato con marco doble y escala de altura al costado.

    Si todavía no hay foto tratada para ese alias, dibuja el recuadro de
    fotografía pendiente en vez de fallar: así el expediente se puede componer
    y revisar antes de que lleguen los diez archivos.
    """
    ruta = os.path.join(DIR_RETRATOS, f"{alias}.jpg")

    c.setStrokeColor(FRAME)
    c.setLineWidth(2.2)
    c.rect(x, y, lado, lado, stroke=1, fill=0)
    c.setLineWidth(0.7)
    c.rect(x - 4, y - 4, lado + 8, lado + 8, stroke=1, fill=0)

    if os.path.exists(ruta):
        c.drawImage(ImageReader(ruta), x, y, lado, lado,
                    preserveAspectRatio=True, anchor="c")
    else:
        c.setFillColor(d.HexColor("#4a453d"))
        c.rect(x, y, lado, lado, stroke=0, fill=1)
        c.setFillColor(PAPER2)
        c.setFont(MONOB, 11)
        c.drawCentredString(x + lado / 2, y + lado / 2 + 6, "FOTOGRAFÍA")
        c.drawCentredString(x + lado / 2, y + lado / 2 - 8, "PENDIENTE")
        c.setFont(MONO, 7.4)
        c.setFillColor(d.HexColor("#9c9384"))
        c.drawCentredString(x + lado / 2, y + lado / 2 - 26, "archivo no recibido")

    # Escala de altura tipo rueda de reconocimiento.
    c.setStrokeColor(RULE)
    c.setFillColor(SOFT)
    c.setFont(MONO, 6.4)
    c.setLineWidth(0.5)
    for i, marca in enumerate(range(200, 110, -20)):
        yy = y + lado - 14 - i * (lado - 28) / 4
        c.line(x + lado + 10, yy, x + lado + 20, yy)
        c.drawString(x + lado + 24, yy - 2, str(marca))


def caja_declaracion(c, x, y, ancho, alto, rotulo, fecha, texto):
    """
    Caja de declaración: rótulo, fecha de la toma y el texto entre comillas.

    Las dos declaraciones de cada sujeto van lado a lado a propósito — el juego
    entero consiste en compararlas, y apiladas no se comparan igual.
    """
    d.caja(c, x, y, ancho, alto, relleno=DATA)
    c.setFillColor(RED)
    c.rect(x, y, 2.6, alto, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont(MONOB, 8.2)
    c.drawString(x + 10, y + alto - 13, rotulo)
    c.setFillColor(SOFT)
    c.setFont(MONO, 7.2)
    c.drawRightString(x + ancho - 9, y + alto - 13, fecha)

    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.line(x + 10, y + alto - 19, x + ancho - 9, y + alto - 19)

    d.bloque(c, x + 10, y + alto - 32, f"«{texto}»", ancho - 20,
             fuente=MONOI, tam=8.0, inter=11.0, justificado=False)


def nivel_sospecha(c, y):
    """Cinco casillas vacías para que la unidad marque durante la partida."""
    c.setFillColor(INK)
    c.setFont(MONOB, 8.6)
    c.drawString(MARGEN, y, "NIVEL DE SOSPECHA DE LA UNIDAD")
    c.setFillColor(SOFT)
    c.setFont(MONO, 7.6)
    c.drawString(MARGEN + 178, y, "(rellenar durante la investigación)")

    c.setStrokeColor(INK)
    c.setLineWidth(1.0)
    for i in range(5):
        c.rect(MARGEN + i * 26, y - 24, 20, 16, stroke=1, fill=0)
    c.setFillColor(SOFT)
    c.setFont(MONO, 6.6)
    c.drawString(MARGEN, y - 33, "BAJO")
    c.drawString(MARGEN + 108, y - 33, "ALTO")
    return y - 40


# ─── Páginas ─────────────────────────────────────────────────────────────────


def page_suspect(c, sujeto, indice, total, numero_pagina):
    d.fondo(c, PAPER, fibras=170, semilla=100 + indice)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}",
                     f"FICHA DE SUJETO {sujeto['num']} / {total:02d}")
    d.franja_identificacion(c, sujeto["alias"],
                            "PERSONA DE INTERÉS  ·  DOS TOMAS DE DECLARACIÓN",
                            sujeto["num"])

    tope = d.FRANJA_Y - 22
    lado = 200
    y_foto = tope - lado
    retrato(c, sujeto["alias"], MARGEN, y_foto, lado)

    # Caja de datos, a la derecha del retrato.
    x_datos = MARGEN + lado + 46
    ancho_datos = W - MARGEN - x_datos
    d.caja(c, x_datos, y_foto, ancho_datos, lado, relleno=DATA)

    y = tope - 18
    c.setFillColor(INK)
    c.setFont(MONOB, 9.2)
    c.drawString(x_datos + 12, y, "DATOS DEL SUJETO")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(x_datos + 12, y - 6, x_datos + ancho_datos - 12, y - 6)

    y -= 20
    ancho_valor = ancho_datos - 24 - 86
    y = d.par_dato(c, x_datos + 12, y, "ALIAS", sujeto["alias"], ancho_valor,
                   ancho_etiqueta=86)
    c.setFillColor(SOFT)
    c.setFont(MONOB, 9.2)
    c.drawString(x_datos + 12, y, "NOMBRE LEGAL")
    d.tachado(c, x_datos + 98, y - 2, ancho_valor - 12)
    y -= 12.6
    y = d.par_dato(c, x_datos + 12, y, "SUJETO N.º",
                   f"{sujeto['num']} de {total:02d}", ancho_valor,
                   ancho_etiqueta=86)
    y = d.par_dato(c, x_datos + 12, y, "VÍNCULO", sujeto["vinculo"], ancho_valor,
                   ancho_etiqueta=86)
    y = d.par_dato(c, x_datos + 12, y, "UNIDAD", sujeto["equipo"], ancho_valor,
                   ancho_etiqueta=86)
    y = d.par_dato(c, x_datos + 12, y, "PRESENTE", sujeto["presente"], ancho_valor,
                   ancho_etiqueta=86)
    c.setFillColor(RED)
    c.setFont(MONOB, 8.6)
    c.drawString(x_datos + 12, y - 2, "ESTADO:  BAJO INVESTIGACIÓN")

    # Perfil.
    y = seccion(c, y_foto - 20, "PERFIL DEL SUJETO")
    y = d.bloque(c, MARGEN, y, sujeto["perfil"], ANCHO_UTIL, tam=8.6, inter=12.2)

    # Las dos declaraciones, lado a lado.
    y = seccion(c, y - 8, "DECLARACIONES TOMADAS — COMPARAR AMBAS TOMAS")
    ancho_col = (ANCHO_UTIL - 14) / 2
    alto_col = max(
        d.alto_bloque(f"«{sujeto[k]}»", ancho_col - 20, MONOI, 8.0, 11.0)
        for k in ("decl1", "decl2")
    ) + 40
    tope_col = y + 6
    caja_declaracion(c, MARGEN, tope_col - alto_col, ancho_col, alto_col,
                     "DECLARACIÓN I", caso.FECHA_DECL_I.split(",")[0],
                     sujeto["decl1"])
    caja_declaracion(c, MARGEN + ancho_col + 14, tope_col - alto_col, ancho_col,
                     alto_col, "DECLARACIÓN II", caso.FECHA_DECL_II.split(",")[0],
                     sujeto["decl2"])
    y = tope_col - alto_col - 12

    # Observaciones.
    y = seccion(c, y, "OBSERVACIONES DEL INVESTIGADOR")
    y = d.bloque(c, MARGEN, y, sujeto["observa"], ANCHO_UTIL, tam=8.6, inter=12.2)

    nivel_sospecha(c, y - 12)
    d.pie(c, f"EXPEDIENTE {caso.CASO}  ·  SUJETO {sujeto['num']}  ·  "
             f"{sujeto['alias']}", f"FICHA {sujeto['num']}", numero_pagina)
    c.showPage()


def page_evidence_full(c, evidencia, indice, total, numero_pagina):
    """
    Evidencia a sangre: la pieza ocupa la hoja entera.

    Es el tratamiento de las piezas fotográficas y de los montajes en corcho.
    Enmarcadas quedarían tan reducidas que su propio texto dejaría de leerse,
    y entonces la evidencia ya no prueba nada.
    """
    ruta = os.path.join(DIR_EVIDENCIA, f"EV_{evidencia['letra']}.jpg")
    if os.path.exists(ruta):
        c.drawImage(ImageReader(ruta), 0, 0, W, d.H)
    else:
        d.fondo(c, PAPER2, fibras=120, semilla=400 + indice)

    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}",
                     f"EVIDENCIA {indice + 1} / {total}")

    # Franja de nota sobre la propia pieza, en oscuro para que se lea encima
    # de cualquier fondo.
    alto_nota = d.alto_bloque(evidencia["nota"], ANCHO_UTIL, MONO, 8.6, 12.2)
    alto_franja = alto_nota + 52
    c.setFillColor(d.HexColor("#1c1a17"))
    c.rect(0, 0, W, alto_franja, stroke=0, fill=1)
    c.setStrokeColor(RED)
    c.setLineWidth(2.2)
    c.line(0, alto_franja, W, alto_franja)

    c.setFillColor(d.HexColor("#c8a09a"))
    c.setFont(MONOB, 8.6)
    c.drawString(MARGEN, alto_franja - 20, "NOTA DEL ANALISTA")
    c.setFillColor(SOFT)
    c.setFont(MONO, 7.6)
    c.drawRightString(W - MARGEN, alto_franja - 20,
                      f"{evidencia['titulo']}  ·  EV. {evidencia['letra']}")
    d.bloque(c, MARGEN, alto_franja - 36, evidencia["nota"], ANCHO_UTIL,
             tam=8.6, inter=12.2, color=d.HexColor("#ddd6c5"))

    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawCentredString(W / 2, 8, str(numero_pagina))
    c.showPage()


def page_evidence(c, evidencia, indice, total, numero_pagina):
    d.fondo(c, PAPER, fibras=170, semilla=300 + indice)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}",
                     f"EVIDENCIA {indice + 1} / {total}")
    d.franja_identificacion(c, evidencia["letra"], "", "")

    # El título va junto a la letra grande, no debajo.
    c.setFillColor(INK)
    c.setFont(MONOB, 15)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 46, evidencia["titulo"])
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.2)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 30,
                 "PIEZA REGISTRADA  ·  CADENA DE CUSTODIA VERIFICADA")

    ruta = os.path.join(DIR_EVIDENCIA, f"EV_{evidencia['letra']}.jpg")
    alto_nota = d.alto_bloque(evidencia["nota"], ANCHO_UTIL, MONO, 8.6, 12.2)
    piso = 96 + alto_nota + 74  # nota + banda + anotaciones + pie

    if os.path.exists(ruta):
        lector = ImageReader(ruta)
        ancho_img, alto_img = lector.getSize()
        alto_max = d.FRANJA_Y - 16 - piso
        ancho_max = ANCHO_UTIL - 40
        escala = min(ancho_max / ancho_img, alto_max / alto_img)
        ancho_final, alto_final = ancho_img * escala, alto_img * escala
        x = (W - ancho_final) / 2
        y = d.FRANJA_Y - 16 - alto_final

        # Paspartú: el marco claro es lo que hace que la pieza se lea como
        # una copia montada y no como una imagen pegada en la hoja.
        c.setFillColor(d.HexColor("#b3a68a"))
        c.rect(x - 7, y - 7, ancho_final + 14, alto_final + 14, stroke=0, fill=1)
        c.drawImage(lector, x, y, ancho_final, alto_final)
    else:
        y = piso + 40
        c.setFillColor(PAPER2)
        c.rect(MARGEN + 60, y, ANCHO_UTIL - 120, d.FRANJA_Y - 16 - y,
               stroke=0, fill=1)
        c.setFillColor(SOFT)
        c.setFont(MONOB, 10)
        c.drawCentredString(W / 2, (y + d.FRANJA_Y - 16) / 2, "IMAGEN PENDIENTE")

    y = seccion(c, y - 22, "NOTA DEL ANALISTA")
    y = d.bloque(c, MARGEN, y, evidencia["nota"], ANCHO_UTIL, tam=8.6, inter=12.2)

    y = seccion(c, y - 10, "ANOTACIONES DE LA UNIDAD")
    d.renglones(c, MARGEN, y - 4, ANCHO_UTIL, cantidad=3, paso=16)

    d.pie(c, f"EXPEDIENTE {caso.CASO}  ·  EVIDENCIA {evidencia['letra']}",
          f"EV. {evidencia['letra']}", numero_pagina)
    c.showPage()


# ─── Ensamblado ──────────────────────────────────────────────────────────────


def construir_muestra(ruta):
    """Una ficha y dos evidencias, para validar la estética antes de producir."""
    d.registrar_fuentes()
    c = rl_canvas.Canvas(ruta, pagesize=d.PAGESIZE)
    c.setTitle(f"MUESTRA — EXPEDIENTE {caso.CASO}")

    page_suspect(c, caso.SUJETOS[0], 0, len(caso.SUJETOS), 1)
    por_letra = {e["letra"]: e for e in caso.EVIDENCIAS}
    for i, letra in enumerate(("E", "J")):
        page_evidence_full(c, por_letra[letra], i, len(caso.EVIDENCIAS), 2 + i)

    c.save()
    return ruta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--muestra", action="store_true",
                        help="genera solo las páginas de validación")
    parser.add_argument("-o", "--salida", default=None)
    args = parser.parse_args()

    if args.muestra:
        ruta = args.salida or os.path.join(BASE, "out", "MUESTRA_002.pdf")
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        print(f"  ✓  {construir_muestra(ruta)}")
        return

    raise SystemExit("El expediente completo todavía no está armado: "
                     "corré --muestra por ahora.")


if __name__ == "__main__":
    main()
