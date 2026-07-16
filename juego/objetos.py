"""Los 8 objetos del juego, con su posición, planta y función.

Orden y funciones tomados del original (enum `ObjetosJuego` en ibaca y
`Item.js` en ultrabolido).
"""
from __future__ import annotations

from . import config as C


class Objeto:
    def __init__(self, clave, nombre, icono, bit, planta=0, pos=(0, 0),
                 oculto=False, portador=None) -> None:
        self.clave = clave
        self.nombre = nombre
        self.icono = icono
        self.bit = bit
        self.planta = planta
        self.gx, self.gy = pos
        self.oculto = oculto        # no está en el mapa (aún no aparece)
        self.portador = portador    # None | "guillermo" | "adso"

    @property
    def en_suelo(self) -> bool:
        return not self.oculto and self.portador is None

    def colocar(self, planta, gx, gy) -> None:
        self.planta = planta
        self.gx, self.gy = gx, gy
        self.oculto = False
        self.portador = None


def construir_objetos(mapa) -> dict[str, Objeto]:
    """Crea los 8 objetos en sus posiciones iniciales."""
    scr = mapa.planta(C.PLANTA_SCRIPTORIUM)
    baja = mapa.planta(C.PLANTA_BAJA)

    mp = scr.anclas["mesa_pergamino"]
    ml = scr.anclas["mesa_libro"]
    enf = baja.anclas["enfermeria"]

    objs = {
        "libro": Objeto("libro", "El libro (Coena Cipriani)", "L", C.OBJ_LIBRO,
                        C.PLANTA_SCRIPTORIUM, ml),
        "guantes": Objeto("guantes", "Guantes", "G", C.OBJ_GUANTES,
                          C.PLANTA_BAJA, enf),
        "gafas": Objeto("gafas", "Gafas", "O", C.OBJ_GAFAS, portador="guillermo"),
        "pergamino": Objeto("pergamino", "Manuscrito de Venancio", "P",
                            C.OBJ_PERGAMINO, C.PLANTA_SCRIPTORIUM, mp),
        "llave1": Objeto("llave1", "Llave del altar", "1", C.OBJ_LLAVE1, oculto=True),
        "llave2": Objeto("llave2", "Llave de Malaquías", "2", C.OBJ_LLAVE2, oculto=True),
        "llave3": Objeto("llave3", "Llave del pasadizo", "3", C.OBJ_LLAVE3,
                         portador="adso"),
        "lampara": Objeto("lampara", "Lámpara de aceite", "F", C.OBJ_LAMPARA, oculto=True),
    }
    return objs
