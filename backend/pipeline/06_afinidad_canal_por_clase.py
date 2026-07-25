"""
Paso 3 de Frente B (CORREGIDO): cruzar la matriz pública de redes por (edad,
género) (paso 2, data/theta_k/canal_publico_bruto.csv) con la distribución
conjunta real de (edad, género) de cada una de las 12 clases de LCA.

Corrección importante sobre la versión anterior de este script: Instagram /
Facebook / Messenger NO son canales de entrega de Colsubsidio (nunca se manda
una oferta de crédito por Instagram DM) -- son comportamiento en redes, y
sirven para entender GUSTOS/INTERESES/A QUÉ CONTENIDO RESPONDE la persona
(familia "redes sociales / intereses" de §5.2, Tipo B), no para decidir POR
CUÁL canal real (push / WhatsApp / email, físico se deja para después)
se manda la oferta. Esa mezcla iba antes en la misma tabla que el canal real
y eso estaba mal -- se separan en dos salidas distintas:

  1. theta_k_canal.csv          -- SOLO canal real de entrega. Se decide con
     la única señal real y específica de canal que tenemos: tasa de
     deshabilitar PUSH por edad (60+: 57%, resto: 31%), más el benchmark de
     industria (no viene de redes sociales, viene de research de marketing
     engagement) de que WhatsApp Business tiene open rate 85-98% vs push
     20-40% vs email ~20-25% -- por eso WhatsApp es el canal por defecto
     salvo que haya una razón real para preferir push (más barato) o email
     (respaldo/registro).
  2. theta_k_interes_digital_bruto.csv -- el mix Instagram/Facebook/Messenger
     y el reach digital agregado, SIN NINGUNA decisión de canal todavía --
     insumo crudo para la siguiente familia (vector de interés, Tipo B), que
     se construye en un paso aparte, no aquí.

Se deja explícitamente FUERA de este paso la idea de diferenciar por tamaño
de empresa/horario de oficina -- confirmado que la jornada laboral en
Colombia es un estándar único (Ley 2101/2021, ~8:00am-5:00pm con almuerzo
12-2pm), no varía por tipo de empresa. Ese dato general de jornada se guarda
para usarse después como contexto de "momento del día" en el World State /
capa agéntica (§5.3), no como parte de esta tabla.
"""

import pandas as pd

RUTA_DATA = "data/processed/data_limpia.pkl"
RUTA_PI = "data/processed/lca_pi.pkl"
RUTA_CANAL_BRUTO = "data/theta_k/canal_publico_bruto.csv"
RUTA_SALIDA_CANAL = "data/theta_k/theta_k_canal.csv"
RUTA_SALIDA_INTERES_BRUTO = "data/theta_k/theta_k_interes_digital_bruto.csv"

# Push-disablement (dato global de industria push notifications, no Colombia-específico,
# se aplica como aproximación al bucket "Mayor de 55 años" -- el corte real de la fuente
# es "60+", nuestro bucket empieza en 55, imprecisión documentada, no oculta).
TASA_DESHABILITAR_PUSH = {
    "Mayor de 55 años": 0.57,
    "_default": 0.31,
}

# Benchmark de industria (marketing engagement research, NO viene de redes sociales):
# WhatsApp Business open rate 85-98%, push 20-40%, email ~20-25%. No es Colombia-
# específico ni por edad -- es la única base real que tenemos para rankear los 3
# canales de entrega entre sí quitando el sesgo de redes sociales.
OPEN_RATE_BENCHMARK = {"whatsapp": (85, 98), "push": (20, 40), "email": (20, 25)}


def main():
    print("Cargando data e insumos de pasos previos ...")
    df = pd.read_pickle(RUTA_DATA)
    pi = pd.read_pickle(RUTA_PI)
    canal = pd.read_csv(RUTA_CANAL_BRUTO)

    cols_clase = [c for c in pi.columns if c.startswith("clase_")]
    k = len(cols_clase)
    df = df.reset_index(drop=True).copy()
    df["clase"] = pi[cols_clase].values.argmax(axis=1)

    # --- Distribución conjunta real (edad, género) por clase ---
    conjunta = (
        df.groupby(["clase", "RANGO_EDAD", "GENERO"]).size().reset_index(name="n")
    )
    conjunta["pct"] = conjunta.groupby("clase")["n"].transform(lambda s: s / s.sum())

    # --- Mix relativo de plataforma, ahora por (edad, género), no solo edad ---
    canal_pivot = canal.set_index(["rango_edad"])[["pct_F", "pct_M"]]
    plataformas = canal["plataforma"].unique().tolist()

    # tabla: (rango_edad, genero) -> {plataforma: pct_del_universo_de_esa_plataforma}
    universo = {}
    reach_prom = {}  # (rango_edad, genero) -> alcance digital promedio (proxy de "qué tan digital es este segmento")
    for _, row in canal.iterrows():
        edad = row["rango_edad"]
        for genero, col in [("F", "pct_F"), ("M", "pct_M")]:
            universo.setdefault((edad, genero), {})[row["plataforma"]] = row[col]

    for (edad, genero), vals in universo.items():
        suma = sum(vals.values())
        reach_prom[(edad, genero)] = suma / len(vals)  # promedio simple de alcance entre las 3 plataformas
        for p in vals:
            vals[p] = vals[p] / suma * 100  # normalizado dentro de (edad,género) -> mix relativo

    # --- Cruce: para cada clase, mezcla ponderada por su composición real de (edad, género) ---
    filas = []
    for clase in range(k):
        sub = conjunta[conjunta["clase"] == clase]
        afinidad = {p: 0.0 for p in plataformas}
        reach_index = 0.0
        push_disable = 0.0
        for _, r in sub.iterrows():
            edad, genero, peso = r["RANGO_EDAD"], r["GENERO"], r["pct"]
            mix = universo.get((edad, genero))
            if mix is None:
                continue  # género "Sin dato" u otro no cubierto por la fuente pública
            for p in plataformas:
                afinidad[p] += peso * mix[p]
            reach_index += peso * reach_prom[(edad, genero)]
            tasa = TASA_DESHABILITAR_PUSH.get(edad, TASA_DESHABILITAR_PUSH["_default"])
            push_disable += peso * tasa

        fila = {"clase": clase, "reach_digital_index": round(reach_index, 2),
                "tasa_deshabilitar_push_estimada": round(push_disable * 100, 1)}
        for p in plataformas:
            fila[f"mix_{p}"] = round(afinidad[p], 1)
        filas.append(fila)

    resultado = pd.DataFrame(filas)

    # --- SALIDA 1: canal real de entrega -- SOLO con señal específica de canal ---
    # (tasa de deshabilitar push, del canal push en sí; benchmark de industria
    # WhatsApp/push/email; y ahora también reach_digital_index como proxy de
    # compromiso digital general -- ninguna de las tres viene de "qué red social
    # usa", son señales legítimas de canal, no de plataforma).
    #
    # Corrección 23-jul-2026 (el usuario notó que la regla anterior SIEMPRE
    # devolvía "WhatsApp primero" en las dos ramas posibles -- sesgo real de
    # diseño, no un hallazgo de los datos). Se agrega una tercera rama con
    # evidencia real: 27% de millennials prefieren push a SMS en banca (Fiserv/
    # Engage Hub) -- los segmentos de alto compromiso digital (reach_digital_index
    # alto: clases jóvenes 1,2,7,8) sí deben tener push compitiendo de verdad,
    # no solo como secundario fijo. WhatsApp se mantiene como default fuerte para
    # el resto porque el hallazgo Colombia 2023-24 (WhatsApp subiendo como canal
    # preferido, 8.8/10, vs. línea telefónica cayendo de 43% a 30%) sí lo respalda.
    UMBRAL_ALTO_COMPROMISO_DIGITAL = 18.0

    def decidir_canal(row):
        if row["tasa_deshabilitar_push_estimada"] > 45:
            return "WhatsApp primero + email de respaldo (push poco confiable: alta tasa de deshabilitar en este segmento)"
        if row["reach_digital_index"] >= UMBRAL_ALTO_COMPROMISO_DIGITAL:
            return "WhatsApp y Push como igual de fuertes (27% de millennials prefiere push a SMS en banca -- alto compromiso digital de este segmento), email de respaldo"
        return "WhatsApp primero (open rate 85-98% vs push 20-40% vs email 20-25%), push como secundario de bajo costo, email de respaldo/registro"

    canal = resultado[["clase", "tasa_deshabilitar_push_estimada", "reach_digital_index"]].copy()
    canal["canal_recomendado"] = resultado.apply(decidir_canal, axis=1)
    canal.to_csv(RUTA_SALIDA_CANAL, index=False, encoding="utf-8-sig")
    print(f"Guardado: {RUTA_SALIDA_CANAL}\n")
    print(canal.to_string(index=False))

    # --- SALIDA 2: insumo crudo para vector de interés (Tipo B) -- SIN decisión de canal ---
    interes_bruto = resultado[["clase", "reach_digital_index"] + [f"mix_{p}" for p in plataformas]].copy()
    interes_bruto.to_csv(RUTA_SALIDA_INTERES_BRUTO, index=False, encoding="utf-8-sig")
    print(f"\nGuardado (insumo crudo, sin decisión de canal): {RUTA_SALIDA_INTERES_BRUTO}\n")
    print(interes_bruto.to_string(index=False))

    print(
        "\nJornada laboral Colombia (Ley 2101/2021 + fuente citada): estándar único, no varía "
        "por tipo de empresa -- 8:00am-5:00pm, almuerzo 12:00-2:00pm (8h efectivas + 1h almuerzo "
        "no remunerada, tope semanal 42h desde 15-jul-2026). Se guarda como dato de contexto de "
        "día para el World State/capa agéntica (§5.3), NO se usa aquí como señal de clase."
    )


if __name__ == "__main__":
    main()
