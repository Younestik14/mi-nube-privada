import sqlite3
import os

def init_db():
    # Usamos una ruta absoluta para que siempre encuentre el archivo
    db_path = os.path.join(os.getcwd(), 'datos_estudiantes.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (nombre TEXT, num_estudiante TEXT PRIMARY KEY, estado TEXT)''')
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
