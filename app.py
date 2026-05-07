# =========================================================
# INGENIERÍA PRO v8.0
# Cálculo de Secciones + Presupuestos REBT + FV
# Versión profesional para uso público
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Pro v8.0",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# CABECERA PROFESIONAL
# =========================================================

st.title("⚡ INGENIERÍA PRO v8.0 — Herramienta Profesional REBT + FV")

st.markdown("""
Aplicación profesional para **cálculo de secciones**, **instalaciones fotovoltaicas**  
y **presupuestos eléctricos** conforme al **REBT**.

- Cálculo de conductores según ITC-BT-19, ITC-BT-20 e ITC-BT-40  
- Cálculo FV en **corriente continua** con caída de tensión reglamentaria  
- Entrada por **potencia** o **intensidad directa**  
- Presupuesto estructurado por circuitos REBT  

---
""")

# =========================================================
# ESTILO VISUAL PROFESIONAL
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
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.40);
    letter-spacing: 0.5px;
}
</style>

<div class="footer-container">
<span class="watermark-text">
Younesse Tikent Tifaoui
</span>
</div>

""", unsafe_allow_html=True)

# =========================================================
# FUNCIÓN EXPORTACIÓN EXCEL
# =========================================================

def exportar_excel(df, hoja="Datos"):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        df.to_excel(writer, index=False, sheet_name=hoja)

        workbook = writer.book
        worksheet = writer.sheets[hoja]

        formato_header = workbook.add_format({
            'bold': True,
            'bg_color': '#1f2937',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })

        formato_texto = workbook.add_format({'border': 1})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, formato_header)

        worksheet.set_column('A:Z', 35, formato_texto)

    return output.getvalue()

# =========================================================
# SIDEBAR PROFESIONAL
# =========================================================

with st.sidebar:

    st.header("📂 Módulos de trabajo")

    modo = st.radio(
        "Selecciona el módulo",
        [
            "📐 Cálculo de secciones de conductores",
            "💰 Presupuesto detallado REBT"
        ]
    )
# =========================================================
# MÓDULO PROFESIONAL — CÁLCULO DE SECCIONES (REBT + FV)
# =========================================================

if modo == "📐 Cálculo de secciones de conductores":

    st.title("📐 Cálculo de Secciones de Conductores (REBT + FV)")

    st.markdown("""
    Este módulo calcula la **sección mínima reglamentaria** de los conductores según:

    - ITC-BT-19 → Intensidad máxima admisible  
    - ITC-BT-20 → Caída de tensión máxima permitida  
    - ITC-BT-40 → Instalaciones interiores en viviendas  
    - Instalaciones fotovoltaicas en **corriente continua**  

    Permite calcular mediante:
    - Potencia  
    - Intensidad directa (Ib)  

    ---
    """)

    # =====================================================
    # SECCIONES NORMALIZADAS
    # =====================================================

    secciones_ref = [
        1.5, 2.5, 4, 6, 10,
        16, 25, 35, 50, 70,
        95, 120, 150, 185, 240
    ]

    # =====================================================
    # TABLAS REBT — Intensidades admisibles
    # =====================================================

    tablas_adm = {

        "A1 - Empotrado en tubo (pared aislante)": {
            "PVC":  [14.5,19.5,26,34,46,61,80,99,119,151,182,210,240,273,321],
            "XLPE": [18.5,25,33,43,59,77,102,126,153,194,233,268,307,352,415]
        },

        "A2 - Multiconductor en tubo (pared aislante)": {
            "PVC":  [14,18.5,25,32,43,57,75,92,110,139,167,192,219,248,291],
            "XLPE": [17.5,24,32,41,54,73,95,117,141,179,216,249,285,324,380]
        },

        "B1 - Conductores en tubo sobre pared": {
            "PVC":  [17.5,24,32,41,57,76,101,125,151,192,232,269,300,341,400],
            "XLPE": [22,30,40,52,71,94,126,157,190,241,292,338,388,442,523]
        },

        "B2 - Multiconductor en tubo sobre pared": {
            "PVC":  [16.5,23,30,38,52,69,92,114,138,175,210,244,282,319,375],
            "XLPE": [21,28,38,49,66,88,117,146,175,222,269,312,358,408,481]
        },

        "C - Cable directamente sobre pared": {
            "PVC":  [19.5,27,36,46,63,85,112,138,168,213,258,299,344,391,461],
            "XLPE": [24,33,45,58,80,107,138,171,209,269,328,382,441,506,599]
        },

        "D1 - Conductos enterrados": {
            "PVC":  [22,29,38,47,63,81,104,125,148,183,216,246,278,312,361],
            "XLPE": [26,34,44,56,73,95,121,146,173,213,252,287,324,363,419]
        },

        "E - Multiconductor al aire libre": {
            "PVC":  [22,30,40,51,70,94,126,154,187,237,286,331,381,434,511],
            "XLPE": [26,36,49,63,86,115,149,185,225,289,352,410,473,542,641]
        },

        "F - Unipolares en contacto sobre bandeja": {
            "PVC":  [21,28,38,50,68,92,121,150,184,233,282,327,376,428,505],
            "XLPE": [25,34,46,61,83,112,146,181,221,281,341,396,455,517,613]
        }
    }

    # =====================================================
    # FUNCIÓN — Sección térmica según REBT
    # =====================================================

    def get_seccion_adm(metodo, aislamiento, ib):

        ais = "PVC" if "PVC" in aislamiento else "XLPE"
        intensidades = tablas_adm[metodo][ais]

        for i, intensidad in enumerate(intensidades):
            if intensidad >= ib:
                return secciones_ref[i]

        return 240  # Máxima sección normalizada

    # =====================================================
    # FORMULARIO DE ENTRADA
    # =====================================================

    c1, c2 = st.columns(2)

    with c1:

        tipo_instalacion = st.selectbox(
            "🏷 Tipo de instalación",
            ["CA REBT (general)", "FV en corriente continua"]
        )

        sistema = st.selectbox(
            "🔌 Sistema eléctrico",
            ["Monofásico 230V", "Trifásico 400V"] if tipo_instalacion == "CA REBT (general)" else ["Corriente continua FV"]
        )

        modo_intensidad = st.selectbox(
            "Modo de cálculo de intensidad",
            ["A partir de potencia", "Introducir intensidad directamente"]
        )

        if modo_intensidad == "A partir de potencia":
            potencia = st.number_input(
                "⚡ Potencia (W)",
                value=5750.0
            )
        else:
            ib_input = st.number_input(
                "🔁 Intensidad de cálculo Ib (A)",
                value=25.0
            )

        longitud = st.number_input(
            "📏 Longitud del circuito (m)",
            value=30.0
        )

        if tipo_instalacion == "CA REBT (general)":
            cos_phi = st.slider(
                "cos φ (factor de potencia)",
                0.70, 1.00, 0.90
            )
        else:
            cos_phi = 1.00  # FV CC → cos φ = 1

        uso = st.selectbox(
            "🏷 Tipo de circuito",
            ["General", "Motores", "Vehículo eléctrico", "Fotovoltaica"]
        )

    with c2:

        material = st.radio(
            "Material del conductor",
            ["Cobre (Cu)", "Aluminio (Al)"]
        )

        aislamiento = st.radio(
            "Tipo de aislamiento",
            ["PVC (70°C)", "XLPE/EPR (90°C)"]
        )

        metodo = st.selectbox(
            "Método de instalación (REBT)",
            list(tablas_adm.keys())
        )

        max_cdt = st.number_input(
            "Caída de tensión máxima permitida (%)",
            value=3.0
        )

        if tipo_instalacion == "FV en corriente continua":
            v_cc = st.number_input(
                "Tensión de trabajo FV (Vcc)",
                value=600.0
            )
        else:
            v_cc = None

    # =====================================================
    # FACTORES REBT
    # =====================================================

    k_u = 1.25 if uso in ["Motores", "Vehículo eléctrico"] else 1.0

    if tipo_instalacion == "CA REBT (general)":
        v_fase = 230 if "Mono" in sistema else 400
    else:
        v_fase = v_cc

    # =====================================================
    # CÁLCULO DE INTENSIDAD
    # =====================================================

    if modo_intensidad == "Introducir intensidad directamente":
        ib = ib_input
    else:
        if tipo_instalacion == "CA REBT (general)":
            if v_fase == 230:
                ib = (potencia * k_u) / (v_fase * cos_phi)
            else:
                ib = (potencia * k_u) / (1.732 * v_fase * cos_phi)
        else:
            ib = (potencia * k_u) / v_fase if v_fase > 0 else 0

    # =====================================================
    # SECCIÓN TÉRMICA
    # =====================================================

    s_adm = get_seccion_adm(metodo, aislamiento, ib)

    # =====================================================
    # CONDUCTIVIDAD
    # =====================================================

    if "Cobre" in material:
        gamma = 48 if "PVC" in aislamiento else 44
    else:
        gamma = 30 if "PVC" in aislamiento else 28

    # =====================================================
    # CÁLCULO DE CAÍDA DE TENSIÓN
    # =====================================================

    if tipo_instalacion == "CA REBT (general)":

        if modo_intensidad == "A partir de potencia":

            if v_fase == 230:
                s_cdt = (2 * longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)
            else:
                s_cdt = (longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)

        else:  # Intensidad directa

            if v_fase == 230:
                s_cdt = (2 * longitud * ib) / (gamma * (max_cdt/100 * v_fase))
            else:
                s_cdt = (longitud * ib) / (gamma * (max_cdt/100 * v_fase))

    else:
        # FV en corriente continua (ida y vuelta)
        delta_v = max_cdt / 100 * v_fase
        s_cdt = (2 * longitud * ib) / (gamma * delta_v) if delta_v > 0 else 240

    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)

    # =====================================================
    # SECCIÓN FINAL (ANTES DE MÍNIMOS REGLAMENTARIOS)
    # =====================================================

    s_final = max(s_adm, s_cdt_norm)

    # =====================================================
    # SECCIÓN MÍNIMA REGLAMENTARIA SEGÚN USO (REBT)
    # =====================================================

    seccion_minima_rebt = {
        "General": 1.5,
        "Motores": 2.5,
        "Vehículo eléctrico": 6.0,
        "Fotovoltaica": 4.0
    }

    s_min_regl = seccion_minima_rebt.get(uso, 1.5)

    # Sección final aplicando mínimo reglamentario
    s_final_regl = max(s_final, s_min_regl)

    st.divider()

    st.markdown(f"""
    <div class="resultado-caja">
    SECCIÓN FINAL REGLAMENTARIA: {s_final_regl} mm²
    <br>
    <small>
    Ib = {ib:.2f} A |
    Térmica = {s_adm} mm² |
    CdT = {s_cdt:.2f} mm² |
    Mínimo REBT = {s_min_regl} mm²
    </small>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # TABLA RESUMEN
    # =====================================================

    df_calc = pd.DataFrame({
        "Parámetro": [
            "Tipo instalación", "Sistema", "Potencia (W)", "Longitud (m)", "cos φ",
            "Material", "Aislamiento", "Método REBT",
            "Ib (A)", "Sección térmica (mm²)", "Sección CdT (mm²)",
            "Sección mínima REBT (mm²)", "SECCIÓN FINAL REGLAMENTARIA (mm²)"
        ],
        "Valor": [
            tipo_instalacion, sistema,
            potencia if modo_intensidad == "A partir de potencia" else "-",
            longitud, cos_phi,
            material, aislamiento, metodo,
            round(ib, 2), s_adm, round(s_cdt, 2),
            s_min_regl, s_final_regl
        ]
    })

    st.dataframe(df_calc, use_container_width=True)

    excel_calc = exportar_excel(df_calc, "Calculo_Secciones_REBT_FV")

    st.download_button(
        "📥 Descargar memoria de cálculo (Excel)",
        excel_calc,
        "calculo_secciones_rebt_fv.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
# =========================================================
# =========================================================
# MÓDULO PROFESIONAL — PRESUPUESTO REBT
# =========================================================
# =========================================================

else:

    st.title("💰 Presupuesto detallado de instalación eléctrica (REBT)")

    st.markdown("""
    Este módulo genera un **presupuesto profesional** conforme al  
    **Reglamento Electrotécnico de Baja Tensión (REBT)**, estructurado por circuitos:

    - Materiales normalizados  
    - Materiales personalizados  
    - Mano de obra (oficial y ayudante)  
    - Gastos generales y beneficio industrial  
    - IVA aplicable  

    Ideal para:
    - Ofertas a cliente  
    - Memorias económicas  
    - Proyectos eléctricos  
    - Estudios comparativos  

    ---
    """)

    # =====================================================
    # CONFIGURACIÓN ECONÓMICA
    # =====================================================

    with st.sidebar:

        st.header("⚙️ Parámetros económicos")

        gastos_generales = st.slider(
            "% Gastos Generales",
            0, 30, 13
        )

        beneficio_industrial = st.slider(
            "% Beneficio Industrial",
            0, 20, 6
        )

        iva_tipo = st.selectbox(
            "IVA (%)",
            [21, 10, 4, 0]
        )

        precio_oficial = st.number_input(
            "Oficial 1ª (€/h)",
            value=36.0
        )

        precio_ayudante = st.number_input(
            "Ayudante (€/h)",
            value=26.5
        )

        multiplicador = (
            1
            + gastos_generales / 100
            + beneficio_industrial / 100
        )

    # =====================================================
    # CATÁLOGO BASE (PRECIOS POR DEFECTO)
    # =====================================================

    catalogo_base = {

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
    # CAPÍTULOS REBT (ITC-BT-25)
    # =====================================================

    capitulos = {

        "DI": "Derivación Individual",
        "CGMP": "Cuadro General de Mando y Protección",

        "C1": "Iluminación",
        "C2": "Tomas de uso general y frigorífico",
        "C3": "Cocina y horno",
        "C4": "Lavadora, lavavajillas y termo",
        "C5": "Baños y cocina",
        "C6": "Iluminación adicional",
        "C7": "Tomas adicionales",

        "C8": "Calefacción",
        "C9": "Aire acondicionado",
        "C10": "Secadora",

        "C11": "Domótica",
        "C12": "Auxiliares",
        "C13": "Recarga de vehículo eléctrico",
        "C14": "Instalación fotovoltaica",

        "PAT": "Puesta a tierra"
    }

    datos_export = []

    # =====================================================
    # CAPÍTULOS DINÁMICOS — PRESUPUESTO REBT
    # =====================================================

    for codigo, nombre in capitulos.items():

        with st.expander(f"🛠️ {codigo} — {nombre}"):

            st.markdown(f"""
            ### 📘 Capítulo {codigo} — {nombre}

            Introduce los materiales, unidades y mano de obra asociada a este capítulo.
            Este apartado corresponde a uno de los circuitos definidos en el **REBT (ITC-BT-25)**.
            """)

            # ---------------------------------------------
            # MATERIALES DEL CATÁLOGO (CON PRECIO EDITABLE)
            # ---------------------------------------------
            st.markdown("## 📦 Materiales normalizados")
            st.caption("Selecciona materiales habituales y ajusta su precio unitario si es necesario.")

            materiales = st.multiselect(
                f"Materiales incluidos en {codigo}",
                list(catalogo_base.keys()),
                key=f"sel_{codigo}"
            )

            coste_materiales = 0

            for item in materiales:

                col1, col2, col3 = st.columns([4, 2, 2])

                with col1:
                    st.markdown(f"**{item}**")

                with col2:
                    precio_edit = st.number_input(
                        f"Precio {item}",
                        min_value=0.0,
                        value=float(catalogo_base[item]),
                        step=0.10,
                        key=f"precio_edit_{codigo}_{item}"
                    )

                with col3:
                    cantidad = st.number_input(
                        f"Cantidad {item}",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key=f"cant_{codigo}_{item}"
                    )

                subtotal = precio_edit * cantidad
                coste_materiales += subtotal

                st.markdown(f"Subtotal: **{subtotal:.2f} €**")
                st.divider()

            # ---------------------------------------------
            # MATERIALES PERSONALIZADOS
            # ---------------------------------------------
            st.markdown("## ➕ Materiales personalizados")
            st.caption("Añade materiales no incluidos en catálogo, con precio y cantidad libre.")

            num_personalizados = st.number_input(
                f"Nº de materiales personalizados en {codigo}",
                min_value=0,
                max_value=20,
                step=1,
                key=f"pers_count_{codigo}"
            )

            coste_personalizados = 0

            for i in range(num_personalizados):

                st.markdown(f"### Material personalizado #{i+1}")

                nombre_pers = st.text_input(
                    f"Nombre del material #{i+1}",
                    key=f"pers_name_{codigo}_{i}"
                )

                precio_pers = st.number_input(
                    f"Precio unitario (€) #{i+1}",
                    min_value=0.0,
                    value=0.0,
                    step=0.10,
                    key=f"pers_price_{codigo}_{i}"
                )

                cantidad_pers = st.number_input(
                    f"Cantidad #{i+1}",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"pers_qty_{codigo}_{i}"
                )

                subtotal_pers = precio_pers * cantidad_pers
                coste_personalizados += subtotal_pers

                st.markdown(f"Subtotal: **{subtotal_pers:.2f} €**")
                st.divider()

            # Sumar catálogo + personalizados
            coste_materiales += coste_personalizados

            # ---------------------------------------------
            # MANO DE OBRA
            # ---------------------------------------------
            st.markdown("## 👷 Mano de obra")
            st.caption("Introduce las horas estimadas de trabajo para este capítulo.")

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
                horas_oficial * precio_oficial +
                horas_ayudante * precio_ayudante
            )

            # ---------------------------------------------
            # TOTAL CAPÍTULO
            # ---------------------------------------------
            total_capitulo = (coste_materiales + mano_obra) * multiplicador

            st.markdown(f"""
            <div class="resultado-caja">
            TOTAL CAPÍTULO {codigo}: {total_capitulo:,.2f} €
            </div>
            """, unsafe_allow_html=True)

            # Guardar para exportación
            if total_capitulo > 0:

                datos_export.append({

                    "Capítulo": f"{codigo} — {nombre}",
                    "Materiales (€)": round(coste_materiales, 2),
                    "Mano de obra (€)": round(mano_obra, 2),
                    "Base (€)": round(total_capitulo, 2),
                    "IVA (%)": iva_tipo,
                    "TOTAL (€)": round(total_capitulo * (1 + iva_tipo / 100), 2)
                })
# =====================================================
# TOTAL FINAL DEL PRESUPUESTO
# =====================================================

    if len(datos_export) > 0:

        st.divider()

        df_presupuesto = pd.DataFrame(datos_export)

        total_final = df_presupuesto["TOTAL (€)"].sum()

        st.markdown(f"""
        <div class="total-final-banner">
        PRESUPUESTO TOTAL INSTALACIÓN
        <br>
        <span style="color:#ffd700">
        {total_final:,.2f} €
        </span>
        <br><br>
        <small>Importe calculado según estructura de circuitos del REBT (ITC-BT-25).</small>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(df_presupuesto, use_container_width=True)

        # ---------------------------------------------
        # EXPORTAR EXCEL
        # ---------------------------------------------
        excel_presupuesto = exportar_excel(df_presupuesto, "Presupuesto_REBT")

        st.download_button(
            "📊 Descargar Presupuesto (Excel)",
            excel_presupuesto,
            "presupuesto_rebt.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # ---------------------------------------------
        # EXPORTAR CSV
        # ---------------------------------------------
        csv_presupuesto = df_presupuesto.to_csv(
            index=False,
            sep=';',
            encoding='utf-16'
        )

        st.download_button(
            "📥 Descargar Presupuesto (CSV)",
            csv_presupuesto,
            "presupuesto_rebt.csv",
            "text/csv",
            use_container_width=True
        )
