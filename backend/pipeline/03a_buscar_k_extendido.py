"""
Extensión de la búsqueda de K de 03_lca.py: el BIC bajaba monótonamente
hasta K=12 (el candidato más alto probado ayer) sin doblarse hacia arriba,
así que no había evidencia de que 12 fuera el óptimo real -- solo el mejor
de los candidatos probados. Este script prueba K=14,16,18,20 (mismo one-hot,
misma muestra de 200k, misma configuración) para ver si el BIC por fin gira.

A N grande (200k, peor 1.56M) es normal y esperado que el BIC crudo no
converja a un mínimo claro -- la literatura (Nylund et al., CenterStat,
Weller et al. 2020) recomienda NO decidir K con un solo criterio en ese
régimen. Por eso, además del BIC, reportamos por cada K:
  - SABIC (BIC ajustado por tamaño de muestra, penaliza menos, suele mostrar
    un codo más claro que el BIC crudo) -- stepmix lo trae nativo (.sabic()).
  - Entropía relativa (stepmix .relative_entropy()) -- no es criterio de
    selección, es diagnóstico de qué tan bien separadas/clasificables quedan
    las clases (cerca de 1 = clases nítidas, cerca de 0 = solapadas).
  - Tamaño de la clase más chica (dominante) -- una clase con muy pocas
    personas no sirve para el scorer/negocio aunque baje el BIC.

Solo hace la búsqueda -- NO ajusta el modelo final sobre 1.56M filas. Eso se
decide después de ver esta curva, para no comprometer ~1-1.5h de cómputo a
un K elegido a ciegas.
"""

import time

import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
from stepmix.stepmix import StepMix
from stepmix.utils import max_one_hot

RUTA_ENTRADA = "data/processed/data_limpia.pkl"

COLUMNAS_LCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]

N_MUESTRA_BUSQUEDA_K = 200_000
CANDIDATOS_YA_PROBADOS = [4, 5, 6, 7, 8, 9, 10, 12]
CANDIDATOS_NUEVOS = [14, 16, 18, 20]
RANDOM_STATE = 42

ABS_TOL = 1e-6
MAX_ITER = 300


def codificar_entero(df, columnas):
    enc = OrdinalEncoder(dtype=int)
    X = enc.fit_transform(df[columnas].astype(str))
    return X, enc


def elegir_k(X_onehot, mm_params, candidatos, n_muestra, random_state):
    rng = np.random.RandomState(random_state)
    idx_muestra = rng.choice(len(X_onehot), size=min(n_muestra, len(X_onehot)), replace=False)
    X_muestra = X_onehot[idx_muestra]

    resultados = []
    for k in candidatos:
        t0 = time.perf_counter()
        modelo = StepMix(
            n_components=k,
            measurement="categorical",
            measurement_params=mm_params,
            n_init=1,
            init_params="kmeans",
            abs_tol=ABS_TOL,
            max_iter=MAX_ITER,
            random_state=random_state,
            progress_bar=0,
        )
        modelo.fit(X_muestra)
        bic = modelo.bic(X_muestra)
        sabic = modelo.sabic(X_muestra)
        entropia = modelo.relative_entropy(X_muestra)
        clase_dom = modelo.predict_proba(X_muestra).argmax(axis=1)
        tam_clases = np.bincount(clase_dom, minlength=k)
        clase_min_pct = tam_clases.min() / len(X_muestra) * 100
        dt = time.perf_counter() - t0
        resultados.append(
            {"k": k, "bic": bic, "sabic": sabic, "entropia": entropia,
             "clase_min_pct": clase_min_pct, "tam_clases": tam_clases.tolist()}
        )
        print(
            f"K={k:>2}  BIC={bic:,.1f}  SABIC={sabic:,.1f}  entropia={entropia:.3f}  "
            f"clase_min={clase_min_pct:.1f}%  ({dt:.1f}s, {modelo.n_iter_} iters)",
            flush=True,
        )

    return resultados


def main():
    print(f"Cargando {RUTA_ENTRADA} ...", flush=True)
    df = pd.read_pickle(RUTA_ENTRADA)

    print(f"Codificando {len(COLUMNAS_LCA)} columnas como enteros ...", flush=True)
    X_int, encoder = codificar_entero(df, COLUMNAS_LCA)

    print("Calculando one-hot UNA sola vez ...", flush=True)
    X_onehot, max_n_outcomes, total_outcomes = max_one_hot(X_int.astype(float))
    X_onehot = X_onehot.astype(np.float32)
    mm_params = {
        "integer_codes": False,
        "max_n_outcomes": max_n_outcomes,
        "total_outcomes": total_outcomes,
    }
    print(f"one-hot: {X_onehot.shape}, {X_onehot.nbytes / 1e6:.0f} MB", flush=True)

    print(f"\nRe-corriendo candidatos ya probados ayer (referencia, misma seed): {CANDIDATOS_YA_PROBADOS}", flush=True)
    ref = elegir_k(X_onehot, mm_params, CANDIDATOS_YA_PROBADOS, N_MUESTRA_BUSQUEDA_K, RANDOM_STATE)

    print(f"\nCandidatos nuevos: {CANDIDATOS_NUEVOS}", flush=True)
    nuevos = elegir_k(X_onehot, mm_params, CANDIDATOS_NUEVOS, N_MUESTRA_BUSQUEDA_K, RANDOM_STATE)

    todos = ref + nuevos
    print("\n--- Curva completa (K, BIC, SABIC, entropia, clase_min%) ---", flush=True)
    for r in todos:
        print(
            f"K={r['k']:>2}  BIC={r['bic']:,.1f}  SABIC={r['sabic']:,.1f}  "
            f"entropia={r['entropia']:.3f}  clase_min={r['clase_min_pct']:.1f}%",
            flush=True,
        )

    mejor_bic = min(todos, key=lambda r: r["bic"])["k"]
    mejor_sabic = min(todos, key=lambda r: r["sabic"])["k"]
    print(f"\nK con menor BIC: {mejor_bic}  |  K con menor SABIC: {mejor_sabic}", flush=True)
    print(
        "Decisión final de K: no tomar el mínimo automáticamente -- revisar si a partir de "
        "cierto K la entropía cae fuerte o alguna clase queda con clase_min% muy chico "
        "(clase poco útil para el scorer aunque el criterio siga bajando).",
        flush=True,
    )


if __name__ == "__main__":
    main()
