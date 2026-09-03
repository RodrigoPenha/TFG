# -*- coding: utf-8 -*-
"""
Calcula la cota inferior del fitness de cada grupo de grafos de entrada.

Se obtiene por voto mayoritario arista a arista: si k de los m grafos de entrada
tienen una arista, el coste inevitable de esa posición es min(k, m-k), y lo mejor
posible es poner la arista si la tiene la mayoría. Por tanto

    cota = (1/m) * suma_k min(c_k, m - c_k)

Se trabaja sobre el triángulo superior de la matriz de adyacencia para contar cada
arista una sola vez, ya que los grafos son no dirigidos.

Es una cota INFERIOR: el grafo que la alcanza puede ser inconexo, y en ese caso
ningún individuo válido llega a ese valor.

Resultado por pantalla y en cota_inferior.txt.
"""

import glob
import pickle

import numpy as np


def cota_inferior(grafos):
    A = np.array([np.asarray(g) for g in grafos])
    iu = np.triu_indices(A.shape[1], k=1)   # posiciones i<j: cada arista una vez
    X = A[:, iu[0], iu[1]].astype(int)      # m x L
    m = len(grafos)
    c = X.sum(axis=0)                        # grafos que contienen cada arista
    return float(np.minimum(c, m - c).sum()) / m


lineas = [f"{'grupo':32s} {'m':>3s} {'cota inferior':>14s}", "-" * 51]

for ruta in sorted(glob.glob("grafos_*/N*/clase*.pkl")):
    with open(ruta, "rb") as f:
        grafos = pickle.load(f)
    grupo = ruta.replace("\\", "/").replace(".pkl", "")
    lineas.append(f"{grupo:32s} {len(grafos):>3d} {cota_inferior(grafos):>14.1f}")

texto = "\n".join(lineas)
print(texto)
with open("cota_inferior.txt", "w", encoding="utf-8") as f:
    f.write(texto + "\n")