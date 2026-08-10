#!/usr/bin/env python3
"""
Compone el EXPEDIENTE 000 — DEMOSTRACIÓN.

    python3 build_demo.py

Expediente de práctica para enseñar la mecánica antes de jugar el caso real.
Caso genérico, cuatro sujetos, tres evidencias y once páginas. No usa ninguna
fotografía ni ninguna imagen generada: todo se compone en texto, así se
imprime barato y se explica en quince minutos.

Comparte el sistema de diseño con el expediente grande (design.py) y reutiliza
sus bloques de página, pero sus datos viven acá arriba y no en caso.py.
"""

import argparse
import os

from reportlab.pdfgen import canvas as rl_canvas

import design as d
from build_expediente import caja_declaracion, nivel_sospecha, seccion
from design import (ANCHO_UTIL, DATA, FRAME, INK, MARGEN, MONO, MONOB, PAPER,
                    PAPER2, RED, RULE, SOFT, W)

BASE = os.path.dirname(os.path.abspath(__file__))

# ─── El caso ─────────────────────────────────────────────────────────────────

CASO = "000–DEMOSTRACIÓN"
TITULO = "DESAPARICIÓN PARCIAL DE UN POSTRE"
OFICINA = "OFICINA DE INVESTIGACIÓN FAMILIAR"
DIVISION = "DIVISIÓN DE ASUNTOS DOMÉSTICOS  ·  CASO DE PRÁCTICA"
LUGAR = "Cocina de la casa"
FECHA_DECL_I = "esa misma noche"
FECHA_DECL_II = "tres días después"
VENTANA = "19:30 — 19:50"

LINEA_TIEMPO = [
    ("18:00", "El queque queda servido en la cocina, entero", False),
    ("19:12", "Alguien entra a la cocina y sale a los dos minutos", False),
    ("19:34", "Alguien entra a la cocina y no sale hasta las 19:50", True),
    ("20:00", "Se descubre que falta un tercio del queque", True),
]

SUJETOS = [
    {
        "num": "01",
        "alias": "ANA",
        "rol": "TESTIGO",
        "vinculo": "Estuvo en el patio casi toda la noche",
        "perfil": "Se pasó la noche afuera conversando. Desde el patio se ve la "
                  "puerta de la cocina, aunque no lo que pasa adentro.",
        "decl1": "Yo estaba en el patio. No vi nada raro.",
        "decl2": "Estaba en el patio. Ahora que lo pienso, sí vi salir a "
                 "alguien de la cocina con un plato, como a las nueve menos "
                 "diez. No le vi la cara. No lo dije antes porque no quería "
                 "acusar a nadie sin estar segura.",
        "cambio": "Agrega un dato nuevo que no la beneficia en nada.",
        "observa": "Su segunda declaración aporta información que antes se "
                   "guardó. Nada de lo que agregó mejora su propia situación.",
    },
    {
        "num": "02",
        "alias": "BRUNO",
        "rol": "CULPABLE",
        "vinculo": "Dice haber estado en la sala toda la noche",
        "perfil": "Tranquilo, poco hablador. Nadie lo tuvo en cuenta en ningún "
                  "momento de la investigación.",
        "decl1": "Estuve en la sala con Carla desde las siete. No me levanté "
                 "para nada en toda la noche.",
        "decl2": "Estuve en la sala con Carla desde las siete. No me levanté "
                 "para nada en toda la noche.",
        "cambio": "Sin variación. Texto idéntico en ambas tomas.",
        "observa": "Único sujeto cuyas dos declaraciones coinciden palabra por "
                   "palabra, con tres días de diferencia. Se le pidió "
                   "repetirla con sus propias palabras y dijo exactamente lo "
                   "mismo.",
    },
    {
        "num": "03",
        "alias": "CARLA",
        "rol": "CÓMPLICE",
        "vinculo": "Estuvo en la sala",
        "perfil": "Atenta a todo lo que pasa en la casa. Es de las que se dan "
                  "cuenta de las cosas antes que el resto.",
        "decl1": "Yo estaba en la sala. Bruno andaba por ahí también, pero la "
                 "verdad no sabría decir si se levantó en algún momento.",
        "decl2": "Yo estaba en la sala. Bruno estuvo conmigo todo el rato, "
                 "desde las siete hasta que se descubrió lo del queque. No se "
                 "levantó ni una vez. De eso estoy segura.",
        "cambio": "Convierte un «no sabría decir» en una coartada cerrada para "
                  "otra persona.",
        "observa": "Es el único cambio del expediente que beneficia a alguien "
                   "distinto de quien declara. Contradice a la EVIDENCIA A.",
    },
    {
        "num": "04",
        "alias": "DIEGO",
        "rol": "PISTA FALSA",
        "vinculo": "Entró a la cocina esa noche",
        "perfil": "Muy goloso, y toda la familia lo sabe. Es el primero al que "
                  "todo el mundo va a mirar.",
        "decl1": "Yo no entré a la cocina en toda la noche.",
        "decl2": "Mentí. Sí entré, como a las siete y cuarto, pero solo fui a "
                 "servirme agua. Salí de una. No dije nada porque sabía que me "
                 "iban a echar la culpa a mí.",
        "cambio": "Confiesa algo que lo deja peor parado que su versión "
                  "anterior.",
        "observa": "Su entrada a la cocina está registrada y duró dos minutos, "
                   "fuera de la ventana crítica.",
    },
]

EVIDENCIAS = [
    {
        "letra": "A",
        "titulo": "CONTROL DE LA COCINA",
        "tipo": "tabla",
        "nota": "La tía anotó las entradas a la cocina porque estaba pendiente "
                "del horno. Registró la hora de entrada y la de salida, sin "
                "anotar quién era cada quien.",
        "columnas": ["ENTRADA", "SALIDA", "DURACIÓN", "OBSERVACIÓN"],
        "filas": [
            ["19:12", "19:14", "2 min", "—"],
            ["19:34", "19:50", "16 min", "coincide con la ventana"],
            ["20:02", "20:05", "3 min", "posterior al hallazgo"],
        ],
        "destacar": [1],
        "cierre": "Nadie más entró a la cocina entre las 18:00 y las 20:00.",
    },
    {
        "letra": "B",
        "titulo": "INFORME DEL POSTRE",
        "tipo": "parrafos",
        "nota": "Estado en que se encontró el queque y qué se puede deducir de "
                "cómo fue cortado.",
        "parrafos": [
            "Falta aproximadamente un tercio. No fue arrancado con la mano: "
            "el corte es limpio y se hizo con el cuchillo de sierra.",
            "El cuchillo apareció lavado y guardado en su gaveta. El plato "
            "usado también: lavado, secado y puesto en su lugar, boca abajo, "
            "como se acomodan en esta casa.",
            "Quien se lo comió se tomó el tiempo de ordenar. Eso descarta a "
            "cualquiera que haya estado en la cocina solo un par de minutos.",
        ],
        "cierre": "Comer, lavar, secar y guardar toma bastante más de dos "
                  "minutos.",
    },
    {
        "letra": "C",
        "titulo": "ACTA DE DECLARACIONES CRUZADAS",
        "tipo": "cruzada",
        "nota": "Comparación de las dos tomas de declaración de los cuatro "
                "sujetos. La oficina no interpreta: solo consigna qué cambió.",
    },
]

PREGUNTAS = [
    {"n": "P1", "texto": "¿QUIÉN SE COMIÓ EL QUEQUE?", "puntos": 6,
     "tipo": "rejilla", "respuesta": "BRUNO — Sujeto 02"},
    {"n": "P2", "texto": "¿QUIÉN LO ENCUBRIÓ?", "puntos": 2,
     "tipo": "rejilla", "respuesta": "CARLA — Sujeto 03"},
    {"n": "P3", "texto": "¿EN QUÉ VENTANA OCURRIÓ?", "puntos": 1,
     "tipo": "opciones", "correcta": 2,
     "opciones": ["18:00 – 18:30", "19:10 – 19:15", "19:30 – 19:50",
                  "20:00 – 20:15"],
     "respuesta": "19:30 – 19:50"},
    {"n": "P4", "texto": "¿QUÉ EVIDENCIA DESCARTA A DIEGO?", "puntos": 1,
     "tipo": "opciones", "correcta": 1,
     "opciones": ["La A, por la hora de entrada",
                  "La A y la B juntas: entró 2 minutos y no daba tiempo",
                  "La C, porque cambió su declaración",
                  "Ninguna: Diego sigue siendo sospechoso"],
     "respuesta": "La A y la B juntas: entró 2 minutos y no daba tiempo"},
]

BONUS = {
    "n": "B1", "texto": "¿QUÉ TIENE DE RARO LA DECLARACIÓN DEL CULPABLE?",
    "puntos": 2, "correcta": 2,
    "opciones": ["Que se contradice con la de Carla",
                 "Que cambió por completo entre una toma y otra",
                 "Que es idéntica palabra por palabra en ambas tomas",
                 "Que se negó a declarar la segunda vez"],
    "respuesta": "Es idéntica palabra por palabra: está memorizada",
}

PUNTAJE_BASE = sum(p["puntos"] for p in PREGUNTAS)  # 10

LECCION = [
    ("Agrega algo que no lo beneficia",
     "Testigo honesto que no quería meterse", "ANA"),
    ("Confiesa una vergüenza chiquita",
     "Inocente con un secreto tonto", "DIEGO"),
    ("Agrega una coartada para OTRA persona",
     "Está encubriendo", "CARLA"),
    ("No cambia ni una sola palabra",
     "La tiene memorizada", "BRUNO"),
]

SOLUCION = [
    ("QUÉ PASÓ",
     "Bruno entró a la cocina a las 19:34 y se comió un tercio del queque. Se "
     "tomó dieciséis minutos porque después lavó el cuchillo, lavó el plato y "
     "lo guardó boca abajo, como van en esa casa. Salió a las 19:50 con el "
     "plato en la mano, y Ana lo vio salir desde el patio sin reconocerlo."),
    ("QUIÉN LO ENCUBRIÓ",
     "Carla. En la primera declaración dijo que no sabría decir si Bruno se "
     "había levantado. En la segunda, ya sabiendo que alguien estuvo dieciséis "
     "minutos en la cocina, lo puso sentado a su lado toda la noche. Nadie le "
     "preguntó eso: lo agregó ella."),
    ("POR QUÉ DIEGO NO FUE",
     "Porque entró a las 19:12 y salió a las 19:14. Dos minutos no alcanzan "
     "para cortar, comer, lavar el cuchillo, lavar el plato y guardarlo. Diego "
     "mintió, pero mintió por miedo a que le echaran la culpa — que es "
     "exactamente lo que la mesa iba a hacer."),
    ("LA LECCIÓN DEL CASO",
     "Tres de los cuatro cambiaron su declaración y solo uno de esos tres es "
     "culpable de algo. Cambiar de versión no acusa a nadie: lo que acusa es "
     "hacia dónde cambia. Y la declaración idéntica palabra por palabra, que "
     "parece la más sólida de todas, es la única imposible."),
]


# ─── Bloques propios de la demo ──────────────────────────────────────────────


def sin_foto(c, x, y, lado):
    """
    Recuadro de retrato ausente.

    La demo no lleva fotografías a propósito: se juega con gente que todavía no
    conoce la mecánica y la idea es que miren las declaraciones, no las caras.
    """
    c.setFillColor(d.HexColor("#4a453d"))
    c.rect(x, y, lado, lado, stroke=0, fill=1)
    c.setStrokeColor(FRAME)
    c.setLineWidth(2.2)
    c.rect(x, y, lado, lado, stroke=1, fill=0)
    c.setLineWidth(0.7)
    c.rect(x - 4, y - 4, lado + 8, lado + 8, stroke=1, fill=0)

    # Silueta simple, dibujada con dos formas.
    c.setFillColor(d.HexColor("#2b2822"))
    cx = x + lado / 2
    c.circle(cx, y + lado * 0.62, lado * 0.145, stroke=0, fill=1)
    c.ellipse(cx - lado * 0.27, y + lado * 0.10, cx + lado * 0.27,
              y + lado * 0.52, stroke=0, fill=1)

    c.setFillColor(d.HexColor("#8e8676"))
    c.setFont(MONO, 7.2)
    c.drawCentredString(cx, y + 10, "CASO DE PRÁCTICA")


def tabla(c, y, columnas, filas, destacar=(), alto_fila=20):
    """Tabla con cabecera oscura. Devuelve la y siguiente."""
    anchos = [ANCHO_UTIL * p for p in (0.16, 0.16, 0.18, 0.50)][:len(columnas)]

    c.setFillColor(d.HexColor("#3a362e"))
    c.rect(MARGEN, y - alto_fila, ANCHO_UTIL, alto_fila, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.setFont(MONOB, 8.2)
    x = MARGEN
    for titulo, ancho_col in zip(columnas, anchos):
        c.drawString(x + 8, y - alto_fila + 6.5, titulo)
        x += ancho_col
    y -= alto_fila

    for i, fila in enumerate(filas):
        resaltada = i in destacar
        c.setFillColor(d.HexColor("#e8cdc5") if resaltada
                       else (PAPER2 if i % 2 else DATA))
        c.rect(MARGEN, y - alto_fila, ANCHO_UTIL, alto_fila, stroke=0, fill=1)
        c.setFillColor(RED if resaltada else INK)
        c.setFont(MONOB if resaltada else MONO, 8.4)
        x = MARGEN
        for valor, ancho_col in zip(fila, anchos):
            c.drawString(x + 8, y - alto_fila + 6.5, str(valor))
            x += ancho_col
        y -= alto_fila

    c.setStrokeColor(d.HexColor("#6f6552"))
    c.setLineWidth(1)
    c.rect(MARGEN, y, ANCHO_UTIL, alto_fila * (len(filas) + 1), stroke=1, fill=0)
    return y


def cierre(c, y, texto):
    """Caja de conclusión con filete rojo."""
    alto = d.alto_bloque(texto, ANCHO_UTIL - 24, MONO, 8.6, 12.2) + 22
    d.caja(c, MARGEN, y - alto, ANCHO_UTIL, alto, relleno=DATA)
    c.setFillColor(RED)
    c.rect(MARGEN, y - alto, 2.6, alto, stroke=0, fill=1)
    d.bloque(c, MARGEN + 14, y - 18, texto, ANCHO_UTIL - 24, tam=8.6, inter=12.2)
    return y - alto - 12


# ─── Páginas ─────────────────────────────────────────────────────────────────


def page_cover(c):
    d.fondo(c, d.KRAFT, fibras=240, semilla=1)
    c.setFillColor(d.HexColor("#bfae8d"))
    c.rect(0, d.H - 118, W, 118, stroke=0, fill=1)
    c.rect(W - 260, d.H - 152, 200, 40, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont(MONOB, 13)
    c.drawString(MARGEN, d.H - 44, OFICINA)
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN, d.H - 62, DIVISION)
    c.setFillColor(INK)
    c.setFont(MONOB, 10)
    c.drawRightString(W - 76, d.H - 138, "PARA APRENDER")

    c.setStrokeColor(INK)
    c.setLineWidth(4)
    c.line(MARGEN, d.H - 178, W - MARGEN, d.H - 178)
    c.setLineWidth(1)
    c.line(MARGEN, d.H - 185, W - MARGEN, d.H - 185)

    c.setFillColor(SOFT)
    c.setFont(MONO, 9)
    c.drawString(MARGEN, d.H - 212, "EXPEDIENTE N.º")
    c.setFillColor(INK)
    c.setFont(MONOB, 42)
    c.drawString(MARGEN, d.H - 258, CASO)
    c.setFillColor(SOFT)
    c.setFont(MONO, 10)
    c.drawString(MARGEN, d.H - 280, TITULO)

    datos = [
        ("QUÉ ES ESTO", "Un caso de práctica para aprender a jugar"),
        ("SOSPECHOSOS", "4 (cuatro)"),
        ("EVIDENCIAS", "3 (tres)"),
        ("PUNTAJE", f"{PUNTAJE_BASE} puntos + 2 de desempate"),
        ("DURACIÓN", "15 minutos"),
        ("SE JUEGA", "Todos juntos, en voz alta"),
    ]
    alto_caja = 34 + len(datos) * 25
    y_caja = d.H - 316 - alto_caja
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

    alto_nota = 96
    y_nota = y_caja - 20 - alto_nota
    d.caja(c, MARGEN, y_nota, ANCHO_UTIL, alto_nota, relleno=PAPER2)
    c.setFillColor(INK)
    c.setFont(MONOB, 10)
    c.drawString(MARGEN + 18, y_nota + alto_nota - 24, "ANTES DE EMPEZAR")
    d.bloque(c, MARGEN + 18, y_nota + alto_nota - 44,
             "Este caso es inventado y no tiene nada que ver con nadie. Sirve "
             "para una sola cosa: entender cómo se lee un expediente antes de "
             "jugar el de verdad. Se resuelve entre todos, sin equipos y sin "
             "apuro.", ANCHO_UTIL - 36, tam=8.6, inter=12.2)

    d.sello(c, W - 180, y_caja + 54, "PRÁCTICA", angulo=-13, tam=17)
    d.pie(c, f"EXPEDIENTE {CASO}", "PORTADA")
    c.showPage()


def page_como_se_juega(c):
    d.fondo(c, PAPER, fibras=170, semilla=2)
    d.barra_superior(c, f"EXPEDIENTE {CASO}", "CÓMO SE JUEGA")
    y = d.titular(c, d.H - 100, "LA REGLA DE ORO",
                  "Si entienden esta página, ya saben jugar.")

    y = d.bloque(
        c, MARGEN, y,
        "Cada sospechoso declaró dos veces: una la noche de los hechos y otra "
        "unos días después. El expediente trae las dos, lado a lado. Casi "
        "todos cambian algo entre una y otra, porque así funciona la memoria "
        "y así funciona el miedo a quedar mal.",
        ANCHO_UTIL, tam=9.0, inter=13.2) - 10
    y = d.bloque(
        c, MARGEN, y,
        "Por eso la pregunta no es quién cambió su versión. La pregunta es "
        "HACIA DÓNDE cambió. Eso es todo el juego:",
        ANCHO_UTIL, tam=9.0, inter=13.2) - 6

    # La tabla que enseña el mecanismo.
    y = seccion(c, y, "LOS CUATRO TIPOS DE CAMBIO")
    y += 4
    ancho_a, ancho_b = ANCHO_UTIL * 0.42, ANCHO_UTIL * 0.38
    for i, (cambio, significa, quien) in enumerate(LECCION):
        alto_fila = 30
        c.setFillColor(PAPER2 if i % 2 else DATA)
        c.rect(MARGEN, y - alto_fila, ANCHO_UTIL, alto_fila, stroke=0, fill=1)
        culpa = quien in ("CARLA", "BRUNO")
        c.setFillColor(RED if culpa else INK)
        c.setFont(MONOB if culpa else MONO, 8.6)
        c.drawString(MARGEN + 10, y - 19, cambio)
        c.setFillColor(SOFT)
        c.setFont(MONO, 8.4)
        c.drawString(MARGEN + 10 + ancho_a, y - 19, significa)
        c.setFillColor(RED if culpa else SOFT)
        c.setFont(MONOB, 8.6)
        c.drawRightString(W - MARGEN - 10, y - 19, quien)
        y -= alto_fila
    c.setStrokeColor(d.HexColor("#6f6552"))
    c.setLineWidth(1)
    c.rect(MARGEN, y, ANCHO_UTIL, 30 * len(LECCION), stroke=1, fill=0)

    y = cierre(c, y - 14,
               "Las dos filas en rojo son las que importan. Nadie agrega una "
               "coartada para otra persona sin razón, y nadie repite una frase "
               "palabra por palabra tres días después salvo que la haya "
               "ensayado.")

    y = seccion(c, y, "EL ORDEN PARA LEER")
    for i, paso in enumerate([
        "Leer las cuatro fichas y comparar las dos declaraciones de cada uno.",
        "Leer las tres evidencias y ubicarlas en la hora en que pasaron.",
        "Marcar la hoja de respuestas rellenando las burbujas.",
        "Voltear a la última página y ver si le atinaron.",
    ], 1):
        c.setFillColor(RED)
        c.setFont(MONOB, 9.4)
        c.drawString(MARGEN, y, f"{i}.")
        y = d.bloque(c, MARGEN + 20, y, paso, ANCHO_UTIL - 20, tam=8.8,
                     inter=12.4) - 4

    y = seccion(c, y - 6, "CÓMO SE PUNTÚA")
    for pregunta in PREGUNTAS:
        c.setFillColor(RED)
        c.setFont(MONOB, 9)
        c.drawString(MARGEN, y, pregunta["n"])
        c.setFillColor(INK)
        c.setFont(MONO, 8.8)
        c.drawString(MARGEN + 34, y, pregunta["texto"])
        c.setFillColor(INK)
        c.setFont(MONOB, 9)
        c.drawRightString(W - MARGEN, y,
                          f"{pregunta['puntos']} "
                          f"{'pt' if pregunta['puntos'] == 1 else 'pts'}")
        y -= 18
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.2)
    c.drawString(MARGEN, y - 4,
                 "Acusar a un inocente en P1 o P2 resta 2 puntos. El total "
                 "nunca baja de cero.")

    d.pie(c, f"EXPEDIENTE {CASO}", "CÓMO SE JUEGA", 2)
    c.showPage()


def page_suspect(c, sujeto, indice, numero_pagina):
    d.fondo(c, PAPER, fibras=170, semilla=100 + indice)
    d.barra_superior(c, f"EXPEDIENTE {CASO}",
                     f"FICHA DE SUJETO {sujeto['num']} / {len(SUJETOS):02d}")
    d.franja_identificacion(c, sujeto["alias"],
                            "PERSONA DE INTERÉS  ·  DOS TOMAS DE DECLARACIÓN",
                            sujeto["num"])

    tope = d.FRANJA_Y - 26
    lado = 176
    y_foto = tope - lado
    sin_foto(c, MARGEN, y_foto, lado)

    x_datos = MARGEN + lado + 30
    ancho_datos = W - MARGEN - x_datos
    d.caja(c, x_datos, y_foto, ancho_datos, lado, relleno=DATA)
    c.setFillColor(INK)
    c.setFont(MONOB, 9.2)
    c.drawString(x_datos + 12, tope - 18, "DATOS DEL SUJETO")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(x_datos + 12, tope - 24, x_datos + ancho_datos - 12, tope - 24)

    y = tope - 40
    ancho_valor = ancho_datos - 24 - 86
    y = d.par_dato(c, x_datos + 12, y, "ALIAS", sujeto["alias"], ancho_valor,
                   ancho_etiqueta=86)
    y = d.par_dato(c, x_datos + 12, y, "SUJETO N.º",
                   f"{sujeto['num']} de {len(SUJETOS):02d}", ancho_valor,
                   ancho_etiqueta=86)
    y = d.par_dato(c, x_datos + 12, y, "UBICACIÓN", sujeto["vinculo"],
                   ancho_valor, ancho_etiqueta=86)
    c.setFillColor(RED)
    c.setFont(MONOB, 8.6)
    c.drawString(x_datos + 12, y - 4, "ESTADO:  BAJO INVESTIGACIÓN")

    y = seccion(c, y_foto - 22, "PERFIL DEL SUJETO")
    y = d.bloque(c, MARGEN, y, sujeto["perfil"], ANCHO_UTIL, tam=8.8,
                 inter=12.6)

    y = seccion(c, y - 10, "DECLARACIONES TOMADAS — COMPARAR AMBAS TOMAS")
    ancho_col = (ANCHO_UTIL - 14) / 2
    alto_col = max(
        d.alto_bloque(f"«{sujeto[k]}»", ancho_col - 20, d.MONOI, 8.0, 11.0)
        for k in ("decl1", "decl2")
    ) + 40
    tope_col = y + 6
    caja_declaracion(c, MARGEN, tope_col - alto_col, ancho_col, alto_col,
                     "DECLARACIÓN I", FECHA_DECL_I, sujeto["decl1"])
    caja_declaracion(c, MARGEN + ancho_col + 14, tope_col - alto_col, ancho_col,
                     alto_col, "DECLARACIÓN II", FECHA_DECL_II, sujeto["decl2"])
    y = tope_col - alto_col - 14

    y = seccion(c, y, "OBSERVACIONES DEL INVESTIGADOR")
    y = d.bloque(c, MARGEN, y, sujeto["observa"], ANCHO_UTIL, tam=8.8,
                 inter=12.6)

    nivel_sospecha(c, y - 14)
    d.pie(c, f"EXPEDIENTE {CASO}", f"FICHA {sujeto['num']}  ·  "
          f"{sujeto['alias']}", numero_pagina)
    c.showPage()


def page_evidencia(c, evidencia, indice, numero_pagina):
    d.fondo(c, PAPER, fibras=170, semilla=300 + indice)
    d.barra_superior(c, f"EXPEDIENTE {CASO}",
                     f"EVIDENCIA {indice + 1} / {len(EVIDENCIAS)}")
    d.franja_identificacion(c, evidencia["letra"], "", "")
    c.setFillColor(INK)
    c.setFont(MONOB, 15)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 46, evidencia["titulo"])
    c.setFillColor(SOFT)
    c.setFont(MONO, 8.2)
    c.drawString(MARGEN + 52, d.FRANJA_Y + 30, "PIEZA REGISTRADA")

    y = seccion(c, d.FRANJA_Y - 24, "NOTA DEL ANALISTA")
    y = d.bloque(c, MARGEN, y, evidencia["nota"], ANCHO_UTIL, tam=8.8,
                 inter=12.6) - 14

    if evidencia["tipo"] == "tabla":
        y = tabla(c, y, evidencia["columnas"], evidencia["filas"],
                  destacar=evidencia.get("destacar", ()))
        y = cierre(c, y - 16, evidencia["cierre"])

    elif evidencia["tipo"] == "parrafos":
        for parrafo in evidencia["parrafos"]:
            y = d.bloque(c, MARGEN, y, parrafo, ANCHO_UTIL, tam=8.8,
                         inter=12.6) - 10
        y = cierre(c, y - 4, evidencia["cierre"])

    else:  # cruzada
        x_sujeto, x_cambio = MARGEN + 10, MARGEN + 110
        c.setFillColor(d.HexColor("#3a362e"))
        c.rect(MARGEN, y - 20, ANCHO_UTIL, 20, stroke=0, fill=1)
        c.setFillColor(PAPER)
        c.setFont(MONOB, 8.4)
        c.drawString(x_sujeto, y - 13.5, "SUJETO")
        c.drawString(x_cambio, y - 13.5, "QUÉ CAMBIÓ ENTRE UNA TOMA Y LA OTRA")
        y_tabla = y
        y -= 20

        ancho_cambio = W - MARGEN - x_cambio - 12
        for i, sujeto in enumerate(SUJETOS):
            alto_fila = max(
                d.alto_bloque(sujeto["cambio"], ancho_cambio, MONO, 8.4, 11.8)
                + 14, 32)
            c.setFillColor(PAPER2 if i % 2 else DATA)
            c.rect(MARGEN, y - alto_fila, ANCHO_UTIL, alto_fila, stroke=0,
                   fill=1)
            c.setFillColor(INK)
            c.setFont(MONOB, 9)
            c.drawString(x_sujeto, y - 16, f"{sujeto['num']}  {sujeto['alias']}")
            d.bloque(c, x_cambio, y - 16, sujeto["cambio"], ancho_cambio,
                     tam=8.4, inter=11.8, justificado=False)
            c.setStrokeColor(RULE)
            c.setLineWidth(0.4)
            c.line(MARGEN, y - alto_fila, W - MARGEN, y - alto_fila)
            y -= alto_fila
        c.setStrokeColor(d.HexColor("#6f6552"))
        c.setLineWidth(1.2)
        c.rect(MARGEN, y, ANCHO_UTIL, y_tabla - y, stroke=1, fill=0)

        y = cierre(c, y - 16,
                   "Tres de los cuatro cambiaron algo. Solo uno de esos "
                   "cambios está ahí para tapar a otra persona.")

    y = seccion(c, y - 4, "ANOTACIONES")
    d.renglones(c, MARGEN, y - 4, ANCHO_UTIL, cantidad=3, paso=16)

    d.pie(c, f"EXPEDIENTE {CASO}", f"EV. {evidencia['letra']}", numero_pagina)
    c.showPage()


def page_answers(c, numero_pagina):
    d.fondo(c, PAPER, fibras=150, semilla=5)
    d.barra_superior(c, f"EXPEDIENTE {CASO}", "HOJA DE RESOLUCIÓN")

    c.setFillColor(INK)
    c.setFont(MONOB, 20)
    c.drawString(MARGEN, d.H - 104, "HOJA DE RESOLUCIÓN")
    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawRightString(W - MARGEN, d.H - 100, "RELLENAR LA BURBUJA COMPLETAMENTE")
    c.setStrokeColor(RED)
    c.setLineWidth(2.5)
    c.line(MARGEN, d.H - 113, MARGEN + 250, d.H - 113)

    y = d.banda_seccion(
        c, d.H - 150,
        "P1  ·  ¿QUIÉN SE COMIÓ EL QUEQUE?   |   P2  ·  ¿QUIÉN LO ENCUBRIÓ?")
    c.setFillColor(SOFT)
    c.setFont(MONO, 7.8)
    c.drawString(MARGEN, y - 4,
                 "Una sola marca en cada columna.   Burbuja 1 = se lo comió "
                 "(6 pts).   Burbuja 2 = lo encubrió (2 pts).")

    # Rejilla de cuatro nombres, sin fotos.
    y -= 26
    paso = ANCHO_UTIL / len(SUJETOS)
    for i, sujeto in enumerate(SUJETOS):
        cx = MARGEN + paso * (i + 0.5)
        d.caja(c, cx - paso / 2 + 8, y - 96, paso - 16, 96, relleno=DATA)
        c.setFillColor(INK)
        c.setFont(MONOB, 13)
        c.drawCentredString(cx, y - 30, sujeto["alias"])
        c.setFillColor(SOFT)
        c.setFont(MONO, 7.4)
        c.drawCentredString(cx, y - 44, f"SUJETO {sujeto['num']}")
        for dx, etiqueta in ((-24, "1"), (24, "2")):
            d.burbuja(c, cx + dx, y - 70, r=7.5)
            c.setFillColor(SOFT)
            c.setFont(MONOB, 7)
            c.drawCentredString(cx + dx, y - 88, etiqueta)
    y -= 118

    for pregunta in PREGUNTAS:
        if pregunta["tipo"] != "opciones":
            continue
        y = d.banda_seccion(c, y - 18,
                            f"{pregunta['n']}  ·  {pregunta['texto']}   "
                            f"({pregunta['puntos']} "
                            f"{'pt' if pregunta['puntos'] == 1 else 'pts'})")
        y -= 12
        for opcion in pregunta["opciones"]:
            d.burbuja(c, MARGEN + 8, y + 3, r=6)
            c.setFillColor(INK)
            c.setFont(MONO, 8.6)
            c.drawString(MARGEN + 24, y, opcion)
            y -= 21
        y -= 12

    c.setFillColor(d.HexColor("#3a362e"))
    c.rect(MARGEN, y - 18, ANCHO_UTIL, 18, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.setFont(MONOB, 9.5)
    c.drawString(MARGEN + 8, y - 12.5,
                 f"DESEMPATE  ·  {BONUS['texto']}   ({BONUS['puntos']} pts)")
    y -= 30
    for opcion in BONUS["opciones"]:
        d.burbuja(c, MARGEN + 8, y + 3, r=6)
        c.setFillColor(INK)
        c.setFont(MONO, 8.6)
        c.drawString(MARGEN + 24, y, opcion)
        y -= 21

    d.pie(c, f"EXPEDIENTE {CASO}", "RESPUESTAS", numero_pagina)
    c.showPage()


def page_solution(c, numero_pagina):
    d.fondo(c, d.HexColor("#2a2723"), fibras=90, semilla=7)
    c.setFillColor(RED)
    c.rect(0, d.BARRA_Y, W, d.BARRA_ALTO, stroke=0, fill=1)
    c.setFillColor(d.HexColor("#f6efe6"))
    c.setFont(MONOB, 10)
    c.drawString(MARGEN, d.BARRA_Y + 12, f"EXPEDIENTE {CASO}")
    c.setFont(MONO, 8.6)
    c.drawRightString(W - MARGEN, d.BARRA_Y + 12.5, "LA RESPUESTA")

    c.setFillColor(d.HexColor("#f6efe6"))
    c.setFont(MONOB, 20)
    c.drawString(MARGEN, d.H - 104, "RESOLUCIÓN DEL CASO")
    c.setStrokeColor(d.RED_L)
    c.setLineWidth(2.5)
    c.line(MARGEN, d.H - 113, MARGEN + 250, d.H - 113)
    c.setFillColor(d.RED_L)
    c.setFont(MONOB, 9)
    c.drawString(MARGEN, d.H - 132, "NO VOLTEAR ANTES DE MARCAR LAS BURBUJAS")

    y_caja = d.H - 226
    c.setFillColor(d.HexColor("#332f2a"))
    c.setStrokeColor(d.RED_L)
    c.setLineWidth(1.6)
    c.rect(MARGEN, y_caja, ANCHO_UTIL, 80, stroke=1, fill=1)
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 12)
    c.drawString(MARGEN + 16, y_caja + 56, "SE LO COMIÓ:  BRUNO — SUJETO 02")
    c.drawString(MARGEN + 16, y_caja + 36, "LO ENCUBRIÓ:  CARLA — SUJETO 03")
    c.setFillColor(d.HexColor("#c9c1b1"))
    c.setFont(MONO, 8.6)
    c.drawString(MARGEN + 16, y_caja + 16,
                 "El más callado de la mesa y la que nadie estaba mirando.")

    y = y_caja - 24
    for titulo, texto in SOLUCION:
        c.setFillColor(d.RED_L)
        c.setFont(MONOB, 8.8)
        c.drawString(MARGEN, y, titulo)
        y = d.bloque(c, MARGEN, y - 14, texto, ANCHO_UTIL, tam=8.4, inter=11.8,
                     color=d.HexColor("#ddd6c5")) - 10

    filas = [(p["n"], p["respuesta"], p["puntos"]) for p in PREGUNTAS]
    filas.append((BONUS["n"], BONUS["respuesta"], BONUS["puntos"]))
    alto_clave = 34 + (len(filas) + 1) * 15
    y_clave = y - alto_clave
    c.setFillColor(d.HexColor("#332f2a"))
    c.setStrokeColor(d.HexColor("#5a5349"))
    c.setLineWidth(1)
    c.rect(MARGEN, y_clave, ANCHO_UTIL, alto_clave, stroke=1, fill=1)

    yy = y_clave + alto_clave - 18
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 9)
    c.drawString(MARGEN + 12, yy, "CLAVE DE CALIFICACIÓN")
    yy -= 17
    for etiqueta, respuesta, puntos in filas:
        c.setFillColor(d.HexColor("#9c9484"))
        c.setFont(MONOB, 7.8)
        c.drawString(MARGEN + 12, yy, etiqueta)
        c.setFillColor(d.HexColor("#ddd6c5"))
        c.setFont(MONO, 7.8)
        c.drawString(MARGEN + 44, yy, respuesta)
        c.setFillColor(d.HexColor("#f0a898"))
        c.setFont(MONOB, 7.8)
        c.drawRightString(W - MARGEN - 12, yy,
                          f"{puntos} {'pt' if puntos == 1 else 'pts'}")
        yy -= 15
    c.setFillColor(d.HexColor("#f0a898"))
    c.setFont(MONOB, 8.4)
    c.drawRightString(W - MARGEN - 12, yy - 2,
                      f"TOTAL: {PUNTAJE_BASE} PUNTOS  (+{BONUS['puntos']} "
                      f"de desempate)")

    c.setFillColor(SOFT)
    c.setFont(MONO, 8)
    c.drawCentredString(W / 2, 30, str(numero_pagina))
    c.showPage()


# ─── Ensamblado ──────────────────────────────────────────────────────────────

PAGINAS_ESPERADAS = 2 + len(SUJETOS) + len(EVIDENCIAS) + 2


def construir(ruta):
    d.registrar_fuentes()
    c = rl_canvas.Canvas(ruta, pagesize=d.PAGESIZE)
    c.setTitle(f"EXPEDIENTE {CASO}")
    c.setAuthor(OFICINA)
    c.setSubject(TITULO)

    page_cover(c)
    page_como_se_juega(c)

    pagina = 3
    for i, sujeto in enumerate(SUJETOS):
        page_suspect(c, sujeto, i, pagina)
        pagina += 1
    for i, evidencia in enumerate(EVIDENCIAS):
        page_evidencia(c, evidencia, i, pagina)
        pagina += 1

    page_answers(c, pagina)
    page_solution(c, pagina + 1)
    c.save()

    if c.getPageNumber() - 1 != PAGINAS_ESPERADAS:
        raise SystemExit(f"Salieron {c.getPageNumber() - 1} páginas y se "
                         f"esperaban {PAGINAS_ESPERADAS}.")
    return ruta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--salida", default=None)
    args = parser.parse_args()
    ruta = args.salida or os.path.join(BASE, "out", "EXPEDIENTE_000_DEMO.pdf")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    construir(ruta)
    print(f"  ✓  {ruta}   {PAGINAS_ESPERADAS} páginas")


if __name__ == "__main__":
    main()
