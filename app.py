import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILO DARK INTEGRAL ---
st.set_page_config(page_title="Ingeniería Pro - Dark Mode Edition", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    
    .footer-container {
        position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%;
    }
    .watermark-text { font-size: 13px; color: rgba(255, 255, 255, 0.2); font-weight: normal; font-family: sans-serif; }

    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 22px;
        background-color: #1f2937; padding: 15px; border-radius: 10px;
        border-left: 6px solid #22d3ee; margin-bottom: 10px; text-align: right;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }

    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 38px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
        padding: 40px; border-radius: 20px; text-align: center;
        border: 2px solid #ffd700; margin-top: 40px;
        box-shadow: 0px 15px 30px rgba(0,0,0,0.6);
    }

    .stExpander { 
        border: 1px solid #374151 !important; border-radius: 12px !important; 
        background-color: #161b22 !important; margin-bottom: 15px !important;
    }

    .stNumberInput input, .stSelectbox div { background-color: #0d1117 !important; color: white !important; }
    </style>

    <div class="footer-container">
        <span class="watermark-text">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica Especializada</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. MOTOR DE CÁLCULO REBT (AMPLIADO SEGÚN ITC-BT-19 / UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Matriz de intensidades admisibles para Cobre (2 conductores cargados, 30°C aire / 20°C tierra)
tablas_adm = {
    "A1": {"PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321], 
           "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]},
    "A2": {"PVC": [14, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291], 
           "XLPE": [17.5, 24, 32, 41, 54, 73, 95, 117, 141, 179, 216, 249, 285, 324, 380]},
    "B1": {"PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400], 
           "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]},
    "B2": {"PVC": [16.5, 23, 30, 38, 52, 69, 92, 114, 138, 175, 210, 244, 282, 319, 375], 
           "XLPE": [21, 28, 38, 49, 66, 88, 117, 146, 175, 222, 269, 312, 358, 408, 481]},
    "C":  {"PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461], 
           "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]},
    "D1": {"PVC": [22, 29, 38, 47, 63, 81, 104, 125, 148, 183, 216, 246, 278, 312, 361], 
           "XLPE": [26, 34, 44, 56, 73, 95, 121, 146, 173, 213, 252, 287, 324, 363, 419]},
    "D2": {"PVC": [26, 34, 45, 56, 74, 96, 123, 147, 174, 216, 254, 290, 327, 367, 424], 
           "XLPE": [32, 42, 54, 67, 89, 115, 146, 175, 206, 256, 300, 341, 385, 433, 501]},
    "E":  {"PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286, 331, 381, 434, 511], 
           "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352, 410, 473, 542, 641]},
    "F":  {"PVC": [21, 28, 38, 50, 68, 92, 121, 150, 184, 233, 282, 327, 376, 428, 505], 
           "XLPE": [25, 34, 46, 61, 83, 112, 146, 181, 221, 281, 341, 396, 455, 517, 613]},
    "G":  {"PVC": [24, 33, 45, 57, 78, 106, 140, 173, 212, 268, 324, 376, 432, 492, 580], 
           "XLPE": [30, 40, 54, 69, 94, 127, 167, 208, 254, 322, 390, 451, 519, 591, 699]}
}

def get_seccion_adm(metodo_str, aislamiento, ib):
    # Extrae el primer código (ej: "A1") del string del selectbox
    m_code = metodo_str.split(" ")[0]
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    
    # Si el código existe en nuestras tablas, lo usamos; si no, por defecto C (el más común)
    intensidades = tablas_adm.get(m_code, tablas_adm["C"])[ais_key]
    
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib:
            return secciones_ref[i]
    return 240 # Límite superior por seguridad

# --- 3. BASE DE DATOS DE PRECIOS ---
precios_master = {
    "CABLES": {1.5: 0.28, 2.5: 0.42, 4: 0.68, 6: 1.35, 10: 2.25, 16: 3.60},
    "MANO_OBRA": {"Oficial": 34.00, "Ayudante": 28.50}
}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel de Control")
    modo = st.radio("Módulo:", ["📐 Calculadora REBT", "💰 Presupuesto Maestro"])
    
    if modo == "💰 Presupuesto Maestro":
        st.divider()
        gastos_gen = st.slider("% Gastos Generales", 0, 20, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA (%)", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 5. CALCULADORA TÉCNICA ---
if modo == "📐 Calculadora REBT":
    st.title("📐 Dimensionamiento de Líneas s/ REBT")
    c1, c2 = st.columns(2)
    with c1:
        sistema = st.selectbox("Suministro", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia (W)", value=5750, step=500)
        longitud = st.number_input("Longitud (m)", value=30.0, step=5.0)
        cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90)
        uso = st.selectbox("Uso Específico", ["General (1.0)", "Motores (1.25)", "Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        k_u = 1.25 if ("Motores" in uso or "Vehículo" in uso) else (1.8 if "Descarga" in uso else 1.0)
    
    with c2:
        material = st.radio("Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        
        # LISTA COMPLETA DE MÉTODOS REBT
        metodos_rebt_desc = [
            "A1 - Conductores aislados en tubo en pared aislante",
            "A2 - Cable multiconductor en tubo en pared aislante",
            "B1 - Conductores aislados en tubo sobre pared",
            "B2 - Cable multiconductor en tubo sobre pared",
            "C - Cable sobre pared",
            "D1 - Cable en conductos enterrados",
            "D2 - Cable enterrado directamente",
            "E - Cable multiconductor al aire libre",
            "F - Cables unipolares en contacto al aire libre",
            "G - Cables unipolares separados al aire libre"
        ]
        metodo_inst = st.selectbox("Método de Instalación", metodos_rebt_desc)
        max_cdt = st.number_input("CdT Máx (%)", value=3.0, step=0.5)

    # Lógica de cálculo
    v_fase = 230 if "Mono" in sistema else 400
    ib = (potencia * k_u) / (v_fase * cos_phi) if v_fase == 230 else (potencia * k_u) / (1.732 * v_fase * cos_phi)
    
    # 1. Sección por Intensidad Admisible
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    
    # 2. Sección por Caída de Tensión
    cond_gamma = (48 if "PVC" in aislamiento else 44) if "Cobre" in material else (30 if "PVC" in aislamiento else 28)
    s_cdt = (2 if v_fase == 230 else 1) * longitud * (potencia/v_fase if v_fase==230 else ib) * cos_phi / (cond_gamma * (max_cdt/100 * v_fase))
    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)
    
    # Resultado final (el mayor de ambos criterios)
    s_final = max(s_adm, s_cdt_norm)

    st.divider()
    st.markdown(f"""
    <div class="resultado-caja">
        SECCIÓN REGLAMENTARIA FINAL: {s_final} mm² <br>
        <small style='font-size: 14px;'>
            Criterio Térmico (Iadm): {s_adm} mm² | 
            Criterio CdT: {s_cdt:.2f} mm² (Norm: {s_cdt_norm} mm²) | 
            Intensidad Ib: {ib:.2f} A
        </small>
    </div>
    """, unsafe_allow_html=True)

# --- 6. PRESUPUESTO MAESTRO (11 CAPÍTULOS) ---
else:
    st.title("💰 Generador de Presupuestos DTIE")
    capitulos = []

    def render_capitulo(titulo, lista_materiales, h_of, h_ay):
        with st.expander(titulo):
            c_mat, c_mo = st.columns(2)
            tot_mat = 0
            for item in lista_materiales:
                q = c_mat.number_input(f"Cant: {item['nom']}", value=item['def_q'], key=f"q_{titulo}_{item['nom']}")
                p = c_mat.number_input(f"P.U. (€): {item['nom']}", value=item['def_p'], key=f"p_{titulo}_{item['nom']}")
                tot_mat += (q * p)
            h1 = c_mo.number_input("Horas Oficial", value=float(h_of), key=f"h1_{titulo}")
            h2 = c_mo.number_input("Horas Ayudante", value=float(h_ay), key=f"h2_{titulo}")
            tot_mo = (h1 * precios_master["MANO_OBRA"]["Oficial"]) + (h2 * precios_master["MANO_OBRA"]["Ayudante"])
            total_cap = (tot_mat + tot_mo) * f_multiplicador
            st.markdown(f'<div class="resultado-caja">{total_cap:,.2f} €</div>', unsafe_allow_html=True)
            return (titulo, total_cap)

    # Bloque de Capítulos
    capitulos.append(render_capitulo("CAP I: DERIVACIÓN INDIVIDUAL", [{'nom': "Cable 10mm² (m)", 'def_q': 45.0, 'def_p': 2.25}], 3, 2))
    capitulos.append(render_capitulo("CAP II: CUADRO GENERAL", [{'nom': "Caja 36 mod", 'def_q': 1.0, 'def_p': 58.0}, {'nom': "Protecciones", 'def_q': 1.0, 'def_p': 140.0}], 5, 0))
    capitulos.append(render_capitulo("CAP III: ALUMBRADO (C1)", [{'nom': "Mecanismos", 'def_q': 12.0, 'def_p': 4.50}, {'nom': "Cable 1.5mm²", 'def_q': 200.0, 'def_p': 0.28}], 8, 4))
    capitulos.append(render_capitulo("CAP IV: TOMAS GENERALES (C2)", [{'nom': "Bases 16A", 'def_q': 20.0, 'def_p': 5.20}, {'nom': "Cable 2.5mm²", 'def_q': 250.0, 'def_p': 0.42}], 10, 6))
    capitulos.append(render_capitulo("CAP V: COCINA Y HORNO (C3)", [{'nom': "Cable 6mm²", 'def_q': 25.0, 'def_p': 1.35}], 2, 1))
    capitulos.append(render_capitulo("CAP VI: LAVADORA/TERMO (C4)", [{'nom': "Cable 4mm²", 'def_q': 60.0, 'def_p': 0.68}], 4, 2))
    capitulos.append(render_capitulo("CAP VII: BAÑOS/COCINA (C5)", [{'nom': "Bases seg.", 'def_q': 6.0, 'def_p': 6.10}], 4, 2))
    capitulos.append(render_capitulo("CAP VIII: CLIMATIZACIÓN", [{'nom': "Línea dedicada", 'def_q': 1.0, 'def_p': 85.0}], 3, 0))
    capitulos.append(render_capitulo("CAP IX: PUESTA A TIERRA", [{'nom': "Pica + Cable desnudo", 'def_q': 1.0, 'def_p': 120.0}], 2, 2))
    capitulos.append(render_capitulo("CAP X: TELECOMUNICACIONES", [{'nom': "Tomas RTV/RJ45", 'def_q': 8.0, 'def_p': 12.0}], 6, 2))
    capitulos.append(render_capitulo("CAP XI: TASAS Y CERTIFICADOS", [{'nom': "CIE + Tasas", 'def_q': 1.0, 'def_p': 215.0}], 0, 0))

    # RESUMEN FINAL
    st.divider()
    total_neto = sum([val for nom, val in capitulos])
    total_con_iva = total_neto * (1 + iva_tipo/100)
    
    st.markdown(
        f'<div class="total-final-banner">'
        f'PRESUPUESTO FINAL (IVA {iva_tipo}% INCL.)<br>'
        f'{total_con_iva:,.2f} €'
        f'</div>', 
        unsafe_allow_html=True
    )




