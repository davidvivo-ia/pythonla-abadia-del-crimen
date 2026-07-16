"""Núcleo del juego: bucle principal, estados, render isométrico y reglas."""
from __future__ import annotations

import json
import math
import os
import random

import pygame

from . import config as C
from .entidades import Adso, Guillermo, Monje
from .hud import HUD
from .iso import foco_camara, mundo_a_pantalla, profundidad
from .mapa import Mapa
from .tiempo import Reloj

# Estados del juego
MENU, JUGANDO, PAUSA, DIALOGO, GAMEOVER, VICTORIA, AYUDA = range(7)


# Monjes de la abadía (nombre, color de hábito, zona donde deambulan, frase)
DEF_MONJES = [
    ("Abad",       (60, 50, 90),   "iglesia",     "La paz sea contigo, fray Guillermo."),
    ("Jorge",      (40, 38, 34),   "biblioteca",  "El saber no debe abrirse a todos..."),
    ("Malaquías",  (70, 60, 50),   "biblioteca",  "La biblioteca está prohibida."),
    ("Severino",   (60, 90, 80),   "enfermeria",  "Ven a la enfermería si necesitas hierbas."),
    ("Berengario", (90, 70, 60),   "scriptorium", "He visto cosas terribles esta noche."),
    ("Bernardo",   (110, 40, 40),  "capitular",   "La Inquisición todo lo ve."),
    ("Remigio",    (80, 74, 60),   "cocina",      "El pan y el vino no faltan aquí."),
]

# Reliquias a recolectar (clave -> definición)
DEF_ITEMS = [
    ("llave",     "Llave del Aedificium", "K", "refectorio"),
    ("lentes",    "Lentes de Guillermo",  "L", "scriptorium"),
    ("lampara",   "Lámpara de aceite",    "F", "cocina"),
    ("pergamino", "Pergamino cifrado",    "P", "capitular"),
]


class Juego:
    def __init__(self, pantalla: pygame.Surface) -> None:
        self.pantalla = pantalla
        self.reloj_fps = pygame.time.Clock()
        self.hud = HUD()
        self.rng = random.Random(1987)
        self.estado = MENU
        self.opcion_menu = 0
        self.ejecutando = True
        self._nuevo_mundo()

    # ------------------------------------------------------------------ #
    def _nuevo_mundo(self) -> None:
        self.mapa = Mapa()
        cx, cy = self.mapa.centro_estancia("iglesia")
        self.guillermo = Guillermo(cx, cy + 2)
        self.adso = Adso(cx - 1, cy + 3)
        self.reloj = Reloj()
        self.reloj.franja = 3  # comienza en "Capítulo" (de día, sin oficio)
        self.obsequium = C.OBSEQUIUM_MAX
        self.cam_x, self.cam_y = foco_camara(self.guillermo.x, self.guillermo.y)
        self.mensajes: list[list] = []
        self.dialogo_texto = ""

        self.monjes: list[Monje] = []
        for nombre, color, zona, frase in DEF_MONJES:
            mx, my = self.mapa.centro_estancia(zona)
            m = Monje(mx, my, color, nombre, zona)
            m.frase_base = frase
            self.monjes.append(m)

        self.items: dict[str, dict] = {}
        for clave, nombre, icono, zona in DEF_ITEMS:
            ex, ey = self.mapa.centro_estancia(zona)
            self.items[clave] = {
                "nombre": nombre, "icono": icono,
                "pos": (int(ex), int(ey)), "tomado": False, "activo": True,
            }
        # El libro prohibido sólo aparece con todas las reliquias
        bx, by = self.mapa.centro_estancia("biblioteca")
        self.items["libro"] = {
            "nombre": "El libro prohibido", "icono": "B",
            "pos": (int(bx), int(by)), "tomado": False, "activo": False,
        }

    # ------------------------------------------------------------------ #
    def mensaje(self, txt: str, dur: float = 3.5) -> None:
        self.mensajes.append([txt, dur])
        if len(self.mensajes) > 4:
            self.mensajes.pop(0)

    # ================================================================== #
    #  BUCLE PRINCIPAL
    # ================================================================== #
    def correr(self) -> None:
        while self.ejecutando:
            dt = self.reloj_fps.tick(C.FPS) / 1000.0
            dt = min(dt, 0.05)
            self._eventos()
            if self.estado == JUGANDO:
                self._actualizar(dt)
            self._render()
            pygame.display.flip()

    # ------------------------------------------------------------------ #
    def _eventos(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.ejecutando = False
            elif ev.type == pygame.KEYDOWN:
                self._tecla(ev.key)

    def _tecla(self, key) -> None:
        if self.estado == MENU:
            self._tecla_menu(key)
        elif self.estado == JUGANDO:
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.estado = PAUSA
            elif key == pygame.K_e:
                self._interactuar()
            elif key == pygame.K_F5:
                self.guardar()
            elif key == pygame.K_m:
                pass  # (reservado)
        elif self.estado == PAUSA:
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.estado = JUGANDO
            elif key == pygame.K_q:
                self.estado = MENU
            elif key == pygame.K_F5:
                self.guardar()
        elif self.estado == DIALOGO:
            self.estado = JUGANDO
        elif self.estado in (GAMEOVER, VICTORIA, AYUDA):
            self.estado = MENU

    def _tecla_menu(self, key) -> None:
        opciones = self._opciones_menu()
        if key in (pygame.K_UP, pygame.K_w):
            self.opcion_menu = (self.opcion_menu - 1) % len(opciones)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.opcion_menu = (self.opcion_menu + 1) % len(opciones)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._elegir_menu(opciones[self.opcion_menu])

    def _opciones_menu(self) -> list[str]:
        ops = ["Nueva partida"]
        if os.path.exists(C.ARCHIVO_GUARDADO):
            ops.append("Continuar")
        ops += ["Cómo se juega", "Salir"]
        return ops

    def _elegir_menu(self, op: str) -> None:
        if op == "Nueva partida":
            self._nuevo_mundo()
            self.estado = JUGANDO
            self._intro()
        elif op == "Continuar":
            if self.cargar():
                self.estado = JUGANDO
        elif op == "Cómo se juega":
            self.estado = AYUDA
        elif op == "Salir":
            self.ejecutando = False

    def _intro(self) -> None:
        self.mensaje("El Abad: «Un monje ha muerto. Descubrid al culpable.»", 6)
        self.mensaje("Reúne las reliquias y llega a la biblioteca.", 6)

    # ================================================================== #
    #  ACTUALIZACIÓN
    # ================================================================== #
    def _actualizar(self, dt: float) -> None:
        teclas = pygame.key.get_pressed()
        control_adso = teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]
        entrada = self._entrada_direccion(teclas)

        if control_adso:
            self.guillermo.actualizar(self.mapa, (0, 0), dt)
            self.adso.actualizar(self.mapa, self.guillermo, entrada, dt)
        else:
            self.guillermo.actualizar(self.mapa, entrada, dt)
            self.adso.actualizar(self.mapa, self.guillermo, None, dt)

        for m in self.monjes:
            m.actualizar(self.mapa, dt, self.rng)

        self._camara(dt)
        self._obsequium(dt)
        self._items()

        if self.reloj.actualizar(dt):
            self._cambio_franja()

        # Mensajes con temporizador
        for msg in self.mensajes:
            msg[1] -= dt
        self.mensajes = [m for m in self.mensajes if m[1] > 0]

        if self.obsequium <= 0:
            self.estado = GAMEOVER
            self.mensaje_final = ("El Abad ya no tolera tu desobediencia. "
                                  "Eres expulsado de la abadía.")
        if self.reloj.fin_del_juego and not self.items["libro"]["tomado"]:
            self.estado = GAMEOVER
            self.mensaje_final = ("Amanece el séptimo día y el misterio "
                                  "sigue sin resolverse.")

    def _entrada_direccion(self, teclas) -> tuple[float, float]:
        # En isométrico, "arriba" en pantalla combina los ejes de la rejilla.
        dx = dy = 0.0
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dx -= 1; dy -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dx += 1; dy += 1
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= 1; dy += 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += 1; dy -= 1
        return dx, dy

    def _camara(self, dt: float) -> None:
        objetivo_x, objetivo_y = foco_camara(self.guillermo.x, self.guillermo.y)
        k = min(1.0, dt * 6.0)
        self.cam_x += (objetivo_x - self.cam_x) * k
        self.cam_y += (objetivo_y - self.cam_y) * k

    def _obsequium(self, dt: float) -> None:
        zona = self.mapa.zona(*self.guillermo.tile)
        delta = 0.0
        r = self.reloj
        if r.es_servicio:
            delta = C.REGEN_OBEDIENTE if zona == "iglesia" else -C.DREN_FALTAR_SERVICIO
        elif r.zona_requerida == "refectorio":
            delta = C.REGEN_OBEDIENTE if zona == "refectorio" else -C.DREN_VAGAR_NOCHE
        elif r.es_noche:
            delta = C.REGEN_OBEDIENTE if zona == "celda" else -C.DREN_VAGAR_NOCHE
        else:
            delta = -C.DREN_ZONA_PROHIBIDA if zona == "biblioteca" else C.REGEN_OBEDIENTE * 0.4
        self.obsequium = max(0.0, min(C.OBSEQUIUM_MAX, self.obsequium + delta * dt))

    def _items(self) -> None:
        g = self.guillermo
        # Activa el libro cuando estén las cuatro reliquias
        if not self.items["libro"]["activo"]:
            if all(self.items[k]["tomado"] for k in
                   ("llave", "lentes", "lampara", "pergamino")):
                self.items["libro"]["activo"] = True
                self.mensaje("El libro prohibido aguarda en la biblioteca.", 6)
        for clave, obj in self.items.items():
            if obj["tomado"] or not obj["activo"]:
                continue
            gx, gy = obj["pos"]
            if math.hypot(g.x - (gx + 0.5), g.y - (gy + 0.5)) < 0.8:
                obj["tomado"] = True
                self.mensaje(f"Has tomado: {obj['nombre']}.", 4)
                if clave == "libro":
                    self.estado = VICTORIA

    def _cambio_franja(self) -> None:
        r = self.reloj
        if r.es_servicio:
            self.mensaje(f"Suenan las campanas: {r.nombre}. Acude a la iglesia.", 5)
        elif r.clave == "noche":
            self.mensaje("Cae la noche. Deberías retirarte a tu celda.", 5)
        elif r.zona_requerida == "refectorio":
            self.mensaje("Es hora de comer en el refectorio.", 4)

    def _interactuar(self) -> None:
        g = self.guillermo
        cerca = None
        mejor = 1.6
        for m in self.monjes:
            d = math.hypot(g.x - m.x, g.y - m.y)
            if d < mejor:
                mejor, cerca = d, m
        if cerca:
            self.dialogo_texto = f"{cerca.nombre}: «{cerca.frase_base}»"
            self.estado = DIALOGO

    # ================================================================== #
    #  RENDER
    # ================================================================== #
    def _render(self) -> None:
        if self.estado == MENU:
            self._render_menu()
        elif self.estado == AYUDA:
            self._render_ayuda()
        else:
            self._render_mundo()
            if self.estado == JUGANDO:
                self.hud.dibujar(self.pantalla, self)
            elif self.estado == PAUSA:
                self.hud.dibujar(self.pantalla, self)
                self._overlay_pausa()
            elif self.estado == DIALOGO:
                self.hud.dibujar(self.pantalla, self)
                self._overlay_dialogo()
            elif self.estado == GAMEOVER:
                self._overlay_final("EXPULSADO", getattr(self, "mensaje_final", ""), C.ROJO)
            elif self.estado == VICTORIA:
                self._overlay_final(
                    "MISTERIO RESUELTO",
                    "Has hallado el libro prohibido y desvelado el crimen de la abadía.",
                    C.ORO)

    # ------------------------------------------------------------------ #
    def _render_mundo(self) -> None:
        self.pantalla.fill(C.AZUL_NOCHE if self.reloj.es_noche else (34, 40, 46))
        cx, cy = C.ANCHO // 2, C.ALTO // 2 - 40

        # Paso 1: suelos
        objetos = []  # (depth, callable)
        for gy in range(self.mapa.alto):
            for gx in range(self.mapa.ancho):
                t = self.mapa.tiles[gy][gx]
                if t == C.VACIO:
                    continue
                sx, sy = mundo_a_pantalla(gx, gy, self.cam_x, self.cam_y, cx, cy)
                if sx < -TILE_MARGEN or sx > C.ANCHO + TILE_MARGEN:
                    continue
                if sy < -TILE_MARGEN or sy > C.ALTO + TILE_MARGEN:
                    continue
                if t in (C.SUELO, C.PUERTA, C.ALTAR, C.CAMA):
                    self._dibujar_suelo(gx, gy, cx, cy, t)
                if t in (C.MURO, C.ALTAR, C.CAMA):
                    objetos.append((profundidad(gx, gy),
                                    self._factoria_bloque(gx, gy, cx, cy, t)))

        # Paso 2: entidades y bloques ordenados por profundidad
        for ent in [*self.monjes, self.adso, self.guillermo]:
            objetos.append((profundidad(ent.x, ent.y) + 0.4,
                            self._factoria_entidad(ent, cx, cy)))
        objetos.sort(key=lambda o: o[0])
        for _, fn in objetos:
            fn()

        self._iluminacion(cx, cy)

    def _rombo(self, gx, gy, cx, cy, dz=0):
        n = mundo_a_pantalla(gx, gy, self.cam_x, self.cam_y, cx, cy)
        e = mundo_a_pantalla(gx + 1, gy, self.cam_x, self.cam_y, cx, cy)
        s = mundo_a_pantalla(gx + 1, gy + 1, self.cam_x, self.cam_y, cx, cy)
        w = mundo_a_pantalla(gx, gy + 1, self.cam_x, self.cam_y, cx, cy)
        if dz:
            n = (n[0], n[1] - dz); e = (e[0], e[1] - dz)
            s = (s[0], s[1] - dz); w = (w[0], w[1] - dz)
        return n, e, s, w

    def _dibujar_suelo(self, gx, gy, cx, cy, t) -> None:
        zona = self.mapa.zona(gx, gy)
        color, borde = C.COLORES_ZONA.get(zona, C.COLORES_ZONA["claustro"])
        if t == C.PUERTA:
            color = tuple(min(255, c + 25) for c in color)
        # Tenue tablero de ajedrez para dar textura
        if (gx + gy) % 2 == 0:
            color = tuple(max(0, c - 10) for c in color)
        rombo = self._rombo(gx, gy, cx, cy)
        pygame.draw.polygon(self.pantalla, color, rombo)
        pygame.draw.polygon(self.pantalla, borde, rombo, 1)

    def _factoria_bloque(self, gx, gy, cx, cy, t):
        def dibujar():
            self._dibujar_bloque(gx, gy, cx, cy, t)
        return dibujar

    def _dibujar_bloque(self, gx, gy, cx, cy, t) -> None:
        if t == C.MURO:
            altura = C.ALTURA_MURO
            base = C.GRIS_PIEDRA
            zona = self.mapa.zona(gx, gy)
            if zona == "biblioteca":
                base = (96, 78, 60)
        elif t == C.ALTAR:
            altura = 24; base = C.ORO
        else:  # CAMA
            altura = 12; base = (120, 70, 60)
        n, e, s, w = self._rombo(gx, gy, cx, cy)
        nt, et, st, wt = self._rombo(gx, gy, cx, cy, altura)
        izq = tuple(int(c * 0.62) for c in base)
        der = tuple(int(c * 0.78) for c in base)
        top = tuple(min(255, int(c * 1.05)) for c in base)
        pygame.draw.polygon(self.pantalla, izq, [w, s, st, wt])
        pygame.draw.polygon(self.pantalla, der, [s, e, et, st])
        pygame.draw.polygon(self.pantalla, top, [nt, et, st, wt])
        pygame.draw.polygon(self.pantalla, C.NEGRO, [nt, et, st, wt], 1)

    def _factoria_entidad(self, ent, cx, cy):
        def dibujar():
            self._dibujar_entidad(ent, cx, cy)
        return dibujar

    def _dibujar_entidad(self, ent, cx, cy) -> None:
        sx, sy = mundo_a_pantalla(ent.x, ent.y, self.cam_x, self.cam_y, cx, cy)
        bob = math.sin(ent.paso) * 2.0 if ent.velocidad > 0 else 0.0
        # Sombra
        sombra = pygame.Surface((30, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 90), sombra.get_rect())
        self.pantalla.blit(sombra, (sx - 15, sy - 6))
        # Hábito (trapecio)
        alto_cuerpo = 30
        base_y = sy - int(bob)
        top_y = base_y - alto_cuerpo
        cuerpo = [(sx - 11, base_y), (sx + 11, base_y),
                  (sx + 7, top_y + 6), (sx - 7, top_y + 6)]
        oscuro = tuple(int(c * 0.7) for c in ent.color)
        pygame.draw.polygon(self.pantalla, ent.color, cuerpo)
        pygame.draw.polygon(self.pantalla, oscuro, cuerpo, 2)
        # Capucha / cabeza
        pygame.draw.circle(self.pantalla, (222, 200, 170), (sx, top_y + 2), 7)
        pygame.draw.circle(self.pantalla, oscuro, (sx, top_y + 2), 7, 2)
        # Etiqueta de nombre para monjes cercanos
        if isinstance(ent, Monje):
            d = math.hypot(self.guillermo.x - ent.x, self.guillermo.y - ent.y)
            if d < 3.2:
                self.hud.texto(self.pantalla, ent.nombre, sx, top_y - 12,
                               self.hud.f_pequena, C.PERGAMINO, centro=True)

    def _iluminacion(self, cx, cy) -> None:
        osc = self.reloj.oscuridad()
        if osc <= 0.01:
            return
        oscuridad = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        oscuridad.fill((6, 8, 20, int(235 * osc)))
        # "Agujero" de luz alrededor de Guillermo (linterna/lámpara)
        gx, gy = mundo_a_pantalla(self.guillermo.x, self.guillermo.y,
                                  self.cam_x, self.cam_y, cx, cy)
        radio = 190 if self.items["lampara"]["tomado"] else 120
        luz = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        for r in range(radio, 0, -8):
            a = int(255 * (1 - r / radio))
            pygame.draw.circle(luz, (0, 0, 0, a), (radio, radio), r)
        oscuridad.blit(luz, (gx - radio, gy - radio),
                       special_flags=pygame.BLEND_RGBA_SUB)
        self.pantalla.blit(oscuridad, (0, 0))

    # ------------------------------------------------------------------ #
    def _overlay_pausa(self) -> None:
        self._velo(160)
        self.hud.texto(self.pantalla, "PAUSA", C.ANCHO // 2, 240,
                       self.hud.f_titulo, C.ORO_CLARO, centro=True)
        for i, t in enumerate(["ESC/P — Reanudar", "F5 — Guardar", "Q — Menú principal"]):
            self.hud.texto(self.pantalla, t, C.ANCHO // 2, 340 + i * 40,
                           self.hud.f_media, C.PERGAMINO, centro=True)

    def _overlay_dialogo(self) -> None:
        h = 130
        panel = pygame.Surface((C.ANCHO - 160, h), pygame.SRCALPHA)
        panel.fill((22, 18, 14, 235))
        pygame.draw.rect(panel, C.ORO, panel.get_rect(), 2)
        self.pantalla.blit(panel, (80, C.ALTO - h - 110))
        self.hud.texto(self.pantalla, self.dialogo_texto, 110, C.ALTO - h - 78,
                       self.hud.f_media, C.PERGAMINO)
        self.hud.texto(self.pantalla, "(pulsa una tecla para continuar)",
                       110, C.ALTO - h - 30, self.hud.f_pequena, C.PERGAMINO_2)

    def _overlay_final(self, titulo, texto, color) -> None:
        self._velo(210)
        self.hud.texto(self.pantalla, titulo, C.ANCHO // 2, 250,
                       self.hud.f_titulo, color, centro=True)
        # Texto multilínea sencillo
        palabras = texto.split()
        linea, y = "", 350
        for p in palabras:
            if len(linea) + len(p) > 54:
                self.hud.texto(self.pantalla, linea, C.ANCHO // 2, y,
                               self.hud.f_media, C.PERGAMINO, centro=True)
                linea, y = "", y + 34
            linea += p + " "
        self.hud.texto(self.pantalla, linea, C.ANCHO // 2, y,
                       self.hud.f_media, C.PERGAMINO, centro=True)
        self.hud.texto(self.pantalla, "Pulsa una tecla para volver al menú",
                       C.ANCHO // 2, y + 80, self.hud.f_pequena, C.PERGAMINO_2, centro=True)

    def _velo(self, alpha: int) -> None:
        velo = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        velo.fill((8, 6, 4, alpha))
        self.pantalla.blit(velo, (0, 0))

    def _render_menu(self) -> None:
        self.pantalla.fill((18, 16, 14))
        # Viñeta decorativa
        for i in range(0, C.ALTO, 4):
            c = 18 + int(10 * math.sin(i * 0.03))
            pygame.draw.line(self.pantalla, (c, c - 2, c - 6), (0, i), (C.ANCHO, i))
        self.hud.texto(self.pantalla, "LA ABADÍA", C.ANCHO // 2, 150,
                       self.hud.f_titulo, C.ORO_CLARO, centro=True)
        self.hud.texto(self.pantalla, "DEL CRIMEN", C.ANCHO // 2, 218,
                       self.hud.f_titulo, C.ORO, centro=True)
        self.hud.texto(self.pantalla, "Edición 2026 · Python", C.ANCHO // 2, 275,
                       self.hud.f_media, C.PERGAMINO_2, centro=True)
        ops = self._opciones_menu()
        for i, op in enumerate(ops):
            sel = (i == self.opcion_menu)
            color = C.ORO_CLARO if sel else C.PERGAMINO
            prefijo = "» " if sel else "  "
            self.hud.texto(self.pantalla, prefijo + op, C.ANCHO // 2, 360 + i * 46,
                           self.hud.f_grande, color, centro=True)
        self.hud.texto(self.pantalla,
                       "Inspirado en la obra de Paco Menéndez y en «El nombre de la rosa»",
                       C.ANCHO // 2, C.ALTO - 40, self.hud.f_pequena,
                       C.PERGAMINO_2, centro=True)

    def _render_ayuda(self) -> None:
        self.pantalla.fill((18, 16, 14))
        self.hud.texto(self.pantalla, "CÓMO SE JUEGA", C.ANCHO // 2, 70,
                       self.hud.f_grande, C.ORO_CLARO, centro=True)
        lineas = [
            "Encarnas a fray Guillermo de Occam, investigando una serie de",
            "crímenes en una abadía benedictina. Tu novicio Adso te sigue.",
            "",
            "MOVIMIENTO:   Flechas o WASD (movimiento isométrico)",
            "CONTROLAR A ADSO:   mantén CTRL y muévete",
            "HABLAR / EXAMINAR:   E  (junto a un monje)",
            "PAUSA:   ESC o P        GUARDAR:   F5",
            "",
            "OBSEQUIUM (barra inferior derecha): tu obediencia al Abad.",
            "  · Acude a la iglesia en los oficios (Laudes, Prima, Sexta,",
            "    Vísperas, Completas).",
            "  · No deambules de noche: retírate a tu celda.",
            "  · La biblioteca está prohibida... pero guarda secretos.",
            "  Si el obsequium llega a cero, serás expulsado.",
            "",
            "OBJETIVO: reúne las 4 reliquias (llave, lentes, lámpara y",
            "pergamino) y entra en la biblioteca para hallar el libro",
            "prohibido antes de que acabe el séptimo día.",
        ]
        y = 130
        for ln in lineas:
            self.hud.texto(self.pantalla, ln, 160, y, self.hud.f_media, C.PERGAMINO)
            y += 30
        self.hud.texto(self.pantalla, "Pulsa una tecla para volver",
                       C.ANCHO // 2, C.ALTO - 40, self.hud.f_pequena,
                       C.PERGAMINO_2, centro=True)

    # ================================================================== #
    #  GUARDADO / CARGA
    # ================================================================== #
    def guardar(self) -> None:
        datos = {
            "dia": self.reloj.dia, "franja": self.reloj.franja, "t": self.reloj.t,
            "obsequium": self.obsequium,
            "guillermo": [self.guillermo.x, self.guillermo.y],
            "adso": [self.adso.x, self.adso.y],
            "items": {k: v["tomado"] for k, v in self.items.items()},
            "items_activos": {k: v["activo"] for k, v in self.items.items()},
            "monjes": [[m.x, m.y] for m in self.monjes],
        }
        try:
            with open(C.ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            self.mensaje("Partida guardada.", 3)
        except OSError as e:
            self.mensaje(f"No se pudo guardar: {e}", 4)

    def cargar(self) -> bool:
        try:
            with open(C.ARCHIVO_GUARDADO, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False
        self._nuevo_mundo()
        self.reloj.dia = d["dia"]; self.reloj.franja = d["franja"]; self.reloj.t = d["t"]
        self.obsequium = d["obsequium"]
        self.guillermo.x, self.guillermo.y = d["guillermo"]
        self.adso.x, self.adso.y = d["adso"]
        for k, tomado in d["items"].items():
            if k in self.items:
                self.items[k]["tomado"] = tomado
        for k, activo in d.get("items_activos", {}).items():
            if k in self.items:
                self.items[k]["activo"] = activo
        for m, pos in zip(self.monjes, d["monjes"]):
            m.x, m.y = pos
        self.cam_x, self.cam_y = foco_camara(self.guillermo.x, self.guillermo.y)
        self.mensaje("Partida cargada.", 3)
        return True


TILE_MARGEN = 120
