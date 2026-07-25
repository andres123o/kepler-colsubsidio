"""
Paso 3b de Frente A: ajuste final de LCA con K=12 fijo, sobre las 1.56M filas
completas (no la muestra de 200k). K=12 se decidió en 03a_buscar_k_extendido.py:
es el candidato más alto que convergió limpio (no tocó el tope de iteraciones),
con entropía sólida (0.939) -- K>=14 no convergió con n_init=1, así que no eran
comparables/confiables, y el rubric del hackathon pesa explicabilidad (85%)
más que exprimir el último punto de BIC.

Reusa exactamente la misma config que 03_lca.py (one-hot precalculado una sola
vez, abs_tol=1e-6, max_iter=300, n_init=2 con init_params='kmeans') pero sin
repetir la búsqueda de K -- eso ya se hizo y decidió.
"""

import time

import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
from stepmix.stepmix import StepMix
from stepmix.utils import max_one_hot

RUTA_ENTRADA = "data/processed/data_limpia.pkl"
RUTA_SALIDA_PI = "data/processed/lca_pi.pkl"
RUTA_SALIDA_MODELO = "data/processed/lca_modelo.pkl"

COLUMNAS_LCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]

K_FINAL = 12
RANDOM_STATE = 42
ABS_TOL = 1e-6
MAX_ITER = 300


def codificar_entero(df, columnas):
    enc = OrdinalEncoder(dtype=int)
    X = enc.fit_transform(df[columnas].astype(str))
    return X, enc


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

    print(f"\nAjustando el modelo final (K={K_FINAL}) sobre toda la población ({len(X_onehot):,} filas) ...", flush=True)
    t0 = time.perf_counter()
    modelo_final = StepMix(
        n_components=K_FINAL,
        measurement="categorical",
        measurement_params=mm_params,
        n_init=2,
        init_params="kmeans",
        abs_tol=ABS_TOL,
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
        progress_bar=1,
    )
    modelo_final.fit(X_onehot)
    dt = time.perf_counter() - t0
    print(
        f"Ajuste final: {dt:.1f}s ({dt/60:.1f} min), {modelo_final.n_iter_} iteraciones, "
        f"convergió={modelo_final.converged_}",
        flush=True,
    )

    pi = modelo_final.predict_proba(X_onehot)
    clase_dominante = pi.argmax(axis=1)

    print("\n--- Tamaño de cada clase (según clase dominante) ---", flush=True)
    print(pd.Series(clase_dominante).value_counts().sort_index(), flush=True)

    print("\n--- Perfil de cada clase (top-2 categorías por columna) ---", flush=True)
    df_perfil = df[COLUMNAS_LCA].copy()
    df_perfil["clase"] = clase_dominante
    for k in range(K_FINAL):
        n_clase = int((clase_dominante == k).sum())
        print(f"\n=== Clase {k} (n={n_clase:,}, {n_clase/len(df)*100:.1f}%) ===", flush=True)
        subset = df_perfil[df_perfil["clase"] == k]
        for col in COLUMNAS_LCA:
            top = subset[col].value_counts(normalize=True).head(2)
            print(f"  {col}: {dict(top.round(2))}", flush=True)

    resultado = pd.DataFrame(pi, columns=[f"clase_{k}" for k in range(K_FINAL)])
    resultado.insert(0, "SERIE", df["SERIE"].values)
    resultado.to_pickle(RUTA_SALIDA_PI)
    pd.to_pickle(
        {"modelo": modelo_final, "encoder": encoder, "columnas": COLUMNAS_LCA, "k": K_FINAL},
        RUTA_SALIDA_MODELO,
    )
    print(f"\nGuardado: {RUTA_SALIDA_PI} y {RUTA_SALIDA_MODELO}", flush=True)


if __name__ == "__main__":
    main()
