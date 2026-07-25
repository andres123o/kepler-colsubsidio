"""
Paso 3 de Frente A: LCA real (StepMix) sobre las columnas categóricas crudas.

A diferencia de MCA (que fue un chequeo visual), esto SÍ produce el artefacto
que se usa después: pi_i, la mezcla de clases por persona.

Versión optimizada tras diagnosticar por qué la primera corrida tardó >1h sin
terminar (ver conversación) -- cambios, cada uno sin pérdida de calidad:

1. El one-hot se calcula UNA sola vez (con la misma función que usa la librería
   por dentro, stepmix.utils.max_one_hot) y se le pasa a StepMix ya listo con
   integer_codes=False. Antes, la librería lo recalculaba desde cero en cada
   E-step Y en cada M-step de cada iteración -- el mismo cálculo, repetido miles
   de veces sin necesidad.
2. abs_tol baja de 1e-10 (default) a 1e-6 -- 1e-10 persigue precisión por debajo
   del ruido estadístico normal de una muestra de 1.56M filas, no aporta nada.
3. max_iter baja de 1000 (default) a 300 -- como techo de seguridad, no como
   corte forzado; con el punto 2 debería converger mucho antes.
4. n_init baja: 1 en la búsqueda de K (se hace 8 veces, prioriza velocidad) y 2
   en el ajuste final (init_params='kmeans' ya parte de un punto informado por
   los datos reales, no al azar puro -- necesita menos reintentos que antes).
5. El array one-hot se guarda en float32 en vez de float64 -- mismo resultado
   práctico para probabilidades, la mitad de memoria/ancho de banda.

Qué hace, en orden:
1. Carga data/processed/data_limpia.pkl.
2. Codifica las 10 columnas como enteros y LUEGO como one-hot, una sola vez.
3. Prueba varios K sobre una muestra de 200k filas (subconjunto del one-hot ya
   calculado, no se recalcula) y compara BIC.
4. Ajusta el modelo final con el K elegido sobre TODA la población (1.56M).
5. Guarda pi_i (probabilidad de cada clase por persona) + el modelo.
6. Imprime el perfil de cada clase para poder explicarla en una frase.
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

N_MUESTRA_BUSQUEDA_K = 200_000
CANDIDATOS_K = [4, 5, 6, 7, 8, 9, 10, 12]
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
        dt = time.perf_counter() - t0
        resultados.append((k, bic))
        print(f"K={k:>2}  BIC={bic:,.1f}  ({dt:.1f}s, {modelo.n_iter_} iters)")

    mejor_k = min(resultados, key=lambda t: t[1])[0]
    return mejor_k, resultados


def main():
    print(f"Cargando {RUTA_ENTRADA} ...")
    df = pd.read_pickle(RUTA_ENTRADA)

    print(f"Codificando {len(COLUMNAS_LCA)} columnas como enteros ...")
    X_int, encoder = codificar_entero(df, COLUMNAS_LCA)

    print("Calculando one-hot UNA sola vez (antes se recalculaba en cada iteración) ...")
    X_onehot, max_n_outcomes, total_outcomes = max_one_hot(X_int.astype(float))
    X_onehot = X_onehot.astype(np.float32)
    mm_params = {
        "integer_codes": False,
        "max_n_outcomes": max_n_outcomes,
        "total_outcomes": total_outcomes,
    }
    print(f"one-hot: {X_onehot.shape}, {X_onehot.nbytes / 1e6:.0f} MB")

    print(f"\nBuscando K sobre una muestra de {N_MUESTRA_BUSQUEDA_K:,} filas ...")
    mejor_k, resultados = elegir_k(X_onehot, mm_params, CANDIDATOS_K, N_MUESTRA_BUSQUEDA_K, RANDOM_STATE)
    print(f"\nK elegido por BIC (menor es mejor): {mejor_k}")

    print(f"\nAjustando el modelo final (K={mejor_k}) sobre toda la población ({len(X_onehot):,} filas) ...")
    t0 = time.perf_counter()
    modelo_final = StepMix(
        n_components=mejor_k,
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
    print(f"Ajuste final: {time.perf_counter() - t0:.1f}s, {modelo_final.n_iter_} iteraciones, convergió={modelo_final.converged_}")

    pi = modelo_final.predict_proba(X_onehot)  # (n_personas, K) -- la mezcla suave
    clase_dominante = pi.argmax(axis=1)

    print("\n--- Tamaño de cada clase (según clase dominante) ---")
    print(pd.Series(clase_dominante).value_counts().sort_index())

    print("\n--- Perfil de cada clase (top-2 categorías por columna) ---")
    df_perfil = df[COLUMNAS_LCA].copy()
    df_perfil["clase"] = clase_dominante
    for k in range(mejor_k):
        n_clase = int((clase_dominante == k).sum())
        print(f"\n=== Clase {k} (n={n_clase:,}) ===")
        subset = df_perfil[df_perfil["clase"] == k]
        for col in COLUMNAS_LCA:
            top = subset[col].value_counts(normalize=True).head(2)
            print(f"  {col}: {dict(top.round(2))}")

    resultado = pd.DataFrame(pi, columns=[f"clase_{k}" for k in range(mejor_k)])
    resultado.insert(0, "SERIE", df["SERIE"].values)
    resultado.to_pickle(RUTA_SALIDA_PI)
    pd.to_pickle(
        {"modelo": modelo_final, "encoder": encoder, "columnas": COLUMNAS_LCA, "k": mejor_k},
        RUTA_SALIDA_MODELO,
    )
    print(f"\nGuardado: {RUTA_SALIDA_PI} y {RUTA_SALIDA_MODELO}")


if __name__ == "__main__":
    main()
