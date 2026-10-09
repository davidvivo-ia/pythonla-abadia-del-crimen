"""Interfaz: reloj canónico, obsequium (0-31), inventario y minimapa."""
from __future__ import annotations

import pygame

from . import config as C


class HUD:
    def __init__(self) -> None:
        pygame.font.init()
        self.f_grande = self._fuente(28)
        self.f_media = self._fuente(19)
        self.f_pequena = self._fuente(14)
        self.f_titulo = self._fuente(60)
        self._cache_minimapa: dict[int, pygame.Surface] = {}

    @staticmethod
    def _fuente(tam):
        for nombre in ("Garamond", "Georgia", "Palatino Linotype", "serif"):
            ruta = pygame.font.match_font(nombre)
            if ruta:
                return pygame.font.Font(ruta, tam)
        return pygame.font.Font(None, tam)

    # ------------------------------------------------------------------ #
    def texto(self, sup, txt, x, y, fuente=None, color=C.PERGAMINO,
              sombra=True, centro=False):
        fuente = fuente or self.f_media
        if sombra:
            s = fuente.render(txt, True, C.NEGRO)
            r = s.get_rect(center=(x + 1, y + 1)) if centro else s.get_rect(topleft=(x + 1, y + 1))
            sup.blit(s, r)
        img = fuente.render(txt, True, color)
        r = img.get_rect(center=(x, y)) if centro else img.get_rect(topleft=(x, y))
        sup.blit(img, r)
        return r

    # ------------------------------------------------------------------ #
    def dibujar(self, sup, juego) -> None:
        self._panel(sup, juego)
        self._minimapa(sup, juego)
        self._mensajes(sup, juego)

    def _panel(self, sup, juego) -> None:
        alto = 88
        panel = pygame.Surface((C.ANCHO, alto), pygame.SRCALPHA)
        panel.fill((20, 16, 12, 210))
        pygame.draw.line(panel, C.ORO, (0, 0), (C.ANCHO, 0), 2)
        sup.blit(panel, (0, C.ALTO - alto))
        y = C.ALTO - alto + 12

        # Reloj + ubicación (abajo-izquierda)
        self.texto(sup, juego.reloj.hora_texto(), 20, y, self.f_grande, C.ORO_CLARO)
        self.texto(sup, f"{C.NOMBRE_PLANTA[juego.guillermo.planta]} · "
                        f"Estás en: {juego.estancia_actual_nombre()}", 20, y + 38,
                   self.f_pequena, C.PERGAMINO_2)
        prog = int(juego.reloj.progreso * 200)
        pygame.draw.rect(sup, C.GRIS_OSCURO, (20, y + 58, 200, 6))
        pygame.draw.rect(sup, C.PERGAMINO_2, (20, y + 58, prog, 6))

        # Inventario (centro): los 8 objetos
        self.texto(sup, "Objetos:", 330, y, self.f_media, C.PERGAMINO)
        for i, obj in enumerate(juego.objetos.values()):
            tiene = obj.portador == "guillermo"
            tiene_adso = obj.portador == "adso"
            cx = 345 + i * 42
            col = C.ORO if tiene else ((70, 90, 130) if tiene_adso else C.GRIS_OSCURO)
            pygame.draw.circle(sup, col, (cx, y + 48), 13)
            pygame.draw.circle(sup, C.NEGRO, (cx, y + 48), 13, 2)
            self.texto(sup, obj.icono, cx, y + 48, self.f_media, C.NEGRO,
                       sombra=False, centro=True)

        # Obsequium (abajo-derecha, 0..31)
        ox = C.ANCHO - 320
        self.texto(sup, "Obsequium", ox, y, self.f_media, C.PERGAMINO)
        frac = max(0.0, juego.obsequium / C.OBSEQUIUM_MAX)
        w = 280
        pygame.draw.rect(sup, C.GRIS_OSCURO, (ox, y + 34, w, 20))
        col = C.VERDE if frac > 0.5 else (C.ORO if frac > 0.25 else C.ROJO)
        pygame.draw.rect(sup, col, (ox, y + 34, int(w * frac), 20))
        pygame.draw.rect(sup, C.NEGRO, (ox, y + 34, w, 20), 2)
        self.texto(sup, f"{juego.obsequium}/{C.OBSEQUIUM_MAX}", ox + w - 44, y + 36,
                   self.f_pequena, C.BLANCO)

    def _minimapa(self, sup, juego) -> None:
        planta = juego.mapa.planta(juego.guillermo.planta)
        escala = 4
        mw, mh = planta.ancho * escala, planta.alto * escala
        mx, my = C.ANCHO - mw - 16, 16
        # La parte estática (muros, puertas, escaleras) se dibuja una vez por
        # planta y se cachea: evita ~2000 rellenos por frame.
        base = self._cache_minimapa.get(id(planta))
        if base is None:
            base = pygame.Surface((mw + 8, mh + 8), pygame.SRCALPHA)
            base.fill((10, 8, 6, 190))
            for gy in range(planta.alto):
                for gx in range(planta.ancho):
                    t = planta.tiles[gy][gx]
                    if t == C.VACIO:
                        continue
                    if t == C.MURO or t == C.MESA:
                        col = (70, 64, 58)
                    elif t == C.PUERTA:
                        col = C.ORO
                    elif t == C.ESCALERA:
                        col = (120, 200, 120)
                    elif t == C.ESPEJO:
                        col = (180, 160, 200)
                    else:
                        col = (150, 140, 120)
                    base.fill(col, (4 + gx * escala, 4 + gy * escala, escala, escala))
            # Abreviaturas de cada estancia sobre su centro.
            for clave, e in planta.estancias.items():
                cxm, cym = e.centro
                img = self.f_pequena.render(C.NOMBRE_CORTO.get(clave, "?"), True, C.BLANCO)
                base.blit(img, (4 + cxm * escala - img.get_width() // 2,
                                4 + cym * escala - img.get_height() // 2))
            self._cache_minimapa[id(planta)] = base
        sup.blit(base, (mx - 4, my - 4))
        # Resalta la estancia en la que está Guillermo.
        actual = planta.estancia_de(*juego.guillermo.tile)
        if actual:
            e = planta.estancias[actual]
            pygame.draw.rect(sup, C.ORO_CLARO, (mx + e.x * escala, my + e.y * escala,
                                                e.w * escala, e.h * escala), 1)
        for obj in juego.objetos.values():
            if obj.en_suelo and obj.planta == juego.guillermo.planta:
                sup.fill(C.ORO_CLARO, (mx + obj.gx * escala - 1, my + obj.gy * escala - 1, 3, 3))
        for m in juego.monjes.values():
            if m.vivo and m.activo and m.planta == juego.guillermo.planta:
                sup.fill(C.ROJO, (mx + int(m.x) * escala, my + int(m.y) * escala, escala, escala))
        g = juego.guillermo
        sup.fill(C.BLANCO, (mx + int(g.x) * escala - 1, my + int(g.y) * escala - 1, 4, 4))

    def _mensajes(self, sup, juego) -> None:
        y = 118
        for msg, t in juego.mensajes:
            alpha = min(255, int(t * 140))
            s = self.f_media.render(msg, True, C.PERGAMINO)
            s.set_alpha(alpha)
            if s.get_width() > C.ANCHO - 340:
                s = pygame.transform.smoothscale(s, (C.ANCHO - 340, s.get_height()))
            fondo = pygame.Surface((s.get_width() + 24, s.get_height() + 10), pygame.SRCALPHA)
            fondo.fill((20, 16, 12, min(200, alpha)))
            sup.blit(fondo, (C.ANCHO // 2 - fondo.get_width() // 2, y))
            sup.blit(s, (C.ANCHO // 2 - s.get_width() // 2, y + 5))
            y += 40
