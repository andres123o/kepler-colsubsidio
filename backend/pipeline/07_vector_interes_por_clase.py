"""
Paso 4 de Frente B: vector de interés final por clase (familia 2 de 4,
Tipo B -- §5.2). A diferencia de canal (paso 3), esta tabla combina datos
reales (edad/género/categoría/segmento familiar de cada clase, ya calculados
en LCA) con investigación de consumo real citada (Raddar, estudios Gen Z
Colombia) mediante SÍNTESIS RAZONADA, no una fórmula estadística -- se marca
así explícitamente, con nivel de confianza por fila, para no presentarlo
como más "calculado" de lo que es.

Fuentes de la síntesis:
- Raddar (millennials Colombia): vivienda como símbolo de estabilidad, 87%
  quiere viajar, gasto 24% mayor que el promedio en bienestar/placer.
- Gen Z Colombia: 58% tecnología/ciencia, 41% interés en educación, 30%
  ahorra específicamente para educación, 66% ahorra activamente.
- Composición real por clase: RANGO_EDAD, GENERO, CATEGORIA,
  SEGMENTO_GRUPO_FAMILIAR (data/theta_k/clases_perfil_demografico.csv).
- reach_digital_index (data/theta_k/theta_k_interes_digital_bruto.csv),
  usado únicamente para el eje tecnología/entretenimiento -- NO para canal.

Revisión aplicada (5 correcciones tras razonar cada clase contra el dato
real, no aceptadas a ciegas):
1. Clase 0: reordenado -- día a día/rotativo primero (Cat A, presupuesto
   ajustado), educación de los hijos segundo (real pero periódico).
2. Clase 1: reordenado -- rotativo/flujo de caja primero (independiente/
   informal, ingreso irregular), tecnología segundo.
3. Clase 3: mantiene consolidación de deudas + salud, pero marcada
   confianza BAJA -- es inferencia razonable del régimen "Independiente",
   no tiene una cifra de investigación específica detrás como las demás.
4. Clase 4: se agrega vivienda/libre inversión aspiracional -- la mejor
   mezcla de ingreso de las 12 clases (31.6% Cat C) + mayoría sin
   dependientes estaba subponderada en la versión anterior.
5. Clase 7: se agrega vivienda aspiracional -- mejor ingreso/estabilidad
   laboral (empresa foco) que las otras clases jóvenes justifica el hallazgo
   de Raddar (vivienda = símbolo de estabilidad) con más fuerza aquí que en
   las clases 1/2/8.

Nota transversal: "Gen Z" real son personas de ~14-29 años en 2026; nuestro
bucket "20 a 35 años" mezcla Gen Z con millennials tempranos -- se etiqueta
como "consistente direccionalmente", no como pertenencia generacional exacta.
"""

import pandas as pd

RUTA_SALIDA = "data/theta_k/theta_k_vector_interes.csv"

# clase -> (intereses en orden de prioridad, confianza, razonamiento corto)
VECTOR_INTERES = {
    0: (["Día a día / rotativo", "Educación de los hijos"], "media",
        "100% F, Cat A (presupuesto ajustado -> necesidad inmediata primero), 55.6% monoparental + 11.2% nuclear integral (67% con hijos probable) -> educación real pero secundaria/periódica"),
    1: (["Rotativo / flujo de caja", "Tecnología / entretenimiento"], "media",
        "95% M, joven, Cat A, 100% sin grupo, régimen independiente/facultativo -> ingreso irregular, flujo de caja pesa más que consumo discrecional"),
    2: (["Tecnología / entretenimiento", "Ahorro para educación"], "alta",
        "91% <35 (mezcla Gen Z + millennial temprano, bucket no distingue exacto), 100% sin grupo, Cat A -> match directo con estudio Gen Z Colombia (58% tech, 30% ahorra para educación)"),
    3: (["Consolidación de deudas", "Salud"], "BAJA",
        "Cat B, régimen 'Independiente' (98%), edad muy repartida sin pico -> inferencia razonable, sin cifra de investigación específica detrás, distinta de las demás filas"),
    4: (["Vivienda / libre inversión aspiracional", "Salud", "Consolidación de deudas"], "media",
        "0% jóvenes, mejor mezcla de ingreso de las 12 clases (31.6% Cat C), 54.4% sin grupo familiar, Bogotá 55% -> profesional establecido, sin dependientes, ingreso alto"),
    5: (["Genérico -- sin señal suficiente"], "muy baja",
        "Dato 'Sin dato' dominante en casi todas las columnas -- no asignar interés fino"),
    6: (["Día a día / rotativo", "Educación (si hay hijos)"], "media",
        "100% M, Cat A, familia mixta -- 36.7% sin grupo / 35% monoparental / 22.5% nuclear (no hay mayoría clara, se deja condicional)"),
    7: (["Viajes", "Vivienda aspiracional", "Tecnología"], "media",
        "85.6% joven, mejor mezcla de ingreso entre clases jóvenes (13.5% Cat C), empresa foco (empleo formal/grande) -> match con Raddar (87% quiere viajar, vivienda = símbolo de estabilidad) más creíble aquí que en 1/2/8 por el ingreso/estabilidad"),
    8: (["Tecnología / entretenimiento", "Viajes"], "media",
        "84.4% joven, 99.7% sin grupo (el perfil 'soltero' más puro), sin ventaja de ingreso particular -> perfil genérico joven-soltero"),
    9: (["Educación de los hijos", "Vivienda", "Consolidación de deudas"], "media",
        "Adultos 36-55+, buena mezcla de ingreso (27.2% Cat C), 66% con estructura familiar (38.3% monoparental + 18.5% nuclear + 9.6% pareja), empresa foco -> edad de padres compatible con hijos en edad escolar/universitaria"),
    10: (["Salud", "Tranquilidad financiera / consolidación"], "alta",
         "95.4% mayores de 55 (pensionados), Cat A, sin grupo/pareja (sin dependientes jóvenes) -> salud es la prioridad mejor fundamentada de las 12"),
    11: (["Educación de los hijos"], "alta",
         "86.7% monoparental (55.6% + 8.6% ampliada) -- la concentración más alta de las 12 clases, sin nadie mayor de 46 años -> señal más limpia y específica del set"),
}


def main():
    filas = []
    for clase, (intereses, confianza, razon) in VECTOR_INTERES.items():
        filas.append({
            "clase": clase,
            "interes_1": intereses[0],
            "interes_2": intereses[1] if len(intereses) > 1 else "",
            "interes_3": intereses[2] if len(intereses) > 2 else "",
            "confianza": confianza,
            "razonamiento": razon,
        })
    df = pd.DataFrame(filas).sort_values("clase")
    df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Guardado: {RUTA_SALIDA}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
