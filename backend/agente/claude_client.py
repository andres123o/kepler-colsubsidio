"""
Wrapper directo del SDK de Anthropic — sin framework, siguiendo la
recomendación del propio artículo de Anthropic ("Building Effective
Agents"): usar la API directamente, pocas líneas por llamada, fácil de
debuggear. Cada función es un paso independiente de la cadena.
"""

import json
import os
import re

from dotenv import load_dotenv
import anthropic

from . import prompts

load_dotenv()

MODELO = "claude-sonnet-4-6"
_cliente = None


def _get_cliente():
    global _cliente
    if _cliente is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta ANTHROPIC_API_KEY — ponla en un archivo .env en la raíz de colsubsidio/ "
                "(hay un .env.example de referencia). No se hardcodea la key en el código."
            )
        _cliente = anthropic.Anthropic(api_key=api_key)
    return _cliente


def _extraer_json(texto: str) -> dict:
    """Extrae el JSON de la respuesta — robusto a que Claude piense en voz alta
    antes de responder (contar caracteres, borrador, autochequeo), que es
    comportamiento esperado y sano, no un error del modelo. Busca, en este orden:
    1. El último bloque ```json ... ``` o ``` ... ``` del texto (el modelo pone
       la respuesta final al final, después de su razonamiento visible).
    2. Si no hay bloque de código, el último {...} balanceado del texto completo.
    """
    texto = texto.strip()

    bloques = re.findall(r"```(?:json)?\s*(.*?)```", texto, re.DOTALL)
    if bloques:
        return json.loads(bloques[-1].strip())

    # Sin fences — buscar el último {...} balanceado escaneando desde el final.
    fin = texto.rfind("}")
    while fin != -1:
        profundidad = 0
        for i in range(fin, -1, -1):
            if texto[i] == "}":
                profundidad += 1
            elif texto[i] == "{":
                profundidad -= 1
                if profundidad == 0:
                    try:
                        return json.loads(texto[i:fin + 1])
                    except json.JSONDecodeError:
                        break
        fin = texto.rfind("}", 0, fin)

    raise ValueError(f"No se encontró JSON válido en la respuesta. Texto crudo:\n{texto[:1000]}")


def _llamar(system, user, max_tokens=3000):
    cliente = _get_cliente()
    resp = cliente.messages.create(
        model=MODELO,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    texto = resp.content[0].text
    return _extraer_json(texto)


def analista_segmento(contexto: dict, contexto_actualidad: str = "No disponible.", perfil_segmento: str = "") -> dict:
    """Paso 1: lee las señales del segmento UNA vez (+ actualidad de Perplexity si hay), decide ángulos + estado mental."""
    fila_scorer = contexto["scorer"]
    fila_interes = contexto["interes"]
    fila_macro = contexto["macro"]
    fila_cal = contexto["calendario"]
    fila_canal = contexto["canal"]
    fila_estilo = contexto["estilo"]

    system = prompts.ANALISTA_SEGMENTO_SYSTEM.format(principios=prompts.PRINCIPIOS_ANTISESGO_ANTIGENERICO)
    user = prompts.ANALISTA_SEGMENTO_USER_TEMPLATE.format(
        contexto_actualidad=contexto_actualidad,
        perfil_segmento=perfil_segmento,
        kb=prompts.KB_CATALOGO,
        clase=contexto["clase"],
        producto=contexto["producto_solicitado"],
        interes_1=fila_interes.get("interes_1", ""),
        confianza=fila_interes.get("confianza", ""),
        razonamiento_interes=fila_interes.get("razonamiento", ""),
        rubro=fila_estilo.get("rubro_contenido_dominante", ""),
        tono=fila_estilo.get("tono_comunicacion", ""),
        formato=fila_estilo.get("formato_estilo_dominante", ""),
        sensibilidad_inflacion=fila_macro.get("sensibilidad_inflacion_index", ""),
        atractivo_compra_cartera=fila_macro.get("atractivo_compra_cartera", ""),
        pct_con_hijos=fila_cal.get("pct_con_hijos_probable", ""),
        relevancia_educativo=fila_cal.get("relevancia_educativo_timing", ""),
        relevancia_viajes=fila_cal.get("relevancia_viajes_timing", ""),
        accion_ventana_prima=fila_cal.get("accion_ventana_prima", ""),
        canal_recomendado=fila_canal.get("canal_recomendado", ""),
        elegible_libranza=fila_scorer.get("elegible_libranza", ""),
    )
    return _llamar(system, user)


def planificador_cadencia(analisis: dict, canal_recomendado: str, producto: str, relevancia_educativo: str = "", relevancia_viajes: str = "") -> dict:
    """Paso 2: reparte ángulos entre los 3 nodos fijos, sin repetir, y arma el resumen ejecutivo."""
    user = prompts.PLANIFICADOR_CADENCIA_USER_TEMPLATE.format(
        producto=producto,
        analisis_json=json.dumps(analisis, ensure_ascii=False, indent=2),
        canal_recomendado=canal_recomendado,
        relevancia_educativo=relevancia_educativo,
        relevancia_viajes=relevancia_viajes,
    )
    return _llamar(prompts.PLANIFICADOR_CADENCIA_SYSTEM, user)


def copywriter(nodos: list, producto: str, tono: str) -> list:
    """Paso 3: escribe el contenido de LOS 3 NODOS en una sola llamada (antes eran
    3 llamadas separadas — mismo patrón real de Trii: un copywriter, toda la
    campaña). Devuelve una lista de dicts {"dia":..., "copy":{...}}."""
    system = prompts.COPYWRITER_SYSTEM.format(
        principios=prompts.PRINCIPIOS_ANTISESGO_ANTIGENERICO,
        principios_enganche=prompts.PRINCIPIOS_ENGANCHE_CANAL,
    )
    user = prompts.COPYWRITER_USER_TEMPLATE.format(
        kb=prompts.KB_CATALOGO,
        producto=producto,
        tono=tono,
        nodos_json=json.dumps(nodos, ensure_ascii=False, indent=2),
    )
    resultado = _llamar(system, user, max_tokens=4000)
    return resultado["nodos"]


def humanizador(nodos_con_copy: list) -> list:
    """Paso 4: pule los 3 nodos en una sola llamada — nunca toca cifras/producto/CTA/formato."""
    system = prompts.HUMANIZER_SYSTEM.format(
        principios=prompts.PRINCIPIOS_ANTISESGO_ANTIGENERICO,
        principios_enganche=prompts.PRINCIPIOS_ENGANCHE_CANAL,
    )
    user = prompts.HUMANIZER_USER_TEMPLATE.format(
        nodos_json=json.dumps(nodos_con_copy, ensure_ascii=False, indent=2),
    )
    resultado = _llamar(system, user, max_tokens=4000)
    return resultado["nodos"]


def juez_calidad(nodos_completos: list, producto: str, tono: str) -> list:
    """L2: control de calidad por LLM (no reglas) para los 3 nodos en una sola
    llamada — revisa desviación de ángulo, tono, formato, y "olor a IA"."""
    user = prompts.JUEZ_CALIDAD_USER_TEMPLATE.format(
        producto=producto,
        tono=tono,
        nodos_json=json.dumps(nodos_completos, ensure_ascii=False, indent=2),
    )
    resultado = _llamar(prompts.JUEZ_CALIDAD_SYSTEM, user, max_tokens=4000)
    return resultado["veredictos"]
