# =========================================================
# INGENIERÍA PRO v9.1
# Cálculo de Secciones REBT + FV (solo cálculo)
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
    page_title="Ingeniería Pro v9.1",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# ESTILO VISUAL PROFESIONAL
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #050816;
    color: #e5e7eb;
    font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Títulos principales */
h1, h2, h3, h4 {
    color: #f9fafb !important;
    font-weight: 800 !important;
}

/* Texto general */
label, .stMarkdown, p, span, div {
    color: #e5e7eb !important;
}

/* Inputs */
.stNumberInput input,
.stSelectbox div,
.stRadio > label,
.stSlider > div {
    background-color: #020617 !important;
    color: #e5e7eb !important;
}

/* Caja resultado principal */
.resultado-caja {
    color: #f9fafb !important;
    font-weight: 900 !important;
    font-size: 26px;
    background: radial-gradient(circle at top left, #22d3ee22, #020617);
    padding: 22px;
    border-radius: 16px;
    border-left: 6px solid #22d3ee;
    margin-bottom: 20px;
    text-align: right;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.7);
}

/* Banner final */
.total-final-banner {
    color: #f9fafb !important;
    font-weight: 900 !important;
    font-size: 30px;
    background: linear-gradient(135deg, #020617 0%, #111827 40%, #0f172a 100%);
    padding: 28px;
    border-radius: 20px;
    text-align: left;
    border: 2px solid #22d3ee;
    margin-top: 30px;
    box-shadow: 0px 18px 40px rgba(0,0,0,0.85);
}

/* Expanders */
.stExpander {
    border: 1px solid #1f2937 !important;
    border-radius: 14px !important;
    background-color: #020617 !important;
    margin-bottom: 18px !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: #020617 !important;
}

/* Footer marca de agua */
.footer-container {
    position: fixed;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    pointer-events: none;
    text-align: center;
    width: 100%;
}

.watermark-text {
    font-size: 13px;
    font-weight: 600;
    color: rgba(148, 163, 184, 0.55);
    letter-spacing: 0.6px;
}

/* Tarjetas de sección */
.card {
    background: #020617;
    border-radius: 16px;
    padding: 18px 20px;
    border: 1px solid #1f2937;
    box-shadow: 0px 10px 25px rgba(0,0,0,0.65);
    margin-bottom: 18px;
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    color: #e5e7eb;
    margin-bottom: 6px;
}

.card-subtitle {
    font-size: 13px;
    color: #9ca3af;
    margin-bottom: 10px;
}

</style>

<div class="footer-container">
<span class="watermark-text">
Ingeniería Pro — Younesse Tikent Tifaoui
</span>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CABECERA PROFESIONAL
# =========================================================

st.markdown("""
# ⚡ INGENIERÍA PRO v9.1 — Cálculo Profesional de Secciones REBT + FV

Aplicación profesional para **cálculo de secciones de conductores** en:

- Instalaciones en **CA** según ITC-BT-19, ITC-BT-20 e ITC-BT-40  
- Instalaciones **fotovoltaicas en corriente continua**  

Se calculan:

- **Sección térmica** (intensidad máxima admisible, tablas REBT)  
- **Sección por caída de tensión** usando las ecuaciones reglamentarias  
- **Sección mínima reglamentaria** según uso del circuito  
- **Procedimiento detallado del cálculo**  
- **Tabla ITC‑BT‑19** con la sección seleccionada resaltada  

---
""")

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
            'bg_color': '#111827',
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
# MÓDULO ÚNICO — CÁLCULO DE SECCIONES (REBT + FV)
# =========================================================

st.markdown("## 📐 Módulo de cálculo de secciones de conductores (REBT + FV)")

st.markdown("""
Se utilizan las **ecuaciones reglamentarias de caída de tensión**:

**Monofásica**

\

\[
S_{min} = \\frac{2 \\cdot \\rho \\cdot L \\cdot P}{U \\cdot \\Delta U_{max}}
\\quad\\text{o}\\quad
S_{min} = \\frac{2 \\cdot L \\cdot P}{\\sigma \\cdot U \\cdot \\Delta U_{max}}
\\]



**Trifásica**

\

\[
S_{min} = \\frac{\\rho \\cdot L \\cdot P}{U \\cdot \\Delta U_{max}}
\\quad\\text{o}\\quad
S_{min} = \\frac{L \\cdot P}{\\sigma \\cdot U \\cdot \\Delta U_{max}}
\\]



Con:

- \\( \\rho \\): resistividad (Ω·mm²/m)  
- \\( \\sigma \\): conductividad (Ω^{-1}·m/mm²)  
- \\( L \\): longitud del circuito (m)  
- \\( P \\): potencia (W)  
- \\( U \\): tensión (V)  
- \\( \\Delta U_{max} \\): caída de tensión máxima (V)  

---
""")

with st.expander("📷 Tabla de ecuaciones utilizada (resumen)"):
    st.markdown("""
**Monofásica**

\

\[
P = U \\cdot I \\cdot \\cos \\varphi
\\]



\

\[
S_{cdt,mono} = \\frac{2 \\cdot L \\cdot P}{\\sigma \\cdot U \\cdot \\Delta U_{max}}
\\]



**Trifásica**

\

\[
P = \\sqrt{3} \\cdot U \\cdot I \\cdot \\cos \\varphi
\\]



\

\[
S_{cdt,tri} = \\frac{L \\cdot P}{\\sigma \\cdot U \\cdot \\Delta U_{max}}
\\]



**Fotovoltaica CC (ida y vuelta)**

\

\[
P = U_{cc} \\cdot I
\\]



\

\[
S_{cdt,FV} = \\frac{2 \\cdot L \\cdot P}{\\sigma \\cdot U_{cc} \\cdot \\Delta U_{max}}
\\]


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
    st.markdown('<div class="card"><div class="card-title">Datos eléctricos</div><div class="card-subtitle">Definición del circuito y condiciones de servicio</div>', unsafe_allow_html=True)

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

    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card"><div class="card-title">Datos de instalación</div><div class="card-subtitle">Método, aislamiento y límites reglamentarios</div>', unsafe_allow_html=True)

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

    max_cdt_pct = st.number_input(
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

    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# FACTORES Y TENSIONES
# =====================================================

k_u = 1.25 if uso in ["Motores", "Vehículo eléctrico"] else 1.0

if tipo_instalacion == "CA REBT (general)":
    v_fase = 230 if "Mono" in sistema else 400
else:
    v_fase = v_cc

delta_u_max = max_cdt_pct / 100 * v_fase  # V

# =====================================================
# CÁLCULO DE INTENSIDAD Y POTENCIA
# =====================================================

if modo_intensidad == "Introducir intensidad directamente":
    ib = ib_input
    if tipo_instalacion == "CA REBT (general)":
        if "Mono" in sistema:
            potencia_calc = v_fase * ib * cos_phi
        else:
            potencia_calc = math.sqrt(3) * v_fase * ib * cos_phi
    else:
        potencia_calc = v_fase * ib  # FV CC
else:
    potencia_calc = potencia * k_u
    if tipo_instalacion == "CA REBT (general)":
        if "Mono" in sistema:
            ib = potencia_calc / (v_fase * cos_phi)
        else:
            ib = potencia_calc / (math.sqrt(3) * v_fase * cos_phi)
    else:
        ib = potencia_calc / v_fase if v_fase > 0 else 0

# =====================================================
# SECCIÓN TÉRMICA (TABLAS REBT)
# =====================================================

s_adm = get_seccion_adm(metodo, aislamiento, ib)

# =====================================================
# CONDUCTIVIDAD σ
# =====================================================

if "Cobre" in material:
    sigma = 48 if "PVC" in aislamiento else 44
else:
    sigma = 30 if "PVC" in aislamiento else 28

# =====================================================
# CÁLCULO DE SECCIÓN POR CAÍDA DE TENSIÓN
# =====================================================

if tipo_instalacion == "CA REBT (general)":

    if "Mono" in sistema:
        # Monofásica: S = 2·L·P / (σ·U·ΔUmax)
        s_cdt = (2 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max) if delta_u_max > 0 else 240
        ecuacion_usada = r"S_{cdt,mono} = \dfrac{2 \cdot L \cdot P}{\sigma \cdot U \cdot \Delta U_{max}}"
    else:
        # Trifásica: S = L·P / (σ·U·ΔUmax)
        s_cdt = (longitud * potencia_calc) / (sigma * v_fase * delta_u_max) if delta_u_max > 0 else 240
        ecuacion_usada = r"S_{cdt,tri} = \dfrac{L \cdot P}{\sigma \cdot U \cdot \Delta U_{max}}"

else:
    # FV en CC (ida y vuelta): S = 2·L·P / (σ·Ucc·ΔUmax)
    s_cdt = (2 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max) if delta_u_max > 0 else 240
    ecuacion_usada = r"S_{cdt,FV} = \dfrac{2 \cdot L \cdot P}{\sigma \cdot U_{cc} \cdot \Delta U_{max}}"

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

# =====================================================
# RESULTADO PRINCIPAL
# =====================================================

st.divider()

st.markdown(f"""
<div class="resultado-caja">
SECCIÓN FINAL REGLAMENTARIA: {s_final_regl} mm²
<br>
<small>
Ib = {ib:.2f} A |
Térmica (ITC-BT-19) = {s_adm} mm² |
CdT (ecuación) = {s_cdt:.2f} mm² (normalizada: {s_cdt_norm} mm²) |
Mínimo REBT = {s_min_regl} mm²
</small>
</div>
""", unsafe_allow_html=True)

# =====================================================
# TABLA OFICIAL ITC-BT-19 CON SUBRAYADO AUTOMÁTICO
# =====================================================

st.markdown("### 📘 Tabla ITC‑BT‑19 — Intensidades admisibles (método seleccionado)")

tabla_oficial = pd.DataFrame({
    "Sección (mm²)": secciones_ref,
    "PVC (A)": tablas_adm[metodo]["PVC"],
    "XLPE (A)": tablas_adm[metodo]["XLPE"]
})

# Fila y columna a resaltar
if s_final_regl in tabla_oficial["Sección (mm²)"].values:
    fila_resaltar = tabla_oficial.index[tabla_oficial["Sección (mm²)"] == s_final_regl][0]
else:
    fila_resaltar = None

columna_resaltar = "PVC (A)" if "PVC" in aislamiento else "XLPE (A)"

def resaltar_celda(row):
    estilos = []
    for col in tabla_oficial.columns:
        base = ""
        if fila_resaltar is not None and row.name == fila_resaltar and col == columna_resaltar:
            base = "background-color: #22d3ee; color: #020617; font-weight: 900; border: 1px solid #0f172a;"
        elif fila_resaltar is not None and row.name == fila_resaltar:
            base = "text-decoration: underline; font-weight: 700;"
        elif col == columna_resaltar:
            base = "text-decoration: underline; font-weight: 700;"
        estilos.append(base)
    return estilos

st.dataframe(
    tabla_oficial.style.apply(resaltar_celda, axis=1),
    use_container_width=True
)

# =====================================================
# PROCEDIMIENTO DETALLADO DEL CÁLCULO
# =====================================================

st.markdown("### 📘 Procedimiento seguido en el cálculo")

st.markdown("""
#### 1️⃣ Cálculo de la potencia de diseño

- Si introduces **potencia**:
  - Se aplica un factor de utilización \\(k_u\\) según el uso (motores, VE, etc.).
- Si introduces **intensidad**:
  - Se calcula la potencia a partir de:

  - **Monofásica**  
    \

\[
    P = U \\cdot I \\cdot \\cos \\varphi
    \\]



  - **Trifásica**  
    \

\[
    P = \\sqrt{3} \\cdot U \\cdot I \\cdot \\cos \\varphi
    \\]



  - **Fotovoltaica CC**  
    \

\[
    P = U_{cc} \\cdot I
    \\]


""")

st.markdown(f"""
**Potencia de cálculo utilizada:**  

\

\[
P = {potencia_calc:,.2f}\\ \\text{{W}}
\\]


""")

st.markdown("""
#### 2️⃣ Cálculo de la sección por intensidad admisible (térmica)

Se usa la tabla de intensidades admisibles de la **ITC-BT-19** según:

- Método de instalación  
- Tipo de aislamiento (PVC / XLPE)  
- Material (Cu / Al)  

Se busca la **primera sección normalizada** cuya intensidad admisible sea ≥ \\(I_b\\).
""")

st.markdown(f"""
**Intensidad de cálculo:**  

\

\[
I_b = {ib:.2f}\\ \\text{{A}}
\\]



**Sección térmica resultante:**  

\

\[
S_{{adm}} = {s_adm}\\ \\text{{mm}}^2
\\]


""")

st.markdown("""
#### 3️⃣ Cálculo de la sección por caída de tensión

Se aplica la ecuación reglamentaria correspondiente:

- **Monofásica**  
\

\[
S_{{cdt,mono}} = \\frac{{2 \\cdot L \\cdot P}}{{\\sigma \\cdot U \\cdot \\Delta U_{{max}}}}
\\]



- **Trifásica**  
\

\[
S_{{cdt,tri}} = \\frac{{L \\cdot P}}{{\\sigma \\cdot U \\cdot \\Delta U_{{max}}}}
\\]



- **Fotovoltaica CC**  
\

\[
S_{{cdt,FV}} = \\frac{{2 \\cdot L \\cdot P}}{{\\sigma \\cdot U_{{cc}} \\cdot \\Delta U_{{max}}}}
\\]


""")

st.markdown(f"""
**Ecuación aplicada en este caso:**

\

\[
{ecuacion_usada}
\\]



**Datos numéricos:**

- Longitud: \\(L = {longitud}\\ \\text{{m}}\\)  
- Conductividad: \\(\\sigma = {sigma}\\ \\Omega^{{-1}}\\cdot m/\\text{{mm}}^2\\)  
- Tensión: \\(U = {v_fase}\\ \\text{{V}}\\)  
- Caída máxima: \\(\\Delta U_{{max}} = {delta_u_max:.2f}\\ \\text{{V}}\\)  
- Potencia: \\(P = {potencia_calc:,.2f}\\ \\text{{W}}\\)

**Resultado de sección por caída de tensión:**

\

\[
S_{{cdt}} = {s_cdt:.2f}\\ \\text{{mm}}^2
\\quad\\Rightarrow\\quad
S_{{cdt,norm}} = {s_cdt_norm}\\ \\text{{mm}}^2
\\]


""")

st.markdown("""
#### 4️⃣ Aplicación de mínimos reglamentarios

Se compara:

- Sección térmica \\(S_{adm}\\)  
- Sección por caída de tensión normalizada \\(S_{cdt,norm}\\)  
- Sección mínima reglamentaria \\(S_{min,REBT}\\) según uso:

- General → 1.5 mm²  
- Motores → 2.5 mm²  
- Vehículo eléctrico → 6 mm²  
- Fotovoltaica → 4 mm²  

La sección final es:

\

\[
S_{{final}} = \\max\\left(S_{{adm}},\\ S_{{cdt,norm}},\\ S_{{min,REBT}}\\right)
\\]


""")

st.markdown(f"""
<div class="total-final-banner">
Resultado final del cálculo de sección
<br><br>
Sección térmica: <b>{s_adm} mm²</b><br>
Sección por caída de tensión (normalizada): <b>{s_cdt_norm} mm²</b><br>
Sección mínima REBT por uso: <b>{s_min_regl} mm²</b><br><br>
<span style="color:#22d3ee">
SECCIÓN FINAL REGLAMENTARIA: {s_final_regl} mm²
</span>
</div>
""", unsafe_allow_html=True)

# =====================================================
# TABLA RESUMEN + EXPORTACIÓN
# =====================================================

df_calc = pd.DataFrame({
    "Parámetro": [
        "Tipo instalación", "Sistema", "Uso del circuito",
        "Potencia de cálculo (W)", "Intensidad Ib (A)",
        "Longitud (m)", "cos φ", "Material", "Aislamiento",
        "Método instalación REBT",
        "Sección térmica (mm²)", "Sección CdT (mm²)",
        "Sección CdT normalizada (mm²)",
        "Sección mínima REBT (mm²)",
        "SECCIÓN FINAL REGLAMENTARIA (mm²)"
    ],
    "Valor": [
        tipo_instalacion, sistema, uso,
        round(potencia_calc, 2), round(ib, 2),
        longitud, cos_phi, material, aislamiento,
        metodo,
        s_adm, round(s_cdt, 2),
        s_cdt_norm,
        s_min_regl,
        s_final_regl
    ]
})

st.markdown("### 📊 Resumen numérico del cálculo")
st.dataframe(df_calc, use_container_width=True)

excel_calc = exportar_excel(df_calc, "Calculo_Secciones_REBT_FV")

st.download_button(
    "📥 Descargar memoria de cálculo (Excel)",
    excel_calc,
    "calculo_secciones_rebt_fv.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
