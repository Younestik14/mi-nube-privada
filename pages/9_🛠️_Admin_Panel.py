import streamlit as st
import sqlite3

st.sidebar.title("🔐 Acceso Admin")
if st.sidebar.text_input("Contraseña:", type="password") == "1868628":
    st.title("Panel de Aprobación")
    conn = sqlite3.connect('datos_estudiantes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios")
    for usuario in c.fetchall():
        nombre, num, estado = usuario
        col1, col2 = st.columns(2)
        col1.write(f"{nombre} ({num}) - {estado}")
        if estado == "pendiente":
            if col2.button("✅ Aprobar", key=num):
                c.execute("UPDATE usuarios SET estado='aprobado' WHERE num_estudiante=?", (num,))
                conn.commit()
                st.rerun()
    conn.close()
else:
    st.warning("Introduce la contraseña en la barra lateral.")
