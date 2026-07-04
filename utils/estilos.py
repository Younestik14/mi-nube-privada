import streamlit as st

def aplicar_marca_agua():
    marca_agua = """
    <style>
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 20px;
        color: rgba(128, 128, 128, 0.3); /* Color gris con transparencia */
        font-size: 20px;
        font-weight: bold;
        z-index: 1000;
        pointer-events: none; /* Esto evita que tape los botones o clicks */
    }
    </style>
    <div class="watermark">Younesse Tikent Tifaoui</div>
    """
    st.markdown(marca_agua, unsafe_allow_html=True)
