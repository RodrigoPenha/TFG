# -*- coding: utf-8 -*-
"""
Algoritmo genetico de generacion de grafos contrafactuales
"""

import networkx as nx
import random
import matplotlib.pyplot as plt

labels = ['A','B','C']

graphs = list()

g1 = nx.Graph()

g1.add_node('A1', element='A')
g1.add_node('A2', element='A')
g1.add_node('B1', element='B')
g1.add_node('C1', element='C')
g1.add_node('C2', element='C')

g1.add_edges_from([('A1', 'A2'),('A2', 'C2'),('C2', 'A1'),('B1', 'A2'),('C1', 'A1')])


def modify_graph(G):
    # Elegir una acción aleatoria
    action = random.choice(['remove_node', 'add_node_edge', 'add_edge'])
    
    if action == 'remove_node':
        # Eliminar un nodo aleatorio, si hay nodos disponibles
        if len(G.nodes) > 0:
            node_to_remove = random.choice(list(G.nodes))
            G.remove_node(node_to_remove)
            print(f"Removed node: {node_to_remove}")
    
    elif action == 'add_node_edge':
        # Crear un nuevo nodo y un enlace a un nodo existente
        new_label = random.choice(labels)
        new_node = f'{new_label}{len(G.nodes)}'  # Generar un nombre único
        if len(G.nodes) > 0:
            existing_node = random.choice(list(G.nodes))
            G.add_node(new_node, element=new_label)
            G.add_edge(new_node, existing_node)
            print(f"Added node: {new_node} and connected it to {existing_node}")
    
    elif action == 'add_edge':
        # Añadir un nuevo enlace entre dos nodos existentes
        if len(G.nodes) >= 2:
            nodes = random.sample(list(G.nodes), 2)
            G.add_edge(nodes[0], nodes[1])
            print(f"Added edge between: {nodes[0]} and {nodes[1]}")
            
# Visualizar el grafo           
pos = nx.spring_layout(g1)  # Posiciona los nodos
nx.draw(g1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# Etiquetas para los nodos usando solo el elemento
labels = {node: data['element'] for node, data in g1.nodes(data=True)}
nx.draw_networkx_labels(g1, pos, labels=labels)

# Mostrar el grafo
plt.title("Grafo Representado")
plt.show()
            

modify_graph(g1)

# Visualizar el grafo
pos = nx.spring_layout(g1)  # Posiciona los nodos
nx.draw(g1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

# Etiquetas para los nodos usando solo el elemento
labels = {node: data['element'] for node, data in g1.nodes(data=True)}
nx.draw_networkx_labels(g1, pos, labels=labels)

# Mostrar el grafo
plt.title("Grafo Modificado")
plt.show()
