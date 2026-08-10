"""
Datos del EXPEDIENTE 002 — EL CONSTRUCTOR.

Fuente única de verdad. Los tres scripts leen de acá: si algo cambia — un
nombre, una hora, una declaración — se cambia en este archivo y nada más.
El documento de diseño que explica el porqué de cada pieza está en
CASO_002_BIBLIA.md.
"""

# ─── Identificación del caso ─────────────────────────────────────────────────

CASO = "002–CONSTRUCTOR"
TITULO = "MUERTE DE ADULTO MAYOR EN REUNIÓN FAMILIAR"
OFICINA = "OFICINA DE INVESTIGACIÓN FAMILIAR"
DIVISION = "DIVISIÓN DE ASUNTOS DOMÉSTICOS  ·  UNIDAD DE MUERTES DUDOSAS"
SESION = "NOCHE DE PRIMOS — SESIÓN ÚNICA"
LUGAR = "Condominio Teruma — casa del Sujeto n.º 01"

FECHA_HECHOS = "sábado 11 de julio"
FECHA_DECL_I = "12 de julio, 03:50–05:10"
FECHA_DECL_II = "22 de julio, 09:00–14:30"
VENTANA = "21:30 — 22:15"

# ─── Víctima ─────────────────────────────────────────────────────────────────

VICTIMA = {
    "nombre": "WILLIAM GUILLERMO",
    "apodo": "«BOB EL CONSTRUCTOR»",
    "edad": "74 años",
    "vinculo": "Abuelo de los Sujetos 01, 04, 06, 08 y 09",
    "perfil": (
        "Ludópata de años; la familia lo sabía a medias y nadie sabía cuánto. "
        "Arreglatodo compulsivo: si algo sonaba raro, lo abría. Callejero — se "
        "pasaba el día caminando el barrio, hablando con todo el mundo y "
        "enterándose de cosas que no le correspondían."
    ),
    "causa": "Intoxicación por sobredosis de su propia medicación cardíaca",
    "hallazgo": (
        "Colapsó a las 22:40 durante la reunión. Falleció a las 03:20 en el "
        "hospital. El certificado inicial consignó causa natural. La toxicología "
        "llegó diez días después."
    ),
}

# ─── Línea de tiempo ─────────────────────────────────────────────────────────

LINEA_TIEMPO = [
    ("19:38", "El occiso llega caminando, como siempre", False),
    ("20:05", "Manda un mensaje: «hoy lo digo»", True),
    ("21:00", "Toma su pastilla de la noche en la mesa, a la vista de todos", False),
    ("21:20", "Sale al parqueo con otra persona. Discuten", True),
    ("21:51", "Brindis. Alguien le entrega su vaso", True),
    ("22:40", "Colapsa. Se llama a la ambulancia", False),
    ("03:20", "Fallece en el hospital", False),
]

# Nodos que se resaltan en rojo en la línea de tiempo de la página 02.
TIEMPO_CRITICO = ("20:05", "21:20", "21:51")

# ─── Los diez sujetos ────────────────────────────────────────────────────────
#
# rol: CULPABLE | COMPLICE | SOPORTE | DESCARTADO | FALSA
# El rol nunca se imprime en las fichas — solo lo usa la página de solución.

SUJETOS = [
    {
        "num": "01",
        "cambio": "Precisa la permanencia del Sujeto n.º 02 en la cocina: de «en algún momento» a «todo el rato, desde las nueve».",
        "alias": "FÍO",
        "equipo": "Equipo 1",
        "presente": "Sí — anfitriona",
        "vinculo": "Nieta del occiso · pareja del Sujeto n.º 02",
        "rol": "COMPLICE",
        "perfil": (
            "Anfitriona de la noche: la casa es suya. Temperamento frontal, no le "
            "esquiva a una discusión y suele llevar la voz cantante en cualquier "
            "mesa. La familia comenta abiertamente que tiene al Sujeto n.º 02 «con "
            "correa»."
        ),
        "decl1": (
            "Yo estaba en la cocina casi todo el rato. Marce me estuvo ayudando con "
            "los tragos en algún momento, no sé bien a qué hora. Perdón, es que "
            "estoy muy mal."
        ),
        "decl2": (
            "Yo estaba en la cocina casi todo el rato. Marce estuvo conmigo en la "
            "cocina todo el rato, desde las nueve hasta el brindis. No se movió de "
            "ahí ni un minuto. De eso sí estoy segura."
        ),
        "observa": (
            "Entre la primera y la segunda toma, un «me ayudó en algún momento» se "
            "convirtió en una coartada cerrada de tres horas para otra persona. "
            "Recogió y lavó todos los vasos antes de que llegara la ambulancia; "
            "atribuye el gesto a los nervios."
        ),
    },
    {
        "num": "02",
        "cambio": "Sin variación. Texto idéntico en ambas tomas.",
        "alias": "MARCE",
        "equipo": "Equipo 2",
        "presente": "Sí",
        "vinculo": "Pareja del Sujeto n.º 01 · sin vínculo de sangre",
        "rol": "CULPABLE",
        "perfil": (
            "Reputación de despistado crónico dentro del grupo — la broma familiar "
            "es que opera con una sola neurona. Se moviliza en un vehículo alemán "
            "de gama alta y jamás deja pasar la oportunidad de mencionarlo."
        ),
        "decl1": (
            "Estuve con Fío en la cocina desde como las nueve. Ayudándole con los "
            "tragos y con el hielo. No me moví de ahí en toda la noche."
        ),
        "decl2": (
            "Estuve con Fío en la cocina desde como las nueve. Ayudándole con los "
            "tragos y con el hielo. No me moví de ahí en toda la noche."
        ),
        "observa": (
            "Único sujeto del expediente cuyas dos declaraciones coinciden palabra "
            "por palabra, con diez días de diferencia entre las tomas. Se le pidió "
            "reformularla con sus propias palabras y repitió la misma frase. Niega "
            "haber salido al parqueo en toda la noche."
        ),
    },
    {
        "num": "03",
        "cambio": "Matiza la hora de una fotografía y remite al archivo.",
        "alias": "NICOLE",
        "equipo": "Equipo 1",
        "presente": "Sí",
        "vinculo": "Mejor amiga del Sujeto n.º 01 · sin vínculo familiar",
        "rol": "SOPORTE",
        "perfil": (
            "Mejor amiga del Sujeto n.º 01 desde hace años; cae a estas reuniones "
            "como una más de la familia sin serlo. Documenta compulsivamente todo "
            "lo que ocurre a su alrededor. Arrastra una fijación prolongada con un "
            "individuo ajeno al grupo y mantiene un vínculo reciente con otro."
        ),
        "decl1": (
            "Estuve entrando y saliendo al patio toda la noche tomando fotos. Tengo "
            "como sesenta, todas con hora."
        ),
        "decl2": (
            "Estuve entrando y saliendo al patio toda la noche. La del parqueo creo "
            "que la tomé como a las nueve y algo, pero mejor revisen el archivo: yo "
            "con las horas soy un desastre."
        ),
        "observa": (
            "Deriva normal de memoria entre una toma y otra. Su carrete aporta las "
            "EVIDENCIAS B y C, y las dos tomas que sitúan al Sujeto n.º 09 dormida "
            "en el sofá durante la ventana crítica."
        ),
    },
    {
        "num": "04",
        "cambio": "Agrega una salida al pasillo alrededor de las 21:30.",
        "alias": "JIME",
        "equipo": "Equipo 1",
        "presente": "Sí",
        "vinculo": "Nieta del occiso · pareja del Sujeto n.º 05",
        "rol": "DESCARTADO",
        "perfil": (
            "Estatura reducida, presencia desproporcionadamente grande. Permanece "
            "conectada a su dispositivo de forma casi permanente cuando su pareja "
            "está en línea, lo que la convierte en testigo involuntario de buena "
            "parte de la noche."
        ),
        "decl1": (
            "Estuve en videollamada con Daleek desde antes de las siete. No colgué "
            "en toda la noche, ni cuando pasó lo del abuelo."
        ),
        "decl2": (
            "Estuve en videollamada con Daleek desde antes de las siete. En algún "
            "momento salí al pasillo porque adentro no se oía nada; eso fue como a "
            "las nueve y media."
        ),
        "observa": (
            "El registro técnico confirma llamada continua de 18:50 a 23:04. "
            "Coartada verificada. El audio de esa misma llamada aporta la "
            "EVIDENCIA H."
        ),
    },
    {
        "num": "05",
        "cambio": "Sin cambios de fondo. Amplía la negativa a pronunciarse.",
        "alias": "DALEEK",
        "equipo": "Equipo 1",
        "presente": "No — videollamada desde el exterior",
        "vinculo": "Pareja del Sujeto n.º 04 · sin vínculo de sangre",
        "rol": "DESCARTADO",
        "perfil": (
            "Vive en Estados Unidos y participa solo por videollamada. Apodado "
            "«mantequilla» porque se resbala de cualquier pregunta directa."
        ),
        "decl1": "No sabría decirte. Yo veía lo que la cámara agarraba, nada más.",
        "decl2": (
            "Es que de verdad no sabría decirte. Se oía gente, sí, pero yo no "
            "podría jurar quién era. No me hagan decir algo que no vi."
        ),
        "observa": (
            "Coartada física incuestionable: no estuvo en el país. Su estilo "
            "evasivo es de carácter y no de ocultamiento — se comporta igual en "
            "ambas tomas y sobre todos los temas, incluidos los irrelevantes."
        ),
    },
    {
        "num": "06",
        "cambio": "Retira la coartada anterior. Declara una salida de 15 min y su motivo real.",
        "alias": "NACHO",
        "equipo": "Equipo 2",
        "presente": "Sí",
        "vinculo": "Nieto del occiso · pareja del Sujeto n.º 07",
        "rol": "FALSA",
        "perfil": (
            "El alma del grupo. Enamoradísimo del Sujeto n.º 07, nunca a más de "
            "tres metros de ella; la familia se lo goza sin piedad."
        ),
        "decl1": (
            "Estuve con Mariela toda la noche. No me separé de ella ni para ir por "
            "hielo."
        ),
        "decl2": (
            "Mentí en lo del hielo. Sí salí, como quince minutos, y volví justo "
            "para el brindis. Y no iba por hielo: iba por cigarros. No quiero que "
            "en la casa se enteren."
        ),
        "observa": (
            "Cambio de versión hacia una confesión que lo perjudica. El registro de "
            "la caseta (EVIDENCIA D) confirma salida a las 21:35 y regreso a las "
            "21:50."
        ),
    },
    {
        "num": "07",
        "cambio": "Sostiene la versión inicial pese a que el Sujeto n.º 06 la retiró.",
        "alias": "MARIELA",
        "equipo": "Equipo 3",
        "presente": "Sí",
        "vinculo": "Pareja del Sujeto n.º 06 · sin vínculo de sangre",
        "rol": "FALSA",
        "perfil": (
            "Historial de incidentes memorables que la familia no deja morir. Si "
            "pasa algo raro en una reunión, su nombre sale por pura estadística."
        ),
        "decl1": "Estuve con Nacho todo el rato. Los dos juntos, toda la noche.",
        "decl2": (
            "Estuve con Nacho todo el rato. Ya sé lo que les dijo él. Yo lo que "
            "digo es lo que digo."
        ),
        "observa": (
            "Única persona del expediente que sostiene una coartada que el propio "
            "beneficiario ya retiró. Interrogada sobre la contradicción, se negó a "
            "ampliar."
        ),
    },
    {
        "num": "08",
        "cambio": "Agrega su rol en la preparación del pastillero semanal.",
        "alias": "NANA",
        "equipo": "Equipo 2",
        "presente": "Sí",
        "vinculo": "Nieta del occiso · sin pareja declarada",
        "rol": "FALSA",
        "perfil": (
            "Soltera, muy soltera, y trabaja veinte horas al día. Capacidad "
            "logística superior: organiza operaciones complejas sin que nadie se "
            "entere de que las organizó."
        ),
        "decl1": (
            "Estuve yendo y viniendo entre la cocina y la sala. Ni me acuerdo bien "
            "de los horarios, yo venía saliendo del trabajo."
        ),
        "decl2": (
            "Estuve yendo y viniendo. Yo le armaba el pastillero al abuelo todos "
            "los domingos, eso lo sabe toda la familia. El de esa semana se lo "
            "entregué completo."
        ),
        "observa": (
            "Le organizaba la medicación semanal al occiso: es quien mejor conocía "
            "el tratamiento y quien tenía acceso habitual. La EVIDENCIA E resuelve "
            "su situación en un sentido y abre otra línea en sentido contrario."
        ),
    },
    {
        "num": "09",
        "cambio": "Agrega valoración clínica sobre la magnitud de la dosis.",
        "alias": "FABI",
        "equipo": "Equipo 3",
        "presente": "Sí",
        "vinculo": "Nieta del occiso · pareja del Sujeto n.º 10",
        "rol": "FALSA",
        "perfil": (
            "Estudia medicina y no tiene vida. Se duerme en cualquier parte — y "
            "babea. Interrogarla más de media hora es contraproducente."
        ),
        "decl1": (
            "Me quedé dormida en el sofá como a las nueve y media. Me despertaron "
            "los gritos. Cuando lo vi supe de una que era el corazón y llamé a la "
            "ambulancia."
        ),
        "decl2": (
            "Me quedé dormida en el sofá. Sí, sé de dosis, estudio eso. Y "
            "precisamente por eso les digo: lo que le dieron no fue un descuido, "
            "fue una barbaridad."
        ),
        "observa": (
            "Único sujeto con formación clínica del expediente. Dos tomas del "
            "carrete del Sujeto n.º 03 la sitúan dormida en el sofá entre las 21:30 "
            "y las 22:20. Fue quien reconoció el cuadro y llamó a emergencias."
        ),
    },
    {
        "num": "10",
        "cambio": "Agrega el avistamiento de dos personas en el parqueo a las 21:20.",
        "alias": "DEYLER",
        "equipo": "Equipo 3",
        "presente": "Sí",
        "vinculo": "Pareja del Sujeto n.º 09 · sin vínculo de sangre",
        "rol": "SOPORTE",
        "perfil": (
            "Conduce con un estilo que solo puede describirse como equino. "
            "Preferencia estética declarada por las rubias, chiste recurrente para "
            "molestar al Sujeto n.º 09."
        ),
        "decl1": (
            "Yo estuve un rato en el parqueo, en el carro, viendo el celular. No vi "
            "nada raro."
        ),
        "decl2": (
            "Sí vi. Como a las nueve y veinte había dos personas discutiendo junto "
            "al BMW. Uno era el abuelo, de eso estoy seguro. Al otro no le vi la "
            "cara, pero tenía camisa clara. No quise meterme y por eso no lo dije."
        ),
        "observa": (
            "Cambio de versión hacia información nueva que no lo beneficia en nada. "
            "Testigo presencial parcial del encuentro de las 21:20."
        ),
    },
]

# ─── Las diez evidencias ─────────────────────────────────────────────────────

EVIDENCIAS = [
    {
        "letra": "A",
        "modo": "marco",
        "titulo": "INFORME DE TOXICOLOGÍA",
        "nota": (
            "Concentración compatible con una dosis del orden de ocho veces la "
            "terapéutica. La ventana de ingesta estimada es 21:30–22:15, lo que "
            "descarta la pastilla que el occiso tomó a la vista de todos a las "
            "21:00 y sitúa el vehículo en algo consumido durante el brindis."
        ),
    },
    {
        "letra": "B",
        "modo": "sangre",
        "titulo": "FOTOGRAFÍA — PARQUEO, 21:22",
        "nota": (
            "Tomada desde el patio hacia el parqueo. Dos figuras junto al vehículo "
            "del Sujeto n.º 02. Sin rostros identificables: la ampliación solo "
            "permite establecer que una de las dos viste camisa clara."
        ),
    },
    {
        "letra": "C",
        "modo": "sangre",
        "titulo": "FOTOGRAFÍA — BRINDIS, 21:51",
        "nota": (
            "Momento exacto de la entrega del vaso al occiso. El rostro de quien lo "
            "entrega queda fuera de cuadro; la ampliación conserva el antebrazo, la "
            "manga y el reloj."
        ),
    },
    {
        "letra": "D",
        "modo": "marco",
        "titulo": "CONTROL DE ACCESO — CASETA TERUMA",
        "nota": (
            "Ningún ingreso externo en toda la velada. El único movimiento "
            "registrado es la salida de un residente a las 21:35 y su regreso a las "
            "21:50."
        ),
    },
    {
        "letra": "E",
        "modo": "sangre",
        "titulo": "PASTILLERO Y CAJA DE REPUESTO",
        "nota": (
            "El pastillero semanal fue hallado completo: las siete casillas "
            "intactas. El faltante corresponde a una caja de repuesto guardada en "
            "una gaveta de la cocina del domicilio, no al pastillero."
        ),
    },
    {
        "letra": "F",
        "modo": "sangre",
        "titulo": "LIBRETA DE PRÉSTAMOS",
        "nota": (
            "Fotografiada por el propio occiso tres semanas antes del hecho. "
            "Veinticuatro meses de cuotas anotadas a mano, con una sola inicial en "
            "la columna del acreedor."
        ),
    },
    {
        "letra": "G",
        "modo": "marco",
        "titulo": "MENSAJE DE LAS 20:05",
        "nota": (
            "Último mensaje enviado por el occiso. Tres palabras, sin contexto y "
            "sin respuesta. Fija la intención de revelar algo esa misma noche."
        ),
    },
    {
        "letra": "H",
        "modo": "marco",
        "titulo": "TRANSCRIPCIÓN DE AUDIO",
        "nota": (
            "Fragmento capturado de fondo en una videollamada, entre 21:19 y 21:24. "
            "Dos voces discutiendo en el exterior. Se recuperan cuatro frases "
            "parciales; el resto es ininteligible."
        ),
    },
    {
        "letra": "I",
        "modo": "nativa",
        "titulo": "ACTA DE DECLARACIONES CRUZADAS",
        "nota": (
            "Comparación literal de las dos tomas de declaración de los diez "
            "sujetos. La oficina no interpreta: solo consigna qué cambió. "
            "Interpretar es trabajo de la unidad investigadora."
        ),
    },
    {
        "letra": "J",
        "modo": "sangre",
        "titulo": "PERSONA DE INTERÉS EXTERNA",
        "nota": (
            "Corredor de apuestas al que el occiso mantenía deuda vigente. Fue "
            "la línea prioritaria durante los primeros seis días de la "
            "investigación. Su situación se resuelve contrastando esta ficha "
            "con el control de acceso del condominio."
        ),
    },
]

# ─── Hoja de resolución ──────────────────────────────────────────────────────

PREGUNTAS = [
    {
        "n": "P1",
        "texto": "¿QUIÉN LE ADMINISTRÓ LA SUSTANCIA?",
        "ayuda": "una sola marca",
        "tipo": "rejilla",
        "puntos": 10,
        "respuesta": "MARCE — Sujeto 02",
    },
    {
        "n": "P2",
        "texto": "¿QUIÉN ENCUBRIÓ AL CULPABLE?",
        "ayuda": "una sola marca",
        "tipo": "rejilla",
        "puntos": 4,
        "respuesta": "FÍO — Sujeto 01",
    },
    {
        "n": "P3",
        "texto": "¿CUÁL ERA EL MOTIVO?",
        "ayuda": "una sola marca",
        "tipo": "opciones",
        "puntos": 2,
        "opciones": [
            "Quedarse con la herencia del occiso",
            "Impedir que revelara los préstamos con intereses",
            "Una deuda de juego impaga con un tercero",
            "Un rencor familiar viejo sin resolver",
        ],
        "correcta": 1,
        "respuesta": "Impedir que revelara los préstamos con intereses",
    },
    {
        "n": "P4",
        "texto": "¿DE DÓNDE SALIERON LAS PASTILLAS?",
        "ayuda": "una sola marca",
        "tipo": "opciones",
        "puntos": 2,
        "opciones": [
            "Del pastillero semanal del occiso",
            "De una farmacia, compradas ese mismo día",
            "De la caja de repuesto en la gaveta de la cocina",
            "De la cartera de otro de los sujetos",
        ],
        "correcta": 2,
        "respuesta": "De la caja de repuesto en la gaveta de la cocina",
    },
    {
        "n": "P5",
        "texto": "EVIDENCIAS QUE SUSTENTAN LA ACUSACIÓN",
        "ayuda": "marcar todas las que apliquen",
        "tipo": "evidencias",
        "puntos": 2,
        "respuesta": "A · C · E · F · I",
    },
]

BONUS = [
    {
        "n": "B1",
        "texto": "¿QUÉ TIENE DE ANÓMALA LA DECLARACIÓN DEL CULPABLE?",
        "puntos": 2,
        "tipo": "opciones",
        "opciones": [
            "Se contradice con la de su pareja",
            "Cambió por completo entre una toma y otra",
            "Es idéntica palabra por palabra en ambas tomas",
            "Se negó a firmar la segunda toma",
        ],
        "correcta": 2,
        "respuesta": "Es idéntica palabra por palabra: está memorizada",
    },
    {
        "n": "B2",
        "texto": "¿A CUÁNTO ASCIENDE LA DEUDA TOTAL DE LA LIBRETA?",
        "puntos": 1,
        "tipo": "abierta",
        "respuesta": "₡ 4 860 000  (suma de la columna de la EVIDENCIA F)",
    },
]

PUNTAJE_BASE = sum(p["puntos"] for p in PREGUNTAS)  # 20
PUNTAJE_BONUS = sum(b["puntos"] for b in BONUS)  # 3
PENALIZACION = -2  # por marcar a un inocente en P1 o P2; el total nunca baja de 0

# ─── Solución (solo página del anfitrión) ────────────────────────────────────

SOLUCION = {
    "culpable": "SUJETO N.º 02 — MARCE",
    "complice": "SUJETO N.º 01 — FÍO",
    "gancho": "Nadie mató por plata: mató para que no se supiera cómo la consiguió.",
    "bloques": [
        (
            "QUÉ PASÓ REALMENTE",
            "Hace dos años Marce descubrió que el abuelo estaba endeudado con un "
            "corredor de apuestas. En vez de contárselo a la familia, se ofreció a "
            "cubrirlo: le prestaba para tapar cada deuda, con intereses, y lo "
            "anotaba todo en una libreta. El abuelo, muerto de vergüenza, aceptó y "
            "calló durante dos años. De ese dinero salió el BMW — el chiste de la "
            "familia era literalmente cierto y nadie lo sabía.",
        ),
        (
            "DÓNDE SE LE COMPLICÓ",
            "Tres semanas antes, el abuelo encontró la libreta arreglando algo en "
            "la casa de Fío: si algo sonaba raro, él lo abría. Le tomó fotos, sumó "
            "las cuotas y entendió que lo habían estado ordeñando. El sábado a las "
            "20:05 mandó el mensaje «hoy lo digo». A las 21:20 sacó a Marce al "
            "parqueo y se lo avisó a la cara. A las 21:51, en el brindis, Marce le "
            "entregó el vaso.",
        ),
        (
            "POR QUÉ FÍO ENCUBRE",
            "Sabía lo de los préstamos desde el principio y parte de ese dinero lo "
            "disfrutó. Si cae Marce, cae ella. Lavó todos los vasos antes de que "
            "llegara la ambulancia y, diez días después, convirtió un «me ayudó en "
            "algún momento» en una coartada cerrada de tres horas.",
        ),
        (
            "CÓMO ENCAJAN LAS EVIDENCIAS",
            "A fija la ventana de ingesta y descarta la pastilla de las 21:00. C lo "
            "pone entregando el vaso dentro de esa ventana. E demuestra que las "
            "pastillas no salieron del pastillero de Nana sino de la caja de la "
            "gaveta, que solo conocían Fío y Marce. F da el móvil y G la urgencia. "
            "I expone la declaración memorizada y el blindaje de Fío. D descarta a "
            "cualquier externo, incluido J.",
        ),
        (
            "PISTAS FALSAS",
            "Fabi estudia medicina y sabe de dosis — estuvo dormida, con dos fotos "
            "que lo prueban. Nana le armaba el pastillero y ya fue culpable del "
            "caso anterior — el pastillero está intacto. Nacho confiesa una "
            "escapada de quince minutos y vuelve justo para el brindis, y Mariela "
            "sostiene que nunca se movió: la contradicción más ruidosa del "
            "expediente y los dos estaban tapando unos cigarros.",
        ),
    ],
}
