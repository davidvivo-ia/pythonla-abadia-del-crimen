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
        """Texto del objetivo vigente según el horario y el progreso."""
        tiene = juego.tiene
        if juego.clima_resuelto:
            return "El misterio ha concluido."

        # 1) Obligación horaria en curso: es lo que cuesta obsequium.
        m = juego.reloj.momento
        if m in C.MOMENTO_IGLESIA:
            return f"{juego.reloj.nombre}: acude a la iglesia antes de que acabe."
        if m in C.MOMENTO_REFECTORIO:
            return "Sexta: ocupa tu sitio en el refectorio."
        if m in C.MOMENTO_CELDA:
            return f"{juego.reloj.nombre}: retírate a tu celda a dormir."

        # 2) Tiempo libre: progreso de la investigación.
        faltan = []
        if not tiene("guantes"):
            faltan.append("los guantes (enfermería)")
        if not tiene("pergamino"):
            faltan.append("el pergamino (scriptorium)")
        if not tiene("gafas"):
            if juego.objetos["gafas"].oculto:
                faltan.append("las gafas (reaparecen en la biblioteca el 5º día)")
            else:
                faltan.append("las gafas")
        if faltan:
            lista = ", ".join(faltan[:-1]) + (" y " if len(faltan) > 1 else "") + faltan[-1]
            return "Tiempo libre: consigue " + lista + "."
        if juego.objetos["lampara"].portador != "adso":
            return "Haz que Adso recoja la lámpara (cocina) para entrar en la biblioteca."
        if juego.reloj.dia < 6:
            return "Todo listo: Jorge aguardará tras el espejo desde el 6º día."
        if juego.guillermo.planta != C.PLANTA_BIBLIOTECA:
            return "Sube a la biblioteca y busca la sala del espejo."
        return "Enfréntate a Jorge en el espejo: ¡no te quites los guantes!"

    def to_dict(self):
        return {"pistas": self.pistas, "vistas": list(self._vistas)}

    def from_dict(self, d) -> None:
        self.pistas = [tuple(p) for p in d.get("pistas", [])]
        self._vistas = set(d.get("vistas", []))
