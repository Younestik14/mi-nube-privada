import sqlite3
import streamlit as st

# Código simple para ver quién ha pedido entrar
conn = sqlite3.connect('usuarios.db')
data = conn.execute("SELECT * FROM usuarios").fetchall()
st.table(data)
