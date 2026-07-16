"""Construcción del mapa de la abadía: estancias, muros, puertas y zonas.

El plano se genera a partir de una lista de estancias rectangulares que se
conectan mediante pasillos en forma de L. Cada tile guarda su tipo (suelo,
muro, puerta...) y la zona a la que pertenece (para el color y las reglas de
juego). Así el mapa queda siempre conexo y es fácil de reconfigurar.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config as C


@dataclass
class Estancia:
    clave: str
    zona: str
    x: int
    y: int
    w: int
    h: int

    @property
    def centro(self) -> tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2


# Plano de la abadía (inspirado en el edificio de la novela de Eco).
ESTANCIAS = [
    Estancia("iglesia",     "iglesia",     2,  2, 13, 11),
    Estancia("claustro",    "claustro",   17,  4, 13, 13),
    Estancia("scriptorium", "scriptorium",33,  2, 11,  9),
    Estancia("biblioteca",  "biblioteca", 33, 13, 13, 15),
    Estancia("refectorio",  "refectorio",  2, 15, 12,  8),
    Estancia("cocina",      "cocina",      2, 25,  9,  6),
    Estancia("capitular",   "capitular",  17, 20, 11,  7),
    Estancia("enfermeria",  "enfermeria", 14, 29, 10,  7),
    Estancia("celdas",      "celda",      30, 30, 15,  6),
    Estancia("cripta",      "cripta",      2, 33,  9,  6),
    Estancia("patio",       "patio",      17, 29,  0,  0),  # placeholder (sin uso)
]

# Conexiones entre centros de estancias (por clave).
CONEXIONES = [
    ("iglesia", "claustro"),
    ("claustro", "scriptorium"),
    ("scriptorium", "biblioteca"),
    ("claustro", "biblioteca"),
    ("iglesia", "refectorio"),
    ("refectorio", "cocina"),
    ("claustro", "capitular"),
    ("capitular", "enfermeria"),
    ("enfermeria", "celdas"),
    ("cocina", "cripta"),
    ("refectorio", "capitular"),
]


class Mapa:
    """Rejilla de la abadía con tipos de tile y zonas."""

    def __init__(self) -> None:
        self.ancho = 48
        self.alto = 42
        self.tiles = [[C.VACIO] * self.ancho for _ in range(self.alto)]
        self.zonas = [["claustro"] * self.ancho for _ in range(self.alto)]
        self.estancias = {e.clave: e for e in ESTANCIAS if e.w > 0 and e.h > 0}
        self.decor: dict[tuple[int, int], str] = {}  # (x,y) -> tipo decorado
        self._construir()

    # ------------------------------------------------------------------ #
    def _construir(self) -> None:
        for e in self.estancias.values():
            self._tallar_estancia(e)
        for a, b in CONEXIONES:
            if a in self.estancias and b in self.estancias:
                self._pasillo(self.estancias[a].centro, self.estancias[b].centro)
        self._laberinto_biblioteca()
        self._decorados()

    def _tallar_estancia(self, e: Estancia) -> None:
        for gy in range(e.y, e.y + e.h):
            for gx in range(e.x, e.x + e.w):
                if not self._dentro(gx, gy):
                    continue
                borde = (gx in (e.x, e.x + e.w - 1) or gy in (e.y, e.y + e.h - 1))
                self.tiles[gy][gx] = C.MURO if borde else C.SUELO
                self.zonas[gy][gx] = e.zona

    def _pasillo(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        (ax, ay), (bx, by) = a, b
        # Tramo horizontal y luego vertical (L)
        for gx in range(min(ax, bx), max(ax, bx) + 1):
            self._tallar_pasillo(gx, ay)
        for gy in range(min(ay, by), max(ay, by) + 1):
            self._tallar_pasillo(bx, gy)

    def _tallar_pasillo(self, gx: int, gy: int) -> None:
        if not self._dentro(gx, gy):
            return
        t = self.tiles[gy][gx]
        if t == C.MURO:
            self.tiles[gy][gx] = C.PUERTA
        elif t == C.VACIO:
            self.tiles[gy][gx] = C.SUELO
            self.zonas[gy][gx] = "claustro"

    def _laberinto_biblioteca(self) -> None:
        """Añade tabiques internos a la biblioteca (el famoso laberinto)."""
        b = self.estancias["biblioteca"]
        muros_int = [
            (b.x + 3, b.y + 2, "v", 5), (b.x + 6, b.y + 4, "h", 4),
            (b.x + 9, b.y + 2, "v", 6), (b.x + 2, b.y + 7, "h", 4),
            (b.x + 6, b.y + 9, "v", 4), (b.x + 3, b.y + 11, "h", 6),
        ]
        for mx, my, orient, largo in muros_int:
            for i in range(largo):
                gx = mx + (i if orient == "h" else 0)
                gy = my + (i if orient == "v" else 0)
                if self._dentro(gx, gy) and self.tiles[gy][gx] == C.SUELO:
                    self.tiles[gy][gx] = C.MURO
                    self.zonas[gy][gx] = "biblioteca"
        # Reabrimos huecos para que siga siendo transitable
        for gx, gy in [(b.x + 3, b.y + 6), (b.x + 6, b.y + 7), (b.x + 9, b.y + 7),
                       (b.x + 4, b.y + 11), (b.x + 8, b.y + 4)]:
            if self._dentro(gx, gy):
                self.tiles[gy][gx] = C.SUELO
                self.zonas[gy][gx] = "biblioteca"

    def _decorados(self) -> None:
        ig = self.estancias["iglesia"]
        self._poner(ig.x + ig.w // 2, ig.y + 1, C.ALTAR)
        # Camas en las celdas
        cel = self.estancias["celdas"]
        for gx in range(cel.x + 2, cel.x + cel.w - 1, 3):
            self._poner(gx, cel.y + 2, C.CAMA)

    def _poner(self, gx: int, gy: int, tipo: int) -> None:
        if self._dentro(gx, gy) and self.tiles[gy][gx] in (C.SUELO, C.MURO):
            self.tiles[gy][gx] = tipo

    # ------------------------------------------------------------------ #
    def _dentro(self, gx: int, gy: int) -> bool:
        return 0 <= gx < self.ancho and 0 <= gy < self.alto

    def tipo(self, gx: int, gy: int) -> int:
        if not self._dentro(gx, gy):
            return C.VACIO
        return self.tiles[gy][gx]

    def zona(self, gx: int, gy: int) -> str:
        if not self._dentro(gx, gy):
            return "claustro"
        return self.zonas[gy][gx]

    def transitable(self, gx: int, gy: int) -> bool:
        return self.tipo(int(gx), int(gy)) in C.TRANSITABLES

    def transitable_punto(self, fx: float, fy: float, radio: float = 0.28) -> bool:
        """Comprueba las cuatro esquinas de un círculo de colisión."""
        for dx in (-radio, radio):
            for dy in (-radio, radio):
                if not self.transitable(int(fx + dx), int(fy + dy)):
                    return False
        return True

    def centro_estancia(self, clave: str) -> tuple[float, float]:
        e = self.estancias[clave]
        return e.x + e.w / 2, e.y + e.h / 2

    def zona_de(self, clave: str) -> str:
        return self.estancias[clave].zona
