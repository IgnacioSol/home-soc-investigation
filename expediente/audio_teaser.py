"""
Banda sonora sintetizada del teaser.

No hay música de archivo ni modelo de audio: cada sonido se construye con
numpy a partir de osciladores y ruido filtrado. Para la estética del
expediente eso conviene — lo que pide una pieza así es diseño sonoro (drone,
reloj, golpes, máquina de escribir), no una canción.

    from audio_teaser import construir_pista, guardar_wav
    guardar_wav(construir_pista(eventos, 21.6), "pista.wav")
"""

import struct
import wave

import numpy as np

SR = 44100


# ─── Bloques de síntesis ─────────────────────────────────────────────────────


def _n(segundos):
    return int(round(segundos * SR))


def envolvente(muestras, ataque=0.002, caida=0.25, forma=2.5):
    """Ataque lineal corto y caída exponencial."""
    t = np.arange(muestras) / SR
    env = np.exp(-t / max(caida, 1e-4) * forma)
    subida = _n(ataque)
    if subida > 1:
        env[:subida] *= np.linspace(0, 1, subida)
    return env


def ruido_filtrado(muestras, centro, ancho, semilla=0):
    """
    Ruido con una campana de frecuencia alrededor de `centro`.

    Filtrar por FFT evita implementar biquads y da un control muy directo del
    color de cada golpe, que es lo único que hace falta acá.
    """
    rnd = np.random.default_rng(semilla)
    x = rnd.normal(0, 1, muestras)
    espectro = np.fft.rfft(x)
    frec = np.fft.rfftfreq(muestras, 1 / SR)
    campana = np.exp(-((frec - centro) ** 2) / (2 * max(ancho, 1.0) ** 2))
    return np.fft.irfft(espectro * campana, n=muestras)


def drone(duracion, base=55.0, nivel=0.16):
    """Colchón grave con batido lento. Es la tensión de fondo del teaser."""
    t = np.arange(_n(duracion)) / SR
    voz = np.zeros_like(t)
    for parcial, peso, desafine in ((1, 1.0, 0.0), (1.5, 0.42, 0.13),
                                    (2, 0.30, -0.19), (3, 0.14, 0.27)):
        voz += peso * np.sin(2 * np.pi * (base * parcial + desafine) * t)
    # Respiración lenta: dos LFO desfasados para que no se sienta cíclico.
    lfo = (0.72 + 0.18 * np.sin(2 * np.pi * 0.07 * t)
           + 0.10 * np.sin(2 * np.pi * 0.113 * t + 1.1))
    aire = ruido_filtrado(len(t), 180, 120, semilla=3) * 0.22
    return (voz * lfo + aire) * nivel


def tic(nivel=0.22, semilla=1):
    """Tic de reloj: dos clics muy cortos, uno más apagado que el otro."""
    muestras = _n(0.09)
    golpe = ruido_filtrado(muestras, 2600, 1400, semilla) * envolvente(
        muestras, caida=0.012, forma=3.2)
    cuerpo = ruido_filtrado(muestras, 700, 400, semilla + 9) * envolvente(
        muestras, caida=0.02) * 0.6
    return (golpe + cuerpo) * nivel


def golpe_sello(nivel=0.95):
    """
    Sello contra el papel: madera seca y un sub que le da peso.

    El barrido descendente es lo que lo hace sonar a golpe y no a chasquido.
    """
    muestras = _n(1.6)
    t = np.arange(muestras) / SR
    sub = np.sin(2 * np.pi * (135 * np.exp(-t * 18) + 38) * t) * envolvente(
        muestras, caida=0.16, forma=2.0)
    madera = ruido_filtrado(muestras, 1500, 900, semilla=11) * envolvente(
        muestras, caida=0.035, forma=3.0)
    cola = ruido_filtrado(muestras, 300, 260, semilla=12) * envolvente(
        muestras, caida=0.55, forma=1.4) * 0.35
    return (sub * 0.9 + madera * 0.55 + cola) * nivel


def clac_papel(nivel=0.42, semilla=0):
    """Polaroid que cae sobre el corcho."""
    muestras = _n(0.35)
    cuerpo = ruido_filtrado(muestras, 1100, 800, semilla) * envolvente(
        muestras, caida=0.028, forma=3.0)
    chincheta = ruido_filtrado(muestras, 4200, 1800, semilla + 5) * envolvente(
        muestras, caida=0.010, forma=4.0) * 0.5
    return (cuerpo + chincheta) * nivel


def tecla(nivel=0.30, semilla=0):
    """Tipo de máquina de escribir: el martillo y el rebote metálico."""
    muestras = _n(0.16)
    martillo = ruido_filtrado(muestras, 1900, 1100, semilla) * envolvente(
        muestras, caida=0.014, forma=3.5)
    metal = ruido_filtrado(muestras, 5200, 1500, semilla + 7) * envolvente(
        muestras, caida=0.006, forma=4.5) * 0.45
    return (martillo + metal) * nivel


def riser(duracion, nivel=0.38):
    """Barrido ascendente de tensión, para mientras se traza el hilo."""
    muestras = _n(duracion)
    t = np.arange(muestras) / SR
    avance = (t / duracion) ** 1.7

    x = ruido_filtrado(muestras, 1, 1, semilla=21)  # base espectral
    rnd = np.random.default_rng(31)
    x = rnd.normal(0, 1, muestras)
    espectro = np.fft.rfft(x)
    frec = np.fft.rfftfreq(muestras, 1 / SR)
    # Barrido: se filtra por tramos y se cose, más barato que un filtro variable.
    salida = np.zeros(muestras)
    tramos = 24
    largo = muestras // tramos
    for i in range(tramos):
        centro = 260 + 3400 * (i / tramos) ** 1.6
        banda = np.exp(-((frec - centro) ** 2) / (2 * (centro * 0.55) ** 2))
        trozo = np.fft.irfft(espectro * banda, n=muestras)
        ini, fin = i * largo, min((i + 1) * largo, muestras)
        salida[ini:fin] = trozo[ini:fin]

    tono = np.sin(2 * np.pi * (110 + 260 * avance) * t) * 0.35
    return (salida * 0.9 + tono) * avance * nivel


def impacto(nivel=1.0, caida=1.1):
    """Golpe grave de cierre."""
    muestras = _n(2.2)
    t = np.arange(muestras) / SR
    sub = np.sin(2 * np.pi * (90 * np.exp(-t * 9) + 32) * t) * envolvente(
        muestras, caida=caida, forma=1.6)
    aire = ruido_filtrado(muestras, 420, 380, semilla=17) * envolvente(
        muestras, caida=0.35, forma=2.0) * 0.4
    return (sub + aire) * nivel


# ─── Mezcla ──────────────────────────────────────────────────────────────────


def construir_pista(eventos, duracion, nivel_drone=0.16):
    """
    Mezcla el colchón y la lista de eventos `(segundo, muestra_de_audio)`.

    Devuelve un array mono normalizado y con limitador suave.
    """
    total = _n(duracion)
    pista = np.zeros(total)
    pista += drone(duracion, nivel=nivel_drone)[:total]

    for segundo, sonido in eventos:
        inicio = _n(segundo)
        if inicio >= total:
            continue
        fin = min(total, inicio + len(sonido))
        pista[inicio:fin] += sonido[:fin - inicio]

    # Entrada y salida suaves para que no chasquee al empezar ni al cortar.
    subida, bajada = _n(0.5), _n(1.2)
    pista[:subida] *= np.linspace(0, 1, subida)
    pista[-bajada:] *= np.linspace(1, 0, bajada)

    # Limitador blando: tanh comprime los picos sin recortarlos en cuadrado.
    pico = np.max(np.abs(pista)) or 1.0
    return np.tanh(pista / pico * 1.5) * 0.89


def guardar_wav(pista, ruta, estereo=True):
    """Escribe la pista a WAV de 16 bits. En estéreo abre apenas la imagen."""
    mono = np.clip(pista, -1, 1)
    if estereo:
        # Un retardo mínimo en un canal da anchura sin descuadrar los golpes.
        retardo = _n(0.006)
        derecho = np.concatenate([np.zeros(retardo), mono])[:len(mono)]
        marco = np.stack([mono, derecho * 0.96], axis=1)
    else:
        marco = mono[:, None]

    datos = (marco * 32767).astype(np.int16)
    with wave.open(ruta, "wb") as f:
        f.setnchannels(datos.shape[1])
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(struct.pack(f"<{datos.size}h", *datos.flatten()))
    return ruta
