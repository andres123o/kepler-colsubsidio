# Brief SOTA — Track 1 Colsubsidio: Modelos de hiperpersonalización de crédito
**Kepler / Stateless Labs — Hackathon Colsubsidio × 30X**
**Fecha:** 21 de julio de 2026 · Kickoff 22 de julio
**Estatus del dato:** sin dataset entregado. Todo lo siguiente es condicional al schema real. El supuesto de carga se declara explícito en cada fila.

---

## 0. Encuadre correcto del problema (antes de cualquier modelo)

Colsubsidio pide un motor que decida **{producto, momento, canal}** por afiliado para maximizar la toma incremental de crédito. Backward desde esa decisión de negocio, el problema se descompone en cuatro sub-problemas, y **cada uno tiene una familia de modelo distinta que le corresponde**:

| Sub-pregunta de negocio | Objeto matemático | Familia correcta |
|---|---|---|
| ¿Qué producto? | Ranking de propensión por producto | GBM tabular calibrado |
| ¿Vale la pena ofrecerlo (o iba a tomarlo igual)? | CATE — efecto incremental de la oferta | Uplift / meta-learners (roadmap) |
| ¿Cuándo? | Hazard h(t\|x) con censura | Supervivencia / time-to-event |
| ¿Por qué canal, con qué exploración? | Política que balancea explotar/explorar | Contextual bandit |

**Error a evitar:** tratar esto como un problema de recomendación tipo Netflix/Spotify. El catálogo de crédito es ~10 productos, no millones; cada afiliado toma crédito un puñado de veces en su vida, no miles de interacciones. El régimen de datos es *catálogo minúsculo + positivos ultra-esparsos + clase desbalanceada*, no *catálogo gigante + interacciones densas*. La maquinaria de retrieval (two-tower, ANN) resuelve un problema que Colsubsidio no tiene.

**El moat real:** la señal conductual cross-vertical (droguería, recreación, educación, vivienda, salud, turismo) que ningún banco ve. El precedente no es Netflix — es Ant Financial / scoring cross-domain de super-apps. Confirmado: Colsubsidio opera crédito (educación, libre inversión, compra de cartera, vivienda) sobre ~1.5M afiliados con datos multi-vertical reales.

---

## 1. Matriz comparativa de enfoques

Leyenda viabilidad 5 días: 🟢 MVP factible · 🟡 factible parcial / como feature · 🔴 fuera de alcance (va a roadmap).

### 1.1 GBM de propensión + SHAP (calibrado)
- **Fundamento matemático:** P(toma_producto_k | x) vía gradient boosting (XGBoost/LightGBM/**CatBoost** — CatBoost por manejo nativo de las muchas categóricas de caja). Multiclase o one-vs-rest por producto. Calibración isotónica/Platt obligatoria: el argmax de valor esperado río abajo necesita probabilidades verdaderas, no scores. SHAP (valores de Shapley) como "por qué" que el agente usa como argumento.
- **Datos:** tabular estándar — atributos del afiliado + tenencia histórica de productos + features cross-vertical. Es el requisito más bajo.
- **Precedente:** stack estándar de scoring/propensión en banca; es el stack en producción de Kepler en Trii (XGBoost+SHAP).
- **Viabilidad:** 🟢 Es el MVP.
- **Rol en Kepler:** Capa 1. Núcleo del entregable ejecutable.
- **Debilidad:** asociacional, no causal. Predice quién toma, no a quién *mover*.

### 1.2 Uplift / meta-learners (T-learner, X-learner, DR-learner)
- **Fundamento:** CATE τ(x) = E[Y(1)−Y(0)|X=x]. T-learner: dos modelos separados tratado/control. X-learner (Künzel et al. 2019): imputa efectos individuales en cada brazo y los combina ponderando por propensity — mejor bajo asignación desbalanceada. DR-learner: pseudo-outcome doblemente robusto con cross-fitting, con garantías bajo estimación flexible de nuisance.
- **Datos:** **requiere asignación aleatoria o tratamiento loggeado con propensity conocida.** Sin esto no hay identificación — se estima ruido. Un dataset estático de atributos+tenencia NO lo tiene.
- **Precedente:** Booking.com, Swiggy, Criteo uplift; EconML (Microsoft), CausalML (Uber).
- **Viabilidad:** 🔴 como MVP (falta la data de tratamiento). 🟢 como roadmap una vez el bandit genera data.
- **Rol en Kepler:** Capa 3. Es la respuesta a "¿por qué no lo copia un banco?" — el moat compone: cada semana de ejecución genera data propietaria treatment→response.
- **Supuesto de carga:** si el dataset SÍ trae ofertas loggeadas con flag de tratamiento, esto sube de roadmap a MVP.

### 1.3 Causal forest (Wager & Athey 2018; Athey, Tibshirani, Wager 2019)
- **Fundamento:** random forest que particiona el espacio de covariables maximizando heterogeneidad del efecto de tratamiento (no de la varianza del outcome). Estimación no-paramétrica de τ(x) con intervalos de confianza válidos (honest splitting).
- **Datos:** igual restricción causal que 1.2. Costo computacional mayor que meta-learners.
- **Precedente:** referencia académica de HTE; benchmark estándar en la literatura de uplift.
- **Viabilidad:** 🔴 MVP · 🟡 roadmap (buena para intervalos de confianza sobre el efecto, útil para el reporte a stakeholders escépticos — el caso Diego Torres en Trii).
- **Rol en Kepler:** Capa 3, estimador alternativo a X/DR-learner.

### 1.4 Matrix factorization clásico
- **Fundamento:** R ≈ U·Vᵀ, factores latentes usuario/ítem por descomposición de la matriz de interacción.
- **Datos:** matriz usuario×ítem con densidad razonable. Aquí la matriz es ~N×10 con positivos rarísimos — casi degenerada. No aprovecha side-features (limitación central de MF).
- **Precedente:** Netflix Prize (2009). Contexto equivocado para este caso.
- **Viabilidad:** 🔴 baja utilidad; el catálogo es demasiado chico y las side-features son justo el moat que MF ignora.
- **Rol en Kepler:** ninguno para crédito. Posible para cross-sell *dentro* de una vertical de alto volumen (droguería), no para el catálogo de crédito.

### 1.5 Two-tower deep retrieval (YouTube DNN; Google Play)
- **Fundamento:** encoders independientes g(usuario), h(ítem); score = ⟨g,h⟩; sampled softmax sobre catálogo masivo + ANN (Faiss) para retrieval sublineal. Resuelve *retrieval desde billones de ítems*.
- **Datos:** millones de ítems, interacciones densas continuas. Colsubsidio: ~10 productos de crédito → el retrieval es trivial, no necesitas ANN.
- **Precedente:** YouTube (Covington et al. 2016), Alibaba (100M productos). Escala que no aplica.
- **Viabilidad:** 🔴 arquitectónicamente mal ajustado al catálogo de crédito.
- **Rol en Kepler:** ninguno para crédito. Reconsiderar solo si el reto se expande a recomendación sobre catálogo grande (convenios comerciales, +900 aliados; turismo).

### 1.6 Modelos secuenciales / atención (DIN, DIEN, SASRec, BERT4Rec)
- **Fundamento:** self-attention sobre el historial de comportamiento del usuario (SASRec, BERT4Rec) o attention sobre interés local respecto al ítem candidato (DIN/DIEN de Alibaba). Capturan orden y evolución del interés.
- **Datos:** secuencias largas de interacción por usuario. Para *crédito* las secuencias son cortísimas. Para *comportamiento cross-vertical* (compras droguería, uso recreación) sí hay secuencia rica.
- **Precedente:** Alibaba (DIN/DIEN), SASRec/BERT4Rec en RecSys.
- **Viabilidad:** 🔴 para el evento crédito · 🟡 como **encoder de historial cross-vertical** cuyo embedding entra como feature al GBM — solo si hay volumen y tiempo.
- **Rol en Kepler:** posible enriquecedor de features en Capa 0, fase 2.

### 1.7 Grafo heterogéneo / HeteroGNN
- **Fundamento:** grafo afiliado–familia–empleador–producto–uso; message passing con atención (HAN, R-GCN) para capturar relaciones que un modelo tabular no ve (efectos de red familiar/empleador).
- **Datos:** relaciones explícitas ensambladas en grafo + volumen. ETL pesado.
- **Precedente:** la literatura fintech de GNN es **abrumadoramente fraude/AML**, no recomendación de ofertas. Señal de alerta: poco precedente en el uso exacto que se propone.
- **Viabilidad:** 🔴 MVP (ETL se come los 5 días; lo más difícil de explicar en decisión regulada).
- **Rol en Kepler:** slide de visión. Steelman: si el dataset trae tablas relacionales con vínculos familia/empleador y volumen, un embedding de HeteroGNN *como feature* del GBM (no end-to-end) puede sumar en fase 2.

### 1.8 Supervivencia / time-to-event (Cox PH, DeepSurv, MTLR, hazard discreto)
- **Fundamento:** función de hazard h(t|x) = riesgo instantáneo de tomar el producto en t dado que no lo tomó antes; función de supervivencia S(t). **Maneja censura a la derecha**: el afiliado que aún no toma es censurado, no negativo — corrección clave sobre el clasificador binario. Cox PH interpretable; DeepSurv/MTLR para no-linealidad (DeepSurv fue superior a RandForest/MTLR en comparativas de purchase-timing).
- **Datos:** timestamps de origen y evento por afiliado/producto. Granularidad temporal es el requisito.
- **Precedente:** buy-till-you-die / time-to-next-purchase; CoxPH para time-to-open de campañas.
- **Viabilidad:** 🟢/🟡 según granularidad temporal del dataset. Un hazard discreto sobre bins semanales es rápido de montar.
- **Rol en Kepler:** Capa 2. El "cuándo". Diferenciador SOTA que la mayoría de equipos omite.

### 1.9 Contextual bandit (Thompson Sampling)
- **Fundamento:** política que en cada ronda elige oferta/canal muestreando de la posterior de la recompensa esperada por brazo; balancea explotar (lo que sabe que funciona) vs. explorar (generar información). Genera, por diseño, la data de tratamiento con propensity conocida que hace CATE identificable.
- **Datos:** requiere el loop de ejecución (no un dataset estático). Es el mecanismo, no el modelo offline.
- **Precedente:** personalización de ofertas en producción (news, e-commerce, fintech).
- **Viabilidad:** 🔴 implementar en 5 días · 🟢 como *diseño* del data flywheel en el pitch.
- **Rol en Kepler:** Capa 3-4. Convierte la ejecución en el generador de la data causal. Es el puente honesto entre el MVP asociacional y el sistema causal maduro.

### 1.10 Mixture-of-experts / segmentación interpretable + modelos locales
- **Fundamento:** segmentación (latent class / GMM / árbol) para cold-start y narrativa + scoring fino dentro de cada segmento (gating de MoE). Balancea interpretabilidad (pitch, regulación) y precisión individual.
- **Datos:** tabular. Bajo requisito.
- **Precedente:** mixture-of-experts en credit/limits (WSDM 2021, e-commerce lending).
- **Viabilidad:** 🟢 la segmentación es rápida y vende bien; los expertos locales son el GBM de 1.1.
- **Rol en Kepler:** Capa 0 (segmentación para cold-start y pitch) envolviendo Capa 1.

---

## 2. Arquitectura híbrida recomendada

Backward desde la decisión del agente {producto, momento, canal}:

```
CAPA 0 — FEATURE STORE CROSS-VERTICAL  (el moat)
  Features de droguería, recreación, educación, vivienda, salud, turismo.
  RFM por vertical + recencia de life-events (matrícula escolar → propensión
  crédito educativo; interacción subsidio vivienda → propensión hipotecaria).
  Segmentación interpretable (GMM / árbol) para cold-start y narrativa de pitch.
        │
        ▼
CAPA 1 — PROPENSIÓN / RANKING  (MVP, ejecutable en 5 días)
  GBM (CatBoost) → P(toma | x, ofrecido) por producto, CALIBRADO.
  SHAP como argumento del "por qué" por afiliado.
        │
        ▼
CAPA 2 — TIMING  (el "cuándo")
  Hazard h(t|x) por producto (Cox / hazard discreto / DeepSurv).
  Maneja censura. Convierte "qué" en "qué + cuándo".
        │
        ▼
CAPA 3 — CAUSAL / FLYWHEEL  (roadmap que lo hace SOTA y honesto)
  CATE(oferta, canal) vía X/DR-learner o causal forest,
  identificable gracias a data generada por bandit (Thompson).
        │
        ▼
CAPA 4 — POLÍTICA / AGENTE
  argmax  E[valor incremental]  =  CATE × valor × ajuste_repago
          sujeto a  hazard-timing, canal, elegibilidad regulatoria,
          fatiga de contacto.
  SHAP adjunto a cada recomendación como argumento auditable.
```

### El razonamiento matemático de por qué (no solo el veredicto)

El objetivo **no** es max P(toma). Ese es el error clásico de uplift: maximizar propensión targetea a los *sure-things* (los que tomarían igual) → oferta desperdiciada + riesgo de sobreendeudamiento (pasivo legal bajo Habeas Data y deber de información). El objetivo correcto es:

```
maximizar   τ(x)·v_k·r(x)      [efecto incremental × valor producto × ajuste repago]
sujeto a    trigger cuando h(t|x) cruza umbral   [timing por hazard]
```

donde τ(x) es el CATE. El **MVP aproxima** τ(x) con propensión calibrada + reglas de negocio (porque no hay data de tratamiento). El **sistema maduro sustituye** la aproximación por un τ(x) identificado desde la data del bandit. Esa progresión — de aproximación asociacional a identificación causal vía el propio loop de ejecución — es la historia a prueba de data scientist senior, y es exactamente la epistemología de Kepler: SHAP como puntero de atención, test/control como única prueba causal.

---

## 3. Restricción regulatoria (corrige el supuesto SFC del brief)

- Colsubsidio **no** está vigilada por la SFC para su crédito (no es establecimiento de crédito). Vigilancia = **Superintendencia del Subsidio Familiar**.
- Matiz Ley 789/2002 art. 16: la SuperSubsidio vigila las operaciones de crédito de las cajas *aplicando las reglamentaciones de administración de riesgo crediticio que la superintendencia bancaria (hoy SFC) dicta para establecimientos de crédito* → principios tipo SARC cascadean indirectamente.
- Restricción vinculante para un modelo de scoring/oferta: **Habeas Data (Ley 1266 de 2008)** sobre dato crediticio + deber de información al afiliado (Ley 789 art. 24, vigilancia de SuperSubsidio sobre la información dada a usuarios).
- **Implicación:** decisión explicable a nivel individual → mata el deep model puro *para la decisión de crédito* y vindica SHAP-sobre-GBM.
- **Distinción estratégica:** una *oferta* (marketing) es objeto regulatorio más liviano que una *aprobación de crédito*. Kepler recomienda oferta/timing/canal; el underwriting se queda en el motor de riesgo existente de Colsubsidio. Más limpio legalmente y más vendible políticamente.

---

## 4. Qué cambiaría la recomendación (supuestos de carga)

1. **Si el dataset trae ofertas loggeadas con flag de tratamiento y propensity** → uplift/CATE sube de roadmap a MVP. Cambia todo: el MVP se vuelve causal desde el día 1.
2. **Si trae secuencias transaccionales cross-vertical de alto volumen** → un encoder secuencial (SASRec) como generador de embeddings-feature para el GBM se vuelve viable en fase 2.
3. **Si trae tablas relacionales con vínculos familia/empleador explícitos + volumen** → HeteroGNN como feature (no end-to-end) entra a evaluación de fase 2.
4. **Si la granularidad temporal es pobre (solo snapshots)** → la Capa 2 (supervivencia) se degrada a un clasificador de ventana; documentar la pérdida.

**Primera acción al recibir el dataset:** analizar schema, granularidad temporal y volumen ANTES de comprometerse con familia de modelo. La elección se ancla a los datos reales, no a la familia de moda.

---

## 5. Referencias clave (para defender ante DS senior)

- Wager & Athey (2018); Athey, Tibshirani & Wager (2019) — causal forest / HTE.
- Künzel et al. (2019) — X-learner. Kennedy (DR-learner).
- EconML (Microsoft), CausalML (Uber) — implementación uplift.
- Covington et al. (2016) — YouTube DNN / two-tower.
- Zhou et al. — DIN/DIEN (Alibaba). SASRec, BERT4Rec — secuenciales.
- Katzman et al. — DeepSurv; MTLR — supervivencia ML.
- Literatura Ant Financial / super-app cross-domain scoring — precedente del moat cross-vertical.
- Ley 1266/2008 (Habeas Data), Ley 789/2002, Decreto 2595/2012 — marco regulatorio caja.


Verdicto: para el MVP del hackathon con un dataset estático, las variables de mercado aportan casi cero a la personalización por persona y cuestan tiempo. Ganan su lugar en exactamente dos puntos: la capa de timing y como interacciones. Google Trends: fase 2, no MVP. Robustecer con macro aquí es un error de Occam, no una mejora. El razonamiento:

Por qué el macro no personaliza (el punto que un DS senior no te tumba). Una variable macro en el tiempo t —inflación 6.5%, tasa 12%— es constante para todos los afiliados en ese instante. En un corte transversal (snapshot de afiliados) tiene varianza cero entre filas. Un árbol/GBM literalmente no puede partir sobre una columna donde todas las filas valen lo mismo: no distingue al afiliado A del B, que es exactamente lo que necesitas para personalizar. Agregar "inflación = 6.5%" a cada fila no añade información; añade una columna muerta que diluye el SHAP (costo regulatorio) sin ganancia.

La única forma en que el macro entra a nivel individual: como interacción. inflación × nivel_ingreso, tasa × carga_de_deuda_actual. Eso sí tiene varianza transversal y captura sensibilidad diferencial: cuando sube la tasa, el afiliado con deuda alta (candidato a compra de cartera) responde distinto al de deuda baja. El macro solo no; el macro × rasgo-heterogéneo sí. Ese es el movimiento sofisticado, y solo vale la pena si tienes la variable individual que interactúa.

Dónde el macro sí tiene señal real: la dimensión temporal, no la transversal.

Capa 2 (timing / hazard): el macro modula el hazard base h₀(t) — cuándo pica la demanda de cada producto. Cox con covariable tiempo-variante. Esto es legítimo pero requiere que el dataset tenga múltiples ventanas temporales.
Capa de forecasting agregado (el "cuántos"): si Kepler proyecta volumen semanal de toma de crédito, el macro es regresor válido a nivel agregado. Es literalmente el es_exogena=1 que ya usas en Trii: la tasa de BanRep afecta el ángulo del copy de CDT. Mismo principio.

Google Trends específicamente. No se puede unir por afiliado (es intención de búsqueda nacional agregada, no per-persona) → cero para personalización. Como nowcasting de demanda de categoría a nivel agregado es plausible pero ruidoso y nacional; para 5 días es distracción. Su único uso legítimo en el hackathon es como evidencia en la narrativa del pitch (una slide de contexto de demanda), no como feature del modelo.

El principio es_exogena aplica igual acá. Flaggea los shocks exógenos (decisión de tasa, alza de salario mínimo, días promocionales) para que el modelo no aprenda artefactos de calendario como si fueran conducta del afiliado. Se excluyen como driver de entrenamiento pero se conservan para feature engineering y atribución.

El momento macro actual — y aquí sí hay un ángulo de pitch afilado. BanRep subió a 12% el 30 de junio (+75pbs, ciclo contractivo), con inflación 2026 proyectada por su equipo técnico por encima de 6.5% al cierre. Colsubsidio posiciona su crédito con tasas por debajo del sistema financiero tradicional. En un entorno de tasas al alza, la brecha entre el crédito de la caja y el crédito bancario se ensancha → la propuesta de valor relativa del crédito Colsubsidio se fortalece justo ahora. Ese es un insight de contexto de demanda que refuerza el pitch sin necesidad de meter macro como feature por persona. Es narrativa, no modelo.

Sobre "robustecer". Para 5 días, la robustez viene de calibración, validación honesta (encuadre test/control) y manejo correcto de censura/desbalance — no de apilar features macro débilmente relevantes sobre un modelo transversal. Cada columna exógena de varianza cero infla riesgo de overfitting y ensucia la explicabilidad que la regulación exige. Menos es más aquí.

Qué cambiaría esto (el pivote):

Si el dataset es un panel temporal (varias ventanas de observación) y no un snapshot → el macro gana varianza temporal y entra legítimo en la capa hazard/forecasting.
Si el target incluye repago/default (no solo toma) → el macro pesa mucho más, porque el default es macro-sensible. Pero eso es underwriting, que dijimos se queda en el motor de riesgo de Colsubsidio.
Si te dan 3+ años de historia → puedes estimar sensibilidad a la tasa por segmento (la interacción), y eso sí sería un diferenciador genuino.

Resumen operativo: el dataset solo es viable para el MVP; el macro no lo robustece a nivel persona. Guárdalo para la capa temporal (si el dato es panel) y para la narrativa de contexto de demanda en el pitch. Si quieres, integro esta sección al brief como apéndice "Rol de variables exógenas" para que quede en un solo documento para el equipo.