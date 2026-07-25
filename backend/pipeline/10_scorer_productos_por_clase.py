"""
Paso 7: Scorer aditivo glass-box + elegibilidad (§5.4), a nivel de clase
(las 12 clases de LCA -- el demo usa la clase dominante de cada afiliado,
argmax de pi_i; producción real blendearía con theta_i = suma pi_ik*theta_k,
fuera de alcance de este script).

Alcance confirmado con el usuario para este demo:
- NO calcula monto -- solo producto(s) elegible(s) + sub-producto + razones.
- Puede devolver 1, 2 o 3 productos por clase -- nunca un número forzado; solo
  se muestran los que tengan score > 0 entre los que pasan elegibilidad.
- Elegibilidad: SOLO la regla de libranza (Libre inversión requiere nómina o
  pensión -- Ley 1527/2012 cubre "salario o pensión", excluye Facultativo/
  Independiente/Sin dato en PIRAMIDE_NUEVA). Antigüedad/tipo de contrato
  del catálogo NO se verifica -- no existe esa columna en los datos, se
  excluye del gate por decisión explícita (no sobreingeniería).

Fuentes de señal, todas ya calculadas en pasos previos -- no se inventa nada
nuevo aquí, este paso solo las combina:
- theta_k_vector_interes.csv   (Frente B, familia 2)
- theta_k_sensibilidad_macro.csv (familia 3)
- theta_k_demanda_calendario.csv (familia 4)
- clases_perfil_demografico.csv  (PIRAMIDE_NUEVA para elegibilidad, RANGO_EDAD
  para sub-producto de Educativo)

Puntaje aditivo (glass-box, cada punto es una razón nombrada):
  interes_1 -> +3, interes_2 -> +2, interes_3 -> +1
  macro: 'subir rotativo' -> Rotativo_cupo +2 | 'compra cartera alto' -> Compra_cartera +2
  calendario: educativo 'alta' -> Educativo +2 | viajes 'alta' -> Libre_inversion +2
              ventana prima menciona 'compra de cartera' -> Compra_cartera +1
              ventana prima menciona 'rotativo' -> Rotativo_cupo +1
"""

import pandas as pd

RUTA_PERFIL = "data/theta_k/clases_perfil_demografico.csv"
RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_MACRO = "data/theta_k/theta_k_sensibilidad_macro.csv"
RUTA_CALENDARIO = "data/theta_k/theta_k_demanda_calendario.csv"
RUTA_SALIDA = "data/theta_k/scorer_resultado_por_clase.csv"

PIRAMIDE_NO_LIBRANZA = {"6.1 Facultativo", "6.2 Independiente", "Sin dato"}

# Mapa interés (texto libre de theta_k_vector_interes) -> producto del catálogo real de 7 líneas
MAPA_INTERES_PRODUCTO = [
    ("educaci", "Educativo"),
    ("ahorro para educaci", "Educativo"),
    ("vivienda", "Hipotecario"),
    ("viaje", "Libre_inversion"),
    ("salud", "Libre_inversion"),
    ("tecnolog", "Libre_inversion"),
    ("entretenimiento", "Libre_inversion"),
    ("día a día", "Rotativo_cupo"),
    ("flujo de caja", "Rotativo_cupo"),
    ("consolidaci", "Compra_cartera"),
    ("tranquilidad financiera", "Compra_cartera"),
]

SUBPRODUCTO_LIBRE_INVERSION = {
    "viaje": "Viajes", "salud": "Salud", "tecnolog": "Tecnología/otros fines", "entretenimiento": "Tecnología/otros fines",
}


def producto_de_interes(texto):
    t = texto.lower()
    for clave, producto in MAPA_INTERES_PRODUCTO:
        if clave in t:
            return producto
    return None


def main():
    perfil = pd.read_csv(RUTA_PERFIL, encoding="utf-8-sig")
    interes = pd.read_csv(RUTA_INTERES, encoding="utf-8-sig")
    macro = pd.read_csv(RUTA_MACRO, encoding="utf-8-sig")
    calendario = pd.read_csv(RUTA_CALENDARIO, encoding="utf-8-sig")

    piramide = perfil[perfil["variable"] == "PIRAMIDE_NUEVA"].pivot(index="clase", columns="categoria", values="pct").fillna(0)
    pct_no_libranza = piramide[[c for c in PIRAMIDE_NO_LIBRANZA if c in piramide.columns]].sum(axis=1)

    edad = perfil[perfil["variable"] == "RANGO_EDAD"].pivot(index="clase", columns="categoria", values="pct").fillna(0)

    filas_salida = []
    for clase in range(12):
        elegible_libranza = pct_no_libranza.get(clase, 100) < 50  # mayoría con nómina/pensión

        puntos = {}
        razones = {}

        def sumar(producto, pts, razon):
            puntos[producto] = puntos.get(producto, 0) + pts
            razones.setdefault(producto, []).append(f"{razon} (+{pts})")

        fila_int = interes[interes["clase"] == clase].iloc[0]
        pesos_interes = [("interes_1", 3), ("interes_2", 2), ("interes_3", 1)]
        sub_libre_inversion = None
        for col, pts in pesos_interes:
            texto = str(fila_int.get(col, "") or "")
            if not texto or texto.lower().startswith("sin") or texto.lower().startswith("genérico"):
                continue
            producto = producto_de_interes(texto)
            if producto is None:
                continue
            if producto == "Libre_inversion" and not elegible_libranza:
                continue  # gate de elegibilidad -- ni siquiera entra al puntaje
            sumar(producto, pts, f"Interés real de la clase: '{texto}'")
            if producto == "Libre_inversion" and sub_libre_inversion is None:
                for clave, sub in SUBPRODUCTO_LIBRE_INVERSION.items():
                    if clave in texto.lower():
                        sub_libre_inversion = sub
                        break

        fila_macro = macro[macro["clase"] == clase].iloc[0]
        if "Rotativo" in str(fila_macro["implicacion_producto"]):
            sumar("Rotativo_cupo", 2, "Alta sensibilidad a inflación (dato DANE) -- necesidad de día a día")
        if str(fila_macro["atractivo_compra_cartera"]).startswith("alto"):
            sumar("Compra_cartera", 2, "Propensión real a consolidación + tasa BanRep 12% (muy sobre la meta)")

        fila_cal = calendario[calendario["clase"] == clase].iloc[0]
        if fila_cal["relevancia_educativo_timing"] == "alta":
            sumar("Educativo", 2, "Ventana de calendario: regreso a clases/matrícula (enero/julio)")
        if fila_cal["relevancia_viajes_timing"] == "alta" and elegible_libranza:
            sumar("Libre_inversion", 2, "Ventana de calendario: vacaciones escolares (dic-ene/jun-jul)")
            if sub_libre_inversion is None:
                sub_libre_inversion = "Viajes"
        accion_prima = str(fila_cal["accion_ventana_prima"])
        if "compra de cartera" in accion_prima.lower():
            sumar("Compra_cartera", 1, "Ventana de prima (30-jun/20-dic): efectivo extra para consolidar")
        if "rotativo" in accion_prima.lower():
            sumar("Rotativo_cupo", 1, "Ventana de prima (30-jun/20-dic): recordatorio de cupo")

        ranking = sorted(puntos.items(), key=lambda kv: kv[1], reverse=True)[:3]

        sub_producto_txt = ""
        if any(p == "Educativo" for p, _ in ranking):
            pct_joven = edad.loc[clase].get("20 a 35 años", 0)
            pct_con_hijos = fila_cal["pct_con_hijos_probable"]
            if pct_joven > 50:
                sub_educativo = "Técnico/Pregrado (propio)"
            elif pct_con_hijos >= 50:
                sub_educativo = "Apoyo educativo a hijos (colegio/pregrado)"
            else:
                sub_educativo = "Posgrado/especialización (propio)"
            sub_producto_txt += f"Educativo->{sub_educativo}; "
        if any(p == "Libre_inversion" for p, _ in ranking) and sub_libre_inversion:
            sub_producto_txt += f"Libre_inversion->{sub_libre_inversion}; "

        filas_salida.append({
            "clase": clase,
            "elegible_libranza": elegible_libranza,
            "productos_top": " > ".join(f"{p}({s})" for p, s in ranking) if ranking else "(sin señal suficiente)",
            "sub_producto": sub_producto_txt.strip(),
            "razones": " | ".join(f"[{p}] " + "; ".join(razones[p]) for p, _ in ranking),
        })

    resultado = pd.DataFrame(filas_salida)
    resultado.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Guardado: {RUTA_SALIDA}\n")
    for _, r in resultado.iterrows():
        print(f"=== Clase {r['clase']} (libranza elegible: {r['elegible_libranza']}) ===")
        print(f"  Productos: {r['productos_top']}")
        print(f"  Sub-producto: {r['sub_producto']}")
        print(f"  Razones: {r['razones']}")
        print()


if __name__ == "__main__":
    main()
