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

</style>
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
# MENÚ PRINCIPAL — VENTANA CENTRAL
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
                st.rerun()
        with b2:
            if st.button("📐 Presupuesto instalación vivienda", use_container_width=True):
                st.session_state["modo"] = "presupuesto"
                st.rerun()
    st.stop()

modo = st.session_state["modo"]
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

    # ---------------------------------------------------------
    # TABLAS ITC‑BT‑19 — Intensidades admisibles
    # ---------------------------------------------------------

    secciones_ref = [
        1.50, 2.50, 4.00, 6.00, 10.00,
        16.00, 25.00, 35.00, 50.00, 70.00,
        95.00, 120.00, 150.00, 185.00, 240.00
    ]

    tablas_adm = {
        "A1 - Empotrado en tubo (pared aislante)": {
            "desc": "Empotrado en pared aislante (tubo)",
            "PVC":  [14.50,19.50,26.00,34.00,46.00,61.00,80.00,99.00,119.00,151.00,182.00,210.00,240.00,273.00,321.00],
            "XLPE": [18.50,25.00,33.00,43.00,59.00,77.00,102.00,126.00,153.00,194.00,233.00,268.00,307.00,352.00,415.00]
        },
        "B1 - Conductores en tubo sobre pared": {
            "desc": "Tubo sobre pared",
            "PVC":  [17.50,24.00,32.00,41.00,57.00,76.00,101.00,125.00,151.00,192.00,232.00,269.00,300.00,341.00,400.00],
            "XLPE": [22.00,30.00,40.00,52.00,71.00,94.00,126.00,157.00,190.00,241.00,292.00,338.00,388.00,442.00,523.00]
        },
        "C - Cable directamente sobre pared": {
            "desc": "Cable directamente sobre pared",
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
    # ENTRADA DE DATOS
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
    # CÁLCULO DE INTENSIDAD
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

    # ---------------------------------------------------------
    # SECCIÓN POR TÉRMICA (ITC‑BT‑19)
    # ---------------------------------------------------------

    s_adm = get_seccion_adm(metodo, aislamiento, ib_corr)

    # ---------------------------------------------------------
    # SECCIÓN POR CAÍDA DE TENSIÓN
    # ---------------------------------------------------------

    sigma = 48.0 if "Cobre" in material else 30.0
    if "XLPE" in aislamiento:
        sigma -= 4.0

    if sistema == "Monofásico 230 V":
        s_cdt = (2.0 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
        ecuacion_cdt = r"S_{cdt,mono}=\dfrac{2\,L\,P}{\sigma\,U\,\Delta U_{\max}}"
    elif sistema == "Trifásico 400 V":
        s_cdt = (longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
        ecuacion_cdt = r"S_{cdt,tri}=\dfrac{L\,P}{\sigma\,U\,\Delta U_{\max}}"
    else:
        s_cdt = (2.0 * longitud * potencia_calc) / (sigma * v_fase * delta_u_max)
        ecuacion_cdt = r"S_{cdt,FV}=\dfrac{2\,L\,P}{\sigma\,U_{cc}\,\Delta U_{\max}}"

    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240.00)

    # ---------------------------------------------------------
    # SECCIÓN MÍNIMA REBT
    # ---------------------------------------------------------

    s_min_rebt = {
        "General": 1.5,
        "Motores": 2.5,
        "Vehículo eléctrico": 6.0,
        "Fotovoltaica": 4.0
    }[uso]

    # ---------------------------------------------------------
    # SECCIÓN FINAL
    # ---------------------------------------------------------

    s_final = max(s_adm, s_cdt_norm, s_min_rebt)

    # ---------------------------------------------------------
    # CÁLCULOS AVANZADOS DE LÍNEA
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
    # JUSTIFICACIÓN EN TARJETAS PREMIUM
    # ---------------------------------------------------------

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

    tarjeta_formula_latex(
        rf"I_{{b,corr}} = \dfrac{{I_b}}{{f_{{temp}}\,f_{{agrup}}}} = \dfrac{{{ib:.2f}}}{{{f_temp:.2f}\cdot{f_agrup:.2f}}} = {ib_corr:.2f}\,\mathrm{{A}}"
    )

    tarjeta_formula_latex(
        rf"{ecuacion_cdt} = {s_cdt:.2f}\,\mathrm{{mm}}^2"
    )

    tarjeta_formula_latex(
        rf"R_{{línea}} = \dfrac{{\rho\cdot2L}}{{S}} = {r_linea:.4f}\,\Omega"
    )

    tarjeta_formula_latex(
        rf"Z_{{línea}} = \sqrt{{R_{{línea}}^2 + X_{{línea}}^2}} = {z_linea:.4f}\,\Omega"
    )

    tarjeta_formula_latex(
        rf"I_{{cc,teo}} = \dfrac{{U}}{{Z_{{línea}}}} = {icc_teorica:.0f}\,\mathrm{{A}}"
    )

    tarjeta_formula_latex(
        rf"I_n \ge I_{{b,corr}} \Rightarrow I_n = {mt_recomendado}\,\mathrm{{A}}"
    )

    # ---------------------------------------------------------
    # TABLA ITC‑BT‑19 — ENCABEZADO COMPLETO
    # ---------------------------------------------------------

    st.markdown("### Tabla ITC‑BT‑19 — Intensidades admisibles")

    st.markdown(
        f"""
        <div style='padding:10px 0; color:{text_main};'>
        <b>Método:</b> {metodo}<br>
        <b>Descripción:</b> {tablas_adm[metodo]['desc']}<br>
        <b>Tipo de instalación:</b> {tipo_instalacion}<br>
        <b>Sistema:</b> {sistema}
        </div>
        """,
        unsafe_allow_html=True
    )

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
                estilos.append("background-color: rgba(255,255,255,0.25); color: #ffffff; font-weight: 900;")
            elif row.name == fila:
                estilos.append("text-decoration: underline; font-weight: 700; color: #e2e8f0;")
            elif c == col:
                estilos.append("text-decoration: underline; font-weight: 700; color: #e2e8f0;")
            else:
                estilos.append("")
        return estilos

    st.dataframe(
        tabla.style.apply(estilo, axis=1),
        use_container_width=True
    )

    # ---------------------------------------------------------
    # RESULTADOS
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
    # EXPORTACIÓN
    # ---------------------------------------------------------

    df = pd.DataFrame({
        "Parámetro": [
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
            "Resistencia"
# CATÁLOGO NORMALIZADO — PESTAÑAS POR FAMILIAS
# =========================================================

if modo == "presupuesto":

    st.markdown(
        "<h1 style='margin-bottom:0.2rem;'>Presupuesto instalación eléctrica de vivienda</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:{text_soft}; margin-top:0;'>Presupuesto por capítulos C1–C13, derivación individual y cuadro general, con catálogo normalizado ampliado.</p>",
        unsafe_allow_html=True
    )

    st.markdown("## 📦 Catálogo de productos normalizados")

    # Inicializar catálogo si no existe
    if "catalogo_productos" not in st.session_state:
        st.session_state["catalogo_productos"] = []

    # ---------------------------------------------------------
    # DEFINICIÓN DE PRODUCTOS POR FAMILIAS
    # ---------------------------------------------------------

    productos_mecanismos = [
        ("INT-S", "Interruptor simple", "ud", 5.00, 4.00),
        ("INT-D", "Interruptor doble", "ud", 7.50, 5.00),
        ("INT-C", "Interruptor conmutado", "ud", 7.50, 5.00),
        ("INT-CR", "Interruptor cruzamiento", "ud", 9.00, 5.50),
        ("PULS-S", "Pulsador simple", "ud", 5.50, 4.00),
        ("TC-S", "Toma corriente simple 16A", "ud", 7.50, 5.00),
        ("TC-D", "Toma corriente doble 16A", "ud", 11.00, 7.00),
        ("TC-USB", "Toma USB doble", "ud", 22.00, 8.00),
        ("TC-TV", "Toma TV", "ud", 9.00, 5.00),
        ("TC-RJ45", "Toma RJ45 Cat6", "ud", 12.00, 6.00),
        ("TC-RJ45-7", "Toma RJ45 Cat7", "ud", 18.00, 7.00),
        ("REG-LED", "Regulador LED", "ud", 28.00, 10.00),
        ("BASE-SUP", "Base superficie", "ud", 3.00, 2.00),
        ("BASE-EMP", "Base empotrada", "ud", 2.50, 2.00)
    ]

    productos_iluminacion = [
        ("DL-6W", "Downlight LED 6W", "ud", 8.00, 4.00),
        ("DL-12W", "Downlight LED 12W", "ud", 10.00, 4.50),
        ("DL-18W", "Downlight LED 18W", "ud", 12.00, 5.00),
        ("PLAF-24W", "Plafón LED 24W", "ud", 18.00, 6.00),
        ("TIRA-LED-12V", "Tira LED 12V", "m", 4.00, 2.00),
        ("TIRA-LED-24V", "Tira LED 24V", "m", 5.00, 2.50),
        ("APLIQ", "Aplique interior", "ud", 15.00, 6.00),
        ("FOCO-EMP", "Foco empotrado", "ud", 7.00, 3.00)
    ]

    productos_cableado = [
        ("H07V-K-1.5", "Cable H07V-K 1.5 mm²", "m", 0.80, 0.50),
        ("H07V-K-2.5", "Cable H07V-K 2.5 mm²", "m", 1.20, 0.60),
        ("H07V-K-4", "Cable H07V-K 4 mm²", "m", 1.80, 0.80),
        ("H07V-K-6", "Cable H07V-K 6 mm²", "m", 2.50, 1.00),
        ("H07V-K-10", "Cable H07V-K 10 mm²", "m", 4.00, 1.50),
        ("MANG-3G1.5", "Manguera 3G1.5", "m", 1.50, 0.80),
        ("MANG-3G2.5", "Manguera 3G2.5", "m", 2.20, 1.00),
        ("MANG-5G6", "Manguera 5G6", "m", 8.00, 2.50),
        ("LSZH-2.5", "Cable libre halógenos 2.5 mm²", "m", 1.80, 0.80),
        ("FV-4", "Cable FV 4 mm²", "m", 1.50, 0.80),
        ("FV-6", "Cable FV 6 mm²", "m", 2.20, 1.00),
        ("FV-10", "Cable FV 10 mm²", "m", 3.80, 1.50)
    ]

    productos_canalizacion = [
        ("TUBO-20", "Tubo corrugado 20 mm", "m", 0.60, 0.40),
        ("TUBO-25", "Tubo corrugado 25 mm", "m", 0.80, 0.50),
        ("TUBO-32", "Tubo corrugado 32 mm", "m", 1.20, 0.70),
        ("CAN-40x20", "Canaleta PVC 40x20", "m", 2.50, 1.00),
        ("CAN-60x40", "Canaleta PVC 60x40", "m", 4.00, 1.50),
        ("BANDEJA", "Bandeja perforada", "m", 6.00, 2.00),
        ("TUBO-RIG", "Tubo rígido", "m", 1.80, 0.80)
    ]

    productos_protecciones = [
        ("CG-12M", "Cuadro empotrado 12 módulos", "ud", 55.00, 25.00),
        ("CG-24M", "Cuadro empotrado 24 módulos", "ud", 75.00, 35.00),
        ("CG-36M", "Cuadro empotrado 36 módulos", "ud", 95.00, 45.00),
        ("IGA-25", "IGA 25 A", "ud", 18.00, 6.00),
        ("IGA-40", "IGA 40 A", "ud", 22.00, 6.00),
        ("ID-AC-30", "ID 30 mA tipo AC", "ud", 28.00, 8.00),
        ("ID-A-30", "ID 30 mA tipo A", "ud", 38.00, 10.00),
        ("ID-F-30", "ID 30 mA tipo F", "ud", 55.00, 12.00),
        ("PIA-10", "PIA 10 A", "ud", 6.00, 3.00),
        ("PIA-16", "PIA 16 A", "ud", 6.50, 3.00),
        ("PIA-20", "PIA 20 A", "ud", 7.00, 3.00),
        ("PIA-25", "PIA 25 A", "ud", 8.00, 3.00),
        ("PIA-32", "PIA 32 A", "ud", 9.00, 3.00),
        ("SOBT", "Protector sobretensiones", "ud", 45.00, 15.00),
        ("CONTACT", "Contactor", "ud", 22.00, 8.00),
        ("RELE", "Relé modular", "ud", 12.00, 5.00)
    ]

    productos_DI = [
        ("DI-CABLE-10", "Cable DI 10 mm²", "m", 3.50, 1.50),
        ("DI-CABLE-16", "Cable DI 16 mm²", "m", 5.00, 2.00),
        ("DI-CABLE-25", "Cable DI 25 mm²", "m", 8.00, 3.00),
        ("DI-TUBO-40", "Tubo 40 mm", "m", 2.50, 1.00),
        ("DI-ICP", "Caja ICP", "ud", 18.00, 8.00),
        ("DI-EMB", "Caja embarrado", "ud", 22.00, 10.00)
    ]

    productos_vehiculo = [
        ("WB-7.4", "Wallbox 7.4 kW", "ud", 450.00, 80.00),
        ("WB-11", "Wallbox 11 kW", "ud", 550.00, 90.00),
        ("VE-CABLE-6", "Cable VE 6 mm²", "m", 2.80, 1.20),
        ("VE-CABLE-10", "Cable VE 10 mm²", "m", 4.50, 1.80)
    ]

    productos_domotica = [
        ("DOM-ACT", "Actuador domótico", "ud", 35.00, 10.00),
        ("DOM-SENS", "Sensor domótico", "ud", 22.00, 8.00),
        ("DOM-WIFI", "Módulo WiFi", "ud", 18.00, 6.00)
    ]

    # ---------------------------------------------------------
    # MOSTRAR CATÁLOGO EN PESTAÑAS
    # ---------------------------------------------------------

    tabs = st.tabs([
        "Mecanismos", "Iluminación", "Cableado", "Canalización",
        "Protecciones", "Derivación individual", "Vehículo eléctrico",
        "Domótica", "Varios"
    ])

    familias = [
        productos_mecanismos,
        productos_iluminacion,
        productos_cableado,
        productos_canalizacion,
        productos_protecciones,
        productos_DI,
        productos_vehiculo,
        productos_domotica,
        []
    ]

    nombres_familias = [
        "Mecanismos", "Iluminación", "Cableado", "Canalización",
        "Protecciones", "Derivación individual", "Vehículo eléctrico",
        "Domótica", "Varios"
    ]

    for tab, familia, nombre in zip(tabs, familias, nombres_familias):
        with tab:
            st.markdown(f"### {nombre}")

            if familia:
                df_fam = pd.DataFrame([
                    {
                        "Referencia": ref,
                        "Descripción": desc,
                        "Unidad": unidad,
                        "Precio material (€)": pm,
                        "Precio mano de obra (€)": pmo
                    }
                    for ref, desc, unidad, pm, pmo in familia
                ])

                st.dataframe(df_fam, use_container_width=True)

                # Añadir al catálogo global
                for ref, desc, unidad, pm, pmo in familia:
                    item = {
                        "Referencia": ref,
                        "Descripción": desc,
                        "Unidad": unidad,
                        "Familia": nombre,
                        "Precio material (€)": pm,
                        "Precio mano de obra (€)": pmo
                    }
                    if item not in st.session_state["catalogo_productos"]:
                        st.session_state["catalogo_productos"].append(item)

            else:
                st.info("Sin productos adicionales en esta familia.")

    # ---------------------------------------------------------
    # CREAR PRODUCTO PERSONALIZADO
    # ---------------------------------------------------------

    st.markdown("### ➕ Crear producto personalizado")

    with st.expander("Añadir nuevo producto"):
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
# =========================================================
# PRESUPUESTO — CAPÍTULOS C1 A C7 (Diseño compacto)
# =========================================================

st.markdown("## 📐 Presupuesto por capítulos (C1–C13)")

# Parámetros económicos globales
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

# Lista de capítulos C1–C7
capitulos_1 = [
    "C1 - Iluminación",
    "C2 - Tomas de uso general",
    "C3 - Cocina y horno",
    "C4 - Lavadora / lavavajillas",
    "C5 - Baños y auxiliares",
    "C6 - Climatización",
    "C7 - Calefacción"
]

# Para almacenar resultados
resultados_parciales = []

# ---------------------------------------------------------
# FUNCIÓN DE CÁLCULO COMPACTO
# ---------------------------------------------------------

def calcular_capitulo(nombre_capitulo, productos_catalogo):
    st.markdown(f"### {nombre_capitulo}")

    with st.expander(nombre_capitulo, expanded=False):

        # Selección de productos
        productos_sel = st.multiselect(
            f"Selecciona productos para {nombre_capitulo}",
            options=[p["Descripción"] for p in productos_catalogo],
            key=f"sel_{nombre_capitulo}"
        )

        # Tabla editable compacta
        tabla_items = []
        for desc in productos_sel:
            fila = next((p for p in productos_catalogo if p["Descripción"] == desc), None)
            if fila:
                col1, col2 = st.columns([2, 1])
                with col1:
                    qty = st.number_input(
                        f"Cantidad — {desc}",
                        min_value=0.0,
                        value=1.0,
                        step=1.0,
                        key=f"qty_{nombre_capitulo}_{desc}"
                    )
                with col2:
                    st.markdown(f"Unidad: **{fila['Unidad']}**")

                tabla_items.append({
                    "Descripción": desc,
                    "Unidad": fila["Unidad"],
                    "Cantidad": qty,
                    "PM": fila["Precio material (€)"],
                    "PMO": fila["Precio mano de obra (€)"]
                })

        # Mano de obra directa
        horas = st.number_input(
            f"Horas de mano de obra directa en {nombre_capitulo}",
            min_value=0.0,
            value=0.0,
            step=0.5,
            key=f"horas_{nombre_capitulo}"
        )

        # Cálculos
        mat_total = sum(item["PM"] * item["Cantidad"] for item in tabla_items)
        mo_prod = sum(item["PMO"] * item["Cantidad"] for item in tabla_items)
        mo_directa = horas * mano_obra_hora
        mo_total = mo_prod + mo_directa

        base_cap = mat_total + mo_total
        gastos = base_cap * (amort_pct / 100)
        beneficio = (base_cap + gastos) * (benef_pct / 100)
        base_imp = base_cap + gastos + beneficio
        iva = base_imp * (iva_pct / 100)
        total = base_imp + iva

        # Mostrar totales
        st.markdown("#### Totales del capítulo")
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(f"**Materiales:** {mat_total:.2f} €")
            st.markdown(f"**Mano de obra:** {mo_total:.2f} €")
        with colB:
            st.markdown(f"**Gastos generales:** {gastos:.2f} €")
            st.markdown(f"**Beneficio:** {beneficio:.2f} €")
        with colC:
            st.markdown(f"**Base imponible:** {base_imp:.2f} €")
            st.markdown(f"**IVA:** {iva:.2f} €")
            st.markdown(f"### Total capítulo: **{total:.2f} €**")

        # Justificación compacta en tarjetas premium
        st.markdown("#### Justificación (tarjetas premium)")

        tarjeta_formula_latex(
            rf"\text{{Materiales}} = \sum (p_{{m,i}}\cdot q_i) = {mat_total:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Mano de obra productos}} = \sum (p_{{mo,i}}\cdot q_i) = {mo_prod:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Mano de obra directa}} = {horas:.2f}\cdot{mano_obra_hora:.2f} = {mo_directa:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Base capítulo}} = {base_cap:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Gastos generales}} = {base_cap:.2f}\cdot{amort_pct:.2f}\% = {gastos:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Beneficio}} = ({base_cap:.2f}+{gastos:.2f})\cdot{benef_pct:.2f}\% = {beneficio:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{IVA}} = {base_imp:.2f}\cdot{iva_pct:.2f}\% = {iva:.2f}\ \mathrm{{€}}"
        )
        tarjeta_formula_latex(
            rf"\text{{Total capítulo}} = {total:.2f}\ \mathrm{{€}}"
        )

        return {
            "Capítulo": nombre_capitulo,
            "Material (€)": mat_total,
            "Mano de obra (€)": mo_total,
            "Base capítulo (€)": base_cap,
            "Gastos generales (€)": gastos,
            "Beneficio (€)": beneficio,
            "Base imponible (€)": base_imp,
            "IVA (€)": iva,
            "Total capítulo (€)": total
        }

# ---------------------------------------------------------
# PROCESAR CAPÍTULOS C1–C7
# ---------------------------------------------------------

for cap in capitulos_1:
    datos = calcular_capitulo(cap, st.session_state["catalogo_productos"])
    resultados_parciales.append(datos)
# =========================================================
# PRESUPUESTO — CAPÍTULOS C8 A C13 + DI + CUADRO GENERAL
# =========================================================

capitulos_2 = [
    "C8 - ACS eléctrico",
    "C9 - Secadora",
    "C10 - Lavavajillas adicional",
    "C11 - Horno adicional",
    "C12 - Vehículo eléctrico",
    "C13 - Domótica / servicios especiales",
    "Derivación individual",
    "Cuadro general"
]

# ---------------------------------------------------------
# PROCESAR CAPÍTULOS C8–C13 + DI + CUADRO
# ---------------------------------------------------------

for cap in capitulos_2:
    datos = calcular_capitulo(cap, st.session_state["catalogo_productos"])
    resultados_parciales.append(datos)

# =========================================================
# RESUMEN GLOBAL DEL PRESUPUESTO
# =========================================================

st.markdown("## 💰 Resumen global del presupuesto")

df_caps = pd.DataFrame(resultados_parciales)

st.dataframe(
    df_caps.style.format({
        "Material (€)": "{:.2f}",
        "Mano de obra (€)": "{:.2f}",
        "Base capítulo (€)": "{:.2f}",
        "Gastos generales (€)": "{:.2f}",
        "Beneficio (€)": "{:.2f}",
        "Base imponible (€)": "{:.2f}",
        "IVA (€)": "{:.2f}",
        "Total capítulo (€)": "{:.2f}"
    }),
    use_container_width=True
)

# Totales globales
total_material = df_caps["Material (€)"].sum()
total_mo = df_caps["Mano de obra (€)"].sum()
total_base = df_caps["Base capítulo (€)"].sum()
total_gastos = df_caps["Gastos generales (€)"].sum()
total_benef = df_caps["Beneficio (€)"].sum()
total_base_imp = df_caps["Base imponible (€)"].sum()
total_iva = df_caps["IVA (€)"].sum()
total_final = df_caps["Total capítulo (€)"].sum()

st.markdown(
    f"<h2 style='margin-top:1rem; font-weight:700;'>💰 Total presupuesto (con IVA): {total_final:.2f} €</h2>",
    unsafe_allow_html=True
)

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

# =========================================================
# EXPORTACIÓN A EXCEL
# =========================================================

st.markdown("### 📤 Exportación del presupuesto")

excel_presupuesto = exportar_excel(df_caps, "Presupuesto_Vivienda")

st.download_button(
    "📥 Descargar presupuesto (Excel)",
    excel_presupuesto,
    "presupuesto_vivienda.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
# =========================================================
# BOTÓN PARA VOLVER AL MENÚ PRINCIPAL
# =========================================================

st.markdown("---")

c_back = st.container()
with c_back:
    if st.button("⬅️ Volver al menú principal", use_container_width=True):
        st.session_state["modo"] = None
        st.rerun()

# =========================================================
# FIN DEL ARCHIVO
# =========================================================
