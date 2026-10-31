"""REBT Suite v8 - version mejorada (visual + funcional)."""
from __future__ import annotations

import streamlit as st

from v7_engine import *
from v7_ui import init as v7_init, render as v7_render
from v8_styles import inject as inject_css

st.set_page_config(
    page_title="REBT Suite v8 · Instalaciones Eléctricas",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "tema" not in st.session_state:
    st.session_state["tema"] = "Oscuro"
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "Inicio"

inject_css(st.session_state["tema"])
v7_init()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="glass" style="padding:1rem 1.2rem; margin-bottom:1rem;">'
        '<div style="font-size:1.3rem; font-weight:800;">⚡ REBT Suite</div>'
        '<div style="color:var(--text2); font-size:.8rem;">v8 · Instalaciones eléctricas</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    paginas = [
        ("🏠", "Inicio", "Landing y accesos rápidos"),
        ("🧩", "Diseñador Pro", "Proyecto · circuitos · inspector · unifilar"),
        ("📊", "Estadísticas", "KPIs y gráficos"),
        ("⚙️", "Configuración", "Perfil y apariencia"),
        ("ℹ️", "Acerca de", "Info y créditos"),
    ]
    for icon, nombre, desc in paginas:
        active = "active" if st.session_state["pagina_actual"] == nombre else ""
        if st.button(f"{icon}  {nombre}", key=f"nav_{nombre}", use_container_width=True):
            st.session_state["pagina_actual"] = nombre
            st.rerun()
        st.caption(desc)

    st.markdown("---")
    tema = st.radio("Tema", ["Oscuro", "Claro"],
                    index=0 if st.session_state["tema"] == "Oscuro" else 1,
                    horizontal=True)
    if tema != st.session_state["tema"]:
        st.session_state["tema"] = tema
        st.rerun()

    st.markdown("---")
    st.caption("Proyecto: " + st.session_state.get("v7_project", {}).get("name", "Sin nombre"))
    cs = st.session_state.get("v7_circuits", [])
    st.caption(f"Circuitos: {len(cs)}")

# ---------- Páginas ----------
pagina = st.session_state["pagina_actual"]

if pagina == "Inicio":
    st.markdown(
        '<div class="hero fade-in">'
        '<div class="kicker">REBT SUITE · v8</div>'
        '<h1>Diseña instalaciones con criterio y claridad</h1>'
        '<p>Calcula secciones de cable, dimensiona fotovoltaica, genera presupuestos y documentación técnica '
        'con una experiencia de trabajo moderna y trazable.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="glass fade-in"><h3>🧩 Diseñador Pro</h3>'
                    '<p style="color:var(--text2);">Gestiona proyectos, circuitos, inspector REBT, unifilar SVG, '
                    'presupuesto y exportación.</p></div>', unsafe_allow_html=True)
        if st.button("Abrir Diseñador Pro", type="primary", use_container_width=True):
            st.session_state["pagina_actual"] = "Diseñador Pro"
            st.rerun()
    with c2:
        st.markdown('<div class="glass fade-in"><h3>⚡ Calculadora rápida</h3>'
                    '<p style="color:var(--text2);">Sección de cable y protecciones en segundos con plantillas.</p></div>',
                    unsafe_allow_html=True)
        if st.button("Ir a calculadora", use_container_width=True):
            st.session_state["pagina_actual"] = "Diseñador Pro"
            st.rerun()
    with c3:
        st.markdown('<div class="glass fade-in"><h3>☀️ Fotovoltaica</h3>'
                    '<p style="color:var(--text2);">Dimensionado de autoconsumo con excedentes.</p></div>',
                    unsafe_allow_html=True)
        if st.button("Ir a FV", use_container_width=True):
            st.session_state["pagina_actual"] = "Diseñador Pro"
            st.rerun()

    st.markdown("")
    st.markdown('<p class="section-label" style="font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;opacity:.62;">KPIs del proyecto</p>',
                unsafe_allow_html=True)
    cs = st.session_state.get("v7_circuits", [])
    from v7_engine import summary as v7_summary
    p = st.session_state.get("v7_project", {})
    s = v7_summary(cs, p.get("iga", 40)) if cs else {"circuits": 0, "power_kw": 0.0, "errors": 0, "warnings": 0, "ok": 0}
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi"><div class="label">Circuitos</div><div class="value">{s["circuits"]}</div>'
                f'<div class="sub">activos</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><div class="label">Potencia</div><div class="value">{s["power_kw"]:.1f} kW</div>'
                f'<div class="sub">total</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi err"><div class="label">Errores</div><div class="value">{s["errors"]}</div>'
                f'<div class="sub">REBT</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi ok"><div class="label">OK</div><div class="value">{s["ok"]}</div>'
                f'<div class="sub">comprobaciones</div></div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="glass"><h3>Ejemplos prellenados</h3>'
                '<p style="color:var(--text2);">Carga un ejemplo completo con datos reales para ver cómo funciona.</p></div>',
                unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    e1.button("🏠 Casa unifamiliar", use_container_width=True)
    e2.button("🏭 Nave industrial", use_container_width=True)
    e3.button("☀️ Vivienda con FV", use_container_width=True)

elif pagina == "Diseñador Pro":
    v7_render()

elif pagina == "Estadísticas":
    st.markdown('<div class="hero"><div class="kicker">ESTADÍSTICAS</div>'
                '<h1>Métricas del proyecto</h1>'
                '<p>Resumen de circuitos, potencia y estado REBT.</p></div>', unsafe_allow_html=True)
    cs = st.session_state.get("v7_circuits", [])
    if not cs:
        st.info("Añade circuitos en el Diseñador Pro para ver estadísticas.")
    else:
        import pandas as pd
        df = pd.DataFrame([{"Circuito": c["name"], "Uso": c["kind"], "kW": c["power_kw"],
                            "m": c["length_m"], "Sección": c["section"], "PIA": c["breaker"]} for c in cs])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.metric("Potencia total", f"{sum(c['power_kw'] for c in cs):.2f} kW")
        st.metric("Circuitos", len(cs))

elif pagina == "Configuración":
    st.markdown('<div class="hero"><div class="kicker">CONFIGURACIÓN</div>'
                '<h1>Perfil y apariencia</h1></div>', unsafe_allow_html=True)
    p = st.session_state.setdefault("v7_project", {})
    p["name"] = st.text_input("Nombre del proyecto", p.get("name", "Proyecto sin nombre"))
    p["designer"] = st.text_input("Proyectista", p.get("designer", ""))
    p["location"] = st.text_input("Ubicación", p.get("location", ""))
    p["iga"] = st.number_input("IGA (A)", 6, 400, int(p.get("iga", 40)), 1)
    st.session_state["v7_project"] = p

elif pagina == "Acerca de":
    st.markdown('<div class="hero"><div class="kicker">ACERCA DE</div>'
                '<h1>REBT Suite v8</h1>'
                '<p>Herramienta de apoyo al diseño de instalaciones de baja tensión conforme al REBT.</p></div>',
                unsafe_allow_html=True)
    st.markdown("""
    **Construida con:** Python, Streamlit, pandas, plotly, reportlab.

    **Mejoras v8:**
    - Rediseño visual moderno (glassmorphism, modo oscuro/claro).
    - Navegación lateral con KPIs.
    - Validación inline y notificaciones.
    - Exportación a Excel/PDF/JSON.
    - Accesibilidad mejorada.

    **Aviso legal:** herramienta de apoyo al predimensionado. Verifica los valores críticos antes de un uso profesional.
    """)

st.markdown('<div class="footer">REBT Suite v8 · Younesse Tikent Tifaoui · '
            'Herramienta de apoyo, no sustituye verificación profesional.</div>', unsafe_allow_html=True)
