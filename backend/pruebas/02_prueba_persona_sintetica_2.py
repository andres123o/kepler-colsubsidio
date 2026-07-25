"""
Segunda prueba de punta a punta con una persona nueva distinta -- mismo
mecanismo real (LCA entrenado -> pi_i real -> blend theta_i = suma pi_ik*theta_k),
esta vez incluyendo también la capa nueva de estilo de comunicación
(theta_k_estilo_comunicacion.csv), que no existía en la primera prueba.
"""

import numpy as np
import pandas as pd
from stepmix.utils import max_one_hot

import importlib.util
spec = importlib.util.spec_from_file_location("scorer10", "pipeline/10_scorer_productos_por_clase.py")
scorer10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer10)

PERSONA_NUEVA = {
    "GENERO": "M",
    "RANGO_EDAD": "20 a 35 años",
    "CATEGORIA": "A",
    "SEGMENTO_GRUPO_FAMILIAR": "AFILLIADO SIN GRUPO_FAMILIAR",
    "SEGMENTO_POBLACIONAL": "Joven",
    "PIRAMIDE_NUEVA": "1 Grandes",
    "EMPRESA_FOCO": "SI",
    "CIUDAD_GRUPO": "Bogotá D.C.",
    "DROGUERIA": "NO",
    "PISCILAGO": "SI",
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
    print("\n--- pi_i real (mezcla suave) ---")
    contribuyentes = [c for c in np.argsort(-pi) if pi[c] > 0.01]
    for c in contribuyentes:
        print(f"  Clase {c}: {pi[c]*100:.1f}%")

    perfil = pd.read_csv("data/theta_k/clases_perfil_demografico.csv", encoding="utf-8-sig")
    interes = pd.read_csv("data/theta_k/theta_k_vector_interes.csv", encoding="utf-8-sig")
    macro = pd.read_csv("data/theta_k/theta_k_sensibilidad_macro.csv", encoding="utf-8-sig")
    calendario = pd.read_csv("data/theta_k/theta_k_demanda_calendario.csv", encoding="utf-8-sig")
    canal = pd.read_csv("data/theta_k/theta_k_canal.csv", encoding="utf-8-sig")
    digital = pd.read_csv("data/theta_k/theta_k_interes_digital_bruto.csv", encoding="utf-8-sig")
    estilo = pd.read_csv("data/theta_k/theta_k_estilo_comunicacion.csv", encoding="utf-8-sig")

    piramide = perfil[perfil["variable"] == "PIRAMIDE_NUEVA"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    pct_no_libranza = piramide[[c for c in scorer10.PIRAMIDE_NO_LIBRANZA if c in piramide.columns]].sum(axis=1)
    edad = perfil[perfil["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    # --- Blend numérico directo ---
    def blend_num(df, col):
        return sum(pi[c] * df[df["clase"] == c][col].values[0] for c in range(k) if len(df[df["clase"] == c]))

    tasa_push_blend = blend_num(canal, "tasa_deshabilitar_push_estimada")
    reach_blend = blend_num(digital, "reach_digital_index")
    sensib_inflacion_blend = blend_num(macro, "sensibilidad_inflacion_index")
    pct_hijos_blend = blend_num(calendario, "pct_con_hijos_probable")
    prob_libranza = sum(pi[c] for c in range(k) if pct_no_libranza.get(c, 100) < 50)

    print(f"\n--- Canal (blend) ---")
    print(f"  Tasa deshabilitar push blendeada: {tasa_push_blend:.1f}%")
    for c in contribuyentes:
        print(f"  [{pi[c]*100:.0f}% clase {c}] {canal[canal.clase==c]['canal_recomendado'].values[0]}")

    print(f"\n--- Estilo de comunicación (blend textual ponderado) ---")
    for c in contribuyentes:
        fila_e = estilo[estilo.clase == c].iloc[0]
        print(f"  [{pi[c]*100:.0f}% clase {c}] Rubro: {fila_e['rubro_contenido_dominante']} | Tono: {fila_e['tono_comunicacion']} | Formato: {fila_e['formato_estilo_dominante']}")

    print(f"\n--- Macro (blend) ---")
    print(f"  Sensibilidad inflación blendeada: {sensib_inflacion_blend:.3f}")
    for c in contribuyentes:
        print(f"  [{pi[c]*100:.0f}% clase {c}] Compra cartera: {macro[macro.clase==c]['atractivo_compra_cartera'].values[0]}")

    print(f"\n--- Calendario (blend) ---")
    print(f"  % con hijos probable blendeado: {pct_hijos_blend:.1f}%")
    for c in contribuyentes:
        fila_c = calendario[calendario.clase == c].iloc[0]
        print(f"  [{pi[c]*100:.0f}% clase {c}] Educativo timing: {fila_c['relevancia_educativo_timing']} | Viajes timing: {fila_c['relevancia_viajes_timing']} | Ventana prima: {fila_c['accion_ventana_prima']}")

    print(f"\n--- Probabilidad elegibilidad libranza: {prob_libranza*100:.1f}% ---")

    # --- Score blendeado (igual método que la prueba 1) ---
    puntajes_por_clase = {}
    elegible_por_clase = {}
    sub_educ_por_clase, sub_libre_por_clase = {}, {}
    for clase in range(k):
        elegible = pct_no_libranza.get(clase, 100) < 50
        elegible_por_clase[clase] = elegible
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

    todos_productos = sorted({p for scores in puntajes_por_clase.values() for p in scores})
    blend = {p: sum(pi[c] * puntajes_por_clase[c].get(p, 0) for c in range(k)) for p in todos_productos}
    ranking = sorted(blend.items(), key=lambda kv: kv[1], reverse=True)

    print("\n--- Score blendeado por producto ---")
    for p, s in ranking:
        if s > 0.05:
            print(f"  {p}: {s:.2f}")

    top = [p for p, s in ranking if s > 0.05][:3]
    print(f"\n--- Resultado final: {' > '.join(top) if top else '(sin señal suficiente)'} ---")
    for p in top:
        if p == "Educativo":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if "Educativo" in puntajes_por_clase[c] else 0))
            print(f"  Sub-producto Educativo: {sub_educ_por_clase[c_dom]}")
        if p == "Libre_inversion":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if sub_libre_por_clase[c] else 0))
            print(f"  Sub-producto Libre Inversión: {sub_libre_por_clase[c_dom]}")


if __name__ == "__main__":
    main()
