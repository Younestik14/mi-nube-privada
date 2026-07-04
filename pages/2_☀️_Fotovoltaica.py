import streamlit as st
import math

st.set_page_config(page_title="Módulo Fotovoltaica", page_icon="☀️", layout="wide")

st.title("☀️ Módulo 2: Dimensionamiento Fotovoltaico")
st.markdown("Cálculo de potencia pico, número de módulos, configuración de strings e inversores/baterías.")

# --- ENTRADA DE DATOS (Panel Lateral) ---
with st.sidebar:
    st.header("⚙️ Parámetros de Diseño")
    
    tipo_instalacion = st.radio("Tipo de Instalación", ["Conectada a Red (Autoconsumo)", "Aislada con Baterías"])
    
    st.subheader("📊 Datos de Consumo y Radiación")
    if tipo_instalacion == "Conectada a Red (Autoconsumo)":
        consumo_anual = st.number_input("Consumo Anual Estimado (kWh/año)", value=5000, step=500)
        hsp = st.number_input("Horas de Sol Pico (HSP) medias anuales", value=4.8, min_value=1.0, max_value=7.0, step=0.1)
        F_perdidas = st.slider("Factor de Pérdidas del Sistema (%)", min_value=10, max_value=30, value=15) / 100.0
    else:
        consumo_diario = st.number_input("Consumo Diario Estimado (Wh/día)", value=3000, step=250)
        hsp_peor = st.number_input("HSP del mes más desfavorable (invierno)", value=3.2, min_value=1.0, max_value=7.0, step=0.1)
        dias_autonomia = st.slider("Días de Autonomía (Baterías)", min_value=1, max_value=5, value=2)
        v_bateria = st.selectbox("Tensión del Banco de Baterías (V)", [12, 24, 48], index=2)
        F_perdidas = 0.25 # Mayor margen de pérdidas en aislada (baterías/inversor)

    st.subheader("🔌 Especificaciones del Panel Solar")
    p_panel = st.number_input("Potencia Máxima del Panel ($P_{max}$ en Wp)", value=450, step=10)
    vmp_panel = st.number_input("Tensión a Máxima Potencia ($V_{mp}$ en V)", value=41.5, step=0.5)
    voc_panel = st.number_input("Tensión en Circuito Abierto ($V_{oc}$ en V)", value=49.5, step=0.5)

    if tipo_instalacion == "Conectada a Red (Autoconsumo)":
        st.subheader("⚡ Parámetros del Inversor")
        v_max_mppt = st.number_input("Tensión Máxima del MPPT (V)", value=800, step=50)
        v_min_mppt = st.number_input("Tensión Mínima del MPPT (V)", value=200, step=50)

# --- LÓGICA DE CÁLCULO ---

if tipo_instalacion == "Conectada a Red (Autoconsumo)":
    # Potencia pico teórica para cubrir el consumo teórico anualizado
    # E_anual = P_pico * HSP * 365 * (1 - PR)
    p_pico_req = consumo_anual / (hsp * 365 * (1 - F_perdidas)) # en kWp
    p_pico_req_w = p_pico_req * 1000 # en Wp
    
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_instalada = (num_paneles * p_panel) / 1000 # kWp
    
    # Configuración de Strings recomendada para el MPPT (Simple aproximación por tensión)
    paneles_max_serie = math.floor(v_max_mppt / voc_panel)
    paneles_min_serie = math.ceil(v_min_mppt / vmp_panel)
    
else:
    # Instalación Aislada
    # E_diaria = P_pico * HSP * (1 - Pérdidas) -> P_pico = E_diaria / (HSP * (1 - Pérdidas))
    p_pico_req_w = consumo_diario / (hsp_peor * (1 - F_perdidas))
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_instalada = (num_paneles * p_panel) / 1000 # kWp
    
    # Cálculo de Baterías (con descarga máxima recomendada del 60% para estacionarias/litio)
    dod = 0.6
    cap_util_wh = consumo_diario * dias_autonomia
    cap_nominal_ah = cap_util_wh / (v_bateria * dod)

# --- PANEL DE RESULTADOS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Potencia Pico Sugerida", value=f"{p_pico_req_w/1000:.2f} kWp")
with col2:
    st.metric(label="Número de Paneles Requeridos", value=f"{num_paneles} uds")
with col3:
    st.metric(label="Potencia Real del Campo FV", value=f"{potencia_total_instalada:.2f} kWp")

st.write("---")

# --- DETALLES DE CONFIGURACIÓN ---
col_det1, col_det2 = st.columns(2)

with col_det1:
    st.subheader("📐 Configuración del Campo de Captación")
    st.write(f"* **Módulos totales:** {num_paneles} de {p_panel} Wp.")
    if tipo_instalacion == "Conectada a Red (Autoconsumo)":
        st.write(f"* **Límites de paneles en serie por MPPT:** Mínimo **{paneles_min_serie}** / Máximo **{paneles_max_serie}** paneles.")
        st.write(f"* **Tensión del campo (Voc total en frío estimado):** {num_paneles * voc_panel:.1f} V.")
    else:
        # Recomendación simple para aislada de acoplamiento por tensión de batería
        paneles_serie = int(v_bateria / 12) # Regla de dedo para paneles de "12V" o MPPT adaptativo
        st.write(f"* **Configuración recomendada:** Acoplar mediante regulador MPPT.")

with col_det2:
    if tipo_instalacion == "Aislada con Baterías":
        st.subheader("🔋 Sistema de Acumulación (Baterías)")
        st.write(f"* **Capacidad Mínima Necesaria:** {cap_nominal_ah:.2f} Ah a {v_bateria} V.")
        st.write(f"* **Energía almacenable total:** {(cap_nominal_ah * v_bateria)/1000:.2f} kWh.")
        st.info("Nota: Cálculo basado en una profundidad de descarga (DoD) del 60%.")
    else:
        st.subheader("📈 Estimación de Producción Mensual Eficiente")
        rendimiento_estimado_diario = potencia_total_instalada * hsp * (1 - F_perdidas)
        st.write(f"* **Generación diaria media:** {rendimiento_estimado_diario:.2f} kWh/día.")
        st.write(f"* **Generación anual estimada:** {rendimiento_estimado_diario * 365:.1f} kWh/año.")

# --- GUARDAR EN SESSION STATE ---
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

st.write("---")
st.subheader("💾 Guardar Datos en el Proyecto")
nombre_fv = st.text_input("Etiqueta de la instalación FV", value="Generación Solar Principal")

if st.button("Guardar instalación solar"):
    st.session_state['proyecto'][nombre_fv] = {
        "tipo": tipo_instalacion,
        "potencia_kwp": round(potencia_total_instalada, 2),
        "num_paneles": num_paneles,
        "batería_ah": round(cap_nominal_ah, 2) if tipo_instalacion == "Aislada con Baterías" else "N/A"
    }
    st.success(f"✔️ ¡Instalación '{nombre_fv}' guardada!")

if st.session_state['proyecto']:
    st.write("### 📋 Resumen del proyecto actual:")
    st.json(st.session_state['proyecto'])
