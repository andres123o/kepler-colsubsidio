"""
Función canónica única para evaluar UNA persona de punta a punta:
encoder -> pi_i real (StepMix) -> blend de las 5 tablas theta_k -> scorer con
elegibilidad determinística. Reemplaza la lógica que estaba duplicada (con
variaciones) en 11_prueba_persona_sintetica.py, 13_prueba_persona_sintetica_2.py
y 14_prueba_lote_personas.py -- de aquí en adelante, cualquier prueba o la
futura capa agéntica debe importar `evaluar_persona` de este módulo, no
reimplementar el cálculo.

Fix incluido (encontrado en la prueba de lote del 23-jul-2026): la
elegibilidad de libranza es DETERMINÍSTICA sobre el dato real y conocido de
la persona (PIRAMIDE_NUEVA), nunca una probabilidad blendeada por pi_i entre
clases -- un dato ya observado no debe promediarse.
"""

import numpy as np
import pandas as pd
from stepmix.utils import max_one_hot

import importlib.util
_spec = importlib.util.spec_from_file_location("scorer10", "pipeline/10_scorer_productos_por_clase.py")
_scorer10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scorer10)

RUTA_MODELO = "data/processed/lca_modelo.pkl"
RUTA_PERFIL = "data/theta_k/clases_perfil_demografico.csv"
RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_MACRO = "data/theta_k/theta_k_sensibilidad_macro.csv"
RUTA_CALENDARIO = "data/theta_k/theta_k_demanda_calendario.csv"
RUTA_CANAL = "data/theta_k/theta_k_canal.csv"
RUTA_ESTILO = "data/theta_k/theta_k_estilo_comunicacion.csv"


def _cargar_todo():
    modelo_data = pd.read_pickle(RUTA_MODELO)
    return {
        "modelo": modelo_data["modelo"], "encoder": modelo_data["encoder"],
        "columnas": modelo_data["columnas"], "k": modelo_data["k"],
        "perfil": pd.read_csv(RUTA_PERFIL, encoding="utf-8-sig"),
        "interes": pd.read_csv(RUTA_INTERES, encoding="utf-8-sig"),
        "macro": pd.read_csv(RUTA_MACRO, encoding="utf-8-sig"),
        "calendario": pd.read_csv(RUTA_CALENDARIO, encoding="utf-8-sig"),
        "canal": pd.read_csv(RUTA_CANAL, encoding="utf-8-sig"),
        "estilo": pd.read_csv(RUTA_ESTILO, encoding="utf-8-sig"),
    }


_CACHE = None


def evaluar_persona(persona: dict, contexto=None):
    """persona: dict con las 10 columnas de COLUMNAS_LCA (GENERO, RANGO_EDAD, ...).
    Devuelve dict con pi_i, productos top (con score blendeado), sub-producto,
    canal, estilo de comunicación y elegibilidad de libranza -- todo con el
    fix determinístico aplicado."""
    global _CACHE
    if _CACHE is None:
        _CACHE = _cargar_todo()
    d = _CACHE
    modelo, encoder, columnas, k = d["modelo"], d["encoder"], d["columnas"], d["k"]
    perfil, interes, macro, calendario, canal, estilo = d["perfil"], d["interes"], d["macro"], d["calendario"], d["canal"], d["estilo"]

    # Elegibilidad de libranza: DETERMINÍSTICA sobre el dato real, no blendeada.
    elegible_libranza = persona["PIRAMIDE_NUEVA"] not in _scorer10.PIRAMIDE_NO_LIBRANZA

    fila = pd.DataFrame([[persona[c] for c in columnas]], columns=columnas)
    X_int = encoder.transform(fila.astype(str))
    mm = modelo.measurement_params
    X_onehot, _, _ = max_one_hot(X_int.astype(float), max_n_outcomes=mm["max_n_outcomes"], total_outcomes=mm["total_outcomes"])
    pi = modelo.predict_proba(X_onehot.astype(np.float32))[0]

    edad = perfil[perfil["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    puntajes_por_clase, sub_libre_por_clase, sub_educ_por_clase = {}, {}, {}
    for clase in range(k):
        puntos = {}
        fila_int = interes[interes["clase"] == clase].iloc[0]
        sub_libre = None
        for col, pts in [("interes_1", 3), ("interes_2", 2), ("interes_3", 1)]:
            texto = str(fila_int.get(col, "") or "")
            if not texto or texto.lower().startswith(("sin", "genérico")):
                continue
            producto = _scorer10.producto_de_interes(texto)
            if producto is None or (producto == "Libre_inversion" and not elegible_libranza):
                continue
            puntos[producto] = puntos.get(producto, 0) + pts
            if producto == "Libre_inversion" and sub_libre is None:
                for clave, sub in _scorer10.SUBPRODUCTO_LIBRE_INVERSION.items():
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
        if fila_cal["relevancia_viajes_timing"] == "alta" and elegible_libranza:
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
    top = [(p, round(s, 2)) for p, s in ranking if s > 0.05][:3]

    sub_producto = {}
    for p, _ in top:
        if p == "Educativo":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if "Educativo" in puntajes_por_clase[c] else 0))
            sub_producto["Educativo"] = sub_educ_por_clase[c_dom]
        if p == "Libre_inversion":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if sub_libre_por_clase[c] else 0))
            sub_producto["Libre_inversion"] = sub_libre_por_clase[c_dom]

    contribuyentes = [int(c) for c in np.argsort(-pi) if pi[c] > 0.01]

    def blend_num(df, col):
        return sum(pi[c] * df[df["clase"] == c][col].values[0] for c in range(k) if len(df[df["clase"] == c]))

    return {
        "pi": {c: round(float(pi[c]), 4) for c in contribuyentes},
        "elegible_libranza": elegible_libranza,
        "productos_top": top,
        "sub_producto": sub_producto,
        "tasa_deshabilitar_push_pct": round(blend_num(canal, "tasa_deshabilitar_push_estimada"), 1),
        "sensibilidad_inflacion": round(blend_num(macro, "sensibilidad_inflacion_index"), 3),
        "pct_con_hijos_probable": round(blend_num(calendario, "pct_con_hijos_probable"), 1),
        "rubro_dominante": estilo[estilo.clase == contribuyentes[0]]["rubro_contenido_dominante"].values[0],
        "tono_dominante": estilo[estilo.clase == contribuyentes[0]]["tono_comunicacion"].values[0],
        "formato_dominante": estilo[estilo.clase == contribuyentes[0]]["formato_estilo_dominante"].values[0],
    }


if __name__ == "__main__":
    # Prueba rápida de humo -- una persona conocida (Persona 6 del lote, la que
    # expuso el bug) para confirmar que el módulo consolidado da el resultado ya corregido.
    persona_prueba = {
        "GENERO": "M", "RANGO_EDAD": "20 a 35 años", "CATEGORIA": "A",
        "SEGMENTO_GRUPO_FAMILIAR": "AFILLIADO SIN GRUPO_FAMILIAR", "SEGMENTO_POBLACIONAL": "Joven",
        "PIRAMIDE_NUEVA": "6.2 Independiente", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Sin dato",
        "DROGUERIA": "NO", "PISCILAGO": "NO",
    }
    import json
    print(json.dumps(evaluar_persona(persona_prueba), indent=2, ensure_ascii=False))
