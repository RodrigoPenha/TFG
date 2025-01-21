# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:17:50 2024

@author: rodri
"""

import csv
import time
import FuncionesAlgoritmo
import Importargrafos
import networkx as nx
import random
import matplotlib.pyplot as plt
import itertools
from ofs import ofs

def algoritmo_genetico(num_individuos, cruce, generaciones, originales, iniciales, clf):

    

    # Convertimos las representaciones de los grafos a objetos de la clase nx.Graph

    poblacionActual = [nx.from_numpy_array(grafo) for grafo in iniciales]
    grafos_originales_nx = [nx.from_numpy_array(grafo) for grafo in originales]

    # Obtenemos la clasificación que tienen que tener los grafos contrafactuales
    objetivo =  1 - FuncionesAlgoritmo.clasificar(poblacionActual[0], clf)

    print("Fitness de la población inicial:")
    fitness_poblacion = [FuncionesAlgoritmo.fitness(x, grafos_originales_nx) for x in poblacionActual]
    print(fitness_poblacion)

    parejas = list(itertools.combinations(poblacionActual, 2))

    # Parámetros del algoritmo genético
    

    # para cada permutacion de los grafos originales calculamos la interseccion de las aristas y las guardamos en la lista 
    # Lista para guardar las combinaciones agrupadas por tamaño (excluyendo tamaño 1)
    combinaciones_grafos = []

    # Generar combinaciones para subconjuntos de diferentes tamaños (sin incluir tamaño 1)
    for size in range(len(grafos_originales_nx), 1, -1):  # Desde 5 grafos hasta 2
        combinaciones = list(itertools.combinations(grafos_originales_nx, size))
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

    for iteracion in range(generaciones):
        # print(f"\nIteración {iteracion + 1}")
        
        # Generamos todas las combinaciones de parejas en la población actual.
        parejas = list(itertools.combinations(poblacionActual, 2))
        
        # Creamos una lista para almacenar la nueva descendencia generada en esta iteración.
        nueva_descendencia = []
        
        # Realizamos el cruce para cada pareja y añadimos los hijos a la lista de descendencia.
        for padre, madre in parejas:
            padre = FuncionesAlgoritmo.graphToRepr(padre)
            madre = FuncionesAlgoritmo.graphToRepr(madre)
            hijo1, hijo2 = FuncionesAlgoritmo.cruce(padre, madre, cruce)
            # Comprobamos que los hijos sean conexos
            hijo1 = FuncionesAlgoritmo.reprToGraph(hijo1)
            hijo2 = FuncionesAlgoritmo.reprToGraph(hijo2)

            if FuncionesAlgoritmo.conexo(hijo1, permutaciones_aristas_grafos_original, clf, objetivo):
                #print("Hijo 1 es conexo no se descarta")
                nueva_descendencia.append(hijo1)

            
            if FuncionesAlgoritmo.conexo(hijo2, permutaciones_aristas_grafos_original, clf, objetivo):
                #print("Hijo 2 es conexo y no se descarta")
                nueva_descendencia.append(hijo2)

        
            
            
            
        
        # Añadimos la nueva descendencia a la población actual
        print(f"Descendencia generada: {len(nueva_descendencia)} individuos")
        poblacionActual.extend(nueva_descendencia)
        
        # Si la población supera el límite, nos quedamos con los 50 mejores individuos
        if len(poblacionActual) > num_individuos:
            poblacionActual = sorted(poblacionActual, key=lambda x: FuncionesAlgoritmo.fitness(x,grafos_originales_nx))[:num_individuos]

        # Mostrar el estado de la población
        #print(f"Población actual ({len(poblacionActual)} individuos): {poblacionActual}")
        print("Fitness de la población actual:")
        fitness_poblacion = [FuncionesAlgoritmo.fitness(x, grafos_originales_nx) for x in poblacionActual]
        print(fitness_poblacion)

    # Resultado final
    # print("\nPoblación final:")
    # print(poblacionActual)
    print("Fitness de la población final:")
    fitness_poblacion = [FuncionesAlgoritmo.fitness(x, grafos_originales_nx) for x in poblacionActual]
    print(fitness_poblacion)
    valor_poblacion = [Importargrafos.oracle(nx.adjacency_matrix(x).toarray(), clf) for x in poblacionActual]
    print(valor_poblacion)
    return poblacionActual[0], FuncionesAlgoritmo.fitness(poblacionActual[0], grafos_originales_nx)

# importamos los grafos y el clasificador
graphs,clf = Importargrafos.importgrafos()

# parámetros del algoritmo genético
numero_grafos = [2, 4, 6] # Número de grafos originales
max_individuos = [10, 20, 30]  # Número máximo de individuos en la población
num_iteraciones = [10, 20, 30]  # Número de iteraciones de cruce
op_cruce = [FuncionesAlgoritmo.cruce_un_punto, FuncionesAlgoritmo.cruce_dos_puntos]  # Operador de cruce


max_num_grafos = max(numero_grafos)
archivo_salida = "resultados.csv"

grafos_originales = []

random.seed(1234)

while max_num_grafos > 0:
        grafo = graphs[random.choice(list(graphs.keys()))][1] # elegimos un grafo aleatorio el diccionario nos devuelve una tupla de etiqueta y grafo
        if Importargrafos.oracle(grafo, clf) == 0:
            grafos_originales.append(grafo)
            max_num_grafos = max_num_grafos-1

poblacionInicial = list()
    
for grafo in grafos_originales:
    # i = 0
    contrafactual = None
    while contrafactual is None:
        contrafactual = ofs(grafo, clf)
        # i += 1
    poblacionInicial.append(contrafactual)
# print(f"numero de errores {i} \n")

# print(f"población inicial {poblacionInicial}")
# print(f"grafos originales {grafos_originales}")

# Escritura del fichero de resultados
with open(archivo_salida, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Escribir cabecera
    writer.writerow(["Numero_grafos","Poblacion_maxima", "Cruce", "Numero_iteraciones", "Score", "Tiempo_de_ejecución"])

    # Probar todas las combinaciones de parámetros
    for numero_grafos, max_individuos, op_cruce, num_iteraciones in itertools.product(numero_grafos, max_individuos, op_cruce, num_iteraciones):
        print(f"Probando con {numero_grafos} grafos, {max_individuos} individuos, {op_cruce.__name__} y {num_iteraciones} iteraciones")
        inicio = time.time()
        mejor_grafo, score = algoritmo_genetico(max_individuos, op_cruce,num_iteraciones, grafos_originales[:numero_grafos], poblacionInicial[:numero_grafos], clf)
        tiempo_ejecucion = time.time() - inicio

        # Guardar resultados en el fichero
        writer.writerow([numero_grafos, max_individuos, op_cruce.__name__, num_iteraciones, score, tiempo_ejecucion])
