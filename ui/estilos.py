"""Estilos visuales de la aplicacion (CSS profesional).

Se mantienen todas las clases CSS originales ('aviso-normativa',
'caja-log', 'caja-ayuda') para no romper el resto de la interfaz, y se
anaden mejoras visuales (tipografia, sombras, tarjetas, gradientes,
bordes redondeados) para lograr un aspecto de software profesional.
"""

from __future__ import annotations

import streamlit as st

CSS_APLICACION = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1300px;
}

h1, h2, h3 {
    color: #0B3D91 !important;
    font-weight: 700 !important;
}

/* ---- Cabecera principal tipo software premium ---- */
.cabecera-app {
    background: linear-gradient(135deg, #0B3D91 0%, #12579E 55%, #1C7FBF 100%);
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(11, 61, 145, 0.25);
}
.cabecera-app h1 {
    color: #FFFFFF !important;
    margin: 0;
    font-size: 1.9rem;
}
.cabecera-app p {
    color: #E7F0FF !important;
    margin: 4px 0 0 0;
    font-size: 0.95rem;
}

/* ---- Pestanas ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 2px solid #E4EBF7;
}
.stTabs [data-baseweb="tab"] {
    background-color: #EEF3FB;
    border-radius: 10px 10px 0 0;
    padding: 10px 16px;
    font-weight: 600;
    transition: background-color 0.2s ease-in-out;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #DCE8FA;
}
.stTabs [data-baseweb="tab"] p {color: #0B3D91 !important;}
.stTabs [aria-selected="true"] {
    background-color: #0B3D91 !important;
    box-shadow: 0 2px 8px rgba(11, 61, 145, 0.3);
}
.stTabs [aria-selected="true"] p {color: #FFFFFF !important;}

/* ---- Metricas tipo tarjeta ---- */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE6F5;
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 2px 10px rgba(15, 40, 90, 0.06);
    transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 40, 90, 0.12);
}
div[data-testid="stMetric"] * {color: #0B3D91 !important;}

/* ---- Botones ---- */
.stButton > button, .stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: 0 2px 6px rgba(15, 40, 90, 0.08);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    box-shadow: 0 6px 14px rgba(15, 40, 90, 0.18);
    transform: translateY(-1px);
}

/* ---- Barra lateral profesional ---- */
section[data-testid="stSidebar"] {
    background-color: #F7FAFF;
    border-right: 1px solid #E4EBF7;
}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    color: #0B3D91 !important;
}

/* ---- Expanders con aspecto de tarjeta ---- */
summary {
    border-radius: 10px !important;
}

/* ---- Avisos y cajas informativas (clases originales) ---- */
.aviso-normativa {
    background-color: #FFF6E5;
    border-left: 5px solid #E8A33D;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.9rem;
    margin-bottom: 10px;
    color: #6B4B00 !important;
    box-shadow: 0 2px 8px rgba(232, 163, 61, 0.12);
}
.aviso-normativa * {color: #6B4B00 !important;}

.caja-log {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E5;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 0.82rem;
    margin-bottom: 6px;
    color: #2B2B2B !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.caja-log * {color: #2B2B2B !important;}

.caja-ayuda {
    background-color: #EAF4EC;
    border-left: 5px solid #2E7D32;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 10px;
    color: #14421A !important;
}
.caja-ayuda * {color: #14421A !important;}

/* ---- Tarjeta generica reutilizable ---- */
.tarjeta-kpi {
    background-color: #FFFFFF;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(15, 40, 90, 0.06);
    border: 1px solid #E9EFFA;
}
</style>
"""


def aplicar_estilos() -> None:
    """Inyecta el CSS profesional de la aplicacion en la pagina de Streamlit.

    Debe llamarse una vez, justo despues de 'configurar_pagina()'.
    """
    st.markdown(CSS_APLICACION, unsafe_allow_html=True)
