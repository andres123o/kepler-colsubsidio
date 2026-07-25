"""
Paso 1 de Frente A: limpieza del dataset real antes de MCA + LCA.

Qué hace, en orden:
1. Carga el CSV completo (1.56M filas).
2. Elimina ESTADOAFILIADO (100% constante, verificado empíricamente).
3. Canonicaliza duplicados de captura en PIRAMIDE_NUEVA.
4. Agrupa CIUDAD_AFILIADO por cercanía real a Bogotá (no por departamento crudo),
   usando como proxy la Región Metropolitana Bogotá-Cundinamarca (Ley 2199/2022).
5. Recodifica blancos como "Sin dato" explícito (no NaN) en las columnas que se
   usan para segmentar, para que sea una categoría legible más, no un vacío.
6. Guarda el resultado limpio en data/processed/data_limpia.pkl para no releer el
   CSV de 200MB en cada paso siguiente (MCA, LCA).

Nota de honestidad: la lista de municipios de la Región Metropolitana (línea
REGION_METROPOLITANA) se arma de memoria a partir de la Ley 2199/2022 y debe
verificarse contra el texto oficial antes de usarla en el pitch final. Los
municipios con volumen bajo dudoso quedan en "Otro municipio de Cundinamarca"
por precaución.
"""

import pandas as pd

RUTA_CSV = "data/raw/Usos_Productos_Afiliados_SIN_ID.csv"
RUTA_SALIDA = "data/processed/data_limpia.pkl"

# Municipios que sí están conurbados/funcionalmente integrados a Bogotá
# (Ley 2199/2022, Región Metropolitana Bogotá-Cundinamarca) -- VERIFICAR antes del pitch.
REGION_METROPOLITANA = {
    "SOACHA", "CHIA", "COTA", "CAJICA", "SOPO", "TOCANCIPA",
    "ZIPAQUIRA", "FUNZA", "MOSQUERA", "MADRID", "FACATATIVA",
}

# Municipios de Cundinamarca que aparecen en la data pero están lejos de Bogotá
# (no conurbados) -- se agrupan aparte para no perder el gradiente cerca/lejos.
OTRO_CUNDINAMARCA = {
    "FUSAGASUGA", "GIRARDOT", "VILLA DE SAN DIEGO DE UBATE",
    "SIBATE", "EL ROSAL", "LA MESA",
}


def agrupar_ciudad(valor):
    if not isinstance(valor, str) or valor.strip() == "":
        return "Sin dato"
    v = valor.strip().upper()
    if v == "BOGOTA D.C.":
        return "Bogotá D.C."
    if v in REGION_METROPOLITANA:
        return "Región metropolitana"
    if v in OTRO_CUNDINAMARCA:
        return "Otro municipio de Cundinamarca"
    return "Otro departamento"


def limpiar_categorica(serie):
    """Blancos/NaN -> 'Sin dato' explícito, en vez de dejarlos vacíos."""
    return serie.fillna("Sin dato").replace(r"^\s*$", "Sin dato", regex=True)


def main():
    print(f"Leyendo {RUTA_CSV} ...")
    df = pd.read_csv(
        RUTA_CSV,
        sep=";",
        dtype=str,
        keep_default_na=False,  # los blancos del CSV llegan como "", no NaN
    )
    n_inicial = len(df)
    print(f"Filas leídas: {n_inicial:,}")

    # 1. Eliminar columna constante (confirmado 100% "Al dia" en el 1.56M)
    assert df["ESTADOAFILIADO"].nunique() == 1, (
        "ESTADOAFILIADO dejó de ser constante -- revisar antes de eliminarla"
    )
    df = df.drop(columns=["ESTADOAFILIADO"])

    # 1b. Sacar CATEGORIA=D (solo 2 filas en 1.56M) -- una categoría con n=2 no se
    # puede modelar estadísticamente y distorsiona MCA/LCA como outlier (verificado:
    # infla ejes de MCA a valores >18 cuando el resto está entre -2 y +2). Se maneja
    # aparte con regla manual si vuelve a aparecer, no con clustering.
    n_antes = len(df)
    df = df[df["CATEGORIA"] != "D"].copy()
    print(f"Filas CATEGORIA=D excluidas del modelado: {n_antes - len(df)}")

    # 2. Canonicalizar duplicados de captura en PIRAMIDE_NUEVA
    df["PIRAMIDE_NUEVA"] = df["PIRAMIDE_NUEVA"].replace({
        "1. Grandes": "1 Grandes",
        "5 Micro Transaccional Colsubsidio": "5 Micro Transaccional",
    })

    # 3. Agrupar ciudad por cercanía real a Bogotá
    df["CIUDAD_GRUPO"] = df["CIUDAD_AFILIADO"].apply(agrupar_ciudad)

    # 4. Recodificar EMPRESA_FOCO a SI/NO explícito (hoy es "X"/vacío)
    df["EMPRESA_FOCO"] = df["EMPRESA_FOCO"].apply(lambda v: "SI" if v.strip() == "X" else "NO")

    # 5. Blancos -> "Sin dato" en las columnas categóricas que van a MCA/LCA
    columnas_categoricas_modelo = [
        "GENERO", "RANGO_EDAD", "CATEGORIA", "SEGMENTO_GRUPO_FAMILIAR",
        "SEGMENTO_POBLACIONAL", "PIRAMIDE_NUEVA",
    ]
    for col in columnas_categoricas_modelo:
        df[col] = limpiar_categorica(df[col])

    # Las banderas de servicio (SI/NO) ya vienen limpias -- no tienen blancos reales
    # (se verificó en el diagnóstico empírico previo). Se conservan tal cual, incluidas
    # HOTELES/AGENCIAS/VIVIENDA, aunque esas tres NO entran a MCA/LCA (van como reglas
    # de excepción en el motor de elegibilidad, no como eje de segmentación).

    print(f"Filas finales: {len(df):,} (de {n_inicial:,} originales)")

    df.to_pickle(RUTA_SALIDA)
    print(f"Guardado: {RUTA_SALIDA} ({len(df):,} filas, {len(df.columns)} columnas)")

    print("\n--- Verificación rápida post-limpieza ---")
    print("PIRAMIDE_NUEVA (debe tener 8 categorías, sin duplicados sucios):")
    print(df["PIRAMIDE_NUEVA"].value_counts())
    print("\nCIUDAD_GRUPO (nuevo, 5 categorías):")
    print(df["CIUDAD_GRUPO"].value_counts())
    print("\nEMPRESA_FOCO (recodificado):")
    print(df["EMPRESA_FOCO"].value_counts())


if __name__ == "__main__":
    main()
