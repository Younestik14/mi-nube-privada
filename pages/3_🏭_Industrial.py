import streamlit as st
import math

st.set_page_config(page_title="Módulo Industrial", page_icon="🏭", layout="wide")

st.title("🏭 Módulo 3: Cálculos de Receptores Industriales")
st.markdown("Gestión de motores eléctricos, arranque industrial y compensación de energía reactiva.")

# --- ENTRADA DE DATOS (Panel Lateral) ---
with st.sidebar:
    st.header("⚙️ Datos del Motor / Carga")
    
    p_motor_kw = st.number_input("Potencia Mecánica del Motor (kW)", value=11.0, step=1.0)
    tension_ind = st.selectbox("Tensión de alimentación (V)", [400, 230, 690], index=0)
    
    rendimiento = st.slider("Rendimiento del motor (η %)", min_value=50, max_value=99, value=88) / 100.0
    cos_phi_actual = st.number_input("Factor de Potencia actual (cos φ)", value=0.75, min_value=0.2, max_value=1.0, step=0.05)
    
    st.subheader("⚡ Compensación de Reactiva")
    corregir_pf = st.checkbox("¿Calcular batería de condensadores?", value=True)
    cos_phi_objetivo = st.number_input("Cos φ Objetivo", value=0.95, min_value=0.8, max_value=1.0, step=0.01)

    st.subheader("🚀 Método de Arranque")
    tipo_arranque = st.selectbox(
        "Tipo de Arranque", 
        ["Directo", "Estrella - Triángulo (Y-Δ)", "Arrancador Suave (Soft Starter)", "Variador de Frecuencia (VFD)"]
    )

# --- LÓGICA DE CÁLCULO ---

# 1. Potencia eléctrica absorbida de la red
p_electrica_w = (p_motor_kw * 1000) / rendimiento

# 2. Intensidad Nominal (Trifásico por defecto en industria)
i_nominal = p_electrica_w / (math.sqrt(3) * tension_ind * cos_phi_actual)

# 3. Estimación de Intensidad de Arranque (I_arr) y Protección técnica recomendada
# Factores multiplicadores típicos según ITC-BT-47 / REBT
if tipo_arranque == "Directo":
    f_arr = 6.0
    f_prot = 1.35
elif tipo_arranque == "Estrella - Triángulo (Y-Δ)":
    f_arr = 2.0
    f_prot = 1.0
elif tipo_arranque == "Arrancador Suave (Soft Starter)":
    f_arr = 3.0
    f_prot = 1.15
else: # Variador de frecuencia (Mantiene la corriente controlada)
    f_arr = 1.1
    f_prot = 1.05

i_arranque = i_nominal * f_arr
calibre_proteccion = i_nominal * f_prot

# 4. Cálculo de la Batería de Condensadores (Q_c)
if corregir_pf and cos_phi_actual < cos_phi_objetivo:
    # Fórmulas de potencia: Q = P * (tan(phi_actual) - tan(phi_objetivo))
    phi_actual = math.acos(cos_phi_actual)
    phi_objetivo = math.acos(cos_phi_objetivo)
    
    q_condensador = (p_electrica_w / 1000) * (math.tan(phi_actual) - math.tan(phi_objetivo))
else:
    q_condensador = 0.0

# --- PANEL DE RESULTADOS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Intensidad Nominal ($I_n$)", value=f"{i_nominal:.2f} A")
with col2:
    st.metric(label="Corriente de Arranque Estimada ($I_arr$)", value=f"{i_arranque:.2f} A")
with col3:
    st.metric(label="Potencia de Condensador Req.", value=f"{q_condensador:.2f} kVAr" if q_condensador > 0 else "N/A")

st.write("---")

# --- RECOMENDACIÓN TÉCNICA ---
col_inf1, col_inf2 = st.columns(2)

with col_inf1:
    st.subheader("🛡️ Selección de Protecciones y Maniobra")
    st.write(f"* **Magnetotérmico recomendado (Curva D/K para motores):** Calibre mínimo de **{calibre_proteccion:.2f} A**.")
    st.write(f"* **Contactor principal:** Dimensionar para categoría **AC-3** a {i_nominal:.2f} A.")
    st.write(f"* **Sección de alimentación:** Recuerda que según REBT (ITC-BT-47), los motores de automoción/industria se calculan con un **125%** de la $I_n$ de la carga.")

with col_inf2:
    st.subheader("📊 Análisis Energético")
    st.write(f"* **Potencia Eléctrica Absorbida:** {p_electrica_w/1000:.2f} kW")
    if q_condensador > 0:
        st.write(f"* **Beneficio:** Reducción de la corriente de línea tras el punto de conexión del condensador.")
        i_corregida = p_electrica_w / (math.sqrt(3) * tension_ind * cos_phi_objetivo)
        st.write(f"* **Nueva Intensidad de línea calculada:** **{i_corregida:.2f} A** (Ahorro de corriente del {((i_nominal - i_corregida)/i_nominal)*100:.1f}%)")
    else:
        st.write("* El Factor de Potencia actual ya cumple o es superior al objetivo seleccionado.")

# --- GUARDAR EN SESSION STATE ---
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

st.write("---")
st.subheader("💾 Guardar Receptor en el Proyecto")
nombre_motor = st.text_input("Nombre de la Carga Industrial", value="Motor Cinta Transportadora")

if st.button("Guardar carga industrial"):
    st.session_state['proyecto'][nombre_motor] = {
        "tipo": f"Motor ({tipo_arranque})",
        "potencia_kw": p_motor_kw,
        "intensidad": round(i_nominal, 2),
        "kvar_bateria": round(q_condensador, 2)
    }
    st.success(f"✔️ ¡Carga '{nombre_motor}' indexada correctamente!")

if st.session_state['proyecto']:
    st.write("### 📋 Base de Datos actual del proyecto:")
    st.json(st.session_state['proyecto'])
