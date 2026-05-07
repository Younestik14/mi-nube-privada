import streamlit as st
import pandas as pd
import math
from supabase import create_client

# --- 1. CONFIGURACIÓN GLOBAL Y ESTILOS ---
st.set_page_config(page_title="Ingeniería Eléctrica Pro", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .watermark {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        font-family: sans-serif; font-size: 16px; color: rgba(255, 255, 255, 0.6);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%; font-weight: bold;
    }
    p, label, .stMarkdown, .stMetric, div, span, button { font-weight: bold !important; }
    .resultado-negro {
        color: #000000 !important; font-weight: 900 !important; font-size: 24px;
        background-color: #f1f3f5; padding: 12px; border-radius: 8px;
        border-left: 6px solid #000000; margin-bottom: 10px; text-align: center;
    }
    .total-final {
        color: #ffffff !important; font-weight: 900 !important; font-size: 32px;
        background-color: #000000; padding: 20px; border-radius: 10px; text-align: center;
    }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. LÓGICA DE NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Panel de Control")
    seleccion = st.radio("Herramienta:", ["📐 Calculadora Técnica", "💰 Presupuesto Profesional"])
    st.divider()
    if seleccion == "💰 Presupuesto Profesional":
        st.header("📈 Ajustes Económicos")
        beneficio = st.slider("% Beneficio Industrial", 0, 50, 20)
        iva = st.selectbox("% IVA", [21, 10, 4, 0])
        f_margen = 1 + (beneficio / 100)

# --- 3. SECCIÓN: CALCULADORA TÉCNICA (Resumen) ---
if seleccion == "📐 Calculadora Técnica":
    st.title("📐 Cálculo de Secciones Profesionales")
    st.info("Utilice el menú lateral para ir al presupuesto detallado con mecanismos y protecciones.")

# --- 4. SECCIÓN: PRESUPUESTO PROFESIONAL ---
elif seleccion == "💰 Presupuesto Profesional":
    st.title("💰 Presupuesto de Obra Eléctrica Detallado")
    
    total_coste_directo = 0

    # --- CAPÍTULO: CUADRO ELÉCTRICO ---
    with st.expander("🔌 CUADRO ELÉCTRICO Y PROTECCIONES", expanded=True):
        st.subheader("Configuración de Calidad")
        calidad = st.select_slider("Calidad de las Protecciones", options=["Estándar", "Profesional", "Premium (Superinmunizados)"])
        p_base_iga = 45 if calidad == "Estándar" else (85 if calidad == "Profesional" else 150)
        
        c_c4 = st.checkbox("¿Desglosar C4 en 3 circuitos independientes? (C4.1, C4.2, C4.3)")
        
        st.markdown("**Protecciones a instalar:**")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            q_iga = st.number_input("IGA + Sobretensiones (Ud)", value=1)
            q_dif = st.number_input("Diferenciales (Ud)", value=2)
        with col_q2:
            n_pias = 8 if c_c4 else 5
            q_pia = st.number_input("Magnetotérmicos (PIAs) (Ud)", value=n_pias)
        
        total_cuadro = (q_iga * p_base_iga) + (q_dif * (p_base_iga*0.8)) + (q_pia * 12)
        st.write(f"Coste estimado materiales cuadro ({calidad}): {total_cuadro:.2f} €")
        total_coste_directo += total_cuadro

    # --- CAPÍTULO: C1 ALUMBRADO (TIMBRE Y PULSADOR) ---
    with st.expander("💡 C1: ALUMBRADO Y AVISO ACÚSTICO", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Mecanismos de mando**")
            p_sencillo = st.number_input("Interruptores sencillos", value=4)
            p_conmutado = st.number_input("Conmutadores", value=2)
            p_cruzamiento = st.number_input("Cruzamientos", value=1)
            p_pulsador = st.number_input("Pulsadores Timbre", value=1)
        with c2:
            st.markdown("**Avisador**")
            zumbador = st.number_input("Zumbador/Timbre (Ud)", value=1)
            mo_c1 = st.number_input("Mano de obra C1 (€)", value=150)
        
        coste_c1 = (p_sencillo*6) + (p_conmutado*9) + (p_cruzamiento*14) + (p_pulsador*8) + (zumbador*15) + mo_c1
        total_coste_directo += coste_c1

    # --- CAPÍTULO: C2 TOMAS DE CORRIENTE Y RETORNOS ---
    with st.expander("🔌 C2: TOMAS DE USO GENERAL", expanded=False):
        st.info("Incluye cableado de fase, neutro, tierra y retornos para conmutaciones.")
        col_c2_1, col_c2_2 = st.columns(2)
        with col_c2_1:
            enchufes_c2 = st.number_input("Bases de enchufe 16A (C2)", value=10)
            m_cable_25 = st.number_input("Metros cable 2.5mm² (Azul/Gris/Tierra)", value=60)
        with col_c2_2:
            m_retorno = st.number_input("Metros Cable Retorno 1.5mm² (Negro/Blanco)", value=30)
            p_retorno = st.number_input("Precio/m cable retorno", value=0.45)
        
        coste_c2 = (enchufes_c2*7) + (m_cable_25*0.7) + (m_retorno*p_retorno) + 120
        total_coste_directo += coste_c2

    # --- CAPÍTULOS POTENCIA (C3, C4, C5) ---
    with st.expander("🍳 C3, C4, C5: COCINA Y POTENCIA", expanded=False):
        st.write("Configuración de circuitos de alta potencia")
        c3_coste = st.number_input("Coste material C3 (Cocina/Horno 6mm²)", value=120.0)
        if c_c4:
            st.write("C4 Desglosado (Lavadora, Lavavajillas, Termo independientes)")
            c4_coste = st.number_input("Coste material C4 desglosado (4mm² x3)", value=280.0)
        else:
            c4_coste = st.number_input("Coste material C4 (4mm²)", value=100.0)
        c5_coste = st.number_input("Coste material C5 (Baño/Auxiliar)", value=80.0)
        total_coste_directo += (c3_coste + c4_coste + c5_coste)

    # --- RESULTADOS FINALES ---
    st.divider()
    subtotal_venta = total_coste_directo * f_margen
    total_final_iva = subtotal_venta * (1 + (iva/100))

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.write("Coste Directo (Materiales + MO):")
        st.markdown(f'<div class="resultado-negro">{total_coste_directo:,.2f} €</div>', unsafe_allow_html=True)
    with col_f2:
        st.write(f"Base Imponible (con {beneficio}% Beneficio):")
        st.markdown(f'<div class="resultado-negro">{subtotal_venta:,.2f} €</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="total-final">TOTAL PRESUPUESTO (IVA INCL.): {total_final_iva:,.2f} €</div>', unsafe_allow_html=True)
    
    st.success(f"Presupuesto generado con protecciones de calidad **{calidad}**.")
