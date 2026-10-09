# Comparativa con el original y plan de mejora

Documento que compara la primera versión de este remake con los **datos
canónicos** extraídos de las fuentes de ingeniería inversa, y detalla el plan de
mejora aplicado para maximizar la fidelidad al juego de 1987.

## Fuentes estudiadas

| Fuente | Lenguaje | Qué aportó |
|---|---|---|
| [luzbel/vigasocosdl-la-abadia-del-crimen](https://github.com/luzbel/vigasocosdl-la-abadia-del-crimen) + [Nicholas-Campbell/TheAbbeyOfCrime](https://github.com/Nicholas-Campbell/TheAbbeyOfCrime) (`khaz/` desensamblado de Manuel Abadía) | Z80 ASM | Mapa de memoria, los 57 mensajes, tabla de duración de etapas, mecánica de obsequium (`0x2d7f`), enigma del espejo, fórmula de puntuación |
| [ibaca/la-abadia-del-crimen](https://github.com/ibaca/la-abadia-del-crimen) | Java | Roster de 8 personajes con máquinas de estado, planta de 3 niveles (`plantas[3][256]`), init de objetos/puertas, guion por días |
| [ultrabolido/abadia](https://github.com/ultrabolido/abadia) | JavaScript | **Frases reales en español** (`phrases.json`), matrices de estancias (`floors.json`), enums de objetos, `executeTimeOfDayActions` |
| [Samuel85/Abbey](https://github.com/Samuel85/Abbey) · [carstene1ns/AbbeyOfCrime](https://github.com/carstene1ns/AbbeyOfCrime) | C++ (VIGASOCO) | Validación cruzada del calendario de eventos (`AccionesDia.cpp`) |

## Comparativa

| Aspecto | Versión 1.0 (inicial) | Original / canónico | Versión 2.0 (esta) |
|---|---|---|---|
| **Horas canónicas** | 11 franjas inventadas | 7: Noche, Prima, Tercia, Sexta, Nona, Vísperas, Completas | ✅ Las 7 reales |
| **Inicio** | Día 1, franja libre | Día 1, **Nona**, obsequium **31** | ✅ Fiel |
| **Obsequium** | 0–100, drenaje continuo | **0–31**, solo baja **−2** por infracción puntual; nunca sube; a 0 → expulsión | ✅ Fiel (por eventos) |
| **Personajes** | 7 genéricos inventados | 8 reales: Guillermo, Adso, Abad, Malaquías, Berengario, Severino, Jorge (ciego), Bernardo Gui | ✅ Los 8 con rol y guion |
| **Objetos** | 4 reliquias inventadas | 8: libro, guantes, gafas, pergamino, 3 llaves, lámpara | ✅ Los 8 con función real |
| **Mapa** | 1 planta generada | **3 plantas**: baja, scriptorium, biblioteca-laberinto | ✅ 3 plantas con escaleras |
| **Biblioteca** | Zona con tabiques | Laberinto **a oscuras**, requiere lámpara; sala del espejo | ✅ Oscura + enigma del espejo |
| **Trama** | Sin guion | 7 días con muertes y diálogos programados | ✅ Guion día a día |
| **Diálogos** | Inventados | Frases reales en español (`GestorFrases`/`phrases.json`) | ✅ Textos verbatim |
| **Final** | "Coge el libro" | Jorge, el libro envenenado, guantes, incendio | ✅ Clímax fiel + % de misión |
| **Muertes del jugador** | Solo obsequium 0 | Obsequium, leer sin guantes, trampa del espejo, oscuridad, día 7 | ✅ Todas |

## Plan de mejora aplicado (v2.0)

1. **Reloj fiel** (`tiempo.py`): 7 momentos con nombres españoles, días 1–7,
   tabla de duración `DURATION[7][7]` del original, inicio en Día 1 · Nona.
2. **Obsequium canónico** (`juego.py`): entero 0–31, penalizaciones puntuales
   de −2 (llegar tarde a un oficio, no ocupar tu sitio, no dormir en la celda,
   no soltar el pergamino ante el Abad), sin regeneración; expulsión al bajar de
   0, con la frase real 14.
3. **8 personajes reales** (`personajes.py`) con rutinas horarias (acuden a la
   iglesia en Prima/Vísperas, al refectorio en Sexta, a su celda de noche) y
   máquinas de estado por personaje (Malaquías mata a Severino, Jorge en el
   espejo, Bernardo persigue el pergamino…).
4. **8 objetos funcionales** (`objetos.py`): las gafas + el pergamino revelan el
   enigma; los guantes salvan de leer el libro envenenado; la lámpara ilumina la
   biblioteca y se agota; las llaves y el pergamino dan bonus.
5. **Mapa de 3 plantas** (`mapa.py`): planta baja (iglesia, claustro, cocina,
   refectorio, celdas, enfermería, sala capitular), scriptorium y
   biblioteca-laberinto a oscuras con la sala del espejo, unidas por escaleras.
6. **Guion de 7 días** (`guion.py`): anuncios de los crímenes (Venancio,
   Berengario, Severino, Malaquías), llegada de Bernardo el día 4, desaparición
   de las gafas el día 2, aparición de llaves/lámpara, y el desenlace con Jorge.
7. **Enigma del espejo**: número romano aleatorio (IXX/XIX/XXI) y elección de la
   escalera correcta; acierto abre el pasadizo, error = trampa mortal.
8. **Textos del pergamino**: introducción (monólogo de Adso) y final (el
   incendio de la abadía) reales, y **porcentaje de misión** con la fórmula
   `7·(día−1) + momento + 4·bonus`.
9. **Diálogos reales en español** (`frases.py`) mostrados por proximidad (`E`).
10. **Audio procedural opcional** (`audio.py`): campanas al cambiar de oficio,
    generadas sin ficheros externos (si hay `numpy`).

> Nota de alcance: la **geometría exacta** de cada pantalla del original vive en
> los datos binarios de la ROM (`abadia*.bin`), no en código. Aquí se reconstruye
> una planta fiel *en espíritu* (estancias, conexiones, laberinto y escaleras)
> sin copiar esos binarios propiedad de Opera Soft.

## Versión 3.0 — capa de presentación "next-gen" 2026

Sobre la base fiel v2.0 se añadió una capa de presentación moderna (ver detalle
técnico en `ABADIA_DISENO.md`, sección 11-bis):

- Post-procesado **bloom + viñeta + grano** fílmico (módulo `efectos.py`).
- **Iluminación dinámica**: antorchas cálidas parpadeantes por estancia, velas y
  la lámpara de aceite, con oscuridad perforada por máscaras de luz.
- **Partículas**: polvo en suspensión, llamas, chispas al recoger objetos y
  polvo de pisadas.
- **Sacudida de cámara** y **transiciones** con fundido entre estados.
- **HUD glassmorphism** con **ticker de objetivo** y **códice de detective**
  (`codex.py`, tecla `J`) que registra las pistas.
- Todo en pygame puro y cacheado: se mantiene por encima de 60 FPS, con un
  interruptor (`F`) para desactivar el post-procesado en equipos modestos.

## Versión 3.1 — auditoría adversarial (dos revisores independientes)

Una revisión línea a línea más un revisor independiente sin acceso a las
conclusiones del primero produjeron 24 hallazgos; los reales se corrigieron:

- **Jugabilidad**: la sala del espejo estaba sellada por su propio decorado
  (juego inganable andando) → entrada lateral y **verificación automática de
  conexidad** al construir el mapa; la lámpara no recargaba aceite (soft-lock)
  → se repone al amanecer; aviso al entrar en la biblioteca sin lámpara.
- **Narrativa**: los diálogos del clímax nunca se mostraban → **escena de
  diálogos encadenados**; los eventos del día 1 eran código muerto → se lanzan
  al salir de la intro; Berengario seguía vivo tras su asesinato; el enigma del
  espejo no se resolvía → ahora hay que **teclear el número romano** (1/2/3) y
  fallar es la trampa; **Bernardo Gui arrebata el manuscrito** (−2); los
  monjes rotan sus frases canónicas en vez de repetir una.
- **Robustez**: `cargar()` validado contra guardados dañados (aviso en el
  menú); ruta de guardado absoluta; índice del menú seguro; `tipo()/zona()`
  aceptan flotantes; mensajes largos se parten en líneas en vez de aplastarse.
- **Legibilidad**: nombres de estancia en el mundo, HUD y minimapa; noche
  legible; ticker de objetivo con la obligación horaria y la ubicación real
  de cada objeto.
- **Rendimiento**: suelo de cada planta pre-renderizado (−1 600 polígonos por
  frame), minimapa cacheado en la planta, partículas independientes del
  frame-rate; porcentaje de misión normalizado al 100 %.
