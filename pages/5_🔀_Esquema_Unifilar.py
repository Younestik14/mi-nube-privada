import streamlit as st

st.set_page_config(page_title="Esquema Unifilar", page_icon="🔀", layout="wide")

st.title("🔀 Módulo 5: Generación de Esquema Unifilar")
st.markdown("Representación lógica y jerárquica de la instalación eléctrica.")

# Recuperar datos del proyecto
elementos_proyecto = st.session_state.get('proyecto', {})

if not elementos_proyecto:
    st.warning("⚠️ No se han encontrado circuitos calculados. Vuelve a los módulos anteriores para guardar líneas, motores o sistemas FV.")
else:
    # --- CONFIGURACIÓN DEL CUADRO GENERAL ---
    with st.sidebar:
        st.header("🛡️ Protecciones de Cabecera")
        nombre_cuadro = st.text_input("Nombre del Cuadro Principal", value="Cuadro General (CGMP)")
        iga_calibre = st.selectbox("Calibre IGA (A)", [25, 32, 40, 50, 63, 80, 100, 125], index=2)
        dif_sensibilidad = st.selectbox("Sensibilidad Diferencial (mA)", [30, 300, 500], index=0)

    st.subheader(f"Esquema Lógico: {nombre_cuadro}")
    
    # --- CONSTRUCCIÓN DEL DIAGRAMA CON GRAPHVIZ ---
    # Creamos el código DOT (lenguaje de descripción de gráficos)
    dot_code = f"""
    digraph G {{
        rankdir=LR;
        node [shape=box, style=filled, color="#E1E4E8", fontname="Arial"];
        
        // Nodo Principal
        RAIZ [label="{nombre_cuadro}\\nIGA: {iga_calibre}A | Dif: {dif_sensibilidad}mA", fillcolor="#005088", fontcolor=white];
    """

    # Añadimos los circuitos guardados al diagrama
    for i, (nombre, datos) in enumerate(elementos_proyecto.items()):
        # Limpiar nombre para evitar errores en DOT
        node_id = f"CIRC_{i}"
        
        # Definir etiquetas según el tipo de carga
        if "sistema" in datos: # Es una línea (Módulo 1)
            label = f"{nombre}\\nSecc: {datos['seccion']}mm² {datos['material']}\\nI_calc: {datos['intensidad']}A"
            color = "#D0E0E3"
        elif "potencia_kwp" in datos: # Es FV (Módulo 2)
            label = f"SISTEMA SOLAR: {nombre}\\nPot: {datos['potencia_kwp']}kWp | {datos['num_paneles']} Paneles"
            color = "#FFF2CC"
        elif "kvar_bateria" in datos: # Es Motor (Módulo 3)
            label = f"MOTOR: {nombre}\\nPot: {datos['potencia_kw']}kW | I_nom: {datos['intensidad']}A"
            color = "#FAD7A0"
        else:
            label = nombre
            color = "#E1E4E8"

        dot_code += f'    {node_id} [label="{label}", fillcolor="{color}"];\n'
        dot_code += f'    RAIZ -> {node_id};\n'

    dot_code += "}"

    # Renderizar el gráfico
    st.graphviz_chart(dot_code)

    # --- TABLA DETALLADA DE PROTECCIONES ---
    st.write("---")
    st.subheader("📋 Detalle de Aparamenta por Circuito")
    
    detalles = []
    for nombre, datos in elementos_proyecto.items():
        if "intensidad" in datos:
            i_nom = datos["intensidad"]
            # Lógica simple de selección de PIA (Pequeño Interruptor Automático)
            pias_estandar = [6, 10, 16, 20, 25, 32, 40, 50, 63]
            pia_sugerido = 63
            for p in pias_estandar:
                if p >= i_nom * 1.1: # Margen del 10%
                    pia_sugerido = p
                    break
            
            detalles.append({
                "Circuito": nombre,
                "Intensidad Calc.": f"{i_nom} A",
                "PIA Sugerido": f"{pia_sugerido} A",
                "Curva": "C" if "Motor" not in str(datos.get("tipo")) else "D",
                "Diferencial": f"2x40A / {dif_sensibilidad}mA" if iga_calibre <= 40 else f"4x63A / {dif_sensibilidad}mA"
            })
    
    if detalles:
        st.table(detalles)
    
    st.info("💡 Este diagrama representa la conexión aguas abajo del Cuadro Principal. Puedes descargar la imagen haciendo clic derecho sobre el diagrama.")

# Guardar en el estado para la memoria técnica
st.session_state['cuadro_general'] = {
    "nombre": nombre_cuadro if elementos_proyecto else "",
    "iga": iga_calibre if elementos_proyecto else 0
}
