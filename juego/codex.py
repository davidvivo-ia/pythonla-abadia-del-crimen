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
        """Texto del objetivo vigente según el horario, la posición y el progreso."""
        tiene = juego.tiene
        if juego.clima_resuelto:
            return "El misterio ha concluido."

        # 1) Obligación horaria: solo si Guillermo NO está ya donde debe.
        m = juego.reloj.momento
        g = juego.guillermo
        zona = juego.mapa.planta(C.PLANTA_BAJA).zona(*g.tile) if g.planta == C.PLANTA_BAJA else ""
        if m in C.MOMENTO_IGLESIA and zona != "iglesia":
            return f"{juego.reloj.nombre}: acude a la iglesia antes de que acabe."
        if m in C.MOMENTO_REFECTORIO and zona != "refectorio":
            return "Sexta: ocupa tu sitio en el refectorio."
        if m in C.MOMENTO_CELDA and zona != "celda":
            return f"{juego.reloj.nombre}: retírate a tu celda a dormir."
        cumpliendo = (m in C.MOMENTO_IGLESIA or m in C.MOMENTO_REFECTORIO
                      or m in C.MOMENTO_CELDA)
        prefijo = "✓ Cumples el horario. Luego: " if cumpliendo else "Tiempo libre: "

        # 2) Progreso de la investigación, con la ubicación REAL de cada objeto.
        def donde(clave) -> str:
            o = juego.objetos[clave]
            if o.oculto:
                return ""
            p = juego.mapa.planta(o.planta)
            est = p.estancia_de(o.gx, o.gy)
            nombre = C.NOMBRE_ESTANCIA.get(est, "") if est else ""
            nombre = nombre.split(" (")[0] or C.NOMBRE_PLANTA[o.planta]   # sin paréntesis anidados
            return f" ({nombre.lower()})"

        faltan = []
        if not tiene("guantes"):
            faltan.append("los guantes" + donde("guantes"))
        if not tiene("pergamino"):
            faltan.append("el pergamino" + donde("pergamino"))
        if not tiene("gafas"):
            if juego.objetos["gafas"].oculto:
                faltan.append("las gafas (reaparecen en la biblioteca el 5º día)")
            else:
                faltan.append("las gafas" + donde("gafas"))
        if faltan:
            lista = ", ".join(faltan[:-1]) + (" y " if len(faltan) > 1 else "") + faltan[-1]
            return prefijo + "consigue " + lista + "."
        lamp = juego.objetos["lampara"]
        if lamp.portador != "adso":
            if lamp.oculto:
                return prefijo + "espera a la lámpara (aparece en la cocina el 3º día)."
            return prefijo + "recoge la lámpara" + donde("lampara") + "; Adso la llevará."
        if juego.reloj.dia < 6:
            return prefijo + "todo listo; Jorge aguardará tras el espejo desde el 6º día."
        if g.planta != C.PLANTA_BIBLIOTECA:
            return prefijo + "sube a la biblioteca y busca la sala del espejo."
        return "Enfréntate a Jorge en el espejo: ¡no te quites los guantes!"

    def to_dict(self):
        return {"pistas": self.pistas, "vistas": list(self._vistas)}

    def from_dict(self, d) -> None:
        self.pistas = [tuple(p) for p in d.get("pistas", [])]
        self._vistas = set(d.get("vistas", []))
