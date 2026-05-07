import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS AVANZADOS ---
st.set_page_config(page_title="Ingeniería Pro - Sistema Integral de Presupuestación", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Marca de Agua Minimalista */
    .footer-container {
        position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%;
    }
    .watermark-text { 
        font-size: 13px; color: rgba(255, 255, 255, 0.2); font-weight: normal; font-family: sans-serif;
    }

    /* Tipografía y Negritas */
    p, label, .stMarkdown, div, span, button, .stSelectbox, .stNumberInput { 
        font-weight: bold !important; 
    }

    /* Estética de Resultados Técnicos */
    .resultado-caja {
        color: #000000 !important; font-weight: 900 !important; font-size: 20px;
        background-color: #f8f9fa; padding: 10px; border-radius: 8px;
        border-left: 6px solid #1f2937; margin-bottom: 5px; text-align: right;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    /* Banner de Total Final Profesional */
    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 36px;
        background: linear-gradient(90deg, #1e1e1e 0%, #343a40 100%);
        padding: 30px; border-radius: 15px; text-align: center;
        border: 2px solid #ffc107; margin-top: 30px;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }

    .stExpander { 
        border: 1px solid #e0e0e0 !important; 
        border-radius: 12px !important; 
        background-color: #ffffff !important;
        margin-bottom: 15px !important;
    }
    </style>

    <div class="footer-container">
        <span class="watermark-text">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica Especializada</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. MOTOR DE CÁLCULO REBT (ITC-BT-19 Y MÁS) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Tablas de intensidades admisibles (Cobre, 2 cond. cargados, Temp amb 30°C)
tablas_adm = {
    "A1": {"PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321], 
           "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]},
    "B1": {"PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400], 
           "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]},
    "C":  {"PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461], 
           "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]},
    "E":  {"PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286, 331, 381, 434, 511], 
           "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352, 410, 473, 542, 641]}
}

def get_seccion_adm(metodo, aislamiento, ib):
    m_code = metodo.split(" ")[0]
    m_key = "A1" if m_code in ["A1", "A2"] else ("B1" if m_code in ["B1", "B2"] else (m_code if m_code in tablas_adm else "C"))
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm.get(m_key, tablas_adm["C"])[ais_key]
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib: return secciones_ref[i]
    return 240

# --- 3. BASE DE DATOS DE PRECIOS UNITARIOS ---
precios_master = {
    "CABLES": {1.5: 0.28, 2.5: 0.42, 4: 0.68, 6: 1.35, 10: 2.25, 16: 3.60, 25: 5.80, 35: 8.10},
    "CANALIZACION": {"Tubo 20": 0.18, "Tubo 25": 0.26, "Tubo 32": 0.52, "Canaleta": 4.50},
    "MANO_OBRA": {"Oficial": 34.00, "Ayudante": 28.50}
}

# --- 4. SIDEBAR - CONFIGURACIÓN GLOBAL ---
with st.sidebar:
    st.header("🏢 Configuración de Obra")
    modo = st.radio("Herramienta:", ["📐 Calculadora REBT", "💰 Generador de Presupuesto"])
    
    st.divider()
    if modo == "💰 Generador de Presupuesto":
        st.subheader("Coeficientes de Venta")
        gastos_gen = st.slider("% Gastos Generales", 0, 20, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA Aplicable", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 5. LÓGICA DE LA CALCULADORA TÉCNICA ---
if modo == "📐 Calculadora REBT":
    st.title("📐 Dimensionamiento de Conductores s/ REBT")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Datos de Carga")
        sistema = st.selectbox("Tensión Nominal", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Cálculo (W)", value=5750, step=500)
        longitud = st.number_input("Longitud de la Línea (m)", value=30.0, step=5.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
        uso = st.selectbox("Tipo de Carga (Recargo)", ["General (1.0)", "Motores (1.25)", "Lámparas Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        k_u = 1.25 if ("Motores" in uso or "Vehículo" in uso) else (1.8 if "Descarga" in uso else 1.0)
    
    with c2:
        st.subheader("Condiciones de Instalación")
        material = st.radio("Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Referencia (ITC-BT-19)", list(tablas_adm.keys()) + ["D1 - Enterrado bajo tubo"])
        max_cdt = st.number_input("Caída de Tensión Máxima admisible (%)", value=3.0, step=0.5)

    # Procesamiento
    v_fase = 230 if "Mono" in sistema else 400
    ib = (potencia * k_u) / (v_fase * cos_phi) if v_fase == 230 else (potencia * k_u) / (1.732 * v_fase * cos_phi)
    
    # Cálculo por Intensidad
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    if material == "Aluminio (Al)": s_adm = secciones_ref[secciones_ref.index(s_adm) + 2] # Ajuste simplificado Al

    # Cálculo por Caída de Tensión
    cond_gamma = (48 if "PVC" in aislamiento else 44) if "Cobre" in material else (30 if "PVC" in aislamiento else 28)
    s_cdt = (2 if v_fase == 230 else 1) * longitud * (potencia/v_fase if v_fase==230 else ib) * cos_phi / (cond_gamma * (max_cdt/100 * v_fase))
    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)

    # Resultado Final
    s_final = max(s_adm, s_cdt_norm)

    st.divider()
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Intensidad Ib", f"{ib:.2f} A")
    res2.metric("Sección por Iadm", f"{s_adm} mm²")
    res3.metric("Sección por CdT", f"{s_cdt_norm} mm²")
    st.markdown(f'<div class="resultado-caja">SECCIÓN REGLAMENTARIA: {s_final} mm²</div>', unsafe_allow_html=True)

# --- 6. GENERADOR DE PRESUPUESTO COMPLEJO ---
else:
    st.title("💰 Presupuesto Maestro de Instalación Eléctrica")
    st.info("Desglose pormenorizado por capítulos técnicos. Incluye materiales, mano de obra y coeficientes.")

    capitulos = []

    # Función auxiliar para cálculos internos de capítulo
    def render_capitulo(titulo, lista_materiales, h_of, h_ay):
        with st.expander(titulo):
            c_mat, c_mo = st.columns(2)
            tot_mat = 0
            for item in lista_materiales:
                q = c_mat.number_input(f"Cant: {item['nom']}", value=item['def_q'], key=f"q_{titulo}_{item['nom']}")
                p = c_mat.number_input(f"P.U. (€): {item['nom']}", value=item['def_p'], key=f"p_{titulo}_{item['nom']}")
                tot_mat += (q * p)
            
            h1 = c_mo.number_input("Horas Oficial 1ª", value=float(h_of), key=f"h1_{titulo}")
            h2 = c_mo.number_input("Horas Ayudante", value=float(h_ay), key=f"h2_{titulo}")
            tot_mo = (h1 * precios_master["MANO_OBRA"]["Oficial"]) + (h2 * precios_master["MANO_OBRA"]["Ayudante"])
            
            total_cap = (tot_mat + tot_mo) * f_multiplicador
            st.markdown(f'<div class="resultado-caja">Subtotal {titulo}: {total_cap:,.2f} €</div>', unsafe_allow_html=True)
            return (titulo, total_cap)

    # Definición de Capítulos
    # 1. Derivación Individual
    capitulos.append(render_capitulo("CAP I: DERIVACIÓN INDIVIDUAL", 
        [{'nom': "Cable unipolar 10mm² (m)", 'def_q': 45.0, 'def_p': 2.25}, {'nom': "Tubo corrugado 32mm (m)", 'def_q': 15.0, 'def_p': 0.52}], 3, 2))

    # 2. Cuadro General (CGMP)
    capitulos.append(render_capitulo("CAP II: CUADRO GENERAL DE PROTECCIÓN", 
        [{'nom': "Caja 36 módulos", 'def_q': 1.0, 'def_p': 58.0}, {'nom': "IGA + Protector Sobretensiones", 'def_q': 1.0, 'def_p': 85.0}, {'nom': "Diferenciales 40A/30mA", 'def_q': 2.0, 'def_p': 28.0}], 5, 0))

    # 3. Alumbrado (C1)
    capitulos.append(render_capitulo("CAP III: CIRCUITO ALUMBRADO (C1)", 
        [{'nom': "Mecanismos (Int/Conm)", 'def_q': 12.0, 'def_p': 4.50}, {'nom': "Cable 1.5mm² (m)", 'def_q': 200.0, 'def_p': 0.28}], 8, 4))

    # 4. Tomas de Corriente (C2)
    capitulos.append(render_capitulo("CAP IV: TOMAS DE USO GENERAL (C2)", 
        [{'nom': "Bases enchufe 16A", 'def_q': 20.0, 'def_p': 5.20}, {'nom': "Cable 2.5mm² (m)", 'def_q': 250.0, 'def_p': 0.42}], 10, 6))

    # 5. Cocina y Horno (C3)
    capitulos.append(render_capitulo("CAP V: COCINA Y HORNO (C3)", 
        [{'nom': "Base 25A + Caja", 'def_q': 1.0, 'def_p': 12.50}, {'nom': "Cable 6mm² (m)", 'def_q': 25.0, 'def_p': 1.35}], 2, 1))

    # 6. Lavadora/Lavavajillas (C4)
    capitulos.append(render_capitulo("CAP VI: LAVADORA, LAVAVAJILLAS Y TERMO (C4)", 
        [{'nom': "Bases 16A Estancas", 'def_q': 3.0, 'def_p': 8.90}, {'nom': "Cable 4mm² (m)", 'def_q': 60.0, 'def_p': 0.68}], 4, 2))

    # 7. Baños y Cocina Aux (C5)
    capitulos.append(render_capitulo("CAP VII: BAÑOS Y AUX. COCINA (C5)", 
        [{'nom': "Bases 16A seguridad", 'def_q': 6.0, 'def_p': 6.10}, {'nom': "Cable 2.5mm² (m)", 'def_q': 80.0, 'def_p': 0.42}], 4, 2))

    # 8. Climatización (C9)
    capitulos.append(render_capitulo("CAP VIII: CLIMATIZACIÓN", 
        [{'nom': "PIA 25A dedicado", 'def_q': 1.0, 'def_p': 14.0}, {'nom': "Cable 6mm² (m)", 'def_q': 40.0, 'def_p': 1.35}], 3, 0))

    # 9. Puesta a Tierra
    capitulos.append(render_capitulo("CAP IX: RED DE PUESTA A TIERRA", 
        [{'nom': "Pica de acero cobrizado 2m", 'def_q': 1.0, 'def_p': 22.0}, {'nom': "Arqueta + Puente prueba", 'def_q': 1.0, 'def_p': 18.0}, {'nom': "Cable Desnudo 35mm² (m)", 'def_q': 15.0, 'def_p': 8.10}], 2, 2))

    # 10. Telecomunicaciones (ICT)
    capitulos.append(render_capitulo("CAP X: TELECOMUNICACIONES (RTV/Banda Ancha)", 
        [{'nom': "Tomas RTV-SAT", 'def_q': 4.0, 'def_p': 11.0}, {'nom': "Tomas Datos RJ45 Cat6", 'def_q': 4.0, 'def_p': 14.50}, {'nom': "Registro Enlace", 'def_q': 1.0, 'def_p': 32.0}], 6, 2))

    # 11. Legalización y Certificación
    capitulos.append(render_capitulo("CAP XI: LEGALIZACIÓN Y TASAS", 
        [{'nom': "Tasas Industria / OCI", 'def_q': 1.0, 'def_p': 65.0}, {'nom': "Certificado Instalación (CIE)", 'def_q': 1.0, 'def_p': 150.0}], 2, 0))

    # --- RESUMEN FINAL ---
    st.divider()
    st.subheader("📊 Resumen del Presupuesto")
    
    total_neto = 0
    for nom, val in capitulos:
        col_n, col_v = st.columns([4, 1])
        col_n.write(f"**{nom}**")
        col_v.markdown(f"**{val:,.2f} €**")
        total_neto += val
    
    total_con_iva = total_neto * (1 + iva_tipo/100)
    
    st.markdown(
        f'<div class="total-final-banner">'
        f'PRESUPUESTO TOTAL (IVA {iva_tipo}% INCLUIDO)<br>'
        f'{total_con_iva:,.2f} €'
        f'</div>', 
        unsafe_allow_html=True
    )
    
    # Exportación simple (Simulada)
    st.download_button("Descargar Informe (CSV)", pd.DataFrame(capitulos, columns=["Capítulo", "Importe"]).to_csv(), "presupuesto.csv", "text/csv")
