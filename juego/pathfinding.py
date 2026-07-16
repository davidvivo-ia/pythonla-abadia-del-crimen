"""Búsqueda de caminos sobre la rejilla (A* con heurística Manhattan)."""
from __future__ import annotations

import heapq

from .mapa import Mapa

VECINOS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def a_estrella(mapa: Mapa, inicio: tuple[int, int],
               meta: tuple[int, int], max_nodos: int = 4000) -> list[tuple[int, int]]:
    """Devuelve una lista de tiles desde 'inicio' hasta 'meta' (excluido el inicio).

    Lista vacía si no hay camino o se supera el presupuesto de nodos.
    """
    if inicio == meta:
        return []
    if not mapa.transitable(*meta):
        return []

    frontera: list[tuple[int, int, tuple[int, int]]] = [(0, 0, inicio)]
    de_donde: dict[tuple[int, int], tuple[int, int] | None] = {inicio: None}
    coste: dict[tuple[int, int], int] = {inicio: 0}
    contador = 0

    while frontera and contador < max_nodos:
        _, _, actual = heapq.heappop(frontera)
        contador += 1
        if actual == meta:
            return _reconstruir(de_donde, meta)
        ax, ay = actual
        for dx, dy in VECINOS:
            sig = (ax + dx, ay + dy)
            if not mapa.transitable(*sig):
                continue
            nuevo = coste[actual] + 1
            if sig not in coste or nuevo < coste[sig]:
                coste[sig] = nuevo
                h = abs(sig[0] - meta[0]) + abs(sig[1] - meta[1])
                heapq.heappush(frontera, (nuevo + h, nuevo, sig))
                de_donde[sig] = actual
    return []


def _reconstruir(de_donde: dict, meta: tuple[int, int]) -> list[tuple[int, int]]:
    camino = [meta]
    actual = de_donde.get(meta)
    while actual is not None:
        camino.append(actual)
        actual = de_donde.get(actual)
    camino.reverse()
    return camino[1:]  # sin el tile de inicio
