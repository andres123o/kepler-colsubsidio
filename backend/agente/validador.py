"""
Gate L1 determinista — validación por reglas, sin LLM, entre pasos de la
cadena (el "gate" que recomienda el artículo de Anthropic para prompt
chaining). Mismo espíritu que copy_validator.py en Kepler/Trii, adaptado.

Alcance del L1 (corregido 24-jul-2026, decisión explícita del usuario):
SOLO cosas objetivas y medibles — límite de caracteres por canal, términos
legalmente prohibidos (DataCrédito), tope de cifras de monto, gate de
libranza. La puntuación (guion largo, comillas, etc.) y las buenas prácticas
de marketing (emojis, palabras de spam) NO viven acá — eso es cuestión de
buen criterio de escritura, y vive en el prompt del copywriter/humanizador
(agente/prompts.py, PRINCIPIOS_ENGANCHE_CANAL), no en un filtro que rechace
después. La razón: el usuario no quiere un ciclo de reintento que "arregle"
lo que el agente escribió mal — quiere que el agente razone bien desde el
primer intento. Un gate que bloquea sin reintento downstream no cumple
ninguna función más que registrar la alerta, así que para lo subjetivo no
vale la pena — para lo objetivo (caracteres) sí, porque ahí no hay duda de
si está bien o mal.
"""

import re

PROHIBIDO = ["datacrédito", "datacredito", "buró", "buro externo"]
PATRON_MONTO = re.compile(r"\$\s?[\d.,]+|(\bmillones?\b)")

# Límites reales por canal (benchmarks de industria, investigados 24-jul-2026)
LIMITES_CANAL = {
    # "cuerpo" faltaba acá — el formato de email SIEMPRE incluye cuerpo
    # (ver prompts.py: PRINCIPIOS_ENGANCHE_CANAL, formato exacto {"asunto",
    # "preheader", "cuerpo"}), así que cualquier email real quedaba marcado
    # como "campo que no aplica" sin razón. Rango basado en los mismos
    # cuerpos de email reales que ya usa el sistema (~90-220 caracteres).
    "email": {"asunto": (30, 50), "preheader": (30, 80), "cuerpo": (80, 220)},
    "push": {"titulo": (35, 50), "cuerpo": (80, 120)},
    "whatsapp": {"mensaje": (50, 160)},
}


def _validar_formato_canal(copy: dict, canal: str) -> list[str]:
    problemas = []
    limites = LIMITES_CANAL.get(canal)
    if limites is None:
        return [f"Canal desconocido: '{canal}' (debe ser whatsapp/push/email)"]

    for campo, (minimo, maximo) in limites.items():
        valor = copy.get(campo)
        if not valor:
            problemas.append(f"Falta el campo '{campo}', obligatorio para canal {canal}")
            continue
        largo = len(valor)
        if largo < minimo or largo > maximo:
            problemas.append(f"'{campo}' tiene {largo} caracteres, fuera del rango {minimo}-{maximo} para {canal}")

    # Campos de otro canal que no deberían estar (ej. 'asunto' en un push)
    campos_esperados = set(limites.keys())
    campos_extra = set(copy.keys()) - campos_esperados
    if campos_extra:
        problemas.append(f"Campos que no aplican al canal {canal}: {campos_extra}")

    return problemas


def validar_nodo(copy: dict, elegible_libranza: bool, producto: str, canal: str) -> list[str]:
    """Devuelve una lista de problemas encontrados — vacía si el nodo pasa.
    Solo criterios objetivos (ver docstring del módulo) — puntuación y buenas
    prácticas de marketing viven en el prompt del copywriter, no acá."""
    problemas = []
    texto_completo = " ".join(str(v) for v in copy.values()).lower()

    for palabra in PROHIBIDO:
        if palabra in texto_completo:
            problemas.append(f"Menciona término prohibido: '{palabra}'")

    montos_encontrados = PATRON_MONTO.findall(texto_completo)
    if len(montos_encontrados) > 1:
        problemas.append(f"Más de una cifra de monto en el mismo nodo: {montos_encontrados}")

    if producto == "Libre_inversion" and not elegible_libranza:
        problemas.append("Se generó copy de Libre Inversión para un segmento NO elegible para libranza — bloqueado")

    problemas.extend(_validar_formato_canal(copy, canal))

    return problemas
