"""
Simulación de Salesforce Marketing Cloud para el demo — NO hay conexión
real (no tenemos credenciales de Colsubsidio). Simula exactamente el
mecanismo real que investigamos: escribir atributos en una "Data Extension"
(acá un JSON local) y crear una "campaña" (journey de 3 nodos) filtrada por
esos atributos.

En producción real esto se reemplaza por llamadas reales a la API de
Salesforce Marketing Cloud (REST API, Journey Builder) — la interfaz de
estas funciones (escribir_atributos_segmento / crear_campana) no cambiaría,
solo la implementación interna.
"""

import json
import os
import threading

from . import salesforce_client

RUTA_DATA_EXTENSION = "data/salesforce_simulado_data_extension.json"
RUTA_CAMPANAS = "data/salesforce_simulado_campanas.json"

# El orquestador corre segmentos en paralelo (ThreadPoolExecutor) — sin este
# lock, dos threads podrían leer-modificar-escribir el mismo JSON a la vez y
# uno se pisaría al otro (perdería la campaña que el otro thread ya guardó).
_LOCK = threading.Lock()


def _leer_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _escribir_json(ruta, data):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def escribir_atributos_segmento(clase: int, producto: str, contexto: dict):
    """Simula escribir/actualizar columnas en la Data Extension — por SEGMENTO,
    no por persona (eso ya lo probamos aparte con motor/scorer_persona.py)."""
    with _LOCK:
        data = _leer_json(RUTA_DATA_EXTENSION)
        data[str(clase)] = {
            "clase": clase,
            "producto_top1": producto,
            "rubro": contexto["estilo"].get("rubro_contenido_dominante"),
            "tono": contexto["estilo"].get("tono_comunicacion"),
            "canal_recomendado": contexto["canal"].get("canal_recomendado"),
            "elegible_libranza": contexto["scorer"].get("elegible_libranza"),
        }
        _escribir_json(RUTA_DATA_EXTENSION, data)


def crear_campana(clase: int, producto: str, nodos_con_copy: list):
    """Simula crear el journey de 3 nodos filtrado por atributo (clase, producto).
    Se crea como BORRADOR — generar la campaña (lectura/análisis) nunca implica
    enviarla (escritura real hacia el afiliado); eso requiere una confirmación
    humana explícita vía marcar_enviada() (patrón "human-in-the-loop en
    escrituras", mismo que ya usa el agente premium de Trii: preview primero,
    ejecución solo tras aprobación)."""
    with _LOCK:
        campanas = _leer_json(RUTA_CAMPANAS)
        campanas[f"clase_{clase}_{producto}"] = {
            "filtro_atributo": {"segmento": clase, "producto_top1": producto},
            "nodos": nodos_con_copy,
            "estado_envio": "borrador",
            "enviada_en": None,
        }
        _escribir_json(RUTA_CAMPANAS, campanas)
        return campanas[f"clase_{clase}_{producto}"]


def marcar_enviada(clase: int, producto: str) -> dict:
    """Confirmación humana explícita: recién acá se considera 'enviada' la
    campaña (nunca automático al generarla). Dispara el evento real de entrada
    del Journey (salesforce_client.disparar_evento_journey) — hoy simulado,
    con la misma forma que devolvería la API real, y guarda esa respuesta."""
    with _LOCK:
        campanas = _leer_json(RUTA_CAMPANAS)
        clave = f"clase_{clase}_{producto}"
        if clave not in campanas:
            raise KeyError(f"No existe una campaña generada para {clave}")

        respuesta = salesforce_client.disparar_evento_journey(
            contact_key=f"segmento_{clase}",
            data={"producto_top1": producto, "clase": clase},
        )

        campanas[clave]["estado_envio"] = "enviada"
        campanas[clave]["enviada_en"] = respuesta["recibido_en"]
        campanas[clave]["respuesta_sfmc"] = respuesta
        _escribir_json(RUTA_CAMPANAS, campanas)
        return campanas[clave]
