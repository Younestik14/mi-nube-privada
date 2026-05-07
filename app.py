import streamlit as st
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SEA-NUBE", page_icon="📁")
PASSWORD_CORRECTA = "Laaljorra_2002"
BASE_FOLDER = "uploads"

if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)

# --- SEGURIDAD ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acceso Privado")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pwd == PASSWORD_CORRECTA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# --- GESTIÓN DE NAVEGACIÓN ---
if "ruta_actual" not in st.session_state:
    st.session_state["ruta_actual"] = BASE_FOLDER

def ir_a_carpeta(nombre):
    st.session_state["ruta_actual"] = os.path.join(st.session_state["ruta_actual"], nombre)

def volver_atras():
    if st.session_state["ruta_actual"] != BASE_FOLDER:
        st.session_state["ruta_actual"] = os.path.dirname(st.session_state["ruta_actual"])

# --- INTERFAZ PRINCIPAL ---
st.title("📁 Gestor de Archivos")
st.write(f"📍 Estás en: `{st.session_state['ruta_actual']}`")

# Navegación rápida
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("⬅️ Volver al inicio"):
        st.session_state["ruta_actual"] = BASE_FOLDER
        st.rerun()
with col_nav2:
    if st.button("⬆️ Subir un nivel"):
        volver_atras()
        st.rerun()

st.divider()

# --- SECCIÓN: CREAR CARPETA Y SUBIDA MÚLTIPLE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🆕 Nueva Carpeta")
    nueva_carpeta = st.text_input("Nombre de la carpeta")
    if st.button("Crear Carpeta"):
        if nueva_carpeta:
            nueva_ruta = os.path.join(st.session_state["ruta_actual"], nueva_carpeta)
            if not os.path.exists(nueva_ruta):
                os.makedirs(nueva_ruta)
                st.success(f"Carpeta '{nueva_carpeta}' creada")
                st.rerun()
            else:
                st.warning("La carpeta ya existe")

with col2:
    st.subheader("📤 Subida Múltiple")
    # El truco está en: accept_multiple_files=True
    archivos_subidos = st.file_uploader(
        "Arrastra varios archivos aquí", 
        accept_multiple_files=True, 
        label_visibility="collapsed"
    )
    
    if archivos_subidos:
        if st.button(f"Guardar {len(archivos_subidos)} archivos"):
            for archivo in archivos_subidos:
                with open(os.path.join(st.session_state["ruta_actual"], archivo.name), "wb") as f:
                    f.write(archivo.getbuffer())
            st.success(f"✅ Se han guardado {len(archivos_subidos)} archivos.")
            st.rerun()

st.divider()

# --- SECCIÓN: LISTADO DE CONTENIDO ---
st.subheader("Contenido de la carpeta")
try:
    contenido = os.listdir(st.session_state["ruta_actual"])
except FileNotFoundError:
    st.session_state["ruta_actual"] = BASE_FOLDER
    st.rerun()

if not contenido:
    st.info("Esta carpeta está vacía")
else:
    for item in contenido:
        ruta_item = os.path.join(st.session_state["ruta_actual"], item)
        es_carpeta = os.path.isdir(ruta_item)
        
        c1, c2 = st.columns([3, 1])
        
        if es_carpeta:
            with c1:
                st.write(f"📁 **{item}**")
            with c2:
                if st.button("Abrir", key=f"btn_{item}"):
                    ir_a_carpeta(item)
                    st.rerun()
        else:
            with c1:
                st.write(f"📄 {item}")
            with c2:
                with open(ruta_item, "rb") as f:
                    st.download_button("Descargar", f, file_name=item, key=f"dl_{item}")

# --- BARRA LATERAL ---
st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
