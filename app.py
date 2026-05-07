import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILO DARK INTEGRAL ---
st.set_page_config(page_title="Ingeniería Pro v3.0 - Full Suite", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    
    /* Contenedor de resultados tipo display industrial */
    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 24px;
        background-color: #1f2937; padding: 20px; border-radius: 12px;
        border-left: 8px solid #22d3ee; margin-bottom: 15px; text-align: right;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }

    /* Banner de presupuesto final */
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

    .stNumberInput input, .stSelectbox div { background-color: #0d1117 !important; color: white !important; }
    
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

# --- 2. MOTOR DE CÁLCULO REBT (MATRIZ COMPLETA UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Matriz extendida: Incluye métodos A1, A2, B1, B2, C, D1, D2, E, F, G
# Valores para Cobre, 2 conductores cargados (Monofásico)
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

def get_seccion_adm(metodo_key, aislamiento, ib):
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm.get(metodo_key, tablas_adm["C - Cable sobre pared de madera/mampostería"])[ais_key]
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib: return secciones_ref[i]
    return 240

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    modo = st.radio("Módulo de Trabajo:", ["📐 Dimensionado REBT", "💰 Presupuesto Maestro"])
    
    if modo == "💰 Presupuesto Maestro":
        st.divider()
        st.subheader("Coeficientes Económicos")
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA Aplicable (%)", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. CALCULADORA TÉCNICA EXTENDIDA ---
if modo == "📐 Dimensionado REBT":
    st.title("📐 Oficina Técnica: Cálculo de Líneas s/ REBT")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Datos de Carga")
        sistema = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Cálculo (W)", value=5750, step=100)
        longitud = st.number_input("Longitud de la Línea (m)", value=30.0, step=1.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
        uso = st.selectbox("Factor de Uso", ["General (1.0)", "Motores (1.25)", "Lámparas de Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        k_u = 1.25 if ("Motores" in uso or "Vehículo" in uso) else (1.8 if "Descarga" in uso else 1.0)

    with c2:
        st.subheader("Parámetros de Instalación")
        material = st.radio("Material Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Tipo de Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Instalación (UNE-HD 60364-5-52)", list(tablas_adm.keys()))
        max_cdt = st.number_input("Caída de Tensión Máx. Admitida (%)", value=3.0, step=0.1)

    # Lógica Matemática
    v_fase = 230 if "Mono" in sistema else 400
    ib = (potencia * k_u) / (v_fase * cos_phi) if v_fase == 230 else (potencia * k_u) / (1.732 * v_fase * cos_phi)
    
    # 1. Criterio de Intensidad Admisible
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    
    # 2. Criterio de Caída de Tensión
    # Conductividad γ (Cu: PVC=48, XLPE=44 | Al: PVC=30, XLPE=28)
    if "Cobre" in material:
        gamma = 48 if "PVC" in aislamiento else 44
    else:
        gamma = 30 if "PVC" in aislamiento else 28
    
    # Fórmula S = (2*L*P)/(gamma*e*V) para monofásico, S = (L*P)/(gamma*e*V) para trifásico
    if v_fase == 230:
        s_cdt = (2 * longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)
    else:
        s_cdt = (longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)
        
    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)
    
    # Sección Final
    s_final = max(s_adm, s_cdt_norm)

    st.divider()
    st.markdown(f"""
    <div class="resultado-caja">
        SECCIÓN REGLAMENTARIA: {s_final} mm²<br>
        <small style="font-size:14px; font-weight:normal;">
            Intensidad de Diseño (Ib): {ib:.2f} A | 
            Criterio Térmico: {s_adm} mm² | 
            Criterio CdT: {s_cdt:.2f} mm²
        </small>
    </div>
    """, unsafe_allow_html=True)

# --- 5. PRESUPUESTO MAESTRO COMPLETO (12 CIRCUITOS + CONFIG) ---
else:
    st.title("💰 Gestor de Presupuestos: Electrificación Elevada")
    
    tab_cfg, tab_pre = st.tabs(["🛠️ Configuración de Precios Unitarios", "📋 Generación de Capítulos"])

    with tab_cfg:
        st.subheader("Base de Datos de Precios (Editable)")
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            st.markdown("#### ⚡ Cables (€/m)")
            p_c15 = st.number_input("1.5 mm²", 0.10, 2.00, 0.32)
            p_c25 = st.number_input("2.5 mm²", 0.20, 3.00, 0.48)
            p_c40 = st.number_input("4 mm²", 0.40, 5.00, 0.75)
            p_c60 = st.number_input("6 mm²", 0.80, 8.00, 1.45)
            p_c10 = st.number_input("10 mm²", 1.50, 15.0, 2.60)
            p_c16 = st.number_input("16 mm²", 2.50, 25.0, 4.10)

        with col_p2:
            st.markdown("#### 📦 Materiales (€/u)")
            p_meca = st.number_input("Mecanismo (Interr/Conmut)", 2.0, 50.0, 5.20)
            p_enchufe = st.number_input("Base de Enchufe 16A", 2.0, 50.0, 6.10)
            p_caja_cgpm = st.number_input("Caja CGPM / Cuadro", 30.0, 500.0, 85.0)
            p_pia = st.number_input("Automático (PIA) medio", 5.0, 100.0, 12.50)
            p_diff = st.number_input("Diferencial 40A/30mA", 20.0, 200.0, 45.0)

        with col_p3:
            st.markdown("#### 👷 Mano de Obra (€/h)")
            p_oficial = st.number_input("Oficial de 1ª", 20.0, 60.0, 36.0)
            p_ayudante = st.number_input("Ayudante", 15.0, 50.0, 26.5)
            st.info("Nota: Los precios configurados aquí se propagan a todos los cálculos del presupuesto.")

    db_precios = {
        "c1.5": p_c15, "c2.5": p_c25, "c4": p_c40, "c6": p_c60, "c10": p_c10, "c16": p_c16,
        "meca": p_meca, "base": p_enchufe, "cuadro": p_caja_cgpm, "pia": p_pia, "diff": p_diff,
        "mo_of": p_oficial, "mo_ay": p_ayudante
    }

    with tab_pre:
        resumen_costes = []

        def crear_capitulo(id_cap, nombre, materiales, h_of, h_ay):
            with st.expander(f"{id_cap}: {nombre}"):
                c_m, c_o = st.columns(2)
                sub_mat = 0
                for m in materiales:
                    cant = c_m.number_input(f"Cant. {m['label']}", value=float(m['q']), key=f"q_{id_cap}_{m['label']}")
                    sub_mat += cant * m['p']
                
                total_mo = (h_of * db_precios["mo_of"]) + (h_ay * db_precios["mo_ay"])
                total_cap = (sub_mat + total_mo) * f_multiplicador
                st.markdown(f'<div class="resultado-caja">{total_cap:,.2f} €</div>', unsafe_allow_html=True)
                return total_cap

        # 12 CIRCUITOS REGLAMENTARIOS + DI + CUADRO
        resumen_costes.append(crear_capitulo("DI", "DERIVACIÓN INDIVIDUAL", [{"label": "Manguera 3x10mm²", "q": 25, "p": db_precios["c10"]}], 4, 2))
        resumen_costes.append(crear_capitulo("CGMP", "CUADRO GENERAL DE PROTECCIÓN", [{"label": "Caja+IGA+Sobretensiones", "q": 1, "p": db_precios["cuadro"] + 120}, {"label": "Diferenciales", "q": 3, "p": db_precios["diff"]}], 6, 0))
        resumen_costes.append(crear_capitulo("C1", "ILUMINACIÓN", [{"label": "Cable 1.5", "q": 150, "p": db_precios["c1.5"]}, {"label": "Mecanismos", "q": 15, "p": db_precios["meca"]}], 10, 5))
        resumen_costes.append(crear_capitulo("C2", "TOMAS DE CORRECO GENERAL", [{"label": "Cable 2.5", "q": 200, "p": db_precios["c2.5"]}, {"label": "Enchufes", "q": 22, "p": db_precios["base"]}], 12, 6))
        resumen_costes.append(crear_capitulo("C3", "COCINA Y HORNO", [{"label": "Cable 6", "q": 20, "p": db_precios["c6"]}, {"label": "Toma 25A", "q": 1, "p": 15.0}], 3, 1))
        resumen_costes.append(crear_capitulo("C4", "LAVADORA, LAVAVAJILLAS, TERMO", [{"label": "Cable 4", "q": 60, "p": db_precios["c4"]}, {"label": "Enchufes", "q": 3, "p": db_precios["base"]}], 6, 2))
        resumen_costes.append(crear_capitulo("C5", "BAÑOS Y TOMAS DE COCINA", [{"label": "Cable 2.5", "q": 80, "p": db_precios["c2.5"]}, {"label": "Enchufes", "q": 8, "p": db_precios["base"]}], 5, 2))
        resumen_costes.append(crear_capitulo("C8", "CALEFACCIÓN", [{"label": "Cable 6", "q": 40, "p": db_precios["c6"]}], 4, 0))
        resumen_costes.append(crear_capitulo("C9", "AIRE ACONDICIONADO", [{"label": "Cable 6", "q": 30, "p": db_precios["c6"]}], 4, 0))
        resumen_costes.append(crear_capitulo("C10", "SECADORA", [{"label": "Cable 2.5", "q": 25, "p": db_precios["c2.5"]}], 2, 0))
        resumen_costes.append(crear_capitulo("C11", "DOMÓTICA Y SEGURIDAD", [{"label": "Cable 1.5", "q": 100, "p": db_precios["c1.5"]}], 8, 2))
        resumen_costes.append(crear_capitulo("C12", "VEHÍCULO ELÉCTRICO", [{"label": "Cable 6 o 10", "q": 40, "p": db_precios["c10"]}, {"label": "Protección EV", "q": 1, "p": 180}], 5, 2))
        resumen_costes.append(crear_capitulo("PAT", "PUESTA A TIERRA", [{"label": "Pica + Cable desnudo", "q": 1, "p": db_precios["cuadro"] + 40}], 3, 3))

        # --- RESUMEN DE TOTALES ---
        st.divider()
        total_neto = sum(resumen_costes)
        impuestos = total_neto * (iva_tipo / 100)
        total_final = total_neto + impuestos

        st.markdown(f"""
        <div class="total-final-banner">
            PRESUPUESTO TOTAL EJECUCIÓN<br>
            <span style="color:#ffd700">{total_final:,.2f} €</span><br>
            <small style="font-size:18px; font-weight:normal;">
                Base Imponible: {total_neto:,.2f} € | IVA ({iva_tipo}%): {impuestos:,.2f} €
            </small>
        </div>
        """, unsafe_allow_html=True)

        # Generación de tabla de datos para exportación
        nombres_cap = ["DI", "Cuadro", "C1", "C2", "C3", "C4", "C5", "C8", "C9", "C10", "C11", "C12", "Tierras"]
        df_export = pd.DataFrame({"Descripción": nombres_cap, "Total (€)": resumen_costes})
        st.download_button("📥 Exportar Presupuesto a CSV", df_export.to_csv(index=False), "presupuesto_profesional.csv", "text/csv")
