# Prompt para Opus — Guion de pitch (2 minutos, Hackathon Colsubsidio × 30X, Reto 1)

Eres un experto en pitches de hackathon. Tu única tarea es escribir el **guion hablado** de un
pitch de **2 minutos exactos** (para decir en voz alta, natural, no leído) que presenta la
solución al Reto 1 de un hackathon. No escribas código, no describas la interfaz en detalle más
allá de lo que un presentador diría mientras la muestra — el objetivo es el texto que se dice en
voz alta.

## El reto tal cual lo planteó Colsubsidio (pégalo mentalmente como el problema real, no lo resumas de más)

> **Crédito hiperpersonalizado**
>
> **El problema.** Colsubsidio tiene una ventaja única: conoce a sus afiliados como pocos actores
> del mercado financiero. Sabe dónde trabajan, cuánto ganan, qué servicios usan, cómo está
> compuesto su hogar y qué momentos clave han marcado su vida. Pero hoy ese conocimiento aún no se
> convierte en una experiencia realmente personalizada: muchos afiliados reciben la misma oferta
> de crédito y son contactados por los mismos canales.
>
> El desafío está claro: complementar ese activo de datos en ofertas relevantes, oportunas y
> accionables; propuestas que conecten con la realidad de cada afiliado, aumenten la conversión y
> demuestren que el crédito puede sentirse hecho a la medida.
>
> **Tu misión:** convertir ese conocimiento y enriquecerlo para brindar ofertas de crédito que cada
> afiliado sienta diseñadas exclusivamente para él.
>
> **Cómo se ve un buen resultado:** usa datos del afiliado, los enriquece con señales externas
> (redes sociales, comportamiento digital, intereses, eventos de vida o data alternativa) y genera
> una oferta específica. Dos afiliados distintos reciben ofertas claramente distintas (producto,
> no solo monto). Cada oferta trae una razón clara en lenguaje natural. El equipo puede explicar
> qué señales pesaron más. (Suma puntos) la oferta llega por un canal funcional y en el momento
> adecuado, no solo en un dashboard. Ejemplo textual que ellos mismos dan de una buena explicación:
> *"Llevas 6 años con nosotros y recientemente tuviste un hijo; este crédito tiene condiciones
> preferenciales para acompañar este momento."*
>
> **No-negociables:** mínimo 3 señales distintas combinadas (perfil estático + comportamiento/
> contexto). Explicabilidad total, cero caja negra. Nada de datos de buró externo (DataCrédito).

## Lo que de verdad se construyó (hechos reales, no inventes ni generalices — usa esto tal cual)

**Segmentación real, no simulada:** MCA + LCA (Latent Class Analysis) sobre el dataset real del
hackathon (1,566,026 filas de afiliados). K=12 clases reales, decidido con evidencia (BIC/SABIC +
entropía + estabilidad de convergencia, no a ojo). Cada afiliado no cae en una sola categoría fija:
tiene una **probabilidad real de pertenecer a cada uno de los 12 grupos** (mezcla suave, π_i) —
esto es lo que estadísticamente reemplaza "edad e ingresos" por una combinación real de señales.

**Las señales combinadas (cumple y supera el mínimo de 3 que pide el reto):** perfil estático
(edad, categoría de ingreso, composición familiar) + comportamiento/interés real (vector de interés
sintetizado combinando los datos reales del afiliado con investigación real de mercado — Raddar,
estudios Gen Z Colombia) + sensibilidad macro real (tasa BanRep, inflación DANE, con pesos reales
de la Ley de Engel, no estimados a ojo) + calendario/timing real (ventanas de matrícula, prima,
vacaciones, con fechas verificadas). Todo eso se hereda por persona con shrinkage bayesiano
(θ_i = Σ π_ik · θ_k) — nunca un cruce persona-a-persona inventado.

**El sistema agéntico — esto es el corazón técnico, dale peso real:** no es "una llamada a un LLM".
Es una cadena de 4 pasos independientes (patrón de prompt chaining, el mismo que recomienda
Anthropic en su research "Building Effective Agents": patrones simples y bien definidos superan a
frameworks complejos que producen resultados mediocres). Cada paso tiene un trabajo único:
1. **Analista de segmento** — investiga en tiempo real (búsqueda web real) qué mueve HOY a ese
   grupo específico, según su interés real, para saber qué ángulo usar.
2. **Planificador de cadencia** — cruza esas señales con la estructura real del journey (día 0,
   día X, día Y) y reparte una etapa psicológica distinta y un ángulo/dato único por mensaje, sin
   repetir entre mensajes.
3. **Copywriter** — escribe el texto seguiendo exactamente lo que el paso 2 asignó.
4. **Humanizador** — pule el texto para que suene humano y se pueda escanear rápido, nunca frío ni
   genérico.

Después de escribir, pasa por **2 validadores automáticos** (no solo estilo): uno de reglas
objetivas (límites reales de cada canal, cifras, términos prohibidos) y uno que verifica el texto
contra el conocimiento real de los productos de Colsubsidio — para que nunca haya una afirmación
incorrecta o inventada sobre un producto real de crédito.

**Explicabilidad total (cumple el no-negociable de "cero caja negra"):** cada oferta llega con las
señales reales que pesaron — quién la recibe (perfil real), por qué (el ángulo real conectado al
dato), y cómo se le habla (el tono real). Nada de esto es una caja negra: se puede señalar
exactamente qué dato produjo qué decisión.

**Canal y momento reales, no solo dashboard (el "suma puntos" del reto):** la campaña se crea como
borrador en Salesforce Marketing Cloud (WhatsApp/push/email, según lo que de verdad funciona por
canal para cada grupo), un humano aprueba y confirma el envío real (nunca se envía sola), y después
se traen periódicamente las métricas reales de resultado de esa campaña.

**Conexión real con los sistemas de Colsubsidio (no hipotética — investigado con evidencia real):**
confirmamos que Colsubsidio corre sobre SAP (BTP + HANA Cloud) como su sistema real, y que ya usan
Salesforce Marketing Cloud para enviar sus comunicaciones (evidencia técnica real, no supuesta). El
patrón de integración real entre esos dos sistemas es MuleSoft (la propia herramienta de Salesforce
para esto, con un caso de uso ya documentado exactamente para mover datos de SAP a un data lake que
alimenta un motor externo). Así conectaríamos de verdad: se trae el histórico real vía esa capa para
entrenar el modelo una vez; para correrlo ya entrenado, se consulta en tiempo real por cédula o por
lote (la API real de SAP lo permite, hasta 2.000 personas de una); y antes de enviar la campaña, se
actualiza en Salesforce el filtro real de a quién le llega el mensaje correcto — ni un afiliado de
más, ni de menos.

## Evidencia real de que esto ya funciona en producción — no es un prototipo desde cero

Este motor no nació para este hackathon. Es la misma arquitectura (Kepler) ya instanciada antes
para Trii, una fintech colombiana, donde corre en producción real desde hace **2 meses** y ya
mejoró la conversión en **4.3 puntos porcentuales**. Colsubsidio es una instancia nueva del mismo
motor general (cambia qué predice y qué datos usa, el ciclo entender→modelar→accionar→medir es el
mismo) — no un experimento sin historial: llega con track record real de producción. Usa este dato
como refuerzo de credibilidad, lo más natural es en el cierre o en el tramo de "por qué importa" —
no lo satures ni le quites tiempo a la demo en vivo.

## Los DOS frentes de la solución — esto tiene que quedar explícito, nombra los dos por separado

1. **Frente de automatización:** hoy este proceso completo (leer el dato, decidir el ángulo,
   escribir el mensaje, revisarlo, montarlo en el canal) lo hacen mínimo 2 personas, entre 3 días y
   una semana. Con este sistema, sale en máximo 5 minutos.
2. **Frente de autonomía/hiperpersonalización real:** no es solo más rápido — los mensajes y la
   conversión suben porque cada oferta está genuinamente hecha a la medida de esa persona, no es
   velocidad reemplazando personalización, es velocidad Y personalización real al mismo tiempo.

## Decisión pendiente de formato — razona esto explícitamente, no lo saltes

Todavía no decidimos el formato final de estos 2 minutos. Las opciones sobre la mesa:
(a) Grabar al presentador usando el sistema real en vivo (screen recording real, sin cortes, tal
    como se ve en pantalla).
(b) Diapositivas narradas, sin mostrar el sistema funcionando.
(c) Diapositivas con un video incrustado adentro que muestra el sistema funcionando.

**Restricción real ya encontrada (notas de la sesión informativa oficial del hackathon,
`informacion-importante.md`):** el reto pide explícitamente "Demo en vivo" y dice, en la misma
lista de entregables, **"Sin videos pregrabados"**. Esto es una tensión real que hay que resolver,
no ignorar: un video —sea independiente o incrustado dentro de diapositivas— podría no cumplir esa
regla tal como está escrita, porque lo que se espera es que el jurado vea el sistema funcionando en
vivo de verdad, no una grabación de eso.

Con esa restricción explícita en mente: razona las tres opciones, di con claridad cuál cumple mejor
la regla real del reto sin sacrificar que se vea el sistema funcionando, y da una recomendación —
no elijas en automático la que "se ve mejor" en video si eso arriesga incumplir un requisito
explícito del reto.

## Contexto de la demo en vivo (para que sepas qué se está mostrando en pantalla durante esos 50s)

Es una demo **en vivo real** (no video, no hay red de seguridad de reintento) sobre una interfaz
real: login → elegir un producto de crédito → un motor corre el pipeline completo (loader visible)
→ aparecen 2 campañas reales, cada una con quién la recibe, cómo se le habla y por qué, con el
mensaje completo editable → se aprueba y envía de verdad (dispara el evento real hacia el canal) →
aparecen las métricas reales de gestión de esa campaña. El narrador va a estar clickeando esto
mientras habla — el guion de esta sección debe ser natural para acompañar esas acciones, no una
descripción técnica de la UI.

## Feedback real ya recibido de una mentora del reto — el guion tiene que satisfacer esto punto por punto

Transcripción textual del feedback, no lo reinterpretes de más:

> Tenemos que lograr explicar qué es el modelo, es replicable. Explicar que aunque es con data
> dummy, es replicable y escalable. Además, explicar en una frase rápida qué hace el modelo.
> Después explicar end-to-end la lógica. Es que cuando prueben, sea tan intuitivo que la gente
> entienda y haga todo solos, se entienda todo el proceso.
>
> Modelo → sistemas agénticos, búsqueda web, precisamente eso.
>
> Cómo se conecta con Salesforce y cómo se envía. Importante saber si se pueden crear campañas en
> Salesforce y cómo se envían, y cómo sabemos que le llegan al segmento correcto → todo en 2
> minutos y bien explicado y con detalle en 2 min.
>
> Practicar mucho y explicar claramente cómo funciona todo sin trabarme, y que el flujo funciona
> bien.
>
> Que sea intuitivo y correcto.

Puntos concretos que el guion debe cubrir por esto (ya tienes el material real para cada uno más
arriba en este documento, solo asegúrate de que ninguno se quede afuera):
- Una frase rápida y clara de qué hace el modelo (no técnica, para cualquiera).
- Que el modelo es replicable y escalable a pesar de correr hoy con datos simulados curados a mano
  (ver la nota de MODO_MOCK más abajo) — esto hay que decirlo explícito, no dar por hecho que se
  entiende solo.
- La lógica end-to-end, mencionando que es un sistema agéntico con búsqueda web real (no solo "un
  LLM").
- Cómo se conecta con Salesforce, que sí se pueden crear campañas reales ahí, cómo se envían, y
  cómo se garantiza que le llega al segmento correcto (no a cualquiera) — esto ya está en la
  sección de "Conexión real con los sistemas de Colsubsidio" más arriba, asegúrate de que quede
  claro y no se pierda por falta de tiempo.
- Todo esto tiene que sonar intuitivo, fluido, sin trabarse — prioriza claridad sobre densidad si
  hay que elegir, dado que son 2 minutos exactos.

**Nota importante sobre MODO_MOCK (dilo con honestidad, no lo escondas):** la demo en vivo corre
hoy con contenido curado a mano en vez de llamar a Perplexity/Claude en vivo por cada clic — no
es un modelo falso ni relleno genérico, es el mismo tipo de salida que produce el pipeline real
(mismas reglas, mismo formato, validado contra el mismo gate de calidad), fijado así a propósito
para que la demo en vivo sea confiable sin depender de la latencia/estabilidad de una llamada de
red en el momento exacto frente al jurado. El pipeline real (búsqueda web + Claude en cadena) sí
existe y sí se probó — la arquitectura completa es la misma, replicable y escalable a cualquier
producto o segmento nuevo sin tocar código.

## Estructura de tiempo — respétala exacta, en este orden

1. **Hook + Problema — 20 segundos.** Arranca con tensión real (dos afiliados distintos, misma
   oferta, mismo canal, hoy) — no repitas el brief palabra por palabra, hazlo memorable.
2. **Qué construimos — 20 segundos.** Aterriza rápido en los dos frentes (automatización +
   autonomía/hiperpersonalización) y en que hay un modelo real de segmentación detrás, no reglas a
   ojo.
3. **Demo en vivo — 50 segundos.** El tramo más largo — que se sienta que de verdad está pasando
   en pantalla, con al menos una mención de una razón real ("por qué a esta persona") al estilo del
   ejemplo que da el propio reto.
4. **Tech stack + por qué importa — 10 segundos.** Muy corto, una sola frase con peso: sistema
   agéntico de pasos encadenados + búsqueda web en tiempo real + los nombres reales (segmentación
   real, Salesforce Marketing Cloud) — y por qué importa: no es un truco de un solo cliente, es un
   motor que se puede instanciar en cualquier organización con datos propios (y ya lo probó: ver
   la sección de evidencia real en producción con Trii).
5. **Equipo + qué sigue + cierre — 20 segundos.** Cierre memorable, conecta de vuelta con el hook.
   Buen lugar para el dato de Trii (2 meses en producción, +4.3pp de conversión) si no alcanzó a
   entrar antes — da la sensación de "esto ya funciona en el mundo real", no solo en la demo.

## Instrucciones finales

- Español neutro colombiano, tono seguro, hablado (no de lectura). Nunca nombrar jerga interna
  ("clase 2", "segmento 7") — siempre el concepto real (interés, perfil, producto).
- Nunca inventes una cifra o afirmación que no esté en este documento.
- Entrega el guion completo con el tiempo (segundos) marcado al lado de cada sección, y una
  versión corta de "qué se está haciendo en pantalla" entre paréntesis en la sección de demo, para
  que quien lo lea en voz alta sepa qué clic acompaña qué frase.
