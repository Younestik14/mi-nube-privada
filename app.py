import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN Y MARCA DE AGUA ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Marca de agua */
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-family: sans-serif;
        font-size: 16px;
        color: rgba(0, 0, 0, 0.3);
        z-index: 9999;
        pointer-events: none;
        text-align: center;
        width: 100%;
    }
    /* Estilo para resultados en negro */
    .resultado-negro {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 24px;
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #000000;
        margin-bottom: 10px;
    }
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
        potencia = st.number_input("Potencia de la carga (W)", value=3300, step=100)
        longitud = st.number_input("Longitud de la línea (m)", value=25, min_value=1)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.85)
        caida_pct = st.number_input("Caída de Tensión permitida (%)", value=3.0, min_value=0.1, max_value=7.0, step=0.1)

    with col_b:
        st.subheader("Configuración y Carga")
        tipo_carga = st.selectbox("Tipo de Carga (Coeficiente)", [
            "General (k=1.0)", 
            "Motores (k=1.25)", 
            "Lámparas de descarga/LED (k=1.8)",
            "Vivienda - Línea General (k=1.0)"
        ])
        # Asignar coeficiente k según REBT
        k_carga = 1.25 if "Motores" in tipo_carga else (1.8 if "descarga" in tipo_carga else 1.0)
        
        material = st.radio("Material Conductor", ["Cobre", "Aluminio"], horizontal=True)
        aislante = st.radio("Aislamiento", ["PVC", "XLPE"], horizontal=True)
        metodo = st.selectbox("Método de Instalación", [
            "A1: Unipolares en tubo empotrado", "A2: Multiconductor en tubo empotrado",
            "B1: Unipolares en tubo sobre superficie", "B2: Multiconductor en tubo sobre superficie",
            "C: Sobre pared", "D: Enterrado bajo tubo", "E: Bandeja perforada",
            "F: Al aire (contacto)", "G: Al aire (separados)"
        ], index=2)
        temp_amb = st.number_input("Temperatura Ambiente (°C)", value=40, min_value=10, max_value=70)
        agrup = st.number_input("Nº de Circuitos Agrupados", 1, 12, 1)

    # --- CÁLCULOS TÉCNICOS ---
    idx_m = ["A1","A2","B1","B2","C","D","E","F","G"].index(metodo.split(":")[0])
    V = 230 if "Mono" in red else 400
    
    # Intensidad de diseño considerando el coeficiente de carga
    Ib_base = potencia / (V * cos_phi) if V == 230 else potencia / (math.sqrt(3) * V * cos_phi)
    Ib = Ib_base * k_carga
    
    # Conductividad ajustada
    gamma = (48 if aislante == "PVC" else 44) if material == "Cobre" else (30 if aislante == "PVC" else 28)
    
    # Factor de temperatura
    t_max = 70 if aislante == "PVC" else 90
    f_temp = math.sqrt((t_max - temp_amb) / (t_max - 40)) if temp_amb < t_max else 0.1
    
    # Factor agrupamiento
    f_agrup = {1:1.0, 2:0.8, 3:0.7, 4:0.65, 5:0.6, 6:0.57}.get(agrup, 0.5)
    f_total = f_temp * f_agrup
    
    # Sección por Caída de Tensión
    e_lim = (caida_pct/100)*V
    S_cdt = (2 if V==230 else 1) * longitud * Ib_base * cos_phi / (gamma * e_lim)
    
    # Selección Final
    seccion_final = None
    iz_final = 0
    f_mat = 1.0 if material == "Cobre" else 0.78
    tabla_ref = TABLAS_IZ[aislante]
    
    for s in SECCIONES:
        if s in tabla_ref:
            iz_disponible = tabla_ref[s][idx_m] * f_mat * f_total
            if s >= S_cdt and iz_disponible >= Ib:
                seccion_final = s
                iz_final = iz_disponible
                break

    # --- MOSTRAR RESULTADOS (FUENTE NEGRA) ---
    st.divider()
    st.subheader("📊 Resultados de Ingeniería")
    
    res1, res2, res3 = st.columns(3)
    
    with res1:
        st.write("Intensidad de Cálculo (con Coeficiente):")
        st.markdown(f'<div class="resultado-negro">{Ib:.2f} A</div>', unsafe_allow_html=True)
        st.caption(f"Ib base: {Ib_base:.2f}A x k={k_carga}")

    with res2:
        st.write("Sección mínima por Caída de Tensión:")
        st.markdown(f'<div class="resultado-negro">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)

    with res3:
        st.write("SECCIÓN COMERCIAL RECOMENDADA:")
        if seccion_final:
            st.markdown(f'<div class="resultado-negro" style="background-color: #d4edda;">{seccion_final} mm²</div>', unsafe_allow_html=True)
        else:
            st.error("No se encontró sección válida.")

    if seccion_final:
        st.write("---")
        st.info(f"Capacidad real del cable seleccionado ($I_z$ corregida): **{iz_final:.2f} A**")

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
