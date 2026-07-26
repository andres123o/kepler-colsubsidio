# Kepler para Colsubsidio — Hackathon Colsubsidio × 30X (Reto 1: Crédito Hiperpersonalizado)

Motor de decisión que, por afiliado, determina **qué** producto de crédito ofrecer, **cuándo**
y **por qué canal** — usando el perfil enriquecido del afiliado (incluyendo señal conductual
cross-vertical: droguería, recreación, educación, vivienda, salud, turismo) en vez de solo
variables financieras clásicas.

Instancia del sistema general de Kepler (entender usuarios vía ML/DeepL → volver eso accionable
en comunicaciones hiperpersonalizadas) aplicada a Colsubsidio. Repo independiente — no reutiliza
código del backend/frontend de la instancia Trii.

## Estado

- [x] Segmentación real (LCA, K=12, sobre las 1,566,026 filas del dataset del hackathon)
- [x] Tablas exógenas θ_k (canal, interés, macro, calendario, estilo de comunicación) por clase
- [x] Scorer aditivo + motor de elegibilidad (libranza, Ley 1527/2012)
- [x] Agente de 4 pasos (analista → planificador → copywriter → humanizador) + gate L1 determinista
      + gate L2 (juez de calidad)
- [x] Backend FastAPI (`backend/`) + frontend Next.js (`frontend/`) — demo funcional completo:
      login → elegir producto → generar campaña → revisar/editar en el canvas → aprobar y enviar
      → ver métricas de gestión
- [x] Simulación de Salesforce Marketing Cloud (borrador → enviada, con la forma real de su API)

## Cómo correrlo (< 5 minutos)

Requiere Python 3.12+ y Node 20+. Dos terminales, backend y frontend por separado.

### 1. Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows — en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env — pon tus keys (ver abajo)
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:3000` → login `admin@colsubsidio.com` / `admin2024`.

### Variables de entorno

**Backend** (`backend/.env`, ver `backend/.env.example`):
- `ANTHROPIC_API_KEY` — clave de Claude. No se llama mientras `MODO_MOCK=True` (ver abajo), pero
  hay que tenerla puesta para el día que se apague.
- `PERPLEXITY_API_KEY` — clave de Perplexity, mismo caso.
- `FRONTEND_ORIGIN` — para CORS. Local: `http://localhost:3000`.

**Frontend** (`frontend/.env.local`):
- `NEXT_PUBLIC_BACKEND_URL` — Local: `http://localhost:8000`.

## Por qué el demo corre en modo mock (`MODO_MOCK = True` en `backend/agente/orquestador.py`)

El reto exige demo **en vivo, sin video pregrabado**. El pipeline real (Perplexity + Claude, 6
llamadas por segmento) sí funciona — probado en vivo el 25-jul-2026 — pero encontramos un modo de
falla real (el copywriter devolvió texto plano en vez de JSON, respuesta cortada a media frase).
Correr eso sin red de seguridad frente a un jurado, en un formato que no admite reintento por
video, es un riesgo innecesario para un hackathon de 5 días — la práctica recomendada por jueces
de hackathon reales es justamente mockear la llamada lenta/frágil a un LLM. El contenido mock
(`backend/agente/datos_mock.py`) no es relleno genérico: está escrito a mano siguiendo exactamente
las mismas reglas del pipeline real (límites de caracteres por canal, una idea por frase, KB real
de productos) y validado contra el mismo gate L1 (`validador.py`). Para volver a producción real:
`MODO_MOCK = False` — la interfaz de `procesar_segmento()` no cambia en absoluto.

## Estructura

```
colsubsidio/
  backend/
    app/            — FastAPI: routers (productos, campanas, kb, sugerencias), config, servicios
    agente/          — motor: contexto_segmento, prompts, claude_client, perplexity_client,
                       validador (gate L1), orquestador (pipeline + MODO_MOCK), datos_mock
    data/theta_k/    — tablas θ_k por clase (canal, interés, macro, calendario, estilo)
    data/processed/  — tamano_clases.json (real) + lca_modelo.pkl.gz / lca_pi.pkl.gz (modelo LCA
                       real entrenado, comprimidos — sin comprimir pesan 143-165MB, GitHub
                       rechaza archivos de más de 100MB)
    segmentacion/    — scripts de Frente A/B (MCA, LCA, tablas θ_k) — uso único, ya corridos
    pruebas/         — scripts de validación con personas sintéticas/reales — uso único
    vercel.json      — config de despliegue (@vercel/python)
  frontend/
    app/(login, dashboard/campañas, dashboard/configuración)
    components/      — CampanaCanvas (revisión/edición pre-envío), MetricasCampana (gestión
                       post-envío), EscenarioResultado, EscenarioProcesando, AvisoTemporada
    lib/api.ts        — cliente HTTP tipado
  Usos_Productos_Afiliados_SIN_ID.csv  — dataset real (NUNCA se commitea, ver .gitignore)
```

## Despliegue (Vercel)

Un repo, dos proyectos de Vercel (uno por Root Directory — Vercel no puede servir Next.js y
FastAPI desde el mismo proyecto):
- **Backend**: Root Directory `backend`, variables de entorno `ANTHROPIC_API_KEY`,
  `PERPLEXITY_API_KEY`, `FRONTEND_ORIGIN` (URL real del frontend ya desplegado).
- **Frontend**: Root Directory `frontend`, variable `NEXT_PUBLIC_BACKEND_URL` (URL real del
  backend ya desplegado).
