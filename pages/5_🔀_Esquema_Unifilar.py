import streamlit as st
import pandas as pd

st.set_page_config(page_title="Diseño Unifilar Caneco Style", page_icon="⚡", layout="wide")

st.title("⚡ Módulo 3: Configuración y Cálculo de Esquema Unifilar")
st.markdown("Generación de esquemas unifilares con simbología normalizada y árbol de distribución inspirado en Caneco BT.")

# --- INICIALIZACIÓN DE LA TOPOLOGÍA DEL CUADRO ---
if 'cuadro_unifilar' not in st.session_state:
    # Estructura precargada con la acometida y circuitos básicos del REBT para pruebas rápidas
    st.session_state['cuadro_unifilar'] = [
        {
            "id": "C1", 
            "tipo": "Alumbrado General", 
            "polos": "1P+N", 
            "pia": "10A", 
            "seccion": "1.5 mm²", 
            "icp": "6 kA",
            "mecanismo": "Interruptor / Pulsador",
            "icono": "💡"
        },
        {
            "id": "C2", 
            "tipo": "Tomas de Uso General", 
            "polos": "1P+N", 
            "pia": "16A", 
            "seccion": "2.5 mm²", 
            "icp": "6 kA",
            "mecanismo": "Base 16A + T",
            "icono": "🔌"
        },
        {
            "id": "C3", 
            "tipo": "Cocina y Horno", 
            "polos": "1P+N", 
            "pia": "25A", 
            "seccion": "6 mm²", 
            "icp": "6 kA",
            "mecanismo": "Base 25A + T",
            "icono": "🍳"
        }
    ]

# --- PANTALLA PRINCIPAL: DATOS GENERALES DE LA ACOMETIDA ---
st.subheader("🏢 Datos Generales del Cuadro y Suministro de Cabecera")
col_cab1, col_cab2, col_cab3, col_cab4 = st.columns(4)

with col_cab1:
    nombre_cuadro = st.text_input("Identificación del Cuadro", value="CGMP (Cuadro General)")
with col_cab2:
    v_servicio = st.selectbox("Tensión de Red", ["Monofásica (230 V)", "Trifásica (400 V)"])
with col_cab3:
    iga_cabecera = st.selectbox("Calibre IGA General", ["25 A", "32 A", "40 A", "50 A", "63 A"])
with col_cab4:
    sens_dif = st.selectbox("Sensibilidad Diferencial", ["30 mA (Personas)", "300 mA (Industrial)"])

st.write("---")

# --- DISTRIBUCIÓN EN PANTALLA PRINCIPAL (ESTILO INTERFAZ CANECO) ---
col_izq, col_der = st.columns([1, 2])

# --- COLUMNA IZQUIERDA: GESTIÓN DE LÍNEAS Y CIRCUITOS DE SALIDA ---
with col_izq:
    st.header("🛠️ Configuración de Línea")
    
    with st.form("nuevo_circuito_form"):
        id_circuito = st.text_input("Etiqueta de Circuito (Ej: C4, M1)", value=f"C{len(st.session_state['cuadro_unifilar']) + 1}")
        tipo_carga = st.selectbox("Destino / Tipo de Carga:", [
            "Alumbrado General", 
            "Tomas de Uso General", 
            "Cocina y Horno", 
            "Lavadora y Termo", 
            "Baños y Cocina", 
            "Motor Asíncrono (Fuerza)",
            "Circuito de Maniobra / LOGO!",
            "Línea de Telecomunicaciones"
        ])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            polos = st.selectbox("Polaridad", ["1P+N", "3P", "3P+N"])
            calibre_pia = st.selectbox("Calibre PIA", ["6A", "10A", "16A", "20A", "25A", "32A", "40A", "50A", "63A"])
        with col_f2:
            seccion_cable = st.selectbox("Sección Conductor", ["1.5 mm²", "2.5 mm²", "4 mm²", "6 mm²", "10 mm²", "16 mm²"])
            poder_corte = st.selectbox("Poder de Corte (Icn)", ["4.5 kA", "6 kA", "10 kA"])
            
        mecanismo_final = st.selectbox("Elemento Terminal / Salida", [
            "Punto de Luz / Portalámparas E27", 
            "Base de enchufe 16A (Niessen Zenit)", 
            "Base de fuerza Simon 25A", 
            "Bornero / Conexión Directa", 
            "Guardamotor + Contactor KM",
            "Autómata LOGO! / Cuadro Mando"
        ])
        
        # Asignación automática de iconos según carga
        iconos_dict = {"Alumbrado": "💡", "Tomas": "🔌", "Cocina": "🍳", "Lavadora": "🧺", "Baños": "🚿", "Motor": "⚙️", "Maniobra": "🤖"}
        icono_sel = next((v for k, v in iconos_dict.items() if k in tipo_carga), "⚡")
        
        btn_add = st.form_submit_button("➕ Insertar Circuito en Barras")
        
        if btn_add:
            # Comprobar duplicados
            if any(c["id"] == id_circuito for c in st.session_state['cuadro_unifilar']):
                st.error(f"La etiqueta {id_circuito} ya existe en el cuadro.")
            else:
                st.session_state['cuadro_unifilar'].append({
                    "id": id_circuito,
                    "tipo": tipo_carga,
                    "polos": polos,
                    "pia": calibre_pia,
                    "seccion": seccion_cable,
                    "icp": poder_corte,
                    "mecanismo": mecanismo_final,
                    "icono": icono_sel
                })
                st.success(f"Circuito {id_circuito} acoplado con éxito.")
                st.rerun()
                # --- COLUMNA DERECHA: VISOR DE ESQUEMA UNIFILAR ESTILO CANECO BT (PARTE 2) ---
with col_der:
    st.header(f"📊 Vista de Caneco BT: {nombre_cuadro}")
    
    # 1. Dibujo de la Acometida de Cabecera General
    st.markdown("### 🔌 Entrada General y Protección de Cabecera")
    
    # Renderizado en texto monoespaciado técnico del bloque general
    esquema_cabecera = f"""
    [ ACOMETIDA GENERAL ]
             │
             ▼
    ┌─────────────────┐
    │  IGA: {iga_cabecera:<10}│  <-- Protección Magnetotérmica General
    │  Icn: 10 kA     │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  DIF: {sens_dif:<10}│  <-- Protección Diferencial Resi9
    └─────────────────┘
             │
    ═════════╧═════════════════════════════════════════════════════════ (Embarrado Cuadro R9)
    """
    st.code(esquema_cabecera, language="text")
    
    # 2. Generación del árbol dinámico de circuitos derivados
    st.markdown("### 🌿 Líneas y Circuitos Derivados")
    
    if not st.session_state['cuadro_unifilar']:
        st.info("El embarrado está vacío. Añade circuitos desde el panel izquierdo.")
    else:
        # Dibujamos las columnas verticales simulando la salida de Caneco
        for c in st.session_state['cuadro_unifilar']:
            with st.expander(f"{c['icono']} Línea {c['id']}: {c['tipo']}", expanded=True):
                col_c1, col_c2 = st.columns([1, 2])
                
                with col_c1:
                    # Representación gráfica normalizada del ramal
                    dibujo_ramal = f"""
         │ (Derivación Embarrado)
         ▼
       ──[ ]──  {c['polos']}
      /       \\
     [  {c['pia']:<4}  ] PIA (Poder corte: {c['icp']})
     [_______]
         │
         │  Manguera: {c['seccion']} Cu
         ▼
     ┌───────┐
     │ {c['icono']}     │ Terminal:
     └───────┘ {c['mecanismo']}
                    """
                    st.code(dibujo_ramal, language="text")
                    
                with col_c2:
                    st.markdown("**Ficha de Datos Técnicos (Caneco BT Check):**")
                    datos_tabla = {
                        "Parámetro Técnico": ["Código Circuito", "Destino de Carga", "Tipo de Polos", "Calibre Magnetotérmico", "Capacidad de Corte", "Sección Conductor", "Elemento Mecanismo Final"],
                        "Valor Asignado": [c['id'], c['tipo'], c['polos'], c['pia'], c['icp'], c['seccion'], c['mecanismo']]
                    }
                    st.table(pd.DataFrame(datos_tabla))
                    
                    # Botón individual para eliminar circuitos del cuadro
                    if st.button(f"🗑️ Eliminar Salida {c['id']}", key=f"del_{c['id']}"):
                        st.session_state['cuadro_unifilar'] = [circ for circ in st.session_state['cuadro_unifilar'] if circ['id'] != c['id']]
                        st.success(f"Circuito {c['id']} desconectado del embarrado.")
                        st.rerun()

    # --- TABLA RESUMEN DE COMPILACIÓN GENERAL ---
    st.write("---")
    st.subheader("📋 Resumen de Cargas de la Instalación")
    
    if st.session_state['cuadro_unifilar']:
        df_resumen = pd.DataFrame(st.session_state['cuadro_unifilar'])
        df_resumen.columns = ["ID Línea", "Uso / Destino", "Polos", "Protección PIA", "Sección Manguera", "Poder Corte Icn", "Mecanismo Conectado", "Icono"]
        st.dataframe(df_resumen[["ID Línea", "Uso / Destino", "Polos", "Protección PIA", "Sección Manguera", "Poder Corte Icn", "Mecanismo Conectado"]], use_container_width=True, hide_index=True)
        
        # Opción para reiniciar el cuadro completo
        if st.button("🗑️ Vaciar Configuración Completa del Cuadro"):
            st.session_state['cuadro_unifilar'] = []
            st.rerun()
