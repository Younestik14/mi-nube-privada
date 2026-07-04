import streamlit as st
import pandas as pd

st.set_page_config(page_title="Memoria Técnica de Diseño MTD", page_icon="📝", layout="wide")

st.title("📝 Módulo 2: Memoria Técnica de Diseño (IEBT)")
st.markdown("Cumplimentación e integración de datos según el modelo oficial de la Dirección General de Energía y Minas.")

# --- INICIALIZACIÓN DEL STATE PARA GUARDAR LOS DATOS DEL DOCUMENTO ---
if 'mtd_datos' not in st.session_state:
    st.session_state['mtd_datos'] = {
        # Titular
        "titular_nombre": "", "titular_nif": "", "titular_direccion": "", "titular_cp": "", "titular_poblacion": "La Aljorra",
        # Emplazamiento
        "emp_calle": "", "emp_num": "", "emp_poblacion": "Cartagena", "emp_cp": "30390", "emp_uso": "Vivienda",
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
    "📄 4. Vista Previa del Documento Oficial"
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
            empresa = st.text_input("Razon Social de la Empresa:", value=st.session_state['mtd_datos']['inst_empresa'])
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
# PESTAÑA 4: VISTA PREVIA (ESTRUCTURA OFICIAL)
# ==========================================
with tabs_mtd[3]:
    st.subheader("📄 Copia de Revisión Oficial - Dirección General de Industria")
    st.info("Esta vista preliminar reproduce fielmente los campos del formulario oficial listos para anexar al visado o firma del instalador.")
    
    d = st.session_state['mtd_datos']
    
    html_oficial = f"""
    <div style="border: 2px solid #333; padding: 20px; font-family: monospace; background-color: #f9f9f9; color: #111; border-radius: 5px;">
        <h3 style="text-align: center; margin-top: 0;">MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</h3>
        <hr style="border-top: 1px solid #333;">
        
        <b>[1] DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN</b><br>
        • Nombre/Razon Social: {d['titular_nombre'] if d['titular_nombre'] else "................................................."}<br>
        • N.I.F.: {d['titular_nif'] if d['titular_nif'] else "....................."}<br>
        • Dirección: {d['titular_direccion'] if d['titular_direccion'] else "................................................."} &nbsp;&nbsp; Población: {d['titular_poblacion']}<br>
        • C.P.: {d['titular_cp'] if d['titular_cp'] else "..........."}<br>
        <br>
        
        <b>[2] DATOS DE EMPLAZAMIENTO DE LA INSTALACIÓN</b><br>
        • Emplazamiento: {d['emp_calle'] if d['emp_calle'] else "................................................."} &nbsp;&nbsp; Nº: {d['emp_num'] if d['emp_num'] else "...."}<br>
        • Localidad/Municipio: {d['emp_poblacion']} &nbsp;&nbsp; C.P.: {d['emp_cp']}<br>
        • Uso del Edificio/Local: {d['emp_uso']}<br>
        <br>
        
        <b>[3] DATOS IDENTIFICATIVOS DEL REDACTOR DE LA MEMORIA (EMPRESA INSTALADORA)</b><br>
        • Razón Social Empresa: {d['inst_empresa']} &nbsp;&nbsp; N.I.F.: {d['inst_nif']}<br>
        • N.º Inscripción Comunidad Autónoma: {d['inst_num']}<br>
        • Categoría: {d['inst_categoria']}<br>
        <br>
        
        <b>[4] PRINCIPALES CARACTERÍSTICAS TÉCNICAS</b><br>
        • Tensión de servicio: {d['car_tension']}<br>
        • Potencia prevista: {d['car_potencia']} kW<br>
        • Tipo/Ubicación CPM: {d['car_cpm']}<br>
        • Calibre del IGA General: {d['car_iga']}<br>
        <hr style="border-top: 1px solid #333;">
        <p style="text-align: right; font-size: 11px;">Documento visado digitalmente conforme a la Guía Técnica REBT - Región de Murcia</p>
    </div>
    """
    
    st.markdown(html_oficial, unsafe_allow_html=True)
    
    # Botón complementario para exportar a texto plano los datos estructurados
    st.write("---")
    resumen_texto = (
        f"MEMORIA TÉCNICA DE DISEÑO\n"
        f"=========================\n"
        f"TITULAR: {d['titular_nombre']} ({d['titular_nif']})\n"
        f"EMPLAZAMIENTO: {d['emp_calle']}, Nº{d['emp_num']} - {d['emp_poblacion']}\n"
        f"EMPRESA INSTALADORA: {d['inst_empresa']} Reg:{d['inst_num']}\n"
        f"POTENCIA PREVISTA: {d['car_potencia']} kW - IGA: {d['car_iga']}\n"
    )
    
    st.download_button(
        label="📥 Descargar Extracto Estructurado de la Memoria (.TXT)",
        data=resumen_texto,
        file_name="extracto_mtd_murcia.txt",
        mime="text/plain"
    )
