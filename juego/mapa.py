"""Mapa de la abadía en 3 plantas conectadas por escaleras.

- Planta 0 (baja): iglesia, claustro, refectorio, cocina, celdas, enfermería,
  sala capitular, cripta y la entrada con la escalera al scriptorium.
- Planta 1 (scriptorium): la gran sala de copistas con la mesa del pergamino.
- Planta 2 (biblioteca): el laberinto a oscuras y la sala del espejo.

Cada planta es una rejilla independiente; las escaleras (`ESCALERA`) enlazan
posiciones entre plantas. No se copia la geometría binaria del original
(propiedad de Opera Soft): se reconstruye una planta fiel en espíritu.
"""
from __future__ import annotations

from dataclasses import dataclass

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


class Planta:
    """Una planta de la abadía: rejilla de tipos y zonas."""

    def __init__(self, ancho: int, alto: int) -> None:
        self.ancho = ancho
        self.alto = alto
        self.tiles = [[C.VACIO] * ancho for _ in range(alto)]
        self.zonas = [["claustro"] * ancho for _ in range(alto)]
        self.estancias: dict[str, Estancia] = {}
        self.anclas: dict[str, tuple[int, int]] = {}
        self.luces: list[tuple[int, int, tuple, int]] = []   # (gx,gy,color,radio)
        self.oscura = False

    def add_luz(self, gx, gy, color=(255, 170, 70), radio=150) -> None:
        self.luces.append((gx, gy, color, radio))

    # ------------------------------------------------------------------ #
    def add_estancia(self, e: Estancia) -> None:
        self.estancias[e.clave] = e
        for gy in range(e.y, e.y + e.h):
            for gx in range(e.x, e.x + e.w):
                if not self.dentro(gx, gy):
                    continue
                borde = gx in (e.x, e.x + e.w - 1) or gy in (e.y, e.y + e.h - 1)
                self.tiles[gy][gx] = C.MURO if borde else C.SUELO
                self.zonas[gy][gx] = e.zona
        self.anclas[e.clave] = e.centro

    def pasillo(self, a: tuple[int, int], b: tuple[int, int], zona="claustro") -> None:
        (ax, ay), (bx, by) = a, b
        for gx in range(min(ax, bx), max(ax, bx) + 1):
            self._tallar(gx, ay, zona)
        for gy in range(min(ay, by), max(ay, by) + 1):
            self._tallar(bx, gy, zona)

    def _tallar(self, gx: int, gy: int, zona: str) -> None:
        if not self.dentro(gx, gy):
            return
        t = self.tiles[gy][gx]
        if t == C.MURO:
            self.tiles[gy][gx] = C.PUERTA
        elif t == C.VACIO:
            self.tiles[gy][gx] = C.SUELO
            self.zonas[gy][gx] = zona

    def poner(self, gx: int, gy: int, tipo: int) -> None:
        if self.dentro(gx, gy):
            self.tiles[gy][gx] = tipo

    # ------------------------------------------------------------------ #
    def dentro(self, gx: int, gy: int) -> bool:
        return 0 <= gx < self.ancho and 0 <= gy < self.alto

    def tipo(self, gx: int, gy: int) -> int:
        return self.tiles[gy][gx] if self.dentro(int(gx), int(gy)) else C.VACIO

    def zona(self, gx: int, gy: int) -> str:
        return self.zonas[gy][gx] if self.dentro(int(gx), int(gy)) else "claustro"

    def transitable(self, gx: int, gy: int) -> bool:
        return self.tipo(int(gx), int(gy)) in C.TRANSITABLES

    def transitable_punto(self, fx: float, fy: float, radio: float = 0.28) -> bool:
        for dx in (-radio, radio):
            for dy in (-radio, radio):
                if not self.transitable(int(fx + dx), int(fy + dy)):
                    return False
        return True

    def ancla(self, clave: str) -> tuple[float, float]:
        gx, gy = self.anclas.get(clave, (self.ancho // 2, self.alto // 2))
        return gx + 0.5, gy + 0.5


class Mapa:
    """Contenedor de las 3 plantas y las escaleras que las conectan."""

    def __init__(self) -> None:
        self.plantas = [self._construir_baja(),
                        self._construir_scriptorium(),
                        self._construir_biblioteca()]
        self.plantas[C.PLANTA_BIBLIOTECA].oscura = True
        # Escaleras: (planta, gx, gy) -> (planta_destino, gx, gy)
        self.escaleras: dict[tuple[int, int, int], tuple[int, int, int]] = {}
        self._conectar_escaleras()
        self._verificar_conexidad()

    def planta(self, i: int) -> Planta:
        return self.plantas[i]

    # ------------------------------------------------------------------ #
    def _verificar_conexidad(self) -> None:
        """Garantiza que todo punto clave es alcanzable andando desde su escalera.

        Un decorado o tabique mal colocado puede sellar una estancia sin que
        nada falle en apariencia; esta comprobación convierte ese error
        silencioso en una excepción clara al arrancar.
        """
        requisitos = {
            C.PLANTA_BAJA: ((20, 34), ["iglesia", "claustro", "refectorio", "cocina",
                                       "capitular", "enfermeria", "celda_abad", "celdas",
                                       "celda_guillermo", "cripta", "entrada", "altar"]),
            C.PLANTA_SCRIPTORIUM: ((4, 4), ["scriptorium", "mesa_pergamino", "mesa_libro",
                                            "mesa_malaquias"]),
            C.PLANTA_BIBLIOTECA: ((4, 4), ["biblioteca", "espejo", "entrada_espejo",
                                           "sala_iluminada"]),
        }
        fallos = []
        for idx, (origen, anclas) in requisitos.items():
            p = self.plantas[idx]
            alcanzables = self._bfs(p, origen)
            for clave in anclas:
                gx, gy = p.anclas[clave]
                if (int(gx), int(gy)) not in alcanzables:
                    fallos.append(f"{C.NOMBRE_PLANTA[idx]}:{clave}")
            for (pl, gx, gy) in self.escaleras:
                if pl == idx and (gx, gy) not in alcanzables:
                    fallos.append(f"{C.NOMBRE_PLANTA[idx]}:escalera({gx},{gy})")
        if fallos:
            raise RuntimeError("Mapa inconexo; puntos inalcanzables: " + ", ".join(fallos))

    @staticmethod
    def _bfs(p: Planta, origen: tuple[int, int]) -> set[tuple[int, int]]:
        vistos = {origen}
        cola = [origen]
        while cola:
            x, y = cola.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in vistos and p.transitable(*n):
                    vistos.add(n)
                    cola.append(n)
        return vistos

    # ------------------------------------------------------------------ #
    def _construir_baja(self) -> Planta:
        p = Planta(46, 42)
        p.add_estancia(Estancia("iglesia", "iglesia", 2, 2, 14, 11))
        p.add_estancia(Estancia("claustro", "claustro", 18, 4, 12, 12))
        p.add_estancia(Estancia("refectorio", "refectorio", 2, 15, 12, 8))
        p.add_estancia(Estancia("cocina", "cocina", 2, 25, 9, 6))
        p.add_estancia(Estancia("capitular", "capitular", 18, 19, 10, 7))
        p.add_estancia(Estancia("enfermeria", "enfermeria", 32, 3, 11, 8))
        p.add_estancia(Estancia("celda_abad", "celda", 32, 13, 6, 5))
        p.add_estancia(Estancia("celdas", "celda", 30, 20, 14, 6))
        p.add_estancia(Estancia("celda_guillermo", "celda", 32, 28, 7, 5))
        p.add_estancia(Estancia("cripta", "cripta", 2, 33, 9, 6))
        p.add_estancia(Estancia("entrada", "claustro", 15, 30, 8, 7))

        p.pasillo(p.anclas["iglesia"], p.anclas["claustro"])
        p.pasillo(p.anclas["claustro"], p.anclas["enfermeria"])
        p.pasillo(p.anclas["iglesia"], p.anclas["refectorio"])
        p.pasillo(p.anclas["refectorio"], p.anclas["cocina"])
        p.pasillo(p.anclas["claustro"], p.anclas["capitular"])
        p.pasillo(p.anclas["claustro"], p.anclas["celda_abad"])
        p.pasillo(p.anclas["celda_abad"], p.anclas["celdas"])
        p.pasillo(p.anclas["capitular"], p.anclas["celdas"])
        p.pasillo(p.anclas["celdas"], p.anclas["celda_guillermo"])
        p.pasillo(p.anclas["cocina"], p.anclas["cripta"])
        p.pasillo(p.anclas["capitular"], p.anclas["entrada"])
        p.pasillo(p.anclas["cripta"], p.anclas["entrada"])

        ig = p.estancias["iglesia"]
        p.poner(ig.x + ig.w // 2, ig.y + 1, C.ALTAR)
        p.anclas["altar"] = (ig.x + ig.w // 2, ig.y + 2)
        # Antorchas de pared y velas del altar.
        p.add_luz(ig.x + ig.w // 2, ig.y + 1, (255, 210, 120), 170)
        p.add_luz(ig.x + 2, ig.y + 2, (255, 160, 60), 120)
        p.add_luz(ig.x + ig.w - 3, ig.y + 2, (255, 160, 60), 120)
        cl = p.estancias["claustro"]
        p.add_luz(cl.x + 2, cl.y + 2, (255, 160, 60), 120)
        p.add_luz(cl.x + cl.w - 3, cl.y + cl.h - 3, (255, 160, 60), 120)
        re = p.estancias["refectorio"]
        p.add_luz(re.x + 2, re.y + 2, (255, 165, 70), 120)
        co = p.estancias["cocina"]
        p.add_luz(co.x + 2, co.y + 2, (255, 140, 50), 110)
        return p

    def _construir_scriptorium(self) -> Planta:
        p = Planta(26, 22)
        p.add_estancia(Estancia("scriptorium", "scriptorium", 2, 2, 22, 16))
        # Mesas de copista
        for mx in range(5, 22, 4):
            p.poner(mx, 6, C.MESA)
            p.poner(mx, 11, C.MESA)
        p.anclas["mesa_pergamino"] = (7, 7)
        p.anclas["mesa_libro"] = (9, 7)
        p.anclas["mesa_malaquias"] = (19, 12)
        p.add_luz(4, 4, (255, 170, 70), 140)
        p.add_luz(21, 4, (255, 170, 70), 140)
        p.add_luz(12, 15, (255, 160, 60), 130)
        return p

    def _construir_biblioteca(self) -> Planta:
        p = Planta(30, 26)
        p.add_estancia(Estancia("biblioteca", "biblioteca", 2, 2, 26, 22))
        b = p.estancias["biblioteca"]
        # Tabiques del laberinto
        tabiques = [(6, 3, "v", 8), (9, 6, "h", 6), (13, 3, "v", 9),
                    (5, 12, "h", 7), (16, 8, "v", 10), (20, 4, "v", 12),
                    (10, 16, "h", 9), (23, 10, "h", 5)]
        for mx, my, orient, largo in tabiques:
            for i in range(largo):
                gx = mx + (i if orient == "h" else 0)
                gy = my + (i if orient == "v" else 0)
                if p.dentro(gx, gy) and p.tiles[gy][gx] == C.SUELO:
                    p.tiles[gy][gx] = C.MURO
        # Huecos para que sea transitable
        for gx, gy in [(6, 8), (11, 6), (13, 9), (8, 12), (16, 14),
                       (20, 10), (14, 16), (23, 12), (18, 18)]:
            p.poner(gx, gy, C.SUELO)
        # Sala del espejo (esquina) y sala iluminada.
        # El espejo decora la pared norte; la entrada es LATERAL para que el
        # decorado (no transitable) nunca bloquee la única puerta.
        p.add_estancia(Estancia("sala_espejo", "espejo", 22, 18, 6, 6))
        esp = p.estancias["sala_espejo"]
        p.poner(esp.x + esp.w // 2, esp.y + 1, C.ESPEJO)
        p.anclas["espejo"] = (esp.x + esp.w // 2, esp.y + 2)        # punto de interacción
        p.anclas["entrada_espejo"] = (esp.x + 1, esp.y + 3)         # acceso lateral
        p.add_estancia(Estancia("sala_iluminada", "espejo", 2, 18, 6, 6))
        p.anclas["sala_iluminada"] = p.estancias["sala_iluminada"].centro
        p.pasillo(p.anclas["biblioteca"], p.anclas["entrada_espejo"], "biblioteca")
        p.pasillo(p.anclas["biblioteca"], p.anclas["sala_iluminada"], "biblioteca")
        # La sala del espejo y la iluminada tienen luz propia (fría/dorada).
        p.add_luz(esp.x + esp.w // 2, esp.y + 2, (150, 190, 255), 150)
        sil = p.estancias["sala_iluminada"]
        p.add_luz(sil.x + sil.w // 2, sil.y + sil.h // 2, (255, 220, 150), 150)
        return p

    # ------------------------------------------------------------------ #
    def _conectar_escaleras(self) -> None:
        # Baja (entrada) <-> Scriptorium
        b = self.plantas[C.PLANTA_BAJA]
        s = self.plantas[C.PLANTA_SCRIPTORIUM]
        lib = self.plantas[C.PLANTA_BIBLIOTECA]

        e_baja = (20, 34)
        e_scr_abajo = (4, 4)
        e_scr_arriba = (22, 4)
        e_lib = (4, 4)

        b.poner(*e_baja, C.ESCALERA)
        b.anclas["escalera_arriba"] = e_baja
        s.poner(*e_scr_abajo, C.ESCALERA)
        s.poner(*e_scr_arriba, C.ESCALERA)
        lib.poner(*e_lib, C.ESCALERA)

        self._enlazar((C.PLANTA_BAJA, *e_baja), (C.PLANTA_SCRIPTORIUM, *e_scr_abajo))
        self._enlazar((C.PLANTA_SCRIPTORIUM, *e_scr_arriba), (C.PLANTA_BIBLIOTECA, *e_lib))

    def _enlazar(self, a, b) -> None:
        self.escaleras[a] = b
        self.escaleras[b] = a

    def escalera_en(self, planta: int, gx: int, gy: int):
        return self.escaleras.get((planta, int(gx), int(gy)))
