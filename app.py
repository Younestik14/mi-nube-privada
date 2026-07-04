# 🏠_Inicio.py
import streamlit as st
from auth import verificar_acceso # Importa la lista de aprobados

st.set_page_config(page_title="Mi Nube Privada", layout="wide")

if 'autorizado' not in st.session_state:
    st.session_state.autorizado = False

if not st.session_state.autorizado:
    st.title("🔐 Acceso a la Oficina Técnica")
    id_input = st.text_input("Introduce tu Número Regional para entrar:", type="password")
    
    if st.button("Acceder"):
        if verificar_acceso(id_input):
            st.session_state.autorizado = True
            st.rerun() 
        else:
            st.error("Acceso denegado. Si ya solicitaste acceso, espera a que el admin te acepte.")
    
    st.stop() # Bloquea el resto de la página

# Si llega aquí, es porque está autorizado
st.success("Acceso concedido.")

# Título Principal
st.title("⚡ CoreElec: Plataforma de Ingeniería Eléctrica")
st.subheader("Herramienta integral de cálculo, diseño y presupuestado")

st.markdown("""
Bienvenido a la plataforma modular para proyectos eléctricos e industriales. 
Utiliza el menú de la izquierda para navegar por los diferentes módulos de cálculo y gestión.
""")

# Ventana de Ayuda / Guía Rápida integrada en el Home
st.header("❓ Ventana de Ayuda y Documentación")

with st.expander("📖 ¿Cómo usar los módulos de cálculo?"):
    st.write("""
    1. **Cálculo de Sección:** Introduce la potencia, tensión, longitud y tipo de instalación (CNE / IEC) para obtener la sección de conductor por caída de tensión y densidad de corriente.
    2. **Fotovoltaica:** Dimensionamiento de strings, reguladores, inversores y cálculo de producción solar estimado por ubicación.
    3. **Industrial:** Cálculo de cargas motoras, corregido de factor de potencia ($\cos \phi$) y arranque de motores.
    """)

with st.expander("📊 Gestión de Archivos (Importar/Exportar)"):
    st.write("""
    Puedes guardar tu progreso en la pestaña **Importar/Exportar**. El sistema genera un archivo en formato `.json` 
    con todos los datos introducidos para que puedas retomar el proyecto en cualquier momento sin perder datos.
    """)

with st.expander("🛠️ Notas sobre el Esquema Unifilar y Memoria"):
    st.write("""
    - El módulo de **Esquema Unifilar** genera un árbol lógico basado en los circuitos calculados en los módulos previos.
    - La **Memoria Técnica** recopila los resultados finales y permite exportar un borrador estructurado en formato Word (`.docx`) o PDF.
    """)

st.info("💡 **Consejo:** Asegúrate de rellenar los datos en orden (Cálculos -> Mediciones -> Presupuesto) para que el flujo de datos sea automático.")
