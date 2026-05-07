import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN Y ESTILOS (LOGO Y.T, MARCA DE AGUA Y FUENTES BOLD) ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Logo Y.T Estilizado */
    .logo-yt {
        position: fixed;
        top: 15px;
        left: 15px;
        font-family: 'Arial Black', sans-serif;
        font-size: 24px;
        color: #22d3ee; /* Color cian eléctrico */
        border: 2px solid #22d3ee;
        padding: 2px 10px;
        border-radius: 5px;
        z-index: 10000;
        background-color: rgba(15, 23, 42, 0.8); /* Fondo sutil para legibilidad */
    }

    /* Marca de agua Blanca */
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-family: sans-serif;
        font-size: 16px;
        color: rgba(255, 255, 255, 0.6); /* Blanco con transparencia */
        z-index: 9999;
        pointer-events: none;
        text-align: center;
        width: 100%;
        font-weight: bold;
    }
    
    /* Forzar negrita en etiquetas y textos generales */
    p, label, .stMarkdown, .stMetric, div {
        font-weight: bold !important;
    }

    /* Estilo para resultados destacados en negro y bold */
    .resultado-destacado {
        color: #000000 !important;
        font-weight: 900 !important; /* Extra bold */
        font-size: 26px;
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #000000;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
    <div class="logo-yt">Y.T</div>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. CREDENCIALES SUPABASE ---
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-key-anon-public"

try:
    if "tu-proyecto" not in SUPABASE_URL:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception:
    supabase = None

# --- 3. BASE DE DATOS TÉCNICA (SECCIONES Y TABLAS) ---
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

# --- 4. NAVEGACIÓN ---
menu = st.sidebar.radio("Navegación", ["📐 Calculadora REBT", "📂 Gestión de Archivos"])

if menu == "📐 Calculadora REBT":
    st.title("⚡ Calculadora Profesional REBT")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Entrada de Datos")
        red = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia (W)", value=3300, step=100)
        longitud = st.number_input("Longitud (m)", value=25, min_value=1)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85)
        caida_pct = st.number_input("Caída Tensión Permitida (%)", value=3.0, step=0.1)

    with col_b:
        st.subheader("Configuración Carga e Instalación")
        tipo_carga = st.selectbox("Tipo de Carga", [
            "General (k=1.0)", "Motores (k=1.25)", "Descarga/LED (k=1.8)"
        ])
        k_carga = 1.25 if "Motores" in tipo_carga else (1.8 if "Descarga" in tipo_carga else 1.0)
        material = st.radio("Material", ["Cobre", "Aluminio"], horizontal=True)
        aislante = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        metodo = st.selectbox("Método Instalación", ["A1","A2","B1","B2","C","D","E","F","G"], index=2)
        temp_amb = st.number_input("Temperatura Ambiente (°C)", value=40)
        agrup = st.number_input("Nº Circuitos Agrupados", 1, 12, 1)

    # --- CÁLCULOS ---
    V = 230 if "Mono" in red else 400
    idx_m = ["A1","A2","B1","B2","C","D","E","F","G"].index(metodo)
    Ib_base = potencia / (V * cos_phi) if V == 230 else potencia / (math.sqrt(3) * V * cos_phi)
    Ib = Ib_base * k_carga
    gamma = (48 if aislante == "PVC" else 44) if material == "Cobre" else (30 if aislante == "PVC" else 28)
    
    t_max = 70 if aislante == "PVC" else 90
    f_temp = math.sqrt((t_max - temp_amb) / (t_max - 40)) if temp_amb < t_max else 0.1
    f_agrup = {1:1.0, 2:0.8, 3:0.7, 4:0.65}.get(agrup, 0.5)
    f_total = f_temp * f_agrup
    
    e_lim = (caida_pct/100)*V
    S_cdt = (2 if V==230 else 1) * longitud * Ib_base * cos_phi / (gamma * e_lim)
    
    seccion_final = None
    iz_final = 0
    tabla_ref = TABLAS_IZ[aislante]
    f_mat = 1.0 if material == "Cobre" else 0.78
    
    for s in SECCIONES:
        if s in tabla_ref:
            iz_corr = tabla_ref[s][idx_m] * f_mat * f_total
            if s >= S_cdt and iz_corr >= Ib:
                seccion_final = s
                iz_final = iz_corr
                break

    # --- RESULTADOS (NEGRITA Y NEGRO) ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    with res1:
        st.write("Intensidad Ib (con k):")
        st.markdown(f'<div class="resultado-destacado">{Ib:.2f} A</div>', unsafe_allow_html=True)
    with res2:
        st.write("Sección Mín. por Voltaje:")
        st.markdown(f'<div class="resultado-destacado">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)
    with res3:
        st.write("SECCIÓN RECOMENDADA:")
        color = "#d4edda" if seccion_final else "#f8d7da"
        st.markdown(f'<div class="resultado-destacado" style="background-color: {color};">{seccion_final if seccion_final else "ERROR"} mm²</div>', unsafe_allow_html=True)

else:
    st.title("📂 Gestión de Archivos")
    # (Código de Supabase igual al anterior...)
    
