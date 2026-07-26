# Kepler para Colsubsidio — Hackathon Colsubsidio × 30X (Reto 1: Crédito Hiperpersonalizado)

**Qué hacemos:** convertimos los 1.6M afiliados de Colsubsidio, hoy tratados con la misma oferta
de crédito por el mismo canal, en 1.6M ofertas distintas — qué producto, con qué monto, por qué
canal y en qué momento — con una segmentación estadística real (no caja negra) que combina lo que
Colsubsidio ya sabe de cada afiliado con señal de mercado citada de fuente real, y un agente que
solo se encarga de redactar el mensaje, nunca de decidir el crédito.

**Acceso a la demo:** `http://localhost:3000` (o la URL de Vercel) → usuario `admin@colsubsidio.com`
/ contraseña `admin2024`.

---

## 1. El problema y cómo lo resolvemos

Colsubsidio tiene **1.6M afiliados, 73% potenciales para crédito, solo 16% de penetración**. Hoy
casi todos reciben la misma oferta por el mismo canal. Nuestra solución tiene tres piezas, cada una
resolviendo una parte distinta del problema:

1. **Segmentación estadística real (MCA + Latent Class Analysis)** sobre los datos reales de
   afiliados que sí nos entregó Colsubsidio, para agrupar afiliados en perfiles de comportamiento
   con base matemática, no reglas a mano.
2. **Enriquecimiento con datos externos reales** (comportamiento digital, macroeconomía, calendario,
   intereses de consumo) para completar lo que el dataset entregado no tenía — el reto exige
   combinar perfil **y** comportamiento, y no autoriza usar buró de crédito (DataCrédito).
3. **Un scorer transparente** que decide producto + monto + canal + momento con razones nombradas
   y cuantificadas (no SHAP pegado a una red neuronal), y un **agente Claude de 4 pasos** que solo
   redacta el mensaje final — la decisión de crédito nunca es generativa.

---

## 2. Los datos: qué nos dio Colsubsidio, qué es real y qué es simulado

**Lo que Colsubsidio entregó es real**, no un dataset genérico: `Usos_Productos_Afiliados_SIN_ID.csv`
(`backend/data/raw/`), **1,566,026 filas** de afiliados reales anonimizados (sin cédula). Pero **no
es data de crédito** — el reto se llama "Crédito Hiperpersonalizado" y sin embargo lo que nos dieron
es un snapshot demográfico y de uso de *otros* servicios de Colsubsidio: género, rango de edad,
categoría de ingreso (A/B/C), segmento de grupo familiar, empresa, ciudad, y flags de uso de
droguería, Piscilago, hoteles, agencias y vivienda. **No hay historial de crédito, ni fechas, ni
tenencia de producto, ni variable objetivo** — es información de quién es el afiliado y qué otros
servicios de Colsubsidio usa, no de su comportamiento crediticio.

Verificamos empíricamente cada columna sobre las 1,566,026 filas completas (no una muestra) antes
de decidir qué hacer con ella:

| Columna | Lo que encontramos | Qué hicimos con eso |
|---|---|---|
| `CATEGORIA` (ingreso) | 75.9% de la base cae en la misma categoría (A) | El monto no puede ser el eje de personalización para la mayoría → el eje real es producto/canal/momento |
| `HOTELES` / `AGENCIAS` / `VIVIENDA` | Señal positiva en menos del 0.1% de filas | Sin masa para segmentar, pero sí sirven como regla de alta confianza cuando aparecen (ej. `VIVIENDA=SI` dispara oferta de vivienda con certeza) |
| `DROGUERIA` / `PISCILAGO` | Señal real en ~5-6% de filas | Sí entran como eje de la segmentación |
| `ESTADOAFILIADO` | 100% constante ("Al día") | Fuera del modelo, no aporta nada |

Como el reto **exige** combinar el perfil del afiliado con señal de comportamiento que el dataset no
traía, y **prohíbe** usar buró de crédito externo (DataCrédito/CIFIN — Ley 1266/2008), enriquecimos
cada segmento (nunca cada persona individual) con cuatro familias de datos externos reales y
citables — no inventados:

| Familia | Fuente real | Qué aporta |
|---|---|---|
| Comportamiento digital → canal | DataReportal *Digital 2026 Colombia*, NapoleonCat | Por qué canal contactar a cada perfil (WhatsApp, push, email, físico) |
| Intereses de consumo | Estudios Raddar (millennials Colombia), estudios Gen Z Colombia | De qué producto/necesidad hablarle a cada perfil |
| Macroeconomía | Banco de la República (tasa de política 12%), DANE (inflación, Ley de Engel por nivel de ingreso) | Cuánto se prioriza crédito rotativo/consolidación de deudas según el momento |
| Calendario de demanda | Prima legal (Art. 306 CST), calendario escolar/universitario real de Colombia | Cuándo es el mejor momento para cada producto |

Cada afiliado hereda estas cuatro tablas **por segmento vía membresía estadística suave**
(`θ_i = Σ_k π_ik · θ_k`, shrinkage bayesiano estilo James-Stein) — no se inventa un dato por
persona; se hereda el perfil agregado, matemáticamente correcto, del segmento al que pertenece con
cierta probabilidad. Detalle completo, con cada cifra y su fuente, en `cnoslidado-estrategia.md`
§5.2.

**Lo único simulado, y declarado como tal, es la demo en vivo:** como las cédulas del CSV son
anónimas, para la demo generamos perfiles sintéticos muestreando de las condicionales reales de cada
segmento (estadísticamente consistentes, no aleatorios) — la interfaz `enrich(cédula) → {señales}`
es idéntica entre el simulador de hoy y un conector real de producción. En producción con
Colsubsidio esto se resolvería con datos de consentimiento real (Tier 1, ver §5), no con simulación.

---

## 3. Cómo se construyó el modelo estadístico — MCA + Latent Class Analysis

**Por qué no deep learning:** el 60% del rubric del reto es personalización + explicabilidad + UX,
y hay una regla explícita de "no caja negra". Se evaluaron y descartaron con razón técnica: redes
neuronales, two-tower/deep retrieval, modelos secuenciales (SASRec/BERT4Rec), GNN, uplift/CATE —
todos pierden por diseño frente a un modelo glass-box en este rubric (detalle en
`cnoslidado-estrategia.md` §3).

**Paso 1 — MCA (Multiple Correspondence Analysis):** el análogo categórico de PCA (el dataset es
~100% categórico, así que k-means/distancia euclidiana es matemáticamente incorrecto aquí). Corrido
como chequeo de estructura antes de comprometer el modelo final: confirma que las columnas
categóricas tienen correlación real, no ruido. Script: `backend/pipeline/02_mca.py`.

**Paso 2 — Latent Class Analysis vía StepMix:** mixtura generativa que da a cada afiliado una
**membresía suave** entre K clases (`π_i`, con `Σπ_ik = 1`) en vez de una etiqueta dura — esto es lo
que habilita la hiperpersonalización, porque cada afiliado es una combinación única de segmentos.
Scripts: `backend/pipeline/03_lca.py` → `03a_buscar_k_extendido.py` → `03b_ajuste_final.py`.

**Selección de K, con evidencia, no a ojo:** se probó K=4 a 20, comparando BIC, SABIC y entropía
relativa (los tres nativos de StepMix). K=7 y todo K≥14 **no convergieron** (tope de iteraciones) —
sus métricas no son comparables. **K=12 es el candidato más alto que convergió limpio**, con
entropía 0.939 (alta separación entre clases). Ajuste final de producción sobre las **1,566,026
filas completas**: 51.6 minutos reales, convergencia confirmada, `random_state=42` fijo
(reproducible). Las 12 clases resultantes van de 13.5% a 1.3% de la base, ninguna degenerada.
Tabla completa de resultados por K y perfil de las 12 clases en `cnoslidado-estrategia.md` §5.1.1.

**Modelo guardado:** `backend/data/processed/lca_modelo.pkl.gz` (parámetros del modelo) y
`lca_pi.pkl.gz` (membresía π_i por afiliado, anonimizada con un número de serie correlativo, sin
cédula). Comprimidos porque sin comprimir pesan 143-165MB (GitHub rechaza archivos >100MB).

**El scorer, glass-box, no una caja negra con explicación pegada encima:**

```
Score(i, producto_k) = Elegibilidad_ik × Σ_j  w_jk · señal_ij
```

Cada término es una razón nombrada y cuantificada — los top-3 términos **son** la explicación en
lenguaje natural que ve el afiliado. La elegibilidad usa las reglas reales de libranza de
Colsubsidio (Decreto 1072/2015, categoría A/B/C → SMMLV → tope de monto), así que la salida no es
"recomendación" sino oferta accionable real. Implementado en `backend/motor/scorer_persona.py`.

---

## 4. El sistema agéntico: 4 pasos, con techo de vidrio explícito

**Frontera de explicabilidad, no negociable:** el scorer de arriba decide **qué** ofrecer (producto,
monto, canal, razones) de forma 100% transparente. El agente Claude **solo** decide **cómo**
comunicarlo — nunca recalcula ni la oferta ni el monto.

Pipeline de 4 llamadas encadenadas (mismo patrón *prompt chaining* usado en el resto de Kepler,
implementado en `backend/agente/orquestador.py`, `claude_client.py`, `perplexity_client.py`,
`prompts.py`):

1. **Analista de segmento** — Perplexity busca contexto/actualidad real del grupo (temporada,
   tendencia de categoría).
2. **Planificador de cadencia** — Claude reparte los ángulos entre 3 mensajes espaciados (día 0,
   día 3, día 7) sin repetir el mismo dato entre nodos.
3. **Copywriter** — Claude escribe el copy de los 3 mensajes siguiendo exactamente el plan.
4. **Humanizador** — Claude pule el tono para que suene natural, no corporativo.

Después de las 4 llamadas: **gate L1** (`backend/agente/validador.py` — reglas determinísticas,
límites de caracteres por canal, una idea por frase, sin costo de LLM) y **gate L2** (Claude como
juez de calidad sobre el resultado final). Nada se envía sin pasar ambos gates.

**Por qué la demo corre en modo mock** (`MODO_MOCK = True` en `backend/agente/orquestador.py`): el
reto exige demo en vivo sin video de respaldo. El pipeline real (Perplexity + Claude) funciona —
probado en vivo el 25-jul-2026 — pero tiene un modo de falla real bajo presión de tiempo (el
copywriter puede devolver texto cortado). El contenido mock (`datos_mock.py`) no es relleno
genérico: está escrito a mano con las mismas reglas del pipeline real y pasa el mismo gate L1. Para
volver a modo real: `MODO_MOCK = False`, la interfaz no cambia.

---

## 5. Conexión real con los sistemas de Colsubsidio: SAP y Salesforce Marketing Cloud

Investigamos, con fuente real citada (no es un plan hipotético), cómo Kepler se conectaría a la
infraestructura real ya confirmada de Colsubsidio — documentación completa en
`investigacion-conexion-sap-salesforce.md`.

**Lo que confirmamos con evidencia real:**
- **SAP**: Colsubsidio corre desde 2023 sobre **SAP Business Technology Platform + SAP Analytics
  Cloud + SAP HANA Cloud** (fuente: SAP News Center, marzo 2025).
- **Salesforce Marketing Cloud** (ex-ExactTarget) es su plataforma real de envío de comunicaciones —
  confirmado técnicamente vía los registros SPF/DKIM de sus correos promocionales reales, y
  verbalmente por la mentora del reto.

**Cómo alimentaríamos el modelo desde SAP (inferencia, sin reentrenar):** vía **OData** sobre el
**SAP API Business Hub** — el mismo patrón que usa `API_BUSINESS_PARTNER` (entity set
`A_BusinessPartner`, con filtro/paginación/batch por HTTP, autenticado con OAuth contra BTP).
Reemplazaría el CSV local por una consulta filtrada por cédula o por lote, sin tocar el modelo ya
entrenado. Para reentrenar con el histórico completo, el patrón real de mercado (no algo que
inventamos) es leer del **data lake** (S3/Azure Blob) al que SAP y Salesforce ya vuelcan sus datos
por lote — el caso de uso 4 del propio "MuleSoft Accelerator for SAP", la integración oficial que
Salesforce vende para conectar exactamente estos dos sistemas.

**Cómo enviaríamos segmentos y ofertas actualizados a Salesforce, para crear campañas filtradas por
segmento o por persona específica:**
- **Data Extensions** (`POST .../data/v1/customobjects`) — creamos el objeto con los atributos de
  segmento/oferta por afiliado.
- **Carga de filas** (`.../data/v1/customobjectdata/key/{key}/rowset`) — subimos el lote de
  personas con su segmento, producto recomendado, canal y razones, listo para que Marketing Cloud
  filtre campañas por cualquiera de esos atributos (igual que hoy filtra por atributos propios).
- **Bulk Data Ingest API** para volúmenes grandes (todo el 1.6M en un job, no fila por fila).
- **Disparo del envío** — OAuth2 client credentials + `POST /interaction/v1/events`, para entrar un
  contacto a un Journey de Marketing Cloud. Ya implementado con esta misma forma en
  `backend/agente/salesforce_client.py`.

**Estado real en este repo, sin maquillar:** la conexión a Salesforce en la demo **no es real** —
usamos `backend/agente/salesforce_simulado.py`, que escribe el mismo flujo borrador→enviada en JSON
local (`backend/data/salesforce_simulado_campanas.json`), con la forma exacta de la API real, para
poder mostrar el flujo completo sin credenciales de producción de Colsubsidio. Conectar el real
requiere que su equipo de Salesforce cree un "Installed Package" (server-to-server) con permisos de
Data Extensions para nosotros — no es algo que se resuelva sin su cooperación, y lo decimos así en
el pitch en vez de aparentar que ya está conectado.

---

## 6. Cómo correrlo (< 5 minutos)

Requiere Python 3.12+ y Node 20+. Dos terminales, backend y frontend por separado.

### Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows — en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env — pon tus keys (ver abajo)
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```
cd frontend
npm install
npm run dev
```

### Acceder a la demo

Abrir `http://localhost:3000` →

- **Usuario:** `admin@colsubsidio.com`
- **Contraseña:** `admin2024`

### Variables de entorno

**Backend** (`backend/.env`, ver `backend/.env.example`):
- `ANTHROPIC_API_KEY` — clave de Claude. No se llama mientras `MODO_MOCK=True`, pero debe estar
  puesta para el día que se apague el modo mock.
- `PERPLEXITY_API_KEY` — clave de Perplexity, mismo caso.

**Frontend** (`frontend/.env.local`):
- `NEXT_PUBLIC_BACKEND_URL` — local: `http://localhost:8000`.

---

## 7. Estructura del repo

```
colsubsidio/
  backend/
    app/
      routers/       — FastAPI: productos, campanas, kb, sugerencias
      services/       — eventos.py
    agente/           — motor agéntico: orquestador (pipeline + MODO_MOCK), claude_client,
                       perplexity_client, prompts, validador (gate L1), datos_mock,
                       salesforce_client (real) / salesforce_simulado (demo)
    motor/            — scorer_persona.py (scorer aditivo glass-box + elegibilidad)
    pipeline/         — 01_limpieza → 02_mca → 03_lca → 03a/03b (ajuste K=12) → 04-11
                       (perfiles, canal, interés, macro, calendario, estilo por clase) — scripts de
                       uso único, ya corridos, no parte de la app en producción
    data/
      raw/            — Usos_Productos_Afiliados_SIN_ID.csv (dataset real, NUNCA se commitea)
      processed/      — lca_modelo.pkl.gz / lca_pi.pkl.gz (modelo LCA real ya entrenado),
                       tamano_clases.json
      theta_k/        — las 4 tablas exógenas por clase (canal, interés, macro, calendario) +
                       estilo de comunicación
    pruebas/          — validación con personas sintéticas y reales, uso único
    vercel.json
  frontend/
    app/(login, dashboard/campañas, dashboard/configuración)
    components/       — CampanaCanvas (revisión/edición pre-envío), MetricasCampana (gestión
                       post-envío), EscenarioResultado, EscenarioProcesando, AvisoTemporada
    lib/api.ts        — cliente HTTP tipado
```

**Documentación de investigación completa** (fuentes reales citadas en cada afirmación):
- `cnoslidado-estrategia.md` — documento maestro: rubric, diagnóstico del dato, arquitectura
  completa, resultados MCA/LCA con tablas, las 4 familias θ_k, regulación.
- `investigacion-conexion-sap-salesforce.md` — integración SAP + Salesforce Marketing Cloud.
- `resultado1.md` — por qué se descartó cada familia de modelos "de moda".
- `resultado2.md` — canales reales confirmados de Colsubsidio (app, WhatsApp Business API, email,
  IVR).

---

## 8. Despliegue (Vercel)

Un repo, dos proyectos de Vercel (Vercel no puede servir Next.js y FastAPI desde el mismo
proyecto):
- **Backend**: Root Directory `backend`, variables `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`.
- **Frontend**: Root Directory `frontend`, variable `NEXT_PUBLIC_BACKEND_URL` (URL real del backend
  ya desplegado).

---

## 9. Notas de seguridad y regulación

El dataset que entregó Colsubsidio es de afiliados reales anonimizados. **Nunca se commitea al
repo** (`.gitignore` bloquea `*.csv` crudos, `data/raw/`, `data/real/`, `data_limpia.pkl`). El
tratamiento de esta data interna está cubierto por el aviso de privacidad vigente de Colsubsidio
(autoriza uso para "ofertas y promociones", Ley 1581/2012 + Decreto 1377/2013). Los `.pkl.gz` del
modelo LCA sí se suben (son parámetros del modelo, no datos por persona); las probabilidades
reales por afiliado (`lca_pi.pkl.gz`) están anonimizadas con un número de serie correlativo, sin
cédula. Nunca se usa buró de crédito externo (DataCrédito/CIFIN) — prohibido explícitamente por el
reto y por la Ley 1266/2008.
