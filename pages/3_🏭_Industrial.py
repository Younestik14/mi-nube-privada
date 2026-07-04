import streamlit as st
import math
import pandas as pd
import streamlit as st
# 1. Importas tus funciones de estilo desde la carpeta utils
from utils.style import aplicar_estilo_global, generar_banner

# 2. Configuras la página de Streamlit
st.set_page_config(page_title="Mi Apartado - IDEA", layout="wide", initial_sidebar_state="collapsed")

# 3. Aplicas el diseño y generas el banner superior
aplicar_estilo_global()
generar_banner("⚡ Módulo Técnico", "Subtítulo explicativo del cálculo actual.")

# 4. Metes tus componentes dentro de la tarjeta estilizada usando HTML simple
st.markdown('<div class="premium-card"><h4>📋 Parámetros de Diseño</h4>', unsafe_allow_html=True)

# ... AQUÍ VA TODO TU CÓDIGO NORMAL (st.text_input, st.selectbox, st.button, etc.) ...

st.markdown('</div>', unsafe_allow_html=True) # <-- Cierras la tarjeta al final
st.set_page_config(page_title="Diseño Multifilar Industrial", page_icon="🏭", layout="wide")

st.title("🏭 Módulo 3: Modelado de Esquema Multifilar (Fuerza y Mando)")
st.markdown("Diseña la arquitectura de tu cuadro eléctrico asociando elementos de potencia y circuitos de maniobra según el REBT.")

# --- INICIALIZACIÓN DEL ESQUEMA EN SESSION STATE ---
if 'esquema_multifilar' not in st.session_state:
    st.session_state['esquema_multifilar'] = []
if 'proyecto' not in st.session_state:
    st.session_state['proyecto'] = {}

# --- CATÁLOGO EXTENSO DE APARAMENTA COMERCIAL ---
COMPONENTES_FUERZA = [
    "Interruptor Seccionador en Carga (Corte General)",
    "Interruptor Automático Magnetotérmico (PIA)",
    "Interruptor Automático Caja Moldeada (MCCB)",
    "Interruptor Diferencial Superinmunizado (Clase A/B)",
    "Disyuntor Guardamotor (Protección Térmico-Magnética de Motores)",
    "Contactor de Potencia (KM)",
    "Relé Térmico de Sobrecarga (F)",
    "Variador de Frecuencia (VFD) / Arrancador Suave",
    "Bornes de Potencia (U-V-W-PE)"
]

COMPONENTES_MANDO = [
    "Transformador de Maniobra (400V/230V a 24V CA)",
    "Fuente de Alimentación Conmutada (230V CA a 24V CC)",
    "Seta de Emergencia (Contacto NC de seguridad)",
    "Interruptor Magnetotérmico de Maniobra (Calibre bajo 2A-6A)",
    "Autómata Programable (PLC / LOGO!)",
    "Módulo de Relé de Seguridad (Pilz / Preadvertencia)",
    "Contactor Auxiliar / Relé de Maniobra (KA)",
    "Pulsador de Marcha (NA) / Paro (NC)",
    "Final de Carrera / Sensor Inductivo",
    "Piloto Luminoso de Señalización (H)",
    "Sirena / Avisador Acústico"
]

# --- INTERFAZ PRINCIPAL DE MODELADO ---
st.header("🛠️ Configuración de Líneas del Esquema")

with st.form("form_multifilar", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        id_linea = st.text_input("Identificador de la Línea / Símbolo", value="Línea Cinta Transportadora - Q1")
        tipo_arranque = st.selectbox(
            "Configuración del Circuito de Fuerza",
            [
                "Salida Directa (Protección + Contactor)",
                "Arranque Motor con Guardamotor + Contactor + Térmico",
                "Línea de Distribución Directa (Solo Protección)",
                "Salida Especial con Variador de Frecuencia",
                "Línea Dedicada a Maniobra (Alimentación de Mando)"
            ]
        )
        potencia_linea_kw = st.number_input("Potencia Activa Asociada (kW)", value=4.0, step=0.5)

    with col2:
        st.markdown("**⚡ Aparamenta de Fuerza Seleccionada**")
        comp_fuerza_sel = st.multiselect(
            "Componentes en el carril DIN de Potencia:",
            COMPONENTES_FUERZA,
            default=[COMPONENTES_FUERZA[4], COMPONENTES_FUERZA[5]] if "Motor" in tipo_arranque else [COMPONENTES_FUERZA[1]]
        )
        seccion_cable = st.selectbox("Sección del conductor (mm2)", [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50])

    with col3:
        st.markdown("**🧠 Circuito de Mando y Maniobra Asociado**")
        tension_mando = st.selectbox("Tensión del Lazo de Mando", ["24 V CC (Seguridad)", "24 V CA", "230 V CA", "Sin circuito de mando"])
        comp_mando_sel = st.multiselect(
            "Componentes del circuito de maniobra:",
            COMPONENTES_MANDO,
            default=[COMPONENTES_MANDO[2], COMPONENTES_MANDO[4], COMPONENTES_MANDO[7], COMPONENTES_MANDO[9]] if tension_mando != "Sin circuito de mando" else []
        )
        longitud_linea = st.number_input("Longitud del circuito (m)", value=25.0, step=5.0)

    btn_guardar_linea = st.form_submit_button("📥 Enclavar Línea en el Esquema")

if btn_guardar_linea:
    # Cálculo básico de corrientes para dimensionar calibres comerciales
    pot_w = potencia_linea_kw * 1000
    # Asumimos trifásico 400V para fuerza industrial estándar, cos_phi = 0.8
    i_nominal = pot_w / (math.sqrt(3) * 400 * 0.8) if potencia_linea_kw > 0 else 0
    
    # Factor de seguridad por arranque en fuerza (ITC-BT-47)
    i_diseno = i_nominal * 1.25 if "Motor" in tipo_arranque else i_nominal
    
    st.session_state['esquema_multifilar'].append({
        "id": id_linea,
        "config_fuerza": tipo_arranque,
        "potencia_kw": potencia_linea_kw,
        "i_nom": round(i_nominal, 2),
        "i_diseno": round(i_diseno, 2),
        "componentes_fuerza": comp_fuerza_sel,
        "tension_mando": tension_mando,
        "componentes_mando": comp_mando_sel,
        "seccion": seccion_cable,
        "longitud": longitud_linea
    })
    st.success(f"✔️ Línea '{id_linea}' añadida al árbol del esquema multifilar.")
    # --- CÁLCULO DE CALIBRES, VISUALIZACIÓN Y AUDITORÍA DE ERRORES (PARTE 2) ---
st.write("---")
st.header("📋 Desglose Técnico del Esquema y Calibres de Aparamenta")

if not st.session_state['esquema_multifilar']:
    st.info("El esquema está vacío. Configura y añade líneas desde el panel superior para generar el cableado y los calibres.")
else:
    errores_esquema = []
    potencia_total_cuadro = 0.0
    datos_esquema_tabla = []
    
    # Series comerciales homologadas
    calibres_pia = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125]
    
    for linea in st.session_state['esquema_multifilar']:
        potencia_total_cuadro += linea["potencia_kw"]
        
        # 1. Dimensionamiento de la protección de potencia (Fuerza)
        calibre_fuerza = 125
        for c_com in calibres_pia:
            if c_com >= linea["i_diseno"]:
                calibre_fuerza = c_com
                break
                
        # 2. Dimensionamiento del Contactor (KM) según categoría AC-3 (Motores) o AC-1 (Resistivo)
        if "Motor" in linea["config_fuerza"]:
            cat_contactor = f"AC-3 (Servicio Motor) - Mínimo {calibre_fuerza}A"
        else:
            cat_contactor = f"AC-1 (Carga no inductiva) - Mínimo {calibre_fuerza}A"
            
        # 3. Verificación de Caída de Tensión (CdT) en Fuerza
        gamma = 48.5  # Conductividad del cobre a temperatura de servicio
        v_base = 400 if "Maniobra" not in linea["config_fuerza"] else 230
        f_dist = 1 if "Maniobra" not in linea["config_fuerza"] else 2
        
        cdt_v = (f_dist * linea["longitud"] * (linea["potencia_kw"] * 1000)) / (gamma * linea["seccion"] * v_base)
        cdt_porc = (cdt_v / v_base) * 100
        
        # --- ALERTAS INTELIGENTES DE LA LÍNEA ---
        if cdt_porc > 5.0:
            errores_esquema.append(f"❌ **Línea [{linea['id']}]:** Caída de tensión excesiva ({round(cdt_porc, 2)}%). Supera el 5% máximo reglamentario para fuerza en el REBT. **Solución:** Incrementa la sección del cable.")
            
        if "Motor" in linea["config_fuerza"]:
            tiene_termico = any("Térmico" in x or "Guardamotor" in x for x in linea["componentes_fuerza"])
            if not tiene_termico:
                errores_esquema.append(f"❌ **Línea [{linea['id']}]:** Peligro crítico. Se ha configurado un motor asíncrono pero no se ha seleccionado Relé Térmico ni Disyuntor Guardamotor en el circuito de potencia.")
                
        if linea["tension_mando"] != "Sin circuito de mando" and not any("Transformador" in x or "Fuente" in x for x in linea["componentes_mando"]):
            errores_esquema.append(f"⚠️ **Línea [{linea['id']}]:** El lazo de mando funciona a baja tensión ({linea['tension_mando']}) pero no has incluido un Transformador o Fuente de Alimentación de aislamiento en la aparamenta.")

        # Añadir al listado visual del esquema
        datos_esquema_tabla.append({
            "Línea / Símbolo": linea["id"],
            "Configuración": linea["config_fuerza"],
            "Potencia (kW)": linea["potencia_kw"],
            "Intensidad (A)": f"{linea['i_nom']} A",
            "Protección Sugerida": f"{calibre_fuerza}A (Curva D/C)" if "Motor" in linea["config_fuerza"] else f"{calibre_fuerza}A (Curva C)",
            "Contactor Asociado": cat_contactor,
            "Sección": f"{linea['seccion']} mm2",
            "CdT (%)": f"{round(cdt_porc, 2)}%",
            "Elementos Mando": ", ".join(linea["componentes_mando"]) if linea["componentes_mando"] else "Ninguno (Mando directo)"
        })

    # Renderizar la matriz del esquema multifilar
    df_esquema = pd.DataFrame(datos_esquema_tabla)
    st.dataframe(df_esquema, use_container_width=True, hide_index=True)
    
    # --- CÁLCULO DE CABECERA GENERAL DEL CUADRO ---
    i_simultanea_cuadro = sum(l["i_nom"] for l in st.session_state['esquema_multifilar']) * 0.8
    
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.metric(label="Potencia Activa Total del Cuadro", value=f"{round(potencia_total_cuadro, 2)} kW")
    with col_inf2:
        st.metric(label="Intensidad General Simultánea Estimada (80%)", value=f"{round(i_simultanea_cuadro, 2)} A")

    # --- APARTADO EXCLUSIVO DE TELEMETRÍA DE ERRORES ---
    st.write("---")
    st.subheader("🚨 Panel de Alertas y Errores de Diseño Eléctrico")
    
    if errores_esquema:
        for err in errores_esquema:
            if "❌" in err:
                st.error(err)
            else:
                st.warning(err)
    else:
        st.success("🎉 ¡Esquema multifilar impecable! Toda la aparamenta está bien coordinada, protegida térmicamente y cumple los límites del REBT.")

    # --- CONTROLES DE MEMORIA ---
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🗑️ Resetear Esquema Completo"):
            st.session_state['esquema_multifilar'] = []
            st.rerun()
            
    with col_btn2:
        if st.button("💾 Enviar Cuadro al Resumen General"):
            st.session_state['proyecto'][nombre_cuadro] = {
                "tipo": "Cuadro Multifilar de Fuerza y Maniobra",
                "potencia_kw": round(potencia_total_cuadro, 2),
                "intensidad_cabecera": round(i_simultanea_cuadro, 2),
                "lineas_activas": len(st.session_state['esquema_multifilar'])
            }
            st.success("✔️ Arquitectura de cuadro volcada al buffer del proyecto.")
