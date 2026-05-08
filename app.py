# =========================================================
# INGENIERÍA PRO — macOS Sonoma Glass Premium + Animaciones
# Cálculo de secciones REBT + FV con justificación compacta
# en tarjetas animadas estilo Apple Pro Apps
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ingeniería Pro — Secciones REBT + FV",
    layout="wide",
    page_icon="⚡"
)

# ---------------------------------------------------------
# MODO CLARO / OSCURO (macOS Sonoma Glass)
# ---------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "Oscuro"

top_left, top_mid, top_right = st.columns([1.5, 2, 2])

with top_left:
    theme = st.radio("Tema", ["Oscuro", "Claro"], index=0 if st.session_state["theme"] == "Oscuro" else 1)
    st.session_state["theme"] = theme

if theme == "Oscuro":
    bg_body = "radial-gradient(circle at top, #020617 0%, #020617 40%, #020617 100%)"
    text_main = "#f9fafb"
    text_soft = "#9ca3af"
    input_bg = "rgba(15,23,42,0.85)"
    input_border = "rgba(148,163,184,0.55)"
    df_bg = "rgba(15,23,42,0.90)"
    bar_bg = "rgba(15,23,42,0.88)"
    bar_border = "rgba(148,163,184,0.55)"
    card_bg = "rgba(15,23,42,0.88)"
    card_border = "rgba(148,163,184,0.65)"
else:
    bg_body = "radial-gradient(circle at top, #e5e7eb 0%, #f3f4f6 40%, #f9fafb 100%)"
    text_main = "#020617"
    text_soft = "#4b5563"
    input_bg = "rgba(255,255,255,0.90)"
    input_border = "rgba(148,163,184,0.55)"
    df_bg = "rgba(255,255,255,0.96)"
    bar_bg = "rgba(255,255,255,0.90)"
    bar_border = "rgba(148,163,184,0.55)"
    card_bg = "rgba(255,255,255,0.92)"
    card_border = "rgba(148,163,184,0.65)"

# ---------------------------------------------------------
# ESTILO GLOBAL — macOS SONOMA GLASS PREMIUM + ANIMACIONES
# ---------------------------------------------------------
st.markdown(f"""
<style>
:root {{
    --text-main: {text_main};
    --text-soft: {text_soft};
}}

/* Fondo general tipo Sonoma Glass */
body {{
    background: {bg_body} !important;
    transition: background 0.6s ease-in-out;
}}

/* Tipografía global */
* {{
    font-weight: 600 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
}}

/* KaTeX normal (no bold) */
.katex, .katex * {{
    font-weight: normal !important;
}}

/* Barra superior estilo macOS Pro Apps */
.topbar {{
    width: 100%;
    padding: 10px 18px;
    margin-bottom: 10px;
    border-radius: 18px;
    background: {bar_bg};
    border: 1px solid {bar_border};
    backdrop-filter: blur(26px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--text-main);
    box-shadow: 0 22px 55px rgba(15,23,42,0.55);
    transition: box-shadow 0.25s ease, transform 0.25s ease, background 0.4s ease;
}}
.topbar:hover {{
    box-shadow: 0 26px 70px rgba(15,23,42,0.65);
    transform: translateY(-1px);
}}
.topbar-left {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.topbar-title {{
    font-size: 18px;
    font-weight: 700;
}}
.topbar-menu span {{
    margin-left: 18px;
    font-size: 14px;
    color: var(--text-soft);
    cursor: default;
    transition: color 0.2s ease;
}}
.topbar-menu span:hover {{
    color: var(--text-main);
}}

/* Inputs y selects estilo Sonoma Glass + animaciones */
.stNumberInput input,
.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stRadio > label {{
    background: {input_bg} !important;
    color: var(--text-main) !important;
    border-radius: 14px !important;
    border: 1px solid {input_border} !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    backdrop-filter: blur(20px);
    transition: border 0.2s ease, box-shadow 0.2s ease, transform 0.08s ease, background 0.3s ease;
}}
.stNumberInput input:focus,
.stTextInput input:focus {{
    border: 1px solid rgba(96,165,250,0.95) !important;
    box-shadow: 0 0 0 1px rgba(96,165,250,0.85);
    transform: translateY(-1px);
}}

/* Radio labels */
.stRadio > label {{
    padding: 4px 8px !important;
}}

/* Slider label color */
[data-testid="stSlider"] label {{
    color: var(--text-main) !important;
}}

/* Botones estilo macOS Pro */
.stButton button {{
    border-radius: 999px !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
    border: 1px solid rgba(148,163,184,0.55) !important;
    background: linear-gradient(135deg, rgba(59,130,246,0.98), rgba(37,99,235,0.98)) !important;
    color: #f9fafb !important;
    box-shadow: 0 14px 32px rgba(37,99,235,0.55);
    transition: transform 0.08s ease, box-shadow 0.12s ease, filter 0.12s ease;
}}
.stButton button:hover {{
    filter: brightness(1.05);
    box-shadow: 0 18px 40px rgba(37,99,235,0.65);
}}
.stButton button:active {{
    transform: translateY(1px) scale(0.99);
    box-shadow: 0 8px 20px rgba(37,99,235,0.55);
}}

/* Línea divisoria entre bloques */
.ecuacion-divider {{
    width: 100%;
    height: 3px;
    background: rgba(255,255,255,0.35);
    margin: 22px 0;
    border-radius: 3px;
    opacity: 0.9;
}}

/* Tarjetas de fórmula estilo Sonoma Glass Premium */
.formula-card {{
    background: {card_bg};
    border-radius: 18px;
    border: 1px solid {card_border};
    backdrop-filter: blur(26px);
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 18px 45px rgba(15,23,42,0.55);
    transition: box-shadow 0.25s ease, transform 0.18s ease, background 0.3s ease, border-color 0.3s ease;
    opacity: 0.98;
}}
.formula-card:hover {{
    box-shadow: 0 24px 60px rgba(15,23,42,0.70);
    transform: translateY(-1px);
    border-color: rgba(96,165,250,0.85);
}}

/* Dataframe más integrado */
[data-testid="stDataFrame"] {{
    border-radius: 18px !important;
    overflow: hidden !important;
    background: {df_bg} !important;
    backdrop-filter: blur(22px);
    transition: box-shadow 0.25s ease, transform 0.15s ease;
}}
[data-testid="stDataFrame"]:hover {{
    box-shadow: 0 22px 55px rgba(15,23,42,0.45);
    transform: translateY(-1px);
}}

/* Títulos */
h1, h2, h3, h4 {{
    color: var(--text-main) !important;
}}

/* Scroll suave */
html {{
    scroll-behavior: smooth;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA SUPERIOR ESTILO macOS
# ---------------------------------------------------------
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <span style="font-size:20px;">⚡</span>
    <span class="topbar-title">Ingeniería Pro</span>
  </div>
  <div class="topbar-menu">
    <span>Archivo</span>
    <span>Exportar</span>
    <span>Ayuda</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CABECERA
# ---------------------------------------------------------
st.markdown(
    "<h1 style='font-weight:700; margin-bottom:0.2rem;'>Cálculo de Secciones REBT + FV</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<p style='color:{text_soft}; margin-top:0;'>Dimensionado de conductores según ITC‑BT‑19, caída de tensión, factores de corrección y cálculos avanzados de línea.</p>",
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------
def exportar_excel(df, hoja="Datos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=hoja)
    return output.getvalue()

# ---------------------------------------------------------
# SECCIONES NORMALIZADAS
# ---------------------------------------------------------
secciones_ref = [
    1.50, 2.50, 4.00, 6.00, 10.00,
    16.00, 25.00, 35.00, 50.00, 70.00,
    95.00, 120.00, 150.00, 185.00, 240.00
]

# ---------------------------------------------------------
# TABLAS REBT ITC-BT-19
# ---------------------------------------------------------
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

def get_seccion_adm(metodo, aislamiento, ib):
    ais = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm[metodo][ais]
    for i, intensidad in enumerate(intensidades):
        if intensidad >= ib:
            return secciones_ref[i]
    return 240.00

# ---------------------------------------------------------
# FORMULARIO PRINCIPAL
# ---------------------------------------------------------
st.markdown("### Datos de diseño")

c1, c2 = st.columns(2)

with c1:
    tipo_instalacion = st.selectbox("Tipo de instalación", ["CA REBT (general)", "FV en corriente continua"])
    sistema = st.selectbox(
        "Sistema eléctrico",
        ["Monofásico 230 V", "Trifásico 400 V"] if tipo_instalacion == "CA REBT (general)" else ["Corriente continua FV"]
    )
    modo_intensidad = st.selectbox("Modo de cálculo de intensidad", ["A partir de potencia", "Introducir intensidad directamente"])

    if modo_intensidad == "A partir de potencia":
        potencia = st.number_input("Potencia (W)", value=5750.0, min_value=0.0, step=50.0)
    else:
        ib_input = st.number_input("Intensidad Ib (A)", value=25.0, min_value=0.0, step=1.0)

    longitud = st.number_input("Longitud del circuito (m)", value=30.0, min_value=0.0, step=1.0)
    cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90) if tipo_instalacion == "CA REBT (general)" else 1.00
    uso = st.selectbox("Tipo de circuito", ["General", "Motores", "Vehículo eléctrico", "Fotovoltaica"])

with c2:
    material = st.radio("Material del conductor", ["Cobre (Cu)", "Aluminio (Al)"])
    aislamiento = st.radio("Aislamiento", ["PVC (70 °C)", "XLPE/EPR (90 °C)"])
    metodo = st.selectbox("Método de instalación (ITC‑BT‑19)", list(tablas_adm.keys()))
    max_cdt_pct = st.number_input("Caída de tensión máxima permitida (%)", value=3.0, min_value=0.1, max_value=10.0, step=0.1)
    v_cc = st.number_input("Tensión FV (Vcc)", value=600.0, min_value=0.0, step=10.0) if tipo_instalacion == "FV en corriente continua" else None

    st.markdown("#### Factores de corrección (opcional)")
    f_temp = st.number_input("Factor de temperatura", value=1.00, min_value=0.50, max_value=1.20, step=0.01)
    f_agrup = st.number_input("Factor de agrupamiento", value=1.00, min_value=0.30, max_value=1.00, step=0.01)

# ---------------------------------------------------------
# CÁLCULOS ELÉCTRICOS BÁSICOS
# ---------------------------------------------------------
k_u = 1.25 if uso in ["Motores", "Vehículo eléctrico"] else 1.0

if sistema == "Monofásico 230 V":
    v_fase = 230.0
elif sistema == "Trifásico 400 V":
    v_fase = 400.0
else:
    v_fase = v_cc

delta_u_max = (max_cdt_pct / 100.0) * v_fase

if modo_intensidad == "Introducir intensidad directamente":
    ib = ib_input
    if sistema == "Trifásico 400 V":
        potencia_calc = math.sqrt(3.0) * v_fase * ib * cos_phi
    else:
        potencia_calc = v_fase * ib * cos_phi
else:
    potencia_calc = potencia * k_u
    if sistema == "Trifásico 400 V":
        ib = potencia_calc / (math.sqrt(3.0) * v_fase * cos_phi)
    else:
        ib = potencia_calc / (v_fase * cos_phi)

ib_corr = ib / (f_temp * f_agrup)
s_adm = get_seccion_adm(metodo, aislamiento, ib_corr)

sigma = 48.0 if "Cobre" in material else 30.0
if "XLPE" in aislamiento:
    sigma -= 4.0

if sistema == "Monofásico 230 V":
    s_cdt = (2.0 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_cdt = r"S_{cdt,mono}=\dfrac{2\,L\,P}{\sigma\,U\,\Delta U_{{\max}}}"
elif sistema == "Trifásico 400 V":
    s_cdt = (longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_cdt = r"S_{cdt,tri}=\dfrac{L\,P}{\sigma\,U\,\Delta U_{{\max}}}"
else:
    s_cdt = (2.0 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
    ecuacion_cdt = r"S_{cdt,FV}=\dfrac{2\,L\,P}{\sigma\,U_{{cc}}\,\Delta U_{{\max}}}"

s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240.00)

s_min_rebt = {
    "General": 1.5,
    "Motores": 2.5,
    "Vehículo eléctrico": 6.0,
    "Fotovoltaica": 4.0
}[uso]

s_final = max(s_adm, s_cdt_norm, s_min_rebt)

# ---------------------------------------------------------
# CÁLCULOS AVANZADOS (R, X, Z, ΔU real, magnetotérmico)
# ---------------------------------------------------------
rho = 0.018 if "Cobre" in material else 0.028

r_linea = (rho * 2.0 * longitud) / s_final
x_linea = 0.08e-3 * 2.0 * longitud
z_linea = math.sqrt(r_linea**2 + x_linea**2)

if sistema == "Trifásico 400 V":
    delta_u_real = math.sqrt(3.0) * ib * (r_linea * cos_phi + x_linea * math.sqrt(max(0.0, 1 - cos_phi**2)))
else:
    delta_u_real = ib * (r_linea * cos_phi + x_linea * math.sqrt(max(0.0, 1 - cos_phi**2)))

delta_u_real_pct = (delta_u_real / v_fase) * 100.0 if v_fase > 0 else 0.0

magnetos = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]
mt_recomendado = next((m for m in magnetos if m >= ib_corr), magnetos[-1])

icc_teorica = v_fase / z_linea if z_linea > 0 else 0.0

# ---------------------------------------------------------
# JUSTIFICACIÓN EN TARJETAS — ESTILO B COMPACTO
# ---------------------------------------------------------
st.markdown("### Justificación de los cálculos (tarjetas compactas)")

# Potencia
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    if sistema == "Monofásico 230 V":
        st.latex(rf"P = U\,I\,\cos\varphi = {v_fase:.0f}\cdot{ib:.2f}\cdot{cos_phi:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}")
    elif sistema == "Trifásico 400 V":
        st.latex(rf"P = \sqrt{{3}}\,U\,I\,\cos\varphi = \sqrt{{3}}\cdot{v_fase:.0f}\cdot{ib:.2f}\cdot{cos_phi:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}")
    else:
        st.latex(rf"P = U_{{cc}}\,I = {v_fase:.0f}\cdot{ib:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}")
    st.markdown('</div>', unsafe_allow_html=True)

# Intensidad Ib
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    if sistema == "Trifásico 400 V":
        st.latex(rf"I_b = \dfrac{{P}}{{\sqrt{{3}}\,U\,\cos\varphi}} = \dfrac{{{potencia_calc:.2f}}}{{\sqrt{{3}}\cdot{v_fase:.0f}\cdot{cos_phi:.2f}}} = {ib:.2f}\,\mathrm{{A}}")
    else:
        st.latex(rf"I_b = \dfrac{{P}}{{U\,\cos\varphi}} = \dfrac{{{potencia_calc:.2f}}}{{{v_fase:.0f}\cdot{cos_phi:.2f}}} = {ib:.2f}\,\mathrm{{A}}")
    st.markdown('</div>', unsafe_allow_html=True)

# Intensidad corregida
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"I_{{b,corr}} = \dfrac{{I_b}}{{f_{{temp}}\,f_{{agrup}}}} = \dfrac{{{ib:.2f}}}{{{f_temp:.2f}\cdot{f_agrup:.2f}}} = {ib_corr:.2f}\,\mathrm{{A}}")
    st.markdown('</div>', unsafe_allow_html=True)

# Sección por caída de tensión
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    if sistema == "Monofásico 230 V":
        st.latex(rf"{ecuacion_cdt} = \dfrac{{2\cdot{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2")
    elif sistema == "Trifásico 400 V":
        st.latex(rf"{ecuacion_cdt} = \dfrac{{{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2")
    else:
        st.latex(rf"{ecuacion_cdt} = \dfrac{{2\cdot{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2")
    st.markdown('</div>', unsafe_allow_html=True)

# Resistencia de línea
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"R_{{línea}} = \dfrac{{\rho\cdot2L}}{{S}} = \dfrac{{{rho:.3f}\cdot2\cdot{longitud:.2f}}}{{{s_final:.2f}}} = {r_linea:.4f}\,\Omega")
    st.markdown('</div>', unsafe_allow_html=True)

# Reactancia de línea
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"X_{{línea}} \approx 0.08\ \mathrm{{m\Omega/m}}\cdot2L = 0.08\cdot10^{{-3}}\cdot2\cdot{longitud:.2f} = {x_linea:.4f}\,\Omega")
    st.markdown('</div>', unsafe_allow_html=True)

# Impedancia de línea
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"Z_{{línea}} = \sqrt{{R_{{línea}}^2 + X_{{línea}}^2}} = \sqrt{{{r_linea:.4f}^2 + {x_linea:.4f}^2}} = {z_linea:.4f}\,\Omega")
    st.markdown('</div>', unsafe_allow_html=True)

# Caída de tensión real
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    if sistema == "Trifásico 400 V":
        st.latex(rf"\Delta U = \sqrt{{3}}\,I_b\,(R_{{línea}}\cos\varphi + X_{{línea}}\sin\varphi) = \sqrt{{3}}\cdot{ib:.2f}\cdot({r_linea:.4f}\cdot{cos_phi:.2f} + {x_linea:.4f}\cdot\sqrt{{1-{cos_phi:.2f}^2}}) = {delta_u_real:.2f}\,\mathrm{{V}}")
    else:
        st.latex(rf"\Delta U = I_b\,(R_{{línea}}\cos\varphi + X_{{línea}}\sin\varphi) = {ib:.2f}\cdot({r_linea:.4f}\cdot{cos_phi:.2f} + {x_linea:.4f}\cdot\sqrt{{1-{cos_phi:.2f}^2}}) = {delta_u_real:.2f}\,\mathrm{{V}}")
    st.markdown('</div>', unsafe_allow_html=True)

# Corriente de cortocircuito teórica
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"I_{{cc,teo}} = \dfrac{{U}}{{Z_{{línea}}}} = \dfrac{{{v_fase:.0f}}}{{{z_linea:.4f}}} = {icc_teorica:.0f}\,\mathrm{{A}}")
    st.markdown('</div>', unsafe_allow_html=True)

# Magnetotérmico recomendado
with st.container():
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(rf"I_n \ge I_{{b,corr}} \Rightarrow I_n = {mt_recomendado}\,\mathrm{{A}}")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TABLA ITC-BT-19 — RESALTADO DINÁMICO
# ---------------------------------------------------------
st.markdown("### Tabla ITC‑BT‑19 — Intensidades admisibles")

tabla = pd.DataFrame({
    "Sección (mm²)": [f"{s:.2f}" for s in secciones_ref],
    "PVC (A)": [f"{x:.2f}" for x in tablas_adm[metodo]["PVC"]],
    "XLPE (A)": [f"{x:.2f}" for x in tablas_adm[metodo]["XLPE"]]
})

fila = None
if f"{s_final:.2f}" in tabla["Sección (mm²)"].values:
    fila = tabla.index[tabla["Sección (mm²)"] == f"{s_final:.2f}"][0]

col = "PVC (A)" if "PVC" in aislamiento else "XLPE (A)"

def estilo(row):
    estilos = []
    for c in tabla.columns:
        if row.name == fila and c == col:
            estilos.append(
                "background-color: rgba(255,255,255,0.25); color: #ffffff; font-weight: 900; transition: background-color 0.25s ease;"
            )
        elif row.name == fila:
            estilos.append(
                "text-decoration: underline; font-weight: 700; color: #e2e8f0; transition: color 0.25s ease;"
            )
        elif c == col:
            estilos.append(
                "text-decoration: underline; font-weight: 700; color: #e2e8f0; transition: color 0.25s ease;"
            )
        else:
            estilos.append("")
    return estilos

st.dataframe(
    tabla.style.apply(estilo, axis=1),
    use_container_width=True
)

# ---------------------------------------------------------
# RESULTADOS PRINCIPALES
# ---------------------------------------------------------
st.markdown("### Resultados principales")

c_res1, c_res2, c_res3 = st.columns(3)

with c_res1:
    st.markdown(f"**Sección térmica ITC‑BT‑19:** {s_adm:.2f} mm²")
    st.markdown(f"**Sección por CdT normalizada:** {s_cdt_norm:.2f} mm²")

with c_res2:
    st.markdown(f"**Sección mínima REBT por uso:** {s_min_rebt:.2f} mm²")
    st.markdown(f"**Sección final reglamentaria:** {s_final:.2f} mm²")

with c_res3:
    st.markdown(f"**Caída de tensión real:** {delta_u_real:.2f} V")
    st.markdown(f"**Caída de tensión real:** {delta_u_real_pct:.2f} %")

st.markdown(f"**Magnetotérmico recomendado (In):** {mt_recomendado} A")

# ---------------------------------------------------------
# CÁLCULOS AVANZADOS — IMPEDANCIA Y LÍNEA
# ---------------------------------------------------------
st.markdown("### Cálculos avanzados de línea")

c_adv1, c_adv2 = st.columns(2)

with c_adv1:
    st.markdown(f"**Resistencia de línea (ida y vuelta):** {r_linea:.4f} Ω")
    st.markdown(f"**Reactancia de línea (ida y vuelta):** {x_linea:.4f} Ω")
with c_adv2:
    st.markdown(f"**Impedancia de línea:** {z_linea:.4f} Ω")
    st.markdown(f"**Corriente de cortocircuito teórica (solo línea):** {icc_teorica:.0f} A")

# ---------------------------------------------------------
# MEMORIA + EXPORTACIÓN EXCEL
# ---------------------------------------------------------
st.markdown("### Memoria del cálculo")

df = pd.DataFrame({
    "Parámetro": [
        "Tema visual",
        "Tipo instalación", "Sistema", "Uso",
        "Potencia utilizada (W)", "Intensidad Ib (A)", "Intensidad Ib corregida (A)",
        "Longitud (m)", "cos φ",
        "Material", "Aislamiento", "Método REBT",
        "Factor temperatura", "Factor agrupamiento",
        "Sección térmica ITC‑BT‑19 (mm²)",
        "Sección por CdT (mm²)",
        "Sección por CdT normalizada (mm²)",
        "Sección mínima REBT (mm²)",
        "SECCIÓN FINAL (mm²)",
        "Resistencia línea (Ω)",
        "Reactancia línea (Ω)",
        "Impedancia línea (Ω)",
        "Caída de tensión real (V)",
        "Caída de tensión real (%)",
        "Magnetotérmico recomendado (A)",
        "Icc teórica (A)"
    ],
    "Valor": [
        theme,
        tipo_instalacion, sistema, uso,
        f"{potencia_calc:.2f}", f"{ib:.2f}", f"{ib_corr:.2f}",
        f"{longitud:.2f}", f"{cos_phi:.2f}",
        material, aislamiento, metodo,
        f"{f_temp:.2f}", f"{f_agrup:.2f}",
        f"{s_adm:.2f}",
        f"{s_cdt:.2f}",
        f"{s_cdt_norm:.2f}",
        f"{s_min_rebt:.2f}",
        f"{s_final:.2f}",
        f"{r_linea:.4f}",
        f"{x_linea:.4f}",
        f"{z_linea:.4f}",
        f"{delta_u_real:.2f}",
        f"{delta_u_real_pct:.2f}",
        f"{mt_recomendado:.0f}",
        f"{icc_teorica:.0f}"
    ]
})

st.dataframe(df, use_container_width=True)

excel = exportar_excel(df, "Calculo_Secciones")

st.download_button(
    "📥 Descargar memoria en Excel",
    excel,
    "calculo_secciones.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
