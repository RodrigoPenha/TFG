# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:17:50 2024

@author: rodri
"""

import csv
import time
import FuncionesAlgoritmo
import Importargrafos
import Visualizacion
import networkx as nx
import random
import itertools
from sortedcontainers import SortedKeyList

from obs import obs
from ofs import ofs2
import pickle


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
    probabilidades_acumuladas = list(itertools.accumulate(probabilidades))
    # Elegir el primer individuo
    r1 = random.random()
    ind1 = next(i for i, prob in enumerate(probabilidades_acumuladas) if r1 <= prob)

    # Elegir el segundo índice asegurando que sea distinto del primero
    while True:
        r2 = random.random()
        ind2 = next(i for i, prob in enumerate(probabilidades_acumuladas) if r2 <= prob)
        if ind1 != ind2:
            break

    seleccionados = poblacion[ind1], poblacion[ind2]  # Selecciona 2 padres
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

    for i, individuo in enumerate(poblacionActual):
        print(f"Individuo {i}: {individuo.fitness}")
        for j, grafo in enumerate(grafos_originales_nx):
            print(f"distancia grafo {j}: {len(set(individuo.grafo.edges).symmetric_difference(set(grafo.edges)))}")

    for iteracion in range(iteraciones):
        # print(f"\nIteración {iteracion + 1}")
        # for i, individuo in enumerate(poblacionActual):
        #     print(f"Individuo {i}: {individuo.fitness}")
        #     for j, grafo in enumerate(grafos_originales_nx):
        #         print(f"distancia grafo {j}: {len(set(individuo.grafo.edges).symmetric_difference(set(grafo.edges)))}")
        
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
            if FuncionesAlgoritmo.clasificar(hijo1, clf) == objetivo:
                #print("Hijo 1 clasifica igual que el objetivo")
                poblacionActual.add(Individuo(hijo1, grafos_originales_nx))
        else:
            pass
            print("Hijo 1 no es conexo se descarta")

        if FuncionesAlgoritmo.conexo(hijo2, permutaciones_aristas_grafos_original, clf, objetivo):
            if FuncionesAlgoritmo.clasificar(hijo2, clf) == objetivo:
                #print("Hijo 2 clasifica igual que el objetivo")
                poblacionActual.add(Individuo(hijo2, grafos_originales_nx))
        else:    
            print("Hijo 2 no es conexo se descarta")
        
        
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
    for i, individuo in enumerate(poblacionActual):
        print(f"Individuo {i}: {individuo.fitness}")
        for j, grafo in enumerate(grafos_originales_nx):
             print(f"distancia grafo {j}: {len(set(individuo.grafo.edges).symmetric_difference(set(grafo.edges)))}")

    # Guardamos los 5 mejores grafos (imagen + GraphML reutilizable)
    Visualizacion.guardar_mejores_grafos(poblacionActual, n=5)

    return poblacionActual[0].grafo, poblacionActual[0].fitness

# importamos los grafos y el clasificador
random.seed(12345)
graphs,clf = Importargrafos.importgrafos()

# parámetros del algoritmo genético
numero_grafos = [5] # Número de grafos originales
max_individuos = [200]  # Número máximo de individuos en la población
num_iteraciones = [25000]  # Número de iteraciones de cruce
op_cruce = [FuncionesAlgoritmo.cruce_uniforme]  # Operador de cruce


max_num_grafos = max(numero_grafos)
archivo_salida = "resultados.csv"

grafos_originales = []

aleatorio = True

if aleatorio:
    while max_num_grafos > 0:
            grafo2 = graphs[random.choice(list(graphs.keys()))][1] # elegimos un grafo aleatorio el diccionario nos devuelve una tupla de etiqueta y grafo
            if Importargrafos.oracle(grafo2, clf) == 0:
                grafos_originales.append(grafo2)
                max_num_grafos = max_num_grafos-1
else:
    #cargamos los grafos de un fichero
    archivo_grafos = "grafos_cercanos.pkl"
    with open(archivo_grafos, "rb") as f:
        grafos_originales = pickle.load(f)

poblacionInicial = list()
    
for grafo2 in grafos_originales:
    # i = 0
    contrafactual = None
    while contrafactual is None:
        print("Calculando contrafactual")
        contrafactual = ofs2(grafo2, clf)
        # i += 1
    contrafactual = obs(grafo2, contrafactual, clf, 5, 4000)
    print("Contrafactual calculado")
    poblacionInicial.append(contrafactual)

# Guardamos los grafos originales y los contrafactuales iniciales (imagen + GraphML)
Visualizacion.guardar_grafos(grafos_originales, "grafos_originales")
Visualizacion.guardar_contrafactuales(poblacionInicial, grafos_originales, "contrafactuales")

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
