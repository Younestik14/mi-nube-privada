import streamlit as st
import math

st.title("⚡ Cálculo de Sección de Conductores")

# Formulario de entrada de datos
col1, col2 = st.columns(2)

with col1:
    sistema = st.selectbox("Sistema eléctrico", ["Trifásico", "Monofásico"])
    tension = st.number_input("Tensión nominal (V)", value=400 if sistema == "Trifásico" else 230)
    potencia = st.number_input("Potencia de la carga (W)", value=5000)

with col2:
    cos_phi = st.number_input("Factor de potencia (cos phi)", value=0.85, min_value=0.0, max_value=1.0)
    longitud = st.number_input("Longitud de la línea (metros)", value=30.0)
    conductividad = st.selectbox("Material del conductor", ["Cobre (Cu)", "Aluminio (Al)"])

# Lógica de cálculo básica (Intensidad)
cond_val = 56 if "Cobre" in conductividad else 35

if sistema == "Trifásico":
    intensidad = potencia / (math.sqrt(3) * tension * cos_phi)
else:
    intensidad = potencia / (tension * cos_phi)

st.write("---")
st.subheader("📊 Resultados Preliminares")
st.metric(label="Intensidad de Corriente (I)", value=f"{intensidad:.2f} A")

# Aquí añadirías las tablas normativas para la sección por caída de tensión e intensidad admisible
st.info("Próximo paso: Vincular con bases de datos normativas de cables según canalización.")
