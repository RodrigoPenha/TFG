# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:17:50 2024

@author: rodri
"""

import FuncionesAlgoritmo
import Importargrafos
import networkx as nx
import random
import matplotlib.pyplot as plt
import itertools

import os
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

# repr_G = FuncionesAlgoritmo.graphToRepr(G)
# repr_G1 = FuncionesAlgoritmo.graphToRepr(G1)


# hijo1, hijo2 = FuncionesAlgoritmo.cruce(repr_G, repr_G1, FuncionesAlgoritmo.cruce_dos_puntos)

# G_hijo1 = FuncionesAlgoritmo.reprToGraph(hijo1)


# pos = nx.spring_layout(G_hijo1)  # Posiciona los nodos
# nx.draw(G_hijo1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# nx.draw_networkx_labels(G_hijo1, pos)

# # Mostrar el grafo
# plt.title("G Hijo1")
# plt.show()

# G_hijo2 = FuncionesAlgoritmo.reprToGraph(hijo2)

# pos = nx.spring_layout(G_hijo2)  # Posiciona los nodos
# nx.draw(G_hijo2, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# nx.draw_networkx_labels(G_hijo2, pos)

# # Mostrar el grafo
# plt.title("G Hijo2")
# plt.show()
# cambiar el path al directorio del archivo

graphs,clf = Importargrafos.importgrafos()

#cantidad de grafos para la poblacion inicial
n = 5 
grafos_originales = list()
poblacionInicial = list()
random.seed(2024)

info = []
results = {'pred':[],'true':[]} 

while n > 0:
    grafo = graphs[random.choice(list(graphs.keys()))][1] # elegimos un grafo aleatorio el diccionario nos devuelve una tupla de etiqueta y grafo
    if Importargrafos.oracle(grafo, clf) == 1:
        grafos_originales.append(grafo)
        n = n-1
'''
for grafo in grafos_originales:
    poblacionInicial.append(FuncionesAlgoritmo.OFS(grafo, clf))
'''
# Provisional hasta tener un algoritmo que encuentre contrafactuales
n = 5 
while n > 0:
    grafo = graphs[random.choice(list(graphs.keys()))][1] # elegimos un grafo aleatorio el diccionario nos devuelve una tupla de etiqueta y grafo
    if Importargrafos.oracle(grafo, clf) == 0:
        poblacionInicial.append(grafo)
        n = n-1

print(f"población inicial {poblacionInicial}")
print(f"grafos originales {grafos_originales}")

# Convertimos las representaciones de los grafos a objetos de la clase nx.Graph

poblacionActual = [nx.from_numpy_array(grafo) for grafo in poblacionInicial]
grafos_originales = [nx.from_numpy_array(grafo) for grafo in grafos_originales]

parejas = list(itertools.combinations(poblacionActual, 2))

# Parámetros del algoritmo genético
max_individuos = 40  # Número máximo de individuos en la población
num_iteraciones = 15  # Número de iteraciones de cruce

# para cada permutacion de los grafos originales calculamos la interseccion de las aristas y las guardamos en la lista 
# Lista para guardar las combinaciones agrupadas por tamaño (excluyendo tamaño 1)
combinaciones_grafos = []

# Generar combinaciones para subconjuntos de diferentes tamaños (sin incluir tamaño 1)
for size in range(len(grafos_originales), 1, -1):  # Desde 5 grafos hasta 2
    combinaciones = list(itertools.combinations(grafos_originales, size))
    combinaciones_grafos.append(combinaciones)

# hacemos la interseccion de las aristas de las combinaciones de los grafos originales
permutaciones_aristas_grafos_original = []  # Lista para guardar las aristas comunes de cada permutación, ordenadas por tamaño
for combinaciones in combinaciones_grafos:
    lista_permutaciones = []
    for combinacion in combinaciones:
        aristas = set(combinacion[0].edges)
        for grafo in combinacion[1:]:
            aristas = aristas.intersection(set(grafo.edges))
        lista_permutaciones.append(aristas)
    permutaciones_aristas_grafos_original.append(lista_permutaciones)

print(f"len permutaciones {len(permutaciones_aristas_grafos_original)}")
print(f"len permutaciones0 {len(permutaciones_aristas_grafos_original[0])}")
print(f"len permutaciones0,0 {len(permutaciones_aristas_grafos_original[0][0])}")
print(f"len permutaciones1 {len(permutaciones_aristas_grafos_original[1])}")
print(f"len permutaciones1,0 {len(permutaciones_aristas_grafos_original[1][0])}")
print(f"len permutaciones2 {len(permutaciones_aristas_grafos_original[2])}")
print(f"len permutaciones2,0 {len(permutaciones_aristas_grafos_original[2][0])}")
print(f"len permutaciones3 {len(permutaciones_aristas_grafos_original[3])}")
print(f"len permutaciones3,0 {len(permutaciones_aristas_grafos_original[3][0])}")


for iteracion in range(num_iteraciones):
    print(f"\nIteración {iteracion + 1}")
    
    # Generamos todas las combinaciones de parejas en la población actual.
    parejas = list(itertools.combinations(poblacionActual, 2))
    
    # Creamos una lista para almacenar la nueva descendencia generada en esta iteración.
    nueva_descendencia = []
    
    # Realizamos el cruce para cada pareja y añadimos los hijos a la lista de descendencia.
    for padre, madre in parejas:
        padre = FuncionesAlgoritmo.graphToRepr(padre)
        madre = FuncionesAlgoritmo.graphToRepr(madre)
        hijo1, hijo2 = FuncionesAlgoritmo.cruce_dos_puntos(padre, madre)
        # Comprobamos que los hijos sean conexos
        hijo1 = FuncionesAlgoritmo.reprToGraph(hijo1)
        hijo2 = FuncionesAlgoritmo.reprToGraph(hijo2)
        if not nx.is_connected(hijo1):
            
            if FuncionesAlgoritmo.conexo(hijo1, permutaciones_aristas_grafos_original, clf):
                #print("Hijo 1 es conexo no se descarta")
                nueva_descendencia.append(hijo1)
        if not nx.is_connected(hijo2):
            
            if FuncionesAlgoritmo.conexo(hijo2, permutaciones_aristas_grafos_original, clf):
                #print("Hijo 2 es conexo y no se descarta")
                nueva_descendencia.append(hijo2)
        
    
    # Añadimos la nueva descendencia a la población actual
    poblacionActual.extend(nueva_descendencia)
    
    # Si la población supera el límite, nos quedamos con los 50 mejores individuos
    if len(poblacionActual) > max_individuos:
        poblacionActual = sorted(poblacionActual, key=lambda x: FuncionesAlgoritmo.fitness(x,grafos_originales))[:max_individuos]

    # Mostrar el estado de la población
    print(f"Población actual ({len(poblacionActual)} individuos): {poblacionActual}")

# Resultado final
print("\nPoblación final:")
print(poblacionActual)
print("Fitness de la población final:")
fitness_poblacion = [FuncionesAlgoritmo.fitness(x, grafos_originales) for x in poblacionActual]
print(fitness_poblacion)
valor_poblacion = [Importargrafos.oracle(nx.adjacency_matrix(x).toarray(), clf) for x in poblacionActual]
print(valor_poblacion)