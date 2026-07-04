import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Módulo Fotovoltaica REBT", page_icon="☀️", layout="wide")

st.title("☀️ Módulo 2: Dimensionamiento Fotovoltaico según Normativa Española")
st.markdown("Cálculo y clasificación según el **RD 244/2019**, selección de inversores comerciales y esquema de protecciones.")

# --- BASE DE DATOS DE INVERSORES COMERCIALES (Datos de catálogo reales) ---
INVERSORES_COMERCIALES = [
    {"marca": "Enphase IQ8AC (Microinversor)", "potencia_w": 366, "tipo": "Microinversor", "fases": "Monofásico"},
    {"marca": "Huawei SUN2000-2KTL-L1", "potencia_w": 2000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Fronius Primo 3.0-1", "potencia_w": 3000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Huawei SUN2000-5KTL-L1", "potencia_w": 5000, "tipo": "Inversor de String", "fases": "Monofásico"},
    {"marca": "Fronius Symo 6.0-3-M", "potencia_w": 6000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Huawei SUN2000-10KTL-M1", "potencia_w": 10000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Ingeteam INGCON SUN 20TL", "potencia_w": 20000, "tipo": "Inversor de String", "fases": "Trifásico"},
    {"marca": "Huawei SUN2000-50KTL-M0", "potencia_w": 50000, "tipo": "Inversor de String", "fases": "Trifásico"}
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
        consumo_diario = st.number_input("Consumo Diario Estimado (Wh/día)", value=4000, step=500)
        hsp = st.number_input("HSP del mes más desfavorable (Invierno)", value=3.2, min_value=1.0, step=0.1)
        dias_autonomia = st.slider("Días de Autonomía Requeridos", min_value=1, max_value=5, value=2)
        v_bateria = st.selectbox("Tensión del Banco de Baterías (V)", [12, 24, 48], index=2)
    else:
        consumo_anual = st.number_input("Consumo Anual de la Vivienda/Industria (kWh/año)", value=5500, step=500)
        hsp = st.number_input("Horas de Sol Pico (HSP) medias anuales", value=4.7, min_value=1.0, step=0.1)

with col_config2:
    st.markdown("**⚡ Factores de Rendimiento y Afección de Sombras**")
    sombreado = st.radio(
        "Presencia de Sombras (Árboles, chimeneas, edificios colindantes):",
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

# Penalización del rendimiento por sombras y corrección
f_perdidas_base = 0.15 if not "Aislada" in modalidad else 0.25
if sombreado == "Sombras parciales / temporales (Pérdidas moderadas)":
    f_perdidas = f_perdidas_base + (0.02 if "Microinversores" in solucion_sombras or "Optimizadores" in solucion_sombras else 0.15)
elif sombreado == "Sombras severas":
    f_perdidas = f_perdidas_base + (0.05 if "Microinversores" in solucion_sombras or "Optimizadores" in solucion_sombras else 0.35)
else:
    f_perdidas = f_perdidas_base

st.write("---")
st.header("🔌 Características de los Componentes")

col_comp1, col_comp2 = st.columns(2)
with col_comp1:
    p_panel = st.number_input("Potencia del Panel Solar Seleccionado (Wp)", value=450, step=10)
    vmp_panel = st.number_input("Tensión a máxima potencia Vmp (V)", value=41.5, step=0.5)
    isc_panel = st.number_input("Corriente de Cortocircuito Isc (A)", value=13.5, step=0.5)
with col_comp2:
    fases_instalacion = st.selectbox("Tipo de Red Eléctrica de la instalación", ["Monofásico", "Trifásico"])

# --- LÓGICA DE CÁLCULO FOTOVOLTAICO ---
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
    # Buscar el microinversor en la base de datos
    for inv in INVERSORES_COMERCIALES:
        if inv["tipo"] == "Microinversor":
            inversor_sugerido = inv
            num_microinversores = num_paneles
            break
else:
    # Buscar inversor central que cubra la potencia total en kWp (con margen de sobredimensionamiento estándar del 10-20%)
    potencia_busqueda_w = (potencia_total_kwp * 1000) * 0.90
    for inv in INVERSORES_COMERCIALES:
        if inv["tipo"] == "Inversor de String" and inv["fases"] == fases_instalacion:
            if inv["potencia_w"] >= potencia_busqueda_w:
                inversor_sugerido = inv
                break
    # Si excede nuestra tabla, coger el más grande
    if not inversor_sugerido:
        inversor_sugerido = INVERSORES_COMERCIALES[-1]

# --- PANEL DE RESULTADOS ---
st.write("---")
st.header("📊 Dictamen y Resultados del Dimensionamiento")

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric(label="Potencia Campo FV Real Instalada", value=f"{potencia_total_kwp:.2f} kWp")
    st.caption(f"Número de paneles: **{num_paneles} uds** de {p_panel}Wp")
with col_res2:
    if num_microinversores > 0:
        st.metric(label="Inversor Comercial Asignado", value=f"{num_microinversores}x {inversor_sugerido['marca']}")
        st.caption(f"Potencia unitaria: {inversor_sugerido['potencia_w']}W AC")
    else:
        st.metric(label="Inversor Comercial Asignado", value=inversor_sugerido["marca"])
        st.caption(f"Potencia Nominal del Equipo: **{inversor_sugerido['potencia_w']/1000:.1f} kW AC**")
with col_res3:
    st.metric(label="Pérdidas Totales Estimadas", value=f"{f_perdidas*100:.1f} %")
    st.caption(f"Estrategia contra sombras: **{solucion_sombras.split(' (')[0]}**")

# --- ESQUEMA DE PROTECCIONES REBT ---
st.write("---")
st.header("🛡️ Esquema Técnico de Protecciones Obligatorias (REBT)")

col_prot1, col_prot2 = st.columns(2)

with col_prot1:
    st.subheader("🔌 Tramo Corriente Continua (CC) - Aguas arriba del Inversor")
    if "Microinversores" in solucion_sombras:
        st.info("ℹ️ Al usar Microinversores, la conversión CC a CA se realiza en el propio panel. No se requiere un cuadro de CC centralizado de alta tensión. Las protecciones se simplifican al tramo de Alterna.")
    else:
        # Cálculo de fusibles e interruptor de corte en carga
        corriente_string = isc_panel * 1.25
        fusible_calibre = 15 if corriente_string <= 15 else 20 # Valores estándar comerciales aproximados
        
        st.markdown(f"""
        * **Interruptor de Corte en Carga (Seccionador CC):** Mínimo **1000V CC** con capacidad de corte para soportar la tensión del string en vacío.
        * **Fusibles de protección (Polo + y Polo -):** Calibre sugerido de **{fusible_calibre}A** (gPV especial fotovoltaica).
        * **Protector contra Sobretensiones Transitorias (SPD CC):** Clase II, tensión de operación superior a la Voc máxima del string (ej. 600V/1000V CC) conectado a la toma de tierra del edificio.
        """)

with col_prot2:
    st.subheader("⚡ Tramo Corriente Alterna (CA) - Cuadro de Interconexión Solar")
    
    # Calcular corriente AC aproximada de salida del inversor para dimensionar magnetotérmico
    p_ac_estimada = inversor_sugerido["potencia_w"] if num_microinversores == 0 else (inversor_sugerido["potencia_w"] * num_microinversores)
    v_ac = 230 if fases_instalacion == "Monofásico" else 400
    
    if fases_instalacion == "Monofásico":
        i_ac = p_ac_estimada / v_ac
    else:
        i_ac = p_ac_estimada / (math.sqrt(3) * v_ac)
        
    # Calibres comerciales estándar de interruptores automáticos
    calibres_pia = [6, 10, 16, 20, 25, 32, 40, 50, 63]
    pia_ac = calibres_pia[-1]
    for p in calibres_pia:
        if p >= i_ac * 1.25: # Margen normativo del 25% para evitar disparos térmicos continuados
            pia_ac = p
            break
            
    st.markdown(f"""
    * **Interruptor Automático (PIA CA):** **{fases_instalacion}**, Calibre de **{pia_ac}A**, Curva C. Capacidad de corte de 6kA según ITC-BT-22.
    * **Interruptor Diferencial (ID CA):** Calibre de **{max(pia_ac, 25)}A / 30mA**. **¡Obligatorio Tipo Clase A / Superinmunizado o Tipo B!** (Para soportar las componentes continuas y fugas de los filtros de los inversores).
    * **Protección contra Sobretensiones (Permanentes y Transitorias CA):** Protector combinado Bobina de disparo + Vigía de tensión para proteger el inversor de anomalías en la red de la distribuidora.
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
    st.success(f"✔️ ¡Instalación solar '{nombre_fv}' guardada con éxito con su correspondiente inversor comercial!")
