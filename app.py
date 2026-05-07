import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Ingeniería Pro v3.0", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    
    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 24px;
        background-color: #1f2937; padding: 20px; border-radius: 12px;
        border-left: 8px solid #22d3ee; margin-bottom: 15px; text-align: right;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }

    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 42px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
        padding: 50px; border-radius: 25px; text-align: center;
        border: 3px solid #ffd700; margin-top: 50px;
        box-shadow: 0px 20px 40px rgba(0,0,0,0.7);
    }

    .stExpander { 
        border: 1px solid #374151 !important; border-radius: 15px !important; 
        background-color: #161b22 !important; margin-bottom: 20px !important;
    }

    .footer-container {
        position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%;
    }
    .watermark-text { font-size: 12px; color: rgba(255, 255, 255, 0.15); }
    </style>
    <div class="footer-container"><span class="watermark-text">Desarrollado por Oficina Técnica Pro - 2026</span></div>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE DATOS TÉCNICA (REBT / UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

tablas_adm = {
    "B1 - Conductores en tubo (Sobre pared)": {
        "PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400],
        "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]
    },
    "C - Cable bajo mampostería": {
        "PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461],
        "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]
    }
}

def get_seccion_adm(metodo_key, aislamiento, ib):
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm.get(metodo_key, tablas_adm["C - Cable bajo mampostería"])[ais_key]
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib: return secciones_ref[i]
    return 240

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    modo = st.radio("Módulo:", ["📐 Dimensionado REBT", "💰 Presupuesto Maestro"])
    
    if modo == "💰 Presupuesto Maestro":
        st.divider()
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA Aplicable (%)", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. MÓDULO CÁLCULO ---
if modo == "📐 Dimensionado REBT":
    st.title("📐 Oficina Técnica: Cálculo de Líneas")
    c1, c2 = st.columns(2)
    with c1:
        sistema = st.selectbox("Sistema", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia (W)", value=5750)
        longitud = st.number_input("Longitud (m)", value=25.0)
    with c2:
        material = st.radio("Material", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Instalación", list(tablas_adm.keys()))
        max_cdt = st.number_input("Caída de Tensión Máx (%)", value=3.0)

    v_fase = 230 if "Mono" in sistema else 400
    ib = potencia / (v_fase if v_fase == 230 else 1.732 * v_fase)
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    
    gamma = (48 if "PVC" in aislamiento else 44) if "Cobre" in material else (30 if "PVC" in aislamiento else 28)
    s_cdt = (2 * longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase) if v_fase == 230 else (longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)
    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)
    s_final = max(s_adm, s_cdt_norm)

    st.divider()
    st.markdown(f'<div class="resultado-caja">SECCIÓN REGLAMENTARIA: {s_final} mm²<br><small style="font-size:14px;">Ib: {ib:.2f} A | S(térmica): {s_adm}mm² | S(CdT): {s_cdt:.2f}mm²</small></div>', unsafe_allow_html=True)

# --- 5. MÓDULO PRESUPUESTO ---
else:
    st.title("💰 Gestor de Presupuestos Detallado")
    
    # Precios y Catálogo
    catalogo = {
        "Cable 1.5mm²": 0.38, "Cable 2.5mm²": 0.58, "Cable 6mm²": 1.65, "Cable 10mm²": 2.80,
        "PIA 10A": 8.90, "PIA 16A": 9.50, "PIA 25A": 14.80, "PIA 40A": 22.00,
        "Dif. 40A Clase A": 62.00, "IGA+Sobretensiones": 115.00,
        "Base Enchufe 16A": 6.80, "Base Enchufe 25A": 15.20, "Tubo Ø20mm": 0.68, "Tubo Ø32mm": 1.35
    }

    explicaciones = {
        "DI": "Enlace desde centralización de contadores hasta el CGMP.",
        "CGMP": "Cuadro con protecciones magnetotérmicas y diferenciales.",
        "C1": "Iluminación general (máx 30 puntos). Cable 1.5mm².",
        "C2": "Tomas de uso general y frigorífico. Cable 2.5mm².",
        "C3": "Cocina y horno. Cable 6mm².",
        "C4": "Lavadora, lavavajillas y termo. Cable 4mm².",
        "C5": "Tomas en baños y encimera de cocina. Cable 2.5mm².",
        "C13": "Infraestructura de Recarga de Vehículo Eléctrico (ITC-BT-52).",
        "PAT": "Instalación de toma de tierra y conductor de protección."
    }

    capitulos = {
        "DI": "DERIVACIÓN INDIVIDUAL", "CGMP": "CUADRO GENERAL", "C1": "ILUMINACIÓN",
        "C2": "TOMAS GENERALES", "C3": "COCINA Y HORNO", "C4": "LAVADORA/TERMO",
        "C5": "BAÑOS Y COCINA", "C13": "VEHÍCULO ELÉCTRICO (IRVE)", "PAT": "PUESTA A TIERRA"
    }

    data_presupuesto = []

    for code, name in capitulos.items():
        with st.expander(f"🛠️ {code}: {name}"):
            st.info(f"**Definición REBT:** {explicaciones[code]}")
            c_sel, c_q = st.columns([3, 1])
            seleccion = c_sel.multiselect("Materiales:", list(catalogo.keys()), key=f"sel_{code}")
            
            coste_mat = 0
            materiales_str = []
            for item in seleccion:
                cant = c_q.number_input(f"Uds {item}", 0.0, 500.0, 1.0, key=f"q_{code}_{item}")
                parcial = cant * catalogo[item]
                coste_mat += parcial
                materiales_str.append(f"{item} (x{cant})")

            h_of = st.number_input("Horas Oficial 1ª (36€/h)", 0.0, 200.0, 0.0, key=f"h_{code}")
            total_cap = (coste_mat + (h_of * 36)) * f_multiplicador
            
            st.markdown(f'<div class="resultado-caja">{total_cap:,.2f} €</div>', unsafe_allow_html=True)
            
            if total_cap > 0:
                data_presupuesto.append({
                    "Código": code,
                    "Capítulo": name,
                    "Descripción Normativa": explicaciones[code],
                    "Desglose Materiales": ", ".join(materiales_str),
                    "Mano de Obra (h)": h_of,
                    "Coste Total (€)": round(total_cap, 2)
                })

    if data_presupuesto:
        st.divider()
        df = pd.DataFrame(data_presupuesto)
        total_neto = df["Coste Total (€)"].sum()
        iva = total_neto * (iva_tipo/100)
        
        st.markdown(f'<div class="total-final-banner">PRESUPUESTO TOTAL: {(total_neto + iva):,.2f} €</div>', unsafe_allow_html=True)

        # EXPORTACIÓN DETALLADA
        csv_data = df.to_csv(index=False, sep=';', encoding='utf-16')
        st.download_button(
            label="📥 Descargar Presupuesto Detallado para Excel",
            data=csv_data,
            file_name='Presupuesto_REBT_Detallado.csv',
            mime='text/csv',
        )
