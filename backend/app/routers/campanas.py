"""
Endpoint SSE: el orquestador corre en un thread de fondo (ThreadPoolExecutor
por dentro, uno por segmento) y va empujando eventos de progreso reales a una
cola (EmisorEventos) mientras el generador de acá los transforma a formato
Server-Sent Events para el frontend. GET (no POST) para poder consumirlo con
EventSource nativo del navegador — el payload es solo un slug de producto.
"""

import json
import threading

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.eventos import EmisorEventos
from agente.orquestador import lanzar_campana_por_producto
from agente import salesforce_simulado

router = APIRouter(prefix="/api/campanas", tags=["campanas"])


def _formatear_sse(evento: dict) -> str:
    return f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"


@router.get("/procesar")
def procesar(producto: str):
    emisor = EmisorEventos()

    def _correr():
        try:
            resultados = lanzar_campana_por_producto(producto, emisor=emisor)
            emisor.emitir("completado", resultados=resultados)
        except Exception as e:
            emisor.emitir("error", mensaje=str(e))
        finally:
            emisor.cerrar()

    threading.Thread(target=_correr, daemon=True).start()

    def _stream():
        for evento in emisor.eventos():
            yield _formatear_sse(evento)

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/enviar")
def enviar(clase: int, producto: str):
    """Confirmación humana explícita — generar la campaña nunca la envía sola
    (ver salesforce_simulado.crear_campana). Solo acá queda 'enviada'."""
    return salesforce_simulado.marcar_enviada(clase, producto)
