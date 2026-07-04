import streamlit as st
from auth import init_db, registrar_usuario
from utils.style import aplicar_estilo_global

st.set_page_config(page_title="Acceso Oficina Técnica", layout="centered")
aplicar_estilo_global()
init_db()

st.title("🔐 Acceso a la Oficina Técnica")

with st.form("registro_form"):
    nombre = st.text_input("Nombre Completo:")
    num_reg = st.text_input("Número Regional de Estudiante:")
    submit = st.form_submit_button("Solicitar Acceso")

    if submit:
        if nombre and num_reg:
            if registrar_usuario(nombre, num_reg):
                st.success("Solicitud enviada correctamente. Esperando validación.")
            else:
                st.error("Este número de estudiante ya tiene una solicitud.")
        else:
            st.warning("Por favor, rellena todos los campos.")
