import streamlit as st


def inject_css(tema="Oscuro"):
    oscuro = tema == "Oscuro"
    bg = "#0b1220" if oscuro else "#f5f7fb"
    panel = "rgba(20,30,52,0.72)" if oscuro else "rgba(255,255,255,0.85)"
    text = "#e6edf7" if oscuro else "#0f172a"
    text2 = "#9fb0cc" if oscuro else "#475569"
    accent = "#38bdf8" if oscuro else "#2563eb"
    accent2 = "#a78bfa" if oscuro else "#7c3aed"
    border = "rgba(148,163,184,0.16)" if oscuro else "rgba(15,23,42,0.10)"

    st.markdown(f"""
<style>
:root {{
  --bg:{bg}; --panel:{panel}; --text:{text}; --text2:{text2};
  --accent:{accent}; --accent2:{accent2}; --border:{border};
}}
html,body,[data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 600px at 10% -10%, {accent}22, transparent 60%),
              radial-gradient(900px 500px at 90% 0%, {accent2}18, transparent 60%), var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter','Segoe UI',system-ui,sans-serif;
}}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg,var(--bg),var(--bg)) !important; border-right:1px solid var(--border); }}
.block-container {{ padding-top:1.2rem; max-width:1400px; }}
h1,h2,h3 {{ color:var(--text) !important; letter-spacing:-0.02em; }}
.glass {{ background:var(--panel); backdrop-filter:blur(12px); border:1px solid var(--border); border-radius:14px; padding:1.2rem 1.4rem; box-shadow:0 10px 30px rgba(0,0,0,.18); }}
.hero {{ background:linear-gradient(120deg,{accent},{accent2}); border-radius:20px; padding:2rem 2.4rem; color:#fff; }}
.hero h1 {{ color:#fff !important; }}
.kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1rem; }}
.kpi .label {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; color:var(--text2); }}
.kpi .value {{ font-size:1.6rem; font-weight:800; color:var(--text); }}
.stButton>button {{ border-radius:10px !important; border:1px solid var(--border) !important; background:var(--panel) !important; color:var(--text) !important; font-weight:600 !important; }}
.stButton>button:hover {{ border-color:{accent} !important; color:{accent} !important; }}
.stButton>button[kind="primary"] {{ background:linear-gradient(120deg,{accent},{accent2}) !important; color:#fff !important; border:none !important; }}
[data-testid="stMetric"] {{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1rem; }}
.stTabs [data-baseweb="tab"] {{ color:var(--text2); font-weight:600; }}
.stTabs [aria-selected="true"] {{ color:{accent} !important; }}
.stAlert {{ border-radius:10px !important; }}
::-webkit-scrollbar {{ width:10px; }} ::-webkit-scrollbar-thumb {{ background:{accent}44; border-radius:8px; }}
</style>
""", unsafe_allow_html=True)