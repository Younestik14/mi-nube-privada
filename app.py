# =========================================================
# INGENIERÍA PRO — Estilo Apple Minimalista + Login
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
# LOGIN APPLE — CENTRADO + ELEVADO + ENTER
# =========================================================

PASSWORD = "SEA2526"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.markdown("""
    <style>
    .login-wrapper {
        height: 100vh;
        width: 100%;
        display: flex;
        justify-content: flex-start;
        align-items: center;
        flex-direction: column;
        padding-top: 12vh; /* ← SUBE EL LOGIN */
        text-align: center;
    }
    .login-title {
        font-size: 42px;
        font-weight: 700;
        color: #f5f5f7;
        margin-bottom: 10px;
    }
    .login-subtitle {
        font-size: 16px;
        color: #9ca3af;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">Ingeniería Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Introduce la contraseña</div>', unsafe_allow_html=True)

    password_input = st.text_input("", type="password", key="login", label_visibility="collapsed")

    # ENTER = validar
    if password_input == PASSWORD:
        st.session_state.auth = True
        st.rerun()

    if st.button("Entrar"):
        if password_input == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =========================================================
# ESTILO GLOBAL APPLE MINIMALISTA
# =========================================================

st.markdown("""
<style>

:root {
    --text-main: #f9fafb;
    --text-soft: #9ca3af;
}

/* TODA LA TIPOGRAFÍA EN BOLD */
* {
    font-weight: 600 !important;
}

/* EXCEPCIÓN: KaTeX NO bold */
.katex, .katex * {
    font-weight: normal !important;
}

/* Inputs estilo Apple */
.stNumberInput input,
.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stRadio > label {
    background: rgba(255,255,255,0.06) !important;
    color: var(--text-main) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    padding: 14px 18px !important;
    font-size: 18px !important;
}

/* Línea divisoria entre ecuaciones */
.ecuacion-divider {
    width: 100%;
    height: 3px;
    background: rgba(255,255,255,0.35);
    margin: 26px 0;
    border-radius: 3px;
}

/* Sin recuadros en toda la app */
.card,
.formula-card,
.resultado-caja,
.total-final-banner {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 0 28px 0 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CABECERA
# =========================================================

st.markdown("""
# ⚡ Ingeniería Pro — Cálculo de Secciones REBT + FV
""")

# =========================================================
# EXPORTACIÓN EXCEL
# =========================================================

def exportar_excel(df, hoja="Datos"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=hoja)
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
# TABLAS REBT
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

def get_seccion_adm(metodo, aislamiento, ib):
    ais = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm[metodo][ais]
    for i, intensidad in enumerate(intensidades):
        if intensidad >= ib:
            return secciones_ref[i]
    return 240.00

# =========================================================
# FORMULARIO
# =========================================================

c1, c2 = st.columns(2)

with c1:
    tipo_instalacion = st.selectbox("Tipo de instalación", ["CA REBT (general)", "FV en corriente continua"])
    sistema = st.selectbox("Sistema eléctrico", ["Monofásico 230V", "Trifásico 400V"] if tipo_instalacion=="CA REBT (general)" else ["Corriente continua FV"])
    modo_intensidad = st.selectbox("Modo de cálculo de intensidad", ["A partir de potencia", "Introducir intensidad directamente"])
    if modo_intensidad == "A partir de potencia":
        potencia = st.number_input("Potencia (W)", value=5750.0)
    else:
        ib_input = st.number_input("Intensidad Ib (A)", value=25.0)
    longitud = st.number_input("Longitud (m)", value=30.0)
    cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90) if tipo_instalacion=="CA REBT (general)" else 1.00
    uso = st.selectbox("Tipo de circuito", ["General", "Motores", "Vehículo eléctrico", "Fotovoltaica"])

with c2:
    material = st.radio("Material", ["Cobre (Cu)", "Aluminio (Al)"])
    aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"])
    metodo = st.selectbox("Método REBT", list(tablas_adm.keys()))
    max_cdt_pct = st.number_input("Caída de tensión máx (%)", value=3.0)
    v_cc = st.number_input("Tensión FV (Vcc)", value=600.0) if tipo_instalacion=="FV en corriente continua" else None

# =========================================================
# CÁLCULOS
# =========================================================

k_u = 1.25 if uso in ["Motores","Vehículo eléctrico"] else 1.0
v_fase = 230 if sistema=="Monofásico 230V" else (400 if sistema=="Trifásico 400V" else v_cc)
delta_u_max = (max_cdt_pct/100)*v_fase

if modo_intensidad=="Introducir intensidad directamente":
    ib = ib_input
    potencia_calc = v_fase*ib*cos_phi if sistema!="Trifásico 400V" else math.sqrt(3)*v_fase*ib*cos_phi
else:
    potencia_calc = potencia*k_u
    ib = potencia_calc/(v_fase*cos_phi) if sistema!="Trifásico 400V" else potencia_calc/(math.sqrt(3)*v_fase*cos_phi)

s_adm = get_seccion_adm(metodo, aislamiento, ib)

sigma = 48 if "Cobre" in material else 30
if "XLPE" in aislamiento:
    sigma -= 4

if sistema=="Monofásico 230V":
    s_cdt = (2*longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,mono}=\frac{2\cdot L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"
elif sistema=="Trifásico 400V":
    s_cdt = (longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,tri}=\frac{L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"
else:
    s_cdt = (2*longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,FV}=\frac{2\cdot L\cdot P}{\sigma\cdot U_{cc}\cdot\Delta U_{\max}}"

s_cdt_norm = next((s for s in secciones_ref if s>=s_cdt), 240.00)

s_min_rebt = {
    "General": 1.5,
    "Motores": 2.5,
    "Vehículo eléctrico": 6.0,
    "Fotovoltaica": 4.0
}[uso]

s_final = max(s_adm, s_cdt_norm, s_min_rebt)

# =========================================================
# ECUACIONES (SIN RECUADROS + LÍNEAS BLANCAS)
# =========================================================

st.latex(rf"{ecuacion_usada}")
st.markdown('<div class="ecuacion-divider"></div>', unsafe_allow_html=True)

st.latex(rf"S_{{cdt}} = {s_cdt:.2f}\ \text{{mm}}^2")
st.markdown('<div class="ecuacion-divider"></div>', unsafe_allow_html=True)

if sistema=="Monofásico 230V":
    st.latex(r"P = U \cdot I \cdot \cos\varphi")
elif sistema=="Trifásico 400V":
    st.latex(r"P = \sqrt{3}\cdot U \cdot I \cdot \cos\varphi")
else:
    st.latex(r"P = U_{cc} \cdot I")

st.markdown('<div class="ecuacion-divider"></div>', unsafe_allow_html=True)

st.latex(rf"P = {potencia_calc:.2f}\ \text{{W}}")

# =========================================================
# RESULTADO FINAL
# =========================================================

st.markdown(f"""
## SECCIÓN FINAL REGLAMENTARIA: **{s_final:.2f} mm²**
""")

# =========================================================
# MEMORIA + EXCEL
# =========================================================

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
        tipo_instalacion, sistema, uso,
        f"{potencia_calc:.2f}", f"{ib:.2f}",
        f"{longitud:.2f}", f"{cos_phi:.2f}",
        material, aislamiento, metodo,
        f"{s_adm:.2f}", f"{s_cdt:.2f}",
        f"{s_cdt_norm:.2f}", f"{s_min_rebt:.2f}",
        f"{s_final:.2f}"
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
