import streamlit as st
import pandas as pd
import math
import io

# --- 1. CONFIGURACIÓN Y ESTILO DARK PROFESIONAL ---
st.set_page_config(page_title="Ingeniería Pro v3.0 - Full Suite", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    
    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 24px;
        background-color: #1f2937; padding: 20px; border-radius: 12px;
        border-left: 8px solid #22d3ee; margin-bottom: 15px; text-align: right;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }

    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 42px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
        padding: 50px; border-radius: 25px; text-align: center;
        border: 3px solid #ffd700; margin-top: 50px;
        box-shadow: 0px 20px 40px rgba(0,0,0,0.7);
    }

    .stExpander { 
        border: 1px solid #374151 !important; border-radius: 15px !important; 
        background-color: #161b22 !important; margin-bottom: 20px !important;
    }
    
    .footer-container {
        position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%;
    }
    .watermark-text { font-size: 12px; color: rgba(255, 255, 255, 0.15); }
    </style>
    <div class="footer-container"><span class="watermark-text">Younesse Tikent Tifaoui - Senior Technical Consultant</span></div>
    """,
    unsafe_allow_html=True
)

# --- FUNCIÓN DE EXPORTACIÓN ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Presupuesto')
    return output.getvalue()

# --- 2. MOTOR DE CÁLCULO REBT (MATRIZ UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
tablas_adm = {
    "A1 - Empotrado en tubo (Pared aislante)": {
        "PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321],
        "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]
    },
    "A2 - Multiconductor en tubo (Pared aislante)": {
        "PVC": [14, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291],
        "XLPE": [17.5, 24, 32, 41, 54, 73, 95, 117, 141, 179, 216, 249, 285, 324, 380]
    },
    "B1 - Conductores en tubo (Sobre pared)": {
        "PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400],
        "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]
    },
    "B2 - Multiconductor en tubo (Sobre pared)": {
        "PVC": [16.5, 23, 30, 38, 52, 69, 92, 114, 138, 175, 210, 244, 282, 319, 375],
        "XLPE": [21, 28, 38, 49, 66, 88, 117, 146, 175, 222, 269, 312, 358, 408, 481]
    },
    "C - Cable sobre pared de madera/mampostería": {
        "PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461],
        "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]
    },
    "D1 - Cable en conductos enterrados": {
        "PVC": [22, 29, 38, 47, 63, 81, 104, 125, 148, 183, 216, 246, 278, 312, 361],
        "XLPE": [26, 34, 44, 56, 73, 95, 121, 146, 173, 213, 252, 287, 324, 363, 419]
    },
    "E - Multiconductor al aire libre": {
        "PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286, 331, 381, 434, 511],
        "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352, 410, 473, 542, 641]
    },
    "F - Unipolares en contacto (Bandeja perforada)": {
        "PVC": [21, 28, 38, 50, 68, 92, 121, 150, 184, 233, 282, 327, 376, 428, 505],
        "XLPE": [25, 34, 46, 61, 83, 112, 146, 181, 221, 281, 341, 396, 455, 517, 613]
    }
}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    modo = st.radio("Módulo de Trabajo:", ["📐 Dimensionado REBT", "💰 Presupuesto Maestro"])
    st.divider()
    iva_tipo = st.selectbox("IVA Aplicable (%)", [21, 10, 4, 0], index=0)
    
    if modo == "💰 Presupuesto Maestro":
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. MÓDULO TÉCNICO ---
if modo == "📐 Dimensionado REBT":
    st.title("📐 Oficina Técnica: Cálculo de Líneas s/ REBT")
    c1, c2 = st.columns(2)
    with c1:
        sistema = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Cálculo (W)", value=5750, step=100)
        longitud = st.number_input("Longitud de la Línea (m)", value=30.0, step=1.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
    with c2:
        material = st.radio("Material Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Tipo de Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Instalación", list(tablas_adm.keys()))
        max_cdt = st.number_input("Caída de Tensión Máx (%)", value=3.0, step=0.1)

    # Cálculo Intensidad
    v_fase = 230 if "Mono" in sistema else 400
    ib = potencia / (v_fase * cos_phi) if v_fase == 230 else potencia / (math.sqrt(3) * v_fase * cos_phi)
    
    # Sección por Intensidad Admisible
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm[metodo_inst][ais_key]
    s_adm = secciones_ref[next((i for i, v in enumerate(intensidades) if v >= ib), -1)]
    
    st.divider()
    st.markdown(f'<div class="resultado-caja">SECCIÓN REGLAMENTARIA: {s_adm} mm²<br><small>Intensidad: {ib:.2f} A</small></div>', unsafe_allow_html=True)
    
    df_calc = pd.DataFrame({"Variable": ["Potencia", "Intensidad", "Sección"], "Valor": [f"{potencia} W", f"{ib:.2f} A", f"{s_adm} mm²"]})
    st.download_button("📥 Descargar Memoria (Excel)", to_excel(df_calc), "calculo_rebt.xlsx")

# --- 5. PRESUPUESTO MAESTRO (COMPLETO) ---
else:
    st.title("💰 Gestor de Presupuestos: Electrificación s/ REBT")
    tab_cfg, tab_pre = st.tabs(["🛠️ Configuración de Precios", "📋 Generación de Capítulos"])

    with tab_cfg:
        st.subheader("Base de Datos de Precios (Catálogo)")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            st.markdown("#### ⚡ Cables (€/m)")
            p_c15 = st.number_input("1.5 mm²", 0.10, 2.00, 0.32, key="cfg_c15")
            p_c25 = st.number_input("2.5 mm²", 0.20, 3.00, 0.48, key="cfg_c25")
            p_c40 = st.number_input("4 mm²", 0.40, 5.00, 0.75, key="cfg_c40")
            p_c60 = st.number_input("6 mm²", 0.80, 8.00, 1.45, key="cfg_c60")
            p_c10 = st.number_input("10 mm²", 1.50, 15.0, 2.60, key="cfg_c10")
            p_c16 = st.number_input("16 mm²", 2.50, 25.0, 4.10, key="cfg_c16")
        with col_p2:
            st.markdown("#### 🔘 Mecanismos (€/u)")
            p_interr = st.number_input("Interruptor Simple", 2.0, 50.0, 4.20, key="cfg_int")
            p_conmut = st.number_input("Conmutador", 2.0, 50.0, 5.80, key="cfg_con")
            p_cruza = st.number_input("Cruzamiento", 2.0, 50.0, 11.50, key="cfg_cru")
            p_enchufe_16 = st.number_input("Base Enchufe 16A", 2.0, 50.0, 6.10, key="cfg_e16")
            p_enchufe_25 = st.number_input("Base Enchufe 25A", 5.0, 60.0, 14.50, key="cfg_e25")
            p_toma_tvcet = st.number_input("Toma TV/Datos", 5.0, 80.0, 12.00, key="cfg_tv")
            p_estanca = st.number_input("Base Estanca IP54", 8.0, 100.0, 18.50, key="cfg_est")
        with col_p3:
            st.markdown("#### 🛡️ Protecciones (€/u)")
            p_iga_sobre = st.number_input("IGA + Sobretensiones", 50.0, 300.0, 125.0, key="cfg_iga")
            p_pia_10 = st.number_input("PIA 10A", 5.0, 40.0, 8.50, key="cfg_p10")
            p_pia_16 = st.number_input("PIA 16A", 5.0, 40.0, 9.20, key="cfg_p16")
            p_pia_20 = st.number_input("PIA 20A", 5.0, 40.0, 11.50, key="cfg_p20")
            p_pia_25 = st.number_input("PIA 25A", 5.0, 50.0, 14.00, key="cfg_p25")
            p_diff_25 = st.number_input("Diferencial 25A", 30.0, 250.0, 55.0, key="cfg_d25")
            p_diff_40 = st.number_input("Diferencial 40A", 30.0, 250.0, 65.0, key="cfg_d40")
        with col_p4:
            st.markdown("#### 🚇 Tubos (€/m)")
            p_t20 = st.number_input("Tubo Ø20mm", 0.30, 6.0, 0.65, key="cfg_t20")
            p_t25 = st.number_input("Tubo Ø25mm", 0.40, 8.0, 0.85, key="cfg_t25")
            p_t32 = st.number_input("Tubo Ø32mm", 0.60, 12.0, 1.25, key="cfg_t32")
            p_oficial = st.number_input("Oficial 1ª (€/h)", 20.0, 60.0, 36.0, key="cfg_mo1")
            p_ayudante = st.number_input("Ayudante (€/h)", 15.0, 50.0, 26.5, key="cfg_mo2")

    catalogo_precios = {
        "Cable 1.5 mm²": p_c15, "Cable 2.5 mm²": p_c25, "Cable 4 mm²": p_c40, "Cable 6 mm²": p_c60,
        "Interruptor Simple": p_interr, "Conmutador": p_conmut, "Cruzamiento": p_cruza,
        "Enchufe 16A": p_enchufe_16, "Enchufe 25A": p_enchufe_25, "Toma TV/Datos": p_toma_tvcet,
        "IGA + Sobretensiones": p_iga_sobre, "PIA 10A": p_pia_10, "PIA 16A": p_pia_16, "PIA 25A": p_pia_25,
        "Diferencial 40A": p_diff_40, "Tubo Ø20mm": p_t20, "Tubo Ø25mm": p_t25
    }

    explicaciones_tecnicas = {
        "DI": "Derivación Individual", "CGMP": "Cuadro General", "C1": "Iluminación",
        "C2": "Tomas uso general", "C3": "Cocina/Horno", "C4": "Lavadora/Termo",
        "C5": "Baño/Cocina", "C13": "Vehículo Eléctrico", "PAT": "Tierra"
    }

    with tab_pre:
        resumen_costes, nombres_export, desc_tecnica = [], [], []
        
        for code, name in explicaciones_tecnicas.items():
            with st.expander(f"🛠️ {code}: {name}"):
                c_sel, c_cant = st.columns([2, 1])
                seleccion = c_sel.multiselect(f"Materiales:", list(catalogo_precios.keys()), key=f"sel_{code}")
                coste_mat = 0.0
                for item in seleccion:
                    q = c_cant.number_input(f"Cant. {item}", 0.0, 1000.0, 0.0, key=f"q_{code}_{item}")
                    coste_mat += q * catalogo_precios[item]
                
                c_h1, c_h2 = st.columns(2)
                h_of = c_h1.number_input("Horas Oficial", 0.0, 100.0, 0.0, key=f"hof_{code}")
                h_ay = c_h2.number_input("Horas Ayudante", 0.0, 100.0, 0.0, key=f"hay_{code}")
                
                subtotal = (coste_mat + (h_of * p_oficial) + (h_ay * p_ayudante)) * f_multiplicador
                st.write(f"Subtotal: **{subtotal:,.2f} €**")
                
                if subtotal > 0:
                    resumen_costes.append(subtotal)
                    nombres_export.append(f"{code} - {name}")
                    desc_tecnica.append(explicaciones_tecnicas[code])

        if resumen_costes:
            st.divider()
            total_neto = sum(resumen_costes)
            impuestos = total_neto * (iva_tipo / 100)
            
            st.markdown(f'<div class="total-final-banner">TOTAL: {total_neto + impuestos:,.2f} €<br><small>Base: {total_neto:,.2f} € | IVA: {impuestos:,.2f} €</small></div>', unsafe_allow_html=True)
            
            df_final = pd.DataFrame({"Capítulo": nombres_export, "Justificación": desc_tecnica, "Total (€)": resumen_costes})
            
            c_down1, c_down2 = st.columns(2)
            c_down1.download_button("📊 Descargar Excel", to_excel(df_final), "presupuesto.xlsx")
            c_down2.download_button("📥 Descargar CSV", df_final.to_csv(index=False, sep=';').encode('utf-16'), "presupuesto.csv")
        
