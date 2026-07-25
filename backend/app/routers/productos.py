from fastapi import APIRouter

from app.core.config import PRODUCTOS
from agente.contexto_segmento import segmentos_elegibles_para, afiliados_reales_para

router = APIRouter(prefix="/api/productos", tags=["productos"])


@router.get("")
def listar_productos():
    """n_afiliados es un número real (conteo del modelo LCA sobre las 1.56M
    filas, no una estimación) — se muestra al usuario en vez de 'n
    segmentos', que es una etiqueta interna nuestra. n_segmentos se mantiene
    solo para uso interno (limitar cuántas clases procesa el demo)."""
    productos = []
    for p in PRODUCTOS:
        segmentos = segmentos_elegibles_para(p["slug"])
        productos.append({
            **p,
            "n_segmentos": len(segmentos),
            "n_afiliados": afiliados_reales_para(p["slug"], segmentos),
        })
    return {"productos": productos}
