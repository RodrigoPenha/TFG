# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 12:25:18 2024

@author: rodri
"""

import itertools
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

def cruce(padre1, padre2, opcion):
    if opcion not in [cruce_dos_puntos, cruce_un_punto]:
        raise ValueError(" La funcion de cruce no esta implementada")    
    return opcion(padre1,padre2)

# funcion que combierte un grafo desconexo en conexo de
def conexo(G, permutaciones_aristas_grafos_original,clf, objetivo):
    if not nx.is_connected(G):
        print("El grafo no es conexo")
        # Encuentra las componentes conexas
        componentes = list(nx.connected_components(G))
        
        # Conectar cada componente con la siguiente
        for i in range(len(componentes) - 1):
            componente_actual = list(componentes[i])
            siguiente_componente = list(componentes[i + 1])
            posibles_aristas = [x for x in itertools.product(componente_actual, siguiente_componente)]
            for lista_permutaciones in permutaciones_aristas_grafos_original:
                for permu in lista_permutaciones: # Interseccion de las aristas de las permutaciones de grafos originales de un mismo tamaño sin importar el orden
                        for arista in permu: # Selecciona una arista de la interseccion y comprueba si coincide con alguna de las posibles aristas
                            if arista in posibles_aristas:
                                g_aux = G.copy()
                                g_aux.add_edge(*arista)
                                if clasificar(g_aux, clf) == objetivo:
                                    G.add_edge(*arista)
                                    break
                        else:
                            break
                else:
                    break
                # Selecciona un nodo aleatorio de cada componente y conecta ambos
            else:
                continue # Se ha podido conectar las componentes con aristas de los grafos originales y se pasa a la siguiente iteracion
            print("No se ha podido conectar las componentes con aristas de los grafos originales")
            return False
        
    return True


def fitness (G, Originales: list):
    '''
    Distancia de edicion entre el grafo G y los grafos originales
    '''
    #print("Calculando fitness")
    mean_distance = 0
    for grafo in Originales:
        mean_distance += len(set(grafo.edges).difference(set(G.edges)))
    result = mean_distance/len(Originales)
    #print(f"Fitness: {result}")
    return result



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



        
    
    
        
        