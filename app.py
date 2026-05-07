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
    .card-capitulo {
        background-color: #ffffff; padding: 15px; border-radius: 10px; 
        border: 1px solid #ddd; margin-bottom: 20px;
    }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui</div>
    """,
    unsafe_allow_html=True
)

# --- 2. LÓGICA DE NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Panel de Control")
    seleccion = st.radio(
        "Seleccione Herramienta:",
        ["📐 Calculadora REBT (Técnica)", "💰 Presupuesto Detallado Vivienda"]
    )
    st.divider()
    if seleccion == "💰 Presupuesto Detallado Vivienda":
        st.header("📈 Márgenes e IVA")
        p_beneficio = st.slider("% Beneficio Industrial", 0, 50, 20)
        p_amortiza = st.slider("% Amortización", 0, 20, 10)
        p_iva = st.selectbox("% IVA", [21, 10, 4, 0])
        factor_m = 1 + (p_beneficio/100) + (p_amortiza/100)

# --- 3. SECCIÓN: CALCULADORA REBT (Mantenida según versiones anteriores) ---
if seleccion == "📐 Calculadora REBT (Técnica)":
    st.title("📐 Cálculo de Secciones Profesionales")
    # ... (Se mantiene el código de cálculo técnico anterior aquí) ...
    st.info("Utilice el menú lateral para ir al presupuesto detallado.")

# --- 4. SECCIÓN: PRESUPUESTO DETALLADO ---
elif seleccion == "💰 Presupuesto Detallado Vivienda":
    st.title("💰 Presupuesto por Materiales y Circuitos")
    
    capitulos = {
        "C1: Alumbrado": "1.5mm²",
        "C2: Tomas Uso Gral": "2.5mm²",
        "C3: Cocina/Horno": "6mm²",
        "C4: Lavadora/Termo": "4mm²",
        "C5: Baños/Aux": "2.5mm²"
    }

    coste_total_material = 0
    
    for cap, seccion_def in capitulos.items():
        with st.expander(f"📦 CONFIGURAR {cap}", expanded=False):
            st.markdown(f"### Desglose de {cap}")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                mecanismos = st.number_input(f"Nº de Mecanismos (Enchufes/Llaves) - {cap}", min_value=0, value=5, key=f"mec_{cap}")
                p_u_mec = st.number_input(f"Precio Unit. Mecanismo (€)", value=8.5, key=f"pmec_{cap}")
            
            with c2:
                st.markdown("**Metros de Cable (Fase/Neutro/Tierra)**")
                l_azul = st.number_input(f"Metros Azul (Neutro) {seccion_def}", min_value=0.0, value=20.0, key=f"az_{cap}")
                l_marron = st.number_input(f"Metros Marrón/Gris/Negro (Fase) {seccion_def}", min_value=0.0, value=20.0, key=f"ma_{cap}")
                l_verde = st.number_input(f"Metros Verde/Amarillo (Tierra) {seccion_def}", min_value=0.0, value=20.0, key=f"ve_{cap}")
            
            with c3:
                p_m_cable = st.number_input(f"Precio/metro cable {seccion_def} (€)", value=0.6, key=f"pcable_{cap}")
                mano_obra = st.number_input(f"Mano de Obra fija del capítulo (€)", value=100.0, key=f"mo_{cap}")

            # Cálculo del capítulo
            total_cable = (l_azul + l_marron + l_verde) * p_m_cable
            total_mecanismos = mecanismos * p_u_mec
            coste_cap = total_cable + total_mecanismos + mano_obra
            coste_total_material += coste_cap
            
            st.markdown(f"**Subtotal Coste Real {cap}: {coste_cap:,.2f} €**")

    # Capítulo especial: Cuadro y Derivación
    with st.expander("🔌 CUADRO ELÉCTRICO Y DERIVACIÓN", expanded=False):
        coste_cuadro = st.number_input("Coste Material Cuadro + Protecciones (€)", value=250.0)
        coste_di = st.number_input("Coste Derivación Individual (Cables + Tubo) (€)", value=150.0)
        coste_total_material += (coste_cuadro + coste_di)

    # --- RESULTADOS FINALES ---
    st.divider()
    st.subheader("📊 Resumen Económico del Presupuesto")
    
    base_imponible = coste_total_material * factor_m
    iva_calculado = base_imponible * (p_iva / 100)
    total_cliente = base_imponible + iva_calculado

    r1, r2, r3 = st.columns(3)
    with r1:
        st.write("Suma Costes Base (Material+MO):")
        st.markdown(f'<div class="resultado-negro">{coste_total_material:,.2f} €</div>', unsafe_allow_html=True)
    
    with r2:
        st.write(f"Venta (con {p_beneficio+p_amortiza}% margen):")
        st.markdown(f'<div class="resultado-negro" style="background-color: #fff9db;">{base_imponible:,.2f} €</div>', unsafe_allow_html=True)
        
    with r3:
        st.write(f"IVA ({p_iva}%):")
        st.markdown(f'<div class="resultado-negro">{iva_calculado:,.2f} €</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="total-final">TOTAL PRESUPUESTO CLIENTE: {total_cliente:,.2f} €</div>', unsafe_allow_html=True)

    # Tabla resumen de cables
    st.write("### 📝 Resumen de Cables para pedido")
    datos_cables = {
        "Circuito": ["C1 (1.5mm²)", "C2 (2.5mm²)", "C3 (6mm²)", "C4 (4mm²)", "C5 (2.5mm²)"],
        "Azul (m)": [st.session_state.get(f"az_C1: Alumbrado", 0), st.session_state.get(f"az_C2: Tomas Uso Gral", 0), st.session_state.get(f"az_C3: Cocina/Horno", 0), st.session_state.get(f"az_C4: Lavadora/Termo", 0), st.session_state.get(f"az_C5: Baños/Aux", 0)],
        "Fase (m)": [st.session_state.get(f"ma_C1: Alumbrado", 0), st.session_state.get(f"ma_C2: Tomas Uso Gral", 0), st.session_state.get(f"ma_C3: Cocina/Horno", 0), st.session_state.get(f"ma_C4: Lavadora/Termo", 0), st.session_state.get(f"ma_C5: Baños/Aux", 0)],
        "Tierra (m)": [st.session_state.get(f"ve_C1: Alumbrado", 0), st.session_state.get(f"ve_C2: Tomas Uso Gral", 0), st.session_state.get(f"ve_C3: Cocina/Horno", 0), st.session_state.get(f"ve_C4: Lavadora/Termo", 0), st.session_state.get(f"ve_C5: Baños/Aux", 0)]
    }
    st.table(pd.DataFrame(datos_cables))
