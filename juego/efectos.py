"""Efectos "next-gen": post-procesado filmico y sistema de partículas.

- PostFX: bloom (resplandor), viñeta y grano de película, todo en pygame puro
  (sin dependencias) operando sobre superficies reducidas para ir rápido.
- Particulas: motas de polvo en suspensión, llamas de antorchas/velas y polvo
  de pisadas, proyectadas en el mundo isométrico.
"""
from __future__ import annotations

import math
import random

import pygame

from . import config as C
from .iso import mundo_a_pantalla


# --------------------------------------------------------------------------- #
#  POST-PROCESADO
# --------------------------------------------------------------------------- #
class PostFX:
    def __init__(self, ancho, alto) -> None:
        self.ancho, self.alto = ancho, alto
        self.rng = random.Random(2026)
        self.t = 0.0
        self.vineta = self._crear_vineta()
        self.grano = [self._crear_grano() for _ in range(6)]
        self.escala_bloom = 5
        self._umbral = None

    # -- construcción ------------------------------------------------------- #
    def _crear_vineta(self):
        """Degradado radial: centro transparente, bordes oscuros (sutil)."""
        v = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        cx, cy = self.ancho / 2, self.alto / 2
        maxd = math.hypot(cx, cy)
        alpha_max = 120
        N = 90
        for i in range(N):
            f = i / N                      # 0 -> anillo exterior; 1 -> centro
            radio = int(maxd * (1.0 - f))
            if radio <= 0:
                continue
            alpha = int(alpha_max * (1.0 - f) ** 2.4)
            # Elipse para respetar el aspecto 16:9.
            rw, rh = int(radio * 1.18), radio
            pygame.draw.ellipse(v, (0, 0, 0, alpha),
                                (cx - rw, cy - rh, rw * 2, rh * 2))
        return v

    def _crear_grano(self):
        # Grano fílmico sutil: se suma (BLEND_RGB_ADD ignora set_alpha), por eso
        # el rango de valores se mantiene bajo. Con numpy se genera al instante;
        # sin él, se recurre a PixelArray (más lento, sólo al arrancar).
        w, h = self.ancho // 3, self.alto // 3
        try:
            import numpy as np
            ruido = np.random.default_rng(self.rng.randrange(1 << 30)).integers(
                0, 17, size=(w, h), dtype=np.uint8)
            base = pygame.surfarray.make_surface(np.stack([ruido] * 3, axis=-1))
        except Exception:
            base = pygame.Surface((w, h))
            pa = pygame.PixelArray(base)
            for y in range(h):
                for x in range(w):
                    v = self.rng.randint(0, 16)
                    pa[x, y] = (v, v, v)
            del pa
        return pygame.transform.smoothscale(base, (self.ancho, self.alto))

    # -- aplicación --------------------------------------------------------- #
    def _bloom(self, origen):
        pa, a = self.ancho // self.escala_bloom, self.alto // self.escala_bloom
        peq = pygame.transform.smoothscale(origen, (pa, a))
        # Umbral: restamos un gris medio para quedarnos con lo brillante.
        if self._umbral is None or self._umbral.get_size() != (pa, a):
            self._umbral = pygame.Surface((pa, a))
            self._umbral.fill((118, 118, 118))
        peq.blit(self._umbral, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        # Desenfoque por reescalado (una pasada).
        peq = pygame.transform.smoothscale(peq, (pa // 2, a // 2))
        grande = pygame.transform.smoothscale(peq, (self.ancho, self.alto))
        return grande

    def aplicar(self, origen, destino, dt=0.016, intensidad_bloom=1.0) -> None:
        self.t += dt
        destino.blit(origen, (0, 0))
        bloom = self._bloom(origen)
        if intensidad_bloom < 1.0:
            bloom.set_alpha(int(255 * intensidad_bloom))
        destino.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.velo_filmico(destino)

    def velo_filmico(self, sup) -> None:
        sup.blit(self.vineta, (0, 0))
        g = self.grano[int(self.t * 24) % len(self.grano)]
        sup.blit(g, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


# --------------------------------------------------------------------------- #
#  PARTÍCULAS
# --------------------------------------------------------------------------- #
class Particula:
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "vida", "vida0", "color", "r", "tipo")

    def __init__(self, x, y, z, vx, vy, vz, vida, color, r, tipo) -> None:
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.vida = self.vida0 = vida
        self.color = color
        self.r = r
        self.tipo = tipo


class Particulas:
    def __init__(self) -> None:
        self.items: list[Particula] = []
        self.rng = random.Random(7)
        self._t = 0.0

    def emitir(self, x, y, tipo, n=1, z=0.0) -> None:
        for _ in range(n):
            if tipo == "llama":
                self.items.append(Particula(
                    x + self.rng.uniform(-0.1, 0.1), y + self.rng.uniform(-0.1, 0.1),
                    z + self.rng.uniform(0, 6), self.rng.uniform(-0.05, 0.05),
                    self.rng.uniform(-0.05, 0.05), self.rng.uniform(18, 34),
                    self.rng.uniform(0.5, 0.9),
                    (255, self.rng.randint(120, 190), 40), self.rng.uniform(3, 6), tipo))
            elif tipo == "polvo":
                self.items.append(Particula(
                    x, y, z + self.rng.uniform(4, 26), self.rng.uniform(-0.12, 0.12),
                    self.rng.uniform(-0.12, 0.12), self.rng.uniform(2, 8),
                    self.rng.uniform(9.0, 18.0), (230, 210, 165),
                    self.rng.uniform(1, 2.2), tipo))
            elif tipo == "pisada":
                self.items.append(Particula(
                    x, y, 0, self.rng.uniform(-0.3, 0.3), self.rng.uniform(-0.3, 0.3),
                    self.rng.uniform(6, 14), self.rng.uniform(0.3, 0.6),
                    (200, 185, 150), self.rng.uniform(1.5, 3), tipo))
            elif tipo == "chispa":
                ang = self.rng.uniform(0, math.tau)
                sp = self.rng.uniform(0.4, 1.2)
                self.items.append(Particula(
                    x, y, z, math.cos(ang) * sp, math.sin(ang) * sp,
                    self.rng.uniform(10, 20), self.rng.uniform(0.4, 0.8),
                    (255, 220, 130), self.rng.uniform(1.5, 3), tipo))

    def actualizar(self, dt, juego) -> None:
        self._t += dt
        planta = juego.planta_actual
        g = juego.guillermo

        # Motas de polvo ambientales alrededor del jugador.
        if self.rng.random() < 0.6:
            self.emitir(g.x + self.rng.uniform(-6, 6), g.y + self.rng.uniform(-6, 6),
                        "polvo", 1)
        # Llamas en las luces de la planta.
        for (lx, ly, _col, _rad) in getattr(planta, "luces", []):
            if self.rng.random() < 0.5:
                self.emitir(lx + 0.5, ly + 0.5, "llama", 1, z=10)
        # Vela del altar / lámpara del jugador.
        if juego.objetos["lampara"].portador == "adso" and juego.aceite > 0:
            if self.rng.random() < 0.4:
                self.emitir(juego.adso.x, juego.adso.y, "llama", 1, z=14)
        # Polvo de pisadas.
        if g.velocidad > 0.01 and self.rng.random() < 0.5:
            self.emitir(g.x, g.y, "pisada", 1)

        vivos = []
        for p in self.items:
            p.vida -= dt * 6
            if p.vida <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz
            if p.tipo == "llama":
                p.vz *= 0.94
                p.vx *= 0.9
                p.vy *= 0.9
            elif p.tipo == "polvo":
                p.z += math.sin((self._t + p.vida) * 2) * 0.15
            vivos.append(p)
        self.items = vivos[-900:]      # tope de seguridad

    def dibujar(self, sup, juego, cx, cy) -> None:
        for p in self.items:
            sx, sy = mundo_a_pantalla(p.x, p.y, juego.cam_x, juego.cam_y, cx, cy)
            sy -= int(p.z)
            f = max(0.0, min(1.0, p.vida / p.vida0))
            col = (int(p.color[0] * f), int(p.color[1] * f), int(p.color[2] * f))
            r = max(1, int(p.r))
            if p.tipo in ("llama", "chispa"):
                pygame.draw.circle(sup, (col[0] // 2, col[1] // 2, col[2] // 3),
                                   (sx, sy), r + 2)
            pygame.draw.circle(sup, col, (sx, sy), r)
