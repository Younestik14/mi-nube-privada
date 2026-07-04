import streamlit as st

def aplicar_estilo_global():
    """Inyecta el CSS avanzado para el Modo Oscuro Premium en toda la web."""
    st.markdown("""
        <style>
            /* Optimización del espacio de trabajo */
            .main .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 95%;
            }
            
            /* Tarjetas contenedoras en Modo Oscuro */
            .premium-card {
                background-color: #1e293b;   /* Fondo de tarjeta gris azulado oscuro */
                border: 1px solid #334155;    /* Borde sutil gris */
                padding: 22px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            }
            
            /* Títulos de los bloques de cálculo */
            .premium-card h4 {
                color: #f8fafc;              /* Texto del título en blanco */
                margin-top: 0;
                font-weight: 600;
                border-bottom: 2px solid #3b82f6; /* Línea de acento azul */
                padding-bottom: 8px;
                font-size: 16px;
                letter-spacing: 0.5px;
            }
            
            /* Estilo personalizado para las cajas de código (Esquemas ASCII) en modo oscuro */
            code {
                color: #38bdf8 !important;   /* Texto cian de alta visibilidad técnica */
                background-color: #0f172a !important; /* Fondo negro azulado */
            }
        </style>
    """, unsafe_allow_html=True)

def generar_banner(titulo, subtitulo):
    """Renderiza el banner superior con un gradiente oscuro industrial."""
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            color: white;
            padding: 24px 30px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            border: 1px solid #1d4ed8;
        ">
            <h1 style='color: white; margin: 0; font-size: 24px; font-weight: 700;'>{titulo}</h1>
            <p style='color: #93c5fd; margin: 6px 0 0 0; font-size: 13px;'>{subtitulo}</p>
        </div>
    """, unsafe_allow_html=True)
