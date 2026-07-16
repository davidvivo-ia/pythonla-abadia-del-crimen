"""Configuración global: constantes canónicas, paleta y ajustes.

Los valores (horas canónicas, objetos, obsequium, guion) están tomados de la
ingeniería inversa del original (desensamblado de Manuel Abadía y los ports
Java de ibaca y JS de ultrabolido). Ver COMPARATIVA_Y_MEJORAS.md.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Ventana / motor
# --------------------------------------------------------------------------- #
TITULO = "La Abadía del Crimen — Edición 2026"
ANCHO, ALTO = 1280, 720
FPS = 60

TILE_W = 64
TILE_H = 32
ALTURA_MURO = 40

VEL_GUILLERMO = 4.2
VEL_ADSO = 4.6
VEL_MONJE = 2.6

# --------------------------------------------------------------------------- #
# Paleta (claroscuro medieval / pergamino)
# --------------------------------------------------------------------------- #
NEGRO       = (12, 10, 8)
PERGAMINO   = (222, 205, 165)
PERGAMINO_2 = (198, 178, 138)
TINTA       = (40, 30, 22)
ORO         = (198, 160, 74)
ORO_CLARO   = (230, 198, 120)
ROJO        = (150, 42, 38)
ROJO_SANGRE = (120, 24, 24)
VERDE       = (86, 110, 64)
AZUL_NOCHE  = (16, 20, 38)
GRIS_PIEDRA = (120, 116, 108)
GRIS_OSCURO = (70, 68, 64)
BLANCO      = (238, 232, 220)

COLORES_ZONA = {
    "claustro":   ((150, 146, 128), (120, 116, 100)),
    "iglesia":    ((120, 108, 132), (96, 84, 108)),
    "refectorio": ((160, 132, 96),  (130, 104, 72)),
    "cocina":     ((150, 120, 92),  (120, 92, 68)),
    "scriptorium":((146, 150, 120), (116, 120, 92)),
    "biblioteca": ((92, 82, 70),    (66, 58, 48)),
    "celda":      ((132, 128, 116), (104, 100, 90)),
    "capitular":  ((138, 128, 148), (108, 100, 118)),
    "enfermeria": ((120, 148, 132), (92, 118, 104)),
    "cripta":     ((80, 76, 88),    (56, 52, 64)),
    "espejo":     ((150, 120, 150), (110, 86, 110)),
}

# --------------------------------------------------------------------------- #
# Tipos de tile
# --------------------------------------------------------------------------- #
VACIO = 0
SUELO = 1
MURO  = 2
PUERTA = 3
ALTAR = 4
CAMA = 5
ESCALERA = 6      # transitable; conecta plantas
ESPEJO = 7        # decorado no transitable (la habitación del espejo)
MESA = 8          # decorado no transitable

TRANSITABLES = {SUELO, PUERTA, ESCALERA}

# --------------------------------------------------------------------------- #
# Plantas
# --------------------------------------------------------------------------- #
PLANTA_BAJA = 0
PLANTA_SCRIPTORIUM = 1
PLANTA_BIBLIOTECA = 2
NOMBRE_PLANTA = {0: "Abadía", 1: "Scriptorium", 2: "Biblioteca"}

# --------------------------------------------------------------------------- #
# Horas canónicas (momento del día). Orden del original.
# --------------------------------------------------------------------------- #
NOCHE, PRIMA, TERCIA, SEXTA, NONA, VISPERAS, COMPLETAS = range(7)
NOMBRE_MOMENTO = ["Noche", "Prima", "Tercia", "Sexta", "Nona", "Vísperas", "Completas"]

# Momentos que exigen estar en un sitio (para el obsequium):
MOMENTO_IGLESIA = {PRIMA, VISPERAS}     # oficios
MOMENTO_REFECTORIO = {SEXTA}            # comida
MOMENTO_CELDA = {COMPLETAS, NOCHE}      # dormir

# Tabla de duración de etapas del original: DURATION[dia-1][momento].
# (0 = en el original avanza por evento; aquí todos avanzan por tiempo.)
DURACION_ETAPAS = [
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    [0x00, 0x00, 0x05, 0x00, 0x05, 0x00, 0x00],
    [0x00, 0x00, 0x05, 0x00, 0x05, 0x00, 0x00],
    [0x0f, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00],
    [0x0f, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00],
    [0x0f, 0x00, 0x05, 0x00, 0x05, 0x00, 0x00],
    [0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
]

SEGUNDOS_POR_MOMENTO = 24.0   # duración real de cada momento
DIA_INICIAL = 1
MOMENTO_INICIAL = NONA
DIAS_TOTALES = 7

# --------------------------------------------------------------------------- #
# Objetos (bit -> clave). Orden del original.
# --------------------------------------------------------------------------- #
OBJ_LIBRO     = 0x80
OBJ_GUANTES   = 0x40
OBJ_GAFAS     = 0x20
OBJ_PERGAMINO = 0x10
OBJ_LLAVE1    = 0x08
OBJ_LLAVE2    = 0x04
OBJ_LLAVE3    = 0x02
OBJ_LAMPARA   = 0x01

# --------------------------------------------------------------------------- #
# Obsequium (0..31). Solo baja, de 2 en 2. A <0 -> expulsión.
# --------------------------------------------------------------------------- #
OBSEQUIUM_MAX = 31
OBSEQUIUM_PENALIZACION = 2

# Enigma del espejo
NUMEROS_ROMANOS = ["IXX", "XIX", "XXI"]

ARCHIVO_GUARDADO = "partida_abadia.json"
