import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="Importar / Exportar", page_icon="📥", layout="wide")

st.title("📥 Módulo 7: Gestión de Archivos y Datos")
st.markdown("Guarda tu progreso localmente o recupera un proyecto guardado previamente.")

# Inicializar estructuras de datos si no existen
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}
if 'partidas_manuales' not in st.session_state:
    st.session_state['partidas_manuales'] = []

col_exp, col_imp = st.columns(2)

# --- SECCIÓN DE EXPORTACIÓN (GUARDAR) ---
with col_exp:
    st.header("📤 Exportar Proyecto Actual")
    st.write("Descarga toda la configuración de circuitos, motores y datos financieros en un único archivo de respaldo.")
    
    if st.session_state['proyecto'] or st.session_state['partidas_manuales']:
        # Empaquetamos todo el estado de la sesión relevante en un diccionario estructurado
        datos_totales = {
            "version_aplicacion": "1.0",
            "elementos_calculados": st.session_state['proyecto'],
            "partidas_manuales": st.session_state['partidas_manuales']
        }
        
        # Convertimos el diccionario a formato JSON (identado para lectura humana fácil)
        json_string = json.dumps(datos_totales, indent=4, ensure_ascii=False)
        
        st.info(f"📋 Elementos listos para exportar: {len(st.session_state['proyecto'])} circuitos/sistemas.")
        
        # Botón de descarga para el archivo JSON
        st.download_button(
            label="💾 Descargar Archivo del Proyecto (.json)",
            data=json_string,
            file_name="respaldo_proyecto_electrico.json",
            mime="application/json"
        )
    else:
        st.warning("⚠️ No hay datos registrados en este momento para poder exportar.")

# --- SECCIÓN DE IMPORTACIÓN (CARGAR) ---
with col_imp:
    st.header("📥 Importar Proyecto Existente")
    st.write("Sube un archivo `.json` generado anteriormente por esta plataforma para restaurar la sesión de trabajo.")
    
    archivo_subido = st.file_uploader("Selecciona el archivo del proyecto", type=["json"])
    
    if archivo_subido is not None:
        try:
            # Leer y parsear el archivo JSON cargado por el usuario
            datos_cargados = json.load(archivo_subido)
            
            # Validar de manera simple que el formato corresponda a nuestra app
            if "elementos_calculados" in datos_cargados and "partidas_manuales" in datos_cargados:
                
                # Caja de confirmación para no machacar datos por error
                st.warning("⚠️ Al cargar el archivo se sobrescribirán los datos que tengas actualmente en la sesión.")
                if st.button("Confirmar y Cargar Datos"):
                    st.session_state['proyecto'] = datos_cargados["elementos_calculados"]
                    st.session_state['partidas_manuales'] = datos_cargados["partidas_manuales"]
                    st.success("✔️ ¡Proyecto restaurado con éxito! Ya puedes navegar por las pestañas para ver los cálculos y la memoria.")
            else:
                st.error("❌ El formato del archivo JSON no es compatible con esta aplicación.")
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")

# --- INSPECTOR DE DATOS CRUDOS ---
st.write("---")
with st.expander("🔍 Desarrollador: Ver estructura interna del Session State"):
    st.write("Variables actuales en memoria temporal:")
    st.json({
        "proyecto_actual": st.session_state['proyecto'],
        "partidas_manuales": st.session_state['partidas_manuales']
    })
