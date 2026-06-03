import streamlit as st
import time

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Simulador SEA - CIFP Politécnico de Cartagena",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para diseño industrial y animación del motor
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { border-radius: 4px; font-weight: bold; height: 3em; }
    .motor-container { text-align: center; padding: 20px; border: 2px solid #333; border-radius: 8px; background-color: #fafafa; }
    .motor-axis {
        font-size: 50px;
        display: inline-block;
    }
    @keyframes spin-cw { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes spin-ccw { 0% { transform: rotate(360deg); } 100% { transform: rotate(0deg); } }
    .spin-clockwise { animation: spin-cw 1s linear infinite; }
    .spin-counterclockwise { animation: spin-ccw 1s linear infinite; }
    .motor-stop { color: #d32f2f; }
    .motor-run-cw { color: #2e7d32; }
    .motor-run-ccw { color: #0288d1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ENCABEZADO INSTITUCIONAL
# ==========================================
st.title("⚡ Plataforma Web de Simulación de Automatismos Cableados")
st.caption("Desarrollado para el Grado Superior en Sistemas Electrotécnicos y Automatizados (SEA) | CIFP Politécnico de Cartagena")
st.divider()

# ==========================================
# CONTROL DE ESTADOS DE MEMORIA (SESSION STATE)
# ==========================================
# Inicialización de contactores, temporizadores y relés térmicos
estados_iniciales = {
    # Circuito 1
    'K1_C1': False,
    # Circuito 2
    'KM1_CW': False, 'KM2_CCW': False, 'F2_TRIP': False,
    # Circuito 3
    'KM1_LINEA': False, 'KM2_ESTRELLA': False, 'KM3_TRIANGULO': False, 'KT1_TIMER': False, 'C3_RUNNING': False
}

for clave, valor in estados_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor

# ==========================================
# MENÚ DE SELECCIÓN DE CIRCUITOS (TABS)
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🎯 1. Marcha/Paro (Autoenclavamiento)", 
    "🔄 2. Inversión de Giro (Seguridad Eléctrica)", 
    "📐 3. Arranque Estrella-Triángulo (Temporizado)"
])

# ==========================================
# TAB 1: MARCHA / PARO CON AUTOENCLAVAMIENTO
# ==========================================
with tab1:
    st.header("Circuito de Marcha y Paro de un Contactor")
    st.info("🎯 **Objetivo didáctico:** Comprender el concepto de realimentación o autoenclavamiento utilizando el contacto auxiliar NA (13-14) en paralelo con el pulsador de marcha.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🕹️ Interfaz del Cuadro")
        q1 = st.toggle("🔌 Disyuntor Magnetotérmico (Q1)", value=True, key="q1_c1")
        s1_nc = st.button("🔴 Pulsador de Paro (S1 - NC)", use_container_width=True, key="s1_c1")
        s2_na = st.button("🟢 Pulsador de Marcha (S2 - NA)", use_container_width=True, key="s2_c1")
        
        # Procesamiento lógico inmediato
        if s1_nc or not q1:
            st.session_state.K1_C1 = False
        elif s2_na and q1:
            st.session_state.K1_C1 = True

    with col2:
        st.subheader("📊 Estado de las Salidas y Carga")
        c_k1, c_m1 = st.columns(2)
        
        with c_k1:
            if st.session_state.K1_C1:
                st.success("### 🧲 Contactor K1\n**ESTADO:** ACTIVADO (A1-A2 con tensión)")
                st.caption("Contacto auxiliar 13-14 cerrado.")
            else:
                st.error("### 🧲 Contactor K1\n**ESTADO:** DESACTIVADO")
                
        with c_m1:
            if st.session_state.K1_C1:
                st.markdown('<div class="motor-container"><div class="motor-axis spin-clockwise">⚙️</div><h3 class="motor-run-cw">MOTOR EN MARCHA</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="motor-container"><div class="motor-axis motor-stop">⚙️</div><h3 class="motor-stop">MOTOR PARADO</h3></div>', unsafe_allow_html=True)

        st.markdown("#### 📐 Ecuación Booleana del Automatismo:")
        st.code("K1 = Q1 * /S1 * (S2 + K1)", language="python")

# ==========================================
# TAB 2: INVERSIÓN DE GIRO CON ENCLAVAMIENTO
# ==========================================
with tab2:
    st.header("Inversión de Giro de un Motor Trifásico")
    st.info("⚠️ **Objetivo didáctico:** Estudiar el **enclavamiento eléctrico por software/hardware**. Los contactos NC cruzados de KM1 y KM2 impiden que ambos se activen a la vez, lo que provocaría un cortocircuito entre fases.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🕹️ Interfaz del Cuadro")
        q2 = st.toggle("🔌 Disyuntor General (Q2)", value=True)
        
        # Simulación de salto de Relé Térmico (Ferna/Avería)
        f2_thermal = st.checkbox("🚨 Disparar Relé Térmico F2 (Avería por sobreintensidad)", value=st.session_state.F2_TRIP)
        st.session_state.F2_TRIP = f2_thermal
        
        st.divider()
        s0_paro = st.button("🔴 Pulsador de Paro General (S0 - NC)", use_container_width=True)
        s1_cw = st.button("🔄 Marcha Derecha (S1 - NA)", use_container_width=True)
        s2_ccw = st.button("🔄 Marcha Izquierda (S2 - NA)", use_container_width=True)
        
        # --- LÓGICA DE CONTROL (ÁLGEBRA DE CONTACTOS) ---
        if s0_paro or not q2 or st.session_state.F2_TRIP:
            st.session_state.KM1_CW = False
            st.session_state.KM2_CCW = False
        else:
            if s1_cw and not st.session_state.KM2_CCW: # Enclavamiento: No entra KM1 si KM2 está activo
                st.session_state.KM1_CW = True
                st.session_state.KM2_CCW = False
            elif s2_ccw and not st.session_state.KM1_CW: # Enclavamiento: No entra KM2 si KM1 está activo
                st.session_state.KM2_CCW = True
                st.session_state.KM1_CW = False

    with col2:
        st.subheader("📊 Diagnóstico de la Planta")
        
        if st.session_state.F2_TRIP:
            st.error("🚨 ALARMA: El Relé Térmico F2 ha saltado. Contacto 95-96 abierto. Rearme el relé para operar.")
        
        c_km1, c_km2, c_motor2 = st.columns(3)
        
        with c_km1:
            st.metric("Contactor KM1 (Derecha)", "ON" if st.session_state.KM1_CW else "OFF")
        with c_km2:
            st.metric("Contactor KM2 (Izquierda)", "ON" if st.session_state.KM2_CCW else "OFF")
            
        with c_motor2:
            if st.session_state.KM1_CW:
                st.markdown('<div class="motor-container"><div class="motor-axis spin-clockwise">⚙️</div><h3 class="motor-run-cw">GIRO DERECHA (CW)</h3></div>', unsafe_allow_html=True)
            elif st.session_state.KM2_CCW:
                st.markdown('<div class="motor-container"><div class="motor-axis spin-counterclockwise">⚙️</div><h3 class="motor-run-ccw">GIRO IZQUIERDA (CCW)</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="motor-container"><div class="motor-axis motor-stop">⚙️</div><h3 class="motor-stop">MOTOR DETENIDO</h3></div>', unsafe_allow_html=True)

        st.markdown("#### 📐 Ecuaciones de Enclavamiento Cruzado:")
        st.code("KM1 = Q2 * /F2 * /S0 * (S1 + KM1) * /KM2  (Bloqueo por KM2)\nKM2 = Q2 * /F2 * /S0 * (S2 + KM2) * /KM1  (Bloqueo por KM1)", language="python")

# ==========================================
# TAB 3: ARRANQUE ESTRELLA-TRIÁNGULO
# ==========================================
with tab3:
    st.header("Arranque Temporizado Estrella - Triángulo")
    st.info("📉 **Objetivo didáctico:** Reducir la corriente de arranque ($I_a$) del motor trifásico. Arranca en Estrella ($\lambda$) para reducir la tensión por fase a $230\text{ V}$, y pasados unos segundos conmuta a Triángulo ($\Delta$) para trabajar a la tensión nominal de $400\text{ V}$.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🕹️ Mandos del Sistema")
        q3 = st.toggle("🔌 Disyuntor Potencia (Q3)", value=True)
        s3_stop = st.button("🔴 Parar Proceso (S3)", use_container_width=True)
        s4_start = st.button("🚀 Iniciar Secuencia Estrella-Triángulo (S4)", use_container_width=True)
        
        t_config = st.slider("⏱️ Ajuste del Temporizador KT1 (Segundos)", min_value=2, max_value=8, value=4)
        
        if s3_stop or not q3:
            st.session_state.KM1_LINEA = False
            st.session_state.KM2_ESTRELLA = False
            st.session_state.KM3_TRIANGULO = False
            st.session_state.C3_RUNNING = False

    with col2:
        st.subheader("📈 Ejecución de la Maniobra en Tiempo Real")
        
        # Hilo de ejecución de la temporización mediante simulación controlada
        if s4_start and q3 and not st.session_state.C3_RUNNING:
            st.session_state.C3_RUNNING = True
            # Fase 1: Línea + Estrella
            st.session_state.KM1_LINEA = True
            st.session_state.KM2_ESTRELLA = True
            st.session_state.KM3_TRIANGULO = False
            
            # Crear barra de progreso visual para el profesorado
            progreso_bar = st.progress(0, text="Fase de Estrella (⚡ Reducción de Intensidad)")
            for i in range(100):
                time.sleep(t_config / 100)
                progreso_bar.progress(i + 1)
            
            # Fase 2: Conmutación a Triángulo (Paso por cero/corte)
            st.session_state.KM2_ESTRELLA = False
            st.session_state.KM3_TRIANGULO = True
            progreso_bar.empty()
            st.success("✅ Conmutación completada con éxito: Motor trabajando a pleno régimen en Triángulo.")

        # Visualización de los tres contactores concurrentes
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.metric("LÍNEA (KM1)", "CONECTADO" if st.session_state.KM1_LINEA else "DESCONECTADO")
        with col_c2:
            st.metric("ESTRELLA (KM2)", "CONECTADO" if st.session_state.KM2_ESTRELLA else "DESCONECTADO")
        with col_c3:
            st.metric("TRIÁNGULO (KM3)", "CONECTADO" if st.session_state.KM3_TRIANGULO else "DESCONECTADO")

        # Estado del motor final
        if st.session_state.KM1_LINEA and st.session_state.KM2_ESTRELLA:
            st.warning("⚙️ **Modo Actual:** Funcionando en CONEXIÓN ESTRELLA ($I$ reducida a $\\frac{1}{3}$)")
        elif st.session_state.KM1_LINEA and st.session_state.KM3_TRIANGULO:
            st.success("⚙️ **Modo Actual:** Funcionando en CONEXIÓN TRIÁNGULO (Par y Potencia Máxima nominal)")
        else:
            st.info("💤 Sistema en espera de rearme o arranque.")
