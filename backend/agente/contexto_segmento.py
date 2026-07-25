"""
Arma el contexto completo de UN segmento (una de las 12 clases de LCA),
juntando las tablas que ya construyó Frente B — no calcula nada nuevo, solo
organiza lo que ya existe en un solo diccionario, listo para pasarle al
primer paso del agente (analista_segmento).
"""

import datetime
import json
import re

import pandas as pd

RUTA_SCORER = "data/theta_k/scorer_resultado_por_clase.csv"
RUTA_INTERES = "data/theta_k/theta_k_vector_interes.csv"
RUTA_MACRO = "data/theta_k/theta_k_sensibilidad_macro.csv"
RUTA_CALENDARIO = "data/theta_k/theta_k_demanda_calendario.csv"
RUTA_CANAL = "data/theta_k/theta_k_canal.csv"
RUTA_ESTILO = "data/theta_k/theta_k_estilo_comunicacion.csv"
RUTA_PERFIL_DEMOGRAFICO = "data/theta_k/clases_perfil_demografico.csv"

_CACHE = None


def _cargar():
    global _CACHE
    if _CACHE is None:
        _CACHE = {
            "scorer": pd.read_csv(RUTA_SCORER, encoding="utf-8-sig"),
            "interes": pd.read_csv(RUTA_INTERES, encoding="utf-8-sig"),
            "macro": pd.read_csv(RUTA_MACRO, encoding="utf-8-sig"),
            "calendario": pd.read_csv(RUTA_CALENDARIO, encoding="utf-8-sig"),
            "canal": pd.read_csv(RUTA_CANAL, encoding="utf-8-sig"),
            "estilo": pd.read_csv(RUTA_ESTILO, encoding="utf-8-sig"),
            "perfil_demografico": pd.read_csv(RUTA_PERFIL_DEMOGRAFICO, encoding="utf-8-sig"),
        }
    return _CACHE


# Traduce/normaliza un valor crudo de columna (mayúsculas fijas, guion bajo
# como separador, "/" o guion largo/doble como separador de conceptos,
# códigos cortos como GENERO=F/M) a texto natural — nunca mostrarle a un
# humano el dato tal cual sale del CSV (encontrado real: "AFILLIADO SIN
# GRUPO_FAMILIAR" y "F"/"M" sueltos no se entendían en la interfaz).
_ETIQUETAS_LEGIBLES = {"F": "Mujeres", "M": "Hombres"}


def texto_visible(valor: str) -> str:
    directo = _ETIQUETAS_LEGIBLES.get(valor)
    if directo:
        return directo
    texto = valor.replace("_", " ")
    texto = re.sub(r"\s*/\s*", " y ", texto)
    texto = re.sub(r"\s*(--|—)\s*", ", ", texto)
    if texto.isupper():
        texto = texto.capitalize()
    return texto.replace("Afilliado", "Afiliado")


def descripcion_legible_segmento(clase: int) -> str:
    """Arma una descripción corta y REAL de quién es esta gente (edad, género,
    categoría, situación familiar dominantes) — para que Perplexity y el
    analista busquen/razonen sobre personas concretas, no un tema genérico."""
    d = _cargar()
    perfil = d["perfil_demografico"]
    perfil = perfil[perfil["clase"] == clase]

    def top_categoria(variable, n=1):
        sub = perfil[perfil["variable"] == variable].nlargest(n, "pct")
        return [(r["categoria"], round(r["pct"], 1)) for _, r in sub.iterrows()]

    edad = top_categoria("RANGO_EDAD")
    genero = top_categoria("GENERO")
    categoria_ingreso = top_categoria("CATEGORIA")
    familia = top_categoria("SEGMENTO_GRUPO_FAMILIAR")

    partes = []
    if genero:
        partes.append(f"{texto_visible(genero[0][0])} ({genero[0][1]}%)")
    if edad:
        partes.append(f"{edad[0][0]} ({edad[0][1]}%)")
    if categoria_ingreso:
        partes.append(f"Categoría {categoria_ingreso[0][0]} ({categoria_ingreso[0][1]}%)")
    if familia:
        partes.append(f"{texto_visible(familia[0][0])} ({familia[0][1]}%)")

    return ", ".join(partes)


def segmentos_elegibles_para(producto: str) -> list[int]:
    """Filtra qué clases tienen señal real (score > 0) para el producto pedido,
    leyendo la columna 'productos_top' del scorer — formato "Producto(score) > ..."."""
    d = _cargar()
    clases = []
    for _, fila in d["scorer"].iterrows():
        if producto in str(fila["productos_top"]):
            clases.append(int(fila["clase"]))
    return clases


_TAMANO_CLASES = None
# El tamaño real por clase (dominante por probabilidad máxima, sobre las
# 1.56M filas reales) se precalculó UNA vez y se guardó acá — antes esta
# función cargaba el pickle completo de probabilidades por afiliado
# (`lca_pi.pkl`, ~157MB) solo para sacar 12 números. Ese archivo nunca debe
# subirse al repo/desplegarse (GitHub rechaza archivos de más de 100MB, y
# Vercel tiene su propio límite de tamaño de función) — nunca se vuelve a
# necesitar el pickle completo en producción, solo para regenerar este JSON
# si el modelo LCA se reentrena (ver segmentacion/03b_ajuste_final.py).
_RUTA_TAMANO_CLASES = "data/processed/tamano_clases.json"


def _tamano_clases() -> dict:
    """Cuántos afiliados reales caen en cada clase (dominante por probabilidad
    máxima) — calculado una sola vez sobre las 1.56M filas reales, no una
    estimación. Sirve para traducir 'n segmentos' a 'n afiliados reales' en
    cualquier lugar de cara al usuario — 'segmento'/'clase' es una etiqueta
    interna nuestra, nunca debe mostrarse tal cual (misma regla que ya rige el
    copy del agente, agente/prompts.py)."""
    global _TAMANO_CLASES
    if _TAMANO_CLASES is None:
        with open(_RUTA_TAMANO_CLASES, "r", encoding="utf-8") as f:
            _TAMANO_CLASES = {int(clase): n for clase, n in json.load(f).items()}
    return _TAMANO_CLASES


def afiliados_reales_para(producto: str, segmentos: list[int] | None = None) -> int:
    """Suma de afiliados reales en las clases elegibles para este producto —
    el número que se le muestra al usuario, nunca 'n segmentos'. Si el
    caller ya calculó la lista de segmentos elegibles (ej. productos.py, que
    también necesita el conteo para n_segmentos), se le puede pasar acá para
    no recorrer dos veces la tabla scorer por el mismo producto."""
    tamanos = _tamano_clases()
    if segmentos is None:
        segmentos = segmentos_elegibles_para(producto)
    return sum(tamanos.get(clase, 0) for clase in segmentos)


# Fechas reales verificadas (Ministerio de Educación Nacional / Secretaría de
# Educación de Bogotá, Resolución 2433 del 27-oct-2025, vía Noticias
# Caracol/El Tiempo/Infobae, julio 2026): último día de actividades
# académicas y graduaciones de grado 11 el 27 de noviembre; vacaciones de fin
# de año inician el 30 de noviembre; el año lectivo 2027 arranca el 26 de
# enero. Nunca una fecha estimada — ver feedback_no_datos_estimados de este
# mismo proyecto: si hay fuente real barata de conseguir, se usa esa, no un
# cálculo a ojo.
_TEMPORADAS = [
    {
        "nombre": "las graduaciones de grado 11",
        "fecha": datetime.date(2026, 11, 27),
        # Fijo, no derivado del vector de interés: un bachiller que se
        # gradúa y su familia piensan en educación (universidad/técnico), no
        # en el interés dominante de su clase LCA — nunca otro producto.
        "producto_fijo": "Educativo",
    },
    {"nombre": "las vacaciones de fin de año", "fecha": datetime.date(2026, 11, 30), "columna": "relevancia_viajes_timing"},
    {"nombre": "el regreso a clases", "fecha": datetime.date(2027, 1, 26), "columna": "relevancia_educativo_timing"},
]

# Relevancia_educativo_timing (usada por "el regreso a clases") es
# específicamente la ventana de MATRÍCULA (prompts.py: "87% de los momentos
# de matrícula de enero"), no de grados/graduaciones — por eso "las
# graduaciones de grado 11" es una temporada aparte, con su propia fecha real
# y sin depender de esa columna.

# Mapeo real interés dominante -> producto del catálogo (5 productos con
# señal real del scorer). No es un modelo, es el mismo vínculo que ya usa el
# copy real del sistema (ej. Libre Inversión ya se redacta como "viajes,
# salud, vivienda", ver kb/productos.txt).
_INTERES_A_PRODUCTO = {
    "Día a día / rotativo": "Rotativo_cupo",
    "Rotativo / flujo de caja": "Rotativo_cupo",
    "Tecnología / entretenimiento": "Libre_inversion",
    "Consolidación de deudas": "Compra_cartera",
    "Vivienda / libre inversión aspiracional": "Libre_inversion",
    "Viajes": "Libre_inversion",
    "Educación de los hijos": "Educativo",
    "Salud": "Libre_inversion",
}
# Catálogo canónico slug -> nombre visible (única fuente — app/core/config.py
# reexporta esto mismo como PRODUCTOS, en vez de mantener su propia copia;
# antes había 2 copias en el backend que ya habían empezado a divergir del
# tercer mapa que tenía CampanaCanvas.tsx en el frontend).
PRODUCTOS_CATALOGO = [
    {"slug": "Hipotecario", "nombre": "Crédito Hipotecario"},
    {"slug": "Libre_inversion", "nombre": "Libre Inversión"},
    {"slug": "Educativo", "nombre": "Crédito Educativo"},
    {"slug": "Rotativo_cupo", "nombre": "Rotativo (cupo)"},
    {"slug": "Compra_cartera", "nombre": "Compra de Cartera"},
]
_NOMBRE_PRODUCTO = {p["slug"]: p["nombre"] for p in PRODUCTOS_CATALOGO}


def proxima_temporada_relevante() -> dict:
    """Próxima temporada real del calendario colombiano + qué producto real
    del catálogo conviene preparar para ella — mismo dato de calendario que
    ya usa el pipeline (contexto_de_clase), traducido acá a una acción
    concreta ("prepara esta campaña"), no una etiqueta de interés abstracta.
    Sugerencia proactiva para el equipo, no para el afiliado."""
    d = _cargar()
    hoy = datetime.date.today()
    futuras = [t for t in _TEMPORADAS if t["fecha"] >= hoy]
    if not futuras:
        return {"disponible": False}

    proxima = min(futuras, key=lambda t: t["fecha"])

    if "producto_fijo" in proxima:
        # Temporada con vínculo directo al producto (ej. graduaciones ->
        # crédito educativo) — no se deriva del interés dominante de cada
        # clase, siempre es ese producto.
        intereses = []
        productos_vistos = [proxima["producto_fijo"]]
    else:
        calendario = d["calendario"]
        estilo = d["estilo"]
        clases_relevantes = calendario[calendario[proxima["columna"]] == "alta"]["clase"].tolist()
        intereses = estilo[estilo["clase"].isin(clases_relevantes)]["rubro_contenido_dominante"].dropna().unique().tolist()

        productos_vistos = []
        for interes in intereses:
            slug = _INTERES_A_PRODUCTO.get(interes)
            if slug and slug not in productos_vistos:
                productos_vistos.append(slug)

    return {
        "disponible": True,
        "temporada": proxima["nombre"],
        "fecha": proxima["fecha"].isoformat(),
        "dias_faltantes": (proxima["fecha"] - hoy).days,
        "intereses_relevantes": intereses,
        "productos_sugeridos": [{"slug": s, "nombre": _NOMBRE_PRODUCTO.get(s, s)} for s in productos_vistos],
    }


def contexto_de_clase(clase: int, producto: str) -> dict:
    """Devuelve el contexto completo de una clase para un producto específico —
    esto es lo que consume el paso 1 del agente (analista_segmento)."""
    d = _cargar()

    def fila(tabla):
        sub = d[tabla][d[tabla]["clase"] == clase]
        return sub.iloc[0].to_dict() if len(sub) else {}

    return {
        "clase": clase,
        "producto_solicitado": producto,
        "scorer": fila("scorer"),
        "interes": fila("interes"),
        "macro": fila("macro"),
        "calendario": fila("calendario"),
        "canal": fila("canal"),
        "estilo": fila("estilo"),
    }
