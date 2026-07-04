import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import streamlit as st
# 1. Importas tus funciones de estilo desde la carpeta utils
from utils.style import aplicar_estilo_global, generar_banner
from seguridad import verificar_sesion
verificar_sesion()
# ... resto de tu código de la página ...
# 2. Configuras la página de Streamlit
st.set_page_config(page_title="Mi Apartado - IDEA", layout="wide", initial_sidebar_state="collapsed")

# 3. Aplicas el diseño y generas el banner superior
aplicar_estilo_global()
generar_banner("⚡ Módulo Técnico", "Subtítulo explicativo del cálculo actual.")

# 4. Metes tus componentes dentro de la tarjeta estilizada usando HTML simple
st.markdown('<div class="premium-card"><h4>📋 Parámetros de Diseño</h4>', unsafe_allow_html=True)

# ... AQUÍ VA TODO TU CÓDIGO NORMAL (st.text_input, st.selectbox, st.button, etc.) ...

st.markdown('</div>', unsafe_allow_html=True) # <-- Cierras la tarjeta al final

st.set_page_config(page_title="Memoria Técnica de Diseño MTD", page_icon="📝", layout="wide")

st.title("📝 Módulo 2: Memoria Técnica de Diseño (IEBT)")
st.markdown("Cumplimentación e integración de datos según el modelo oficial de la Dirección General de Energía y Minas.")

# --- INICIALIZACIÓN DEL STATE PARA GUARDAR LOS DATOS DEL DOCUMENTO ---
if 'mtd_datos' not in st.session_state:
    st.session_state['mtd_datos'] = {
        # Titular
        "titular_nombre": "JUAN PÉREZ LÓPEZ", "titular_nif": "23456789X", "titular_direccion": "Calle Mayor 12", "titular_cp": "30392", "titular_poblacion": "La Aljorra",
        # Emplazamiento
        "emp_calle": "Avenida de Murcia 45", "emp_num": "Bajo", "emp_poblacion": "Cartagena", "emp_cp": "30390", "emp_uso": "Vivienda",
        # Instalador
        "inst_empresa": "IDEA TSG", "inst_nif": "B30888888", "inst_num": "4567-MUR", "inst_categoria": "Especialista",
        # Características
        "car_tension": "230 V (Monofásica)", "car_potencia": 9.2, "car_cpm": "En Fachada (Norma Iberdrola)", "car_iga": "40 A"
    }

# --- PANTALLA PRINCIPAL: PESTAÑAS DE TRABAJO ---
tabs_mtd = st.tabs([
    "🏢 1. Datos Identificativos y Emplazamiento", 
    "🛠️ 2. Empresa Instaladora y Técnico", 
    "⚡ 3. Características Técnicas de la Instalación",
    "📄 4. Generación y Descarga de PDF Oficial"
])

# ==========================================
# PESTAÑA 1: TITULAR Y EMPLAZAMIENTO
# ==========================================
with tabs_mtd[0]:
    st.subheader("👤 Datos del Titular y Ubicación de la Instalación")
    with st.form("form_titular_emplazamiento"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Datos del Titular de la Instalación:**")
            nombre = st.text_input("Nombre / Razón Social del Titular:", value=st.session_state['mtd_datos']['titular_nombre'])
            nif = st.text_input("N.I.F. / C.I.F.:", value=st.session_state['mtd_datos']['titular_nif'])
            dir_titular = st.text_input("Dirección Postal Titular:", value=st.session_state['mtd_datos']['titular_direccion'])
            pob_titular = st.text_input("Población / Distrito:", value=st.session_state['mtd_datos']['titular_poblacion'])
            cp_titular = st.text_input("Código Postal (Titular):", value=st.session_state['mtd_datos']['titular_cp'])
        with col2:
            st.markdown("**Datos de Emplazamiento (Ubicación de la Obra):**")
            calle_emp = st.text_input("Calle / Avda / Polígono:", value=st.session_state['mtd_datos']['emp_calle'])
            num_emp = st.text_input("Número / Bloque / Piso:", value=st.session_state['mtd_datos']['emp_num'])
            pob_emp = st.text_input("Localidad / Municipio:", value=st.session_state['mtd_datos']['emp_poblacion'])
            cp_emp = st.text_input("Código Postal (Ubicación):", value=st.session_state['mtd_datos']['emp_cp'])
            uso_emp = st.selectbox("Uso del Local / Edificio:", 
                                   ["Vivienda", "Local Comercial / Oficinas", "Nave Industrial (Fuerza)", "Garaje / Parking con IRVE", "Piscina / Alumbrado Exterior"])
        btn_save_1 = st.form_submit_button("💾 Guardar Bloque 1")
        if btn_save_1:
            st.session_state['mtd_datos'].update({
                "titular_nombre": nombre, "titular_nif": nif, "titular_direccion": dir_titular, "titular_poblacion": pob_titular, "titular_cp": cp_titular,
                "emp_calle": calle_emp, "emp_num": num_emp, "emp_poblacion": pob_emp, "emp_cp": cp_emp, "emp_uso": uso_emp
            })
            st.success("Sección 1 guardada correctamente en memoria local.")

# ==========================================
# PESTAÑA 2: EMPRESA INSTALADORA
# ==========================================
with tabs_mtd[1]:
    st.subheader("🔧 Datos Identificativos del Redactor de la Memoria")
    with st.form("form_instalador"):
        col_inst1, col_inst2 = st.columns(2)
        with col_inst1:
            st.markdown("**Empresa Habilitada en Baja Tensión:**")
            empresa = st.text_input("Razón Social de la Empresa:", value=st.session_state['mtd_datos']['inst_empresa'])
            nif_emp = st.text_input("N.I.F. Empresa:", value=st.session_state['mtd_datos']['inst_nif'])
        with col_inst2:
            st.markdown("**Registro y Cualificación:**")
            num_reg = st.text_input("Número de Inscripción Industrial:", value=st.session_state['mtd_datos']['inst_num'])
            cat_inst = st.selectbox("Categoría Habilitada:", ["Básica (IBTB)", "Especialista (IBTE)"], index=1 if st.session_state['mtd_datos']['inst_categoria'] == "Especialista" else 0)
        btn_save_2 = st.form_submit_button("💾 Guardar Bloque 2")
        if btn_save_2:
            st.session_state['mtd_datos'].update({
                "inst_empresa": empresa, "inst_nif": nif_emp, "inst_num": num_reg, "inst_categoria": cat_inst
            })
            st.success("Sección 2 guardada correctamente.")

# ==========================================
# PESTAÑA 3: CARACTERÍSTICAS TÉCNICAS
# ==========================================
with tabs_mtd[2]:
    st.subheader("⚡ Características Técnicas Específicas del Diseño")
    with st.form("form_caracteristicas"):
        col_car1, col_car2 = st.columns(2)
        with col_car1:
            st.markdown("**Datos del Suministro Eléctrico:**")
            tension = st.selectbox("Tensión de Servicio Nominal:", ["230 V (Monofásica)", "400 V (Trifásica)"])
            potencia = st.number_input("Potencia Prevista en el Proyecto (kW):", min_value=1.0, max_value=150.0, value=st.session_state['mtd_datos']['car_potencia'], step=0.1)
        with col_car2:
            st.markdown("**Elementos de Enlace y Protección:**")
            cpm = st.text_input("Ubicación de la Caja General de Protección (CGP/CPM):", value=st.session_state['mtd_datos']['car_cpm'])
            iga = st.selectbox("Calibre del Interruptor General Automático (IGA):", ["25 A", "32 A", "40 A", "50 A", "63 A"])
        btn_save_3 = st.form_submit_button("💾 Guardar Datos Técnicos")
        if btn_save_3:
            st.session_state['mtd_datos'].update({
                "car_tension": tension, "car_potencia": potencia, "car_cpm": cpm, "car_iga": iga
            })
            st.success("Sección de Parámetros Eléctricos actualizada.")

# ==========================================
# PESTAÑA 4: MOTOR DE IMPRESIÓN Y EXPORTACIÓN PDF
# ==========================================
with tabs_mtd[3]:
    st.subheader("📄 Generación Automatizada del Formulario de la Región de Murcia")
    st.info("Al pulsar el botón de abajo, el sistema maquetará los datos introducidos sobre la plantilla estructurada de la Dirección General de Energía y Minas.")
    
    d = st.session_state['mtd_datos']
    
    # Función interna para compilar el PDF usando FPDF2 sin depender de archivos externos
    def generar_pdf_oficial(datos):
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        
        # Encabezado Institucional
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, "REGIÓN DE MURCIA", ln=True, align="L")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 4, "Consejería de Ciencia, Tecnologías, Industria y Comercio", ln=True, align="L")
        pdf.cell(0, 4, "Dirección General de Industria, Energía y Minas", ln=True, align="L")
        pdf.ln(6)
        
        # Título del Documento Oficial
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 8, "MEMORIA TÉCNICA DE DISEÑO PARA INSTALACIONES ELÉCTRICAS BT", ln=True, align="C", fill=True)
        pdf.ln(5)
        
        # SECCIÓN 1
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(40, 40, 40)
        pdf.cell(0, 6, " 1. DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.cell(0, 6, f"Nombre o Razón Social: {datos['titular_nombre']}", ln=True)
        pdf.cell(90, 6, f"N.I.F. / C.I.F.: {datos['titular_nif']}", ln=False)
        pdf.cell(90, 6, f"C.P.: {datos['titular_cp']}", ln=True)
        pdf.cell(0, 6, f"Dirección Social: {datos['titular_direccion']}", ln=True)
        pdf.cell(0, 6, f"Municipio / Población: {datos['titular_poblacion']}", ln=True)
        pdf.ln(4)
        
        # SECCIÓN 2
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, " 2. DATOS DE EMPLAZAMIENTO DE LA INSTALACIÓN", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.cell(130, 6, f"Calle / Avenida / Polígono: {datos['emp_calle']}", ln=False)
        pdf.cell(50, 6, f"Nº / Bloque: {datos['emp_num']}", ln=True)
        pdf.cell(90, 6, f"Localidad / Municipio: {datos['emp_poblacion']}", ln=False)
        pdf.cell(90, 6, f"Código Postal: {datos['emp_cp']}", ln=True)
        pdf.cell(0, 6, f"Uso Principal del Local: {datos['emp_uso']}", ln=True)
        pdf.ln(4)
        
        # SECCIÓN 3
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, " 3. DATOS IDENTIFICATIVOS DEL REDACTOR (EMPRESA INSTALADORA)", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.cell(120, 6, f"Empresa Instaladora: {datos['inst_empresa']}", ln=False)
        pdf.cell(60, 6, f"N.I.F.: {datos['inst_nif']}", ln=True)
        pdf.cell(120, 6, f"Nº Inscripción Comunidad Autónoma: {datos['inst_num']}", ln=False)
        pdf.cell(60, 6, f"Categoría: {datos['inst_categoria']}", ln=True)
        pdf.ln(4)
        
        # SECCIÓN 4
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, " 4. PRINCIPALES CARACTERÍSTICAS TÉCNICAS DEL DISEÑO", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.cell(100, 6, f"Tensión de Servicio: {datos['car_tension']}", ln=False)
        pdf.cell(80, 6, f"Potencia Máxima Prevista: {datos['car_potencia']} kW", ln=True)
        pdf.cell(100, 6, f"Ubicación de CPM: {datos['car_cpm']}", ln=False)
        pdf.cell(80, 6, f"Calibre Interruptor IGA: {datos['car_iga']}", ln=True)
        
        # Pie de página técnico normalizado
        pdf.ln(25)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 4, "Documento cumplimentado telemáticamente mediante el Gestor Homologado REBT.", ln=True, align="C")
        pdf.cell(0, 4, "Válido para su presentación ante la Dirección General de Industria, Energía y Minas de Murcia.", ln=True, align="C")
        
        # Guardar en memoria de bytes
        buffer = io.BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

    try:
        pdf_bytes = generar_pdf_oficial(d)
        
        st.success("✨ ¡El documento MTD ha sido compilado y rellenado con éxito en formato oficial!")
        
        # Botón de descarga real del PDF rellenado automáticamente
        st.download_button(
            label="📥 Descargar Memoria Técnica Oficial (.PDF)",
            data=pdf_bytes,
            file_name=f"MTD_{d['titular_nombre'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        # Vista de control rápida para el instalador
        st.markdown("---")
        st.markdown("**Resumen de validación rápida:**")
        st.json(d)
        
    except Exception as e:
        st.error(f"Fallo en el motor de renderizado PDF: {e}")
