# app.py
# Aplicación profesional de ingeniería eléctrica
# - Login + roles (SQLite)
# - Cálculo de secciones
# - Presupuesto C1–C13
# - Memoria REBT (Word + PDF)
# - PDF de presupuesto (ReportLab)
# - Catálogo editable (JSON)
# - Estilo macOS Sonoma (static/sonoma.css)

import streamlit as st
from pathlib import Path
from datetime import datetime

# -----------------------------
# IMPORTACIÓN DE MÓDULOS LOCALES
# -----------------------------
from modules.db_init import ensure_db_initialized
from auth.login import login_form, logout_button
from auth.security import require_role, create_user, list_users, delete_user
from modules.catalogo import cargar_catalogo, editor_catalogo_ui
from modules.presupuesto import calcular_presupuesto_completo, exportar_excel_avanzado
from modules.secciones import (
    calcular_linea,
    calcular_derivacion_individual,
    intensidad_por_potencia,
    caida_tension,
)
from modules.memoria_rebt import generar_memoria_word, generar_memoria_pdf
from modules.pdf_generator import generar_pdf_presupuesto


# =========================================================
# CONFIGURACIÓN GLOBAL
# =========================================================

st.set_page_config(
    page_title="Ingeniería Eléctrica PRO",
    page_icon="⚡",
    layout="wide",
)

# Cargar CSS Sonoma
css_path = Path("static/sonoma.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Inicializar base de datos
ensure_db_initialized()


# =========================================================
# UTILIDADES DE INTERFAZ
# =========================================================

def card_open():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def divider():
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


def titulo_centrado(titulo: str, subtitulo: str = ""):
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom: 1.5rem;">
            <h1 style="margin-bottom:0;">{titulo}</h1>
            <p style="opacity:0.8; margin-top:0.3rem;">{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# LOGIN
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # Login centrado en la parte superior
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        titulo_centrado("⚡ Ingeniería Eléctrica PRO", "Acceso técnico profesional")
        card_open()
        login_form()
        card_close()
    st.stop()


# =========================================================
# CABECERA PRINCIPAL
# =========================================================

titulo_centrado(
    "⚡ Ingeniería Eléctrica PRO",
    "Cálculo, presupuesto y memoria REBT con estética macOS Sonoma",
)

# Selector central de módulo
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


# =========================================================
# MÓDULO: INICIO
# =========================================================

if opcion == "🏠 Inicio":
    col1, col2 = st.columns(2)

    with col1:
        card_open()
        st.markdown("### 👋 Bienvenido")
        st.write(f"**Usuario:** {st.session_state['username']}")
        st.write(f"**Rol:** {st.session_state['role']}")
        st.write(
            "Esta herramienta integra cálculo de secciones, presupuesto completo, "
            "memoria técnica REBT y exportación profesional (PDF, Word, Excel)."
        )
        card_close()

    with col2:
        card_open()
        st.markdown("### 🧩 Módulos disponibles")
        st.markdown("- 📐 Cálculo de secciones y protecciones")
        st.markdown("- 💰 Presupuesto C1–C13 con Excel y PDF")
        st.markdown("- 📘 Memoria técnica REBT (Word + PDF)")
        st.markmarkdown("- 📦 Catálogo editable de materiales")
        st.markdown("- 👥 Administración de usuarios (solo admin)")
        card_close()


# =========================================================
# MÓDULO: CÁLCULO DE SECCIONES
# =========================================================

elif opcion == "📐 Cálculo de secciones":
    card_open()
    st.markdown("### 📐 Cálculo de secciones y protecciones")

    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre de la línea", "C1 - Iluminación")
    with col2:
        potencia = st.number_input("Potencia (W)", min_value=100, value=2000, step=100)
    with col3:
        longitud = st.number_input("Longitud (m)", min_value=1, value=15, step=1)

    col4, col5 = st.columns(2)
    with col4:
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

    with col5:
        st.markdown("#### Cálculo rápido de caída de tensión")
        pot_quick = st.number_input("Potencia rápida (W)", min_value=100, value=3000, key="pot_quick")
        long_quick = st.number_input("Longitud rápida (m)", min_value=1, value=20, key="long_quick")
        sec_quick = st.number_input("Sección rápida (mm²)", min_value=1.5, value=4.0, step=0.5, key="sec_quick")

        if st.button("Calcular caída rápida", use_container_width=True, key="btn_quick"):
            Iq = intensidad_por_potencia(pot_quick)
            cq = caida_tension(Iq, long_quick, sec_quick)
            st.write(f"**Intensidad:** {Iq:.2f} A")
            st.write(f"**Caída de tensión:** {cq:.2f} %")

    card_close()


# =========================================================
# MÓDULO: PRESUPUESTO
# =========================================================

elif opcion == "💰 Presupuesto":
    card_open()
    st.markdown("### 💰 Presupuesto completo C1–C13")

    catalogo = cargar_catalogo()
    lista_capitulos = list(catalogo.keys())

    st.markdown("Puedes editar el catálogo en el módulo **📦 Catálogo** (solo admin).")

    if st.button("Calcular presupuesto", use_container_width=True):
        presupuesto = calcular_presupuesto_completo(catalogo, lista_capitulos)

        st.markdown("#### 📊 Capítulos")
        st.dataframe(presupuesto["df"], use_container_width=True)

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
            excel_bytes = exportar_excel_avanzado(presupuesto, "presupuesto.xlsx")
            st.download_button(
                "📥 Descargar Excel",
                data=excel_bytes,
                file_name="presupuesto.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_e2:
            pdf_path = "presupuesto.pdf"
            generar_pdf_presupuesto(
                output_path=pdf_path,
                proyecto={"nombre": "Proyecto genérico"},
                presupuesto=presupuesto,
                firma_digital={
                    "nombre": "Técnico",
                    "dni": "00000000X",
                    "cargo": "Instalador autorizado",
                },
            )
            st.download_button(
                "📄 Descargar PDF",
                data=open(pdf_path, "rb").read(),
                file_name="presupuesto.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    card_close()


# =========================================================
# MÓDULO: MEMORIA REBT
# =========================================================

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
        potencia_prevista = st.text_input("Potencia prevista", "Según cálculo")
        localidad = st.text_input("Localidad", "Orihuela (Alicante)")

    divider()

    st.markdown("#### Datos de firma digital")
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        firma_nombre = st.text_input("Nombre técnico", "Técnico")
    with colf2:
        firma_dni = st.text_input("DNI técnico", "00000000X")
    with colf3:
        firma_cargo = st.text_input("Cargo", "Instalador autorizado")

    if st.button("Generar memoria REBT (Word + PDF)", use_container_width=True):
        proyecto = {
            "nombre": nombre,
            "cliente": cliente,
            "direccion": direccion,
            "tipo": tipo,
            "potencia": potencia_prevista,
            "localidad": localidad,
        }

        # Aquí podrías conectar con tus cálculos reales de secciones y protecciones
        secciones = {
            "C1": {"seccion": 1.5, "descripcion": "Iluminación"},
            "C2": {"seccion": 2.5, "descripcion": "Tomas de corriente"},
            "Derivación individual": {
                "seccion": 10,
                "longitud": 20,
                "caida": 1.8,
                "descripcion": "DI 10 mm²",
            },
        }

        protecciones = {
            "Cuadro general": {
                "proteccion": "IGA 40A",
                "intensidad": 40,
                "descripcion": "Protección general",
            },
            "Diferencial general": {
                "proteccion": "ID 40A 30mA",
                "intensidad": 40,
                "descripcion": "Diferencial general",
            },
        }

        presupuesto = {
            "capitulos": [
                {
                    "Capítulo": "C1",
                    "Material (€)": 100,
                    "Mano de obra (€)": 80,
                    "Total capítulo (€)": 230,
                },
                {
                    "Capítulo": "C2",
                    "Material (€)": 150,
                    "Mano de obra (€)": 90,
                    "Total capítulo (€)": 290,
                },
            ],
            "total_final": 520,
        }

        firma = {
            "nombre": firma_nombre,
            "dni": firma_dni,
            "cargo": firma_cargo,
        }

        # Word
        word_path = "memoria_rebt.docx"
        generar_memoria_word(
            word_path,
            proyecto,
            secciones,
            protecciones,
            presupuesto,
            firma,
        )

        # PDF
        pdf_path = "memoria_rebt.pdf"
        generar_memoria_pdf(
            pdf_path,
            proyecto,
            presupuesto,
            firma,
        )

        colw, colp = st.columns(2)
        with colw:
            st.download_button(
                "📘 Descargar Memoria Word",
                data=open(word_path, "rb").read(),
                file_name="memoria_rebt.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with colp:
            st.download_button(
                "📄 Descargar Memoria PDF",
                data=open(pdf_path, "rb").read(),
                file_name="memoria_rebt.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    card_close()


# =========================================================
# MÓDULO: CATÁLOGO
# =========================================================

elif opcion == "📦 Catálogo":
    card_open()
    st.markdown("### 📦 Catálogo de materiales (solo admin)")
    require_role("admin")
    editor_catalogo_ui()
    card_close()


# =========================================================
# MÓDULO: ADMINISTRACIÓN (USUARIOS)
# =========================================================

elif opcion == "👥 Administración":
    require_role("admin")
    card_open()
    st.markdown("### 👥 Administración de usuarios")

    tab1, tab2 = st.tabs(["➕ Crear usuario", "📋 Listado de usuarios"])

    with tab1:
        st.markdown("#### Crear nuevo usuario")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_user = st.text_input("Usuario")
        with col2:
            new_name = st.text_input("Nombre completo")
        with col3:
            new_role = st.selectbox("Rol", ["tecnico", "admin"])

        colp1, colp2 = st.columns(2)
        with colp1:
            new_pass = st.text_input("Contraseña", type="password")
        with colp2:
            new_pass2 = st.text_input("Repetir contraseña", type="password")

        if st.button("Crear usuario", use_container_width=True):
            if new_pass != new_pass2:
                st.error("Las contraseñas no coinciden.")
            elif not new_user:
                st.error("El usuario es obligatorio.")
            else:
                ok = create_user(new_user, new_pass, new_name, new_role)
                if ok:
                    st.success("Usuario creado correctamente.")
                else:
                    st.error("No se ha podido crear el usuario (puede que ya exista).")

    with tab2:
        st.markdown("#### Usuarios registrados")
        usuarios = list_users()
        if not usuarios:
            st.info("No hay usuarios registrados.")
        else:
            for u in usuarios:
                colu1, colu2, colu3, colu4 = st.columns([2, 2, 1, 1])
                with colu1:
                    st.write(f"**{u['username']}**")
                with colu2:
                    st.write(f"{u['full_name']} ({u['role']})")
                with colu3:
                    st.write(u["created_at"])
                with colu4:
                    if u["username"] != "admin":
                        if st.button("Eliminar", key=f"del_{u['id']}"):
                            if delete_user(u["id"]):
                                st.success("Usuario eliminado.")
                                st.experimental_rerun()

    card_close()


# =========================================================
# MÓDULO: CUENTA
# =========================================================

elif opcion == "👤 Cuenta":
    card_open()
    st.markdown("### 👤 Cuenta de usuario")
    st.write(f"**Usuario:** {st.session_state['username']}")
    st.write(f"**Rol:** {st.session_state['role']}")
    st.write(f"**Sesión iniciada:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    divider()
    logout_button()
    card_close()
