"""
Prueba 2 de 2: POR LOTE/SEGMENTO -- una muestra más grande (500 filas reales),
procesada de forma EFICIENTE (un solo predict_proba sobre toda la matriz, no
persona por persona) para responder la pregunta de "modo Kepler": si tengo
muchos afiliados, ¿cómo agrupo la comunicación por microsegmento/segmento en
vez de mandar 500 mensajes distintos? Es el mismo motor, usado en modo lote.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
from stepmix.utils import max_one_hot

COLUMNAS_LCA = [
    "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA", "EMPRESA_FOCO", "CIUDAD_GRUPO",
    "DROGUERIA", "PISCILAGO",
]
N = 500
SEMILLA = 7


def main():
    modelo_data = pd.read_pickle("data/processed/lca_modelo.pkl")
    modelo, encoder, k = modelo_data["modelo"], modelo_data["encoder"], modelo_data["k"]

    df = pd.read_pickle("data/processed/data_limpia.pkl")
    muestra = df.sample(n=N, random_state=SEMILLA).reset_index(drop=True)

    import time
    t0 = time.perf_counter()
    X_int = encoder.transform(muestra[COLUMNAS_LCA].astype(str))
    mm = modelo.measurement_params
    X_onehot, _, _ = max_one_hot(X_int.astype(float), max_n_outcomes=mm["max_n_outcomes"], total_outcomes=mm["total_outcomes"])
    pi = modelo.predict_proba(X_onehot.astype(np.float32))
    dt = time.perf_counter() - t0

    print(f"Tiempo para procesar {N} personas EN LOTE (un solo predict_proba): {dt:.2f}s ({dt/N*1000:.1f}ms/persona)\n")

    clase_dominante = pi.argmax(axis=1)
    canal = pd.read_csv("data/theta_k/theta_k_canal.csv", encoding="utf-8-sig")
    estilo = pd.read_csv("data/theta_k/theta_k_estilo_comunicacion.csv", encoding="utf-8-sig")
    macro = pd.read_csv("data/theta_k/theta_k_sensibilidad_macro.csv", encoding="utf-8-sig")

    resumen = pd.Series(clase_dominante).value_counts(normalize=True).sort_index() * 100

    print("--- Distribución del lote de 500 por clase dominante (microsegmento) ---")
    filas = []
    for clase in range(k):
        pct_lote = resumen.get(clase, 0.0)
        fila_c = canal[canal.clase == clase].iloc[0]
        fila_e = estilo[estilo.clase == clase].iloc[0]
        fila_m = macro[macro.clase == clase].iloc[0]
        filas.append({
            "clase": clase,
            "pct_del_lote": round(pct_lote, 1),
            "n_personas": int(round(pct_lote / 100 * N)),
            "rubro": fila_e["rubro_contenido_dominante"],
            "tono": fila_e["tono_comunicacion"].split(" -- ")[0],
            "canal": fila_c["canal_recomendado"].split(",")[0],
            "sensib_inflacion": fila_m["sensibilidad_inflacion_index"],
        })
    tabla = pd.DataFrame(filas).sort_values("pct_del_lote", ascending=False)
    print(tabla.to_string(index=False))

    print(
        f"\nLectura modo Kepler/lote: en vez de {N} mensajes distintos, esto se resume en "
        f"hasta {k} campañas por microsegmento -- una por clase presente en el lote, cada una "
        "con su propio rubro/tono/canal ya calculado, lista para que la capa agéntica redacte "
        "UN mensaje por microsegmento (no uno por persona) cuando el caso de uso sea "
        "comunicación masiva en vez de una consulta individual."
    )

    n_clases_presentes = (resumen > 0).sum()
    print(f"\n{n_clases_presentes} de {k} clases aparecen en esta muestra de {N} -- microsegmentación real, no un solo balde genérico.")


if __name__ == "__main__":
    main()
