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

# --- 2. BASE DE DATOS DE PRECIOS BASE (DTIE) ---
precios_base = {
    "1,5mm": 0.25, "2,5mm": 0.38, "4mm": 0.64, "6mm": 1.30,
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, "IGA": 56.2, "DIF": 13.82,
    "PIA10": 3.60, "PIA16": 9.31, "PIA25": 3.64, "INT": 2.44, "CONM": 2.42,
    "CRUZ": 5.74, "TC16A": 2.79, "TC25A": 7.10, "PULS": 3.28, "ZUMB": 24.73,
    "ELEC": 33.00, "OPER": 29.00
}

# --- 3. MENÚ NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Gestión DTIE")
    modo = st.radio("Herramienta:", ["📐 Calculadora Técnica Completa", "💰 Presupuesto DTIE (Cap I-VIII)"])
    
    # Los coeficientes solo se muestran si el modo es Presupuesto
    if modo == "💰 Presupuesto DTIE (Cap I-VIII)":
        st.divider()
        st.header("📈 Coeficientes de Venta")
        p_ben = st.slider("% Beneficio", 0, 30, 15)
        p_amo = st.slider("% Amortización", 0, 10, 5)
        p_iva = st.selectbox("% IVA", [21, 10, 0], index=0)
        f_total = 1 + (p_ben/100) + (p_amo/100)
    else:
        f_total = 1.0 # En calculadora técnica no aplicamos márgenes comerciales
        p_iva = 0

# --- 4. SECCIÓN: CALCULADORA TÉCNICA COMPLETA ---
if modo == "📐 Calculadora Técnica Completa":
    st.title("📐 Calculadora de Secciones REBT (Criterios Técnicos)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Datos de la Carga")
        red = st.selectbox("Tipo de Red", ["Monofásica 230V", "Trifásica 400V"])
        P = st.number_input("Potencia (W)", value=5750, step=100)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de potencia (cos φ)", 0.70, 1.00, 0.90)
        k_recep = st.selectbox("Factor Receptores", ["General (1.0)", "Motores (1.25)", "Descarga/LED (1.8)"])
        k = 1.25 if "Motores" in k_recep else (1.8 if "Descarga" in k_recep else 1.0)

    with col_b:
        st.subheader("Instalación y Entorno")
        material = st.radio("Material del Conductor", ["Cobre", "Aluminio"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo = st.selectbox("Método de Instalación", ["A1 - Empotrado", "B1 - Superficie", "C - Bajo pared"])
        t_amb = st.number_input("Temperatura Ambiente (°C)", value=40)
        caida_max = st.number_input("Caída de tensión máx (%)", value=3.0)

    # Lógica REBT
    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (math.sqrt(3) * V * cos_phi)
    gamma = (48 if "PVC" in aislamiento else 44) if material == "Cobre" else (30 if "PVC" in aislamiento else 28)
    e_lim = (caida_max / 100) * V
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * e_lim)
    
    st.divider()
    res1, res2 = st.columns(2)
    with res1:
        st.write("Intensidad de Diseño (Ib):")
        st.markdown(f'<div class="resultado-negro">{Ib:.2f} A</div>', unsafe_allow_html=True)
    with res2:
        st.write("Sección teórica por CdT:")
        st.markdown(f'<div class="resultado-negro">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: PRESUPUESTO DTIE ---
else:
    st.title("💰 Presupuesto DTIE - Detalle por Capítulos")
    capitulos_finales = []

    # Capítulo I
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", expanded=False):
        m1 = st.number_input("Metros cable 6mm²", value=48)
        h1 = st.number_input("Horas Oficial 1ª", value=2.0)
        h2 = st.number_input("Horas Operario", value=1.5)
        coste = (m1*precios_base["6mm"] + h1*precios_base["ELEC"] + h2*precios_base["OPER"]) * f_total
        capitulos_finales.append(("I. DERIVACIÓN INDIVIDUAL", coste))

    # Capítulo II
    with st.expander("CAPÍTULO II: CUADRO DE PROTECCIÓN", expanded=False):
        c2_1 = st.number_input("Cuadro (Ud)", value=1)
        c2_2 = st.number_input("IGA (Ud)", value=1)
        c2_3 = st.number_input("Diferenciales (Ud)", value=2)
        coste = (c2_1*precios_base["Cuadro"] + c2_2*precios_base["IGA"] + c2_3*precios_base["DIF"]) * f_total
        capitulos_finales.append(("II. CUADRO DE PROTECCIÓN", coste))

    # Capítulos III al VIII (Resumen de lógica)
    with st.expander("CAPÍTULOS III - IV: ILUMINACIÓN Y TOMAS", expanded=False):
        c3_1 = st.number_input("Metros 1,5mm²", value=315)
        c4_1 = st.number_input("Metros 2,5mm²", value=325)
        coste = (c3_1*precios_base["1,5mm"] + c4_1*precios_base["2,5mm"]) * f_total
        capitulos_finales.append(("III-IV. LUZ Y TOMAS", coste))

    with st.expander("CAPÍTULO VIII: TELECOM Y TIMBRE", expanded=False):
        c8_1 = st.number_input("Pulsadores", value=1)
        c8_2 = st.number_input("Zumbador", value=1)
        coste = (c8_1*precios_base["PULS"] + c8_2*precios_base["ZUMB"]) * f_total
        capitulos_finales.append(("VIII. TELECOM. Y TIMBRE", coste))

    # --- RESUMEN FINAL ---
    st.divider()
    st.subheader("📊 RESUMEN ECONÓMICO")
    total_bi = sum(imp for _, imp in capitulos_finales)
    
    for cap, imp in capitulos_finales:
        c_n, c_v = st.columns([3, 1])
        c_n.write(cap)
        c_v.markdown(f'<div class="resultado-negro">{imp:,.2f} €</div>', unsafe_allow_html=True)
    
    total_iva = total_bi * (p_iva / 100)
    st.markdown(f'<div class="total-final">TOTAL PRESUPUESTO: {(total_bi + total_iva):,.2f} €</div>', unsafe_allow_html=True)
