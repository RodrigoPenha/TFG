import pickle
import random
import networkx as nx
import numpy as np
import FuncionesAlgoritmo
import Importargrafos

random.seed(12345)
graphs,clf = Importargrafos.importgrafos()

# Buscar un grafo aleatorio y el más cercano a él que evalúen igual
distancia_minima = float('inf')
grafo_global_mas_cercano = None
grafo_global = None
for grafo in graphs.values():
    # Convertir a NetworkX graph si es necesario
    G1 = nx.from_numpy_array(grafo[1]) if isinstance(grafo[1], (list, tuple, np.ndarray)) else grafo[1]
    if FuncionesAlgoritmo.clasificar(G1, clf) == 1:
        for grafo2 in graphs.values():
            G2 = nx.from_numpy_array(grafo2[1]) if isinstance(grafo2[1], (list, tuple, np.ndarray)) else grafo2[1]
            if not np.array_equal(grafo[1], grafo2[1]) and FuncionesAlgoritmo.clasificar(G1, clf) == 0:
                distancia = len(
                    set(G1.edges())
                    .symmetric_difference(
                        set(G2.edges())
                    )
                )
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    grafo_global = grafo
                    grafo_global_mas_cercano = grafo2
        print(f"Distancia minima: {distancia_minima} entre {grafo} y {grafo_global_mas_cercano} ")


print("Grafo más cercano que evalúa igual:")
print(grafo_global_mas_cercano)
print("distancia minima:")
print(distancia_minima)

# Guardar los 2 grafos cercanos en un fichero para su posterior uso
grafos_cercanos = [grafo, grafo_global_mas_cercano]

archivo_grafos_cercanos = "grafos_cercanos.pkl"

with open(archivo_grafos_cercanos, "wb") as f:
    pickle.dump(grafos_cercanos, f)

print(f"Los 2 grafos cercanos guardados en {archivo_grafos_cercanos}")



# Para cargar los grafos en otro momento:
# with open(archivo_grafos, "rb") as f:
#     grafos_originales = pickle.load(f)
