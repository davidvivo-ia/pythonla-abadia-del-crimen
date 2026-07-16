"""Códice: diario de detective (pistas descubiertas) y objetivo actual.

Registra los hallazgos de la investigación y calcula el objetivo vigente a
partir del estado de la partida — una capa de "immersive sim" moderna.
"""
from __future__ import annotations

from . import config as C


class Codex:
    def __init__(self) -> None:
        self.pistas: list[tuple[str, str]] = []   # (día·hora, texto)
        self._vistas: set[str] = set()

    def anotar(self, sello: str, texto: str) -> None:
        clave = texto[:40]
        if clave in self._vistas:
            return
        self._vistas.add(clave)
        self.pistas.append((sello, texto))
        self.pistas = self.pistas[-40:]

    # ------------------------------------------------------------------ #
    def objetivo(self, juego) -> str:
        """Texto del objetivo vigente según el progreso."""
        tiene = juego.tiene
        if juego.clima_resuelto:
            return "El misterio ha concluido."
        faltan = [n for k, n in (("guantes", "guantes"), ("gafas", "gafas"),
                                 ("pergamino", "el pergamino")) if not tiene(k)]
        if faltan:
            return "Reúne " + ", ".join(faltan) + " por la abadía."
        if juego.guillermo.planta != C.PLANTA_BIBLIOTECA:
            return "Sube por las escaleras hasta la biblioteca."
        if juego.reloj.dia < 6:
            return "Investiga; Jorge aguardará tras el espejo el 6º día."
        return "Enfréntate a Jorge en el espejo (¡lleva los guantes!)."

    def to_dict(self):
        return {"pistas": self.pistas, "vistas": list(self._vistas)}

    def from_dict(self, d) -> None:
        self.pistas = [tuple(p) for p in d.get("pistas", [])]
        self._vistas = set(d.get("vistas", []))
