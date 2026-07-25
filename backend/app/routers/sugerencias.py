from fastapi import APIRouter

from agente.contexto_segmento import proxima_temporada_relevante

router = APIRouter(prefix="/api/sugerencias", tags=["sugerencias"])


@router.get("/proxima-temporada")
def proxima_temporada():
    """Sugerencia proactiva para el equipo (no para el afiliado) — próxima
    temporada real del calendario colombiano + a qué intereses les sube la
    relevancia, usando el mismo dato de calendario que ya consume el
    pipeline. Hoy se muestra en el dashboard; en el pitch se explica como el
    dato que alimentaría una alerta real hacia el canal de comunicación
    interna del equipo (ej. Slack)."""
    return proxima_temporada_relevante()
