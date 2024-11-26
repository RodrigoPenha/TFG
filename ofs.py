from Importargrafos import oracle
import random
import copy

'''
Algoritmo que realiza una búsqueda heurística de un primer grafo contrafactual 
a partir de modificaciones sobre el grafo E introducido como parámetro.
E = grafo, k = las aristas que se modifican en cada iteración, max = número máximo de iteraciones a realizar

returns E_c El grafo contrafactual encontrado o None si no ha sido posible
'''
def ofs(E, clf, k = 5, max = 2000,):
    i = 0
    E_c = copy.deepcopy(E) # Copia profunda para no modificar los valores del grafo original E
    edges = set() # Conjunto para almacenar las aristas editadas

    while i < max and oracle(E_c, clf) == oracle(E, clf):
        i += 1
        j = 0
        while j < k:
            j += 1
            # Número entero aleatorio para seleccionar la operación a realizar
            if random.randint(0,1) < 0.5:
                # Selecciona una arista cualquiera que no esté contenida en E ni edges
                edge = pick(matrix_and_list(E, edges, 1), 0)
                if edge is None:
                    print("Error: It doesn't exists more edges")
                    return None
                # La arista es añadida al grafo contrafactual candidato y al conjunto edges
                mod_edge_graph(E_c, edge, 1)
                edges.add(edge)
            else:
                # Selecciona una arista cualquiera que esté contenida en E y no en edges
                edge = pick(matrix_and_list(E, edges, 0), 1)
                if edge is None:
                    print("Error: It doesn't exists more edges")
                    return None
                # La arista es eliminada del grafo contrafactual candidato y añadida al conjunto edges
                mod_edge_graph(E_c, edge, 0)
                edges.add(edge)

    # Se retorna el grafo si es clasificado en la clase opuesta
    if oracle(E_c, clf) == 1 - oracle(E, clf):
        return E_c
    else:
        return None
    
''' 
Función auxiliar utilizado para añadir o eliminar una arista de un grafo, representado en matriz de adyacencia.
graph = Grafo a modificar, edge = arista a modificar y value = 0 (eliminar) o 1 (añadir)
'''
def mod_edge_graph(graph, edge, value): 
    graph[edge[0]][edge[1]] = value
    graph[edge[1]][edge[0]] = value

'''
Función que añade o eliminar las aristas que se le introducen al grafo correspondiente. 
Similar al método anterior pero esta recibe una lista de aristas L.
graph = Grafo a modificar, L = lista de aristas a modificar, op = operación a realizar, para eliminar (0) y añadir (1)
'''
def matrix_and_list(graph, L, op): 
    aux = copy.deepcopy(graph)
    for edge in L:
        mod_edge_graph(aux, edge, op)
    return aux
    
'''
Función encargado de seleccionar una arista aleatoria a partir de la matriz de adyacencia introducido "graph".
'''
def pick(graph, value):
    x = random.randint(0, len(graph)-1)
    y = random.randint(0, len(graph)-1)

    for i in range(x,len(graph)):
        for j in range(0, len(graph)):
            if (i != x or j >= y) and graph[i][j] == value and i != j:
                return (i,j)
            
    for i in range(0,x+1):
        for j in range(0, len(graph)):
            if (i != x or j < y) and graph[i][j] == value and i != j:
                return (i,j)
            
    return None
