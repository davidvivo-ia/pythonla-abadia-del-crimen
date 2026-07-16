"""Entidades del juego: Guillermo, Adso y los monjes con IA."""
from __future__ import annotations

import math

from . import config as C
from .mapa import Mapa
from .pathfinding import a_estrella


class Entidad:
    """Base con posición flotante en la rejilla y colisión con deslizamiento."""

    def __init__(self, x: float, y: float, color, nombre: str = "") -> None:
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.nombre = nombre
        self.dir_x = 0.0
        self.dir_y = 1.0            # mirando "al frente"
        self.velocidad = 0.0        # magnitud actual (para animación)
        self.paso = 0.0             # fase de animación de balanceo

    # ------------------------------------------------------------------ #
    def _mover(self, mapa: Mapa, dx: float, dy: float) -> None:
        """Mueve aplicando colisión eje a eje (permite deslizarse por muros)."""
        if dx and mapa.transitable_punto(self.x + dx, self.y):
            self.x += dx
        if dy and mapa.transitable_punto(self.x, self.y + dy):
            self.y += dy
        mag = math.hypot(dx, dy)
        self.velocidad = mag
        if mag > 1e-4:
            self.dir_x, self.dir_y = dx / mag, dy / mag
            self.paso += mag * 8.0

    @property
    def tile(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


class Guillermo(Entidad):
    """Fray Guillermo de Occam — controlado por el jugador."""

    def __init__(self, x, y) -> None:
        super().__init__(x, y, C.TINTA, "Guillermo")

    def actualizar(self, mapa: Mapa, entrada: tuple[float, float], dt: float) -> None:
        ix, iy = entrada
        mag = math.hypot(ix, iy)
        if mag > 1e-4:
            ix, iy = ix / mag, iy / mag
            v = C.VEL_GUILLERMO * dt
            self._mover(mapa, ix * v, iy * v)
        else:
            self.velocidad = 0.0


class Adso(Entidad):
    """Adso de Melk — sigue a Guillermo salvo control manual."""

    def __init__(self, x, y) -> None:
        super().__init__(x, y, (60, 70, 120), "Adso")

    def actualizar(self, mapa: Mapa, objetivo: Entidad,
                   entrada_manual, dt: float) -> None:
        if entrada_manual is not None:
            ix, iy = entrada_manual
            mag = math.hypot(ix, iy)
            if mag > 1e-4:
                ix, iy = ix / mag, iy / mag
                v = C.VEL_ADSO * dt
                self._mover(mapa, ix * v, iy * v)
            else:
                self.velocidad = 0.0
            return

        # Seguimiento: mantiene una distancia prudente con el maestro.
        dx = objetivo.x - self.x
        dy = objetivo.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1.4:
            v = C.VEL_ADSO * dt
            self._mover(mapa, dx / dist * v, dy / dist * v)
        else:
            self.velocidad = 0.0


class Monje(Entidad):
    """Monje con IA: patrulla por su zona con rutas A*."""

    def __init__(self, x, y, color, nombre: str, zona_base: str) -> None:
        super().__init__(x, y, color, nombre)
        self.zona_base = zona_base
        self.ruta: list[tuple[int, int]] = []
        self.espera = 0.0
        self.frase = ""
        self.frase_t = 0.0

    def actualizar(self, mapa: Mapa, dt: float, rng) -> None:
        self.frase_t = max(0.0, self.frase_t - dt)
        if not self.ruta:
            self.espera -= dt
            if self.espera <= 0:
                self._nueva_meta(mapa, rng)
                self.espera = rng.uniform(0.4, 1.8)
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
            self._mover(mapa, dx / dist * v, dy / dist * v)

    def _nueva_meta(self, mapa: Mapa, rng) -> None:
        for _ in range(12):
            gx = rng.randint(0, mapa.ancho - 1)
            gy = rng.randint(0, mapa.alto - 1)
            if mapa.transitable(gx, gy):
                self.ruta = a_estrella(mapa, self.tile, (gx, gy))
                if self.ruta:
                    return

    def decir(self, texto: str) -> None:
        self.frase = texto
        self.frase_t = 3.2
