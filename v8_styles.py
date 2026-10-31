"""Estilos modernos para REBT Suite v8."""
from __future__ import annotations


def css(tema: str = "Oscuro") -> str:
    oscuro = tema == "Oscuro"
    if oscuro:
        bg0 = "#0b1220"
        bg1 = "#111a2e"
        panel = "rgba(20, 30, 52, 0.72)"
        panel2 = "rgba(28, 40, 68, 0.6)"
        border = "rgba(148, 163, 184, 0.16)"
        text = "#e6edf7"
        text2 = "#9fb0cc"
        accent = "#38bdf8"
        accent2 = "#a78bfa"
        ok = "#22c55e"
        warn = "#f59e0b"
        err = "#ef4444"
    else:
        bg0 = "#f5f7fb"
        bg1 = "#ffffff"
        panel = "rgba(255, 255, 255, 0.85)"
        panel2 = "rgba(248, 250, 252, 0.9)"
        border = "rgba(15, 23, 42, 0.10)"
        text = "#0f172a"
        text2 = "#475569"
        accent = "#2563eb"
        accent2 = "#7c3aed"
        ok = "#16a34a"
        warn = "#d97706"
        err = "#dc2626"

    return f"""
<style>
:root {{
  --bg0:{bg0}; --bg1:{bg1}; --panel:{panel}; --panel2:{panel2};
  --border:{border}; --text:{text}; --text2:{text2};
  --accent:{accent}; --accent2:{accent2}; --ok:{ok}; --warn:{warn}; --err:{err};
  --radius:14px; --radius-sm:10px; --shadow:0 10px 30px rgba(0,0,0,.18);
  --glass:blur(12px) saturate(140%);
}}
html, body, [data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 600px at 10% -10%, {accent}22, transparent 60%),
              radial-gradient(900px 500px at 90% 0%, {accent2}18, transparent 60%),
              var(--bg0) !important;
  color: var(--text) !important;
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, var(--bg1), var(--bg0)) !important;
  border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1320px; }}
h1,h2,h3 {{ color: var(--text) !important; letter-spacing: -0.02em; }}
p, span, label, div {{ color: inherit; }}

/* Glass cards */
.glass {{
  background: var(--panel);
  backdrop-filter: var(--glass);
  -webkit-backdrop-filter: var(--glass);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.2rem 1.4rem;
  box-shadow: var(--shadow);
  transition: transform .18s ease, box-shadow .18s ease;
}}
.glass:hover {{ transform: translateY(-2px); box-shadow: 0 14px 36px rgba(0,0,0,.22); }}

/* Hero */
.hero {{
  position: relative; overflow: hidden;
  background: linear-gradient(120deg, {accent}, {accent2});
  border-radius: 20px; padding: 2.2rem 2.4rem; color: #fff;
  box-shadow: 0 20px 40px {accent}33;
}}
.hero h1 {{ color: #fff !important; font-size: 2.4rem; margin: .2rem 0; }}
.hero p {{ color: rgba(255,255,255,.9) !important; margin: 0; font-size: 1.05rem; }}
.hero .kicker {{ font-size: .72rem; letter-spacing: .16em; font-weight: 800; opacity: .85; }}

/* KPI */
.kpi {{
  background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1rem 1.1rem; text-align: left;
}}
.kpi .label {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .1em; color: var(--text2); }}
.kpi .value {{ font-size: 1.6rem; font-weight: 800; color: var(--text); margin-top: .2rem; }}
.kpi .sub {{ font-size: .78rem; color: var(--text2); margin-top: .15rem; }}
.kpi.ok .value {{ color: var(--ok); }}
.kpi.warn .value {{ color: var(--warn); }}
.kpi.err .value {{ color: var(--err); }}

/* Badges */
.badge {{
  display: inline-flex; align-items: center; gap: .4rem;
  padding: .25rem .7rem; border-radius: 999px; font-size: .72rem; font-weight: 700;
  background: {accent}22; color: {accent}; border: 1px solid {accent}44;
}}
.badge.ok {{ background: {ok}22; color: {ok}; border-color: {ok}44; }}
.badge.warn {{ background: {warn}22; color: {warn}; border-color: {warn}44; }}
.badge.err {{ background: {err}22; color: {err}; border-color: {err}44; }}

/* Buttons */
.stButton > button, .stDownloadButton > button {{
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
  background: var(--panel) !important;
  color: var(--text) !important;
  transition: all .15s ease !important;
  font-weight: 600 !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  border-color: {accent} !important;
  color: {accent} !important;
  transform: translateY(-1px);
}}
.stButton > button[kind="primary"] {{
  background: linear-gradient(120deg, {accent}, {accent2}) !important;
  color: #fff !important; border: none !important;
}}

/* Inputs */
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {{
  background: var(--panel2) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--radius-sm) !important;
}}
.stTextInput > div > div > input:focus {{ border-color: {accent} !important; box-shadow: 0 0 0 2px {accent}33; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: .4rem; border-bottom: 1px solid var(--border); }}
.stTabs [data-baseweb="tab"] {{
  background: transparent; border-radius: 8px 8px 0 0; padding: .6rem 1rem;
  color: var(--text2); font-weight: 600;
}}
.stTabs [aria-selected="true"] {{ color: {accent} !important; border-bottom: 2px solid {accent}; }}

/* Metrics */
[data-testid="stMetric"] {{
  background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem;
}}
[data-testid="stMetricLabel"] {{ color: var(--text2) !important; }}
[data-testid="stMetricValue"] {{ color: var(--text) !important; }}

/* Dataframe */
[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}

/* Alerts */
.stAlert {{ border-radius: var(--radius-sm) !important; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-thumb {{ background: {accent}44; border-radius: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}

/* Animations */
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.fade-in {{ animation: fadeIn .35s ease; }}

/* Sidebar nav */
.nav-item {{
  display: flex; align-items: center; gap: .6rem;
  padding: .55rem .8rem; border-radius: 8px; margin: .15rem 0;
  color: var(--text2); font-weight: 600; font-size: .9rem;
  transition: all .15s ease;
}}
.nav-item:hover {{ background: {accent}14; color: {accent}; }}
.nav-item.active {{ background: {accent}22; color: {accent}; }}

/* Status dot */
.dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
.dot.ok {{ background: var(--ok); box-shadow: 0 0 8px var(--ok); }}
.dot.warn {{ background: var(--warn); }}
.dot.err {{ background: var(--err); }}

/* Footer */
.footer {{
  margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
  color: var(--text2); font-size: .78rem; text-align: center;
}}
</style>
"""


def inject(tema: str = "Oscuro") -> None:
    import streamlit as st
    st.markdown(css(tema), unsafe_allow_html=True)
