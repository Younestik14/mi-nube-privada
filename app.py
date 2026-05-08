# ============================================================
# app.py — Ingeniería Eléctrica PRO (macOS Sonoma Edition)
# ============================================================

import streamlit as st
import sqlite3
import hashlib
import base64
import json
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from docx import Document
import logging
import math

# ============================================================
# SISTEMA DE LOGS
# ============================================================

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

logging.info("Aplicación iniciada")

# ============================================================
# CONFIGURACIÓN STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Ingeniería Eléctrica PRO",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# INICIALIZACIÓN SEGURA DEL ESTADO DE SESIÓN
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

if "role" not in st.session_state:
    st.session_state["role"] = None

if "full_name" not in st.session_state:
    st.session_state["full_name"] = None

# ============================================================
# CSS SONOMA
# ============================================================

st.markdown("""
<style>

html, body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
    background: var(--bg);
    color: var(--text);
}

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

.glass-card {
    background: var(--card-bg);
    backdrop-filter: blur(18px) saturate(180%);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 8px 24px var(--shadow);
}

.stButton > button {
    background: linear-gradient(180deg, #007aff, #0051a8);
    color: white;
    border-radius: 12px;
    padding: 10px 18px;
    border: none;
    font-weight: 600;
}

.divider {
    width: 100%;
    height: 2px;
    background: var(--border);
    margin: 20px 0;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# UTILIDADES DE UI
# ============================================================

def card_open():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def divider():
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

def titulo_centrado(titulo, subtitulo=""):
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom: 1.5rem;">
            <h1 style="margin-bottom:0;">{titulo}</h1>
            <p style="opacity:0.8; margin-top:0.3rem;">{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# BASE DE DATOS SQLITE (ADMIN = 1868628 / Laaljorra_2002)
# ============================================================

DB_PATH = "usuarios.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT,
                role TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

        admin_pass = hashlib.sha256("Laaljorra_2002".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("1868628", admin_pass, "Administrador", "admin", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logging.info("Base de datos creada y usuario admin generado")

init_db()

# ============================================================
# AUTENTICACIÓN
# ============================================================

def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash, role, full_name FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False, None, None

    stored_hash, role, full_name = row
    if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
        logging.info(f"Usuario {username} inició sesión")
        return True, role, full_name

    logging.warning(f"Intento fallido de login para {username}")
    return False, None, None

def require_role(role):
    if st.session_state.get("role") != role:
        st.error("No tienes permisos para acceder a esta sección.")
        st.stop()

# ============================================================
# LOGIN UI (ESTABLE, SIN RERUN)
# ============================================================

def login_ui():
    card_open()
    st.markdown("### 🔐 Iniciar sesión")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar", use_container_width=True):
        ok, role, full_name = login(username, password)
        if ok:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.session_state["full_name"] = full_name
        else:
            st.error("Usuario o contraseña incorrectos")

    card_close()

# ============================================================
# CATÁLOGO BASE
# ============================================================

CATALOGO_PATH = "catalogo.json"

CATALOGO_BASE = {
    "C1 - Iluminación": [
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

def init_catalogo():
    if not os.path.exists(CATALOGO_PATH):
        with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
            json.dump(CATALOGO_BASE, f, indent=4, ensure_ascii=False)
        logging.info("Catálogo generado automáticamente")

init_catalogo()

def cargar_catalogo():
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_catalogo(catalogo):
    with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=4, ensure_ascii=False)
# ============================================================
# CÁLCULO DE SECCIONES EXTENDIDO — ITC‑BT‑19
# ============================================================

INTENSIDADES_ADM = {
    "A1": {1.5: 14, 2.5: 18, 4: 24, 6: 31, 10: 43, 16: 57, 25: 76},
    "A2": {1.5: 16, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89},
    "B1": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101},
    "B2": {1.5: 20, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 113},
}

FACTORES_AGRUPAMIENTO = {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60, 6: 0.57}
FACTORES_TEMPERATURA = {25: 1.08, 30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71}
SECCIONES = [1.5, 2.5, 4, 6, 10, 16, 25]

def intensidad_por_potencia(potencia_w):
    return potencia_w / (230 * 0.95)

def intensidad_admisible(metodo, seccion, agrupamiento, temperatura):
    base = INTENSIDADES_ADM[metodo][seccion]
    return base * FACTORES_AGRUPAMIENTO[agrupamiento] * FACTORES_TEMPERATURA[temperatura]

def seleccionar_seccion_extendida(I, metodo, agrupamiento, temperatura):
    for s in SECCIONES:
        if intensidad_admisible(metodo, s, agrupamiento, temperatura) >= I:
            return s
    return SECCIONES[-1]

def caida_tension(I, L, S):
    r = 0.0225 / S
    return (math.sqrt(3) * I * r * L / 230) * 100

def seleccionar_magnetotermico(I):
    if I <= 10: return "10 A"
    if I <= 16: return "16 A"
    if I <= 20: return "20 A"
    if I <= 25: return "25 A"
    if I <= 32: return "32 A"
    if I <= 40: return "40 A"
    if I <= 50: return "50 A"
    return "63 A"

def seleccionar_diferencial(I):
    if I <= 25: return "30 mA — 25 A"
    if I <= 40: return "30 mA — 40 A"
    return "30 mA — 63 A"

def calcular_linea_extendida(nombre, potencia, longitud, metodo, agrupamiento, temperatura):
    I = intensidad_por_potencia(potencia)
    S = seleccionar_seccion_extendida(I, metodo, agrupamiento, temperatura)
    caida = caida_tension(I, longitud, S)

    return {
        "nombre": nombre,
        "intensidad": I,
        "seccion": S,
        "caida": caida,
        "magnetotermico": seleccionar_magnetotermico(I),
        "diferencial": seleccionar_diferencial(I),
        "metodo": metodo,
        "agrupamiento": agrupamiento,
        "temperatura": temperatura,
    }

# ============================================================
# PRESUPUESTO COMPLETO
# ============================================================

def calcular_capitulo(nombre_capitulo, catalogo):
    productos = catalogo.get(nombre_capitulo, [])
    total_material = sum(p["precio_material"] * p["cantidad"] for p in productos)
    total_mano_obra = sum(p["precio_mano_obra"] * p["cantidad"] for p in productos)

    base = total_material + total_mano_obra
    gastos = base * 0.15
    beneficio = base * 0.06
    base_imp = base + gastos + beneficio
    iva = base_imp * 0.21
    total = base_imp + iva

    return {
        "Capítulo": nombre_capitulo,
        "Material (€)": total_material,
        "Mano de obra (€)": total_mano_obra,
        "Base capítulo (€)": base,
        "Gastos generales (€)": gastos,
        "Beneficio (€)": beneficio,
        "Base imponible (€)": base_imp,
        "IVA (€)": iva,
        "Total capítulo (€)": total,
    }

def calcular_presupuesto_completo(catalogo, lista_capitulos):
    caps = [calcular_capitulo(c, catalogo) for c in lista_capitulos]

    tot = {
        "material": sum(c["Material (€)"] for c in caps),
        "mano_obra": sum(c["Mano de obra (€)"] for c in caps),
        "base": sum(c["Base capítulo (€)"] for c in caps),
        "gastos": sum(c["Gastos generales (€)"] for c in caps),
        "beneficio": sum(c["Beneficio (€)"] for c in caps),
        "base_imponible": sum(c["Base imponible (€)"] for c in caps),
        "iva": sum(c["IVA (€)"] for c in caps),
        "total_final": sum(c["Total capítulo (€)"] for c in caps),
    }

    return {"capitulos": caps, "totales": tot}

# ============================================================
# GENERADOR PDF
# ============================================================

def generar_pdf_presupuesto(proyecto, presupuesto):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "Presupuesto — Ingeniería Eléctrica PRO")

    c.setFont("Helvetica", 12)
    c.drawString(40, 770, f"Proyecto: {proyecto['nombre']}")

    y = 730
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Capítulos:")
    y -= 20

    c.setFont("Helvetica", 10)
    for cap in presupuesto["capitulos"]:
        c.drawString(40, y, f"{cap['Capítulo']}: {cap['Total capítulo (€)']:.2f} €")
        y -= 15
        if y < 80:
            c.showPage()
            y = 800

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"TOTAL: {presupuesto['totales']['total_final']:.2f} €")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# GENERADOR WORD MEMORIA REBT
# ============================================================

def generar_memoria_word(proyecto, secciones, protecciones, presupuesto):
    doc = Document()

    doc.add_heading("Memoria Técnica REBT", level=1)
    doc.add_paragraph(f"Proyecto: {proyecto['nombre']}")
    doc.add_paragraph(f"Cliente: {proyecto['cliente']}")
    doc.add_paragraph(f"Dirección: {proyecto['direccion']}")
    doc.add_paragraph(f"Tipo: {proyecto['tipo']}")

    doc.add_heading("Secciones", level=2)
    for k, v in secciones.items():
        doc.add_paragraph(f"{k}: {v['seccion']} mm² — {v['descripcion']}")

    doc.add_heading("Protecciones", level=2)
    for k, v in protecciones.items():
        doc.add_paragraph(f"{k}: {v['proteccion']} — {v['descripcion']}")

    doc.add_heading("Presupuesto", level=2)
    for cap in presupuesto["capitulos"]:
        doc.add_paragraph(f"{cap['Capítulo']}: {cap['Total capítulo (€)']} €")

    if "total_final" in presupuesto:
        doc.add_paragraph(f"TOTAL: {presupuesto['total_final']} €")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# MENÚ PRINCIPAL
# ============================================================

titulo_centrado(
    "⚡ Ingeniería Eléctrica PRO",
    "Cálculo, presupuesto y memoria REBT — Estética macOS Sonoma"
)

col_l, col_c, col_r = st.columns([1, 3, 1])
with col_c:
    opcion = st.radio(
        "Selecciona un módulo",
        [
            "🏠 Inicio",
            "📐 Cálculo de secciones",
            "💰 Presupuesto",
            "📘 Memoria REBT",
            "📦 Catálogo",
            "👥 Administración",
            "👤 Cuenta",
        ],
        horizontal=True,
    )

divider()
# ============================================================
# CONTROL DE ACCESO
# ============================================================

if not st.session_state["logged_in"]:
    titulo_centrado("⚡ Ingeniería Eléctrica PRO", "Acceso técnico profesional")
    login_ui()
    st.stop()

# ============================================================
# MÓDULOS DE INTERFAZ
# ============================================================

# ------------------------------------------------------------
# 1) INICIO
# ------------------------------------------------------------
if opcion == "🏠 Inicio":
    col1, col2 = st.columns(2)

    with col1:
        card_open()
        st.markdown("### 👋 Bienvenido")
        st.write(f"**Usuario:** {st.session_state['username']}")
        st.write(f"**Rol:** {st.session_state['role']}")
        st.write("Selecciona un módulo arriba para comenzar.")
        card_close()

    with col2:
        card_open()
        st.markdown("### 🧩 Módulos disponibles")
        st.markdown("- 📐 Cálculo de secciones extendido ITC‑BT‑19")
        st.markdown("- 💰 Presupuesto completo con PDF")
        st.markdown("- 📘 Memoria técnica REBT (Word + PDF)")
        st.markdown("- 📦 Catálogo editable de materiales")
        st.markdown("- 👥 Administración avanzada de usuarios")
        card_close()

# ------------------------------------------------------------
# 2) CÁLCULO DE SECCIONES EXTENDIDO
# ------------------------------------------------------------
elif opcion == "📐 Cálculo de secciones":
    card_open()
    st.markdown("### 📐 Cálculo de secciones — Modo EXTENDIDO ITC‑BT‑19")

    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre de la línea", "C1 - Iluminación")
        potencia = st.number_input("Potencia (W)", min_value=100, value=2000)
    with col2:
        longitud = st.number_input("Longitud (m)", min_value=1, value=15)
        metodo = st.selectbox("Método instalación (ITC‑BT‑19)", ["A1", "A2", "B1", "B2"])
    with col3:
        agrupamiento = st.selectbox("Nº de circuitos agrupados", [1,2,3,4,5,6])
        temperatura = st.selectbox("Temperatura ambiente (°C)", [25,30,35,40,45,50])

    if st.button("Calcular sección extendida", use_container_width=True):
        datos = calcular_linea_extendida(nombre, potencia, longitud, metodo, agrupamiento, temperatura)

        divider()
        st.markdown("### Resultado extendido")
        st.json(datos)

    card_close()

# ------------------------------------------------------------
# 3) PRESUPUESTO
# ------------------------------------------------------------
elif opcion == "💰 Presupuesto":
    card_open()
    st.markdown("### 💰 Presupuesto completo C1–C13")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    if st.button("Calcular presupuesto", use_container_width=True):
        presupuesto = calcular_presupuesto_completo(catalogo, lista_capitulos)

        st.markdown("#### 📊 Capítulos")
        st.dataframe(presupuesto["capitulos"], use_container_width=True)

        divider()
        st.markdown("#### 📈 Totales")

        tot = presupuesto["totales"]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Material total:** {tot['material']:.2f} €")
            st.write(f"**Mano de obra total:** {tot['mano_obra']:.2f} €")
            st.write(f"**Base capítulos:** {tot['base']:.2f} €")
            st.write(f"**Gastos generales:** {tot['gastos']:.2f} €")
            st.write(f"**Beneficio industrial:** {tot['beneficio']:.2f} €")
        with col2:
            st.write(f"**Base imponible:** {tot['base_imponible']:.2f} €")
            st.write(f"**IVA total:** {tot['iva']:.2f} €")
            st.write(f"**TOTAL PRESUPUESTO:** {tot['total_final']:.2f} €")

        divider()

        pdf_bytes = generar_pdf_presupuesto(
            proyecto={"nombre": "Proyecto genérico"},
            presupuesto=presupuesto
        )
        st.download_button(
            "📄 Descargar PDF",
            data=pdf_bytes,
            file_name="presupuesto.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    card_close()

# ------------------------------------------------------------
# 4) MEMORIA REBT
# ------------------------------------------------------------
elif opcion == "📘 Memoria REBT":
    card_open()
    st.markdown("### 📘 Generación de Memoria Técnica REBT")

    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del proyecto")
        cliente = st.text_input("Cliente")
        direccion = st.text_input("Dirección")
    with col2:
        tipo = st.text_input("Tipo de instalación", "Instalación eléctrica en vivienda")
        localidad = st.text_input("Localidad", "Orihuela (Alicante)")

    divider()

    if st.button("Generar memoria REBT (Word + PDF)", use_container_width=True):
        proyecto = {
            "nombre": nombre,
            "cliente": cliente,
            "direccion": direccion,
            "tipo": tipo,
            "localidad": localidad,
        }

        secciones = {
            "C1": {"seccion": 1.5, "descripcion": "Iluminación"},
            "C2": {"seccion": 2.5, "descripcion": "Tomas de corriente"},
        }

        protecciones = {
            "Cuadro general": {
                "proteccion": "IGA 40A",
                "descripcion": "Protección general"
            }
        }

        presupuesto = {
            "capitulos": [
                {"Capítulo": "C1", "Total capítulo (€)": 230},
                {"Capítulo": "C2", "Total capítulo (€)": 290},
            ],
            "total_final": 520,
        }

        word_bytes = generar_memoria_word(proyecto, secciones, protecciones, presupuesto)
        st.download_button(
            "📘 Descargar Memoria Word",
            data=word_bytes,
            file_name="memoria_rebt.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

        pdf_bytes = generar_pdf_presupuesto(proyecto, presupuesto)
        st.download_button(
            "📄 Descargar Memoria PDF",
            data=pdf_bytes,
            file_name="memoria_rebt.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    card_close()

# ------------------------------------------------------------
# 5) CATÁLOGO
# ------------------------------------------------------------
elif opcion == "📦 Catálogo":
    require_role("admin")
    card_open()
    st.markdown("### 📦 Catálogo de materiales (solo admin)")

    catalogo = cargar_catalogo()
    capitulo = st.selectbox("Selecciona un capítulo", list(catalogo.keys()))

    productos = catalogo[capitulo]

    st.write("### Productos del capítulo")

    for i, p in enumerate(productos):
        p["nombre"] = st.text_input(f"Nombre {i+1}", p["nombre"])
        p["cantidad"] = st.number_input(f"Cantidad {i+1}", value=p["cantidad"])
        p["precio_material"] = st.number_input(f"Precio material {i+1}", value=p["precio_material"])
        p["precio_mano_obra"] = st.number_input(f"Precio mano de obra {i+1}", value=p["precio_mano_obra"])
        st.markdown("---")

    if st.button("Guardar cambios", use_container_width=True):
        guardar_catalogo(catalogo)
        st.success("Catálogo actualizado correctamente.")

    card_close()

# ------------------------------------------------------------
# 6) ADMINISTRACIÓN AVANZADA
# ------------------------------------------------------------
elif opcion == "👥 Administración":
    require_role("admin")
    card_open()
    st.markdown("### 👥 Administración avanzada de usuarios")

    # ============================================================
    # CREAR USUARIO
    # ============================================================
    st.markdown("## ➕ Crear nuevo usuario")

    new_user = st.text_input("Nuevo usuario")
    new_pass = st.text_input("Contraseña", type="password")
    new_name = st.text_input("Nombre completo")
    new_role = st.selectbox("Rol", ["admin", "tecnico", "invitado"])

    if st.button("Crear usuario", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO users (username, password_hash, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                new_user,
                hashlib.sha256(new_pass.encode()).hexdigest(),
                new_name,
                new_role,
                datetime.now().isoformat()
            ))
            conn.commit()
            st.success("Usuario creado correctamente.")
            logging.info(f"Usuario creado: {new_user} ({new_role})")
        except:
            st.error("Error: el usuario ya existe.")
        conn.close()

    divider()

    # ============================================================
    # EDITAR USUARIO
    # ============================================================
    st.markdown("## ✏️ Editar usuario existente")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    usuarios = [u[0] for u in c.fetchall()]
    conn.close()

    user_to_edit = st.selectbox("Selecciona usuario", usuarios)

    if user_to_edit:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT full_name, role FROM users WHERE username=?", (user_to_edit,))
        full_name, role = c.fetchone()
        conn.close()

        new_full_name = st.text_input("Nuevo nombre completo", full_name)
        new_role_edit = st.selectbox("Nuevo rol", ["admin", "tecnico", "invitado"], index=["admin","tecnico","invitado"].index(role))

        if st.button("Guardar cambios", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                UPDATE users SET full_name=?, role=? WHERE username=?
            """, (new_full_name, new_role_edit, user_to_edit))
            conn.commit()
            conn.close()
            st.success("Usuario actualizado correctamente.")
            logging.info(f"Usuario editado: {user_to_edit} → {new_role_edit}")

    divider()

    # ============================================================
    # CAMBIAR CONTRASEÑA
    # ============================================================
    st.markdown("## 🔑 Cambiar contraseña")

    user_pass = st.selectbox("Usuario", usuarios, key="pass_user")
    new_pass_1 = st.text_input("Nueva contraseña", type="password")
    new_pass_2 = st.text_input("Repetir contraseña", type="password")

    if st.button("Actualizar contraseña", use_container_width=True):
        if new_pass_1 != new_pass_2:
            st.error("Las contraseñas no coinciden.")
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                UPDATE users SET password_hash=? WHERE username=?
            """, (hashlib.sha256(new_pass_1.encode()).hexdigest(), user_pass))
            conn.commit()
            conn.close()
            st.success("Contraseña actualizada correctamente.")
            logging.info(f"Contraseña cambiada para usuario: {user_pass}")

    divider()

    # ============================================================
    # BORRAR USUARIO
    # ============================================================
    st.markdown("## 🗑️ Borrar usuario")

    user_delete = st.selectbox("Selecciona usuario a borrar", usuarios, key="delete_user")

    if st.button("Borrar usuario", use_container_width=True):
        if user_delete == "1868628":
            st.error("No puedes borrar el usuario administrador principal.")
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (user_delete,))
            conn.commit()
            conn.close()
            st.success(f"Usuario '{user_delete}' eliminado.")
            logging.warning(f"Usuario eliminado: {user_delete}")

    divider()

    # ============================================================
    # PANEL DE AUDITORÍA (LOGS)
    # ============================================================
    st.markdown("## 📜 Panel de auditoría (logs)")

    if os.path.exists("app.log"):
        with open("app.log", "r", encoding="utf-8") as f:
            logs = f.readlines()[-200:]
        st.text("".join(logs))
    else:
        st.info("No hay logs disponibles.")

    card_close()

# ------------------------------------------------------------
# 7) CUENTA
# ------------------------------------------------------------
elif opcion == "👤 Cuenta":
    card_open()
    st.markdown("### 👤 Cuenta de usuario")
    st.write(f"**Usuario:** {st.session_state['username']}")
    st.write(f"**Rol:** {st.session_state['role']}")
    st.write(f"**Sesión iniciada:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.session_state["full_name"] = None
        st.experimental_set_query_params()
        st.stop()

    card_close()

# ============================================================
# FIN DEL ARCHIVO APP.PY COMPLETO
# ============================================================
