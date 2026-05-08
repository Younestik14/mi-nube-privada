# =========================================================
# INGENIERÍA PRO — macOS Sonoma Glass Premium + Animaciones
# Secciones REBT + FV  ·  Presupuesto Vivienda REBT
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ingeniería Pro — Secciones y Presupuesto",
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

body {{
    background: {bg_body} !important;
    transition: background 0.6s ease-in-out;
}}

* {{
    font-weight: 600 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
}}

.katex, .katex * {{
    font-weight: normal !important;
}}

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

.stRadio > label {{
    padding: 4px 8px !important;
}}

[data-testid="stSlider"] label {{
    color: var(--text-main) !important;
}}

.stButton button {{
    border-radius: 999px !important;
    padding: 10px 26px !important;
    font-size: 15px !important;
    border: 1px solid rgba(148,163,184,0.55) !important;
    background: linear-gradient(135deg, rgba(59,130,246,0.98), rgba(37,99,235,0.98)) !important;
    color: #f9fafb !important;
    box-shadow: 0 18px 40px rgba(37,99,235,0.55);
    transition: transform 0.08s ease, box-shadow 0.12s ease, filter 0.12s ease;
}}
.stButton button:hover {{
    filter: brightness(1.05);
    box-shadow: 0 22px 55px rgba(37,99,235,0.65);
}}
.stButton button:active {{
    transform: translateY(1px) scale(0.99);
    box-shadow: 0 10px 24px rgba(37,99,235,0.55);
}}

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

h1, h2, h3, h4 {{
    color: var(--text-main) !important;
}}

html {{
    scroll-behavior: smooth;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA SUPERIOR
# ---------------------------------------------------------
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <span style="font-size:20px;">⚡</span>
    <span class="topbar-title">Ingeniería Pro</span>
  </div>
  <div class="topbar-menu">
    <span>Secciones</span>
    <span>Presupuesto</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# UTILIDADES COMUNES
# ---------------------------------------------------------
def exportar_excel(df, hoja="Datos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=hoja)
    return output.getvalue()

def tarjeta_formula_latex(latex_str: str):
    st.markdown('<div class="formula-card">', unsafe_allow_html=True)
    st.latex(latex_str)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# SELECCIÓN DE MÓDULO — VENTANA CENTRAL
# ---------------------------------------------------------
if "modo" not in st.session_state:
    st.session_state["modo"] = None

if st.session_state["modo"] is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c_center_left, c_center, c_center_right = st.columns([1, 2, 1])
    with c_center:
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0.5rem;'>Elige el programa</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='text-align:center; color:{text_soft}; margin-bottom:1.5rem;'>Selecciona el módulo con el que quieres trabajar.</p>",
            unsafe_allow_html=True
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button("⚡ Cálculo de secciones REBT + FV", use_container_width=True):
                st.session_state["modo"] = "secciones"
                st.experimental_rerun()
        with b2:
            if st.button("📐 Presupuesto instalación vivienda", use_container_width=True):
                st.session_state["modo"] = "presupuesto"
                st.experimental_rerun()
    st.stop()

modo = st.session_state["modo"]

# Botones para cambiar de módulo en la parte superior
c_mod1, c_mod2, c_mod3 = st.columns([1, 1, 3])
with c_mod1:
    if st.button("⚡ Secciones"):
        st.session_state["modo"] = "secciones"
        st.experimental_rerun()
with c_mod2:
    if st.button("📐 Presupuesto"):
        st.session_state["modo"] = "presupuesto"
        st.experimental_rerun()

# =========================================================
# MÓDULO 1 — CÁLCULO DE SECCIONES REBT + FV
# =========================================================
if modo == "secciones":

    st.markdown(
        "<h1 style='margin-bottom:0.2rem;'>Cálculo de Secciones REBT + FV</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:{text_soft}; margin-top:0;'>Dimensionado de conductores según ITC‑BT‑19, caída de tensión, factores de corrección y cálculos avanzados de línea.</p>",
        unsafe_allow_html=True
    )

    secciones_ref = [
        1.50, 2.50, 4.00, 6.00, 10.00,
        16.00, 25.00, 35.00, 50.00, 70.00,
        95.00, 120.00, 150.00, 185.00, 240.00
    ]

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

    st.markdown("### Justificación de los cálculos (tarjetas premium)")

    if sistema == "Monofásico 230 V":
        tarjeta_formula_latex(
            rf"P = U\,I\,\cos\varphi = {v_fase:.0f}\cdot{ib:.2f}\cdot{cos_phi:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}"
        )
    elif sistema == "Trifásico 400 V":
        tarjeta_formula_latex(
            rf"P = \sqrt{{3}}\,U\,I\,\cos\varphi = \sqrt{{3}}\cdot{v_fase:.0f}\cdot{ib:.2f}\cdot{cos_phi:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}"
        )
    else:
        tarjeta_formula_latex(
            rf"P = U_{{cc}}\,I = {v_fase:.0f}\cdot{ib:.2f} = {potencia_calc:.2f}\,\mathrm{{W}}"
        )

    if sistema == "Trifásico 400 V":
        tarjeta_formula_latex(
            rf"I_b = \dfrac{{P}}{{\sqrt{{3}}\,U\,\cos\varphi}} = \dfrac{{{potencia_calc:.2f}}}{{\sqrt{{3}}\cdot{v_fase:.0f}\cdot{cos_phi:.2f}}} = {ib:.2f}\,\mathrm{{A}}"
        )
    else:
        tarjeta_formula_latex(
            rf"I_b = \dfrac{{P}}{{U\,\cos\varphi}} = \dfrac{{{potencia_calc:.2f}}}{{{v_fase:.0f}\cdot{cos_phi:.2f}}} = {ib:.2f}\,\mathrm{{A}}"
        )

    tarjeta_formula_latex(
        rf"I_{{b,corr}} = \dfrac{{I_b}}{{f_{{temp}}\,f_{{agrup}}}} = \dfrac{{{ib:.2f}}}{{{f_temp:.2f}\cdot{f_agrup:.2f}}} = {ib_corr:.2f}\,\mathrm{{A}}"
    )

    if sistema == "Monofásico 230 V":
        tarjeta_formula_latex(
            rf"{ecuacion_cdt} = \dfrac{{2\cdot{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2"
        )
    elif sistema == "Trifásico 400 V":
        tarjeta_formula_latex(
            rf"{ecuacion_cdt} = \dfrac{{{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2"
        )
    else:
        tarjeta_formula_latex(
            rf"{ecuacion_cdt} = \dfrac{{2\cdot{longitud:.2f}\cdot{potencia_calc:.2f}}}{{{sigma:.2f}\cdot{v_fase:.0f}\cdot{delta_u_max:.2f}}} = {s_cdt:.2f}\,\mathrm{{mm}}^2"
        )

    tarjeta_formula_latex(
        rf"R_{{línea}} = \dfrac{{\rho\cdot2L}}{{S}} = \dfrac{{{rho:.3f}\cdot2\cdot{longitud:.2f}}}{{{s_final:.2f}}} = {r_linea:.4f}\,\Omega"
    )

    tarjeta_formula_latex(
        rf"X_{{línea}} \approx 0.08\ \mathrm{{m\Omega/m}}\cdot2L = 0.08\cdot10^{{-3}}\cdot2\cdot{longitud:.2f} = {x_linea:.4f}\,\Omega"
    )

    tarjeta_formula_latex(
        rf"Z_{{línea}} = \sqrt{{R_{{línea}}^2 + X_{{línea}}^2}} = \sqrt{{{r_linea:.4f}^2 + {x_linea:.4f}^2}} = {z_linea:.4f}\,\Omega"
    )

    if sistema == "Trifásico 400 V":
        tarjeta_formula_latex(
            rf"\Delta U = \sqrt{{3}}\,I_b\,(R_{{línea}}\cos\varphi + X_{{línea}}\sin\varphi) = \sqrt{{3}}\cdot{ib:.2f}\cdot({r_linea:.4f}\cdot{cos_phi:.2f} + {x_linea:.4f}\cdot\sqrt{{1-{cos_phi:.2f}^2}}) = {delta_u_real:.2f}\,\mathrm{{V}}"
        )
    else:
        tarjeta_formula_latex(
            rf"\Delta U = I_b\,(R_{{línea}}\cos\varphi + X_{{línea}}\sin\varphi) = {ib:.2f}\cdot({r_linea:.4f}\cdot{cos_phi:.2f} + {x_linea:.4f}\cdot\sqrt{{1-{cos_phi:.2f}^2}}) = {delta_u_real:.2f}\,\mathrm{{V}}"
        )

    tarjeta_formula_latex(
        rf"I_{{cc,teo}} = \dfrac{{U}}{{Z_{{línea}}}} = \dfrac{{{v_fase:.0f}}}{{{z_linea:.4f}}} = {icc_teorica:.0f}\,\mathrm{{A}}"
    )

    tarjeta_formula_latex(
        rf"I_n \ge I_{{b,corr}} \Rightarrow I_n = {mt_recomendado}\,\mathrm{{A}}"
    )

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

    st.markdown("### Cálculos avanzados de línea")

    c_adv1, c_adv2 = st.columns(2)

    with c_adv1:
        st.markdown(f"**Resistencia de línea (ida y vuelta):** {r_linea:.4f} Ω")
        st.markdown(f"**Reactancia de línea (ida y vuelta):** {x_linea:.4f} Ω")
    with c_adv2:
        st.markdown(f"**Impedancia de línea:** {z_linea:.4f} Ω")
        st.markdown(f"**Corriente de cortocircuito teórica (solo línea):** {icc_teorica:.0f} A")

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

# =========================================================
# MÓDULO 2 — PRESUPUESTO INSTALACIÓN ELÉCTRICA VIVIENDA
# =========================================================
else:
    st.markdown(
        "<h1 style='margin-bottom:0.2rem;'>Presupuesto instalación eléctrica de vivienda</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:{text_soft}; margin-top:0;'>Presupuesto por capítulos (circuitos, derivación individual y cuadro), con productos normalizados, mano de obra, amortización, beneficio e IVA.</p>",
        unsafe_allow_html=True
    )

    # -----------------------------
    # Catálogo de productos normalizados
    # -----------------------------
    st.markdown("### Catálogo de productos normalizados")

    if "catalogo_productos" not in st.session_state:
        st.session_state["catalogo_productos"] = [
            {
                "Referencia": "TC-S-16A",
                "Descripción": "Toma de corriente simple 16 A",
                "Unidad": "ud",
                "Familia": "Tomas",
                "Precio material (€)": 7.50,
                "Precio mano de obra (€)": 5.00
            },
            {
                "Referencia": "TC-D-16A",
                "Descripción": "Toma de corriente doble 16 A",
                "Unidad": "ud",
                "Familia": "Tomas",
                "Precio material (€)": 11.00,
                "Precio mano de obra (€)": 7.00
            },
            {
                "Referencia": "PL-LED",
                "Descripción": "Punto de luz LED empotrado",
                "Unidad": "ud",
                "Familia": "Iluminación",
                "Precio material (€)": 10.00,
                "Precio mano de obra (€)": 4.00
            },
            {
                "Referencia": "INT-S",
                "Descripción": "Interruptor simple",
                "Unidad": "ud",
                "Familia": "Mecanismos",
                "Precio material (€)": 5.00,
                "Precio mano de obra (€)": 4.50
            },
            {
                "Referencia": "INT-C",
                "Descripción": "Interruptor conmutado",
                "Unidad": "ud",
                "Familia": "Mecanismos",
                "Precio material (€)": 7.50,
                "Precio mano de obra (€)": 5.00
            },
            {
                "Referencia": "CGMP-12M",
                "Descripción": "Cuadro general empotrado 12 módulos",
                "Unidad": "ud",
                "Familia": "Cuadros",
                "Precio material (€)": 55.00,
                "Precio mano de obra (€)": 25.00
            },
            {
                "Referencia": "CONJ-PROTECC",
                "Descripción": "Conjunto protecciones (IGA+ID+PIAs)",
                "Unidad": "ud",
                "Familia": "Protecciones",
                "Precio material (€)": 90.00,
                "Precio mano de obra (€)": 35.00
            },
            {
                "Referencia": "CANAL-PVC",
                "Descripción": "Canalización PVC empotrada",
                "Unidad": "m",
                "Familia": "Canalización",
                "Precio material (€)": 2.50,
                "Precio mano de obra (€)": 1.70
            },
            {
                "Referencia": "CABLE-H07V-K",
                "Descripción": "Cable H07V-K 2,5 mm²",
                "Unidad": "m",
                "Familia": "Cableado",
                "Precio material (€)": 1.80,
                "Precio mano de obra (€)": 1.00
            }
        ]

    df_catalogo = pd.DataFrame(st.session_state["catalogo_productos"])
    st.dataframe(df_catalogo, use_container_width=True)

    st.markdown("#### Crear producto personalizado")

    with st.expander("➕ Crear nuevo producto"):
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            ref_new = st.text_input("Referencia", value="")
            desc_new = st.text_input("Descripción", value="")
        with colp2:
            unidad_new = st.text_input("Unidad (ud, m, etc.)", value="ud")
            familia_new = st.text_input("Familia", value="Varios")
        with colp3:
            pm_new = st.number_input("Precio material (€)", value=0.0, min_value=0.0, step=0.10)
            pmo_new = st.number_input("Precio mano de obra (€)", value=0.0, min_value=0.0, step=0.10)

        if st.button("Añadir producto al catálogo"):
            if ref_new and desc_new:
                st.session_state["catalogo_productos"].append({
                    "Referencia": ref_new,
                    "Descripción": desc_new,
                    "Unidad": unidad_new,
                    "Familia": familia_new,
                    "Precio material (€)": pm_new,
                    "Precio mano de obra (€)": pmo_new
                })
                st.success("Producto añadido al catálogo.")
            else:
                st.warning("Referencia y descripción son obligatorias.")

    df_catalogo = pd.DataFrame(st.session_state["catalogo_productos"])

    # -----------------------------
    # Parámetros económicos globales
    # -----------------------------
    st.markdown("### Parámetros económicos globales")

    colg1, colg2, colg3, colg4 = st.columns(4)
    with colg1:
        iva_pct = st.number_input("IVA (%)", value=21.0, min_value=0.0, max_value=30.0, step=0.5)
    with colg2:
        amort_pct = st.number_input("Amortización / gastos generales (%)", value=10.0, min_value=0.0, max_value=50.0, step=0.5)
    with colg3:
        benef_pct = st.number_input("Beneficio industrial (%)", value=15.0, min_value=0.0, max_value=50.0, step=0.5)
    with colg4:
        mano_obra_hora = st.number_input("Precio mano de obra base (€/h)", value=22.0, min_value=0.0, step=0.5)

    # -----------------------------
    # Capítulos por circuito (cada uno en su bloque)
    # -----------------------------
    st.markdown("### Capítulos por circuito y elementos principales")

    capitulos = [
        "C1 - Iluminación",
        "C2 - Tomas de uso general",
        "C3 - Cocina y horno",
        "C4 - Lavadora / lavavajillas",
        "C5 - Baños y auxiliares",
        "C6 - Climatización",
        "C7 - Derivación individual",
        "C8 - Cuadro general"
    ]

    datos_capitulos = []

    for cap in capitulos:
        with st.expander(cap, expanded=False):
            st.markdown(f"**{cap}**")

            colc1, colc2 = st.columns(2)
            with colc1:
                horas_cap = st.number_input(
                    f"Horas de mano de obra ({cap})",
                    value=0.0,
                    min_value=0.0,
                    step=0.5,
                    key=f"horas_{cap}"
                )
            with colc2:
                productos_sel = st.multiselect(
                    f"Productos a incluir en {cap}",
                    options=df_catalogo["Descripción"].tolist(),
                    key=f"productos_{cap}"
                )

            # Cálculo de materiales y mano de obra por productos
            mat_total = 0.0
            mo_total_prod = 0.0

            for desc in productos_sel:
                fila = df_catalogo[df_catalogo["Descripción"] == desc]
                if fila.empty:
                    continue
                pm = float(fila["Precio material (€)"].iloc[0])
                pmo = float(fila["Precio mano de obra (€)"].iloc[0])
                unidad = fila["Unidad"].iloc[0]

                qty = st.number_input(
                    f"Cantidad de '{desc}' ({unidad}) en {cap}",
                    value=1.0,
                    min_value=0.0,
                    step=1.0 if unidad == "ud" else 0.5,
                    key=f"qty_{cap}_{desc}"
                )

                mat_total += pm * qty
                mo_total_prod += pmo * qty

            mo_horas = horas_cap * mano_obra_hora
            mo_total = mo_total_prod + mo_horas
            base_cap = mat_total + mo_total

            gastos_generales = base_cap * (amort_pct / 100.0)
            beneficio = (base_cap + gastos_generales) * (benef_pct / 100.0)
            base_imponible = base_cap + gastos_generales + beneficio
            iva = base_imponible * (iva_pct / 100.0)
            total_cap = base_imponible + iva

            datos_capitulos.append({
                "Capítulo": cap,
                "Material (€)": mat_total,
                "Mano de obra (€)": mo_total,
                "Base capítulo (€)": base_cap,
                "Gastos generales (€)": gastos_generales,
                "Beneficio (€)": beneficio,
                "Base imponible (€)": base_imponible,
                "IVA (€)": iva,
                "Total capítulo (€)": total_cap
            })

            st.markdown("**Justificación capítulo (tarjetas premium)**")

            tarjeta_formula_latex(
                rf"\text{{Material capítulo}} = \sum (p_{{m,i}}\cdot q_i) = {mat_total:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Mano de obra productos}} = \sum (p_{{mo,i}}\cdot q_i) = {mo_total_prod:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Mano de obra directa}} = {horas_cap:.2f}\cdot{mano_obra_hora:.2f} = {mo_horas:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Mano de obra total}} = {mo_total_prod:.2f}+{mo_horas:.2f} = {mo_total:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Base capítulo}} = {mat_total:.2f}+{mo_total:.2f} = {base_cap:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Gastos generales}} = {base_cap:.2f}\cdot{amort_pct:.2f}\% = {gastos_generales:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Beneficio}} = ({base_cap:.2f}+{gastos_generales:.2f})\cdot{benef_pct:.2f}\% = {beneficio:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Base imponible}} = {base_cap:.2f}+{gastos_generales:.2f}+{beneficio:.2f} = {base_imponible:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{IVA}} = {base_imponible:.2f}\cdot{iva_pct:.2f}\% = {iva:.2f}\ \mathrm{{€}}"
            )
            tarjeta_formula_latex(
                rf"\text{{Total capítulo}} = {base_imponible:.2f}+{iva:.2f} = {total_cap:.2f}\ \mathrm{{€}}"
            )

    # -----------------------------
    # Resumen global del presupuesto
    # -----------------------------
    st.markdown("### Resumen global del presupuesto")

    if len(datos_capitulos) == 0:
        st.info("Introduce datos en al menos un capítulo para generar el resumen.")
    else:
        df_caps = pd.DataFrame(datos_capitulos)

        st.dataframe(df_caps.style.format({
            "Material (€)": "{:.2f}",
            "Mano de obra (€)": "{:.2f}",
            "Base capítulo (€)": "{:.2f}",
            "Gastos generales (€)": "{:.2f}",
            "Beneficio (€)": "{:.2f}",
            "Base imponible (€)": "{:.2f}",
            "IVA (€)": "{:.2f}",
            "Total capítulo (€)": "{:.2f}"
        }), use_container_width=True)

        total_material = df_caps["Material (€)"].sum()
        total_mo = df_caps["Mano de obra (€)"].sum()
        total_base = df_caps["Base capítulo (€)"].sum()
        total_gastos = df_caps["Gastos generales (€)"].sum()
        total_benef = df_caps["Beneficio (€)"].sum()
        total_base_imp = df_caps["Base imponible (€)"].sum()
        total_iva = df_caps["IVA (€)"].sum()
        total_final = df_caps["Total capítulo (€)"].sum()

        st.markdown(
            f"<h2 style='margin-top:1rem; font-weight:700;'>💰 Presupuesto total (con IVA): {total_final:.2f} €</h2>",
            unsafe_allow_html=True
        )

        st.markdown("### Desglose global")

        coltot1, coltot2, coltot3, coltot4 = st.columns(4)
        with coltot1:
            st.markdown(f"**Material total:** {total_material:.2f} €")
            st.markdown(f"**Mano de obra total:** {total_mo:.2f} €")
        with coltot2:
            st.markdown(f"**Base capítulos:** {total_base:.2f} €")
            st.markdown(f"**Gastos generales:** {total_gastos:.2f} €")
        with coltot3:
            st.markdown(f"**Beneficio industrial:** {total_benef:.2f} €")
            st.markdown(f"**Base imponible:** {total_base_imp:.2f} €")
        with coltot4:
            st.markdown(f"**IVA total:** {total_iva:.2f} €")
            st.markdown(f"**Total presupuesto:** {total_final:.2f} €")

        st.markdown("### Exportación del presupuesto")

        excel_presupuesto = exportar_excel(df_caps, "Presupuesto_Vivienda")

        st.download_button(
            "📥 Descargar presupuesto (Excel)",
            excel_presupuesto,
            "presupuesto_vivienda.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
