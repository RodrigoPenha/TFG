"""
Busca, para cada clasificación del oráculo (0 y 1), el grupo de N grafos NO
contrafactuales (grafos originales del dataset) mutuamente MÁS LEJANOS posibles
(máxima diversidad).

La distancia entre grafos es la distancia de edición usada en el resto del
proyecto: número de aristas en la diferencia simétrica de ambos grafos.

Se generan grupos de varios tamaños (2, 5, 8 y 11) y se guardan aislados en
carpetas para poder consumirlos fácilmente en el algoritmo:

    grafos_lejanos/
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

import networkx as nx
import numpy as np

import FuncionesAlgoritmo
import Importargrafos

TAMANOS = [2, 5, 8, 11]  # tamaños de grupo a generar
DIR_SALIDA = "grafos_lejanos"  # carpeta raíz donde se aíslan los grupos

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


def grupo_mas_lejano(D, n):
    """Heurística greedy para el grupo de n grafos mutuamente más lejanos.

    Arranca con el par de grafos más alejado y, en cada paso, añade el grafo que
    maximiza la suma de distancias a los ya seleccionados (max-sum diversity).
    """
    m = D.shape[0]
    if n >= m:
        return list(range(m))

    # Par inicial más lejano.
    i, j = np.unravel_index(np.argmax(D), D.shape)
    seleccion = [int(i), int(j)]

    while len(seleccion) < n:
        mejor_k, mejor_suma = None, -1
        for k in range(m):
            if k in seleccion:
                continue
            suma = sum(D[k, s] for s in seleccion)
            if suma > mejor_suma:
                mejor_suma, mejor_k = suma, k
        seleccion.append(mejor_k)

    return sorted(seleccion)


# Precalculamos los candidatos y su matriz de distancias una sola vez por clase
# (la matriz no depende del tamaño del grupo pedido).
datos_por_clase = {}
for clase in (0, 1):
    candidatos = candidatos_por_clase(clase)
    aristas = [c[2] for c in candidatos]
    datos_por_clase[clase] = {
        "nombres": [c[0] for c in candidatos],
        "matrices": [c[1] for c in candidatos],
        "D": matriz_distancias(aristas),
    }

for n in TAMANOS:
    carpeta = os.path.join(DIR_SALIDA, f"N{n}")
    os.makedirs(carpeta, exist_ok=True)

    for clase in (0, 1):
        datos = datos_por_clase[clase]
        nombres, matrices, D = datos["nombres"], datos["matrices"], datos["D"]

        if len(matrices) < n:
            print(f"[lejanos N{n} clase {clase}] solo hay {len(matrices)} grafos; se omite.")
            continue

        indices = grupo_mas_lejano(D, n)
        coste = coste_grupo(D, indices)
        pares = n * (n - 1) / 2
        print(f"\n[lejanos N{n} clase {clase}] coste={coste} media_por_par={coste / pares:.2f}")
        print("  grafos:", [nombres[i] for i in indices])

        grupo_matrices = [matrices[i] for i in indices]
        archivo = os.path.join(carpeta, f"clase{clase}.pkl")
        with open(archivo, "wb") as f:
            pickle.dump(grupo_matrices, f)
        print(f"  guardado en {archivo}")

# Para cargar los grafos en Algoritmo.py (aleatorio = False):
#   with open("grafos_lejanos/N5/clase0.pkl", "rb") as f:
#       grafos_originales = pickle.load(f)
