"""
Selecciona, para cada clasificación del oráculo (0 y 1), un grupo de N grafos NO
contrafactuales (grafos originales del dataset) elegidos COMPLETAMENTE AL AZAR y
sin repetición.

Es el grupo de control de la experimentación: comparte población y filtro por
clase con `buscar_grafos_cercanos.py` y `buscar_grafos_lejanos.py`, de modo que
la única variable que cambia entre las tres condiciones es la dispersión del
grupo (mínima / aleatoria / máxima).

Se generan grupos de varios tamaños (2, 5, 8 y 11) y se guardan aislados en
carpetas para poder consumirlos fácilmente en el algoritmo:

    grafos_aleatorios/
        N2/  clase0.pkl  clase1.pkl
        N5/  clase0.pkl  clase1.pkl
        N8/  clase0.pkl  clase1.pkl
        N11/ clase0.pkl  clase1.pkl

Cada grupo se guarda como una lista de matrices de adyacencia (numpy), el mismo
formato que `grafos_originales` en Algoritmo.py, de modo que puede cargarse con
la rama `aleatorio = False`.
"""

import itertools
import os
import pickle
import random

import networkx as nx
import numpy as np

import FuncionesAlgoritmo
import Importargrafos

TAMANOS = [2, 5, 8, 11]  # tamaños de grupo a generar
DIR_SALIDA = "grafos_aleatorios"  # carpeta raíz donde se aíslan los grupos
SEMILLA = 2024  # fija el muestreo para que los experimentos sean reproducibles

graphs, clf = Importargrafos.importgrafos()


def candidatos_por_clase(clase):
    """[(nombre, matriz, conjunto_de_aristas)] de los grafos cuya clasificación
    del oráculo es `clase`."""
    candidatos = []
    for nombre, (_, matriz) in graphs.items():
        G = nx.from_numpy_array(matriz)
        if FuncionesAlgoritmo.clasificar(G, clf) == clase:
            candidatos.append((nombre, matriz, set(G.edges())))
    return candidatos


def matriz_distancias(aristas):
    """Matriz simétrica de distancias de edición a partir de los conjuntos de
    aristas."""
    m = len(aristas)
    D = np.zeros((m, m), dtype=int)
    for i in range(m):
        for j in range(i + 1, m):
            d = len(aristas[i].symmetric_difference(aristas[j]))
            D[i, j] = D[j, i] = d
    return D


def coste_grupo(D, indices):
    """Suma de las distancias de todos los pares dentro del grupo."""
    return sum(D[a, b] for a, b in itertools.combinations(indices, 2))


def grupo_aleatorio(m, n, rng):
    """n índices distintos elegidos al azar de entre los m candidatos.

    `rng.sample` muestrea sin reemplazo, así que ningún grafo se repite dentro
    del grupo.
    """
    if n >= m:
        return list(range(m))
    return sorted(rng.sample(range(m), n))


# Precalculamos los candidatos y su matriz de distancias una sola vez por clase.
# La matriz no se usa para elegir el grupo (la selección es aleatoria), solo para
# poder informar de su coste y compararlo con el de los grupos cercanos/lejanos.
datos_por_clase = {}
for clase in (0, 1):
    candidatos = candidatos_por_clase(clase)
    aristas = [c[2] for c in candidatos]
    datos_por_clase[clase] = {
        "nombres": [c[0] for c in candidatos],
        "matrices": [c[1] for c in candidatos],
        "D": matriz_distancias(aristas),
    }

rng = random.Random(SEMILLA)

for n in TAMANOS:
    carpeta = os.path.join(DIR_SALIDA, f"N{n}")
    os.makedirs(carpeta, exist_ok=True)

    for clase in (0, 1):
        datos = datos_por_clase[clase]
        nombres, matrices, D = datos["nombres"], datos["matrices"], datos["D"]

        if len(matrices) < n:
            print(f"[aleatorios N{n} clase {clase}] solo hay {len(matrices)} grafos; se omite.")
            continue

        indices = grupo_aleatorio(len(matrices), n, rng)
        coste = coste_grupo(D, indices)
        pares = n * (n - 1) / 2
        print(f"\n[aleatorios N{n} clase {clase}] coste={coste} media_por_par={coste / pares:.2f}")
        print("  grafos:", [nombres[i] for i in indices])

        grupo_matrices = [matrices[i] for i in indices]
        archivo = os.path.join(carpeta, f"clase{clase}.pkl")
        with open(archivo, "wb") as f:
            pickle.dump(grupo_matrices, f)
        print(f"  guardado en {archivo}")

# Para cargar los grafos en Algoritmo.py (aleatorio = False):
#   with open("grafos_aleatorios/N5/clase0.pkl", "rb") as f:
#       grafos_originales = pickle.load(f)
