import streamlit as st
from auth import init_db, registrar_usuario

init_db()

st.title("🔐 Registro de Acceso")
with st.form("registro"):
    nombre = st.text_input("Nombre completo:")
    num = st.text_input("Número regional:")
    if st.form_submit_button("Enviar"):
        if registrar_usuario(nombre, num):
            st.success("¡Enviado! Espera a que el administrador te apruebe.")
        else:
            st.error("Error: ese número ya existe.")
