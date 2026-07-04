import streamlit as st
import os

st.sidebar.title("🔐 Acceso Admin")
if st.sidebar.text_input("Contraseña:", type="password") == "1868628":
    st.title("🛠️ Solicitudes Pendientes")
    
    if os.path.exists("solicitudes.txt"):
        with open("solicitudes.txt", "r") as f:
            solicitudes = f.readlines()
            
        for linea in solicitudes:
            datos = linea.strip().split(",")
            if len(datos) == 2:
                nombre, id_estudiante = datos
                st.write(f"👤 **{nombre}** - ID: `{id_estudiante}`")
    else:
        st.info("No hay solicitudes nuevas.")
        
    st.warning("⚠️ Nota: Para aprobar, añade el ID manualmente al archivo `auth.py`")
else:
    st.warning("Solo para administrador.")
