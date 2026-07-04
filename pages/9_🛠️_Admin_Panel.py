import streamlit as st
import os

st.sidebar.title("🔐 Acceso Admin")
if st.sidebar.text_input("Contraseña:", type="password") == "1868628":
    st.title("🛠️ Gestión de Solicitudes")

    if os.path.exists("solicitudes.txt"):
        with open("solicitudes.txt", "r") as f:
            lineas = f.readlines()
        
        # Guardamos las solicitudes en una lista para procesarlas
        solicitudes = [l.strip().split(",") for l in lineas if "," in l]

        if not solicitudes:
            st.info("No hay solicitudes pendientes.")
        
        for i, (nombre, id_estudiante) in enumerate(solicitudes):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"👤 **{nombre}** (ID: `{id_estudiante}`)")
            
            # BOTÓN ACEPTAR
            if col2.button("✅ Aceptar", key=f"acc_{i}"):
                st.success(f"Añade este ID a tu archivo auth.py: {id_estudiante}")
                # Aquí podrías automatizar más, pero por seguridad, 
                # mantén el control manual de la lista blanca.
                
            # BOTÓN RECHAZAR
            if col3.button("❌ Rechazar", key=f"rej_{i}"):
                # Quitamos la línea del archivo
                del solicitudes[i]
                with open("solicitudes.txt", "w") as f:
                    for s in solicitudes:
                        f.write(f"{s[0]},{s[1]}\n")
                st.rerun()
    else:
        st.info("No hay archivo de solicitudes.")
else:
    st.warning("Introduce la contraseña para ver las solicitudes.")
