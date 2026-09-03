# -*- coding: utf-8 -*-
"""
Comparación de los tres operadores de cruce.

Para cada fuente de grafos (cercanos / lejanos) se calcula UNA SOLA VEZ la
población inicial y se ejecuta el algoritmo genético con cada operador de cruce
partiendo de esa misma población, de modo que la única diferencia entre las
ejecuciones sea el operador.

Se instrumentan las funciones de FuncionesAlgoritmo mediante envoltorios, sin
modificar el código del algoritmo, para contabilizar:

  - descendientes evaluados y distribución de sus componentes conexas,
  - reparaciones de conectividad con éxito y descartes,
  - mutaciones aplicadas (una por hijo duplicado o de clase incorrecta),
  - inserciones efectivas en la población,
  - llamadas al clasificador (coste dominante del algoritmo).

Resultados en experimentos_cruces/: un JSON con todas las métricas y un log por
ejecución.
"""

import io
import json
import os
import pickle
import random
import sys
import time
from collections import Counter
from datetime import datetime

import networkx as nx
import numpy as np

import Algoritmo
import FuncionesAlgoritmo
import Importargrafos
import Visualizacion
from Algoritmo import algoritmo_genetico
from obs import obs
from ofs import ofs2

# =========================== CONFIGURACIÓN ===========================
FUENTES = ["cercanos", "lejanos"]
TAM_GRUPO = 11
# Clase del oráculo sobre la que se comparan los cruces. Por defecto la 0, que es
# para la que OFS2 encuentra contrafactuales; se puede pedir otra por línea de
# órdenes:  python experimentacion_cruces.py 1
CLASE = 0

# Tope de llamadas a ofs2 por grafo. ofs2 es heurístico y puede devolver None
# indefinidamente (con la clase 1 lo hace siempre), así que sin este tope el
# bucle de la población inicial no termina nunca.
MAX_INTENTOS_CONTRAFACTUAL = 50
POBLACION = 100
ITERACIONES = 2000
SEMILLA = 12345

CRUCES = [
    FuncionesAlgoritmo.cruce_un_punto,
    FuncionesAlgoritmo.cruce_dos_puntos,
    FuncionesAlgoritmo.cruce_uniforme,
]

DIR_SALIDA = "experimentos_cruces"
# =====================================================================


# --------------------------- instrumentación ---------------------------
class Contadores:
    def __init__(self):
        self.componentes = Counter()   # nº de componentes de cada hijo evaluado
        self.hijos = 0                 # descendientes que llegan a conectividad
        self.reparados = 0             # inconexos reparados con éxito
        self.fallo_reparacion = 0      # inconexos con 2 comp. no reparables
        self.descartados_3mas = 0      # inconexos con >=3 comp. (descarte directo)
        self.mutaciones = 0
        self.clasificaciones = 0
        self.inserciones = 0

    def como_dict(self, m):
        inconexos = self.hijos - self.componentes[1]
        return {
            "hijos_evaluados": self.hijos,
            "hijos_conexos": self.componentes[1],
            "hijos_inconexos": inconexos,
            "pct_inconexos": round(inconexos / self.hijos * 100, 2) if self.hijos else 0,
            "distribucion_componentes": {str(k): v for k, v in sorted(self.componentes.items())},
            "reparados": self.reparados,
            "fallo_reparacion_2comp": self.fallo_reparacion,
            "descartados_3mas_comp": self.descartados_3mas,
            "mutaciones": self.mutaciones,
            "clasificaciones": self.clasificaciones,
            "inserciones": max(self.inserciones - m, 0),   # descontada la población inicial
        }


def instrumentar(cnt):
    """Envuelve las funciones del módulo para contabilizar, devolviendo los
    originales para poder restaurarlos."""
    orig = {
        "conexo": FuncionesAlgoritmo.conexo,
        "mutar": FuncionesAlgoritmo.mutar,
        "clasificar": FuncionesAlgoritmo.clasificar,
        "Individuo": Algoritmo.Individuo,
    }

    def conexo(G, permutaciones, clf, objetivo, *a, **kw):
        ncomp = nx.number_connected_components(G)
        cnt.hijos += 1
        cnt.componentes[ncomp] += 1
        res = orig["conexo"](G, permutaciones, clf, objetivo, *a, **kw)
        if ncomp >= 3:
            cnt.descartados_3mas += 1
        elif ncomp == 2:
            if res:
                cnt.reparados += 1
            else:
                cnt.fallo_reparacion += 1
        return res

    def mutar(G, permutaciones):
        cnt.mutaciones += 1
        return orig["mutar"](G, permutaciones)

    def clasificar(G, clf):
        cnt.clasificaciones += 1
        return orig["clasificar"](G, clf)

    class IndividuoContado(orig["Individuo"]):
        def __init__(self, *a, **kw):
            cnt.inserciones += 1
            super().__init__(*a, **kw)

    FuncionesAlgoritmo.conexo = conexo
    FuncionesAlgoritmo.mutar = mutar
    FuncionesAlgoritmo.clasificar = clasificar
    Algoritmo.Individuo = IndividuoContado
    return orig


def restaurar(orig):
    FuncionesAlgoritmo.conexo = orig["conexo"]
    FuncionesAlgoritmo.mutar = orig["mutar"]
    FuncionesAlgoritmo.clasificar = orig["clasificar"]
    Algoritmo.Individuo = orig["Individuo"]


def silenciar_visualizacion():
    """El algoritmo guarda imágenes al terminar; aquí no interesan."""
    vis = Algoritmo.Visualizacion
    vis.guardar_comparacion_inicial_final = lambda *a, **kw: None
    vis.guardar_mejores_grafos = lambda *a, **kw: None


# --------------------------- población inicial ---------------------------
def poblacion_inicial(originales, clf, cache):
    """Calcula (o recupera de caché) los contrafactuales de partida.

    Devuelve None si algún grafo agota MAX_INTENTOS_CONTRAFACTUAL llamadas a
    ofs2 sin contrafactual, para que la fuente se omita en lugar de bloquearse.
    """
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            pob = pickle.load(f)
        print(f"  población inicial recuperada de {cache}", flush=True)
        return pob

    pob = []
    for i, grafo in enumerate(originales, 1):
        c = None
        for intento in range(1, MAX_INTENTOS_CONTRAFACTUAL + 1):
            c = ofs2(grafo, clf)
            if c is not None:
                break
            print(f"  grafo {i}: intento {intento}/{MAX_INTENTOS_CONTRAFACTUAL} "
                  f"sin contrafactual", flush=True)
        if c is None:
            print(f"  [AVISO] sin contrafactual para el grafo {i} tras "
                  f"{MAX_INTENTOS_CONTRAFACTUAL} intentos", flush=True)
            return None
        c = obs(grafo, c, clf, 5, 4000)
        pob.append(c)
        print(f"  contrafactual {i}/{len(originales)} calculado", flush=True)

    with open(cache, "wb") as f:
        pickle.dump(pob, f)
    return pob


def fitness_de(pob, originales):
    """Fitness de cada individuo de la población inicial."""
    ori = [nx.from_numpy_array(g) for g in originales]
    return [FuncionesAlgoritmo.fitness(nx.from_numpy_array(g), ori) for g in pob]


def cota_inferior(originales):
    """Mínimo teórico del fitness: voto mayoritario arista a arista."""
    A = np.array([np.asarray(g) for g in originales])
    iu = np.triu_indices(A.shape[1], k=1)
    X = A[:, iu[0], iu[1]].astype(int)
    m = len(originales)
    return float(np.minimum(X.sum(axis=0), m - X.sum(axis=0)).sum()) / m


# --------------------------------- main ---------------------------------
def main():
    os.makedirs(DIR_SALIDA, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    silenciar_visualizacion()

    print("Cargando dataset y clasificador...", flush=True)
    graphs, clf = Importargrafos.importgrafos()

    salida = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "configuracion": {
            "tam_grupo": TAM_GRUPO, "clase": CLASE, "poblacion": POBLACION,
            "iteraciones": ITERACIONES, "semilla": SEMILLA,
            "cruces": [c.__name__ for c in CRUCES], "fuentes": FUENTES,
        },
        "grupos": {},
    }

    for fuente in FUENTES:
        print(f"\n{'='*70}\nFUENTE {fuente} N{TAM_GRUPO} clase{CLASE}\n{'='*70}", flush=True)
        with open(os.path.join(f"grafos_{fuente}", f"N{TAM_GRUPO}",
                               f"clase{CLASE}.pkl"), "rb") as f:
            originales = pickle.load(f)

        cache = os.path.join(DIR_SALIDA,
                             f"poblacion_inicial_{fuente}_N{TAM_GRUPO}_clase{CLASE}.pkl")
        random.seed(SEMILLA)
        np.random.seed(SEMILLA)
        pob_ini = poblacion_inicial(originales, clf, cache)
        if pob_ini is None:
            print(f"  se omite la fuente {fuente} N{TAM_GRUPO} clase{CLASE}: "
                  f"OFS2 no da población inicial", flush=True)
            salida["grupos"][fuente] = {"omitido": "sin poblacion inicial (ofs2)"}
            continue

        f_ini = fitness_de(pob_ini, originales)
        cota = cota_inferior(originales)
        idx_mejor = min(range(len(f_ini)), key=lambda i: f_ini[i])
        print(f"  cota inferior del fitness: {cota:.1f}", flush=True)
        print(f"  fitness inicial: mejor {min(f_ini):.1f}, peor {max(f_ini):.1f}", flush=True)

        # Grafos de la población inicial, con la diferencia respecto a su
        # original en node-link y en matriz de adyacencia: es la línea base con
        # la que se compara lo que consiga cada operador de cruce.
        prefijo_inicial = os.path.join(DIR_SALIDA,
                                       f"{fuente}_N{TAM_GRUPO}_clase{CLASE}_{marca}_inicial")
        Visualizacion.guardar_contrafactuales(pob_ini, originales, prefijo=prefijo_inicial)
        # El mejor individuo inicial, además, en un archivo propio.
        ruta_mejor = f"{prefijo_inicial}_mejor.graphml"
        nx.write_graphml(nx.from_numpy_array(pob_ini[idx_mejor]), ruta_mejor)
        print(f"  mejor individuo inicial: índice {idx_mejor}, en {ruta_mejor}",
              flush=True)

        salida["grupos"][fuente] = {
            "cota_inferior": cota,
            "fitness_inicial": {"mejor": min(f_ini), "peor": max(f_ini),
                                "todos": f_ini},
            "mejor_inicial": {"indice": idx_mejor, "fitness": f_ini[idx_mejor]},
            "cruces": {},
        }

        for cruce in CRUCES:
            nombre = cruce.__name__
            print(f"\n  --- {nombre} ---", flush=True)

            # misma semilla y misma población inicial para todos los operadores
            random.seed(SEMILLA)
            np.random.seed(SEMILLA)

            cnt = Contadores()
            orig = instrumentar(cnt)
            log = os.path.join(DIR_SALIDA, f"{fuente}_N{TAM_GRUPO}_{nombre}_{marca}.log")
            stdout = sys.stdout
            t0 = time.time()
            try:
                with io.open(log, "w", encoding="utf-8") as fh:
                    sys.stdout = fh
                    _, score = algoritmo_genetico(
                        POBLACION, cruce, ITERACIONES,
                        originales, pob_ini, clf,
                    )
            finally:
                sys.stdout = stdout
                restaurar(orig)
            segundos = time.time() - t0

            metricas = cnt.como_dict(len(pob_ini))
            metricas.update({
                "score": score,
                "segundos": round(segundos, 1),
                "gap_vs_cota_pct": round((score - cota) / cota * 100, 2),
                "mejora_sobre_inicial": round(min(f_ini) - score, 1),
            })
            salida["grupos"][fuente]["cruces"][nombre] = metricas

            print(f"    score {score:.1f}  (gap {metricas['gap_vs_cota_pct']:.1f}%)  "
                  f"{segundos/60:.1f} min", flush=True)
            print(f"    hijos {metricas['hijos_evaluados']}, "
                  f"inconexos {metricas['pct_inconexos']}%, "
                  f"reparados {metricas['reparados']}, "
                  f"descartados>=3comp {metricas['descartados_3mas_comp']}", flush=True)
            print(f"    inserciones {metricas['inserciones']}, "
                  f"mutaciones {metricas['mutaciones']}, "
                  f"clasificaciones {metricas['clasificaciones']}", flush=True)

            ruta = os.path.join(DIR_SALIDA, f"comparacion_cruces_{marca}.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(salida, f, ensure_ascii=False, indent=2)

    # Vuelca el JSON también al final: si todas las fuentes se omiten no se ha
    # entrado nunca al bucle de cruces y ese volcado no se habría hecho.
    ruta = os.path.join(DIR_SALIDA, f"comparacion_cruces_{marca}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"\nResultados en {ruta}", flush=True)


if __name__ == "__main__":
    main()