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
import pandas as pd

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
# INICIALIZACIÓN ESTADO DE SESIÓN
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
        {"nombre": "Punto de luz", "cantidad": 8, "precio_material": 12.0, "precio_mano_obra": 8.0, "rendimiento_h": 0.30},
        {"nombre": "Interruptor", "cantidad": 8, "precio_material": 6.0, "precio_mano_obra": 4.0, "rendimiento_h": 0.20},
    ],
    "C2 - Tomas de corriente": [
        {"nombre": "Toma de corriente", "cantidad": 10, "precio_material": 9.0, "precio_mano_obra": 6.0, "rendimiento_h": 0.25},
    ],
    "C3 - Cocina y horno": [
        {"nombre": "Toma especial cocina", "cantidad": 2, "precio_material": 18.0, "precio_mano_obra": 10.0, "rendimiento_h": 0.40},
    ],
    "C4 - Lavadora, lavavajillas": [
        {"nombre": "Toma especial", "cantidad": 2, "precio_material": 15.0, "precio_mano_obra": 9.0, "rendimiento_h": 0.35},
    ],
    "C5 - Baños": [
        {"nombre": "Toma baño", "cantidad": 2, "precio_material": 12.0, "precio_mano_obra": 8.0, "rendimiento_h": 0.30},
    ],
    "C6 - Climatización": [
        {"nombre": "Línea aire acondicionado", "cantidad": 1, "precio_material": 40.0, "precio_mano_obra": 20.0, "rendimiento_h": 1.50},
    ],
    "C7 - Calefacción": [
        {"nombre": "Línea calefacción", "cantidad": 1, "precio_material": 35.0, "precio_mano_obra": 18.0, "rendimiento_h": 1.20},
    ],
    "C8 - Termo eléctrico": [
        {"nombre": "Línea termo", "cantidad": 1, "precio_material": 22.0, "precio_mano_obra": 12.0, "rendimiento_h": 0.80},
    ],
    "C9 - Automatización": [
        {"nombre": "Actuador domótico", "cantidad": 4, "precio_material": 30.0, "precio_mano_obra": 15.0, "rendimiento_h": 0.50},
    ],
    "C10 - Telecomunicaciones": [
        {"nombre": "Toma RJ45", "cantidad": 4, "precio_material": 14.0, "precio_mano_obra": 8.0, "rendimiento_h": 0.30},
    ],
    "C11 - Seguridad": [
        {"nombre": "Detector de presencia", "cantidad": 2, "precio_material": 25.0, "precio_mano_obra": 12.0, "rendimiento_h": 0.40},
    ],
    "C12 - Cuadro eléctrico": [
        {"nombre": "ICP + IGA + ID + PIA", "cantidad": 1, "precio_material": 120.0, "precio_mano_obra": 40.0, "rendimiento_h": 4.00},
    ],
    "C13 - Derivación individual": [
        {"nombre": "Cableado DI", "cantidad": 1, "precio_material": 80.0, "precio_mano_obra": 30.0, "rendimiento_h": 2.00},
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
# CÁLCULO DE SECCIONES PROFESIONAL REBT / UNE 20460-5-523
# ============================================================

METODOS_INSTALACION = {
    "A1": "Cable unipolar en tubo empotrado en pared aislante",
    "A2": "Cable multipolar en tubo empotrado en pared aislante",
    "B1": "Cable unipolar en bandeja perforada",
    "B2": "Cable multipolar en bandeja perforada",
    "C":  "Cable sobre pared",
    "D1": "Cable enterrado directamente",
    "D2": "Cable enterrado en tubo",
    "E":  "Cable en canal protectora",
    "F1": "Cable en bandeja cerrada",
    "F2": "Cable en bandeja ventilada",
}

TIPO_CABLE = ["PVC", "XLPE", "EPR"]

INT_ADM = {
    "PVC": {
        "A1": {1.5: 14, 2.5: 18, 4: 24, 6: 31, 10: 43, 16: 57, 25: 76},
        "A2": {1.5: 16, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89},
        "B1": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101},
        "B2": {1.5: 20, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 113},
        "C":  {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101},
        "D1": {1.5: 20, 2.5: 25, 4: 33, 6: 42, 10: 57, 16: 76, 25: 99},
        "D2": {1.5: 19, 2.5: 24, 4: 32, 6: 41, 10: 55, 16: 73, 25: 96},
        "E":  {1.5: 17, 2.5: 22, 4: 30, 6: 39, 10: 54, 16: 72, 25: 95},
        "F1": {1.5: 16, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89},
        "F2": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101},
    },
    "XLPE": {
        "A1": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101},
        "A2": {1.5: 20, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 113},
        "B1": {1.5: 21, 2.5: 28, 4: 37, 6: 48, 10: 66, 16: 88, 25: 117},
        "B2": {1.5: 23, 2.5: 30, 4: 40, 6: 52, 10: 72, 16: 96, 25: 127},
        "C":  {1.5: 21, 2.5: 28, 4: 37, 6: 48, 10: 66, 16: 88, 25: 117},
        "D1": {1.5: 23, 2.5: 29, 4: 38, 6: 49, 10: 67, 16: 89, 25: 118},
        "D2": {1.5: 22, 2.5: 28, 4: 37, 6: 48, 10: 65, 16: 87, 25: 116},
        "E":  {1.5: 20, 2.5: 26, 4: 35, 6: 45, 10: 62, 16: 83, 25: 111},
        "F1": {1.5: 20, 2.5: 26, 4: 35, 6: 45, 10: 62, 16: 83, 25: 111},
        "F2": {1.5: 21, 2.5: 28, 4: 37, 6: 48, 10: 66, 16: 88, 25: 117},
    },
    "EPR": {
        "A1": {1.5: 19, 2.5: 25, 4: 34, 6: 44, 10: 60, 16: 80, 25: 106},
        "A2": {1.5: 21, 2.5: 28, 4: 38, 6: 49, 10: 67, 16: 89, 25: 118},
        "B1": {1.5: 22, 2.5: 29, 4: 39, 6: 51, 10: 70, 16: 93, 25: 123},
        "B2": {1.5: 24, 2.5: 31, 4: 42, 6: 54, 10: 74, 16: 98, 25: 130},
        "C":  {1.5: 22, 2.5: 29, 4: 39, 6: 51, 10: 70, 16: 93, 25: 123},
        "D1": {1.5: 24, 2.5: 30, 4: 40, 6: 52, 10: 71, 16: 94, 25: 125},
        "D2": {1.5: 23, 2.5: 29, 4: 39, 6: 51, 10: 69, 16: 92, 25: 122},
        "E":  {1.5: 21, 2.5: 27, 4: 37, 6: 48, 10: 66, 16: 88, 25: 117},
        "F1": {1.5: 21, 2.5: 27, 4: 37, 6: 48, 10: 66, 16: 88, 25: 117},
        "F2": {1.5: 22, 2.5: 29, 4: 39, 6: 51, 10: 70, 16: 93, 25: 123},
    },
}

SECCIONES_DISPONIBLES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50]

COEF_TEMPERATURA = {
    10: 1.22, 15: 1.17, 20: 1.12, 25: 1.08, 30: 1.00,
    35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50,
}

COEF_AGRUPAMIENTO = {
    1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60,
    6: 0.57, 7: 0.54, 8: 0.52, 9: 0.50, 10: 0.48,
}

COEF_CONDUCTORES_CARGADOS = {
    2: 1.00,
    3: 0.90,
    4: 0.80,
    5: 0.75,
    6: 0.72,
}

COEF_RESISTIVIDAD_TERRENO = {
    1.0: 1.00,
    1.2: 0.96,
    1.5: 0.90,
    2.0: 0.84,
    2.5: 0.80,
}

COEF_PROFUNDIDAD = {
    0.7: 1.00,
    1.0: 0.96,
    1.2: 0.93,
}

COEF_BANDEJA = {
    "Perforada": 1.00,
    "Ventilada": 0.95,
    "Cerrada": 0.90,
}

def intensidad_por_potencia(potencia_w, cosfi=0.95, tension=230):
    return potencia_w / (tension * cosfi)

def intensidad_admisible_base(tipo_cable, metodo, seccion):
    return INT_ADM[tipo_cable][metodo][seccion]

def aplicar_coeficientes(Iadm, factores):
    coef_total = 1.0
    for f in factores:
        coef_total *= f
    return Iadm * coef_total

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

def seleccionar_seccion_por_intensidad(I, tipo_cable, metodo, factores):
    for s in SECCIONES_DISPONIBLES:
        if s not in INT_ADM[tipo_cable][metodo]:
            continue
        Iadm_base = intensidad_admisible_base(tipo_cable, metodo, s)
        Iadm_corr = aplicar_coeficientes(Iadm_base, factores)
        if Iadm_corr >= I:
            return s, Iadm_base, Iadm_corr
    s = SECCIONES_DISPONIBLES[-1]
    Iadm_base = intensidad_admisible_base(tipo_cable, metodo, SECCIONES_DISPONIBLES[-2])
    Iadm_corr = aplicar_coeficientes(Iadm_base, factores)
    return s, Iadm_base, Iadm_corr

def caida_tension_por_seccion(I, L, S, tension=230):
    r = 0.0225 / S
    return (math.sqrt(3) * I * r * L / tension) * 100

def seleccionar_seccion_por_caida(I, L, caida_max, tipo_cable, metodo, factores):
    for s in SECCIONES_DISPONIBLES:
        caida = caida_tension_por_seccion(I, L, s)
        Iadm_base = intensidad_admisible_base(tipo_cable, metodo, s)
        Iadm_corr = aplicar_coeficientes(Iadm_base, factores)
        if caida <= caida_max and Iadm_corr >= I:
            return s, caida
    s = SECCIONES_DISPONIBLES[-1]
    caida = caida_tension_por_seccion(I, L, s)
    return s, caida

def calcular_linea_profesional(
    nombre,
    potencia,
    longitud,
    metodo,
    tipo_cable,
    n_circuitos,
    n_conductores_cargados,
    temperatura,
    resistividad_terreno,
    profundidad,
    tipo_bandeja,
    usar_intensidad,
    usar_caida,
    caida_max
):
    I = intensidad_por_potencia(potencia)

    factores = []
    factores.append(COEF_TEMPERATURA[temperatura])
    factores.append(COEF_AGRUPAMIENTO[n_circuitos])
    factores.append(COEF_CONDUCTORES_CARGADOS[n_conductores_cargados])

    if metodo in ["D1", "D2"]:
        factores.append(COEF_RESISTIVIDAD_TERRENO[resistividad_terreno])
        factores.append(COEF_PROFUNDIDAD[profundidad])

    if metodo in ["B1", "B2", "F1", "F2"]:
        factores.append(COEF_BANDEJA[tipo_bandeja])

    resultados = {}

    if usar_intensidad:
        S_int, Iadm_base, Iadm_corr = seleccionar_seccion_por_intensidad(
            I, tipo_cable, metodo, factores
        )
        resultados["por_intensidad"] = {
            "seccion": S_int,
            "Iadm_base": Iadm_base,
            "Iadm_corr": Iadm_corr,
        }
    else:
        S_int = None

    if usar_caida:
        S_caida, caida = seleccionar_seccion_por_caida(
            I, longitud, caida_max, tipo_cable, metodo, factores
        )
        resultados["por_caida"] = {
            "seccion": S_caida,
            "caida": caida,
        }
    else:
        S_caida = None

    secciones_validas = [s for s in [S_int, S_caida] if s is not None]
    S_final = max(secciones_validas) if secciones_validas else None

    magneto = seleccionar_magnetotermico(I)
    diferencial = seleccionar_diferencial(I)

    return {
        "nombre": nombre,
        "intensidad_calculada_A": I,
        "seccion_final_mm2": S_final,
        "metodo": metodo,
        "descripcion_metodo": METODOS_INSTALACION[metodo],
        "tipo_cable": tipo_cable,
        "factores": {
            "temperatura": COEF_TEMPERATURA[temperatura],
            "agrupamiento": COEF_AGRUPAMIENTO[n_circuitos],
            "conductores_cargados": COEF_CONDUCTORES_CARGADOS[n_conductores_cargados],
            "resistividad_terreno": COEF_RESISTIVIDAD_TERRENO.get(resistividad_terreno, 1.0),
            "profundidad": COEF_PROFUNDIDAD.get(profundidad, 1.0),
            "bandeja": COEF_BANDEJA.get(tipo_bandeja, 1.0),
        },
        "criterios": resultados,
        "protecciones": {
            "magnetotermico": magneto,
            "diferencial": diferencial,
        },
    }

# ============================================================
# PRESUPUESTO HIPER‑DETALLADO CON PARÁMETROS CONFIGURABLES
# ============================================================

def calcular_capitulo_detallado(
    nombre_capitulo,
    productos,
    coste_hora_mo=25.0,
    pct_gastos=0.15,
    pct_seg=0.02,
    pct_amort=0.03,
    pct_benef=0.06,
    pct_iva=0.21,
):
    detalle = []
    total_material = 0.0
    total_mano_obra = 0.0

    for p in productos:
        cant = float(p.get("cantidad", 0) or 0)
        pm = float(p.get("precio_material", 0) or 0)
        rend = float(p.get("rendimiento_h", 0) or 0)

        coste_mat = cant * pm
        horas = cant * rend
        coste_mo = horas * coste_hora_mo

        total_material += coste_mat
        total_mano_obra += coste_mo

        detalle.append({
            "Capítulo": nombre_capitulo,
            "Descripción": p.get("nombre", ""),
            "Cantidad": cant,
            "Precio material unitario (€)": pm,
            "Coste material (€)": coste_mat,
            "Rendimiento (h/u)": rend,
            "Horas totales": horas,
            "Coste mano de obra (€)": coste_mo,
        })

    base_directa = total_material + total_mano_obra
    gastos_generales = base_directa * pct_gastos
    seguridad_salud = base_directa * pct_seg
    amortizacion = base_directa * pct_amort
    indirectos = gastos_generales + seguridad_salud + amortizacion
    beneficio = base_directa * pct_benef
    base_imponible = base_directa + indirectos + beneficio
    iva = base_imponible * pct_iva
    total_capitulo = base_imponible + iva

    resumen = {
        "Capítulo": nombre_capitulo,
        "Material (€)": total_material,
        "Mano de obra (€)": total_mano_obra,
        "Base directa (€)": base_directa,
        "Gastos generales (€)": gastos_generales,
        "Seguridad y salud (€)": seguridad_salud,
        "Amortización (€)": amortizacion,
        "Indirectos totales (€)": indirectos,
        "Beneficio (€)": beneficio,
        "Base imponible (€)": base_imponible,
        "IVA (€)": iva,
        "Total capítulo (€)": total_capitulo,
    }

    return resumen, detalle

def calcular_presupuesto_detallado(
    catalogo,
    lista_capitulos,
    coste_hora_mo=25.0,
    pct_gastos=0.15,
    pct_seg=0.02,
    pct_amort=0.03,
    pct_benef=0.06,
    pct_iva=0.21,
):
    capitulos_resumen = []
    lineas_detalle = []

    for cap in lista_capitulos:
        resumen, detalle = calcular_capitulo_detallado(
            cap,
            catalogo.get(cap, []),
            coste_hora_mo,
            pct_gastos,
            pct_seg,
            pct_amort,
            pct_benef,
            pct_iva,
        )
        capitulos_resumen.append(resumen)
        lineas_detalle.extend(detalle)

    totales = {
        "material": sum(c["Material (€)"] for c in capitulos_resumen),
        "mano_obra": sum(c["Mano de obra (€)"] for c in capitulos_resumen),
        "base_directa": sum(c["Base directa (€)"] for c in capitulos_resumen),
        "gastos_generales": sum(c["Gastos generales (€)"] for c in capitulos_resumen),
        "seguridad_salud": sum(c["Seguridad y salud (€)"] for c in capitulos_resumen),
        "amortizacion": sum(c["Amortización (€)"] for c in capitulos_resumen),
        "indirectos": sum(c["Indirectos totales (€)"] for c in capitulos_resumen),
        "beneficio": sum(c["Beneficio (€)"] for c in capitulos_resumen),
        "base_imponible": sum(c["Base imponible (€)"] for c in capitulos_resumen),
        "iva": sum(c["IVA (€)"] for c in capitulos_resumen),
        "total_final": sum(c["Total capítulo (€)"] for c in capitulos_resumen),
    }

    return {
        "capitulos": capitulos_resumen,
        "detalle": lineas_detalle,
        "totales": totales,
    }

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

    if "total_final" in presupuesto.get("totales", {}):
        doc.add_paragraph(f"TOTAL: {presupuesto['totales']['total_final']} €")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# MENÚ PRINCIPAL
# ============================================================

titulo_centrado(
    "⚡ Ingeniería Eléctrica PRO",
    "Cálculo profesional, presupuesto hiper‑detallado y memoria REBT — Estética macOS Sonoma"
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

# 1) INICIO
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
        st.markdown("- 📐 Cálculo de secciones profesional REBT / UNE")
        st.markdown("- 💰 Presupuesto hiper‑detallado con rendimientos y parámetros configurables")
        st.markdown("- 📘 Memoria técnica REBT (Word + PDF)")
        st.markdown("- 📦 Catálogo editable de materiales")
        st.markdown("- 👥 Administración avanzada de usuarios")
        card_close()

# 2) CÁLCULO DE SECCIONES PROFESIONAL (ESTILO TABLA TÉCNICA + LaTeX)
elif opcion == "📐 Cálculo de secciones":
    card_open()
    st.markdown("### 📐 Cálculo de secciones — Modo INGENIERÍA COMPLETA REBT / UNE")

    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre de la línea", "C1 - Iluminación")
        potencia = st.number_input("Potencia (W)", min_value=100.0, value=2000.0)
        longitud = st.number_input("Longitud (m)", min_value=1.0, value=15.0)
    with col2:
        metodo = st.selectbox("Método instalación (ITC‑BT‑19)", list(METODOS_INSTALACION.keys()))
        tipo_cable = st.selectbox("Tipo de cable", TIPO_CABLE)
        n_conductores_cargados = st.selectbox("Nº conductores cargados", [2,3,4,5,6])
    with col3:
        n_circuitos = st.selectbox("Nº de circuitos agrupados", list(COEF_AGRUPAMIENTO.keys()))
        temperatura = st.selectbox("Temperatura ambiente (°C)", list(COEF_TEMPERATURA.keys()))
        caida_max = st.number_input("Caída máxima permitida (%)", min_value=1.0, max_value=10.0, value=3.0)

    col4, col5, col6 = st.columns(3)
    with col4:
        resistividad_terreno = st.selectbox("Resistividad térmica terreno (K·m/W)", [1.0,1.2,1.5,2.0,2.5])
    with col5:
        profundidad = st.selectbox("Profundidad enterrado (m)", [0.7,1.0,1.2])
    with col6:
        tipo_bandeja = st.selectbox("Tipo de bandeja", ["Perforada","Ventilada","Cerrada"])

    divider()
    st.markdown("#### 🎛 Criterios de cálculo (modo asistido)")

    colA, colB = st.columns(2)
    with colA:
        usar_intensidad = st.checkbox("Aplicar criterio por intensidad admisible", value=True)
    with colB:
        usar_caida = st.checkbox("Aplicar criterio por caída de tensión", value=True)

    if st.button("Calcular sección profesional", use_container_width=True):
        datos = calcular_linea_profesional(
            nombre=nombre,
            potencia=potencia,
            longitud=longitud,
            metodo=metodo,
            tipo_cable=tipo_cable,
            n_circuitos=n_circuitos,
            n_conductores_cargados=n_conductores_cargados,
            temperatura=temperatura,
            resistividad_terreno=resistividad_terreno,
            profundidad=profundidad,
            tipo_bandeja=tipo_bandeja,
            usar_intensidad=usar_intensidad,
            usar_caida=usar_caida,
            caida_max=caida_max,
        )

        divider()
        st.markdown("### 🟦 Sección final tomada")
        st.markdown(
            f"<h2 style='margin-top:0;'>Sección final: {datos['seccion_final_mm2']} mm²</h2>",
            unsafe_allow_html=True
        )

        criterios = datos["criterios"]
        fila_int = criterios.get("por_intensidad", {})
        fila_caida = criterios.get("por_caida", {})

        tabla = [
            {"Parámetro": "Intensidad calculada", "Valor": f"{datos['intensidad_calculada_A']:.2f} A"},
            {"Parámetro": "Método", "Valor": f"{datos['metodo']} — {datos['descripcion_metodo']}"},
            {"Parámetro": "Tipo de cable", "Valor": datos["tipo_cable"]},
        ]

        if fila_int:
            tabla.extend([
                {"Parámetro": "Iadm base", "Valor": f"{fila_int['Iadm_base']:.2f} A"},
                {"Parámetro": "Iadm corregida", "Valor": f"{fila_int['Iadm_corr']:.2f} A"},
                {"Parámetro": "Sección por intensidad", "Valor": f"{fila_int['seccion']} mm²"},
            ])

        if fila_caida:
            tabla.extend([
                {"Parámetro": "Caída de tensión", "Valor": f"{fila_caida['caida']:.2f} %"},
                {"Parámetro": "Sección por caída", "Valor": f"{fila_caida['seccion']} mm²"},
            ])

        tabla.append({"Parámetro": "Sección final tomada", "Valor": f"{datos['seccion_final_mm2']} mm²"})

        st.markdown("#### 📊 Tabla técnica del cálculo")
        st.table(pd.DataFrame(tabla))

        divider()
        st.markdown("#### 🔌 Protecciones recomendadas")
        st.write(f"**Magnetotérmico:** {datos['protecciones']['magnetotermico']}")
        st.write(f"**Diferencial:** {datos['protecciones']['diferencial']}")

        divider()
        st.markdown("#### 📐 Fórmulas utilizadas")

        st.latex(r"I = \frac{P}{V \cdot \cos\varphi}")
        st.latex(r"\Delta V\% = \frac{\sqrt{3} \cdot I \cdot R \cdot L}{V} \cdot 100")

    card_close()

# 3) PRESUPUESTO HIPER‑DETALLADO (PARÁMETROS CONFIGURABLES)
elif opcion == "💰 Presupuesto":
    card_open()
    st.markdown("### 💰 Presupuesto hiper‑detallado con rendimientos")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    coste_hora_mo = st.number_input("Coste hora mano de obra (€ / h)", min_value=10.0, max_value=100.0, value=25.0)

    colp1, colp2, colp3 = st.columns(3)
    with colp1:
        pct_gastos = st.number_input("Gastos generales (%)", min_value=0.0, max_value=50.0, value=15.0)
        pct_seg = st.number_input("Seguridad y salud (%)", min_value=0.0, max_value=20.0, value=2.0)
    with colp2:
        pct_amort = st.number_input("Amortización (%)", min_value=0.0, max_value=20.0, value=3.0)
        pct_benef = st.number_input("Beneficio (%)", min_value=0.0, max_value=30.0, value=6.0)
    with colp3:
        pct_iva = st.number_input("IVA (%)", min_value=0.0, max_value=30.0, value=21.0)

    st.markdown("#### ✏️ Edición de capítulos y productos")

    cap_sel = st.selectbox("Capítulo a editar", lista_capitulos)
    productos = catalogo[cap_sel]

    st.info("Puedes editar todos los campos y añadir nuevas filas en el editor.")

    df = pd.DataFrame(productos)
    if "rendimiento_h" not in df.columns:
        df["rendimiento_h"] = 0.25

    df_edit = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{cap_sel}",
    )

    if st.button("Guardar capítulo editado", use_container_width=True):
        catalogo[cap_sel] = df_edit.to_dict(orient="records")
        guardar_catalogo(catalogo)
        st.success("Capítulo actualizado en el catálogo.")

    divider()

    if st.button("Calcular presupuesto detallado", use_container_width=True):
        presupuesto = calcular_presupuesto_detallado(
            catalogo,
            lista_capitulos,
            coste_hora_mo,
            pct_gastos/100.0,
            pct_seg/100.0,
            pct_amort/100.0,
            pct_benef/100.0,
            pct_iva/100.0,
        )

        st.markdown("#### 📊 Resumen por capítulos")
        st.dataframe(presupuesto["capitulos"], use_container_width=True)

        divider()
        st.markdown("#### 📋 Detalle línea a línea")
        st.dataframe(presupuesto["detalle"], use_container_width=True)

        divider()
        st.markdown("#### 📈 Totales globales")

        tot = presupuesto["totales"]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Material total:** {tot['material']:.2f} €")
            st.write(f"**Mano de obra total:** {tot['mano_obra']:.2f} €")
            st.write(f"**Base directa:** {tot['base_directa']:.2f} €")
            st.write(f"**Gastos generales:** {tot['gastos_generales']:.2f} €")
            st.write(f"**Seguridad y salud:** {tot['seguridad_salud']:.2f} €")
            st.write(f"**Amortización:** {tot['amortizacion']:.2f} €")
        with col2:
            st.write(f"**Indirectos totales:** {tot['indirectos']:.2f} €")
            st.write(f"**Beneficio:** {tot['beneficio']:.2f} €")
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

# 4) MEMORIA REBT
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

        presupuesto_demo = {
            "capitulos": [
                {"Capítulo": "C1", "Total capítulo (€)": 230},
                {"Capítulo": "C2", "Total capítulo (€)": 290},
            ],
            "totales": {"total_final": 520},
        }

        word_bytes = generar_memoria_word(proyecto, secciones, protecciones, presupuesto_demo)
        st.download_button(
            "📘 Descargar Memoria Word",
            data=word_bytes,
            file_name="memoria_rebt.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

        pdf_bytes = generar_pdf_presupuesto(proyecto, presupuesto_demo)
        st.download_button(
            "📄 Descargar Memoria PDF",
            data=pdf_bytes,
            file_name="memoria_rebt.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    card_close()

# 5) CATÁLOGO (ADMIN PUEDE AÑADIR / CAMBIAR PRODUCTOS Y CAPÍTULOS)
elif opcion == "📦 Catálogo":
    require_role("admin")
    card_open()
    st.markdown("### 📦 Catálogo de materiales (solo admin)")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    st.markdown("#### ➕ Añadir nuevo capítulo")
    nuevo_cap = st.text_input("Nombre del nuevo capítulo")
    if st.button("Crear capítulo", use_container_width=True):
        if nuevo_cap and nuevo_cap not in catalogo:
            catalogo[nuevo_cap] = []
            guardar_catalogo(catalogo)
            st.success(f"Capítulo '{nuevo_cap}' creado.")
        else:
            st.error("Nombre vacío o capítulo ya existente.")

    divider()

    capitulo = st.selectbox("Selecciona un capítulo", list(catalogo.keys()))
    productos = catalogo[capitulo]

    st.markdown("#### ✏️ Productos del capítulo (editor dinámico)")
    df = pd.DataFrame(productos) if productos else pd.DataFrame(
        columns=["nombre", "cantidad", "precio_material", "precio_mano_obra", "rendimiento_h"]
    )

    df_edit = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"catalogo_{capitulo}",
    )

    colc1, colc2 = st.columns(2)
    with colc1:
        if st.button("Guardar cambios en capítulo", use_container_width=True):
            catalogo[capitulo] = df_edit.to_dict(orient="records")
            guardar_catalogo(catalogo)
            st.success("Capítulo actualizado correctamente.")
    with colc2:
        if st.button("Borrar capítulo seleccionado", use_container_width=True):
            if capitulo == "C12 - Cuadro eléctrico" or capitulo == "C13 - Derivación individual":
                st.warning("Mejor no borrar capítulos críticos del ejemplo base.")
            else:
                del catalogo[capitulo]
                guardar_catalogo(catalogo)
                st.success(f"Capítulo '{capitulo}' eliminado.")

    card_close()

# 6) ADMINISTRACIÓN AVANZADA
elif opcion == "👥 Administración":
    require_role("admin")
    card_open()
    st.markdown("### 👥 Administración avanzada de usuarios")

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

    st.markdown("## 📜 Panel de auditoría (logs)")

    if os.path.exists("app.log"):
        with open("app.log", "r", encoding="utf-8") as f:
            logs = f.readlines()[-200:]
        st.text("".join(logs))
    else:
        st.info("No hay logs disponibles.")

    card_close()

# 7) CUENTA
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
