"""
Paso 2 de Frente A: MCA sobre las columnas categóricas limpias.

Qué hace:
1. Carga data/processed/data_limpia.pkl (salida de 01_limpieza.py).
2. Selecciona las 10 columnas que sí cargan señal (ver diagnóstico empírico en
   cnoslidado-estrategia.md §2) -- deja fuera HOTELES/AGENCIAS/VIVIENDA (casi sin
   varianza, van como reglas de excepción más adelante, no como eje de MCA).
3. Corre MCA con 5 dimensiones.
4. Reporta cuánto explica cada dimensión (inercia) y qué categorías definen cada
   una, para poder decir en el pitch "la dimensión 1 significa esto" con evidencia,
   no con intuición.
5. Guarda las coordenadas de cada persona en data/processed/mca_coordenadas.pkl.
"""

import pandas as pd
import prince

RUTA_ENTRADA = "data/processed/data_limpia.pkl"
RUTA_SALIDA_COORDENADAS = "data/processed/mca_coordenadas.pkl"
RUTA_SALIDA_MODELO = "data/processed/mca_modelo.pkl"

COLUMNAS_MCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]

N_COMPONENTES = 5


def main():
    print(f"Cargando {RUTA_ENTRADA} ...")
    df = pd.read_pickle(RUTA_ENTRADA)
    X = df[COLUMNAS_MCA].astype("category")
    print(f"Filas: {len(X):,} | Columnas usadas: {COLUMNAS_MCA}")

    print(f"\nCorriendo MCA con {N_COMPONENTES} dimensiones ...")
    mca = prince.MCA(n_components=N_COMPONENTES, random_state=42)
    mca = mca.fit(X)

    print("\n--- % de inercia explicada por dimensión (como el %varianza de un PCA) ---")
    print(mca.percentage_of_variance_)
    print(f"Acumulado con {N_COMPONENTES} dimensiones: {mca.cumulative_percentage_of_variance_[-1]:.1f}%")

    coords_filas = mca.row_coordinates(X)
    coords_filas.columns = [f"dim_{i}" for i in range(N_COMPONENTES)]

    print("\n--- Qué categoría empuja más cada dimensión (coordenadas de columna) ---")
    coords_columnas = mca.column_coordinates(X)
    for dim in range(N_COMPONENTES):
        col = coords_columnas.iloc[:, dim].sort_values()
        print(f"\nDimensión {dim} -- extremo negativo:")
        print(col.head(4))
        print(f"Dimensión {dim} -- extremo positivo:")
        print(col.tail(4))

    coords_filas.to_pickle(RUTA_SALIDA_COORDENADAS)
    pd.to_pickle(mca, RUTA_SALIDA_MODELO)
    print(f"\nGuardado: {RUTA_SALIDA_COORDENADAS} y {RUTA_SALIDA_MODELO}")


if __name__ == "__main__":
    main()
