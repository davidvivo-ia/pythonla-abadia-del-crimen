"""Personajes: Guillermo, Adso y los 6 monjes con IA por horarios.

Roster y roles tomados del original (8 personajes, orden fijo):
Guillermo, Adso, Malaquías, Abad, Berengario, Severino, Jorge, Bernardo.
"""
from __future__ import annotations

import math

from . import config as C
from .pathfinding import a_estrella


class Entidad:
    def __init__(self, x, y, planta, color, nombre="") -> None:
        self.x = float(x)
        self.y = float(y)
        self.planta = planta
        self.color = color
        self.nombre = nombre
        self.dir_x, self.dir_y = 0.0, 1.0
        self.velocidad = 0.0
        self.paso = 0.0

    def _mover(self, planta, dx, dy) -> None:
        x0, y0 = self.x, self.y
        if dx and planta.transitable_punto(self.x + dx, self.y):
            self.x += dx
        if dy and planta.transitable_punto(self.x, self.y + dy):
            self.y += dy
        # La velocidad refleja el desplazamiento REAL (contra un muro = 0).
        mag = math.hypot(self.x - x0, self.y - y0)
        self.velocidad = mag
        if mag > 1e-4:
            self.dir_x, self.dir_y = (self.x - x0) / mag, (self.y - y0) / mag
            self.paso += mag * 8.0

    @property
    def tile(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


class Guillermo(Entidad):
    def __init__(self, x, y, planta=0) -> None:
        super().__init__(x, y, planta, C.TINTA, "Guillermo")

    def actualizar(self, planta, entrada, dt) -> None:
        ix, iy = entrada
        mag = math.hypot(ix, iy)
        if mag > 1e-4:
            v = C.VEL_GUILLERMO * dt
            self._mover(planta, ix / mag * v, iy / mag * v)
        else:
            self.velocidad = 0.0


class Adso(Entidad):
    def __init__(self, x, y, planta=0) -> None:
        super().__init__(x, y, planta, (60, 70, 120), "Adso")

    def actualizar(self, planta, maestro, entrada_manual, dt) -> None:
        # Adso siempre está en la planta de Guillermo.
        if self.planta != maestro.planta:
            self.planta = maestro.planta
            self.x, self.y = maestro.x, maestro.y
        if entrada_manual is not None:
            ix, iy = entrada_manual
            mag = math.hypot(ix, iy)
            if mag > 1e-4:
                v = C.VEL_ADSO * dt
                self._mover(planta, ix / mag * v, iy / mag * v)
            else:
                self.velocidad = 0.0
            return
        dx, dy = maestro.x - self.x, maestro.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1.4:
            v = C.VEL_ADSO * dt
            self._mover(planta, dx / dist * v, dy / dist * v)
        else:
            self.velocidad = 0.0


class Monje(Entidad):
    """Monje con IA: se dirige a la estancia que le toca según la hora."""

    def __init__(self, x, y, planta, color, nombre, home, frases=()) -> None:
        super().__init__(x, y, planta, color, nombre)
        self.home = home              # ancla de su celda/zona
        self.frases = list(frases) or [""]
        self.frase_base = self.frases[0]
        self._i_frase = 0
        self.vivo = True
        self.activo = True
        self.ruta: list[tuple[int, int]] = []
        self.objetivo_ancla = home
        self.espera = 0.0

    def frase(self) -> str:
        """Siguiente frase del monje (van rotando para no repetirse)."""
        f = self.frases[self._i_frase % len(self.frases)]
        self._i_frase += 1
        return f

    # ------------------------------------------------------------------ #
    def objetivo_para(self, reloj) -> str:
        """Ancla destino según el horario (solo en planta baja)."""
        if self.planta != C.PLANTA_BAJA:
            return self.home
        m = reloj.momento
        if m in C.MOMENTO_IGLESIA:
            return "iglesia"
        if m in C.MOMENTO_REFECTORIO:
            return "refectorio"
        if m in C.MOMENTO_CELDA:
            return self.home
        return self.home

    def actualizar(self, mapa, reloj, dt, rng) -> None:
        if not (self.vivo and self.activo):
            self.velocidad = 0.0
            return
        planta = mapa.planta(self.planta)
        destino = self.objetivo_para(reloj)
        if destino != self.objetivo_ancla:
            self.objetivo_ancla = destino
            self.ruta = []

        if not self.ruta:
            self.espera -= dt
            if self.espera <= 0:
                self._planear(planta, rng)
                self.espera = rng.uniform(0.3, 1.2)
            self.velocidad = 0.0
            return

        meta = self.ruta[0]
        cx, cy = meta[0] + 0.5, meta[1] + 0.5
        dx, dy = cx - self.x, cy - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.12:
            self.ruta.pop(0)
            return
        v = C.VEL_MONJE * dt
        if v >= dist:
            self.x, self.y = cx, cy
            self.ruta.pop(0)
        else:
            self._mover(planta, dx / dist * v, dy / dist * v)

    def _planear(self, planta, rng) -> None:
        # Objetivo aproximado: el ancla + deriva aleatoria por la estancia.
        ax, ay = planta.anclas.get(self.objetivo_ancla, (planta.ancho // 2, planta.alto // 2))
        for _ in range(10):
            gx = ax + rng.randint(-2, 2)
            gy = ay + rng.randint(-2, 2)
            if planta.transitable(gx, gy):
                self.ruta = a_estrella(planta, self.tile, (gx, gy))
                if self.ruta:
                    return

    def teleport(self, planta, gx, gy, home=None) -> None:
        self.planta = planta
        self.x, self.y = gx + 0.5, gy + 0.5
        self.ruta = []
        if home is not None:            # nueva zona de deambulación
            self.home = home
            self.objetivo_ancla = home


# Definición de los monjes (además de Guillermo y Adso).
#   clave, nombre, color, planta inicial, ancla home, frases (rotan al hablar)
DEF_MONJES = [
    ("abad",       "Abad",       (60, 50, 90),  C.PLANTA_BAJA, "iglesia", (
        "BIENVENIDO A ESTA ABADIA, HERMANO.",
        "DEBEIS RESPETAR MIS ORDENES Y LAS DE LA ABADIA. ASISTIR A LOS OFICIOS Y A LA COMIDA.",
        "DE NOCHE DEBEIS ESTAR EN VUESTRA CELDA.")),
    ("severino",   "Severino",   (60, 90, 80),  C.PLANTA_BAJA, "enfermeria", (
        "VENERABLE HERMANO, SOY SEVERINO, EL ENCARGADO DEL HOSPITAL.",
        "EN ESTA ABADIA SUCEDEN COSAS MUY EXTRAÑAS. ALGUIEN NO QUIERE QUE LOS MONJES DECIDAN POR SI SOLOS LO QUE DEBEN SABER.",
        "ESCUCHAD HERMANO, HE ENCONTRADO UN EXTRAÑO LIBRO EN MI CELDA.")),
    ("malaquias",  "Malaquías",  (70, 60, 50),  C.PLANTA_SCRIPTORIUM, "scriptorium", (
        "LO SIENTO, VENERABLE HERMANO, NO PODEIS SUBIR A LA BIBLIOTECA.",
        "SI LO DESEAIS, BERENGARIO OS MOSTRARA EL SCRIPTORIUM.",
        "DEBEIS ABANDONAR EL EDIFICIO, HERMANO.")),
    ("berengario", "Berengario", (90, 70, 60),  C.PLANTA_SCRIPTORIUM, "scriptorium", (
        "AQUI TRABAJAN LOS MEJORES COPISTAS DE OCCIDENTE.",
        "AQUI TRABAJABA VENANCIO.",
        "DEJAD EL MANUSCRITO DE VENANCIO O ADVERTIRE AL ABAD.")),
    ("jorge",      "Jorge",      (40, 38, 34),  C.PLANTA_BIBLIOTECA, "sala_espejo", (
        "SED BIENVENIDO, VENERABLE HERMANO; Y ESCUCHAD LO QUE OS DIGO.",
        "LAS VIAS DEL ANTICRISTO SON LENTAS Y TORTUOSAS. NO DESPERDICIEIS LOS ULTIMOS DIAS.")),
    ("bernardo",   "Bernardo Gui", (110, 40, 40), C.PLANTA_BAJA, "claustro", (
        "HA LLEGADO BERNARDO, DEBEIS ABANDONAR LA INVESTIGACION.",
        "DADME EL MANUSCRITO, FRAY GUILLERMO.")),
]
