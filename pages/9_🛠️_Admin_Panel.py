import streamlit as st

st.sidebar.title("🔐 Acceso Admin")
if st.sidebar.text_input("Contraseña:", type="password") == "1868628":
    st.title("🛠️ Gestión de Estudiantes")
    
    nuevo_estudiante = st.text_input("Añadir ID de estudiante:")
    if st.button("Autorizar"):
        # Esto es solo un ejemplo conceptual
        st.success(f"ID {nuevo_estudiante} añadido a la lista autorizada.")
        st.info("Nota: Para guardar cambios permanentes, copia la lista actualizada al archivo auth.py")
else:
    st.warning("Solo para administrador.")
