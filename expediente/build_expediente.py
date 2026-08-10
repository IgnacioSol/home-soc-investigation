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


def _puntos(n):
    return f"{n} pt" if n == 1 else f"{n} pts"


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
    d.pie(c, f"EXPEDIENTE {caso.CASO}", 
          f"FICHA {sujeto['num']}  ·  {sujeto['alias']}", numero_pagina)
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

    d.pie(c, f"EXPEDIENTE {caso.CASO}", f"EV. {evidencia['letra']}", numero_pagina)
    c.showPage()


def page_cover(c):
    d.fondo(c, d.KRAFT, fibras=240, semilla=1)

    # Banda superior con la pestaña de folder saliente a la derecha.
    c.setFillColor(d.HexColor("#bfae8d"))
    c.rect(0, d.H - 118, W, 118, stroke=0, fill=1)
    c.rect(W - 260, d.H - 152, 200, 40, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont(MONOB, 13)
    c.drawString(MARGEN, d.H - 44, caso.OFICINA)
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN, d.H - 62, caso.DIVISION)
    c.drawString(MARGEN, d.H - 78, caso.SESION)
    c.setFillColor(INK)
    c.setFont(MONOB, 10)
    c.drawRightString(W - 76, d.H - 138, "CASO ABIERTO")

    c.setStrokeColor(INK)
    c.setLineWidth(4)
    c.line(MARGEN, d.H - 178, W - MARGEN, d.H - 178)
    c.setLineWidth(1)
    c.line(MARGEN, d.H - 185, W - MARGEN, d.H - 185)

    c.setFillColor(SOFT)
    c.setFont(MONO, 9)
    c.drawString(MARGEN, d.H - 212, "EXPEDIENTE N.º")
    c.setFillColor(INK)
    c.setFont(MONOB, 46)
    c.drawString(MARGEN, d.H - 262, caso.CASO)
    c.setFillColor(SOFT)
    c.setFont(MONO, 10)
    c.drawString(MARGEN, d.H - 284, caso.TITULO)

    # Caja de datos del caso.
    datos = [
        ("CLASIFICACIÓN", "CONFIDENCIAL — NIVEL FAMILIA"),
        ("TIPO DE CASO", "Muerte dudosa. Homicidio confirmado por toxicología"),
        ("LUGAR", caso.LUGAR),
        ("FECHA DE LOS HECHOS", caso.FECHA_HECHOS),
        ("VENTANA CRÍTICA", caso.VENTANA),
        ("PERSONAS DE INTERÉS", f"{len(caso.SUJETOS)} (diez)"),
        ("EQUIPOS ASIGNADOS", "3 unidades investigadoras"),
        ("TIEMPO DE RESOLUCIÓN", "75 – 90 minutos"),
    ]
    alto_caja = 34 + len(datos) * 25
    y_caja = d.H - 320 - alto_caja
    d.caja(c, MARGEN, y_caja, ANCHO_UTIL, alto_caja, relleno=PAPER)
    y = y_caja + alto_caja - 28
    for etiqueta, valor in datos:
        c.setFillColor(SOFT)
        c.setFont(MONOB, 9)
        c.drawString(MARGEN + 18, y, etiqueta)
        c.setFillColor(INK)
        c.setFont(MONO, 9)
        c.drawString(MARGEN + 190, y, valor)
        y -= 25

    # Caja de registro de la unidad, para rellenar a mano.
    alto_reg = 128
    y_reg = y_caja - 20 - alto_reg
    d.caja(c, MARGEN, y_reg, ANCHO_UTIL, alto_reg, relleno=PAPER2)
    c.setFillColor(INK)
    c.setFont(MONOB, 10)
    c.drawString(MARGEN + 18, y_reg + alto_reg - 24, "ASIGNACIÓN DE LA UNIDAD")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(MARGEN + 18, y_reg + alto_reg - 32, W - MARGEN - 18,
           y_reg + alto_reg - 32)

    c.setFillColor(SOFT)
    c.setFont(MONO, 9)
    c.drawString(MARGEN + 18, y_reg + 76, "UNIDAD N.º")
    c.drawString(MARGEN + 240, y_reg + 76, "INVESTIGADORES:")
    c.drawString(MARGEN + 18, y_reg + 26, "HORA INICIO")
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(MARGEN + 100, y_reg + 72, MARGEN + 220, y_reg + 72)
    c.line(MARGEN + 370, y_reg + 72, W - MARGEN - 18, y_reg + 72)
    c.line(MARGEN + 240, y_reg + 48, W - MARGEN - 18, y_reg + 48)
    c.line(MARGEN + 110, y_reg + 22, MARGEN + 230, y_reg + 22)

    d.sello(c, W - 190, y_caja + 60, "CONFIDENCIAL", "NO DIVULGAR", angulo=-13)
    d.pie(c, f"EXPEDIENTE {caso.CASO}  ·  DOCUMENTO DE TRABAJO", "PORTADA")
    c.showPage()


def page_briefing(c):
    d.fondo(c, PAPER, fibras=170, semilla=2)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "INFORME PRELIMINAR")

    y = d.titular(c, d.H - 100, "RESUMEN DE LOS HECHOS")

    parrafos = [
        "Sábado por la noche. La familia se reúne en el condominio Teruma, en "
        "casa del Sujeto n.º 01, para la Noche de Primos de siempre. El occiso "
        "—74 años, abuelo de cinco de los diez presentes— llega caminando a las "
        "19:38, como hacía siempre.",

        "A las 22:40 se desploma delante de todos. Fallece a las 03:20 en el "
        "hospital. El certificado inicial consigna causa natural: era un hombre "
        "mayor con el corazón comprometido y nadie tuvo motivo para dudarlo. Se "
        "vela, se entierra y la familia sigue.",

        "Diez días después llega la toxicología. La concentración de su propia "
        "medicación cardíaca en sangre es del orden de ocho veces la "
        "terapéutica. Se abre el expediente y se vuelve a tomar declaración a "
        "las diez personas que estuvieron esa noche.",

        "El control de acceso del condominio no registra el ingreso de ninguna "
        "persona ajena. Las diez declaraciones de la primera toma se dieron "
        "cuando todos creían que había sido el corazón. Las de la segunda, "
        "sabiendo que fue un homicidio. Ahí está el caso.",
    ]
    for parrafo in parrafos:
        y = d.bloque(c, MARGEN, y, parrafo, ANCHO_UTIL, tam=9.0, inter=13.2) - 8

    # Línea de tiempo vertical: con siete nodos la horizontal no deja espacio
    # para las etiquetas y hay que abreviarlas hasta volverlas inútiles.
    y = seccion(c, y - 8, "LÍNEA DE TIEMPO ESTABLECIDA")
    y -= 4
    x_hora, x_texto = MARGEN + 10, MARGEN + 96
    for hora, evento, critico in caso.LINEA_TIEMPO:
        color = RED if critico else INK
        c.setFillColor(color)
        c.setFont(MONOB, 9.4)
        c.drawString(x_hora, y, hora)
        c.circle(x_hora + 62, y + 3, 3.4, stroke=0, fill=1)
        c.setFillColor(INK if not critico else RED)
        c.setFont(MONO if not critico else MONOB, 8.8)
        c.drawString(x_texto, y, evento)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(x_hora + 62, y - 10, x_hora + 62, y + 14)
        y -= 22

    y = seccion(c, y - 6, "PROTOCOLO DE LA UNIDAD")
    pasos = [
        "Leer las diez FICHAS DE SUJETO. Cada una trae dos declaraciones: la "
        "de la madrugada del sábado y la de diez días después.",
        "Comparar las dos tomas de cada sujeto. Casi todos cambian algo. Lo que "
        "importa no es quién cambió, sino en qué dirección.",
        "Analizar las diez EVIDENCIAS (A–J) y ubicarlas en la línea de tiempo.",
        "Completar la HOJA DE RESOLUCIÓN rellenando las burbujas.",
        "Entregar antes de que se agote el tiempo. La hora de entrega decide "
        "los empates que el desempate no resuelva.",
    ]
    for i, paso in enumerate(pasos, 1):
        c.setFillColor(RED)
        c.setFont(MONOB, 9.4)
        c.drawString(MARGEN, y, f"{i}.")
        y = d.bloque(c, MARGEN + 20, y, paso, ANCHO_UTIL - 20, tam=8.6,
                     inter=12.0) - 2

    c.setFillColor(SOFT)
    c.setFont(MONO, 9)
    c.drawString(MARGEN, 62, "COPIA N.º ____ DE 3")
    d.pie(c, f"EXPEDIENTE {caso.CASO}", "INFORME PRELIMINAR", 2)
    c.showPage()


def page_victim(c):
    d.fondo(c, PAPER, fibras=170, semilla=3)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "FICHA DE LA VÍCTIMA")
    d.franja_identificacion(c, caso.VICTIMA["nombre"], caso.VICTIMA["apodo"],
                            "†", color_numero=RED)

    tope = d.FRANJA_Y - 22
    lado = 200
    y_foto = tope - lado
    retrato(c, "VICTIMA", MARGEN, y_foto, lado)

    x_datos = MARGEN + lado + 46
    ancho_datos = W - MARGEN - x_datos
    d.caja(c, x_datos, y_foto, ancho_datos, lado, relleno=DATA)
    c.setFillColor(INK)
    c.setFont(MONOB, 9.2)
    c.drawString(x_datos + 12, tope - 18, "DATOS DEL OCCISO")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(x_datos + 12, tope - 24, x_datos + ancho_datos - 12, tope - 24)

    y = tope - 38
    ancho_valor = ancho_datos - 24 - 86
    for etiqueta, valor in (
        ("APODO", caso.VICTIMA["apodo"]),
        ("EDAD", caso.VICTIMA["edad"]),
        ("VÍNCULO", caso.VICTIMA["vinculo"]),
        ("HALLAZGO", "Colapso a las 22:40 · deceso 03:20"),
    ):
        y = d.par_dato(c, x_datos + 12, y, etiqueta, valor, ancho_valor,
                       ancho_etiqueta=86)
    c.setFillColor(SOFT)
    c.setFont(MONOB, 9.2)
    c.drawString(x_datos + 12, y, "NOMBRE LEGAL")
    d.tachado(c, x_datos + 98, y - 2, ancho_valor - 12)
    y -= 22
    c.setFillColor(RED)
    c.setFont(MONOB, 8.6)
    c.drawString(x_datos + 12, y, "CAUSA: HOMICIDIO")

    y = seccion(c, y_foto - 20, "QUIÉN ERA")
    y = d.bloque(c, MARGEN, y, caso.VICTIMA["perfil"], ANCHO_UTIL, tam=8.8,
                 inter=12.6)

    y = seccion(c, y - 10, "CAUSA DE LA MUERTE")
    y = d.bloque(c, MARGEN, y, caso.VICTIMA["causa"] + ". " +
                 caso.VICTIMA["hallazgo"], ANCHO_UTIL, tam=8.8, inter=12.6)

    y = seccion(c, y - 10, "POR QUÉ IMPORTA QUIÉN ERA")
    y = d.bloque(
        c, MARGEN, y,
        "Tres rasgos del occiso explican el caso. Apostaba, y eso lo dejó "
        "expuesto a quien quisiera aprovecharse. Arreglaba todo lo que sonaba "
        "raro, y por eso terminó abriendo algo que no debía. Y andaba todo el "
        "día en la calle hablando con medio barrio, así que se enteraba de "
        "cosas que no le correspondían. Una persona así acumula, sin querer, "
        "razones para que alguien prefiera que se calle.",
        ANCHO_UTIL, tam=8.8, inter=12.6)

    d.sello(c, W - 170, y - 52, "OCCISO", angulo=-11, tam=16)
    d.pie(c, f"EXPEDIENTE {caso.CASO}", "FICHA DEL OCCISO", 3)
    c.showPage()


def page_rules(c):
    d.fondo(c, PAPER, fibras=170, semilla=4)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "REGLAS Y PUNTUACIÓN")
    y = d.titular(c, d.H - 100, "CÓMO SE PUNTÚA",
                  "Leer antes de empezar. La unidad que no entienda el puntaje "
                  "juega en desventaja.")

    y = seccion(c, y - 4, "PUNTAJE BASE — 20 PUNTOS")
    y -= 2
    for pregunta in caso.PREGUNTAS:
        c.setFillColor(RED)
        c.setFont(MONOB, 9)
        c.drawString(MARGEN, y, pregunta["n"])
        c.setFillColor(INK)
        c.setFont(MONO, 8.8)
        c.drawString(MARGEN + 34, y, pregunta["texto"].capitalize())
        c.setFillColor(INK)
        c.setFont(MONOB, 9)
        c.drawRightString(W - MARGEN, y, _puntos(pregunta["puntos"]))
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.line(MARGEN, y - 6, W - MARGEN, y - 6)
        y -= 22

    y -= 6
    d.caja(c, MARGEN, y - 66, ANCHO_UTIL, 62, relleno=DATA)
    c.setFillColor(RED)
    c.rect(MARGEN, y - 66, 2.6, 62, stroke=0, fill=1)
    c.setFillColor(RED)
    c.setFont(MONOB, 9)
    c.drawString(MARGEN + 12, y - 22, "PENALIZACIÓN")
    d.bloque(c, MARGEN + 12, y - 38,
             "Acusar a una persona inocente en P1 o en P2 resta 2 puntos por "
             "cada error. El puntaje de una unidad nunca baja de cero: tirar al "
             "aire cuesta, pero no deja a nadie fuera del juego.",
             ANCHO_UTIL - 24, tam=8.4, inter=11.6)
    y -= 82

    y = seccion(c, y, "DESEMPATE — 3 PUNTOS QUE SOLO SE CUENTAN SI HAY EMPATE")
    y -= 2
    for bonus in caso.BONUS:
        c.setFillColor(RED)
        c.setFont(MONOB, 9)
        c.drawString(MARGEN, y, bonus["n"])
        c.setFillColor(INK)
        c.setFont(MONO, 8.8)
        c.drawString(MARGEN + 34, y, bonus["texto"].capitalize())
        c.setFillColor(INK)
        c.setFont(MONOB, 9)
        c.drawRightString(W - MARGEN, y, _puntos(bonus["puntos"]))
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.line(MARGEN, y - 6, W - MARGEN, y - 6)
        y -= 22

    y = seccion(c, y - 10, "CÓMO LEER LAS DOS DECLARACIONES")
    y = d.bloque(
        c, MARGEN, y,
        "Cada ficha trae la declaración de la madrugada del sábado y la de "
        "diez días después. Casi todos los sujetos cambian algo entre una y "
        "otra: así funciona la memoria y así funciona el miedo. Cambiar de "
        "versión no acusa a nadie por sí solo.",
        ANCHO_UTIL, tam=8.8, inter=12.6) - 8
    y = d.bloque(
        c, MARGEN, y,
        "Lo que la unidad tiene que preguntarse es hacia dónde cambió cada "
        "quien. Hay cambios que agregan verdad. Hay cambios que confiesan una "
        "vergüenza chiquita. Y hay cambios que no agregan nada excepto una "
        "coartada para otra persona. Esos tres no significan lo mismo.",
        ANCHO_UTIL, tam=8.8, inter=12.6)

    c.setFillColor(SOFT)
    c.setFont(MONO, 9)
    c.drawString(MARGEN, 62, "COPIA N.º ____ DE 3")
    d.pie(c, f"EXPEDIENTE {caso.CASO}", "REGLAS Y PUNTUACIÓN", 4)
    c.showPage()


def page_cross_statements(c, evidencia, indice, total, numero_pagina):
    """
    EVIDENCIA I — el acta de declaraciones cruzadas.

    Se compone nativa y no como imagen: es una tabla de diez filas con texto
    corrido, y reducida a una figura dejaría de leerse. Es además la pieza que
    más se relee durante la partida.
    """
    d.fondo(c, PAPER, fibras=170, semilla=310 + indice)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}",
                     f"EVIDENCIA {indice + 1} / {total}")
    d.franja_identificacion(c, evidencia["letra"], "", "")
    c.setFillColor(INK)
    c.setFont(MONOB, 15)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 46, evidencia["titulo"])
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.2)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 30,
                 f"TOMA I: {caso.FECHA_DECL_I}   ·   TOMA II: {caso.FECHA_DECL_II}")

    y = d.FRANJA_Y - 26
    y = d.bloque(c, MARGEN, y, evidencia["nota"], ANCHO_UTIL, tam=8.6,
                 inter=12.2) - 12

    # Cabecera de la tabla.
    x_sujeto, x_cambio = MARGEN + 8, MARGEN + 120
    c.setFillColor(d.HexColor("#3a362e"))
    c.rect(MARGEN, y - 20, ANCHO_UTIL, 20, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.setFont(MONOB, 8.6)
    c.drawString(x_sujeto, y - 14, "SUJETO")
    c.drawString(x_cambio, y - 14, "QUÉ CAMBIÓ ENTRE LA TOMA I Y LA TOMA II")
    y_tabla = y
    y -= 20

    ancho_cambio = W - MARGEN - x_cambio - 10
    for i, sujeto in enumerate(caso.SUJETOS):
        alto_fila = max(
            d.alto_bloque(sujeto["cambio"], ancho_cambio, MONO, 8.2, 11.4) + 12,
            30)
        c.setFillColor(PAPER2 if i % 2 else DATA)
        c.rect(MARGEN, y - alto_fila, ANCHO_UTIL, alto_fila, stroke=0, fill=1)

        c.setFillColor(INK)
        c.setFont(MONOB, 9)
        c.drawString(x_sujeto, y - 15, f"{sujeto['num']}  {sujeto['alias']}")
        d.bloque(c, x_cambio, y - 15, sujeto["cambio"], ancho_cambio,
                 tam=8.2, inter=11.4, justificado=False)

        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.line(MARGEN, y - alto_fila, W - MARGEN, y - alto_fila)
        y -= alto_fila

    c.setStrokeColor(d.HexColor("#6f6552"))
    c.setLineWidth(1.2)
    c.rect(MARGEN, y, ANCHO_UTIL, y_tabla - y, stroke=1, fill=0)

    y = seccion(c, y - 14, "ANOTACIONES DE LA UNIDAD")
    d.renglones(c, MARGEN, y - 4, ANCHO_UTIL, cantidad=3, paso=16)

    d.pie(c, f"EXPEDIENTE {caso.CASO}", f"EV. {evidencia['letra']}", numero_pagina)
    c.showPage()


def page_board(c, numero_pagina):
    """Tablero de corcho en blanco: la herramienta de trabajo de la unidad."""
    ruta = os.path.join(DIR_EVIDENCIA, "EV_TABLERO.jpg")
    if os.path.exists(ruta):
        c.drawImage(ImageReader(ruta), 0, 0, W, d.H)
    else:
        d.fondo(c, d.KRAFT, fibras=200, semilla=9)

    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "TABLERO DE LA UNIDAD")

    c.setFillColor(d.HexColor("#1c1a17"))
    c.rect(0, 0, W, 56, stroke=0, fill=1)
    c.setStrokeColor(RED)
    c.setLineWidth(2.2)
    c.line(0, 56, W, 56)
    c.setFillColor(d.HexColor("#c8a09a"))
    c.setFont(MONOB, 8.6)
    c.drawString(MARGEN, 36, "INSTRUCCIONES")
    c.setFillColor(d.HexColor("#ddd6c5"))
    c.setFont(MONO, 8.4)
    c.drawString(MARGEN, 20,
                 "Trazar con lápiz rojo las relaciones que la unidad establezca. "
                 "Este tablero no se califica.")
    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawRightString(W - MARGEN, 20, str(numero_pagina))
    c.showPage()


def _rejilla_caras(c, y_tope, alto_disponible):
    """
    Rejilla de las diez caras con dos burbujas bajo cada una.

    Una sola rejilla sirve para P1 y P2: la burbuja izquierda marca quién
    administró la sustancia y la derecha quién encubrió. Con dos rejillas
    separadas la hoja se iba a tres páginas y calificar dejaba de ser rápido.
    """
    columnas, filas = 5, 2
    ancho_celda = ANCHO_UTIL / columnas
    alto_celda = alto_disponible / filas
    lado_foto = min(ancho_celda - 14, alto_celda - 58)

    for i, sujeto in enumerate(caso.SUJETOS):
        fila, columna = divmod(i, columnas)
        cx = MARGEN + ancho_celda * (columna + 0.5)
        tope = y_tope - fila * alto_celda

        x_foto = cx - lado_foto / 2
        y_foto = tope - lado_foto - 4
        ruta = os.path.join(DIR_RETRATOS, f"{sujeto['alias'].replace('Í', 'I')}.jpg")
        if os.path.exists(ruta):
            c.drawImage(ImageReader(ruta), x_foto, y_foto, lado_foto, lado_foto)
        else:
            c.setFillColor(d.HexColor("#4a453d"))
            c.rect(x_foto, y_foto, lado_foto, lado_foto, stroke=0, fill=1)
            c.setFillColor(PAPER2)
            c.setFont(MONO, 6.4)
            c.drawCentredString(cx, y_foto + lado_foto / 2 - 2, "PENDIENTE")
        c.setStrokeColor(FRAME)
        c.setLineWidth(1.1)
        c.rect(x_foto, y_foto, lado_foto, lado_foto, stroke=1, fill=0)

        c.setFillColor(INK)
        c.setFont(MONOB, 8.6)
        c.drawCentredString(cx, y_foto - 13, sujeto["alias"])
        c.setFillColor(SOFT)
        c.setFont(MONO, 6.6)
        c.drawCentredString(cx, y_foto - 22, f"SUJETO {sujeto['num']}")

        # Dos burbujas: P1 a la izquierda, P2 a la derecha.
        for dx, etiqueta in ((-22, "1"), (22, "2")):
            d.burbuja(c, cx + dx, y_foto - 38, r=6.4)
            c.setFillColor(SOFT)
            c.setFont(MONOB, 6.4)
            c.drawCentredString(cx + dx, y_foto - 52, etiqueta)


def page_answers_1(c, numero_pagina):
    d.fondo(c, PAPER, fibras=150, semilla=5)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "HOJA DE RESOLUCIÓN  1 / 2")

    c.setFillColor(INK)
    c.setFont(MONOB, 20)
    c.drawString(MARGEN, d.H - 104, "HOJA DE RESOLUCIÓN")
    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawRightString(W - MARGEN, d.H - 100,
                      "RELLENAR LA BURBUJA COMPLETAMENTE  ·  NO USAR LÁPIZ")
    c.setStrokeColor(RED)
    c.setLineWidth(2.5)
    c.line(MARGEN, d.H - 113, MARGEN + 250, d.H - 113)

    d.caja(c, MARGEN, d.H - 174, ANCHO_UTIL, 48, relleno=PAPER2)
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN + 14, d.H - 148, "UNIDAD N.º")
    c.drawString(MARGEN + 190, d.H - 148, "INVESTIGADORES:")
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(MARGEN + 78, d.H - 152, MARGEN + 170, d.H - 152)
    c.line(MARGEN + 300, d.H - 152, W - MARGEN - 14, d.H - 152)

    y = d.banda_seccion(
        c, d.H - 200,
        "P1  ·  ¿QUIÉN ADMINISTRÓ LA SUSTANCIA?   |   "
        "P2  ·  ¿QUIÉN ENCUBRIÓ AL CULPABLE?")
    c.setFillColor(SOFT)
    c.setFont(MONO, 7.6)
    c.drawString(MARGEN, y - 4,
                 "Una sola marca en cada columna. Burbuja 1 = administró "
                 "(10 pts).   Burbuja 2 = encubrió (4 pts).")

    _rejilla_caras(c, y - 20, 400)

    c.setFillColor(SOFT)
    c.setFont(MONO, 7.8)
    c.drawString(MARGEN, 74,
                 "Marcar a una persona inocente en P1 o P2 resta 2 puntos. "
                 "El total nunca baja de cero.")
    d.pie(c, f"EXPEDIENTE {caso.CASO}", "RESPUESTAS 1/2", numero_pagina)
    c.showPage()


def page_answers_2(c, numero_pagina):
    d.fondo(c, PAPER, fibras=150, semilla=6)
    d.barra_superior(c, f"EXPEDIENTE {caso.CASO}", "HOJA DE RESOLUCIÓN  2 / 2")

    y = d.H - 96
    for pregunta in caso.PREGUNTAS:
        if pregunta["tipo"] != "opciones":
            continue
        y = d.banda_seccion(
            c, y - 18, f"{pregunta['n']}  ·  {pregunta['texto']}   "
                       f"({pregunta['ayuda']})")
        y -= 12
        for opcion in pregunta["opciones"]:
            d.burbuja(c, MARGEN + 8, y + 3, r=6)
            c.setFillColor(INK)
            c.setFont(MONO, 8.6)
            c.drawString(MARGEN + 24, y, opcion)
            y -= 22
        y -= 14

    # P5 — evidencias, fila única de burbujas.
    p5 = caso.PREGUNTAS[-1]
    y = d.banda_seccion(c, y - 18,
                        f"{p5['n']}  ·  {p5['texto']}   ({p5['ayuda']})")
    y -= 30
    paso = ANCHO_UTIL / len(caso.EVIDENCIAS)
    for i, evidencia in enumerate(caso.EVIDENCIAS):
        cx = MARGEN + paso * (i + 0.5)
        d.burbuja(c, cx, y, r=7)
        c.setFillColor(INK)
        c.setFont(MONOB, 9)
        c.drawCentredString(cx, y - 22, evidencia["letra"])
    y -= 44

    # Desempate.
    c.setFillColor(d.HexColor("#3a362e"))
    c.rect(MARGEN, y - 18, ANCHO_UTIL, 18, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.setFont(MONOB, 9.5)
    c.drawString(MARGEN + 8, y - 12.5,
                 "DESEMPATE  ·  SOLO SE CUENTA SI DOS UNIDADES QUEDAN IGUALES")
    y -= 30

    b1 = caso.BONUS[0]
    c.setFillColor(RED)
    c.setFont(MONOB, 8.8)
    c.drawString(MARGEN, y, b1["n"])
    c.setFillColor(INK)
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN + 28, y, b1["texto"])
    c.setFillColor(SOFT)
    c.setFont(MONOB, 8.2)
    c.drawRightString(W - MARGEN, y, _puntos(b1["puntos"]))
    y -= 20
    for opcion in b1["opciones"]:
        d.burbuja(c, MARGEN + 8, y + 3, r=6)
        c.setFillColor(INK)
        c.setFont(MONO, 8.6)
        c.drawString(MARGEN + 22, y, opcion)
        y -= 20

    y -= 8
    b2 = caso.BONUS[1]
    c.setFillColor(RED)
    c.setFont(MONOB, 8.8)
    c.drawString(MARGEN, y, b2["n"])
    c.setFillColor(INK)
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN + 28, y, b2["texto"])
    c.setFillColor(SOFT)
    c.setFont(MONOB, 8.2)
    c.drawRightString(W - MARGEN, y, _puntos(b2["puntos"]))
    y -= 26
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.4)
    c.drawString(MARGEN + 22, y, "₡")
    c.setStrokeColor(INK)
    c.setLineWidth(0.9)
    c.line(MARGEN + 36, y - 3, MARGEN + 300, y - 3)

    # Firma y hora.
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(MARGEN, 96, MARGEN + 240, 96)
    c.line(W - MARGEN - 200, 96, W - MARGEN, 96)
    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawString(MARGEN, 82, "FIRMA DEL INVESTIGADOR A CARGO")
    c.drawString(W - MARGEN - 200, 82, "HORA DE ENTREGA")

    d.pie(c, f"EXPEDIENTE {caso.CASO}", "RESPUESTAS 2/2", numero_pagina)
    c.showPage()


def page_solution(c, numero_pagina):
    d.fondo(c, d.HexColor("#2a2723"), fibras=90, semilla=7)
    c.setFillColor(RED)
    c.rect(0, d.BARRA_Y, W, d.BARRA_ALTO, stroke=0, fill=1)
    c.setFillColor(d.HexColor("#f6efe6"))
    c.setFont(MONOB, 10)
    c.drawString(MARGEN, d.BARRA_Y + 12, f"EXPEDIENTE {caso.CASO}")
    c.setFont(MONO, 8.6)
    c.drawRightString(W - MARGEN, d.BARRA_Y + 12.5, "SOLO ANFITRIÓN")

    c.setFillColor(d.HexColor("#f6efe6"))
    c.setFont(MONOB, 20)
    c.drawString(MARGEN, d.H - 104, "RESOLUCIÓN DEL CASO")
    c.setStrokeColor(RED_L := d.RED_L)
    c.setLineWidth(2.5)
    c.line(MARGEN, d.H - 113, MARGEN + 250, d.H - 113)
    c.setFillColor(RED_L)
    c.setFont(MONOB, 9)
    c.drawString(MARGEN, d.H - 132, "NO IMPRIMIR ESTA PÁGINA PARA LOS EQUIPOS")

    # Caja del culpable.
    y_caja = d.H - 232
    c.setFillColor(d.HexColor("#332f2a"))
    c.setStrokeColor(RED_L)
    c.setLineWidth(1.6)
    c.rect(MARGEN, y_caja, ANCHO_UTIL, 86, stroke=1, fill=1)
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 12)
    c.drawString(MARGEN + 16, y_caja + 62, f"CULPABLE:  {caso.SOLUCION['culpable']}")
    c.drawString(MARGEN + 16, y_caja + 42,
                 f"ENCUBRIÓ:  {caso.SOLUCION['complice']}")
    c.setFillColor(d.HexColor("#c9c1b1"))
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN + 16, y_caja + 20, caso.SOLUCION["gancho"])

    y = y_caja - 22
    for titulo, texto in caso.SOLUCION["bloques"]:
        c.setFillColor(RED_L)
        c.setFont(MONOB, 8.8)
        c.drawString(MARGEN, y, titulo)
        y = d.bloque(c, MARGEN, y - 14, texto, ANCHO_UTIL, tam=8.2, inter=11.4,
                     color=d.HexColor("#ddd6c5")) - 8

    # Clave de calificación.
    alto_clave = 34 + (len(caso.PREGUNTAS) + len(caso.BONUS) + 3) * 14
    y_clave = y - alto_clave
    c.setFillColor(d.HexColor("#332f2a"))
    c.setStrokeColor(d.HexColor("#5a5349"))
    c.setLineWidth(1)
    c.rect(MARGEN, y_clave, ANCHO_UTIL, alto_clave, stroke=1, fill=1)

    yy = y_clave + alto_clave - 18
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 9)
    c.drawString(MARGEN + 12, yy, "CLAVE DE CALIFICACIÓN")
    yy -= 16
    for pregunta in caso.PREGUNTAS:
        c.setFillColor(d.HexColor("#9c9484"))
        c.setFont(MONOB, 7.8)
        c.drawString(MARGEN + 12, yy, pregunta["n"])
        c.setFillColor(d.HexColor("#ddd6c5"))
        c.setFont(MONO, 7.8)
        c.drawString(MARGEN + 44, yy, pregunta["respuesta"])
        c.setFillColor(d.HexColor("#f0a898"))
        c.setFont(MONOB, 7.8)
        c.drawRightString(W - MARGEN - 12, yy, _puntos(pregunta["puntos"]))
        yy -= 14
    c.setStrokeColor(d.HexColor("#5a5349"))
    c.setLineWidth(0.5)
    c.line(MARGEN + 12, yy + 4, W - MARGEN - 12, yy + 4)
    yy -= 10
    for bonus in caso.BONUS:
        c.setFillColor(d.HexColor("#9c9484"))
        c.setFont(MONOB, 7.8)
        c.drawString(MARGEN + 12, yy, bonus["n"])
        c.setFillColor(d.HexColor("#ddd6c5"))
        c.setFont(MONO, 7.8)
        c.drawString(MARGEN + 44, yy, bonus["respuesta"])
        c.setFillColor(d.HexColor("#f0a898"))
        c.setFont(MONOB, 7.8)
        c.drawRightString(W - MARGEN - 12, yy, _puntos(bonus["puntos"]))
        yy -= 14
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 8.4)
    c.drawRightString(W - MARGEN - 12, yy - 2,
                      f"TOTAL: {caso.PUNTAJE_BASE} PUNTOS  "
                      f"(+{caso.PUNTAJE_BONUS} de desempate)")

    c.setFillColor(d.HexColor("#8a8274"))
    c.setFont(MONO, 7.4)
    c.drawString(MARGEN + 12, yy - 20,
                 "Si el desempate tampoco resuelve: gana la unidad que entregó "
                 "primero.")
    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawCentredString(W / 2, 30, str(numero_pagina))
    c.showPage()


# ─── Ensamblado ──────────────────────────────────────────────────────────────


# 4 preliminares + 10 fichas + 10 evidencias + tablero + 2 respuestas + solución
PAGINAS_ESPERADAS = 4 + len(caso.SUJETOS) + len(caso.EVIDENCIAS) + 1 + 2 + 1


def construir(ruta):
    """Compone el expediente completo y verifica el número de páginas."""
    d.registrar_fuentes()
    c = rl_canvas.Canvas(ruta, pagesize=d.PAGESIZE)
    c.setTitle(f"EXPEDIENTE {caso.CASO}")
    c.setAuthor(caso.OFICINA)
    c.setSubject(caso.TITULO)

    page_cover(c)
    page_briefing(c)
    page_victim(c)
    page_rules(c)

    pagina = 5
    for i, sujeto in enumerate(caso.SUJETOS):
        page_suspect(c, sujeto, i, len(caso.SUJETOS), pagina)
        pagina += 1

    for i, evidencia in enumerate(caso.EVIDENCIAS):
        modo = evidencia.get("modo", "marco")
        if modo == "sangre":
            page_evidence_full(c, evidencia, i, len(caso.EVIDENCIAS), pagina)
        elif modo == "nativa":
            page_cross_statements(c, evidencia, i, len(caso.EVIDENCIAS), pagina)
        else:
            page_evidence(c, evidencia, i, len(caso.EVIDENCIAS), pagina)
        pagina += 1

    page_board(c, pagina)
    page_answers_1(c, pagina + 1)
    page_answers_2(c, pagina + 2)
    page_solution(c, pagina + 3)

    c.save()

    if c.getPageNumber() - 1 != PAGINAS_ESPERADAS:
        raise SystemExit(
            f"El expediente salió con {c.getPageNumber() - 1} páginas y se "
            f"esperaban {PAGINAS_ESPERADAS}."
        )
    return ruta


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

    ruta = args.salida or os.path.join(BASE, "out", "EXPEDIENTE_002.pdf")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    construir(ruta)
    print(f"  ✓  {ruta}   {PAGINAS_ESPERADAS} páginas")


if __name__ == "__main__":
    main()
