"""Reloj de la abadía: días (1-7) y los 7 momentos canónicos."""
from __future__ import annotations

from . import config as C


class Reloj:
    def __init__(self) -> None:
        self.dia = C.DIA_INICIAL
        self.momento = C.MOMENTO_INICIAL
        self.t = 0.0
        self.fin_del_juego = False

    # ------------------------------------------------------------------ #
    def actualizar(self, dt: float) -> bool:
        """Avanza el tiempo. Devuelve True si cambió de momento."""
        self.t += dt
        if self.t >= self.duracion_actual():
            self.t = 0.0
            return self.avanzar_momento()
        return False

    def avanzar_momento(self) -> bool:
        self.momento += 1
        if self.momento > C.COMPLETAS:
            self.momento = C.NOCHE
            self.dia += 1
            if self.dia > C.DIAS_TOTALES:
                self.dia = C.DIAS_TOTALES
                self.fin_del_juego = True
        return True

    def duracion_actual(self) -> float:
        """Segundos reales del momento actual (modula por la tabla original)."""
        base = C.SEGUNDOS_POR_MOMENTO
        etapa = C.DURACION_ETAPAS[min(self.dia - 1, 6)][self.momento]
        # Las etapas 'largas' del original (noche) duran algo más.
        factor = 1.4 if etapa >= 0x0f else (1.15 if etapa else 1.0)
        return base * factor

    # ------------------------------------------------------------------ #
    @property
    def nombre(self) -> str:
        return C.NOMBRE_MOMENTO[self.momento]

    @property
    def es_noche(self) -> bool:
        return self.momento in (C.NOCHE, C.COMPLETAS)

    @property
    def progreso(self) -> float:
        return min(1.0, self.t / self.duracion_actual())

    def hora_texto(self) -> str:
        return f"Día {self.dia} · {self.nombre}"

    def oscuridad(self) -> float:
        if self.momento == C.NOCHE:
            return 0.85
        if self.momento == C.COMPLETAS:
            return 0.55
        if self.momento == C.VISPERAS:
            return 0.25
        return 0.0
