"""
Capa complementaria (independiente de macro y de canal): rubro de contenido +
tono/formato de comunicación por clase. Responde "de qué le hablo y cómo",
NO "por cuál canal lo mando" (eso ya está resuelto en theta_k_canal.csv) ni
"qué tan sensible es a la macroeconomía" (eso vive aparte, en
theta_k_sensibilidad_macro.csv, y NO se conecta lógicamente con esto -- son
señales complementarias, no derivadas una de otra).

Fuentes reales usadas (todas ya citadas antes o nuevas esta vuelta):
- Vector de interés ya construido (theta_k_vector_interes.csv) -- define el
  RUBRO dominante (educación, vivienda, viajes, salud, consolidación, día a
  día, tecnología).
- Hallazgos nuevos de consumo Colombia: hogar/decoración fue la categoría de
  mayor crecimiento transaccional (72.25%, 2024); millennials/Gen Z
  RECORTARON 26% su gasto en moda (contraintuitivo, se documenta para no
  asumir "joven = moda"); millennials usan mucho apps financieras y siguen
  influencers digitales para finanzas; Gen Z conecta ahorro con bienestar.
- Mix de plataforma (theta_k_interes_digital_bruto.csv) -- aquí SÍ es su
  lugar correcto: informa FORMATO (visual/breve vs. conversacional vs.
  informativo), no canal de entrega.
"""

import pandas as pd

RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_DIGITAL = "data/theta_k/theta_k_interes_digital_bruto.csv"
RUTA_SALIDA = "data/theta_k/theta_k_estilo_comunicacion.csv"

# rubro (detectado en el interés ya construido) -> tono de comunicación
TONO_POR_RUBRO = {
    "educaci": "Cálido/familiar -- enfocado en el logro y futuro de los hijos, no en el crédito en sí",
    "vivienda": "Aspiracional -- vivienda como símbolo de estabilidad/realización (hallazgo Raddar)",
    "viaje": "Aspiracional/visual -- experiencias, no el producto financiero",
    "salud": "Cercano/tranquilizador -- bienestar y protección, evitar tecnicismos",
    "tecnolog": "Directo, orientado a apps/autogestión -- coherente con uso fintech real de millennials/Gen Z",
    "entretenimiento": "Ligero, informal, breve",
    "día a día": "Práctico/urgente -- resolver el mes, no aspiracional",
    "flujo de caja": "Práctico/urgente -- lenguaje de control y previsibilidad, no de consumo",
    "consolidaci": "Directo/datos -- tranquilidad financiera, cifras claras (tasa, cuota), no emocional",
    "tranquilidad financiera": "Directo/datos, tono de tranquilidad y simplicidad",
}


def tono_de_texto(texto):
    t = texto.lower()
    for clave, tono in TONO_POR_RUBRO.items():
        if clave in t:
            return tono
    return None


def formato_de_mix(mix_fb, mix_ig, mix_msg):
    m = {"Facebook (informativo/texto)": mix_fb, "Instagram (visual/breve, tipo historia)": mix_ig, "Messenger/WhatsApp (conversacional/directo)": mix_msg}
    ganador = max(m, key=m.get)
    return ganador


def main():
    interes = pd.read_csv(RUTA_INTERES, encoding="utf-8-sig")
    digital = pd.read_csv(RUTA_DIGITAL, encoding="utf-8-sig")

    filas = []
    for _, r in interes.iterrows():
        clase = r["clase"]
        rubro_1 = str(r.get("interes_1", "") or "")
        tono = tono_de_texto(rubro_1) if rubro_1 and not rubro_1.lower().startswith(("sin", "genérico")) else "Sin señal suficiente -- usar tono neutro/institucional"

        fila_d = digital[digital["clase"] == clase]
        if len(fila_d):
            formato = formato_de_mix(fila_d["mix_facebook"].values[0], fila_d["mix_instagram"].values[0], fila_d["mix_messenger_proxy_whatsapp"].values[0])
        else:
            formato = "No disponible"

        filas.append({
            "clase": clase,
            "rubro_contenido_dominante": rubro_1 if rubro_1 else "(sin señal)",
            "tono_comunicacion": tono,
            "formato_estilo_dominante": formato,
        })

    resultado = pd.DataFrame(filas).sort_values("clase")
    resultado.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    print(f"Guardado: {RUTA_SALIDA}\n")
    print(resultado.to_string(index=False))
    print(
        "\nNota: esta tabla NO se cruza con theta_k_sensibilidad_macro.csv -- son señales "
        "complementarias (una dice de qué/cómo hablarle, la otra qué tan sensible es a la "
        "macroeconomía), no una se deriva de la otra."
    )


if __name__ == "__main__":
    main()
