# =========================================================
# INGENIERÍA PRO — Estilo Apple + Login
# Cálculo de Secciones REBT + FV
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Pro",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# LOGIN ESTILO APPLE
# =========================================================

PASSWORD = "SEA2526"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 90vh;
    }
    .login-box {
        background: rgba(15, 23, 42, 0.78);
        backdrop-filter: blur(18px);
        padding: 40px 50px;
        border-radius: 22px;
        border: 1px solid rgba(148, 163, 184, 0.45);
        text-align: center;
        width: 380px;
        box-shadow: 0px 22px 50px rgba(0,0,0,0.55);
    }
    .login-title {
        font-size: 30px;
        font-weight: 700;
        color: #f5f5f7;
        margin-bottom: 18px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
    }
    .login-subtitle {
        font-size: 14px;
        color: #9ca3af;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">Ingeniería Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Acceso restringido — introduce la contraseña</div>', unsafe_allow_html=True)

    password_input = st.text_input("Contraseña", type="password", label_visibility="collapsed")

    if st.button("Entrar"):
        if password_input == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# =========================================================
# ESTILO GLOBAL TIPO APPLE
# =========================================================

st.markdown("""
<style>

:root {
    --bg-main: #020617;
    --bg-card: rgba(15, 23, 42, 0.92);
    --bg-glass: rgba(15, 23, 42, 0.78);
    --border-soft: rgba(148, 163, 184, 0.35);
    --accent: #0ea5e9;
    --accent-soft: rgba(56, 189, 248, 0.18);
    --text-main: #f9fafb;
    --text-soft: #9ca3af;
    --radius-xl: 20px;
    --shadow-soft: 0 18px 45px rgba(0,0,0,0.55);
}

.stApp {
    background: radial-gradient(circle at top, #020617 0%, #020617 40%, #020617 100%);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
}

/* Títulos */
h1, h2, h3, h4 {
    color: var(--text-main) !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em;
}
h1 {
    font-size: 2.4rem !important;
    margin-bottom: 0.4rem !important;
}

/* Tarjetas */
.card {
    background: var(--bg-glass);
    border-radius: var(--radius-xl);
    padding: 20px 22px;
    border: 1px solid var(--border-soft);
    box-shadow: var(--shadow-soft);
    margin-bottom: 18px;
    backdrop-filter: blur(18px);
}

/* Tarjetas de fórmulas */
.formula-card {
    background: var(--bg-card);
    padding: 22px;
    border-radius: var(--radius-xl);
    border: 1px solid var(--border-soft);
    text-align: center;
    margin-bottom: 18px;
    box-shadow: var(--shadow-soft);
}

/* Caja resultado principal */
.resultado-caja {
    color: var(--text-main) !important;
    font-weight: 800 !important;
    font-size: 26px;
    background: radial-gradient(circle at top left, var(--accent-soft), #020617);
    padding: 22px;
    border-radius: var(--radius-xl);
    border-left: 5px solid var(--accent);
    margin-bottom: 20px;
    text-align: right;
    box-shadow: var(--shadow-soft);
}

/* Banner final */
.total-final-banner {
    color: var(--text-main) !important;
    font-weight: 800 !important;
    font-size: 28px;
    background: linear-gradient(135deg, #020617 0%, #020617 40%, #020617 100%);
    padding: 24px;
    border-radius: var(--radius-xl);
    text-align: left;
    border: 1px solid var(--border-soft);
    margin-top: 26px;
    box-shadow: var(--shadow-soft);
}

/* Inputs tipo Apple */
.stNumberInput input,
.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stRadio > label,
.stSlider > div {
    background: rgba(15, 23, 42, 0.9) !important;
    color: var(--text-main) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(148, 163, 184, 0.45) !important;
}

/* Botones */
button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #22c55e) !important;
    color: white !important;
    border-radius: 999px !important;
    border: none !important;
    padding: 0.45rem 1.4rem !important;
    font-weight: 600 !important;
    box-shadow: 0 12px 30px rgba(34, 197, 94, 0.35) !important;
}
button[kind="primary"]:hover {
    filter: brightness(1.05);
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-xl);
    overflow: hidden;
    box-shadow: var(--shadow-soft);
}

/* Footer */
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
    font-weight: 500;
    color: rgba(148, 163, 184, 0.7);
    letter-spacing: 0.08em;
}

</style>

<div class="footer-container">
<span class="watermark-text">
Ingeniería Pro — Younesse Tikent Tifaoui
</span>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CABECERA
# =========================================================

st.markdown("""
# ⚡ Ingeniería Pro — Cálculo de Secciones REBT + FV

Aplicación profesional para **cálculo de secciones de conductores**:

- Instalaciones en **CA** (ITC‑BT‑19, ITC‑BT‑20, ITC‑BT‑40)  
- Instalaciones **fotovoltaicas en corriente continua**  

Incluye:

- Sección térmica (tablas REBT)
- Sección por caída de tensión (ecuaciones oficiales)
- Sección mínima reglamentaria
- Procedimiento detallado
- Tabla ITC‑BT‑19 con fila y columna resaltadas

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
            'bg_color': '#0f172a',
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
# SECCIONES NORMALIZADAS
# =========================================================

secciones_ref = [
    1.50, 2.50, 4.00, 6.00, 10.00,
    16.00, 25.00, 35.00, 50.00, 70.00,
    95.00, 120.00, 150.00, 185.00, 240.00
]

# =========================================================
# TABLAS REBT — Intensidades admisibles
# =========================================================

tablas_adm = {
    "A1 - Empotrado en tubo (pared aislante)": {
        "PVC":  [14.50,19.50,26.00,34.00,46.00,61.00,80.00,99.00,119.00,151.00,182.00,210.00,240.00,273.00,321.00],
        "XLPE": [18.50,25.00,33.00,43.00,59.00,77.00,102.00,126.00,153.00,194.00,233.00,268.00,307.00,352.00,415.00]
    },
    "B1 - Conductores en tubo sobre pared": {
        "PVC":  [17.50,24.00,32.00,41.00,57.00,76.00,101.00,125.00,151.00,192.00,232.00,269.00,300.00,341.00,400.00],
        "XLPE": [22.00,30.00,40.00,52.00,71.00,94.00,126.00,157.00,190.00,241.00,292.00,338.00,388.00,442.00,523.00]
    },
    "C - Cable directamente sobre pared": {
        "PVC":  [19.50,27.00,36.00,46.00,63.00,85.00,112.00,138.00,168.00,213.00,258.00,299.00,344.00,391.00,461.00],
        "XLPE": [24.00,33.00,45.00,58.00,80.00,107.00,138.00,171.00,209.00,269.00,328.00,382.00,441.00,506.00,599.00]
    }
}

# =========================================================
# FUNCIÓN — Sección térmica
# =========================================================

def get_seccion_adm(metodo, aislamiento, ib):
    ais = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm[metodo][ais]
    for i, intensidad in enumerate(intensidades):
        if intensidad >= ib:
            return secciones_ref[i]
    return 240.00

# =========================================================
# FORMULARIO PRINCIPAL (ESTILO APPLE)
# =========================================================

c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

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
        potencia = st.number_input("⚡ Potencia (W)", value=5750.0)
    else:
        ib_input = st.number_input("🔁 Intensidad Ib (A)", value=25.0)

    longitud = st.number_input("📏 Longitud (m)", value=30.0)

    cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90) if tipo_instalacion == "CA REBT (general)" else 1.00

    uso = st.selectbox(
        "🏷 Tipo de circuito",
        ["General", "Motores", "Vehículo eléctrico", "Fotovoltaica"]
    )

    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    material = st.radio("Material", ["Cobre (Cu)", "Aluminio (Al)"])
    aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"])
    metodo = st.selectbox("Método REBT", list(tablas_adm.keys()))
    max_cdt_pct = st.number_input("Caída de tensión máx (%)", value=3.0)

    v_cc = st.number_input("Tensión FV (Vcc)", value=600.0) if tipo_instalacion == "FV en corriente continua" else None

    st.markdown('</div>', unsafe_allow_html=True)
# =========================================================
# CÁLCULOS
# =========================================================

# Factor de utilización según tipo de circuito
k_u = 1.25 if uso in ["Motores", "Vehículo eléctrico"] else 1.0

# Tensión según sistema
v_fase = 230 if sistema == "Monofásico 230V" else (400 if sistema == "Trifásico 400V" else v_cc)

# Caída de tensión máxima permitida en voltios
delta_u_max = (max_cdt_pct / 100) * v_fase

# =========================================================
# CÁLCULO DE POTENCIA E INTENSIDAD
# =========================================================

if modo_intensidad == "Introducir intensidad directamente":
    ib = ib_input

    if sistema == "Monofásico 230V":
        potencia_calc = v_fase * ib * cos_phi
    elif sistema == "Trifásico 400V":
        potencia_calc = math.sqrt(3) * v_fase * ib * cos_phi
    else:
        potencia_calc = v_fase * ib  # FV CC

else:
    potencia_calc = potencia * k_u

    if sistema == "Monofásico 230V":
        ib = potencia_calc / (v_fase * cos_phi)
    elif sistema == "Trifásico 400V":
        ib = potencia_calc / (math.sqrt(3) * v_fase * cos_phi)
    else:
        ib = potencia_calc / v_fase  # FV CC

# =========================================================
# SECCIÓN TÉRMICA (TABLAS REBT)
# =========================================================

s_adm = get_seccion_adm(metodo, aislamiento, ib)

# =========================================================
# CONDUCTIVIDAD σ SEGÚN MATERIAL Y AISLAMIENTO
# =========================================================

if "Cobre" in material:
    sigma = 48 if "PVC" in aislamiento else 44
else:
    sigma = 30 if "PVC" in aislamiento else 28

# =========================================================
# CÁLCULO DE SECCIÓN POR CAÍDA DE TENSIÓN
# =========================================================

if sistema == "Monofásico 230V":
    s_cdt = (2 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_usada = r"S_{cdt,mono}=\frac{2\cdot L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"

elif sistema == "Trifásico 400V":
    s_cdt = (longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_usada = r"S_{cdt,tri}=\frac{L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"

else:  # FV CC
    s_cdt = (2 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_usada = r"S_{cdt,FV}=\frac{2\cdot L\cdot P}{\sigma\cdot U_{cc}\cdot\Delta U_{\max}}"

# Normalización a sección comercial
s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240.00)

# =========================================================
# SECCIÓN MÍNIMA REGLAMENTARIA
# =========================================================

s_min_rebt = {
    "General": 1.5,
    "Motores": 2.5,
    "Vehículo eléctrico": 6.0,
    "Fotovoltaica": 4.0
}[uso]

# =========================================================
# SECCIÓN FINAL
# =========================================================

s_final = max(s_adm, s_cdt_norm, s_min_rebt)

# =========================================================
# RESULTADO PRINCIPAL — ESTILO APPLE
# =========================================================

st.markdown(f"""
<div class="resultado-caja">
SECCIÓN FINAL REGLAMENTARIA: {s_final:.2f} mm²
<br>
<small>
Ib = {ib:.2f} A |
Térmica = {s_adm:.2f} mm² |
CdT = {s_cdt:.2f} mm² (→ {s_cdt_norm:.2f} mm²) |
Mínimo REBT = {s_min_rebt:.2f} mm²
</small>
</div>
""", unsafe_allow_html=True)
# =========================================================
# TARJETAS DE FÓRMULAS (KaTeX PERFECTO — ESTILO APPLE)
# =========================================================

st.markdown("### 📘 Ecuaciones aplicadas")

# -----------------------------
# Fórmula principal (KaTeX)
# -----------------------------
st.markdown('<div class="formula-card">', unsafe_allow_html=True)
st.latex(rf"{ecuacion_usada}")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Resultado numérico de la fórmula
# -----------------------------
st.markdown('<div class="formula-card">', unsafe_allow_html=True)
st.latex(rf"S_{{cdt}} = {s_cdt:.2f}\ \text{{mm}}^2")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Fórmula de potencia (según sistema)
# -----------------------------
st.markdown('<div class="formula-card">', unsafe_allow_html=True)

if sistema == "Monofásico 230V":
    st.latex(r"P = U \cdot I \cdot \cos\varphi")
elif sistema == "Trifásico 400V":
    st.latex(r"P = \sqrt{3}\cdot U \cdot I \cdot \cos\varphi")
else:
    st.latex(r"P = U_{cc} \cdot I")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Resultado numérico de potencia
# -----------------------------
st.markdown('<div class="formula-card">', unsafe_allow_html=True)
st.latex(rf"P = {potencia_calc:.2f}\ \text{{W}}")
st.markdown('</div>', unsafe_allow_html=True)
# =========================================================
# TABLA ITC‑BT‑19 — DOS DECIMALES + SUBRAYADO DINÁMICO
# =========================================================

st.markdown("### 📘 Tabla ITC‑BT‑19 — Intensidades admisibles")

# Construcción de tabla con dos decimales siempre
tabla = pd.DataFrame({
    "Sección (mm²)": [f"{s:.2f}" for s in secciones_ref],
    "PVC (A)": [f"{x:.2f}" for x in tablas_adm[metodo]["PVC"]],
    "XLPE (A)": [f"{x:.2f}" for x in tablas_adm[metodo]["XLPE"]]
})

# Determinar fila seleccionada
fila = tabla.index[tabla["Sección (mm²)"] == f"{s_final:.2f}"][0] \
       if f"{s_final:.2f}" in tabla["Sección (mm²)"].values else None

# Determinar columna según aislamiento
col = "PVC (A)" if "PVC" in aislamiento else "XLPE (A)"

# Estilo dinámico estilo Apple
def estilo(row):
    estilos = []
    for c in tabla.columns:
        # Intersección → resaltado Apple
        if row.name == fila and c == col:
            estilos.append(
                "background-color: rgba(14,165,233,0.35); "
                "color: #f9fafb; font-weight: 900; "
                "border: 1px solid rgba(14,165,233,0.55);"
            )
        # Fila seleccionada
        elif row.name == fila:
            estilos.append(
                "text-decoration: underline; font-weight: 700; "
                "color: #e2e8f0;"
            )
        # Columna seleccionada
        elif c == col:
            estilos.append(
                "text-decoration: underline; font-weight: 700; "
                "color: #e2e8f0;"
            )
        else:
            estilos.append("")
    return estilos

# Mostrar tabla con estilo Apple
st.dataframe(
    tabla.style.apply(estilo, axis=1),
    use_container_width=True
)
# =========================================================
# EXPORTACIÓN Y MEMORIA FINAL — ESTILO APPLE
# =========================================================

st.markdown("### 📘 Memoria del cálculo")

df = pd.DataFrame({
    "Parámetro": [
        "Tipo instalación", "Sistema", "Uso",
        "Potencia utilizada (W)", "Intensidad Ib (A)",
        "Longitud (m)", "cos φ",
        "Material", "Aislamiento", "Método REBT",
        "Sección térmica (mm²)",
        "Sección por CdT (mm²)",
        "Sección por CdT normalizada (mm²)",
        "Sección mínima REBT (mm²)",
        "SECCIÓN FINAL (mm²)"
    ],
    "Valor": [
        tipo_instalacion,
        sistema,
        uso,
        f"{potencia_calc:.2f}",
        f"{ib:.2f}",
        f"{longitud:.2f}",
        f"{cos_phi:.2f}",
        material,
        aislamiento,
        metodo,
        f"{s_adm:.2f}",
        f"{s_cdt:.2f}",
        f"{s_cdt_norm:.2f}",
        f"{s_min_rebt:.2f}",
        f"{s_final:.2f}"
    ]
})

# Mostrar tabla memoria estilo Apple
st.dataframe(df, use_container_width=True)

# Generar Excel
excel = exportar_excel(df, "Calculo_Secciones")

# Botón de descarga estilo Apple
st.download_button(
    "📥 Descargar memoria en Excel",
    excel,
    "calculo_secciones.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
