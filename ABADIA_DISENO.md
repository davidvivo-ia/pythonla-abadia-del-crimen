# La Abadía del Crimen — Edición 2026
### Documento de diseño y guía completa de desarrollo en Python

> Remake moderno del clásico de **Paco Menéndez** y **Opera Soft** (1987),
> inspirado en *El nombre de la rosa* de **Umberto Eco**.
> Motor isométrico propio en **Python + pygame**. Ejecutable: `python3 abadia.py`.

---

## Índice

1. [El juego original: investigación y contexto](#1-el-juego-original)
2. [Análisis de mecánicas a replicar](#2-análisis-de-mecánicas)
3. [Visión del remake 2026 ("vitaminado")](#3-visión-del-remake-2026)
4. [Arquitectura del software](#4-arquitectura-del-software)
5. [Paso a paso: cómo se ha construido](#5-paso-a-paso-de-construcción)
6. [Matemática de la proyección isométrica](#6-proyección-isométrica)
7. [Descripción módulo a módulo](#7-módulos)
8. [Bucle de juego y máquina de estados](#8-bucle-y-estados)
9. [Reglas: obsequium, horario y victoria](#9-reglas-de-juego)
10. [Cómo ejecutar, jugar y depurar](#10-ejecución)
11. [Hoja de ruta: cómo seguir vitaminándolo](#11-hoja-de-ruta)
12. [Créditos y fuentes](#12-créditos-y-fuentes)

---

## 1. El juego original

**La Abadía del Crimen** (1987) es una aventura isométrica programada por Paco
Menéndez con gráficos y diseño de Juan Delcán para Opera Soft. Al no conseguir
los derechos del nombre de la novela de Eco, se publicó como *La Abadía del
Crimen*. Está considerado uno de los mejores videojuegos de la era de los 8 bits
(Amstrad CPC, ZX Spectrum, MSX, MS-DOS).

**Argumento.** Encarnas a **Fray Guillermo de Occam** (el Guillermo de
Baskerville de la novela) acompañado de tu novicio **Adso de Melk**. El Abad os
encarga investigar la muerte de un monje. Durante **siete días**, mientras
suceden nuevos crímenes, debéis recorrer la abadía, cumplir la disciplina
monástica y desentrañar el misterio, que conduce a una **biblioteca-laberinto**
prohibida.

**Claves técnicas del original:**

- Perspectiva **isométrica** con scroll por estancias (el "Videograph engine").
- **IA de personajes**: los monjes se mueven por el mapa con rutinas propias y
  muestran diálogos de texto.
- **Reloj de horas canónicas**: el tiempo avanza y marca obligaciones.
- Mecánica de **obsequium** (obediencia) que limita la libertad del jugador.
- Márgenes de error mínimos: objetos disponibles solo en ventanas de tiempo, y
  *game over* instantáneos si te sales del guion.
- Música de Bach y Schubert; famosa protección anti-copia (`¡Pirata!`).

El repositorio de referencia
[`luzbel/vigasocosdl-la-abadia-del-crimen`](https://github.com/luzbel/vigasocosdl-la-abadia-del-crimen)
contiene el **desensamblado en ensamblador** del original (`abadia.asm`,
`depurador.asm`, mapas de memoria/ROM/disco). Es la fuente canónica para
entender la lógica de bajo nivel; aquí la reinterpretamos a alto nivel en Python.

---

## 2. Análisis de mecánicas

Del original extraemos los pilares que un remake fiel debe conservar:

| Mecánica | Descripción | En nuestro remake |
|---|---|---|
| **Movimiento isométrico** | Guillermo se mueve en 8 direcciones sobre rombos 2:1 | `iso.py` + colisión con deslizamiento |
| **Adso** | Sigue a Guillermo; se puede controlar aparte | Seguimiento con distancia + control con `CTRL` |
| **Horas canónicas** | Maitines→Laudes→Prima→…→Completas→Noche | `tiempo.py` (`Reloj`) |
| **Obsequium** | Barra de obediencia que baja con infracciones | `Juego._obsequium()` |
| **Oficios obligatorios** | Hay que estar en la iglesia a ciertas horas | zona requerida por franja |
| **Noche** | Deambular está penalizado; oscuridad | iluminación dinámica + drenaje |
| **Objetos con propósito** | Llave, lentes, lámpara, libro… | sistema de reliquias |
| **Biblioteca-laberinto** | Zona prohibida y meta final | tabiques internos + libro final |
| **IA de monjes** | Deambulan y hablan | `entidades.Monje` con A* |
| **Siete días** | Estructura temporal con final | contador de día y *game over* al 7.º |

---

## 3. Visión del remake 2026

"Vitaminarlo" significa conservar el alma del clásico y añadir todo lo que hoy
se espera de un juego hecho en Python:

- **Motor isométrico propio** con *depth sorting* (algoritmo del pintor),
  muros extruidos en 3/4 y sombras.
- **Ciclo día/noche con iluminación dinámica**: de noche cae la oscuridad y
  Guillermo lleva un halo de luz (mayor si porta la lámpara), con mezcla
  sustractiva de superficies (`BLEND_RGBA_SUB`).
- **HUD completo**: reloj de horas canónicas, barra de obsequium, inventario de
  reliquias y **minimapa** en vivo.
- **IA con A\*** (`pathfinding.py`) para que los monjes naveguen la abadía.
- **Máquina de estados**: menú, juego, pausa, diálogo, *game over*, victoria y
  pantalla de ayuda.
- **Guardar/cargar** en JSON (tecla `F5`).
- **Estética "pergamino"**: paleta de claroscuro medieval y tipografía serif.
- **Código limpio, modular y comentado en español**, fácil de extender.

Todo autocontenido: una sola dependencia (`pygame`) y un único ejecutable
`abadia.py`.

---

## 4. Arquitectura del software

```
pythonla-abadia-del-crimen/
├── abadia.py                 ← LANZADOR (punto de entrada único)
├── requirements.txt          ← dependencias (pygame; numpy opcional)
├── ABADIA_DISENO.md          ← este documento
├── COMPARATIVA_Y_MEJORAS.md  ← comparativa con el original y plan de mejora
├── README.md                 ← guía rápida
├── assets/                   ← capturas / recursos
└── juego/                    ← paquete del juego
    ├── __init__.py
    ├── config.py             ← constantes canónicas, paleta, horario
    ├── iso.py                ← proyección isométrica y cámara
    ├── mapa.py               ← 3 plantas (abadía, scriptorium, biblioteca) + escaleras
    ├── pathfinding.py        ← A* sobre la rejilla
    ├── personajes.py         ← Guillermo, Adso y los 6 monjes con IA por horarios
    ├── objetos.py            ← los 8 objetos y su función
    ├── tiempo.py             ← reloj de días y 7 horas canónicas
    ├── frases.py             ← diálogos reales en español + intro/final
    ├── guion.py              ← eventos programados de los 7 días
    ├── hud.py                ← interfaz: obsequium, reloj, inventario, minimapa
    ├── audio.py              ← campanas procedurales (opcional)
    └── juego.py              ← núcleo: bucle, estados, render y reglas
```

> **Nota de versiones.** La v1.0 fue una interpretación libre. La **v2.0**
> (actual) reconstruye el juego a partir de la ingeniería inversa del original;
> la comparativa completa y las fuentes están en
> [`COMPARATIVA_Y_MEJORAS.md`](COMPARATIVA_Y_MEJORAS.md).

**Principio de diseño:** separación por responsabilidades. `config.py` centraliza
todos los números "mágicos" para poder ajustar el balance sin tocar la lógica.
`juego.py` orquesta; el resto son piezas reutilizables y testeables por separado.

---

## 5. Paso a paso de construcción

Estos son los pasos que seguirías (y que se siguieron) para generar el juego
desde cero:

1. **Investigar el original** (repositorio en ensamblador + documentación) y
   extraer las mecánicas de la [sección 2](#2-análisis-de-mecánicas).
2. **Preparar el entorno**:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install pygame
   ```
3. **Definir la configuración** (`config.py`): resolución, tamaño de tile
   isométrico (`64×32`), paleta, lista de horas canónicas y parámetros de
   obsequium.
4. **Escribir la proyección isométrica** (`iso.py`): fórmulas mundo↔pantalla y
   clave de profundidad. Ver [sección 6](#6-proyección-isométrica).
5. **Generar el mapa** (`mapa.py`): estancias rectangulares (iglesia, claustro,
   scriptorium, biblioteca, refectorio, cocina, sala capitular, enfermería,
   celdas, cripta) conectadas por pasillos en L, con puertas automáticas y un
   laberinto interno en la biblioteca. Cada tile guarda **tipo** y **zona**.
6. **Implementar el pathfinding** (`pathfinding.py`): A* con heurística
   Manhattan para la IA.
7. **Crear las entidades** (`entidades.py`): clase base con movimiento suave y
   colisión eje-a-eje (deslizamiento); Guillermo (input), Adso (seguimiento) y
   Monje (patrulla con A*).
8. **Modelar el tiempo** (`tiempo.py`): avance de franjas, día y nivel de
   oscuridad para la iluminación.
9. **Dibujar el HUD** (`hud.py`): panel inferior con reloj, reliquias y
   obsequium, más minimapa y mensajes flotantes.
10. **Ensamblar el núcleo** (`juego.py`): bucle principal, máquina de estados,
    render isométrico en dos pasadas (suelos → objetos ordenados), iluminación,
    reglas de obsequium, recogida de objetos y guardado.
11. **Escribir el lanzador** (`abadia.py`): comprobación de dependencias y
    arranque de la ventana.
12. **Probar** en modo *headless* (`SDL_VIDEODRIVER=dummy`) para validar
    conectividad del mapa, condición de victoria y ausencia de errores, y
    generar capturas.

---

## 6. Proyección isométrica

Usamos rombos **2:1** (ancho doble que alto). Con `TILE_W=64`, `TILE_H=32`:

```
sx = (gx - gy) * (TILE_W / 2)      # coordenada X en pantalla
sy = (gx + gy) * (TILE_H / 2)      # coordenada Y en pantalla
```

donde `(gx, gy)` son coordenadas de mundo en tiles (pueden ser flotantes para
movimiento suave). A esto se le resta la **cámara** y se le suma el centro de la
pantalla para centrar a Guillermo.

**Ordenación por profundidad (algoritmo del pintor):** todo lo que está "más
abajo-derecha" se dibuja después. La clave es:

```
profundidad = gx + gy
```

El render se hace en **dos pasadas**:

1. **Suelos**: todos los rombos de suelo (el orden entre ellos es indiferente).
2. **Objetos altos y entidades**: muros extruidos, altar, camas y personajes,
   todos ordenados por `profundidad` para que se ocluyan correctamente (una
   pared delante tapa a un monje detrás, y viceversa).

Los **muros** se dibujan como bloques 3/4: cara izquierda y derecha (más
oscuras) más la cara superior (rombo elevado `ALTURA_MURO` píxeles).

Las **direcciones de entrada** se convierten a ejes de rejilla para que
"arriba" en el teclado suba en diagonal por la pantalla:

```
Arriba  → (-1, -1)      Abajo → (+1, +1)
Izq.    → (-1, +1)      Der.  → (+1, -1)
```

---

## 7. Módulos

### `config.py`
Todas las constantes: ventana, `FPS`, tamaños de tile, velocidades, **paleta**
cromática, **colores por zona**, tipos de tile, la tabla de **horas canónicas**
`HORAS` (clave, nombre, es_noche, es_servicio, zona_requerida), parámetros de
**obsequium** y nombre del archivo de guardado.

### `iso.py`
`mundo_a_pantalla()`, `profundidad()` y `foco_camara()`. Matemática pura, sin
estado: fácil de testear.

### `mapa.py`
Clase `Mapa`: rejilla de `48×42`. A partir de una lista de `Estancia`
(rectángulos con zona) talla suelos y muros, conecta centros con pasillos en L
(`_pasillo`), abre **puertas** donde un pasillo cruza un muro, añade el
**laberinto** de la biblioteca y coloca decorados (altar, camas). Expone
`transitable()`, `transitable_punto()` (colisión circular) y `zona()`.

### `pathfinding.py`
`a_estrella()`: A* clásico con `heapq`, heurística Manhattan y presupuesto de
nodos para no bloquear el hilo. Devuelve la lista de tiles del camino.

### `entidades.py`
- `Entidad`: posición flotante, `_mover()` con colisión **eje a eje** (permite
  resbalar por las paredes) y fase de animación de balanceo.
- `Guillermo`: se mueve según la entrada normalizada del jugador.
- `Adso`: sigue a Guillermo manteniendo distancia; controlable con `CTRL`.
- `Monje`: elige metas aleatorias transitables y las alcanza con A*; guarda una
  frase de diálogo.

### `tiempo.py`
Clase `Reloj`: acumula segundos, avanza de **franja** y de **día**, marca el fin
del juego al superar el 7.º día y calcula el nivel de **oscuridad** para la
iluminación.

### `hud.py`
Clase `HUD`: carga fuentes serif, dibuja el **panel inferior** (reloj a la
izquierda, reliquias en el centro, obsequium a la derecha — igual que el
original), el **minimapa** (muros, puertas, items, monjes y Guillermo) y los
**mensajes** flotantes.

### `juego.py`
Clase `Juego`: el director de orquesta.
- `_nuevo_mundo()` instancia mapa, personajes, reloj, reliquias y monjes.
- `correr()` es el bucle principal (dt fijo por `Clock.tick`).
- `_actualizar()` gestiona entrada, física, IA, cámara, obsequium, items y
  tiempo.
- `_render_mundo()` hace las dos pasadas isométricas + iluminación.
- Estados de UI: menú, ayuda, pausa, diálogo, *game over*, victoria.
- `guardar()` / `cargar()` serializan el estado en JSON.

---

## 8. Bucle y estados

```
        ┌──────┐  Nueva partida   ┌─────────┐
        │ MENU │ ───────────────► │ JUGANDO │◄─────┐
        └──────┘                  └─────────┘      │ (tecla)
           ▲   ▲ Continuar/Ayuda   │  │  │         │
           │   └───────────────────┘  │  │   ┌─────────┐
   (tecla) │       obsequium=0 /      │  │   │ DIÁLOGO │
           │       7.º día  ─────► GAMEOVER  └─────────┘
           │                          │
           │        libro hallado ► VICTORIA
           │                          │
           └────────── PAUSA ◄────────┘  (ESC/P)
```

El bucle mantiene **60 FPS** con `pygame.time.Clock`. El `dt` se limita a
`0.05 s` para que un pico de latencia no atraviese paredes.

---

## 9. Reglas de juego

### Horario canónico (fiel al original)
Cada día tiene **7 momentos** (`config.HORAS` → `NOCHE, PRIMA, TERCIA, SEXTA,
NONA, VÍSPERAS, COMPLETAS`). La partida empieza en **Día 1 · Nona**. Algunos
momentos exigen estar en un sitio:

- **Oficios** (Prima, Vísperas) → **iglesia**.
- **Comida** (Sexta) → **refectorio**.
- **Descanso** (Completas, Noche) → **tu celda**.

### Obsequium (obediencia)
Entero de **0 a 31** (como en el original). **Solo baja**, de **2 en 2**, y
**nunca se regenera**. Se penaliza por infracciones puntuales:

| Infracción | Frase del Abad | Efecto |
|---|---|---|
| Faltar a un oficio | «Llegáis tarde, fray Guillermo» | **−2** |
| No ocupar tu sitio en la comida | «Ocupad vuestro sitio» | **−2** |
| No dormir en tu celda | «Entrad en vuestra celda» | **−2** |
| No entregar el manuscrito al Abad | «Dadme el manuscrito» | **−2** |

Si el obsequium baja de **0** → *game over*: «No habéis respetado mis órdenes.
Abandonad para siempre esta abadía».

### Objetos (8) y objetivo
Los **8 objetos** del original: **libro, guantes, gafas, pergamino, 3 llaves y
lámpara**. Para ganar debes: reunir **guantes**, **gafas** y **pergamino**;
subir al **scriptorium** y a la **biblioteca** (a oscuras: necesitas la
**lámpara** que porta Adso); resolver el **enigma del espejo** (número romano
IXX/XIX/XXI) y llegar ante **Jorge** el 6.º/7.º día. Con los **guantes**
sobrevives al **libro envenenado** y **resuelves el misterio**; sin ellos,
mueres. Otras muertes: obsequium a 0, perderse en la oscuridad, o agotarse el
7.º día. La puntuación final sigue la fórmula del original:
`7·(día−1) + momento + 4·bonus`.

---

## 10. Ejecución

### Instalación
```bash
pip install -r requirements.txt      # o: pip install pygame
```

### Arrancar el juego
```bash
python3 abadia.py
```

### Controles

| Acción | Tecla |
|---|---|
| Mover a Guillermo | Flechas o `W A S D` |
| Controlar a Adso | mantén `CTRL` + mover |
| Acción (hablar / escaleras / espejo) | `E` |
| Pausa | `ESC` o `P` |
| Guardar | `F5` |
| Menú / continuar | flechas + `Enter` |

### Depuración *headless*
Para validar sin pantalla (CI, servidores):
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -c "import abadia"
```
El juego incluye comprobaciones de que el mapa es **conexo** y de que la partida
es **ganable** (todas las reliquias son alcanzables desde el punto de inicio).

---

## 11. Hoja de ruta

Ideas para seguir "vitaminando" el proyecto:

- **Audio**: música de fondo (Bach/Schubert de dominio público) y efectos de
  campanas al cambiar de hora.
- **Sprites**: sustituir las figuras geométricas por *sprites* isométricos.
- **Guion narrativo por días**: los crímenes de la novela (Adelmo, Venancio,
  Berengario, Severino, Malaquías) con pistas y diálogos evolutivos.
- **IA avanzada**: rutinas horarias por monje (cada uno acude a los oficios).
- **El laberinto de la biblioteca** como puzle de orientación con pergaminos.
- **Inventario interactivo** y combinación de objetos (lentes + pergamino).
- **Empaquetado**: `PyInstaller` para generar un ejecutable de escritorio.
- **Accesibilidad**: remapeo de teclas, escalado de UI, modo alto contraste.

---

## 11-bis. Capa de presentación "next-gen" (v3.0)

Sobre el motor base se añade una capa de presentación moderna, toda en pygame
puro (sin shaders ni dependencias nuevas; `numpy` sólo para el audio):

- **Pipeline de post-procesado** (`efectos.PostFX`): el mundo se dibuja en un
  **lienzo** intermedio y se le aplica **bloom** (resplandor: umbralizado +
  desenfoque por reescalado en 1/5 de resolución, sumado en aditivo),
  **viñeta** (degradado radial precomputado) y **grano** fílmico (tiles de ruido
  precomputados). Todo cacheado para ir sobrado de 60 FPS.
- **Iluminación dinámica** (`_iluminacion`): antorchas cálidas por estancia con
  **parpadeo** (halos aditivos con brillo prehorneado en 6 niveles y cacheados),
  velas del altar, y la **lámpara** de Adso que abre un cono de luz en la
  biblioteca a oscuras. La oscuridad se "perfora" con máscaras radiales cacheadas.
- **Sistema de partículas** (`efectos.Particulas`): motas de polvo en suspensión,
  **llamas** en cada luz, **chispas** al recoger objetos y polvo de pisadas,
  proyectadas en el mundo isométrico.
- **Sacudida de cámara** en campanas, penalizaciones y muertes.
- **Transiciones** con fundido entre estados y **HUD glassmorphism** (paneles de
  cristal con borde de neón), **ticker de objetivo** y **códice de detective**
  (`codex.Codex`, tecla `J`) que registra las pistas descubiertas.
- **Toggle de rendimiento**: `F` activa/desactiva el post-procesado.

El truco de integración clave: los *helpers* de dibujo siguen escribiendo en
`self.pantalla`, pero durante el render del mundo esa referencia se intercambia
temporalmente por el lienzo intermedio; así se añadió todo el pipeline sin tocar
el código de dibujo isométrico existente.

---

## 12. Créditos y fuentes

- **Original (1987):** Paco Menéndez (programación), Juan Delcán (gráficos),
  Opera Soft.
- **Inspiración literaria:** *El nombre de la rosa*, Umberto Eco (1980).
- **Desensamblado de referencia:**
  <https://github.com/luzbel/vigasocosdl-la-abadia-del-crimen>
- **Documentación consultada:**
  - <https://en.wikipedia.org/wiki/La_Abad%C3%ADa_del_Crimen>
  - <https://www.mobygames.com/game/14113/la-abadia-del-crimen/>
  - <https://gamefaqs.gamespot.com/cpc/939396-la-abadia-del-crimen>

> Este remake es un homenaje educativo y no comercial. Todos los derechos de la
> obra original pertenecen a sus autores.
