"""Guion de los 7 días: eventos programados al cambiar de momento.

Reproduce `executeTimeOfDayActions` (ultrabolido) / `AccionesDia` (ibaca):
anuncios de los crímenes, aparición de objetos, activación de personajes,
desaparición de las gafas, llegada de Bernardo Gui y colocación de Jorge.
"""
from __future__ import annotations

from . import config as C
from . import frases


def ejecutar(j) -> None:
    """Aplica los eventos del momento actual. Se llama al cambiar de momento."""
    dia, m = j.reloj.dia, j.reloj.momento
    O, M = j.objetos, j.monjes

    if m == C.PRIMA:
        _prima(j, dia, O, M)
    elif m == C.TERCIA:
        _tercia(j, dia, O, M)
    elif m == C.SEXTA:
        _sexta(j, dia, O, M)
    elif m == C.NONA:
        _nona(j, dia, O, M)
    elif m == C.VISPERAS:
        _visperas(j, dia, O, M)
    elif m == C.NOCHE:
        _noche(j, dia, O, M)


def _anuncio(j, quien, idx) -> None:
    texto = frases.frase(idx)
    j.mensaje(f"{quien}: «{texto}»", 6)
    j.pista(f"{quien}: {texto}")


# --------------------------------------------------------------------------- #
def _prima(j, dia, O, M) -> None:
    # Al amanecer se repone el aceite de la lámpara (como resetLamp del original),
    # evitando quedar atrapado en la oscuridad de la biblioteca.
    if dia >= 3:
        j.aceite = 100.0
        if O["lampara"].oculto and O["lampara"].portador is None:
            cocina = j.mapa.planta(C.PLANTA_BAJA).anclas["cocina"]
            O["lampara"].colocar(C.PLANTA_BAJA, *cocina)

    if dia == 2:
        # Desaparecen las gafas.
        O["gafas"].oculto = True
        O["gafas"].portador = None
        j.mensaje("Tus gafas han desaparecido.", 5)
        _anuncio(j, "El Abad", 0x16)          # la biblioteca es secreta
    elif dia == 3:
        # Berengario aparece asesinado; Jorge se lleva el libro (aunque lo
        # tuviera Guillermo) y aparece en la planta baja para ser presentado.
        M["berengario"].vivo = False
        O["libro"].oculto = True
        O["libro"].portador = None
        M["jorge"].teleport(C.PLANTA_BAJA, *_tile(j, C.PLANTA_BAJA, "claustro"), home="claustro")
        M["jorge"].activo = True
        if O["pergamino"].portador != "guillermo":
            lib = j.mapa.planta(C.PLANTA_BIBLIOTECA).anclas["sala_iluminada"]
            O["pergamino"].colocar(C.PLANTA_BIBLIOTECA, *lib)
            j.mensaje("El manuscrito de Venancio ha sido llevado a la biblioteca.", 5)
        _anuncio(j, "El Abad", 0x1A)          # Berengario asesinado
    elif dia == 5:
        pass                                  # (la llave 1 se oculta en Sexta)


def _tercia(j, dia, O, M) -> None:
    if dia == 3:
        _anuncio(j, "El Abad", 0x30)          # presenta a Jorge
    elif dia == 5:
        # Malaquías mata a Severino y luego muere envenenado por el libro.
        M["severino"].vivo = False
        M["malaquias"].vivo = False
        _anuncio(j, "El Abad", 0x1C)          # Severino asesinado y encerrado
        _anuncio(j, "Malaquías", 0x1F)        # "tenía el poder de mil escorpiones"
        _anuncio(j, "El Abad", 0x20)          # Malaquías ha muerto


def _sexta(j, dia, O, M) -> None:
    if dia == 4:
        # Llega Bernardo Gui.
        M["bernardo"].activo = True
        M["bernardo"].teleport(C.PLANTA_BAJA, *_tile(j, C.PLANTA_BAJA, "entrada"))
        _anuncio(j, "El Abad", 0x11)          # abandonad la investigación
    elif dia == 5:
        # La llave del altar se retira si nadie la ha cogido (ventana: Noche→Sexta).
        if O["llave1"].en_suelo:
            O["llave1"].oculto = True


def _nona(j, dia, O, M) -> None:
    if dia == 3:
        M["jorge"].activo = False             # Jorge desaparece


def _visperas(j, dia, O, M) -> None:
    if dia == 2:
        _anuncio(j, "El Abad", 0x18)          # Berengario ha desaparecido
    elif dia == 5:
        M["bernardo"].activo = False
        _anuncio(j, "El Abad", 0x1D)          # Bernardo se marcha


def _noche(j, dia, O, M) -> None:
    if dia == 5:
        # Aparecen las gafas (sala iluminada) y la llave 1 (altar).
        if O["gafas"].portador is None:
            lib = j.mapa.planta(C.PLANTA_BIBLIOTECA).anclas["sala_iluminada"]
            O["gafas"].colocar(C.PLANTA_BIBLIOTECA, *lib)
            j.mensaje("Tus gafas han aparecido en la sala iluminada de la biblioteca.", 6)
        altar = j.mapa.planta(C.PLANTA_BAJA).anclas["altar"]
        O["llave1"].colocar(C.PLANTA_BAJA, *altar)
        j.mensaje("Una llave brilla sobre el altar de la iglesia (hasta Sexta).", 6)
    elif dia == 6:
        mm = j.mapa.planta(C.PLANTA_SCRIPTORIUM).anclas["mesa_malaquias"]
        O["llave2"].colocar(C.PLANTA_SCRIPTORIUM, *mm)
        j.mensaje("Una llave ha quedado sobre la mesa de Malaquías (scriptorium).", 6)
        M["jorge"].teleport(C.PLANTA_BIBLIOTECA, *_tile(j, C.PLANTA_BIBLIOTECA, "espejo"),
                            home="sala_espejo")
        M["jorge"].activo = True
        _anuncio(j, "El Abad", 0x1E)          # mañana abandonaréis


def _tile(j, planta, ancla) -> tuple[int, int]:
    gx, gy = j.mapa.planta(planta).anclas.get(ancla, (5, 5))
    return int(gx), int(gy)
