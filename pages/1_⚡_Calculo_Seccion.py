import streamlit as st
import math

st.set_page_config(page_title="Cálculo de Sección", page_icon="⚡", layout="wide")

st.title("⚡ Módulo 1: Cálculo de Sección de Conductores")
st.markdown("Cálculo técnico de conductores por caída de tensión e intensidad admisible.")

# --- ENTRADA DE DATOS ---
with st.sidebar:
    st.header("⚙️ Parámetros de la Instalación")
    
    sistema = st.selectbox("Sistema Eléctrico", ["Trifásico", "Monofásico"])
    tension = st.number_input("Tensión Nominal (V)", value=400 if sistema == "Trifásico" else 230, step=10)
    
    tipo_carga = st.radio("Tipo de Carga", ["Potencia Activa (W)", "Potencia Aparente (VA)"])
    valor_carga = st.number_input(f"Valor de la {tipo_carga}", value=15000 if sistema == "Trifásico" else 3500, step=500)
    
    cos_phi = st.number_input("Factor de Potencia (cos φ)", value=0.85, min_value=0.1, max_value=1.0, step=0.05)
    longitud = st.number_input("Longitud de la línea (m)", value=50.0, min_value=1.0, step=5.0)
    
    material = st.selectbox("Material del Conductor", ["Cobre (Cu)", "Aluminio (Al)"])
    aislamiento = st.selectbox("Tipo de Aislamiento (Temp. Máx)", ["XLPE / EPR (90°C)", "PVC (70°C)"])
    
    cdt_max = st.slider("Caída de Tensión Máxima Permitida (%)", min_value=0.5, max_value=7.0, value=3.0, step=0.5)

# --- LÓGICA DE CÁLCULO ---

# 1. Conversión de potencias y cálculo de Intensidad (I)
if tipo_carga == "Potencia Activa (W)":
    p_activa = valor_carga
    p_aparente = p_activa / cos_phi
else:
    p_aparente = valor_carga
    p_activa = p_aparente * cos_phi

if sistema == "Trifásico":
    intensidad = p_aparente / (math.sqrt(3) * tension)
else:
    intensidad = p_aparente / tension

# 2. Conductividad (𝛾) según material y temperatura estimada de servicio
# Valores corregidos para temperatura de diseño (aproximación comercial estándar)
if material == "Cobre (Cu)":
    conductividad = 48.5 if "XLPE" in aislamiento else 44.0
else: # Aluminio
    conductividad = 30.0 if "XLPE" in aislamiento else 27.2

# 3. Cálculo de Sección por Caída de Tensión (S_cdt)
# Monofásico: S = (2 * L * P) / (𝛾 * e * V)
# Trifásico: S = (L * P) / (𝛾 * e * V)
cdt_voltios = (cdt_max / 100.0) * tension

if sistema == "Monofásico":
    seccion_cdt = (2 * longitud * p_activa) / (conductividad * cdt_voltios * tension)
else:
    seccion_cdt = (longitud * p_activa) / (conductividad * cdt_voltios * tension)

# 4. Sección comercial normalizada superior
secciones_comerciales = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
seccion_teorica = max(seccion_cdt, 1.5) # Mínimo técnico por norma general

seccion_elegida_cdt = secciones_comerciales[-1]
for s in secciones_comerciales:
    if s >= seccion_teorica:
        seccion_elegida_cdt = s
        break

# --- INTERFAZ DE RESULTADOS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Intensidad de Diseño ($I_d$)", value=f"{intensidad:.2f} A")
with col2:
    st.metric(label="Sección Mínima (Por CdT)", value=f"{seccion_cdt:.2f} mm²")
with col3:
    st.metric(label="Sección Comercial Sugerida", value=f"{seccion_elegida_cdt} mm²")

st.write("---")

# --- GUARDAR DATOS EN SESSION STATE (Para usar en Mediciones/Presupuesto) ---
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

st.subheader("💾 Almacenamiento en el Proyecto")
nombre_linea = st.text_input("Nombre o ID de la línea (ej. Subcuadro General, Motor 1)", value="Línea Principal")

if st.button("Guardar línea en memoria temporal"):
    st.session_state['proyecto'][nombre_linea] = {
        "sistema": sistema,
        "tension": tension,
        "intensidad": round(intensidad, 2),
        "seccion": seccion_elegida_cdt,
        "longitud": longitud,
        "material": material
    }
    st.success(f"✔️ ¡Línea '{nombre_linea}' guardada con éxito!")

# Mostrar tabla de líneas guardadas actualmente
if st.session_state['proyecto']:
    st.write("### 📋 Líneas actualmente registradas:")
    st.json(st.session_state['proyecto'])
