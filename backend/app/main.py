"""
API de Colsubsidio (Reto 1 — Crédito Hiperpersonalizado). Sirve de puente
entre el frontend (Next.js) y el motor/agente ya validado en agente/.

Correr desde backend/, con el venv activo:
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_ORIGIN
from app.routers import productos, campanas, kb, sugerencias

app = FastAPI(title="Colsubsidio — Crédito Hiperpersonalizado")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(productos.router)
app.include_router(campanas.router)
app.include_router(kb.router)
app.include_router(sugerencias.router)


@app.get("/api/health")
def health():
    return {"ok": True}
