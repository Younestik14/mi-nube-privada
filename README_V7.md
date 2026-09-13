# REBT Suite — Diseñador Pro v7

Rediseño de la capa de diseño eléctrico integrado sobre la aplicación existente.

## Mejoras
- Dashboard de proyecto con KPIs.
- Editor de circuitos con búsqueda y edición.
- Plantillas por uso y auto-dimensionado preliminar.
- Cálculo de Ib y caída de tensión estimada.
- Inspector con errores, avisos y comprobaciones OK.
- Reparto de cargas por L1/L2/L3.
- Unifilar SVG generado automáticamente.
- Presupuesto preliminar y exportación de mediciones a Excel.
- Exportación/importación JSON con esquema v7.
- Módulos separados `v7_engine.py` y `v7_ui.py` para evitar seguir ampliando el `app.py` monolítico.

## Importante
Los valores de intensidad admisible y las comprobaciones son de **prevalidación orientativa**. Para un proyecto profesional hay que verificar método de instalación, temperatura, agrupamiento, tipo de conductor, aislamiento, longitud total, cortocircuito, selectividad, REBT/UNE y tablas aplicables.
