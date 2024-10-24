# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 12:25:18 2024

@author: rodri
"""

import networkx as nx
# import matplotlib.pyplot as plt
import numpy as np
# import random
import math

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
    
    if not nx.is_connected(G):
        raise Warning('El grafo resultante no es conexo')
    
    return G




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



        
    
    
        
        