"""Configuración global: constantes, paleta, horario canónico y ajustes."""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Ventana / motor
# --------------------------------------------------------------------------- #
TITULO = "La Abadía del Crimen — Edición 2026"
ANCHO, ALTO = 1280, 720
FPS = 60

# Tamaño del rombo isométrico (ancho x alto del tile en pantalla)
TILE_W = 64
TILE_H = 32
# Altura visual de una pared / bloque elevado en píxeles
ALTURA_MURO = 40

# Velocidad de las entidades en tiles por segundo
VEL_GUILLERMO = 4.2
VEL_ADSO = 4.6
VEL_MONJE = 2.6

# --------------------------------------------------------------------------- #
# Paleta cromática (estética pergamino / claroscuro medieval)
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

# Colores de suelo por zona (id_zona -> (color, color_borde))
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
    "patio":      ((96, 120, 78),   (74, 96, 58)),
    "cripta":     ((80, 76, 88),    (56, 52, 64)),
}

# --------------------------------------------------------------------------- #
# Tipos de tile del mapa
# --------------------------------------------------------------------------- #
VACIO = 0     # exterior / no dibujado
SUELO = 1
MURO  = 2
PUERTA = 3    # transitable
ALTAR = 4     # decorado no transitable
CAMA = 5      # decorado no transitable

TRANSITABLES = {SUELO, PUERTA}

# --------------------------------------------------------------------------- #
# Horario de horas canónicas
# --------------------------------------------------------------------------- #
# Cada franja: (clave, nombre, es_noche, es_servicio, zona_requerida)
#   es_servicio -> Guillermo debería estar en la iglesia
#   es_noche    -> vagar penaliza obsequium; se activa la iluminación nocturna
HORAS = [
    ("maitines",  "Maitines",  True,  False, None),
    ("laudes",    "Laudes",    True,  True,  "iglesia"),
    ("prima",     "Prima",     False, True,  "iglesia"),
    ("capitulo",  "Capítulo",  False, False, None),
    ("tercia",    "Tercia",    False, False, None),
    ("sexta",     "Sexta",     False, True,  "iglesia"),
    ("comida",    "Comida",    False, False, "refectorio"),
    ("nona",      "Nona",      False, False, None),
    ("visperas",  "Vísperas",  False, True,  "iglesia"),
    ("completas", "Completas", False, True,  "iglesia"),
    ("noche",     "Noche",     True,  False, "celda"),
]

# Segundos reales que dura cada franja horaria
SEGUNDOS_POR_FRANJA = 42.0
DIAS_TOTALES = 7

# --------------------------------------------------------------------------- #
# Obsequium (barra de obediencia)
# --------------------------------------------------------------------------- #
OBSEQUIUM_MAX = 100.0
# Drenajes por segundo según la infracción
DREN_FALTAR_SERVICIO = 5.0   # no estar en la iglesia durante un oficio
DREN_VAGAR_NOCHE     = 1.6   # deambular de noche fuera de la celda
DREN_ZONA_PROHIBIDA  = 3.2   # estar en la biblioteca sin permiso
REGEN_OBEDIENTE      = 2.4   # recompensa por cumplir el horario

# --------------------------------------------------------------------------- #
# Guardado
# --------------------------------------------------------------------------- #
ARCHIVO_GUARDADO = "partida_abadia.json"
