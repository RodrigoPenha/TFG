# TFG

Algoritmo genético para buscar contrafactuales de grupo sobre grafos de conectividad
cerebral (ADHD-200). Python 3.12, dependencias con [uv](https://docs.astral.sh/uv/).

## Instalación

```bash
uv sync
```

Todo se ejecuta con `uv run python <script>.py`.

## Ejecución

```bash
# 1. grupos de grafos de entrada (una vez): crea grafos_<fuente>/N<tam>/clase<c>.pkl
uv run python buscar_grafos_cercanos.py
uv run python buscar_grafos_lejanos.py
uv run python buscar_grafos_aleatorios.py

# 2a. campaña completa: todos los grupos x todas las combinaciones de parámetros
uv run python experimentacion.py                    # o: ... cercanos lejanos
# 2b. una sola ejecución
uv run python Algoritmo.py
# 2c. comparación de los tres operadores de cruce
uv run python experimentacion_cruces.py

# 3. análisis
uv run python calcular_cota_inferior.py   # -> cota_inferior.txt
uv run python comprobar_validez.py        # -> comprobar_validez.txt
```

Resultados: `experimentacion.py` → `experimentos/<fuente>/N<tam>/` (JSON + PNG/GraphML con
marca de tiempo, no se sobrescriben); `experimentacion_cruces.py` → `experimentos_cruces/`;
`Algoritmo.py` → `resultados.csv` y las imágenes de nombre fijo del directorio raíz
(se sobrescriben en cada ejecución).

## Dónde se configura

Ningún script lee parámetros por línea de órdenes (salvo las fuentes de
`experimentacion.py`): se editan en el propio fichero.

| Qué | `experimentacion.py` (bloque `CONFIGURACIÓN`) | `Algoritmo.py` (bloque `if __name__ == "__main__":`) |
| --- | --- | --- |
| Grafos de entrada | `FUENTES`, `TAMANOS_GRUPO`, `CLASES` | `fuente`, `tam_grupo`, `clase` |
| Nº de grafos del grupo | todo el grupo | `numero_grafos` |
| Tamaño de población | `max_individuos` | `max_individuos` |
| Operador de cruce | `op_cruce` | `op_cruce` |
| Iteraciones | `num_iteraciones` | `num_iteraciones` |
| Semilla | `SEMILLA` | `random.seed(...)` |

- Fuentes: `"cercanos"`, `"lejanos"`, `"aleatorios"` (grupos precomputados) o `"aleatorio"`
  (muestreo al vuelo, puede repetir grafos). Tamaños de grupo: 2, 5, 8 y 11.
- Cruces disponibles en `FuncionesAlgoritmo`: `cruce_un_punto`, `cruce_dos_puntos`,
  `cruce_uniforme`.
- Las listas de parámetros se combinan entre sí: se prueban todas las combinaciones.
- La población inicial no se configura: son los contrafactuales de cada grafo original
  calculados con OFS2 + OBS (`MAX_INTENTOS_CONTRAFACTUAL` limita los reintentos de OFS2).
- `experimentacion_cruces.py` se configura en sus constantes de cabecera: `FUENTES`,
  `TAM_GRUPO`, `CLASE`, `POBLACION`, `ITERACIONES`, `CRUCES`, `SEMILLA`.
- El dataset se lee de `data/ADHD/` (`Importargrafos.importgrafos()`).
