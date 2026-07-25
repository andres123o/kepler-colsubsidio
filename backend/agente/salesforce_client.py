"""
Cliente real de Salesforce Marketing Cloud (Journey Builder REST API),
investigado contra la documentación oficial de Salesforce Developers
("Fire an Entry Event", Marketing Cloud Engagement APIs). Colsubsidio
todavía no entregó credenciales reales, así que disparar_evento_journey()
devuelve una respuesta simulada, pero con la MISMA forma que devolvería la
API real, para que conectar el sistema real después sea prender la llamada
HTTP comentada abajo, sin tocar la interfaz de esta función (mismo principio
que ya usa salesforce_simulado.py).

Referencia real:
- Token (OAuth2, client credentials): POST
  https://{subdominio}.auth.marketingcloudapis.com/v2/token
  body: {"grant_type": "client_credentials", "client_id": ..., "client_secret": ...}
  -> {"access_token": ..., "token_type": "Bearer", "expires_in": 1199}
- Disparar evento de entrada de un Journey: POST
  https://{subdominio}.rest.marketingcloudapis.com/interaction/v1/events
  body: {"contactKey": ..., "eventDefinitionKey": ..., "data": {...}}
  -> 201 {"eventInstanceId": "..."} si el evento existe y el contacto está activo
  -> 400 si la eventDefinitionKey no existe o el contacto no está activo

Variables de entorno que se necesitan cuando Colsubsidio entregue las
credenciales reales (hoy no están seteadas, por eso siempre simula):
SFMC_SUBDOMINIO, SFMC_CLIENT_ID, SFMC_CLIENT_SECRET, SFMC_EVENT_DEFINITION_KEY.
"""

import datetime
import os
import uuid

SFMC_SUBDOMINIO = os.environ.get("SFMC_SUBDOMINIO", "")
SFMC_CLIENT_ID = os.environ.get("SFMC_CLIENT_ID", "")
SFMC_CLIENT_SECRET = os.environ.get("SFMC_CLIENT_SECRET", "")
SFMC_EVENT_DEFINITION_KEY = os.environ.get("SFMC_EVENT_DEFINITION_KEY", "APIEvent-Colsubsidio-Campanas")

_URL_TOKEN = "https://{sub}.auth.marketingcloudapis.com/v2/token"
_URL_EVENTO = "https://{sub}.rest.marketingcloudapis.com/interaction/v1/events"


def _credenciales_configuradas() -> bool:
    return bool(SFMC_SUBDOMINIO and SFMC_CLIENT_ID and SFMC_CLIENT_SECRET)


def construir_evento_journey(contact_key: str, data: dict) -> dict:
    """Forma real del payload que espera /interaction/v1/events."""
    return {
        "contactKey": contact_key,
        "eventDefinitionKey": SFMC_EVENT_DEFINITION_KEY,
        "data": data,
    }


def disparar_evento_journey(contact_key: str, data: dict) -> dict:
    """Dispara el evento de entrada del Journey para este contacto (acá,
    un segmento). Con credenciales reales configuradas haría la llamada
    real; hoy siempre simula, devolviendo la misma forma de respuesta."""
    payload = construir_evento_journey(contact_key, data)

    if _credenciales_configuradas():
        # Llamada real — queda comentada porque todavía no hay credenciales
        # de Colsubsidio para probarla. El resto del sistema no cambia cuando
        # esto se active: la función sigue devolviendo el mismo dict.
        #
        # token_resp = requests.post(_URL_TOKEN.format(sub=SFMC_SUBDOMINIO), json={
        #     "grant_type": "client_credentials",
        #     "client_id": SFMC_CLIENT_ID,
        #     "client_secret": SFMC_CLIENT_SECRET,
        # })
        # token_resp.raise_for_status()
        # access_token = token_resp.json()["access_token"]
        #
        # resp = requests.post(
        #     _URL_EVENTO.format(sub=SFMC_SUBDOMINIO),
        #     headers={"Authorization": f"Bearer {access_token}"},
        #     json=payload,
        # )
        # resp.raise_for_status()
        # return resp.json()
        pass

    return {
        "eventInstanceId": str(uuid.uuid4()),
        "statusCode": 201,
        "simulado": True,
        "payload_enviado": payload,
        "recibido_en": datetime.datetime.utcnow().isoformat() + "Z",
    }
