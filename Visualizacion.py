# -*- coding: utf-8 -*-
"""Funciones de visualizacion y guardado de grafos.

Centraliza todo el dibujado para mantener el algoritmo libre de logica de
visualizacion. Para cada conjunto de grafos se generan tres salidas:
- <prefijo>.png: vista node-link (nodos y aristas), una celda grande por grafo.
- <prefijo>_matriz.png: mapa de calor de la matriz de adyacencia de cada grafo.
- <prefijo>_<i>.graphml: un fichero por grafo, abrible en Gephi/yEd/Cytoscape
  y recargable con nx.read_graphml.

Las dos vistas se complementan: la node-link muestra la 'forma' del grafo y la
matriz es mas legible cuando el grafo es denso (muchos nodos/aristas).
"""

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import networkx as nx
import numpy as np

# Colores del diff entre un grafo y su contrafactual
_COL_SIN_CAMBIO = "#bdbdbd"
_COL_AÑADIDA = "#2ca02c"   # arista 0 -> 1
_COL_ELIMINADA = "#d62728"  # arista 1 -> 0


def _a_nx(grafo):
    """Convierte una matriz de adyacencia numpy (o un nx.Graph) en nx.Graph."""
    if isinstance(grafo, nx.Graph):
        return grafo
    return nx.from_numpy_array(grafo)


def _dibujar_node_link(G, ax, titulo):
    """Dibuja el grafo como nodos y aristas, optimizado para grafos densos."""
    n = G.number_of_nodes()
    # Layout con buena separacion: k mayor reparte los nodos; mas iteraciones
    # estabilizan la disposicion. La semilla la hace reproducible.
    k = 1.5 / np.sqrt(n) if n else None
    pos = nx.spring_layout(G, k=k, iterations=200, seed=12345)
    grados = dict(G.degree())
    # Nodos pequenos; tamano y color segun el grado para resaltar los hubs.
    tam = [20 + 6 * grados[v] for v in G.nodes()]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", width=0.3, alpha=0.1)
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=tam,
        node_color=[grados[v] for v in G.nodes()], cmap="viridis", linewidths=0,
    )
    ax.set_title(titulo, fontsize=10)
    ax.axis("off")


def _dibujar_matriz(G, ax, titulo):
    """Dibuja la matriz de adyacencia del grafo como mapa de calor binario."""
    A = nx.to_numpy_array(G)
    ax.imshow(A > 0, cmap="binary", interpolation="nearest")
    ax.set_title(titulo, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def guardar_grafos(grafos, prefijo, titulos=None):
    """Guarda una lista de grafos (matrices numpy o nx.Graph) en varias vistas."""
    grafos = [_a_nx(g) for g in grafos]
    cols = len(grafos)
    if cols == 0:
        return

    def titulo(i):
        return titulos[i] if titulos else f"#{i + 1}"

    # Vista node-link (una celda grande por grafo) + GraphML reutilizable
    fig, axes = plt.subplots(1, cols, figsize=(6.5 * cols, 6.5))
    for i, (ax, G) in enumerate(zip(np.atleast_1d(axes), grafos)):
        _dibujar_node_link(G, ax, titulo(i))
        nx.write_graphml(G, f"{prefijo}_{i + 1}.graphml")
    fig.tight_layout()
    fig.savefig(f"{prefijo}.png", dpi=150)
    plt.close(fig)

    # Vista matriz de adyacencia
    fig, axes = plt.subplots(1, cols, figsize=(5 * cols, 5))
    for i, (ax, G) in enumerate(zip(np.atleast_1d(axes), grafos)):
        _dibujar_matriz(G, ax, titulo(i))
    fig.tight_layout()
    fig.savefig(f"{prefijo}_matriz.png", dpi=150)
    plt.close(fig)

    print(f"Guardados {cols} grafos en {prefijo}.png, {prefijo}_matriz.png y {prefijo}_*.graphml")


def _clasificar_aristas(Go, Gc):
    """Devuelve (sin_cambio, anadidas, eliminadas) comparando original y contrafactual."""
    eo = set(map(frozenset, Go.edges()))
    ec = set(map(frozenset, Gc.edges()))
    sin_cambio = [tuple(e) for e in (eo & ec)]
    anadidas = [tuple(e) for e in (ec - eo)]   # 0 -> 1
    eliminadas = [tuple(e) for e in (eo - ec)]  # 1 -> 0
    return sin_cambio, anadidas, eliminadas


def _dibujar_node_link_diff(Go, Gc, ax, titulo):
    """Node-link del contrafactual resaltando las aristas que cambian vs el original."""
    sin_cambio, anadidas, eliminadas = _clasificar_aristas(Go, Gc)
    # Layout sobre la union de aristas para poder situar tambien las eliminadas.
    U = nx.Graph()
    U.add_nodes_from(Go.nodes())
    U.add_edges_from(sin_cambio + anadidas + eliminadas)
    n = U.number_of_nodes()
    k = 1.5 / np.sqrt(n) if n else None
    pos = nx.spring_layout(U, k=k, iterations=200, seed=12345)
    nx.draw_networkx_edges(U, pos, edgelist=sin_cambio, ax=ax,
                           edge_color=_COL_SIN_CAMBIO, width=0.3, alpha=0.08)
    nx.draw_networkx_edges(U, pos, edgelist=eliminadas, ax=ax,
                           edge_color=_COL_ELIMINADA, width=0.9, alpha=0.7, style="dashed")
    nx.draw_networkx_edges(U, pos, edgelist=anadidas, ax=ax,
                           edge_color=_COL_AÑADIDA, width=0.9, alpha=0.85)
    nx.draw_networkx_nodes(U, pos, ax=ax, node_size=15, node_color="#444444", linewidths=0)
    ax.set_title(titulo, fontsize=10)
    ax.axis("off")


def _dibujar_matriz_diff(Go, Gc, ax, titulo):
    """Matriz de adyacencia del contrafactual coloreada por categoria de cambio."""
    nodos = list(Go.nodes())
    Ao = nx.to_numpy_array(Go, nodelist=nodos) > 0
    Ac = nx.to_numpy_array(Gc, nodelist=nodos) > 0
    # 0 = sin arista, 1 = sin cambio, 2 = anadida (0->1), 3 = eliminada (1->0)
    cat = np.zeros(Ao.shape, dtype=int)
    cat[Ao & Ac] = 1
    cat[~Ao & Ac] = 2
    cat[Ao & ~Ac] = 3
    cmap = ListedColormap(["white", _COL_SIN_CAMBIO, _COL_AÑADIDA, _COL_ELIMINADA])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    ax.imshow(cat, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(titulo, fontsize=10)


def guardar_contrafactuales(contrafactuales, originales, prefijo="contrafactuales", titulos=None):
    """Guarda los contrafactuales resaltando las diferencias con su grafo original.

    Compara contrafactuales[i] con originales[i]. Genera node-link y matriz con
    las aristas anadidas (0->1) en verde y las eliminadas (1->0) en rojo.
    """
    cfs = [_a_nx(g) for g in contrafactuales]
    ors = [_a_nx(g) for g in originales]
    cols = len(cfs)
    if cols == 0:
        return
    if len(ors) < cols:
        raise ValueError("Hacen falta tantos grafos originales como contrafactuales.")

    def titulo(i, Go, Gc):
        if titulos:
            return titulos[i]
        _, anadidas, eliminadas = _clasificar_aristas(Go, Gc)
        return f"#{i + 1}  +{len(anadidas)} / -{len(eliminadas)}"

    # Vista node-link con el diff + GraphML del contrafactual
    fig, axes = plt.subplots(1, cols, figsize=(6.5 * cols, 6.5))
    for i, (ax, Go, Gc) in enumerate(zip(np.atleast_1d(axes), ors, cfs)):
        _dibujar_node_link_diff(Go, Gc, ax, titulo(i, Go, Gc))
        nx.write_graphml(Gc, f"{prefijo}_{i + 1}.graphml")
    leyenda = [
        Line2D([0], [0], color=_COL_AÑADIDA, lw=2, label="0->1 (añadida)"),
        Line2D([0], [0], color=_COL_ELIMINADA, lw=2, ls="--", label="1->0 (eliminada)"),
        Line2D([0], [0], color=_COL_SIN_CAMBIO, lw=2, label="sin cambio"),
    ]
    fig.legend(handles=leyenda, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(f"{prefijo}.png", dpi=150)
    plt.close(fig)

    # Vista matriz de adyacencia con el diff
    fig, axes = plt.subplots(1, cols, figsize=(5 * cols, 5))
    for i, (ax, Go, Gc) in enumerate(zip(np.atleast_1d(axes), ors, cfs)):
        _dibujar_matriz_diff(Go, Gc, ax, titulo(i, Go, Gc))
    leyenda = [
        Patch(color=_COL_AÑADIDA, label="0->1 (añadida)"),
        Patch(color=_COL_ELIMINADA, label="1->0 (eliminada)"),
        Patch(color=_COL_SIN_CAMBIO, label="sin cambio"),
    ]
    fig.legend(handles=leyenda, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(f"{prefijo}_matriz.png", dpi=150)
    plt.close(fig)

    print(f"Guardados {cols} contrafactuales en {prefijo}.png, {prefijo}_matriz.png y {prefijo}_*.graphml")


def guardar_mejores_grafos(poblacion, n=5, prefijo="mejores_grafos"):
    """Guarda los n mejores individuos de la poblacion (node-link + matriz + GraphML).

    Espera objetos con atributos .grafo (nx.Graph) y .fitness.
    """
    mejores = list(poblacion[:n])
    titulos = [f"#{i + 1}  fitness={ind.fitness:.4f}" for i, ind in enumerate(mejores)]
    guardar_grafos([ind.grafo for ind in mejores], prefijo, titulos)
    return mejores