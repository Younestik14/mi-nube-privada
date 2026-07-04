import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mediciones y Presupuesto", page_icon="📊", layout="wide")

st.title("📊 Módulo 4: Mediciones y Presupuesto")
st.markdown("Generación automática de presupuesto a partir de los elementos calculados y partidas auxiliares.")

# Inicializar la base de datos de precios por defecto si no existe
if 'precios_base' not in st.session_state:
    st.session_state['precios_base'] = {
        "Cable Cu (por metro)": 2.50,
        "Panel Solar 450Wp (ud)": 120.00,
        "Inversor Solar (ud)": 800.00,
        "Batería Condensadores (kVAr)": 45.00,
        "Mano de obra Oficial 1ª (h)": 28.00,
        "Pequeño Material y canalización (m)": 5.00
    }

# Verificar si hay datos guardados de los módulos anteriores
elementos_proyecto = st.session_state.get('proyecto', {})

# --- VISTA DE PRECIOS BASE ---
with st.expander("💰 Configurar Cuadro de Precios Unitarios"):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.session_state['precios_base']["Cable Cu (por metro)"] = st.number_input("Precio Cable Cu (€/m)", value=st.session_state['precios_base']["Cable Cu (por metro)"])
        st.session_state['precios_base']["Panel Solar 450Wp (ud)"] = st.number_input("Precio Módulo FV (€/ud)", value=st.session_state['precios_base']["Panel Solar 450Wp (ud)"])
        st.session_state['precios_base']["Inversor Solar (ud)"] = st.number_input("Precio Inversor Estándar (€)", value=st.session_state['precios_base']["Inversor Solar (ud)"])
    with col_p2:
        st.session_state['precios_base']["Batería Condensadores (kVAr)"] = st.number_input("Precio Reactiva (€/kVAr)", value=st.session_state['precios_base']["Batería Condensadores (kVAr)"])
        st.session_state['precios_base']["Mano de obra Oficial 1ª (h)"] = st.number_input("Mano de obra (€/h)", value=st.session_state['precios_base']["Mano de obra Oficial 1ª (h)"])

st.write("---")

# --- CONSTRUCCIÓN DEL PRESUPUESTO AUTOMÁTICO ---
st.subheader("📋 Partidas Generadas Automáticamente")

filas_presupuesto = []

if not elementos_proyecto:
    st.info("⚠️ No hay elementos guardados desde los módulos de cálculo. Se puede armar el presupuesto con partidas manuales abajo.")
else:
    # Procesar lo que venga del Módulo 1, 2 y 3
    for nombre, datos in elementos_proyecto.items():
        if "sistema" in datos: # Es una línea eléctrica (Módulo 1)
            longitud = datos["longitud"]
            precio_u = st.session_state['precios_base']["Cable Cu (por metro)"] * (datos["seccion"] / 6) # Factor corrector simple por sección
            filas_presupuesto.append({
                "Código": "GEN-CABLE",
                "Descripción": f"Conductor {datos['material']} de {datos['seccion']} mm² para '{nombre}'",
                "Cantidad": longitud,
                "Precio Unitario (€)": round(precio_u, 2),
                "Total (€)": round(longitud * precio_u, 2)
            })
        elif "potencia_kwp" in datos: # Es fotovoltaica (Módulo 2)
            # Paneles
            num_paneles = datos["num_paneles"]
            precio_p = st.session_state['precios_base']["Panel Solar 450Wp (ud)"]
            filas_presupuesto.append({
                "Código": "FV-PANEL",
                "Descripción": f"Módulo fotovoltaico de 450Wp para '{nombre}'",
                "Cantidad": num_paneles,
                "Precio Unitario (€)": precio_p,
                "Total (€)": round(num_paneles * precio_p, 2)
            })
            # Inversor (Aproximación técnica: 1 ud si hay paneles)
            precio_inv = st.session_state['precios_base']["Inversor Solar (ud)"]
            filas_presupuesto.append({
                "Código": "FV-INV",
                "Descripción": f"Inversor solar acoplado a red / aislada para '{nombre}'",
                "Cantidad": 1,
                "Precio Unitario (€)": precio_inv,
                "Total (€)": precio_inv
            })
        elif "kvar_bateria" in datos: # Es carga industrial (Módulo 3)
            kvar = datos["kvar_bateria"]
            if kvar > 0:
                precio_b = st.session_state['precios_base']["Batería Condensadores (kVAr)"]
                filas_presupuesto.append({
                    "Código": "IND-BAT",
                    "Descripción": f"Equipo de compensación de reactiva de {kvar} kVAr para '{nombre}'",
                    "Cantidad": 1,
                    "Precio Unitario (€)": round(kvar * precio_b, 2),
                    "Total (€)": round(kvar * precio_b, 2)
                })

# --- AÑADIR PARTIDAS MANUALES (Mano de obra, etc.) ---
st.write("---")
st.subheader("➕ Añadir Partidas Manuales / Auxiliares")

col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
with col_m1:
    desc_manual = st.text_input("Descripción de la partida", value="Instalación, conexionado y puesta en marcha")
with col_m2:
    cant_manual = st.number_input("Cantidad", value=10.0, step=1.0)
with col_m3:
    precio_manual = st.number_input("Precio Unitario (€)", value=st.session_state['precios_base']["Mano de obra Oficial 1ª (h)"], step=5.0)

if 'partidas_manuales' not in st.session_state:
    st.session_state['partidas_manuales'] = []

if st.button("Agregar Partida al Presupuesto"):
    st.session_state['partidas_manuales'].append({
        "Código": "MAN-MANUAL",
        "Descripción": desc_manual,
        "Cantidad": cant_manual,
        "Precio Unitario (€)": precio_manual,
        "Total (€)": round(cant_manual * precio_manual, 2)
    })
    st.success("Partida añadida.")

# Consolidar todas las partidas
todas_las_partidas = filas_presupuesto + st.session_state['partidas_manuales']

if todas_las_partidas:
    df_presupuesto = pd.DataFrame(todas_las_partidas)
    st.dataframe(df_presupuesto, use_container_width=True)
    
    # --- RESUMEN ECONÓMICO FINAL ---
    st.write("---")
    st.subheader("📊 Resumen Económico")
    
    base_imponible = df_presupuesto["Total (€)"].sum()
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        beneficio_pct = st.slider("Margen de Beneficio Industrial / Gastos (%)", min_value=0, max_value=40, value=15)
        iva_pct = st.selectbox("Impuesto (IVA %)", [21, 10, 0], index=0)
    
    total_con_beneficio = base_imponible * (1 + (beneficio_pct / 100.0))
    cuota_iva = total_con_beneficio * (iva_pct / 100.0)
    precio_final_venta = total_con_beneficio + cuota_iva
    
    with col_r2:
        st.markdown(f"**Base Imponible de Mediciones:** {base_imponible:,.2f} €")
        st.markdown(f"**Con Beneficio Industrial ({beneficio_pct}%):** {total_con_beneficio:,.2f} €")
        st.markdown(f"**IVA ({iva_pct}%):** {cuota_iva:,.2f} €")
        st.write("### 💰 TOTAL PRESUPUESTO:")
        st.title(f"{precio_final_venta:,.2f} €")
        
    # Guardar presupuesto en el session state general para exportaciones
    st.session_state['resumen_economico'] = {
        "base_imponible": base_imponible,
        "total_con_beneficio": total_con_beneficio,
        "precio_final": precio_final_venta,
        "partidas": todas_las_partidas
    }
else:
    st.warning("El presupuesto está vacío por ahora.")
