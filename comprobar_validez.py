# -*- coding: utf-8 -*-
"""
Comprueba que las soluciones guardadas son contrafactuales válidos.

Un contrafactual de un grupo de grafos de clase c tiene que cumplir dos cosas:

  1. que el oráculo lo clasifique como 1 - c (si no, no es un contrafactual:
     es un grafo parecido a los de entrada y de la misma clase),
  2. que sea conexo (restricción del problema).

El score que guarda la experimentación NO comprueba nada de esto: es solo la
distancia media a los originales, así que una solución inválida puede tener un
score estupendo. Este script recorre `experimentos/<fuente>/N<tam>/` y comprueba
TODOS los grafos guardados de cada grupo: los `tam_grupo` contrafactuales de la
población inicial (`*_inicial_<i>.graphml`, junto al JSON) y los 5 mejores
individuos de cada combinación del barrido (`*_pob<N>_mejores_<k>.graphml`, en
la subcarpeta de su operador de cruce). A cada uno le pasa el oráculo y verifica
la conexión.

Salida por pantalla y en comprobar_validez.txt.
"""

import glob
import json
import os

import networkx as nx
import numpy as np

import Importargrafos


def matriz(grafo):
    """Matriz de adyacencia entera, con los nodos ordenados por su id.

    read_graphml devuelve los nodos como str y en orden de aparición; sin
    ordenar, los índices de nodo que usa el oráculo no corresponderían.
    """
    nodos = sorted(grafo.nodes(), key=int)
    return (nx.to_numpy_array(grafo, nodelist=nodos) > 0).astype(int)


def revisar(ruta_json, clf):
    """Comprueba clase y conexión de las soluciones de un grupo."""
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)
    # Bajo experimentos/ puede haber JSON de otras campanas (p. ej. la
    # comparacion de operadores de cruce), con otro esquema: se ignoran.
    if "resultados" not in datos or "clase" not in datos:
        return []
    base = ruta_json[:-len(".json")]
    # Los originales son de clase `clase`; el contrafactual tiene que ser la otra.
    esperada = 1 - datos["clase"]

    dir_json = os.path.dirname(ruta_json)

    # 1) TODA la poblacion inicial: un contrafactual por cada grafo original del
    #    grupo (tam_grupo = 2, 5, 8 u 11), no solo el mejor de ellos.
    rutas = [("inicial", f"inicial_{i}", f"{base}_inicial_{i}.graphml")
             for i in range(1, datos["tam_grupo"] + 1)]
    if not any(os.path.exists(r) for _, _, r in rutas):
        # Ejecuciones antiguas en las que solo se guardo el mejor individuo inicial.
        rutas = [("inicial", "inicial", f"{base}_mejor_inicial.graphml")]

    # 2) De cada combinacion del barrido, los 5 mejores individuos que guarda el
    #    genetico, no solo el primero: la solucion que se reporta es la mejor,
    #    pero las otras cuatro son igual de utilizables como contrafactual.
    for r in datos["resultados"]:
        # El nombre lleva el operador de cruce ademas de la poblacion, porque el
        # barrido puede probar varios; el JSON lo guarda ya construido.
        nombre = r.get("Prefijo") or f"{os.path.basename(base)}_pob{r['Poblacion_maxima']}"
        etiqueta = nombre[len(os.path.basename(base)) + 1:]
        # Los ficheros de cada combinacion estan en la subcarpeta de su operador
        # de cruce; si no aparecen ahi se prueba junto al JSON, que es como
        # quedaban las ejecuciones anteriores al reparto en subcarpetas.
        dir_cruce = os.path.join(dir_json, r.get("Cruce", ""))
        if not os.path.isdir(dir_cruce):
            dir_cruce = dir_json
        mejores = sorted(
            glob.glob(os.path.join(dir_cruce, f"{nombre}_mejores_*.graphml")),
            key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]))
        if mejores:
            for ruta in mejores:
                k = ruta.rsplit("_", 1)[1].split(".")[0]
                rutas.append(("final", f"{etiqueta}_mejor{k}", ruta))
        else:
            # Ejecuciones antiguas sin los 5 mejores: al menos la solucion final.
            rutas.append(("final", etiqueta,
                          os.path.join(dir_cruce, f"{nombre}_comparacion_final.graphml")))

    filas = []
    for tipo, etiqueta, ruta in rutas:
        if not os.path.exists(ruta):
            continue
        A = matriz(nx.read_graphml(ruta))
        clase = Importargrafos.oracle(A, clf)
        conexo = nx.is_connected(nx.from_numpy_array(A))
        filas.append({
            "grupo": f"{datos['fuente']}/N{datos['tam_grupo']}/clase{datos['clase']}",
            "tipo": tipo,
            "solucion": etiqueta,
            "clase": clase,
            "esperada": esperada,
            "conexo": conexo,
            "valido": clase == esperada and conexo,
        })
    return filas


def main():
    _, clf = Importargrafos.importgrafos()

    filas = []
    # Los resultados estan repartidos en experimentos/<fuente>/N<tam>/, con una
    # subcarpeta por operador de cruce, asi que se busca en todo el arbol.
    patron = os.path.join("experimentos", "**", "*.json")
    for ruta in sorted(glob.glob(patron, recursive=True)):
        filas.extend(revisar(ruta, clf))

    # Las etiquetas ya no son de longitud fija (llevan el cruce, la poblacion y
    # cual de los 5 mejores es), asi que la columna se ajusta a lo que haya.
    ancho = max([len(f["solucion"]) for f in filas] + [len("solucion")])
    L = []
    cab = (f"{'grupo':24s} {'solucion':>{ancho}s} {'clase':>6s} {'esperada':>9s} "
           f"{'conexo':>7s}  veredicto")
    L.append(cab)
    L.append("-" * (len(cab) + 10))
    for f in filas:
        motivos = []
        if f["clase"] != f["esperada"]:
            motivos.append("clase incorrecta")
        if not f["conexo"]:
            motivos.append("inconexo")
        L.append(f"{f['grupo']:24s} {f['solucion']:>{ancho}s} {f['clase']:>6d} {f['esperada']:>9d} "
                 f"{str(f['conexo']):>7s}  {'OK' if f['valido'] else 'INVALIDO: ' + ', '.join(motivos)}")

    invalidas = [f for f in filas if not f["valido"]]
    iniciales = [f for f in filas if f["tipo"] == "inicial"]
    finales = [f for f in filas if f["tipo"] == "final"]
    mala_clase = [f for f in finales if f["clase"] != f["esperada"]]
    L.append("")
    L.append(f"{len(invalidas)} de {len(filas)} soluciones invalidas "
             f"({len(iniciales)} iniciales + {len(finales)} finales comprobadas)")
    L.append(f"  iniciales invalidas: {len([f for f in iniciales if not f['valido']])} "
             f"de {len(iniciales)}")
    L.append(f"  finales invalidas:   {len([f for f in finales if not f['valido']])} "
             f"de {len(finales)}")
    L.append(f"de ellas, {len(mala_clase)} de {len(finales)} soluciones FINALES tienen "
             f"la misma clase que los grafos de entrada: no son contrafactuales")
    if mala_clase:
        L.append("")
        L.append("Causa: en Algoritmo.py la clase objetivo se deduce de la poblacion")
        L.append("inicial, que YA es contrafactual, en vez de deducirla de los originales:")
        L.append("    objetivo = 1 - clasificar(poblacionActual[0].grafo, clf)")
        L.append("Como poblacionActual[0] ya clasifica como 1-c, objetivo sale c, que es")
        L.append("la clase de los grafos de entrada. El genetico busca lo contrario de lo")
        L.append("que deberia.")

    texto = "\n".join(L)
    print(texto)
    with open("comprobar_validez.txt", "w", encoding="utf-8") as f:
        f.write(texto + "\n")


if __name__ == "__main__":
    main()
