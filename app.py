# modules/db_init.py

import sqlite3
from pathlib import Path
from typing import Optional
import hashlib

DB_PATH = Path("database.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabla de usuarios
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'tecnico',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Tabla de proyectos
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client_name TEXT,
            address TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        """
    )

    # Tabla de presupuestos
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            total FLOAT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
    )

    # Tabla de memorias REBT
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
    )

    # Usuario admin por defecto
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "admin",
                hash_password("admin123"),
                "Administrador",
                "admin",
            ),
        )

    conn.commit()
    conn.close()


def ensure_db_initialized():
    if not DB_PATH.exists():
        init_db()
    else:
        # Podrías añadir migraciones aquí si en el futuro cambian las tablas
        pass


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
# auth/login.py

import streamlit as st
from modules.db_init import get_connection, hash_password


def login_form():
    st.markdown("### Iniciar sesión")

    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    if st.button("Acceder", use_container_width=True):
        if authenticate(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = get_user_role(username)
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")


def authenticate(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    row = cur.fetchone()

    if row is None:
        return False

    return row["password_hash"] == hash_password(password)


def get_user_role(username: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT role FROM users WHERE username = ?",
        (username,)
    )
    row = cur.fetchone()

    return row["role"] if row else "tecnico"


def logout_button():
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def require_login():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("Debes iniciar sesión para continuar.")
        login_form()
        st.stop()
# auth/security.py

import streamlit as st
from functools import wraps
from modules.db_init import get_connection, hash_password


# ---------------------------------------------------------
# VALIDACIÓN DE ROLES
# ---------------------------------------------------------

def user_has_role(required_role: str) -> bool:
    """
    Comprueba si el usuario actual tiene el rol requerido.
    """
    if "role" not in st.session_state:
        return False

    current_role = st.session_state["role"]

    # admin siempre tiene acceso
    if current_role == "admin":
        return True

    return current_role == required_role


# ---------------------------------------------------------
# DECORADORES DE SEGURIDAD
# ---------------------------------------------------------

def require_role(role: str):
    """
    Decorador para proteger funciones según rol.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not user_has_role(role):
                st.error("No tienes permisos para acceder a esta sección.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_authentication(func):
    """
    Decorador para exigir login antes de ejecutar una función.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
            st.warning("Debes iniciar sesión para continuar.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------
# GESTIÓN DE USUARIOS
# ---------------------------------------------------------

def create_user(username: str, password: str, full_name: str, role: str = "tecnico") -> bool:
    """
    Crea un usuario nuevo en la base de datos.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (username, hash_password(password), full_name, role)
        )
        conn.commit()
        return True
    except Exception:
        return False


def list_users():
    """
    Devuelve todos los usuarios registrados.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, username, full_name, role, created_at FROM users")
    return cur.fetchall()


def delete_user(user_id: int) -> bool:
    """
    Elimina un usuario por ID.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception:
        return False
# modules/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from datetime import datetime
import os


def generar_pdf_presupuesto(
    output_path: str,
    proyecto: dict,
    presupuesto: dict,
    firma_digital: dict,
    logo_path: str = "assets/logo.png"
):
    """
    Genera un PDF profesional del presupuesto usando ReportLab.
    """

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # ---------------------------------------------------------
    # ENCABEZADO
    # ---------------------------------------------------------
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 20 * mm, height - 40 * mm, width=40 * mm, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(70 * mm, height - 25 * mm, "PRESUPUESTO DE INSTALACIÓN ELÉCTRICA")

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 50 * mm, f"Proyecto: {proyecto.get('nombre', '')}")
    c.drawString(20 * mm, height - 56 * mm, f"Cliente: {proyecto.get('cliente', '')}")
    c.drawString(20 * mm, height - 62 * mm, f"Dirección: {proyecto.get('direccion', '')}")
    c.drawString(20 * mm, height - 68 * mm, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    # ---------------------------------------------------------
    # TABLA DE CAPÍTULOS
    # ---------------------------------------------------------
    data = [["Capítulo", "Material (€)", "Mano de obra (€)", "Total (€)"]]

    for cap in presupuesto["capitulos"]:
        data.append([
            cap["Capítulo"],
            f"{cap['Material (€)']:.2f}",
            f"{cap['Mano de obra (€)']:.2f}",
            f"{cap['Total capítulo (€)']:.2f}",
        ])

    data.append(["", "", "TOTAL", f"{presupuesto['total_final']:.2f} €"])

    table = Table(data, colWidths=[70 * mm, 30 * mm, 30 * mm, 30 * mm])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    table.wrapOn(c, 20 * mm, height - 200 * mm)
    table.drawOn(c, 20 * mm, height - 200 * mm)

    # ---------------------------------------------------------
    # FIRMA DIGITAL
    # ---------------------------------------------------------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, 40 * mm, "Firma digital:")

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, 34 * mm, f"Nombre: {firma_digital.get('nombre', '')}")
    c.drawString(20 * mm, 28 * mm, f"DNI: {firma_digital.get('dni', '')}")
    c.drawString(20 * mm, 22 * mm, f"Cargo: {firma_digital.get('cargo', '')}")
    c.drawString(20 * mm, 16 * mm, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    # ---------------------------------------------------------
    # PIE DE PÁGINA
    # ---------------------------------------------------------
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, 10 * mm, "Documento generado automáticamente por la aplicación de ingeniería eléctrica.")

    c.save()
    return output_path
# modules/memoria_rebt.py

from docx import Document
from datetime import datetime
from modules.pdf_generator import generar_pdf_presupuesto


def generar_memoria_word(
    output_path: str,
    proyecto: dict,
    secciones: dict,
    protecciones: dict,
    presupuesto: dict,
    firma_digital: dict
):
    """
    Genera la Memoria Técnica REBT en formato Word.
    """

    doc = Document()

    # ---------------------------------------------------------
    # PORTADA
    # ---------------------------------------------------------
    doc.add_heading("MEMORIA TÉCNICA DE DISEÑO (MTD)", level=1)
    doc.add_paragraph(f"Proyecto: {proyecto.get('nombre', '')}")
    doc.add_paragraph(f"Cliente: {proyecto.get('cliente', '')}")
    doc.add_paragraph(f"Dirección: {proyecto.get('direccion', '')}")
    doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    doc.add_page_break()

    # ---------------------------------------------------------
    # 1. DATOS GENERALES
    # ---------------------------------------------------------
    doc.add_heading("1. Datos generales", level=2)
    doc.add_paragraph(f"Tipo de instalación: {proyecto.get('tipo', 'Instalación eléctrica en vivienda')}")
    doc.add_paragraph(f"Potencia prevista: {proyecto.get('potencia', 'Según cálculo')}")
    doc.add_paragraph(f"Instalador: {firma_digital.get('nombre', '')}")
    doc.add_paragraph(f"DNI: {firma_digital.get('dni', '')}")
    doc.add_paragraph(f"Cargo: {firma_digital.get('cargo', '')}")

    # ---------------------------------------------------------
    # 2. SECCIONES DE CONDUCTORES
    # ---------------------------------------------------------
    doc.add_heading("2. Secciones de conductores", level=2)

    for nombre, datos in secciones.items():
        p = doc.add_paragraph()
        p.add_run(f"{nombre}: ").bold = True
        p.add_run(f"{datos['seccion']} mm² — {datos['descripcion']}")

    # ---------------------------------------------------------
    # 3. PROTECCIONES
    # ---------------------------------------------------------
    doc.add_heading("3. Protecciones", level=2)

    for nombre, datos in protecciones.items():
        p = doc.add_paragraph()
        p.add_run(f"{nombre}: ").bold = True
        p.add_run(f"{datos['proteccion']} — {datos['descripcion']}")

    # ---------------------------------------------------------
    # 4. CIRCUITOS C1–C13
    # ---------------------------------------------------------
    doc.add_heading("4. Circuitos C1–C13", level=2)

    for cap in presupuesto["capitulos"]:
        p = doc.add_paragraph()
        p.add_run(f"{cap['Capítulo']}: ").bold = True
        p.add_run(f"Material: {cap['Material (€)']:.2f} €, Mano de obra: {cap['Mano de obra (€)']:.2f} €, Total: {cap['Total capítulo (€)']:.2f} €")

    # ---------------------------------------------------------
    # 5. DERIVACIÓN INDIVIDUAL
    # ---------------------------------------------------------
    doc.add_heading("5. Derivación individual", level=2)
    di = secciones.get("Derivación individual", {})
    doc.add_paragraph(f"Sección: {di.get('seccion', '—')} mm²")
    doc.add_paragraph(f"Longitud: {di.get('longitud', '—')} m")
    doc.add_paragraph(f"Caída de tensión: {di.get('caida', '—')} %")

    # ---------------------------------------------------------
    # 6. CUADRO GENERAL
    # ---------------------------------------------------------
    doc.add_heading("6. Cuadro general", level=2)
    cg = protecciones.get("Cuadro general", {})
    doc.add_paragraph(f"Protección general: {cg.get('proteccion', '—')}")
    doc.add_paragraph(f"Intensidad asignada: {cg.get('intensidad', '—')} A")

    # ---------------------------------------------------------
    # 7. OBSERVACIONES REBT
    # ---------------------------------------------------------
    doc.add_heading("7. Observaciones REBT", level=2)
    doc.add_paragraph(
        "La instalación cumple con el Reglamento Electrotécnico para Baja Tensión (REBT) "
        "y sus Instrucciones Técnicas Complementarias (ITC-BT)."
    )

    # ---------------------------------------------------------
    # FIRMA DIGITAL
    # ---------------------------------------------------------
    doc.add_page_break()
    doc.add_heading("Firma digital", level=2)
    doc.add_paragraph(f"Nombre: {firma_digital.get('nombre', '')}")
    doc.add_paragraph(f"DNI: {firma_digital.get('dni', '')}")
    doc.add_paragraph(f"Cargo: {firma_digital.get('cargo', '')}")
    doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    doc.save(output_path)
    return output_path


def generar_memoria_pdf(
    output_path: str,
    proyecto: dict,
    presupuesto: dict,
    firma_digital: dict
):
    """
    Genera la memoria REBT en PDF reutilizando el generador de presupuesto.
    """
    return generar_pdf_presupuesto(
        output_path=output_path,
        proyecto=proyecto,
        presupuesto=presupuesto,
        firma_digital=firma_digital
    )
# modules/presupuesto.py

import streamlit as st
import pandas as pd


# ---------------------------------------------------------
# CÁLCULO DE UN CAPÍTULO
# ---------------------------------------------------------

def calcular_capitulo(nombre_capitulo: str, catalogo: dict) -> dict:
    """
    Calcula un capítulo del presupuesto usando el catálogo.
    Devuelve un diccionario con todos los importes.
    """

    productos = catalogo.get(nombre_capitulo, [])

    total_material = 0
    total_mano_obra = 0

    for p in productos:
        total_material += p["precio_material"] * p["cantidad"]
        total_mano_obra += p["precio_mano_obra"] * p["cantidad"]

    base_capitulo = total_material + total_mano_obra
    gastos_generales = base_capitulo * 0.15
    beneficio = base_capitulo * 0.06
    base_imponible = base_capitulo + gastos_generales + beneficio
    iva = base_imponible * 0.21
    total_capitulo = base_imponible + iva

    return {
        "Capítulo": nombre_capitulo,
        "Material (€)": total_material,
        "Mano de obra (€)": total_mano_obra,
        "Base capítulo (€)": base_capitulo,
        "Gastos generales (€)": gastos_generales,
        "Beneficio (€)": beneficio,
        "Base imponible (€)": base_imponible,
        "IVA (€)": iva,
        "Total capítulo (€)": total_capitulo,
    }


# ---------------------------------------------------------
# CÁLCULO COMPLETO DEL PRESUPUESTO
# ---------------------------------------------------------

@st.cache_data
def calcular_presupuesto_completo(catalogo: dict, lista_capitulos: list) -> dict:
    """
    Calcula todos los capítulos del presupuesto y devuelve:
    - Lista de capítulos
    - Totales globales
    """

    resultados = []

    for cap in lista_capitulos:
        datos = calcular_capitulo(cap, catalogo)
        resultados.append(datos)

    df = pd.DataFrame(resultados)

    total_material = df["Material (€)"].sum()
    total_mano_obra = df["Mano de obra (€)"].sum()
    total_base = df["Base capítulo (€)"].sum()
    total_gastos = df["Gastos generales (€)"].sum()
    total_benef = df["Beneficio (€)"].sum()
    total_base_imp = df["Base imponible (€)"].sum()
    total_iva = df["IVA (€)"].sum()
    total_final = df["Total capítulo (€)"].sum()

    return {
        "capitulos": resultados,
        "df": df,
        "totales": {
            "material": total_material,
            "mano_obra": total_mano_obra,
            "base": total_base,
            "gastos": total_gastos,
            "beneficio": total_benef,
            "base_imponible": total_base_imp,
            "iva": total_iva,
            "total_final": total_final,
        },
    }


# ---------------------------------------------------------
# EXPORTACIÓN A EXCEL AVANZADA
# ---------------------------------------------------------

def exportar_excel_avanzado(presupuesto: dict, nombre_archivo: str):
    """
    Exporta el presupuesto a un Excel con varias hojas:
    - Resumen
    - Capítulos
    """

    df = presupuesto["df"]
    tot = presupuesto["totales"]

    with pd.ExcelWriter(nombre_archivo, engine="xlsxwriter") as writer:

        # Hoja 1: Capítulos
        df.to_excel(writer, sheet_name="Capítulos", index=False)

        # Hoja 2: Resumen
        resumen = pd.DataFrame([
            ["Material total", tot["material"]],
            ["Mano de obra total", tot["mano_obra"]],
            ["Base capítulos", tot["base"]],
            ["Gastos generales", tot["gastos"]],
            ["Beneficio industrial", tot["beneficio"]],
            ["Base imponible", tot["base_imponible"]],
            ["IVA total", tot["iva"]],
            ["TOTAL PRESUPUESTO", tot["total_final"]],
        ], columns=["Concepto", "Importe (€)"])

        resumen.to_excel(writer, sheet_name="Resumen", index=False)

    with open(nombre_archivo, "rb") as f:
        return f.read()
# modules/secciones.py

import math
import streamlit as st


# ---------------------------------------------------------
# CONSTANTES GENERALES
# ---------------------------------------------------------

RESISTIVIDAD_CU = 0.0225  # ohm·mm²/m
COSFI = 0.95
V = 230  # tensión monofásica


# ---------------------------------------------------------
# INTENSIDAD POR POTENCIA
# ---------------------------------------------------------

def intensidad_por_potencia(potencia_w):
    """
    Calcula la intensidad a partir de la potencia.
    """
    return potencia_w / (V * COSFI)


# ---------------------------------------------------------
# CAÍDA DE TENSIÓN
# ---------------------------------------------------------

def caida_tension(intensidad, longitud_m, seccion_mm2):
    """
    Cálculo de caída de tensión en %.
    """
    r = RESISTIVIDAD_CU / seccion_mm2
    caida_v = math.sqrt(3) * intensidad * r * longitud_m
    return (caida_v / V) * 100


# ---------------------------------------------------------
# SECCIÓN SEGÚN ITC‑BT‑19 (simplificada)
# ---------------------------------------------------------

def seleccionar_seccion(intensidad):
    """
    Selección simplificada de sección según ITC‑BT‑19.
    """
    if intensidad <= 10:
        return 1.5
    elif intensidad <= 16:
        return 2.5
    elif intensidad <= 20:
        return 4
    elif intensidad <= 25:
        return 6
    elif intensidad <= 32:
        return 10
    elif intensidad <= 40:
        return 16
    elif intensidad <= 63:
        return 25
    else:
        return 35


# ---------------------------------------------------------
# SELECCIÓN DE MAGNETOTÉRMICO
# ---------------------------------------------------------

def seleccionar_magnetotermico(intensidad):
    """
    Selección automática de magnetotérmico.
    """
    if intensidad <= 10:
        return "10 A"
    elif intensidad <= 16:
        return "16 A"
    elif intensidad <= 20:
        return "20 A"
    elif intensidad <= 25:
        return "25 A"
    elif intensidad <= 32:
        return "32 A"
    elif intensidad <= 40:
        return "40 A"
    elif intensidad <= 50:
        return "50 A"
    else:
        return "63 A"


# ---------------------------------------------------------
# SELECCIÓN DE DIFERENCIAL
# ---------------------------------------------------------

def seleccionar_diferencial(intensidad):
    """
    Selección automática de diferencial.
    """
    if intensidad <= 25:
        return "30 mA — 25 A"
    elif intensidad <= 40:
        return "30 mA — 40 A"
    else:
        return "30 mA — 63 A"


# ---------------------------------------------------------
# CÁLCULO COMPLETO DE UNA LÍNEA
# ---------------------------------------------------------

def calcular_linea(nombre, potencia_w, longitud_m):
    """
    Devuelve todos los datos de una línea:
    - Intensidad
    - Sección
    - Caída de tensión
    - Magnetotérmico
    - Diferencial
    """

    intensidad = intensidad_por_potencia(potencia_w)
    seccion = seleccionar_seccion(intensidad)
    caida = caida_tension(intensidad, longitud_m, seccion)
    magneto = seleccionar_magnetotermico(intensidad)
    diferencial = seleccionar_diferencial(intensidad)

    return {
        "nombre": nombre,
        "potencia_w": potencia_w,
        "longitud_m": longitud_m,
        "intensidad": intensidad,
        "seccion": seccion,
        "caida": caida,
        "magnetotermico": magneto,
        "diferencial": diferencial,
        "descripcion": f"Línea {nombre}: {seccion} mm², {magneto}, caída {caida:.2f}%",
    }


# ---------------------------------------------------------
# DERIVACIÓN INDIVIDUAL
# ---------------------------------------------------------

def calcular_derivacion_individual(potencia_w, longitud_m):
    """
    Cálculo específico para la DI según REBT.
    """

    intensidad = intensidad_por_potencia(potencia_w)
    seccion = seleccionar_seccion(intensidad)
    caida = caida_tension(intensidad, longitud_m, seccion)

    return {
        "seccion": seccion,
        "longitud": longitud_m,
        "caida": caida,
        "descripcion": f"DI {seccion} mm² — caída {caida:.2f}%",
    }
# modules/catalogo.py

import json
from pathlib import Path
import streamlit as st

CATALOGO_PATH = Path("catalogo.json")


# ---------------------------------------------------------
# CARGA DEL CATÁLOGO
# ---------------------------------------------------------

def cargar_catalogo():
    """
    Carga el catálogo desde catalogo.json.
    Si no existe, crea uno por defecto.
    """

    if not CATALOGO_PATH.exists():
        catalogo_base = generar_catalogo_base()
        guardar_catalogo(catalogo_base)
        return catalogo_base

    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# GUARDAR CATÁLOGO
# ---------------------------------------------------------

def guardar_catalogo(catalogo: dict):
    """
    Guarda el catálogo en catalogo.json.
    """
    with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=4, ensure_ascii=False)


# ---------------------------------------------------------
# CATÁLOGO BASE (C1–C13)
# ---------------------------------------------------------

def generar_catalogo_base():
    """
    Catálogo inicial con capítulos C1–C13.
    Cada capítulo contiene una lista de productos:
    - nombre
    - cantidad
    - precio_material
    - precio_mano_obra
    """

    return {
        "C1 - Circuito de iluminación": [
            {"nombre": "Punto de luz", "cantidad": 8, "precio_material": 12.0, "precio_mano_obra": 8.0},
            {"nombre": "Interruptor", "cantidad": 8, "precio_material": 6.0, "precio_mano_obra": 4.0},
        ],
        "C2 - Tomas de corriente": [
            {"nombre": "Toma de corriente", "cantidad": 10, "precio_material": 9.0, "precio_mano_obra": 6.0},
        ],
        "C3 - Cocina y horno": [
            {"nombre": "Toma especial cocina", "cantidad": 2, "precio_material": 18.0, "precio_mano_obra": 10.0},
        ],
        "C4 - Lavadora, lavavajillas": [
            {"nombre": "Toma especial", "cantidad": 2, "precio_material": 15.0, "precio_mano_obra": 9.0},
        ],
        "C5 - Baños": [
            {"nombre": "Toma baño", "cantidad": 2, "precio_material": 12.0, "precio_mano_obra": 8.0},
        ],
        "C6 - Climatización": [
            {"nombre": "Línea aire acondicionado", "cantidad": 1, "precio_material": 40.0, "precio_mano_obra": 20.0},
        ],
        "C7 - Calefacción": [
            {"nombre": "Línea calefacción", "cantidad": 1, "precio_material": 35.0, "precio_mano_obra": 18.0},
        ],
        "C8 - Termo eléctrico": [
            {"nombre": "Línea termo", "cantidad": 1, "precio_material": 22.0, "precio_mano_obra": 12.0},
        ],
        "C9 - Automatización": [
            {"nombre": "Actuador domótico", "cantidad": 4, "precio_material": 30.0, "precio_mano_obra": 15.0},
        ],
        "C10 - Telecomunicaciones": [
            {"nombre": "Toma RJ45", "cantidad": 4, "precio_material": 14.0, "precio_mano_obra": 8.0},
        ],
        "C11 - Seguridad": [
            {"nombre": "Detector de presencia", "cantidad": 2, "precio_material": 25.0, "precio_mano_obra": 12.0},
        ],
        "C12 - Cuadro eléctrico": [
            {"nombre": "ICP + IGA + ID + PIA", "cantidad": 1, "precio_material": 120.0, "precio_mano_obra": 40.0},
        ],
        "C13 - Derivación individual": [
            {"nombre": "Cableado DI", "cantidad": 1, "precio_material": 80.0, "precio_mano_obra": 30.0},
        ],
    }


# ---------------------------------------------------------
# EDITOR DE CATÁLOGO (INTERFAZ STREAMLIT)
# ---------------------------------------------------------

def editor_catalogo_ui():
    """
    Interfaz para editar el catálogo desde Streamlit.
    """

    st.subheader("📦 Editor de catálogo")

    catalogo = cargar_catalogo()

    capitulo = st.selectbox("Selecciona un capítulo", list(catalogo.keys()))

    productos = catalogo[capitulo]

    st.write("### Productos del capítulo")

    for i, p in enumerate(productos):
        st.text_input(f"Nombre {i+1}", value=p["nombre"], key=f"nombre_{i}")
        st.number_input(f"Cantidad {i+1}", value=p["cantidad"], key=f"cantidad_{i}")
        st.number_input(f"Precio material {i+1}", value=p["precio_material"], key=f"pmat_{i}")
        st.number_input(f"Precio mano de obra {i+1}", value=p["precio_mano_obra"], key=f"pmo_{i}")
        st.markdown("---")

    if st.button("Guardar cambios", use_container_width=True):
        for i, p in enumerate(productos):
            p["nombre"] = st.session_state[f"nombre_{i}"]
            p["cantidad"] = st.session_state[f"cantidad_{i}"]
            p["precio_material"] = st.session_state[f"pmat_{i}"]
            p["precio_mano_obra"] = st.session_state[f"pmo_{i}"]

        guardar_catalogo(catalogo)
        st.success("Catálogo actualizado correctamente.")
/* ---------------------------------------------------------
   ESTILO GLOBAL macOS SONOMA
--------------------------------------------------------- */

html, body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
    background: var(--bg);
    color: var(--text);
    transition: background 0.3s ease, color 0.3s ease;
}

/* ---------------------------------------------------------
   MODO CLARO / OSCURO AUTOMÁTICO
--------------------------------------------------------- */

@media (prefers-color-scheme: light) {
    :root {
        --bg: #f5f5f7;
        --card-bg: rgba(255, 255, 255, 0.65);
        --text: #1d1d1f;
        --border: rgba(0, 0, 0, 0.08);
        --shadow: rgba(0, 0, 0, 0.08);
    }
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg: #1c1c1e;
        --card-bg: rgba(40, 40, 42, 0.55);
        --text: #f5f5f7;
        --border: rgba(255, 255, 255, 0.08);
        --shadow: rgba(0, 0, 0, 0.5);
    }
}

/* ---------------------------------------------------------
   TARJETAS ESTILO SONOMA GLASS
--------------------------------------------------------- */

.stCard, .glass-card {
    background: var(--card-bg);
    backdrop-filter: blur(18px) saturate(180%);
    -webkit-backdrop-filter: blur(18px) saturate(180%);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 8px 24px var(--shadow);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px var(--shadow);
}

/* ---------------------------------------------------------
   BOTONES ESTILO APPLE
--------------------------------------------------------- */

.stButton > button {
    background: linear-gradient(180deg, #007aff, #0051a8);
    color: white;
    border-radius: 12px;
    padding: 10px 18px;
    border: none;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: linear-gradient(180deg, #0a84ff, #0062cc);
    transform: translateY(-2px);
}

.stButton > button:active {
    transform: scale(0.97);
}

/* ---------------------------------------------------------
   INPUTS
--------------------------------------------------------- */

input, select, textarea {
    background: var(--card-bg) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    padding: 8px 12px !important;
    transition: border 0.2s ease;
}

input:focus, select:focus, textarea:focus {
    border: 1px solid #0a84ff !important;
    outline: none !important;
}

/* ---------------------------------------------------------
   TABLAS
--------------------------------------------------------- */

table {
    background: var(--card-bg) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

thead {
    background: rgba(0, 0, 0, 0.05);
    font-weight: 600;
}

tbody tr:hover {
    background: rgba(0, 122, 255, 0.08);
    transition: background 0.2s ease;
}

/* ---------------------------------------------------------
   SCROLLBAR ESTILO APPLE
--------------------------------------------------------- */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: rgba(120, 120, 128, 0.4);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(120, 120, 128, 0.6);
}

/* ---------------------------------------------------------
   TITULOS
--------------------------------------------------------- */

h1, h2, h3, h4 {
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text);
}

/* ---------------------------------------------------------
   SEPARADORES
--------------------------------------------------------- */

.divider {
    width: 100%;
    height: 2px;
    background: var(--border);
    margin: 20px 0;
}
# app.py

import streamlit as st
from pathlib import Path

# -----------------------------
# IMPORTACIÓN DE MÓDULOS
# -----------------------------
from modules.db_init import ensure_db_initialized
from auth.login import login_form, logout_button
from auth.security import require_authentication, require_role
from modules.catalogo import cargar_catalogo, editor_catalogo_ui
from modules.presupuesto import calcular_presupuesto_completo, exportar_excel_avanzado
from modules.secciones import calcular_linea, calcular_derivacion_individual
from modules.memoria_rebt import generar_memoria_word, generar_memoria_pdf
from modules.pdf_generator import generar_pdf_presupuesto


# -----------------------------
# CONFIGURACIÓN INICIAL
# -----------------------------
st.set_page_config(
    page_title="Ingeniería Eléctrica PRO",
    page_icon="⚡",
    layout="wide"
)

# Cargar CSS Sonoma
css_path = Path("static/sonoma.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Inicializar base de datos
ensure_db_initialized()


# -----------------------------
# LOGIN
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_form()
    st.stop()


# -----------------------------
# MENÚ PRINCIPAL
# -----------------------------
st.sidebar.title("⚡ Menú principal")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "🏠 Inicio",
        "📐 Cálculo de secciones",
        "💰 Presupuesto",
        "📘 Memoria REBT",
        "📦 Catálogo",
        "👤 Cuenta"
    ]
)


# -----------------------------
# 1. INICIO
# -----------------------------
if opcion == "🏠 Inicio":
    st.title("⚡ Aplicación de Ingeniería Eléctrica PRO")
    st.write("Bienvenido, **" + st.session_state["username"] + "**.")
    st.write("Selecciona una opción en el menú lateral para comenzar.")


# -----------------------------
# 2. CÁLCULO DE SECCIONES
# -----------------------------
elif opcion == "📐 Cálculo de secciones":
    st.title("📐 Cálculo de secciones y protecciones")

    nombre = st.text_input("Nombre de la línea", "C1 - Iluminación")
    potencia = st.number_input("Potencia (W)", min_value=100, value=2000)
    longitud = st.number_input("Longitud (m)", min_value=1, value=15)

    if st.button("Calcular línea", use_container_width=True):
        datos = calcular_linea(nombre, potencia, longitud)

        st.success("Cálculo realizado correctamente.")
        st.json(datos)


# -----------------------------
# 3. PRESUPUESTO
# -----------------------------
elif opcion == "💰 Presupuesto":
    st.title("💰 Presupuesto completo")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    if st.button("Calcular presupuesto", use_container_width=True):
        presupuesto = calcular_presupuesto_completo(catalogo, lista_capitulos)

        st.subheader("📊 Resultado")
        st.dataframe(presupuesto["df"], use_container_width=True)

        st.subheader("📈 Totales")
        st.json(presupuesto["totales"])

        # Exportación Excel
        excel_bytes = exportar_excel_avanzado(presupuesto, "presupuesto.xlsx")
        st.download_button(
            "📥 Descargar Excel",
            data=excel_bytes,
            file_name="presupuesto.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Exportación PDF
        pdf_path = "presupuesto.pdf"
        generar_pdf_presupuesto(
            output_path=pdf_path,
            proyecto={"nombre": "Proyecto genérico"},
            presupuesto=presupuesto,
            firma_digital={"nombre": "Técnico", "dni": "00000000X", "cargo": "Instalador autorizado"}
        )
        st.download_button(
            "📄 Descargar PDF",
            data=open(pdf_path, "rb").read(),
            file_name="presupuesto.pdf",
            mime="application/pdf"
        )


# -----------------------------
# 4. MEMORIA REBT
# -----------------------------
elif opcion == "📘 Memoria REBT":
    st.title("📘 Generación de Memoria Técnica REBT")

    st.write("Completa los datos del proyecto:")

    nombre = st.text_input("Nombre del proyecto")
    cliente = st.text_input("Cliente")
    direccion = st.text_input("Dirección")

    if st.button("Generar memoria", use_container_width=True):
        proyecto = {
            "nombre": nombre,
            "cliente": cliente,
            "direccion": direccion
        }

        # Datos ficticios para ejemplo
        secciones = {
            "C1": {"seccion": 1.5, "descripcion": "Iluminación"},
            "C2": {"seccion": 2.5, "descripcion": "Tomas de corriente"},
        }

        protecciones = {
            "Cuadro general": {"proteccion": "IGA 40A", "intensidad": 40, "descripcion": "Protección general"}
        }

        presupuesto = {
            "capitulos": [
                {"Capítulo": "C1", "Material (€)": 100, "Mano de obra (€)": 80, "Total capítulo (€)": 230},
                {"Capítulo": "C2", "Material (€)": 150, "Mano de obra (€)": 90, "Total capítulo (€)": 290},
            ],
            "total_final": 520
        }

        firma = {"nombre": "Técnico", "dni": "00000000X", "cargo": "Instalador autorizado"}

        # Word
        word_path = "memoria_rebt.docx"
        generar_memoria_word(word_path, proyecto, secciones, protecciones, presupuesto, firma)

        st.download_button(
            "📘 Descargar Memoria Word",
            data=open(word_path, "rb").read(),
            file_name="memoria_rebt.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # PDF
        pdf_path = "memoria_rebt.pdf"
        generar_memoria_pdf(pdf_path, proyecto, presupuesto, firma)

        st.download_button(
            "📄 Descargar Memoria PDF",
            data=open(pdf_path, "rb").read(),
            file_name="memoria_rebt.pdf",
            mime="application/pdf"
        )


# -----------------------------
# 5. CATÁLOGO
# -----------------------------
elif opcion == "📦 Catálogo":
    st.title("📦 Catálogo de materiales")
    require_role("admin")
    editor_catalogo_ui()


# -----------------------------
# 6. CUENTA
# -----------------------------
elif opcion == "👤 Cuenta":
    st.title("👤 Cuenta de usuario")
    st.write(f"Usuario: **{st.session_state['username']}**")
    st.write(f"Rol: **{st.session_state['role']}**")
    logout_button()
