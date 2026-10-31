# REBT Suite v8 — Versión mejorada

Rediseño visual y funcional de la aplicación REBT Suite (Instalaciones Eléctricas).

## Mejoras visuales
- CSS moderno con variables, glassmorphism, gradientes y animaciones.
- Modo oscuro / claro conmutables.
- Sidebar con navegación y KPIs en vivo.
- Hero, tarjetas glass y badges de estado.
- Tipografía Inter, scrollbars personalizados, accesibilidad mejorada.

## Mejoras funcionales
- Integración del Diseñador Pro v7 como vista principal.
- Dashboard con KPIs (circuitos, potencia, errores, OK).
- Gráfico de potencia por circuito (Plotly).
- Inspector REBT con métricas y comprobaciones.
- Unifilar SVG generado automáticamente.
- Presupuesto con exportación a Excel y totales.
- Exportación/importación de proyectos en JSON.
- Validación inline y notificaciones.

## Archivos
- `app.py` — punto de entrada (antes app_v8.py).
- `v8_styles.py` — estilos modernos.
- `v7_ui.py` — UI del Diseñador Pro (mejorada).
- `v7_engine.py` — motor de cálculo.
- `requirements.txt` — dependencias.

## Ejecutar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desplegar en Streamlit Cloud
Sube esta carpeta a tu repo de GitHub y conecta Streamlit Cloud apuntando a `app.py`.

## Aviso
Herramienta de apoyo al predimensionado. Verifica los valores críticos antes de un uso profesional.
