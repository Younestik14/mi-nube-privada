import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN Y MARCA DE AGUA ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

# Marca de agua persistente
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-family: sans-serif;
        font-size: 14px;
        color: rgba(150, 150, 150, 0.5);
        z-index: 9999;
        pointer-events: none;
    }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. CREDENCIALES SUPABASE ---
# Sustituye con tus datos reales de Supabase
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-key-anon-public"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None

# --- 3. BASE DE DATOS REBT (UNE 20460-5-523) ---
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Estructura: [A1, A2, B1, B2, C, D, E, F, G]
tablas_iz = {
    "PVC_Mono": {
        1.5: [13,13,15,15,18,18,20,22,24], 2.5: [18,17,21,20,25,24,28,30,33],
        4: [24,23,28,27,34,32,37,40,45], 6: [31,29,36,35,44,41,48,52,58],
        10: [42,40,50,48,60,55,66,71,80], 16: [56,53,66,64,80,73,88,96,107],
        25: [73,70,88,84,106,96,117,127,143], 35: [90,86,109,103,131,117,144,157,176],
        50: [108,103,131,124,159,141,175,190,214], 70: [136,130,167,158,204,179,222,242,273],
        95: [164,156,202,192,247,216,269,293,332], 120: [188,179,234,222,286,249,312,339,384]
    },
    "XLPE_Mono": {
        1.5: [16,16,19,19,22,22,25,27,30], 2.5: [23,22,27,26,31,30,35,38,41],
        4: [30,29,36,35,42,40,47,51,56], 6: [39,37,46,45,54,51,61,66,73],
        10: [53,51,63,61,75,69,84,91,101], 16: [70,67,83,81,100,91,112,122,136],
        25: [93,89,111,106,133,120,149,161,181], 35: [114,109,137,131,164,147,184,199,224],
        50: [137,131,166,159,200,178,225,243,274], 70: [173,165,211,202,257,226,286,310,350],
        95: [209,199,256,245,313,274,348,377,426], 120: [240,229,297,284,364,316,405,438,496]
    }
}

# --- 4. LÓGICA DE NAVEGACIÓN ---
menu = st.sidebar.radio("Navegación", ["📐 Calculadora REBT", "📂 Gestión de Archivos"])

if menu == "📐 Calculadora REBT":
    st.title("⚡ Calculadora de Secciones REBT Pro")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Entrada de Datos")
        red = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia Activa (W)", value=3300, step=100)
        L = st.number_input("Longitud de Línea (m)", value=25, min_value=1)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85)
        caida_pct = st.slider("Máxima Caída Permitida (%)", 1.0, 5.0, 3.0)

    with col_b:
        st.subheader("Instalación y Factores")
        material = st.radio("Material Conductor", ["Cobre", "Aluminio"], horizontal=True)
        aislante = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        metodo = st.selectbox("Método de Instalación", [
            "A1: Unipolares en tubo empotrado", "A2: Multiconductor en tubo empotrado",
            "B1: Unipolares en tubo sobre superficie", "B2: Multiconductor en tubo sobre superficie",
            "C: Sobre pared", "D: Enterrado bajo tubo", "E: Bandeja perforada",
            "F: Al aire (contacto)", "G: Al aire (separados)"
        ], index=2)
        temp = st.slider("Temperatura Ambiente (°C)", 15, 60, 40)
        agrup = st.number_input("Nº de Circuitos en el conducto", 1, 10, 1)

    # CÁLCULOS TÉCNICOS
    idx_m = ["A1","A2","B1","B2","C","D","E","F","G"].index(metodo.split(":")[0])
    V = 230 if "Mono" in red else 400
    gamma = (48 if aislante == "PVC" else 44) if material == "Cobre" else (30 if aislante == "PVC" else 28)
    
    Ib = P / (V * cos_phi) if V == 230 else P / (math.sqrt(3) * V * cos_phi)
    
    # Factores de corrección
    f_temp = 1.0 if temp <= 40 else (1 - (temp - 40) * 0.05)
    f_agrup = {1:1, 2:0.8, 3:0.7, 4:0.65}.get(agrup, 0.5)
    f_total = f_temp * f_agrup
    
    # Sección por Caída de Tensión
    e_lim = (caida_pct/100)*V
    S_cdt = (2 if V==230 else 1) * L * Ib * cos_phi / (gamma * e_lim)
    
    # Búsqueda en Tablas UNE
    seccion_ok = None
    iz_actual = 0
    tabla_ref = tablas_iz[f"{aislante}_Mono"]
    f_mat = 1.0 if material == "Cobre" else 0.78
    
    for s in SECCIONES:
        if s in tabla_ref:
            iz_disponible = tabla_ref[s][idx_m] * f_mat * f_total
            if s >= S_cdt and iz_disponible >= Ib:
                seccion_ok = s
                iz_actual = iz_disponible
                break

    # MOSTRAR RESULTADOS
    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Intensidad de Diseño", f"{Ib:.2f} A")
    r2.metric("Sección por Voltaje", f"{S_cdt:.2f} mm²")
    if seccion_ok:
        r3.metric("SECCIÓN RECOMENDADA", f"{seccion_ok} mm²", delta="Cumple REBT")
        st.success(f"Instalación validada: El cable soporta hasta {iz_actual:.2f} A en estas condiciones.")
    else:
        st.error("No se encontró sección comercial que cumpla ambos criterios.")

else:
    st.title("📂 Gestión de Documentos (Nube)")
    if supabase:
        archivo = st.file_uploader("Subir archivos (PDF, Planos, Imágenes)", accept_multiple_files=True)
        if archivo and st.button("Guardar en Supabase"):
            for f in archivo:
                supabase.storage.from_("archivos").upload(f.name, f.getvalue(), {"upsert": "true"})
            st.success("Guardado con éxito.")
            st.rerun()
        
        st.subheader("Archivos en la nube")
        try:
            lista = supabase.storage.from_("archivos").list()
            for item in lista:
                if item['name'] != ".emptyFolderPlaceholder":
                    c1, c2 = st.columns([5,1])
                    c1.write(f"📄 {item['name']}")
                    url = supabase.storage.from_("archivos").get_public_url(item['name'])
                    c2.link_button("Ver", url)
        except:
            st.info("Sube tu primer archivo para empezar.")
    else:
        st.warning("Conecta tu base de datos de Supabase para activar esta sección.")
