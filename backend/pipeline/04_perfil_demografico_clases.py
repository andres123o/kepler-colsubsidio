"""
Paso 1 de Frente B: extraer la composición demográfica completa (GENERO x
RANGO_EDAD x CIUDAD_GRUPO) de cada una de las 12 clases de LCA, en una tabla
limpia y reutilizable.

No es research ni modelo nuevo -- es organizar lo que el ajuste final de LCA
(03b_ajuste_final.py) ya calculó, pero con la distribución COMPLETA por
columna (no solo el top-2 que se imprimió en ese script), porque el cruce con
la matriz pública de canal (paso 2) necesita la masa de probabilidad completa,
no solo las dos categorías más grandes.

Salida: data/theta_k/clases_perfil_demografico.csv, formato largo
(clase, variable, categoria, pct) -- fácil de leer y de cruzar después.
"""

import pandas as pd

RUTA_DATA = "data/processed/data_limpia.pkl"
RUTA_PI = "data/processed/lca_pi.pkl"
RUTA_SALIDA = "data/theta_k/clases_perfil_demografico.csv"

VARIABLES_DEMOGRAFICAS = ["GENERO", "RANGO_EDAD", "CIUDAD_GRUPO", "SEGMENTO_GRUPO_FAMILIAR", "CATEGORIA", "PIRAMIDE_NUEVA"]


def main():
    print(f"Cargando {RUTA_DATA} y {RUTA_PI} ...")
    df = pd.read_pickle(RUTA_DATA)
    pi = pd.read_pickle(RUTA_PI)

    assert len(df) == len(pi), "data_limpia y lca_pi tienen distinto número de filas -- revisar"

    cols_clase = [c for c in pi.columns if c.startswith("clase_")]
    k = len(cols_clase)
    print(f"K={k} clases detectadas en {RUTA_PI}")

    clase_dominante = pi[cols_clase].values.argmax(axis=1)
    df = df.reset_index(drop=True).copy()
    df["clase"] = clase_dominante

    filas = []
    for var in VARIABLES_DEMOGRAFICAS:
        for clase in range(k):
            subset = df.loc[df["clase"] == clase, var]
            dist = subset.value_counts(normalize=True)
            for categoria, pct in dist.items():
                filas.append({
                    "clase": clase,
                    "variable": var,
                    "categoria": categoria,
                    "pct": round(pct * 100, 2),
                })

    resultado = pd.DataFrame(filas).sort_values(["variable", "clase", "pct"], ascending=[True, True, False])
    resultado.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Guardado: {RUTA_SALIDA} ({len(resultado)} filas)")

    print("\n--- Verificación: cada (clase, variable) debe sumar ~100% ---")
    check = resultado.groupby(["variable", "clase"])["pct"].sum()
    fuera_de_rango = check[(check < 99.5) | (check > 100.5)]
    if len(fuera_de_rango):
        print("ALERTA -- sumas fuera de 99.5-100.5%:")
        print(fuera_de_rango)
    else:
        print("OK -- todas las combinaciones (clase, variable) suman ~100%.")

    print("\n--- Vista previa: RANGO_EDAD por clase ---")
    edad = resultado[resultado["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    print(edad)

    print("\n--- Vista previa: GENERO por clase ---")
    genero = resultado[resultado["variable"] == "GENERO"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    print(genero)

    print("\n--- Vista previa: CIUDAD_GRUPO por clase ---")
    ciudad = resultado[resultado["variable"] == "CIUDAD_GRUPO"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    print(ciudad)


if __name__ == "__main__":
    main()
