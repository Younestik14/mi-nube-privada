import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Ingeniería Pro - Presupuesto Maestro DTIE", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    /* Marca de agua pequeña y transparente */
    .footer-container {
        position: fixed;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        pointer-events: none;
        text-align: center;
        width: 100%;
        font-family: sans-serif;
    }

    .watermark-text {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.25); /* Muy transparente */
        font-weight: normal;
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
        <span class="watermark-text">Hecho por Younesse Tikent Tifaoui - Consultoría Técnica</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE PRECIOS UNITARIOS ---
db_precios = {
    "CABLES": {"1.5mm": 0.25, "2.5mm": 0.38, "4mm": 0.64, "6mm": 1.30, "10mm": 2.10},
    "PROTECCIONES": {"Cuadro 36 mod": 53.92, "IGA Combi": 56.20, "PIA 10A": 3.60, "PIA 16A": 9.31, "PIA 25A": 3.64},
    "MECANISMOS": {"Interruptor": 2.44, "Base 16A": 2.79, "Base 25A": 7.10, "Tomas RJ45": 12.50},
    "MANO OBRA": {"Oficial 1ª": 33.00, "Ayudante": 29.00}
}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Parámetros")
    modo = st.radio("Sección:", ["📐 Calculadora Técnica", "💰 Presupuesto Detallado"])
    
    if modo == "💰 Presupuesto Detallado":
        st.divider()
        p_ben = st.number_input("% Beneficio Industrial", 0, 100, 15)
        p_amo = st.number_input("% Gastos Generales", 0, 100, 5)
        p_iva = st.selectbox("Tipo de IVA (%)", [21, 10, 4, 0], index=0)
        f_total = 1 + (p_ben/100) + (p_amo/100)
    else:
        f_total = 1.0

# --- 4. CALCULADORA TÉCNICA ACTUALIZADA ---
if modo == "📐 Calculadora Técnica":
    st.title("📐 Cálculo de Secciones s/ REBT")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parámetros Eléctricos")
        red = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        P = st.number_input("Potencia Instalar (W)", value=5750)
        L = st.number_input("Longitud (m)", value=25.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
        k_rec = st.selectbox("Uso / Factor de Recargo", ["General (1.0)", "Motores (1.25)", "Lámparas de Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        
        # Lógica de recargo según uso
        k = 1.25 if ("Motores" in k_rec or "Vehículo" in k_rec) else (1.8 if "Descarga" in k_rec else 1.0)
    
    with col2:
        st.subheader("Entorno e Instalación")
        mat = st.radio("Material Conductor", ["Cobre", "Aluminio"], horizontal=True)
        ais = st.radio("Aislamiento", ["PVC (70°C)", "XLPE (90°C)"], horizontal=True)
        metodos_rebt = [
            "A1 - Empotrado en tubo (pared aislante)", "B1 - Superficie en tubo (pared madera)",
            "C - Directo bajo pared", "E - Aire libre", "D - Enterrado bajo tubo"
        ]
        met = st.selectbox("Método de Instalación", metodos_rebt)
        caida = st.number_input("Caída de Tensión Máx (%)", value=3.0)

    # Cálculos
    V = 230 if "Mono" in red else 400
    Ib = (P * k) / (V * cos_phi) if V == 230 else (P * k) / (1.732 * V * cos_phi)
    gamma = (48 if "PVC" in ais else 44) if mat == "Cobre" else (30 if "PVC" in ais else 28)
    
    # Sección por Caída de Tensión
    S_cdt = (2 if V == 230 else 1) * L * (P/V if V==230 else Ib) * cos_phi / (gamma * (caida/100*V))
    
    # Normalización de sección (Valores comerciales)
    secciones_comerciales = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
    S_norm = next((s for s in secciones_comerciales if s >= S_cdt), 240)

    st.divider()
    c_r1, c_r2, c_r3 = st.columns(3)
    c_r1.metric("Intensidad (Ib)", f"{Ib:.2f} A")
    c_r2.metric("Sección Calculada", f"{S_cdt:.2f} mm²")
    c_r3.subheader(f"✅ Sección Normalizada: {S_norm} mm²")

# --- 5. PRESUPUESTO CON MANO DE OBRA EN CADA CAPÍTULO ---
else:
    st.title("💰 Presupuesto Técnico Detallado")
    capitulos_data = []

    def bloque_mano_obra(key_prefix):
        c_mo1, c_mo2 = st.columns(2)
        h_of = c_mo1.number_input(f"Horas Oficial 1ª", value=2.0, key=f"h_of_{key_prefix}")
        p_of = c_mo2.number_input(f"Precio/h Oficial (€)", value=db_precios["MANO OBRA"]["Oficial 1ª"], key=f"p_of_{key_prefix}")
        h_ay = c_mo1.number_input(f"Horas Ayudante", value=1.0, key=f"h_ay_{key_prefix}")
        p_ay = c_mo2.number_input(f"Precio/h Ayudante (€)", value=db_precios["MANO OBRA"]["Ayudante"], key=f"p_ay_{key_prefix}")
        return (h_of * p_of) + (h_ay * p_ay)

    # CAP I
    with st.expander("CAPÍTULO I: DERIVACIÓN INDIVIDUAL"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Metros Cable 6mm²", value=48.0) * c2.number_input("Precio/m 6mm²", value=1.30)
        coste_mo = bloque_mano_obra("cap1")
        capitulos_data.append(("CAP I: DERIVACIÓN INDIVIDUAL", (coste_mat + coste_mo) * f_total))

    # CAP II
    with st.expander("CAPÍTULO II: CUADRO DE PROTECCIÓN"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Ud. Cuadro + Protecciones", value=1) * c2.number_input("P.U. Conjunto Cuadro", value=180.0)
        coste_mo = bloque_mano_obra("cap2")
        capitulos_data.append(("CAP II: CUADRO DE PROTECCIÓN", (coste_mat + coste_mo) * f_total))

    # CAP III
    with st.expander("CAPÍTULO III: ILUMINACIÓN (C1)"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Puntos de Luz", value=10) * c2.number_input("Coste Material/Punto", value=15.0)
        coste_mo = bloque_mano_obra("cap3")
        capitulos_data.append(("CAP III: ILUMINACIÓN", (coste_mat + coste_mo) * f_total))

    # CAP IV
    with st.expander("CAPÍTULO IV: TOMAS DE USO GENERAL (C2)"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Ud. Tomas 16A", value=18) * c2.number_input("P.U. Mecanismo+Caja", value=8.5)
        coste_mo = bloque_mano_obra("cap4")
        capitulos_data.append(("CAP IV: TOMAS USO GENERAL", (coste_mat + coste_mo) * f_total))

    # CAP V
    with st.expander("CAPÍTULO V: COCINA Y HORNO (C3)"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Línea Reforzada 6mm² (m)", value=15.0) * c2.number_input("P.U. Línea Cocina", value=2.5)
        coste_mo = bloque_mano_obra("cap5")
        capitulos_data.append(("CAP V: COCINA Y HORNO", (coste_mat + coste_mo) * f_total))

    # CAP VI
    with st.expander("CAPÍTULO VI: LAVADORA Y TERMO (C4)"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Línea 4mm² (m)", value=20.0) * c2.number_input("P.U. Línea C4", value=1.8)
        coste_mo = bloque_mano_obra("cap6")
        capitulos_data.append(("CAP VI: LAVADORA Y TERMO", (coste_mat + coste_mo) * f_total))

    # CAP VII
    with st.expander("CAPÍTULO VII: BAÑOS Y COCINA (C5)"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Ud. Tomas Humedas", value=6) * c2.number_input("P.U. C5", value=9.0)
        coste_mo = bloque_mano_obra("cap7")
        capitulos_data.append(("CAP VII: BAÑOS Y COCINA", (coste_mat + coste_mo) * f_total))

    # CAP VIII
    with st.expander("CAPÍTULO VIII: TELECOM Y GESTIÓN"):
        c1, c2 = st.columns(2)
        coste_mat = c1.number_input("Ud. Tomas RJ45/TV", value=5) * c2.number_input("P.U. Telecom", value=22.0)
        coste_mo = bloque_mano_obra("cap8")
        capitulos_data.append(("CAP VIII: TELECOM Y GESTIÓN", (coste_mat + coste_mo) * f_total))

    # --- DESGLOSE FINAL ---
    st.divider()
    st.subheader("📊 RESUMEN ECONÓMICO")
    total_neto = 0
    for nombre, importe in capitulos_data:
        r1, r2 = st.columns([3, 1])
        r1.write(f"**{nombre}**")
        r2.markdown(f'<div class="resultado-negro">{importe:,.2f} €</div>', unsafe_allow_html=True)
        total_neto += importe
    
    total_con_iva = total_neto * (1 + p_iva/100)
    st.markdown(f'<div class="total-final">PRESUPUESTO TOTAL (IVA {p_iva}% INC.): {total_con_iva:,.2f} €</div>', unsafe_allow_html=True)
