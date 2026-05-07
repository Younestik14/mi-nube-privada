# =========================================================
# INGENIERÍA PRO v6.0
# CÁLCULO DE SECCIONES + PRESUPUESTOS REBT
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Pro v6.0",
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

.stNumberInput input,
.stSelectbox div {
    background-color: #0d1117 !important;
    color: white !important;
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
# FUNCIÓN EXPORTACIÓN EXCEL
# =========================================================

def exportar_excel(df, hoja="Datos"):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name=hoja
        )

        workbook = writer.book
        worksheet = writer.sheets[hoja]

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

        formato_money = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00 €'
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
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Configuración")

    modo = st.radio(

        "Módulo",

        [
            "📐 Cálculo de Secciones",
            "💰 Presupuesto Maestro"
        ]
    )

# =========================================================
# =========================================================
# MÓDULO CÁLCULO DE SECCIONES
# =========================================================
# =========================================================

if modo == "📐 Cálculo de Secciones":

    # =====================================================
    # SECCIONES NORMALIZADAS
    # =====================================================

    secciones_ref = [

        1.5, 2.5, 4, 6, 10,
        16, 25, 35, 50, 70,
        95, 120, 150, 185, 240
    ]

    # =====================================================
    # TABLAS REBT
    # =====================================================

    tablas_adm = {

        "A1 - Empotrado en tubo": {

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

        "B1 - Tubo sobre pared": {

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
        }
    }

    # =====================================================
    # FUNCIÓN
    # =====================================================

    def get_seccion_adm(
        metodo,
        aislamiento,
        ib
    ):

        ais = (
            "PVC"
            if "PVC" in aislamiento
            else "XLPE"
        )

        intensidades = tablas_adm[metodo][ais]

        for i, intensidad in enumerate(intensidades):

            if intensidad >= ib:

                return secciones_ref[i]

        return 240

    # =====================================================
    # TÍTULO
    # =====================================================

    st.title("📐 Oficina Técnica - Cálculo de Secciones")

    c1, c2 = st.columns(2)

    # =====================================================
    # DATOS
    # =====================================================

    with c1:

        sistema = st.selectbox(
            "Sistema",
            [
                "Monofásico 230V",
                "Trifásico 400V"
            ]
        )

        potencia = st.number_input(
            "Potencia (W)",
            value=5750.0
        )

        longitud = st.number_input(
            "Longitud (m)",
            value=30.0
        )

        cos_phi = st.slider(
            "cos φ",
            0.70,
            1.00,
            0.90
        )

        uso = st.selectbox(
            "Tipo uso",
            [
                "General",
                "Motores",
                "Vehículo eléctrico"
            ]
        )

    with c2:

        material = st.radio(
            "Material",
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
            "CdT máxima (%)",
            value=3.0
        )

    # =====================================================
    # FACTORES
    # =====================================================

    if uso == "Motores":

        k_u = 1.25

    elif uso == "Vehículo eléctrico":

        k_u = 1.25

    else:

        k_u = 1.0

    v_fase = (
        230
        if "Mono" in sistema
        else 400
    )

    # =====================================================
    # INTENSIDAD
    # =====================================================

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

    # =====================================================
    # SECCIÓN TÉRMICA
    # =====================================================

    s_adm = get_seccion_adm(
        metodo,
        aislamiento,
        ib
    )

    # =====================================================
    # CONDUCTIVIDAD
    # =====================================================

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

    # =====================================================
    # CdT
    # =====================================================

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

    s_cdt_norm = next(

        (
            s for s in secciones_ref
            if s >= s_cdt
        ),

        240
    )

    s_final = max(
        s_adm,
        s_cdt_norm
    )

    # =====================================================
    # RESULTADO
    # =====================================================

    st.divider()

    st.markdown(f"""
    <div class="resultado-caja">

    SECCIÓN FINAL:
    {s_final} mm²

    <br>

    <small>

    Ib = {ib:.2f} A

    |

    Térmica = {s_adm} mm²

    |

    CdT = {s_cdt:.2f} mm²

    </small>

    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # TABLA
    # =====================================================

    df_calc = pd.DataFrame({

        "Parámetro": [

            "Sistema",
            "Potencia",
            "Longitud",
            "cos φ",
            "Material",
            "Aislamiento",
            "Método",
            "Ib",
            "Sección térmica",
            "Sección CdT",
            "SECCIÓN FINAL"
        ],

        "Valor": [

            sistema,
            potencia,
            longitud,
            cos_phi,
            material,
            aislamiento,
            metodo,
            round(ib, 2),
            s_adm,
            round(s_cdt, 2),
            s_final
        ]
    })

    st.dataframe(
        df_calc,
        use_container_width=True
    )

    # =====================================================
    # EXPORTACIÓN
    # =====================================================

    excel_calc = exportar_excel(
        df_calc,
        "Memoria_Calculo"
    )

    st.download_button(

        "📥 Descargar Memoria Excel",

        excel_calc,

        "memoria_calculo.xlsx",

        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

        use_container_width=True
    )

# =========================================================
# =========================================================
# MÓDULO PRESUPUESTO
# =========================================================
# =========================================================

else:

    # =====================================================
    # CONFIGURACIÓN ECONÓMICA
    # =====================================================

    with st.sidebar:

        st.divider()

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
            + beneficio_industrial / 100
        )

    # =====================================================
    # TÍTULO
    # =====================================================

    st.title("💰 Presupuesto Maestro REBT")

    # =====================================================
    # CATÁLOGO
    # =====================================================

    catalogo_precios = {

        "Cable 1.5 mm²": 0.32,
        "Cable 2.5 mm²": 0.48,
        "Cable 4 mm²": 0.75,
        "Cable 6 mm²": 1.45,
        "Cable 10 mm²": 2.60,

        "Tubo Ø16mm": 0.45,
        "Tubo Ø20mm": 0.65,
        "Tubo Ø25mm": 0.85,

        "Interruptor Simple": 4.20,
        "Conmutador": 5.80,
        "Cruzamiento": 11.50,

        "Base Enchufe 16A": 6.10,
        "Base Enchufe 25A": 14.50,

        "Base USB": 18.00,
        "Base Estanca": 18.50,

        "Toma TV": 9.50,
        "Toma RJ45": 18.00,

        "Detector Movimiento": 32.00,

        "Plafón LED": 32.00,
        "Downlight LED": 18.00,

        "IGA 40A": 48.00,

        "PIA 10A": 8.50,
        "PIA 16A": 9.20,
        "PIA 20A": 11.50,
        "PIA 25A": 14.00,

        "Diferencial 40A Clase A": 65.00,

        "Protector Sobretensiones": 110.00,

        "Caja Cuadro": 75.00,

        "Wallbox 7.4kW": 680.00,

        "Panel Solar": 210.00,

        "Actuador KNX": 145.00
    }

    # =====================================================
    # CAPÍTULOS
    # =====================================================

    capitulos = {

        "DI":
        "DERIVACIÓN INDIVIDUAL",

        "CGMP":
        "CUADRO GENERAL",

        "C1":
        "ILUMINACIÓN",

        "C2":
        "TOMAS GENERALES",

        "C3":
        "COCINA Y HORNO",

        "C4":
        "LAVADORA Y TERMO",

        "C5":
        "BAÑOS Y COCINA",

        "C13":
        "VEHÍCULO ELÉCTRICO",

        "C14":
        "FOTOVOLTAICA",

        "PAT":
        "PUESTA A TIERRA"
    }

    datos_export = []

    # =====================================================
    # CAPÍTULOS DINÁMICOS
    # =====================================================

    for codigo, nombre in capitulos.items():

        with st.expander(f"🛠️ {codigo} - {nombre}"):

            materiales = st.multiselect(

                f"Materiales {codigo}",

                list(catalogo_precios.keys()),

                key=f"sel_{codigo}"
            )

            coste_materiales = 0

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

                    "Materiales (€)":
                    round(coste_materiales, 2),

                    "Mano de obra (€)":
                    round(mano_obra, 2),

                    "Base (€)":
                    round(total_capitulo, 2),

                    "IVA (%)":
                    iva_tipo,

                    "TOTAL (€)":
                    round(
                        total_capitulo *
                        (
                            1 + iva_tipo / 100
                        ),
                        2
                    )
                })

    # =====================================================
    # TOTAL FINAL
    # =====================================================

    if len(datos_export) > 0:

        st.divider()

        df_presupuesto = pd.DataFrame(
            datos_export
        )

        total_final = df_presupuesto[
            "TOTAL (€)"
        ].sum()

        st.markdown(f"""
        <div class="total-final-banner">

        PRESUPUESTO TOTAL

        <br>

        <span style="color:#ffd700">
        {total_final:,.2f} €
        </span>

        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            df_presupuesto,
            use_container_width=True
        )

        # =================================================
        # EXPORTAR EXCEL
        # =================================================

        excel_presupuesto = exportar_excel(

            df_presupuesto,

            "Presupuesto"
        )

        st.download_button(

            "📊 Descargar Presupuesto Excel",

            excel_presupuesto,

            "presupuesto_profesional.xlsx",

            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

            use_container_width=True
        )

        # =================================================
        # EXPORTAR CSV
        # =================================================

        csv_presupuesto = df_presupuesto.to_csv(

            index=False,
            sep=';',
            encoding='utf-16'
        )

        st.download_button(

            "📥 Descargar CSV",

            csv_presupuesto,

            "presupuesto.csv",

            "text/csv",

            use_container_width=True
        )
