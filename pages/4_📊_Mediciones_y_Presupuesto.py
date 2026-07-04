import streamlit as st
import pandas as pd
import streamlit as st
# 1. Importas tus funciones de estilo desde la carpeta utils
from utils.style import aplicar_estilo_global, generar_banner
from seguridad import verificar_sesion
verificar_sesion()
# ... resto de tu código de la página ...
# 2. Configuras la página de Streamlit
st.set_page_config(page_title="Mi Apartado - IDEA", layout="wide", initial_sidebar_state="collapsed")

# 3. Aplicas el diseño y generas el banner superior
aplicar_estilo_global()
generar_banner("⚡ Módulo Técnico", "Subtítulo explicativo del cálculo actual.")

# 4. Metes tus componentes dentro de la tarjeta estilizada usando HTML simple
st.markdown('<div class="premium-card"><h4>📋 Parámetros de Diseño</h4>', unsafe_allow_html=True)

# ... AQUÍ VA TODO TU CÓDIGO NORMAL (st.text_input, st.selectbox, st.button, etc.) ...

st.markdown('</div>', unsafe_allow_html=True) # <-- Cierras la tarjeta al final

st.set_page_config(page_title="Mediciones y Presupuestos DTIE", page_icon="💰", layout="wide")

st.title("💰 Módulo 4: Mediciones, Justificación de Precios y Presupuesto")
st.markdown("Gestión del presupuesto por capítulos utilizando descripciones comerciales reales y desglose técnico de precios.")

# --- INICIALIZACIÓN DE COEFICIENTES ECONÓMICOS ---
if 'coef_beneficio' not in st.session_state:
    st.session_state['coef_beneficio'] = 0.15
if 'coef_amortizacion' not in st.session_state:
    st.session_state['coef_amortizacion'] = 0.05

# --- BASE DE DATOS AMPLIADA CON COMPONENTES REALES ---
if 'catalogo_productos' not in st.session_state:
    st.session_state['catalogo_productos'] = {
        # --- Cables y Conductores (Métricas Reales) ---
        "Cable unipolar 1.5 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 0.25, "unidad": "ML"},
        "Cable unipolar 2.5 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 0.38, "unidad": "ML"},
        "Cable unipolar 4 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 0.64, "unidad": "ML"},
        "Cable unipolar 6 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 1.30, "unidad": "ML"},
        "Cable unipolar 10 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 2.15, "unidad": "ML"},
        "Cable unipolar 16 mm² flexible libre de halógenos (H07Z1-K)": {"precio_base": 3.40, "unidad": "ML"},
        "Cable de cobre desnudo 35 mm² para línea de toma de tierra": {"precio_base": 4.80, "unidad": "ML"},
        
        # --- Canalizaciones y Conducciones ---
        "Tubo corrugado de PVC métrica 20 mm (aislamiento e instalación empotrada)": {"precio_base": 0.16, "unidad": "ML"},
        "Tubo corrugado de PVC métrica 25 mm (aislamiento e instalación empotrada)": {"precio_base": 0.23, "unidad": "ML"},
        "Tubo rígido de PVC métrica 32 mm (instalaciones superficiales/garajes)": {"precio_base": 0.85, "unidad": "ML"},
        "Canaleta plástica aislante protectora para distribución fija (40x60 mm)": {"precio_base": 2.45, "unidad": "ML"},
        "Bandeja portacables de chapa de acero perforada con tapa (60x100 mm)": {"precio_base": 8.90, "unidad": "ML"},
        
        # --- Envolventes y Cajas ---
        "Cuadro eléctrico Hager VS312PE de superficie (36 módulos, puerta opaca)": {"precio_base": 53.92, "unidad": "ud"},
        "Caja de registro y distribución empotrable Solera (160x100x50 mm)": {"precio_base": 1.30, "unidad": "ud"},
        "Caja de registro empotrable general Solera (250x250x60 mm)": {"precio_base": 2.96, "unidad": "ud"},
        "Caja universal Solera para mecanismos enlazables (1 elemento)": {"precio_base": 0.13, "unidad": "ud"},
        
        # --- Aparamenta de Cabecera y Protecciones REBT ---
        "Protector combinado contra sobretensiones permanentes y transitorias Schneider (1P+N, 40A)": {"precio_base": 56.20, "unidad": "ud"},
        "Interruptor General Automático (IGA) Schneider Resi9 (2P, 40A, Curva C)": {"precio_base": 18.50, "unidad": "ud"},
        "Interruptor Diferencial Schneider Resi9 (2P, 25A, 30mA, Clase AC)": {"precio_base": 13.82, "unidad": "ud"},
        "Interruptor Diferencial Superinmunizado Hager (2P, 40A, 30mA, Clase A)": {"precio_base": 42.10, "unidad": "ud"},
        "Bloque diferencial rearmable automático autocontrolado (2P, 40A)": {"precio_base": 115.00, "unidad": "ud"},
        
        # --- Pequeño Material y Mecanismos (Series Comerciales) ---
        "Interruptor automático magnetotérmico Schneider Resi9 10A (Alumbrado)": {"precio_base": 3.60, "unidad": "ud"},
        "Interruptor automático magnetotérmico Hager DPN 16A (Tomas corrientes)": {"precio_base": 9.31, "unidad": "ud"},
        "Interruptor automático magnetotérmico Schneider Resi9 25A (Cocina/Horno)": {"precio_base": 3.64, "unidad": "ud"},
        "Interruptor monopolar Niessen Zenit (Color Blanco, incluye bastidor)": {"precio_base": 2.44, "unidad": "ud"},
        "Conmutador rotativo o empotrable Niessen Zenit (Color Blanco)": {"precio_base": 2.42, "unidad": "ud"},
        "Cruzamiento para conmutación múltiple Niessen Zenit": {"precio_base": 5.74, "unidad": "ud"},
        "Pulsador básico Niessen Zenit para telerruptores o timbres": {"precio_base": 3.28, "unidad": "ud"},
        "Base de enchufe bipolar con toma de tierra Niessen Zenit (16A)": {"precio_base": 2.79, "unidad": "ud"},
        "Base de enchufe de fuerza Simon para cocina y horno (2 polos + T, 25A)": {"precio_base": 7.10, "unidad": "ud"},
        
        # --- Automatización, Conectividad y Auxiliares ---
        "Módulo Autómata Programable LOGO! 24RCEO (Siemens, alimentación 24V)": {"precio_base": 145.00, "unidad": "ud"},
        "Fuente de alimentación conmutada para carril DIN (230V CA a 24V CC, 2.5A)": {"precio_base": 32.40, "unidad": "ud"},
        "Pica de toma de tierra de acero cobreado (Longitud 1.5 metros, diametral)": {"precio_base": 14.20, "unidad": "ud"},
        "Timbre acústico o zumbador electrónico modular para carril DIN": {"precio_base": 24.73, "unidad": "ud"},
        "Regleta de conexión de bornes de 12 polos (Sección 4mm² Lexman)": {"precio_base": 0.54, "unidad": "ud"},
        "Regleta de conexión de bornes de 12 polos (Sección 25mm² Lexman)": {"precio_base": 2.45, "unidad": "ud"},
        "Portalámparas básico E27 curvo para superficie": {"precio_base": 1.84, "unidad": "ud"},
        
        # --- Mano de Obra Técnica ---
        "Hora de oficial de 1ª electricista para montaje, conexionado y pruebas": {"precio_base": 33.00, "unidad": "horas"},
        "Hora de operario para apertura de rozas, recibido con yeso y limpieza": {"precio_base": 29.00, "unidad": "horas"}
    }

if 'capitulos_presupuesto' not in st.session_state:
    st.session_state['capitulos_presupuesto'] = {
        "CAPÍTULO I: DERIVACIÓN INDIVIDUAL": [],
        "CAPÍTULO II: CUADRO DE PROTECCIÓN": [],
        "CAPÍTULO III: CIRCUITO DE ILUMINACIÓN": [],
        "CAPÍTULO IV: TOMAS DE USO GENERAL": [],
        "CAPÍTULO V: CIRCUITO DE COCINA Y HORNO": [],
        "CAPÍTULO VI: LAVADORA Y TERMO": [],
        "CAPÍTULO VII: BAÑOS Y COCINA": [],
        "CAPÍTULO VIII: TELEFONÍA, TV Y PORTERO": []
    }

tabs_p = st.tabs(["🗂️ 1. Catálogo y Coeficientes", "📝 2. Añadir Partidas por Capítulo", "📊 3. Presupuesto y Resumen General"])

# --- TAB 1: GESTIÓN DE PRODUCTOS Y PRECIOS BASE ---
with tabs_p[0]:
    st.subheader("⚙️ Parámetros Económicos de Justificación de Precios")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.session_state['coef_beneficio'] = st.number_input("Coeficiente de Beneficio Industrial (BI)", value=0.15, step=0.01, format="%.2f")
    with col_e2:
        st.session_state['coef_amortizacion'] = st.number_input("Coeficiente de Gastos Generales / Amortización", value=0.05, step=0.01, format="%.2f")
        
    st.write("---")
    st.subheader("📦 Catálogo de Aparamenta y Precios de Venta")
    
    tabla_cat = []
    for descripcion, datos in st.session_state['catalogo_productos'].items():
        p_base = datos["precio_base"]
        bi = p_base * st.session_state['coef_beneficio']
        am = p_base * st.session_state['coef_amortizacion']
        p_venta = p_base + bi + am
        tabla_cat.append({
            "Designación Comercial del Material": descripcion,
            "Unidad": datos["unidad"],
            "Precio Base (€)": round(p_base, 2),
            "B.I. (€)": round(bi, 3),
            "Amort. (€)": round(am, 3),
            "Precio Venta Unitario (€)": round(p_venta, 3)
        })
    st.dataframe(pd.DataFrame(tabla_cat), use_container_width=True, hide_index=True)
   # --- TAB 2: REGISTRO DE PARTIDAS CON REDONDEO A 2 DECIMALES (PARTE 2) ---
with tabs_p[1]:
    st.subheader("📝 Gestión de Partidas e Mediciones")
    
    with st.form("form_partida"):
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            capitulo_sel = st.selectbox("Selecciona el Capítulo:", list(st.session_state['capitulos_presupuesto'].keys()))
            materiales_reales = list(st.session_state['catalogo_productos'].keys())
            material_sel = st.selectbox("Selección de Material / Equipo Comercial:", materiales_reales)
            
        with col_f2:
            num_partidas_actuales = len(st.session_state['capitulos_presupuesto'][capitulo_sel])
            prefijo = capitulo_sel.split(":")[0].replace("CAPÍTULO ", "").strip()
            num_partida = st.text_input("Número de Partida", value=f"{prefijo}.{num_partidas_actuales + 1}")
            medicion = st.number_input("Medición / Cantidad", value=1.0, min_value=0.01, step=1.0)
            
        with col_f3:
            st.markdown("**Desglose de Costes Unitarios:**")
            prod_info = st.session_state['catalogo_productos'][material_sel]
            st.info(f"Unidad de Medida: {prod_info['unidad']}\n\nPrecio de Coste Base: {round(prod_info['precio_base'], 2)} €")
            
        btn_partida = st.form_submit_button("➕ Registrar Partida en el Presupuesto")
        
        if btn_partida:
            base_p = round(prod_info['precio_base'], 2)
            bi_p = round(base_p * st.session_state['coef_beneficio'], 2)
            am_p = round(base_p * st.session_state['coef_amortizacion'], 2)
            precio_venta_unitario = round(base_p + bi_p + am_p, 2)
            importe_total_partida = round(precio_venta_unitario * medicion, 2)
            
            st.session_state['capitulos_presupuesto'][capitulo_sel].append({
                "partida": num_partida,
                "designacion": material_sel,
                "unidades": prod_info['unidad'],
                "medicion": medicion,
                "precio_base": base_p,
                "bi": bi_p,
                "amortizacion": am_p,
                "precio_venta": precio_venta_unitario,
                "importe": importe_total_partida
            })
            st.success(f"Partida {num_partida} guardada en {capitulo_sel}.")

# --- TAB 3: DESGLOSE DE CAPÍTULOS Y HOJA DE CABECERA TOTAL (2 DECIMALES) ---
with tabs_p[2]:
    st.subheader("📊 Estructura de Capítulos del Proyecto")
    
    costes_parciales_capitulos = {}
    total_subtotal = 0.0
    
    for cap, partidas in st.session_state['capitulos_presupuesto'].items():
        st.markdown(f"#### 📁 {cap}")
        if not partidas:
            st.caption("Sin partidas registradas.")
            costes_parciales_capitulos[cap] = 0.0
        else:
            df_partidas = pd.DataFrame(partidas)
            df_visible = df_partidas[[
                "partida", "designacion", "unidades", "medicion", 
                "precio_base", "bi", "amortizacion", "precio_venta", "importe"
            ]].copy()
            
            # Formatear visualmente las columnas numéricas a 2 decimales fijos
            columnas_precio = ["precio_base", "bi", "amortizacion", "precio_venta", "importe"]
            for col in columnas_precio:
                df_visible[col] = df_visible[col].map("{:.2f}".format)
            
            df_visible.columns = [
                "Partida", "Designación Material Comercial", "Unidades", "Medición", 
                "Precio Base (€)", "B.I. (€)", "Amort. (€)", "Precio Venta (€)", "Importe (€)"
            ]
            
            st.dataframe(df_visible, use_container_width=True, hide_index=True)
            
            coste_cap = round(df_partidas["importe"].sum(), 2)
            costes_parciales_capitulos[cap] = coste_cap
            total_subtotal += coste_cap
            st.markdown(f"**Coste Parcial del Capítulo:** `{'{:.2f}'.format(coste_cap)} €`")
        st.write("---")

    # --- HOJA RESUMEN GENERAL DEL PRESUPUESTO ---
    st.subheader("📉 RESUMEN GENERAL DEL PRESUPUESTO")
    
    resumen_data = []
    for cap, parcial in costes_parciales_capitulos.items():
        resumen_data.append({
            "Capítulo Eléctrico": cap,
            "Coste Parcial Real (€)": "{:.2f}".format(parcial)
        })
        
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Cierre de Liquidación con 2 decimales
    total_subtotal = round(total_subtotal, 2)
    iva_porcentaje = 0.21
    importe_iva = round(total_subtotal * iva_porcentaje, 2)
    total_general = round(total_subtotal + importe_iva, 2)
    
    # Algoritmo de transcripción nativa a texto legal (2 decimales estrictos)
    def numero_a_letras(numero):
        def _convertir_grupo(n):
            unidades = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
            decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
            especiales = {11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince", 
                          16: "dieciséis", 17: "diecisiete", 18: "diecocho", 19: "diecinueve"}
            centenas = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", 
                        "seiscientos", "setecientos", "ochocientos", "novecientos"]
            if n == 100: return "cien"
            u = n % 10
            d = (n // 10) % 10
            c = n // 100
            res = centenas[c]
            dec_val = d * 10 + u
            if dec_val in especiales:
                res += " " + especiales[dec_val]
            else:
                if d > 0:
                    if d == 2 and u > 0: res += " veinti" + unidades[u]
                    else:
                        res += " " + decenas[d]
                        if u > 0: res += " y " + unidades[u]
                elif u > 0: res += " " + unidades[u]
            return res.strip()

        partes = str(round(numero, 2)).split('.')
        enteros = int(partes[0])
        centimos = int(partes[1]) if len(partes) > 1 else 0
        if len(partes) > 1 and len(partes[1]) == 1: 
            centimos *= 10

        if enteros == 0: txt_ent = "cero"
        elif enteros < 1000: txt_ent = _convertir_grupo(enteros)
        elif enteros < 1000000:
            m = enteros // 1000
            r = enteros % 1000
            txt_m = "mil" if m == 1 else f"{_convertir_grupo(m)} mil"
            txt_ent = f"{txt_m} {_convertir_grupo(r)}".strip()
        else: txt_ent = f"{enteros} euros"

        if txt_ent.endswith("un"): txt_ent += "o"
        txt_cen = _convertir_grupo(centimos) if centimos > 0 else "cero"
        if txt_cen.endswith("un"): txt_cen += "o"
        return f"{txt_ent} euros con {txt_cen} céntimos".capitalize()

    st.write("### 🧾 Resumen Económico del Presupuesto de Contrata")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric(label="SUBTOTAL (Ejecución Material)", value=f"{'{:.2f}'.format(total_subtotal)} €")
    with col_t2:
        st.metric(label="I.V.A. Presupuestario (21%)", value=f"{'{:.2f}'.format(importe_iva)} €")
    with col_t3:
        st.metric(label="TOTAL PRESUPUESTO CONTRATA", value=f"{'{:.2f}'.format(total_general)} €")
        
    st.markdown(f"> **Importe en letra oficial:** *{numero_a_letras(total_general)}*")

    # --- RESET BUTTON ---
    if st.button("🗑️ Vaciar Hojas y Mediciones"):
        for cap in st.session_state['capitulos_presupuesto']:
            st.session_state['capitulos_presupuesto'][cap] = []
        st.rerun()
