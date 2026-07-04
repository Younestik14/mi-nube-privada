# seguridad.py
import streamlit as st

def verificar_sesion():
    if not st.session_state.get('autorizado', False):
        st.error("Debes iniciar sesión primero.")
        st.stop()
