"""
Paso 5 de Frente B (familia 3 de 4): sensibilidad macro por clase.

A diferencia de canal e interés, esta familia NO se calcula por persona ni
por clase de forma independiente -- el macro es un ÚNICO estado nacional
(§5.3, World State), y lo que varía por clase es la INTERACCIÓN: cuánto le
pega ese mismo estado macro a cada segmento. Esto es exactamente el patrón
"modula por interacción, no es feature por persona" que ya usa el doc para
World State (§5.3).

Estado macro actual (real, citado, único, jul-2026):
- Tasa de política monetaria BanRep: 12% (subida 75pbs jun-jul 2026)
- Inflación anual mayo-2026: 5.8% total / 6.0% núcleo
- Proyección BanRep cierre 2026: 6.4% (meta de largo plazo: 3%)

Dos mecanismos de interacción, cada uno con su propia justificación:

1. sensibilidad_inflacion_index: entre más ingreso bajo, mayor proporción del
   presupuesto se va a bienes básicos, así que la misma inflación golpea más
   fuerte en términos relativos -- Ley de Engel. Los pesos por categoría YA
   NO son una elección razonada a ojo -- se calibraron con dato real DANE:
   % del ingreso gastado en alimentos por nivel socioeconómico (pobre 23.78%,
   vulnerable 22.24%, media 15.80%, alta 8.16%), normalizado 0-1 contra Cat A.
   sensibilidad = %A*peso_A + %B*peso_B + %C*peso_C (pesos ver _GASTO_ALIMENTOS_PCT)

2. atractivo_compra_cartera: la propensión base viene del vector de interés
   ya construido (paso 4) -- las clases donde "Consolidación de deudas" ya
   apareció como interés (3, 4, 9) son las que más se benefician de
   consolidar deuda cuando la tasa de referencia está alta (12%, muy por
   encima del histórico/meta de 3%) -- la tasa alta no CREA el interés, lo
   AMPLIFICA sobre una propensión que ya era real.
"""

import pandas as pd

RUTA_PERFIL = "data/theta_k/clases_perfil_demografico.csv"
RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_SALIDA = "data/theta_k/theta_k_sensibilidad_macro.csv"

MACRO_ESTADO = {
    "tasa_banrep_pct": 12.0,
    "inflacion_actual_pct": 5.8,
    "inflacion_proyectada_2026_pct": 6.4,
    "meta_inflacion_pct": 3.0,
}

# Pesos calibrados con dato real DANE (no la elección razonada 1.0/0.5/0.2 de la
# versión anterior): % del ingreso gastado en alimentos por nivel socioeconómico --
# pobre 23.78%, vulnerable 22.24%, media 15.80%, alta 8.16%. Cat A (<=2 SMMLV) se
# aproxima al promedio pobre+vulnerable (23.01%), Cat B (2-4 SMMLV) a "media"
# (15.80%), Cat C (>4 SMMLV) a "alta" (8.16%) -- normalizado contra Cat A (la más
# sensible = 1.0) para que el índice conserve la MISMA escala 0-1 de antes.
_GASTO_ALIMENTOS_PCT = {"A": (23.78 + 22.24) / 2, "B": 15.80, "C": 8.16}
PESO_SENSIBILIDAD = {k: round(v / _GASTO_ALIMENTOS_PCT["A"], 3) for k, v in _GASTO_ALIMENTOS_PCT.items()}


def main():
    perfil = pd.read_csv(RUTA_PERFIL, encoding="utf-8-sig")
    interes = pd.read_csv(RUTA_INTERES, encoding="utf-8-sig")

    cat = perfil[perfil["variable"] == "CATEGORIA"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    filas = []
    for clase in cat.index:
        pct_a = cat.loc[clase].get("A", 0)
        pct_b = cat.loc[clase].get("B", 0)
        pct_c = cat.loc[clase].get("C", 0)
        sensibilidad = (pct_a * PESO_SENSIBILIDAD["A"] + pct_b * PESO_SENSIBILIDAD["B"] + pct_c * PESO_SENSIBILIDAD["C"]) / 100

        fila_interes = interes[interes["clase"] == clase]
        intereses_txt = " ".join(str(fila_interes[c].values[0]) for c in ["interes_1", "interes_2", "interes_3"] if c in fila_interes)
        tiene_consolidacion = "onsolidaci" in intereses_txt  # matchea "Consolidación"/"consolidacion" sin depender de tildes/mayúsculas exactas

        filas.append({
            "clase": clase,
            "sensibilidad_inflacion_index": round(sensibilidad, 3),
            "atractivo_compra_cartera": "alto (propensión ya real en vector de interés + tasa BanRep 12%, muy sobre la meta)" if tiene_consolidacion else "bajo/medio (sin propensión previa de consolidación)",
            "implicacion_producto": (
                "Subir prioridad de Rotativo día a día/cupo" if sensibilidad >= 0.7
                else "Sensibilidad a inflación media -- sin ajuste fuerte" if sensibilidad >= 0.4
                else "Baja sensibilidad a inflación -- foco en otros ejes"
            ),
        })

    resultado = pd.DataFrame(filas).sort_values("clase")
    resultado.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Macro estado (único, nacional): {MACRO_ESTADO}\n")
    print(f"Guardado: {RUTA_SALIDA}\n")
    print(resultado.to_string(index=False))


if __name__ == "__main__":
    main()
