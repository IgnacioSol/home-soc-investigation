#!/usr/bin/env python3
"""
Arma el teaser del EXPEDIENTE 002 en MP4 vertical.

    python3 make_teaser.py                 # 1080×1920, 24 fps
    python3 make_teaser.py --horizontal    # 1920×1080

No es video generado: son cuadros compuestos con el mismo sistema de diseño
del expediente y unidos con ffmpeg. La portada sale del PDF ya compuesto y las
polaroids de los retratos ya tratados, así que el teaser no puede desincronizar
con el material impreso.

No revela nada del caso: muestra las diez caras y ninguna pista.
"""

import argparse
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio_teaser as au
import caso
import evidencia_lib as ev
from evidencia_lib import fuente, medir

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "out", "EXPEDIENTE_002.pdf")
DIR_RETRATOS = os.path.join(BASE, "photos_fbi")

FPS = 24
FONDO = (14, 13, 12)

# Guion: (nombre, duración en segundos). El orden es el del video.
GUION = [
    ("portada", 3.6),
    ("sello", 2.4),
    ("corte", 0.8),
    ("polaroids", 6.4),
    ("hilo", 3.0),
    ("cierre", 5.4),
]


# ─── Utilidades de animación ─────────────────────────────────────────────────


def suave(t):
    """Aceleración y frenado suaves. t en [0, 1]."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rebote(t):
    """Entrada con sobrepaso: llega, se pasa un poco y vuelve."""
    t = max(0.0, min(1.0, t))
    return 1 + (2.70158 + 1) * (t - 1) ** 3 + 2.70158 * (t - 1) ** 2


def mezclar(fondo, capa, alfa):
    """Funde `capa` sobre `fondo` con opacidad global."""
    if alfa <= 0:
        return fondo
    if alfa >= 1:
        return capa
    return Image.blend(fondo, capa, alfa)


class Grano:
    """
    Banco de ruido precalculado.

    Generar ruido nuevo en cada cuadro a 1080×1920 cuesta más que todo el resto
    del compositor junto; con seis texturas rotando el ojo no nota la repetición.
    """

    def __init__(self, tamano, cantidad=6, sigma=6.0, semilla=4):
        rnd = np.random.default_rng(semilla)
        ancho, alto = tamano
        self.banco = [rnd.normal(0, sigma, (alto, ancho, 1)) for _ in range(cantidad)]

    def aplicar(self, img, indice):
        arr = np.asarray(img, dtype=np.float32) + self.banco[indice % len(self.banco)]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def vineta(img, fuerza=0.55):
    ancho, alto = img.size
    ys = np.linspace(-1, 1, alto)[:, None]
    xs = np.linspace(-1, 1, ancho)[None, :]
    radio = np.sqrt(xs ** 2 + ys ** 2) / math.sqrt(2)
    factor = np.clip(1 - fuerza * np.clip(radio - 0.35, 0, None) ** 1.6 * 2.2,
                     0.15, 1.0)[:, :, None]
    arr = np.asarray(img, dtype=np.float32) * factor
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def texto_centrado(draw, y, texto, tam, color, ancho_lienzo, negrita=True,
                   espaciado=0):
    """Dibuja una línea centrada, con tracking opcional entre letras."""
    fnt = fuente("monob" if negrita else "mono", tam)
    if not espaciado:
        ancho_txt = medir(draw, texto, fnt)[0]
        draw.text(((ancho_lienzo - ancho_txt) / 2, y), texto, font=fnt, fill=color)
        return
    anchos = [medir(draw, ch, fnt)[0] + espaciado for ch in texto]
    x = (ancho_lienzo - sum(anchos)) / 2
    for ch, avance in zip(texto, anchos):
        draw.text((x, y), ch, font=fnt, fill=color)
        x += avance


# ─── Recursos ────────────────────────────────────────────────────────────────


def render_portada(ancho_objetivo):
    """Saca la portada del PDF ya compuesto, para que no se desincronicen."""
    if not os.path.exists(PDF):
        raise SystemExit("Falta out/EXPEDIENTE_002.pdf. Corré build_expediente.py.")
    resolucion = round(ancho_objetivo / 612 * 72)
    with tempfile.TemporaryDirectory() as tmp:
        prefijo = os.path.join(tmp, "p")
        subprocess.run(["pdftoppm", "-jpeg", "-r", str(resolucion),
                        "-f", "1", "-l", "1", PDF, prefijo], check=True)
        archivo = next(f for f in sorted(os.listdir(tmp)) if f.endswith(".jpg"))
        return Image.open(os.path.join(tmp, archivo)).convert("RGB").copy()


def construir_polaroids(ancho_pol):
    """Una polaroid por sujeto, ya rotada, con su posición en el tablero."""
    rnd = random.Random(7)
    piezas = []
    for i, sujeto in enumerate(caso.SUJETOS):
        archivo = os.path.join(DIR_RETRATOS,
                               f"{sujeto['alias'].replace('Í', 'I')}.jpg")
        if os.path.exists(archivo):
            with Image.open(archivo) as im:
                interior = im.convert("RGB").copy()
        else:
            interior = ev.silueta(400, fondo=(70, 62, 50))
        pol = ev.polaroid(interior, sujeto["alias"], ancho=ancho_pol,
                          borde=int(ancho_pol * 0.055),
                          borde_inferior=int(ancho_pol * 0.20),
                          tam_pie=int(ancho_pol * 0.11), semilla=i + 2)
        piezas.append({"img": pol.rotate(rnd.uniform(-4.5, 4.5), expand=True,
                                         resample=Image.BICUBIC)})
    return piezas


def repartir(piezas, tamano, filas=(3, 3, 2, 2)):
    """Coloca las polaroids en filas centradas sobre el tablero."""
    ancho, alto = tamano
    alto_pieza = piezas[0]["img"].height
    margen_sup = int(alto * 0.085)
    paso_y = (alto - margen_sup - int(alto * 0.16)) / len(filas)

    indice = 0
    for f, cuantas in enumerate(filas):
        ancho_fila = sum(piezas[indice + k]["img"].width for k in range(cuantas))
        hueco = (ancho - ancho_fila) / (cuantas + 1)
        x = hueco
        for _ in range(cuantas):
            pieza = piezas[indice]
            pieza["pos"] = (int(x),
                            int(margen_sup + f * paso_y + (paso_y - alto_pieza) / 2))
            pieza["centro"] = (pieza["pos"][0] + pieza["img"].width // 2,
                               pieza["pos"][1] + pieza["img"].height // 2)
            x += pieza["img"].width + hueco
            indice += 1
    return piezas


# ─── Escenas ─────────────────────────────────────────────────────────────────


class Teaser:
    def __init__(self, tamano):
        self.ancho, self.alto = tamano
        self.negro = Image.new("RGB", tamano, FONDO)
        self.grano = Grano(tamano)

        self.portada = render_portada(int(self.ancho * 0.86))
        self.corcho = ev.corcho(self.ancho, self.alto, semilla=12).convert("RGB")
        self.piezas = repartir(construir_polaroids(int(self.ancho * 0.30)), tamano)

        # Hilo: recorrido entre polaroids, no en orden, como lo trazaría alguien.
        orden = [0, 4, 7, 1, 9, 3, 6]
        self.ruta = [self.piezas[i]["centro"] for i in orden]

    # ── portada ──
    def portada_frame(self, t, dur):
        avance = suave(t / dur)
        escala = 1.10 - 0.10 * avance
        pagina = self.portada.resize(
            (int(self.portada.width * escala), int(self.portada.height * escala)),
            Image.LANCZOS)
        marco = self.negro.copy()
        marco.paste(pagina, ((self.ancho - pagina.width) // 2,
                             (self.alto - pagina.height) // 2))
        marco = vineta(marco, 0.7)
        return mezclar(self.negro, marco, min(1.0, t / 0.7))

    # ── sello ──
    def sello_frame(self, t, dur):
        marco = self.portada_frame(dur, dur)  # portada ya asentada
        golpe = 0.55
        if t < golpe:
            escala = 1 + 2.4 * (1 - suave(t / golpe))
            alfa = suave(t / golpe)
        else:
            escala, alfa = 1.0, 1.0

        # La portada ya trae estampado CONFIDENCIAL, así que el sello animado
        # dice otra cosa y cae en la mitad baja, donde no se le encima.
        lienzo = Image.new("RGBA", (self.ancho, self.alto), (0, 0, 0, 0))
        ev.sello(lienzo, (int(self.ancho * 0.44), int(self.alto * 0.66)),
                 "HOMICIDIO", angulo=-9, tam=int(self.ancho * 0.085))
        if escala != 1.0:
            nuevo = (int(lienzo.width * escala), int(lienzo.height * escala))
            grande = lienzo.resize(nuevo, Image.BICUBIC)
            lienzo = grande.crop((
                (nuevo[0] - self.ancho) // 2, (nuevo[1] - self.alto) // 2,
                (nuevo[0] - self.ancho) // 2 + self.ancho,
                (nuevo[1] - self.alto) // 2 + self.alto))

        capa = lienzo.split()[3].point(lambda v: int(v * alfa))
        lienzo.putalpha(capa)
        marco = marco.convert("RGBA")
        marco.alpha_composite(lienzo)
        marco = marco.convert("RGB")

        # Sacudida del golpe.
        if golpe <= t < golpe + 0.18:
            desvio = int(14 * math.sin((t - golpe) / 0.18 * math.pi * 3))
            marco = marco.transform(marco.size, Image.AFFINE,
                                    (1, 0, desvio, 0, 1, -desvio // 2))
        return marco

    # ── corte a negro ──
    def corte_frame(self, t, dur):
        return mezclar(self.sello_frame(2.4, 2.4), self.negro, suave(t / dur))

    # ── polaroids ──
    def tablero(self, cuantas, t_local):
        marco = self.corcho.copy()
        for i, pieza in enumerate(self.piezas[:cuantas]):
            img = pieza["img"]
            if i == cuantas - 1 and t_local < 1.0:
                escala = 1 + 0.35 * (1 - rebote(t_local))
                nuevo = (max(1, int(img.width * escala)),
                         max(1, int(img.height * escala)))
                img = img.resize(nuevo, Image.BICUBIC)
            pos = (pieza["centro"][0] - img.width // 2,
                   pieza["centro"][1] - img.height // 2)
            sombra = Image.new("RGBA", marco.size, (0, 0, 0, 0))
            silueta = img.copy()
            silueta.putalpha(img.split()[3].point(lambda v: min(v, 120)))
            sombra.alpha_composite(silueta, (pos[0] + 9, pos[1] + 12))
            marco = Image.alpha_composite(
                marco.convert("RGBA"), sombra.filter(ImageFilter.GaussianBlur(10))
            ).convert("RGBA")
            marco.alpha_composite(img, pos)
            marco = marco.convert("RGB")
        return marco

    def polaroids_frame(self, t, dur):
        por_pieza = dur / len(self.piezas)
        cuantas = min(len(self.piezas), int(t / por_pieza) + 1)
        marco = self.tablero(cuantas, (t % por_pieza) / por_pieza)
        return mezclar(self.negro, marco, min(1.0, t / 0.5))

    # ── hilo rojo ──
    def hilo_frame(self, t, dur):
        marco = self.tablero(len(self.piezas), 1.0)
        avance = suave(t / dur) * (len(self.ruta) - 1)
        capa = Image.new("RGBA", marco.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)
        for i in range(int(avance)):
            draw.line([self.ruta[i], self.ruta[i + 1]], fill=(168, 32, 26, 225),
                      width=6)
        entero = int(avance)
        if entero < len(self.ruta) - 1:
            frac = avance - entero
            a, b = self.ruta[entero], self.ruta[entero + 1]
            draw.line([a, (a[0] + (b[0] - a[0]) * frac,
                           a[1] + (b[1] - a[1]) * frac)],
                      fill=(168, 32, 26, 225), width=6)
        for punto in self.ruta[:entero + 1]:
            ev.chincheta(capa, punto, radio=int(self.ancho * 0.014))
        marco = marco.convert("RGBA")
        marco.alpha_composite(capa)
        return marco.convert("RGB")

    # ── cierre ──
    def cierre_frame(self, t, dur):
        base = mezclar(self.hilo_frame(3.0, 3.0), self.negro,
                       suave(min(1.0, t / 0.9)))
        marco = base.copy()
        draw = ImageDraw.Draw(marco)

        lineas = [
            (1.0, "DIEZ PERSONAS DE INTERÉS", 0.040, (196, 186, 164)),
            (1.9, "UNA DE ELLAS MIENTE", 0.052, (206, 78, 62)),
            (2.9, "NOCHE DE PRIMOS", 0.034, (196, 186, 164)),
        ]
        y = self.alto * 0.38
        for inicio, texto, escala_tam, color in lineas:
            if t < inicio:
                continue
            # Aparición a máquina de escribir.
            visibles = min(len(texto), int((t - inicio) / 0.045))
            texto_centrado(draw, y, texto[:visibles], int(self.ancho * escala_tam),
                           color, self.ancho, espaciado=int(self.ancho * 0.004))
            y += self.alto * 0.075

        if t > 3.6:
            texto_centrado(draw, self.alto * 0.63, "EXPEDIENTE 002",
                           int(self.ancho * 0.026), (128, 120, 105), self.ancho,
                           negrita=False, espaciado=int(self.ancho * 0.006))
        return marco

    # ── despacho ──
    def frame(self, indice):
        t = indice / FPS
        for nombre, dur in GUION:
            if t < dur:
                metodo = getattr(self, f"{nombre}_frame")
                return self.grano.aplicar(metodo(t, dur), indice)
            t -= dur
        return self.grano.aplicar(self.cierre_frame(GUION[-1][1], GUION[-1][1]),
                                  indice)


# ─── Banda sonora ────────────────────────────────────────────────────────────


def inicio_de(nombre):
    """Segundo en que arranca una escena del guion."""
    t = 0.0
    for escena, dur in GUION:
        if escena == nombre:
            return t
        t += dur
    raise KeyError(nombre)


# Las tres líneas del cierre, con el mismo calendario que usa cierre_frame.
CIERRE_LINEAS = [(1.0, 24), (1.9, 19), (2.9, 15)]
PASO_TECLA = 0.045


def construir_eventos(duracion):
    """
    Lista de (segundo, sonido) alineada con la animación.

    Los tiempos se derivan del mismo GUION que compone el video, así que si se
    reordena una escena el audio la sigue sin tocar nada más.
    """
    eventos = []

    # Reloj de fondo hasta que el hilo toma el mando.
    for i in range(1, int(inicio_de("hilo"))):
        eventos.append((i + 0.05, au.tic(nivel=0.16, semilla=i)))

    # El sello cae a los 0.55 s de su escena, igual que en sello_frame.
    eventos.append((inicio_de("sello") + 0.55, au.golpe_sello()))

    # Una polaroid por tramo, con el mismo reparto que polaroids_frame.
    inicio_pol = inicio_de("polaroids")
    por_pieza = dict(GUION)["polaroids"] / len(caso.SUJETOS)
    for i in range(len(caso.SUJETOS)):
        eventos.append((inicio_pol + i * por_pieza,
                        au.clac_papel(nivel=0.40, semilla=i * 3)))

    # Riser mientras se traza el hilo, y golpe al cortar a negro.
    dur_hilo = dict(GUION)["hilo"]
    eventos.append((inicio_de("hilo"), au.riser(dur_hilo)))
    eventos.append((inicio_de("cierre"), au.impacto(nivel=0.85)))

    # Máquina de escribir, una tecla por letra.
    inicio_cierre = inicio_de("cierre")
    for k, (arranque, letras) in enumerate(CIERRE_LINEAS):
        for j in range(letras):
            eventos.append((inicio_cierre + arranque + j * PASO_TECLA,
                            au.tecla(nivel=0.22, semilla=k * 40 + j)))

    eventos.append((duracion - 1.9, au.impacto(nivel=0.7, caida=1.4)))
    return eventos


# ─── Montaje ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--horizontal", action="store_true")
    parser.add_argument("--sin-audio", action="store_true",
                        help="deja el video mudo")
    parser.add_argument("-o", "--salida", default=None)
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("Falta ffmpeg: apt-get install ffmpeg")

    tamano = (1920, 1080) if args.horizontal else (1080, 1920)
    salida = args.salida or os.path.join(
        BASE, "out", f"TEASER_002{'_H' if args.horizontal else ''}.mp4")
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    total = int(sum(dur for _, dur in GUION) * FPS)
    print(f"Componiendo {total} cuadros a {tamano[0]}×{tamano[1]}…")

    teaser = Teaser(tamano)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(total):
            teaser.frame(i).save(os.path.join(tmp, f"f{i:05d}.jpg"), quality=93)
            if i % 60 == 0:
                print(f"  · {i}/{total}", flush=True)

        # El grano por cuadro rompe la compresión temporal: sin denoise el
        # archivo pasa de 90 MB y no entra por WhatsApp. hqdn3d limpia el ruido
        # entre cuadros y deja el grano espacial, que es el que se ve.
        orden = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                 "-i", os.path.join(tmp, "f%05d.jpg")]

        if not args.sin_audio:
            duracion = total / FPS
            pista = au.construir_pista(construir_eventos(duracion), duracion)
            wav = au.guardar_wav(pista, os.path.join(tmp, "pista.wav"))
            orden += ["-i", wav, "-c:a", "aac", "-b:a", "160k", "-shortest"]
            print("  · banda sonora sintetizada")

        orden += ["-vf", "hqdn3d=2:1.5:4:4",
                  "-c:v", "libx264", "-preset", "slow", "-crf", "26",
                  "-pix_fmt", "yuv420p", "-movflags", "+faststart", salida]
        subprocess.run(orden, check=True)

    print(f"  ✓  {salida}   {total / FPS:.1f} s")


if __name__ == "__main__":
    main()
