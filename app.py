import streamlit as st
import pandas as pd
import math
import io  # Añadido para manejo de memoria

# --- 1. CONFIGURACIÓN Y ESTILO DARK INTEGRAL ---
st.set_page_config(page_title="Ingeniería Pro v3.0 - Full Suite", layout="wide", page_icon="⚡")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stMarkdown, p, span, div { color: #ffffff !important; font-weight: bold !important; }
    
    /* Contenedor de resultados tipo display industrial */
    .resultado-caja {
        color: #ffffff !important; font-weight: 900 !important; font-size: 24px;
        background-color: #1f2937; padding: 20px; border-radius: 12px;
        border-left: 8px solid #22d3ee; margin-bottom: 15px; text-align: right;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }

    /* Banner de presupuesto final */
    .total-final-banner {
        color: #ffffff !important; font-weight: 900 !important; font-size: 42px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d3436 100%);
        padding: 50px; border-radius: 25px; text-align: center;
        border: 3px solid #ffd700; margin-top: 50px;
        box-shadow: 0px 20px 40px rgba(0,0,0,0.7);
    }

    .stExpander { 
        border: 1px solid #374151 !important; border-radius: 15px !important; 
        background-color: #161b22 !important; margin-bottom: 20px !important;
    }

    .stNumberInput input, .stSelectbox div { background-color: #0d1117 !important; color: white !important; }
    
    .footer-container {
        position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%);
        z-index: 9999; pointer-events: none; text-align: center; width: 100%;
    }
    .watermark-text { font-size: 12px; color: rgba(255, 255, 255, 0.15); }
    </style>
    <div class="footer-container"><span class="watermark-text">Younesse Tikent Tifaoui - Senior Technical Consultant</span></div>
    """,
    unsafe_allow_html=True
)

# --- FUNCIÓN PARA CONVERTIR DATAFRAME A EXCEL (AÑADIDO) ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Hoja1')
    return output.getvalue()

# --- 2. MOTOR DE CÁLCULO REBT (MATRIZ UNE-HD 60364-5-52) ---
secciones_ref = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

tablas_adm = {
    "A1 - Empotrado en tubo (Pared aislante)": {
        "PVC": [14.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321],
        "XLPE": [18.5, 25, 33, 43, 59, 77, 102, 126, 153, 194, 233, 268, 307, 352, 415]
    },
    "A2 - Multiconductor en tubo (Pared aislante)": {
        "PVC": [14, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291],
        "XLPE": [17.5, 24, 32, 41, 54, 73, 95, 117, 141, 179, 216, 249, 285, 324, 380]
    },
    "B1 - Conductores en tubo (Sobre pared)": {
        "PVC": [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400],
        "XLPE": [22, 30, 40, 52, 71, 94, 126, 157, 190, 241, 292, 338, 388, 442, 523]
    },
    "B2 - Multiconductor en tubo (Sobre pared)": {
        "PVC": [16.5, 23, 30, 38, 52, 69, 92, 114, 138, 175, 210, 244, 282, 319, 375],
        "XLPE": [21, 28, 38, 49, 66, 88, 117, 146, 175, 222, 269, 312, 358, 408, 481]
    },
    "C - Cable sobre pared de madera/mampostería": {
        "PVC": [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 391, 461],
        "XLPE": [24, 33, 45, 58, 80, 107, 138, 171, 209, 269, 328, 382, 441, 506, 599]
    },
    "D1 - Cable en conductos enterrados": {
        "PVC": [22, 29, 38, 47, 63, 81, 104, 125, 148, 183, 216, 246, 278, 312, 361],
        "XLPE": [26, 34, 44, 56, 73, 95, 121, 146, 173, 213, 252, 287, 324, 363, 419]
    },
    "E - Multiconductor al aire libre": {
        "PVC": [22, 30, 40, 51, 70, 94, 126, 154, 187, 237, 286, 331, 381, 434, 511],
        "XLPE": [26, 36, 49, 63, 86, 115, 149, 185, 225, 289, 352, 410, 473, 542, 641]
    },
    "F - Unipolares en contacto (Bandeja perforada)": {
        "PVC": [21, 28, 38, 50, 68, 92, 121, 150, 184, 233, 282, 327, 376, 428, 505],
        "XLPE": [25, 34, 46, 61, 83, 112, 146, 181, 221, 281, 341, 396, 455, 517, 613]
    }
}

def get_seccion_adm(metodo_key, aislamiento, ib):
    ais_key = "PVC" if "PVC" in aislamiento else "XLPE"
    intensidades = tablas_adm.get(metodo_key, tablas_adm["C - Cable sobre pared de madera/mampostería"])[ais_key]
    for i, i_adm in enumerate(intensidades):
        if i_adm >= ib: return secciones_ref[i]
    return 240

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    modo = st.radio("Módulo de Trabajo:", ["📐 Dimensionado REBT", "💰 Presupuesto Maestro"])
    
    if modo == "💰 Presupuesto Maestro":
        st.divider()
        st.subheader("Coeficientes Económicos")
        gastos_gen = st.slider("% Gastos Generales", 0, 30, 13)
        beneficio_ind = st.slider("% Beneficio Industrial", 0, 20, 6)
        iva_tipo = st.selectbox("IVA Aplicable (%)", [21, 10, 4, 0], index=0)
        f_multiplicador = 1 + (gastos_gen / 100) + (beneficio_ind / 100)
    else:
        f_multiplicador = 1.0

# --- 4. CALCULADORA TÉCNICA ---
if modo == "📐 Dimensionado REBT":
    st.title("📐 Oficina Técnica: Cálculo de Líneas s/ REBT")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Datos de Carga")
        sistema = st.selectbox("Sistema Eléctrico", ["Monofásico 230V", "Trifásico 400V"])
        potencia = st.number_input("Potencia de Cálculo (W)", value=5750, step=100)
        longitud = st.number_input("Longitud de la Línea (m)", value=30.0, step=1.0)
        cos_phi = st.slider("Factor de Potencia (cos φ)", 0.70, 1.00, 0.90)
        uso = st.selectbox("Factor de Uso", ["General (1.0)", "Motores (1.25)", "Lámparas de Descarga (1.8)", "Vehículo Eléctrico (1.25)"])
        k_u = 1.25 if ("Motores" in uso or "Vehículo" in uso) else (1.8 if "Descarga" in uso else 1.0)
    with c2:
        st.subheader("Parámetros de Instalación")
        material = st.radio("Material Conductor", ["Cobre (Cu)", "Aluminio (Al)"], horizontal=True)
        aislamiento = st.radio("Tipo de Aislamiento", ["PVC (70°C)", "XLPE/EPR (90°C)"], horizontal=True)
        metodo_inst = st.selectbox("Método de Instalación (UNE-HD 60364-5-52)", list(tablas_adm.keys()))
        max_cdt = st.number_input("Caída de Tensión Máx. Admitida (%)", value=3.0, step=0.1)

    v_fase = 230 if "Mono" in sistema else 400
    ib = (potencia * k_u) / (v_fase * cos_phi) if v_fase == 230 else (potencia * k_u) / (1.732 * v_fase * cos_phi)
    s_adm = get_seccion_adm(metodo_inst, aislamiento, ib)
    gamma = (48 if "PVC" in aislamiento else 44) if "Cobre" in material else (30 if "PVC" in aislamiento else 28)
    s_cdt = (2 * longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase) if v_fase == 230 else (longitud * potencia) / (gamma * (max_cdt/100 * v_fase) * v_fase)
    s_cdt_norm = next((s for s in secciones_ref if s >= s_cdt), 240)
    s_final = max(s_adm, s_cdt_norm)

    st.divider()
    st.markdown(f'<div class="resultado-caja">SECCIÓN REGLAMENTARIA: {s_final} mm²<br><small style="font-size:14px; font-weight:normal;">Intensidad (Ib): {ib:.2f} A | Térmico: {s_adm} mm² | CdT: {s_cdt:.2f} mm²</small></div>', unsafe_allow_html=True)
    
    # --- EXPORTACIÓN EXCEL PARA CÁLCULO TÉCNICO (AÑADIDO) ---
    df_calc = pd.DataFrame({
        "Variable": ["Sistema", "Potencia (W)", "Longitud (m)", "Cos φ", "Material", "Aislamiento", "Intensidad Ib (A)", "Sección Térmica (mm²)", "Sección CdT (mm²)", "SECCIÓN FINAL (mm²)"],
        "Valor": [sistema, potencia, longitud, cos_phi, material, aislamiento, f"{ib:.2f}", s_adm, f"{s_cdt:.2f}", s_final]
    })
    excel_data_calc = to_excel(df_calc)
    st.download_button("📥 Descargar Memoria de Cálculo (Excel)", excel_data_calc, "memoria_calculo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- 5. PRESUPUESTO MAESTRO ---
else:
    st.title("💰 Gestor de Presupuestos: Electrificación s/ REBT")
    tab_cfg, tab_pre = st.tabs(["🛠️ Configuración de Precios Unitarios", "📋 Generación de Capítulos"])

    with tab_cfg:
        st.subheader("Base de Datos de Precios (Catálogo)")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            st.markdown("#### ⚡ Cables (€/m)")
            p_c15 = st.number_input("1.5 mm²", 0.10, 2.00, 0.32)
            p_c25 = st.number_input("2.5 mm²", 0.20, 3.00, 0.48)
            p_c40 = st.number_input("4 mm²", 0.40, 5.00, 0.75)
            p_c60 = st.number_input("6 mm²", 0.80, 8.00, 1.45)
            p_c10 = st.number_input("10 mm²", 1.50, 15.0, 2.60)
            p_c16 = st.number_input("16 mm²", 2.50, 25.0, 4.10)

        with col_p2:
            st.markdown("#### 🔘 Mecanismos (€/u)")
            p_interr = st.number_input("Interruptor Simple", 2.0, 50.0, 4.20)
            p_conmut = st.number_input("Conmutador", 2.0, 50.0, 5.80)
            p_cruza = st.number_input("Cruzamiento", 2.0, 50.0, 11.50)
            p_enchufe_16 = st.number_input("Base Enchufe 16A", 2.0, 50.0, 6.10)
            p_enchufe_25 = st.number_input("Base Enchufe 25A", 5.0, 60.0, 14.50)
            p_toma_tvcet = st.number_input("Toma TV/Datos", 5.0, 80.0, 12.00)
            p_estanca = st.number_input("Base Estanca IP54", 8.0, 100.0, 18.50)

        with col_p3:
            st.markdown("#### 🛡️ Protecciones (€/u)")
            p_iga_sobre = st.number_input("IGA + Sobretensiones (Kit)", 50.0, 300.0, 125.0)
            p_pia_10 = st.number_input("PIA 10A", 5.0, 40.0, 8.50)
            p_pia_16 = st.number_input("PIA 16A", 5.0, 40.0, 9.20)
            p_pia_20 = st.number_input("PIA 20A", 5.0, 40.0, 11.50)
            p_pia_25 = st.number_input("PIA 25A", 5.0, 50.0, 14.00)
            p_diff_claseA_25 = st.number_input("Diferencial A 25A", 30.0, 250.0, 55.0)
            p_diff_claseA_40 = st.number_input("Diferencial A 40A", 30.0, 250.0, 65.0)
            p_diff_claseA_63 = st.number_input("Diferencial A 63A", 30.0, 350.0, 95.0)

        with col_p4:
            st.markdown("#### 🚇 Tubos (€/m)")
            p_t16 = st.number_input("Tubo Ø16mm", 0.20, 5.0, 0.45)
            p_t20 = st.number_input("Tubo Ø20mm", 0.30, 6.0, 0.65)
            p_t25 = st.number_input("Tubo Ø25mm", 0.40, 8.0, 0.85)
            p_t32 = st.number_input("Tubo Ø32mm", 0.60, 12.0, 1.25)
            p_t40 = st.number_input("Tubo Ø40mm", 1.00, 20.0, 2.10)
            p_t50 = st.number_input("Tubo Ø50mm", 1.50, 30.0, 3.40)
            p_t63 = st.number_input("Tubo Ø63mm", 2.00, 45.0, 4.80)

        st.divider()
        c_mo1, c_mo2, c_cuad = st.columns(3)
        p_oficial = c_mo1.number_input("Oficial de 1ª (€/h)", 20.0, 60.0, 36.0)
        p_ayudante = c_mo2.number_input("Ayudante (€/h)", 15.0, 50.0, 26.5)
        p_caja_vacia = c_cuad.number_input("Caja Cuadro (Envolvente) (€)", 20.0, 500.0, 75.0)

    catalogo_precios = {
        "Cable 1.5 mm²": p_c15, "Cable 2.5 mm²": p_c25, "Cable 4 mm²": p_c40, 
        "Cable 6 mm²": p_c60, "Cable 10 mm²": p_c10, "Cable 16 mm²": p_c16,
        "Interruptor Simple": p_interr, "Conmutador": p_conmut, "Cruzamiento": p_cruza,
        "Enchufe 16A": p_enchufe_16, "Enchufe 25A": p_enchufe_25, 
        "Toma TV/Datos": p_toma_tvcet, "Base Estanca": p_estanca,
        "IGA + Sobretensiones": p_iga_sobre, "PIA 10A": p_pia_10, "PIA 16A": p_pia_16,
        "PIA 20A": p_pia_20, "PIA 25A": p_pia_25, 
        "Diferencial 25A Clase A": p_diff_claseA_25, "Diferencial 40A Clase A": p_diff_claseA_40, "Diferencial 63A Clase A": p_diff_claseA_63,
        "Tubo Ø16mm": p_t16, "Tubo Ø20mm": p_t20, "Tubo Ø25mm": p_t25, "Tubo Ø32mm": p_t32,
        "Tubo Ø40mm": p_t40, "Tubo Ø50mm": p_t50, "Tubo Ø63mm": p_t63,
        "Caja Cuadro": p_caja_vacia, "Peines Conexión": 12.0, "Pica Tierra + Cable": 115.0
    }

    explicaciones_tecnicas = {
        "DI": "Derivación Individual: Cableado desde contadores hasta el cuadro general.",
        "CGMP": "Cuadro General: IGA, Sobretensiones, Diferenciales y PIAs de protección.",
        "C1": "Iluminación: Máximo 30 puntos de luz (Sección 1.5mm²).",
        "C2": "Tomas uso general: Bases 16A para electrodomésticos básicos (Sección 2.5mm²).",
        "C3": "Cocina y Horno: Circuito de potencia alta (Sección 6mm²).",
        "C4": "Lavadora/Lavavajillas/Termo: Circuito independiente (Sección 4mm²).",
        "C5": "Baños y Cocina: Zonas húmedas, bases de enchufe (Sección 2.5mm²).",
        "C6": "Adicional Iluminación: Cuando C1 excede 30 puntos.",
        "C7": "Adicional Tomas: Cuando C2 excede 20 bases.",
        "C8": "Calefacción: Circuito para emisores térmicos.",
        "C9": "Aire Acondicionado: Climatización independiente.",
        "C10": "Secadora: Circuito independiente según REBT.",
        "C11": "Domótica/Seguridad: Sistemas de control del hogar.",
        "C12": "Circuito Adicional Tomas: Refuerzo de C2/C5.",
        "C13": "IRVE: Punto de recarga para vehículo eléctrico (ITC-BT-52).",
        "PAT": "Puesta a Tierra: Electrodos y red equipotencial de seguridad."
    }

    with tab_pre:
        capitulos_config = {
            "DI": "DERIVACIÓN INDIVIDUAL", "CGMP": "CUADRO GENERAL DE MANDO Y PROTECCIÓN",
            "C1": "ILUMINACIÓN", "C2": "TOMAS DE USO GENERAL Y FRIGORÍFICO",
            "C3": "COCINA Y HORNO", "C4": "LAVADORA, LAVAVAJILLAS Y TERMO ELÉCTRICO",
            "C5": "BAÑOS Y TOMAS DE CORRIENTE DE COCINA", "C6": "CIRCUITO ADICIONAL (C1)",
            "C7": "CIRCUITO ADICIONAL (C2)", "C8": "CALEFACCIÓN",
            "C9": "AIRE ACONDICIONADO", "C10": "SECADORA",
            "C11": "DOMÓTICA Y SEGURIDAD", "C12": "CIRCUITO ADICIONAL TOMAS GENERALES",
            "C13": "RECARGA DE VEHÍCULO ELÉCTRICO (IRVE)", "PAT": "INSTALACIÓN DE PUESTA A TIERRA"
        }
        
        resumen_costes, nombres_export, desc_tecnica = [], [], []

        for code, name in capitulos_config.items():
            with st.expander(f"🛠️ {code}: {name}"):
                st.info(f"**Requisito REBT:** {explicaciones_tecnicas[code]}")
                c_sel, c_cant = st.columns([2, 1])
                seleccion = c_sel.multiselect(f"Añadir materiales a {code}:", list(catalogo_precios.keys()), key=f"sel_{code}")
                coste_materiales = sum(c_cant.number_input(f"Cant. {item}", min_value=0.0, value=0.0, step=1.0, key=f"q_{code}_{item}") * catalogo_precios[item] for item in seleccion)
                st.divider()
                c_h1, c_h2 = st.columns(2)
                h_of = c_h1.number_input(f"Horas Oficial", 0.0, 500.0, 0.0, key=f"h_of_{code}")
                h_ay = c_h2.number_input(f"Horas Ayudante", 0.0, 500.0, 0.0, key=f"h_ay_{code}")
                total_cap = (coste_materiales + (h_of * p_oficial) + (h_ay * p_ayudante)) * f_multiplicador
                st.markdown(f'<div class="resultado-caja">{total_cap:,.2f} €</div>', unsafe_allow_html=True)
                
                if total_cap > 0:
                    resumen_costes.append(total_cap)
                    nombres_export.append(f"{code} - {name}")
                    desc_tecnica.append(explicaciones_tecnicas[code])

        if resumen_costes:
            st.divider()
            total_neto = sum(resumen_costes)
            impuestos = total_neto * (iva_tipo / 100)
            st.markdown(f'<div class="total-final-banner">PRESUPUESTO TOTAL EJECUCIÓN<br><span style="color:#ffd700">{total_neto + impuestos:,.2f} €</span><br><small style="font-size:18px; font-weight:normal;">Base Imponible: {total_neto:,.2f} € | IVA ({iva_tipo}%): {impuestos:,.2f} €</small></div>', unsafe_allow_html=True)
            
            df_final = pd.DataFrame({
                "Capítulo": nombres_export,
                "Justificación Técnica": desc_tecnica,
                "Importe (€)": resumen_costes
            })
            
            # --- BOTONES DE DESCARGA (ACTUALIZADOS A EXCEL) ---
            st.download_button("📥 Descargar Presupuesto Detallado (CSV)", df_final.to_csv(index=False, sep=';', encoding='utf-16'), "presupuesto_ingenieria.csv", "text/csv")
            
            # Línea añadida para descarga en Excel
            excel_presupuesto = to_excel(df_final)
            st.download_button("📊 Descargar Presupuesto Detallado (Excel)", excel_presupuesto, "presupuesto_profesional.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
