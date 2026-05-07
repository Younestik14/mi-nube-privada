import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN Y MARCA DE AGUA ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-family: sans-serif;
        font-size: 16px;
        color: rgba(150, 150, 150, 0.4);
        z-index: 9999;
        pointer-events: none;
        text-align: center;
        width: 100%;
    }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #eee; }
    </style>
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

# --- 3. BASE DE DATOS TÉCNICA ---
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Tablas de Intensidad (Cobre, 40°C aire). Columnas: A1, A2, B1, B2, C, D, E, F, G
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
        25: [93,89,111,106,133,120,149,161,181], 35: [114,109,137,131,164,147,184,199,224],
        50: [137,131,166,159,200,178,225,243,274], 70: [173,165,211,202,257,226,286,310,350]
    }
}

# --- 4. NAVEGACIÓN ---
menu = st.sidebar.radio("Navegación", ["📐 Calculadora REBT", "📂 Gestión de Archivos"])

if menu == "📐 Calculadora REBT":
    st.title("⚡ Calculadora de Secciones REBT Pro")
    
    with st.container():
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Entrada de Datos")
            red = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
            P = st.number_input("Potencia Activa (W)", value=3300, step=100)
            L = st.number_input("Longitud de Línea (m)", value=25, min_value=1)
            cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85)
            caida_pct = st.slider("Máxima Caída Permitida (%)", 0.5, 5.0, 3.0)

        with col_b:
            st.subheader("Factores Ambientales e Instalación")
            material = st.radio("Material Conductor", ["Cobre", "Aluminio"], horizontal=True)
            aislante = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
            metodo = st.selectbox("Método de Instalación", [
                "A1: Unipolares en tubo empotrado", "A2: Multiconductor en tubo empotrado",
                "B1: Unipolares en tubo sobre superficie", "B2: Multiconductor en tubo sobre superficie",
                "C: Sobre pared", "D: Enterrado bajo tubo", "E: Bandeja perforada",
                "F: Al aire (contacto)", "G: Al aire (separados)"
            ], index=2)
            temp = st.slider("Temperatura Ambiente (°C)", 10, 60, 40)
            agrup = st.number_input("Nº de Circuitos Agrupados", 1, 12, 1)

    # --- CÁLCULOS TÉCNICOS ---
    idx_m = ["A1","A2","B1","B2","C","D","E","F","G"].index(metodo.split(":")[0])
    V = 230 if "Mono" in red else 400
    
    # Conductividad (gamma) ajustada por temperatura de servicio
    if material == "Cobre":
        gamma = 48 if aislante == "PVC" else 44
    else:
        gamma = 30 if aislante == "PVC" else 28
        
    Ib = P / (V * cos_phi) if V == 230 else P / (math.sqrt(3) * V * cos_phi)
    
    # Factor de corrección por Temperatura ambiente (Ref 40°C aire)
    t_ref = 40
    t_max = 70 if aislante == "PVC" else 90
    f_temp = math.sqrt((t_max - temp) / (t_max - t_ref))
    
    # Factor de corrección por Agrupamiento
    f_agrup = {1:1.0, 2:0.8, 3:0.7, 4:0.65, 5:0.6, 6:0.57}.get(agrup, 0.5)
    f_total = f_temp * f_agrup
    
    # SECCIÓN POR CAÍDA DE TENSIÓN
    e_lim = (caida_pct/100)*V
    S_cdt = (2 if V==230 else 1) * L * Ib * cos_phi / (gamma * e_lim)
    
    # SELECCIÓN FINAL (Cumpliendo ambos criterios)
    seccion_final = None
    iz_final = 0
    f_mat = 1.0 if material == "Cobre" else 0.78 # Factor reducción aluminio
    tabla_ref = TABLAS_IZ[aislante]
    
    for s in SECCIONES:
        if s in tabla_ref:
            iz_base = tabla_ref[s][idx_m] * f_mat
            iz_corregida = iz_base * f_total
            if s >= S_cdt and iz_corregida >= Ib:
                seccion_final = s
                iz_final = iz_corregida
                break

    # --- MOSTRAR RESULTADOS ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Intensidad de Diseño (Ib)", f"{Ib:.2f} A")
    res2.metric("Sección por CdT (Límite)", f"{S_cdt:.2f} mm²")
    
    if seccion_final:
        res3.metric("SECCIÓN RECOMENDADA", f"{seccion_final} mm²")
        
        st.info(f"💡 **Análisis de Temperatura:** Con {temp}°C y {agrup} circuitos, la capacidad real del cable es **{iz_final:.2f} A**.")
        
        # Barra de carga térmica
        carga_termica = (Ib / iz_final)
        st.write(f"Carga térmica del conductor: **{carga_termica*100:.1f}%**")
        st.progress(min(carga_termica, 1.0))
        
        caida_real = (S_cdt / seccion_final) * caida_pct
        st.write(f"Caída de tensión final: **{caida_real:.2f} %**")
    else:
        st.error("No se encontró sección comercial que cumpla los criterios bajo estas condiciones extremas.")

else:
    st.title("📂 Gestión de Documentos (Nube)")
    if supabase:
        archivo = st.file_uploader("Subir archivos", accept_multiple_files=True)
        if archivo and st.button("Guardar en Supabase"):
            for f in archivo:
                supabase.storage.from_("archivos").upload(f.name, f.getvalue(), {"upsert": "true"})
            st.success("Guardado.")
            st.rerun()
        
        lista = supabase.storage.from_("archivos").list()
        for item in lista:
            if item['name'] != ".emptyFolderPlaceholder":
                c1, c2 = st.columns([5,1])
                c1.write(f"📄 {item['name']}")
                url = supabase.storage.from_("archivos").get_public_url(item['name'])
                c2.link_button("Ver", url)
    else:
        st.warning("Configura Supabase para habilitar la nube.")
