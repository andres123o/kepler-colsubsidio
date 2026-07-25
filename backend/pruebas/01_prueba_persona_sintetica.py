"""
Prueba de punta a punta: una persona NUEVA (inventada, no una fila del CSV),
corrida por el pipeline REAL -- LCA entrenado -> pi_i real (mezcla suave, no
clase dominante) -> blend theta_i = suma pi_ik*theta_k -> scorer.

Objetivo: hasta ahora todo se probó a nivel de las 12 clases (usando la clase
dominante de cada fila). Esto prueba el mecanismo que de verdad hace la
hiperpersonalización -- que una persona real casi nunca es 100% una sola
clase, es una MEZCLA, y el resultado debe reflejar esa mezcla, no colapsar a
"la clase más parecida".

Nota de honestidad sobre el blend: pi_ik*theta_k se puede promediar
directamente para columnas NUMÉRICAS (sensibilidad, reach, tasas) -- para
texto (interés, canal recomendado) no se puede promediar strings, así que
para el SCORER se recalcula el puntaje de cada producto por clase (no solo
el top-3 que se guardó antes) y se blendea ese número, que es lo que
realmente importa para el resultado final. Para sub-producto se toma el de
la clase con mayor peso en pi_i entre las que sí eligieron ese producto --
simplificación declarada, no una fórmula más fina.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
from stepmix.utils import max_one_hot

# Reimport de la lógica de mapeo del scorer (paso 10) para recalcular el
# puntaje COMPLETO por clase (todas las 7 líneas, no solo el top-3 guardado).
import importlib.util
spec = importlib.util.spec_from_file_location("scorer10", "pipeline/10_scorer_productos_por_clase.py")
scorer10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer10)

# --- 1. Afiliado sintético, inventado a propósito para que NO calce limpio
#     con una sola clase (mezcla mujer adulta clase media, con rasgos de
#     varias clases a la vez) ---
PERSONA_NUEVA = {
    "GENERO": "F",
    "RANGO_EDAD": "36 a 45 años",
    "CATEGORIA": "B",
    "SEGMENTO_GRUPO_FAMILIAR": "PAREJA CONYUGAL",
    "SEGMENTO_POBLACIONAL": "Medio",
    "PIRAMIDE_NUEVA": "2 Medianas",
    "EMPRESA_FOCO": "NO",
    "CIUDAD_GRUPO": "Bogotá D.C.",
    "DROGUERIA": "SI",
    "PISCILAGO": "NO",
}

RUTA_MODELO = "data/processed/lca_modelo.pkl"


def main():
    modelo_data = pd.read_pickle(RUTA_MODELO)
    modelo, encoder, columnas, k = modelo_data["modelo"], modelo_data["encoder"], modelo_data["columnas"], modelo_data["k"]

    fila = pd.DataFrame([[PERSONA_NUEVA[c] for c in columnas]], columns=columnas)
    print("Persona nueva (inventada):")
    print(fila.T.to_string())

    X_int = encoder.transform(fila.astype(str))
    mm = modelo.measurement_params
    X_onehot, _, _ = max_one_hot(X_int.astype(float), max_n_outcomes=mm["max_n_outcomes"], total_outcomes=mm["total_outcomes"])
    X_onehot = X_onehot.astype(np.float32)

    pi = modelo.predict_proba(X_onehot)[0]
    print("\n--- pi_i real (mezcla suave sobre las 12 clases) ---")
    for c in np.argsort(-pi):
        if pi[c] > 0.01:
            print(f"  Clase {c}: {pi[c]*100:.1f}%")

    # --- 2. Recalcular el puntaje COMPLETO por clase (las 7 líneas, no top-3) ---
    perfil = pd.read_csv("data/theta_k/clases_perfil_demografico.csv", encoding="utf-8-sig")
    interes = pd.read_csv("data/theta_k/theta_k_vector_interes.csv", encoding="utf-8-sig")
    macro = pd.read_csv("data/theta_k/theta_k_sensibilidad_macro.csv", encoding="utf-8-sig")
    calendario = pd.read_csv("data/theta_k/theta_k_demanda_calendario.csv", encoding="utf-8-sig")
    piramide = perfil[perfil["variable"] == "PIRAMIDE_NUEVA"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    pct_no_libranza = piramide[[c for c in scorer10.PIRAMIDE_NO_LIBRANZA if c in piramide.columns]].sum(axis=1)

    puntajes_por_clase = {}
    elegible_libranza_por_clase = {}
    sub_educ_por_clase = {}
    sub_libre_por_clase = {}
    edad = perfil[perfil["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    for clase in range(k):
        elegible = pct_no_libranza.get(clase, 100) < 50
        elegible_libranza_por_clase[clase] = elegible
        puntos = {}
        fila_int = interes[interes["clase"] == clase].iloc[0]
        sub_libre = None
        for col, pts in [("interes_1", 3), ("interes_2", 2), ("interes_3", 1)]:
            texto = str(fila_int.get(col, "") or "")
            if not texto or texto.lower().startswith(("sin", "genérico")):
                continue
            producto = scorer10.producto_de_interes(texto)
            if producto is None or (producto == "Libre_inversion" and not elegible):
                continue
            puntos[producto] = puntos.get(producto, 0) + pts
            if producto == "Libre_inversion" and sub_libre is None:
                for clave, sub in scorer10.SUBPRODUCTO_LIBRE_INVERSION.items():
                    if clave in texto.lower():
                        sub_libre = sub
        fila_macro = macro[macro["clase"] == clase].iloc[0]
        if "Rotativo" in str(fila_macro["implicacion_producto"]):
            puntos["Rotativo_cupo"] = puntos.get("Rotativo_cupo", 0) + 2
        if str(fila_macro["atractivo_compra_cartera"]).startswith("alto"):
            puntos["Compra_cartera"] = puntos.get("Compra_cartera", 0) + 2
        fila_cal = calendario[calendario["clase"] == clase].iloc[0]
        if fila_cal["relevancia_educativo_timing"] == "alta":
            puntos["Educativo"] = puntos.get("Educativo", 0) + 2
        if fila_cal["relevancia_viajes_timing"] == "alta" and elegible:
            puntos["Libre_inversion"] = puntos.get("Libre_inversion", 0) + 2
            if sub_libre is None:
                sub_libre = "Viajes"
        accion = str(fila_cal["accion_ventana_prima"]).lower()
        if "compra de cartera" in accion:
            puntos["Compra_cartera"] = puntos.get("Compra_cartera", 0) + 1
        if "rotativo" in accion:
            puntos["Rotativo_cupo"] = puntos.get("Rotativo_cupo", 0) + 1

        puntajes_por_clase[clase] = puntos
        sub_libre_por_clase[clase] = sub_libre
        pct_joven = edad.loc[clase].get("20 a 35 años", 0)
        pct_hijos = fila_cal["pct_con_hijos_probable"]
        sub_educ_por_clase[clase] = (
            "Técnico/Pregrado (propio)" if pct_joven > 50
            else "Apoyo educativo a hijos (colegio/pregrado)" if pct_hijos >= 50
            else "Posgrado/especialización (propio)"
        )

    # --- 3. Blend real: theta_i(producto) = suma pi_ik * score_k(producto) ---
    todos_productos = sorted({p for scores in puntajes_por_clase.values() for p in scores})
    blend = {p: sum(pi[c] * puntajes_por_clase[c].get(p, 0) for c in range(k)) for p in todos_productos}
    prob_libranza = sum(pi[c] for c in range(k) if elegible_libranza_por_clase[c])

    print(f"\n--- Probabilidad de elegibilidad de libranza (blend real, no binario de clase) ---")
    print(f"  {prob_libranza*100:.1f}% de su mezcla cae en clases con nómina/pensión")

    print("\n--- Score blendeado por producto (theta_i, no theta_k de una sola clase) ---")
    ranking = sorted(blend.items(), key=lambda kv: kv[1], reverse=True)
    for p, s in ranking:
        if s > 0.05:
            print(f"  {p}: {s:.2f}")

    top = [p for p, s in ranking if s > 0.05][:3]
    print(f"\n--- Resultado final: {' > '.join(top) if top else '(sin señal suficiente)'} ---")
    for p in top:
        if p == "Educativo":
            clase_dominante_para_p = max(range(k), key=lambda c: pi[c] * (1 if "Educativo" in puntajes_por_clase[c] else 0))
            print(f"  Sub-producto Educativo (heredado de la clase con más peso que lo eligió): {sub_educ_por_clase[clase_dominante_para_p]}")
        if p == "Libre_inversion":
            clase_dominante_para_p = max(range(k), key=lambda c: pi[c] * (1 if sub_libre_por_clase[c] else 0))
            print(f"  Sub-producto Libre Inversión: {sub_libre_por_clase[clase_dominante_para_p]}")


if __name__ == "__main__":
    main()
