import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Módulo Fotovoltaica REBT", page_icon="☀️", layout="wide")

st.title("☀️ Módulo 2: Dimensionamiento Fotovoltaico según Normativa Española")
st.markdown("Cálculo y clasificación según el **RD 244/2019**, selección de inversores y placas comerciales con protecciones.")

# --- 1. BASE DE DATOS DE PANELES COMERCIALES (Catálogo Real) ---
PANELES_COMERCIALES = [
    {"modelo": "Jinko Solar Tiger Neo N-type 440W", "potencia_wp": 440, "vmp": 44.03, "isc": 13.80, "tipo": "Residencial (Monocristalino)"},
    {"modelo": "Longi Hi-MO 6 Explorer 450W", "potencia_wp": 450, "vmp": 44.91, "isc": 13.01, "tipo": "Residencial (Monocristalino)"},
    {"modelo": "JA Solar DeepBlue 3.0 550W", "potencia_wp": 550, "vmp": 41.96, "isc": 14.00, "tipo": "Industrial/Suelo"},
    {"modelo": "Trina Solar Vertex S+ 505W", "potencia_wp": 505, "vmp": 43.40, "isc": 14.79, "tipo": "Residencial/Industrial"},
    {"modelo": "Canadian Solar HiKu7 650W", "potencia_wp": 650, "vmp": 38.30, "isc": 18.35, "tipo": "Industrial de Gran Potencia"},
    {"modelo": "Risen Titan 410W (Black Frame)", "potencia_wp": 410, "vmp": 34.89, "isc": 12.42, "tipo": "Residencial / Estético"}
]

# --- 2. BASE DE DATOS DE INVERSORES COMERCIALES (Catálogo Real Ampliado) ---
INVERSORES_COMERCIALES = [
    # Microinversores
    {"marca": "Enphase IQ8L (Microinversor)", "potencia_w": 349, "tipo": "Microinversor", "fases": "Monofásico"},
    {"marca": "Enphase IQ8AC (Microinversor)", "potencia_w": 366, "tipo": "Microinversor", "fases": "Monofásico"},
    {"marca": "Hoymiles HM-1500 (Multi-panel)", "potencia_w": 1500, "tipo": "Microinversor", "fases": "Monofásico"},
    # Monofásicos Red (Residencial)
    {"marca": "Huawei SUN2000-2KTL-L1", "potencia_w": 2000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Huawei SUN2000-3KTL-L1", "potencia_w": 3000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Fronius Primo 3.0-1", "potencia_w": 3000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "SolarEdge SE4000H Wave", "potencia_w": 4000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Huawei SUN2000-5KTL-L1", "potencia_w": 5000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Fronius Primo 6.0-1", "potencia_w": 6000, "tipo": "Inversor de String", "fases": "Monofásico"},
    # Trifásicos (Residencial Grande / Industrial)
    {"marca": "Huawei SUN2000-5KTL-M1", "potencia_w": 5000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Fronius Symo 6.0-3-M", "potencia_w": 6000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Huawei SUN2000-10KTL-M1", "potencia_w": 10000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "SolarEdge SE15K Trifásico", "potencia_w": 15000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Ingeteam 20TL Pro", "potencia_w": 20000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Huawei SUN2000-30KTL-M3", "potencia_w": 30000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Huawei SUN2000-50KTL-M2", "potencia_w": 50000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Ingeteam INGCON SUN 100TL", "potencia_w": 100000, "tipo": "Inversor de String", "fases": "Trifásico"}
]

# --- CONFIGURACIÓN E INTRODUCCIÓN DE DATOS ---
st.header("⚙️ Configuración del Proyecto Solar")

MODALIDADES_AUTOCONSUMO = [
    "Autoconsumo SIN excedentes (Requiere sistema antivertido - ITC-BT-40)",
    "Autoconsumo CON excedentes ACOGIDO a compensación simplificada",
    "Autoconsumo CON excedentes NO acogido a compensación",
    "Instalación Aislada de la Red (No aplica RD 244/2019)"
]

col_config1, col_config2 = st.columns(2)

with col_config1:
    modalidad = st.selectbox("Modalidad de la Instalación (RD 244/2019 / REBT)", MODALIDADES_AUTOCONSUMO)
    
    if "Aislada" in modalidad:
        consumo_diario = st.number_input("Consumo Diario Estimado (Wh/día)", value=5000, step=500)
        hsp = st.number_input("HSP del mes más desfavorable (Invierno)", value=3.2, min_value=1.0, step=0.1)
        dias_autonomia = st.slider("Días de Autonomía Requeridos", min_value=1, max_value=5, value=2)
        v_bateria = st.selectbox("Tensión del Banco de Baterías (V)", [12, 24, 48], index=2)
    else:
        consumo_anual = st.number_input("Consumo Anual de la Instalación (kWh/año)", value=6500, step=500)
        hsp = st.number_input("Horas de Sol Pico (HSP) medias anuales de la zona", value=4.7, min_value=1.0, step=0.1)

with col_config2:
    st.markdown("**⚡ Factores de Rendimiento y Afección de Sombras**")
    sombreado = st.radio(
        "Presencia de Sombras (Árboles, chimeneas, estructuras):",
        ["Sin sombras (Condición óptima)", "Sombras parciales / temporales (Pérdidas moderadas)", "Sombras severas"]
    )
    
    solucion_sombras = "Inversor Central Estándar"
    if sombreado != "Sin sombras (Condición óptima)":
        solucion_sombras = st.selectbox(
            "🛠️ Elemento técnico corrector para mitigar sombras:",
            [
                "Mantener Inversor de String estándar (Mayor pérdida por efecto 'cuello de botella')",
                "Instalar Optimizadores de Potencia (Uno por panel - Maximiza MPPT individual)",
                "Instalar Microinversores (Un inversor por panel - Independencia total)"
            ]
        )

# Penalización del rendimiento por sombras y corrección por tecnología
f_perdidas_base = 0.15 if not "Aislada" in modalidad else 0.25
if sombreado == "Sombras parciales / temporales (Pérdidas moderadas)":
    f_perdidas = f_perdidas_base + (0.02 if "Microinversores" in solucion_sombras or "Optimizadores" in solucion_sombras else 0.15)
elif sombreado == "Sombras severas":
    f_perdidas = f_perdidas_base + (0.05 if "Microinversores" in solucion_sombras or "Optimizadores" in solucion_sombras else 0.35)
else:
    f_perdidas = f_perdidas_base

st.write("---")
st.header("🔌 Selección de Componentes de Catálogo")

col_comp1, col_comp2 = st.columns(2)
with col_comp1:
    # Selector de paneles comerciales directo de base de datos
    nombres_paneles = [p["modelo"] for p in PANELES_COMERCIALES]
    panel_seleccionado_nombre = st.selectbox("Selecciona el Módulo Fotovoltaico comercial:", nombres_paneles)
    
    # Extraer objeto seleccionado
    panel_sel = next(item for item in PANELES_COMERCIALES if item["modelo"] == panel_seleccionado_nombre)
    st.caption(f"Ficha técnica: **{panel_sel['potencia_wp']}Wp** | Vmp: {panel_sel['vmp']}V | Isc: {panel_sel['isc']}A | Uso: {panel_sel['tipo']}")

with col_comp2:
    fases_instalacion = st.selectbox("Tipo de Red Eléctrica de la instalación (Salida del inversor)", ["Monofásico", "Trifásico"])
    # --- LÓGICA DE CÁLCULO FOTOVOLTAICO ---
p_panel = panel_sel["potencia_wp"]
vmp_panel = panel_sel["vmp"]
isc_panel = panel_sel["isc"]

if not "Aislada" in modalidad:
    p_pico_req_w = (consumo_anual / (hsp * 365 * (1 - f_perdidas))) * 1000
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_kwp = (num_paneles * p_panel) / 1000
    cap_nominal_ah = 0
else:
    p_pico_req_w = consumo_diario / (hsp * (1 - f_perdidas))
    num_paneles = math.ceil(p_pico_req_w / p_panel)
    potencia_total_kwp = (num_paneles * p_panel) / 1000
    cap_util_wh = consumo_diario * dias_autonomia
    cap_nominal_ah = cap_util_wh / (v_bateria * 0.6)

# --- SELECCIÓN AUTOMÁTICA DEL INVERSOR COMERCIAL ---
inversor_sugerido = None
num_microinversores = 0

if "Microinversores" in solucion_sombras:
    for inv in INVERSORES_COMERCIALES:
        if inv["tipo"] == "Microinversor":
            inversor_sugerido = inv
            num_microinversores = num_paneles
            break
else:
    potencia_busqueda_w = (potencia_total_kwp * 1000) * 0.90
    for inv in INVERSORES_COMERCIALES:
        if inv["tipo"] == "Inversor de String" and inv["fases"] == fases_instalacion:
            if inv["potencia_w"] >= potencia_busqueda_w:
                inversor_sugerido = inv
                break
    if not inversor_sugerido:
        inversor_sugerido = [i for i in INVERSORES_COMERCIALES if i["fases"] == fases_instalacion][-1]

# --- PANEL DE RESULTADOS ---
st.write("---")
st.header("📊 Dictamen y Resultados del Dimensionamiento")

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric(label="Potencia Campo FV Instalada", value=f"{potencia_total_kwp:.2f} kWp")
    st.write(f"* **Módulo:** {panel_sel['modelo']}")
    st.write(f"* **Cantidad:** **{num_paneles} módulos**")
with col_res2:
    if num_microinversores > 0:
        st.metric(label="Sistema de Inversión Asignado", value=f"{num_microinversores}x Unidades")
        st.write(f"* **Modelo:** {inversor_sugerido['marca']}")
        st.write(f"* **Potencia total AC:** {round((inversor_sugerido['potencia_w'] * num_microinversores)/1000, 2)} kW")
    else:
        st.metric(label="Inversor Comercial Asignado", value=inversor_sugerido["marca"])
        st.write(f"* **Tipo:** {inversor_sugerido['tipo']} ({inversor_sugerido['fases']})")
        st.write(f"* **Potencia de catálogo:** {inversor_sugerido['potencia_w']/1000:.1f} kW AC")
with col_res3:
    st.metric(label="Pérdidas de Rendimiento", value=f"{f_perdidas*100:.1f} %")
    st.write(f"* **Estado de sombras:** {sombreado.split(' (')[0]}")
    st.write(f"* **Tecnología correctora:** {solucion_sombras.split(' (')[0]}")

# --- ESQUEMA DE PROTECCIONES REBT ---
st.write("---")
st.header("🛡️ Esquema Técnico de Protecciones Obligatorias (REBT)")

col_prot1, col_prot2 = st.columns(2)

with col_prot1:
    st.subheader("🔌 Tramo Corriente Continua (CC)")
    if "Microinversores" in solucion_sombras:
        st.info("ℹ️ Los microinversores eliminan el tramo de CC centralizado de alta tensión. No requiere fusibles CC ni SPD de alta tensión, la salida del módulo va directa en CA.")
    else:
        corriente_string = isc_panel * 1.25
        fusible_calibre = 15 if corriente_string <= 15 else (20 if corriente_string <= 20 else 25)
        st.markdown(f"""
        * **Seccionador General CC:** Interruptor de corte en carga independiente omnipolar (1000V CC).
        * **Fusibles de protección String:** Calibre de **{fusible_calibre}A**, curva gPV para corriente continua (en polo + y polo -).
        * **Protección contra Descargas Atmosféricas:** Descargador de sobretensiones transitorias (SPD) **Clase II CC** derivado a tierra.
        """)

with col_prot2:
    st.subheader("⚡ Tramo Corriente Alterna (CA)")
    p_ac_estimada = inversor_sugerido["potencia_w"] if num_microinversores == 0 else (inversor_sugerido["potencia_w"] * num_microinversores)
    v_ac = 230 if fases_instalacion == "Monofásico" else 400
    
    i_ac = p_ac_estimada / v_ac if fases_instalacion == "Monofásico" else p_ac_estimada / (math.sqrt(3) * v_ac)
    calibres_pia = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
    pia_ac = calibres_pia[-1]
    for p in calibres_pia:
        if p >= i_ac * 1.25:
            pia_ac = p
            break
            
    st.markdown(f"""
    * **Interruptor Automático de Conexión (PIA):** Automático **{fases_instalacion}**, Calibre **{pia_ac}A**, Curva C (Poder de corte $\ge$ 6kA).
    * **Diferencial de Interconexión (ID):** Calibre de **{max(pia_ac, 25)}A / 30mA, Obligatorio Clase A (Superinmunizado)** o Tipo B para evitar el cegado del núcleo por corrientes continuas de fuga.
    * **Vigía de Red (Sobretensiones permanentes y transitorias CA):** Protector asociado a bobina de emisión para desconectar el inversor si la tensión de red fluctúa fuera de márgenes reglamentarios.
    """)

# --- GUARDAR EN SESSION STATE ---
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

st.write("---")
st.subheader("💾 Guardar Datos en el Proyecto Global")
nombre_fv = st.text_input("Identificador del Sistema Solar", value="Autoconsumo Solar FV")

if st.button("Guardar instalación solar"):
    st.session_state['proyecto'][nombre_fv] = {
        "tipo": modalidad.split(" (")[0],
        "potencia_kwp": round(potencia_total_kwp, 2),
        "num_paneles": num_paneles,
        "elemento_maniobra": inversor_sugerido["marca"] if num_microinversores == 0 else f"{num_microinversores}x {inversor_sugerido['marca']}",
        "batería_ah": round(cap_nominal_ah, 2) if "Aislada" in modalidad else "N/A"
    }
    st.success(f"✔️ ¡Instalación '{nombre_fv}' indexada con componentes de catálogo!")
