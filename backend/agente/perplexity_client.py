"""
Investigación de actualidad vía la API de BÚSQUEDA de Perplexity
(https://api.perplexity.ai/search) — NO chat completions. Devuelve
resultados reales (título, snippet, url, fecha) que el analista_segmento
lee y decide si son útiles — nunca se sintetiza una respuesta artificial
acá, el paso 1 de la cadena hace ese trabajo con el modelo completo.

Mismo propósito que perplexity_client.py de Kepler/Trii, pero endpoint,
query y prompts propios de Colsubsidio (instancias independientes).
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

URL_API = "https://api.perplexity.ai/search"


def investigar_actualidad(rubro: str, fecha_referencia: str, perfil_segmento: str) -> dict:
    """rubro: el rubro de contenido dominante del segmento (ej. 'Viajes').
    perfil_segmento: descripción REAL de quién es esta gente — se usa para construir
    una query específica, no un tema genérico.
    fecha_referencia: fecha actual en texto, para anclar la búsqueda a "esta semana"."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "disponible": False,
            "motivo": "Falta PERPLEXITY_API_KEY en .env — se sigue sin este contexto adicional, no bloquea el resto de la cadena.",
        }

    query = f"Colombia {fecha_referencia} {rubro} noticias eventos calendario relevante para {perfil_segmento}"

    try:
        with httpx.Client(timeout=30) as cliente:
            resp = cliente.post(
                URL_API,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"query": query, "max_results": 3, "max_tokens_per_page": 256},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {"disponible": False, "motivo": f"Error consultando Perplexity: {e}"}

    resultados = data.get("results", [])
    if not resultados:
        return {"disponible": False, "motivo": "Perplexity no devolvió resultados para esta búsqueda."}

    resumen = "\n\n".join(
        f"- [{r.get('title', 'sin título')}] ({r.get('date') or r.get('last_updated', 'sin fecha')}): "
        f"{r.get('snippet', '')[:300]}"
        for r in resultados
    )
    return {"disponible": True, "resumen": resumen, "fuentes": [r.get("url") for r in resultados]}
