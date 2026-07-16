"""Audio procedural opcional: campanas de la abadía generadas sin ficheros.

Si no hay `numpy` o el mezclador de audio falla, el juego funciona en silencio.
"""
from __future__ import annotations

import math


class Audio:
    def __init__(self) -> None:
        self.ok = False
        self.campana = None
        try:
            import numpy as np  # noqa: F401
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.campana = self._crear_campana()
            self.ok = self.campana is not None
        except Exception:
            self.ok = False

    def _crear_campana(self):
        try:
            import numpy as np
            import pygame
            sr = 44100
            dur = 1.6
            n = int(sr * dur)
            t = np.linspace(0, dur, n, endpoint=False)
            # Campana: fundamental + parciales inarmónicos con decaimiento.
            parciales = [(1.0, 1.0), (2.76, 0.6), (5.4, 0.35), (8.9, 0.2)]
            base = 220.0
            onda = np.zeros(n)
            for mult, amp in parciales:
                onda += amp * np.sin(2 * math.pi * base * mult * t)
            onda *= np.exp(-3.0 * t)                 # decaimiento
            onda /= np.max(np.abs(onda)) + 1e-9
            datos = (onda * 0.35 * 32767).astype(np.int16)
            estereo = np.column_stack((datos, datos))
            return pygame.sndarray.make_sound(np.ascontiguousarray(estereo))
        except Exception:
            return None

    def tocar_campana(self, veces: int = 1) -> None:
        if self.ok and self.campana:
            try:
                self.campana.play()
            except Exception:
                pass
