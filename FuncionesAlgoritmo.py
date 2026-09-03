# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 12:25:18 2024

@author: rodri
"""

import itertools
import random
import networkx as nx
# import matplotlib.pyplot as plt
import numpy as np
# import random
import math
import Importargrafos
import ofs #Algortimo de busqueda heuristica de un grafo contrafactual implementado por Mónica

def graphToRepr (G):
    A = nx.adjacency_matrix(G).toarray()
    x = 1
    y = 0
    n = len(A)
    representacion = []
    for i in range(int(n*(n-1)/2)):
        representacion.append(A[y][x])
        x+=1
        if x % n == 0:
            y+=1
            x = y + 1
    return representacion

def reprToGraph (R):
    n = len(R)
    
    dim = int((1+math.sqrt(1 + 8*n))/2)
    
    matriz = np.zeros((dim,dim))
    x = 1
    y = 0
    
    for i in range(n):
        matriz[y][x]= R[i]
        matriz[x][y]= R[i]
        x+=1
        if x % dim == 0:
            y+=1
            x = y + 1
    G = nx.from_numpy_array(matriz)
    
    return G

def clasificar (G, clf):
    return Importargrafos.oracle(nx.adjacency_matrix(G).toarray(), clf)


def clave_grafo(G):
    """
    Devuelve una clave hashable que identifica al grafo por su matriz de adyacencia.

    Reutiliza graphToRepr (triángulo superior de la matriz, suficiente por ser el
    grafo no dirigido) y lo empaqueta en un objeto bytes: dos grafos con la misma
    matriz de adyacencia producen la misma clave.
    """
    return bytes(int(v) for v in graphToRepr(G))


def mutar(G, permutaciones_aristas_grafos_original):
    """
    Muta un grafo AÑADIENDO una arista presente en al menos dos de los grafos
    originales. Las candidatas salen de permutaciones_aristas_grafos_original,
    que solo contiene intersecciones de subconjuntos de tamaño 2 o mayor, por lo
    que una arista presente en un único original nunca puede añadirse. La
    probabilidad de cada arista crece con el número de originales que la
    contienen (reutilizando elegir_arista_ponderada).

    Como solo añade aristas, la conexidad del grafo se preserva siempre. Se
    excluyen las aristas que el grafo ya tiene para garantizar que el resultado
    sea realmente distinto.
    """
    G_mutado = G.copy()
    aristas_actuales = set(G_mutado.edges())

    # Aristas candidatas por grupo, excluyendo las que G ya tiene. Una arista
    # compartida por más originales aparece en más grupos/combinaciones, por lo
    # que acumula más peso de forma natural.
    grupos = [
        [a for interseccion in grupo for a in interseccion
         if a not in aristas_actuales and (a[1], a[0]) not in aristas_actuales]
        for grupo in permutaciones_aristas_grafos_original
    ]
    if not any(grupos):          # no queda ninguna arista nueva que añadir
        return G_mutado

    # Score decreciente: los grupos con más originales (índices bajos) pesan más.
    n = len(grupos)
    scores = [n - i for i in range(n)]

    arista = elegir_arista_ponderada(grupos, scores)
    G_mutado.add_edge(*arista)
    return G_mutado



def cruce_un_punto(padre1, padre2):
    if len(padre1) != len(padre2):
        raise ValueError('Los padres tiene que tener el mismo tamaño')
        
    punto_cruce = np.random.randint(1, len(padre1))
    
    # Creamos los hijos combinando las partes de los padres
    hijo1 = np.concatenate((padre1[:punto_cruce], padre2[punto_cruce:]))
    hijo2 = np.concatenate((padre2[:punto_cruce], padre1[punto_cruce:]))
    
    return hijo1, hijo2

def cruce_dos_puntos(padre1, padre2):
    # Comprobamos que los padres tengan el mismo tamaño
    if len(padre1) != len(padre2):
        raise ValueError("Los padres deben tener el mismo tamaño.")
    
    # Obtenemos dos puntos de cruce aleatorios diferentes
    punto1, punto2 = sorted(np.random.choice(range(1, len(padre1)), size=2, replace=False))
    
    # Creamos los hijos combinando los segmentos de los padres
    hijo1 = np.concatenate((padre1[:punto1], padre2[punto1:punto2], padre1[punto2:]))
    hijo2 = np.concatenate((padre2[:punto1], padre1[punto1:punto2], padre2[punto2:]))
    
    return hijo1, hijo2

def cruce_uniforme(padre1, padre2):
    if len(padre1) != len(padre2):
        raise ValueError('Los padres tienen que tener el mismo tamaño')
        
    # Creamos una mascara aleatoria para el cruce
    mascara = np.random.randint(0, 2, size=len(padre1)).astype(bool)
    
    # Creamos los hijos
    hijo1 = np.where(mascara, padre1, padre2)
    hijo2 = np.where(mascara, padre2, padre1)

    return hijo1, hijo2

def cruce(padre1, padre2, opcion):
    if opcion not in [cruce_dos_puntos, cruce_un_punto, cruce_uniforme]:
        raise ValueError(" La funcion de cruce no esta implementada")    
    return opcion(padre1,padre2)

def elegir_arista_ponderada(listas_aristas, scores):
    # Construir aristas y pesos en una sola pasada
    aristas, pesos = zip(*(
        (arista, score)
        for lista, score in zip(listas_aristas, scores)
        for arista in lista
    ))

    # Elegir una arista al azar según la distribución de pesos
    return random.choices(aristas, weights=pesos, k=1)[0]

# funcion que combierte un grafo desconexo en conexo de
def conexo(G, permutaciones_aristas_grafos_original,clf, objetivo, max_iter=500, max_aristas=10):
    if not nx.is_connected(G):
        #print("El grafo no es conexo")
        # Encuentra las componentes conexas
        componentes = list(nx.connected_components(G))
        
        # Conectar cada componente con la siguiente
        scores = [i/len(permutaciones_aristas_grafos_original)+1 for i in range(len(permutaciones_aristas_grafos_original)+1, 0, -1)]
        # Solo conectamos cuando hay 2 componentes
        if len(componentes) == 2:
            componente_actual = list(componentes[0])
            siguiente_componente = list(componentes[1])
            posibles_aristas = set([x for x in itertools.product(componente_actual, siguiente_componente)])
            posibles_aristas_en_permutaciones = []
            for permutaciones in permutaciones_aristas_grafos_original:
                aristas_mismo_score = []
                for intersecion in permutaciones:
                    aristas_mismo_score.extend(list(posibles_aristas.intersection(intersecion)))
                posibles_aristas_en_permutaciones.append(aristas_mismo_score)
            # añadir las aristas que no estan en la interseccion
            posibles_aristas_en_permutaciones.append(list(posibles_aristas))
            for i in range(max_aristas):
                for _ in range(max_iter):
                    aristas = [elegir_arista_ponderada(posibles_aristas_en_permutaciones, scores) for _ in range(i+1)]
                    g_aux = G.copy()
                    for arista in aristas:
                        g_aux.add_edge(*arista)
                    if clasificar(g_aux, clf) == objetivo:
                        for arista in aristas:
                            G.add_edge(*arista)
                        if nx.is_connected(G):
                            return True
                        else:
                            print("Error conectando los componentes")
        #retorno False si no se pudo conectar las componentes
        return False
    return True


def fitness(G, originales: list):
    """
    Calcula la distancia de edición promedio entre el grafo G y una lista de grafos originales.

    Parámetros:
    - G: Grafo de NetworkX.
    - originales: Lista de grafos de NetworkX.

    Retorna:
    - Distancia de edición promedio entre G y los grafos originales.
    """
    if not originales:
        raise ValueError("La lista de grafos originales no puede estar vacía.")

    # Calcular la distancia de edición promedio
    total_distance = sum(
        len(set(grafo.edges).symmetric_difference(set(G.edges))) for grafo in originales
    )
    return total_distance / len(originales)



# G = nx.Graph()

# G.add_nodes_from(['v1','v2','v3','v4'])

# G1 = G.copy()

# G.add_edges_from([('v1','v2'),('v2','v3'),('v2','v4'),('v3','v4')])

# G1.add_edges_from([('v1','v2'),('v2','v3'),('v2','v4'),('v3','v4'), ('v1', 'v4')])

# pos = nx.spring_layout(G)  # Posiciona los nodos
# nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# nx.draw_networkx_labels(G, pos)

# # Mostrar el grafo
# plt.title("G Representado")
# plt.show()

# pos = nx.spring_layout(G1)  # Posiciona los nodos
# nx.draw(G1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# nx.draw_networkx_labels(G1, pos)

# # Mostrar el grafo
# plt.title("G1 Representado")
# plt.show()

# adj_matrix_G = nx.adjacency_matrix(G).toarray()
# adj_matrix_G1 = nx.adjacency_matrix(G1).toarray()

# reprG = adjMatrixToRepr(adj_matrix_G)

# reprG1 = adjMatrixToRepr(adj_matrix_G1)



        
    
    
        
        