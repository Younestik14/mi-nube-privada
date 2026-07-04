import streamlit as st

st.title("🔐 Registro de Solicitud")

with st.form("solicitud"):
    nombre = st.text_input("Tu nombre completo:")
    id_solicitado = st.text_input("Tu número regional:")
    enviar = st.form_submit_button("Enviar solicitud")

    if enviar:
        # Abrimos el archivo en modo 'append' (añadir)
        with open("solicitudes.txt", "a") as f:
            f.write(f"{nombre},{id_solicitado}\n")
        st.success("Solicitud enviada al administrador.")
