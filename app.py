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
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, 
    "IGA_COMBI": 67.44, # IGA + Sobretensiones Combinado
    "DIF": 13.82, "DIF_SI": 45.50,
    "PIA10": 3.60, "PIA16": 9.31, "PIA20": 10.50, "PIA25": 3.64,
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

# --- 4. SECCIÓN: CALCULADORA TÉCNICA COMPLETA (MANTENIDA) ---
if modo == "📐 Calculadora Técnica Completa":
    st.title("📐 Calculadora de Secciones REBT")
    col_a, col_b = st.columns(2)
    with col_a:
        red = st.selectbox("Tipo de Red", ["Monofásica 230V", "Trifásica 400V"])
        P = st.number_input("Potencia (W)", value=5750)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de potencia", 0.70, 1.00, 0.90)
        k_recep = st.selectbox("Factor Receptores", ["General (1.0)", "Motores (1.25)", "Descarga/LED (1.8)"])
        k = 1.25 if "Motores" in k_recep else (1.8 if "Descarga" in k_recep else 1.0)
    with col_b:
        material = st.radio("Material", ["Cobre", "Aluminio"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        metodo = st.selectbox("Método de Instalación", ["A1 - Empotrado", "B1 - Superficie", "C - Bajo pared", "E - Aire libre"])
        t_amb = st.number_input("Temp. Ambiente (°C)", value=40)
        caida_max = st.number_input("Caída tensión máx (%)", value=3.0)

    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (math.sqrt(3) * V * cos_phi)
    gamma = (48 if "PVC" in aislamiento else 44) if material == "Cobre" else (30 if "PVC" in aislamiento else 28)
    e_lim = (caida_max / 100) * V
    S_cdt = (2 if V == 230 else 1) * L * Ib * cos_phi / (gamma * e_lim)
    
    st.divider()
    res1, res2 = st.columns(2)
    res1.metric("Intensidad (Ib)", f"{Ib:.2f} A")
    res2.metric("Sección Teórica", f"{S_cdt:.2f} mm²")

# --- 5. SECCIÓN: PRESUPUESTO DETALLADO ---
else:
    st.title("💰 Presupuesto DTIE - Desglose Total de Materiales y MO")
    caps = []

    # CAP I
    with st.expander("I. DERIVACIÓN INDIVIDUAL", expanded=False):
        coste = (st.number_input("Metros 6mm²", value=48)*precios_base["6mm"] + 2.0*precios_base["ELEC"] + 1.5*precios_base["OPER"]) * f_total
        caps.append(("I. DERIVACIÓN INDIVIDUAL", coste))

    # CAP II: CUADRO CON IGA COMBI Y PIAs DETALLADOS
    with st.expander("II. CUADRO DE PROTECCIÓN (IGA COMBI + PIAs)", expanded=True):
        st.subheader("Protecciones de Cabecera")
        q_iga = st.number_input("IGA Combinado + Sobretensiones (Combi)", value=1)
        q_dif_si = st.number_input("Diferenciales Superinmunizados (SI)", value=1)
        q_dif_std = st.number_input("Diferenciales Estándar", value=1)
        
        st.subheader("Desglose de Magnetotérmicos (PIAs)")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p10 = st.number_input("PIA 10A (C1 - Alumbrado)", value=2)
            p16 = st.number_input("PIA 16A (C2 - Tomas / C5 - Baños)", value=5)
        with col_p2:
            p20 = st.number_input("PIA 20A (C4 - Lavadora/Termo)", value=1)
            p25 = st.number_input("PIA 25A (C3 - Cocina/Horno)", value=1)
        
        h_mo_c = st.number_input("Horas Montaje y Cableado Cuadro", value=4.5)
        
        coste_mat = (precios_base["Cuadro"] + q_iga*precios_base["IGA_COMBI"] + 
                     q_dif_si*precios_base["DIF_SI"] + q_dif_std*precios_base["DIF"] +
                     p10*precios_base["PIA10"] + p16*precios_base["PIA16"] + 
                     p20*precios_base["PIA20"] + p25*precios_base["PIA25"])
        coste_total = (coste_mat + h_mo_c*precios_base["ELEC"]) * f_total
        caps.append(("II. CUADRO DE PROTECCIÓN", coste_total))

    # CAP III
    with st.expander("III. CIRCUITO DE ILUMINACIÓN (C1)", expanded=False):
        coste = (315*precios_base["1,5mm"] + 12*precios_base["INT"] + 2*precios_base["DIMMER"] + 1*precios_base["DETECTOR"] + 8.0*precios_base["ELEC"]) * f_total
        caps.append(("III. CIRCUITO DE ILUMINACIÓN", coste))

    # CAP IV
    with st.expander("IV. TOMAS USO GENERAL Y USB (C2)", expanded=False):
        coste = (325*precios_base["2,5mm"] + 18*precios_base["TC16A"] + 3*precios_base["USB"] + 10.0*precios_base["ELEC"]) * f_total
        caps.append(("IV. CIRCUITO TOMAS USO GENERAL", coste))

    # CAP V, VI, VII
    with st.expander("V-VII. CIRCUITOS DE POTENCIA (C3, C4, C5)", expanded=False):
        coste = (30*precios_base["6mm"] + 2*precios_base["TC25A"] + 85*precios_base["4mm"] + 120*precios_base["2,5mm"] + 12.0*precios_base["ELEC"]) * f_total
        caps.append(("V-VII. CIRCUITOS DE POTENCIA", coste))

    # CAP VIII
    with st.expander("VIII. TELECOMUNICACIONES, DATOS Y GESTIÓN", expanded=False):
        coste = (4*precios_base["RJ45"] + 3*precios_base["TV_SAT"] + precios_base["ZUMB"] + 150.0 + 4.0*precios_base["ELEC"]) * f_total
        caps.append(("VIII. TELECOM. Y GESTIÓN", coste))

    # RESUMEN FINAL
    st.divider()
    total_bi = 0
    for n, i in caps:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{n}**")
        c2.markdown(f'<div class="resultado-negro">{i:,.2f} €</div>', unsafe_allow_html=True)
        total_bi += i
    
    st.markdown(f'<div class="total-final">TOTAL FINAL (IVA {p_iva}%): {(total_bi * (1+p_iva/100)):,.2f} €</div>', unsafe_allow_html=True)
