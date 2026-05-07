import streamlit as st
from supabase import create_client
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="SEA Mi Nube",
    page_icon="☁️",
    layout="centered"
)

# --- 2. CREDENCIALES DE SUPABASE ---
# Sustituye con tus datos reales de Settings > API en Supabase
SUPABASE_URL = "https://pviqrttodnjewgrvthxn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB2aXFydHRvZG5qZXdncnZ0aHhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxNDEyODIsImV4cCI6MjA5MzcxNzI4Mn0.bjeTAAxhOtKLYMUfhGk3COfcEaXSKkkzEvaLD-Qj3-w"

# Inicializamos el cliente de Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("Error al conectar con Supabase. Revisa tus credenciales.")

# --- 3. SISTEMA DE SEGURIDAD ---
PASSWORD_SITIO = "Laaljorra_2002"  # <--- Cambia tu contraseña aquí

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def login():
    st.title("🔐 Acceso Privado")
    pwd = st.text_input("Introduce la contraseña para entrar:", type="password")
    if st.button("Acceder"):
        if pwd == PASSWORD_SITIO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

# Si no está autenticado, detiene la ejecución aquí
if not st.session_state["autenticado"]:
    login()
    st.stop()

# --- 4. INTERFAZ PRINCIPAL (Solo visible si estás logueado) ---
st.title("☁️ Mi Almacenamiento Permanente")
st.markdown("Los archivos se guardan en la nube de Supabase de forma segura.")

# Botón para cerrar sesión en el lateral
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

st.divider()

# --- 5. SECCIÓN DE SUBIDA (MULTIPLE) ---
st.subheader("📤 Subir Archivos")
archivos_nuevos = st.file_uploader(
    "Puedes arrastrar varios archivos a la vez", 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if archivos_nuevos:
    if st.button(f"Guardar {len(archivos_nuevos)} archivos en la nube"):
        for arc in archivos_nuevos:
            try:
                # Subir archivo al bucket 'archivos'
                content = arc.getvalue()
                supabase.storage.from_("archivos").upload(
                    path=arc.name, 
                    file=content,
                    file_options={"cache-control": "3600", "upsert": "true"} # upsert: true permite sobrescribir
                )
                st.success(f"✅ {arc.name} guardado.")
            except Exception as e:
                st.error(f"Error con {arc.name}: {e}")
        st.rerun()

st.divider()

# --- 6. SECCIÓN DE LISTADO Y GESTIÓN ---
st.subheader("📁 Mis Archivos Guardados")

try:
    # Listar archivos del bucket 'archivos'
    respuesta = supabase.storage.from_("archivos").list()
    
    if not respuesta or len(respuesta) == 0:
        st.info("Aún no hay archivos en tu nube.")
    else:
        for item in respuesta:
            nombre = item['name']
            
            # Saltamos el archivo por defecto de Supabase
            if nombre == ".emptyFolderPlaceholder":
                continue
                
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 {nombre}")
            
            with col2:
                # Generar URL pública para descargar
                url = supabase.storage.from_("archivos").get_public_url(nombre)
                st.link_button("Descargar", url)
            
            with col3:
                # Botón para borrar
                if st.button("🗑️", key=f"del_{nombre}"):
                    supabase.storage.from_("archivos").remove([nombre])
                    st.warning(f"Eliminado: {nombre}")
                    st.rerun()

except Exception as e:
    st.error(f"No se pudo cargar la lista de archivos: {e}")
