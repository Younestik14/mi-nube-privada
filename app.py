import streamlit as st
from graphviz import Digraph

# ==========================================
# CONFIGURACIÓN DEL ENTORNO Y ARQUITECTURA
# ==========================================
st.set_page_config(
    page_title="GRAFCET to KOP Compiler - CIFP Politécnico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos profesionales para simular un software de ingeniería (Siemens TIA Portal / EcoStruxure)
st.markdown("""
<style>
    body { color: #E0E0E0; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: #AEAEAE;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #61AFEF; }
    .stTabs [aria-selected="true"] { background-color: #282C34 !important; color: #61AFEF !important; border-bottom: 2px solid #61AFEF !important; }
    div.stCodeBlock { border-left: 4px solid #98C379 !important; }
    .kop-network {
        background-color: #FFFFFF;
        color: #000000;
        padding: 20px;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        border-left: 5px solid #005A9C;
        margin-bottom: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ESTRUCTURAS DE DATOS COHERENTES (MODELO)
# ==========================================
class Etapa:
    def __init__(self, numero, es_inicial=False):
        self.numero = int(numero)
        self.es_inicial = es_inicial
        self.acciones = []  # Lista de strings (ej. "KM1", "Y1")

class Transition:
    def __init__(self, desde_etapa, hacia_etapa, receptividad):
        self.desde = int(desde_etapa)
        self.hacia = int(hacia_etapa)
        self.receptividad = str(receptividad)  # Condición booleana (ej. "S1 * FC1")

# Inicialización del estado de la aplicación
if 'etapas' not in st.session_state:
    # GRAFCET inicial por defecto: Secuencia lineal E0 -> E1 -> E0
    st.session_state.etapas = {
        0: Etapa(0, es_inicial=True),
        1: Etapa(1, es_inicial=False)
     Packs = [("KM1", 0)] 
    st.session_state.etapas[0].acciones = ["H0"]
    st.session_state.etapas[1].acciones = ["KM1", "Y1"]

if 'transiciones' not in st.session_state:
    st.session_state.transiciones = [
        Transition(0, 1, "S1"),
        Transition(1, 0, "FC1")
    ]

# ==========================================
# BANNER INSTITUCIONAL
# ==========================================
st.title("🎛️ IDE Industrial: Compilador GRAFCET a Esquemas de Contactos (KOP)")
st.caption("Módulo de Configuración de Sistemas Automatizados | Sistemas Electrotécnicos y Automatizados (SEA) | CIFP Politécnico de Cartagena")
st.divider()

# ==========================================
# PANEL LATERAL: EDITOR DE GRAFCET
# ==========================================
with st.sidebar:
    st.header("🛠️ Configuración de la Secuencia")
    
    # --- SECCIÓN ETAPAS ---
    with st.expander("📝 Gestión de Etapas", expanded=True):
        num_etapa = st.number_input("Número de Etapa", min_value=0, max_value=99, step=1)
        init_etapa = st.checkbox("¿Es etapa inicial? (X0)", value=False)
        acciones_input = st.text_input("Acciones asociadas (separadas por comas)", placeholder="KM1, Y1")
        
        if st.button("💾 Registrar/Modificar Etapa", use_container_width=True):
            nueva_etapa = Etapa(num_etapa, es_inicial=init_etapa)
            if acciones_input:
                nueva_etapa.acciones = [a.strip() for a in acciones_input.split(",")]
            
            # Si se marca como inicial, quitar el flag a las demás (solo puede haber una inicial en esta arquitectura)
            if init_etapa:
                for e in st.session_state.etapas.values():
                    e.es_inicial = False
                    
            st.session_state.etapas[num_etapa] = nueva_etapa
            st.rerun()

    # --- SECCIÓN TRANSICIONES ---
    with st.expander("🔀 Gestión de Transiciones (Flujo)", expanded=True):
        etapa_origen = st.selectbox("Desde Etapa (X_i)", options=sorted(list(st.session_state.etapas.keys())))
        etapa_destino = st.selectbox("Hacia Etapa (X_j)", options=sorted(list(st.session_state.etapas.keys())))
        receptividad = st.text_input("Condición de Transición (Receptividad)", placeholder="S1 * /FC1")
        
        if st.button("➕ Añadir Transición", use_container_width=True):
            nueva_transicion = Transition(etapa_origen, etapa_destino, receptividad if receptividad else "1")
            st.session_state.transiciones.append(nueva_transicion)
            st.rerun()

    st.divider()
    if st.button("🗑️ Reiniciar Proyecto", type="primary", use_container_width=True):
        st.session_state.etapas = {0: Etapa(0, es_inicial=True)}
        st.session_state.transiciones = []
        st.rerun()

# ==========================================
# ÁREA DE TRABAJO PRINCIPAL (VISTAS)
# ==========================================
tab_grafcet, tab_ecuaciones, tab_kop = st.tabs([
    "📊 Vista 1: Diagrama GRAFCET", 
    "🧮 Vista 2: Ecuaciones Booleanas de Estado", 
    "🧱 Vista 3: Esquema de Contactos (KOP / Ladder)"
])

# ------------------------------------------
# TAB 1: DIAGRAMA GRAFCET (GRAFVIZ)
# ------------------------------------------
with tab_grafcet:
    st.subheader("Representación Estructurada del GRAFCET")
    
    dot = Digraph(comment='GRAFCET Plant')
    dot.attr(rankdir='TB', size='10,8', bgcolor='transparent')
    
    # Dibujar nodos de etapa
    for id_e, etapa in st.session_state.etapas.items():
        shape = "doublebox" if etapa.es_inicial else "box"
        label = f"X{etapa.numero}\n-------"
        if etapa.acciones:
            label += "\n" + "\n".join([f"| {a} |" for a in etapa.acciones])
        
        dot.node(f"E{etapa.numero}", label, shape=shape, color="#61AFEF", fontcolor="#E0E0E0", style="bold")

    # Dibujar transiciones intermedias
    for idx, trans in enumerate(st.session_state.transiciones):
        trans_id = f"T{idx}"
        # Nodo de la barra de transición
        dot.node(trans_id, label="", shape="hline", width="0.6", color="#E5C07B", style="bold")
        # Etiqueta de la receptividad al lado de la barra
        dot.edge(f"E{trans.desde}", trans_id, label=f"  {trans.receptividad}", fontcolor="#E5C07B", color="#E0E0E0")
        dot.edge(trans_id, f"E{trans.hacia}", color="#E0E0E0")

    st.graphviz_chart(dot)

# ------------------------------------------
# TAB 2: ECUACIONES BOOLEANAS DE ESTADO
# ------------------------------------------
with tab_ecuaciones:
    st.subheader("Análisis Matemático del Automatismo Secuencial")
    st.write("Ecuaciones de **Activación ($Set$)**, **Desactivación ($Reset$)** y **Salidas** deducidas del modelo:")
    
    for id_e, etapa in sorted(st.session_state.etapas.items()):
        st.markdown(f"### 🟩 Etapa $X_{etapa.numero}$")
        
        # Buscar transiciones entrantes (Activación)
        entrantes = [t for t in st.session_state.transiciones if t.hacia == etapa.numero]
        if entrantes:
            eq_set = " + ".join([f"(X_{t.desde} \cdot {t.receptividad})" for t in entrantes])
        else:
            eq_set = "0 \text{ (Sin transiciones entrantes)}"
            
        # Buscar transiciones salientes (Desactivación)
        salientes = [t for t in st.session_state.transiciones if t.desde == etapa.numero]
        if salientes:
            eq_reset = " + ".join([f"X_{t.hacia}" for t in salientes])
        else:
            eq_reset = "0 \text{ (Fin de secuencia)}"
            
        # Mostrar fórmulas formateadas en LaTeX
        st.latex(f"Set(X_{{{etapa.numero}}}) = {eq_set}")
        st.latex(f"Reset(X_{{{etapa.numero}}}) = {eq_reset}")
        st.markdown("---")
        
    # Ecuaciones lógicas de las salidas físicas
    st.subheader("⚙️ Ecuaciones Booleanas de las Salidas Físicas")
    mapa_salidas = {}
    for etapa in st.session_state.etapas.values():
        for accion in etapa.acciones:
            if accion not in mapa_salidas:
                mapa_salidas[accion] = []
            mapa_salidas[accion].append(f"X_{etapa.numero}")
            
    for salida, condiciones in mapa_salidas.items():
        st.latex(f"{salida} = " + " + ".join(condiciones))

# ------------------------------------------
# TAB 3: TRADUCCIÓN AUTOMÁTICA A KOP (LADDER)
# ------------------------------------------
with tab_kop:
    st.subheader("Código de Contactos Generado (Norma IEC 61131-3)")
    st.write("A continuación se presentan las redes o *networks* de contactos necesarias para programar un autómata programable (PLC):")
    
    # 1. Generación de las redes de las Etapas (Set/Reset)
    for id_e, etapa in sorted(st.session_state.etapas.items()):
        st.markdown(f"#### Network {etapa.numero + 1}: Evolución de la Etapa X{etapa.numero}")
        
        entrantes = [t for t in st.session_state.transiciones if t.hacia == etapa.numero]
        salientes = [t for t in st.session_state.transiciones if t.desde == etapa.numero]
        
        # Formatear la rama superior de activación (Set)
        set_lines = ""
        for t in entrantes:
            set_lines += f"     |---[ X{t.desde} ]---[ {t.receptividad} ]---|\n"
            
        # Si es etapa inicial, añadir la condición del primer ciclo de scan (First Scan)
        if etapa.es_inicial:
            set_lines += "     |---[ First_Scan ]-----------|\n"
            
        reset_str = " * ".join([f"/X{t.hacia}" for t in salientes])
        reset_contacts = "".join([f"---[ /X{t.hacia} ]" for t in salientes])
        
        # Renderizado en formato ASCII profesional de ingeniería
        st.markdown(f"""
```text
  L1                                                                        L2
  |                                                                          |
  |--+-----------------------------+--{reset_contacts}----------------( S )--|
  {set_lines}     |---[ X{etapa.numero} ]-----------| (Autoenclavamiento)
  |
