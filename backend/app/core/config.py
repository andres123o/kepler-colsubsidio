import os

# El login real vive en el frontend (Server Action de Next.js,
# frontend/app/login/actions.ts) — este backend no lo llama nunca, así que no
# duplicamos credenciales/cookie de auth acá (antes había un router
# /api/auth completo que nadie invocaba).

from agente.contexto_segmento import PRODUCTOS_CATALOGO

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

# Solo los 5 productos que el motor (motor/scorer_persona.py) puede asignar
# realmente como top-producto de un segmento — el catálogo completo tiene 7
# líneas (agente/kb/productos.txt), pero "Rotativo_seguros_impuestos" y
# "Consumo_general" son contexto informativo para el copy, nunca una salida
# del scorer, así que no se ofrecen acá (elegirlos no devolvería segmentos).
# Fuente única: agente/contexto_segmento.py (el motor ya necesita este mismo
# catálogo internamente, así que vive ahí, no acá).
PRODUCTOS = PRODUCTOS_CATALOGO
