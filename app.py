import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN GLOBAL Y ESTILOS (BOLD + MARCA AGUA BLANCA) ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Marca de agua Blanca Centrada */
    .watermark {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        font-family: sans-serif; font-size: 16px; color: rgba(255, 255, 255, 0.6);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%; font-weight: bold;
    }
    
    /* Forzar negrita en toda la interfaz */
    p, label, .stMarkdown, .stMetric, div, span, button {
        font-weight: bold !important;
    }

    /* Estilo para resultados destacados (Negro sobre Gris) */
    .resultado-negro {
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 24px;
        background-color: #f1f3f5;
        padding: 12px;
        border-radius: 8px;
        border-left: 6px solid #000000;
        margin-bottom: 10px;
        text-align: center;
    }

    /* Estilo para Totales de Presupuesto */
    .total-final {
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 32px;
        background-color: #000000;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. CONFIGURACIÓN DE NUBE (SUPABASE) ---
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-key-anon"
try:
    if "tu-proyecto" not in SUPABASE_URL:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except:
    supabase = None

# --- 3. MENÚ DE NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Panel de Control")
    seleccion = st.radio(
        "Seleccione Herramienta:",
        ["📐 Calculadora REBT (Técnica)", "💰 Presupuesto de Vivienda", "📂 Archivos en la Nube"]
    )
    st.divider()
    st.info("Configuración Global: REBT 2024 / ITC-BT-19")

# --- 4. SECCIÓN: CALCULADORA REBT ---
if seleccion == "📐 Calculadora REBT (Técnica)":
    st.title("📐 Cálculo de Secciones por REBT")
    
    # Base de datos simplificada para el ejemplo
    SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70]
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Carga y Línea")
        red = st.selectbox("Tensión", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia (W)", value=3300)
        L = st.number_input("Longitud (m)", value=30)
        cos_phi = st.slider("cos φ", 0.7, 1.0, 0.85)
        caida_max = st.number_input("Caída Tensión Máx (%)", value=3.0)

    with col_b:
        st.subheader("Entorno e Instalación")
        tipo_carga = st.selectbox("Tipo de Receptores", ["General (k=1.0)", "Motores (k=1.25)", "Descarga/LED (k=1.8)"])
        k = 1.25 if "Motores" in tipo_carga else (1.8 if "Descarga" in tipo_carga else 1.0)
        material = st.radio("Conductor", ["Cobre", "Aluminio"], horizontal=True)
        temp_amb = st.slider("Temperatura Ambiente (°C)", 10, 60, 40)
        metodo = st.selectbox("Método de Instalación", ["A1", "A2", "B1", "B2", "C", "D", "E", "F", "G"], index=4)

    # Lógica de cálculo simplificada
    V = 230 if "Mono" in red else 400
    Ib_real = P / (V * cos_phi) if V == 230 else P / (math.sqrt(3) * V * cos_phi)
    Ib_calculo = Ib_real * k
    gamma = 48 if material == "Cobre" else 30
    
    e_lim = (caida_max / 100) * V
    S_cdt = (2 if V == 230 else 1) * L * Ib_real * cos_phi / (gamma * e_lim)

    st.divider()
    res1, res2, res3 = st.columns(3)
    with res1:
        st.write("Intensidad de Cálculo (Ib):")
        st.markdown(f'<div class="resultado-negro">{Ib_calculo:.2f} A</div>', unsafe_allow_html=True)
    with res2:
        st.write("Sección por Voltaje:")
        st.markdown(f'<div class="resultado-negro">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)
    with res3:
        # Buscamos la sección comercial superior
        s_comercial = next((s for s in SECCIONES if s >= S_cdt), "N/A")
        st.write("SECCIÓN RECOMENDADA:")
        st.markdown(f'<div class="resultado-negro" style="background-color: #d4edda;">{s_comercial} mm²</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: PRESUPUESTO ---
elif seleccion == "💰 Presupuesto de Vivienda":
    st.title("💰 Generador de Presupuesto")
    
    with st.sidebar:
        st.header("Márgenes")
        beneficio = st.slider("% Beneficio", 0, 50, 20)
        iva = st.selectbox("% IVA", [21, 10, 4, 0])
    
    capitulos = ["1. Derivación Individual", "2. Cuadro Eléctrico", "3. Alumbrado (C1)", "4. Tomas Uso Gral (C2)", "5. Cocina/Horno (C3)", "6. Lavadora/Termo (C4)", "7. Baño/Aux (C5)", "8. Otros"]
    
    costes = {}
    f_margen = 1 + (beneficio / 100)
    
    st.subheader("Costes de Material y Mano de Obra")
    c1, c2 = st.columns(2)
    for i, cap in enumerate(capitulos):
        with (c1 if i % 2 == 0 else c2):
            costes[cap] = st.number_input(f"Coste Base {cap} (€)", value=100.0, step=50.0)

    st.divider()
    subtotal = sum(costes.values()) * f_margen
    total_iva = subtotal * (iva / 100)
    
    st.subheader("Desglose Final (Precio Venta)")
    for cap, valor in costes.items():
        st.write(f"🔹 {cap}")
        st.markdown(f'<div class="resultado-negro" style="text-align: right;">{(valor * f_margen):,.2f} €</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="total-final">TOTAL CON IVA: {(subtotal + total_iva):,.2f} €</div>', unsafe_allow_html=True)

# --- 6. SECCIÓN: ARCHIVOS ---
else:
    st.title("📂 Gestión de Documentos")
    if supabase:
        subida = st.file_uploader("Arrastra aquí tus planos o facturas", accept_multiple_files=True)
        if subida and st.button("Subir a la Nube"):
            for f in subida:
                supabase.storage.from_("archivos").upload(f.name, f.getvalue())
            st.success("Archivos guardados.")
        
        st.subheader("Documentos Guardados")
        # Aquí iría el listado de archivos de Supabase
    else:
        st.warning("⚠️ Conecte Supabase para usar el almacenamiento.")
