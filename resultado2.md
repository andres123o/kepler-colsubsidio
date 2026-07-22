Canales confirmados

App "Mi Colsubsidio" (billetera móvil) — con push. La app incorporó mensajería push para notificaciones e integró funciones como descarga de certificados y cotización de seguros. Notifica actualizaciones, promociones y funcionalidades, permite consultar y pagar crédito de consumo e hipotecario, gestionar cupo de crédito, y actualizar datos de afiliación. Clave para ti: el afiliado puede actualizar su número de celular y correo electrónico desde la app → Colsubsidio tiene teléfono y email por afiliado, lo que habilita SMS/WhatsApp/email además de push. 
Colsubsidio + 2

WhatsApp Business API — confirmado, con bots nombrados. Operan al menos dos asesores virtuales: "Santiago", línea WhatsApp 312 404 3993, para actualización de datos y trámites de afiliados, y "Andrés", línea WhatsApp 310 217 6677, para proveedores. Múltiples números + bots con nombre propio = casi con certeza WhatsApp Business API vía un BSP (Business Solution Provider), no WhatsApp personal. 
Colsubsidio
Colsubsidio

Email transaccional/servicio. Correos de servicio al cliente diferenciados (servicioalcliente@colsubsidio.com y una cuenta separada para proveedores). Canal de email establecido. 
Colsubsidio

Contact center / IVR telefónico. Audio línea (601) 744 7525 y conmutador 742 0100 con menú de opciones y ruteo a asesor. Canal de voz con IVR. 
Colsubsidio
Colsubsidio

Portal transaccional web. transacciones.colsubsidio.com — superficie web autenticada.

Stack de inteligencia (lo que revela cómo procesan datos)

Señal de reclutamiento reveladora: Colsubsidio abrió un rol de "Analista de Datos de Mercadeo" que requiere Excel, SQL y Power BI. El analytics de mercadeo es SQL + Power BI (ecosistema Microsoft), orientado a reporting. No encontré evidencia pública de una CDP ni de un motor de orquestación de journeys (Salesforce Marketing Cloud, Braze, etc.) en Colsubsidio. Dato adyacente: en el ecosistema de cajas, Compensar sí aparece como cliente de Salesforce, Colsubsidio no. 
Colsubsidio

Lo que NO pude confirmar (marcado explícito)
Proveedor del WhatsApp Business API. No hay evidencia pública del BSP. Candidatos probables por presencia en Colombia/LATAM (inferencia, no confirmado): Infobip, Auronix, Yalo, Gupshup, Zenvia/Sinch, Twilio. Se confirmaría mirando los headers/metadata de los mensajes o preguntando en el hackathon.
CRM/CDP de marketing. Sin confirmación. La huella pública (Power BI/SQL) sugiere que la capa de orquestación inteligente puede ser un vacío real, no una plataforma ya instalada.
SMS. Probable (tienen el teléfono y contact center), pero sin confirmación directa de proveedor.
Implicación para dónde ejecuta Kepler

La superficie de ejecución existe y es rica: push (app) + WhatsApp API + email + IVR/voz + web, con teléfono y correo por afiliado. Lo que aparenta faltar es la capa de inteligencia/orquestación que decide qué mandar, a quién y cuándo — que es exactamente lo que Kepler aporta. El pitch encaja: no llegas a reemplazar sus tuberías de entrega (ya las tienen), llegas a poner el cerebro encima. WhatsApp + push son los dos canales de mayor alcance y menor fricción para el afiliado; ancla ahí la ejecución del sistema.

Si en el hackathon te dan acceso o contacto técnico, las dos preguntas que cierran este mapa son: quién es el BSP de WhatsApp, y si existe alguna CDP/orquestador o si hoy las campañas salen por scripts/SQL contra los canales.

---

## Complemento — mezcla de canales para el sistema (por qué SMS fuera, ads como 4º canal)

**SMS descartado, con evidencia, no por intuición.** En LatAm el costo por conversión de SMS es ~$20–73 USD vs. ~$1.04–1.39 USD en WhatsApp para un envío comparable — 20-50x menos eficiente. Colombia tiene 76-94% de penetración de WhatsApp (según fuente) y las tarifas de utility/authentication más baratas de la región ($0.0008/msg). Con Colsubsidio ya operando WhatsApp Business API con bots propios (Santiago, Andrés), SMS no aporta nada que WhatsApp no resuelva mejor y más barato. Contact center/IVR ya confirmado tampoco sustituye — es canal reactivo (inbound), no de campaña saliente.

**Restricción técnica real de WhatsApp que el diseño del agente debe respetar:** Meta exige plantillas pre-aprobadas por categoría (Marketing/Utility/Authentication) para iniciar conversación — no se puede generar texto libre en tiempo real como en email. Revisión de plantilla toma hasta 24h y para servicios financieros regulados exige ruta de escalamiento a humano si hay bot de por medio. Esto significa que el nodo de WhatsApp del sistema necesita una librería de plantillas pre-aprobadas por ángulo/etapa — no generación libre — mientras que email sí puede ser más flexible.

**Canal 4 (diferenciador, no núcleo): retargeting pagado vía Custom Audiences/Customer Match.** Para el segmento que no abre ni email/push/WhatsApp, la práctica de banca real es exportar el segmento con score a Meta Ads/Google Ads y pujar más alto por audiencias de alto LTV (3-5x el bid genérico en casos documentados). Esto no reemplaza los 3 canales propios, es la acción de respaldo que el agente puede elegir para el afiliado de baja apertura — y es el tipo de pieza que demuestra pensamiento de sistema completo frente al jurado, porque casi ningún equipo lo va a proponer.

**Conclusión de mezcla:** WhatsApp + push como canales primarios (mayor alcance, ya con infraestructura confirmada en Colsubsidio), email para contenido con más detalle/disclaimers legales, SMS fuera, ads de retargeting como canal de respaldo mencionado en el pitch aunque no se implemente a fondo en el MVP de 5 días.