# EXPEDIENTE 002 — EL CONSTRUCTOR

Juego de misterio impreso para diez personas en tres equipos. Estética de
expediente policial, 28 páginas en español, listo para imprimir.

---

## Qué imprimir

| | |
|---|---|
| **Para los equipos** | páginas **1 – 27**, a color, **3 copias** (una por unidad) |
| **Para el anfitrión** | página **28**, **una sola copia** |
| Formato | US Letter · a color · una cara |

**La página 28 es la solución.** Va siempre al final justamente para que se
puedan imprimir las 1–27 por triplicado sin ella. Si la imprimís de más, se
acabó el juego.

Consejo de anfitrión: engrapá cada juego por separado o metelo en un folder
manila. Parte de la gracia es repartir tres expedientes idénticos.

---

## Cómo se juega

Diez personas, tres equipos, **75 – 90 minutos**.

1. Cada equipo recibe su copia de las páginas 1–27 y anota su número de unidad
   en la portada.
2. Leen las diez fichas de sujeto. Cada ficha trae **dos declaraciones**: la de
   la madrugada del sábado, cuando todos creían que había sido el corazón, y la
   de diez días después, ya sabiendo que fue un homicidio.
3. Cruzan las diez evidencias (A–J) con la línea de tiempo.
4. Usan la página 25 —el tablero de corcho— para trazar sus conexiones con
   lápiz rojo. Esa página no se califica.
5. Rellenan la hoja de resolución (páginas 26–27) y la entregan con la hora
   anotada.

Al final se comparan las tres hojas contra la página 28. Calificar tres hojas
de burbujas toma unos dos minutos.

### Puntaje

| | | |
|---|---|---|
| P1 | Quién administró la sustancia | 10 pts |
| P2 | Quién encubrió al culpable | 4 pts |
| P3 | Motivo | 2 pts |
| P4 | Origen de las pastillas | 2 pts |
| P5 | Evidencias que sustentan la acusación | 2 pts |
| | **Total base** | **20 pts** |

**Penalización:** −2 puntos por acusar a una persona inocente en P1 o en P2. El
puntaje de una unidad nunca baja de cero.

**Desempate:** dos preguntas extra (3 pts) que **solo se cuentan si dos unidades
quedan iguales**. Si el desempate tampoco resuelve, gana quien entregó primero.

---

## Cómo se regenera

```bash
pip install -r requirements.txt
sudo apt-get install fonts-liberation fonts-urw-base35   # tipografías

python3 process_photos.py      # photos/ALIAS.*  ->  photos_fbi/ALIAS.jpg
python3 make_evidence.py       # evidence/EV_A.jpg … EV_J.jpg + EV_TABLERO.jpg
python3 build_expediente.py    # out/EXPEDIENTE_002.pdf
```

### Los retratos

Poné las diez fotos en `photos/` con **un archivo por persona y nombres
distintos**:

```
FIO  MARCE  NICOLE  JIME  DALEEK  NACHO  MARIELA  NANA  FABI  DEYLER
```

`process_photos.py` verifica que los diez `md5sum` sean únicos **antes** de
procesar y se detiene si dos retratos resultan ser el mismo archivo. Ese chequeo
existe porque en la producción anterior las diez fotos llegaron con el mismo
nombre, unas sobrescribieron a otras y dos retratos se perdieron.

Mientras falten fotos el expediente se compone igual, con el recuadro de
«FOTOGRAFÍA PENDIENTE» en su lugar. La víctima sale en silueta salvo que
aparezca `photos/VICTIMA.*`.

### Los archivos

| Archivo | Qué hace |
|---|---|
| `caso.py` | **Fuente única de verdad**: sujetos, evidencias, preguntas, solución |
| `design.py` | Paleta, retícula y primitivas de página (manual §1) |
| `evidencia_lib.py` | Superficies, cinta, corcho, polaroids, sellos, envejecido |
| `process_photos.py` | Pipeline de retratos: detección, recorte y filtro de archivo |
| `make_evidence.py` | Genera las diez evidencias y el tablero |
| `build_expediente.py` | Compone el PDF y verifica que salgan 28 páginas |
| `CASO_002_BIBLIA.md` | **Spoilers.** El diseño del caso y por qué cada pieza está donde está |

Para cambiar un nombre, una hora o una declaración: se toca `caso.py` y nada
más.

---

## Verificación antes de imprimir

```bash
python3 build_expediente.py                     # falla si no salen 28 páginas
pdftoppm -jpeg -r 60 out/EXPEDIENTE_002.pdf /tmp/p
```

Y **mirá el render**. Las dos páginas que históricamente se desbordan son la
hoja de resolución y la de solución; ambas están ajustadas, pero cualquier
cambio de texto en `caso.py` puede volver a empujarlas. No des por bueno un PDF
que no viste renderizado.
