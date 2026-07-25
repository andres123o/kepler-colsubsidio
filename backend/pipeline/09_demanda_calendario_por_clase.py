"""
Paso 6 de Frente B (familia 4 de 4): demanda de categoría / calendario por
clase. Igual que macro (familia 3), el calendario es un ÚNICO estado
nacional -- lo que varía por clase es qué tan relevante es cada evento para
ese segmento, no el evento en sí.

Calendario real, verificado (jul-2026), NO se incluye declaración de renta
(descartada por decisión del usuario -- no se verificó el umbral de
obligados a declarar, se prefiere no usarla como señal hasta confirmarlo):

- Prima de servicios: 30-jun y primeros 20 días de dic (Art. 306 CST, fechas
  no prorrogables, aplica a todo afiliado con relación laboral formal).
- Vacaciones escolares: dic-ene y jun-jul.
- Regreso a clases / matrícula: enero (colegio) y enero + julio (universidad,
  semestre I/II).

Modulación por clase -- reutiliza datos que YA existen, no se inventa nada
nuevo:
1. relevancia_educativo_timing: proxy = % de la clase en estructura familiar
   con hijos probable (monoparental + monoparental ampliada + nuclear
   integral + nuclear ampliada), de data/theta_k/clases_perfil_demografico.csv.
2. relevancia_viajes_timing: 1 si "Viajes" ya apareció en el vector de
   interés de esa clase (paso 4), si no, 0 -- no se recalcula, se hereda.
3. relevancia_prima: universal (aplica a todos), pero la ACCIÓN sugerida
   depende de la sensibilidad macro ya calculada (paso 5): si la clase tiene
   consolidación como interés real, prima = ventana para compra de cartera;
   si tiene alta sensibilidad a inflación, prima = ventana de alivio/cupo.
"""

import pandas as pd

RUTA_PERFIL = "data/theta_k/clases_perfil_demografico.csv"
RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_MACRO = "data/theta_k/theta_k_sensibilidad_macro.csv"
RUTA_SALIDA = "data/theta_k/theta_k_demanda_calendario.csv"

CALENDARIO = {
    "prima": ["30 de junio", "primeros 20 días de diciembre"],
    "vacaciones_escolares": ["diciembre-enero", "junio-julio"],
    "regreso_a_clases": ["enero (colegio)", "enero y julio (universidad, semestre I/II)"],
}

CATEGORIAS_CON_HIJOS = [
    "FAMILIA MONOPARENTAL", "FAMILIA MONOPARENTAL AMPLIADA",
    "FAMILIA NUCLEAR INTEGRAL", "FAMILIA NUCLEAR AMPLIADA",
]


def main():
    perfil = pd.read_csv(RUTA_PERFIL, encoding="utf-8-sig")
    interes = pd.read_csv(RUTA_INTERES, encoding="utf-8-sig")
    macro = pd.read_csv(RUTA_MACRO, encoding="utf-8-sig")

    fam = perfil[perfil["variable"] == "SEGMENTO_GRUPO_FAMILIAR"]
    fam_pivot = fam.pivot(index="clase", columns="categoria", values="pct").fillna(0)

    filas = []
    for clase in fam_pivot.index:
        pct_con_hijos = sum(fam_pivot.loc[clase].get(c, 0) for c in CATEGORIAS_CON_HIJOS)

        fila_interes = interes[interes["clase"] == clase]
        intereses_txt = " ".join(str(fila_interes[c].values[0]) for c in ["interes_1", "interes_2", "interes_3"] if c in fila_interes)
        tiene_viajes = "iajes" in intereses_txt
        tiene_consolidacion = "onsolidaci" in intereses_txt

        fila_macro = macro[macro["clase"] == clase]
        alta_sensib_inflacion = float(fila_macro["sensibilidad_inflacion_index"].values[0]) >= 0.7 if len(fila_macro) else False

        if tiene_consolidacion:
            accion_prima = "Ventana para compra de cartera (usar el efectivo extra de la prima para consolidar)"
        elif alta_sensib_inflacion:
            accion_prima = "Ventana de alivio/cupo -- recordatorio de rotativo día a día"
        else:
            accion_prima = "Ventana neutra -- sin acción prioritaria específica"

        filas.append({
            "clase": clase,
            "pct_con_hijos_probable": round(pct_con_hijos, 1),
            "relevancia_educativo_timing": "alta" if pct_con_hijos >= 50 else ("media" if pct_con_hijos >= 25 else "baja"),
            "relevancia_viajes_timing": "alta" if tiene_viajes else "baja",
            "accion_ventana_prima": accion_prima,
        })

    resultado = pd.DataFrame(filas).sort_values("clase")
    resultado.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Calendario nacional (único): {CALENDARIO}\n")
    print(f"Guardado: {RUTA_SALIDA}\n")
    print(resultado.to_string(index=False))


if __name__ == "__main__":
    main()
