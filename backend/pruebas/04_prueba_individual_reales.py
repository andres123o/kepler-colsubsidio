"""
Prueba 1 de 2: INDIVIDUAL -- 50 filas REALES del CSV (no sintéticas),
corridas una por una por el pipeline completo (scorer_persona.evaluar_persona,
ya con el fix de libranza consolidado). Responde: "¿cómo se comporta el
modelo persona por persona con datos reales?" -- para el requerimiento
literal del reto (una cédula -> una respuesta).
"""

import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "motor")
from scorer_persona import evaluar_persona, _cargar_todo, RUTA_MODELO

COLUMNAS_LCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]

N = 50
SEMILLA = 7


def main():
    df = pd.read_pickle("data/processed/data_limpia.pkl")
    muestra = df.sample(n=N, random_state=SEMILLA).reset_index(drop=True)

    filas = []
    for i, row in muestra.iterrows():
        persona = {c: row[c] for c in COLUMNAS_LCA}
        r = evaluar_persona(persona)
        n_productos = len(r["productos_top"])
        clase_dom = max(r["pi"], key=r["pi"].get)
        blend_real = len(r["pi"]) > 1
        filas.append({
            "serie": row["SERIE"],
            "clase_dominante": clase_dom,
            "pct_clase_dominante": round(r["pi"][clase_dom] * 100, 1),
            "es_blend": blend_real,
            "n_productos": n_productos,
            "top1": r["productos_top"][0][0] if n_productos else "(SIN SEÑAL)",
            "elegible_libranza": r["elegible_libranza"],
            "rubro": r["rubro_dominante"],
        })

    resultado = pd.DataFrame(filas)
    resultado.to_csv("data/pruebas_resultado/prueba_individual_50_resultado.csv", index=False, encoding="utf-8-sig")

    print(f"=== Resumen de {N} personas reales ===\n")
    print(f"% que es mezcla real (más de 1 clase con peso >1%): {resultado['es_blend'].mean()*100:.0f}%")
    print(f"Promedio de % de la clase dominante (qué tan 'limpio' es el calce): {resultado['pct_clase_dominante'].mean():.1f}%")
    print(f"\nDistribución de número de productos por persona:")
    print(resultado["n_productos"].value_counts().sort_index())
    print(f"\n% elegibles para libranza: {resultado['elegible_libranza'].mean()*100:.0f}%")
    print(f"\nTop-1 producto, distribución:")
    print(resultado["top1"].value_counts())
    print(f"\nRubro dominante, distribución:")
    print(resultado["rubro"].value_counts())
    print(f"\nCasos sin señal suficiente (n_productos==0): {(resultado['n_productos']==0).sum()} de {N}")
    print("\n--- Primeras 10 filas de detalle ---")
    print(resultado.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
