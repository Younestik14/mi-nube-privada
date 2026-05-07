import streamlit as st
import math
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="REBT Pro Calculator", page_icon="⚡", layout="wide")

# Estilo personalizado para mejorar la interfaz
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS TÉCNICA ---
secciones = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Intensidades Admisibles (Cobre, PVC/XLPE, Mono/Tri) - Basado en Método B1/C
tablas_iz = {
    "PVC_Mono": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321],
    "XLPE_Mono": [18.5, 25, 33, 43, 59, 79, 104, 129, 155, 196, 238, 276, 316, 360, 424],
    "PVC_Tri": [13, 17.5, 23, 30, 40, 54, 70, 86, 103, 131, 159, 183, 210, 239, 281],
    "XLPE_Tri": [17, 23, 30, 40, 54, 72, 94, 117, 141, 179, 216, 250, 287, 327, 385]
}

# --- INTERFAZ PRINCIPAL ---
st.title("⚡ Calculadora Eléctrica Profesional REBT")
st.caption("Cálculo de secciones según Reglamento Electrotécnico de Baja Tensión (España)")

# --- SIDEBAR: ENTRADA DE DATOS ---
with st.sidebar:
    st.header("🔌 Datos de la Carga")
    tipo_red = st.selectbox("Tipo de Suministro", ["Monofásico 230V", "Trifásico 400V"])
    potencia = st.number_input("Potencia Activa (W)", value=3300, step=100)
    cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85, help="Típico 0.85 en motores, 1.0 en resistencias")
    longitud = st.number_input("Longitud de la línea (m)", value=20, min_value=1)
    
    st.header("🏗️ Condiciones de Instalación")
    material = st.radio("Material del Conductor", ["Cobre", "Aluminio"], horizontal=True)
    aislamiento = st.radio("Tipo de Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
    
    # Factores de corrección reales
    temp_amb = st.slider("Temperatura Ambiente (°C)", 10, 60, 40, help="Referencia estándar: 40°C al aire, 25°C enterrado")
    agrupamiento = st.number_input("Nº de circuitos en el mismo conducto", value=1, min_value=1)

# --- LÓGICA DE INGENIERÍA ---

# 1. Tensión e Intensidad de diseño (Ib)
V = 230 if "Monofásico" in tipo_red else 400
if V == 230:
    Ib = potencia / (V * cos_phi)
    key_tabla = "Mono"
else:
    Ib = potencia / (math.sqrt(3) * V * cos_phi)
    key_tabla = "Tri"

# 2. Conductividad (gamma) ajustada por temperatura
if material == "Cobre":
    gamma = 48 if "PVC" in aislamiento else 44
else:
    gamma = 30 if "PVC" in aislamiento else 28

# 3. Factores de Corrección (Simplificados según Norma)
# Factor temperatura (aprox)
f_temp = 1.0 if temp_amb <= 40 else (1 - (temp_amb - 40) * 0.05)
# Factor agrupamiento (según tabla ITC-BT-19)
f_agrup = {1: 1.0, 2: 0.8, 3: 0.7, 4: 0.65, 5: 0.6}.get(agrupamiento, 0.5)

f_total = max(0.1, f_temp * f_agrup)

# 4. Cálculo por Caída de Tensión (S_cdt)
# Suponemos 3% para receptores y 5% para otros casos (configurable)
e_max = 0.03 * V 
if V == 230:
    S_cdt = (2 * longitud * Ib * cos_phi) / (gamma * e_max)
else:
    S_cdt = (longitud * Ib * cos_phi) / (gamma * e_max)

# 5. Selección de Sección Comercial
col_iz = f"{'PVC' if 'PVC' in aislamiento else 'XLPE'}_{key_tabla}"
factor_mat = 1.0 if material == "Cobre" else 0.78 # Reducción para Aluminio en mismas tablas

seccion_final = None
iz_final = 0

for i, s in enumerate(secciones):
    iz_base = tablas_iz[col_iz][i] * factor_mat
    iz_corregida = iz_base * f_total
    
    # Debe cumplir Caída de Tensión Y Calentamiento (Iz corregida > Ib)
    if s >= S_cdt and iz_corregida >= Ib:
        seccion_final = s
        iz_final = iz_corregida
        break

# --- INTERFAZ DE RESULTADOS ---
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Intensidad de Diseño (Ib)", f"{Ib:.2f} A")
    st.caption("Corriente que circulará por el cable")

with c2:
    st.metric("Factor de Corrección Total", f"{f_total:.2f}")
    st.caption(f"Temp: {f_temp:.2f} | Agrup: {f_agrup:.2f}")

with c3:
    if seccion_final:
        st.metric("SECCIÓN NOMINAL", f"{seccion_final} mm²", delta_color="normal")
        st.caption(f"Capacidad real (Iz): {iz_final:.2f} A")
    else:
        st.error("❌ Sección no encontrada")

st.divider()

# --- COMPARATIVA Y ESCENARIOS ---
tab1, tab2 = st.tabs(["📊 Análisis Técnico", "📖 Guía REBT"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Desglose del Cálculo")
        st.write(f"- **Sección mínima por caída de tensión:** {S_cdt:.2f} mm²")
        st.write(f"- **Conductividad utilizada:** {gamma} m/(Ω·mm²)")
        st.write(f"- **Pérdida de potencia estimada:** {((Ib**2 * longitud) / (gamma * seccion_final if seccion_final else 1)):.2f} W")
    
    with col_b:
        st.subheader("Cumplimiento Criterio Térmico")
        if seccion_final:
            progreso = Ib / iz_final
            st.progress(min(progreso, 1.0))
            st.write(f"Carga sobre el cable: **{progreso*100:.1f}%**")

with tab2:
    st.info("""
    **Recordatorios de la ITC-BT-19:**
    * **Sección mínima en viviendas:** 1.5 mm² para iluminación, 2.5 mm² para fuerza, 6 mm² para cocina/horno.
    * **Tubos:** El diámetro del tubo debe permitir sacar y meter los cables fácilmente (sección libre del 60%).
    * **Caída de Tensión:** 
        * Viviendas: 3% total.
        * Instalaciones industriales: 3% receptores, 5% alumbrado.
    """)

# Botón de exportación (Simulado)
if st.button("Generar Informe Técnico (PDF)"):
    st.toast("Función en desarrollo... ¡Pero los cálculos son válidos!")
