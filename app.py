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

# --- 2. BASE DE DATOS DE PRECIOS (DATOS EXTRAÍDOS DE TUS EXCEL) ---
precios_base = {
    "1,5mm": 0.25, "2,5mm": 0.38, "4mm": 0.64, "6mm": 1.30,
    "20mm": 0.16, "25mm": 0.23, "Cuadro": 53.92, "IGA": 56.20,
    "DIF": 13.82, "PIA10": 3.60, "PIA16": 9.31, "PIA25": 3.64,
    "INT": 2.44, "CONM": 2.42, "CRUZ": 5.74, "TC16A": 2.79,
    "TC25A": 7.10, "PULS": 3.28, "ZUMB": 24.73, "UNIV": 0.13,
    "CAJAL": 1.30, "CAJAXL": 2.96, "ELEC": 33.00, "OPER": 29.00
}

# --- 3. MENÚ NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Gestión DTIE")
    modo = st.radio("Herramienta:", ["📐 Calculadora Técnica Completa", "💰 Presupuesto DTIE (Cap I-VIII)"])
    st.divider()
    st.header("📈 Coeficientes de Venta")
    p_ben = st.slider("% Beneficio", 0, 30, 15)
    p_amo = st.slider("% Amortización", 0, 10, 5)
    p_iva = st.selectbox("% IVA", [21, 10, 0], index=0)
    
    # Factor de justificación de precios (Base + Beneficio + Amortización)
    f_total = 1 + (p_ben/100) + (p_amo/100)

# --- 4. SECCIÓN: CALCULADORA TÉCNICA COMPLETA ---
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

    # Lógica de Cálculo REBT
    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (math.sqrt(3) * V * cos_phi)
    
    # Conductividad según material y aislamiento
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

# --- 5. SECCIÓN: PRESUPUESTO DTIE (CAP I-VIII) ---
else:
    st.title("💰 Presupuesto DTIE - Esquema de Capítulos")
    
    capitulos_finales = []

    # CAPÍTULO I
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", expanded=False):
        m1 = st.number_input("Metros cable 6mm² (DI)", 0, 500, 48)
        h1 = st.number_input("Horas Oficial 1ª (DI)", 0.0, 100.0, 2.0)
        h2 = st.number_input("Horas Operario (DI)", 0.0, 100.0, 1.5)
        coste = (m1 * precios_base["6mm"] + h1 * precios_base["ELEC"] + h2 * precios_base["OPER"]) * f_total
        capitulos_finales.append(("I. DERIVACIÓN INDIVIDUAL", coste))

    # CAPÍTULO II
    with st.expander("CAPÍTULO II: CUADRO DE PROTECCIÓN", expanded=False):
        c2_1 = st.number_input("Cuadro 36 mód.", 0, 5, 1)
        c2_2 = st.number_input("IGA + Sobretensiones", 0, 5, 1)
        c2_3 = st.number_input("Diferenciales", 0, 10, 2)
        c2_4 = st.number_input("PIA 16A (Varios)", 0, 20, 4)
        coste = (c2_1*precios_base["Cuadro"] + c2_2*precios_base["IGA"] + c2_3*precios_base["DIF"] + c2_4*precios_base["PIA16"]) * f_total
        capitulos_finales.append(("II. CUADRO DE PROTECCIÓN", coste))

    # CAPÍTULO III
    with st.expander("CAPÍTULO III: CIRCUITO DE ILUMINACIÓN (C1)", expanded=False):
        c3_1 = st.number_input("Metros 1,5mm² (C1)", 0, 1000, 315)
        c3_2 = st.number_input("Interruptores", 0, 50, 4)
        c3_3 = st.number_input("Conmutadores", 0, 50, 10)
        coste = (c3_1*precios_base["1,5mm"] + c3_2*precios_base["INT"] + c3_3*precios_base["CONM"]) * f_total
        capitulos_finales.append(("III. CIRCUITO DE ILUMINACIÓN", coste))

    # CAPÍTULO IV - VIII (Simplificados para brevedad pero siguiendo tu lógica)
    with st.expander("CAPÍTULO IV: TOMAS DE USO GENERAL (C2)", expanded=False):
        c4_1 = st.number_input("Metros 2,5mm² (C2)", 0, 1000, 325)
        c4_2 = st.number_input("Bases 16A (C2)", 0, 100, 18)
        coste = (c4_1*precios_base["2,5mm"] + c4_2*precios_base["TC16A"]) * f_total
        capitulos_finales.append(("IV. CIRCUITO TOMAS USO GENERAL", coste))

    with st.expander("CAPÍTULO V, VI, VII: COCINA, LAVADORA, BAÑOS", expanded=False):
        c5_1 = st.number_input("Metros 6mm² (C3)", 0, 500, 30)
        c5_2 = st.number_input("Bases 25A (C3)", 0, 10, 2)
        c5_3 = st.number_input("Metros 4mm² (C4)", 0, 500, 85)
        coste = (c5_1*precios_base["6mm"] + c5_2*precios_base["TC25A"] + c5_3*precios_base["4mm"]) * f_total
        capitulos_finales.append(("V-VII. CIRCUITOS DE POTENCIA", coste))

    with st.expander("CAPÍTULO VIII: TELECOMUNICACIONES Y TIMBRE", expanded=False):
        c8_1 = st.number_input("Pulsadores", 0, 10, 1)
        c8_2 = st.number_input("Zumbador", 0, 5, 1)
        coste = (c8_1*precios_base["PULS"] + c8_2*precios_base["ZUMB"]) * f_total
        capitulos_finales.append(("VIII. TELECOM. Y TIMBRE", coste))

    # --- RESUMEN FINAL ---
    st.divider()
    st.subheader("📊 RESUMEN FINAL DEL PRESUPUESTO")
    total_bi = 0
    for cap, imp in capitulos_finales:
        c_n, c_v = st.columns([3, 1])
        c_n.write(cap)
        c_v.markdown(f'<div class="resultado-negro">{imp:,.2f} €</div>', unsafe_allow_html=True)
        total_bi += imp
    
    total_iva = total_bi * (p_iva / 100)
    st.markdown(f'<div class="total-final">TOTAL (BI + IVA): {(total_bi + total_iva):,.2f} €</div>', unsafe_allow_html=True)
