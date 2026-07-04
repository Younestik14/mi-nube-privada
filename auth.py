import sqlite3
import streamlit as st

def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (nombre TEXT, num_estudiante TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def registrar_usuario(nombre, num_estudiante):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios VALUES (?, ?)", (nombre, num_estudiante))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # El número ya existe
    finally:
        conn.close()
