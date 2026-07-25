"""
Prueba controlada de velocidad real en esta máquina: cuánto tarda UNA sola
iteración de EM de StepMix por tamaño de muestra, para poder extrapolar
cuánto tardaría la corrida completa en vez de adivinar.
"""

import time
import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
from stepmix.stepmix import StepMix

COLUMNAS_LCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]

print("Cargando data limpia ...")
df = pd.read_pickle("data/processed/data_limpia.pkl")
enc = OrdinalEncoder(dtype=int)
X_full = enc.fit_transform(df[COLUMNAS_LCA].astype(str))
print(f"Filas totales: {len(X_full):,}")

TAMANOS = [20_000, 100_000, 400_000, len(X_full)]
ITER_FIJAS = 10  # mismas iteraciones para todos los tamaños -> comparación limpia

rng = np.random.RandomState(0)
resultados = []
for n in TAMANOS:
    idx = rng.choice(len(X_full), size=min(n, len(X_full)), replace=False)
    X = X_full[idx]

    modelo = StepMix(
        n_components=8,
        measurement="categorical",
        n_init=1,
        init_params="kmeans",
        max_iter=ITER_FIJAS,
        abs_tol=0.0,  # sin margen -> corre practicamente las 10 iteraciones completas
        random_state=0,
        progress_bar=0,
    )
    t0 = time.perf_counter()
    modelo.fit(X)
    t1 = time.perf_counter()
    seg_totales = t1 - t0
    seg_por_iter = seg_totales / ITER_FIJAS
    print(f"n={n:>9,}  ->  {seg_totales:6.2f}s en {ITER_FIJAS} iters  =  {seg_por_iter:.3f}s/iter")
    resultados.append((n, seg_por_iter))

print("\n--- Extrapolación ---")
n_final, seg_iter_final = resultados[-1]
for iters_estimadas in [50, 100, 200, 300, 500]:
    total_un_init = seg_iter_final * iters_estimadas
    print(f"Con {iters_estimadas} iteraciones (1 init) sobre {n_final:,} filas: ~{total_un_init/60:.1f} min")
