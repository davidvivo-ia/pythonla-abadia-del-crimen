"""Núcleo del juego: bucle, estados, render isométrico y reglas canónicas."""
from __future__ import annotations

import json
import math
import os
import random

import pygame

from . import config as C
from . import frases, guion
from .audio import Audio
from .codex import Codex
from .efectos import Particulas, PostFX
from .hud import HUD
from .iso import foco_camara, mundo_a_pantalla, profundidad
from .mapa import Mapa
from .objetos import construir_objetos
from .personajes import DEF_MONJES, Adso, Guillermo, Monje
from .tiempo import Reloj

MENU, INTRO, JUGANDO, PAUSA, DIALOGO, GAMEOVER, VICTORIA, AYUDA, FINAL = range(9)

TILE_MARGEN = 140
COOLDOWN_ESCALERA = 0.5


class Juego:
    def __init__(self, pantalla) -> None:
        self.pantalla = pantalla
        self.lienzo = pygame.Surface((C.ANCHO, C.ALTO)).convert()
        self.reloj_fps = pygame.time.Clock()
        self.hud = HUD()
        self.audio = Audio()
        self.fx = PostFX(C.ANCHO, C.ALTO)
        self.particulas = Particulas()
        self.rng = random.Random(1327)
        self.estado = MENU
        self.opcion_menu = 0
        self.ejecutando = True
        self.fx_on = True
        self.mostrar_codex = False
        self.shake = 0.0
        self.fade = 0.0
        self._estado_prev = MENU
        self._dt = 0.016
        self._glow_cache: dict = {}
        self._mask_cache: dict = {}
        # Superficies reutilizadas cada frame (evitan reservas de memoria).
        self._sombra = pygame.Surface((30, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(self._sombra, (0, 0, 0, 90), self._sombra.get_rect())
        self._oscuridad = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        self._nuevo_mundo()

    # ------------------------------------------------------------------ #
    def _nuevo_mundo(self) -> None:
        self.mapa = Mapa()
        baja = self.mapa.planta(C.PLANTA_BAJA)
        cx, cy = baja.ancla("iglesia")
        self.guillermo = Guillermo(cx, cy + 2, C.PLANTA_BAJA)
        self.adso = Adso(cx - 1, cy + 3, C.PLANTA_BAJA)
        self.reloj = Reloj()
        self.obsequium = C.OBSEQUIUM_MAX
        self.objetos = construir_objetos(self.mapa)
        self.monjes = {}
        for clave, nombre, color, planta, home, frase_base in DEF_MONJES:
            px, py = self.mapa.planta(planta).ancla(home)
            m = Monje(px, py, planta, color, nombre, home, frase_base)
            if clave in ("jorge", "bernardo"):
                m.activo = False
            self.monjes[clave] = m

        self.cam_x, self.cam_y = foco_camara(self.guillermo.x, self.guillermo.y)
        self.mensajes: list[list] = []
        self.dialogo_texto = ""
        self.bonus: set[str] = set()
        self.romano = self.rng.randrange(3)          # índice IXX/XIX/XXI
        self.cd_escalera = 0.0
        self.cnt_oscuras = 0.0
        self.aceite = 100.0
        self.mensaje_final = ""
        self.clima_resuelto = False
        self.codex = Codex()
        self.particulas = Particulas()
        self.shake = 0.0
        self.mostrar_codex = False

    def mensaje(self, txt, dur=4.0) -> None:
        self.mensajes.append([txt, dur])
        if len(self.mensajes) > 4:
            self.mensajes.pop(0)

    def pista(self, texto) -> None:
        """Registra una pista en el códice con su sello temporal."""
        self.codex.anotar(f"D{self.reloj.dia}·{self.reloj.nombre}", texto)

    def sacudir(self, fuerza=6.0) -> None:
        self.shake = max(self.shake, fuerza)

    @property
    def planta_actual(self):
        return self.mapa.planta(self.guillermo.planta)

    # ================================================================== #
    def correr(self) -> None:
        while self.ejecutando:
            dt = min(self.reloj_fps.tick(C.FPS) / 1000.0, 0.05)
            self._dt = dt
            self._eventos()
            if self.estado == JUGANDO:
                self._actualizar(dt)
            self._render()
            pygame.display.flip()

    def _eventos(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.ejecutando = False
            elif ev.type == pygame.KEYDOWN:
                self._tecla(ev.key)

    def _tecla(self, key) -> None:
        if self.estado == MENU:
            self._tecla_menu(key)
        elif self.estado == INTRO:
            self.estado = JUGANDO
            self.mensaje(f"El Abad: «{frases.frase(0x01)}»", 6)
            self.mensaje(f"El Abad: «{frases.frase(0x02)}»", 7)
        elif self.estado == JUGANDO:
            if self.mostrar_codex and key not in (pygame.K_j, pygame.K_ESCAPE):
                return
            if key in (pygame.K_ESCAPE, pygame.K_p):
                if self.mostrar_codex:
                    self.mostrar_codex = False
                else:
                    self.estado = PAUSA
            elif key == pygame.K_e:
                self._interactuar()
            elif key == pygame.K_j:
                self.mostrar_codex = not self.mostrar_codex
            elif key == pygame.K_f:
                self.fx_on = not self.fx_on
            elif key == pygame.K_F5:
                self.guardar()
        elif self.estado == PAUSA:
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.estado = JUGANDO
            elif key == pygame.K_q:
                self.estado = MENU
            elif key == pygame.K_F5:
                self.guardar()
        elif self.estado == DIALOGO:
            self.estado = JUGANDO
        elif self.estado == VICTORIA:
            self.estado = FINAL
        elif self.estado in (GAMEOVER, AYUDA, FINAL):
            self.estado = MENU

    def _tecla_menu(self, key) -> None:
        ops = self._opciones_menu()
        if key in (pygame.K_UP, pygame.K_w):
            self.opcion_menu = (self.opcion_menu - 1) % len(ops)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.opcion_menu = (self.opcion_menu + 1) % len(ops)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._elegir_menu(ops[self.opcion_menu])

    def _opciones_menu(self):
        ops = ["Nueva partida"]
        if os.path.exists(C.ARCHIVO_GUARDADO):
            ops.append("Continuar")
        ops += ["Cómo se juega", "Salir"]
        return ops

    def _elegir_menu(self, op) -> None:
        if op == "Nueva partida":
            self._nuevo_mundo()
            self.estado = INTRO
        elif op == "Continuar":
            if self.cargar():
                self.estado = JUGANDO
        elif op == "Cómo se juega":
            self.estado = AYUDA
        elif op == "Salir":
            self.ejecutando = False

    # ================================================================== #
    #  ACTUALIZACIÓN
    # ================================================================== #
    def _actualizar(self, dt) -> None:
        teclas = pygame.key.get_pressed()
        control_adso = teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]
        entrada = self._entrada_direccion(teclas)
        planta = self.planta_actual

        if control_adso:
            self.guillermo.actualizar(planta, (0, 0), dt)
            self.adso.actualizar(planta, self.guillermo, entrada, dt)
        else:
            self.guillermo.actualizar(planta, entrada, dt)
            self.adso.actualizar(planta, self.guillermo, None, dt)

        for m in self.monjes.values():
            m.actualizar(self.mapa, self.reloj, dt, self.rng)

        self.cd_escalera = max(0.0, self.cd_escalera - dt)
        self.shake = max(0.0, self.shake - dt * 22.0)
        self._camara(dt)
        self._recoger_objetos()
        self._oscuridad_biblioteca(dt)
        self.particulas.actualizar(dt, self)

        prev_m = self.reloj.momento
        if self.reloj.actualizar(dt):
            self._penalizar_ausencia(prev_m)
            guion.ejecutar(self)
            self._campanas()

        for msg in self.mensajes:
            msg[1] -= dt
        self.mensajes = [m for m in self.mensajes if m[1] > 0]

        if self.reloj.fin_del_juego and not self.clima_resuelto:
            self._fin(f"El Abad: «{frases.frase(0x25)}» Se acaba el séptimo día.")

    def _entrada_direccion(self, teclas):
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

    def _camara(self, dt) -> None:
        ox, oy = foco_camara(self.guillermo.x, self.guillermo.y)
        k = min(1.0, dt * 6.0)
        self.cam_x += (ox - self.cam_x) * k
        self.cam_y += (oy - self.cam_y) * k

    def _recoger_objetos(self) -> None:
        g = self.guillermo
        for obj in self.objetos.values():
            if not obj.en_suelo or obj.planta != g.planta:
                continue
            if math.hypot(g.x - (obj.gx + 0.5), g.y - (obj.gy + 0.5)) < 0.85:
                obj.portador = "adso" if obj.clave in ("lampara", "llave3") else "guillermo"
                self.mensaje(f"Recoges: {obj.nombre}.", 4)
                self.pista(f"Objeto hallado: {obj.nombre}.")
                self.particulas.emitir(obj.gx + 0.5, obj.gy + 0.5, "chispa", 14, z=8)
                self._bonus_objeto(obj.clave)
                # El enigma se revela en cuanto se reúnen gafas y pergamino,
                # sea cual sea el orden en que se recojan.
                if obj.clave in ("gafas", "pergamino") and self.tiene("gafas") \
                        and self.tiene("pergamino"):
                    self.mensaje(f"El pergamino revela: «{self._enigma()}»", 7)
                    self.pista(f"Enigma del espejo: {self._enigma()}")

    def _bonus_objeto(self, clave) -> None:
        if clave in ("guantes", "llave1", "llave2", "llave3"):
            self.bonus.add(clave)

    def _oscuridad_biblioteca(self, dt) -> None:
        if self.guillermo.planta != C.PLANTA_BIBLIOTECA:
            self.cnt_oscuras = 0.0
            return
        self.bonus.add("biblioteca")
        con_luz = self.objetos["lampara"].portador == "adso" and self.aceite > 0
        # En la sala del espejo y la iluminada hay luz propia.
        zona = self.planta_actual.zona(*self.guillermo.tile)
        if zona == "espejo":
            con_luz = True
        if con_luz:
            self.cnt_oscuras = 0.0
            if self.objetos["lampara"].portador == "adso" and self.aceite > 0:
                antes = self.aceite
                self.aceite = max(0.0, self.aceite - dt * 2.0)
                if antes > 40 >= self.aceite:
                    self.mensaje(f"Adso: «{frases.frase(0x28)}»", 4)   # la lámpara se agota
                if self.aceite == 0:
                    self.mensaje(f"Adso: «{frases.frase(0x2A)}»", 4)   # se ha agotado
        else:
            antes = self.cnt_oscuras
            self.cnt_oscuras += dt
            if antes <= 1.0 < self.cnt_oscuras:               # aviso una sola vez
                self.mensaje(f"Adso: «{frases.frase(0x13)}»", 4)
            if self.cnt_oscuras > 12.0:
                self._fin(f"Adso: «{frases.frase(0x2B)}»")

    def _penalizar_ausencia(self, momento) -> None:
        g = self.guillermo
        zona = self.mapa.planta(C.PLANTA_BAJA).zona(*g.tile) if g.planta == C.PLANTA_BAJA else ""
        falta = None
        if momento in C.MOMENTO_IGLESIA:
            if not (g.planta == C.PLANTA_BAJA and zona == "iglesia"):
                falta = 0x06
        elif momento in C.MOMENTO_REFECTORIO:
            if not (g.planta == C.PLANTA_BAJA and zona == "refectorio"):
                falta = 0x2D
        elif momento in C.MOMENTO_CELDA:
            if not (g.planta == C.PLANTA_BAJA and zona == "celda"):
                falta = 0x10
        if falta is not None:
            self._decrementa_obsequium(falta)

    def _decrementa_obsequium(self, idx_frase) -> None:
        self.obsequium -= C.OBSEQUIUM_PENALIZACION
        self.mensaje(f"El Abad: «{frases.frase(idx_frase)}»  (−2 obsequium)", 5)
        self.sacudir(5.0)
        if self.obsequium < 0:
            self.obsequium = 0
            self._fin(f"El Abad: «{frases.frase(0x0E)}»")

    def _campanas(self) -> None:
        r = self.reloj
        self.audio.tocar_campana()
        self.sacudir(3.0)
        if r.momento in C.MOMENTO_IGLESIA:
            self.mensaje(f"Campanas: {r.nombre}. Acude a la iglesia. «{frases.frase(0x17)}»", 5)
        elif r.momento in C.MOMENTO_REFECTORIO:
            self.mensaje(f"{r.nombre}: comida en el refectorio. «{frases.frase(0x19)}»", 5)
        elif r.momento == C.COMPLETAS:
            self.mensaje(f"«{frases.frase(0x0D)}» Retírate a tu celda.", 5)

    # ------------------------------------------------------------------ #
    def _interactuar(self) -> None:
        g = self.guillermo
        # 1) Escaleras
        esc = self.mapa.escalera_en(g.planta, int(g.x), int(g.y))
        if esc and self.cd_escalera <= 0:
            planta, gx, gy = esc
            g.planta = planta
            g.x, g.y = gx + 0.5, gy + 0.5
            # Adso aparece sobre la misma escalera (siempre transitable) y se
            # separa solo al seguir a Guillermo; así nunca nace dentro de un muro.
            self.adso.planta = planta
            self.adso.x, self.adso.y = g.x, g.y
            self.cam_x, self.cam_y = foco_camara(g.x, g.y)
            self.cd_escalera = COOLDOWN_ESCALERA
            self.mensaje(f"Entras en: {C.NOMBRE_PLANTA[planta]}.", 3)
            return
        # 2) Espejo (clímax)
        if g.planta == C.PLANTA_BIBLIOTECA:
            ex, ey = self.planta_actual.ancla("espejo")
            if math.hypot(g.x - ex, g.y - ey) < 2.0:
                self._espejo()
                return
        # 3) Diálogo con monje cercano
        cerca, mejor = None, 1.8
        for m in self.monjes.values():
            if m.vivo and m.activo and m.planta == g.planta:
                d = math.hypot(g.x - m.x, g.y - m.y)
                if d < mejor:
                    mejor, cerca = d, m
        if cerca:
            self.dialogo_texto = f"{cerca.nombre}: «{cerca.frase_base}»"
            self.pista(f"{cerca.nombre}: {cerca.frase_base}")
            self.estado = DIALOGO

    def _espejo(self) -> None:
        self.bonus.add("sala_espejo")
        if not (self.tiene("pergamino") and self.tiene("gafas")):
            self.mensaje(f"El espejo no cede. Necesitas el pergamino y las gafas. «{self._enigma_pista()}»", 6)
            return
        if not self.monjes["jorge"].activo or self.reloj.dia < 6:
            self.mensaje("Tras el espejo no hay nadie aún. (Jorge aparece el 6º día).", 5)
            return
        self.bonus.add("espejo_abierto")
        # Clímax
        if self.tiene("guantes"):
            self.mensaje(f"Jorge: «{frases.frase(0x21)}»", 6)
            self.mensaje(f"Jorge: «{frases.frase(0x2E)}»", 8)
            self.mensaje(f"Adso: «{frases.frase(0x23)}»", 9)
            self.mensaje(f"Jorge: «{frases.frase(0x2F)}»", 6)
            self._victoria()
        else:
            self.mensaje(f"Jorge: «{frases.frase(0x21)}»", 6)
            self._fin(f"«{frases.frase(0x22)}»  (te faltaban los guantes)")

    # ------------------------------------------------------------------ #
    def tiene(self, clave) -> bool:
        return self.objetos[clave].portador == "guillermo"

    def _enigma(self) -> str:
        return frases.frase(0x00, ROMANO=C.NUMEROS_ROMANOS[self.romano])

    def _enigma_pista(self) -> str:
        return frases.frase(0x33)

    def _victoria(self) -> None:
        self.clima_resuelto = True
        self.bonus.update({"gafas_pergamino"})
        self.estado = VICTORIA

    def _fin(self, texto) -> None:
        if self.clima_resuelto:
            return
        self.clima_resuelto = True
        self.mensaje_final = texto
        self.sacudir(12.0)
        self.estado = GAMEOVER

    def _porcentaje(self) -> int:
        a = 7 * (self.reloj.dia - 1) + self.reloj.momento + 4 * len(self.bonus)
        a = 0 if a < 5 else a
        return min(100, a)

    # ================================================================== #
    #  RENDER
    # ================================================================== #
    def _render(self) -> None:
        if self.estado != self._estado_prev:
            # Crossfade sólo en cambios "de pantalla"; abrir o cerrar un overlay
            # (pausa, diálogo) sobre el juego no funde a negro.
            en_juego = {JUGANDO, PAUSA, DIALOGO}
            if not (self.estado in en_juego and self._estado_prev in en_juego):
                self.fade = 1.0
            self._estado_prev = self.estado

        if self.estado == MENU:
            self._render_menu()
            self._filmico_ligero()
        elif self.estado == AYUDA:
            self._render_ayuda()
            self._filmico_ligero()
        elif self.estado == INTRO:
            self._render_texto(frases.INTRO, "LA ABADÍA DEL CRIMEN")
            self._filmico_ligero()
        elif self.estado == FINAL:
            self._render_texto(frases.FINAL, f"MISIÓN: {self._porcentaje()}%")
            self._filmico_ligero()
        else:
            self._render_mundo()                 # escribe en self.pantalla ya post-procesado
            if self.estado in (JUGANDO, PAUSA, DIALOGO):
                self.hud.dibujar(self.pantalla, self)
                self._ticker_objetivo()
            if self.estado == PAUSA:
                self._overlay_pausa()
            elif self.estado == DIALOGO:
                self._overlay_dialogo()
            elif self.estado == GAMEOVER:
                self._overlay_final("FIN", self.mensaje_final, C.ROJO)
            elif self.estado == VICTORIA:
                self._overlay_final(
                    "MISTERIO RESUELTO",
                    "Adso te delató a tiempo: llevabas guantes y el veneno de las "
                    "páginas no llegó a tus labios. Jorge de Burgos, acorralado, "
                    "devoró el libro envenenado. Has resuelto el crimen de la abadía.",
                    C.ORO)
            if self.mostrar_codex and self.estado == JUGANDO:
                self._overlay_codex()

        self._dibujar_transicion()

    def _filmico_ligero(self) -> None:
        if self.fx_on:
            self.fx.velo_filmico(self.pantalla)

    def _dibujar_transicion(self) -> None:
        if self.fade <= 0.0:
            return
        self.fade = max(0.0, self.fade - self._dt * 2.6)
        velo = pygame.Surface((C.ANCHO, C.ALTO))
        velo.set_alpha(int(self.fade * 255))
        velo.fill((6, 5, 4))
        self.pantalla.blit(velo, (0, 0))

    # ---- UI moderna: paneles "glass", ticker de objetivo y códice -------- #
    def _glass(self, rect, alpha=150, borde=C.ORO, glow=True) -> None:
        x, y, w, h = rect
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((18, 20, 28, alpha))
        # brillo superior (glassmorphism)
        top = pygame.Surface((w, h // 2), pygame.SRCALPHA)
        top.fill((90, 110, 140, 26))
        panel.blit(top, (0, 0))
        self.pantalla.blit(panel, (x, y))
        if glow:
            borde_s = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
            pygame.draw.rect(borde_s, (*borde, 130), borde_s.get_rect(),
                             width=2, border_radius=8)
            self.pantalla.blit(borde_s, (x - 3, y - 3), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(self.pantalla, borde, (x, y, w, h), 1, border_radius=6)

    def _ticker_objetivo(self) -> None:
        obj = self.codex.objetivo(self)
        w = 430
        self._glass((16, 16, w, 62), alpha=140, borde=(90, 170, 220))
        self.hud.texto(self.pantalla, "◈ OBJETIVO", 30, 24, self.hud.f_pequena, (140, 200, 240))
        self.hud.texto(self.pantalla, obj, 30, 42, self.hud.f_media, C.PERGAMINO)
        self.hud.texto(self.pantalla, "[J] Códice   [F] Efectos", 30, 66,
                       self.hud.f_pequena, (150, 150, 160))

    def _overlay_codex(self) -> None:
        self._velo(170)
        w, h = 820, 520
        x, y = (C.ANCHO - w) // 2, (C.ALTO - h) // 2
        self._glass((x, y, w, h), alpha=210, borde=(90, 170, 220))
        self.hud.texto(self.pantalla, "CÓDICE DE LA INVESTIGACIÓN", x + w // 2, y + 34,
                       self.hud.f_grande, (150, 200, 240), centro=True)
        self.hud.texto(self.pantalla, self.codex.objetivo(self), x + w // 2, y + 70,
                       self.hud.f_media, C.ORO_CLARO, centro=True)
        pygame.draw.line(self.pantalla, (90, 120, 150), (x + 30, y + 92),
                         (x + w - 30, y + 92), 1)
        cy = y + 108
        pistas = self.codex.pistas[-13:]
        if not pistas:
            self.hud.texto(self.pantalla, "Aún no has descubierto ninguna pista.",
                           x + w // 2, cy + 30, self.hud.f_media, C.PERGAMINO_2, centro=True)
        for sello, texto in pistas:
            self.hud.texto(self.pantalla, sello, x + 30, cy, self.hud.f_pequena, (150, 190, 230))
            t = texto if len(texto) < 78 else texto[:75] + "…"
            self.hud.texto(self.pantalla, t, x + 130, cy, self.hud.f_pequena, C.PERGAMINO)
            cy += 30
        self.hud.texto(self.pantalla, "[J] Cerrar", x + w // 2, y + h - 24,
                       self.hud.f_pequena, (150, 150, 160), centro=True)

    def _render_mundo(self) -> None:
        planta = self.planta_actual
        real = self.pantalla
        self.pantalla = self.lienzo          # los helpers dibujan en el lienzo
        try:
            self.lienzo.fill(C.AZUL_NOCHE if self.reloj.es_noche else (34, 40, 46))
            sh = self.shake
            ox = self.rng.uniform(-sh, sh) if sh > 0.2 else 0
            oy = self.rng.uniform(-sh, sh) if sh > 0.2 else 0
            cx, cy = C.ANCHO // 2 + int(ox), C.ALTO // 2 - 40 + int(oy)
            objetos_dibujo = []

            for gy in range(planta.alto):
                for gx in range(planta.ancho):
                    t = planta.tiles[gy][gx]
                    if t == C.VACIO:
                        continue
                    sx, sy = mundo_a_pantalla(gx, gy, self.cam_x, self.cam_y, cx, cy)
                    if not (-TILE_MARGEN < sx < C.ANCHO + TILE_MARGEN and
                            -TILE_MARGEN < sy < C.ALTO + TILE_MARGEN):
                        continue
                    if t in (C.SUELO, C.PUERTA, C.ALTAR, C.CAMA, C.ESCALERA, C.ESPEJO, C.MESA):
                        self._suelo(planta, gx, gy, cx, cy, t)
                    if t in (C.MURO, C.ALTAR, C.CAMA, C.ESPEJO, C.MESA):
                        objetos_dibujo.append((profundidad(gx, gy),
                                               lambda gx=gx, gy=gy, t=t: self._bloque(planta, gx, gy, cx, cy, t)))

            for obj in self.objetos.values():
                if obj.en_suelo and obj.planta == self.guillermo.planta:
                    objetos_dibujo.append((profundidad(obj.gx, obj.gy) + 0.3,
                                           lambda o=obj: self._objeto(o, cx, cy)))
            ents = [m for m in self.monjes.values()
                    if m.vivo and m.activo and m.planta == self.guillermo.planta]
            ents += [self.adso, self.guillermo]
            for e in ents:
                objetos_dibujo.append((profundidad(e.x, e.y) + 0.4,
                                       lambda e=e: self._entidad(e, cx, cy)))

            objetos_dibujo.sort(key=lambda o: o[0])
            for _, fn in objetos_dibujo:
                fn()

            self._iluminacion(planta, cx, cy)
            self.particulas.dibujar(self.lienzo, self, cx, cy)
        finally:
            self.pantalla = real

        if self.fx_on:
            self.fx.aplicar(self.lienzo, real, self._dt)
        else:
            real.blit(self.lienzo, (0, 0))

    def _rombo(self, gx, gy, cx, cy, dz=0):
        n = mundo_a_pantalla(gx, gy, self.cam_x, self.cam_y, cx, cy)
        e = mundo_a_pantalla(gx + 1, gy, self.cam_x, self.cam_y, cx, cy)
        s = mundo_a_pantalla(gx + 1, gy + 1, self.cam_x, self.cam_y, cx, cy)
        w = mundo_a_pantalla(gx, gy + 1, self.cam_x, self.cam_y, cx, cy)
        if dz:
            n = (n[0], n[1] - dz); e = (e[0], e[1] - dz)
            s = (s[0], s[1] - dz); w = (w[0], w[1] - dz)
        return n, e, s, w

    def _suelo(self, planta, gx, gy, cx, cy, t) -> None:
        zona = planta.zona(gx, gy)
        color, borde = C.COLORES_ZONA.get(zona, C.COLORES_ZONA["claustro"])
        if t == C.PUERTA:
            color = tuple(min(255, c + 25) for c in color)
        elif t == C.ESCALERA:
            color = (120, 170, 120)
        if (gx + gy) % 2 == 0:
            color = tuple(max(0, c - 10) for c in color)
        rombo = self._rombo(gx, gy, cx, cy)
        pygame.draw.polygon(self.pantalla, color, rombo)
        pygame.draw.polygon(self.pantalla, borde, rombo, 1)

    def _bloque(self, planta, gx, gy, cx, cy, t) -> None:
        if t == C.MURO:
            altura, base = C.ALTURA_MURO, C.GRIS_PIEDRA
            if planta.zona(gx, gy) == "biblioteca":
                base = (96, 78, 60)
        elif t == C.ALTAR:
            altura, base = 24, C.ORO
        elif t == C.ESPEJO:
            altura, base = 34, (170, 190, 210)
        elif t == C.MESA:
            altura, base = 12, (120, 92, 64)
        else:
            altura, base = 12, (120, 70, 60)
        n, e, s, w = self._rombo(gx, gy, cx, cy)
        nt, et, st, wt = self._rombo(gx, gy, cx, cy, altura)
        izq = tuple(int(c * 0.62) for c in base)
        der = tuple(int(c * 0.78) for c in base)
        top = tuple(min(255, int(c * 1.05)) for c in base)
        pygame.draw.polygon(self.pantalla, izq, [w, s, st, wt])
        pygame.draw.polygon(self.pantalla, der, [s, e, et, st])
        pygame.draw.polygon(self.pantalla, top, [nt, et, st, wt])
        pygame.draw.polygon(self.pantalla, C.NEGRO, [nt, et, st, wt], 1)

    def _objeto(self, obj, cx, cy) -> None:
        sx, sy = mundo_a_pantalla(obj.gx + 0.5, obj.gy + 0.5, self.cam_x, self.cam_y, cx, cy)
        pulso = 3 + int(2 * math.sin(self.reloj.t * 4))
        pygame.draw.circle(self.pantalla, C.ORO_CLARO, (sx, sy - 6), 8 + pulso, 0)
        pygame.draw.circle(self.pantalla, C.ORO, (sx, sy - 6), 8)
        pygame.draw.circle(self.pantalla, C.NEGRO, (sx, sy - 6), 8, 1)
        self.hud.texto(self.pantalla, obj.icono, sx, sy - 6, self.hud.f_pequena,
                       C.NEGRO, sombra=False, centro=True)

    def _entidad(self, ent, cx, cy) -> None:
        sx, sy = mundo_a_pantalla(ent.x, ent.y, self.cam_x, self.cam_y, cx, cy)
        bob = math.sin(ent.paso) * 2.0 if ent.velocidad > 0 else 0.0
        self.pantalla.blit(self._sombra, (sx - 15, sy - 6))
        base_y = sy - int(bob)
        top_y = base_y - 30
        cuerpo = [(sx - 11, base_y), (sx + 11, base_y), (sx + 7, top_y + 6), (sx - 7, top_y + 6)]
        oscuro = tuple(int(c * 0.7) for c in ent.color)
        pygame.draw.polygon(self.pantalla, ent.color, cuerpo)
        pygame.draw.polygon(self.pantalla, oscuro, cuerpo, 2)
        pygame.draw.circle(self.pantalla, (222, 200, 170), (sx, top_y + 2), 7)
        pygame.draw.circle(self.pantalla, oscuro, (sx, top_y + 2), 7, 2)
        if isinstance(ent, Monje) and math.hypot(self.guillermo.x - ent.x, self.guillermo.y - ent.y) < 3.4:
            self.hud.texto(self.pantalla, ent.nombre, sx, top_y - 12,
                           self.hud.f_pequena, C.PERGAMINO, centro=True)

    def _glow(self, radio, color, nivel):
        """Halo aditivo con brillo prehorneado (nivel 0..5) — sin copias por frame."""
        key = (radio, color, nivel)
        s = self._glow_cache.get(key)
        if s is None:
            b = nivel / 5.0
            s = pygame.Surface((radio * 2, radio * 2)).convert()
            s.fill((0, 0, 0))
            for r in range(radio, 0, -6):
                f = ((1 - r / radio) ** 1.4) * b
                pygame.draw.circle(s, (int(color[0] * f), int(color[1] * f),
                                       int(color[2] * f)), (radio, radio), r)
            self._glow_cache[key] = s
        return s

    def _mask(self, radio):
        s = self._mask_cache.get(radio)
        if s is None:
            s = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            for r in range(radio, 0, -8):
                a = int(255 * (1 - r / radio) ** 1.2)
                pygame.draw.circle(s, (0, 0, 0, a), (radio, radio), r)
            self._mask_cache[radio] = s
        return s

    def _iluminacion(self, planta, cx, cy) -> None:
        con_lampara = self.objetos["lampara"].portador == "adso" and self.aceite > 0
        osc = self.reloj.oscuridad()
        if planta.oscura:
            zona = planta.zona(*self.guillermo.tile)
            osc = 0.55 if (con_lampara or zona == "espejo") else 0.95
        t = self.reloj.t + self.reloj.dia * 3.0

        # 1) Halos cálidos aditivos de las antorchas (ambiente, con parpadeo).
        base = 0.9 if osc > 0.15 else 0.45
        for i, (lx, ly, color, radio) in enumerate(planta.luces):
            sx, sy = mundo_a_pantalla(lx + 0.5, ly + 0.5, self.cam_x, self.cam_y, cx, cy)
            if not (-radio < sx < C.ANCHO + radio and -radio < sy < C.ALTO + radio):
                continue
            flick = 0.72 + 0.22 * math.sin(t * 7 + i * 1.7) + self.rng.uniform(-0.05, 0.05)
            nivel = max(1, min(5, round(base * max(0.35, flick) * 5)))
            g = self._glow(radio, color, nivel)
            self.pantalla.blit(g, (sx - radio, sy - radio), special_flags=pygame.BLEND_RGB_ADD)

        if osc <= 0.01:
            return

        # 2) Oscuridad con "agujeros" de luz (jugador + antorchas).
        oscuridad = self._oscuridad
        oscuridad.fill((6, 8, 20, int(238 * osc)))
        gx, gy = mundo_a_pantalla(self.guillermo.x, self.guillermo.y, self.cam_x, self.cam_y, cx, cy)
        radio_j = 210 if con_lampara else 130
        m = self._mask(radio_j)
        oscuridad.blit(m, (gx - radio_j, gy - radio_j), special_flags=pygame.BLEND_RGBA_SUB)
        for lx, ly, _color, radio in planta.luces:
            sx, sy = mundo_a_pantalla(lx + 0.5, ly + 0.5, self.cam_x, self.cam_y, cx, cy)
            if not (-radio < sx < C.ANCHO + radio and -radio < sy < C.ALTO + radio):
                continue
            oscuridad.blit(self._mask(radio), (sx - radio, sy - radio),
                           special_flags=pygame.BLEND_RGBA_SUB)
        self.pantalla.blit(oscuridad, (0, 0))

    # ------------------------------------------------------------------ #
    def _velo(self, alpha) -> None:
        velo = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        velo.fill((8, 6, 4, alpha))
        self.pantalla.blit(velo, (0, 0))

    def _overlay_pausa(self) -> None:
        self._velo(160)
        self.hud.texto(self.pantalla, "PAUSA", C.ANCHO // 2, 230, self.hud.f_titulo,
                       C.ORO_CLARO, centro=True)
        for i, t in enumerate(["ESC/P — Reanudar", "F5 — Guardar", "Q — Menú"]):
            self.hud.texto(self.pantalla, t, C.ANCHO // 2, 330 + i * 38,
                           self.hud.f_media, C.PERGAMINO, centro=True)

    def _overlay_dialogo(self) -> None:
        h = 140
        panel = pygame.Surface((C.ANCHO - 160, h), pygame.SRCALPHA)
        panel.fill((22, 18, 14, 235))
        pygame.draw.rect(panel, C.ORO, panel.get_rect(), 2)
        self.pantalla.blit(panel, (80, C.ALTO - h - 110))
        self._texto_multilinea(self.dialogo_texto, 110, C.ALTO - h - 88, 74)
        self.hud.texto(self.pantalla, "(pulsa una tecla)", 110, C.ALTO - 130,
                       self.hud.f_pequena, C.PERGAMINO_2)

    def _overlay_final(self, titulo, texto, color) -> None:
        self._velo(215)
        self.hud.texto(self.pantalla, titulo, C.ANCHO // 2, 220, self.hud.f_titulo,
                       color, centro=True)
        self._texto_multilinea(texto, C.ANCHO // 2, 320, 56, centro=True)
        self.hud.texto(self.pantalla, "Pulsa una tecla para continuar",
                       C.ANCHO // 2, C.ALTO - 120, self.hud.f_pequena,
                       C.PERGAMINO_2, centro=True)

    def _texto_multilinea(self, texto, x, y, ancho, centro=False):
        palabras, linea = texto.split(), ""
        for p in palabras:
            if len(linea) + len(p) > ancho:
                self.hud.texto(self.pantalla, linea, x, y, self.hud.f_media,
                               C.PERGAMINO, centro=centro)
                linea, y = "", y + 30
            linea += p + " "
        self.hud.texto(self.pantalla, linea, x, y, self.hud.f_media, C.PERGAMINO, centro=centro)

    def _render_menu(self) -> None:
        self.pantalla.fill((18, 16, 14))
        for i in range(0, C.ALTO, 4):
            c = 18 + int(10 * math.sin(i * 0.03))
            pygame.draw.line(self.pantalla, (c, c - 2, c - 6), (0, i), (C.ANCHO, i))
        self.hud.texto(self.pantalla, "LA ABADÍA", C.ANCHO // 2, 130, self.hud.f_titulo, C.ORO_CLARO, centro=True)
        self.hud.texto(self.pantalla, "DEL CRIMEN", C.ANCHO // 2, 195, self.hud.f_titulo, C.ORO, centro=True)
        self.hud.texto(self.pantalla, "Edición 2026 · Python", C.ANCHO // 2, 248,
                       self.hud.f_media, C.PERGAMINO_2, centro=True)
        for i, op in enumerate(self._opciones_menu()):
            sel = i == self.opcion_menu
            self.hud.texto(self.pantalla, ("» " if sel else "  ") + op, C.ANCHO // 2,
                           330 + i * 44, self.hud.f_grande,
                           C.ORO_CLARO if sel else C.PERGAMINO, centro=True)
        self.hud.texto(self.pantalla,
                       "Inspirado en la obra de Paco Menéndez y «El nombre de la rosa»",
                       C.ANCHO // 2, C.ALTO - 36, self.hud.f_pequena, C.PERGAMINO_2, centro=True)

    def _render_texto(self, lineas, titulo) -> None:
        self.pantalla.fill((16, 14, 12))
        self.hud.texto(self.pantalla, titulo, C.ANCHO // 2, 90, self.hud.f_grande,
                       C.ORO_CLARO, centro=True)
        y = 180
        for ln in lineas:
            self.hud.texto(self.pantalla, ln, C.ANCHO // 2, y, self.hud.f_media,
                           C.PERGAMINO, centro=True)
            y += 34
        self.hud.texto(self.pantalla, "Pulsa una tecla para continuar",
                       C.ANCHO // 2, C.ALTO - 60, self.hud.f_pequena, C.PERGAMINO_2, centro=True)

    def _render_ayuda(self) -> None:
        self.pantalla.fill((18, 16, 14))
        self.hud.texto(self.pantalla, "CÓMO SE JUEGA", C.ANCHO // 2, 60, self.hud.f_grande, C.ORO_CLARO, centro=True)
        lineas = [
            "Eres fray Guillermo de Occam; Adso, tu novicio, te acompaña.",
            "Investiga los crímenes de la abadía durante siete días.",
            "",
            "MOVIMIENTO: flechas o WASD (isométrico)",
            "CONTROLAR A ADSO: mantén CTRL y muévete",
            "ACCIÓN (hablar / escaleras / espejo): E",
            "CÓDICE de pistas: J     EFECTOS visuales: F",
            "PAUSA: ESC/P     GUARDAR: F5",
            "",
            "OBSEQUIUM (0–31): tu obediencia. Acude a los oficios (Prima,",
            "Vísperas), a la comida (Sexta) y duerme en tu celda (Completas,",
            "Noche). Cada falta resta 2. Si baja de 0, el Abad te expulsa.",
            "",
            "OBJETIVO: reúne guantes, gafas y el pergamino; sube por las",
            "escaleras al scriptorium y a la biblioteca (necesitas la lámpara",
            "de Adso en la oscuridad); resuelve el enigma del espejo y llega",
            "ante Jorge el 6º/7º día. Con los GUANTES sobrevivirás al libro",
            "envenenado y resolverás el misterio.",
        ]
        y = 120
        for ln in lineas:
            self.hud.texto(self.pantalla, ln, 150, y, self.hud.f_media, C.PERGAMINO)
            y += 29
        self.hud.texto(self.pantalla, "Pulsa una tecla para volver",
                       C.ANCHO // 2, C.ALTO - 40, self.hud.f_pequena, C.PERGAMINO_2, centro=True)

    # ================================================================== #
    #  GUARDADO / CARGA
    # ================================================================== #
    def guardar(self) -> None:
        datos = {
            "dia": self.reloj.dia, "momento": self.reloj.momento, "t": self.reloj.t,
            "obsequium": self.obsequium, "romano": self.romano, "aceite": self.aceite,
            "guillermo": [self.guillermo.x, self.guillermo.y, self.guillermo.planta],
            "adso": [self.adso.x, self.adso.y, self.adso.planta],
            "bonus": list(self.bonus),
            "objetos": {k: [o.portador, o.oculto, o.planta, o.gx, o.gy]
                        for k, o in self.objetos.items()},
            "monjes": {k: [m.x, m.y, m.planta, m.vivo, m.activo]
                       for k, m in self.monjes.items()},
            "codex": self.codex.to_dict(),
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
        self.reloj.dia, self.reloj.momento, self.reloj.t = d["dia"], d["momento"], d["t"]
        self.obsequium = d["obsequium"]
        self.romano = d.get("romano", 0)
        self.aceite = d.get("aceite", 100.0)
        self.guillermo.x, self.guillermo.y, self.guillermo.planta = d["guillermo"]
        self.adso.x, self.adso.y, self.adso.planta = d["adso"]
        self.bonus = set(d.get("bonus", []))
        for k, (portador, oculto, planta, gx, gy) in d["objetos"].items():
            if k in self.objetos:
                o = self.objetos[k]
                o.portador, o.oculto, o.planta, o.gx, o.gy = portador, oculto, planta, gx, gy
        for k, (x, y, planta, vivo, activo) in d["monjes"].items():
            if k in self.monjes:
                m = self.monjes[k]
                m.x, m.y, m.planta, m.vivo, m.activo = x, y, planta, vivo, activo
        if "codex" in d:
            self.codex.from_dict(d["codex"])
        self.cam_x, self.cam_y = foco_camara(self.guillermo.x, self.guillermo.y)
        self.mensaje("Partida cargada.", 3)
        return True
