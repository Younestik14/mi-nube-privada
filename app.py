# =========================================================
# INGENIERÍA PRO v10.0
# Cálculo de Secciones REBT + FV (solo cálculo)
# Versión profesional definitiva
# =========================================================

import streamlit as st
import pandas as pd
import io
import math

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Pro v10.0",
    layout="wide",
    page_icon="⚡"
)

# =========================================================
# ESTILO VISUAL PREMIUM
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #050816;
    color: #e5e7eb;
    font-family: "Segoe UI", system-ui, sans-serif;
}

/* Títulos */
h1, h2, h3, h4 {
    color: #f9fafb !important;
    font-weight: 800 !important;
}

/* Inputs */
.stNumberInput input,
.stSelectbox div,
.stRadio > label,
.stSlider > div {
    background-color: #0f172a !important;
    color: #e5e7eb !important;
}

/* Tarjetas */
.card {
    background: #0f172a;
    border-radius: 16px;
    padding: 18px 20px;
    border: 1px solid #334155;
    box-shadow: 0px 10px 25px rgba(0,0,0,0.65);
    margin-bottom: 18px;
}

/* Tarjetas de fórmulas */
.formula-card {
    background: #0f172a;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #475569;
    text-align: center;
    margin-bottom: 18px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.45);
}

/* Caja resultado */
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
    font-weight: 600;
    color: rgba(148, 163, 184, 0.55);
    letter-spacing: 0.6px;
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
# ⚡ INGENIERÍA PRO v10.0 — Cálculo Profesional de Secciones REBT + FV

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
# SECCIONES NORMALIZADAS
# =========================================================

secciones_ref = [
    1.5, 2.5, 4, 6, 10,
    16, 25, 35, 50, 70,
    95, 120, 150, 185, 240
]

# =========================================================
# TABLAS REBT — Intensidades admisibles
# =========================================================

tablas_adm = {
    "A1 - Empotrado en tubo (pared aislante)": {
        "PVC":  [14.5,19.5,26,34,46,61,80,99,119,151,182,210,240,273,321],
        "XLPE": [18.5,25,33,43,59,77,102,126,153,194,233,268,307,352,415]
    },
    "B1 - Conductores en tubo sobre pared": {
        "PVC":  [17.5,24,32,41,57,76,101,125,151,192,232,269,300,341,400],
        "XLPE": [22,30,40,52,71,94,126,157,190,241,292,338,388,442,523]
    },
    "C - Cable directamente sobre pared": {
        "PVC":  [19.5,27,36,46,63,85,112,138,168,213,258,299,344,391,461],
        "XLPE": [24,33,45,58,80,107,138,171,209,269,328,382,441,506,599]
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
    return 240

# =========================================================
# FORMULARIO
# =========================================================

c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    tipo_instalacion = st.selectbox("🏷 Tipo de instalación", ["CA REBT (general)", "FV en corriente continua"])
    sistema = st.selectbox("🔌 Sistema eléctrico", ["Monofásico 230V", "Trifásico 400V"] if tipo_instalacion=="CA REBT (general)" else ["Corriente continua FV"])
    modo_intensidad = st.selectbox("Modo de cálculo de intensidad", ["A partir de potencia", "Introducir intensidad directamente"])

    if modo_intensidad == "A partir de potencia":
        potencia = st.number_input("⚡ Potencia (W)", value=5750.0)
    else:
        ib_input = st.number_input("🔁 Intensidad Ib (A)", value=25.0)

    longitud = st.number_input("📏 Longitud (m)", value=30.0)
    cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90) if tipo_instalacion=="CA REBT (general)" else 1.00
    uso = st.selectbox("🏷 Tipo de circuito", ["General", "Motores", "Vehículo eléctrico", "Fotovoltaica"])

    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    material = st.radio("Material", ["Cobre (Cu)", "Aluminio (Al)"])
    aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"])
    metodo = st.selectbox("Método REBT", list(tablas_adm.keys()))
    max_cdt_pct = st.number_input("Caída de tensión máx (%)", value=3.0)
    v_cc = st.number_input("Tensión FV (Vcc)", value=600.0) if tipo_instalacion=="FV en corriente continua" else None

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# CÁLCULOS
# =========================================================

k_u = 1.25 if uso in ["Motores", "Vehículo eléctrico"] else 1.0
v_fase = 230 if sistema=="Monofásico 230V" else (400 if sistema=="Trifásico 400V" else v_cc)
delta_u_max = max_cdt_pct/100 * v_fase

if modo_intensidad == "Introducir intensidad directamente":
    ib = ib_input
    potencia_calc = (v_fase * ib * cos_phi) if sistema=="Monofásico 230V" else (math.sqrt(3)*v_fase*ib*cos_phi if sistema=="Trifásico 400V" else v_fase*ib)
else:
    potencia_calc = potencia * k_u
    ib = potencia_calc/(v_fase*cos_phi) if sistema=="Monofásico 230V" else (potencia_calc/(math.sqrt(3)*v_fase*cos_phi) if sistema=="Trifásico 400V" else potencia_calc/v_fase)

s_adm = get_seccion_adm(metodo, aislamiento, ib)

sigma = 48 if ("Cobre" in material and "PVC" in aislamiento) else \
        44 if ("Cobre" in material and "XLPE" in aislamiento) else \
        30 if ("Aluminio" in material and "PVC" in aislamiento) else 28

if sistema=="Monofásico 230V":
    s_cdt = (2*longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,mono}=\frac{2\cdot L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"
elif sistema=="Trifásico 400V":
    s_cdt = (longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,tri}=\frac{L\cdot P}{\sigma\cdot U\cdot\Delta U_{\max}}"
else:
    s_cdt = (2*longitud*potencia_calc)/(sigma*v_fase*delta_u_max)
    ecuacion_usada = r"S_{cdt,FV}=\frac{2\cdot L\cdot P}{\sigma\cdot U_{cc}\cdot\Delta U_{\max}}"

s_cdt_norm = next((s for s in secciones_ref if s>=s_cdt), 240)

s_min_rebt = {"General":1.5,"Motores":2.5,"Vehículo eléctrico":6.0,"Fotovoltaica":4.0}[uso]
s_final = max(s_adm, s_cdt_norm, s_min_rebt)

# =========================================================
# RESULTADO
# =========================================================

st.markdown(f"""
<div class="resultado-caja">
SECCIÓN FINAL REGLAMENTARIA: {s_final} mm²
<br>
<small>
Ib = {ib:.2f} A |
Térmica = {s_adm} mm² |
CdT = {s_cdt:.2f} mm² (→ {s_cdt_norm} mm²) |
Mínimo REBT = {s_min_rebt} mm²
</small>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TARJETAS DE FÓRMULAS (ESTILO PREMIUM)
# =========================================================

st.markdown("### 📘 Ecuaciones aplicadas")

st.markdown(f"""
<div class="formula-card">
\

\[
{ecuacion_usada}
\\]


</div>
""", unsafe_allow_html=True)

# =========================================================
# TABLA ITC‑BT‑19 CON SUBRAYADO
# =========================================================

st.markdown("### 📘 Tabla ITC‑BT‑19 — Intensidades admisibles")

tabla = pd.DataFrame({
    "Sección (mm²)": secciones_ref,
    "PVC (A)": [round(x,2) for x in tablas_adm[metodo]["PVC"]],
    "XLPE (A)": [round(x,2) for x in tablas_adm[metodo]["XLPE"]]
})

fila = tabla.index[tabla["Sección (mm²)"]==s_final][0] if s_final in tabla["Sección (mm²)"].values else None
col = "PVC (A)" if "PVC" in aislamiento else "XLPE (A)"

def estilo(row):
    estilos=[]
    for c in tabla.columns:
        if row.name==fila and c==col:
            estilos.append("background-color:#22d3ee;color:#020617;font-weight:900;")
        elif row.name==fila:
            estilos.append("text-decoration:underline;font-weight:700;")
        elif c==col:
            estilos.append("text-decoration:underline;font-weight:700;")
        else:
            estilos.append("")
    return estilos

st.dataframe(tabla.style.apply(estilo,axis=1), use_container_width=True)

# =========================================================
# PROCEDIMIENTO DETALLADO
# =========================================================

st.markdown("### 📘 Procedimiento del cálculo")

st.markdown("""
#### 1️⃣ Potencia de diseño
""")

st.markdown("""
<div class="formula-card">
\

\[
P = U\\cdot I\\cdot\\cos\\varphi
\\]


</div>
""", unsafe_allow_html=True)

st.markdown(f"**Potencia utilizada:** {potencia_calc:.2f} W")

st.markdown("""
#### 2️⃣ Sección térmica (ITC‑BT‑19)
""")

st.markdown(f"**Sección térmica:** {s_adm} mm²")

st.markdown("""
#### 3️⃣ Caída de tensión
""")

st.markdown(f"""
<div class="formula-card">
\

\[
{ecuacion_usada}
\\]


</div>
""", unsafe_allow_html=True)

st.markdown(f"**Sección por CdT normalizada:** {s_cdt_norm} mm²")

st.markdown("""
#### 4️⃣ Mínimos reglamentarios
""")

st.markdown(f"**Sección mínima REBT:** {s_min_rebt} mm²")

st.markdown(f"""
<div class="total-final-banner">
SECCIÓN FINAL REGLAMENTARIA: {s_final} mm²
</div>
""", unsafe_allow_html=True)

# =========================================================
# EXPORTACIÓN
# =========================================================

df = pd.DataFrame({
    "Parámetro":[
        "Tipo instalación","Sistema","Uso","Potencia (W)","Ib (A)",
        "Longitud (m)","cos φ","Material","Aislamiento","Método",
        "S térmica","S CdT","S CdT norm","S mínima REBT","S FINAL"
    ],
    "Valor":[
        tipo_instalacion,sistema,uso,round(potencia_calc,2),round(ib,2),
        longitud,cos_phi,material,aislamiento,metodo,
        s_adm,round(s_cdt,2),s_cdt_norm,s_min_rebt,s_final
    ]
})

excel = exportar_excel(df,"Calculo_Secciones")

st.download_button(
    "📥 Descargar memoria (Excel)",
    excel,
    "calculo_secciones.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

