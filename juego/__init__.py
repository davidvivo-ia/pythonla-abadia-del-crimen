"""
La Abadía del Crimen — Edición 2026
====================================

Remake moderno en Python (pygame) del clásico de Paco Menéndez y Opera Soft
(1987), inspirado en «El nombre de la rosa» de Umberto Eco.

Motor isométrico propio, IA de monjes, ciclo día/noche con iluminación
dinámica, mecánica de *obsequium*, calendario de horas canónicas, inventario,
minimapa y sistema de guardado.
"""

__version__ = "2.0.0"
__all__ = [
    "config", "iso", "mapa", "pathfinding", "personajes", "objetos",
    "tiempo", "frases", "guion", "hud", "audio", "juego",
]
