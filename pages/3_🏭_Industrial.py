import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Módulo Industrial REBT", page_icon="🏭", layout="wide")

st.title("🏭 Módulo 3: Gestión de Cargas Industriales y Centro de Mando")
st.markdown("Configuración de receptores, diseño del cuadro general y auditoría automática de errores técnicos según el REBT.")

# Inicializar listas en la sesión si no existen para evitar pérdidas de datos al refrescar
if 'cargas_industriales' not in st.session_state:
    st.session_state['cargas_industriales'] = []
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

# --- PANELES PRINCIPALES DE ENTRADA (Páginas Centrales sin Sidebar) ---
tabs_ing = st.tabs(["🔌 1. Añadir Receptores Industriales", "🛡️ 2. Configuración del Centro de Mando (CGMP)"])

# --- TAB 1: REGISTRO DE MAQUINARIA INDUSTRIAL ---
with tabs_ing[0]:
    st.subheader("Añadir maquinaria y elementos habituales a la instalación")
    
    with st.form("form_cargas", clear_on_submit=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            nombre_carga = st.text_input("Nombre de la Carga / Máquina", value="Motor Extractor Central")
            tipo_receptor = st.selectbox(
                "Tipo de Elemento Industrial",
                [
                    "Motor Asíncrono Trifásico (Fuerza)", 
                    "Horno Industrial / Resistivo", 
                    "Línea de Alumbrado Fluorescente/LED Industrial", 
                    "Grupo de Soldadura", 
                    "Climatización / VRV"
                ]
            )
            sistema_carga = st.selectbox("Alimentación", ["Trifásico", "Monofásico"])
            
        with col_c2:
            potencia_kw = st.number_input("Potencia Nominal (kW)", value=7.5, min_value=0.1, step=0.5)
            tension_carga = st.number_input("Tensión de Servicio (V)", value=400 if sistema_carga == "Trifásico" else 230)
            cos_phi_actual = st.number_input("Cos phi Actual del Receptor", value=0.75, min_value=0.2, max_value=1.0, step=0.05)
            
        with col_c3:
            longitud_ramal = st.number_input("Longitud del ramal al cuadro (m)", value=15.0, step=2.0)
            seccion_conductor = st.selectbox("Sección asignada al cable (mm2)", [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70])
            compensar = st.checkbox("Prever compensación individual de reactiva (Cos phi a 0.95)", value=True)
            
        btn_carga = st.form_submit_button("📥 Registrar Receptor")
        
        if btn_carga:
            p_w = potencia_kw * 1000
            # Coeficiente REBT de seguridad por picos de arranque (ITC-BT-47)
            factor_motor = 1.25 if "Motor" in tipo_receptor else 1.0
            
            if sistema_carga == "Trifásico":
                i_nom = p_w / (math.sqrt(3) * tension_carga * cos_phi_actual)
            else:
                i_nom = p_w / (tension_carga * cos_phi_actual)
                
            i_diseno = i_nom * factor_motor
            
            # Cálculo de potencia reactiva para la batería de condensadores
            kvar_condensador = 0.0
            if compensar and cos_phi_actual < 0.95:
                tan_fi_actual = math.tan(math.acos(cos_phi_actual))
                tan_fi_target = math.tan(math.acos(0.95))
                kvar_condensador = (p_w / 1000) * (tan_fi_actual - tan_fi_target)
                
            st.session_state['cargas_industriales'].append({
                "nombre": nombre_carga,
                "tipo": tipo_receptor,
                "sistema": sistema_carga,
                "potencia_kw": potencia_kw,
                "i_nom": round(i_nom, 2),
                "i_diseno": round(i_diseno, 2),
                "longitud": longitud_ramal,
                "seccion": seccion_conductor,
                "kvar_bateria": round(max(0.0, kvar_condensador), 2),
                "cos_phi": cos_phi_actual
            })
            st.success(f"Receptor registrado correctamente.")

# --- TAB 2: CONFIGURACIÓN DE LA CABECERA DEL CUADRO ---
with tabs_ing[1]:
    st.subheader("Parámetros de la Cabecera del Cuadro General")
    col_cc1, col_cc2 = st.columns(2)
    
    with col_cc1:
        nombre_cuadro = st.text_input("Denominación del Cuadro", value="CGMP Central Industria")
        iga_elegido = st.selectbox("Calibre del IGA deseado (A)", [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 250], index=6)
    with col_cc2:
        dif_sens = st.selectbox("Sensibilidad del Diferencial General", ["30 mA", "300 mA (Industrial)", "500 mA"], index=1)
        tipo_dif = st.selectbox("Tipo de Diferencial", ["Clase AC", "Clase A (Superinmunizado)", "Clase B"])
        # --- PROCESAMIENTO GENERAL, CALIBRES Y ERRORES (PARTE 2) ---
st.write("---")
st.header("📊 Dimensionamiento de Calibres e Inspección de Seguridad")

if not st.session_state['cargas_industriales']:
    st.info("Agrega receptores en la pestaña superior para auditar el Centro de Mando.")
else:
    errores = []
    potencia_total_activa = 0
    datos_receptores_tabla = []
    
    # Tabla de calibres comerciales normalizados en España
    calibres_comerciales = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125]
    
    for c in st.session_state['cargas_industriales']:
        potencia_total_activa += c["potencia_kw"]
        
        # 1. Asignación automática de calibre de protección individual (PIA)
        pia_asignado = 125
        for cal in calibres_comerciales:
            if cal >= c["i_diseno"]:
                pia_asignado = cal
                break
                
        # 2. Verificar Caída de Tensión del ramal (Cobre, aislamiento termoestable)
        gamma = 48.5 
        v_base = 400 if c["sistema"] == "Trifásico" else 230
        factor_dist = 1 if c["sistema"] == "Trifásico" else 2
        
        cdt_v = (factor_dist * c["longitud"] * (c["potencia_kw"]*1000)) / (gamma * c["seccion"] * v_base)
        cdt_porcentaje = (cdt_v / v_base) * 100
        
        # --- Auditoría de Errores por Receptor ---
        if cdt_porcentaje > 5.0:
            errores.append(f"❌ **Línea [{c['nombre']}]:** Caída de tensión excesiva ({round(cdt_porcentaje, 2)}%). Supera el 5% máximo para receptores de fuerza según el REBT. **Solución:** Aumenta la sección del conductor.")
            
        datos_receptores_tabla.append({
            "Receptor": c["nombre"],
            "Potencia (kW)": c["potencia_kw"],
            "I Nominal (A)": c["i_nom"],
            "I Diseño (REBT)": c["i_diseno"],
            "PIA Sugerido": f"{pia_asignado}A",
            "Sección": f"{c['seccion']} mm2",
            "CdT (%)": f"{round(cdt_porcentaje, 2)}%",
            "Condensador (kVAr)": c["kvar_bateria"]
        })

    # Mostrar matriz de cargas
    df_ind = pd.DataFrame(datos_receptores_tabla)
    st.dataframe(df_ind, use_container_width=True, hide_index=True)
    
    # Cálculo global del cuadro aplicando factor de simultaneidad (80%)
    i_total_estimada = sum(item["i_nom"] for item in st.session_state['cargas_industriales']) * 0.8
    
    # --- Auditoría de Errores del Centro de Mando ---
    if iga_elegido < i_total_estimada:
        errores.append(f"❌ **Centro de Mando [{nombre_cuadro}]:** El calibre del IGA ({iga_elegido}A) es INFERIOR a la corriente simultánea estimada de la planta ({round(i_total_estimada, 2)}A). El interruptor saltará por sobrecarga térmica general. **Solución:** Selecciona un calibre de cabecera superior.")
        
    if "AC" in tipo_dif and any("Motor" in item["tipo"] for item in st.session_state['cargas_industriales']):
        errores.append(f"⚠️ **Centro de Mando [{nombre_cuadro}]:** Se ha detectado un Diferencial Clase AC dando servicio a motores asíncronos. Riesgo de cegado del núcleo por armónicos. **Solución:** Sustituye por Clase A (Superinmunizado) o Clase B.")

    # --- PANEL EXCLUSIVO DE TELEMETRÍA DE ERRORES ---
    st.write("---")
    st.subheader("🚨 Panel de Alertas y Errores Normativos")
    
    if errores:
        for err in errores:
            if "❌" in err:
                st.error(err)
            else:
                st.warning(err)
    else:
        st.success("🎉 ¡Instalación en regla! No se han detectado infracciones de calibre ni caídas de tensión fuera de rango legal.")
        
    # --- BOTONES DE CONTROL GENERAL ---
    col_acc1, col_acc2 = st.columns(2)
    with col_acc1:
        if st.button("🗑️ Vaciar Elementos Industriales"):
            st.session_state['cargas_industriales'] = []
            st.rerun()
    with col_acc2:
        if st.button("💾 Consolidar Datos en Memoria Global"):
            st.session_state['proyecto'][nombre_cuadro] = {
                "tipo": "Cuadro Industrial Distribución",
                "potencia_kw": round(potencia_total_activa, 2),
                "intensidad": round(i_total_estimada, 2),
                "kvar_bateria": round(sum(item["kvar_bateria"] for item in st.session_state['cargas_industriales']), 2)
            }
            st.success("✔️ Datos indexados con éxito en la memoria del proyecto.")
