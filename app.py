import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILOS (LOGO Y.T, MARCA DE AGUA Y FUENTES BOLD) ---
st.set_page_config(page_title="Ingeniería Pro - Presupuesto Maestro DTIE", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Contenedor principal de la marca de agua y logo */
    .footer-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        z-index: 9999;
        pointer-events: none;
        text-align: center;
        width: 100%;
        font-family: sans-serif;
    }

    /* Logo Y.T Estilizado */
    .logo-yt-footer {
        font-family: 'Arial Black', sans-serif;
        font-size: 22px;
        color: #22d3ee; 
        border: 2px solid rgba(34, 211, 238, 0.6);
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: bold;
        background-color: rgba(0, 0, 0, 0.2);
    }

    /* Marca de Agua */
    .watermark-text {
        font-size: 16px;
        color: rgba(255, 255, 255, 0.6);
        font-weight: bold;
    }

    /* Forzar negrita en toda la interfaz */
    p, label, .stMarkdown, div, span, button, .stSelectbox, .stNumberInput { 
        font-weight: bold !important; 
    }

    /* Estilo para resultados en negro */
    .resultado-negro {
        color: #000000 !important; font-weight: 900 !important; font-size: 18px;
        background-color: #f0f2f6; padding: 8px; border-radius: 5px;
        border-left: 5px solid #2e3b4e; margin-bottom: 2px; text-align: right;
    }

    /* Estilo Total Final */
    .total-final {
        color: #ffffff !important; font-weight: 900 !important; font-size: 32px;
        background-color: #1e1e1e; padding: 20px; border-radius: 12px; text-align: center;
        border: 2px solid #ffd700; margin-top: 20px;
    }

    .stExpander { border: 1px solid #d1d1d1 !important; border-radius: 10px !important; margin-bottom: 10px !important; }
    </style>

    <div class="footer-container">
        <span class="logo-yt-footer">Y.T</span>
        <span class="watermark-text">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE PRECIOS UNITARIOS ---
db_precios = {
    "CABLES": {
        "1.5mm": 0.25, "2.5mm": 0.38, "4mm": 0.64, "6mm": 1.30, "10mm": 2.10
    },
    "CANALIZACION": {
        "Tubo 20mm": 0.16, "Tubo 25mm": 0.23, "Tubo 32mm": 0.45
    },
    "PROTECCIONES": {
        "Cuadro 36 mod": 53.92, "IGA Combi": 56.20, "DIF Std": 13.82, 
        "DIF SI": 45.50, "PIA 10A": 3.60, "PIA 16A": 9.31, 
        "PIA 20A": 10.50, "PIA 25A": 3.64
    },
    "MECANISMOS": {
        "Interruptor": 2.44, "Conmutador": 2.42, "Cruzamiento": 5.74,
        "Base 16A": 2.79, "Base 25A": 7.10, "USB Doble": 18.20,
        "Dimmer LED": 32.00, "Sensor Presencia": 28.50, "Pulsador": 3.28,
        "Zumbador": 24.73, "Tomas RJ45": 12.50, "Toma TV/SAT": 9.80
    },
    "PEQUEÑO MAT": {
        "Caja Univ": 0.13, "Caja 100x100": 1.30, "Caja 250x250": 2.96,
        "Regleta 4mm": 0.54, "Regleta 25mm": 2.45, "Portalámparas": 1.84
    },
    "MANO OBRA": {
        "Oficial 1ª": 33.00, "Ayudante": 29.00
    }
}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Parámetros de Venta")
    modo = st.radio("Sección:", ["📐 Calculadora Técnica", "💰 Presupuesto Detallado"])
    
    if modo == "💰 Presupuesto Detallado":
        st.divider()
        st.info("Estos coeficientes se aplican al coste base (Material + MO)")
        p_ben = st.number_input("% Beneficio Industrial", 0, 100, 15)
        p_amo = st.number_input("% Gastos Generales/Amort.", 0, 100, 5)
        p_iva = st.selectbox("Tipo de IVA (%)", [21, 10, 4, 0], index=0)
        f_total = 1 + (p_ben/100) + (p_amo/100)
    else:
        f_total = 1.0

# --- 4. CALCULADORA TÉCNICA (MÉTODOS AMPLIADOS) ---
if modo == "📐 Calculadora Técnica":
    st.title("📐 Cálculo de Secciones s/ REBT")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Parámetros Eléctricos")
        red = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia Instalar (W)", value=5750)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de Potencia", 0.70, 1.00, 0.90)
        k_rec = st.selectbox("Uso", ["General (1.0)", "Motores (1.25)", "Descarga (1.8)"])
        k = 1.25 if "Motores" in k_rec else (1.8 if "Descarga" in k_rec else 1.0)
    
    with col2:
        st.subheader("Entorno e Instalación")
        mat = st.radio("Conductor", ["Cobre", "Aluminio"], horizontal=True)
        ais = st.radio("Aislamiento", ["PVC (70°)", "XLPE (90°)"], horizontal=True)
        
        # LISTA COMPLETA DE MÉTODOS DE INSTALACIÓN
        metodos_rebt = [
            "A1 - Conductores aislados en tubo en pared aislante",
            "A2 - Cable multiconductor en tubo en pared aislante",
            "B1 - Conductores aislados en tubo sobre pared de madera",
            "B2 - Cable multiconductor en tubo sobre pared de madera",
            "C - Cable bajo cubierta (directo) sobre pared de madera",
            "D1 - Cable multiconductor en conductos enterrados",
            "D2 - Cable multiconductor enterrado directamente",
            "E - Cable multiconductor al aire libre",
            "F - Cables unipolares en contacto al aire libre",
            "G - Cables unipolares separados al aire libre"
        ]
        met = st.selectbox("Método de Instalación (Referencia)", metodos_rebt)
        caida = st.number_input("CdT Máx (%)", value=3.0)

    # Cálculos
    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (1.732 * V * cos_phi)
    gamma = (48 if "PVC" in ais else 44) if mat == "Cobre" else (30 if "PVC" in ais else 28)
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * (caida/100*V))
    
    st.divider()
    c_r1, c_r2 = st.columns(2)
    c_r1.metric("Intensidad de Diseño (Ib)", f"{Ib:.2f} A")
    c_r2.metric("Sección Teórica CdT", f"{S_cdt:.2f} mm²")

# --- 5. PRESUPUESTO DESGLOSADO ---
else:
    st.title("💰 Elaboración de Presupuesto Técnico DTIE")
    st.caption("Introduce las cantidades y verifica/ajusta los precios unitarios sugeridos.")
    
    capitulos_data = []

    # CAPÍTULOS (DI, Cuadro, Iluminación, Tomas, Cocina, Lavadora, Baños, Telecom)
    # [El contenido de los expanders es el mismo de tu código original para mantener la lógica]
    
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", expanded=False):
        c1, c2 = st.columns(2)
        m_6 = c1.number_input("Metros Cable 6mm²", value=48.0, key="c1_1")
        p_6 = c2.number_input("Precio/m 6mm² (Sugerido: 1.30)", value=db_precios["CABLES"]["6mm"], key="c1_1p")
        h_of = c1.number_input("Horas Oficial 1ª (Montaje DI)", value=2.0)
        p_of = c2.number_input("Precio/h Oficial", value=db_precios["MANO OBRA"]["Oficial 1ª"])
        h_op = c1.number_input("Horas Ayudante", value=1.5)
        p_op = c2.number_input("Precio/h Ayudante", value=db_precios["MANO OBRA"]["Ayudante"])
        sub = (m_6*p_6 + h_of*p_of + h_op*p_op) * f_total
        capitulos_data.append(("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", sub))

    with st.expander("CAPÍTULO II: CUADRO DE PROTECCIÓN", expanded=False):
        c2a, c2b = st.columns(2)
        q_box = c2a.number_input("Envolvente (Cuadro 36 mod)", value=1)
        p_box = c2b.number_input("Precio Cuadro", value=db_precios["PROTECCIONES"]["Cuadro 36 mod"])
        q_iga = c2a.number_input("IGA Combi (Sobretensiones)", value=1)
        p_iga = c2b.number_input("Precio IGA", value=db_precios["PROTECCIONES"]["IGA Combi"])
        q_p10 = c2a.number_input("Cant. PIA 10A (C1)", value=2)
        p_p10 = c2b.number_input("Precio PIA 10A", value=db_precios["PROTECCIONES"]["PIA 10A"])
        h_c = st.number_input("Horas Montaje Cuadro", value=4.5)
        sub = (q_box*p_box + q_iga*p_iga + q_p10*p_p10 + h_c*p_of) * f_total
        capitulos_data.append(("CAPÍTULO II: CUADRO DE PROTECCIÓN", sub))

    with st.expander("CAPÍTULO III: ILUMINACIÓN (C1)", expanded=False):
        c3a, c3b = st.columns(2)
        m_15 = c3a.number_input("Metros Cable 1.5mm²", value=315.0)
        p_15 = c3b.number_input("Precio/m 1.5mm²", value=db_precios["CABLES"]["1.5mm"])
        q_int = c3a.number_input("Mecanismos (Int/Conm)", value=14)
        p_int = c3b.number_input("Precio Mecanismo", value=db_precios["MECANISMOS"]["Interruptor"])
        h_c1 = st.number_input("Horas Instalación C1", value=8.0)
        sub = (m_15*p_15 + q_int*p_int + h_c1*p_of) * f_total
        capitulos_data.append(("CAPÍTULO III: CIRCUITO DE ILUMINACIÓN", sub))

    with st.expander("CAPÍTULO IV: TOMAS USO GENERAL (C2)", expanded=False):
        c4a, c4b = st.columns(2)
        m_25 = c4a.number_input("Metros Cable 2.5mm²", value=325.0)
        p_25 = c4b.number_input("Precio/m 2.5mm²", value=db_precios["CABLES"]["2.5mm"])
        q_base = c4a.number_input("Bases Enchufe 16A", value=18)
        p_base = c4b.number_input("Precio Base 16A", value=db_precios["MECANISMOS"]["Base 16A"])
        h_c2 = st.number_input("Horas Instalación C2", value=10.0)
        sub = (m_25*p_25 + q_base*p_base + h_c2*p_of) * f_total
        capitulos_data.append(("CAPÍTULO IV: TOMAS USO GENERAL", sub))

    with st.expander("CAPÍTULO V: COCINA Y HORNO (C3)", expanded=False):
        c5a, c5b = st.columns(2)
        m_6c = c5a.number_input("Metros Cable 6mm² (C3)", value=30.0)
        p_6c = c5b.number_input("Precio/m 6mm² (C3)", value=db_precios["CABLES"]["6mm"], key="c5_6p")
        q_25a = c5a.number_input("Bases 25A", value=2)
        p_25a = c5b.number_input("Precio Base 25A", value=db_precios["MECANISMOS"]["Base 25A"])
        h_c3 = st.number_input("Horas Instalación C3", value=3.0)
        sub = (m_6c*p_6c + q_25a*p_25a + h_c3*p_of) * f_total
        capitulos_data.append(("CAPÍTULO V: CIRCUITO DE COCINA Y HORNO", sub))

    with st.expander("CAPÍTULO VI: LAVADORA Y TERMO (C4)", expanded=False):
        c6a, c6b = st.columns(2)
        m_4c = c6a.number_input("Metros Cable 4mm² (C4)", value=85.0)
        p_4c = c6b.number_input("Precio/m 4mm²", value=db_precios["CABLES"]["4mm"])
        h_c4 = st.number_input("Horas Instalación C4", value=4.0)
        sub = (m_4c*p_4c + 3*db_precios["MECANISMOS"]["Base 16A"] + h_c4*p_of) * f_total
        capitulos_data.append(("CAPÍTULO VI: CIRCUITO DE LAVADORA Y TERMO", sub))

    with st.expander("CAPÍTULO VII: BAÑOS Y COCINA (C5)", expanded=False):
        c7a, c7b = st.columns(2)
        m_25c = c7a.number_input("Metros Cable 2.5mm² (C5)", value=120.0)
        p_25c = c7b.number_input("Precio/m 2.5mm² (C5)", value=db_precios["CABLES"]["2.5mm"], key="c7_25p")
        h_c5 = st.number_input("Horas Instalación C5", value=5.0)
        sub = (m_25c*p_25c + 6*db_precios["MECANISMOS"]["Base 16A"] + h_c5*p_of) * f_total
        capitulos_data.append(("CAPÍTULO VII: CIRCUITO DE BAÑOS Y COCINA", sub))

    with st.expander("CAPÍTULO VIII: TELECOM Y GESTIÓN", expanded=False):
        c8a, c8b = st.columns(2)
        q_rj = c8a.number_input("Tomas RJ45", value=4)
        p_rj = c8b.number_input("Precio RJ45", value=db_precios["MECANISMOS"]["Tomas RJ45"])
        cie_v = st.number_input("Certificado Instalación (Boletín)", value=150.0)
        h_c8 = st.number_input("Horas Gestión", value=4.0)
        sub = (q_rj*p_rj + cie_v + h_c8*p_of) * f_total
        capitulos_data.append(("CAPÍTULO VIII: TELECOM. Y GESTIÓN", sub))

    # --- RESUMEN FINAL ---
    st.divider()
    st.subheader("📊 DESGLOSE ECONÓMICO FINAL")
    total_neto = 0
    for nombre, importe in capitulos_data:
        r1, r2 = st.columns([3, 1])
        r1.write(f"**{nombre}**")
        r2.markdown(f'<div class="resultado-negro">{importe:,.2f} €</div>', unsafe_allow_html=True)
        total_neto += importe
    
    total_con_iva = total_neto * (1 + p_iva/100)
    st.markdown(f'<div class="total-final">PRESUPUESTO TOTAL (IVA {p_iva}% INCL.): {total_con_iva:,.2f} €</div>', unsafe_allow_html=True)
