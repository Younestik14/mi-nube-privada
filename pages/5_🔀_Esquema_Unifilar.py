import io
import ezdxf
import streamlit as st
import pandas as pd
import streamlit as st
# 1. Importas tus funciones de estilo desde la carpeta utils
from utils.style import aplicar_estilo_global, generar_banner

# 3. Aplicas el diseño y generas el banner superior
aplicar_estilo_global()
generar_banner("⚡ Módulo Técnico", "Subtítulo explicativo del cálculo actual.")

# 4. Metes tus componentes dentro de la tarjeta estilizada usando HTML simple
st.markdown('<div class="premium-card"><h4>📋 Parámetros de Diseño</h4>', unsafe_allow_html=True)

# ... AQUÍ VA TODO TU CÓDIGO NORMAL (st.text_input, st.selectbox, st.button, etc.) ...

st.markdown('</div>', unsafe_allow_html=True) # <-- Cierras la tarjeta al final

st.set_page_config(page_title="Diseño Unifilar Caneco Style", page_icon="⚡", layout="wide")

st.title("⚡ Módulo 3: Configuración y Cálculo de Esquema Unifilar")
st.markdown("Generación de esquemas unifilares con simbología normalizada y árbol de distribución inspirado en Caneco BT.")

# --- INICIALIZACIÓN DE LA TOPOLOGÍA DEL CUADRO ---
if 'cuadro_unifilar' not in st.session_state:
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
        
        iconos_dict = {"Alumbrado": "💡", "Tomas": "🔌", "Cocina": "🍳", "Lavadora": "🧺", "Baños": "🚿", "Motor": "⚙️", "Maniobra": "🤖"}
        icono_sel = next((v for k, v in iconos_dict.items() if k in tipo_carga), "⚡")
        
        btn_add = st.form_submit_button("➕ Insertar Circuito en Barras")
        
        if btn_add:
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

# --- COLUMNA DERECHA: VISOR ESTILO CANECO BT Y EXPORTACIÓN DXF CORREGIDA ---
with col_der:
    st.header(f"📊 Vista de Caneco BT: {nombre_cuadro}")
    
    st.markdown("### 🔌 Entrada General y Protección de Cabecera")
    
    esquema_cabecera = f"""
    [ ACOMETIDA GENERAL ]
             │
             ▼
    ┌─────────────────┐
    │  IGA: {iga_cabecera:<10}│  <-- Protección Magnetotérmica (Fase/Neutro)
    │  Icn: 10 kA     │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  DIF: {sens_dif:<10}│  <-- Interruptor Diferencial (Protección Personas)
    └─────────────────┘
             │
    ═════════╧═════════════════════════════════════════════════════════ (Embarrado de Cobre Cu)
    """
    st.code(esquema_cabecera, language="text")
    
    st.markdown("### 🌿 Líneas y Circuitos Derivados (Simbología Unifilar REBT)")
    
    if not st.session_state['cuadro_unifilar']:
        st.info("El embarrado está vacío. Añade circuitos desde el panel izquierdo.")
    else:
        for c in st.session_state['cuadro_unifilar']:
            with st.expander(f"{c['icono']} Línea {c['id']}: {c['tipo']}", expanded=True):
                col_c1, col_c2 = st.columns([1, 2])
                
                with col_c1:
                    dibujo_ramal = f"""
         │ (Derivación de Barra)
         ▼
       ──[ ]──  {c['polos']} (Símbolo Unifilar Mecanismo)
      /       \\
     [  {c['pia']:<4}  ] PIA Magn. (Icn: {c['icp']})
     [_______]
         │
         │  Manguera LH: {c['seccion']}
         ▼
     ┌───────┐
     │ {c['icono']}     │ Receptor Final:
     └───────┘ {c['mecanismo']}
                    """
                    st.code(dibujo_ramal, language="text")
                    
                with col_c2:
                    st.markdown("**Parámetros de Cálculo de Línea:**")
                    datos_tabla = {
                        "Especificación Técnica (Norma)": ["Identificador", "Uso previsto", "Número de Polos", "Calibre PIA", "Poder de Corte", "Sección Conductor", "Mecanismo Terminal"],
                        "Valor Caneco Check": [c['id'], c['tipo'], c['polos'], c['pia'], c['icp'], c['seccion'], c['mecanismo']]
                    }
                    st.table(pd.DataFrame(datos_tabla))
                    
                    if st.button(f"🗑️ Desconectar Salida {c['id']}", key=f"del_{c['id']}"):
                        st.session_state['cuadro_unifilar'] = [circ for circ in st.session_state['cuadro_unifilar'] if circ['id'] != c['id']]
                        st.success(f"Circuito {c['id']} retirado.")
                        st.rerun()

    st.write("---")
    st.subheader("💾 Exportación a Oficina Técnica (Formato CAD)")
    
    if st.session_state['cuadro_unifilar']:
        def generar_dxf_unifilar():
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Dibujar Cabecera General con posicionamiento mediante diccionario de atributos ('insert')
            msp.add_text("ESQUEMA UNIFILAR - CANECO GENERATOR", dxfattribs={'height': 3.5, 'insert': (0, 80)})
            msp.add_text(f"CUADRO: {nombre_cuadro}", dxfattribs={'height': 2.5, 'insert': (0, 72)})
            
            msp.add_line((10, 65), (10, 55))
            msp.add_lwpolyline([(5, 55), (15, 55), (15, 45), (5, 45), (5, 55)])
            msp.add_text(f"IGA {iga_cabecera}", dxfattribs={'height': 1.8, 'insert': (17, 50)})
            
            msp.add_line((10, 45), (10, 35))
            msp.add_line((0, 35), (len(st.session_state['cuadro_unifilar']) * 30, 35))
            
            x_offset = 15
            for c in st.session_state['cuadro_unifilar']:
                msp.add_line((x_offset, 35), (x_offset, 28))
                
                # Símbolo unifilar normalizado de corte
                msp.add_circle((x_offset, 25), radius=2)
                msp.add_line((x_offset - 4, 23), (x_offset + 4, 23))
                
                msp.add_text(f"Línea {c['id']}", dxfattribs={'height': 1.8, 'color': 1, 'insert': (x_offset + 3, 28)})
                msp.add_text(f"PIA {c['pia']} / {c['polos']}", dxfattribs={'height': 1.5, 'insert': (x_offset + 3, 25)})
                msp.add_text(f"Icn {c['icp']}", dxfattribs={'height': 1.2, 'insert': (x_offset + 3, 22)})
                
                msp.add_line((x_offset, 21), (x_offset, 12))
                msp.add_text(f"Cu {c['seccion']}", dxfattribs={'height': 1.5, 'insert': (x_offset + 2, 16)})
                
                # Carga terminal / Salida final
                msp.add_lwpolyline([
                    (x_offset - 5, 12), (x_offset + 5, 12), 
                    (x_offset + 5, 4), (x_offset - 5, 4), (x_offset - 5, 12)
                ])
                
                nombre_corto = c['tipo'][:15]
                msp.add_text(nombre_corto, dxfattribs={'height': 1.2, 'insert': (x_offset - 4, 7)})
                msp.add_text(c['mecanismo'][:18], dxfattribs={'height': 1.0, 'color': 3, 'insert': (x_offset - 5, 1)})
                
                x_offset += 30
                
            out_stream = io.StringIO()
            doc.write(out_stream)
            return out_stream.getvalue().encode('utf-8')
        
        try:
            dxf_data = generar_dxf_unifilar()
            st.success("¡Plano CAD generado de forma limpia con simbología normalizada!")
            st.download_button(
                label="📥 Descargar Esquema Unifilar en formato (.DXF)",
                data=dxf_data,
                file_name=f"unifilar_{nombre_cuadro.lower().replace(' ', '_')}.dxf",
                mime="image/vnd.dxf"
            )
            st.caption("💡 Puedes abrir directamente este archivo `.dxf` descargado en AutoCAD, ZWCAD o Caneco.")
        except Exception as e:
            st.error(f"No se pudo compilar el bloque CAD: {e}")
            
        if st.button("🗑️ Vaciar Configuración Completa del Cuadro"):
            st.session_state['cuadro_unifilar'] = []
            st.rerun()
