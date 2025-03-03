from Importargrafos import oracle
import random
import copy
import networkx as nx

def mod_edge_graph(graph, edge, value): 
    graph[edge[0]][edge[1]] = value
    graph[edge[1]][edge[0]] = value

'''
Algoritmo que implementa la misma idea que el OFS original, pero añadiendo un enfoque del valor 
betweenness de las aristas proporcionado por la librería networkx.

E = grafo original
clf = clasificador necesario para la función oracle
k = número de aristas a modificar en cada iteración

returns E_c El grafo contrafactual encontrado o None si no ha sido posible
'''
def ofs2(E, clf,k = 5):
    i = 0
    E_c = copy.deepcopy(E)
    E_comp = complement(E)
    aristasEOrig = betweenness(E)
    aristasEComp = betweenness(E_comp)
    idx1 = 0
    idx2 = 0
    # Mientras no se hayan recorrido todas las aristas del grafo E y del grafo complementario E_comp, y que E_c siga en la misma clasificación que E
    while idx1 < len(aristasEOrig) and idx2 < len(aristasEComp) and oracle(E_c, clf) == oracle(E, clf):
        i += 1
        j = 0
        # Un bloque condicional para controlar que no se exceda el index de la lista al k tener valor 5.
        if idx2+k > len(aristasEComp):
            k = 1
        while j < k:
            j += 1
            rand = random.random()
            # Al tener siempre menos aristas en E, cuando llegue al último, rand = 0 para que siempre entre al cuerpo del caso verdadero
            if idx1 == len(aristasEOrig) - 1:
                rand = 0

            prob2 = len(aristasEComp) / (len(aristasEOrig) + len(aristasEComp))

            if rand < prob2: # Añade una arista del grafo complementario
                edge = aristasEComp[idx2]
                mod_edge_graph(E_c, edge, 1)
                idx2 += 1
            else: # Elimina una arista del grafo original
                edge = aristasEOrig[idx1]
                mod_edge_graph(E_c, edge, 0)
                idx1 += 1

    if oracle(E_c,clf) == 1 - oracle(E,clf):
        return E_c
    else:
        return None
    
'''
Función que retorna el grafo complementario al grafo "graph" introducido.
'''
def complement(graph):
    comp = copy.deepcopy(graph)
    for i in range(len(graph)):
        for j in range(i+1, len(graph)):
            if comp[i][j] == 1:
                mod_edge_graph(comp, (i,j), 0)
            else:
                mod_edge_graph(comp, (i,j), 1)
    return comp

'''
Función que ordena las aristas para que una arista (i,j), i siempre sea menor que j.
'''
def sort_edges(betweenness):
    edges = set()
    for edge in betweenness.keys():
        if edge[0] > edge[1]:
            edges.add((edge[1], edge[0]))
        else:
            edges.add((edge))
    return list(edges)
        
'''
Función que dado un grafo, devuelve las aristas ordenadas de mayor a menor betweenness en estructura de diccionario.
'''
def betweenness(graph):
    graph_bet = nx.from_numpy_array(graph)
    edge_betweenness = nx.edge_betweenness_centrality(graph_bet)
    sorted_betweenness = dict(sorted(edge_betweenness.items(), key=lambda x:x[1], reverse=True))
    sorted_edges = sort_edges(sorted_betweenness)
    
    return sorted_edges
