# 🏠_Inicio.py
import streamlit as st
from auth import verificar_acceso # Importa la lista de aprobados

st.set_page_config(page_title="Mi Nube Privada", layout="wide")

if 'autorizado' not in st.session_state:
    st.session_state.autorizado = False

if not st.session_state.autorizado:
    st.title("🔐 Acceso a la Oficina Técnica")
    id_input = st.text_input("Introduce tu Número Regional para entrar:", type="password")
    
    if st.button("Acceder"):
        if verificar_acceso(id_input):
            st.session_state.autorizado = True
            st.rerun() 
        else:
            st.error("Acceso denegado. Si ya solicitaste acceso, espera a que el admin te acepte.")
    
    st.stop() # Bloquea el resto de la página

# Si llega aquí, es porque está autorizado
st.success("Acceso concedido.")
