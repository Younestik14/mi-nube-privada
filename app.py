"""
PROYECTISTA ELECTRICO - REBT
Aplicacion Streamlit para el predimensionado de instalaciones electricas de baja
tension, fotovoltaica de autoconsumo e industrial/motores, conforme al Reglamento
Electrotecnico para Baja Tension (RD 842/2002) y sus Instrucciones Tecnicas
Complementarias (ITC-BT), y al RD 244/2019 de autoconsumo.

AVISO IMPORTANTE
Esta herramienta es de apoyo al predimensionado y uso profesional/didactico. Los
valores de intensidades admisibles, factores de correccion y demas datos tecnicos
son de referencia segun las tablas habituales del REBT (ITC-BT-19, ITC-BT-47,
ITC-BT-40). Antes de emitir documentacion oficial (proyecto, memoria tecnica,
boletin electrico, etc.) se debe verificar cada resultado contra las tablas
oficiales vigentes del REBT/ITC-BT, la normativa de la companhia distribuidora y
el criterio de un tecnico competente colegiado.
"""

import io
import json
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Proyectista Electrico - REBT", page_icon="\u26a1", layout="wide")

# =====================================================================================
# 0. ESTILO VISUAL
# =====================================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: #10263f; }
[data-testid="stMetric"] { background: #f6f4ee; border: 1px solid #e2ddcf; border-radius: 10px; padding: 12px 16px; }
[data-testid="stMetricLabel"] { color: #45688a; font-weight: 600; }
[data-testid="stMetricValue"] { color: #10263f; font-family: 'IBM Plex Mono', monospace; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 15px; }
.stTabs [aria-selected="true"] { color: #c8790f !important; }
div[data-testid="stExpander"] { border: 1px solid #e2ddcf; border-radius: 8px; }
.bloque-nota { background: #f4e2c3; border-left: 4px solid #c8790f; padding: 10px 14px; border-radius: 4px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# =====================================================================================
# 1. DATOS TECNICOS DE REFERENCIA (REBT / ITC-BT)
# =====================================================================================

SECCIONES_MM2 = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# ITC-BT-19, Tabla 1 (orientativa). Intensidades admisibles (A). Conductores de cobre,
# aislamiento PVC, 2 conductores cargados. Metodos de instalacion de referencia
# segun UNE-HD 60364-5-52 / guia tecnica de aplicacion de la ITC-BT-19.
AMPACIDAD = {
    "A1 - Conductores aislados en conducto empotrado en pared aislante": {
        1.5: 13, 2.5: 17.5, 4: 23, 6: 29, 10: 39, 16: 52, 25: 68, 35: 83,
        50: 99, 70: 125, 95: 150, 120: 172, 150: 196, 185: 223, 240: 261, 300: 298,
    },
    "A2 - Cable multiconductor en conducto empotrado en pared aislante": {
        1.5: 13.5, 2.5: 18, 4: 24, 6: 31, 10: 42, 16: 56, 25: 73, 35: 89,
        50: 108, 70: 136, 95: 164, 120: 188, 150: 216, 185: 245, 240: 286, 300: 328,
    },
    "B1 - Conductores aislados en tubo empotrado en obra o en superficie": {
        1.5: 15, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 111,
        50: 134, 70: 171, 95: 207, 120: 239, 150: 262, 185: 296, 240: 346, 300: 388,
    },
    "B2 - Cable multiconductor en tubo en superficie": {
        1.5: 14, 2.5: 19, 4: 25, 6: 32, 10: 45, 16: 61, 25: 80, 35: 96,
        50: 118, 70: 150, 95: 180, 120: 208, 150: 228, 185: 255, 240: 297, 300: 339,
    },
    "C - Cable multiconductor tendido directo sobre pared o techo": {
        1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 96, 35: 119,
        50: 144, 70: 184, 95: 223, 120: 259, 150: 299, 185: 341, 240: 403, 300: 464,
    },
    "D - Cable multiconductor enterrado (bajo tubo o directo)": {
        1.5: 18, 2.5: 24, 4: 31, 6: 39, 10: 52, 16: 67, 25: 86, 35: 103,
        50: 122, 70: 151, 95: 179, 120: 203, 150: 230, 185: 258, 240: 297, 300: 336,
    },
    "E - Cable multiconductor al aire libre / bandeja perforada": {
        1.5: 19, 2.5: 26, 4: 35, 6: 45, 10: 61, 16: 82, 25: 108, 35: 133,
        50: 161, 70: 205, 95: 249, 120: 289, 150: 332, 185: 378, 240: 445, 300: 512,
    },
    "F - Cables unipolares en contacto mutuo, al aire libre": {
        1.5: 19.5, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 112, 35: 138,
        50: 168, 70: 213, 95: 258, 120: 299, 150: 344, 185: 392, 240: 461, 300: 530,
    },
    "G - Cables unipolares separados entre si, al aire libre": {
        1.5: 22, 2.5: 30, 4: 40, 6: 51, 10: 70, 16: 94, 25: 119, 35: 148,
        50: 180, 70: 232, 95: 282, 120: 328, 150: 379, 185: 434, 240: 514, 300: 593,
    },
}

FACTOR_TEMPERATURA = {25: 1.12, 30: 1.08, 35: 1.04, 40: 1.00, 45: 0.91, 50: 0.82, 55: 0.71}
FACTOR_AGRUPAMIENTO = {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60, 6: 0.57, 7: 0.54, 8: 0.52, 9: 0.50}
PROTECCIONES_NORMALIZADAS = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400]

CDT_MAXIMA = {
    "Linea general de alimentacion (LGA)": 0.5,
    "Derivacion individual (con centralizacion de contadores)": 1.0,
    "Derivacion individual (contador unico)": 1.5,
    "Instalacion interior - Alumbrado": 3.0,
    "Instalacion interior - Otros usos (fuerza, tomas...)": 5.0,
}

RESISTIVIDAD_INV_CU = 56.0

FACTORES_ARRANQUE_MOTOR = {
    "Directo": 7.0,
    "Estrella-Triangulo": 2.5,
    "Arrancador electronico (soft-starter)": 3.5,
    "Variador de frecuencia (VFD)": 1.2,
}

PRECIOS_DEFECTO = {
    "cable_1_5": 0.55, "cable_2_5": 0.78, "cable_4": 1.15, "cable_6": 1.65, "cable_10": 2.60,
    "cable_16": 4.10, "cable_25": 6.80, "cable_35": 9.40, "cable_50": 13.20, "cable_70": 18.60,
    "cable_95": 24.50, "cable_120": 31.00, "cable_150": 38.50, "cable_185": 47.00,
    "cable_240": 62.00, "cable_300": 78.00,
    "magnetotermico": 9.50, "diferencial": 42.00, "guardamotor": 55.00,
    "tubo_corrugado": 1.20, "panel_fv": 145.00, "inversor": 650.00, "estructura_fv": 60.00,
    "mecanismo": 6.50, "caja_derivacion": 3.20, "cuadro_general": 85.00, "mano_obra_h": 24.00,
}

COLUMNAS_BT = ["Circuito", "Tipo de receptor", "Fases", "Tension (V)", "Potencia (W)",
               "cos phi", "Longitud (m)", "Temp. ambiente (C)", "Circuitos agrupados",
               "Tipo de linea (cdt)"]
COLUMNAS_MOTORES = ["Motor", "Potencia (kW)", "Tension (V)", "cos phi", "Rendimiento (%)",
                     "Tipo de arranque", "Longitud (m)"]
COLUMNAS_MEDICION_MANUAL = ["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"]


def df_vacio(columnas):
    return pd.DataFrame(columns=columnas)

# =====================================================================================
# 2. FUNCIONES DE CALCULO ELECTRICO
# =====================================================================================

def intensidad_mono(p_w, v, cosphi):
    if not v or not cosphi:
        return 0.0
    return p_w / (v * cosphi)


def intensidad_tri(p_w, v, cosphi):
    if not v or not cosphi:
        return 0.0
    return p_w / (np.sqrt(3) * v * cosphi)


def cdt_mono_pct(long_m, i, cosphi, s_mm2, v):
    if not s_mm2 or not v:
        return 0.0
    return (2 * long_m * i * cosphi) / (RESISTIVIDAD_INV_CU * s_mm2) / v * 100


def cdt_tri_pct(long_m, i, cosphi, s_mm2, v):
    if not s_mm2 or not v:
        return 0.0
    return (np.sqrt(3) * long_m * i * cosphi) / (RESISTIVIDAD_INV_CU * s_mm2) / v * 100


def elegir_seccion_por_intensidad(ib, metodo, factor_correccion):
    tabla = AMPACIDAD[metodo]
    factor_correccion = factor_correccion or 1.0
    for s in SECCIONES_MM2:
        if tabla[s] * factor_correccion >= ib:
            return s
    return SECCIONES_MM2[-1]


def elegir_seccion_por_cdt(long_m, ib, cosphi, v, limite_pct, fases):
    for s in SECCIONES_MM2:
        cdt = cdt_tri_pct(long_m, ib, cosphi, s, v) if fases == "Trifasico" else cdt_mono_pct(long_m, ib, cosphi, s, v)
        if cdt <= limite_pct:
            return s
    return SECCIONES_MM2[-1]


def elegir_proteccion(ib, iz_corregida):
    candidatos = [p for p in PROTECCIONES_NORMALIZADAS if p >= ib]
    if not candidatos:
        return PROTECCIONES_NORMALIZADAS[-1]
    validas = [p for p in candidatos if p <= iz_corregida]
    return validas[0] if validas else candidatos[0]


def calcular_circuito_bt(row, metodo_instalacion):
    fases = row.get("Fases", "Monofasico")
    p = float(row.get("Potencia (W)", 0) or 0)
    v = float(row.get("Tension (V)", 230) or 230)
    cosphi = float(row.get("cos phi", 0.95) or 0.95)
    longitud = float(row.get("Longitud (m)", 0) or 0)
    temp = int(float(row.get("Temp. ambiente (C)", 40) or 40))
    agrup = int(float(row.get("Circuitos agrupados", 1) or 1))
    tipo_linea = row.get("Tipo de linea (cdt)", "Instalacion interior - Otros usos (fuerza, tomas...)")
    limite_cdt = CDT_MAXIMA.get(tipo_linea, 5.0)

    ib = intensidad_tri(p, v, cosphi) if fases == "Trifasico" else intensidad_mono(p, v, cosphi)
    f_temp = FACTOR_TEMPERATURA.get(temp, 1.0)
    f_agr = FACTOR_AGRUPAMIENTO.get(agrup, 1.0)
    factor_corr = f_temp * f_agr

    s_int = elegir_seccion_por_intensidad(ib, metodo_instalacion, factor_corr)
    s_cdt = elegir_seccion_por_cdt(longitud, ib, cosphi, v, limite_cdt, fases)
    seccion = max(s_int, s_cdt)

    iz = AMPACIDAD[metodo_instalacion][seccion] * factor_corr
    cdt = cdt_tri_pct(longitud, ib, cosphi, seccion, v) if fases == "Trifasico" else cdt_mono_pct(longitud, ib, cosphi, seccion, v)
    proteccion = elegir_proteccion(ib, iz)
    cumple = (cdt <= limite_cdt) and (iz >= ib) and (ib <= proteccion <= iz)

    return pd.Series({
        "Ib (A)": round(ib, 2),
        "Seccion (mm2)": seccion,
        "Iz corregida (A)": round(iz, 2),
        "c.d.t. (%)": round(cdt, 2),
        "cdt max (%)": limite_cdt,
        "Proteccion (A)": proteccion,
        "Cumple": "Cumple" if cumple else "Revisar",
    })


def calcular_fv(datos, metodo_instalacion):
    isc = float(datos.get("isc", 0) or 0)
    impp = float(datos.get("impp", 0) or 0)
    num_strings = int(float(datos.get("num_strings", 1) or 1))
    vmpp = float(datos.get("vmpp", 1) or 1)
    dist_dc = float(datos.get("dist_string_inversor", 0) or 0)
    potencia_inversor = float(datos.get("potencia_inversor", 0) or 0)
    tension_ac = float(datos.get("tension_ac", 400) or 400)
    fases_ac = datos.get("fases_ac", "Trifasico")
    dist_ac = float(datos.get("dist_inversor_cuadro", 0) or 0)

    idc_diseno = isc * num_strings * 1.25
    idc_servicio = impp * num_strings
    seccion_dc = elegir_seccion_por_intensidad(idc_diseno, metodo_instalacion, 1.0)
    cdt_dc = cdt_mono_pct(dist_dc, idc_servicio, 1.0, seccion_dc, vmpp)
    requiere_fusibles_dc = num_strings > 2

    fases_norm = "Trifasico" if fases_ac == "Trifasico" else "Monofasico"
    iac = intensidad_tri(potencia_inversor, tension_ac, 1.0) if fases_norm == "Trifasico" else intensidad_mono(potencia_inversor, tension_ac, 1.0)
    seccion_ac = elegir_seccion_por_intensidad(iac * 1.25, metodo_instalacion, 1.0)
    cdt_ac = cdt_tri_pct(dist_ac, iac, 1.0, seccion_ac, tension_ac) if fases_norm == "Trifasico" else cdt_mono_pct(dist_ac, iac, 1.0, seccion_ac, tension_ac)
    proteccion_ac = elegir_proteccion(iac, AMPACIDAD[metodo_instalacion][seccion_ac])

    return {
        "idc_diseno": idc_diseno, "idc_servicio": idc_servicio, "seccion_dc": seccion_dc,
        "cdt_dc": cdt_dc, "requiere_fusibles_dc": requiere_fusibles_dc,
        "iac": iac, "seccion_ac": seccion_ac, "cdt_ac": cdt_ac, "proteccion_ac": proteccion_ac,
    }


def calcular_motor(row, metodo_instalacion):
    p_kw = float(row.get("Potencia (kW)", 0) or 0)
    v = float(row.get("Tension (V)", 400) or 400)
    cosphi = float(row.get("cos phi", 0.85) or 0.85)
    rendimiento = float(row.get("Rendimiento (%)", 90) or 90) / 100
    tipo_arranque = row.get("Tipo de arranque", "Directo")
    longitud = float(row.get("Longitud (m)", 0) or 0)

    in_ = (p_kw * 1000) / (np.sqrt(3) * v * cosphi * rendimiento) if v and cosphi and rendimiento else 0.0
    factor_arranque = FACTORES_ARRANQUE_MOTOR.get(tipo_arranque, 7.0)
    ia = in_ * factor_arranque

    seccion = elegir_seccion_por_intensidad(in_ * 1.25, metodo_instalacion, 1.0)
    iz = AMPACIDAD[metodo_instalacion][seccion]
    cdt = cdt_tri_pct(longitud, in_, cosphi, seccion, v)

    termico_min = in_ * 1.00
    termico_max = in_ * 1.15
    guardamotor = elegir_proteccion(in_, iz)

    return pd.Series({
        "In (A)": round(in_, 2),
        "Ia arranque (A)": round(ia, 2),
        "Seccion (mm2)": seccion,
        "c.d.t. (%)": round(cdt, 2),
        "Termico min (A)": round(termico_min, 2),
        "Termico max (A)": round(termico_max, 2),
        "Guardamotor (A)": guardamotor,
    })

# =====================================================================================
# 3. MEDICIONES, PRESUPUESTO Y MEMORIA
# =====================================================================================

def clave_cable(seccion):
    return "cable_" + str(seccion).replace(".", "_")


def generar_mediciones_auto(circuitos_bt, fv_datos, motores, tipos_activos, metodo_instalacion):
    items = []
    if tipos_activos.get("bt") and not circuitos_bt.empty:
        for _, c in circuitos_bt.iterrows():
            r = calcular_circuito_bt(c, metodo_instalacion)
            nombre = c.get("Circuito", "circuito")
            items.append({"Capitulo": "Baja tension", "Descripcion": f"Cable {r['Seccion (mm2)']} mm2 - {nombre}",
                          "Unidad": "m", "Cantidad": float(c.get("Longitud (m)", 0) or 0), "precio_key": clave_cable(r["Seccion (mm2)"])})
            items.append({"Capitulo": "Baja tension", "Descripcion": f"Interruptor magnetotermico {r['Proteccion (A)']} A - {nombre}",
                          "Unidad": "ud", "Cantidad": 1, "precio_key": "magnetotermico"})
        items.append({"Capitulo": "Baja tension", "Descripcion": "Interruptor diferencial 30 mA",
                      "Unidad": "ud", "Cantidad": max(1, int(np.ceil(len(circuitos_bt) / 5))), "precio_key": "diferencial"})
        items.append({"Capitulo": "Baja tension", "Descripcion": "Cuadro general de mando y proteccion",
                      "Unidad": "ud", "Cantidad": 1, "precio_key": "cuadro_general"})

    if tipos_activos.get("fv") and float(fv_datos.get("num_paneles", 0) or 0) > 0:
        r = calcular_fv(fv_datos, metodo_instalacion)
        num_paneles = float(fv_datos.get("num_paneles", 0) or 0)
        items.append({"Capitulo": "Fotovoltaica", "Descripcion": "Modulo fotovoltaico", "Unidad": "ud",
                      "Cantidad": num_paneles, "precio_key": "panel_fv"})
        items.append({"Capitulo": "Fotovoltaica", "Descripcion": "Inversor", "Unidad": "ud",
                      "Cantidad": 1, "precio_key": "inversor"})
        items.append({"Capitulo": "Fotovoltaica", "Descripcion": "Estructura soporte", "Unidad": "ud",
                      "Cantidad": num_paneles, "precio_key": "estructura_fv"})
        items.append({"Capitulo": "Fotovoltaica", "Descripcion": f"Cable CC {r['seccion_dc']} mm2", "Unidad": "m",
                      "Cantidad": float(fv_datos.get("dist_string_inversor", 0) or 0) * 2, "precio_key": clave_cable(r["seccion_dc"])})
        items.append({"Capitulo": "Fotovoltaica", "Descripcion": f"Cable CA {r['seccion_ac']} mm2", "Unidad": "m",
                      "Cantidad": float(fv_datos.get("dist_inversor_cuadro", 0) or 0) * 2, "precio_key": clave_cable(r["seccion_ac"])})

    if tipos_activos.get("industrial") and not motores.empty:
        for _, m in motores.iterrows():
            r = calcular_motor(m, metodo_instalacion)
            nombre = m.get("Motor", "motor")
            items.append({"Capitulo": "Industrial", "Descripcion": f"Cable {r['Seccion (mm2)']} mm2 - motor {nombre}",
                          "Unidad": "m", "Cantidad": float(m.get("Longitud (m)", 0) or 0), "precio_key": clave_cable(r["Seccion (mm2)"])})
            items.append({"Capitulo": "Industrial", "Descripcion": f"Guardamotor {r['Guardamotor (A)']} A - {nombre}",
                          "Unidad": "ud", "Cantidad": 1, "precio_key": "guardamotor"})

    df = pd.DataFrame(items)
    if df.empty:
        df = pd.DataFrame(columns=["Capitulo", "Descripcion", "Unidad", "Cantidad", "precio_key"])
    df["auto"] = True
    return df


def calcular_presupuesto(mediciones_auto, mediciones_manual, precios, gastos_generales, beneficio_industrial, iva):
    filas = mediciones_auto.copy()
    filas["Precio unitario (EUR)"] = filas["precio_key"].map(lambda k: precios.get(k, 0.0))
    filas = filas[["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"]]

    manual = mediciones_manual.copy()
    if not manual.empty:
        manual = manual[["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"]]
        todas = pd.concat([filas, manual], ignore_index=True)
    else:
        todas = filas

    if todas.empty:
        todas = pd.DataFrame(columns=["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"])

    todas["Cantidad"] = pd.to_numeric(todas["Cantidad"], errors="coerce").fillna(0)
    todas["Precio unitario (EUR)"] = pd.to_numeric(todas["Precio unitario (EUR)"], errors="coerce").fillna(0)
    todas["Importe (EUR)"] = (todas["Cantidad"] * todas["Precio unitario (EUR)"]).round(2)

    por_capitulo = todas.groupby("Capitulo")["Importe (EUR)"].sum() if not todas.empty else pd.Series(dtype=float)
    pem = todas["Importe (EUR)"].sum()
    gg = pem * (gastos_generales / 100)
    bi = pem * (beneficio_industrial / 100)
    pca = pem + gg + bi
    iva_importe = pca * (iva / 100)
    total = pca + iva_importe

    return {"filas": todas, "por_capitulo": por_capitulo, "pem": pem, "gg": gg, "bi": bi,
            "pca": pca, "iva_importe": iva_importe, "total": total}


def generar_memoria_texto(proyecto, circuitos_bt, fv_datos, motores, memoria, tipos_activos, metodo_instalacion):
    partes = []
    partes.append("1. OBJETO\n" + (memoria.get("objeto") or
        f"El objeto de la presente memoria es describir y justificar la instalacion electrica de "
        f"\"{proyecto.get('nombre') or '[nombre del proyecto]'}\", conforme al Reglamento Electrotecnico "
        f"para Baja Tension (RD 842/2002) y sus Instrucciones Tecnicas Complementarias."))
    partes.append("2. TITULAR\n" + (memoria.get("titular") or proyecto.get("cliente") or "[titular]"))
    partes.append("3. EMPLAZAMIENTO\n" + (memoria.get("emplazamiento") or proyecto.get("ubicacion") or "[emplazamiento]"))
    partes.append("4. DESCRIPCION DE LA INSTALACION\n" + (memoria.get("descripcion") or
        "Se describe a continuacion cada uno de los subsistemas incluidos en el proyecto. Metodo de "
        f"instalacion de referencia adoptado: {metodo_instalacion}."))

    if tipos_activos.get("bt") and not circuitos_bt.empty:
        texto = "4.1. Instalacion de baja tension (ITC-BT-19, ITC-BT-25)\nCuadro de circuitos calculados:\n"
        for i, (_, c) in enumerate(circuitos_bt.iterrows(), start=1):
            r = calcular_circuito_bt(c, metodo_instalacion)
            texto += (f" C{i} {c.get('Circuito', 'circuito')}: {c.get('Potencia (W)', 0)} W, "
                      f"{r['Seccion (mm2)']} mm2, Ib={r['Ib (A)']} A, c.d.t.={r['c.d.t. (%)']}%, "
                      f"proteccion {r['Proteccion (A)']} A ({r['Cumple']}).\n")
        partes.append(texto)

    if tipos_activos.get("fv") and float(fv_datos.get("num_paneles", 0) or 0) > 0:
        r = calcular_fv(fv_datos, metodo_instalacion)
        partes.append("4.2. Instalacion fotovoltaica de autoconsumo (RD 244/2019, ITC-BT-40)\n"
            f"Potencia pico: {fv_datos.get('potencia_pico', '-')} kWp ({fv_datos.get('num_paneles', '-')} modulos). "
            f"Tramo CC: seccion {r['seccion_dc']} mm2, c.d.t. {round(r['cdt_dc'], 2)}%. "
            f"Tramo CA: seccion {r['seccion_ac']} mm2, proteccion {r['proteccion_ac']} A, c.d.t. {round(r['cdt_ac'], 2)}%.")

    if tipos_activos.get("industrial") and not motores.empty:
        texto = "4.3. Instalacion industrial / motores (ITC-BT-47)\n"
        for _, m in motores.iterrows():
            r = calcular_motor(m, metodo_instalacion)
            texto += (f" {m.get('Motor', 'Motor')}: {m.get('Potencia (kW)', 0)} kW, In={r['In (A)']} A, "
                      f"Ia={r['Ia arranque (A)']} A, seccion {r['Seccion (mm2)']} mm2, "
                      f"guardamotor {r['Guardamotor (A)']} A.\n")
        partes.append(texto)

    partes.append("5. NORMATIVA APLICABLE\n" + (memoria.get("normativa") or
        "Reglamento Electrotecnico para Baja Tension (RD 842/2002) e Instrucciones Tecnicas "
        "Complementarias ITC-BT correspondientes. RD 244/2019 de autoconsumo, en su caso. "
        "Normativa municipal y de la companhia distribuidora aplicable."))

    return "\n\n".join(partes)

# =====================================================================================
# 4. ESTADO DE LA SESION
# =====================================================================================

def inicializar_estado():
    defaults = {
        "proyecto": {"nombre": "", "cliente": "", "ubicacion": "", "tecnico": "", "fecha": str(date.today())},
        "tipos_activos": {"bt": True, "fv": False, "industrial": False},
        "metodo_instalacion": list(AMPACIDAD.keys())[2],
        "circuitos_bt": df_vacio(COLUMNAS_BT),
        "fv_datos": {"potencia_pico": "", "num_paneles": "", "potencia_panel": "", "voc": "", "isc": "",
                     "vmpp": "", "impp": "", "num_strings": 1, "dist_string_inversor": 15.0,
                     "potencia_inversor": "", "tension_ac": 400.0, "fases_ac": "Trifasico",
                     "dist_inversor_cuadro": 5.0},
        "motores": df_vacio(COLUMNAS_MOTORES),
        "mediciones_manual": df_vacio(COLUMNAS_MEDICION_MANUAL),
        "precios": dict(PRECIOS_DEFECTO),
        "gastos_generales": 13.0, "beneficio_industrial": 6.0, "iva": 21.0,
        "memoria": {"objeto": "", "titular": "", "emplazamiento": "", "descripcion": "", "normativa": ""},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def estado_a_dict():
    s = st.session_state
    return {
        "proyecto": s.proyecto, "tipos_activos": s.tipos_activos, "metodo_instalacion": s.metodo_instalacion,
        "circuitos_bt": s.circuitos_bt.to_dict(orient="records"),
        "fv_datos": s.fv_datos, "motores": s.motores.to_dict(orient="records"),
        "mediciones_manual": s.mediciones_manual.to_dict(orient="records"),
        "precios": s.precios, "gastos_generales": s.gastos_generales,
        "beneficio_industrial": s.beneficio_industrial, "iva": s.iva, "memoria": s.memoria,
    }


def cargar_estado_desde_dict(d):
    if "proyecto" in d:
        st.session_state.proyecto = d["proyecto"]
    if "tipos_activos" in d:
        st.session_state.tipos_activos = d["tipos_activos"]
    if "metodo_instalacion" in d and d["metodo_instalacion"] in AMPACIDAD:
        st.session_state.metodo_instalacion = d["metodo_instalacion"]
    if "circuitos_bt" in d:
        st.session_state.circuitos_bt = pd.DataFrame(d["circuitos_bt"], columns=COLUMNAS_BT) if d["circuitos_bt"] else df_vacio(COLUMNAS_BT)
    if "fv_datos" in d:
        st.session_state.fv_datos = d["fv_datos"]
    if "motores" in d:
        st.session_state.motores = pd.DataFrame(d["motores"], columns=COLUMNAS_MOTORES) if d["motores"] else df_vacio(COLUMNAS_MOTORES)
    if "mediciones_manual" in d:
        st.session_state.mediciones_manual = pd.DataFrame(d["mediciones_manual"], columns=COLUMNAS_MEDICION_MANUAL) if d["mediciones_manual"] else df_vacio(COLUMNAS_MEDICION_MANUAL)
    if "precios" in d:
        st.session_state.precios = d["precios"]
    if "gastos_generales" in d:
        st.session_state.gastos_generales = d["gastos_generales"]
    if "beneficio_industrial" in d:
        st.session_state.beneficio_industrial = d["beneficio_industrial"]
    if "iva" in d:
        st.session_state.iva = d["iva"]
    if "memoria" in d:
        st.session_state.memoria = d["memoria"]


def exportar_excel(presupuesto, circuitos_bt, metodo_instalacion):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        presupuesto["filas"].to_excel(writer, sheet_name="Mediciones y precios", index=False)

        resumen = pd.DataFrame([
            {"Concepto": "PEM (Presupuesto Ejecucion Material)", "Importe (EUR)": round(presupuesto["pem"], 2)},
            {"Concepto": "Gastos generales", "Importe (EUR)": round(presupuesto["gg"], 2)},
            {"Concepto": "Beneficio industrial", "Importe (EUR)": round(presupuesto["bi"], 2)},
            {"Concepto": "Presupuesto de contrata (sin IVA)", "Importe (EUR)": round(presupuesto["pca"], 2)},
            {"Concepto": "IVA", "Importe (EUR)": round(presupuesto["iva_importe"], 2)},
            {"Concepto": "TOTAL PRESUPUESTO", "Importe (EUR)": round(presupuesto["total"], 2)},
        ])
        resumen.to_excel(writer, sheet_name="Resumen presupuesto", index=False)

        if not circuitos_bt.empty:
            filas_bt = []
            for i, (_, c) in enumerate(circuitos_bt.iterrows(), start=1):
                r = calcular_circuito_bt(c, metodo_instalacion)
                filas_bt.append({"Circuito": f"C{i}", **c.to_dict(), **r.to_dict()})
            pd.DataFrame(filas_bt).to_excel(writer, sheet_name="Calculo BT", index=False)
    buffer.seek(0)
    return buffer


def exportar_memoria_word(texto, proyecto):
    try:
        from docx import Document
    except ImportError:
        return None
    doc = Document()
    doc.add_heading(proyecto.get("nombre") or "Memoria tecnica", level=1)
    tabla = doc.add_table(rows=0, cols=2)
    for campo, valor in [("Cliente", proyecto.get("cliente", "")), ("Emplazamiento", proyecto.get("ubicacion", "")),
                         ("Tecnico", proyecto.get("tecnico", "")), ("Fecha", proyecto.get("fecha", ""))]:
        fila = tabla.add_row().cells
        fila[0].text, fila[1].text = campo, str(valor)
    doc.add_paragraph("")
    for bloque in texto.split("\n\n"):
        doc.add_paragraph(bloque)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def exportar_memoria_pdf(estado_dict, texto_memoria, circuitos_bt, fv_datos, motores, presupuesto, metodo_instalacion):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloPortada", parent=styles["Title"], fontSize=22, spaceAfter=16, textColor=colors.HexColor("#10263f"))
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=styles["Heading2"], textColor=colors.HexColor("#c8790f"), spaceBefore=10, spaceAfter=6)
    estilo_normal = styles["Normal"]

    proyecto = estado_dict["proyecto"]
    story = []

    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph(proyecto.get("nombre") or "Memoria Tecnica", estilo_titulo))
    story.append(Paragraph("Memoria Tecnica Descriptiva - Instalacion Electrica", styles["Heading3"]))
    story.append(Spacer(1, 1.5 * cm))
    datos_portada = [
        ["Cliente / Titular:", proyecto.get("cliente", "") or "-"],
        ["Emplazamiento:", proyecto.get("ubicacion", "") or "-"],
        ["Tecnico redactor:", proyecto.get("tecnico", "") or "-"],
        ["Fecha:", proyecto.get("fecha", "") or "-"],
        ["Metodo de instalacion:", metodo_instalacion],
    ]
    tabla_portada = Table(datos_portada, colWidths=[5 * cm, 10 * cm])
    tabla_portada.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#45688a")),
    ]))
    story.append(tabla_portada)
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "Aviso: los valores de intensidades admisibles y factores de correccion utilizados son de "
        "referencia segun las tablas habituales del REBT/ITC-BT. Verificar contra las tablas oficiales "
        "vigentes antes de su uso en documentacion oficial.", styles["Italic"]))
    story.append(PageBreak())

    for bloque in texto_memoria.split("\n\n"):
        lineas = bloque.split("\n")
        titulo = lineas[0]
        cuerpo = lineas[1:]
        story.append(Paragraph(titulo, estilo_subtitulo))
        for parrafo in cuerpo:
            if parrafo.strip():
                texto_html = parrafo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(texto_html, estilo_normal))
        story.append(Spacer(1, 0.3 * cm))
    story.append(PageBreak())

    estilo_cabecera_tabla = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10263f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f4ee")]),
    ])

    if not circuitos_bt.empty:
        story.append(Paragraph("ANEXO I - Calculo de circuitos de baja tension (ITC-BT-19)", styles["Heading1"]))
        data = [["Circuito", "P (W)", "Fases", "Ib (A)", "Seccion (mm2)", "c.d.t. (%)", "Proteccion (A)", "Estado"]]
        for _, c in circuitos_bt.iterrows():
            r = calcular_circuito_bt(c, metodo_instalacion)
            data.append([str(c.get("Circuito", "")), str(c.get("Potencia (W)", "")), str(c.get("Fases", "")),
                         r["Ib (A)"], r["Seccion (mm2)"], r["c.d.t. (%)"], r["Proteccion (A)"], r["Cumple"]])
        t = Table(data, repeatRows=1)
        t.setStyle(estilo_cabecera_tabla)
        story.append(t)
        story.append(PageBreak())

    if float(fv_datos.get("num_paneles", 0) or 0) > 0:
        r = calcular_fv(fv_datos, metodo_instalacion)
        story.append(Paragraph("ANEXO II - Instalacion fotovoltaica de autoconsumo (RD 244/2019)", styles["Heading1"]))
        data = [["Parametro", "Valor"],
                ["Intensidad de diseno CC (1.25 x Isc)", f"{r['idc_diseno']:.2f} A"],
                ["Seccion tramo CC", f"{r['seccion_dc']} mm2"],
                ["c.d.t. tramo CC", f"{r['cdt_dc']:.2f} %"],
                ["Requiere fusibles por string", "Si" if r["requiere_fusibles_dc"] else "No"],
                ["Intensidad AC (salida inversor)", f"{r['iac']:.2f} A"],
                ["Seccion tramo AC", f"{r['seccion_ac']} mm2"],
                ["c.d.t. tramo AC", f"{r['cdt_ac']:.2f} %"],
                ["Proteccion AC", f"{r['proteccion_ac']} A"]]
        t = Table(data, colWidths=[9 * cm, 6 * cm])
        t.setStyle(estilo_cabecera_tabla)
        story.append(t)
        story.append(PageBreak())

    if not motores.empty:
        story.append(Paragraph("ANEXO III - Motores e instalacion industrial (ITC-BT-47)", styles["Heading1"]))
        data = [["Motor", "P (kW)", "In (A)", "Ia arranque (A)", "Seccion (mm2)", "Guardamotor (A)"]]
        for _, m in motores.iterrows():
            r = calcular_motor(m, metodo_instalacion)
            data.append([str(m.get("Motor", "")), str(m.get("Potencia (kW)", "")), r["In (A)"],
                         r["Ia arranque (A)"], r["Seccion (mm2)"], r["Guardamotor (A)"]])
        t = Table(data, repeatRows=1)
        t.setStyle(estilo_cabecera_tabla)
        story.append(t)
        story.append(PageBreak())

    story.append(Paragraph("ANEXO IV - Mediciones y presupuesto", styles["Heading1"]))
    filas = presupuesto["filas"]
    data = [["Capitulo", "Descripcion", "Ud", "Cantidad", "Precio (EUR)", "Importe (EUR)"]]
    for _, f in filas.iterrows():
        data.append([str(f["Capitulo"]), str(f["Descripcion"])[:45], str(f["Unidad"]),
                     round(float(f["Cantidad"]), 2), round(float(f["Precio unitario (EUR)"]), 2),
                     round(float(f["Importe (EUR)"]), 2)])
    t = Table(data, repeatRows=1)
    t.setStyle(estilo_cabecera_tabla)
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))
    resumen = [
        ["PEM (Presupuesto de Ejecucion Material)", f"{presupuesto['pem']:.2f} EUR"],
        ["Gastos generales", f"{presupuesto['gg']:.2f} EUR"],
        ["Beneficio industrial", f"{presupuesto['bi']:.2f} EUR"],
        ["Presupuesto de contrata (sin IVA)", f"{presupuesto['pca']:.2f} EUR"],
        ["IVA", f"{presupuesto['iva_importe']:.2f} EUR"],
        ["TOTAL PRESUPUESTO", f"{presupuesto['total']:.2f} EUR"],
    ]
    t2 = Table(resumen, colWidths=[10 * cm, 5 * cm])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4e2c3")),
                            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
    story.append(t2)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generar_esquema_unifilar_dxf(circuitos_bt, proyecto):
    try:
        import ezdxf
    except ImportError:
        return None

    doc = ezdxf.new("R2010")
    doc.layers.add("LINEAS", color=7)
    doc.layers.add("TEXTOS", color=3)
    doc.layers.add("SIMBOLOS", color=1)
    msp = doc.modelspace()

    ancho_cuadro = max(30, 8 * max(1, len(circuitos_bt)))
    x0, y0 = 0.0, 0.0

    msp.add_lwpolyline([(x0, y0), (x0 + ancho_cuadro, y0), (x0 + ancho_cuadro, y0 - 8), (x0, y0 - 8), (x0, y0)],
                        dxfattribs={"layer": "LINEAS"})
    msp.add_text(f"CUADRO GENERAL - {proyecto.get('nombre') or 'PROYECTO'}",
                 dxfattribs={"layer": "TEXTOS", "height": 1.4}).set_placement((x0 + 2, y0 - 4.5))
    msp.add_text("Acometida", dxfattribs={"layer": "TEXTOS", "height": 1.0}).set_placement((x0 + 2, y0 + 1.5))
    msp.add_line((x0 + ancho_cuadro / 2, y0 + 6), (x0 + ancho_cuadro / 2, y0), dxfattribs={"layer": "LINEAS"})

    espaciado = 8
    y_circuito = y0 - 8
    for i, (_, c) in enumerate(circuitos_bt.iterrows(), start=1):
        nombre = str(c.get("Circuito", "") or f"C{i}")
        x = x0 + 4 + (i - 1) * espaciado
        msp.add_line((x, y0 - 8), (x, y_circuito - 6), dxfattribs={"layer": "LINEAS"})
        msp.add_lwpolyline([(x - 0.8, y_circuito - 2), (x + 0.8, y_circuito - 2),
                             (x + 0.8, y_circuito - 4), (x - 0.8, y_circuito - 4), (x - 0.8, y_circuito - 2)],
                            dxfattribs={"layer": "SIMBOLOS"})
        msp.add_text(f"C{i}", dxfattribs={"layer": "TEXTOS", "height": 0.9}).set_placement((x - 0.6, y_circuito - 3.6))
        msp.add_text(nombre, dxfattribs={"layer": "TEXTOS", "height": 0.8}).set_placement((x - 3, y_circuito - 7))

    stream = io.StringIO()
    doc.write(stream)
    data = stream.getvalue().encode("utf-8")
    return io.BytesIO(data)

# =====================================================================================
# 5. INTERFAZ DE USUARIO
# =====================================================================================

inicializar_estado()

st.title("\u26a1 Proyectista Electrico - REBT")
st.caption("Predimensionado de instalaciones de baja tension, fotovoltaica de autoconsumo e industrial, "
           "conforme al REBT (RD 842/2002, ITC-BT) y RD 244/2019.")

with st.sidebar:
    st.header("\U0001F4CB Datos del proyecto")
    st.session_state.proyecto["nombre"] = st.text_input("Nombre del proyecto", st.session_state.proyecto.get("nombre", ""))
    st.session_state.proyecto["cliente"] = st.text_input("Cliente / Titular", st.session_state.proyecto.get("cliente", ""))
    st.session_state.proyecto["ubicacion"] = st.text_input("Emplazamiento", st.session_state.proyecto.get("ubicacion", ""))
    st.session_state.proyecto["tecnico"] = st.text_input("Tecnico redactor", st.session_state.proyecto.get("tecnico", ""))
    st.session_state.proyecto["fecha"] = st.text_input("Fecha", st.session_state.proyecto.get("fecha", str(date.today())))

    st.divider()
    st.subheader("\U0001F527 Modulos incluidos")
    st.session_state.tipos_activos["bt"] = st.checkbox("\U0001F3E0 Baja tension (REBT)", st.session_state.tipos_activos.get("bt", True))
    st.session_state.tipos_activos["fv"] = st.checkbox("\u2600\ufe0f Fotovoltaica de autoconsumo", st.session_state.tipos_activos.get("fv", False))
    st.session_state.tipos_activos["industrial"] = st.checkbox("\u2699\ufe0f Industrial / motores", st.session_state.tipos_activos.get("industrial", False))

    st.divider()
    st.subheader("\U0001F50C Metodo de instalacion")
    st.caption("ITC-BT-19 - Metodos de referencia A1, A2, B1, B2, C, D, E, F, G")
    st.session_state.metodo_instalacion = st.selectbox(
        "Metodo de referencia para el cableado", list(AMPACIDAD.keys()),
        index=list(AMPACIDAD.keys()).index(st.session_state.metodo_instalacion))

    st.divider()
    st.subheader("\U0001F4BE Guardar / cargar proyecto")
    proyecto_json = json.dumps(estado_a_dict(), ensure_ascii=False, indent=2, default=str)
    st.download_button("Descargar proyecto (.json)", data=proyecto_json,
                       file_name=(st.session_state.proyecto.get("nombre") or "proyecto").replace(" ", "_") + ".json",
                       mime="application/json")
    archivo_proyecto = st.file_uploader("Cargar proyecto (.json)", type=["json"], key="uploader_json")
    if archivo_proyecto is not None:
        try:
            cargar_estado_desde_dict(json.load(archivo_proyecto))
            st.success("Proyecto cargado correctamente.")
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")

    st.markdown('<div class="bloque-nota">\u26a0\ufe0f Los valores de intensidades admisibles y factores de '
                "correccion son orientativos. Verifica siempre contra las tablas oficiales del REBT/ITC-BT "
                "vigentes antes de emitir documentacion oficial.</div>", unsafe_allow_html=True)

tabs = st.tabs(["\u26a1 Baja tension", "\u2600\ufe0f Fotovoltaica", "\u2699\ufe0f Industrial", "\U0001F4CF Mediciones",
                "\U0001F4B0 Presupuesto", "\U0001F4C4 Memoria", "\U0001F4E4 Importar / Exportar"])

with tabs[0]:
    st.subheader("Circuitos de baja tension (ITC-BT-19 / ITC-BT-25)")
    st.caption("Anhade, edita o elimina filas directamente en la tabla. Los resultados se calculan automaticamente.")

    circuitos_editados = st.data_editor(
        st.session_state.circuitos_bt, num_rows="dynamic", use_container_width=True, key="editor_bt",
        column_config={
            "Fases": st.column_config.SelectboxColumn(options=["Monofasico", "Trifasico"], default="Monofasico"),
            "Tipo de receptor": st.column_config.SelectboxColumn(options=["Alumbrado", "Fuerza / tomas", "Climatizacion", "Mixto"], default="Alumbrado"),
            "Temp. ambiente (C)": st.column_config.SelectboxColumn(options=list(FACTOR_TEMPERATURA.keys()), default=40),
            "Circuitos agrupados": st.column_config.SelectboxColumn(options=list(FACTOR_AGRUPAMIENTO.keys()), default=1),
            "Tipo de linea (cdt)": st.column_config.SelectboxColumn(options=list(CDT_MAXIMA.keys()), default="Instalacion interior - Otros usos (fuerza, tomas...)"),
        },
    )
    st.session_state.circuitos_bt = circuitos_editados

    if not circuitos_editados.empty:
        resultados = circuitos_editados.apply(lambda r: calcular_circuito_bt(r, st.session_state.metodo_instalacion), axis=1)
        tabla_resultado = pd.concat([circuitos_editados[["Circuito"]], resultados], axis=1)

        n_total = len(tabla_resultado)
        n_ok = int((tabla_resultado["Cumple"] == "Cumple").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Circuitos totales", n_total)
        c2.metric("Cumplen normativa", n_ok)
        c3.metric("A revisar", n_total - n_ok)

        st.dataframe(tabla_resultado, use_container_width=True)

        try:
            import plotly.express as px
            conteo = tabla_resultado["Cumple"].value_counts().reset_index()
            conteo.columns = ["Estado", "Cantidad"]
            fig = px.pie(conteo, names="Estado", values="Cantidad", hole=0.5,
                        color="Estado", color_discrete_map={"Cumple": "#2f6f4f", "Revisar": "#a8402f"},
                        title="Cumplimiento normativo de los circuitos")
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
    else:
        st.info("Todavia no hay circuitos. Anhade el primero desde la tabla superior.")

with tabs[1]:
    st.subheader("Instalacion fotovoltaica de autoconsumo (RD 244/2019, ITC-BT-40)")
    fv = st.session_state.fv_datos
    c1, c2, c3, c4 = st.columns(4)
    fv["potencia_pico"] = c1.text_input("Potencia pico (kWp)", str(fv.get("potencia_pico", "")))
    fv["num_paneles"] = c2.text_input("Numero de paneles", str(fv.get("num_paneles", "")))
    fv["potencia_panel"] = c3.text_input("Potencia por panel (Wp)", str(fv.get("potencia_panel", "")))
    fv["num_strings"] = c4.number_input("Numero de strings en paralelo", min_value=1, value=int(fv.get("num_strings", 1) or 1))

    c1, c2, c3, c4 = st.columns(4)
    fv["voc"] = c1.text_input("Voc (V)", str(fv.get("voc", "")))
    fv["isc"] = c2.text_input("Isc (A)", str(fv.get("isc", "")))
    fv["vmpp"] = c3.text_input("Vmpp (V)", str(fv.get("vmpp", "")))
    fv["impp"] = c4.text_input("Impp (A)", str(fv.get("impp", "")))

    c1, c2, c3, c4 = st.columns(4)
    fv["dist_string_inversor"] = c1.number_input("Distancia strings -> inversor (m)", value=float(fv.get("dist_string_inversor", 15.0) or 0))
    fv["potencia_inversor"] = c2.text_input("Potencia inversor (W)", str(fv.get("potencia_inversor", "")))
    fv["tension_ac"] = c3.number_input("Tension AC (V)", value=float(fv.get("tension_ac", 400.0) or 0))
    fv["fases_ac"] = c4.selectbox("Fases AC", ["Monofasico", "Trifasico"], index=["Monofasico", "Trifasico"].index(fv.get("fases_ac", "Trifasico")))
    fv["dist_inversor_cuadro"] = st.number_input("Distancia inversor -> cuadro AC (m)", value=float(fv.get("dist_inversor_cuadro", 5.0) or 0))
    st.session_state.fv_datos = fv

    if float(fv.get("num_paneles", 0) or 0) > 0 or float(fv.get("impp", 0) or 0) > 0:
        r = calcular_fv(fv, st.session_state.metodo_instalacion)
        st.markdown("**Tramo CC (paneles -> inversor)**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("I diseno CC (1.25 x Isc)", f"{r['idc_diseno']:.2f} A")
        c2.metric("Seccion CC", f"{r['seccion_dc']} mm2")
        c3.metric("c.d.t. CC", f"{r['cdt_dc']:.2f} %")
        c4.metric("Requiere fusibles", "Si" if r["requiere_fusibles_dc"] else "No")

        st.markdown("**Tramo CA (inversor -> cuadro AC)**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("I AC", f"{r['iac']:.2f} A")
        c2.metric("Seccion AC", f"{r['seccion_ac']} mm2")
        c3.metric("c.d.t. AC", f"{r['cdt_ac']:.2f} %")
        c4.metric("Proteccion AC", f"{r['proteccion_ac']} A")

    st.markdown('<div class="bloque-nota">\u2139\ufe0f Recuerda: interruptor-seccionador CC junto al inversor, '
                "proteccion contra sobretensiones, diferencial adecuado al tipo de inversor (tipo A o "
                "superinmunizado tipo B si el fabricante lo exige) y equipo de medida bidireccional segun "
                "RD 244/2019.</div>", unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Motores y circuitos industriales (ITC-BT-47)")
    motores_editados = st.data_editor(
        st.session_state.motores, num_rows="dynamic", use_container_width=True, key="editor_motores",
        column_config={"Tipo de arranque": st.column_config.SelectboxColumn(options=list(FACTORES_ARRANQUE_MOTOR.keys()), default="Directo")},
    )
    st.session_state.motores = motores_editados

    if not motores_editados.empty:
        resultados_m = motores_editados.apply(lambda r: calcular_motor(r, st.session_state.metodo_instalacion), axis=1)
        tabla_m = pd.concat([motores_editados[["Motor"]], resultados_m], axis=1)
        st.dataframe(tabla_m, use_container_width=True)
    else:
        st.info("Anhade un motor para calcular In, Ia de arranque, seccion y protecciones.")

with tabs[3]:
    st.subheader("Mediciones")
    mediciones_auto = generar_mediciones_auto(st.session_state.circuitos_bt, st.session_state.fv_datos,
                                              st.session_state.motores, st.session_state.tipos_activos,
                                              st.session_state.metodo_instalacion)
    if not mediciones_auto.empty:
        st.markdown("**Generadas automaticamente a partir de los calculos**")
        st.dataframe(mediciones_auto[["Capitulo", "Descripcion", "Unidad", "Cantidad"]], use_container_width=True)
    else:
        st.info("Anhade circuitos en las pestanhas de calculo para generar mediciones automaticamente.")

    st.markdown("**Partidas manuales**")
    st.session_state.mediciones_manual = st.data_editor(
        st.session_state.mediciones_manual, num_rows="dynamic", use_container_width=True, key="editor_mediciones_manual")

with tabs[4]:
    st.subheader("Presupuesto (PEM + Gastos generales + Beneficio industrial + IVA)")
    presupuesto = calcular_presupuesto(mediciones_auto, st.session_state.mediciones_manual, st.session_state.precios,
                                        st.session_state.gastos_generales, st.session_state.beneficio_industrial,
                                        st.session_state.iva)

    if not presupuesto["por_capitulo"].empty:
        try:
            import plotly.express as px
            datos_grafico = presupuesto["por_capitulo"].reset_index()
            datos_grafico.columns = ["Capitulo", "Importe (EUR)"]
            fig = px.bar(datos_grafico, x="Capitulo", y="Importe (EUR)", color="Capitulo", text_auto=".2f",
                        title="Distribucion del presupuesto por capitulo",
                        color_discrete_sequence=["#10263f", "#c8790f", "#2f6f4f", "#45688a"])
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for capitulo, importe in presupuesto["por_capitulo"].items():
                st.write(f"**{capitulo}**: {importe:.2f} EUR")

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("PEM (Presupuesto de Ejecucion Material)", f"{presupuesto['pem']:.2f} EUR")
    st.session_state.gastos_generales = c1.number_input("Gastos generales (%)", value=float(st.session_state.gastos_generales))
    st.session_state.beneficio_industrial = c1.number_input("Beneficio industrial (%)", value=float(st.session_state.beneficio_industrial))
    st.session_state.iva = c2.number_input("IVA (%)", value=float(st.session_state.iva))
    c2.metric("Presupuesto de contrata (sin IVA)", f"{presupuesto['pca']:.2f} EUR")
    st.metric("TOTAL PRESUPUESTO", f"{presupuesto['total']:.2f} EUR")

    with st.expander(f"Editar precios unitarios ({len(st.session_state.precios)})"):
        cols = st.columns(3)
        claves = list(st.session_state.precios.keys())
        for i, k in enumerate(claves):
            st.session_state.precios[k] = cols[i % 3].number_input(k.replace("_", " "), value=float(st.session_state.precios[k]), key=f"precio_{k}")

with tabs[5]:
    st.subheader("Memoria tecnica")
    memoria = st.session_state.memoria
    memoria["objeto"] = st.text_area("Objeto (vacio para usar el texto por defecto)", memoria.get("objeto", ""))
    memoria["normativa"] = st.text_area("Normativa (opcional)", memoria.get("normativa", ""))
    memoria["descripcion"] = st.text_area("Descripcion general (opcional)", memoria.get("descripcion", ""))
    st.session_state.memoria = memoria

    texto_memoria = generar_memoria_texto(st.session_state.proyecto, st.session_state.circuitos_bt,
                                          st.session_state.fv_datos, st.session_state.motores, memoria,
                                          st.session_state.tipos_activos, st.session_state.metodo_instalacion)
    st.text_area("Vista previa", texto_memoria, height=350)

with tabs[6]:
    st.subheader("\U0001F4E5 Importar circuitos, motores o partidas desde CSV/Excel")
    st.caption("Descarga la plantilla, rellenala y vuelve a subirla para cargar datos en bloque.")

    colp1, colp2, colp3 = st.columns(3)
    colp1.download_button("Plantilla circuitos BT (.csv)", df_vacio(COLUMNAS_BT).to_csv(index=False), "plantilla_circuitos_bt.csv", "text/csv")
    colp2.download_button("Plantilla motores (.csv)", df_vacio(COLUMNAS_MOTORES).to_csv(index=False), "plantilla_motores.csv", "text/csv")
    colp3.download_button("Plantilla mediciones (.csv)", df_vacio(COLUMNAS_MEDICION_MANUAL).to_csv(index=False), "plantilla_mediciones.csv", "text/csv")

    tipo_importacion = st.selectbox("Que quieres importar", ["Circuitos de baja tension", "Motores", "Partidas de mediciones manuales"])
    archivo = st.file_uploader("Selecciona un archivo .csv o .xlsx", type=["csv", "xlsx"], key="uploader_datos")
    modo = st.radio("Modo de carga", ["Anhadir a los datos actuales", "Reemplazar los datos actuales"], horizontal=True)

    if archivo is not None:
        try:
            nuevo_df = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)
            if tipo_importacion == "Circuitos de baja tension":
                destino, columnas = "circuitos_bt", COLUMNAS_BT
            elif tipo_importacion == "Motores":
                destino, columnas = "motores", COLUMNAS_MOTORES
            else:
                destino, columnas = "mediciones_manual", COLUMNAS_MEDICION_MANUAL

            nuevo_df = nuevo_df.reindex(columns=columnas)
            if modo == "Reemplazar los datos actuales":
                st.session_state[destino] = nuevo_df
            else:
                st.session_state[destino] = pd.concat([st.session_state[destino], nuevo_df], ignore_index=True)
            st.success(f"Se han importado {len(nuevo_df)} filas en '{tipo_importacion}'.")
        except Exception as e:
            st.error(f"No se pudo importar el archivo: {e}")

    st.divider()
    st.subheader("\U0001F4E4 Exportar resultados")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Excel** - mediciones, presupuesto y calculo BT")
        excel_buffer = exportar_excel(presupuesto, st.session_state.circuitos_bt, st.session_state.metodo_instalacion)
        st.download_button("\U0001F4CA Descargar Excel (.xlsx)", data=excel_buffer,
                           file_name=(st.session_state.proyecto.get("nombre") or "proyecto").replace(" ", "_") + ".xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("**Esquema unifilar** - cuadro general y circuitos")
        st.caption("Se genera en formato DXF (estandar CAD abierto). AutoCAD, BricsCAD y similares lo abren "
                   "directamente y permiten guardarlo como .dwg con 'Guardar como'.")
        dxf_buffer = generar_esquema_unifilar_dxf(st.session_state.circuitos_bt, st.session_state.proyecto)
        if dxf_buffer is not None:
            st.download_button("\U0001F4D0 Descargar esquema unifilar (.dxf)", data=dxf_buffer,
                               file_name=(st.session_state.proyecto.get("nombre") or "esquema").replace(" ", "_") + "_unifilar.dxf",
                               mime="application/dxf")
        else:
            st.warning("Instala la libreria 'ezdxf' (incluida en requirements.txt) para generar el esquema unifilar.")

    with col2:
        st.markdown("**Memoria tecnica en PDF** - portada + capitulos + anexos por capitulo")
        pdf_buffer = exportar_memoria_pdf(estado_a_dict(), texto_memoria, st.session_state.circuitos_bt,
                                          st.session_state.fv_datos, st.session_state.motores, presupuesto,
                                          st.session_state.metodo_instalacion)
        if pdf_buffer is not None:
            st.download_button("\U0001F4D5 Descargar memoria (.pdf)", data=pdf_buffer,
                               file_name=(st.session_state.proyecto.get("nombre") or "memoria").replace(" ", "_") + ".pdf",
                               mime="application/pdf")
        else:
            st.warning("Instala la libreria 'reportlab' (incluida en requirements.txt) para generar el PDF.")

        st.markdown("**Memoria tecnica en Word** - editable")
        word_buffer = exportar_memoria_word(texto_memoria, st.session_state.proyecto)
        if word_buffer is not None:
            st.download_button("\U0001F4C4 Descargar memoria (.docx)", data=word_buffer,
                               file_name=(st.session_state.proyecto.get("nombre") or "memoria").replace(" ", "_") + ".docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.download_button("Descargar memoria (texto .txt)", data=texto_memoria,
                               file_name=(st.session_state.proyecto.get("nombre") or "memoria").replace(" ", "_") + ".txt",
                               mime="text/plain")
