"""
================================================================================
 CALCULADORA DE SECCIONES DE CABLE — REBT
================================================================================
Herramienta de apoyo al cálculo de la sección mínima de conductores en
instalaciones de baja tensión, conforme al Reglamento Electrotécnico para
Baja Tensión (REBT, RD 842/2002) y sus Instrucciones Técnicas Complementarias:

    ITC-BT-14   Línea General de Alimentación (LGA)
    ITC-BT-15   Derivación Individual (DI)
    ITC-BT-18   Puestas a tierra (conductor de protección)
    ITC-BT-19   Prescripciones generales de instalaciones interiores
                (intensidades admisibles y caída de tensión) — Tabla 1
    ITC-BT-07   Redes subterráneas (instalación enterrada, resistividad terreno)
    ITC-BT-47   Instalación de receptores. Motores.

Criterios de dimensionado aplicados (art. 19.2 ITC-BT-19):
    1) Criterio térmico              Ib ≤ In ≤ Iz
    2) Criterio de caída de tensión  ΔU% ≤ ΔU%max según tramo
    3) Criterio térmico de cortocircuito (verificación opcional, S ≥ (Icc·√t)/k)

Fuentes numéricas: Guía-BT-19 (Ministerio de Industria, Turismo y Comercio,
Ed. feb-09 Rev.2) Tablas A, C, D, E, F; ITC-BT-14, ITC-BT-15, ITC-BT-47
(textos oficiales); Libro Blanco de la Instalación (Prysmian) para las
constantes k de cortocircuito. Ver pestaña "Metodología" dentro de la app
para el detalle de cada tabla y sus limitaciones conocidas.

⚠️  Herramienta de apoyo al diseño, no un sustituto del criterio de un
    técnico competente. Antes de emitir un proyecto o memoria firmada,
    contrasta los valores críticos contra la edición vigente de la
    Guía-BT-19 y la norma UNE-HD 60364-5-52.

Autor: Younes — IDEA TSG
================================================================================
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import streamlit as st

# ==============================================================================
# 1. CONSTANTES Y TABLAS NORMATIVAS
# ==============================================================================

# Secciones comerciales normalizadas (mm²) contempladas por esta herramienta.
# Se limita a 300 mm² porque es el rango en el que la Tabla 1 de la
# ITC-BT-19 / Guía-BT-19 es completamente consistente; por encima, la
# práctica habitual (y lo que hace esta app) es recurrir a conductores
# en paralelo en lugar de secciones unipolares extremas.
SECCIONES_NORMALIZADAS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70,
                          95, 120, 150, 185, 240, 300]

# Conductividad a 20°C (m/Ω·mm²) y coeficiente de variación de la
# resistencia con la temperatura (1/°C), para corregir la conductividad
# a la temperatura de servicio real del aislamiento (criterio recomendado
# por la Guía-BT-19 para el cálculo de caída de tensión, más conservador
# que usar la conductividad a 20°C).
CONDUCTIVIDAD_20C = {"Cobre": 56.0, "Aluminio": 35.0}
COEF_TEMP_RESIST = {"Cobre": 0.00393, "Aluminio": 0.00403}
TEMP_SERVICIO = {"PVC": 70.0, "XLPE/EPR": 90.0}
TEMP_REF_TABLA_AIRE = 40.0     # Tabla A Guía-BT-19: intensidades admisibles al aire 40°C
TEMP_REF_TABLA_TERRENO = 25.0  # Tabla D Guía-BT-19: cables enterrados, terreno 25°C
RESISTIVIDAD_REF_TERRENO = 1.5  # K·m/W, condición de cálculo de la Tabla D

# Reactancia lineal aproximada de cables de BT (Ω/km), valor orientativo
# habitual para conductores en conducto o bandeja, usado para no
# despreciar por completo el término reactivo en la caída de tensión.
REACTANCIA_LINEAL_DEFECTO = 0.08

# Constantes k para la verificación térmica de cortocircuito (S = Icc·√t / k),
# fórmula de IEC 60364-5-54 recogida también en ITC-BT-19 / ITC-BT-07.
# Fuente: Libro Blanco de la Instalación (Prysmian), tablas 16/17 ITC-BT-07.
K_CORTOCIRCUITO = {
    ("Cobre", "PVC"): 115,          # 103 si S > 300 mm²
    ("Cobre", "XLPE/EPR"): 143,
    ("Aluminio", "PVC"): 76,        # 68 si S > 300 mm²
    ("Aluminio", "XLPE/EPR"): 94,
}

# Caídas de tensión máximas admisibles (%) según el tramo de la instalación.
# Fuentes: ITC-BT-14 (LGA), ITC-BT-15 (DI), ITC-BT-19 apdo. 2.2.2 (interior),
# ITC-BT-19 (transformador propio), ITC-BT-40 (generación / FV).
CAIDA_TENSION_MAX = {
    "LGA — centralización única de contadores": 0.5,
    "LGA — centralizaciones parciales": 1.0,
    "Derivación Individual — contadores totalmente centralizados": 1.0,
    "Derivación Individual — contadores en más de un lugar": 0.5,
    "Derivación Individual — usuario único (sin LGA)": 1.5,
    "Instalación interior — Alumbrado": 3.0,
    "Instalación interior — Otros usos / fuerza": 5.0,
    "Circuito de motor": 5.0,
    "Alimentación con transformador propio — Alumbrado": 4.5,
    "Alimentación con transformador propio — Otros usos": 6.5,
    "Instalación generadora / FV (ITC-BT-40)": 1.5,
    "Personalizado": None,
}

# Cadenas canónicas para sistema y método de instalación: se usan tanto en la
# UI (opciones de los selectbox) como en la lógica de cálculo, para que no
# puedan desincronizarse entre sí.
SISTEMA_MONO = "Monofásico (230 V)"
SISTEMA_TRI = "Trifásico (400 V)"
METODO_B1 = "B1/B2 — Bajo tubo (empotrado o superficie)"
METODO_C = "C — Bandeja no perforada / directo sobre superficie"
METODO_F = "F — Bandeja perforada, unipolares muy separados (S≥25 mm², XLPE)"
METODO_D = "D — Enterrado bajo tubo (XLPE)"
METODOS_DISPONIBLES = [METODO_B1, METODO_C, METODO_F, METODO_D]

# ------------------------------------------------------------------------------
# Tabla A — Intensidades admisibles (A), cables de COBRE, NO enterrados,
# temperatura ambiente de referencia 40°C. Fuente: Guía-BT-19, Tabla A
# (columnas 5-8 = método B1/B2; columnas 9-12 = método C; columna 13 = F).
# Métodos A1/A2 (empotrado en pared térmicamente aislante) se han excluido
# por ser poco habituales tanto en vivienda/terciario como en industria.
# ------------------------------------------------------------------------------
TABLA_A_COBRE = {
    # sección: {"B1": {"3xPVC","2xPVC","3xXLPE","2xXLPE"}, "C": {...}, "F_3xXLPE": valor|None}
    1.5:  {"B1": (13.5, 15.0, 16.0, 16.5), "C": (19.0, 20.0, 21.0, 24.0), "F": None},
    2.5:  {"B1": (18.5, 21.0, 22.0, 23.0), "C": (26.0, 26.5, 29.0, 33.0), "F": None},
    4:    {"B1": (24.0, 27.0, 30.0, 31.0), "C": (34.0, 36.0, 38.0, 45.0), "F": None},
    6:    {"B1": (32.0, 36.0, 37.0, 40.0), "C": (44.0, 46.0, 49.0, 57.0), "F": None},
    10:   {"B1": (44.0, 50.0, 52.0, 54.0), "C": (60.0, 65.0, 68.0, 76.0), "F": None},
    16:   {"B1": (59.0, 66.0, 70.0, 73.0), "C": (81.0, 87.0, 91.0, 105.0), "F": None},
    25:   {"B1": (77.0, 84.0, 88.0, 95.0), "C": (103.0, 110.0, 116.0, 123.0), "F": 140.0},
    35:   {"B1": (96.0, 104.0, 110.0, 119.0), "C": (127.0, 137.0, 144.0, 154.0), "F": 174.0},
    50:   {"B1": (117.0, 125.0, 133.0, 145.0), "C": (155.0, 167.0, 175.0, 188.0), "F": 210.0},
    70:   {"B1": (149.0, 160.0, 171.0, 185.0), "C": (199.0, 214.0, 224.0, 244.0), "F": 269.0},
    95:   {"B1": (180.0, 194.0, 207.0, 224.0), "C": (241.0, 259.0, 271.0, 296.0), "F": 327.0},
    120:  {"B1": (208.0, 225.0, 240.0, 260.0), "C": (280.0, 301.0, 314.0, 348.0), "F": 380.0},
    150:  {"B1": (236.0, 260.0, 278.0, 299.0), "C": (322.0, 343.0, 363.0, 404.0), "F": 438.0},
    185:  {"B1": (268.0, 297.0, 317.0, 341.0), "C": (368.0, 391.0, 415.0, 464.0), "F": 500.0},
    240:  {"B1": (315.0, 350.0, 374.0, 401.0), "C": (435.0, 468.0, 490.0, 552.0), "F": 590.0},
    300:  {"B1": (361.0, 401.0, 430.0, 461.0), "C": (500.0, 538.0, 563.0, 638.0), "F": 678.0},
}
# Orden de la tupla (3xPVC, 2xPVC, 3xXLPE, 2xXLPE) para B1 y C.
IDX_3PVC, IDX_2PVC, IDX_3XLPE, IDX_2XLPE = 0, 1, 2, 3

# Ratio Al/Cu orientativo para instalación NO enterrada (no publicado de forma
# explícita en la Tabla A de la Guía-BT-19, que remite a la norma UNE para
# aluminio). Ratio ampliamente citado en bibliografía técnica española.
RATIO_ALUMINIO_NO_ENTERRADO = 0.78

# ------------------------------------------------------------------------------
# Tabla D — Intensidades admisibles (A), cables ENTERRADOS bajo tubo,
# aislamiento XLPE 0,6/1 kV. Condiciones: resistividad térmica 1,5 K·m/W,
# terreno a 25°C, profundidad 0,70 m. Fuente: Guía-BT-19, Tabla D.
# En la práctica actual, el cable enterrado es casi siempre XLPE/EPR.
# ------------------------------------------------------------------------------
TABLA_D_ENTERRADO_XLPE = {
    # sección: (3x_Cu, 3x_Al, 2x_Cu, 2x_Al)
    1.5:  (23.0, None, 27.0, None),
    2.5:  (30.0, 23.0, 36.0, 27.0),
    4:    (39.0, 30.0, 46.0, 36.0),
    6:    (48.0, 37.0, 58.0, 44.0),
    10:   (64.0, 49.0, 77.0, 58.0),
    16:   (82.0, 62.0, 100.0, 77.0),
    25:   (105.0, 82.0, 130.0, 98.0),
    35:   (130.0, 98.0, 155.0, 120.0),
    50:   (155.0, 115.0, 183.0, 139.0),
    70:   (190.0, 145.0, 225.0, 170.0),
    95:   (225.0, 175.0, 265.0, 205.0),
    120:  (260.0, 200.0, 305.0, 230.0),
    150:  (300.0, 230.0, 340.0, 265.0),
    185:  (335.0, 260.0, 385.0, 295.0),
    240:  (400.0, 305.0, 440.0, 340.0),
    300:  (455.0, 350.0, 500.0, 385.0),
}

# Tabla C (Guía-BT-19) — Resistividad térmica del terreno.
RESISTIVIDAD_TERRENO = {
    "Inundado (0,40 K·m/W)": 0.40,
    "Muy húmedo (0,50 K·m/W)": 0.50,
    "Húmedo (0,70 K·m/W)": 0.70,
    "Poco húmedo (0,85 K·m/W)": 0.85,
    "Seco (1,00 K·m/W)": 1.00,
    "Arcilloso muy seco (1,20 K·m/W)": 1.20,
    "Arenoso muy seco — referencia Tabla D (1,50 K·m/W)": 1.50,
    "Piedra arenisca (2,00 K·m/W)": 2.00,
    "Piedra caliza (2,50 K·m/W)": 2.50,
    "Piedra granítica (3,00 K·m/W)": 3.00,
}
# Factor de corrección orientativo por resistividad térmica del terreno,
# relativo a la referencia de la Tabla D (1,5 K·m/W = factor 1,0). No
# publicado como tabla cerrada en la Guía-BT-19 consultada; valores
# orientativos de uso extendido — verificar en UNE 20460-5-523 para
# proyectos críticos.
FACTOR_RESISTIVIDAD_TERRENO = {
    0.40: 1.25, 0.50: 1.21, 0.70: 1.18, 0.85: 1.14, 1.00: 1.10,
    1.20: 1.05, 1.50: 1.00, 2.00: 0.93, 2.50: 0.89, 3.00: 0.85,
}

# Tabla E (Guía-BT-19) — Factores de reducción por agrupamiento de circuitos.
# disposicion -> {nº circuitos: factor}; se usa el primer breakpoint >= n.
TABLA_E_AGRUPAMIENTO = {
    "Empotrados o embutidos": {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.70, 6: 0.55, 9: 0.50, 12: 0.45, 16: 0.40, 20: 0.40},
    "Capa única sobre pared/suelo/bandeja no perforada": {1: 1.00, 2: 0.85, 3: 0.80, 4: 0.75, 6: 0.70, 9: 0.70},
    "Capa única fijada bajo techo": {1: 0.95, 2: 0.80, 3: 0.70, 4: 0.70, 6: 0.65, 9: 0.60},
    "Capa única en bandeja perforada (horiz. o vert.)": {1: 1.00, 2: 0.90, 3: 0.80, 4: 0.75, 6: 0.75, 9: 0.70},
    "Capa única en bandeja de escalera / abrazaderas": {1: 1.00, 2: 0.85, 3: 0.80, 4: 0.80, 6: 0.80, 9: 0.80},
}

# Tabla F (Guía-BT-19) — Factor adicional por nº de capas de agrupamiento.
TABLA_F_CAPAS = {1: 1.00, 2: 0.80, 3: 0.73, 4: 0.70, 5: 0.70, 6: 0.68, 7: 0.68, 8: 0.68, 9: 0.66}

# Tabla H (Guía-BT-19) — Agrupamiento de tubos enterrados (un cable/tubo).
TABLA_H_TUBOS_ENTERRADOS = {
    # nº cables: {distancia_m: factor}
    2: {0.0: 0.85, 0.25: 0.90, 0.50: 0.95, 1.0: 0.95},
    3: {0.0: 0.75, 0.25: 0.85, 0.50: 0.90, 1.0: 0.95},
    4: {0.0: 0.70, 0.25: 0.80, 0.50: 0.85, 1.0: 0.90},
    5: {0.0: 0.65, 0.25: 0.80, 0.50: 0.85, 1.0: 0.90},
    6: {0.0: 0.60, 0.25: 0.80, 0.50: 0.80, 1.0: 0.90},
}

MINIMO_ABSOLUTO_MM2 = 1.5
MINIMO_ALUMINIO_MM2 = 16.0   # ITC-BT-07: sección mínima de aluminio en instalaciones fijas
MINIMO_LGA_COBRE_MM2 = 10.0  # ITC-BT-14
MINIMO_LGA_ALUMINIO_MM2 = 16.0


# ==============================================================================
# 2. FUNCIONES DE CALCULO (logica pura, sin dependencias de Streamlit)
# ==============================================================================

@dataclass
class ResultadoCalculo:
    ib: float
    ib_calculo: float
    factor_correccion_total: float
    factor_temperatura: float
    factor_agrupamiento: float
    factor_resistividad: float
    kappa_usado: float
    iz_requerida: float
    seccion_termica: Optional[float]
    iz_tabla_termica: Optional[float]
    seccion_caida_tension: Optional[float]
    delta_u_voltios: float = 0.0
    delta_u_porcentaje: float = 0.0
    delta_u_max_porcentaje: float = 0.0
    seccion_final: Optional[float] = None
    seccion_neutro: Optional[float] = None
    seccion_proteccion: Optional[float] = None
    necesita_paralelo: bool = False
    n_conductores_paralelo: int = 1
    cumple_cortocircuito: Optional[bool] = None
    seccion_min_cortocircuito: Optional[float] = None
    avisos: list = field(default_factory=list)


def calcular_intensidad_empleo(sistema: str, potencia_w: float, tension: float,
                                cos_phi: float) -> float:
    """Corriente de empleo Ib a partir de la potencia activa (W)."""
    cos_phi = max(cos_phi, 0.01)
    if sistema == SISTEMA_MONO:
        return potencia_w / (tension * cos_phi)
    return potencia_w / (math.sqrt(3) * tension * cos_phi)


def factor_motor_unico(in_motor: float) -> float:
    """ITC-BT-47 3.1: un solo motor -> 125% de la intensidad a plena carga."""
    return 1.25 * in_motor


def factor_varios_motores(corrientes_motores: list) -> float:
    """ITC-BT-47 3.2: 125% del motor de mayor potencia + 100% del resto."""
    if not corrientes_motores:
        return 0.0
    ordenados = sorted(corrientes_motores, reverse=True)
    return 1.25 * ordenados[0] + sum(ordenados[1:])


def factor_correccion_temperatura(aislamiento: str, temp_ambiente: float,
                                   enterrado: bool) -> float:
    """
    Factor de correccion por temperatura ambiente distinta de la de
    referencia de la tabla utilizada (40C aire / 25C terreno).
    factor = sqrt((Tmax - Ta) / (Tmax - Tref))
    """
    tmax = TEMP_SERVICIO[aislamiento]
    tref = TEMP_REF_TABLA_TERRENO if enterrado else TEMP_REF_TABLA_AIRE
    if temp_ambiente >= tmax:
        return 0.01
    return math.sqrt((tmax - temp_ambiente) / (tmax - tref))


def factor_correccion_agrupamiento(disposicion: str, n_circuitos: int) -> float:
    """Tabla E Guia-BT-19: factor por numero de circuitos agrupados."""
    tabla = TABLA_E_AGRUPAMIENTO[disposicion]
    breakpoints = sorted(tabla.keys())
    factor = tabla[breakpoints[-1]]
    for bp in breakpoints:
        if n_circuitos <= bp:
            factor = tabla[bp]
            break
    return factor


def factor_correccion_capas(n_capas: int) -> float:
    """Tabla F Guia-BT-19: factor adicional por numero de capas."""
    if n_capas <= 1:
        return 1.0
    capas_disponibles = sorted(TABLA_F_CAPAS.keys())
    factor = TABLA_F_CAPAS[capas_disponibles[-1]]
    for c in capas_disponibles:
        if n_capas <= c:
            factor = TABLA_F_CAPAS[c]
            break
    return factor


def factor_correccion_resistividad(resistividad: float) -> float:
    """Factor orientativo por resistividad termica del terreno (ver Tabla C)."""
    claves = sorted(FACTOR_RESISTIVIDAD_TERRENO.keys())
    mas_cercana = min(claves, key=lambda k: abs(k - resistividad))
    return FACTOR_RESISTIVIDAD_TERRENO[mas_cercana]


def iz_tabla(seccion: float, metodo: str, aislamiento: str, conductor: str,
             n_cargados: int):
    """
    Intensidad admisible tabulada (A) antes de aplicar factores de correccion,
    para una seccion, metodo de instalacion, aislamiento, conductor y numero
    de conductores cargados (2=monofasico, 3=trifasico).
    """
    if metodo == METODO_D:
        fila = TABLA_D_ENTERRADO_XLPE.get(seccion)
        if fila is None:
            return None
        cu3, al3, cu2, al2 = fila
        if conductor == "Cobre":
            valor = cu3 if n_cargados == 3 else cu2
        else:
            valor = al3 if n_cargados == 3 else al2
        return valor

    fila = TABLA_A_COBRE.get(seccion)
    if fila is None:
        return None

    if metodo == METODO_F:
        valor_cu = fila["F"]
        if valor_cu is None:
            return None
    else:
        clave = "B1" if metodo == METODO_B1 else "C"
        tupla = fila[clave]
        if aislamiento == "PVC":
            idx = IDX_3PVC if n_cargados == 3 else IDX_2PVC
        else:
            idx = IDX_3XLPE if n_cargados == 3 else IDX_2XLPE
        valor_cu = tupla[idx]

    if conductor == "Cobre":
        return valor_cu
    return round(valor_cu * RATIO_ALUMINIO_NO_ENTERRADO, 1)


def seccion_por_criterio_termico(ib_calculo: float, metodo: str, aislamiento: str,
                                  conductor: str, n_cargados: int,
                                  factor_correccion: float):
    """
    Busca la menor seccion normalizada cuya Iz (tabla x factor de correccion)
    sea >= Ib de calculo. Si ninguna seccion normalizada basta, evalua si
    hacen falta conductores en paralelo.
    """
    minimo = MINIMO_ALUMINIO_MM2 if conductor == "Aluminio" else MINIMO_ABSOLUTO_MM2
    for s in SECCIONES_NORMALIZADAS:
        if s < minimo:
            continue
        base = iz_tabla(s, metodo, aislamiento, conductor, n_cargados)
        if base is None:
            continue
        iz_real = base * factor_correccion
        if iz_real >= ib_calculo:
            return s, iz_real, False, 1

    s_max = max(SECCIONES_NORMALIZADAS)
    base_max = iz_tabla(s_max, metodo, aislamiento, conductor, n_cargados)
    if base_max is None:
        return None, None, False, 1
    iz_max = base_max * factor_correccion
    n_paralelo = max(2, math.ceil(ib_calculo / iz_max))
    return s_max, iz_max, True, n_paralelo


def kappa_servicio(conductor: str, aislamiento: str, usar_20c: bool = False) -> float:
    """Conductividad (m/ohm*mm2) a la temperatura de servicio del aislamiento."""
    k20 = CONDUCTIVIDAD_20C[conductor]
    if usar_20c:
        return k20
    alpha = COEF_TEMP_RESIST[conductor]
    t_servicio = TEMP_SERVICIO[aislamiento]
    return k20 / (1 + alpha * (t_servicio - 20))


def caida_tension_voltios(sistema: str, ib: float, longitud: float, seccion: float,
                           cos_phi: float, kappa: float,
                           reactancia_ohm_km: float = REACTANCIA_LINEAL_DEFECTO) -> float:
    """
    Caida de tension (V), incluyendo el termino reactivo aproximado.
    e = k_sistema * L * Ib * (R*cosphi + X*sinphi),  R = 1/(kappa*S)
    k_sistema = 2 (monofasico, ida y vuelta) o raiz(3) (trifasico).
    """
    sin_phi = math.sqrt(max(0.0, 1 - cos_phi ** 2))
    r_por_metro = 1.0 / (kappa * seccion)
    x_por_metro = reactancia_ohm_km / 1000.0
    k_sistema = 2.0 if sistema == SISTEMA_MONO else math.sqrt(3)
    return k_sistema * longitud * ib * (r_por_metro * cos_phi + x_por_metro * sin_phi)


def seccion_por_caida_tension(sistema: str, ib: float, longitud: float, tension: float,
                               cos_phi: float, kappa: float, delta_u_max_pct: float,
                               conductor: str):
    """Menor seccion normalizada que respeta el limite de caida de tension."""
    minimo = MINIMO_ALUMINIO_MM2 if conductor == "Aluminio" else MINIMO_ABSOLUTO_MM2
    limite_v = tension * delta_u_max_pct / 100.0
    for s in SECCIONES_NORMALIZADAS:
        if s < minimo:
            continue
        e = caida_tension_voltios(sistema, ib, longitud, s, cos_phi, kappa)
        if e <= limite_v:
            pct = e / tension * 100.0
            return s, e, pct
    s_max = max(SECCIONES_NORMALIZADAS)
    e = caida_tension_voltios(sistema, ib, longitud, s_max, cos_phi, kappa)
    return None, e, e / tension * 100.0


def seccion_conductor_neutro(seccion_fase: float, conductor: str,
                              armonicos_significativos: bool) -> float:
    """
    Seccion del neutro (criterio general REBT / IEC 60364-5-52 punto 524):
    - Si S_fase <= 16 mm2 (Cu) o 25 mm2 (Al): S_neutro = S_fase.
    - Si es mayor y no hay armonicos relevantes: S_neutro >= S_fase / 2,
      redondeada a la seccion normalizada superior, nunca < 16 mm2.
    - Con armonicos de 3er orden significativos: S_neutro = S_fase.
    """
    umbral = 25.0 if conductor == "Aluminio" else 16.0
    if seccion_fase <= umbral or armonicos_significativos:
        return seccion_fase
    objetivo = max(seccion_fase / 2, 16.0)
    for s in SECCIONES_NORMALIZADAS:
        if s >= objetivo:
            return s
    return seccion_fase


def seccion_conductor_proteccion(seccion_fase: float) -> float:
    """
    Seccion del conductor de proteccion (ITC-BT-18 / IEC 60364-5-54):
      Sf <= 16      -> Sp = Sf
      16 < Sf <= 35 -> Sp = 16
      Sf > 35       -> Sp = Sf / 2 (redondeada a seccion normalizada)
    """
    if seccion_fase <= 16:
        return seccion_fase
    if seccion_fase <= 35:
        return 16.0
    objetivo = seccion_fase / 2
    for s in SECCIONES_NORMALIZADAS:
        if s >= objetivo:
            return s
    return seccion_fase


def verificar_cortocircuito(seccion: float, icc_ka: float, tiempo_s: float,
                             conductor: str, aislamiento: str):
    """
    Verificacion termica de cortocircuito: S_min = Icc*sqrt(t) / k (mm2).
    Devuelve (cumple, seccion_minima_necesaria).
    """
    k = K_CORTOCIRCUITO[(conductor, aislamiento)]
    if seccion > 300:
        if (conductor, aislamiento) == ("Cobre", "PVC"):
            k = 103
        elif (conductor, aislamiento) == ("Aluminio", "PVC"):
            k = 68
    icc_a = icc_ka * 1000.0
    s_min = (icc_a * math.sqrt(tiempo_s)) / k
    return seccion >= s_min, round(s_min, 2)


# ==============================================================================
# 3. ESTILO VISUAL (CSS inyectado)
# ==============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
    --bg-primary: #0b1220;
    --bg-panel: #121b2e;
    --bg-panel-alt: #16213a;
    --border-subtle: rgba(232, 163, 61, 0.16);
    --border-strong: rgba(232, 163, 61, 0.40);
    --text-primary: #e8edf4;
    --text-secondary: #8b96a8;
    --accent-copper: #e8a33d;
    --accent-ok: #4fd1c5;
    --accent-fail: #f2545b;
    --grid-line: rgba(232, 237, 244, 0.035);
}

.stApp {
    background-color: var(--bg-primary);
    background-image:
        linear-gradient(var(--grid-line) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 26px 26px;
}

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'IBM Plex Sans', sans-serif;
}
h1, h2, h3, h4 { font-family: 'JetBrains Mono', monospace; letter-spacing: -0.01em; }

/* ---------- Cartouche / titleblock ---------- */
.titleblock {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    border: 1px solid var(--border-strong);
    background: linear-gradient(180deg, var(--bg-panel), var(--bg-panel-alt));
    border-radius: 6px;
    margin-bottom: 1.6rem;
    overflow: hidden;
}
.titleblock-main { padding: 1.1rem 1.4rem; flex: 1; }
.titleblock-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent-copper);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.titleblock-main h1 {
    color: var(--text-primary);
    font-size: 1.55rem;
    margin: 0.15rem 0 0 0;
    font-weight: 700;
}
.titleblock-meta { display: flex; }
.titleblock-meta > div {
    border-left: 1px solid var(--border-subtle);
    padding: 0.9rem 1.1rem;
    min-width: 118px;
    display: flex; flex-direction: column; justify-content: center;
}
.titleblock-meta span {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-secondary);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.titleblock-meta strong {
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-primary);
    font-size: 0.82rem;
    margin-top: 0.15rem;
}

/* ---------- Section labels ---------- */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent-copper);
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0.35rem;
    margin: 0.4rem 0 0.9rem 0;
}

/* ---------- Result cards ---------- */
.result-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
}
.result-card.hero {
    border: 1px solid var(--border-strong);
    background: linear-gradient(135deg, rgba(232,163,61,0.10), var(--bg-panel));
}
.result-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-secondary);
}
.result-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--accent-copper);
    line-height: 1.3;
}
.result-value.small { font-size: 1.15rem; color: var(--text-primary); }
.result-sub { font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.15rem; }
.badge-ok { color: var(--accent-ok); font-weight: 600; }
.badge-fail { color: var(--accent-fail); font-weight: 600; }

/* ---------- Regla de secciones ---------- */
.regla-wrap { display: flex; gap: 4px; margin: 0.6rem 0 1rem 0; flex-wrap: wrap; }
.regla-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    padding: 0.28rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    background: var(--bg-panel);
}
.regla-chip.activa {
    border-color: var(--accent-copper);
    color: #0b1220;
    background: var(--accent-copper);
    font-weight: 700;
}

[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: var(--accent-copper); }
[data-testid="stExpander"] { border: 1px solid var(--border-subtle); border-radius: 6px; }
hr { border-color: var(--border-subtle); }
</style>
"""


# ==============================================================================
# 4. GENERACIÓN DE MEMORIA DE CÁLCULO (texto descargable)
# ==============================================================================

def _generar_memoria(inp: dict, res: dict) -> str:
    L = []
    L.append("=" * 72)
    L.append("MEMORIA DE CALCULO - SECCION DE CONDUCTORES (REBT)")
    L.append("=" * 72)
    L.append("")
    L.append(f"Tipo de circuito:      {inp['tipo_circuito']}")
    L.append(f"Sistema:               {inp['sistema']}  -  Tension: {inp['tension']:g} V")
    L.append(f"Conductor / Aislam.:   {inp['conductor']} / {inp['aislamiento']}")
    L.append(f"Metodo instalacion:    {inp['metodo']}")
    L.append(f"Longitud:              {inp['longitud']:g} m")
    L.append("")
    L.append("-" * 72)
    L.append("1. CRITERIO TERMICO (Ib <= In <= Iz) - ITC-BT-19 art. 19")
    L.append("-" * 72)
    L.append(f"  Ib (corriente de empleo):        {res['ib']:.2f} A")
    L.append(f"  Ib de calculo (tras factores):   {res['ib_calculo']:.2f} A")
    L.append(f"  Factor de correccion total:      {res['factor_total']:.3f}")
    if res.get('s_termica') is not None:
        L.append(f"  Seccion por criterio termico:    {res['s_termica']:g} mm2  (Iz = {res['iz_termica']:.1f} A)")
    L.append("")
    L.append("-" * 72)
    L.append("2. CRITERIO DE CAIDA DE TENSION - ITC-BT-14 / 15 / 19 / 40")
    L.append("-" * 72)
    L.append(f"  Delta U maxima admisible:        {res['delta_u_max']:g} %")
    L.append(f"  Delta U con seccion adoptada:    {res['e_pct']:.2f} %")
    L.append("")
    L.append("-" * 72)
    L.append("3. SECCION FINAL ADOPTADA")
    L.append("-" * 72)
    if res.get('seccion_final') is not None:
        L.append(f"  Seccion de fase:                 {res['seccion_final']:g} mm2")
    if res.get('seccion_neutro'):
        L.append(f"  Seccion de neutro:               {res['seccion_neutro']:g} mm2")
    if res.get('seccion_proteccion'):
        L.append(f"  Seccion de proteccion (PE):      {res['seccion_proteccion']:g} mm2")
    if res.get('necesita_paralelo'):
        L.append(f"  >> Requiere {res['n_paralelo']} conductores en paralelo por fase <<")
    L.append("")
    if res.get('cumple_cc') is not None:
        L.append("-" * 72)
        L.append("4. VERIFICACION TERMICA DE CORTOCIRCUITO")
        L.append("-" * 72)
        estado = "CUMPLE" if res['cumple_cc'] else "NO CUMPLE"
        L.append(f"  Resultado: {estado}  (seccion minima necesaria: {res['s_min_cc']:g} mm2)")
        L.append("")
    if res.get('avisos'):
        L.append("-" * 72)
        L.append("AVISOS")
        L.append("-" * 72)
        for a in res['avisos']:
            L.append(f"  - {a}")
        L.append("")
    L.append("=" * 72)
    L.append("Herramienta de apoyo al diseno. Verificar contra la Guia-BT-19")
    L.append("vigente antes de incorporar a un proyecto o memoria firmada.")
    L.append("=" * 72)
    return "\n".join(L)


# ==============================================================================
# 5. INTERFAZ STREAMLIT
# ==============================================================================

def _render_calculadora():
    avisos = []

    st.markdown('<p class="section-label">1 · Datos eléctricos del circuito</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        opciones_circuito = list(CAIDA_TENSION_MAX.keys())
        tipo_circuito = st.selectbox("Tipo de circuito / tramo", opciones_circuito, index=6,
                                      help="Determina la caída de tensión máxima admisible (ITC-BT-14/15/19/40).")
        sistema = st.selectbox("Sistema", [SISTEMA_MONO, SISTEMA_TRI])
    with c2:
        tension_defecto = 230.0 if sistema == SISTEMA_MONO else 400.0
        tension = st.number_input("Tensión de servicio (V)", min_value=100.0, max_value=1000.0,
                                   value=tension_defecto, step=1.0)
        modo_entrada = st.radio("Datos de partida", ["Potencia activa", "Intensidad directa"], horizontal=True)
    with c3:
        if modo_entrada == "Potencia activa":
            potencia_kw = st.number_input("Potencia activa (kW)", min_value=0.01, value=5.0, step=0.1)
            cos_phi = st.number_input("cos φ", min_value=0.10, max_value=1.00, value=0.90, step=0.01)
            intensidad_directa = None
        else:
            potencia_kw = None
            intensidad_directa = st.number_input("Intensidad (A)", min_value=0.1, value=20.0, step=0.5)
            cos_phi = st.number_input("cos φ (para ΔU)", min_value=0.10, max_value=1.00, value=0.90, step=0.01)

    st.markdown('<p class="section-label">2 · Datos de la instalación</p>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        conductor = st.selectbox("Material conductor", ["Cobre", "Aluminio"])
        metodo = st.selectbox("Método de instalación", METODOS_DISPONIBLES,
                               help="B1/B2 y C cubren la mayoría de vivienda/terciario; F es habitual en bandejas "
                                    "de gran potencia en industria; D es para tramos enterrados.")
    with c5:
        if metodo in (METODO_D, METODO_F):
            aislamiento = "XLPE/EPR"
            st.selectbox("Aislamiento", ["XLPE/EPR"], disabled=True,
                         help="Este método se modela sólo para XLPE/EPR, el estándar actual en enterrado y "
                              "bandejas de gran sección.")
        else:
            aislamiento = st.selectbox("Aislamiento", ["PVC", "XLPE/EPR"])
        longitud = st.number_input("Longitud del circuito (m)", min_value=0.1, value=20.0, step=1.0)
    with c6:
        delta_u_defecto = CAIDA_TENSION_MAX[tipo_circuito]
        valor_defecto = float(delta_u_defecto) if delta_u_defecto is not None else 3.0
        delta_u_max = st.number_input("ΔU máx. admisible (%)", min_value=0.1, max_value=10.0,
                                       value=valor_defecto, step=0.1,
                                       help="Editable: útil si tu proyecto aplica un criterio de compensación "
                                            "de caídas entre tramos distinto del habitual.")

    with st.expander("⚙️ Casuística especial — motores, alumbrado, armónicos"):
        cc1, cc2 = st.columns(2)
        with cc1:
            es_motor = st.checkbox("Circuito de motor (ITC-BT-47)")
            corrientes_motores = []
            ascensor_grua = False
            if es_motor:
                tipo_motor = st.radio("Motores en el circuito", ["Motor único", "Varios motores"], horizontal=True)
                if tipo_motor == "Motor único":
                    in_motor = st.number_input("In del motor (A)", min_value=0.1, value=20.0, step=0.5)
                    corrientes_motores = [in_motor]
                else:
                    texto_motores = st.text_input("In de cada motor, separadas por coma (A)", "20, 10, 8")
                    try:
                        corrientes_motores = [float(x.strip()) for x in texto_motores.split(",") if x.strip()]
                    except ValueError:
                        corrientes_motores = []
                        avisos.append("No se han podido interpretar las intensidades de motores introducidas; "
                                       "revisa el formato (usa comas y punto decimal).")
                ascensor_grua = st.checkbox("Ascensor / grúa (factor adicional ITC-BT-47, ×1,3)")
        with cc2:
            alumbrado_descarga = st.checkbox(
                "Alumbrado de descarga sin corregir f.d.p.",
                help="Aplica un factor orientativo ×1,8 a la intensidad de cálculo (ITC-BT-44) para lámparas "
                     "con reactancia sin condensador de compensación.")
            armonicos = st.checkbox(
                "Cargas no lineales / armónicos de 3er orden significativos",
                help="Informática, variadores de frecuencia, alumbrado electrónico... impide reducir la "
                     "sección del neutro por debajo de la de fase.")

    enterrado = metodo == METODO_D
    with st.expander("🌡️ Condiciones ambientales y agrupamiento"):
        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            temp_defecto = 25.0 if enterrado else 40.0
            temp_ambiente = st.number_input(
                "Temperatura ambiente (°C)", min_value=-10.0, max_value=80.0,
                value=temp_defecto, step=1.0,
                help="La Tabla A/D de la Guía-BT-19 está referida a 40°C (aire) / 25°C (terreno); se corrige "
                     "analíticamente si la temperatura real es distinta.")
            usar_kappa_20c = st.checkbox("Usar conductividad a 20°C para ΔU (menos conservador)", value=False)
        with ce2:
            disposicion = st.selectbox("Disposición de agrupamiento", list(TABLA_E_AGRUPAMIENTO.keys()))
            n_circuitos = st.number_input("Nº de circuitos/ternas agrupados", min_value=1, max_value=50,
                                           value=1, step=1)
        with ce3:
            n_capas = st.number_input("Nº de capas de bandejas/tubos", min_value=1, max_value=9, value=1, step=1)
            if enterrado:
                claves_resist = list(RESISTIVIDAD_TERRENO.keys())
                resistividad_label = st.selectbox("Resistividad térmica del terreno", claves_resist,
                                                   index=len(claves_resist) - 4)
                resistividad = RESISTIVIDAD_TERRENO[resistividad_label]
            else:
                resistividad = RESISTIVIDAD_REF_TERRENO

    with st.expander("⚡ Verificación de cortocircuito (opcional)"):
        verificar_cc = st.checkbox("Verificar criterio térmico de cortocircuito")
        icc_ka, tiempo_s = None, None
        if verificar_cc:
            ccc1, ccc2 = st.columns(2)
            with ccc1:
                icc_ka = st.number_input("Icc en el origen del circuito (kA)", min_value=0.01, value=6.0, step=0.1)
            with ccc2:
                tiempo_s = st.number_input("Tiempo de actuación de la protección (s)", min_value=0.001,
                                            value=0.1, step=0.01, format="%.3f")

    st.divider()

    # ============================ CÁLCULO ============================
    n_cargados = 2 if sistema == SISTEMA_MONO else 3

    if modo_entrada == "Potencia activa":
        ib = calcular_intensidad_empleo(sistema, potencia_kw * 1000.0, tension, cos_phi)
    else:
        ib = intensidad_directa

    ib_calculo = ib
    if es_motor and corrientes_motores:
        if len(corrientes_motores) == 1:
            ib_motor = factor_motor_unico(corrientes_motores[0])
        else:
            ib_motor = factor_varios_motores(corrientes_motores)
        if ascensor_grua:
            ib_motor *= 1.3
        ib_calculo = max(ib_calculo, ib_motor)
        avisos.append(f"Corriente de cálculo ajustada según ITC-BT-47 (motores): {ib_motor:.2f} A.")

    if alumbrado_descarga:
        ib_calculo *= 1.8
        avisos.append("Corriente de cálculo incrementada ×1,8 por alumbrado de descarga sin corregir (orientativo).")

    f_temp = factor_correccion_temperatura(aislamiento, temp_ambiente, enterrado)
    f_agrup = factor_correccion_agrupamiento(disposicion, int(n_circuitos))
    f_capas = factor_correccion_capas(int(n_capas))
    f_resist = factor_correccion_resistividad(resistividad) if enterrado else 1.0
    factor_total = f_temp * f_agrup * f_capas * f_resist

    if f_temp <= 0.05:
        avisos.append("La temperatura ambiente introducida iguala o supera la temperatura máxima de servicio "
                       "del aislamiento elegido: instalación no viable en estas condiciones.")

    s_termica, iz_termica, necesita_paralelo, n_paralelo = seccion_por_criterio_termico(
        ib_calculo, metodo, aislamiento, conductor, n_cargados, factor_total)

    kappa = kappa_servicio(conductor, aislamiento, usar_kappa_20c)
    ib_paralelo = ib_calculo / n_paralelo if necesita_paralelo else ib_calculo
    s_du, e_voltios, e_pct = seccion_por_caida_tension(
        sistema, ib_paralelo, longitud, tension, cos_phi, kappa, delta_u_max, conductor)

    candidatos = [s for s in (s_termica, s_du) if s is not None]
    seccion_final = max(candidatos) if candidatos else None
    if s_termica is not None and s_du is None:
        avisos.append("Ni siquiera 300 mm² cumple el criterio de caída de tensión con la longitud indicada: "
                       "valora más conductores en paralelo, reducir la longitud o elevar el nivel de tensión.")

    if seccion_final is not None:
        e_final = caida_tension_voltios(sistema, ib_paralelo, longitud, seccion_final, cos_phi, kappa)
        e_final_pct = e_final / tension * 100.0
    else:
        e_final, e_final_pct = e_voltios, e_pct

    seccion_neutro = None
    if sistema == SISTEMA_TRI and seccion_final is not None:
        seccion_neutro = seccion_conductor_neutro(seccion_final, conductor, armonicos)

    seccion_proteccion = seccion_conductor_proteccion(seccion_final) if seccion_final is not None else None

    if seccion_final is not None:
        if conductor == "Aluminio" and seccion_final < MINIMO_ALUMINIO_MM2:
            seccion_final = MINIMO_ALUMINIO_MM2
            avisos.append("Sección elevada a 16 mm² por ser el mínimo normativo del aluminio en instalación "
                           "fija (ITC-BT-07).")
        if tipo_circuito.startswith("LGA"):
            minimo_lga = MINIMO_LGA_ALUMINIO_MM2 if conductor == "Aluminio" else MINIMO_LGA_COBRE_MM2
            if seccion_final < minimo_lga:
                seccion_final = minimo_lga
                avisos.append(f"Sección elevada a {minimo_lga:g} mm² por ser el mínimo normativo de la LGA "
                               "(ITC-BT-14).")

    cumple_cc, s_min_cc = None, None
    if verificar_cc and seccion_final is not None:
        cumple_cc, s_min_cc = verificar_cortocircuito(seccion_final, icc_ka, tiempo_s, conductor, aislamiento)
        if not cumple_cc:
            avisos.append(f"La sección adoptada no soporta térmicamente el cortocircuito indicado: se "
                           f"necesitarían ≥ {s_min_cc:g} mm² (o una protección más rápida/limitadora).")

    # ============================ RESULTADOS ============================
    st.markdown('<p class="section-label">Resultado</p>', unsafe_allow_html=True)

    if seccion_final is None:
        st.error("No se ha podido determinar una sección con los parámetros indicados. Revisa los valores.")
        return

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'''<div class="result-card hero">
            <div class="result-label">Sección de fase adoptada</div>
            <div class="result-value">{seccion_final:g} mm²</div>
            <div class="result-sub">{conductor} · {aislamiento}</div>
        </div>''', unsafe_allow_html=True)
    with r2:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Ib de cálculo</div>
            <div class="result-value small">{ib_calculo:.2f} A</div>
            <div class="result-sub">Iz tabla: {iz_termica:.1f} A (S={s_termica:g} mm²)</div>
        </div>''', unsafe_allow_html=True)
    with r3:
        cumple_du = e_final_pct <= delta_u_max
        badge = "badge-ok" if cumple_du else "badge-fail"
        texto_badge = "Cumple" if cumple_du else "No cumple"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Caída de tensión</div>
            <div class="result-value small">{e_final_pct:.2f} %</div>
            <div class="result-sub"><span class="{badge}">{texto_badge}</span> · máx {delta_u_max:g}%</div>
        </div>''', unsafe_allow_html=True)
    with r4:
        neutro_txt = f"{seccion_neutro:g}" if seccion_neutro else "—"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Neutro / Protección (mm²)</div>
            <div class="result-value small">{neutro_txt} / {seccion_proteccion:g}</div>
            <div class="result-sub">Conductor de protección PE</div>
        </div>''', unsafe_allow_html=True)

    if necesita_paralelo:
        st.warning(f"La corriente de cálculo supera la capacidad de un único conductor de "
                   f"{max(SECCIONES_NORMALIZADAS):g} mm². Se necesitan **{n_paralelo} conductores en "
                   f"paralelo** de {seccion_final:g} mm² por fase (mismo material, longitud y aislamiento, "
                   "condición del REBT para la puesta en paralelo de conductores).")

    if verificar_cc:
        if cumple_cc:
            st.success(f"✅ Verificación de cortocircuito: {seccion_final:g} mm² soporta térmicamente "
                       f"Icc={icc_ka:g} kA durante {tiempo_s:g} s (mínimo requerido: {s_min_cc:g} mm²).")
        else:
            st.error(f"⚠️ Verificación de cortocircuito: {seccion_final:g} mm² NO soporta térmicamente "
                     f"Icc={icc_ka:g} kA durante {tiempo_s:g} s. Se requieren ≥ {s_min_cc:g} mm², o una "
                     "protección con actuación más rápida.")

    st.markdown('<p class="section-label">Secciones normalizadas evaluadas</p>', unsafe_allow_html=True)
    chips = "".join(
        f'<span class="regla-chip{" activa" if s == seccion_final else ""}">{s:g}</span>'
        for s in SECCIONES_NORMALIZADAS
    )
    st.markdown(f'<div class="regla-wrap">{chips}</div>', unsafe_allow_html=True)

    for aviso in avisos:
        st.info(aviso)

    with st.expander("📋 Ver detalle del cálculo, sección por sección"):
        filas = []
        for s in SECCIONES_NORMALIZADAS:
            base = iz_tabla(s, metodo, aislamiento, conductor, n_cargados)
            if base is None:
                continue
            iz_real = base * factor_total
            e = caida_tension_voltios(sistema, ib_calculo, longitud, s, cos_phi, kappa)
            pct = e / tension * 100
            filas.append({
                "Sección (mm²)": s,
                "Iz tabla (A)": base,
                "Iz corregida (A)": round(iz_real, 1),
                "Cumple térmico": "✅" if iz_real >= ib_calculo else "❌",
                "ΔU (%)": round(pct, 2),
                "Cumple ΔU": "✅" if pct <= delta_u_max else "❌",
            })
        st.dataframe(pd.DataFrame(filas), width='stretch', hide_index=True)
        st.caption("ΔU aquí calculada con la intensidad total (sin repartir en paralelo), para mostrar por "
                   "qué una sección concreta no bastaría por sí sola.")

    inp = dict(tipo_circuito=tipo_circuito, sistema=sistema, tension=tension, conductor=conductor,
               aislamiento=aislamiento, metodo=metodo, longitud=longitud)
    res = dict(ib=ib, ib_calculo=ib_calculo, factor_total=factor_total, s_termica=s_termica,
               iz_termica=iz_termica, delta_u_max=delta_u_max, e_pct=e_final_pct,
               seccion_final=seccion_final, seccion_neutro=seccion_neutro,
               seccion_proteccion=seccion_proteccion, necesita_paralelo=necesita_paralelo,
               n_paralelo=n_paralelo, cumple_cc=cumple_cc, s_min_cc=s_min_cc, avisos=avisos)
    memoria = _generar_memoria(inp, res)
    st.download_button("⬇️ Descargar memoria de cálculo (.txt)", data=memoria,
                        file_name="memoria_calculo_cable.txt", mime="text/plain")


def _render_tablas():
    st.markdown('<p class="section-label">Tabla A — Intensidades admisibles (A), cobre, no enterrado, '
                'aire a 40°C</p>', unsafe_allow_html=True)
    filas = []
    for s, datos in TABLA_A_COBRE.items():
        b1, c, f = datos["B1"], datos["C"], datos["F"]
        filas.append({
            "Sección (mm²)": s,
            "B1/B2 3×PVC": b1[0], "B1/B2 2×PVC": b1[1], "B1/B2 3×XLPE": b1[2], "B1/B2 2×XLPE": b1[3],
            "C 3×PVC": c[0], "C 2×PVC": c[1], "C 3×XLPE": c[2], "C 2×XLPE": c[3],
            "F (S≥25, XLPE)": f"{f:g}" if f is not None else "—",
        })
    st.dataframe(pd.DataFrame(filas), width='stretch', hide_index=True)
    st.caption("Fuente: Guía-BT-19 (Ministerio de Industria, Turismo y Comercio), Tabla A. Los valores de "
               "aluminio en instalación NO enterrada se estiman con un ratio orientativo de 0,78 respecto "
               "al cobre (la Guía-BT-19 remite a UNE-HD 60364-5-52 para esta combinación).")

    st.markdown('<p class="section-label">Tabla D — Enterrado bajo tubo, XLPE (terreno 25°C, '
                'ρ=1,5 K·m/W, 0,70 m)</p>', unsafe_allow_html=True)
    filas_d = []
    for s, (cu3, al3, cu2, al2) in TABLA_D_ENTERRADO_XLPE.items():
        filas_d.append({"Sección (mm²)": s, "3× Cobre": cu3,
                         "3× Aluminio": f"{al3:g}" if al3 is not None else "—",
                         "2× Cobre": cu2,
                         "2× Aluminio": f"{al2:g}" if al2 is not None else "—"})
    st.dataframe(pd.DataFrame(filas_d), width='stretch', hide_index=True)

    st.markdown('<p class="section-label">Tabla E — Factores de corrección por agrupamiento de '
                'circuitos</p>', unsafe_allow_html=True)
    claves = sorted(set(k for d in TABLA_E_AGRUPAMIENTO.values() for k in d.keys()))
    filas_e = []
    for disp, tabla in TABLA_E_AGRUPAMIENTO.items():
        fila = {"Disposición": disp}
        for k in claves:
            fila[f"{k} circ."] = f"{tabla[k]:.2f}" if k in tabla else "—"
        filas_e.append(fila)
    st.dataframe(pd.DataFrame(filas_e), width='stretch', hide_index=True)

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.markdown('<p class="section-label">Caídas de tensión máximas admisibles</p>', unsafe_allow_html=True)
        filas_u = [{"Tramo": k, "ΔU máx. (%)": f"{v:g}" if v is not None else "según proyecto"}
                   for k, v in CAIDA_TENSION_MAX.items()]
        st.dataframe(pd.DataFrame(filas_u), width='stretch', hide_index=True)
    with col_der:
        st.markdown('<p class="section-label">Constantes k — cortocircuito (S≤300 mm²)</p>',
                    unsafe_allow_html=True)
        filas_k = [{"Conductor": c, "Aislamiento": a, "k": v} for (c, a), v in K_CORTOCIRCUITO.items()]
        st.dataframe(pd.DataFrame(filas_k), width='stretch', hide_index=True)
        st.caption("S_mín = Icc·√t / k. Fuente: IEC 60364-5-54 / Libro Blanco de la Instalación (Prysmian).")


def _render_metodologia():
    st.markdown(
        """
### Criterios de dimensionado aplicados

Esta calculadora sigue el procedimiento de la **ITC-BT-19, artículo 19.2**, que exige que la sección de
un conductor cumpla simultáneamente:

**1. Criterio térmico — Ib ≤ In ≤ Iz.**
La intensidad admisible del cable (Iz), obtenida de la tabla de su método de instalación y corregida por
temperatura ambiente, agrupamiento de circuitos y, si procede, resistividad del terreno, debe ser igual o
superior a la corriente de empleo del circuito.

**2. Criterio de caída de tensión.**
La caída de tensión a lo largo del circuito —calculada con la conductividad del conductor **a su
temperatura de servicio** (70°C PVC / 90°C XLPE, criterio más conservador que usar la conductividad a
20°C)— no debe superar el porcentaje máximo admisible según el tramo (ITC-BT-14, 15, 19 y 40).

**3. Criterio térmico de cortocircuito** (verificación opcional).
Si se aportan la Icc en origen y el tiempo de actuación de la protección, se comprueba S ≥ Icc·√t / k.

La sección final adoptada es la mayor de las que exigen los criterios 1 y 2, redondeada a la sección
normalizada superior.

### Casuística contemplada
- Sistemas monofásico (230 V) y trifásico (400 V).
- Motores según ITC-BT-47: 125 % para motor único; 125 % del mayor + 100 % del resto para varios motores;
  +30 % adicional en ascensores/grúas.
- Alumbrado de descarga sin corregir el factor de potencia (factor orientativo ×1,8).
- Cargas con armónicos significativos → neutro a sección plena.
- Métodos de instalación: tubo empotrado/superficie (B1/B2), bandeja no perforada (C), bandeja perforada
  para grandes secciones (F, S≥25 mm²) y enterrado bajo tubo (D).
- Cobre y aluminio, con la sección mínima de 16 mm² del aluminio en instalación fija (ITC-BT-07) y la
  mínima de la LGA (ITC-BT-14).
- Conductores en paralelo cuando la intensidad supera la capacidad de un único conductor de 300 mm².
- Sección del neutro (mitad de fase cuando aplica) y del conductor de protección (ITC-BT-18).

### Limitaciones conocidas — léelas antes de usar en un proyecto firmado
- Los valores de **aluminio en instalación NO enterrada** son una estimación (ratio 0,78 respecto al
  cobre); la Guía-BT-19 remite a UNE-HD 60364-5-52 para esa combinación, no reproducida aquí íntegra.
- El factor de corrección por **resistividad térmica del terreno** es orientativo: la edición de la
  Guía-BT-19 consultada no publica una tabla cerrada de esa corrección junto a la Tabla D.
- Se excluyen los métodos A1/A2 (empotrado en pared térmicamente aislante) por ser poco habituales; si tu
  instalación usa ese método, la sección resultante aquí será optimista.
- La caída de tensión usa una reactancia lineal orientativa fija (0,08 Ω/km); en secciones muy grandes o
  disposiciones especiales puede diferir ligeramente.
- La verificación de cortocircuito comprueba el criterio **térmico** del conductor, no la coordinación de
  protecciones (curvas, poder de corte, selectividad), que debe verificarse aparte.

**En definitiva:** esta herramienta acelera el predimensionado y documenta el criterio seguido, pero no
sustituye la verificación de un técnico competente con la edición vigente de la Guía-BT-19 y el resto de
normativa aplicable antes de firmar un proyecto.
        """
    )


# ==============================================================================
# 6. PUNTO DE ENTRADA
# ==============================================================================

def main():
    st.set_page_config(page_title="Secciones de Cable · REBT", page_icon="⚡", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="titleblock">
            <div class="titleblock-main">
                <span class="titleblock-eyebrow">Cálculo de secciones · Baja tensión</span>
                <h1>Calculadora de Secciones de Cable</h1>
            </div>
            <div class="titleblock-meta">
                <div><span>Norma</span><strong>REBT · ITC-BT-19</strong></div>
                <div><span>Criterios</span><strong>Térmico · ΔU · Icc</strong></div>
                <div><span>Rev.</span><strong>1.0</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_calc, tab_tablas, tab_metodo = st.tabs(["🔌 Calculadora", "📊 Tablas normativas", "📖 Metodología"])
    with tab_calc:
        _render_calculadora()
    with tab_tablas:
        _render_tablas()
    with tab_metodo:
        _render_metodologia()


if __name__ == "__main__":
    main()
