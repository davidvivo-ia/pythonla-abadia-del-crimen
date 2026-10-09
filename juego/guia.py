"""Guía de navegación: a dónde ir ahora y cómo llegar.

Calcula el destino vigente (obligación horaria, siguiente objeto de la
investigación, escalera a otra planta o el espejo), traza la ruta con A* y la
dibuja como un rastro de puntos en el suelo, una flecha junto a Guillermo y
una marca en el minimapa. Es lo que convierte "ve a tu celda" en un camino.
"""
from __future__ import annotations

import math

import pygame

from . import config as C
from .iso import mundo_a_pantalla
from .pathfinding import a_estrella

# Escalera que hay que tomar en cada planta para dirigirse a otra.
ESCALERA_HACIA = {
    (C.PLANTA_BAJA, C.PLANTA_SCRIPTORIUM): (20, 34),
    (C.PLANTA_BAJA, C.PLANTA_BIBLIOTECA): (20, 34),
    (C.PLANTA_SCRIPTORIUM, C.PLANTA_BAJA): (4, 4),
    (C.PLANTA_SCRIPTORIUM, C.PLANTA_BIBLIOTECA): (22, 4),
    (C.PLANTA_BIBLIOTECA, C.PLANTA_SCRIPTORIUM): (4, 4),
    (C.PLANTA_BIBLIOTECA, C.PLANTA_BAJA): (4, 4),
}

COLOR_RUTA = (120, 220, 255)
COLOR_META = (255, 230, 140)


class Guia:
    def __init__(self) -> None:
        self.planta = None          # planta del destino final
        self.tile = None            # tile del destino final
        self.nombre = ""            # qué es el destino
        self.motivo = ""            # por qué ("Vísperas", "investigación"...)
        self.tile_local = None      # objetivo en la planta actual (destino o escalera)
        self.ruta: list[tuple[int, int]] = []
        self._clave_ruta = None
        self.t = 0.0

    # ------------------------------------------------------------------ #
    def destino(self, juego):
        """(planta, tile, nombre, motivo) o None si no hay nada que hacer."""
        r, g, O = juego.reloj, juego.guillermo, juego.objetos
        mapa = juego.mapa
        baja = mapa.planta(C.PLANTA_BAJA)
        zona = baja.zona(*g.tile) if g.planta == C.PLANTA_BAJA else ""
        m = r.momento

        def ancla(pl, clave, nombre, motivo):
            gx, gy = mapa.planta(pl).anclas[clave]
            return pl, (int(gx), int(gy)), nombre, motivo

        # 1) Obligación horaria (cuesta obsequium).
        if m in C.MOMENTO_IGLESIA and zona != "iglesia":
            return ancla(C.PLANTA_BAJA, "iglesia", "Iglesia", f"{r.nombre}: oficio")
        if m in C.MOMENTO_REFECTORIO and zona != "refectorio":
            return ancla(C.PLANTA_BAJA, "refectorio", "Refectorio", "Sexta: comida")
        if m in C.MOMENTO_CELDA and zona != "celda":
            return ancla(C.PLANTA_BAJA, "celda_guillermo", "Tu celda", f"{r.nombre}: a dormir")
        if m in C.MOMENTO_IGLESIA or m in C.MOMENTO_REFECTORIO or m in C.MOMENTO_CELDA:
            return None                                   # ya estás donde debes

        # 2) Investigación: siguiente objeto visible que falte.
        def obj(clave, nombre):
            o = O[clave]
            if o.en_suelo:
                return o.planta, (int(o.gx), int(o.gy)), nombre, "investigación"
            return None

        for clave, nombre, cond in (("guantes", "Guantes", not juego.tiene("guantes")),
                                    ("pergamino", "Pergamino de Venancio", not juego.tiene("pergamino")),
                                    ("gafas", "Gafas", not juego.tiene("gafas")),
                                    ("lampara", "Lámpara (Adso la llevará)", O["lampara"].portador != "adso")):
            if cond:
                d = obj(clave, nombre)
                if d:
                    return d
        listo = (juego.tiene("guantes") and juego.tiene("pergamino") and juego.tiene("gafas")
                 and O["lampara"].portador == "adso")
        if listo and r.dia >= 6 and juego.monjes["jorge"].activo:
            return ancla(C.PLANTA_BIBLIOTECA, "espejo", "Sala del espejo (Jorge)", "desenlace")
        return None

    # ------------------------------------------------------------------ #
    def actualizar(self, juego, dt) -> None:
        self.t += dt
        d = self.destino(juego)
        g = juego.guillermo
        if d is None:
            self.planta = self.tile = self.tile_local = None
            self.nombre = self.motivo = ""
            self.ruta = []
            self._clave_ruta = None
            return
        self.planta, self.tile, self.nombre, self.motivo = d
        if self.planta == g.planta:
            self.tile_local = self.tile
        else:
            self.tile_local = ESCALERA_HACIA.get((g.planta, self.planta), self.tile)
        clave = (g.planta, g.tile, self.tile_local)
        if clave != self._clave_ruta:
            self._clave_ruta = clave
            self.ruta = a_estrella(juego.mapa.planta(g.planta), g.tile, self.tile_local)

    @property
    def pasos(self) -> int:
        return len(self.ruta)

    def texto(self, juego) -> str:
        if self.tile is None:
            m = juego.reloj.momento
            if m in C.MOMENTO_IGLESIA or m in C.MOMENTO_REFECTORIO or m in C.MOMENTO_CELDA:
                return "✓ Estás donde debes. Espera a que acabe."
            return "Sin destino pendiente: explora o espera."
        via = ""
        if self.planta != juego.guillermo.planta:
            via = f" (por la escalera a {C.NOMBRE_PLANTA[self.planta]})"
        return f"→ Ve a: {self.nombre}{via} · {self.pasos} pasos · {self.motivo}"

    # ------------------------------------------------------------------ #
    def dibujar_mundo(self, juego, sup, cx, cy) -> None:
        """Rastro de puntos hasta el destino, marca del destino y flecha."""
        if not self.ruta:
            return
        g = juego.guillermo
        n = len(self.ruta)
        for i, (gx, gy) in enumerate(self.ruta):
            sx, sy = mundo_a_pantalla(gx + 0.5, gy + 0.5, juego.cam_x, juego.cam_y, cx, cy)
            if not (-20 < sx < C.ANCHO + 20 and -20 < sy < C.ALTO - 80):
                continue
            # Pulso que "fluye" hacia el destino.
            fase = (i - self.t * 6.0) % 5.0
            brillo = 0.45 + 0.55 * max(0.0, 1.0 - fase / 2.0)
            col = tuple(int(c * brillo) for c in COLOR_RUTA)
            r = 4 if i < n - 1 else 7
            pygame.draw.circle(sup, col, (sx, sy - 2), r)
            pygame.draw.circle(sup, (10, 30, 40), (sx, sy - 2), r, 1)
        # Marca del destino local (anillo pulsante + nombre).
        gx, gy = self.tile_local
        sx, sy = mundo_a_pantalla(gx + 0.5, gy + 0.5, juego.cam_x, juego.cam_y, cx, cy)
        if -60 < sx < C.ANCHO + 60 and 0 < sy < C.ALTO - 80:
            rad = 14 + int(4 * math.sin(self.t * 5))
            pygame.draw.circle(sup, COLOR_META, (sx, sy), rad, 2)
            pygame.draw.circle(sup, COLOR_META, (sx, sy), 3)
            etiqueta = self.nombre if self.planta == g.planta else "Escalera"
            juego.hud.texto(sup, f"▼ {etiqueta}", sx, sy - rad - 30, juego.hud.f_media,
                            COLOR_META, centro=True)
        # Flecha junto a Guillermo hacia el siguiente punto de la ruta.
        obj = self.ruta[min(2, n - 1)]
        px, py = mundo_a_pantalla(g.x, g.y, juego.cam_x, juego.cam_y, cx, cy)
        tx, ty = mundo_a_pantalla(obj[0] + 0.5, obj[1] + 0.5, juego.cam_x, juego.cam_y, cx, cy)
        dx, dy = tx - px, ty - py
        d = math.hypot(dx, dy)
        if d > 1:
            ux, uy = dx / d, dy / d
            bx, by = px + ux * 46, py - 20 + uy * 46 * 0.55
            punta = (bx + ux * 14, by + uy * 14 * 0.55)
            izq = (bx - uy * 7, by + ux * 7 * 0.55)
            der = (bx + uy * 7, by - ux * 7 * 0.55)
            pygame.draw.polygon(sup, COLOR_RUTA, [punta, izq, der])
            pygame.draw.polygon(sup, (10, 30, 40), [punta, izq, der], 1)

    def dibujar_minimapa(self, juego, sup, mx, my, escala) -> None:
        if not self.ruta:
            return
        for gx, gy in self.ruta:
            sup.fill(COLOR_RUTA, (mx + gx * escala + 1, my + gy * escala + 1, escala - 2, escala - 2))
        gx, gy = self.tile_local
        if int(self.t * 3) % 2 == 0:
            pygame.draw.rect(sup, COLOR_META, (mx + gx * escala - 2, my + gy * escala - 2,
                                              escala + 4, escala + 4), 2)
