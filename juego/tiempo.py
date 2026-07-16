"""Reloj de la abadía: días y horas canónicas."""
from __future__ import annotations

from . import config as C


class Reloj:
    def __init__(self) -> None:
        self.dia = 1
        self.franja = 0            # índice en C.HORAS
        self.t = 0.0               # segundos dentro de la franja
        self.fin_del_juego = False

    # ------------------------------------------------------------------ #
    def actualizar(self, dt: float) -> bool:
        """Avanza el tiempo. Devuelve True si cambió de franja."""
        self.t += dt
        if self.t >= C.SEGUNDOS_POR_FRANJA:
            self.t = 0.0
            self.franja += 1
            if self.franja >= len(C.HORAS):
                self.franja = 0
                self.dia += 1
                if self.dia > C.DIAS_TOTALES:
                    self.dia = C.DIAS_TOTALES
                    self.fin_del_juego = True
            return True
        return False

    # ------------------------------------------------------------------ #
    @property
    def datos(self):
        return C.HORAS[self.franja]

    @property
    def clave(self) -> str:
        return self.datos[0]

    @property
    def nombre(self) -> str:
        return self.datos[1]

    @property
    def es_noche(self) -> bool:
        return self.datos[2]

    @property
    def es_servicio(self) -> bool:
        return self.datos[3]

    @property
    def zona_requerida(self):
        return self.datos[4]

    @property
    def progreso(self) -> float:
        return self.t / C.SEGUNDOS_POR_FRANJA

    def hora_texto(self) -> str:
        return f"Día {self.dia} · {self.nombre}"

    # Oscuridad objetivo [0..1] según la franja (para la iluminación).
    def oscuridad(self) -> float:
        if self.clave == "noche" or self.clave == "maitines":
            return 0.82
        if self.clave in ("laudes", "completas"):
            return 0.5
        if self.clave in ("visperas",):
            return 0.28
        return 0.0
