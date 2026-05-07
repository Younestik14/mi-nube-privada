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

# --- 2. BASE DE DATOS DE PRECIOS AMPLIADA ---
precios_base = {
    "1,5mm": 0.25, "2,5mm": 0.38, "4mm": 0.64, "6mm": 1.30,
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, "IGA": 56.2, "DIF": 13.82,
    "DIF_SI": 45.50, # Diferencial Superinmunizado
    "PIA10": 3.60, "PIA16": 9.31, "PIA25": 3.64, 
    "INT": 2.44, "CONM": 2.42, "CRUZ": 5.74, 
    "DIMMER": 32.00, "DETECTOR": 28.50, # Regulación y sensores
    "TC16A": 2.79, "USB": 18.20, "TC25A": 7.10, 
    "PULS": 3.28, "ZUMB": 24.73,
    "RJ45": 12.50, "TV_SAT": 9.80, # Datos y TV
    "ELEC": 33.00, "OPER": 29.00, "UNIV": 0.13, "CAJAL": 1.30, "CAJAXL": 2.96,
    "BOLETIN": 150.00
}

# --- 3. MENÚ NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Gestión DTIE")
    modo = st.radio("Herramienta:", ["📐 Calculadora Técnica Completa", "💰 Presupuesto DTIE (Cap I-VIII)"])
    
    if modo == "💰 Presupuesto DTIE (Cap I-VIII)":
        st.divider()
        st.header("📈 Coeficientes de Venta")
        p_ben = st.slider("% Beneficio", 0, 30, 15)
        p_amo = st.slider("% Amortización", 0, 10, 5)
        p_iva = st.selectbox("% IVA", [21, 10, 0], index=0)
        f_total = 1 + (p_ben/100) + (p_amo/100)
    else:
        f_total = 1.0 

# --- 4. SECCIÓN: CALCULADORA TÉCNICA ---
if modo == "📐 Calculadora Técnica Completa":
    st.title("📐 Calculadora de Secciones REBT")
    col_a, col_b = st.columns(2)
    with col_a:
        red = st.selectbox("Tipo de Red", ["Monofásica 230V", "Trifásica 400V"])
        P = st.number_input("Potencia (W)", value=5750)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de potencia", 0.70, 1.00, 0.90)
    with col_b:
        material = st.radio("Material", ["Cobre", "Aluminio"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        caida_max = st.number_input("Caída de tensión máx (%)", value=3.0)

    # Cálculo simplificado para visualización
    V = 230 if "Mono" in red else 400
    Ib = P / (V * cos_phi) if V == 230 else P / (1.732 * V * cos_phi)
    gamma = 48 if material == "Cobre" else 30
    e_lim = (caida_max / 100) * V
    S_cdt = (2 if V == 230 else 1) * L * Ib * cos_phi / (gamma * e_lim)
    
    st.divider()
    st.markdown(f'<div class="resultado-negro">Intensidad: {Ib:.2f} A | Sección teórica: {S_cdt:.2f} mm²</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: PRESUPUESTO DETALLADO ---
else:
    st.title("💰 Presupuesto DTIE - Desglose Profesional")
    caps = []

    # CAP I: DI
    with st.expander("I. DERIVACIÓN INDIVIDUAL", expanded=False):
        c1 = (st.number_input("Metros 6mm²", 0, 500, 48)*precios_base["6mm"] + 2.0*precios_base["ELEC"]) * f_total
        caps.append(("I. DERIVACIÓN INDIVIDUAL", c1))

    # CAP II: CUADRO PRO
    with st.expander("II. CUADRO DE PROTECCIÓN (EQUIPAMIENTO AVANZADO)", expanded=False):
        q_dif_std = st.number_input("Diferenciales Clase AC (Estándar)", value=1)
        q_dif_si = st.number_input("Diferenciales Clase A (Superinmunizados - Recomendado)", value=1)
        q_pia16 = st.number_input("PIA 16A (Circuitos C2, C4, C5)", value=5)
        coste = (precios_base["Cuadro"] + precios_base["IGA"] + q_dif_std*precios_base["DIF"] + 
                 q_dif_si*precios_base["DIF_SI"] + q_pia16*precios_base["PIA16"] + 3.0*precios_base["ELEC"]) * f_total
        caps.append(("II. CUADRO DE PROTECCIÓN", coste))

    # CAP III: ALUMBRADO Y SENSORES
    with st.expander("III. ALUMBRADO (Control y Regulación)", expanded=False):
        q_int = st.number_input("Interruptores/Conmutadores", value=12)
        q_dim = st.number_input("Reguladores de Intensidad (Dimmer LED)", value=2)
        q_det = st.number_input("Detectores de Presencia (Pasillos/Baños)", value=1)
        m_15 = st.number_input("Metros 1.5mm² (Iluminación)", value=315)
        coste = (q_int*precios_base["INT"] + q_dim*precios_base["DIMMER"] + q_det*precios_base["DETECTOR"] + 
                 m_15*precios_base["1,5mm"] + 8.0*precios_base["ELEC"]) * f_total
        caps.append(("III. CIRCUITO DE ILUMINACIÓN", coste))

    # CAP IV: TOMAS DE CORRIENTE Y USB
    with st.expander("IV. TOMAS DE CORRIENTE Y CARGA USB", expanded=False):
        q_tc = st.number_input("Bases de Enchufe 16A", value=18)
        q_usb = st.number_input("Tomas de Carga Doble USB (Empotradas)", value=3)
        m_25 = st.number_input("Metros 2.5mm² (Tomas)", value=325)
        coste = (q_tc*precios_base["TC16A"] + q_usb*precios_base["USB"] + m_25*precios_base["2,5mm"]) * f_total
        caps.append(("IV. CIRCUITO TOMAS USO GENERAL", coste))

    # CAP V-VII: CIRCUITOS POTENCIA
    with st.expander("V-VII. CIRCUITOS DE POTENCIA (C3, C4, C5)", expanded=False):
        c5_coste = (30*precios_base["6mm"] + 2*precios_base["TC25A"] + 85*precios_base["4mm"] + 120*precios_base["2,5mm"]) * f_total
        caps.append(("V-VII. CIRCUITOS DE POTENCIA", c5_coste))

    # CAP VIII: TELECOM Y MULTIMEDIA
    with st.expander("VIII. TELECOMUNICACIONES, DATOS Y TV", expanded=False):
        q_rj45 = st.number_input("Tomas de Datos RJ45 (Cat6)", value=4)
        q_tv = st.number_input("Tomas TV/SAT", value=3)
        q_zumb = st.number_input("Sistema de Timbre/Aviso", value=1)
        c_extra = st.number_input("Gestión Boletín Eléctrico (CIE)", value=150.0)
        coste = (q_rj45*precios_base["RJ45"] + q_tv*precios_base["TV_SAT"] + q_zumb*precios_base["ZUMB"] + c_extra) * f_total
        caps.append(("VIII. TELECOM. Y GESTIÓN", coste))

    # RESUMEN
    st.divider()
    total_bi = 0
    for nombre, importe in caps:
        c1, c2 = st.columns([3, 1])
        c1.write(nombre)
        c2.markdown(f'<div class="resultado-negro">{importe:,.2f} €</div>', unsafe_allow_html=True)
        total_bi += importe
    
    st.markdown(f'<div class="total-final">TOTAL FINAL (IVA INCL.): {(total_bi * (1+p_iva/100)):,.2f} €</div>', unsafe_allow_html=True)
