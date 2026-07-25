# Kepler para Colsubsidio — Hackathon Colsubsidio × 30X (Reto 1: Crédito Hiperpersonalizado)

Motor de decisión que, por afiliado, determina **qué** producto de crédito ofrecer, **cuándo**
y **por qué canal** — usando el perfil enriquecido del afiliado (incluyendo señal conductual
cross-vertical: droguería, recreación, educación, vivienda, salud, turismo) en vez de solo
variables financieras clásicas.

Instancia del sistema general de Kepler (entender usuarios vía ML/DeepL → volver eso accionable
en comunicaciones hiperpersonalizadas) aplicada a Colsubsidio. Repo independiente — no reutiliza
código del backend/frontend de la instancia Trii.

## Estado

- [x] Research Track 1 (modelo) y Track 2 (canales/stack Colsubsidio) — notas de research internas, no versionadas
- [x] Dataset del hackathon recibido (`Usos_Productos_Afiliados_SIN_ID.csv`, 1,566,026 filas) y diagnosticado empíricamente
- [x] Documento maestro consolidado — `cnoslidado-estrategia.md` (arquitectura completa, corregida contra el dato real y el marco legal verificado)
- [x] Entorno de trabajo — `.venv` propio del proyecto (ver `## Entorno` abajo)
- [~] Frente A (segmentación: limpieza + MCA + LCA) — en progreso, ver `## Bitácora` abajo
- [ ] Frente B (tablas exógenas θ_k)
- [ ] Scorer aditivo + motor de elegibilidad
- [ ] Política canal/timing + LLM narrador
- [ ] Demo end-to-end

## Estructura

```
colsubsidio/
  Usos_Productos_Afiliados_SIN_ID.csv  — dataset real (NUNCA se commitea, ver .gitignore)
  .venv/                     — entorno Python del proyecto (nunca se commitea)
  segmentacion/              — scripts de Frente A (ver abajo)
```

## Entorno

Python del proyecto vive en `colsubsidio/.venv` (aislado, `--system-site-packages` NO usado —
autocontenido a propósito). Librerías clave: `prince` (MCA), `stepmix` (LCA real sobre
categóricas), `kmodes` (K-prototypes, plan B no usado todavía), `pandas`/`numpy`/`scikit-learn`.
Para correr cualquier script: `.venv\Scripts\python.exe segmentacion\<script>.py` desde la
carpeta `colsubsidio/`.

## Bitácora

### 2026-07-22/23 — Diagnóstico de dato real + arquitectura consolidada + Frente A (segmentación) en curso

**Diagnóstico empírico del dataset (1,566,026 filas, no muestra):** `RANGO_EDAD` tiene 5 buckets
reales (26.6% tiene 46+ años); `CATEGORIA` 75.9% es "A" (mismo tramo de ingreso — el monto no
puede ser el eje de personalización para la mayoría); `ESTADOAFILIADO` 100% constante (fuera del
modelo); `CIUDAD_AFILIADO` 58.3% vacío, agrupado por Región Metropolitana Bogotá-Cundinamarca
(Ley 2199/2022) en vez de departamento crudo; `HOTELES`/`AGENCIAS`/`VIVIENDA` tienen tasa positiva
<0.1% (inservibles como eje de MCA/LCA, sirven como regla de override rara); `DROGUERIA`/`PISCILAGO`
sí cargan señal real (~5-6%); `CATEGORIA=D` tenía solo 2 filas — se excluyó del modelado (no se
puede modelar estadísticamente n=2). Detalle completo con fuentes en `cnoslidado-estrategia.md` §2.

**Corrección legal:** Ley 1266/2008 (Habeas Data financiero) NO aplica a comportamiento
digital/redes sociales — solo a datos financieros/crediticios (DataCrédito/CIFIN). La ley correcta
para el enriquecimiento exógeno es Ley 1581/2012 + Decreto 1377/2013 (régimen general, vigilada
por la SIC), con excepción de dato de fuente pública. El aviso de privacidad real de Colsubsidio
ya autoriza el uso de su data interna para "ofertas y promociones" — Tier 0 legalmente blindado
sin depender de argumento. Ver `cnoslidado-estrategia.md` §10. *Pendiente: el `.gitignore` y la
sección "Notas de seguridad" de este README todavía citan Ley 1266/2008 para el dataset —
técnicamente debería ser Ley 1581/2012, corregir cuando se retome.*

**Frente A — scripts en `segmentacion/`:**
- `01_limpieza.py` — carga el CSV, dropea `ESTADOAFILIADO`, canonicaliza duplicados de
  `PIRAMIDE_NUEVA`, agrupa `CIUDAD_AFILIADO`, recodifica blancos a "Sin dato" explícito, excluye
  `CATEGORIA=D`. Verificado: el bloque de "Sin dato" simultáneo en 4 columnas (13,910 personas) es
  el mismo grupo exacto en las 4, no azar — probablemente afiliados sin perfil completado, insumo
  real para Tier 1 (progressive profiling). Salida: `data_limpia.pkl`.
- `02_mca.py` — MCA (`prince`) sobre 10 columnas categóricas, 5 dimensiones, 33.9% inercia
  acumulada. Dimensión 0 quedó dominada por "Sin dato" (hallazgo real, no bug). Dimensiones 1-4
  muestran ejes de negocio legibles (etapa de vida, formalidad laboral, estructura familiar).
  Salida: `mca_coordenadas.pkl`, `mca_modelo.pkl`.
- `03_lca.py` — LCA real (`stepmix`, medición `categorical`) sobre las mismas 10 columnas
  (integer-encoded). **Versión optimizada** tras un primer intento que no terminó en >1h10min:
  one-hot precalculado una sola vez (antes se recalculaba en cada E-step Y M-step de cada
  iteración — la causa real de la lentitud, no la cantidad de dato), `abs_tol` de 1e-10→1e-6,
  `max_iter` 1000→300, menos inicializaciones. Salida esperada: `lca_pi.pkl` (mezcla suave π_i por
  persona), `lca_modelo.pkl`.
- `benchmark.py` — script de prueba de velocidad controlada (no crítico, se puede borrar o dejar).

**Dónde quedamos — resultado de la búsqueda de K (sobre muestra de 200k, ya corrido):**
```
K= 4  BIC=3,168,961.2 (37 iters)   K= 8  BIC=2,978,719.3 (255 iters)
K= 5  BIC=3,153,347.0 (21 iters)   K= 9  BIC=2,972,561.5 (285 iters)
K= 6  BIC=3,067,525.6 (273 iters) K=10  BIC=2,969,515.1 (98 iters)
K= 7  BIC=3,001,419.1 (300 iters, no convergió) K=12 BIC=2,920,708.5 (204 iters) <- mejor probado
```
**Decisión pendiente, sin resolver:** el BIC sigue bajando hasta K=12 (el candidato más alto
probado) sin doblarse hacia arriba — no hay evidencia de que 12 sea el K óptimo real, solo es el
mejor *de los candidatos probados* (`CANDIDATOS_K = [4,5,6,7,8,9,10,12]` en `03_lca.py`). El
ajuste final (K=12, `n_init=2`, sobre las 1.56M filas completas) se había arrancado en segundo
plano cuando se pausó la sesión — no se dejó terminar.

**Próximos pasos para mañana, en orden:**
1. Decidir: ¿extender `CANDIDATOS_K` a valores más altos (14, 16, 18, 20) para encontrar el
   verdadero punto donde el BIC se da vuelta, antes de gastar el ajuste final en un K que podría
   no ser el correcto? O aceptar K=12 como razonable dado el tiempo del hackathon.
2. Terminar el ajuste final de LCA (el de 1.56M filas completas quedó a medias/matado). Con la
   velocidad real observada (~0.4-0.5s/iteración en la muestra de 200k), el ajuste final sobre el
   100% de la data puede tardar entre 20 y 35 minutos — correrlo con tiempo de sobra, no a las
   carreras.
3. Con `π_i` ya generado: imprimir y revisar los perfiles de cada clase (ya está el código para
   esto en `03_lca.py`), confirmar que las clases tengan lectura de negocio legible.
4. Empezar Frente B (tablas `θ_k` por familia exógena: canal, intereses, macro, demanda) — no
   depende de que Frente A termine del todo para arrancar la parte de investigación de fuentes
   (DataReportal, BanRep/DANE, Google Trends), solo el paso de "traducir a cada clase k" sí espera
   a que Frente A tenga las clases nombradas.

## Notas de seguridad

El dataset que entregó Colsubsidio en el hackathon es de afiliados reales. **Nunca se commitea al
repo**, ni siquiera en un repo privado (ver `.gitignore` — bloquea `*.csv` y `.venv/`). El
tratamiento de esta data interna está cubierto por el aviso de privacidad vigente de Colsubsidio
(autoriza uso para "ofertas y promociones", Ley 1581/2012); cualquier enriquecimiento con
comportamiento digital/redes sociales en producción sí requeriría autorización previa expresa del
titular bajo esa misma ley, salvo dato de fuente pública — ver `cnoslidado-estrategia.md` §10.
