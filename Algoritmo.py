# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:17:50 2024

@author: rodri
"""

import csv
import os
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
        self.clave = FuncionesAlgoritmo.clave_grafo(grafo)  # identidad por matriz de adyacencia

    def __repr__(self):
        return f"Individuo({self.fitness})"

def seleccion_ruleta(poblacion: list[Individuo]):
    # Con menos de 2 individuos no existen dos padres distintos y el bucle de
    # abajo no terminaría nunca.
    if len(poblacion) < 2:
        raise ValueError("La ruleta necesita al menos 2 individuos distintos.")

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

def algoritmo_genetico(num_individuos, cruce, iteraciones, originales, iniciales, clf, prefijo_salida=None):

    

    # Convertimos las representaciones de los grafos a objetos de la clase nx.Graph
    grafos_originales_nx = [nx.from_numpy_array(grafo) for grafo in originales]
    # creamos la sorted list de los individuos e introducimos los grafos iniciales,
    # descartando duplicados (misma matriz de adyacencia) para que población y
    # conjunto de claves arranquen coherentes
    claves_poblacion = set()
    poblacionActual = []
    for grafo in iniciales:
        individuo = Individuo(nx.from_numpy_array(grafo), grafos_originales_nx)
        if individuo.clave not in claves_poblacion:
            claves_poblacion.add(individuo.clave)
            poblacionActual.append(individuo)

    # Ordenamos la población actual por fitness
    poblacionActual = SortedKeyList(poblacionActual, key=lambda x: x.fitness)


    # Obtenemos la clasificación que tienen que tener los grafos contrafactuales:
    # la contraria a la de los grafos ORIGINALES. Deducirla de poblacionActual[0]
    # la invertía, porque la población inicial ya es contrafactual y por tanto ya
    # clasifica como el objetivo.
    objetivo =  1 - FuncionesAlgoritmo.clasificar(grafos_originales_nx[0], clf)

    print("Fitness de la población inicial:")
    print(poblacionActual)   

    # para cada permutacion de los grafos originales calculamos la interseccion de las aristas y las guardamos en la lista 
    # Lista para guardar las combinaciones agrupadas por tamaño (excluyendo tamaño 1)
    combinaciones_grafos = []

    # Generar combinaciones para subconjuntos de diferentes tamaños (sin incluir tamaño 1)
    for size in range(len(grafos_originales_nx), 1, -1):  # Desde N grafos hasta 2
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

    # Guardamos el mejor individuo inicial (población ya ordenada por fitness) para
    # compararlo al final con la mejor solución encontrada por el genético.
    mejor_inicial = poblacionActual[0]

    def intentar_agregar(hijo, max_intentos_mutacion=10):
        # 1. Reparar conexidad del hijo del cruce (conexo puede modificarlo in place).
        if not FuncionesAlgoritmo.conexo(hijo, permutaciones_aristas_grafos_original, clf, objetivo):
            return False   # no se pudo conectar -> se descarta

        # 2. Intentar añadirlo; si es duplicado o no clasifica al objetivo, mutar
        #    (añadir una arista compartida por los originales) y reintentar.
        for intento in range(max_intentos_mutacion + 1):
            if FuncionesAlgoritmo.clasificar(hijo, clf) == objetivo:
                clave = FuncionesAlgoritmo.clave_grafo(hijo)   # matriz de adyacencia
                if clave not in claves_poblacion:
                    poblacionActual.add(Individuo(hijo, grafos_originales_nx))
                    claves_poblacion.add(clave)
                    return True
            # duplicado o no clasifica al objetivo: mutar y reintentar
            if intento < max_intentos_mutacion:
                hijo = FuncionesAlgoritmo.mutar(hijo, permutaciones_aristas_grafos_original)
        return False

    for iteracion in range(iteraciones):
        print(f"\nIteración {iteracion + 1}")
        # La ruleta necesita dos padres distintos; si la población se ha quedado
        # con un único individuo no hay nada que cruzar y paramos.
        if len(poblacionActual) < 2:
            print("[AVISO] Población con menos de 2 individuos: se detiene el genético.")
            break
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

        # Intentamos añadir cada hijo: rechaza duplicados (misma matriz de
        # adyacencia) y, si sale duplicado o no clasifica al objetivo, muta y reintenta.
        intentar_agregar(hijo1, 10)
        intentar_agregar(hijo2, 10)

        # Si la población supera el límite, nos quedamos con los mejores individuos.
        # Sincronizamos el conjunto de claves antes de borrar los peores.
        if len(poblacionActual) > num_individuos:
            for ind in poblacionActual[num_individuos:]:
                claves_poblacion.discard(ind.clave)
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

    # Comparación entre el mejor grafo inicial y la mejor solución encontrada por el genético.
    mejor_final = poblacionActual[0]
    mejora = mejor_inicial.fitness - mejor_final.fitness
    aristas_cambiadas = len(set(mejor_inicial.grafo.edges).symmetric_difference(set(mejor_final.grafo.edges)))
    print("\nComparación mejor inicial vs mejor final:")
    print(f"  Fitness mejor inicial: {mejor_inicial.fitness}")
    print(f"  Fitness mejor final:   {mejor_final.fitness}")
    porcentaje = (mejora / mejor_inicial.fitness * 100) if mejor_inicial.fitness else 0
    print(f"  Mejora: {mejora} ({porcentaje:.2f}%)")
    print(f"  Aristas distintas entre ambos grafos: {aristas_cambiadas}")

    # Prefijos de salida de las imágenes: si se pasa prefijo_salida, se usa para
    # no sobrescribir entre ejecuciones (p. ej. guardarlas junto al JSON del
    # experimento); si es None, se mantienen los nombres fijos por defecto.
    if prefijo_salida:
        pref_comparacion = f"{prefijo_salida}_comparacion"
        pref_mejores = f"{prefijo_salida}_mejores"
    else:
        pref_comparacion = "comparacion_inicial_final"
        pref_mejores = "mejores_grafos"

    # Imagen comparando el mejor grafo inicial con la mejor solución final:
    # aristas añadidas (0->1) en verde, eliminadas (1->0) en rojo.
    Visualizacion.guardar_comparacion_inicial_final(mejor_inicial.grafo, mejor_final.grafo, prefijo=pref_comparacion)

    # Guardamos los 5 mejores grafos (imagen + GraphML reutilizable). Se dibujan
    # como diff contra el mejor individuo inicial: en la vista plana no se
    # apreciaba qué había cambiado respecto al punto de partida.
    Visualizacion.guardar_mejores_grafos(poblacionActual, n=5, prefijo=pref_mejores,
                                         referencia=mejor_inicial.grafo)

    return poblacionActual[0].grafo, poblacionActual[0].fitness

if __name__ == "__main__":
    # importamos los grafos y el clasificador
    random.seed(12345)
    graphs, clf = Importargrafos.importgrafos()

    # parámetros del algoritmo genético
    numero_grafos = [5]  # Número de grafos originales
    max_individuos = [20]  # Número máximo de individuos en la población
    num_iteraciones = [2000]  # Número de iteraciones de cruce
    op_cruce = [FuncionesAlgoritmo.cruce_uniforme]  # Operador de cruce

    archivo_salida = "resultados.csv"

    # --- Fuente de los grafos originales (edita para elegir) ---
    # fuente:    "cercanos" | "lejanos" | "aleatorios" | "aleatorio"
    #            ("aleatorios" = grupo precomputado sin repeticiones;
    #             "aleatorio"  = muestreo al vuelo, puede repetir grafos)
    # tam_grupo: 2, 5, 8, 11 (carpeta del grupo precomputado; se ignora si aleatorio)
    # clase:     0 | 1 (clasificación del oráculo de los grafos originales)
    fuente = "cercanos"
    tam_grupo = 5
    clase = 0

    # Tope de llamadas a ofs2 por grafo antes de abandonar (evita bucle infinito).
    MAX_INTENTOS_CONTRAFACTUAL = 50

    grafos_originales = []
    if fuente == "aleatorio":
        max_num_grafos = max(numero_grafos)
        while max_num_grafos > 0:
            grafo2 = graphs[random.choice(list(graphs.keys()))][1]  # el diccionario devuelve (etiqueta, grafo)
            if Importargrafos.oracle(grafo2, clf) == clase:
                grafos_originales.append(grafo2)
                max_num_grafos = max_num_grafos - 1
    elif fuente in ("cercanos", "lejanos", "aleatorios"):
        # grupo precomputado por buscar_grafos_{cercanos,lejanos,aleatorios}.py
        archivo_grafos = os.path.join(f"grafos_{fuente}", f"N{tam_grupo}", f"clase{clase}.pkl")
        with open(archivo_grafos, "rb") as f:
            grafos_originales = pickle.load(f)
        print(f"Cargados {len(grafos_originales)} grafos de {archivo_grafos}")
    else:
        raise ValueError(
            f"fuente desconocida: {fuente!r} "
            "(usa 'cercanos', 'lejanos', 'aleatorios' o 'aleatorio')"
        )

    poblacionInicial = list()

    # ofs2 es heurístico y puede devolver None indefinidamente para un grafo
    # concreto, así que limitamos el número de intentos en lugar de reintentar
    # en un bucle infinito.
    for i, grafo2 in enumerate(grafos_originales):
        contrafactual = None
        for intento in range(1, MAX_INTENTOS_CONTRAFACTUAL + 1):
            print(f"Calculando contrafactual del grafo {i} (intento {intento})")
            contrafactual = ofs2(grafo2, clf)
            if contrafactual is not None:
                break
        if contrafactual is None:
            raise RuntimeError(
                f"No se encontró contrafactual para el grafo {i} tras "
                f"{MAX_INTENTOS_CONTRAFACTUAL} intentos."
            )
        contrafactual = obs(grafo2, contrafactual, clf, 5, 4000)
        print("Contrafactual calculado")
        poblacionInicial.append(contrafactual)

    # Guardamos los grafos originales y los contrafactuales iniciales (imagen + GraphML).
    # Los originales van en la vista normal (sin diff): no hay nada con lo que
    # compararlos, son el punto de partida.
    Visualizacion.guardar_grafos(grafos_originales, "grafos_originales")
    Visualizacion.guardar_contrafactuales(poblacionInicial, grafos_originales, "contrafactuales")

    # matriz con las distancias de los grafos originales
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
        writer.writerow(["Numero_grafos", "Poblacion_maxima", "Cruce", "Numero_iteraciones", "Score", "Tiempo_de_ejecución"])

        # Probar todas las combinaciones de parámetros
        for numero_grafos, max_individuos, op_cruce, num_iteraciones in itertools.product(numero_grafos, max_individuos, op_cruce, num_iteraciones):
            print(f"Probando con {numero_grafos} grafos, {max_individuos} individuos, {op_cruce.__name__} y {num_iteraciones} iteraciones")
            inicio = time.time()
            mejor_grafo, score = algoritmo_genetico(max_individuos, op_cruce, num_iteraciones, grafos_originales[:numero_grafos], poblacionInicial[:numero_grafos], clf)
            tiempo_ejecucion = time.time() - inicio

            # Guardar resultados en el fichero
            writer.writerow([numero_grafos, max_individuos, op_cruce.__name__, num_iteraciones, score, tiempo_ejecucion])
