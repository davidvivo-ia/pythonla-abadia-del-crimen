"""Proyección isométrica y utilidades de cámara.

Convenio de coordenadas:
    (gx, gy)  -> coordenadas de mundo en tiles (pueden ser flotantes)
    (sx, sy)  -> coordenadas de pantalla en píxeles

Proyección rómbica (2:1) clásica:
    sx = (gx - gy) * (TILE_W / 2)
    sy = (gx + gy) * (TILE_H / 2)
"""
from __future__ import annotations

from .config import TILE_W, TILE_H


def mundo_a_pantalla(gx: float, gy: float, cam_x: float, cam_y: float,
                     centro_x: int, centro_y: int) -> tuple[int, int]:
    """Convierte coordenadas de tile a píxeles de pantalla, aplicando cámara."""
    sx = (gx - gy) * (TILE_W / 2) - cam_x + centro_x
    sy = (gx + gy) * (TILE_H / 2) - cam_y + centro_y
    return int(sx), int(sy)


def profundidad(gx: float, gy: float) -> float:
    """Clave de ordenación para el pintor: mayor = más cerca de cámara."""
    return gx + gy


def foco_camara(gx: float, gy: float) -> tuple[float, float]:
    """Píxeles a los que la cámara debe apuntar para centrar (gx, gy)."""
    cam_x = (gx - gy) * (TILE_W / 2)
    cam_y = (gx + gy) * (TILE_H / 2)
    return cam_x, cam_y
