"""
Edición de la KB del agente — en producción esto viviría en una tabla
(como funnel_prompts en Kepler/Trii), acá son 3 archivos de texto porque es
un demo (ver agente/prompts.py, _cargar_archivo_kb).
"""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agente.prompts import DIR_KB, ARCHIVOS_KB

router = APIRouter(prefix="/api/kb", tags=["kb"])


class KBActualizar(BaseModel):
    clave: str
    contenido: str


@router.get("")
def leer_kb():
    resultado = {}
    for clave, nombre_archivo in ARCHIVOS_KB.items():
        ruta = os.path.join(DIR_KB, nombre_archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                resultado[clave] = f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"No existe el archivo de KB '{nombre_archivo}'")
    return resultado


@router.put("")
def actualizar_kb(payload: KBActualizar):
    if payload.clave not in ARCHIVOS_KB:
        raise HTTPException(status_code=400, detail=f"Clave desconocida: {payload.clave}")

    ruta = os.path.join(DIR_KB, ARCHIVOS_KB[payload.clave])
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(payload.contenido)
    return {"ok": True}
