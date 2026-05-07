import streamlit as st
import pandas as pd
import math

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
        color: #000000 !important; font-weight: 900 !important; font-size: 22px;
        background-color: #f1f3f5; padding: 10px; border-radius: 8px;
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

# --- 2. MENÚ DE NAVEGACIÓN ---
with st.sidebar:
    st.title("🛡️ Panel de Ingeniería")
    seleccion = st.radio("Seleccione Herramienta:", ["📐 Calculadora Técnica REBT", "💰 Presupuesto Detallado"])
    st.divider()
    st.header("📈 Ajustes Económicos")
    beneficio = st.slider("% Margen (Beneficio + Amort.)", 0, 60, 30)
    iva = st.selectbox("% IVA Aplicable", [21, 10, 4, 0], index=0)
    f_margen = 1 + (beneficio / 100)

# --- 3. SECCIÓN: CALCULADORA TÉCNICA REBT ---
if seleccion == "📐 Calculadora Técnica REBT":
    st.title("📐 Cálculo de Secciones por Caída de Tensión y Calentamiento")
    
    col1, col2 = st.columns(2)
    with col1:
        sistema = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Diseño (W)", value=5750)
        longitud = st.number_input("Longitud de la línea (m)", value=20)
        cos_phi = st.slider("Factor de potencia", 0.7, 1.0, 0.9)
    
    with col2:
        aislante = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"])
        canalizacion = st.selectbox("Método de Instalación (ITC-BT-19)", ["B1 - Tubo en pared", "C - Cable sobre pared", "E - Aire libre"])
        caida_admitida = st.number_input("Caída de tensión máx. (%)", value=3.0)

    # Cálculo simplificado para visualización
    V = 230 if "Mono" in sistema else 400
    gamma = 48 if "PVC" in aislante else 44
    Ib = potencia / (V * cos_phi) if V == 230 else potencia / (math.sqrt(3) * V * cos_phi)
    e = (caida_admitida / 100) * V
    S_cdt = (2 if V == 230 else 1) * longitud * Ib * cos_phi / (gamma * e)
    
    st.divider()
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.write("Intensidad de empleo (Ib):")
        st.markdown(f'<div class="resultado-negro">{Ib:.2f} A</div>', unsafe_allow_html=True)
    with c_res2:
        st.write("Sección mínima por CdT:")
        st.markdown(f'<div class="resultado-negro">{S_cdt:.2f} mm²</div>', unsafe_allow_html=True)

# --- 4. SECCIÓN: PRESUPUESTO DETALLADO ---
elif seleccion == "💰 Presupuesto Detallado":
    st.title("💰 Presupuesto por Circuitos y Mecanismos")
    
    total_materiales = 0

    # --- CUADRO ELÉCTRICO ---
    with st.expander("🔌 CUADRO ELÉCTRICO Y PROTECCIONES", expanded=True):
        calidad = st.select_slider("Gama de Protecciones", ["Básica", "Profesional", "Premium (SI)"])
        desglose_c4 = st.checkbox("Desglosar C4 (Lavadora, Lavavajillas, Termo independientes)")
        
        precios_cuadro = {"Básica": 180, "Profesional": 320, "Premium (SI)": 550}
        coste_base_cuadro = precios_cuadro[calidad]
        if desglose_c4: coste_base_cuadro += 80 # Extra por más PIAs y espacio
        
        st.write(f"Coste estimado cuadro ({calidad}): {coste_base_cuadro} €")
        total_materiales += coste_base_cuadro

    # --- C1: ALUMBRADO ---
    with st.expander("💡 C1: ALUMBRADO, PULSADORES Y ZUMBADOR", expanded=False):
        c1a, c1b = st.columns(2)
        with c1a:
            p_int = st.number_input("Interruptores", 0, 50, 4)
            p_con = st.number_input("Conmutadores", 0, 50, 2)
            p_cru = st.number_input("Cruzamientos", 0, 50, 1)
        with c1b:
            p_pul = st.number_input("Pulsadores Timbre", 0, 10, 1)
            p_zum = st.number_input("Zumbadores", 0, 10, 1)
            p_mo_c1 = st.number_input("Mano de Obra C1 (€)", value=120)
        
        coste_c1 = (p_int*7) + (p_con*10) + (p_cru*15) + (p_pul*9) + (p_zum*18) + p_mo_c1
        total_materiales += coste_c1

    # --- C2: TOMAS GENERALES Y RETORNOS ---
    with st.expander("🔌 C2: TOMAS GENERALES Y RETORNOS", expanded=False):
        c2a, c2b = st.columns(2)
        with c2a:
            ench_c2 = st.number_input("Enchufes 16A", 0, 100, 12)
            m_c2_fnt = st.number_input("Metros Cable 2.5mm² (F+N+T)", 0, 500, 60)
        with c2b:
            m_ret = st.number_input("Metros Cable Retorno (1.5mm²)", 0, 500, 30)
            p_ret = st.number_input("Precio/m Retorno (€)", value=0.45)
            p_mo_c2 = st.number_input("Mano de Obra C2 (€)", value=150)
            
        coste_c2 = (ench_c2*8) + (m_c2_fnt*1.8) + (m_ret*p_ret) + p_mo_c2
        total_materiales += coste_c2

    # --- C3, C4, C5: POTENCIA ---
    with st.expander("🔥 C3, C4, C5: COCINA, BAÑO Y POTENCIA", expanded=False):
        st.info("Configuración de circuitos de gran consumo.")
        coste_c3 = st.number_input("Coste C3 (Cocina/Horno 6mm² + Base 25A)", value=140.0)
        
        label_c4 = "Coste C4 (Lavadora/Lavavajillas/Termo)" if not desglose_c4 else "Coste C4 Desglosado (3 líneas 20A)"
        coste_c4 = st.number_input(label_c4, value=250.0 if desglose_c4 else 110.0)
        
        coste_c5 = st.number_input("Coste C5 (Baño y Auxiliares)", value=90.0)
        total_materiales += (coste_c3 + coste_c4 + coste_c5)

    # --- DERIVACIÓN E INFRAESTRUCTURA ---
    with st.expander("🏗️ DERIVACIÓN INDIVIDUAL Y TIERRA", expanded=False):
        coste_di = st.number_input("Metros Derivación Individual (Material + Tubo)", value=200.0)
        coste_tierra = st.number_input("Pica de tierra y conductor", value=60.0)
        total_materiales += (coste_di + coste_tierra)

    # --- RESULTADO FINAL ---
    st.divider()
    subtotal = total_materiales * f_margen
    total_iva = subtotal * (iva / 100)
    final_cliente = subtotal + total_iva

    col_res_a, col_res_b = st.columns(2)
    with col_res_a:
        st.write("Suma Costes Directos:")
        st.markdown(f'<div class="resultado-negro">{total_materiales:,.2f} €</div>', unsafe_allow_html=True)
    with col_res_b:
        st.write(f"Base Imponible ({beneficio}% margen):")
        st.markdown(f'<div class="resultado-negro" style="background-color: #fff9db;">{subtotal:,.2f} €</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="total-final">TOTAL PRESUPUESTO CLIENTE: {final_cliente:,.2f} €</div>', unsafe_allow_html=True)
