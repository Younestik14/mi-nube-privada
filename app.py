import streamlit as st
import networkx as nx
from graphviz import Digraph
import time

# ==========================================
# CONFIGURACIÓN PRO E INTERFAZ
# ==========================================
st.set_page_config(page_title="SEA Designer & Simulator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2129; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MOTOR DE LÓGICA (CLASES TÉCNICAS)
# ==========================================
class Componente:
    def __init__(self, id, nombre, tipo, padre_id=None, estado_inicial=False):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo  # 'Proteccion', 'Mando', 'Bobina', 'Carga'
        self.padre_id = padre_id # ID del componente aguas arriba
        self.estado = estado_inicial
        self.con_tension = False

def resolver_tension(componentes):
    """
    Algoritmo de propagación de tensión: 
    La tensión fluye si el padre tiene tensión Y el componente actual está 'cerrado'.
    """
    # Ordenar por jerarquía (simplificado: asumiendo que los IDs bajos son aguas arriba)
    ids_ordenados = sorted(componentes.keys())
    
    for c_id in ids_ordenados:
        comp = componentes[c_id]
        if comp.padre_id is None:
            # Es un elemento de entrada (p. ej. el Diferencial principal)
            comp.con_tension = comp.estado
        else:
            padre = componentes.get(comp.padre_id)
            if padre and padre.con_tension and comp.estado:
                comp.con_tension = True
            else:
                comp.con_tension = False

# ==========================================
# GESTIÓN DE ESTADO (MEMORIA DE DISEÑO)
# ==========================================
if 'maquina' not in st.session_state:
    # Maquina inicial por defecto
    st.session_state.maquina = {
        0: Componente(0, "IGM (Magnetotérmico)", "Proteccion", None, True),
        1: Componente(1, "S0 (Paro Emergencia)", "Mando", 0, True),
    }
    st.session_state.next_id = 2

# ==========================================
# SIDEBAR: EDITOR DE DISEÑO
# ==========================================
with st.sidebar:
    st.header("🛠️ Diseñador de Máquina")
    st.subheader("Añadir nuevo elemento")
    
    nuevo_nombre = st.text_input("Nombre del elemento (ej. KM1, S1, H1)")
    nuevo_tipo = st.selectbox("Tipo de contacto", ["NC (Normalmente Cerrado)", "NA (Normalmente Abierto)", "Bobina/Carga"])
    
    # Elegir a qué componente se conecta (Jerarquía eléctrica)
    opciones_padre = {id: comp.nombre for id, comp in st.session_state.maquina.items()}
    padre_seleccionado = st.selectbox("Conectar a (Aguas arriba):", options=list(opciones_padre.keys()), 
                                      format_func=lambda x: opciones_padre[x])
    
    if st.button("➕ Insertar en el esquema"):
        # Lógica de estado inicial: NC empieza en True, NA en False
        estado_init = True if "NC" in nuevo_tipo else False
        tipo_final = "Mando" if "N" in nuevo_tipo else "Carga"
        
        nuevo_comp = Componente(st.session_state.next_id, nuevo_nombre, tipo_final, padre_seleccionado, estado_init)
        st.session_state.maquina[st.session_state.next_id] = nuevo_comp
        st.session_state.next_id += 1
        st.success(f"Elemento {nuevo_nombre} añadido.")

    st.divider()
    if st.button("🗑️ Resetear diseño"):
        st.session_state.maquina = {0: Componente(0, "IGM", "Proteccion", None, True)}
        st.session_state.next_id = 1
        st.rerun()

# ==========================================
# CUERPO PRINCIPAL: SIMULACIÓN Y GRÁFICO
# ==========================================
st.title("🏭 Machine Design & Logic Simulator")

col_control, col_graph = st.columns([1, 1])

with col_control:
    st.subheader("🎮 Panel de Operador")
    st.write("Interactúa con los mandos de tu diseño:")
    
    # Resolver la lógica antes de mostrar
    resolver_tension(st.session_state.maquina)
    
    # Crear interruptores para los elementos que son mandos o protecciones
    for c_id, comp in st.session_state.maquina.items():
        if comp.tipo != "Carga":
            # Usamos un checkbox para simular la pulsación o el estado del contacto
            # Si es NC, el valor por defecto es True
            comp.estado = st.toggle(f"Activar {comp.nombre}", value=comp.estado, key=f"control_{c_id}")

with col_graph:
    st.subheader("📑 Esquema Unifilar Dinámico")
    
    # Generar gráfico con Graphviz
    dot = Digraph(comment='Esquema Eléctrico')
    dot.attr(rankdir='TB', size='8,5')
    dot.attr('node', shape='rectangle', style='filled', fontname='Arial')

    for c_id, comp in st.session_state.maquina.items():
        color = "#2ecc71" if comp.con_tension else "#e74c3c"
        font_color = "black" if comp.con_tension else "white"
        
        label = f"{comp.nombre}\n[{'ON' if comp.con_tension else 'OFF'}]"
        dot.node(str(c_id), label, fillcolor=color, color="black", fontcolor=font_color)
        
        if comp.padre_id is not None:
            dot.edge(str(comp.padre_id), str(c_id))

    st.graphviz_chart(dot)

st.divider()

# ==========================================
# MONITORES DE SALIDA (PILOTOS Y MOTORES)
# ==========================================
st.subheader("🚀 Salidas de Máquina (Actuadores)")
cols_salida = st.columns(max(len([c for c in st.session_state.maquina.values() if c.tipo == "Carga"]), 1))

idx_c = 0
for comp in st.session_state.maquina.values():
    if comp.tipo == "Carga":
        with cols_salida[idx_c]:
            if comp.con_tension:
                st.metric(comp.nombre, "EN SERVICIO", delta="⚡ Tensión OK")
                if "Motor" in comp.nombre or "KM" in comp.nombre:
                    st.write("🔄 Girando...")
                else:
                    st.write("💡 Iluminando...")
            else:
                st.metric(comp.nombre, "PARADO", delta="0V", delta_color="inverse")
            idx_c += 1

# ==========================================
# EXPLICACIÓN TÉCNICA PARA EL PROFESOR
# ==========================================
with st.expander("📝 Análisis técnico del sistema"):
    st.write("""
        **Lógica de Simulación:**
        Este sistema utiliza un algoritmo de **Recorrido de Árbol**. Cada componente hereda el estado eléctrico de su 'padre' aguas arriba. 
        Si un componente aguas arriba (ej. un Pulsador de Paro) se abre, la propiedad `con_tension` se vuelve `False` para toda la rama descendente de forma recursiva.
        
        **Capacidades:**
        - Diseño jerárquico dinámico.
        - Renderizado en tiempo real mediante Graphviz (DOT language).
        - Cálculo de caída de tensión lógica (booleana).
    """)
