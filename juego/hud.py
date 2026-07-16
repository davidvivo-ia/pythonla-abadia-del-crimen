"""Interfaz: barra de obsequium, reloj, inventario, minimapa y mensajes."""
from __future__ import annotations

import pygame

from . import config as C


class HUD:
    def __init__(self) -> None:
        pygame.font.init()
        self.f_grande = self._fuente(30)
        self.f_media = self._fuente(20)
        self.f_pequena = self._fuente(15)
        self.f_titulo = self._fuente(64)

    @staticmethod
    def _fuente(tam: int) -> pygame.font.Font:
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
            r = s.get_rect()
            if centro:
                r.center = (x + 1, y + 1)
            else:
                r.topleft = (x + 1, y + 1)
            sup.blit(s, r)
        img = fuente.render(txt, True, color)
        r = img.get_rect()
        if centro:
            r.center = (x, y)
        else:
            r.topleft = (x, y)
        sup.blit(img, r)
        return r

    # ------------------------------------------------------------------ #
    def dibujar(self, sup, juego) -> None:
        self._panel_inferior(sup, juego)
        self._minimapa(sup, juego)
        self._mensajes(sup, juego)

    def _panel_inferior(self, sup, juego) -> None:
        alto = 84
        panel = pygame.Surface((C.ANCHO, alto), pygame.SRCALPHA)
        panel.fill((20, 16, 12, 205))
        pygame.draw.line(panel, C.ORO, (0, 0), (C.ANCHO, 0), 2)
        sup.blit(panel, (0, C.ALTO - alto))
        base_y = C.ALTO - alto + 12

        # Reloj (abajo-izquierda, como el original)
        self.texto(sup, juego.reloj.hora_texto(), 20, base_y,
                   self.f_grande, C.ORO_CLARO)
        prog = int(juego.reloj.progreso * 200)
        pygame.draw.rect(sup, C.GRIS_OSCURO, (20, base_y + 40, 200, 8))
        pygame.draw.rect(sup, C.PERGAMINO_2, (20, base_y + 40, prog, 8))

        # Inventario (centro)
        self.texto(sup, "Reliquias:", 360, base_y, self.f_media, C.PERGAMINO)
        x = 360
        for i, (clave, obj) in enumerate(juego.items.items()):
            col = C.ORO if obj["tomado"] else C.GRIS_OSCURO
            cx = x + 30 + i * 44
            pygame.draw.circle(sup, col, (cx, base_y + 46), 13)
            pygame.draw.circle(sup, C.NEGRO, (cx, base_y + 46), 13, 2)
            self.texto(sup, obj["icono"], cx, base_y + 46, self.f_media,
                       C.NEGRO, sombra=False, centro=True)

        # Obsequium (abajo-derecha, como el original)
        ox = C.ANCHO - 320
        self.texto(sup, "Obsequium", ox, base_y, self.f_media, C.PERGAMINO)
        frac = max(0.0, juego.obsequium / C.OBSEQUIUM_MAX)
        w = 280
        pygame.draw.rect(sup, C.GRIS_OSCURO, (ox, base_y + 32, w, 20))
        col = C.VERDE if frac > 0.5 else (C.ORO if frac > 0.25 else C.ROJO)
        pygame.draw.rect(sup, col, (ox, base_y + 32, int(w * frac), 20))
        pygame.draw.rect(sup, C.NEGRO, (ox, base_y + 32, w, 20), 2)

    def _minimapa(self, sup, juego) -> None:
        mapa = juego.mapa
        escala = 4
        mw, mh = mapa.ancho * escala, mapa.alto * escala
        mx, my = C.ANCHO - mw - 16, 16
        fondo = pygame.Surface((mw + 8, mh + 8), pygame.SRCALPHA)
        fondo.fill((10, 8, 6, 190))
        sup.blit(fondo, (mx - 4, my - 4))
        for gy in range(mapa.alto):
            for gx in range(mapa.ancho):
                t = mapa.tiles[gy][gx]
                if t == C.VACIO:
                    continue
                if t == C.MURO:
                    col = (70, 64, 58)
                elif t == C.PUERTA:
                    col = C.ORO
                else:
                    col = (150, 140, 120)
                sup.fill(col, (mx + gx * escala, my + gy * escala, escala, escala))
        # Items
        for obj in juego.items.values():
            if not obj["tomado"]:
                gx, gy = obj["pos"]
                sup.fill(C.ORO_CLARO, (mx + gx * escala - 1, my + gy * escala - 1, 3, 3))
        # Monjes
        for m in juego.monjes:
            sup.fill(C.ROJO, (mx + int(m.x) * escala, my + int(m.y) * escala, escala, escala))
        # Guillermo
        g = juego.guillermo
        sup.fill(C.BLANCO, (mx + int(g.x) * escala - 1, my + int(g.y) * escala - 1, 4, 4))

    def _mensajes(self, sup, juego) -> None:
        y = 120
        for msg, t in juego.mensajes:
            alpha = min(255, int(t * 160))
            s = self.f_media.render(msg, True, C.PERGAMINO)
            s.set_alpha(alpha)
            fondo = pygame.Surface((s.get_width() + 24, s.get_height() + 10), pygame.SRCALPHA)
            fondo.fill((20, 16, 12, min(200, alpha)))
            sup.blit(fondo, (C.ANCHO // 2 - fondo.get_width() // 2, y))
            sup.blit(s, (C.ANCHO // 2 - s.get_width() // 2, y + 5))
            y += 40
