import sqlite3
import streamlit as st
from auth import init_db

# Configuración del panel lateral de seguridad
st.set_page_config(page_title="Panel Admin", layout="wide")

st.sidebar.title("🔐 Acceso Admin")
password = st.sidebar.text_input("Contraseña de Administrador:", type="password")

# Solo se muestra el contenido si la contraseña es correcta
if password == "1868628":
    st.title("🛠️ Panel de Aprobación de Estudiantes")
    
    def aprobar_usuario(num_estudiante):
        conn = sqlite3.connect('usuarios.db')
        c = conn.cursor()
        c.execute("UPDATE usuarios SET estado = 'aprobado' WHERE num_estudiante = ?", (num_estudiante,))
        conn.commit()
        conn.close()

    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios")
    registros = c.fetchall()
    conn.close()

# ... (código anterior)
    if not registros:
        st.info("No hay solicitudes pendientes.")
    else:
        for registro in registros:
            # En lugar de nombre, num, estado = registro, usamos índices:
            nombre = registro[0]
            num = registro[1]
            estado = registro[2]
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{nombre}** (ID: {num})")
            col2.write(f"Estado: {estado}")
            # ... resto del código
            if estado == 'pendiente':
                if col3.button("✅ Aprobar", key=num):
                    aprobar_usuario(num)
                    st.rerun()
else:
    if password:
        st.error("Contraseña incorrecta.")
    st.warning("Introduce la contraseña en el panel lateral para gestionar los accesos.")
