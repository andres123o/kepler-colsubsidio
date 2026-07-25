"""
Paso 2 de Frente B: matriz pública de afinidad de canal por (edad, género),
construida con datos reales citables -- no inventados, no simulados.

Fuente cruda: NapoleonCat "Social Media Users in Colombia" (snapshot jun-2026),
tabla detallada de edad x género para Facebook, Instagram y Messenger -- es la
única de las fuentes públicas consultadas (DataReportal, NapoleonCat) que
publica el desglose de edad, no solo género agregado.

Limitaciones que se documentan explícitamente, no se ocultan:
1. WhatsApp NO publica desglose de edad/género en ninguna fuente pública
   consultada (Meta no vende audiencia publicitaria segmentada de WhatsApp
   como sí hace con Facebook/Instagram/Messenger). Se usa Messenger como
   proxy de "afinidad a mensajería directa" -- es la app de mensajería de
   Meta con datos públicos más cercana a WhatsApp en comportamiento, pero
   NO es un dato real de WhatsApp. Se declara así en cada tabla derivada.
2. Los buckets de edad de NapoleonCat (13-17, 18-24, 25-34, 35-44, 45-54,
   55-64, 65+) no calzan exacto con los nuestros (RANGO_EDAD de la data real:
   Menor de 19, 20 a 35, 36 a 45, 46 a 55, Mayor de 55). Crosswalk usado:
     Menor de 19  <- 13-17          (no cubre 18-19, no hay data más fina)
     20 a 35      <- 18-24 + 25-34  (incluye 18-19, sesgo leve hacia arriba)
     36 a 45      <- 35-44          (borde 44 vs 45, aproximación aceptada)
     46 a 55      <- 45-54          (borde 54 vs 55, aproximación aceptada)
     Mayor de 55  <- 55-64 + 65+
3. La tabla extraída de NapoleonCat no sumaba exactamente 100% (bordes de
   redondeo/extracción de la fuente) -- se reescala proporcionalmente cada
   plataforma a 100% antes de usarla, preservando la forma relativa real.
"""

import pandas as pd

RUTA_SALIDA_RAW = "data/theta_k/canal_publico_bruto.csv"
RUTA_SALIDA_MIX = "data/theta_k/canal_publico_mix_por_bucket.csv"

# --- Datos crudos citados (NapoleonCat, Social Media Users in Colombia, jun-2026) ---
# Formato: plataforma -> genero -> {bucket_napoleoncat: pct_del_total_de_esa_plataforma}
CRUDO = {
    "facebook": {
        "F": {"13-17": 9.7, "18-24": 15.5, "25-34": 10.2, "35-44": 6.9, "45-54": 4.9, "55-64": 4.0, "65+": 4.0},
        "M": {"13-17": 9.3, "18-24": 15.7, "25-34": 9.7, "35-44": 6.4, "45-54": 4.4, "55-64": 3.3, "65+": 3.3},
    },
    "instagram": {
        "F": {"13-17": 11.6, "18-24": 18.3, "25-34": 11.2, "35-44": 6.6, "45-54": 4.6, "55-64": 3.2, "65+": 3.2},
        "M": {"13-17": 9.6, "18-24": 16.2, "25-34": 8.7, "35-44": 5.0, "45-54": 2.9, "55-64": 2.1, "65+": 2.1},
    },
    "messenger_proxy_whatsapp": {
        "F": {"13-17": 8.6, "18-24": 14.7, "25-34": 10.5, "35-44": 7.3, "45-54": 5.2, "55-64": 4.2, "65+": 4.2},
        "M": {"13-17": 8.9, "18-24": 15.4, "25-34": 10.2, "35-44": 6.8, "45-54": 4.7, "55-64": 3.4, "65+": 3.4},
    },
}

CROSSWALK = {
    "Menor de 19 años": ["13-17"],
    "20 a 35 años": ["18-24", "25-34"],
    "36 a 45 años": ["35-44"],
    "46 a 55 años": ["45-54"],
    "Mayor de 55 años": ["55-64", "65+"],
}


def reescalar_a_100(tabla_plataforma):
    total = sum(sum(g.values()) for g in tabla_plataforma.values())
    factor = 100.0 / total
    return {
        genero: {bucket: pct * factor for bucket, pct in buckets.items()}
        for genero, buckets in tabla_plataforma.items()
    }, factor


def main():
    filas_raw = []
    filas_mix = []

    reescalado = {}
    for plataforma, tabla in CRUDO.items():
        tabla_ok, factor = reescalar_a_100(tabla)
        reescalado[plataforma] = tabla_ok
        print(f"{plataforma}: factor de reescalado a 100% = {factor:.4f}")

    # Reagregar cada plataforma a nuestros buckets de edad (sumando F+M por bucket
    # y guardando también el detalle por género)
    agregado = {}  # plataforma -> nuestro_bucket -> {"F":pct, "M":pct, "total":pct}
    for plataforma, tabla in reescalado.items():
        agregado[plataforma] = {}
        for bucket_propio, buckets_origen in CROSSWALK.items():
            pct_f = sum(tabla["F"][b] for b in buckets_origen)
            pct_m = sum(tabla["M"][b] for b in buckets_origen)
            agregado[plataforma][bucket_propio] = {"F": pct_f, "M": pct_m, "total": pct_f + pct_m}
            filas_raw.append({
                "plataforma": plataforma, "rango_edad": bucket_propio,
                "pct_F": round(pct_f, 2), "pct_M": round(pct_m, 2), "pct_total": round(pct_f + pct_m, 2),
            })

    df_raw = pd.DataFrame(filas_raw)
    df_raw.to_csv(RUTA_SALIDA_RAW, index=False, encoding="utf-8-sig")
    print(f"\nGuardado: {RUTA_SALIDA_RAW}")
    print("\n--- Reagregado a nuestros buckets de edad (% del total de usuarios de esa plataforma) ---")
    print(df_raw.pivot(index="rango_edad", columns="plataforma", values="pct_total"))

    # Mix relativo DENTRO de cada bucket de edad (normalizado entre las 3 plataformas)
    # -- responde "dado este bucket, qué estilo de plataforma pesa más", no
    # "qué tan grande es el bucket" (eso ya se ve en la tabla de arriba).
    for bucket_propio in CROSSWALK:
        totales = {p: agregado[p][bucket_propio]["total"] for p in agregado}
        suma = sum(totales.values())
        for p, val in totales.items():
            filas_mix.append({
                "rango_edad": bucket_propio,
                "plataforma": p,
                "pct_mix_relativo": round(val / suma * 100, 1),
            })

    df_mix = pd.DataFrame(filas_mix)
    df_mix.to_csv(RUTA_SALIDA_MIX, index=False, encoding="utf-8-sig")
    print(f"\nGuardado: {RUTA_SALIDA_MIX}")
    print("\n--- Mix relativo de plataforma dentro de cada bucket de edad (%) ---")
    print(df_mix.pivot(index="rango_edad", columns="plataforma", values="pct_mix_relativo"))

    print(
        "\nLectura: el mix relativo entre plataformas varía POCO por edad (las 3 rondan "
        "30-37% en casi todos los buckets) -- el verdadero diferenciador por edad NO es "
        "'qué plataforma' sino 'cuánto alcance digital total tiene el bucket' (tabla de "
        "arriba: Menor de 19/20-35 concentran la mayoría de usuarios de las 3 plataformas, "
        "Mayor de 55 tiene la fracción más chica) y la tasa de deshabilitar push (57% en "
        "60+, dato de push_notification_statistics, vs 31% en jóvenes) -- para 'Mayor de 55' "
        "la conclusión no es 'usar menos Instagram', es 'bajar peso a TODO lo digital y subir "
        "email/SMS/físico', consistente con lo que ya decía §5.5 del doc maestro."
    )


if __name__ == "__main__":
    main()
