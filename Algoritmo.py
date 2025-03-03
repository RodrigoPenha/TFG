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
from sortedcontainers import SortedKeyList

from obs import obs
from ofs import ofs2


class Individuo:
    def __init__(self, grafo, grafos_originales_nx):
        self.grafo = grafo
        self.fitness = FuncionesAlgoritmo.fitness(grafo, grafos_originales_nx)

    def __repr__(self):
        return f"Individuo({self.fitness})"

def seleccion_ruleta(poblacion: list[Individuo]):
    fitness_inverso = [1/f.fitness for f in poblacion]  # Como es minimización
    suma_fitness = sum(fitness_inverso)
    probabilidades = [f/suma_fitness for f in fitness_inverso]

    seleccionados = random.choices(poblacion, weights=probabilidades, k=2)  # Selecciona 2 padres
    return seleccionados

def algoritmo_genetico(num_individuos, cruce, iteraciones, originales, iniciales, clf):

    

    # Convertimos las representaciones de los grafos a objetos de la clase nx.Graph
    grafos_originales_nx = [nx.from_numpy_array(grafo) for grafo in originales]
    # creamos la sorted list de los individuos e introducimos los grafos iniciales
    poblacionActual = [Individuo(nx.from_numpy_array(grafo), grafos_originales_nx) for grafo in iniciales]
    
    # Ordenamos la población actual por fitness
    poblacionActual = SortedKeyList(poblacionActual, key=lambda x: x.fitness)
    

    # Obtenemos la clasificación que tienen que tener los grafos contrafactuales
    objetivo =  1 - FuncionesAlgoritmo.clasificar(poblacionActual[0].grafo, clf)

    print("Fitness de la población inicial:")
    print(poblacionActual)   

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

    for iteracion in range(iteraciones):
        print(f"\nIteración {iteracion + 1}")
        
        
        # Realizamos el cruce para cada pareja y añadimos los hijos a la lista de descendencia.
        # Selección de padres
        padre, madre = seleccion_ruleta(poblacionActual)
        # los transformamos a representaciones
        repr_padre = FuncionesAlgoritmo.graphToRepr(padre.grafo)
        repr_madre = FuncionesAlgoritmo.graphToRepr(madre.grafo)
        # cruzamos los padres
        hijo1, hijo2 = FuncionesAlgoritmo.cruce(repr_padre, repr_madre, cruce)
        # los transformamos a grafos
        hijo1 = FuncionesAlgoritmo.reprToGraph(hijo1)
        hijo2 = FuncionesAlgoritmo.reprToGraph(hijo2)

        # Comprobamos si los hijos son conexos
        if FuncionesAlgoritmo.conexo(hijo1, permutaciones_aristas_grafos_original, clf, objetivo):
            #print("Hijo 1 es conexo no se descarta")
            poblacionActual.add(Individuo(hijo1, grafos_originales_nx))
        else:
            pass
            #print("Hijo 1 no es conexo se descarta")

        if FuncionesAlgoritmo.conexo(hijo2, permutaciones_aristas_grafos_original, clf, objetivo):
            #print("Hijo 2 es conexo no se descarta")
            poblacionActual.add(Individuo(hijo2, grafos_originales_nx))
        else:
            pass    
            #print("Hijo 2 no es conexo se descarta")
        
        
        # Si la población supera el límite, nos quedamos con los 50 mejores individuos
        if len(poblacionActual) > num_individuos:
            del poblacionActual[num_individuos:]  #Borra desde num_individuos hasta el final

        # Mostrar el estado de la población
        # print("Fitness de la población actual:")
        # print(poblacionActual)

    # Resultado final
    # print("\nPoblación final:")
    # print(poblacionActual)
    print("Fitness de la población final:")
    print(poblacionActual)
    return poblacionActual[0].grafo, poblacionActual[0].fitness

# importamos los grafos y el clasificador
graphs,clf = Importargrafos.importgrafos()

# parámetros del algoritmo genético
numero_grafos = [4, 6] # Número de grafos originales
max_individuos = [30, 50, 100]  # Número máximo de individuos en la población
num_iteraciones = [200, 500, 1000]  # Número de iteraciones de cruce
op_cruce = [FuncionesAlgoritmo.cruce_un_punto, FuncionesAlgoritmo.cruce_dos_puntos]  # Operador de cruce


max_num_grafos = max(numero_grafos)
archivo_salida = "resultados.csv"

grafos_originales = []

random.seed(12345)

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
        print("Calculando contrafactual")
        contrafactual = ofs2(grafo, clf)
        # i += 1
    contrafactual = obs(grafo, contrafactual, clf, 5, 4000)
    print("Contrafactual calculado")
    poblacionInicial.append(contrafactual)

# matriz con las distancias de los grafos originales
# Calcular la distancia de edición entre los grafos originales y guardar los resultados en una matriz
distancias_edicion = [[0] * len(grafos_originales) for _ in range(len(grafos_originales))]
print("Calculando distancias de edición entre los grafos originales")
for i, grafo1 in enumerate(grafos_originales):
    print(f"Calculando distancias de edición para el grafo {i}")
    for j, grafo2 in enumerate(grafos_originales):
        if i != j:
            distancias_edicion[i][j] = len(set(nx.from_numpy_array(grafo1).edges).difference(set(nx.from_numpy_array(grafo2).edges))) + len(set(nx.from_numpy_array(grafo2).edges).difference(set(nx.from_numpy_array(grafo1).edges)))
        else:
            distancias_edicion[i][j] = 0  # La distancia de un grafo consigo mismo es 0

print("Matriz de distancias de edición:")
for fila in distancias_edicion:
    print(f'{fila} media:{sum(fila)/(len(fila))}')

# matriz con las distancias de los grafos en la población inicial
distancias_edicion_poblacion = [[0] * len(poblacionInicial) for _ in range(len(poblacionInicial))]

for i, grafo1 in enumerate(poblacionInicial):
    print(f"Calculando distancias de edición para el grafo {i}")
    for j, grafo2 in enumerate(grafos_originales):
        distancias_edicion_poblacion[i][j] = len(set(nx.from_numpy_array(grafo1).edges).difference(set(nx.from_numpy_array(grafo2).edges))) + len(set(nx.from_numpy_array(grafo2).edges).difference(set(nx.from_numpy_array(grafo1).edges)))


print("Matriz de distancias de edición de la población inicial:")
for fila in distancias_edicion_poblacion:
    print(f'{fila} media:{sum(fila)/(len(fila))}')



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
