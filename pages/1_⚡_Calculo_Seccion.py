import streamlit as st
import math
import pandas as pd
import streamlit as st
# 1. Importas tus funciones de estilo desde la carpeta utils
from utils.style import aplicar_estilo_global, generar_banner, aplicar_marca_agua

# 3. Aplicas el diseño y generas el banner superior
aplicar_estilo_global()
generar_banner("⚡ Módulo Técnico", "Subtítulo explicativo del cálculo actual.")

# 4. Metes tus componentes dentro de la tarjeta estilizada usando HTML simple
st.markdown('<div class="premium-card"><h4>📋 Parámetros de Diseño</h4>', unsafe_allow_html=True)

# ... AQUÍ VA TODO TU CÓDIGO NORMAL (st.text_input, st.selectbox, st.button, etc.) ...

st.markdown('</div>', unsafe_allow_html=True) # <-- Cierras la tarjeta al final

st.set_page_config(page_title="Cálculo de Secciones REBT", page_icon="⚡", layout="wide")

st.title("⚡ Módulo 1: Cálculo de Secciones según REBT")
st.markdown("Cálculo exhaustivo por **Intensidad Admisible** (UNE-HD 60364-5-52), **Caída de Tensión** y **Secciones Mínimas Reglamentarias**.")

# --- BASE DE DATOS NORMATIVA AMPLIADA ---
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Mapeo de Secciones Mínimas por tipo de circuito (ITC-BT-25 / ITC-BT-19)
SECCIONES_MINIMAS_REBT = {
    "Alumbrado general (C1)": 1.5,
    "Tomas de corriente de uso general / Frigorífico (C2)": 2.5,
    "Cocina y Horno (C3)": 6.0,
    "Lavadora, Lavavajillas y Termo eléctrico (C4)": 4.0,
    "Tomas de corriente de cocina y baño (C5)": 2.5,
    "Instalación Interior General (Fuerza / Motores)": 1.5,
    "Derivación Individual (Contador a Cuadro)": 6.0,
    "Línea General de Alimentación (LGA)": 16.0
}

# Matriz de Intensidades Admisibles para Cobre (Trifásico, 3 conductores cargados)
# Ampliado con métodos A1, A2, B1, B2, C, E, F
IZ_CU_XLPE = {
    "A1 (Conductores aislados en tubo empotrado en pared aislante)": [13, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291, 334],
    "A2 (Cable multiconductor en tubo empotrado en pared aislante)": [13, 17.5, 24, 31, 41, 54, 71, 86, 103, 130, 156, 179, 204, 231, 270, 310],
    "B1 (Conductores aislados en tubo sobre pared o empotrado en mampostería)": [17, 23, 31, 40, 54, 71, 93, 114, 139, 177, 214, 247, 282, 321, 377, 431],
    "B2 (Cable multiconductor en tubo sobre pared o empotrado en mampostería)": [16.5, 22, 30, 38, 49, 65, 84, 103, 124, 156, 188, 216, 245, 278, 324, 371],
    "C (Cable unipolar o multiconductor sobre pared de madera o mampostería)": [22, 30, 40, 52, 71, 94, 124, 152, 184, 233, 282, 326, 373, 426, 498, 569],
    "E (Cable multiconductor en bandeja perforada o al aire libre)": [24, 32, 43, 56, 77, 102, 136, 168, 204, 260, 317, 369, 424, 485, 571, 655],
    "F (Cables unipolares en contacto en bandeja perforada o al aire libre)": [23, 31, 42, 54, 75, 100, 133, 164, 199, 253, 309, 361, 415, 474, 558, 642]
}

IZ_CU_PVC = {
    "A1 (Conductores aislados en tubo empotrado en pared aislante)": [10.5, 15, 19.5, 25, 33, 43, 57, 69, 83, 104, 125, 143, 163, 184, 215, 246],
    "A2 (Cable multiconductor en tubo empotrado en pared aislante)": [10.5, 14, 18.5, 24, 32, 42, 54, 65, 78, 97, 117, 134, 152, 172, 200, 229],
    "B1 (Conductores aislados en tubo sobre pared o empotrado en mampostería)": [13.5, 18, 24, 31, 42, 55, 72, 88, 107, 136, 164, 189, 215, 245, 286, 327],
    "B2 (Cable multiconductor en tubo sobre pared o empotrado en mampostería)": [13, 17.5, 23, 29, 39, 51, 66, 80, 96, 121, 145, 166, 189, 213, 248, 283],
    "C (Cable unipolar o multiconductor sobre pared de madera o mampostería)": [17.5, 24, 32, 41, 57, 76, 99, 121, 147, 185, 224, 258, 294, 335, 391, 446],
    "E (Cable multiconductor en bandeja perforada o al aire libre)": [18.5, 25, 34, 44, 61, 81, 107, 131, 159, 202, 245, 282, 322, 367, 430, 491],
    "F (Cables unipolares en contacto en bandeja perforada o al aire libre)": [18.5, 25, 33, 43, 59, 79, 104, 128, 155, 197, 239, 275, 313, 357, 419, 479]
}

if 'lista_instalaciones' not in st.session_state:
    st.session_state['lista_instalaciones'] = []

# --- FORMULARIO ---
st.header("➕ Añadir Nueva Línea / Circuito")

with st.form("nuevo_circuito_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        id_linea = st.text_input("ID / Nombre de la Línea", value="Línea Cocina C3")
        tipo_circuito = st.selectbox("Tipo de Aplicación (Sección Mínima REBT)", list(SECCIONES_MINIMAS_REBT.keys()))
        sistema = st.selectbox("Sistema", ["Trifásico", "Monofásico"])
        tension = st.number_input("Tensión (V)", value=400 if sistema == "Trifásico" else 230)
        
    with col2:
        potencia = st.number_input("Potencia Activa (W)", value=5750, step=250)
        cos_phi = st.number_input("Cos φ", value=0.90, min_value=0.1, max_value=1.0, step=0.05)
        longitud = st.number_input("Longitud (m)", value=20.0, step=5.0)
        
    with col3:
        aislamiento = st.selectbox("Aislamiento", ["XLPE / EPR (90°C)", "PVC (70°C)"])
        metodo_inst = st.selectbox("Método de Instalación (UNE-HD 60364-5-52)", list(IZ_CU_XLPE.keys()))
        cdt_max = st.number_input("CdT Máxima Permitida (%)", value=3.0, step=0.5)

    with col4:
        st.markdown("**Factores de Corrección**")
        f_temp = st.number_input("Factor Temperatura (K1)", value=1.00, min_value=0.1, max_value=1.5, step=0.05)
        f_agrup = st.number_input("Factor Agrupamiento (K2)", value=1.00, min_value=0.1, max_value=1.5, step=0.05)
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("⚡ Calcular y Añadir Línea")

if submit_btn:
    # 1. Obtener la sección mínima legal
    s_min_legal = SECCIONES_MINIMAS_REBT[tipo_circuito]
    
    # 2. Corriente de diseño (Ib)
    if sistema == "Trifásico":
        I_b = potencia / (math.sqrt(3) * tension * cos_phi)
    else:
        I_b = potencia / (tension * cos_phi)
        
    # 3. Conductividad (gamma)
    gamma = 48.5 if "XLPE" in aislamiento else 44.0
    
    # 4. Cálculo por Caída de Tensión
    cdt_voltios = (cdt_max / 100.0) * tension
    if sistema == "Monofásico":
        s_cdt_teorica = (2 * longitud * potencia) / (gamma * cdt_voltios * tension)
    else:
        s_cdt_teorica = (longitud * potencia) / (gamma * cdt_voltios * tension)
        
    s_comercial_cdt = SECCIONES[-1]
    for s in SECCIONES:
        if s >= s_cdt_teorica:
            s_comercial_cdt = s
            break
            
    # 5. Criterio de Intensidad Admisible (Calentamiento)
    factor_total = f_temp * f_agrup
    I_b_corregida = I_b / factor_total
    
    tabla_iz = IZ_CU_XLPE[metodo_inst] if "XLPE" in aislamiento else IZ_CU_PVC[metodo_inst]
    
    s_comercial_iz = SECCIONES[-1]
    iz_final_cable = 0
    for idx, s in enumerate(SECCIONES):
        if tabla_iz[idx] >= I_b_corregida:
            s_comercial_iz = s
            iz_final_cable = tabla_iz[idx] * factor_total
            break

    # 6. Sección Definitiva (La mayor de los TRES criterios: CdT, Iz, Mínima Legal)
    seccion_final = max(s_comercial_cdt, s_comercial_iz, s_min_legal)
    
    # 7. Indexar resultados
    nueva_instalacion = {
        "id": id_linea,
        "tipo_circuito": tipo_circuito,
        "sistema": sistema,
        "potencia": potencia,
        "Ib": round(I_b, 2),
        "Ib_corr": round(I_b_corregida, 2),
        "longitud": longitud,
        "s_min_legal": s_min_legal,
        "s_cdt": s_comercial_cdt,
        "s_iz": s_comercial_iz,
        "s_final": seccion_final,
        "Iz_real": round(iz_final_cable, 2),
        "desglose": {
            "gamma": gamma,
            "cdt_v": round(cdt_voltios, 2),
            "s_cdt_t": round(s_cdt_teorica, 2),
            "metodo": metodo_inst.split(" ")[0],
            "f_tot": factor_total
        }
    }
    
    st.session_state['lista_instalaciones'].append(nueva_instalacion)
    
    if 'proyecto' not in st.session_state:
        st.session_state['proyecto'] = {}
    st.session_state['proyecto'][id_linea] = {
        "sistema": sistema,
        "tension": tension,
        "intensidad": round(I_b, 2),
        "seccion": seccion_final,
        "longitud": longitud,
        "material": "Cobre (Cu)"
    }
    st.success(f"✔️ Línea '{id_linea}' añadida.")

# --- CUADRO GENERAL ---
st.write("---")
st.header("📋 Cuadro General de Líneas Calculadas")

if not st.session_state['lista_instalaciones']:
    st.info("No hay instalaciones creadas todavía.")
else:
    datos_tabla = []
    for inst in st.session_state['lista_instalaciones']:
        datos_tabla.append({
            "Línea ID": inst["id"],
            "Uso / Circuito": inst["tipo_circuito"],
            "Intensidad Ib (A)": inst["Ib"],
            "Mínima REBT (mm²)": inst["s_min_legal"],
            "Por CdT (mm²)": inst["s_cdt"],
            "Por Calentamiento (mm²)": inst["s_iz"],
            "Sección Final (mm²)": f"👉 {inst['s_final']} mm²",
            "Iz Adm. Real (A)": inst["Iz_real"]
        })
    
    df = pd.DataFrame(datos_tabla)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🗑️ Borrar todas las líneas"):
        st.session_state['lista_instalaciones'] = []
        st.session_state['proyecto'] = {}
        st.rerun()

    # --- DESGLOSE ---
    st.write("---")
    st.header("🧮 Memoria Desglosada del Cálculo")
    
    opciones_lineas = [inst["id"] for inst in st.session_state['lista_instalaciones']]
    linea_seleccionada = st.selectbox("Ver desarrollo matemático de:", opciones_lineas)
    
    for inst in st.session_state['lista_instalaciones']:
        if inst["id"] == linea_seleccionada:
            d = inst["desglose"]
            st.subheader(f"Justificación Técnica - {inst['id']}")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("#### 🔍 Criterio de Caída de Tensión (CdT)")
                st.write(f"Conductividad del material: $\\gamma = {d['gamma']}$")
                st.write(f"Caída de tensión límite admisible: {d['cdt_v']} V")
                if inst["sistema"] == "Monofásico":
                    st.latex(r"S_{teórica} = \frac{2 \cdot L \cdot P}{\gamma \cdot e \cdot V}")
                else:
                    st.latex(r"S_{teórica} = \frac{L \cdot P}{\gamma \cdot e \cdot V}")
                st.info(f"Sección teórica resultante por CdT: **{d['s_cdt_t']} mm²** -> Comercial: **{inst['s_cdt']} mm²**")
                
            with col_m2:
                st.markdown("#### 🌡️ Criterio de Calentamiento e Impedimento Legal")
                st.latex(r"I_{b\_corregida} = \frac{I_b}{K_1 \cdot K_2}")
                st.info(f"Intensidad de diseño corregida: {inst['Ib']} / {d['f_tot']:.2f} = **{inst['Ib_corr']} A**")
                st.write(f"Método de instalación: **{d['metodo']}**. Sección requerida por tablas: **{inst['s_iz']} mm²**")
                st.write(f"Sección mínima impuesta por el REBT para este uso: **{inst['s_min_legal']} mm²**")
            
            st.success(f"**Dictamen final para {inst['id']}:** Se adopta una sección de **{inst['s_final']} mm²** (el valor más exigente de los tres criterios analizados).")
