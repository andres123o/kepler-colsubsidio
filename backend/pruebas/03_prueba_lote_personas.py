"""
Prueba de lote: 6 afiliados sintéticos distintos, deliberadamente elegidos
para cubrir huecos que las 2 pruebas anteriores no cubrieron -- Categoría C
(nunca probada), un perfil ambiguo/genérico, pensionado, independiente/
facultativo (repetir el gate de libranza con otra combinación), familia
numerosa joven, y joven independiente de bajo ingreso. Corre el pipeline
real completo (LCA entrenado -> pi_i -> blend de las 5 tablas -> scorer) por
cada uno y deja un resumen para revisar en conjunto si el modelo da
resultados sensatos, no solo en casos aislados.
"""

import numpy as np
import pandas as pd
from stepmix.utils import max_one_hot

import importlib.util
spec = importlib.util.spec_from_file_location("scorer10", "pipeline/10_scorer_productos_por_clase.py")
scorer10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer10)

PERSONAS = {
    "1_alto_ingreso_establecido": {
        "GENERO": "F", "RANGO_EDAD": "46 a 55 años", "CATEGORIA": "C",
        "SEGMENTO_GRUPO_FAMILIAR": "AFILLIADO SIN GRUPO_FAMILIAR", "SEGMENTO_POBLACIONAL": "Alto",
        "PIRAMIDE_NUEVA": "3 Empresarial Top", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Bogotá D.C.",
        "DROGUERIA": "NO", "PISCILAGO": "NO",
    },
    "2_ambiguo_generico": {
        "GENERO": "M", "RANGO_EDAD": "36 a 45 años", "CATEGORIA": "B",
        "SEGMENTO_GRUPO_FAMILIAR": "FAMILIA NUCLEAR AMPLIADA", "SEGMENTO_POBLACIONAL": "Medio",
        "PIRAMIDE_NUEVA": "5 Micro Transaccional", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Otro departamento",
        "DROGUERIA": "NO", "PISCILAGO": "NO",
    },
    "3_pensionado": {
        "GENERO": "F", "RANGO_EDAD": "Mayor de 55 años", "CATEGORIA": "A",
        "SEGMENTO_GRUPO_FAMILIAR": "PAREJA CONYUGAL", "SEGMENTO_POBLACIONAL": "Básico",
        "PIRAMIDE_NUEVA": "6.3 Pensionado", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Bogotá D.C.",
        "DROGUERIA": "NO", "PISCILAGO": "NO",
    },
    "4_independiente_facultativo": {
        "GENERO": "F", "RANGO_EDAD": "46 a 55 años", "CATEGORIA": "A",
        "SEGMENTO_GRUPO_FAMILIAR": "FAMILIA MONOPARENTAL", "SEGMENTO_POBLACIONAL": "Básico",
        "PIRAMIDE_NUEVA": "6.1 Facultativo", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Sin dato",
        "DROGUERIA": "SI", "PISCILAGO": "NO",
    },
    "5_familia_numerosa_joven": {
        "GENERO": "F", "RANGO_EDAD": "20 a 35 años", "CATEGORIA": "A",
        "SEGMENTO_GRUPO_FAMILIAR": "FAMILIA MONOPARENTAL AMPLIADA", "SEGMENTO_POBLACIONAL": "Básico",
        "PIRAMIDE_NUEVA": "5 Micro Transaccional", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Región metropolitana",
        "DROGUERIA": "SI", "PISCILAGO": "SI",
    },
    "6_joven_independiente_bajo_ingreso": {
        "GENERO": "M", "RANGO_EDAD": "20 a 35 años", "CATEGORIA": "A",
        "SEGMENTO_GRUPO_FAMILIAR": "AFILLIADO SIN GRUPO_FAMILIAR", "SEGMENTO_POBLACIONAL": "Joven",
        "PIRAMIDE_NUEVA": "6.2 Independiente", "EMPRESA_FOCO": "NO", "CIUDAD_GRUPO": "Sin dato",
        "DROGUERIA": "NO", "PISCILAGO": "NO",
    },
}


def cargar_tablas():
    return {
        "perfil": pd.read_csv("data/theta_k/clases_perfil_demografico.csv", encoding="utf-8-sig"),
        "interes": pd.read_csv("data/theta_k/theta_k_vector_interes.csv", encoding="utf-8-sig"),
        "macro": pd.read_csv("data/theta_k/theta_k_sensibilidad_macro.csv", encoding="utf-8-sig"),
        "calendario": pd.read_csv("data/theta_k/theta_k_demanda_calendario.csv", encoding="utf-8-sig"),
        "canal": pd.read_csv("data/theta_k/theta_k_canal.csv", encoding="utf-8-sig"),
        "estilo": pd.read_csv("data/theta_k/theta_k_estilo_comunicacion.csv", encoding="utf-8-sig"),
    }


def correr_persona(nombre, persona, modelo, encoder, columnas, k, tablas):
    # Elegibilidad de libranza: DETERMINÍSTICA sobre el dato real y conocido de la
    # persona (PIRAMIDE_NUEVA ya viene en su respuesta) -- NUNCA una probabilidad
    # blendeada por pi_i entre clases. Bug encontrado en la v1 de este script: usar
    # el blend "tapaba" el dato real de un Facultativo/Independiente si el resto de
    # sus respuestas jalaban hacia una clase mayoritariamente-con-nómina.
    elegible_libranza_real = persona["PIRAMIDE_NUEVA"] not in scorer10.PIRAMIDE_NO_LIBRANZA

    fila = pd.DataFrame([[persona[c] for c in columnas]], columns=columnas)
    X_int = encoder.transform(fila.astype(str))
    mm = modelo.measurement_params
    X_onehot, _, _ = max_one_hot(X_int.astype(float), max_n_outcomes=mm["max_n_outcomes"], total_outcomes=mm["total_outcomes"])
    pi = modelo.predict_proba(X_onehot.astype(np.float32))[0]

    perfil, interes, macro, calendario, canal, estilo = (tablas[k_] for k_ in ["perfil", "interes", "macro", "calendario", "canal", "estilo"])
    piramide = perfil[perfil["variable"] == "PIRAMIDE_NUEVA"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    pct_no_libranza = piramide[[c for c in scorer10.PIRAMIDE_NO_LIBRANZA if c in piramide.columns]].sum(axis=1)
    edad = perfil[perfil["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    puntajes_por_clase, sub_libre_por_clase, sub_educ_por_clase = {}, {}, {}
    for clase in range(k):
        elegible = elegible_libranza_real  # determinístico, igual para todas las clases de esta persona
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
            "Técnico/Pregrado" if pct_joven > 50 else "Apoyo a hijos" if pct_hijos >= 50 else "Posgrado propio"
        )

    todos_productos = sorted({p for scores in puntajes_por_clase.values() for p in scores})
    blend = {p: sum(pi[c] * puntajes_por_clase[c].get(p, 0) for c in range(k)) for p in todos_productos}
    ranking = sorted(blend.items(), key=lambda kv: kv[1], reverse=True)
    top = [(p, s) for p, s in ranking if s > 0.05][:3]

    contribuyentes = [c for c in np.argsort(-pi) if pi[c] > 0.05]
    pi_txt = " + ".join(f"{pi[c]*100:.0f}%cl{c}" for c in contribuyentes)

    rubro_dom = estilo[estilo.clase == contribuyentes[0]]["rubro_contenido_dominante"].values[0]
    tono_dom = estilo[estilo.clase == contribuyentes[0]]["tono_comunicacion"].values[0]
    canal_dom = canal[canal.clase == contribuyentes[0]]["canal_recomendado"].values[0].split(",")[0]

    prob_libranza = 1.0 if elegible_libranza_real else 0.0

    sub = ""
    for p, _ in top:
        if p == "Educativo":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if "Educativo" in puntajes_por_clase[c] else 0))
            sub += f"Educ->{sub_educ_por_clase[c_dom]} "
        if p == "Libre_inversion":
            c_dom = max(range(k), key=lambda c: pi[c] * (1 if sub_libre_por_clase[c] else 0))
            sub += f"LibreInv->{sub_libre_por_clase[c_dom]} "

    return {
        "persona": nombre,
        "pi": pi_txt,
        "productos_top": " > ".join(f"{p}({s:.1f})" for p, s in top) if top else "(SIN SEÑAL)",
        "sub_producto": sub.strip(),
        "rubro": rubro_dom,
        "canal": canal_dom,
        "libranza_pct": round(prob_libranza * 100, 0),
    }


def main():
    modelo_data = pd.read_pickle("data/processed/lca_modelo.pkl")
    modelo, encoder, columnas, k = modelo_data["modelo"], modelo_data["encoder"], modelo_data["columnas"], modelo_data["k"]
    tablas = cargar_tablas()

    resultados = []
    for nombre, persona in PERSONAS.items():
        r = correr_persona(nombre, persona, modelo, encoder, columnas, k, tablas)
        resultados.append(r)

    df = pd.DataFrame(resultados)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(df.to_string(index=False))
    df.to_csv("data/pruebas_resultado/prueba_lote_resultado.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
