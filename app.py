import io
import json
from datetime import date, datetime

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Proyectista Electrico - REBT",
    page_icon="\u26A1",
    layout="wide",
)

# ---------------------------------------------------------------------------
# ESTILOS VISUALES
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.5rem;}
    h1, h2, h3 {color: #0B3D91;}
    .stTabs [data-baseweb="tab-list"] {gap: 6px;}
    .stTabs [data-baseweb="tab"] {
        background-color: #EEF3FB;
        border-radius: 8px 8px 0 0;
        padding: 8px 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0B3D91 !important;
        color: white !important;
    }
    div[data-testid="stMetric"] {
        background-color: #F5F8FF;
        border: 1px solid #DCE6F5;
        border-radius: 10px;
        padding: 10px;
    }
    .aviso-normativa {
        background-color: #FFF6E5;
        border-left: 5px solid #E8A33D;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .caja-log {
        background-color: #F7F7F9;
        border: 1px solid #E0E0E5;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 0.82rem;
        margin-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# TABLAS Y CONSTANTES NORMATIVAS (REBT / ITC-BT) - VALORES DE REFERENCIA
# ---------------------------------------------------------------------------
SECCIONES_MM2 = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Intensidades admisibles (A) - Cu, aislamiento PVC/XLPE 70-90C, 2 conductores
# cargados, temperatura ambiente de referencia 40C aire / 25C terreno segun
# UNE 20460-5-523 y Tabla 1 de la ITC-BT-19. Metodos de instalacion A1,A2,B1,B2,
# C,D,E,F,G. VALORES ORIENTATIVOS: deben verificarse con la edicion vigente del
# REBT antes de emitir un proyecto o memoria oficial.
AMPACIDAD = {
    1.5:  {"A1":14.5, "A2":14,  "B1":17.5, "B2":16.5, "C":19.5, "D":22, "E":22,  "F":23,  "G":26},
    2.5:  {"A1":19.5, "A2":18.5,"B1":24,   "B2":23,   "C":27,   "D":29, "E":30,  "F":31,  "G":36},
    4:    {"A1":26,   "A2":25,  "B1":32,   "B2":30,   "C":36,   "D":38, "E":40,  "F":42,  "G":49},
    6:    {"A1":34,   "A2":32,  "B1":41,   "B2":38,   "C":46,   "D":47, "E":51,  "F":54,  "G":63},
    10:   {"A1":46,   "A2":43,  "B1":57,   "B2":52,   "C":63,   "D":63, "E":70,  "F":75,  "G":86},
    16:   {"A1":61,   "A2":57,  "B1":76,   "B2":69,   "C":85,   "D":81, "E":94,  "F":100, "G":115},
    25:   {"A1":80,   "A2":75,  "B1":96,   "B2":90,   "C":112,  "D":104,"E":119, "F":127, "G":149},
    35:   {"A1":99,   "A2":92,  "B1":119,  "B2":111,  "C":138,  "D":125,"E":147, "F":158, "G":185},
    50:   {"A1":119,  "A2":110, "B1":144,  "B2":133,  "C":168,  "D":148,"E":178, "F":192, "G":225},
    70:   {"A1":151,  "A2":139, "B1":184,  "B2":171,  "C":213,  "D":183,"E":229, "F":246, "G":289},
    95:   {"A1":182,  "A2":167, "B1":223,  "B2":207,  "C":258,  "D":216,"E":278, "F":298, "G":352},
    120:  {"A1":210,  "A2":192, "B1":259,  "B2":239,  "C":299,  "D":246,"E":322, "F":346, "G":410},
    150:  {"A1":240,  "A2":219, "B1":None, "B2":262,  "C":344,  "D":None,"E":371,"F":399, "G":473},
    185:  {"A1":273,  "A2":248, "B1":None, "B2":296,  "C":392,  "D":None,"E":424,"F":456, "G":542},
    240:  {"A1":321,  "A2":291, "B1":None, "B2":344,  "C":461,  "D":None,"E":500,"F":538, "G":641},
    300:  {"A1":367,  "A2":334, "B1":None, "B2":392,  "C":530,  "D":None,"E":576,"F":621, "G":741},
}

METODOS_INSTALACION = {
    "A1": "Conductores aislados en tubo empotrado en pared aislante (interior)",
    "A2": "Cable multiconductor en tubo empotrado en pared aislante",
    "B1": "Conductores aislados en tubo sobre pared o empotrado en obra",
    "B2": "Cable multiconductor en tubo sobre pared o empotrado en obra",
    "C":  "Cable multiconductor directamente sobre la pared o techo",
    "D":  "Cable multiconductor en conducto enterrado o directamente enterrado",
    "E":  "Cable multiconductor al aire libre, bandeja perforada / escalera",
    "F":  "Cables unipolares en contacto mutuo, al aire libre (bandeja)",
    "G":  "Cables unipolares separados, al aire libre (bandeja / soportes)",
}

FACTOR_TEMPERATURA = {
    "PVC": {20:1.22, 25:1.17, 30:1.12, 35:1.06, 40:1.00, 45:0.94, 50:0.87, 55:0.79, 60:0.71},
    "XLPE": {20:1.15, 25:1.12, 30:1.08, 35:1.04, 40:1.00, 45:0.96, 50:0.91, 55:0.87, 60:0.82},
}

FACTOR_AGRUPAMIENTO = {1:1.00, 2:0.80, 3:0.70, 4:0.65, 5:0.60, 6:0.57, 7:0.54, 8:0.52, 9:0.50}

PROTECCIONES_NORMALIZADAS = [6,10,13,16,20,25,32,40,50,63,80,100,125,160,200,250]

CDT_MAXIMA = {
    "Alumbrado": 3.0,
    "Fuerza / Otros usos": 5.0,
    "Derivacion individual": 1.5,
    "Linea general de alimentacion": 0.5,
    "Instalacion fotovoltaica (CC+CA)": 1.5,
}

RESISTIVIDAD_INV_CU = 56.0  # 1/rho (m/ohm*mm2) a 20C, referencia Cu

FACTORES_ARRANQUE_MOTOR = {"directo":1.25, "estrella_triangulo":1.25, "arrancador_suave":1.10, "variador":1.00}

PRECIOS_DEFECTO = {
    "cable_eur_m_mm2": 0.19,
    "tubo_eur_m": 1.35,
    "proteccion_eur_ud": 14.0,
    "mano_obra_eur_h": 24.0,
    "gastos_generales_pct": 13.0,
    "beneficio_industrial_pct": 6.0,
    "iva_pct": 21.0,
}

TIPOS_SUMINISTRO = {
    "CGP individual (usuario unico)": {
        "descripcion": "Suministro para un unico usuario. La CGP incluye los fusibles de seguridad y da paso directamente a la derivacion individual.",
        "elementos": ["Acometida", "CGP", "Equipo de medida (contador)", "Derivacion individual", "ICP + IGA", "Cuadro general de mando y proteccion", "Circuitos interiores"],
    },
    "CGP + Centralizacion de contadores": {
        "descripcion": "Edificio con varios usuarios. La CGP alimenta la Linea General de Alimentacion (LGA) hasta la centralizacion de contadores; de ahi parte una derivacion individual por usuario.",
        "elementos": ["Acometida", "CGP", "Linea General de Alimentacion (LGA)", "Centralizacion de contadores", "Derivacion individual (por usuario)", "ICP + IGA", "Cuadro general de mando y proteccion", "Circuitos interiores"],
    },
    "Suministro en Media Tension con transformador de abonado": {
        "descripcion": "Acometida en Media Tension propiedad del abonado, con centro de transformacion (CT) particular hasta el cuadro general de Baja Tension.",
        "elementos": ["Red de Media Tension", "Celda de proteccion / seccionamiento", "Transformador MT/BT", "Cuadro general de Baja Tension (embarrado)", "Derivacion individual", "Cuadro general de mando y proteccion", "Circuitos interiores"],
    },
    "Generacion propia / Autoconsumo": {
        "descripcion": "Instalacion con generacion fotovoltaica u otra fuente propia, con o sin conexion a la red de distribucion (autoconsumo con o sin excedentes).",
        "elementos": ["Generador (paneles FV / otros)", "Inversor", "Cuadro de protecciones de generacion", "Punto de conexion / Cuadro general de mando y proteccion", "Circuitos interiores"],
    },
}

COLUMNAS_BT = ["Circuito","Descripcion","Tipo","Potencia (W)","Tension (V)","Fases","Longitud (m)",
               "Metodo instalacion","Factor agrupamiento","Temp. ambiente (C)","Aislamiento","Uso"]

COLUMNAS_MOTORES = ["Motor","Descripcion","Potencia (kW)","Tension (V)","Fases","Rendimiento (%)",
                    "cos phi","Longitud (m)","Metodo arranque","Metodo instalacion"]

COLUMNAS_MEDICION_MANUAL = ["Capitulo","Descripcion","Unidad","Cantidad","Precio unitario (EUR)"]


def df_vacio(columnas):
    return pd.DataFrame({c: [] for c in columnas})


# ---------------------------------------------------------------------------
# FUNCIONES DE CALCULO ELECTRICO
# ---------------------------------------------------------------------------

def intensidad_mono(potencia_w, tension_v, cos_phi=0.95):
    if tension_v <= 0:
        return 0.0
    return potencia_w / (tension_v * cos_phi)


def intensidad_tri(potencia_w, tension_v, cos_phi=0.95):
    if tension_v <= 0:
        return 0.0
    return potencia_w / (1.732 * tension_v * cos_phi)


def cdt_mono_pct(intensidad_a, longitud_m, seccion_mm2, tension_v, cos_phi=0.95):
    if seccion_mm2 <= 0 or tension_v <= 0:
        return 0.0
    caida_v = (2 * longitud_m * intensidad_a) / (RESISTIVIDAD_INV_CU * seccion_mm2)
    return (caida_v / tension_v) * 100


def cdt_tri_pct(intensidad_a, longitud_m, seccion_mm2, tension_v, cos_phi=0.95):
    if seccion_mm2 <= 0 or tension_v <= 0:
        return 0.0
    caida_v = (1.732 * longitud_m * intensidad_a) / (RESISTIVIDAD_INV_CU * seccion_mm2)
    return (caida_v / tension_v) * 100


def elegir_seccion_por_intensidad(intensidad_a, metodo, factor_temp=1.0, factor_agrup=1.0):
    for s in SECCIONES_MM2:
        fila = AMPACIDAD.get(s, {})
        iz = fila.get(metodo)
        if iz is None:
            continue
        iz_corregida = iz * factor_temp * factor_agrup
        if iz_corregida >= intensidad_a:
            return s, iz_corregida
    return SECCIONES_MM2[-1], None


def elegir_seccion_por_cdt(intensidad_a, longitud_m, tension_v, cdt_max_pct, trifasico=False, cos_phi=0.95):
    for s in SECCIONES_MM2:
        if trifasico:
            cdt = cdt_tri_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
        else:
            cdt = cdt_mono_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
        if cdt <= cdt_max_pct:
            return s, cdt
    s = SECCIONES_MM2[-1]
    if trifasico:
        cdt = cdt_tri_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
    else:
        cdt = cdt_mono_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
    return s, cdt


def elegir_proteccion(intensidad_a, iz_a=None):
    for p in PROTECCIONES_NORMALIZADAS:
        if p >= intensidad_a:
            if iz_a is not None and p > iz_a:
                continue
            return p
    return PROTECCIONES_NORMALIZADAS[-1]


def calcular_circuito_bt(fila):
    potencia = float(fila.get("Potencia (W)", 0) or 0)
    tension = float(fila.get("Tension (V)", 230) or 230)
    fases = fila.get("Fases", "Monofasico")
    longitud = float(fila.get("Longitud (m)", 0) or 0)
    metodo = fila.get("Metodo instalacion", "B1")
    agrup_n = int(fila.get("Factor agrupamiento", 1) or 1)
    temp_amb = float(fila.get("Temp. ambiente (C)", 40) or 40)
    aislamiento = fila.get("Aislamiento", "PVC")
    uso = fila.get("Uso", "Fuerza / Otros usos")

    trifasico = str(fases).lower().startswith("tri")
    if trifasico:
        intensidad = intensidad_tri(potencia, tension)
    else:
        intensidad = intensidad_mono(potencia, tension)

    tabla_temp = FACTOR_TEMPERATURA.get(aislamiento, FACTOR_TEMPERATURA["PVC"])
    temps = sorted(tabla_temp.keys())
    temp_cercana = min(temps, key=lambda t: abs(t - temp_amb))
    f_temp = tabla_temp[temp_cercana]
    f_agrup = FACTOR_AGRUPAMIENTO.get(agrup_n, 0.5)

    seccion_intensidad, iz = elegir_seccion_por_intensidad(intensidad, metodo, f_temp, f_agrup)
    cdt_max = CDT_MAXIMA.get(uso, 3.0)
    seccion_cdt, cdt = elegir_seccion_por_cdt(intensidad, longitud, tension, cdt_max, trifasico)

    seccion_final = max(seccion_intensidad, seccion_cdt)
    proteccion = elegir_proteccion(intensidad, iz)

    cdt_final = cdt_tri_pct(intensidad, longitud, seccion_final, tension) if trifasico else cdt_mono_pct(intensidad, longitud, seccion_final, tension)
    cumple = (cdt_final <= cdt_max) and (iz is not None)

    return {
        "Intensidad (A)": round(intensidad, 2),
        "Seccion (mm2)": seccion_final,
        "Proteccion (A)": proteccion,
        "CDT (%)": round(cdt_final, 2),
        "CDT max (%)": cdt_max,
        "Cumple": "Si" if cumple else "Revisar",
    }


def calcular_fv(potencia_pico_kwp, tension_mppt_v, num_paneles, longitud_dc_m, longitud_ac_m, potencia_inversor_kw, tension_ac_v=400):
    intensidad_dc = (potencia_pico_kwp * 1000) / tension_mppt_v if tension_mppt_v else 0
    seccion_dc, _ = elegir_seccion_por_intensidad(intensidad_dc, "E", 1.0, 1.0)
    cdt_dc = cdt_mono_pct(intensidad_dc, longitud_dc_m, seccion_dc, tension_mppt_v) if tension_mppt_v else 0

    intensidad_ac = intensidad_tri(potencia_inversor_kw * 1000, tension_ac_v)
    seccion_ac, _ = elegir_seccion_por_intensidad(intensidad_ac, "E", 1.0, 1.0)
    cdt_ac = cdt_tri_pct(intensidad_ac, longitud_ac_m, seccion_ac, tension_ac_v)

    proteccion_dc = elegir_proteccion(intensidad_dc)
    proteccion_ac = elegir_proteccion(intensidad_ac)

    return {
        "Intensidad DC (A)": round(intensidad_dc, 2),
        "Seccion DC (mm2)": seccion_dc,
        "Proteccion DC (A)": proteccion_dc,
        "CDT DC (%)": round(cdt_dc, 2),
        "Intensidad AC (A)": round(intensidad_ac, 2),
        "Seccion AC (mm2)": seccion_ac,
        "Proteccion AC (A)": proteccion_ac,
        "CDT AC (%)": round(cdt_ac, 2),
    }


def calcular_motor(fila):
    potencia_kw = float(fila.get("Potencia (kW)", 0) or 0)
    tension = float(fila.get("Tension (V)", 400) or 400)
    fases = fila.get("Fases", "Trifasico")
    rendimiento = float(fila.get("Rendimiento (%)", 90) or 90) / 100
    cos_phi = float(fila.get("cos phi", 0.85) or 0.85)
    longitud = float(fila.get("Longitud (m)", 0) or 0)
    metodo_arranque = fila.get("Metodo arranque", "directo")
    metodo_inst = fila.get("Metodo instalacion", "B1")

    potencia_absorbida_w = (potencia_kw * 1000) / rendimiento if rendimiento else 0
    trifasico = str(fases).lower().startswith("tri")
    if trifasico:
        intensidad_nominal = intensidad_tri(potencia_absorbida_w, tension, cos_phi)
    else:
        intensidad_nominal = intensidad_mono(potencia_absorbida_w, tension, cos_phi)

    factor_arranque = FACTORES_ARRANQUE_MOTOR.get(metodo_arranque, 1.25)
    intensidad_calculo = intensidad_nominal * factor_arranque

    seccion, iz = elegir_seccion_por_intensidad(intensidad_calculo, metodo_inst, 1.0, 1.0)
    cdt_max = CDT_MAXIMA["Fuerza / Otros usos"]
    seccion_cdt, cdt = elegir_seccion_por_cdt(intensidad_calculo, longitud, tension, cdt_max, trifasico, cos_phi)
    seccion_final = max(seccion, seccion_cdt)
    proteccion = elegir_proteccion(intensidad_calculo, iz)

    return {
        "Intensidad nominal (A)": round(intensidad_nominal, 2),
        "Intensidad de calculo (A)": round(intensidad_calculo, 2),
        "Seccion (mm2)": seccion_final,
        "Proteccion (A)": proteccion,
        "CDT (%)": round(cdt, 2),
        "CDT max (%)": cdt_max,
    }


# ---------------------------------------------------------------------------
# REGISTRO DE CAMBIOS EN TIEMPO REAL
# ---------------------------------------------------------------------------

def registrar_cambio(accion, detalle=""):
    if "historial" not in st.session_state:
        st.session_state["historial"] = []
    st.session_state["historial"].append({
        "hora": datetime.now().strftime("%H:%M:%S"),
        "accion": accion,
        "detalle": detalle,
    })
    # Mantener un historial acotado para no consumir memoria en exceso
    if len(st.session_state["historial"]) > 200:
        st.session_state["historial"] = st.session_state["historial"][-200:]


def detectar_cambios_df(clave_estado, df_nuevo, etiqueta):
    anterior = st.session_state.get(clave_estado)
    if anterior is None or not anterior.equals(df_nuevo):
        filas_antes = 0 if anterior is None else len(anterior)
        filas_ahora = len(df_nuevo)
        if filas_ahora > filas_antes:
            registrar_cambio(f"Añadida fila en {etiqueta}", f"Total filas: {filas_ahora}")
        elif filas_ahora < filas_antes:
            registrar_cambio(f"Eliminada fila en {etiqueta}", f"Total filas: {filas_ahora}")
        else:
            registrar_cambio(f"Editado {etiqueta}", f"Total filas: {filas_ahora}")
        st.session_state[clave_estado] = df_nuevo.copy()


# ---------------------------------------------------------------------------
# MEDICIONES Y PRESUPUESTO
# ---------------------------------------------------------------------------

def clave_cable(seccion_mm2, num_conductores=2):
    return f"Cable Cu {num_conductores}x{seccion_mm2} mm2"


def generar_mediciones_auto(df_bt_calc, df_motores_calc):
    filas = []
    if df_bt_calc is not None and not df_bt_calc.empty:
        for _, r in df_bt_calc.iterrows():
            longitud = float(r.get("Longitud (m)", 0) or 0)
            seccion = r.get("Seccion (mm2)", 1.5)
            proteccion = r.get("Proteccion (A)", 10)
            filas.append({"Capitulo":"Baja Tension","Descripcion":clave_cable(seccion),"Unidad":"m","Cantidad":longitud,"Precio unitario (EUR)":round(seccion*PRECIOS_DEFECTO["cable_eur_m_mm2"],2)})
            filas.append({"Capitulo":"Baja Tension","Descripcion":f"Tubo protector para {clave_cable(seccion)}","Unidad":"m","Cantidad":longitud,"Precio unitario (EUR)":PRECIOS_DEFECTO["tubo_eur_m"]})
            filas.append({"Capitulo":"Baja Tension","Descripcion":f"Proteccion magnetotermica {proteccion} A","Unidad":"ud","Cantidad":1,"Precio unitario (EUR)":PRECIOS_DEFECTO["proteccion_eur_ud"]})
    if df_motores_calc is not None and not df_motores_calc.empty:
        for _, r in df_motores_calc.iterrows():
            longitud = float(r.get("Longitud (m)", 0) or 0)
            seccion = r.get("Seccion (mm2)", 2.5)
            proteccion = r.get("Proteccion (A)", 16)
            filas.append({"Capitulo":"Industrial / Motores","Descripcion":clave_cable(seccion,4),"Unidad":"m","Cantidad":longitud,"Precio unitario (EUR)":round(seccion*PRECIOS_DEFECTO["cable_eur_m_mm2"]*1.6,2)})
            filas.append({"Capitulo":"Industrial / Motores","Descripcion":f"Guardamotor / proteccion {proteccion} A","Unidad":"ud","Cantidad":1,"Precio unitario (EUR)":PRECIOS_DEFECTO["proteccion_eur_ud"]*1.8})
    return pd.DataFrame(filas) if filas else df_vacio(["Capitulo","Descripcion","Unidad","Cantidad","Precio unitario (EUR)"])


def calcular_presupuesto(df_mediciones):
    if df_mediciones is None or df_mediciones.empty:
        return df_vacio(["Capitulo","Descripcion","Unidad","Cantidad","Precio unitario (EUR)","Importe (EUR)"]), {}
    df = df_mediciones.copy()
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
    df["Precio unitario (EUR)"] = pd.to_numeric(df["Precio unitario (EUR)"], errors="coerce").fillna(0)
    df["Importe (EUR)"] = (df["Cantidad"] * df["Precio unitario (EUR)"]).round(2)

    pem = df["Importe (EUR)"].sum()
    gg = pem * PRECIOS_DEFECTO["gastos_generales_pct"] / 100
    bi = pem * PRECIOS_DEFECTO["beneficio_industrial_pct"] / 100
    base_licitacion = pem + gg + bi
    iva = base_licitacion * PRECIOS_DEFECTO["iva_pct"] / 100
    total = base_licitacion + iva

    resumen = {
        "PEM": round(pem, 2),
        "Gastos generales": round(gg, 2),
        "Beneficio industrial": round(bi, 2),
        "Base de licitacion": round(base_licitacion, 2),
        "IVA": round(iva, 2),
        "TOTAL": round(total, 2),
    }
    return df, resumen


def generar_memoria_texto(estado):
    datos = estado.get("datos_proyecto", {})
    tipo_sum = estado.get("tipo_suministro", list(TIPOS_SUMINISTRO.keys())[0])
    info_sum = TIPOS_SUMINISTRO.get(tipo_sum, {})
    partes = []
    partes.append("MEMORIA TECNICA DE DISEÑO (MTD)")
    partes.append("")
    partes.append("1. OBJETO DE LA MEMORIA")
    partes.append(datos.get("objeto") or "Definir el objeto de la instalacion proyectada.")
    partes.append("")
    partes.append("2. TITULAR Y EMPLAZAMIENTO")
    partes.append(f"Titular: {datos.get('titular','-')}")
    partes.append(f"Emplazamiento: {datos.get('emplazamiento','-')}")
    partes.append(f"Referencia catastral / CUPS: {datos.get('referencia','-')}")
    partes.append("")
    partes.append("3. REGLAMENTACION Y DISPOSICIONES APLICADAS")
    partes.append(datos.get("normativa") or ("Reglamento Electrotecnico para Baja Tension (REBT) e Instrucciones Tecnicas Complementarias ITC-BT, "
                  "Normas UNE de aplicacion, Normas particulares de la empresa distribuidora y Ordenanzas municipales que resulten de aplicacion."))
    partes.append("")
    partes.append("4. DESCRIPCION GENERAL DE LA INSTALACION")
    partes.append(f"Tipo de suministro: {tipo_sum}")
    partes.append(info_sum.get("descripcion", ""))
    partes.append("Elementos principales de la instalacion:")
    for el in info_sum.get("elementos", []):
        partes.append(f" - {el}")
    partes.append("")
    partes.append(datos.get("descripcion") or "Describir potencia total prevista, uso del inmueble y caracteristicas generales.")
    partes.append("")
    partes.append("5. CALCULOS JUSTIFICATIVOS")
    partes.append("Los calculos justificativos de secciones, caidas de tension y protecciones de cada circuito, "
                  "instalacion fotovoltaica y motores se detallan en los Anexos de calculo adjuntos a la presente memoria.")
    partes.append("")
    partes.append("6. ANEXOS")
    partes.append(" - Anexo I: Calculos de circuitos de Baja Tension")
    partes.append(" - Anexo II: Calculos de instalacion Fotovoltaica")
    partes.append(" - Anexo III: Calculos de motores / instalacion industrial")
    partes.append(" - Anexo IV: Mediciones y Presupuesto")
    partes.append("")
    partes.append("7. CONCLUSION")
    partes.append("La instalacion descrita cumple con las prescripciones del Reglamento Electrotecnico para Baja Tension "
                  "y sus Instrucciones Tecnicas Complementarias, quedando sujeta a verificacion final por tecnico competente.")
    return "\\n".join(partes)


# ---------------------------------------------------------------------------
# ESTADO DE SESION
# ---------------------------------------------------------------------------

def inicializar_estado():
    if "inicializado" in st.session_state:
        return
    st.session_state["inicializado"] = True
    st.session_state["datos_proyecto"] = {
        "titular": "", "emplazamiento": "", "referencia": "",
        "objeto": "", "normativa": "", "descripcion": "",
        "fecha": str(date.today()),
    }
    st.session_state["tipo_suministro"] = list(TIPOS_SUMINISTRO.keys())[0]
    st.session_state["modulos"] = {"bt": True, "fv": False, "industrial": False}
    st.session_state["df_bt"] = df_vacio(COLUMNAS_BT)
    st.session_state["df_motores"] = df_vacio(COLUMNAS_MOTORES)
    st.session_state["df_mediciones_manual"] = df_vacio(COLUMNAS_MEDICION_MANUAL)
    st.session_state["fv_datos"] = {
        "potencia_pico_kwp": 5.0, "tension_mppt_v": 600.0, "num_paneles": 12,
        "longitud_dc_m": 20.0, "longitud_ac_m": 15.0, "potencia_inversor_kw": 5.0,
        "tension_ac_v": 400.0,
    }
    st.session_state["historial"] = []
    registrar_cambio("Proyecto iniciado", "Se ha creado una nueva sesion de trabajo")


def estado_a_dict():
    return {
        "datos_proyecto": st.session_state.get("datos_proyecto", {}),
        "tipo_suministro": st.session_state.get("tipo_suministro"),
        "modulos": st.session_state.get("modulos", {}),
        "df_bt": st.session_state["df_bt"].to_dict("records"),
        "df_motores": st.session_state["df_motores"].to_dict("records"),
        "df_mediciones_manual": st.session_state["df_mediciones_manual"].to_dict("records"),
        "fv_datos": st.session_state.get("fv_datos", {}),
    }


def cargar_estado_desde_dict(data):
    st.session_state["datos_proyecto"] = data.get("datos_proyecto", {})
    st.session_state["tipo_suministro"] = data.get("tipo_suministro", list(TIPOS_SUMINISTRO.keys())[0])
    st.session_state["modulos"] = data.get("modulos", {"bt": True, "fv": False, "industrial": False})
    st.session_state["df_bt"] = pd.DataFrame(data.get("df_bt", [])) if data.get("df_bt") else df_vacio(COLUMNAS_BT)
    st.session_state["df_motores"] = pd.DataFrame(data.get("df_motores", [])) if data.get("df_motores") else df_vacio(COLUMNAS_MOTORES)
    st.session_state["df_mediciones_manual"] = pd.DataFrame(data.get("df_mediciones_manual", [])) if data.get("df_mediciones_manual") else df_vacio(COLUMNAS_MEDICION_MANUAL)
    st.session_state["fv_datos"] = data.get("fv_datos", {})
    registrar_cambio("Proyecto importado", "Se ha cargado un archivo de proyecto JSON")


def exportar_excel(df_bt_calc, df_motores_calc, df_mediciones, resumen_presupuesto):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if df_bt_calc is not None and not df_bt_calc.empty:
            df_bt_calc.to_excel(writer, sheet_name="Baja Tension", index=False)
        if df_motores_calc is not None and not df_motores_calc.empty:
            df_motores_calc.to_excel(writer, sheet_name="Industrial-Motores", index=False)
        if df_mediciones is not None and not df_mediciones.empty:
            df_mediciones.to_excel(writer, sheet_name="Mediciones", index=False)
        if resumen_presupuesto:
            pd.DataFrame([resumen_presupuesto]).T.rename(columns={0: "Importe (EUR)"}).to_excel(writer, sheet_name="Presupuesto")
    buffer.seek(0)
    return buffer


def exportar_memoria_word(texto_memoria):
    from docx import Document
    doc = Document()
    for linea in texto_memoria.split("\\n"):
        if linea.isupper() and linea.strip() and len(linea.strip()) > 3 and linea[0].isdigit() is False and linea.strip()[0].isalpha():
            doc.add_heading(linea, level=1)
        elif linea.strip().startswith(tuple(f"{n}." for n in range(1, 10))):
            doc.add_heading(linea, level=1)
        else:
            doc.add_paragraph(linea)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def exportar_memoria_pdf(estado, texto_memoria, df_bt_calc, df_fv_calc, df_motores_calc, df_mediciones, resumen_presupuesto):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("TituloPortada", parent=styles["Title"], fontSize=22, spaceAfter=20)
    subt = ParagraphStyle("Subt", parent=styles["Normal"], fontSize=12, spaceAfter=8)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#0B3D91"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#0B3D91"))
    normal = styles["Normal"]

    datos = estado.get("datos_proyecto", {})
    story = []

    # ---- Portada ----
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("MEMORIA TECNICA DE DISEÑO (MTD)", titulo))
    story.append(Paragraph("Instalacion electrica en Baja Tension conforme al REBT", subt))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"<b>Titular:</b> {datos.get('titular','-')}", subt))
    story.append(Paragraph(f"<b>Emplazamiento:</b> {datos.get('emplazamiento','-')}", subt))
    story.append(Paragraph(f"<b>Referencia:</b> {datos.get('referencia','-')}", subt))
    story.append(Paragraph(f"<b>Tipo de suministro:</b> {estado.get('tipo_suministro','-')}", subt))
    story.append(Paragraph(f"<b>Fecha:</b> {datos.get('fecha', str(date.today()))}", subt))
    story.append(PageBreak())

    # ---- Cuerpo de la memoria ----
    for bloque in texto_memoria.split("\\n\\n"):
        lineas = bloque.split("\\n")
        for i, linea in enumerate(lineas):
            if linea.strip()[:2].rstrip(".").isdigit() or (linea.strip() and linea.strip()[0].isdigit() and "." in linea[:3]):
                story.append(Paragraph(linea, h1))
            elif linea.strip().startswith(" - "):
                story.append(Paragraph(linea.strip(), normal))
            else:
                story.append(Paragraph(linea if linea.strip() else "&nbsp;", normal))
        story.append(Spacer(1, 6))
    story.append(PageBreak())

    def tabla_desde_df(df, titulo_tabla):
        story.append(Paragraph(titulo_tabla, h2))
        if df is None or df.empty:
            story.append(Paragraph("Sin datos introducidos para este capitulo.", normal))
            story.append(Spacer(1, 12))
            return
        cols = list(df.columns)
        data = [cols] + df.astype(str).values.tolist()
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B3D91")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 7),
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F8FF")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

    # ---- Anexo I: BT ----
    story.append(Paragraph("ANEXO I - CALCULOS DE CIRCUITOS DE BAJA TENSION", h1))
    tabla_desde_df(df_bt_calc, "Resultados de calculo de circuitos")
    story.append(PageBreak())

    # ---- Anexo II: FV ----
    story.append(Paragraph("ANEXO II - CALCULOS DE INSTALACION FOTOVOLTAICA", h1))
    tabla_desde_df(df_fv_calc, "Resultados de calculo fotovoltaico")
    story.append(PageBreak())

    # ---- Anexo III: Motores ----
    story.append(Paragraph("ANEXO III - CALCULOS DE MOTORES / INDUSTRIAL", h1))
    tabla_desde_df(df_motores_calc, "Resultados de calculo de motores")
    story.append(PageBreak())

    # ---- Anexo IV: Mediciones y presupuesto ----
    story.append(Paragraph("ANEXO IV - MEDICIONES Y PRESUPUESTO", h1))
    tabla_desde_df(df_mediciones, "Mediciones")
    if resumen_presupuesto:
        story.append(Paragraph("Resumen del presupuesto", h2))
        data = [["Concepto", "Importe (EUR)"]] + [[k, f"{v:,.2f}"] for k, v in resumen_presupuesto.items()]
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B3D91")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ]))
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generar_esquema_unifilar_dxf(estado, df_bt_calc):
    """Genera un esquema unifilar en formato DXF (abierto, compatible con
    AutoCAD mediante 'Guardar como .dwg'), con una distribucion inspirada en
    los configuradores profesionales tipo CIEBT: bloques en cascada para la
    acometida / proteccion / medida segun el tipo de suministro elegido, y
    derivaciones horizontales para cada circuito interior.

    NOTA IMPORTANTE: no es posible generar un binario .dwg nativo (formato
    propietario de Autodesk) sin las librerias oficiales de Autodesk/ODA. Se
    genera un .dxf, formato abierto totalmente compatible, que se puede abrir
    y volver a guardar como .dwg desde AutoCAD u otro programa CAD.
    """
    import ezdxf

    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()

    capas = {
        "MARCO": 7, "ACOMETIDA": 5, "PROTECCION": 1, "MEDIDA": 3,
        "CUADRO": 6, "CIRCUITOS": 4, "TEXTOS": 7,
    }
    for nombre, color in capas.items():
        doc.layers.add(name=nombre, color=color)

    tipo_sum = estado.get("tipo_suministro", list(TIPOS_SUMINISTRO.keys())[0])
    elementos = TIPOS_SUMINISTRO.get(tipo_sum, {}).get("elementos", [])

    x0 = 0
    y = 0
    paso_y = 25
    ancho_caja = 90
    alto_caja = 14

    # ---- Marco / cajetin tipo plano profesional ----
    alto_total = paso_y * (len(elementos) + 2) + 40
    ancho_total = 260
    msp.add_lwpolyline(
        [(-20, -alto_total), (-20, 30), (ancho_total, 30), (ancho_total, -alto_total), (-20, -alto_total)],
        dxfattribs={"layer": "MARCO"},
    )
    msp.add_text("ESQUEMA UNIFILAR - INSTALACION ELECTRICA EN BAJA TENSION",
                 dxfattribs={"layer": "TEXTOS", "height": 4}).set_placement((-15, 15))
    msp.add_text(f"Tipo de suministro: {tipo_sum}",
                 dxfattribs={"layer": "TEXTOS", "height": 2.5}).set_placement((-15, 8))

    # ---- Cadena vertical de elementos del suministro (estilo CIEBT) ----
    puntos_conexion = []
    for elemento in elementos:
        cx, cy = x0, y
        msp.add_lwpolyline(
            [(cx, cy), (cx + ancho_caja, cy), (cx + ancho_caja, cy - alto_caja), (cx, cy - alto_caja), (cx, cy)],
            dxfattribs={"layer": "CUADRO"},
        )
        msp.add_text(elemento, dxfattribs={"layer": "TEXTOS", "height": 3}).set_placement(
            (cx + 4, cy - alto_caja / 2 - 1)
        )
        centro = (cx + ancho_caja / 2, cy - alto_caja)
        puntos_conexion.append(centro)
        if len(puntos_conexion) > 1:
            ant = puntos_conexion[-2]
            msp.add_line((ant[0], ant[1]), (centro[0], centro[1] - (paso_y - alto_caja) + alto_caja),
                         dxfattribs={"layer": "ACOMETIDA"})
        y -= paso_y

    ultimo_punto = puntos_conexion[-1] if puntos_conexion else (x0 + ancho_caja / 2, 0)

    # ---- Embarrado del cuadro general ----
    barra_y = ultimo_punto[1] - 10
    msp.add_line((ultimo_punto[0], ultimo_punto[1]), (ultimo_punto[0], barra_y), dxfattribs={"layer": "CUADRO"})
    msp.add_line((-10, barra_y), (ancho_total - 10, barra_y), dxfattribs={"layer": "CUADRO"})
    msp.add_text("EMBARRADO - CUADRO GENERAL DE MANDO Y PROTECCION",
                 dxfattribs={"layer": "TEXTOS", "height": 2.5}).set_placement((-10, barra_y + 2))

    # ---- Derivaciones a cada circuito interior (segun datos introducidos) ----
    if df_bt_calc is not None and not df_bt_calc.empty:
        n = len(df_bt_calc)
        espacio_x = (ancho_total - 10) / max(n, 1)
        for i, (_, fila) in enumerate(df_bt_calc.iterrows()):
            cx = -10 + espacio_x * i + espacio_x / 2
            msp.add_line((cx, barra_y), (cx, barra_y - 10), dxfattribs={"layer": "CIRCUITOS"})
            # simbolo de proteccion magnetotermica (rectangulo pequeño)
            msp.add_lwpolyline(
                [(cx - 3, barra_y - 10), (cx + 3, barra_y - 10), (cx + 3, barra_y - 16), (cx - 3, barra_y - 16), (cx - 3, barra_y - 10)],
                dxfattribs={"layer": "PROTECCION"},
            )
            msp.add_line((cx, barra_y - 16), (cx, barra_y - 26), dxfattribs={"layer": "CIRCUITOS"})
            nombre_circ = str(fila.get("Circuito", f"C{i+1}"))
            seccion = fila.get("Seccion (mm2)", "-")
            proteccion = fila.get("Proteccion (A)", "-")
            etiqueta = f"{nombre_circ}\\nCu {seccion} mm2 / {proteccion} A"
            for j, linea_txt in enumerate(etiqueta.split("\\n")):
                msp.add_text(linea_txt, dxfattribs={"layer": "TEXTOS", "height": 1.8}).set_placement(
                    (cx - 8, barra_y - 30 - j * 3), align="LEFT"
                )
    else:
        msp.add_text("Sin circuitos interiores definidos todavia (ver pestaña Baja Tension)",
                     dxfattribs={"layer": "TEXTOS", "height": 2.5}).set_placement((-10, barra_y - 12))

    # ---- Cajetin inferior (estilo profesional) ----
    cy_cajetin = -alto_total + 5
    msp.add_lwpolyline(
        [(-20, cy_cajetin), (ancho_total, cy_cajetin), (ancho_total, cy_cajetin - 20), (-20, cy_cajetin - 20), (-20, cy_cajetin)],
        dxfattribs={"layer": "MARCO"},
    )
    datos = estado.get("datos_proyecto", {})
    msp.add_text(f"Titular: {datos.get('titular','-')}", dxfattribs={"layer": "TEXTOS", "height": 2.2}).set_placement((-15, cy_cajetin - 6))
    msp.add_text(f"Emplazamiento: {datos.get('emplazamiento','-')}", dxfattribs={"layer": "TEXTOS", "height": 2.2}).set_placement((-15, cy_cajetin - 10))
    msp.add_text(f"Fecha: {datos.get('fecha', str(date.today()))}   Escala: S/E", dxfattribs={"layer": "TEXTOS", "height": 2.2}).set_placement((-15, cy_cajetin - 14))

    buffer = io.StringIO()
    doc.write(buffer)
    contenido = buffer.getvalue()
    return contenido.encode("utf-8")


# ---------------------------------------------------------------------------
# INTERFAZ DE USUARIO
# ---------------------------------------------------------------------------
inicializar_estado()

st.title("\u26A1 Proyectista Electrico - REBT")
st.markdown(
    '<div class="aviso-normativa">Esta herramienta calcula valores orientativos de secciones, '
    'protecciones y caidas de tension conforme a criterios generales del REBT / ITC-BT. '
    'Las tablas de intensidades admisibles y demas valores normativos deben verificarse siempre '
    'frente a la edicion vigente del Reglamento Electrotecnico para Baja Tension antes de su uso '
    'en una memoria o proyecto oficial, y el resultado final debe ser revisado y firmado por un '
    'tecnico competente.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Datos del proyecto")
    dp = st.session_state["datos_proyecto"]
    dp["titular"] = st.text_input("Titular", value=dp.get("titular", ""))
    dp["emplazamiento"] = st.text_input("Emplazamiento", value=dp.get("emplazamiento", ""))
    dp["referencia"] = st.text_input("Referencia catastral / CUPS", value=dp.get("referencia", ""))
    dp["fecha"] = st.text_input("Fecha", value=dp.get("fecha", str(date.today())))

    st.subheader("Tipo de suministro")
    opciones_suministro = list(TIPOS_SUMINISTRO.keys())
    tipo_actual = st.session_state.get("tipo_suministro", opciones_suministro[0])
    nuevo_tipo = st.selectbox(
        "¿Como se alimenta la instalacion?",
        opciones_suministro,
        index=opciones_suministro.index(tipo_actual) if tipo_actual in opciones_suministro else 0,
        help="Determina los elementos que se dibujan en el esquema unifilar (CGP, centralizacion de contadores, transformador de abonado, generacion propia, etc.)",
    )
    if nuevo_tipo != tipo_actual:
        registrar_cambio("Cambio de tipo de suministro", f"{tipo_actual} -> {nuevo_tipo}")
    st.session_state["tipo_suministro"] = nuevo_tipo
    st.caption(TIPOS_SUMINISTRO[nuevo_tipo]["descripcion"])

    st.subheader("Modulos activos")
    modulos = st.session_state["modulos"]
    modulos["bt"] = st.checkbox("Baja Tension", value=modulos.get("bt", True))
    modulos["fv"] = st.checkbox("Fotovoltaica", value=modulos.get("fv", False))
    modulos["industrial"] = st.checkbox("Industrial / Motores", value=modulos.get("industrial", False))

    st.subheader("Proyecto (guardar / cargar)")
    proyecto_json = json.dumps(estado_a_dict(), indent=2, ensure_ascii=False)
    st.download_button("Descargar proyecto (.json)", data=proyecto_json, file_name="proyecto_electrico.json", mime="application/json")
    archivo_proyecto = st.file_uploader("Cargar proyecto (.json)", type=["json"], key="cargador_proyecto")
    if archivo_proyecto is not None:
        try:
            data = json.load(archivo_proyecto)
            cargar_estado_desde_dict(data)
            st.success("Proyecto cargado correctamente.")
        except Exception as e:
            st.error(f"No se ha podido leer el archivo: {e}")

    st.subheader("\U0001F4CB Registro de cambios en tiempo real")
    historial = list(reversed(st.session_state.get("historial", [])))[:15]
    if historial:
        for h in historial:
            st.markdown(
                f'<div class="caja-log"><b>{h["hora"]}</b> - {h["accion"]}<br><span style="color:#666">{h["detalle"]}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Todavia no se han registrado cambios en esta sesion.")


tab_bt, tab_fv, tab_ind, tab_med, tab_pres, tab_esq, tab_mem, tab_io = st.tabs([
    "\u26A1 Baja Tension", "\u2600\uFE0F Fotovoltaica", "\U0001F3ED Industrial",
    "\U0001F9FE Mediciones", "\U0001F4B0 Presupuesto", "\U0001F4D0 Esquema unifilar",
    "\U0001F4C4 Memoria", "\U0001F4C2 Importar/Exportar",
])

df_bt_calc = df_vacio(COLUMNAS_BT)
df_fv_calc = None
df_motores_calc = df_vacio(COLUMNAS_MOTORES)

# ---------------- BAJA TENSION ----------------
with tab_bt:
    st.subheader("Circuitos de Baja Tension")
    if modulos.get("bt"):
        df_editado = st.data_editor(
            st.session_state["df_bt"],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_bt",
            column_config={
                "Fases": st.column_config.SelectboxColumn(options=["Monofasico", "Trifasico"]),
                "Metodo instalacion": st.column_config.SelectboxColumn(options=list(METODOS_INSTALACION.keys())),
                "Aislamiento": st.column_config.SelectboxColumn(options=["PVC", "XLPE"]),
                "Uso": st.column_config.SelectboxColumn(options=list(CDT_MAXIMA.keys())),
            },
        )
        detectar_cambios_df("df_bt", df_editado, "circuitos de Baja Tension")
        st.session_state["df_bt"] = df_editado

        with st.expander("Ver metodos de instalacion disponibles"):
            for k, v in METODOS_INSTALACION.items():
                st.markdown(f"**{k}**: {v}")

        if not df_editado.empty:
            resultados = df_editado.apply(lambda f: pd.Series(calcular_circuito_bt(f)), axis=1)
            df_bt_calc = pd.concat([df_editado.reset_index(drop=True), resultados.reset_index(drop=True)], axis=1)
            st.markdown("#### Resultados de calculo")
            st.dataframe(df_bt_calc, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Circuitos totales", len(df_bt_calc))
            c2.metric("Cumplen", int((df_bt_calc["Cumple"] == "Si").sum()))
            c3.metric("A revisar", int((df_bt_calc["Cumple"] == "Revisar").sum()))

            try:
                import plotly.express as px
                conteo = df_bt_calc["Cumple"].value_counts().reset_index()
                conteo.columns = ["Estado", "Cantidad"]
                fig = px.pie(conteo, names="Estado", values="Cantidad", title="Estado de cumplimiento de circuitos",
                             color="Estado", color_discrete_map={"Si": "#2E7D32", "Revisar": "#C62828"})
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
    else:
        st.info("Activa el modulo 'Baja Tension' en la barra lateral para introducir circuitos.")

# ---------------- FOTOVOLTAICA ----------------
with tab_fv:
    st.subheader("Instalacion Fotovoltaica")
    if modulos.get("fv"):
        fv = st.session_state["fv_datos"]
        col1, col2 = st.columns(2)
        with col1:
            fv["potencia_pico_kwp"] = st.number_input("Potencia pico (kWp)", value=float(fv.get("potencia_pico_kwp", 5.0)), min_value=0.0, step=0.5)
            fv["tension_mppt_v"] = st.number_input("Tension MPPT (V)", value=float(fv.get("tension_mppt_v", 600.0)), min_value=1.0, step=10.0)
            fv["num_paneles"] = st.number_input("Numero de paneles", value=int(fv.get("num_paneles", 12)), min_value=1, step=1)
            fv["longitud_dc_m"] = st.number_input("Longitud tramo CC (m)", value=float(fv.get("longitud_dc_m", 20.0)), min_value=0.0, step=1.0)
        with col2:
            fv["potencia_inversor_kw"] = st.number_input("Potencia inversor (kW)", value=float(fv.get("potencia_inversor_kw", 5.0)), min_value=0.0, step=0.5)
            fv["tension_ac_v"] = st.number_input("Tension CA (V)", value=float(fv.get("tension_ac_v", 400.0)), min_value=1.0, step=10.0)
            fv["longitud_ac_m"] = st.number_input("Longitud tramo CA (m)", value=float(fv.get("longitud_ac_m", 15.0)), min_value=0.0, step=1.0)

        resultado_fv = calcular_fv(
            fv["potencia_pico_kwp"], fv["tension_mppt_v"], fv["num_paneles"],
            fv["longitud_dc_m"], fv["longitud_ac_m"], fv["potencia_inversor_kw"], fv["tension_ac_v"],
        )
        df_fv_calc = pd.DataFrame([resultado_fv])
        st.markdown("#### Resultados de calculo")
        cols = st.columns(4)
        cols[0].metric("Intensidad DC", f"{resultado_fv['Intensidad DC (A)']} A")
        cols[1].metric("Seccion DC", f"{resultado_fv['Seccion DC (mm2)']} mm2")
        cols[2].metric("Intensidad AC", f"{resultado_fv['Intensidad AC (A)']} A")
        cols[3].metric("Seccion AC", f"{resultado_fv['Seccion AC (mm2)']} mm2")
        st.dataframe(df_fv_calc, use_container_width=True)
    else:
        st.info("Activa el modulo 'Fotovoltaica' en la barra lateral para realizar el dimensionado.")


# ---------------- INDUSTRIAL / MOTORES ----------------
with tab_ind:
    st.subheader("Motores e instalacion industrial")
    if modulos.get("industrial"):
        df_editado_m = st.data_editor(
            st.session_state["df_motores"],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_motores",
            column_config={
                "Fases": st.column_config.SelectboxColumn(options=["Monofasico", "Trifasico"]),
                "Metodo arranque": st.column_config.SelectboxColumn(options=list(FACTORES_ARRANQUE_MOTOR.keys())),
                "Metodo instalacion": st.column_config.SelectboxColumn(options=list(METODOS_INSTALACION.keys())),
            },
        )
        detectar_cambios_df("df_motores", df_editado_m, "motores")
        st.session_state["df_motores"] = df_editado_m

        if not df_editado_m.empty:
            resultados_m = df_editado_m.apply(lambda f: pd.Series(calcular_motor(f)), axis=1)
            df_motores_calc = pd.concat([df_editado_m.reset_index(drop=True), resultados_m.reset_index(drop=True)], axis=1)
            st.markdown("#### Resultados de calculo")
            st.dataframe(df_motores_calc, use_container_width=True)
    else:
        st.info("Activa el modulo 'Industrial / Motores' en la barra lateral.")

# ---------------- MEDICIONES ----------------
with tab_med:
    st.subheader("Mediciones")
    df_auto = generar_mediciones_auto(df_bt_calc if modulos.get("bt") else None, df_motores_calc if modulos.get("industrial") else None)
    st.markdown("#### Mediciones generadas automaticamente")
    st.dataframe(df_auto, use_container_width=True)

    st.markdown("#### Mediciones manuales adicionales")
    df_manual_editado = st.data_editor(
        st.session_state["df_mediciones_manual"], num_rows="dynamic", use_container_width=True, key="editor_mediciones",
    )
    detectar_cambios_df("df_mediciones_manual", df_manual_editado, "mediciones manuales")
    st.session_state["df_mediciones_manual"] = df_manual_editado

    df_mediciones_total = pd.concat([df_auto, df_manual_editado], ignore_index=True) if not df_manual_editado.empty else df_auto

# ---------------- PRESUPUESTO ----------------
with tab_pres:
    st.subheader("Presupuesto")
    df_presupuesto, resumen = calcular_presupuesto(df_mediciones_total)
    st.dataframe(df_presupuesto, use_container_width=True)

    if resumen:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PEM", f"{resumen['PEM']:,.2f} EUR")
        c2.metric("Base licitacion", f"{resumen['Base de licitacion']:,.2f} EUR")
        c3.metric("IVA", f"{resumen['IVA']:,.2f} EUR")
        c4.metric("TOTAL", f"{resumen['TOTAL']:,.2f} EUR")

        try:
            import plotly.express as px
            if not df_presupuesto.empty:
                resumen_capitulo = df_presupuesto.groupby("Capitulo")["Importe (EUR)"].sum().reset_index()
                fig = px.bar(resumen_capitulo, x="Capitulo", y="Importe (EUR)", title="Importe por capitulo", color="Capitulo")
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    with st.expander("Editar precios por defecto"):
        for k in list(PRECIOS_DEFECTO.keys()):
            PRECIOS_DEFECTO[k] = st.number_input(k, value=float(PRECIOS_DEFECTO[k]), key=f"precio_{k}")

# ---------------- ESQUEMA UNIFILAR ----------------
with tab_esq:
    st.subheader("Esquema unifilar")
    st.caption(
        "Configurador tipo CIEBT: selecciona el tipo de suministro en la barra lateral y genera "
        "el esquema unifilar con la cadena de acometida, proteccion, medida y derivaciones a cada "
        "circuito interior, listo para exportar en formato DXF."
    )
    info_sum = TIPOS_SUMINISTRO[st.session_state["tipo_suministro"]]
    st.markdown(f"**Tipo de suministro seleccionado:** {st.session_state['tipo_suministro']}")
    st.markdown(info_sum["descripcion"])
    st.markdown("**Elementos que se incluiran en el esquema:**")
    for el in info_sum["elementos"]:
        st.markdown(f"- {el}")
    if not df_bt_calc.empty:
        st.markdown(f"Se incluiran **{len(df_bt_calc)}** circuitos interiores derivados del embarrado del cuadro general.")
    else:
        st.warning("No hay circuitos de Baja Tension definidos todavia; el esquema se generara solo con la parte de suministro.")

# ---------------- MEMORIA ----------------
with tab_mem:
    st.subheader("Memoria Tecnica de Diseño (MTD)")
    dp["objeto"] = st.text_area("1. Objeto de la memoria", value=dp.get("objeto", ""), height=80)
    dp["normativa"] = st.text_area("3. Reglamentacion y disposiciones aplicadas", value=dp.get("normativa", ""), height=80)
    dp["descripcion"] = st.text_area("4. Descripcion general de la instalacion (potencia, uso, caracteristicas)", value=dp.get("descripcion", ""), height=100)

    texto_memoria = generar_memoria_texto({
        "datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"],
    })
    st.markdown("#### Vista previa")
    st.text_area("Contenido de la memoria", value=texto_memoria, height=350)


# ---------------- IMPORTAR / EXPORTAR ----------------
with tab_io:
    st.subheader("Importar datos desde archivo")
    st.markdown("Descarga las plantillas, rellenalas y vuelve a subirlas para importar circuitos, motores o mediciones de forma masiva.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button("Plantilla circuitos BT (.csv)", data=df_vacio(COLUMNAS_BT).to_csv(index=False), file_name="plantilla_circuitos_bt.csv", mime="text/csv")
    with col_b:
        st.download_button("Plantilla motores (.csv)", data=df_vacio(COLUMNAS_MOTORES).to_csv(index=False), file_name="plantilla_motores.csv", mime="text/csv")
    with col_c:
        st.download_button("Plantilla mediciones (.csv)", data=df_vacio(COLUMNAS_MEDICION_MANUAL).to_csv(index=False), file_name="plantilla_mediciones.csv", mime="text/csv")

    tipo_importacion = st.selectbox("¿Que deseas importar?", ["Circuitos de Baja Tension", "Motores", "Mediciones manuales"])
    archivo_datos = st.file_uploader("Selecciona un archivo .csv o .xlsx", type=["csv", "xlsx"], key="cargador_datos")
    if archivo_datos is not None:
        try:
            if archivo_datos.name.endswith(".csv"):
                df_importado = pd.read_csv(archivo_datos)
            else:
                df_importado = pd.read_excel(archivo_datos)
            if tipo_importacion == "Circuitos de Baja Tension":
                st.session_state["df_bt"] = df_importado
            elif tipo_importacion == "Motores":
                st.session_state["df_motores"] = df_importado
            else:
                st.session_state["df_mediciones_manual"] = df_importado
            registrar_cambio("Importacion de archivo", f"{tipo_importacion} desde {archivo_datos.name}")
            st.success(f"Datos de '{tipo_importacion}' importados correctamente. Revisa la pestaña correspondiente.")
        except Exception as e:
            st.error(f"No se ha podido importar el archivo: {e}")

    st.divider()
    st.subheader("Exportar resultados")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        buffer_excel = exportar_excel(df_bt_calc, df_motores_calc, df_mediciones_total if "df_mediciones_total" in dir() else None, resumen if "resumen" in dir() else {})
        st.download_button("\U0001F4CA Excel (mediciones/presupuesto)", data=buffer_excel, file_name="calculo_electrico.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col2:
        try:
            dxf_bytes = generar_esquema_unifilar_dxf({"datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"]}, df_bt_calc)
            st.download_button("\U0001F4D0 Esquema unifilar (.dxf)", data=dxf_bytes, file_name="esquema_unifilar.dxf", mime="application/dxf")
            st.caption("Formato DXF abierto; se puede abrir y guardar como .dwg desde AutoCAD.")
        except Exception as e:
            st.error(f"No se ha podido generar el DXF: {e}")

    with col3:
        try:
            buffer_pdf = exportar_memoria_pdf(
                {"datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"]},
                texto_memoria, df_bt_calc, df_fv_calc, df_motores_calc,
                df_mediciones_total if "df_mediciones_total" in dir() else None,
                resumen if "resumen" in dir() else {},
            )
            st.download_button("\U0001F4C4 Memoria (.pdf)", data=buffer_pdf, file_name="memoria_tecnica.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"No se ha podido generar el PDF: {e}")

    with col4:
        try:
            buffer_word = exportar_memoria_word(texto_memoria)
            st.download_button("\U0001F4DD Memoria (.docx)", data=buffer_word, file_name="memoria_tecnica.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e:
            st.error(f"No se ha podido generar el Word: {e}")
