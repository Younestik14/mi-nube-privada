# =========================================================
# MÓDULO COMPLETO DIMENSIONADO REBT
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN PÁGINA
# =========================================================

st.set_page_config(
    page_title="Cálculo de Secciones REBT",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# ESTILO VISUAL
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
    font-size: 26px;
    background-color: #1f2937;
    padding: 25px;
    border-radius: 15px;
    border-left: 10px solid #22d3ee;
    margin-bottom: 20px;
    text-align: right;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.6);
}

.stNumberInput input,
.stSelectbox div {
    background-color: #0d1117 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIÓN EXPORTACIÓN EXCEL
# =========================================================

def exportar_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name='Memoria_Calculo'
        )

        workbook = writer.book
        worksheet = writer.sheets['Memoria_Calculo']

        formato_header = workbook.add_format({
            'bold': True,
            'bg_color': '#1f2937',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
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

        worksheet.set_column(
            'A:Z',
            35,
            formato_texto
        )

    return output.getvalue()

# =========================================================
# SECCIONES NORMALIZADAS
# =========================================================

secciones_ref = [
    1.5, 2.5, 4, 6, 10,
    16, 25, 35, 50, 70,
    95, 120, 150, 185, 240
]

# =========================================================
# TABLAS INTENSIDADES ADMISIBLES
# UNE-HD 60364-5-52
# =========================================================

tablas_adm = {

    "A1 - Empotrado en tubo (pared aislante)": {

        "PVC": [
            14.5, 19.5, 26, 34, 46,
            61, 80, 99, 119, 151,
            182, 210, 240, 273, 321
        ],

        "XLPE": [
            18.5, 25, 33, 43, 59,
            77, 102, 126, 153, 194,
            233, 268, 307, 352, 415
        ]
    },

    "B1 - Conductores en tubo sobre pared": {

        "PVC": [
            17.5, 24, 32, 41, 57,
            76, 101, 125, 151, 192,
            232, 269, 300, 341, 400
        ],

        "XLPE": [
            22, 30, 40, 52, 71,
            94, 126, 157, 190, 241,
            292, 338, 388, 442, 523
        ]
    },

    "C - Cable sobre pared": {

        "PVC": [
            19.5, 27, 36, 46, 63,
            85, 112, 138, 168, 213,
            258, 299, 344, 391, 461
        ],

        "XLPE": [
            24, 33, 45, 58, 80,
            107, 138, 171, 209, 269,
            328, 382, 441, 506, 599
        ]
    },

    "D1 - Conductos enterrados": {

        "PVC": [
            22, 29, 38, 47, 63,
            81, 104, 125, 148, 183,
            216, 246, 278, 312, 361
        ],

        "XLPE": [
            26, 34, 44, 56, 73,
            95, 121, 146, 173, 213,
            252, 287, 324, 363, 419
        ]
    },

    "E - Multiconductor al aire": {

        "PVC": [
            22, 30, 40, 51, 70,
            94, 126, 154, 187, 237,
            286, 331, 381, 434, 511
        ],

        "XLPE": [
            26, 36, 49, 63, 86,
            115, 149, 185, 225, 289,
            352, 410, 473, 542, 641
        ]
    },

    "F - Bandeja perforada": {

        "PVC": [
            21, 28, 38, 50, 68,
            92, 121, 150, 184, 233,
            282, 327, 376, 428, 505
        ],

        "XLPE": [
            25, 34, 46, 61, 83,
            112, 146, 181, 221, 281,
            341, 396, 455, 517, 613
        ]
    }
}

# =========================================================
# FUNCIÓN SECCIÓN POR INTENSIDAD
# =========================================================

def get_seccion_adm(
    metodo,
    aislamiento,
    ib
):

    ais_key = (
        "PVC"
        if "PVC" in aislamiento
        else "XLPE"
    )

    intensidades = tablas_adm[
        metodo
    ][ais_key]

    for i, intensidad in enumerate(intensidades):

        if intensidad >= ib:

            return secciones_ref[i]

    return 240

# =========================================================
# TÍTULO
# =========================================================

st.title("📐 Oficina Técnica - Cálculo de Secciones REBT")

# =========================================================
# COLUMNAS
# =========================================================

c1, c2 = st.columns(2)

# =========================================================
# DATOS CARGA
# =========================================================

with c1:

    st.subheader("⚡ Datos Eléctricos")

    sistema = st.selectbox(
        "Sistema Eléctrico",
        [
            "Monofásico 230V",
            "Trifásico 400V"
        ]
    )

    potencia = st.number_input(
        "Potencia de cálculo (W)",
        value=5750.0,
        step=100.0
    )

    longitud = st.number_input(
        "Longitud línea (m)",
        value=30.0,
        step=1.0
    )

    cos_phi = st.slider(
        "Factor potencia (cos φ)",
        0.70,
        1.00,
        0.90
    )

    factor_uso = st.selectbox(
        "Factor de uso",
        [
            "General (1.0)",
            "Motores (1.25)",
            "Lámparas descarga (1.8)",
            "Vehículo eléctrico (1.25)"
        ]
    )

# =========================================================
# PARÁMETROS INSTALACIÓN
# =========================================================

with c2:

    st.subheader("🛠️ Instalación")

    material = st.radio(
        "Material conductor",
        [
            "Cobre (Cu)",
            "Aluminio (Al)"
        ]
    )

    aislamiento = st.radio(
        "Aislamiento",
        [
            "PVC (70°C)",
            "XLPE/EPR (90°C)"
        ]
    )

    metodo = st.selectbox(
        "Método instalación",
        list(tablas_adm.keys())
    )

    max_cdt = st.number_input(
        "Caída tensión máxima (%)",
        value=3.0,
        step=0.1
    )

    temperatura = st.number_input(
        "Temperatura ambiente (°C)",
        value=30
    )

# =========================================================
# FACTOR UTILIZACIÓN
# =========================================================

if "Motores" in factor_uso:

    k_u = 1.25

elif "Vehículo" in factor_uso:

    k_u = 1.25

elif "Lámparas" in factor_uso:

    k_u = 1.8

else:

    k_u = 1.0

# =========================================================
# TENSIÓN
# =========================================================

v_fase = (
    230
    if "Mono" in sistema
    else 400
)

# =========================================================
# INTENSIDAD
# =========================================================

if v_fase == 230:

    ib = (
        potencia * k_u
    ) / (
        v_fase * cos_phi
    )

else:

    ib = (
        potencia * k_u
    ) / (
        1.732 *
        v_fase *
        cos_phi
    )

# =========================================================
# SECCIÓN POR INTENSIDAD
# =========================================================

s_adm = get_seccion_adm(
    metodo,
    aislamiento,
    ib
)

# =========================================================
# CONDUCTIVIDAD
# =========================================================

if "Cobre" in material:

    gamma = (
        48
        if "PVC" in aislamiento
        else 44
    )

else:

    gamma = (
        30
        if "PVC" in aislamiento
        else 28
    )

# =========================================================
# CÁLCULO Caída tensión
# =========================================================

if v_fase == 230:

    s_cdt = (

        2 *
        longitud *
        potencia

    ) / (

        gamma *
        (
            max_cdt / 100 *
            v_fase
        ) *
        v_fase
    )

else:

    s_cdt = (

        longitud *
        potencia

    ) / (

        gamma *
        (
            max_cdt / 100 *
            v_fase
        ) *
        v_fase
    )

# =========================================================
# NORMALIZACIÓN SECCIÓN
# =========================================================

s_cdt_norm = next(
    (
        s for s in secciones_ref
        if s >= s_cdt
    ),
    240
)

# =========================================================
# SECCIÓN FINAL
# =========================================================

s_final = max(
    s_adm,
    s_cdt_norm
)

# =========================================================
# RESULTADOS
# =========================================================

st.divider()

st.markdown(f"""
<div class="resultado-caja">

SECCIÓN REGLAMENTARIA:
{s_final} mm²

<br>

<small style="font-size:15px;">

Ib = {ib:.2f} A

|

Térmico = {s_adm} mm²

|

CdT = {s_cdt:.2f} mm²

</small>

</div>
""", unsafe_allow_html=True)

# =========================================================
# TABLA RESULTADOS
# =========================================================

df_resultados = pd.DataFrame({

    "Parámetro": [

        "Sistema",
        "Potencia (W)",
        "Longitud (m)",
        "cos φ",
        "Material",
        "Aislamiento",
        "Método instalación",
        "Temperatura ambiente",
        "Intensidad Ib (A)",
        "Sección térmica (mm²)",
        "Sección CdT (mm²)",
        "SECCIÓN FINAL (mm²)"
    ],

    "Valor": [

        sistema,
        potencia,
        longitud,
        cos_phi,
        material,
        aislamiento,
        metodo,
        temperatura,
        round(ib, 2),
        s_adm,
        round(s_cdt, 2),
        s_final
    ]
})

# =========================================================
# MOSTRAR TABLA
# =========================================================

st.dataframe(
    df_resultados,
    use_container_width=True
)

# =========================================================
# EXPORTAR EXCEL
# =========================================================

excel_data = exportar_excel(
    df_resultados
)

st.download_button(

    "📥 Descargar Memoria de Cálculo Excel",

    excel_data,

    "memoria_calculo_rebt.xlsx",

    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    use_container_width=True
# =========================================================
# =========================================================
#  PRESUPUESTO MAESTRO REBT PROFESIONAL
#  CONTINUACIÓN DEL MÓDULO DE SECCIONES
# =========================================================
# =========================================================

# =========================================================
# SIDEBAR PRESUPUESTO
# =========================================================

with st.sidebar:

    st.divider()

    st.header("💰 Configuración Económica")

    gastos_generales = st.slider(
        "% Gastos Generales",
        0,
        30,
        13
    )

    beneficio_industrial = st.slider(
        "% Beneficio Industrial",
        0,
        20,
        6
    )

    iva_tipo = st.selectbox(
        "IVA Aplicable (%)",
        [21, 10, 4, 0],
        index=0
    )

    precio_oficial = st.number_input(
        "Oficial 1ª (€/h)",
        20.0,
        80.0,
        36.0
    )

    precio_ayudante = st.number_input(
        "Ayudante (€/h)",
        15.0,
        60.0,
        26.5
    )

    multiplicador = (
        1
        + gastos_generales / 100
        + beneficio_industrial / 100
    )

# =========================================================
# TÍTULO
# =========================================================

st.divider()

st.title("💰 Gestor Profesional de Presupuestos REBT")

# =========================================================
# CATÁLOGO COMPLETO
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
    "Cable 50 mm²": 13.50,
    "Cable 70 mm²": 18.00,

    # =====================================================
    # TUBOS
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
    "Bandeja Rejilla": 16.00,

    # =====================================================
    # MECANISMOS
    # =====================================================

    "Interruptor Simple": 4.20,
    "Interruptor Doble": 8.50,
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
    # CUADROS
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
# CAPÍTULOS REBT
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

    "C13": "RECARGA VEHÍCULO ELÉCTRICO",
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

    "C6": "Circuito iluminación adicional.",
    "C7": "Circuito adicional tomas.",
    "C8": "Circuito calefacción.",
    "C9": "Circuito climatización.",
    "C10": "Circuito secadora.",

    "C11": "Automatización y domótica.",
    "C12": "Servicios auxiliares.",

    "C13": "Recarga vehículo eléctrico.",
    "C14": "Sistema fotovoltaico.",

    "PAT": "Sistema de puesta a tierra."
}

# =========================================================
# VARIABLES EXPORTACIÓN
# =========================================================

datos_export = []

# =========================================================
# CAPÍTULOS
# =========================================================

for codigo, nombre in capitulos_config.items():

    with st.expander(f"🛠️ {codigo} - {nombre}"):

        st.info(explicaciones[codigo])

        materiales = st.multiselect(

            f"Materiales {codigo}",

            list(catalogo_precios.keys()),

            key=f"sel_{codigo}"
        )

        coste_materiales = 0

        detalle_materiales = []

        for item in materiales:

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

            detalle_materiales.append({

                "Capítulo": codigo,
                "Elemento": item,
                "Cantidad": cantidad,
                "Precio Unitario (€)": catalogo_precios[item],
                "Subtotal (€)": round(subtotal, 2)
            })

        st.divider()

        col1, col2 = st.columns(2)

        horas_oficial = col1.number_input(

            "Horas Oficial",

            min_value=0.0,

            value=0.0,

            key=f"of_{codigo}"
        )

        horas_ayudante = col2.number_input(

            "Horas Ayudante",

            min_value=0.0,

            value=0.0,

            key=f"ay_{codigo}"
        )

        mano_obra = (

            horas_oficial *
            precio_oficial

            +

            horas_ayudante *
            precio_ayudante
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

            datos_export.append({

                "Capítulo":
                f"{codigo} - {nombre}",

                "Descripción":
                explicaciones[codigo],

                "Materiales (€)":
                round(coste_materiales, 2),

                "Mano de Obra (€)":
                round(mano_obra, 2),

                "GG + BI":
                f"{gastos_generales + beneficio_industrial}%",

                "Base (€)":
                round(total_capitulo, 2),

                "IVA (%)":
                iva_tipo,

                "IVA (€)":
                round(
                    total_capitulo *
                    iva_tipo / 100,
                    2
                ),

                "TOTAL (€)":
                round(
                    total_capitulo *
                    (1 + iva_tipo / 100),
                    2
                )
            })

# =========================================================
# TOTAL FINAL
# =========================================================

if len(datos_export) > 0:

    st.divider()

    df_presupuesto = pd.DataFrame(datos_export)

    total_base = df_presupuesto["Base (€)"].sum()

    total_iva = df_presupuesto["IVA (€)"].sum()

    total_final = df_presupuesto["TOTAL (€)"].sum()

    st.markdown(f"""
    <div class="total-final-banner">

    PRESUPUESTO TOTAL EJECUCIÓN

    <br>

    <span style="color:#ffd700">
    {total_final:,.2f} €
    </span>

    <br>

    <small>

    Base:
    {total_base:,.2f} €

    |

    IVA:
    {total_iva:,.2f} €

    </small>

    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # MOSTRAR TABLA
    # =====================================================

    st.dataframe(
        df_presupuesto,
        use_container_width=True
    )

    # =====================================================
    # EXPORTACIÓN EXCEL
    # =====================================================

    excel_presupuesto = exportar_excel(
        df_presupuesto
    )

    st.download_button(

        "📊 Descargar Presupuesto Profesional Excel",

        excel_presupuesto,

        "presupuesto_profesional.xlsx",

        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

        use_container_width=True
    )

    # =====================================================
    # EXPORTACIÓN CSV
    # =====================================================

    csv_presupuesto = df_presupuesto.to_csv(

        index=False,
        sep=';',
        encoding='utf-16'
    )

    st.download_button(

        "📥 Descargar Presupuesto CSV",

        csv_presupuesto,

        "presupuesto_profesional.csv",

        "text/csv",

        use_container_width=True
    )
