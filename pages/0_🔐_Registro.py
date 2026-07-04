import sys
import os
import streamlit as st
# (No necesitas importar init_db ni registrar_usuario de auth.py si usas la lista blanca)

st.title("🔐 Registro de Acceso")
st.write("Si necesitas acceso, contacta con el administrador.")
# Esto le dice a Python: "busca en la carpeta superior donde están los demás archivos"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import init_db, registrar_usuario
