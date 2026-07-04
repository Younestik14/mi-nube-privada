import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Módulo Fotovoltaica REBT", page_icon="☀️", layout="wide")

st.title("☀️ Módulo 2: Dimensionamiento Fotovoltaico según Normativa Española")
st.markdown("Cálculo y clasificación según el **RD 244/2019** y el **REBT**, con gestión de sombreados y optimización de strings.")

# --- CONFIGURACIÓN E INTRODUCCIÓN DE DATOS EN LA PÁGINA PRINCIPAL ---
st.header("⚙️ Configuración del Proyecto Solar")

# Clasificación según RD 244/2019 en España
MODALIDADES_AUTOCONSUMO = [
    "Autoconsumo SIN excedentes (Requiere sistema antivertido - ITC-BT-40)",
    "Autoconsumo CON excedentes ACOGIDO a compensación simplificada",
    "Autoconsumo CON excedentes NO acogido a compensación",
    "Instalación Aislada de la Red (No aplica RD 244/2019)"
]

col_config1, col_config2 = st.columns(2)

with col_config1:
    modalidad = st.selectbox("Modalidad de la Instalación (RD 244/2019 / REBT)", MODALIDADES_AUTOCONSUMO)
    
    if "Aislada" in modalidad:
        consumo_diario = st.number_input("Consumo Diario Estimado (Wh/día)", value=4000, step=500)
        hsp = st.number_input("HSP del mes más desfavorable (Invierno)", value=3.2, min_value=1.0, step=0.1)
        dias_autonomia = st.slider("Días de Autonomía Requeridos", min_value=1, max_value=5, value=2)
        v_bateria = st.selectbox("Tensión del Banco de Baterías (V)", [12, 24, 48], index=2)
    else:
        consumo_anual = st.number_input("Consumo Anual de la Vivienda/Industria (Commercial/Residencial) (kWh/año)", value=5500, step=500)
        hsp = st.number_input("Horas de Sol Pico (HSP) medias anuales de la zona", value=4.7, min_value=1.0, step=0.1)

with col_config2:
    st.markdown("**⚡ Factores de Rendimiento y Afección de Sombras**")
    sombreado = st.radio(
        "Presencia de Sombras (Árboles, chimeneas, edificios colindantes):",
        ["Sin sombras (Condición óptima)", "Sombras parciales / temporales (Pérdidas moderadas)", "Sombras severas"]
    )
    
    # Solución técnica ante sombras
    solucion_sombras = "Inversor Central Estándar"
    if sombreado != "Sin sombras (Condición óptima)":
        solucion_sombras = st.selectbox(
            "🛠️ Elemento técnico corrector para mitigar sombras:",
            [
                "Mantener Inversor de String estándar (Mayor pérdida por efecto 'cuello de botella')",
                "Instalar Optimizadores de Potencia (Uno por panel - Maximiza MPPT individual)",
                "Instalar Microinversores (Un inversor por panel - Independencia total)"
            ]
        )

# Penalización del rendimiento por sombras y corrección por tecnología
f_perdidas_base = 0.15 if not "Aislada" in modalidad else 0.25

if sombreado == "Sombras parciales / temporales (Pérdidas moderadas)":
    if "Optimizadores" in solucion_sombras:
        f_perdidas = f_perdidas_base + 0.03 # Mitigado casi por completo
    elif "Microinversores" in solucion_sombras:
        f_perdidas = f_perdidas_base + 0.02 # Rendimiento óptimo individual
    else:
        f_perdidas = f_perdidas_base + 0.15 # Penalización fuerte en string
elif sombreado == "Sombras severas":
    if "Optimizadores" in solucion_sombras:
        f_perdidas = f_perdidas_base + 0.08
    elif "Microinversores" in solucion_sombras:
        f_perdidas = f_perdidas_base + 0.05
    else:
        f_perdidas = f_perdidas_base + 0.35 # El string cae por completo
else:
    f_perdidas = f_perdidas_base

st.write("---")
st.header("🔌 Características de los Componentes")

col_comp1, col_comp2 = st.columns(2)
with col_comp1:
    p_panel = st.number_input("Potencia del Panel Solar Seleccionado (Wp)", value=450, step=10)
    vmp_panel = st.number_input("Tensión a máxima potencia Vmp (V)", value=41.5, step=0.5)
with col_comp2:
    if "Microinversores" not in solucion_sombras:
        v_max_mppt = st.number_input("Tensión Máxima del Inversor Central / MPPT (V)", value=800, step=50)
        v_min_mppt = st.number_input("Tensión Mínima del Inversor Central / MPPT (V)", value=200, step=50)
    else:
        st.info("ℹ️ Al usar Microinversores, cada panel se conecta directamente a su propio microinversor de baja tensión. No aplica el cálculo de strings de alta tensión.")

# --- LÓGICA DE CÁLCULO FOTOVOLTAICO ---
if not "Aislada" in modalidad:
    # Autoconsumo (Red)
    p_pico_req_w = consumo_anual / (hsp * 365 * (1 - f_perdidas)) * 1000
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_kwp = (num_paneles * p_panel) / 1000
    cap_nominal_ah = 0
else:
    # Aislada
    p_pico_req_w = consumo_diario / (hsp * (1 - f_perdidas))
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_kwp = (num_paneles * p_panel) / 1000
    
    dod = 0.6 # Profundidad de descarga
    cap_util_wh = consumo_diario * dias_autonomia
    cap_nominal_ah = cap_util_wh / (v_bateria * dod)

# --- PANEL DE RESULTADOS ---
st.write("---")
st.header("📊 Dictamen y Resultados del Dimensionamiento")

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric(label="Potencia Mínima Recomendada", value=f"{p_pico_req_w/1000:.2f} kWp")
    st.caption(f"Pérdidas totales del sistema estimadas: **{f_perdidas*100:.1f}%**")
with col_res2:
    st.metric(label="Número de Módulos Necesarios", value=f"{num_paneles} uds")
with col_res3:
    st.metric(label="Potencia de Campos FV Real Instalada", value=f"{potencia_total_kwp:.2f} kWp")

# --- RECOMENDACIÓN TÉCNICA Y NORMATIVA ---
st.write("---")
col_det1, col_det2 = st.columns(2)

with col_det1:
    st.subheader("📐 Arquitectura del Sistema")
    st.write(f"* **Elemento de Inversión principal:** {solucion_sombras}")
    
    if "Microinversores" in solucion_sombras:
        st.write(f"* **Configuración:** Se instalarán **{num_paneles} microinversores** acoplados individualmente a la parte trasera de cada panel.")
        st.write("* **Ventaja:** Si un panel recibe sombra, el resto sigue rindiendo al 100%. La salida del campo ya es en Corriente Alterna (CA).")
    elif "Optimizadores" in solucion_sombras:
        st.write(f"* **Configuración:** **{num_paneles} optimizadores** de corriente continua + 1 Inversor Centralizado.")
        st.write("* **Ventaja:** Evita el cuello de botella en el string regulando la tensión de cada panel de forma independiente.")
    else:
        st.write("* **Configuración:** Conexión en Serie (String convencional).")
        if "Microinversores" not in solucion_sombras:
            paneles_max_serie = math.floor(v_max_mppt / 49.5) # Asumiendo Voc ~49.5V
            st.write(f"* **Límite técnico por MPPT:** Máximo **{paneles_max_serie}** paneles en serie para no quemar el inversor.")

with col_det2:
    st.subheader("⚖️ Consideraciones Legales REBT")
    if "SIN excedentes" in modalidad:
        st.write("* **REBT (ITC-BT-40):** Obligatorio instalar un **mecanismo antivertido** homologado según la norma UNE 217001.")
        st.write("* **Tramitación:** Tramitación rápida mediante comunicación a la comunidad autónoma (sin necesidad de solicitar punto de conexión a la distribuidora).")
    elif "CON excedentes" in modalidad:
        st.write("* **RD 244/2019:** Si la potencia es $\le$ 15 kW, estás exento de solicitar permisos de acceso y conexión para generación a la distribuidora.")
        st.write("* **Compensación:** La comercializadora compensará tus excedentes mensualmente a precio de pool o pactado (el saldo nunca será negativo).")
    elif "Aislada" in modalidad:
        st.write(f"* **Capacidad del acumulador:** Requiere un banco de baterías de **{cap_nominal_ah:.1f} Ah** a **{v_bateria} V**.")
        st.write("* **Nota:** Queda fuera del alcance de los peajes y trámites administrativos de inyección a red.")

# --- GUARDAR EN SESSION STATE ---
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

st.write("---")
st.subheader("💾 Guardar en el Proyecto Global")
nombre_fv = st.text_input("Identificador del Sistema Solar", value="Autoconsumo Solar FV")

if st.button("Guardar instalación solar"):
    st.session_state['proyecto'][nombre_fv] = {
        "tipo": modalidad.split(" (")[0],
        "potencia_kwp": round(potencia_total_kwp, 2),
        "num_paneles": num_paneles,
        "elemento_maniobra": solucion_sombras,
        "batería_ah": round(cap_nominal_ah, 2) if "Aislada" in modalidad else "N/A"
    }
    st.success(f"✔️ ¡Instalación solar '{nombre_fv}' guardada con éxito!")
