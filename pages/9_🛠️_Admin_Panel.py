import streamlit as st
import sqlite3
import os

st.sidebar.title("🔐 Acceso Admin")
if st.sidebar.text_input("Contraseña:", type="password") == "1868628":
    st.title("Panel de Aprobación")
    
    db_path = os.path.join(os.getcwd(), 'datos_estudiantes.db')
    
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios")
        data = c.fetchall()
        
        for usuario in data:
            nombre, num, estado = usuario
            col1, col2 = st.columns(2)
            col1.write(f"{nombre} ({num}) - {estado}")
            if estado == "pendiente":
                if col2.button("✅ Aprobar", key=num):
                    c.execute("UPDATE usuarios SET estado='aprobado' WHERE num_estudiante=?", (num,))
                    conn.commit()
                    st.rerun()
        conn.close()
    except Exception as e:
        st.error("La base de datos está bloqueada o no existe. Por favor, reinicia la app.")
else:
    st.warning("Introduce la contraseña.")
