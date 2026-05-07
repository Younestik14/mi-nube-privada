import streamlit as st
import pandas as pd
import math

# --- 1. CONFIGURACIÓN Y ESTILO DARK ---
st.set_page_config(page_title="Ingeniería Pro - Presupuestos Dinámicos", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 22px;
        background-color: #1f2937; padding: 15px; border-radius: 10px;
        border-left: 6px solid #22d3ee; margin-bottom: 10px; text-align: right;
    }
    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 38px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
        padding: 40px; border-radius: 20px; text-align: center;
        border: 2px solid #ffd700; margin-top: 40px;
    }
    .stExpander { border: 1px solid #374151 !important; background-color: #161b22 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. MOTOR DE CÁLCULO REBT (ESTÁTICO) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
tablas_adm = {
    "A1": {"PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321], "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]},
    "B1": {"PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400], "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]},
    "C":  {"PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461], "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]}
}

def get_seccion_adm(metodo_str, aislamiento, ib):
    m_code = metodo_str.split(" ")[0]
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm.get(m_code, tablas_adm["C"])[ais_key]
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib: return secciones_ref[i]
    return 240

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Navegación")
    modo = st.radio("Seleccionar Módulo:", ["📐 Calculadora REBT", "💰 Presupuesto Maestro"])
    
    if modo == "💰 Presupuesto Maestro":
        st.divider()
        st.subheader("Coeficientes Económicos")
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA (%)", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. CALCULADORA TÉCNICA ---
if modo == "📐 Calculadora REBT":
    st.title("📐 Dimensionamiento de Líneas")
    # ... (Se mantiene la lógica original del cálculo REBT sin cambios)
    c1, c2 = st.columns(2)
    with c1:
        sistema = st.selectbox("Suministro", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia (W)", value=5750)
        longitud = st.number_input("Longitud (m)", value=30.0)
        cos_phi = st.slider("cos φ", 0.70, 1.00, 0.90)
    with c2:
        material = st.radio("Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Instalación", list(tablas_adm.keys()))
        max_cdt = st.number_input("CdT Máx (%)", value=3.0)

    v_fase = 230 if "Mono" in sistema else 400
    ib = potencia / (v_fase * cos_phi) if v_fase == 230 else potencia / (1.732 * v_fase * cos_phi)
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    st.markdown(f'<div class="resultado-caja">SECCIÓN CALCULADA: {s_adm} mm²</div>', unsafe_allow_html=True)

# --- 5. PRESUPUESTO MAESTRO CON CONFIGURACIÓN DE PRECIOS ---
else:
    st.title("💰 Generador de Presupuestos Profesional")
    
    # Creamos sub-pestañas para organizar la configuración y el presupuesto
    tab_config, tab_presupuesto = st.tabs(["🛠️ Configuración de Precios", "📝 Elaboración de Presupuesto"])

    # --- SUBPÁGINA: CONFIGURACIÓN DE PRECIOS ---
    with tab_config:
        st.subheader("Base de Precios Unitarios")
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            st.markdown("### 🔌 Cables (por metro)")
            p_15 = st.number_input("Cable 1.5mm² (€/m)", value=0.28, step=0.01)
            p_25 = st.number_input("Cable 2.5mm² (€/m)", value=0.42, step=0.01)
            p_40 = st.number_input("Cable 4mm² (€/m)", value=0.68, step=0.01)
            p_60 = st.number_input("Cable 6mm² (€/m)", value=1.35, step=0.05)
            p_10 = st.number_input("Cable 10mm² (€/m)", value=2.25, step=0.05)

        with col_c2:
            st.markdown("### 📦 Aparamenta y Otros")
            p_caja = st.number_input("Caja General (€/u)", value=58.00)
            p_prot = st.number_input("Kit Protecciones (€/u)", value=140.0)
            p_meca = st.number_input("Mecanismo medio (€/u)", value=4.50)
            p_base = st.number_input("Base enchufe medio (€/u)", value=5.20)
            p_tierra = st.number_input("Kit Puesta a Tierra (€/u)", value=120.0)

        with col_c3:
            st.markdown("### 👷 Mano de Obra")
            p_oficial = st.number_input("Hora Oficial (€/h)", value=34.00)
            p_ayudante = st.number_input("Hora Ayudante (€/h)", value=28.50)
            st.info("Estos precios se aplicarán automáticamente a todos los capítulos del presupuesto.")

    # Diccionario dinámico de precios basado en los inputs anteriores
    db_dinamica = {
        "cables": {1.5: p_15, 2.5: p_25, 4: p_40, 6: p_60, 10: p_10},
        "items": {"caja": p_caja, "prot": p_prot, "meca": p_meca, "base": p_base, "tierra": p_tierra},
        "mo": {"oficial": p_oficial, "ayudante": p_ayudante}
    }

    # --- SUBPÁGINA: ELABORACIÓN DE PRESUPUESTO ---
    with tab_presupuesto:
        capitulos = []

        def render_capitulo(titulo, lista_materiales, h_of, h_ay):
            with st.expander(titulo):
                c_mat, c_mo = st.columns(2)
                tot_mat = 0
                for item in lista_materiales:
                    q = c_mat.number_input(f"Cantidad: {item['nom']}", value=float(item['def_q']), key=f"q_{titulo}_{item['nom']}")
                    # El precio unitario se toma de la configuración de precios
                    p_unit = item['precio_ref'] 
                    c_mat.caption(f"Precio Unitario Actual: {p_unit} €")
                    tot_mat += (q * p_unit)
                
                st.markdown("---")
                h1 = c_mo.number_input("Horas Oficial", value=float(h_of), key=f"h1_{titulo}")
                h2 = c_mo.number_input("Horas Ayudante", value=float(h_ay), key=f"h2_{titulo}")
                
                tot_mo = (h1 * db_dinamica["mo"]["oficial"]) + (h2 * db_dinamica["mo"]["ayudante"])
                subtotal = (tot_mat + tot_mo)
                total_cap = subtotal * f_multiplicador
                
                st.markdown(f'<div class="resultado-caja">Subtotal: {subtotal:,.2f} €<br>Con GG/BI: {total_cap:,.2f} €</div>', unsafe_allow_html=True)
                return total_cap

        # Definición de Capítulos vinculados a la base de precios dinámica
        capitulos.append(render_capitulo("CAP I: DERIVACIÓN INDIVIDUAL", 
            [{'nom': "Cable 10mm² (m)", 'def_q': 45, 'precio_ref': db_dinamica["cables"][10]}], 3, 2))
        
        capitulos.append(render_capitulo("CAP II: CUADRO GENERAL", 
            [{'nom': "Caja 36 mod", 'def_q': 1, 'precio_ref': db_dinamica["items"]["caja"]},
             {'nom': "Protecciones", 'def_q': 1, 'precio_ref': db_dinamica["items"]["prot"]}], 5, 0))
        
        capitulos.append(render_capitulo("CAP III: ALUMBRADO (C1)", 
            [{'nom': "Mecanismos", 'def_q': 12, 'precio_ref': db_dinamica["items"]["meca"]},
             {'nom': "Cable 1.5mm²", 'def_q': 200, 'precio_ref': db_dinamica["cables"][1.5]}], 8, 4))
        
        capitulos.append(render_capitulo("CAP IV: TOMAS GENERALES (C2)", 
            [{'nom': "Bases 16A", 'def_q': 20, 'precio_ref': db_dinamica["items"]["base"]},
             {'nom': "Cable 2.5mm²", 'def_q': 250, 'precio_ref': db_dinamica["cables"][2.5]}], 10, 6))

        capitulos.append(render_capitulo("CAP IX: PUESTA A TIERRA", 
            [{'nom': "Kit Tierra", 'def_q': 1, 'precio_ref': db_dinamica["items"]["tierra"]}], 2, 2))

        # --- RESUMEN FINAL ---
        st.divider()
        total_proyecto = sum(capitulos)
        total_con_iva = total_proyecto * (1 + iva_tipo/100)
        
        st.markdown(
            f'<div class="total-final-banner">'
            f'TOTAL PRESUPUESTO (IVA {iva_tipo}% INCL.)<br>'
            f'{total_con_iva:,.2f} €'
            f'</div>', 
            unsafe_allow_html=True
        )

        # Botón para descargar reporte simple
        df_resumen = pd.DataFrame({"Capítulo": ["DI", "Cuadro", "C1", "C2", "Tierra"], "Total (€)": capitulos})
        st.download_button("📥 Descargar Resumen (CSV)", df_resumen.to_csv(index=False), "presupuesto.csv", "text/csv")
