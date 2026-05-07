import streamlit as st
import os

# 1. Configuración de la página y Contraseña
st.set_page_config(page_title="SEA 25-26")
PASSWORD = "SEA2526"

# Función para verificar la contraseña
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Introduce la contraseña", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == PASSWORD}), key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.title("SEA 25-26")

    # 2. Subir archivos
    archivo_subido = st.file_uploader("Elige un archivo para guardar")
    if archivo_subido is not None:
        with open(os.path.join("uploads", archivo_subido.name), "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.success(f"Archivo '{archivo_subido.name}' guardado con éxito.")

    st.divider()

    # 3. Listar y descargar archivos
    st.subheader("Tus archivos guardados:")
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        
    for nombre_archivo in os.listdir("uploads"):
        with open(os.path.join("uploads", nombre_archivo), "rb") as f:
            st.download_button(label=f"Descargar {nombre_archivo}", data=f, file_name=nombre_archivo)