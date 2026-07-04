import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mediciones y Presupuestos DTIE", page_icon="💰", layout="wide")

st.title("💰 Módulo 4: Mediciones, Justificación de Precios y Presupuesto")
st.markdown("Estructuración del presupuesto por capítulos a partir de la base de datos de productos y coeficientes económicos.")

# --- INICIALIZACIÓN DE LA BASE DE DATOS ESTRUCTURADA ---
# Coeficientes por defecto del Excel de origen: BI (15%) y Amortización/Gastos (5%)
if 'coef_beneficio' not in st.session_state:
    st.session_state['coef_beneficio'] = 0.15
if 'coef_amortizacion' not in st.session_state:
    st.session_state['coef_amortizacion'] = 0.05

# Catálogo base de materiales precargados del CSV 'Productos'
if 'catalogo_productos' not in st.session_state:
    st.session_state['catalogo_productos'] = {
        "1,5mm": {"descripcion": "Cable 1.5mm² flexible normal 750V H071-K", "precio_base": 0.25, "unidad": "ML"},
        "2,5mm": {"descripcion": "Cable eléctrico unipolar 2.5mm² libre de halógenos", "precio_base": 0.38, "unidad": "ML"},
        "4mm": {"descripcion": "Cable por metros de 4mm² libre halogenos", "precio_base": 0.64, "unidad": "ML"},
        "6mm": {"descripcion": "Cable corte TOP CABLE solar h1z272-k 6mm negro", "precio_base": 1.30, "unidad": "ML"},
        "20mm": {"descripcion": "Tubo corrugado Gaestopas Corruflex 901.2000.0 métrica 20 una capa", "precio_base": 0.16, "unidad": "ML"},
        "25mm": {"descripcion": "Tubo corrugado Gaestopas Corruflex 901.2500.0 métrica 25 una capa", "precio_base": 0.23, "unidad": "ML"},
        "Cuadro": {"descripcion": "Cuadro eléctrico Hager VS312PE 36 módulos superficie", "precio_base": 53.92, "unidad": "ud"},
        "IGA": {"descripcion": "Protector combinado sobretensiones R9L20640 1P+N 40A Resi9 Combi SPU Schneider", "precio_base": 56.20, "unidad": "ud"},
        "DIF": {"descripcion": "Diferencial Schneider R9R51240 Resi9 25A 30mA", "precio_base": 13.82, "unidad": "ud"},
        "PIA10": {"descripcion": "Automático magnetotérmico Schneider R9F12610 Resi9 10A", "precio_base": 3.60, "unidad": "ud"},
        "PIA16": {"descripcion": "Automatico magnetotermico DPN Hager 16A 1P+N MN916V", "precio_base": 9.31, "unidad": "ud"},
        "PIA25": {"descripcion": "Automático magnetotérmico Schneider R9F12625 Resi9 25A", "precio_base": 3.64, "unidad": "ud"},
        "Elec": {"descripcion": "Hora de oficial de 1ª electricista para trabajos de montaje y conexionado", "precio_base": 33.00, "unidad": "horas"},
        "Oper": {"descripcion": "Hora de operario para apertura de hueco, recibido con yeso y limpieza", "precio_base": 29.00, "unidad": "horas"}
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

# --- PESTAÑAS PRINCIPALES EN PANTALLA CENTRAL ---
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
    st.subheader("📦 Catálogo de Productos Disponibles")
    
    # Crear DataFrame dinámico calculando el precio final con la fórmula del Excel
    tabla_cat = []
    for cod, datos in st.session_state['catalogo_productos'].items():
        p_base = datos["precio_base"]
        bi = p_base * st.session_state['coef_beneficio']
        am = p_base * st.session_state['coef_amortizacion']
        p_venta = p_base + bi + am
        tabla_cat.append({
            "Código": cod,
            "Descripción": datos["descripcion"],
            "Unidad": datos["unidad"],
            "Precio Base (€)": round(p_base, 2),
            "B.I. (€)": round(bi, 3),
            "Amort. (€)": round(am, 3),
            "Precio Venta Venta (€)": round(p_venta, 3)
        })
    st.dataframe(pd.DataFrame(tabla_cat), use_container_width=True, hide_index=True)
    # --- TAB 2: AÑADIR PARTIDAS POR CAPÍTULO (PARTE 2) ---
with tabs_p[1]:
    st.subheader("📝 Gestión de Partidas e Mediciones")
    
    with st.form("form_partida"):
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            capitulo_sel = st.selectbox("Selecciona el Capítulo:", list(st.session_state['capitulos_presupuesto'].keys()))
            # Obtener códigos del catálogo
            codigos_disponibles = list(st.session_state['catalogo_productos'].keys())
            codigo_sel = st.selectbox("Código del Producto / Material:", codigos_disponibles)
            
        with col_f2:
            # Generar número de partida orientativo según el orden actual del capítulo
            num_partidas_actuales = len(st.session_state['capitulos_presupuesto'][capitulo_sel])
            prefijo = capitulo_sel.split(":")[0].replace("CAPÍTULO ", "").strip()
            num_partida = st.text_input("Número de Partida", value=f"{prefijo}.{num_partidas_actuales + 1}")
            medicion = st.number_input("Medición / Cantidad", value=1.0, min_value=0.01, step=1.0)
            
        with col_f3:
            st.markdown("**Vista previa del coste básico:**")
            prod_info = st.session_state['catalogo_productos'][codigo_sel]
            st.info(f"{prod_info['descripcion']}\n\nPrecio Base: {prod_info['precio_base']} € / {prod_info['unidad']}")
            
        btn_partida = st.form_submit_button("➕ Registrar Partida en Capítulo")
        
        if btn_partida:
            # Recuperar datos del producto
            base_p = prod_info['precio_base']
            bi_p = base_p * st.session_state['coef_beneficio']
            am_p = base_p * st.session_state['coef_amortizacion']
            precio_final_unitario = base_p + bi_p + am_p
            importe_total_partida = precio_final_unitario * medicion
            
            st.session_state['capitulos_presupuesto'][capitulo_sel].append({
                "codigo": codigo_sel,
                "partida": num_partida,
                "designacion": prod_info['descripcion'],
                "unidades": prod_info['unidad'],
                "medicion": medicion,
                "precio_base": base_p,
                "bi": bi_p,
                "amortizacion": am_p,
                "precio_venta": precio_final_unitario,
                "importe": importe_total_partida
            })
            st.success(f"Partida {num_partida} añadida correctamente a {capitulo_sel}.")

# --- TAB 3: PRESUPUESTO Y RESUMEN GENERAL (ESTRUCTURA EXCEL) ---
with tabs_p[2]:
    st.subheader("📊 Desglose del Presupuesto por Capítulos")
    
    costes_parciales_capitulos = {}
    total_subtotal = 0.0
    
    # Recorrer cada capítulo y dibujar su tabla si tiene contenido
    for cap, partidas in st.session_state['capitulos_presupuesto'].items():
        st.markdown(f"#### 📁 {cap}")
        if not partidas:
            st.caption("No hay partidas registradas en este capítulo.")
            costes_parciales_capitulos[cap] = 0.0
        else:
            df_partidas = pd.DataFrame(partidas)
            # Reordenar columnas para que cuadre visualmente con el Excel
            df_visible = df_partidas[[
                "codigo", "partida", "designacion", "unidades", "medicion", 
                "precio_base", "bi", "amortizacion", "precio_venta", "importe"
            ]].copy()
            
            # Renombrar cabeceras para el usuario
            df_visible.columns = [
                "Código", "Partida", "Designación", "Unidades", "Medición", 
                "Precio Base (€)", "B.I. (€)", "Amort. (€)", "Precio Venta (€)", "Importe (€)"
            ]
            
            st.dataframe(df_visible, use_container_width=True, hide_index=True)
            
            # Calcular coste parcial del capítulo
            coste_cap = df_partidas["importe"].sum()
            costes_parciales_capitulos[cap] = coste_cap
            total_subtotal += coste_cap
            st.markdown(f"**Coste Parcial del Capítulo:** `{round(coste_cap, 3)} €`")
        st.write("---")

    # --- SECCIÓN: RESUMEN DEL PRESUPUESTO ---
    st.subheader("📉 RESUMEN DEL PRESUPUESTO (Hoja de Cabecera)")
    
    resumen_data = []
    for cap, parcial in costes_parciales_capitulos.items():
        resumen_data.append({
            "Capítulo": cap,
            "Coste Parcial (€)": round(parcial, 3)
        })
        
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Cálculos impositivos
    iva_porcentaje = 0.21
    importe_iva = total_subtotal * iva_porcentaje
    total_general = total_subtotal + importe_iva
    
    # Función auxiliar rápida para convertir los totales en la cadena de texto legal del Excel
    def numero_a_letras(numero):
        # Convertir a flotante y separar enteros de céntimos
        enteros = int(str(round(numero, 2)).split('.')[0])
        try:
            centimos = int(str(round(numero, 2)).split('.')[1])
        except IndexError:
            centimos = 0
            
        # Diccionario básico simplificado para la salida formal
        import num2words
        try:
            texto_enteros = num2words.num2words(enteros, lang='es')
            texto_centimos = num2words.num2words(centimos, lang='es') if centimos > 0 else "cero"
            cadena = f"{texto_enteros} euros con {texto_centimos} céntimos".capitalize()
            return cadena
        except ImportError:
            return "Cierre de presupuesto normalizado (Instale num2words para transcripción literal)"

    # Cuadro de totales calcado al Excel
    st.write("### 🧾 Cierre Económico Oficial")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric(label="SUBTOTAL (Presupuesto Ejecución Material)", value=f"{round(total_subtotal, 3)} €")
    with col_t2:
        st.metric(label="I.V.A. Aplicado (21%)", value=f"{round(importe_iva, 3)} €")
    with col_t3:
        st.metric(label="TOTAL PRESUPUESTO CONTRATA", value=f"{round(total_general, 3)} €")
        
    st.markdown(f"> **Importe en letra:** *{numero_a_letras(total_general)}*")

    # --- BOTÓN DE VACIADO ---
    if st.button("🗑️ Reiniciar todas las Mediciones"):
        for cap in st.session_state['capitulos_presupuesto']:
            st.session_state['capitulos_presupuesto'][cap] = []
        st.rerun()
