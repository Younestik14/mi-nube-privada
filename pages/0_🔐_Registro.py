import streamlit as st

st.title("🔐 Registro de Solicitud")
st.write("Si no tienes acceso, envía tu número regional al administrador:")

# Formulario para que te envíen su solicitud (esto te llegará al correo o por mensaje)
with st.form("solicitud"):
    nombre = st.text_input("Tu nombre completo:")
    id_solicitado = st.text_input("Tu número regional:")
    enviar = st.form_submit_button("Enviar solicitud al Admin")

    if enviar:
        st.info(f"Solicitud recibida para {nombre}. El administrador te notificará cuando seas añadido a la lista blanca.")
