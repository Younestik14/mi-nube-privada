# REBT Suite v5.0

Capa de evolución para **mi-nube-privada**. Conserva la aplicación original y añade un módulo de proyecto eléctrico:

- Gestor de proyecto v5
- Circuitos y cargas
- Inspector REBT orientativo
- Unifilar SVG automático
- Exportación del proyecto a JSON
- Tabla resumen de circuitos
- Arquitectura modular (`v5_engine.py` + `v5_ui.py`)

## Arranque

```bash
pip install -r requirements.txt
streamlit run app.py
```

En la aplicación entra en **Proyecto → Diseñador v5**.

## Nota técnica

Las comprobaciones nuevas son una capa de apoyo al diseño. Los valores de intensidad admisible utilizados por el inspector son referencias simplificadas y no sustituyen la selección mediante la tabla/método de instalación, temperatura, agrupamiento, aislamiento, caída de tensión y demás condiciones aplicables.

Antes de utilizar una salida en un proyecto real, contrastar con el REBT/Guías-BT y las normas UNE/HD vigentes.
