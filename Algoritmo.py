# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 13:17:50 2024

@author: rodri
"""

import FuncionesAlgoritmo
import networkx as nx

import matplotlib.pyplot as plt

G = nx.Graph()

G.add_nodes_from(['v1','v2','v3','v4'])

G1 = G.copy()

G.add_edges_from([('v1','v2'),('v2','v3'),('v2','v4'),('v3','v4')])

G1.add_edges_from([('v1','v2'),('v2','v3'),('v2','v4'),('v3','v4'), ('v1', 'v4')])

pos = nx.spring_layout(G)  # Posiciona los nodos
nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

nx.draw_networkx_labels(G, pos)

# Mostrar el grafo
plt.title("G Representado")
plt.show()

pos = nx.spring_layout(G1)  # Posiciona los nodos
nx.draw(G1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

nx.draw_networkx_labels(G1, pos)

# Mostrar el grafo
plt.title("G1 Representado")
plt.show()

repr_G = FuncionesAlgoritmo.graphToRepr(G)
repr_G1 = FuncionesAlgoritmo.graphToRepr(G1)


hijo1, hijo2 = FuncionesAlgoritmo.cruce_dos_puntos(repr_G, repr_G1)

G_hijo1 = FuncionesAlgoritmo.reprToGraph(hijo1)


pos = nx.spring_layout(G_hijo1)  # Posiciona los nodos
nx.draw(G_hijo1, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

nx.draw_networkx_labels(G_hijo1, pos)

# Mostrar el grafo
plt.title("G Hijo1")
plt.show()

G_hijo2 = FuncionesAlgoritmo.reprToGraph(hijo2)

pos = nx.spring_layout(G_hijo2)  # Posiciona los nodos
nx.draw(G_hijo2, pos, with_labels=False, node_color='lightblue', node_size=700, font_size=16, font_color='black', font_weight='bold', edge_color='gray')

nx.draw_networkx_labels(G_hijo2, pos)

# Mostrar el grafo
plt.title("G Hijo2")
plt.show()