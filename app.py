import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Ingeniería Pro - Presupuesto Maestro DTIE", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .watermark {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        font-family: sans-serif; font-size: 16px; color: rgba(255, 255, 255, 0.4);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%; font-weight: bold;
    }
    p, label, .stMarkdown, div, span, button { font-weight: bold !important; }
    .resultado-negro {
        color: #000000 !important; font-weight: 900 !important; font-size: 18px;
        background-color: #f0f2f6; padding: 8px; border-radius: 5px;
        border-left: 5px solid #2e3b4e; margin-bottom: 2px; text-align: right;
    }
    .total-final {
        color: #ffffff !important; font-weight: 900 !important; font-size: 32px;
        background-color: #1e1e1e; padding: 20px; border-radius: 12px; text-align: center;
        border: 2px solid #ffd700; margin-top: 20px;
    }
    .stExpander { border: 1px solid #d1d1d1 !important; border-radius: 10px !important; margin-bottom: 10px !important; }
    </style>
    <div class="watermark">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica</div>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE PRECIOS UNITARIOS (Extraídos de tus archivos DTIE) ---
# He añadido una columna de "Precio Sugerido" para que sepas qué valor poner.
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

# --- 3. SIDEBAR: COEFICIENTES ---
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

# --- 4. CALCULADORA TÉCNICA (MANTENIDA SIN CAMBIOS) ---
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
        st.subheader("Entorno")
        mat = st.radio("Conductor", ["Cobre", "Aluminio"], horizontal=True)
        ais = st.radio("Aislamiento", ["PVC (70°)", "XLPE (90°)"], horizontal=True)
        met = st.selectbox("Instalación", ["A1 - Empotrado", "B1 - Superficie", "C - Bajo Pared"])
        caida = st.number_input("CdT Máx (%)", value=3.0)

    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (1.732 * V * cos_phi)
    gamma = (48 if "PVC" in ais else 44) if mat == "Cobre" else (30 if "PVC" in ais else 28)
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * (caida/100*V))
    
    st.divider()
    c_r1, c_r2 = st.columns(2)
    c_r1.metric("Intensidad de Diseño (Ib)", f"{Ib:.2f} A")
    c_r2.metric("Sección Teórica CdT", f"{S_cdt:.2f} mm²")

# --- 5. PRESUPUESTO DESGLOSADO (NIVEL MÁXIMO) ---
else:
    st.title("💰 Elaboración de Presupuesto Técnico DTIE")
    st.caption("Introduce las cantidades y verifica/ajusta los precios unitarios sugeridos.")
    
    capitulos_data = []

    # CAP I: DI
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", expanded=False):
        c1, c2 = st.columns(2)
        m_6 = c1.number_input("Metros Cable 6mm²", value=48.0, key="c1_1")
        p_6 = c2.number_input("Precio/m 6mm² (Sugerido: 1.30)", value=db_precios["CABLES"]["6mm"], key="c1_1p")
        h_of = c1.number_input("Horas Oficial 1ª (Montaje DI)", value=2.0)
        p_of = c2.number_input("Precio/h Oficial (Sugerido: 33.00)", value=db_precios["MANO OBRA"]["Oficial 1ª"])
        h_op = c1.number_input("Horas Ayudante (Rozas/Limpieza)", value=1.5)
        p_op = c2.number_input("Precio/h Ayudante (Sugerido: 29.00)", value=db_precios["MANO OBRA"]["Ayudante"])
        
        sub = (m_6*p_6 + h_of*p_of + h_op*p_op) * f_total
        capitulos_data.append(("CAPÍTULO I: DERIVACIÓN INDIVIDUAL", sub))

    # CAP II: CUADRO
    with st.expander("CAPÍTULO II: CUADRO DE PROTECCIÓN", expanded=False):
        st.write("#### Protecciones y Envolvente")
        c2a, c2b = st.columns(2)
        q_box = c2a.number_input("Envolvente (Cuadro 36 mod)", value=1)
        p_box = c2b.number_input("Precio Cuadro (Sugerido: 53.92)", value=db_precios["PROTECCIONES"]["Cuadro 36 mod"])
        q_iga = c2a.number_input("IGA Combi (Sobretensiones)", value=1)
        p_iga = c2b.number_input("Precio IGA (Sugerido: 56.20)", value=db_precios["PROTECCIONES"]["IGA Combi"])
        
        st.write("#### Magnetotérmicos (PIAs)")
        c2c, c2d = st.columns(2)
        q_p10 = c2c.number_input("Cant. PIA 10A (C1)", value=2)
        p_p10 = c2d.number_input("Precio PIA 10A (Sugerido: 3.60)", value=db_precios["PROTECCIONES"]["PIA 10A"])
        q_p16 = c2c.number_input("Cant. PIA 16A (C2/C5)", value=5)
        p_p16 = c2d.number_input("Precio PIA 16A (Sugerido: 9.31)", value=db_precios["PROTECCIONES"]["PIA 16A"])
        q_p25 = c2c.number_input("Cant. PIA 25A (C3)", value=1)
        p_p25 = c2d.number_input("Precio PIA 25A (Sugerido: 3.64)", value=db_precios["PROTECCIONES"]["PIA 25A"])
        
        h_c = st.number_input("Horas Montaje/Peinado de Cuadro", value=4.5)
        sub = (q_box*p_box + q_iga*p_iga + q_p10*p_p10 + q_p16*p_p16 + q_p25*p_p25 + h_c*p_of) * f_total
        capitulos_data.append(("CAPÍTULO II: CUADRO DE PROTECCIÓN", sub))

    # CAP III: ILUMINACIÓN
    with st.expander("CAPÍTULO III: CIRCUITO DE ILUMINACIÓN (C1)", expanded=False):
        c3a, c3b = st.columns(2)
        m_15 = c3a.number_input("Metros Cable 1.5mm²", value=315.0)
        p_15 = c3b.number_input("Precio/m 1.5mm² (Sugerido: 0.25)", value=db_precios["CABLES"]["1.5mm"])
        q_int = c3a.number_input("Mecanismos (Interruptores/Conmut)", value=14)
        p_int = c3b.number_input("Precio medio Mecanismo (Sugerido: 2.44)", value=db_precios["MECANISMOS"]["Interruptor"])
        q_dim = c3a.number_input("Reguladores (Dimmers)", value=2)
        p_dim = c3b.number_input("Precio Dimmer (Sugerido: 32.00)", value=db_precios["MECANISMOS"]["Dimmer LED"])
        h_c1 = st.number_input("Horas Oficial (Tirado y montaje C1)", value=8.0)
        
        sub = (m_15*p_15 + q_int*p_int + q_dim*p_dim + h_c1*p_of) * f_total
        capitulos_data.append(("CAPÍTULO III: CIRCUITO DE ILUMINACIÓN", sub))

    # CAP IV: TOMAS GENERALES
    with st.expander("CAPÍTULO IV: TOMAS DE USO GENERAL (C2)", expanded=False):
        c4a, c4b = st.columns(2)
        m_25 = c4a.number_input("Metros Cable 2.5mm²", value=325.0)
        p_25 = c4b.number_input("Precio/m 2.5mm² (Sugerido: 0.38)", value=db_precios["CABLES"]["2.5mm"])
        q_base = c4a.number_input("Bases de Enchufe 16A", value=18)
        p_base = c4b.number_input("Precio Base 16A (Sugerido: 2.79)", value=db_precios["MECANISMOS"]["Base 16A"])
        q_usb = c4a.number_input("Tomas USB Dobles", value=3)
        p_usb = c4b.number_input("Precio USB (Sugerido: 18.20)", value=db_precios["MECANISMOS"]["USB Doble"])
        h_c2 = st.number_input("Horas Instalación C2", value=10.0)
        
        sub = (m_25*p_25 + q_base*p_base + q_usb*p_usb + h_c2*p_of) * f_total
        capitulos_data.append(("CAPÍTULO IV: TOMAS USO GENERAL", sub))

    # CAP V: COCINA
    with st.expander("CAPÍTULO V: CIRCUITO DE COCINA Y HORNO (C3)", expanded=False):
        c5a, c5b = st.columns(2)
        m_6c = c5a.number_input("Metros Cable 6mm² (C3)", value=30.0)
        p_6c = c5b.number_input("Precio/m 6mm² (Sugerido: 1.30)", value=db_precios["CABLES"]["6mm"], key="c5_6p")
        q_25a = c5a.number_input("Bases Cocina 25A", value=2)
        p_25a = c5b.number_input("Precio Base 25A (Sugerido: 7.10)", value=db_precios["MECANISMOS"]["Base 25A"])
        h_c3 = st.number_input("Horas Instalación C3", value=3.0)
        
        sub = (m_6c*p_6c + q_25a*p_25a + h_c3*p_of) * f_total
        capitulos_data.append(("CAPÍTULO V: CIRCUITO DE COCINA Y HORNO", sub))

    # CAP VI: LAVADORA/TERMO
    with st.expander("CAPÍTULO VI: CIRCUITO DE LAVADORA Y TERMO (C4)", expanded=False):
        c6a, c6b = st.columns(2)
        m_4c = c6a.number_input("Metros Cable 4mm² (C4)", value=85.0)
        p_4c = c6b.number_input("Precio/m 4mm² (Sugerido: 0.64)", value=db_precios["CABLES"]["4mm"])
        h_c4 = st.number_input("Horas Instalación C4", value=4.0)
        
        sub = (m_4c*p_4c + 3*db_precios["MECANISMOS"]["Base 16A"] + h_c4*p_of) * f_total
        capitulos_data.append(("CAPÍTULO VI: CIRCUITO DE LAVADORA Y TERMO", sub))

    # CAP VII: BAÑOS
    with st.expander("CAPÍTULO VII: CIRCUITO DE BAÑOS Y COCINA AUX (C5)", expanded=False):
        c7a, c7b = st.columns(2)
        m_25c = c7a.number_input("Metros Cable 2.5mm² (C5)", value=120.0)
        p_25c = c7b.number_input("Precio/m 2.5mm² (Sugerido: 0.38)", value=db_precios["CABLES"]["2.5mm"], key="c7_25p")
        h_c5 = st.number_input("Horas Instalación C5", value=5.0)
        
        sub = (m_25c*p_25c + 6*db_precios["MECANISMOS"]["Base 16A"] + h_c5*p_of) * f_total
        capitulos_data.append(("CAPÍTULO VII: CIRCUITO DE BAÑOS Y COCINA", sub))

    # CAP VIII: TELECOM/TIMBRE
    with st.expander("CAPÍTULO VIII: TELECOMUNICACIONES Y GESTIÓN", expanded=False):
        c8a, c8b = st.columns(2)
        q_rj = c8a.number_input("Tomas RJ45 Datos", value=4)
        p_rj = c8b.number_input("Precio RJ45 (Sugerido: 12.50)", value=db_precios["MECANISMOS"]["Tomas RJ45"])
        q_tv = c8a.number_input("Tomas TV/SAT", value=3)
        p_tv = c8b.number_input("Precio TV (Sugerido: 9.80)", value=db_precios["MECANISMOS"]["Toma TV/SAT"])
        q_z = c8a.number_input("Zumbador/Timbre", value=1)
        p_z = c8b.number_input("Precio Zumbador (Sugerido: 24.73)", value=db_precios["MECANISMOS"]["Zumbador"])
        
        st.write("#### Gestión y Certificación")
        cie_v = st.number_input("Certificado Instalación (Boletín)", value=150.0)
        h_c8 = st.number_input("Horas Telecom y Gestión", value=4.0)
        
        sub = (q_rj*p_rj + q_tv*p_tv + q_z*p_z + cie_v + h_c8*p_of) * f_total
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
