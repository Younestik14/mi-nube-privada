import streamlit as st

st.set_page_config(page_title="Memoria Técnica", page_icon="📝", layout="wide")

st.title("📝 Módulo 6: Generación de Memoria Técnica")
st.markdown("Generación automática del documento descriptivo y justificativo del proyecto.")

# Recuperar todos los datos del estado de la sesión
elementos_proyecto = st.session_state.get('proyecto', {})
resumen_economico = st.session_state.get('resumen_economico', {})
cuadro_general = st.session_state.get('cuadro_general', {})

if not elementos_proyecto:
    st.warning("⚠️ No hay datos suficientes para generar la memoria. Por favor, calcula y guarda elementos en los módulos anteriores.")
else:
    # --- CONFIGURACIÓN DE LOS DATOS DEL PROYECTO ---
    st.sidebar.header("📋 Datos de Cabecera")
    titulo_proy = st.sidebar.text_input("Título del Proyecto", value="Instalación Eléctrica Industrial y FV")
    proyectista = st.sidebar.text_input("Técnico / Proyectista", value="Ingeniero Técnico")
    cliente = st.sidebar.text_input("Cliente / Empresa", value="Industrias Delta S.L.")
    ubicacion = st.sidebar.text_input("Ubicación", value="Polígono Industrial Cabezo Beaza, Cartagena")

    # --- ESTRUCTURACIÓN DEL TEXTO DE LA MEMORIA ---
    st.subheader("📄 Vista Previa del Documento")

    # Construimos el cuerpo del texto en una variable string para poder exportarla después
    memoria_texto = f"""# MEMORIA TÉCNICA JUSTIFICATIVA

## 1. DATOS GENERALES
* **Proyecto:** {titulo_proy}
* **Ubicación:** {ubicacion}
* **Promotor / Cliente:** {cliente}
* **Redactor del Proyecto:** {proyectista}

---

## 2. OBJETO DE LA INSTALACIÓN
El objeto de la presente memoria es definir, justificar y describir los cálculos técnicos de la instalación eléctrica y de generación de energía solar fotovoltaica para el suministro óptimo de los receptores solicitados por el cliente, cumpliendo estrictamente con la normativa reglamentaria vigente (REBT / CNE).

---

## 3. DESCRIPCIÓN TÉCNICA DE LOS CIRCUITOS Y SISTEMAS
A continuación se detallan los elementos calculados e integrados en el sistema:
"""

    # Bucles para inyectar la información técnica guardada
    for nombre, datos in elementos_proyecto.items():
        if "sistema" in datos: # Línea del Módulo 1
            memoria_texto += f"""
### ⚡ Línea Distribución: {nombre}
* **Tipo de Sistema:** {datos['sistema']} ({datos['tension']} V)
* **Intensidad de Diseño:** {datos['intensidad']} A
* **Conductor Adjudicado:** {datos['seccion']} mm² en material de {datos['material']}.
* **Longitud del tendido:** {datos['longitud']} metros.
"""
        elif "potencia_kwp" in datos: # FV del Módulo 2
            memoria_texto += f"""
### ☀️ Instalación Solar: {nombre}
* **Modalidad:** {datos['tipo']}
* **Potencia Pico Total:** {datos['potencia_kwp']} kWp
* **Número de Módulos:** {datos['num_paneles']} unidades de alta eficiencia.
* **Capacidad Acumulación:** {datos['batería_ah']} Ah (si aplica).
"""
        elif "kvar_bateria" in datos: # Motores del Módulo 3
            memoria_texto += f"""
### 🏭 Carga Industrial: {nombre}
* **Tipo:** {datos['tipo']}
* **Potencia Nominal:** {datos['potencia_kw']} kW
* **Corriente de Operación:** {datos['intensidad']} A
* **Compensación de Reactiva asociada:** {datos['kvar_bateria']} kVAr.
"""

    # Añadir sección de protecciones si se configuró el esquema unifilar
    if cuadro_general:
        memoria_texto += f"""
---

## 4. PROTECCIÓN Y APARAMENTA
El cuadro principal denominado **{cuadro_general['nombre']}** contará con una protección de cabecera armada con un Interruptor General Automático (IGA) de **{cuadro_general['iga']} A**, garantizando la protección contra sobreintensidades y cortocircuitos de la instalación aguas abajo.
"""

    # Añadir resumen económico si está disponible
    if resumen_economico:
        memoria_texto += f"""
---

## 5. RESUMEN ECONÓMICO DEL PROYECTO
El coste de ejecución material y de contrata de la obra se resume en las siguientes partidas económicas consolidadas:
* **Presupuesto Base Imponible:** {resumen_economico['base_imponible']:,.2f} €
* **Presupuesto con Gastos y Beneficio Industrial:** {resumen_economico['total_con_beneficio']:,.2f} €
* **PRECIO DE VENTA FINAL (CON IVA INCLUIDO): {resumen_economico['precio_final']:,.2f} €**
"""

    # Mostrar la memoria formateada de forma elegante en la UI de Streamlit
    st.markdown(memoria_texto)

    st.write("---")
    st.subheader("💾 Descarga de Documentación")
    
    # Botón de descarga nativo de Streamlit para el archivo .txt/.md de la memoria
    st.download_button(
        label="📥 Descargar Memoria Técnica (.md)",
        data=memoria_texto,
        file_name=f"Memoria_{titulo_proy.replace(' ', '_')}.md",
        mime="text/markdown"
    )
    st.info("💡 Consejo: El archivo se descarga en formato Markdown (.md), que es perfectamente compatible con Word, Typora o cualquier editor de texto enriquecido.")
