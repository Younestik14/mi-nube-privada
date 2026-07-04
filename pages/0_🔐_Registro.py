import sqlite3

def init_db():
    # Esto crea el archivo que guardará los nombres de tus alumnos
    conn = sqlite3.connect('datos_estudiantes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (nombre TEXT, num_estudiante TEXT PRIMARY KEY, estado TEXT)''')
    conn.commit()
    conn.close()

def registrar_usuario(nombre, num_estudiante):
    conn = sqlite3.connect('datos_estudiantes.db')
    c = conn.cursor()
    try:
        # Se guarda como 'pendiente' hasta que tú lo apruebes
        c.execute("INSERT INTO usuarios VALUES (?, ?, 'pendiente')", (nombre, num_estudiante))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()
