import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN, LOGO Y ESTILOS ---
st.set_page_config(page_title="REBT Pro - Y.T", layout="wide", page_icon="⚡")

# Inyección de CSS para Personalización Total
st.markdown(
    """
    <style>
    /* Logo Y.T Estilizado en la esquina superior izquierda */
    .logo-yt {
        position: absolute;
        top: -50px;
        left: 0px;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        color: #22d3ee;
        border: 3px solid #22d3ee;
        padding: 5px 15px;
        border-radius: 8px;
        background-color: rgba(0,0,0,0.1);
        z-index: 100;
    }

    /* Marca de agua Blanca abajo al centro */
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-family: sans-serif;
        font-size: 15px;
        color: rgba(255, 255, 255, 0.6);
        z-index: 9999;
        pointer-events: none;
        font-weight: bold;
    }

    /* Forzar todas las fuentes a BOLD */
    html, body, [class*="st-"] {
        font-weight: bold !important;
    }

    /* Contenedor de Resultados (Fuente Negra y Bold) */
    .resultado-caja {
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 26px;
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 10px;
        border-left: 10px solid #22d3ee;
        margin-bottom: 15px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    
    <div class="logo-yt">Y.T</div>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. CREDENCIALES SUPABASE ---
# (Recuerda configurar estas variables en tu panel de Supabase)
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-key-anon"

try:
    if "tu-proyecto" not in SUPABASE_URL:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception:
    supabase = None

# --- 3. BASE DE DATOS REBT (UNE 20460-5-523) ---
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

TABLAS_IZ = {
    "PVC": {
        1.5: [13,13,15,15,18,18,20,22,24], 2.5: [18,17,21,20,25,24,28,30,33],
        4: [24,23,28,27,34,32,37,40,45], 6: [31,29,36,35,44,41,48,52,58],
        10: [42,40,50,48,60,55,66,71,80], 16: [56,53,66,64,80,73,88,96,107],
        25: [73,70,88,84,106,96,117,127,143], 35: [90,86,109,103,131,117,144,157,176],
        50: [108,103,131,124,159,141,175,190,214], 70: [136,130,167,158,204,179,222,242,273]
    },
    "XLPE": {
        1.5: [16,16,19,19,22,22,25,27,30], 2.5: [23,22,27,26,31,30,35,38,41],
        4: [30,29,36,35,42,40,47,51,56], 6: [39,37,46,45,54,51,61,66,73],
        10: [53,51,63,61,75,69,84,91,101], 16: [70,67,83,81,100,91,112,122,136],
        25: [93,89,111,106,133,120,149,161,181], 35: [114,109,137,131,164,147,184,199,224]
    }
}

# --- 4. INTERFAZ Y CÁLCULOS ---
st.title("⚡ Calculadora de Ingeniería REBT Pro")

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Parámetros de Carga")
        tipo_red = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia (W)", value=3300, step=100)
        L = st.number_input("Longitud de Línea (m)", value=25, min_value=1)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85)
        caida_perm = st.number_input("Caída de Tensión Máxima Permitida (%)", value=3.0, step=0.1)
        
        tipo_carga = st.selectbox("Tipo de Carga (Coeficiente REBT)", [
            "General (k=1.0)", 
            "Motores (k=1.25)", 
            "Luminarias Descarga/LED (k=1.8)"
        ])
        k = 1.25 if "Motores" in tipo_carga else (1.8 if "Descarga" in tipo_carga else 1.0)

    with col2:
        st.subheader("🏗️ Condiciones de Instalación")
        material = st.radio("Material Conductor", ["Cobre", "Aluminio"], horizontal=True)
        aislante = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        metodo = st.selectbox("Método de Instalación", ["A1", "A2", "B1", "B2", "C", "D", "E", "F", "G"], index=2)
        temp_amb = st.slider("Temperatura Ambiente (°C)", 10, 60, 40)
        agrup = st.number_input("Nº de Circuitos Agrupados", 1, 10, 1)

# Lógica Matemática
V = 230 if "Mono" in tipo_red else 400
Ib_base = P / (V * cos_phi) if V == 230 else P / (math.sqrt(3) * V * cos_phi)
Ib_diseno = Ib_base * k  # Aplicamos coeficiente de carga

# Coeficientes de corrección
t_max = 70 if aislante == "PVC" else 90
f_temp = math.sqrt((t_max - temp_amb) / (t_max - 40)) if temp_amb < t_max else 0.1
f_agrup = {1:1, 2:0.8, 3:0.7, 4:0.65, 5:0.6}.get(agrup, 0.5)
f_total = f_temp * f_agrup

# Caída de Tensión (Criterio Voltaje)
gamma = (48 if aislante == "PVC" else 44) if material == "Cobre" else (30 if aislante == "PVC" else 28)
e_voltios = (caida_perm / 100) * V
S_cdt = (2 if V == 230 else 1) * L * Ib_base * cos_phi / (gamma * e_voltios)

# Selección de Sección Comercial
seccion_final = None
iz_corregida = 0
tabla_ref = TABLAS_IZ[aislante]
f_mat = 1.0 if material == "Cobre" else 0.78

for s in SECCIONES:
    if s in tabla_ref:
        iz_base = tabla_ref[s][["A1","A2","B1","B2","C","D","E","F","G"].index(metodo)] * f_mat
        iz_adm = iz_base * f_total
        if s >= S_cdt and iz_adm >= Ib_diseno:
            seccion_final = s
            iz_corregida = iz_adm
            break

# --- 5. RESULTADOS (ESTILIZADOS EN NEGRO) ---
st.divider()
st.subheader("📊 Resultados Finales")

r1, r2, r3 = st.columns(3)

with r1:
    st.write("Intensidad de Diseño (Ib x k):")
    st.markdown(f'<div class="resultado-caja">{Ib_diseno:.2f} A</div>', unsafe_allow_html=True)

with r2:
    st.write("Sección por Voltaje (Mín):")
    st.markdown(f'<div class="resultado-caja">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)

with r3:
    st.write("SECCIÓN COMERCIAL:")
    color_bg = "#d4edda" if seccion_final else "#f8d7da"
    st.markdown(f'<div class="resultado-caja" style="background-color: {color_bg};">{seccion_final if seccion_final else "N/A"} mm²</div>', unsafe_allow_html=True)

if seccion_final:
    st.info(f"Capacidad real del cable (Iz corregida): **{iz_corregida:.2f} A**")
    
