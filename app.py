import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Ingeniería Pro - Presupuesto Maestro DTIE", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .footer-container {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        display: flex; align-items: center; justify-content: center; gap: 15px;
        z-index: 9999; pointer-events: none; text-align: center; width: 100%; font-family: sans-serif;
    }
    .logo-yt-footer {
        font-family: 'Arial Black', sans-serif; font-size: 22px; color: #22d3ee; 
        border: 2px solid rgba(34, 211, 238, 0.6); padding: 2px 8px; border-radius: 5px;
        font-weight: bold; background-color: rgba(0, 0, 0, 0.2);
    }
    .watermark-text { font-size: 16px; color: rgba(255, 255, 255, 0.6); font-weight: bold; }
    p, label, .stMarkdown, div, span, button, .stSelectbox, .stNumberInput { font-weight: bold !important; }
    .resultado-negro {
        color: #000000 !important; font-weight: 900 !important; font-size: 18px;
        background-color: #f0f2f6; padding: 8px; border-radius: 5px;
        border-left: 5px solid #2e3b4e; margin-bottom: 2px; text-align: right;
    }
    .total-final {
        color: #ffffff !important; font-weight: 900 !important; font-size: 32px;
        background-color: #1e1e1e; padding: 20px; border-radius: 12px; text-align: center;
        border: 2px solid #ffd700; margin-top: 20px;
    }
    .stExpander { border: 1px solid #d1d1d1 !important; border-radius: 10px !important; margin-bottom: 10px !important; }
    </style>
    <div class="footer-container">
        <span class="logo-yt-footer">Y.T</span>
        <span class="watermark-text">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. LÓGICA REBT: INTENSIDADES ADMISIBLES (ITC-BT-19) ---
# Diccionario simplificado de intensidades admisibles para Cobre (2 conductores cargados para Monofásica)
# Estructura: {Metodo: {Aislamiento: [lista_intensidades_para_secciones_estandar]}}
# Secciones: [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95]
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95]

tablas_adm = {
    "A1": {"PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182], "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233]},
    "B1": {"PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232], "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292]},
    "C":  {"PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258], "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328]},
    "E":  {"PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286], "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352]}
}

def calcular_seccion_rebt(metodo, aislamiento, intensidad_b):
    # Seleccionar tabla según método (agrupamos similares para sencillez)
    m = metodo.split(" ")[0]
    m_key = "A1" if m in ["A1", "A2"] else ("B1" if m in ["B1", "B2"] else (m if m in tablas_adm else "C"))
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    
    intensidades = tablas_adm.get(m_key, tablas_adm["C"])[ais_key]
    
    for i, i_adm in enumerate(intensidades):
        if i_adm >= intensidad_b:
            return secciones_ref[i]
    return 120 # Valor de seguridad

# --- 3. BASE DE PRECIOS ---
db_precios = {
    "CABLES": {"1.5mm": 0.25, "2.5mm": 0.38, "4mm": 0.64, "6mm": 1.30, "10mm": 2.10},
    "PROTECCIONES": {"Cuadro 36 mod": 53.92, "IGA Combi": 56.20, "PIA 10A": 3.60, "PIA 16A": 9.31, "PIA 25A": 3.64},
    "MANO OBRA": {"Oficial 1ª": 33.00, "Ayudante": 29.00}
}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Parámetros de Venta")
    modo = st.radio("Sección:", ["📐 Calculadora Técnica", "💰 Presupuesto Detallado"])
    if modo == "💰 Presupuesto Detallado":
        p_ben = st.number_input("% Beneficio Industrial", 0, 100, 15)
        p_amo = st.number_input("% Gastos Generales", 0, 100, 5)
        p_iva = st.selectbox("Tipo de IVA (%)", [21, 10, 4, 0], index=0)
        f_total = 1 + (p_ben/100) + (p_amo/100)
    else:
        f_total = 1.0

# --- 5. CALCULADORA TÉCNICA (INTEGRACIÓN REBT) ---
if modo == "📐 Calculadora Técnica":
    st.title("📐 Cálculo de Secciones s/ REBT")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Parámetros Eléctricos")
        red = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia Instalar (W)", value=5750)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de Potencia", 0.70, 1.00, 0.90)
        k_rec = st.selectbox("Uso", ["General (1.0)", "Motores (1.25)", "Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        k = 1.25 if ("Motores" in k_rec or "Vehículo" in k_rec) else (1.8 if "Descarga" in k_rec else 1.0)
    
    with col2:
        st.subheader("Entorno e Instalación")
        mat = st.radio("Conductor", ["Cobre", "Aluminio"], horizontal=True)
        ais = st.radio("Aislamiento", ["PVC (70°)", "XLPE (90°)"], horizontal=True)
        metodos_rebt = [
            "A1 - Conductores en tubo (pared aislante)", "B1 - Conductores en tubo (superficie)",
            "C - Cable directo sobre pared", "E - Cable al aire libre (bandeja perforada)",
            "D1 - Cable enterrado en conducto"
        ]
        met = st.selectbox("Método de Instalación", metodos_rebt)
        caida = st.number_input("CdT Máx (%)", value=3.0)

    # Cálculos
    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (1.732 * V * cos_phi)
    
    # 1. Sección por Intensidad Admisible (REBT)
    S_adm = calcular_seccion_rebt(met, ais, Ib)
    
    # 2. Sección por Caída de Tensión
    gamma = (48 if "PVC" in ais else 44) if mat == "Cobre" else (30 if "PVC" in ais else 28)
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * (caida/100*V))
    
    # 3. Elección final
    S_final = max(S_adm, next((s for s in secciones_ref if s >= S_cdt), 95))

    st.divider()
    c_r1, c_r2, c_r3 = st.columns(3)
    c_r1.metric("Intensidad (Ib)", f"{Ib:.2f} A")
    c_r2.metric("Mín. por Térmico", f"{S_adm} mm²")
    c_r3.subheader(f"✅ SECCIÓN FINAL: {S_final} mm²")
    st.info(f"Cálculo realizado aplicando **ITC-BT-19** para el método **{met[:2]}**.")

# --- 6. PRESUPUESTO (SE MANTIENE IGUAL) ---
else:
    st.title("💰 Presupuesto Técnico Detallado")
    # ... [Aquí sigue el resto de tu código de capítulos]
    capitulos_data = []
    # (El resto del código de los capítulos se integra aquí igual que en tu versión anterior)
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", expanded=False):
        c1, c2 = st.columns(2)
        m_6 = c1.number_input("Metros Cable 6mm²", value=48.0)
        p_6 = c2.number_input("Precio/m 6mm²", value=1.30)
        h_of = c1.number_input("Horas Oficial 1ª", value=2.0)
        p_of = c2.number_input("Precio/h Oficial", value=db_precios["MANO OBRA"]["Oficial 1ª"])
        sub = (m_6*p_6 + h_of*p_of) * f_total
        capitulos_data.append(("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", sub))
    
    # [Resumen final simplificado]
    st.divider()
    total_neto = sum([c[1] for c in capitulos_data])
    for n, i in capitulos_data:
        st.write(f"**{n}**: {i:,.2f} €")
    st.markdown(f'<div class="total-final">TOTAL: {total_neto * (1 + p_iva/100):,.2f} €</div>', unsafe_allow_html=True)
