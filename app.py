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

# --- 2. BASE DE DATOS DE PRECIOS BASE ---
precios_base = {
    "1,5mm": 0.25, "2,5mm": 0.38, "4mm": 0.64, "6mm": 1.30,
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, "IGA": 56.2, "DIF": 13.82,
    "DIF_SI": 45.50, "PIA10": 3.60, "PIA16": 9.31, "PIA25": 3.64,
    "INT": 2.44, "CONM": 2.42, "CRUZ": 5.74, "DIMMER": 32.00, "DETECTOR": 28.50,
    "TC16A": 2.79, "USB": 18.20, "TC25A": 7.10, "PULS": 3.28, "ZUMB": 24.73,
    "RJ45": 12.50, "TV_SAT": 9.80, "ELEC": 33.00, "OPER": 29.00,
    "UNIV": 0.13, "CAJAL": 1.30, "CAJAXL": 2.96, "BOLETIN": 150.00
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

# --- 4. SECCIÓN: CALCULADORA TÉCNICA COMPLETA (VERSIÓN ORIGINAL) ---
if modo == "📐 Calculadora Técnica Completa":
    st.title("📐 Calculadora de Secciones REBT (Versión Completa)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Datos de la Carga")
        red = st.selectbox("Tipo de Red", ["Monofásica 230V", "Trifásica 400V"])
        P = st.number_input("Potencia (W)", value=5750, step=100)
        L = st.number_input("Longitud de la línea (m)", value=25.0, step=1.0)
        cos_phi = st.slider("Factor de potencia (cos φ)", 0.70, 1.00, 0.90)
        k_recep = st.selectbox("Factor Receptores", ["General (1.0)", "Motores (1.25)", "Descarga/LED (1.8)"])
        k = 1.25 if "Motores" in k_recep else (1.8 if "Descarga" in k_recep else 1.0)

    with col_b:
        st.subheader("Instalación y Entorno")
        material = st.radio("Material del Conductor", ["Cobre", "Aluminio"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo = st.selectbox("Método de Instalación (ITC-BT-19)", 
                             ["A1 - Empotrado en tubo", "B1 - Superficie en tubo", "C - Cable bajo pared", "E - Aire libre"])
        t_amb = st.number_input("Temperatura Ambiente (°C)", value=40)
        caida_max = st.number_input("Caída de tensión máxima admitida (%)", value=3.0)

    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (math.sqrt(3) * V * cos_phi)
    
    if material == "Cobre":
        gamma = 48 if "PVC" in aislamiento else 44
    else:
        gamma = 30 if "PVC" in aislamiento else 28

    e_lim = (caida_max / 100) * V
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * e_lim)
    
    secciones_comerciales = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95]
    s_final = next((x for x in secciones_comerciales if x >= S_cdt), "Fuera de rango")

    st.divider()
    res1, res2, res3 = st.columns(3)
    with res1:
        st.write("Intensidad de Diseño (Ib):")
        st.markdown(f'<div class="resultado-negro">{Ib:.2f} A</div>', unsafe_allow_html=True)
    with res2:
        st.write("Sección teórica por CdT:")
        st.markdown(f'<div class="resultado-negro">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)
    with res3:
        st.write("SECCIÓN COMERCIAL:")
        st.markdown(f'<div class="resultado-negro" style="background-color: #e7f3ff;">{s_final} mm²</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: PRESUPUESTO DTIE (CAP I-VIII DETALLADO) ---
else:
    st.title("💰 Presupuesto DTIE - Desglose Profesional con Nuevos Mecanismos")
    caps = []

    # CAP I
    with st.expander("I. DERIVACIÓN INDIVIDUAL", expanded=False):
        coste = (st.number_input("Metros 6mm² (DI)", value=48)*precios_base["6mm"] + 2.0*precios_base["ELEC"] + 1.5*precios_base["OPER"]) * f_total
        caps.append(("I. DERIVACIÓN INDIVIDUAL", coste))

    # CAP II
    with st.expander("II. CUADRO DE PROTECCIÓN (EQUIPAMIENTO COMPLETO)", expanded=False):
        q_si = st.number_input("Diferenciales Superinmunizados (Clase A)", value=1)
        q_std = st.number_input("Diferenciales Estándar", value=1)
        coste = (precios_base["Cuadro"] + precios_base["IGA"] + q_si*precios_base["DIF_SI"] + q_std*precios_base["DIF"] + 5*precios_base["PIA16"] + 3.0*precios_base["ELEC"]) * f_total
        caps.append(("II. CUADRO DE PROTECCIÓN", coste))

    # CAP III
    with st.expander("III. CIRCUITO DE ILUMINACIÓN (Control y Confort)", expanded=False):
        q_dim = st.number_input("Reguladores (Dimmers LED)", value=2)
        q_det = st.number_input("Detectores de Movimiento", value=1)
        m_15 = st.number_input("Metros 1.5mm² (Iluminación)", value=315)
        coste = (m_15*precios_base["1,5mm"] + q_dim*precios_base["DIMMER"] + q_det*precios_base["DETECTOR"] + 12*precios_base["INT"] + 8.0*precios_base["ELEC"]) * f_total
        caps.append(("III. CIRCUITO DE ILUMINACIÓN", coste))

    # CAP IV
    with st.expander("IV. TOMAS USO GENERAL Y CARGA USB", expanded=False):
        q_usb = st.number_input("Tomas Doble USB Empotradas", value=3)
        q_tc = st.number_input("Bases de Enchufe 16A", value=18)
        m_25 = st.number_input("Metros 2.5mm² (Tomas)", value=325)
        coste = (m_25*precios_base["2,5mm"] + q_tc*precios_base["TC16A"] + q_usb*precios_base["USB"] + 10.0*precios_base["ELEC"]) * f_total
        caps.append(("IV. CIRCUITO TOMAS USO GENERAL", coste))

    # CAP V, VI, VII (Independientes)
    with st.expander("V. CIRCUITO DE COCINA Y HORNO (C3)", expanded=False):
        coste = (30*precios_base["6mm"] + 2*precios_base["TC25A"] + 5*precios_base["25mm"]) * f_total
        caps.append(("V. CIRCUITO DE COCINA Y HORNO", coste))

    with st.expander("VI. CIRCUITO DE LAVADORA Y TERMO (C4)", expanded=False):
        coste = (85*precios_base["4mm"] + 3*precios_base["TC16A"] + 4.0*precios_base["ELEC"]) * f_total
        caps.append(("VI. CIRCUITO DE LAVADORA Y TERMO", coste))

    with st.expander("VII. CIRCUITO DE BAÑOS Y AUXILIAR (C5)", expanded=False):
        coste = (120*precios_base["2,5mm"] + 6*precios_base["TC16A"] + 5.0*precios_base["ELEC"]) * f_total
        caps.append(("VII. CIRCUITO DE BAÑOS Y AUXILIAR", coste))

    # CAP VIII
    with st.expander("VIII. TELECOMUNICACIONES, DATOS Y GESTIÓN", expanded=False):
        q_rj = st.number_input("Puntos de Red RJ45 (Datos)", value=4)
        q_tv = st.number_input("Tomas TV/SAT", value=3)
        c_cie = st.checkbox("Certificado Instalación (Boletín)", value=True)
        coste = (q_rj*precios_base["RJ45"] + q_tv*precios_base["TV_SAT"] + precios_base["ZUMB"] + (150 if c_cie else 0)) * f_total
        caps.append(("VIII. TELECOM. Y GESTIÓN", coste))

    # RESUMEN
    st.divider()
    total_bi = 0
    for nombre, importe in caps:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{nombre}**")
        c2.markdown(f'<div class="resultado-negro">{importe:,.2f} €</div>', unsafe_allow_html=True)
        total_bi += importe
    
    st.markdown(f'<div class="total-final">TOTAL FINAL (IVA {p_iva}%): {(total_bi * (1+p_iva/100)):,.2f} €</div>', unsafe_allow_html=True)
