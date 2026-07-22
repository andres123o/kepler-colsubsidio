# Kepler para Colsubsidio — Hackathon Colsubsidio × 30X (Reto 1: Crédito Hiperpersonalizado)

Motor de decisión que, por afiliado, determina **qué** producto de crédito ofrecer, **cuándo**
y **por qué canal** — usando el perfil enriquecido del afiliado (incluyendo señal conductual
cross-vertical: droguería, recreación, educación, vivienda, salud, turismo) en vez de solo
variables financieras clásicas.

Instancia del sistema general de Kepler (entender usuarios vía ML/DeepL → volver eso accionable
en comunicaciones hiperpersonalizadas) aplicada a Colsubsidio. Repo independiente — no reutiliza
código del backend/frontend de la instancia Trii.

## Estado

- [x] Research Track 1 (modelo) — ver `resultado1.md`
- [x] Research Track 2 (canales/stack Colsubsidio) — ver `resultado2.md`
- [ ] Dataset del hackathon — pendiente de recibir
- [ ] Scaffold del pipeline (feature store → propensión+SHAP → timing → decisión)
- [ ] Demo end-to-end

## Estructura

```
colsubsidio/
  resultado1.md   — brief SOTA de modelos de personalización (research Opus 4.8)
  resultado2.md    — mapeo de canales/stack real de Colsubsidio
  data/
    sample/        — datos sintéticos/de ejemplo (el dataset real NUNCA se commitea, ver .gitignore)
  backend/         — pipeline de modelo + API (por definir)
  frontend/        — demo/UI (por definir)
```

## Notas de seguridad

El dataset que entregue Colsubsidio en el hackathon es de afiliados reales — cae bajo Habeas
Data (Ley 1266/2008). **Nunca se commitea al repo**, ni siquiera en un repo privado. Usar
`data/sample/` con datos sintéticos para desarrollo y pruebas.
