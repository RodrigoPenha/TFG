import copy
import random
from preprocesado import oracle
from ofs2 import sort_edges, mod_edge_graph
import networkx as nx

'''
Algoritmo encargado de encontrar un segundo grafo contrafactual lo más óptimo posible,
es decir, con la minima distancia de edición posible al grafo E original desde el grafo contrafactual
encontrado Ec1 por OFS.

E = grafo original a la que se quiere volver
Ec1 = grafo obtenido en el algoritmo previo (OFS)
k = número de aristas a modificar en cada iteración
max = número máximo de iteraciones a realizar
subset = variable booleano para seleccionar el algoritmo: True indica la versión implementada por nosotros; y False el original
'''
def obs(E, Ec1, k = 5, max = 2000, subset = False): 
    E_c = copy.deepcopy(Ec1)
    i = 0
    E_d = symmetric_diff(E, E_c) # Consigue una lista de aristas que tienen diferentes E y E_c
    while i < max and len(E_d) > 0:
        i+=1
        k = min(k, len(E_d))
        E_dk = pick(k, E_d, subset) 
        E_ci = matrix_edges(E_c, E_dk)
        if oracle(E_ci) == 1 - oracle(E): # Si E_ci sigue siendo el grafo contrafactual óptimo hasta el momento
            k += 1
            E_c = copy.deepcopy(E_ci)
            E_d = symmetric_diff(E, E_c)
        elif k > 1: # Decrementa para volver hacia atrás, pues ya se ha sobrepasado la línea y E_ci se posiciona en la misma clasificación que E
            k -= 1
        else:
            E_d_aux = []
            for edge in E_d:
                if edge not in E_dk:
                    E_d_aux.append(edge)
            if subset:
                k = 5
            E_d = E_d_aux

    return E_c

'''
Función implementada para ejecutar la selección de un subconjunto, exactamente la mitad, de aristas de mayor o menor betweenness.
E_d = lista de aristas a seleccionar, reverse = True (mayor a menor), False (menor a mayor)
'''
def subset_E_d(E_d, reverse):
    E_d_copy = copy.deepcopy(E_d)
    graphE_d = nx.from_edgelist(E_d_copy)
    edge_betweenness = nx.edge_betweenness_centrality(graphE_d)
    sorted_betweenness = dict(sorted(edge_betweenness.items(), key=lambda x:x[1], reverse=reverse))
    sorted_edges = sort_edges(sorted_betweenness)

    return sorted_edges[0:len(sorted_edges)//2]

'''
Función que realiza la diferencia simétrica entre una matriz de adyacencia y una lista de aristas.
graph = grafo, edges = lista de aristas
returns Una matriz de adyacencia con la diferencia
'''
def matrix_edges(graph, edges):
    E_ci = copy.deepcopy(graph)
    for edge in edges:
        if E_ci[edge[0]][edge[1]] == 1:
            mod_edge_graph(E_ci, edge, 0)
        else:
            mod_edge_graph(E_ci, edge, 1)

    return E_ci

'''
Función que realiza la diferencia simétrica entre dos matrices de adyacencia.
returns Una lista de aristas con las aristas diferentes entre ambos.
'''
def symmetric_diff(graph1, graph2):
    edges = []
    diff = abs(graph1-graph2)
    for i in range(len(graph1)):
        for j in range(len(graph1)):
            if diff[i][j] == 1:
                edges.append((i,j))

    return edges

'''
Función que selecciona "num_edges" aristas de la lista de aristas candidato "pool". Si subset es True, entonces se selecciona de un subconjunto de pool.
'''
def pick(num_edges, pool, subset):
    pool_copy = copy.deepcopy(pool)
    if subset:
        pool_copy = subset_E_d(pool)
    edges = set() # Para no añadir una arista más de una vez
    while len(edges) < num_edges:
        index = random.randint(0, len(pool_copy) - 1)
        edges.add(pool_copy[index])

    return list(edges) # Finalmente se retorna en estructura de lista para fácil manipulación