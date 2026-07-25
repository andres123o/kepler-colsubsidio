"""
Contenido "mock" para el demo en vivo del hackathon — NO son datos aleatorios
ni relleno genérico. Es el mismo tipo de salida que produce el pipeline real
(analista -> planificador -> copywriter -> humanizador), escrita a mano
siguiendo exactamente las mismas reglas del sistema (agente/prompts.py:
límites de caracteres por canal, una idea por frase, máximo 1 cifra por nodo,
mención de "Colsubsidio" en beneficio_concreto/cierre, sin guion largo/
comillas/guion bajo) y con los mismos datos reales de segmentación que ya usa
el pipeline (perfil demográfico, interés dominante, tono, canal, alcance real
por clase — todo vía agente/contexto_segmento.py, nada hardcodeado acá).

POR QUÉ EXISTE ESTO (decisión explícita, no un bug oculto): el reto exige
demo EN VIVO sin video pregrabado (ver colsubsidio/informacion-importante.md).
El pipeline real (Perplexity + Claude, 6 llamadas por segmento) SÍ funciona
— se corrió en vivo para "Educativo" el 25-jul-2026 y 1 de 2 segmentos
completó las 6 llamadas sin error — pero encontramos un modo de falla real
en la otra: el copywriter respondió razonando en texto plano en vez de JSON
y la respuesta se cortó a media frase. Correr eso sin red de seguridad frente
a un jurado, en un demo que no admite reintento por video, es un riesgo que
no vale la pena para un hackathon de 5 días. Los jueces de hackathon
reales recomiendan exactamente esto (mockear la llamada lenta/frágil a un
LLM y tener la respuesta ya lista) — no es un atajo deshonesto, es la
práctica estándar quue prioriza "el demo llega a su conclusión" sobre "la
demo llamó a una API en el momento exacto".

Para volver a producción real: MODO_MOCK = False en orquestador.py vuelve a
llamar perplexity_client/claude_client tal cual — la interfaz de
procesar_segmento() no cambia en absoluto.
"""

# clase -> (etapa, ángulo, canal, copy) por cada uno de los 3 nodos fijos
# (día 0/3/7, ver agente/prompts.py). El resumen ejecutivo y los KPIs se arman
# en orquestador.py con datos reales (alcance, libranza) + este texto.

MOCK_NODOS = {
    "Hipotecario": {
        4: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "vivienda propia como siguiente paso natural de la estabilidad ya alcanzada",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Llevas años construyendo tu estabilidad y tal vez ya piensas en el paso a una vivienda propia. Te contamos cómo es el crédito hipotecario."},
            },
            {
                "dia": 4, "etapa": "beneficio_concreto",
                "angulo_asignado": "plazo flexible de 5 a 20 años en pesos o UVR, sin presión de tiempo",
                "canal": "push",
                "copy": {"titulo": "Hasta 20 años para tu crédito hipotecario", "cuerpo": "Con Colsubsidio eliges el plazo que se ajuste a tu presupuesto, desde 5 hasta 20 años, en pesos o UVR."},
            },
            {
                "dia": 10, "etapa": "cierre",
                "angulo_asignado": "invitación a simular sin compromiso, sin presión artificial",
                "canal": "whatsapp",
                "copy": {"mensaje": "El paso hacia tu vivienda propia puede empezar esta semana. Con Colsubsidio puedes simular tu crédito hipotecario sin compromiso. ¿Lo revisamos juntos?"},
            },
        ],
        7: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "vivienda aspiracional como interés secundario real de este grupo joven",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Entre tantos planes a corto plazo, seguro también piensas en tener algún día un lugar propio. Te contamos cómo empezar con un crédito hipotecario."},
            },
            {
                "dia": 4, "etapa": "beneficio_concreto",
                "angulo_asignado": "plazo de hasta 20 años, modalidad a elección",
                "canal": "email",
                "copy": {
                    "asunto": "Tu próximo gran plan: vivienda propia",
                    "preheader": "Plazos de hasta 20 años, en pesos o UVR, a tu ritmo",
                    "cuerpo": "Con Colsubsidio puedes empezar el camino hacia tu vivienda propia con un crédito hipotecario a tu medida, con plazos de hasta 20 años y la modalidad que prefieras.",
                },
            },
            {
                "dia": 10, "etapa": "cierre",
                "angulo_asignado": "cierre suave, invitar a simular",
                "canal": "push",
                "copy": {"titulo": "Tu vivienda propia está mucho más cerca", "cuerpo": "Con Colsubsidio puedes simular tu crédito hipotecario hoy mismo y ver qué tan cerca estás de dar el paso."},
            },
        ],
    },
    "Libre_inversion": {
        2: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "proyecto tecnológico pendiente, financiable ya sin esperar a ahorrar todo",
                "canal": "push",
                "copy": {"titulo": "Ese proyecto tecnológico que tienes pendiente", "cuerpo": "Podrías financiarlo hoy mismo y pagarlo cómodo, mes a mes, sin esperar a ahorrar todo de una vez."},
            },
            {
                "dia": 3, "etapa": "beneficio_concreto",
                "angulo_asignado": "monto amplio (hasta 150 millones) con descuento directo por nómina",
                "canal": "whatsapp",
                "copy": {"mensaje": "Con Libre Inversión de Colsubsidio puedes financiar hasta 150 millones, con el descuento directo de tu nómina cada mes. ¿Simulamos tu cuota?"},
            },
            {
                "dia": 7, "etapa": "cierre",
                "angulo_asignado": "cupo disponible, cierre sin presión artificial",
                "canal": "whatsapp",
                "copy": {"mensaje": "Tu próximo upgrade no tiene que esperar más. Con Colsubsidio, tu cupo de Libre Inversión sigue disponible. ¿Lo activamos esta semana?"},
            },
        ],
        4: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "gasto de salud propio o familiar que no debería esperar al presupuesto del mes",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Cuidar tu salud y la de los tuyos no debería esperar al presupuesto del mes. Te contamos una forma simple de cubrir ese gasto."},
            },
            {
                "dia": 3, "etapa": "beneficio_concreto",
                "angulo_asignado": "libranza por nómina, sin trámites eternos",
                "canal": "push",
                "copy": {"titulo": "Tu salud, sin esperar hasta el otro mes", "cuerpo": "Con Colsubsidio, Libre Inversión te permite cubrir gastos de salud hoy y pagarlos por nómina, cómodo cada mes."},
            },
            {
                "dia": 7, "etapa": "cierre",
                "angulo_asignado": "trámite pendiente, cierre sin presión",
                "canal": "whatsapp",
                "copy": {"mensaje": "Ese trámite de salud pendiente puede resolverse esta semana. Con Colsubsidio, tu cupo de Libre Inversión sigue disponible. ¿Lo revisamos?"},
            },
        ],
    },
    "Educativo": {
        # Bug real encontrado por el usuario (25-jul-2026): la primera versión
        # de estos 3 nodos hablaba de "la matrícula del mes" en genérico, las
        # 3 veces con el mismo ángulo (repetitivo, no 3 etapas distintas) — y
        # además el producto real "Crédito Educativo" (kb/productos.txt) SOLO
        # cubre técnico/tecnológico/pregrado/posgrado, nunca colegio. Para
        # este segmento (madres 36-45, 69.9% con hijos probable, ventana real
        # de matrícula "alta"), el ángulo correcto es el paso del hijo al
        # pregrado/técnico, no un gasto mensual genérico de colegio.
        0: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "hijo o hija cerca de terminar el colegio, el siguiente paso natural es técnico o universidad",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Si tu hijo o hija está por terminar el colegio, el siguiente paso suele ser un técnico o la universidad. Te contamos cómo financiarlo con Colsubsidio."},
            },
            {
                "dia": 2, "etapa": "beneficio_concreto",
                "angulo_asignado": "cobertura real del producto (técnico, pregrado, posgrado) con plazos flexibles, dato distinto al nodo 1",
                "canal": "whatsapp",
                "copy": {"mensaje": "El crédito educativo de Colsubsidio cubre técnico, pregrado o posgrado, con plazos flexibles. La universidad no depende de tener todo el dinero de una vez."},
            },
            {
                "dia": 6, "etapa": "cierre",
                "angulo_asignado": "ventana real de matrícula de enero cerca, dato más fuerte y distinto para el cierre",
                "canal": "push",
                "copy": {"titulo": "Antes de que llegue la matrícula de enero", "cuerpo": "Con Colsubsidio puedes dejar lista la matrícula del pregrado antes del afán de última hora."},
            },
        ],
        2: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "formación propia (técnico o pregrado) pendiente, financiable ya",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Ese técnico o pregrado que tienes pendiente puede arrancar antes de lo que crees. Te contamos cómo financiarlo."},
            },
            {
                "dia": 2, "etapa": "beneficio_concreto",
                "angulo_asignado": "plazos flexibles, sin frenar otros planes",
                "canal": "push",
                "copy": {"titulo": "Tu pregrado, a tu propio ritmo y sin afán", "cuerpo": "Con Colsubsidio, el crédito educativo te deja pagar tu formación en plazos flexibles, sin frenar tus otros planes."},
            },
            {
                "dia": 6, "etapa": "cierre",
                "angulo_asignado": "cierre invitando a empezar ya",
                "canal": "email",
                "copy": {
                    "asunto": "Tu formación no tiene que esperar",
                    "preheader": "Plazos flexibles con el crédito educativo de Colsubsidio",
                    "cuerpo": "Con Colsubsidio puedes empezar tu técnico o pregrado ya y pagarlo en plazos flexibles, sin desordenar tu presupuesto actual.",
                },
            },
        ],
    },
    "Rotativo_cupo": {
        0: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "gastos del día a día que no avisan, necesidad inmediata real",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Los gastos del día a día no siempre avisan. Tenemos un cupo que se ajusta a lo que necesites este mes. ¿Te cuento cómo funciona?"},
            },
            {
                "dia": 2, "etapa": "beneficio_concreto",
                "angulo_asignado": "cupo renovable, se recupera al pagar",
                "canal": "push",
                "copy": {"titulo": "Tu cupo Colsubsidio, listo cuando lo necesites", "cuerpo": "Con Colsubsidio, cada compra reduce tu cupo y cada pago lo recupera, para lo del día a día sin afán."},
            },
            {
                "dia": 5, "etapa": "cierre",
                "angulo_asignado": "gasto imprevisto, cierre sin presión",
                "canal": "whatsapp",
                "copy": {"mensaje": "Ese gasto que se salió del presupuesto puede resolverse hoy. Con Colsubsidio, tu cupo rotativo sigue disponible. ¿Lo activamos?"},
            },
        ],
        1: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "ingreso irregular (independiente), flujo de caja pesa más que consumo",
                "canal": "push",
                "copy": {"titulo": "Tu flujo de caja, siempre bajo control", "cuerpo": "Con un cupo rotativo de Colsubsidio, decides cuánto usar cada mes según cómo te vaya, sin presión fija."},
            },
            {
                "dia": 2, "etapa": "beneficio_concreto",
                "angulo_asignado": "cupo que se ajusta a ingresos variables",
                "canal": "whatsapp",
                "copy": {"mensaje": "Con ingresos que varían de mes a mes, un cupo que se ajusta a lo que necesitas hace la diferencia. ¿Simulamos tu cupo con Colsubsidio?"},
            },
            {
                "dia": 5, "etapa": "cierre",
                "angulo_asignado": "cierre invitando a activar",
                "canal": "push",
                "copy": {"titulo": "Tu cupo Colsubsidio, listo para usar", "cuerpo": "Actívalo hoy y úsalo cuando tu flujo de caja lo pida, sin trámites de última hora."},
            },
        ],
    },
    "Compra_cartera": {
        # Bug real encontrado por el usuario (25-jul-2026): los 3 nodos de
        # clase 3 decían "unifica"/"un solo pago" desde el primer mensaje —
        # el punto que ya sabe el afiliado, no un dolor real suyo. El único
        # nodo bueno del set original (clase 4, día 0) no lo decía de una:
        # abría con el dolor (compromisos financieros, no una palabra técnica
        # del producto) y dejaba el mecanismo para después. Reescrito con esa
        # misma lógica, anclado en los datos reales de cada clase: clase 3 es
        # independiente/facultativo (no elegible libranza, sin prima real) con
        # tono directo/datos — el dolor real es perder la cuenta de cuánto se
        # debe con ingreso irregular, y el gancho es la tasa BanRep real, alta
        # hoy (dato real del sistema); clase 4 sí es elegible libranza, así
        # que la prima real (ventana real del sistema) sí aplica ahí.
        3: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "dolor real de un independiente: perder la cuenta de cuánto y a quién se debe, sin mencionar el mecanismo todavía",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Como independiente, es fácil perder la cuenta de cuánto debes y a quién exactamente. Te contamos una forma de tener esto más claro."},
            },
            {
                "dia": 3, "etapa": "beneficio_concreto",
                "angulo_asignado": "tasa BanRep real hoy, alta, como razón concreta para actuar ahora",
                "canal": "email",
                "copy": {
                    "asunto": "Tasas altas: buen momento para unificar",
                    "preheader": "Una mejor tasa uniendo tus deudas en un solo crédito",
                    "cuerpo": "Con las tasas del mercado tan altas, Colsubsidio puede darte una mejor tasa al unir tus obligaciones con otras entidades en un solo crédito.",
                },
            },
            {
                "dia": 8, "etapa": "cierre",
                "angulo_asignado": "urgencia real ligada a la tasa alta, no a una prima que este segmento no recibe",
                "canal": "whatsapp",
                "copy": {"mensaje": "Mientras las tasas sigan altas, unificar tus deudas con Colsubsidio puede convenirte más que esperar. ¿Lo revisamos?"},
            },
        ],
        4: [
            {
                "dia": 0, "etapa": "confirmacion_curiosidad",
                "angulo_asignado": "simplificar compromisos financieros en vez de sumar más",
                "canal": "whatsapp",
                "copy": {"mensaje": "Hola. Entre distintos compromisos financieros, a veces lo que más ayuda es simplificar, no sumar más. Te contamos una forma de hacerlo."},
            },
            {
                "dia": 3, "etapa": "beneficio_concreto",
                "angulo_asignado": "prima real de este segmento (sí elegible libranza) conectada al tono aspiracional de estabilidad, dato distinto al nodo 1",
                "canal": "push",
                "copy": {"titulo": "Con tu prima, un paso más hacia el orden", "cuerpo": "Con Colsubsidio puedes usar tu prima para unir tus deudas en un solo crédito y ganar el orden financiero que buscas."},
            },
            {
                "dia": 8, "etapa": "cierre",
                "angulo_asignado": "cierre con el mismo hilo emocional del nodo 1 (orden/estabilidad) mas el dato más fuerte (prima de este mes)",
                "canal": "whatsapp",
                "copy": {"mensaje": "Ese orden financiero que buscas puede empezar con tu prima de este mes. Con Colsubsidio, tu compra de cartera sigue disponible. ¿Lo revisamos?"},
            },
        ],
    },
}


def resumen_mock(producto: str, clase: int, alcance: int, rubro: str) -> dict:
    """Arma resumen + resumen_kpis con datos REALES (alcance, rubro vienen de
    contexto_segmento.py) — solo el texto del resumen es redactado. La
    elegibilidad de libranza ya no se muestra como KPI aparte acá (era jerga
    interna poco clara para el jurado); el gate L1 real (validador.py) la
    sigue usando por su cuenta, directo de contexto["scorer"]."""
    from .contexto_segmento import _NOMBRE_PRODUCTO

    nombre_producto = _NOMBRE_PRODUCTO.get(producto, producto.replace("_", " "))
    return {
        "resumen": f"Grupo con interés real en {rubro.lower()}. La oferta de {nombre_producto} se presenta conectada a ese interés concreto, sin desviar el mensaje hacia otro producto.",
        "resumen_kpis": [
            {"etiqueta": "Alcance real", "valor": f"{alcance:,} afiliados".replace(",", "."), "tipo": "neutro"},
            {"etiqueta": "Interés dominante", "valor": rubro, "tipo": "oportunidad"},
        ],
    }
