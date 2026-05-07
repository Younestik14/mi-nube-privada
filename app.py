import streamlit as st
import pandas as pd
import math
import io

# --- 1. CONFIGURACIÓN Y ESTILO DARK PROFESIONAL ---
st.set_page_config(page_title="Ingeniería Pro v3.0 - Full Suite", layout="wide", page_icon="⚡")

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
    <div class="footer-container"><span class="watermark-text">Younesse Tikent Tifaoui - Senior Technical Consultant</span></div>
    """,
    unsafe_allow_html=True
)

# --- FUNCIÓN DE EXPORTACIÓN ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Presupuesto')
    return output.getvalue()

# --- 2. MOTOR DE CÁLCULO REBT (MATRIZ UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
tablas_adm = {
    "A1 - Empotrado en tubo (Pared aislante)": {
        "PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321],
        "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]
    },
    "A2 - Multiconductor en tubo (Pared aislante)": {
        "PVC": [14, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291],
        "XLPE": [17.5, 24, 32, 41, 54, 73, 95, 117, 141, 179, 216, 249, 285, 324, 380]
    },
    "B1 - Conductores en tubo (Sobre pared)": {
        "PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400],
        "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]
    },
    "B2 - Multiconductor en tubo (Sobre pared)": {
        "PVC": [16.5, 23, 30, 38, 52, 69, 92, 114, 138, 175, 210, 244, 282, 319, 375],
        "XLPE": [21, 28, 38, 49, 66, 88, 117, 146, 175, 222, 269, 312, 358, 408, 481]
    },
    "C - Cable sobre pared de madera/mampostería": {
        "PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461],
        "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]
    },
    "D1 - Cable en conductos enterrados": {
        "PVC": [22, 29, 38, 47, 63, 81, 104, 125, 148, 183, 216, 246, 278, 312, 361],
        "XLPE": [26, 34, 44, 56, 73, 95, 121, 146, 173, 213, 252, 287, 324, 363, 419]
    },
    "E - Multiconductor al aire libre": {
        "PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286, 331, 381, 434, 511],
        "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352, 410, 473, 542, 641]
    },
    "F - Unipolares en contacto (Bandeja perforada)": {
        "PVC": [21, 28, 38, 50, 68, 92, 121, 150, 184, 233, 282, 327, 376, 428, 505],
        "XLPE": [25, 34, 46, 61, 83, 112, 146, 181, 221, 281, 341, 396, 455, 517, 613]
    }
}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    modo = st.radio("Módulo de Trabajo:", ["📐 Dimensionado REBT", "💰 Presupuesto Maestro"])
    st.divider()
    iva_tipo = st.selectbox("IVA Aplicable (%)", [21, 10, 4, 0], index=0)
    
    if modo == "💰 Presupuesto Maestro":
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. MÓDULO TÉCNICO ---
if modo == "📐 Dimensionado REBT":
    st.title("📐 Oficina Técnica: Cálculo de Líneas s/ REBT")
    c1, c2 = st.columns(2)
    with c1:
        sistema = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Cálculo (W)", value=5750, step=100)
        longitud = st.number_input("Longitud de la Línea (m)", value=30.0, step=1.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
    with c2:
        material = st.radio("Material Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Tipo de Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Instalación", list(tablas_adm.keys()))
        max_cdt = st.number_input("Caída de Tensión Máx (%)", value=3.0, step=0.1)

    # Cálculo Intensidad
    v_fase = 230 if "Mono" in sistema else 400
    ib = potencia / (v_fase * cos_phi) if v_fase == 230 else potencia / (math.sqrt(3) * v_fase * cos_phi)
    
    # Sección por Intensidad Admisible
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm[metodo_inst][ais_key]
    s_adm = secciones_ref[next((i for i, v in enumerate(intensidades) if v >= ib), -1)]
    
    st.divider()
    st.markdown(f'<div class="resultado-caja">SECCIÓN REGLAMENTARIA: {s_adm} mm²<br><small>Intensidad: {ib:.2f} A</small></div>', unsafe_allow_html=True)
    
    df_calc = pd.DataFrame({"Variable": ["Potencia", "Intensidad", "Sección"], "Valor": [f"{potencia} W", f"{ib:.2f} A", f"{s_adm} mm²"]})
    st.download_button("📥 Descargar Memoria (Excel)", to_excel(df_calc), "calculo_rebt.xlsx")

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Pro v5.0",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# ESTILO DARK PROFESIONAL
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: white;
}

label, .stMarkdown, p, span, div {
    color: white !important;
    font-weight: bold !important;
}

.resultado-caja {
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 24px;
    background-color: #1f2937;
    padding: 20px;
    border-radius: 12px;
    border-left: 8px solid #22d3ee;
    margin-bottom: 15px;
    text-align: right;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
}

.total-final-banner {
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 42px;
    background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
    padding: 50px;
    border-radius: 25px;
    text-align: center;
    border: 3px solid #ffd700;
    margin-top: 50px;
    box-shadow: 0px 20px 40px rgba(0,0,0,0.7);
}

.stExpander {
    border: 1px solid #374151 !important;
    border-radius: 15px !important;
    background-color: #161b22 !important;
    margin-bottom: 20px !important;
}

.footer-container {
    position: fixed;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    pointer-events: none;
    text-align: center;
    width: 100%;
}

.watermark-text {
    font-size: 12px;
    color: rgba(255,255,255,0.15);
}

</style>

<div class="footer-container">
<span class="watermark-text">
Younesse Tikent Tifaoui - Senior Technical Consultant
</span>
</div>
""", unsafe_allow_html=True)

# =========================================================
# EXPORTACIÓN EXCEL
# =========================================================

def exportar_excel(df, nombre_hoja="Presupuesto"):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name=nombre_hoja
        )

        workbook = writer.book
        worksheet = writer.sheets[nombre_hoja]

        formato_header = workbook.add_format({
            'bold': True,
            'bg_color': '#1f2937',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })

        formato_money = workbook.add_format({
            'num_format': '#,##0.00 €',
            'border': 1
        })

        formato_texto = workbook.add_format({
            'border': 1
        })

        for col_num, value in enumerate(df.columns.values):

            worksheet.write(
                0,
                col_num,
                value,
                formato_header
            )

        worksheet.set_column('A:A', 45, formato_texto)
        worksheet.set_column('B:B', 50, formato_texto)
        worksheet.set_column('C:Z', 20, formato_money)

    return output.getvalue()

# =========================================================
# CATÁLOGO PROFESIONAL COMPLETO
# =========================================================

catalogo_precios = {

    # =====================================================
    # CABLES
    # =====================================================

    "Cable 1.5 mm²": 0.32,
    "Cable 2.5 mm²": 0.48,
    "Cable 4 mm²": 0.75,
    "Cable 6 mm²": 1.45,
    "Cable 10 mm²": 2.60,
    "Cable 16 mm²": 4.10,
    "Cable 25 mm²": 6.50,
    "Cable 35 mm²": 9.20,

    # =====================================================
    # TUBOS Y CANALIZACIONES
    # =====================================================

    "Tubo Ø16mm": 0.45,
    "Tubo Ø20mm": 0.65,
    "Tubo Ø25mm": 0.85,
    "Tubo Ø32mm": 1.25,
    "Tubo Ø40mm": 2.10,
    "Tubo Ø50mm": 3.40,
    "Tubo Ø63mm": 4.80,

    "Canaleta PVC": 4.50,
    "Bandeja Perforada": 12.00,

    # =====================================================
    # MECANISMOS
    # =====================================================

    "Interruptor Simple": 4.20,
    "Interruptor Doble": 8.20,
    "Conmutador": 5.80,
    "Cruzamiento": 11.50,

    "Pulsador": 4.50,
    "Pulsador Luminoso": 8.50,

    "Base Enchufe 16A": 6.10,
    "Base Enchufe 25A": 14.50,
    "Base Schuko": 6.50,
    "Base Doble": 11.50,
    "Base Triple": 18.00,

    "Base USB": 18.00,
    "Base Estanca IP54": 18.50,

    "Toma TV": 9.50,
    "Toma SAT": 14.50,
    "Toma RJ45 Cat6": 18.00,
    "Toma Fibra": 22.00,

    "Detector Movimiento": 32.00,
    "Detector Presencia": 45.00,

    "Regulador Intensidad": 28.00,
    "Termostato Digital": 55.00,

    "Videoportero": 185.00,
    "Portero Electrónico": 95.00,

    "Zumbador": 18.00,

    # =====================================================
    # ILUMINACIÓN
    # =====================================================

    "Plafón LED": 32.00,
    "Downlight LED": 18.00,
    "Pantalla Estanca": 42.00,
    "Proyector LED": 68.00,
    "Luminaria Emergencia": 38.00,

    # =====================================================
    # PROTECCIONES
    # =====================================================

    "IGA 25A": 38.00,
    "IGA 40A": 48.00,
    "IGA 63A": 72.00,

    "PIA 6A": 8.00,
    "PIA 10A": 8.50,
    "PIA 16A": 9.20,
    "PIA 20A": 11.50,
    "PIA 25A": 14.00,
    "PIA 32A": 19.50,
    "PIA 40A": 25.00,
    "PIA 50A": 38.00,
    "PIA 63A": 52.00,

    "Diferencial 25A Clase AC": 42.00,
    "Diferencial 40A Clase AC": 52.00,
    "Diferencial 63A Clase AC": 75.00,

    "Diferencial 25A Clase A": 55.00,
    "Diferencial 40A Clase A": 65.00,
    "Diferencial 63A Clase A": 95.00,

    "Diferencial Superinmunizado": 145.00,
    "Diferencial Rearmable": 225.00,

    "Protector Sobretensiones Permanentes": 110.00,
    "Protector Sobretensiones Transitorias": 95.00,

    "ICP": 38.00,
    "Contactor Modular": 48.00,
    "Relé Temporizado": 42.00,
    "Guardamotor": 68.00,
    "Relé Térmico": 44.00,

    # =====================================================
    # CUADROS Y CAJAS
    # =====================================================

    "Caja Cuadro": 75.00,
    "Embarrado": 18.00,
    "Peines Conexión": 12.00,

    "Caja Registro": 4.50,
    "Caja Derivación": 5.20,
    "Caja Universal": 1.80,

    # =====================================================
    # TIERRA
    # =====================================================

    "Pica Tierra + Cable": 115.00,
    "Borne Tierra": 12.50,
    "Cable Tierra 16mm²": 3.20,

    # =====================================================
    # VEHÍCULO ELÉCTRICO
    # =====================================================

    "Wallbox 7.4kW": 680.00,
    "Wallbox 22kW": 1250.00,
    "Protección IRVE": 280.00,

    # =====================================================
    # FOTOVOLTAICA
    # =====================================================

    "Panel Solar": 210.00,
    "Inversor Solar": 1850.00,
    "Protección CC": 145.00,
    "Estructura Solar": 95.00,

    # =====================================================
    # DOMÓTICA
    # =====================================================

    "Actuador KNX": 145.00,
    "Fuente KNX": 185.00,
    "Pantalla Domótica": 420.00
}

# =========================================================
# CIRCUITOS REBT
# =========================================================

capitulos_config = {

    "DI": "DERIVACIÓN INDIVIDUAL",
    "CGMP": "CUADRO GENERAL DE MANDO Y PROTECCIÓN",

    "C1": "ILUMINACIÓN",
    "C2": "TOMAS DE USO GENERAL",
    "C3": "COCINA Y HORNO",
    "C4": "LAVADORA, LAVAVAJILLAS Y TERMO",
    "C5": "BAÑOS Y COCINA",

    "C6": "ILUMINACIÓN ADICIONAL",
    "C7": "TOMAS ADICIONALES",
    "C8": "CALEFACCIÓN",
    "C9": "AIRE ACONDICIONADO",
    "C10": "SECADORA",

    "C11": "DOMÓTICA",
    "C12": "AUXILIARES",

    "C13": "VEHÍCULO ELÉCTRICO",
    "C14": "FOTOVOLTAICA",

    "PAT": "PUESTA A TIERRA"
}

# =========================================================
# EXPLICACIONES
# =========================================================

explicaciones = {

    "DI": "Derivación individual desde contadores.",
    "CGMP": "Protecciones generales de vivienda.",

    "C1": "Circuito de iluminación.",
    "C2": "Bases de enchufe generales.",
    "C3": "Circuito cocina y horno.",
    "C4": "Lavadora y termo.",
    "C5": "Baños y cocina.",

    "C6": "Circuito iluminación extra.",
    "C7": "Tomas adicionales.",
    "C8": "Calefacción eléctrica.",
    "C9": "Climatización.",
    "C10": "Secadora.",

    "C11": "Automatización y domótica.",
    "C12": "Auxiliares.",

    "C13": "Recarga vehículo eléctrico.",
    "C14": "Sistema fotovoltaico.",

    "PAT": "Sistema de puesta a tierra."
}

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Configuración")

    gastos_generales = st.slider(
        "% Gastos Generales",
        0,
        30,
        13
    )

    beneficio = st.slider(
        "% Beneficio Industrial",
        0,
        20,
        6
    )

    iva_tipo = st.selectbox(
        "IVA (%)",
        [21, 10, 4, 0]
    )

    precio_oficial = st.number_input(
        "Oficial 1ª €/h",
        value=36.0
    )

    precio_ayudante = st.number_input(
        "Ayudante €/h",
        value=26.5
    )

    multiplicador = (
        1
        + gastos_generales / 100
        + beneficio / 100
    )

# =========================================================
# TÍTULO
# =========================================================

st.title("💰 Ingeniería Pro - Presupuesto Maestro REBT")

# =========================================================
# VARIABLES EXPORTACIÓN
# =========================================================

resumen_costes = []
capitulos_export = []
explicaciones_export = []

# =========================================================
# GENERADOR PRESUPUESTO
# =========================================================

for codigo, nombre in capitulos_config.items():

    with st.expander(f"🛠️ {codigo} - {nombre}"):

        st.info(explicaciones[codigo])

        seleccion = st.multiselect(
            f"Materiales {codigo}",
            list(catalogo_precios.keys()),
            key=f"sel_{codigo}"
        )

        coste_materiales = 0

        for item in seleccion:

            cantidad = st.number_input(
                f"Cantidad {item}",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"{codigo}_{item}"
            )

            subtotal = (
                cantidad *
                catalogo_precios[item]
            )

            coste_materiales += subtotal

        st.divider()

        c1, c2 = st.columns(2)

        horas_oficial = c1.number_input(
            "Horas Oficial",
            min_value=0.0,
            value=0.0,
            key=f"of_{codigo}"
        )

        horas_ayudante = c2.number_input(
            "Horas Ayudante",
            min_value=0.0,
            value=0.0,
            key=f"ay_{codigo}"
        )

        mano_obra = (
            horas_oficial * precio_oficial
            +
            horas_ayudante * precio_ayudante
        )

        total_capitulo = (
            coste_materiales
            + mano_obra
        ) * multiplicador

        st.markdown(f"""
        <div class="resultado-caja">
        {total_capitulo:,.2f} €
        </div>
        """, unsafe_allow_html=True)

        if total_capitulo > 0:

            resumen_costes.append(
                total_capitulo
            )

            capitulos_export.append(
                f"{codigo} - {nombre}"
            )

            explicaciones_export.append(
                explicaciones[codigo]
            )

# =========================================================
# TOTAL FINAL
# =========================================================

if resumen_costes:

    st.divider()

    total_base = sum(resumen_costes)

    iva_importe = (
        total_base *
        (iva_tipo / 100)
    )

    total_final = (
        total_base +
        iva_importe
    )

    st.markdown(f"""
    <div class="total-final-banner">

    PRESUPUESTO TOTAL

    <br>

    <span style="color:#ffd700">
    {total_final:,.2f} €
    </span>

    <br>

    <small>
    Base: {total_base:,.2f} €
    |
    IVA ({iva_tipo}%): {iva_importe:,.2f} €
    </small>

    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # DATAFRAME
    # =====================================================

    datos_export = []

    for i in range(len(capitulos_export)):

        base = resumen_costes[i]

        iva_cap = (
            base *
            (iva_tipo / 100)
        )

        total = (
            base +
            iva_cap
        )

        datos_export.append({

            "Capítulo": capitulos_export[i],

            "Descripción Técnica":
            explicaciones_export[i],

            "Base (€)": round(base, 2),

            "IVA (%)": iva_tipo,

            "IVA (€)": round(iva_cap, 2),

            "Total (€)": round(total, 2)
        })

    df_final = pd.DataFrame(datos_export)

    # =====================================================
    # DESCARGA CSV
    # =====================================================

    csv_data = df_final.to_csv(
        index=False,
        sep=';',
        encoding='utf-16'
    )

    st.download_button(
        "📥 Descargar CSV",
        csv_data,
        "presupuesto.csv",
        "text/csv",
        use_container_width=True
    )

    # =====================================================
    # DESCARGA EXCEL
    # =====================================================

    excel_data = exportar_excel(
        df_final,
        "Presupuesto"
    )

    st.download_button(
        "📊 Descargar Excel Profesional",
        excel_data,
        "presupuesto_profesional.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
