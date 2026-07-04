import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Cálculo de Secciones REBT", page_icon="⚡", layout="wide")

st.title("⚡ Módulo 1: Cálculo de Secciones según REBT")
st.markdown("Cálculo exhaustivo por **Intensidad Admisible** (UNE-HD 60364-5-52 / ITC-BT-19) y **Caída de Tensión** con desglose de fórmulas.")

# --- BASE DE DATOS NORMATIVA SIMPLIFICADA (Tabla de intensidades admisibles de muestra para Cu en Aire/Tubo) ---
# En un software comercial esto sería una matriz completa. Aquí estructuramos las más comunes para el motor.
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Intensidades para Cobre, Trifásico (3x), Métodos habituales (B1: Tubo en pared, C: Cable sobre pared, E: Al aire)
IZ_CU_XLPE = {
    "B1": [17, 23, 31, 40, 54, 71, 93, 114, 139, 177, 214, 247, 282, 321, 377, 431],
    "C" : [22, 30, 40, 52, 71, 94, 124, 152, 184, 233, 282, 326, 373, 426, 498, 569],
    "E" : [24, 32, 43, 56, 77, 102, 136, 168, 204, 260, 317, 369, 424, 485, 571, 655]
}

IZ_CU_PVC = {
    "B1": [13.5, 18, 24, 31, 42, 55, 72, 88, 107, 136, 164, 189, 215, 245, 286, 327],
    "C" : [17.5, 24, 32, 41, 57, 76, 99, 121, 147, 185, 224, 258, 294, 335, 391, 446],
    "E" : [18.5, 25, 34, 44, 61, 81, 107, 131, 159, 202, 245, 282, 322, 367, 430, 491]
}

# Inicializar la lista de instalaciones en el session_state si no existe
if 'lista_instalaciones' not in st.session_state:
    st.session_state['lista_instalaciones'] = []

# --- FORMULARIO PARA AÑADIR NUEVA INSTALACIÓN ---
st.header("➕ Añadir Nueva Línea / Circuito")

with st.form("nuevo_circuito_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        id_linea = st.text_input("ID / Nombre de la Línea", value="Línea Subcuadro 1")
        sistema = st.selectbox("Sistema", ["Trifásico", "Monofásico"])
        tension = st.number_input("Tensión (V)", value=400 if sistema == "Trifásico" else 230)
        
    with col2:
        potencia = st.number_input("Potencia Activa (W)", value=15000, step=500)
        cos_phi = st.number_input("Cos φ", value=0.85, min_value=0.1, max_value=1.0, step=0.05)
        longitud = st.number_input("Longitud (m)", value=45.0, step=5.0)
        
    with col3:
        aislamiento = st.selectbox("Aislamiento", ["XLPE / EPR (90°C)", "PVC (70°C)"])
        # Mapeo de métodos REBT (ITC-BT-19)
        metodo_inst = st.selectbox(
            "Método de Instalación (REBT)", 
            [
                "B1 - Bajo tubo en pared aislante / mampostería",
                "C - Unipolar o Multipolar sobre pared de madera/hormigón",
                "E - Al aire libre o en bandeja perforada"
            ]
        )
        cdt_max = st.number_input("CdT Máxima Permitida (%)", value=3.0, step=0.5)

    with col4:
        st.markdown("**Factores de Corrección**")
        f_temp = st.number_input("Factor Temperatura (K1)", value=1.00, min_value=0.1, max_value=1.5, step=0.05, help="Por defecto 1.00 para 40°C al aire libre.")
        f_agrup = st.number_input("Factor Agrupamiento (K2)", value=1.00, min_value=0.1, max_value=1.5, step=0.05, help="Reducción si comparte canalización con otros circuitos.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("⚡ Calcular y Añadir Línea")

# --- LÓGICA DE PROCESAMIENTO AL ENVIAR EL FORMULARIO ---
if submit_btn:
    # 1. Extraer clave del método abreviado (B1, C o E)
    letra_metodo = metodo_inst.split(" - ")[0]
    
    # 2. Corriente de empleo o diseño (Ib)
    if sistema == "Trifásico":
        I_b = potencia / (math.sqrt(3) * tension * cos_phi)
    else:
        I_b = potencia / (tension * cos_phi)
        
    # 3. Conductividad (gamma) corregida según temperatura del conductor
    gamma = 48.5 if "XLPE" in aislamiento else 44.0
    
    # 4. Cálculo por Caída de Tensión (Sección teórica)
    cdt_voltios = (cdt_max / 100.0) * tension
    if sistema == "Monofásico":
        s_cdt_teorica = (2 * longitud * potencia) / (gamma * cdt_voltios * tension)
    else:
        s_cdt_teorica = (longitud * potencia) / (gamma * cdt_voltios * tension)
        
    # Buscar sección comercial mínima para cumplir CdT
    s_comercial_cdt = SECCIONES[-1]
    for s in SECCIONES:
        if s >= s_cdt_teorica:
            s_comercial_cdt = s
            break
            
    # 5. Criterio de Intensidad Admisible (Calentamiento)
    # Corriente corregida que debe soportar teóricamente el cable en tablas: Iz_teorica >= Ib / (K1 * K2)
    factor_total = f_temp * f_agrup
    I_b_corregida = I_b / factor_total
    
    # Seleccionar tabla de intensidades según aislamiento
    tabla_iz = IZ_CU_XLPE[letra_metodo] if "XLPE" in aislamiento else IZ_CU_PVC[letra_metodo]
    
    s_comercial_iz = None
    iz_final_cable = 0
    for idx, s in enumerate(SECCIONES):
        if tabla_iz[idx] >= I_b_corregida:
            s_comercial_iz = s
            iz_final_cable = tabla_iz[idx] * factor_total # Iz real afectada por factores
            break
            
    if s_comercial_iz is None:
        s_comercial_iz = SECCIONES[-1]
        iz_final_cable = tabla_iz[-1] * factor_total

    # 6. Sección Definitiva (La mayor de ambos criterios)
    seccion_final = max(s_comercial_cdt, s_comercial_iz)
    
    # 7. Guardar desglose y memoria de cálculo de esta línea concreta
    nueva_instalacion = {
        "id": id_linea,
        "sistema": sistema,
        "potencia": potencia,
        "Ib": round(I_b, 2),
        "Ib_corr": round(I_b_corregida, 2),
        "longitud": longitud,
        "s_cdt": s_comercial_cdt,
        "s_iz": s_comercial_iz,
        "s_final": seccion_final,
        "Iz_real": round(iz_final_cable, 2),
        "desglose": {
            "gamma": gamma,
            "cdt_v": round(cdt_voltios, 2),
            "s_cdt_t": round(s_cdt_teorica, 2),
            "metodo": letra_metodo,
            "f_tot": factor_total
        }
    }
    
    st.session_state['lista_instalaciones'].append(nueva_instalacion)
    # Sincronizar también con el diccionario del proyecto global para los módulos de presupuesto/unifilar
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
    st.success(f"✔️ Línea '{id_linea}' calculada y añadida al panel general.")

# --- VISTA GENERAL Y TABLA MULTI-INSTALACIÓN ---
st.write("---")
st.header("📋 Cuadro General de Líneas Calculadas")

if not st.session_state['lista_instalaciones']:
    st.info("No hay instalaciones creadas todavía. Utiliza el formulario superior para añadir líneas.")
else:
    # Generar DataFrame para visualización limpia
    datos_tabla = []
    for inst in st.session_state['lista_instalaciones']:
        datos_tabla.append({
            "Línea ID": inst["id"],
            "Sistema": inst["sistema"],
            "Potencia (W)": inst["potencia"],
            "Intensidad Ib (A)": inst["Ib"],
            "Sección por CdT (mm²)": inst["s_cdt"],
            "Sección por Calentamiento (mm²)": inst["s_iz"],
            "Sección Final Mínima (mm²)": f"👉 {inst['s_final']} mm²",
            "Iz Admisible Real (A)": inst["Iz_real"]
        })
    
    df = pd.DataFrame(datos_tabla)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🗑️ Borrar todas las líneas"):
        st.session_state['lista_instalaciones'] = []
        st.session_state['proyecto'] = {}
        st.rerun()

    # --- DESGLOSE MATEMÁTICO INDIVIDUAL (¿Cómo se ha calculado?) ---
    st.write("---")
    st.header("🧮 Memoria Desglosada del Cálculo")
    st.markdown("Selecciona cualquiera de las líneas añadidas para auditar las ecuaciones aplicadas paso a paso:")
    
    opciones_lineas = [inst["id"] for inst in st.session_state['lista_instalaciones']]
    linea_seleccionada = st.selectbox("Ver desarrollo matemático de:", opciones_lineas)
    
    # Buscar los datos de la línea seleccionada
    for inst in st.session_state['lista_instalaciones']:
        if inst["id"] == linea_seleccionada:
            d = inst["desglose"]
            
            st.subheader(f"Justificación Técnica - {inst['id']}")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("#### 🔍 Criterio de Caída de Tensión (CdT)")
                if inst["sistema"] == "Monofásico":
                    st.latex(r"S_{teórica} = \frac{2 \cdot L \cdot P}{\gamma \cdot e \cdot V}")
                    st.write(f"$$S_{{teórica}} = \\frac{{2 \\cdot {inst['longitud']} \\cdot {inst['potencia']}}}{{{d['gamma']} \\cdot {d['cdt_v']} \\cdot {inst['potencia']/(inst['Ib']*0.85):.0f}}} = {d['s_cdt_t']} \\text{{ mm}}^2$$")
                else:
                    st.latex(r"S_{teórica} = \frac{L \cdot P}{\gamma \cdot e \cdot V}")
                    st.write(f"$$S_{{teórica}} = \\frac{{{inst['longitud']} \\cdot {inst['potencia']}}}{{{d['gamma']} \\cdot {d['cdt_v']} \\cdot {inst['potencia']/(math.sqrt(3)*inst['Ib']*0.85):.0f}}} = {d['s_cdt_t']} \\text{{ mm}}^2$$")
                st.write(f"Sección comercial normalizada elegida por CdT: **{inst['s_cdt']} mm²**")
                
            with col_m2:
                st.markdown("#### 🌡️ Criterio de Calentamiento (Intensidad Admisible)")
                st.write(f"Corriente nominal de la carga ($I_b$): **{inst['Ib']} A**")
                st.write(f"Aplicando factores de corrección por entorno ($K_1 \\cdot K_2 = {d['f_tot']:.2f}$):")
                st.latex(r"I_{b\_corregida} = \frac{I_b}{K_1 \cdot K_2}")
                st.write(f"$$I_{{b\\_corregida}} = \\frac{{{inst['Ib']}}}{{{d['f_tot']:.2f}}} = {inst['Ib_corr']} \\text{ A}$$")
                st.write(f"Consultando tablas de la norma para el **Método {d['metodo']}**, la sección mínima que soporta esta corriente es **{inst['s_iz']} mm²** (Admite hasta ${inst['Iz_real']} \\text{{ A}}$ reales).")
            
            st.success(f"**Dictamen final:** Se instala una sección de **{inst['s_final']} mm²** por ser el valor límite más restrictivo de ambos métodos.")
