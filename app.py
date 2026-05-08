# ============================================================
# app.py — Archivo único, completo y autocontenido
# Ingeniería Eléctrica PRO — Estilo macOS Sonoma
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
# CSS SONOMA EMBEBIDO
# ============================================================

st.markdown("""
<style>

html, body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
    background: var(--bg);
    color: var(--text);
    transition: background 0.3s ease, color 0.3s ease;
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
# BASE DE DATOS SQLITE (AUTOGENERADA)
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

        # Crear usuario admin por defecto
        admin_pass = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", admin_pass, "Administrador", "admin", datetime.now().isoformat()))
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
# LOGIN UI
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
            st.session_state["just_logged_in"] = True
        else:
            st.error("Usuario o contraseña incorrectos")

    card_close()

if not st.session_state["logged_in"]:
    login_ui()
    st.stop()
# Refresco seguro después del login
if st.session_state.get("just_logged_in"):
    st.session_state["just_logged_in"] = False
    st.experimental_set_query_params(refresh="1")


# ============================================================
# CATÁLOGO EMBEBIDO (AUTOGENERADO)
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
# FIN BLOQUE 1/3
# ============================================================
# ============================================================
# CÁLCULO DE SECCIONES Y PROTECCIONES
# ============================================================

RESISTIVIDAD_CU = 0.0225  # ohm·mm²/m
COSFI = 0.95
V = 230  # tensión monofásica

def intensidad_por_potencia(potencia_w):
    return potencia_w / (V * COSFI)

def caida_tension(intensidad, longitud_m, seccion_mm2):
    r = RESISTIVIDAD_CU / seccion_mm2
    caida_v = math.sqrt(3) * intensidad * r * longitud_m
    return (caida_v / V) * 100

def seleccionar_seccion(intensidad):
    if intensidad <= 10: return 1.5
    if intensidad <= 16: return 2.5
    if intensidad <= 20: return 4
    if intensidad <= 25: return 6
    if intensidad <= 32: return 10
    if intensidad <= 40: return 16
    if intensidad <= 63: return 25
    return 35

def seleccionar_magnetotermico(intensidad):
    if intensidad <= 10: return "10 A"
    if intensidad <= 16: return "16 A"
    if intensidad <= 20: return "20 A"
    if intensidad <= 25: return "25 A"
    if intensidad <= 32: return "32 A"
    if intensidad <= 40: return "40 A"
    if intensidad <= 50: return "50 A"
    return "63 A"

def seleccionar_diferencial(intensidad):
    if intensidad <= 25: return "30 mA — 25 A"
    if intensidad <= 40: return "30 mA — 40 A"
    return "30 mA — 63 A"

def calcular_linea(nombre, potencia_w, longitud_m):
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


# ============================================================
# PRESUPUESTO COMPLETO
# ============================================================

def calcular_capitulo(nombre_capitulo, catalogo):
    productos = catalogo.get(nombre_capitulo, [])
    total_material = sum(p["precio_material"] * p["cantidad"] for p in productos)
    total_mano_obra = sum(p["precio_mano_obra"] * p["cantidad"] for p in productos)

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

def calcular_presupuesto_completo(catalogo, lista_capitulos):
    resultados = [calcular_capitulo(cap, catalogo) for cap in lista_capitulos]

    totales = {
        "material": sum(r["Material (€)"] for r in resultados),
        "mano_obra": sum(r["Mano de obra (€)"] for r in resultados),
        "base": sum(r["Base capítulo (€)"] for r in resultados),
        "gastos": sum(r["Gastos generales (€)"] for r in resultados),
        "beneficio": sum(r["Beneficio (€)"] for r in resultados),
        "base_imponible": sum(r["Base imponible (€)"] for r in resultados),
        "iva": sum(r["IVA (€)"] for r in resultados),
        "total_final": sum(r["Total capítulo (€)"] for r in resultados),
    }

    return {"capitulos": resultados, "totales": totales}


# ============================================================
# GENERADOR PDF PRESUPUESTO
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

    doc.add_paragraph(f"TOTAL: {presupuesto['total_final']} €")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    titulo_centrado("⚡ Ingeniería Eléctrica PRO", "Acceso técnico profesional")
    login_ui()
    st.stop()

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
# MÓDULOS DE INTERFAZ — PANTALLAS COMPLETAS
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
        st.markdown("- 📐 Cálculo de secciones y protecciones")
        st.markdown("- 💰 Presupuesto completo con Excel y PDF")
        st.markdown("- 📘 Memoria técnica REBT (Word + PDF)")
        st.markdown("- 📦 Catálogo editable de materiales")
        st.markdown("- 👥 Administración de usuarios (solo admin)")
        card_close()


# ------------------------------------------------------------
# 2) CÁLCULO DE SECCIONES
# ------------------------------------------------------------
elif opcion == "📐 Cálculo de secciones":
    card_open()
    st.markdown("### 📐 Cálculo de secciones y protecciones")

    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre de la línea", "C1 - Iluminación")
    with col2:
        potencia = st.number_input("Potencia (W)", min_value=100, value=2000)
    with col3:
        longitud = st.number_input("Longitud (m)", min_value=1, value=15)

    if st.button("Calcular línea", use_container_width=True):
        datos = calcular_linea(nombre, potencia, longitud)

        divider()
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### Resultado numérico")
            st.json(datos)

        with c2:
            st.markdown("#### Resumen técnico")
            st.write(
                f"- Intensidad: **{datos['intensidad']:.2f} A**\n"
                f"- Sección: **{datos['seccion']} mm²**\n"
                f"- Caída de tensión: **{datos['caida']:.2f} %**\n"
                f"- Magnetotérmico: **{datos['magnetotermico']}**\n"
                f"- Diferencial: **{datos['diferencial']}**"
            )

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

        col_e1, col_e2 = st.columns(2)

        with col_e1:
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

        with col_e2:
            st.info("Exportación Excel no incluida en este archivo único.")

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

        # Word
        word_bytes = generar_memoria_word(proyecto, secciones, protecciones, presupuesto)
        st.download_button(
            "📘 Descargar Memoria Word",
            data=word_bytes,
            file_name="memoria_rebt.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

        # PDF
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
# 6) ADMINISTRACIÓN
# ------------------------------------------------------------
elif opcion == "👥 Administración":
    require_role("admin")
    card_open()
    st.markdown("### 👥 Administración de usuarios")

    st.info("Gestión de usuarios no incluida en este archivo único para simplificar.")

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
        st.session_state.clear()
        st.experimental_rerun()

    card_close()


# ============================================================
# FIN DEL ARCHIVO APP.PY COMPLETO
# ============================================================
