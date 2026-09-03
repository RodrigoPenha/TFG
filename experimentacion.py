# -*- coding: utf-8 -*-
"""
Script de experimentación del algoritmo genético.

Ejecuta automáticamente el algoritmo sobre todos los grupos indicados
(combinaciones de fuente x tamaño de grupo x clase), barriendo para cada uno
todas las combinaciones de parámetros del genético. Los resultados de CADA
grupo se guardan en un archivo NUEVO con marca de tiempo, de modo que ninguna
ejecución sobreescribe a las anteriores.

Para cada grupo se guarda:
  - la matriz de distancias de edición de la población inicial,
  - el score del mejor individuo de cada combinación de parámetros,
  - las distancias de ese mejor individuo a cada grafo original (la fila de la
    matriz que le corresponde) y su dispersión, para poder ver si la solución
    es un grafo de consenso o se ha quedado pegada a uno de los originales,
  - los mismos datos que ya se almacenaban en resultados.csv
    (nº de grafos, población máxima, cruce, nº de iteraciones, score y tiempo).

El driver de Algoritmo.py está protegido con `if __name__ == "__main__":`, así
que aquí se reutiliza `algoritmo_genetico` sin relanzar aquel script.
"""

import itertools
import json
import os
import pickle
import random
import sys
import time
from datetime import datetime

import networkx as nx

import FuncionesAlgoritmo
import Importargrafos
import Visualizacion
from Algoritmo import algoritmo_genetico
from obs import obs
from ofs import ofs2

# =========================== CONFIGURACIÓN ===========================
# Se ejecutan automáticamente TODOS los grupos: para cada combinación
# (fuente, tam_grupo, clase) se corre el barrido de parámetros y se guarda un
# JSON independiente con marca de tiempo.
FUENTES = ["cercanos", "lejanos", "aleatorios"]   # también vale "aleatorio"
TAMANOS_GRUPO = [2, 5, 8, 11]   # tamaños de grupo a ejecutar
CLASES = [0, 1]                 # clasificaciones del oráculo a ejecutar

# Parámetros del genético: listas -> se prueban TODAS las combinaciones.
max_individuos = [25, 50, 100]                     # población máxima
num_iteraciones = [5000]                           # iteraciones de cruce
op_cruce = [FuncionesAlgoritmo.cruce_uniforme,     # operador(es) de cruce
            FuncionesAlgoritmo.cruce_un_punto]

# Número máximo de llamadas a ofs2 por grafo antes de darse por vencido. ofs2 es
# heurístico y puede devolver None indefinidamente para un grafo concreto, así
# que sin este tope el bucle de la población inicial no termina nunca.
MAX_INTENTOS_CONTRAFACTUAL = 50

# Raiz de los resultados. Dentro se reparten en <fuente>/N<tam_grupo>/: ahi
# quedan el JSON y la poblacion inicial del grupo, y los ficheros de cada
# combinacion del barrido van en una subcarpeta por operador de cruce.
DIR_EXPERIMENTOS = "experimentos"
SEMILLA = 12345
# =====================================================================


def cargar_grafos_originales(graphs, clf, fuente, tam_grupo, clase):
    """Devuelve la lista de matrices de adyacencia del grupo indicado."""
    if fuente == "aleatorio":
        # Muestreo al vuelo (puede repetir grafos). Se mantiene por compatibilidad;
        # para la experimentación usa la fuente "aleatorios" (grupo precomputado
        # sin repeticiones por buscar_grafos_aleatorios.py).
        seleccion = []
        while len(seleccion) < tam_grupo:
            g = graphs[random.choice(list(graphs.keys()))][1]  # (etiqueta, grafo) -> grafo
            if Importargrafos.oracle(g, clf) == clase:
                seleccion.append(g)
        return seleccion
    if fuente in ("cercanos", "lejanos", "aleatorios"):
        archivo = os.path.join(f"grafos_{fuente}", f"N{tam_grupo}", f"clase{clase}.pkl")
        with open(archivo, "rb") as f:
            return pickle.load(f)
    raise ValueError(
        f"fuente desconocida: {fuente!r} "
        "(usa 'cercanos', 'lejanos', 'aleatorios' o 'aleatorio')"
    )


def calcular_contrafactual(grafo, clf, max_intentos=MAX_INTENTOS_CONTRAFACTUAL):
    """Contrafactual inicial de `grafo`, o None si ofs2 falla `max_intentos` veces.

    ofs2 es heurístico y devuelve None cuando agota las aristas sin cambiar la
    clasificación; para algunos grafos puede fallar siempre. El tope evita el
    bucle infinito del `while contrafactual is None`.
    """
    for intento in range(1, max_intentos + 1):
        contrafactual = ofs2(grafo, clf)
        if contrafactual is not None:
            print(f"Contrafactual encontrado en el intento {intento}")
            return obs(grafo, contrafactual, clf, 5, 4000)
        print(f"Intento {intento}/{max_intentos} sin contrafactual")
    return None


def distancia_edicion(g1, g2):
    """Distancia de edición (nº de aristas en la diferencia simétrica)."""
    e1, e2 = set(nx.from_numpy_array(g1).edges), set(nx.from_numpy_array(g2).edges)
    return len(e1.symmetric_difference(e2))


def matriz_distancias_poblacion(poblacion, grafos_originales):
    """Matriz de distancias de edición de cada individuo de la población inicial
    (contrafactual) respecto a CADA grafo original.

    Fila i = contrafactual i; columna j = grafo original j;
    D[i][j] = distancia de edición(contrafactual_i, original_j).
    La distancia se mide siempre contra los originales (igual que el fitness),
    por eso la diagonal NO es cero: es la distancia de cada contrafactual a su
    propio original."""
    D = [[0] * len(grafos_originales) for _ in range(len(poblacion))]
    for i, g_pob in enumerate(poblacion):
        for j, g_orig in enumerate(grafos_originales):
            D[i][j] = distancia_edicion(g_pob, g_orig)
    return D


def distancias_solucion(grafo, grafos_originales):
    """Fila de la matriz de distancias que le corresponde a la solución final.

    `grafo` es el nx.Graph que devuelve el genético. Se mide contra los mismos
    originales que la matriz de la población inicial, así que su media es
    exactamente el Score: guardando el vector entero se puede ver, además del
    score, CÓMO se reparte. Dos soluciones con el mismo score pueden ser una
    pegada a uno de los originales y otra equidistante de todos (un grafo de
    consenso, que es lo que se busca).
    """
    aristas = set(grafo.edges)
    return [len(aristas.symmetric_difference(set(nx.from_numpy_array(g).edges)))
            for g in grafos_originales]


def dispersion(distancias):
    """Desviación típica / media del vector de distancias a los originales.

    Cerca de 0 la solución es equidistante de todos los originales; cuanto más
    alto, más se parece a unos que a otros.
    """
    n = len(distancias)
    media = sum(distancias) / n
    if not media:
        return 0.0
    varianza = sum((d - media) ** 2 for d in distancias) / n
    return varianza ** 0.5 / media


def nombre_combinacion(base, cruce, poblacion):
    """Nombre base de los ficheros de UNA combinación del barrido.

    Incluye el operador de cruce además de la población: el barrido puede
    probar varios operadores, y sin el nombre del cruce dos combinaciones con
    la misma población escribirían sobre los mismos ficheros.
    """
    return f"{base}_{cruce}_pob{poblacion}"


def ejecutar_grupo(graphs, clf, fuente, tam_grupo, clase):
    """Ejecuta el barrido de parámetros sobre un grupo y guarda su JSON.

    El grupo escribe en experimentos/<fuente>/N<tam_grupo>/: ahí van el JSON y
    los grafos de la población inicial, que son comunes a todo el barrido. Las
    imágenes de comparación inicial-vs-final y de los mejores grafos de cada
    combinación van en una subcarpeta por operador de cruce, con el nombre base
    del JSON más el cruce y la población, de modo que no se sobreescriban entre
    combinaciones."""
    print(f"\n===== Grupo {fuente} N{tam_grupo} clase{clase} =====")

    # Marca de tiempo e identificador base compartidos por el JSON y las imágenes.
    # Cada grupo escribe en la subcarpeta de su fuente y su tamaño de grupo.
    dir_salida = os.path.join(DIR_EXPERIMENTOS, fuente, f"N{tam_grupo}")
    os.makedirs(dir_salida, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{fuente}_N{tam_grupo}_clase{clase}_{marca}"

    # 1) Cargar el grupo de grafos originales
    grafos_originales = cargar_grafos_originales(graphs, clf, fuente, tam_grupo, clase)
    print(f"Cargados {len(grafos_originales)} grafos originales")

    # 2) Calcular los contrafactuales iniciales (población inicial del genético).
    #    Si algún grafo agota los intentos, se aborta el grupo y se sigue con el
    #    siguiente en lugar de quedarse en un bucle infinito.
    poblacionInicial = []
    for i, grafo in enumerate(grafos_originales):
        print(f"Calculando contrafactual del grafo {i}")
        contrafactual = calcular_contrafactual(grafo, clf)
        if contrafactual is None:
            print(f"[AVISO] Sin contrafactual para el grafo {i} tras "
                  f"{MAX_INTENTOS_CONTRAFACTUAL} intentos; se omite el grupo "
                  f"{fuente} N{tam_grupo} clase{clase}.")
            return
        poblacionInicial.append(contrafactual)

    # 3) Matriz de distancias de la población inicial (contrafactuales) respecto
    #    a los grafos originales
    matriz_poblacion = matriz_distancias_poblacion(poblacionInicial, grafos_originales)
    print("Matriz de distancias de la población inicial (respecto a los originales):")
    for fila in matriz_poblacion:
        media = sum(fila) / len(fila) if fila else 0
        print(f"{fila} media:{media:.2f}")

    # 3b) Línea base con la que comparar la solución del genético. La media de
    #     cada fila de la matriz anterior es el fitness de ese individuo (el
    #     genético usa la misma distancia media a los originales), así que el
    #     mejor individuo inicial es el de media mínima. Se guardan las medias,
    #     cuál es el mejor y los propios grafos de la población inicial, con la
    #     diferencia respecto a su original en node-link y en matriz de
    #     adyacencia, para poder verla luego sin repetir la ejecución.
    medias_inicial = [sum(fila) / len(fila) for fila in matriz_poblacion]
    idx_mejor = min(range(len(medias_inicial)), key=lambda i: medias_inicial[i])

    prefijo_inicial = os.path.join(dir_salida, f"{base}_inicial")
    Visualizacion.guardar_contrafactuales(
        poblacionInicial, grafos_originales, prefijo=prefijo_inicial)
    # El mejor individuo inicial, además, en un archivo propio.
    ruta_mejor = os.path.join(dir_salida, f"{base}_mejor_inicial.graphml")
    nx.write_graphml(nx.from_numpy_array(poblacionInicial[idx_mejor]), ruta_mejor)

    print(f"Mejor individuo de la población inicial: índice {idx_mejor}, "
          f"distancia media {medias_inicial[idx_mejor]:.2f}, en {ruta_mejor}")

    # 4) Barrido de parámetros: una fila de resultados por combinación
    numero_grafos = [tam_grupo]  # nº de grafos originales a usar (todo el grupo)
    resultados = []
    for n_grafos, poblacion, cruce, iteraciones in itertools.product(
        numero_grafos, max_individuos, op_cruce, num_iteraciones
    ):
        print(f"Probando con {n_grafos} grafos, {poblacion} individuos, "
              f"{cruce.__name__} y {iteraciones} iteraciones")
        # Prefijo de los ficheros de esta combinación, en la subcarpeta de su
        # operador de cruce dentro del directorio del grupo.
        nombre = nombre_combinacion(base, cruce.__name__, poblacion)
        dir_cruce = os.path.join(dir_salida, cruce.__name__)
        os.makedirs(dir_cruce, exist_ok=True)
        prefijo_img = os.path.join(dir_cruce, nombre)
        inicio = time.time()
        grafo_final, score = algoritmo_genetico(
            poblacion, cruce, iteraciones,
            grafos_originales[:n_grafos], poblacionInicial[:n_grafos], clf,
            prefijo_salida=prefijo_img,
        )
        tiempo_ejecucion = time.time() - inicio

        # Fila de la matriz de distancias correspondiente a la mejor solución.
        # Su media es el Score; el vector dice si la solución se ha quedado
        # pegada a uno de los originales o si es equidistante de todos.
        d_final = distancias_solucion(grafo_final, grafos_originales[:n_grafos])
        print(f"Distancias de la mejor solución a los originales: {d_final} "
              f"media:{sum(d_final) / len(d_final):.2f} cv:{dispersion(d_final):.3f}")

        resultados.append({
            "Numero_grafos": n_grafos,
            "Poblacion_maxima": poblacion,
            "Cruce": cruce.__name__,
            "Numero_iteraciones": iteraciones,
            "Score": score,
            "Tiempo_de_ejecucion": tiempo_ejecucion,
            "Distancias_solucion_final": d_final,
            "Dispersion_solucion_final": dispersion(d_final),
            # Nombre base de los ficheros de esta combinación, para que los
            # scripts de análisis los localicen sin reconstruir el patrón. Están
            # en la subcarpeta que da "Cruce", dentro del directorio del JSON.
            "Prefijo": nombre,
        })

    # 5) Guardar el JSON con el mismo nombre base que las imágenes (no sobreescribe)
    ruta = os.path.join(dir_salida, f"{base}.json")

    salida = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "fuente": fuente,
        "tam_grupo": tam_grupo,
        "clase": clase,
        "matriz_distancias_poblacion_inicial": matriz_poblacion,
        "distancia_media_poblacion_inicial": medias_inicial,
        "mejor_inicial": {
            "indice": idx_mejor,
            "distancia_media": medias_inicial[idx_mejor],
            "distancias": matriz_poblacion[idx_mejor],
        },
        "resultados": resultados,
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Resultados del grupo guardados en {ruta}")


def main():
    """Campaña completa: todas las fuentes x tamaños de grupo x clases.

    Se pueden pasar fuentes concretas por línea de órdenes para relanzar solo
    una parte:  python experimentacion.py cercanos lejanos
    """
    fuentes = sys.argv[1:] or FUENTES
    random.seed(SEMILLA)
    graphs, clf = Importargrafos.importgrafos()

    arranque = time.time()
    for fuente in fuentes:
        inicio = time.time()
        print(f"\n########## FUENTE {fuente} ##########", flush=True)
        for tam_grupo in TAMANOS_GRUPO:
            for clase in CLASES:
                ejecutar_grupo(graphs, clf, fuente, tam_grupo, clase)
        print(f"########## fin {fuente} ({(time.time() - inicio) / 60:.0f} min) "
              f"##########", flush=True)

    print(f"\nCampaña completa en {(time.time() - arranque) / 60:.0f} min")


if __name__ == "__main__":
    main()
