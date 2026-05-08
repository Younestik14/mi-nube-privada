# app.py

import streamlit as st
from pathlib import Path

# -----------------------------
# IMPORTACIÓN DE MÓDULOS
# -----------------------------
from modules.db_init import ensure_db_initialized
from auth.login import login_form, logout_button
from auth.security import require_role
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
    # Login centrado arriba
    col_empty, col_center, col_empty2 = st.columns([1, 2, 1])
    with col_center:
        st.markdown("## ⚡ Ingeniería Eléctrica PRO")
        login_form()
    st.stop()


# -----------------------------
# LAYOUT PRINCIPAL
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; margin-bottom: 1rem;">
        <h1 style="margin-bottom:0;">⚡ Ingeniería Eléctrica PRO</h1>
        <p style="opacity:0.8;">Cálculo, presupuesto y memoria REBT en un entorno profesional estilo macOS Sonoma</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Selector central de módulo
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    opcion = st.radio(
        "Selecciona un módulo",
        [
            "🏠 Inicio",
            "📐 Cálculo de secciones",
            "💰 Presupuesto",
            "📘 Memoria REBT",
            "📦 Catálogo",
            "👤 Cuenta",
        ],
        horizontal=True,
    )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# -----------------------------
# 1. INICIO
# -----------------------------
if opcion == "🏠 Inicio":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 👋 Bienvenido")
        st.write(f"Usuario: **{st.session_state['username']}**")
        st.write(f"Rol: **{st.session_state['role']}**")
        st.write("Selecciona un módulo arriba para empezar a trabajar con el proyecto.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 🧩 Módulos disponibles")
        st.markdown("- 📐 Cálculo de secciones y protecciones")
        st.markdown("- 💰 Presupuesto completo con Excel y PDF")
        st.markdown("- 📘 Memoria técnica REBT (Word + PDF)")
        st.markdown("- 📦 Catálogo editable de materiales")
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 2. CÁLCULO DE SECCIONES
# -----------------------------
elif opcion == "📐 Cálculo de secciones":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
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

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 3. PRESUPUESTO
# -----------------------------
elif opcion == "💰 Presupuesto":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 💰 Presupuesto completo")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    if st.button("Calcular presupuesto", use_container_width=True):
        presupuesto = calcular_presupuesto_completo(catalogo, lista_capitulos)

        st.markdown("#### 📊 Capítulos")
        st.dataframe(presupuesto["df"], use_container_width=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("#### 📈 Totales")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Material total:** {presupuesto['totales']['material']:.2f} €")
            st.write(f"**Mano de obra total:** {presupuesto['totales']['mano_obra']:.2f} €")
            st.write(f"**Base capítulos:** {presupuesto['totales']['base']:.2f} €")
        with col2:
            st.write(f"**Base imponible:** {presupuesto['totales']['base_imponible']:.2f} €")
            st.write(f"**IVA total:** {presupuesto['totales']['iva']:.2f} €")
            st.write(f"**TOTAL PRESUPUESTO:** {presupuesto['totales']['total_final']:.2f} €")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Exportación Excel
        excel_bytes = exportar_excel_avanzado(presupuesto, "presupuesto.xlsx")
        st.download_button(
            "📥 Descargar Excel",
            data=excel_bytes,
            file_name="presupuesto.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # Exportación PDF
        pdf_path = "presupuesto.pdf"
        generar_pdf_presupuesto(
            output_path=pdf_path,
            proyecto={"nombre": "Proyecto genérico"},
            presupuesto=presupuesto,
            firma_digital={"nombre": "Técnico", "dni": "00000000X", "cargo": "Instalador autorizado"},
        )
        st.download_button(
            "📄 Descargar PDF",
            data=open(pdf_path, "rb").read(),
            file_name="presupuesto.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 4. MEMORIA REBT
# -----------------------------
elif opcion == "📘 Memoria REBT":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 📘 Generación de Memoria Técnica REBT")

    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del proyecto")
        cliente = st.text_input("Cliente")
    with col2:
        direccion = st.text_input("Dirección")
        tipo = st.text_input("Tipo de instalación", "Instalación eléctrica en vivienda")

    if st.button("Generar memoria", use_container_width=True):
        proyecto = {
            "nombre": nombre,
            "cliente": cliente,
            "direccion": direccion,
            "tipo": tipo,
        }

        # Datos de ejemplo (puedes conectarlos a tus cálculos reales)
        secciones = {
            "C1": {"seccion": 1.5, "descripcion": "Iluminación"},
            "C2": {"seccion": 2.5, "descripcion": "Tomas de corriente"},
        }

        protecciones = {
            "Cuadro general": {"proteccion": "IGA 40A", "intensidad": 40, "descripcion": "Protección general"},
        }

        presupuesto = {
            "capitulos": [
                {"Capítulo": "C1", "Material (€)": 100, "Mano de obra (€)": 80, "Total capítulo (€)": 230},
                {"Capítulo": "C2", "Material (€)": 150, "Mano de obra (€)": 90, "Total capítulo (€)": 290},
            ],
            "total_final": 520,
        }

        firma = {"nombre": "Técnico", "dni": "00000000X", "cargo": "Instalador autorizado"}

        # Word
        word_path = "memoria_rebt.docx"
        generar_memoria_word(word_path, proyecto, secciones, protecciones, presupuesto, firma)

        st.download_button(
            "📘 Descargar Memoria Word",
            data=open(word_path, "rb").read(),
            file_name="memoria_rebt.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

        # PDF
        pdf_path = "memoria_rebt.pdf"
        generar_memoria_pdf(pdf_path, proyecto, presupuesto, firma)

        st.download_button(
            "📄 Descargar Memoria PDF",
            data=open(pdf_path, "rb").read(),
            file_name="memoria_rebt.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 5. CATÁLOGO
# -----------------------------
elif opcion == "📦 Catálogo":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 📦 Catálogo de materiales (solo admin)")
    require_role("admin")
    editor_catalogo_ui()
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 6. CUENTA
# -----------------------------
elif opcion == "👤 Cuenta":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 👤 Cuenta de usuario")
    st.write(f"Usuario: **{st.session_state['username']}**")
    st.write(f"Rol: **{st.session_state['role']}**")
    logout_button()
    st.markdown("</div>", unsafe_allow_html=True)
