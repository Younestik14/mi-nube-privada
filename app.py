import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Ingeniería Pro - DTIE", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .watermark {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        font-family: sans-serif; font-size: 16px; color: rgba(255, 255, 255, 0.6);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%; font-weight: bold;
    }
    p, label, .stMarkdown, div, span, button { font-weight: bold !important; }
    .resultado-negro {
        color: #000000 !important; font-weight: 900 !important; font-size: 20px;
        background-color: #f8f9fa; padding: 10px; border-radius: 8px;
        border-left: 5px solid #000000; margin-bottom: 5px; text-align: right;
    }
    .total-final {
        color: #ffffff !important; font-weight: 900 !important; font-size: 28px;
        background-color: #000000; padding: 15px; border-radius: 10px; text-align: center;
    }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE DATOS DE PRECIOS (SEGÚN EXCEL PRODUCTOS) ---
precios_base = {
    "1.5mm": 0.25, "2.5mm": 0.38, "4mm": 0.64, "6mm": 1.30,
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, "IGA": 56.20,
    "DIF": 13.82, "PIA10": 3.60, "PIA16": 9.31, "PIA25": 3.64,
    "INT": 2.44, "CONM": 2.42, "CRUZ": 5.74, "TC16A": 2.79,
    "TC25A": 7.10, "PULS": 3.28, "ZUMB": 24.73,
    "ELEC": 33.00, "OPER": 29.00  # Mano de obra base
}

# --- 3. MENÚ NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Gestión DTIE")
    modo = st.radio("Herramienta:", ["📐 Calculadora REBT", "💰 Presupuesto DTIE"])
    st.divider()
    st.header("📈 Coeficientes")
    p_ben = st.slider("% Beneficio", 0, 30, 15)
    p_amo = st.slider("% Amortización", 0, 10, 5)
    p_iva = st.selectbox("% IVA", [21, 10, 0], index=0)
    
    # El multiplicador que se aplica al precio base (Justificación de precios)
    f_total = 1 + (p_ben/100) + (p_amo/100)

# --- 4. SECCIÓN: CALCULADORA REBT ---
if modo == "📐 Calculadora REBT":
    st.title("📐 Cálculo Técnico de Secciones")
    c1, c2 = st.columns(2)
    with c1:
        potencia = st.number_input("Potencia (W)", value=5750)
        distancia = st.number_input("Longitud (m)", value=25)
    with c2:
        v = st.selectbox("Tensión", [230, 400])
        cdt_max = st.number_input("Caída tensión máx %", value=3.0)
    
    # Cálculo
    cos_phi = 0.9
    gamma = 48 # Cobre PVC
    ib = potencia / (v * cos_phi) if v == 230 else potencia / (1.732 * v * cos_phi)
    e = (cdt_max/100) * v
    s = (2 if v == 230 else 1) * distancia * ib * cos_phi / (gamma * e)
    
    st.markdown(f'<div class="resultado-negro">Intensidad: {ib:.2f} A</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="resultado-negro">Sección calculada: {s:.2f} mm²</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: PRESUPUESTO ESQUEMA DTIE ---
else:
    st.title("💰 Presupuesto por Capítulos (Esquema DTIE)")
    
    capitulos_data = []

    # CAP I: DERIVACIÓN INDIVIDUAL
    with st.expander("I. DERIVACIÓN INDIVIDUAL", expanded=False):
        m_6mm = st.number_input("Metros cable 6mm²", value=48, key="c1_1")
        h_elec = st.number_input("Horas Oficial 1ª (Derivación)", value=2.0, key="c1_2")
        h_oper = st.number_input("Horas Operario (Derivación)", value=1.5, key="c1_3")
        
        coste_i = (m_6mm * precios_base["6mm"] + h_elec * precios_base["ELEC"] + h_oper * precios_base["OPER"]) * f_total
        capitulos_data.append(("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", coste_i))

    # CAP II: CUADRO DE PROTECCIÓN
    with st.expander("II. CUADRO DE PROTECCIÓN", expanded=False):
        q_cuadro = st.number_input("Cuadro 36 mód. (Ud)", value=1)
        q_iga = st.number_input("IGA + Sobretensiones (Ud)", value=1)
        q_dif = st.number_input("Diferenciales (Ud)", value=2)
        q_p25 = st.number_input("PIA 25A (Ud)", value=1)
        q_p16 = st.number_input("PIA 16A (Ud)", value=4)
        q_p10 = st.number_input("PIA 10A (Ud)", value=2)
        
        coste_ii = (q_cuadro * precios_base["Cuadro"] + q_iga * precios_base["IGA"] + 
                    q_dif * precios_base["DIF"] + q_p25 * precios_base["PIA25"] + 
                    q_p16 * precios_base["PIA16"] + q_p10 * precios_base["PIA10"]) * f_total
        capitulos_data.append(("CAPÍTULO II: CUADRO DE PROTECCIÓN", coste_ii))

    # CAP III: ILUMINACIÓN (C1)
    with st.expander("III. CIRCUITO DE ILUMINACIÓN (C1)", expanded=False):
        m_15 = st.number_input("Metros cable 1.5mm²", value=315)
        m_t20 = st.number_input("Metros Tubo 20mm (C1)", value=90)
        n_int = st.number_input("Interruptores (Ud)", value=4)
        n_con = st.number_input("Conmutadores (Ud)", value=10)
        
        coste_iii = (m_15 * precios_base["1.5mm"] + m_t20 * precios_base["20mm"] + 
                     n_int * precios_base["INT"] + n_con * precios_base["CONM"]) * f_total
        capitulos_data.append(("CAPÍTULO III: CIRCUITO DE ILUMINACIÓN", coste_iii))

    # CAP IV: TOMAS DE CORRIENTE (C2)
    with st.expander("IV. TOMAS USO GENERAL (C2)", expanded=False):
        m_25 = st.number_input("Metros cable 2.5mm² (C2)", value=325)
        m_t20_c2 = st.number_input("Metros Tubo 20mm (C2)", value=75)
        n_tc16 = st.number_input("Bases Enchufe 16A (C2)", value=18)
        
        coste_iv = (m_25 * precios_base["2.5mm"] + m_t20_c2 * precios_base["20mm"] + 
                    n_tc16 * precios_base["TC16A"]) * f_total
        capitulos_data.append(("CAPÍTULO IV: TOMAS DE CORRIENTE (C2)", coste_iv))

    # CAP V, VI, VII (Resumen de Potencia)
    with st.expander("V, VI, VII. COCINA, LAVADORA Y BAÑOS (C3, C4, C5)", expanded=False):
        n_tc25 = st.number_input("Bases Enchufe 25A (Cocina)", value=2)
        m_cable_c3 = st.number_input("Metros cable 6mm² (C3)", value=30)
        m_cable_c4 = st.number_input("Metros cable 4mm² (C4)", value=85)
        n_tc16_pot = st.number_input("Bases Enchufe 16A (C4+C5)", value=9)
        
        coste_v_vii = (n_tc25 * precios_base["TC25A"] + m_cable_c3 * precios_base["6mm"] + 
                       m_cable_c4 * precios_base["4mm"] + n_tc16_pot * precios_base["TC16A"]) * f_total
        capitulos_data.append(("CAPÍTULOS V-VII: CIRCUITOS DE POTENCIA", coste_v_vii))

    # CAP VIII: TELEFONÍA, TV Y TIMBRE
    with st.expander("VIII. TELECOMUNICACIONES Y TIMBRE", expanded=False):
        n_puls = st.number_input("Pulsadores (Ud)", value=1)
        n_zumb = st.number_input("Zumbador (Ud)", value=1)
        m_t20_viii = st.number_input("Tubo 20mm (Aux)", value=25)
        
        coste_viii = (n_puls * precios_base["PULS"] + n_zumb * precios_base["ZUMB"] + 
                      m_t20_viii * precios_base["20mm"]) * f_total
        capitulos_data.append(("CAPÍTULO VIII: TELECOM., TV Y TIMBRE", coste_viii))

    # --- RESUMEN FINAL ---
    st.divider()
    st.subheader("📊 RESUMEN DEL PRESUPUESTO")
    
    total_bi = 0
    for nombre, importe in capitulos_data:
        col_n, col_v = st.columns([3, 1])
        col_n.write(nombre)
        col_v.markdown(f'<div class="resultado-negro">{importe:,.2f} €</div>', unsafe_allow_html=True)
        total_bi += importe
    
    total_iva = total_bi * (p_iva / 100)
    total_presupuesto = total_bi + total_iva

    st.markdown(f'<div class="total-final">TOTAL PRESUPUESTO: {total_presupuesto:,.2f} €</div>', unsafe_allow_html=True)
