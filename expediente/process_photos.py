#!/usr/bin/env python3
"""
Trata los retratos del expediente: photos/ALIAS.* -> photos_fbi/ALIAS.jpg

    python3 process_photos.py            # procesa lo que haya
    python3 process_photos.py --check    # solo verifica hashes y faltantes

Las diez caras tienen que quedar al mismo tamaño, tono y encuadre. El encuadre
uniforme es lo que hace que la rejilla de la hoja de respuestas se vea de
verdad como una rueda de reconocimiento y no como un collage.
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

import caso

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_ORIGEN = os.path.join(BASE, "photos")
DIR_SALIDA = os.path.join(BASE, "photos_fbi")

LADO_SALIDA = 900
EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic")

ALIAS = [s["alias"] for s in caso.SUJETOS]
# En disco los archivos van sin tilde; FÍO es el único caso.
ARCHIVO_DE_ALIAS = {a: a.replace("Í", "I") for a in ALIAS}


# ─── Verificación previa ─────────────────────────────────────────────────────


def md5(ruta, bloque=1 << 20):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def localizar():
    """Mapea alias -> ruta del original. Devuelve también los que faltan."""
    encontrados, faltantes = {}, []
    for alias in ALIAS:
        base = ARCHIVO_DE_ALIAS[alias]
        for ext in EXTENSIONES:
            for candidato in (base + ext, base + ext.upper()):
                ruta = os.path.join(DIR_ORIGEN, candidato)
                if os.path.exists(ruta):
                    encontrados[alias] = ruta
                    break
            if alias in encontrados:
                break
        else:
            faltantes.append(alias)
    return encontrados, faltantes


def verificar(encontrados):
    """
    Comprueba que los diez hashes sean distintos.

    En la producción original las diez fotos llegaron con el mismo nombre de
    archivo y unas sobrescribieron a otras: dos retratos se duplicaron y dos se
    perdieron. Este chequeo existe para que eso no se repita en silencio.
    """
    por_hash = defaultdict(list)
    for alias, ruta in encontrados.items():
        por_hash[md5(ruta)].append(alias)

    repetidos = {h: a for h, a in por_hash.items() if len(a) > 1}
    for h, aliases in repetidos.items():
        print(f"  ✗  MISMO ARCHIVO para {', '.join(aliases)}  (md5 {h[:12]})",
              file=sys.stderr)
    return repetidos


# ─── Paso 1 — Detección de rostro ────────────────────────────────────────────

CASCADAS = ["haarcascade_frontalface_default.xml",
            "haarcascade_frontalface_alt2.xml",
            "haarcascade_profileface.xml"]
BARRIDOS = [(1.05, 6), (1.05, 4), (1.03, 3), (1.08, 3)]


def fraccion_piel(bgr):
    """Fracción de píxeles en el rango de tono de piel, en YCrCb."""
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    cr, cb = ycrcb[:, :, 1], ycrcb[:, :, 2]
    mascara = (cr >= 133) & (cr <= 180) & (cb >= 77) & (cb <= 130)
    return float(mascara.mean())


def detectar(bgr):
    """
    Devuelve la mejor caja (x, y, w, h) o None.

    Se acumulan candidatos de tres cascadas por cuatro barridos, sobre la gris
    y sobre la gris ecualizada, y después se puntúan. El filtro de tono de piel
    no es opcional: sin él las ventanas y las estructuras del fondo puntúan
    como caras y el recorte sale centrado en una pared.
    """
    alto, ancho = bgr.shape[:2]
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    variantes = [gris, cv2.equalizeHist(gris)]

    candidatos = []
    for archivo in CASCADAS:
        clasificador = cv2.CascadeClassifier(cv2.data.haarcascades + archivo)
        if clasificador.empty():
            continue
        for variante in variantes:
            for escala, vecinos in BARRIDOS:
                detecciones = clasificador.detectMultiScale(
                    variante, scaleFactor=escala, minNeighbors=vecinos,
                    minSize=(max(40, ancho // 20), max(40, alto // 20)),
                )
                candidatos.extend(tuple(int(v) for v in c) for c in detecciones)

    if not candidatos:
        return None

    # Dedupe: cajas con centro a menos de 25 px y lado a menos de 30 px.
    unicos = []
    for x, y, w, h in candidatos:
        cx, cy = x + w / 2, y + h / 2
        if any(abs(cx - (ux + uw / 2)) < 25 and abs(cy - (uy + uh / 2)) < 25
               and abs(w - uw) < 30 for ux, uy, uw, uh in unicos):
            continue
        unicos.append((x, y, w, h))

    ojos = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    def cuenta_ojos(caja):
        """
        Ojos detectados en la mitad superior del candidato.

        El filtro de piel por sí solo no basta: premia cualquier zona amplia de
        piel, así que un escote o un brazo desnudo puntúan como cara y el
        recorte sale en el torso. Los ojos son lo que distingue una cara de una
        mancha de piel.
        """
        if ojos.empty():
            return 0
        x, y, w, h = caja
        media = bgr[max(0, y):y + int(h * 0.62), max(0, x):x + w]
        if media.size == 0:
            return 0
        gris_media = cv2.cvtColor(media, cv2.COLOR_BGR2GRAY)
        return len(ojos.detectMultiScale(gris_media, scaleFactor=1.08,
                                         minNeighbors=6,
                                         minSize=(max(8, w // 12),) * 2))

    def puntuar(caja):
        x, y, w, h = caja
        recorte = bgr[max(0, y):y + h, max(0, x):x + w]
        piel = fraccion_piel(recorte) if recorte.size else 0.0
        tam_rel = w / ancho
        centrado = 1 - abs((x + w / 2) / ancho - 0.5) * 2
        altura = 1 - (y + h / 2) / alto
        score = 1.5 * tam_rel + 1.3 * centrado + 0.5 * altura + 2.2 * piel
        if piel < 0.12:
            score -= 2.5       # descarta ventanas y estructuras del fondo
        score += min(cuenta_ojos(caja), 2) * 1.5
        return score

    return max(unicos, key=puntuar)


# ─── Paso 2 — Recorte cuadrado ───────────────────────────────────────────────


def recortar(pil, caja):
    """Cuadrado centrado en la cara, desplazado hacia abajo para los hombros."""
    ancho, alto = pil.size
    if caja is None:
        lado = min(ancho, alto)
        cx = ancho / 2
        cy = alto * 0.42 if alto > ancho else alto / 2
    else:
        x, y, w, h = caja
        lado = w * 3.1  # cabeza + hombros
        cx = x + w / 2
        cy = y + h / 2 + 0.10 * lado

    lado = min(lado, ancho, alto)
    izq = int(round(min(max(cx - lado / 2, 0), ancho - lado)))
    arr = int(round(min(max(cy - lado / 2, 0), alto - lado)))

    if caja is not None:
        # La caja de Haar suele empezar en la frente, así que el pelo queda por
        # encima. Sin reservar ese aire, el desplazamiento hacia los hombros
        # termina cortando la coronilla.
        aire = 0.95 * caja[3]
        tope_maximo = int(round(caja[1] - aire))
        arr = min(arr, max(tope_maximo, 0))
        arr = min(arr, int(alto - lado))

    lado = int(round(lado))
    return pil.crop((izq, arr, izq + lado, arr + lado)).resize(
        (LADO_SALIDA, LADO_SALIDA), Image.LANCZOS)


# ─── Paso 3 — Filtro de archivo ──────────────────────────────────────────────


def filtro_archivo(pil, semilla=7):
    """Blanco y negro, viñeta, grano y tinte cálido. Resultado reproducible."""
    from PIL import ImageFilter

    gris = pil.convert("L")
    gris = ImageOps.autocontrast(gris, cutoff=1)
    gris = ImageEnhance.Contrast(gris).enhance(1.18)
    gris = ImageEnhance.Brightness(gris).enhance(1.02)
    gris = gris.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=3))

    arr = np.asarray(gris).astype(np.float32) / 255.0
    lado = arr.shape[0]

    ys, xs = np.mgrid[0:lado, 0:lado]
    radio = np.sqrt(((xs / lado - 0.5) * 2) ** 2 + ((ys / lado - 0.5) * 2) ** 2)
    radio /= np.sqrt(2)
    arr *= np.clip(1 - 0.34 * np.clip(radio - 0.55, 0, None) ** 1.5 * 2.2, 0.45, 1.0)

    arr += np.random.default_rng(semilla).normal(0.0, 0.022, arr.shape)
    arr = np.clip(arr, 0, 1)

    rgb = np.dstack([arr * 1.000 + 0.045, arr * 0.985 + 0.030, arr * 0.955 + 0.012])
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")


# ─── Orquestación ────────────────────────────────────────────────────────────


def procesar(alias, ruta_origen):
    pil = Image.open(ruta_origen)
    pil = ImageOps.exif_transpose(pil).convert("RGB")

    bgr = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    caja = detectar(bgr)

    salida = filtro_archivo(recortar(pil, caja))
    destino = os.path.join(DIR_SALIDA, f"{ARCHIVO_DE_ALIAS[alias]}.jpg")
    salida.save(destino, "JPEG", quality=94, subsampling=0)
    return destino, caja


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="solo verifica hashes y faltantes, no procesa")
    args = parser.parse_args()

    os.makedirs(DIR_ORIGEN, exist_ok=True)
    os.makedirs(DIR_SALIDA, exist_ok=True)

    encontrados, faltantes = localizar()
    print(f"Retratos encontrados: {len(encontrados)} de {len(ALIAS)}")
    if faltantes:
        print(f"  ·  faltan: {', '.join(faltantes)}")

    if verificar(encontrados):
        raise SystemExit(
            "\nHay archivos repetidos. Se detiene sin procesar: renombrá cada "
            "foto con el alias que le toca y volvé a correr."
        )

    if args.check:
        return

    for alias in ALIAS:
        if alias not in encontrados:
            continue
        destino, caja = procesar(alias, encontrados[alias])
        estado = "cara detectada" if caja else "SIN CARA — recorte central"
        print(f"  ✓  {os.path.basename(destino):<12} {estado}")


if __name__ == "__main__":
    main()
