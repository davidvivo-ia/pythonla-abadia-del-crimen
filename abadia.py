#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La Abadía del Crimen — Edición 2026
====================================
Punto de entrada del juego. Ejecuta:

    python3 abadia.py

Remake moderno en Python del clásico de Paco Menéndez / Opera Soft (1987),
inspirado en «El nombre de la rosa» de Umberto Eco.

Requisitos: Python 3.10+ y pygame 2.x  (pip install -r requirements.txt)
"""
from __future__ import annotations

import sys


def _comprobar_dependencias() -> None:
    """Avisa con claridad si falta pygame, en lugar de un traceback críptico."""
    try:
        import pygame  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "\n[!] Falta la biblioteca 'pygame'.\n"
            "    Instálala con:\n\n"
            "        pip install pygame\n"
            "    o bien:\n"
            "        pip install -r requirements.txt\n\n"
        )
        sys.exit(1)

    version = sys.version_info
    if version < (3, 10):
        sys.stderr.write(
            f"\n[!] Se requiere Python 3.10 o superior "
            f"(tienes {version.major}.{version.minor}).\n\n"
        )
        sys.exit(1)


def main() -> None:
    _comprobar_dependencias()

    import pygame

    from juego import config as C
    from juego.juego import Juego

    pygame.init()
    pygame.display.set_caption(C.TITULO)
    try:
        pantalla = pygame.display.set_mode((C.ANCHO, C.ALTO))
    except pygame.error as e:
        sys.stderr.write(
            f"\n[!] No se pudo abrir la ventana de vídeo: {e}\n"
            "    ¿Estás en un entorno sin pantalla? Prueba en un escritorio local.\n\n"
        )
        sys.exit(1)

    try:
        Juego(pantalla).correr()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
