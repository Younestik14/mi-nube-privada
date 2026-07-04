import streamlit as st

def aplicar_estilo_global():
    """Inyecta el CSS avanzado para componentes, formularios y tarjetas en toda la web."""
    st.markdown("""
        <style>
            .main .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 95%;
            }
            .premium-card {
                background-color: #f8f9fa;
                border: 1px solid #e2e8f0;
                padding: 22px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
            }
            .premium-card h4 {
                color: #1e293b;
                margin-top: 0;
                font-weight: 600;
                border-bottom: 2px solid #2563eb;
                padding-bottom: 8px;
                font-size: 16px;
            }
            .stTextInput>div>div>input, .stSelectbox>div>div>div {
                border-radius: 6px !important;
            }
        </style>
    """, unsafe_allow_html=True)

def generar_banner(titulo, subtitulo):
    """Renderiza el banner superior con gradiente corporativo homologado."""
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            color: white;
            padding: 24px 30px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.15);
        ">
            <h1 style='color: white; margin: 0; font-size: 24px; font-weight: 700;'>{titulo}</h1>
            <p style='color: #93c5fd; margin: 6px 0 0 0; font-size: 13px;'>{subtitulo}</p>
        </div>
    """, unsafe_allow_html=True)
