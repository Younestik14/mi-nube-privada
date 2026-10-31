"""REBT Suite — Calculadora de instalaciones eléctricas."""
import streamlit as st
from styles import inject_css
from calc_ui import CALCS

st.set_page_config(
    page_title="REBT Suite · Calculadora Eléctrica",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "tema" not in st.session_state:
    st.session_state["tema"] = "Oscuro"

inject_css(st.session_state["tema"])

with st.sidebar:
    st.markdown(
        '<div class="glass" style="padding:1rem 1.2rem; margin-bottom:1rem;">'
        '<div style="font-size:1.3rem; font-weight:800;">⚡ REBT Suite</div>'
        '<div style="color:var(--text2); font-size:.8rem;">Calculadora eléctrica · REBT + IEC</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    calc_name = st.selectbox("Cálculo", list(CALCS.keys()))
    st.markdown("---")
    tema = st.radio("Tema", ["Oscuro", "Claro"],
                    index=0 if st.session_state["tema"] == "Oscuro" else 1,
                    horizontal=True)
    if tema != st.session_state["tema"]:
        st.session_state["tema"] = tema
        st.rerun()
    st.markdown("---")
    st.caption("Herramienta de apoyo al predimensionado. Verifica los valores críticos antes de uso profesional.")

st.markdown(
    f'<div class="hero"><h1>⚡ {calc_name}</h1>'
    f'<p>Cálculo eléctrico conforme a REBT e IEC 60364.</p></div>',
    unsafe_allow_html=True,
)
st.markdown("")

CALCS[calc_name]()