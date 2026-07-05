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

Incluye además:
    - Justificación de fórmulas con los valores sustituidos (pestaña "Fórmulas")
    - Memoria de cálculo exportable en PDF con cajetín tipo plano técnico
    - Presupuesto (mediciones x precios unitarios editables) exportable a Excel

Fuentes numéricas: Guía-BT-19 (Ministerio de Industria, Turismo y Comercio,
Ed. feb-09 Rev.2) Tablas A, C, D, E, F; ITC-BT-14, ITC-BT-15, ITC-BT-47
(textos oficiales); Libro Blanco de la Instalación (Prysmian) para las
constantes k de cortocircuito. Ver pestaña "Metodología" para el detalle de
cada tabla, incluyendo qué valores son directos de la norma y cuáles son
estimaciones ancladas a un valor real verificado.

⚠️  Herramienta de apoyo al diseño, no un sustituto del criterio de un
    técnico competente. Antes de emitir un proyecto o memoria firmada,
    contrasta los valores críticos contra la edición vigente de la
    Guía-BT-19 y la norma UNE-HD 60364-5-52. Los precios del presupuesto
    son orientativos y deben sustituirse por los del proveedor real.

Autor: Younes — IDEA TSG
================================================================================
"""

from __future__ import annotations

import io
import math
from datetime import date

import pandas as pd
import streamlit as st

# ==============================================================================
# 1. CONSTANTES Y TABLAS NORMATIVAS
# ==============================================================================

SECCIONES_NORMALIZADAS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70,
                          95, 120, 150, 185, 240, 300]

CONDUCTIVIDAD_20C = {"Cobre": 56.0, "Aluminio": 35.0}
COEF_TEMP_RESIST = {"Cobre": 0.00393, "Aluminio": 0.00403}
TEMP_SERVICIO = {"PVC": 70.0, "XLPE/EPR": 90.0}
TEMP_REF_TABLA_AIRE = 40.0
TEMP_REF_TABLA_TERRENO = 25.0
RESISTIVIDAD_REF_TERRENO = 1.5

REACTANCIA_LINEAL_DEFECTO = 0.08

K_CORTOCIRCUITO = {
    ("Cobre", "PVC"): 115,
    ("Cobre", "XLPE/EPR"): 143,
    ("Aluminio", "PVC"): 76,
    ("Aluminio", "XLPE/EPR"): 94,
}

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

SISTEMA_MONO = "Monofásico (230 V)"
SISTEMA_TRI = "Trifásico (400 V)"

# Métodos de instalación disponibles. B1, C/E, F y D salen directamente de la
# Tabla A / Tabla D de la Guía-BT-19. A1 y B2 se derivan de B1 aplicando un
# ratio anclado a un valor real verificado de forma independiente (ver
# comentarios junto a cada factor, y la pestaña "Metodología").
METODO_A1 = "A1 — Tubo empotrado en pared aislante (estimado desde B1)"
METODO_B1 = "B1 — Tubo empotrado en obra o en superficie"
METODO_B2 = "B2 — Cable multiconductor en tubo (estimado desde B1)"
METODO_CE = "C/E — Bandeja no perforada o perforada / directo sobre superficie"
METODO_F = "F — Bandeja perforada, unipolares muy separados (S≥25 mm², XLPE)"
METODO_D = "D — Enterrado bajo tubo (XLPE)"
METODOS_DISPONIBLES = [METODO_A1, METODO_B1, METODO_B2, METODO_CE, METODO_F, METODO_D]

# Ratio A1/B1 anclado en un valor real verificado de forma independiente:
# A1, 2,5 mm², 2 cargados, PVC = 17,5 A (fuente: EleCalculador.com, con cita
# textual de la Guía-BT-19) frente a B1 2,5 mm² 2 cargados PVC = 21 A
# (Guía-BT-19 directa) → ratio 17,5/21 = 0,833.
FACTOR_A1_SOBRE_B1 = 0.833

# Ratio B2/B1 anclado en un ejercicio resuelto independiente (circuitoelectrico.com):
# B2, 25 mm², 2 cargados, PVC = 77 A frente a B1 25 mm² 2 cargados PVC = 84 A
# (Guía-BT-19 directa) → ratio 77/84 = 0,917. Coherente con el rango de
# variación (7-12 %) que cita Prysmian entre columnas B1 y B2.
FACTOR_B2_SOBRE_B1 = 0.917

# ------------------------------------------------------------------------------
# Tabla A — Intensidades admisibles (A), cables de COBRE, NO enterrados,
# temperatura ambiente de referencia 40°C. Fuente: Guía-BT-19, Tabla A.
# Aquí solo se tabula B1 (columnas 5-8) y C/E (columnas 9-12) y F (columna 13),
# que son los tres bloques de columnas de los que hay valores directos
# verificados; A1 y B2 se derivan de B1 mediante los factores anteriores.
# ------------------------------------------------------------------------------
TABLA_A_COBRE = {
    1.5:  {"B1": (13.5, 15.0, 16.0, 16.5), "CE": (19.0, 20.0, 21.0, 24.0), "F": None},
    2.5:  {"B1": (18.5, 21.0, 22.0, 23.0), "CE": (26.0, 26.5, 29.0, 33.0), "F": None},
    4:    {"B1": (24.0, 27.0, 30.0, 31.0), "CE": (34.0, 36.0, 38.0, 45.0), "F": None},
    6:    {"B1": (32.0, 36.0, 37.0, 40.0), "CE": (44.0, 46.0, 49.0, 57.0), "F": None},
    10:   {"B1": (44.0, 50.0, 52.0, 54.0), "CE": (60.0, 65.0, 68.0, 76.0), "F": None},
    16:   {"B1": (59.0, 66.0, 70.0, 73.0), "CE": (81.0, 87.0, 91.0, 105.0), "F": None},
    25:   {"B1": (77.0, 84.0, 88.0, 95.0), "CE": (103.0, 110.0, 116.0, 123.0), "F": 140.0},
    35:   {"B1": (96.0, 104.0, 110.0, 119.0), "CE": (127.0, 137.0, 144.0, 154.0), "F": 174.0},
    50:   {"B1": (117.0, 125.0, 133.0, 145.0), "CE": (155.0, 167.0, 175.0, 188.0), "F": 210.0},
    70:   {"B1": (149.0, 160.0, 171.0, 185.0), "CE": (199.0, 214.0, 224.0, 244.0), "F": 269.0},
    95:   {"B1": (180.0, 194.0, 207.0, 224.0), "CE": (241.0, 259.0, 271.0, 296.0), "F": 327.0},
    120:  {"B1": (208.0, 225.0, 240.0, 260.0), "CE": (280.0, 301.0, 314.0, 348.0), "F": 380.0},
    150:  {"B1": (236.0, 260.0, 278.0, 299.0), "CE": (322.0, 343.0, 363.0, 404.0), "F": 438.0},
    185:  {"B1": (268.0, 297.0, 317.0, 341.0), "CE": (368.0, 391.0, 415.0, 464.0), "F": 500.0},
    240:  {"B1": (315.0, 350.0, 374.0, 401.0), "CE": (435.0, 468.0, 490.0, 552.0), "F": 590.0},
    300:  {"B1": (361.0, 401.0, 430.0, 461.0), "CE": (500.0, 538.0, 563.0, 638.0), "F": 678.0},
}
IDX_3PVC, IDX_2PVC, IDX_3XLPE, IDX_2XLPE = 0, 1, 2, 3

RATIO_ALUMINIO_NO_ENTERRADO = 0.78

TABLA_D_ENTERRADO_XLPE = {
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
FACTOR_RESISTIVIDAD_TERRENO = {
    0.40: 1.25, 0.50: 1.21, 0.70: 1.18, 0.85: 1.14, 1.00: 1.10,
    1.20: 1.05, 1.50: 1.00, 2.00: 0.93, 2.50: 0.89, 3.00: 0.85,
}

TABLA_E_AGRUPAMIENTO = {
    "Empotrados o embutidos": {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.70, 6: 0.55, 9: 0.50, 12: 0.45, 16: 0.40, 20: 0.40},
    "Capa única sobre pared/suelo/bandeja no perforada": {1: 1.00, 2: 0.85, 3: 0.80, 4: 0.75, 6: 0.70, 9: 0.70},
    "Capa única fijada bajo techo": {1: 0.95, 2: 0.80, 3: 0.70, 4: 0.70, 6: 0.65, 9: 0.60},
    "Capa única en bandeja perforada (horiz. o vert.)": {1: 1.00, 2: 0.90, 3: 0.80, 4: 0.75, 6: 0.75, 9: 0.70},
    "Capa única en bandeja de escalera / abrazaderas": {1: 1.00, 2: 0.85, 3: 0.80, 4: 0.80, 6: 0.80, 9: 0.80},
}
TABLA_F_CAPAS = {1: 1.00, 2: 0.80, 3: 0.73, 4: 0.70, 5: 0.70, 6: 0.68, 7: 0.68, 8: 0.68, 9: 0.66}

MINIMO_ABSOLUTO_MM2 = 1.5
MINIMO_ALUMINIO_MM2 = 16.0
MINIMO_LGA_COBRE_MM2 = 10.0
MINIMO_LGA_ALUMINIO_MM2 = 16.0

# ------------------------------------------------------------------------------
# Precios orientativos (€) — PUNTO DE PARTIDA EDITABLE, no precios de mercado
# en tiempo real. El precio del cobre fluctúa; sustituye por los de tu
# proveedor antes de presupuestar en firme. Cable unipolar tipo RZ1-K 0,6/1kV
# (Cu), €/m aproximados de referencia.
# ------------------------------------------------------------------------------
PRECIOS_CABLE_COBRE_DEFECTO = {
    1.5: 0.45, 2.5: 0.65, 4: 0.95, 6: 1.35, 10: 2.10, 16: 3.20, 25: 5.50,
    35: 7.50, 50: 10.50, 70: 14.50, 95: 19.50, 120: 24.50, 150: 30.50,
    185: 38.00, 240: 49.00, 300: 62.00,
}
RATIO_PRECIO_ALUMINIO = 0.55  # el cable de aluminio es sensiblemente más barato que el de cobre

PRECIOS_CANALIZACION_DEFECTO = {
    METODO_A1: 1.10, METODO_B1: 1.10, METODO_B2: 1.10,
    METODO_CE: 3.50, METODO_F: 4.50, METODO_D: 6.00,
}
PRECIO_MANO_OBRA_POR_METRO = 2.20
PORCENTAJE_ACCESORIOS = 8.0  # % sobre el subtotal de materiales (cajas, terminales, prensaestopas...)

# Calibres normalizados de interruptor automático (A) y precio orientativo (€)
CALIBRES_MAGNETOTERMICO = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
PRECIOS_MAGNETOTERMICO_DEFECTO = {
    10: 18, 16: 18, 20: 19, 25: 20, 32: 22, 40: 28, 50: 35, 63: 45,
    80: 120, 100: 145, 125: 180, 160: 260, 200: 320, 250: 410,
}
PRECIOS_DIFERENCIAL_DEFECTO = {
    25: 55, 40: 65, 63: 90, 80: 210, 100: 260, 125: 320, 160: 420, 200: 520, 250: 650,
}

# ------------------------------------------------------------------------------
# Catálogo ampliado de materiales típicos de una instalación eléctrica de BT.
# Precios orientativos (€), punto de partida editable en la pestaña Presupuesto
# — no son precios de mercado en tiempo real. Organizado por categorías para
# que el desplegable de "añadir partida" sea manejable.
# ------------------------------------------------------------------------------
CATALOGO_MATERIALES = {
    "Canalizaciones": {
        "Tubo corrugado empotrar Ø16mm": ("m", 0.55),
        "Tubo corrugado empotrar Ø20mm": ("m", 0.65),
        "Tubo corrugado empotrar Ø25mm": ("m", 0.85),
        "Tubo corrugado empotrar Ø32mm": ("m", 1.10),
        "Tubo rígido superficie Ø20mm": ("m", 1.60),
        "Tubo rígido superficie Ø32mm": ("m", 2.40),
        "Bandeja perforada 100mm": ("m", 6.50),
        "Bandeja perforada 200mm": ("m", 9.80),
        "Bandeja perforada 300mm": ("m", 13.50),
        "Bandeja no perforada (rejiband) 200mm": ("m", 8.20),
        "Canaleta PVC 20x12mm": ("m", 2.10),
        "Canaleta PVC 40x25mm": ("m", 4.30),
    },
    "Cajas y mecanismos": {
        "Caja de derivación empotrar 100x100": ("ud", 1.80),
        "Caja de derivación estanca IP65 150x110": ("ud", 6.50),
        "Caja de mecanismo universal": ("ud", 0.60),
        "Interruptor simple (mecanismo + tecla)": ("ud", 8.50),
        "Conmutador": ("ud", 9.50),
        "Pulsador timbre": ("ud", 7.50),
        "Base de enchufe Schuko 16A": ("ud", 8.90),
        "Base industrial CETAC 16A 3P+N+T": ("ud", 22.00),
        "Base industrial CETAC 32A 3P+N+T": ("ud", 35.00),
        "Marco embellecedor": ("ud", 3.20),
    },
    "Protección y maniobra": {
        "Interruptor general automático (IGA)": ("ud", 65.00),
        "Contactor 25A": ("ud", 38.00),
        "Contactor 40A": ("ud", 58.00),
        "Guardamotor 0,4-40A (según ajuste)": ("ud", 75.00),
        "Relé térmico": ("ud", 42.00),
        "Seccionador bajo carga 40A": ("ud", 48.00),
        "Base + fusible cilíndrico 10x38": ("ud", 6.50),
        "Fusible NH tamaño 00": ("ud", 12.00),
    },
    "Cuadros eléctricos": {
        "Cuadro superficie 12 módulos": ("ud", 28.00),
        "Cuadro superficie 24 módulos": ("ud", 42.00),
        "Cuadro superficie 36 módulos": ("ud", 58.00),
        "Cuadro empotrar 24 módulos": ("ud", 48.00),
        "Cuadro empotrar 48 módulos": ("ud", 78.00),
        "Embarrado de peine 12 módulos": ("ud", 9.50),
    },
    "Puesta a tierra": {
        "Pica de acero cobreado 2m Ø14mm": ("ud", 14.00),
        "Cable desnudo Cu 35mm² (tierra)": ("m", 4.80),
        "Grapa de conexión pica-cable": ("ud", 3.50),
        "Soldadura aluminotérmica": ("ud", 9.00),
        "Arqueta de registro de tierra": ("ud", 32.00),
        "Punto de puesta a tierra (caja + borne)": ("ud", 15.00),
    },
    "Luminarias": {
        "Downlight LED 12W empotrar": ("ud", 11.50),
        "Pantalla LED 60x60 40W": ("ud", 28.00),
        "Luminaria estanca IP65 1x36W LED": ("ud", 24.00),
        "Aparato autónomo de emergencia LED": ("ud", 26.00),
        "Proyector LED exterior 50W": ("ud", 45.00),
    },
    "Varios / accesorios": {
        "Prensaestopas M20": ("ud", 0.90),
        "Prensaestopas M32": ("ud", 1.60),
        "Terminal/puntera tubular (según sección)": ("ud", 0.35),
        "Brida de nylon": ("ud", 0.08),
        "Etiqueta de señalización normalizada": ("ud", 1.20),
        "Regleta de conexión": ("ud", 2.50),
    },
}

# Estructura clásica de presupuesto de instalaciones en España: sobre el
# Presupuesto de Ejecución Material (materiales + mano de obra) se aplican
# estos dos porcentajes editables antes del total.
PORCENTAJE_BENEFICIO_DEFECTO = 15.0       # beneficio industrial
PORCENTAJE_AMORTIZACION_DEFECTO = 3.0     # amortización de medios auxiliares / herramientas

# ------------------------------------------------------------------------------
# Catálogo de símbolos para el esquema unifilar (representación simplificada,
# inspirada en IEC 60617). Cada símbolo define cómo dibujarse en el preview
# SVG y qué entidades DXF generar; ver dibujar_simbolo_svg() y
# _dxf_dibujar_simbolo().
# ------------------------------------------------------------------------------
SIMBOLOS_UNIFILAR = [
    "Interruptor automático (magnetotérmico)",
    "Interruptor diferencial",
    "Interruptor general (IGA)",
    "Seccionador",
    "Fusible",
    "Contactor",
    "Guardamotor",
    "Transformador",
    "Motor",
    "Contador de energía",
    "Condensador",
    "Puesta a tierra",
    "Lámpara / receptor",
]


# ==============================================================================
# 2. FUNCIONES DE CALCULO (logica pura, sin dependencias de Streamlit)
# ==============================================================================

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
    """factor = sqrt((Tmax - Ta) / (Tmax - Tref)), Tref=40C aire / 25C terreno."""
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
    Intensidad admisible tabulada (A), antes de factores de correccion.
    A1 y B2 se derivan de B1 aplicando FACTOR_A1_SOBRE_B1 / FACTOR_B2_SOBRE_B1.
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
        tupla_b1 = fila["B1"]
        tupla_ce = fila["CE"]
        idx = None
        if aislamiento == "PVC":
            idx = IDX_3PVC if n_cargados == 3 else IDX_2PVC
        else:
            idx = IDX_3XLPE if n_cargados == 3 else IDX_2XLPE

        if metodo == METODO_A1:
            valor_cu = round(tupla_b1[idx] * FACTOR_A1_SOBRE_B1, 1)
        elif metodo == METODO_B1:
            valor_cu = tupla_b1[idx]
        elif metodo == METODO_B2:
            valor_cu = round(tupla_b1[idx] * FACTOR_B2_SOBRE_B1, 1)
        else:  # METODO_CE
            valor_cu = tupla_ce[idx]

    if conductor == "Cobre":
        return valor_cu
    return round(valor_cu * RATIO_ALUMINIO_NO_ENTERRADO, 1)


def seccion_por_criterio_termico(ib_calculo: float, metodo: str, aislamiento: str,
                                  conductor: str, n_cargados: int,
                                  factor_correccion: float):
    """Menor seccion normalizada cuya Iz (tabla x factor) >= Ib. Si ninguna basta,
    evalua conductores en paralelo con la mayor seccion disponible."""
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
    """e = k_sistema * L * Ib * (R*cosphi + X*sinphi), R = 1/(kappa*S)."""
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
    """Sf<=16(Cu)/25(Al) -> Sn=Sf. Si no, Sn>=Sf/2 (redondeada, min 16). Con
    armonicos de 3er orden significativos, Sn=Sf siempre."""
    umbral = 25.0 if conductor == "Aluminio" else 16.0
    if seccion_fase <= umbral or armonicos_significativos:
        return seccion_fase
    objetivo = max(seccion_fase / 2, 16.0)
    for s in SECCIONES_NORMALIZADAS:
        if s >= objetivo:
            return s
    return seccion_fase


def seccion_conductor_proteccion(seccion_fase: float) -> float:
    """Sf<=16 -> Sp=Sf; 16<Sf<=35 -> Sp=16; Sf>35 -> Sp=Sf/2 (redondeada)."""
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
    """S_min = Icc*sqrt(t) / k (mm2). Devuelve (cumple, seccion_minima)."""
    k = K_CORTOCIRCUITO[(conductor, aislamiento)]
    if seccion > 300:
        if (conductor, aislamiento) == ("Cobre", "PVC"):
            k = 103
        elif (conductor, aislamiento) == ("Aluminio", "PVC"):
            k = 68
    icc_a = icc_ka * 1000.0
    s_min = (icc_a * math.sqrt(tiempo_s)) / k
    return seccion >= s_min, round(s_min, 2)


def calibre_magnetotermico_sugerido(ib_calculo: float) -> int:
    """Menor calibre normalizado de interruptor automático >= Ib de cálculo."""
    for c in CALIBRES_MAGNETOTERMICO:
        if c >= ib_calculo:
            return c
    return CALIBRES_MAGNETOTERMICO[-1]


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
# 4. ORQUESTADOR DE CÁLCULO (puro: dict de entradas -> dict de resultados)
# ==============================================================================

def calcular(inp: dict) -> dict:
    """Ejecuta los 3 criterios de la ITC-BT-19 art. 19.2 a partir del dict de
    entradas producido por _render_inputs(). No toca Streamlit: es testeable
    de forma aislada."""
    avisos = []
    sistema = inp["sistema"]
    n_cargados = 2 if sistema == SISTEMA_MONO else 3

    if inp["modo_entrada"] == "Potencia activa":
        ib = calcular_intensidad_empleo(sistema, inp["potencia_kw"] * 1000.0, inp["tension"], inp["cos_phi"])
    else:
        ib = inp["intensidad_directa"]

    ib_calculo = ib
    ib_motor = None
    if inp["es_motor"] and inp["corrientes_motores"]:
        corrientes = inp["corrientes_motores"]
        if len(corrientes) == 1:
            ib_motor = factor_motor_unico(corrientes[0])
        else:
            ib_motor = factor_varios_motores(corrientes)
        if inp["ascensor_grua"]:
            ib_motor *= 1.3
        ib_calculo = max(ib_calculo, ib_motor)
        avisos.append(f"Corriente de cálculo ajustada según ITC-BT-47 (motores): {ib_motor:.2f} A.")

    if inp["alumbrado_descarga"]:
        ib_calculo *= 1.8
        avisos.append("Corriente de cálculo incrementada ×1,8 por alumbrado de descarga sin corregir (orientativo).")

    f_temp = factor_correccion_temperatura(inp["aislamiento"], inp["temp_ambiente"], inp["enterrado"])
    f_agrup = factor_correccion_agrupamiento(inp["disposicion"], int(inp["n_circuitos"]))
    f_capas = factor_correccion_capas(int(inp["n_capas"]))
    f_resist = factor_correccion_resistividad(inp["resistividad"]) if inp["enterrado"] else 1.0
    factor_total = f_temp * f_agrup * f_capas * f_resist

    if f_temp <= 0.05:
        avisos.append("La temperatura ambiente introducida iguala o supera la temperatura máxima de servicio "
                       "del aislamiento elegido: instalación no viable en estas condiciones.")

    s_termica, iz_termica, necesita_paralelo, n_paralelo = seccion_por_criterio_termico(
        ib_calculo, inp["metodo"], inp["aislamiento"], inp["conductor"], n_cargados, factor_total)

    kappa = kappa_servicio(inp["conductor"], inp["aislamiento"], inp["usar_kappa_20c"])
    ib_paralelo = ib_calculo / n_paralelo if necesita_paralelo else ib_calculo
    s_du, e_voltios, e_pct = seccion_por_caida_tension(
        sistema, ib_paralelo, inp["longitud"], inp["tension"], inp["cos_phi"], kappa,
        inp["delta_u_max"], inp["conductor"])

    candidatos = [s for s in (s_termica, s_du) if s is not None]
    seccion_final = max(candidatos) if candidatos else None
    if s_termica is not None and s_du is None:
        avisos.append("Ni siquiera 300 mm² cumple el criterio de caída de tensión con la longitud indicada: "
                       "valora más conductores en paralelo, reducir la longitud o elevar el nivel de tensión.")

    if seccion_final is not None:
        e_final = caida_tension_voltios(sistema, ib_paralelo, inp["longitud"], seccion_final, inp["cos_phi"], kappa)
        e_final_pct = e_final / inp["tension"] * 100.0
    else:
        e_final, e_final_pct = e_voltios, e_pct

    seccion_neutro = None
    if sistema == SISTEMA_TRI and seccion_final is not None:
        seccion_neutro = seccion_conductor_neutro(seccion_final, inp["conductor"], inp["armonicos"])

    seccion_proteccion = seccion_conductor_proteccion(seccion_final) if seccion_final is not None else None

    if seccion_final is not None:
        if inp["conductor"] == "Aluminio" and seccion_final < MINIMO_ALUMINIO_MM2:
            seccion_final = MINIMO_ALUMINIO_MM2
            avisos.append("Sección elevada a 16 mm² por ser el mínimo normativo del aluminio en instalación "
                           "fija (ITC-BT-07).")
        if inp["tipo_circuito"].startswith("LGA"):
            minimo_lga = MINIMO_LGA_ALUMINIO_MM2 if inp["conductor"] == "Aluminio" else MINIMO_LGA_COBRE_MM2
            if seccion_final < minimo_lga:
                seccion_final = minimo_lga
                avisos.append(f"Sección elevada a {minimo_lga:g} mm² por ser el mínimo normativo de la LGA "
                               "(ITC-BT-14).")

    cumple_cc, s_min_cc = None, None
    if inp["verificar_cc"] and seccion_final is not None:
        cumple_cc, s_min_cc = verificar_cortocircuito(seccion_final, inp["icc_ka"], inp["tiempo_s"],
                                                        inp["conductor"], inp["aislamiento"])
        if not cumple_cc:
            avisos.append(f"La sección adoptada no soporta térmicamente el cortocircuito indicado: se "
                           f"necesitarían ≥ {s_min_cc:g} mm² (o una protección más rápida/limitadora).")

    calibre = calibre_magnetotermico_sugerido(ib_calculo)

    return dict(
        n_cargados=n_cargados, ib=ib, ib_calculo=ib_calculo, ib_motor=ib_motor,
        f_temp=f_temp, f_agrup=f_agrup, f_capas=f_capas, f_resist=f_resist, factor_total=factor_total,
        s_termica=s_termica, iz_termica=iz_termica, necesita_paralelo=necesita_paralelo, n_paralelo=n_paralelo,
        kappa=kappa, ib_paralelo=ib_paralelo, s_du=s_du, e_voltios=e_voltios, e_pct=e_pct,
        seccion_final=seccion_final, e_final=e_final, e_final_pct=e_final_pct,
        seccion_neutro=seccion_neutro, seccion_proteccion=seccion_proteccion,
        cumple_cc=cumple_cc, s_min_cc=s_min_cc, calibre_magnetotermico=calibre, avisos=avisos,
    )


# ==============================================================================
# 5. GENERACIÓN DE PDF (memoria de cálculo con cajetín tipo plano técnico)
# ==============================================================================
# Nota sobre codificación: las fuentes estándar de reportlab (Helvetica) usan
# WinAnsiEncoding, que soporta vocales acentuadas y ñ sin problema, pero NO
# incluye de forma fiable símbolos como Δ, ≤, ≥, √ o ÷. Para evitar glifos
# rotos en el PDF, se sanean esos símbolos a su equivalente ASCII antes de
# escribir cualquier texto; el resto de la app (interfaz Streamlit) sigue
# usando los símbolos Unicode con normalidad, ya que el navegador sí los
# renderiza correctamente.

_PDF_REPLACEMENTS = {
    "Δ": "Delta ", "≤": "<=", "≥": ">=", "√": "raiz", "÷": "/",
    "²": "2", "³": "3", "°": "gr.", "·": "-", "×": "x",
    "—": "-", "–": "-", "✅": "[OK]", "❌": "[NO]", "⚠️": "[AVISO]",
    "⬇️": "", "🔌": "", "📊": "", "📖": "", "⚙️": "", "🌡️": "", "⚡": "",
}


def _pdf_safe(texto: str) -> str:
    texto = str(texto)
    for k, v in _PDF_REPLACEMENTS.items():
        texto = texto.replace(k, v)
    return texto


def generar_pdf_memoria(inp: dict, res: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    AZUL = colors.HexColor("#122340")
    COBRE = colors.HexColor("#b3711f")
    GRIS = colors.HexColor("#5a6472")

    buffer = io.BytesIO()
    margin = 1.6 * cm
    cajetin_h = 2.4 * cm

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin + cajetin_h + 0.3 * cm, bottomMargin=margin + 0.6 * cm,
    )

    fecha_hoy = date.today().strftime("%d/%m/%Y")

    def _cajetin(c, d):
        c.saveState()
        width, height = A4
        top = height - margin
        c.setStrokeColor(AZUL)
        c.setLineWidth(1.1)
        c.rect(margin, top - cajetin_h, width - 2 * margin, cajetin_h)
        divisor_x = width - margin - 5.2 * cm
        c.line(divisor_x, top - cajetin_h, divisor_x, top)
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 12.5)
        c.drawString(margin + 0.35 * cm, top - 0.85 * cm, "MEMORIA DE CALCULO - SECCION DE CONDUCTORES")
        c.setFont("Helvetica", 8.3)
        c.setFillColor(GRIS)
        c.drawString(margin + 0.35 * cm, top - 1.35 * cm, "Reglamento Electrotecnico de Baja Tension - ITC-BT-19")
        c.setFont("Helvetica", 8.3)
        c.drawString(margin + 0.35 * cm, top - 1.85 * cm, _pdf_safe(f"Circuito: {inp['tipo_circuito']}"))

        campos = [
            ("NORMA", "REBT - ITC-BT-19"),
            ("FECHA", fecha_hoy),
            ("REVISION", "1.0"),
        ]
        y = top - 0.55 * cm
        for etiqueta, valor in campos:
            c.setFont("Helvetica-Bold", 6.6)
            c.setFillColor(GRIS)
            c.drawString(divisor_x + 0.3 * cm, y, etiqueta)
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(AZUL)
            c.drawString(divisor_x + 0.3 * cm, y - 0.34 * cm, valor)
            y -= 0.72 * cm
        c.setStrokeColor(COBRE)
        c.setLineWidth(2.2)
        c.line(margin, top - cajetin_h, width - margin, top - cajetin_h)

        c.setFont("Helvetica-Oblique", 6.8)
        c.setFillColor(GRIS)
        c.drawCentredString(
            width / 2, margin * 0.45,
            "Herramienta de apoyo al diseno. Verificar contra la Guia-BT-19 vigente antes de firmar un proyecto.",
        )
        c.drawRightString(width - margin, margin * 0.45, f"Pag. {d.page}")
        c.restoreState()

    styles = getSampleStyleSheet()
    h2 = ParagraphStyle("h2c", parent=styles["Heading2"], textColor=AZUL, fontSize=12, spaceBefore=10, spaceAfter=4)
    normal = ParagraphStyle("normalc", parent=styles["Normal"], fontSize=9.3, leading=13)
    aviso_style = ParagraphStyle("avisoc", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#8a4b00"))

    def fila_estilo(header=True):
        base = [
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ccd1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if header:
            base += [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                      ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        return TableStyle(base)

    story = []

    story.append(Paragraph("1. Datos del circuito", h2))
    datos = [
        ["Concepto", "Valor"],
        ["Tipo de circuito", _pdf_safe(inp["tipo_circuito"])],
        ["Sistema", _pdf_safe(inp["sistema"]) + f"  -  {inp['tension']:g} V"],
        ["Conductor / Aislamiento", f"{inp['conductor']} / {inp['aislamiento']}"],
        ["Metodo de instalacion", _pdf_safe(inp["metodo"])],
        ["Longitud", f"{inp['longitud']:g} m"],
    ]
    t = Table(datos, colWidths=[6.5 * cm, 9.5 * cm])
    t.setStyle(fila_estilo())
    story.append(t)

    story.append(Paragraph("2. Criterio termico (Ib &lt;= In &lt;= Iz) - ITC-BT-19 art. 19", h2))
    termico = [
        ["Magnitud", "Valor"],
        ["Ib (corriente de empleo)", f"{res['ib']:.2f} A"],
        ["Ib de calculo (tras factores)", f"{res['ib_calculo']:.2f} A"],
        ["Factor de correccion total", f"{res['factor_total']:.3f}"],
        ["Seccion por criterio termico", f"{res['s_termica']:g} mm2" if res["s_termica"] else "-"],
        ["Iz obtenida (tabla x factores)", f"{res['iz_termica']:.1f} A" if res["iz_termica"] else "-"],
    ]
    t = Table(termico, colWidths=[6.5 * cm, 9.5 * cm])
    t.setStyle(fila_estilo())
    story.append(t)

    story.append(Paragraph("3. Criterio de caida de tension - ITC-BT-14/15/19/40", h2))
    du = [
        ["Magnitud", "Valor"],
        ["Delta U maxima admisible", f"{res['e_final_pct'] and inp['delta_u_max']:g} %"],
        ["Delta U con la seccion adoptada", f"{res['e_final_pct']:.2f} %"],
        ["Cumple", "SI" if res["e_final_pct"] <= inp["delta_u_max"] else "NO"],
    ]
    t = Table(du, colWidths=[6.5 * cm, 9.5 * cm])
    t.setStyle(fila_estilo())
    story.append(t)

    story.append(Paragraph("4. Seccion final adoptada", h2))
    final_rows = [["Elemento", "Seccion"]]
    if res["seccion_final"] is not None:
        final_rows.append(["Conductor de fase", f"{res['seccion_final']:g} mm2"])
    if res.get("seccion_neutro"):
        final_rows.append(["Conductor de neutro", f"{res['seccion_neutro']:g} mm2"])
    if res.get("seccion_proteccion"):
        final_rows.append(["Conductor de proteccion (PE)", f"{res['seccion_proteccion']:g} mm2"])
    if res.get("necesita_paralelo"):
        final_rows.append(["Conductores en paralelo", f"{res['n_paralelo']} x {res['seccion_final']:g} mm2 por fase"])
    final_rows.append(["Interruptor automatico sugerido", f"{res['calibre_magnetotermico']} A"])
    t = Table(final_rows, colWidths=[6.5 * cm, 9.5 * cm])
    t.setStyle(fila_estilo())
    story.append(t)

    if res.get("cumple_cc") is not None:
        story.append(Paragraph("5. Verificacion termica de cortocircuito", h2))
        estado = "CUMPLE" if res["cumple_cc"] else "NO CUMPLE"
        cc_rows = [
            ["Magnitud", "Valor"],
            ["Resultado", estado],
            ["Seccion minima necesaria", f"{res['s_min_cc']:g} mm2"],
        ]
        t = Table(cc_rows, colWidths=[6.5 * cm, 9.5 * cm])
        t.setStyle(fila_estilo())
        story.append(t)

    story.append(Paragraph("6. Formulas aplicadas", h2))
    for linea in _lineas_formulas_texto(inp, res):
        story.append(Paragraph(_pdf_safe(linea), normal))

    if res.get("avisos"):
        story.append(Paragraph("7. Avisos", h2))
        for a in res["avisos"]:
            story.append(Paragraph("- " + _pdf_safe(a), aviso_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Herramienta de apoyo al diseno. Los valores de esta memoria deben verificarse contra la edicion "
        "vigente de la Guia-BT-19 y la normativa UNE aplicable antes de incorporarse a un proyecto o "
        "memoria tecnica firmada.", normal))

    doc.build(story, onFirstPage=_cajetin, onLaterPages=_cajetin)
    return buffer.getvalue()


# ==============================================================================
# 6. JUSTIFICACIÓN DE FÓRMULAS (texto plano, reutilizado por PDF y por la UI)
# ==============================================================================

def _lineas_formulas_texto(inp: dict, res: dict) -> list:
    """Genera la secuencia de fórmulas con los valores del cálculo actual
    sustituidos, en texto plano (sin LaTeX), para incluir en el PDF."""
    L = []
    sistema = inp["sistema"]
    cos_phi = inp["cos_phi"]

    if inp["modo_entrada"] == "Potencia activa":
        p_w = inp["potencia_kw"] * 1000.0
        if sistema == SISTEMA_MONO:
            L.append(f"Ib = P / (V x cos(phi)) = {p_w:.0f} / ({inp['tension']:g} x {cos_phi:.2f}) "
                      f"= {res['ib']:.2f} A")
        else:
            L.append(f"Ib = P / (raiz(3) x V x cos(phi)) = {p_w:.0f} / (1,732 x {inp['tension']:g} x "
                      f"{cos_phi:.2f}) = {res['ib']:.2f} A")
    else:
        L.append(f"Ib = {res['ib']:.2f} A (introducida directamente)")

    if res.get("ib_motor") is not None:
        if len(inp["corrientes_motores"]) == 1:
            L.append(f"Motor unico (ITC-BT-47): Ib_calculo = 1,25 x In = 1,25 x "
                      f"{inp['corrientes_motores'][0]:.2f} = {res['ib_motor']:.2f} A")
        else:
            ordenados = sorted(inp["corrientes_motores"], reverse=True)
            resto = " + ".join(f"{x:.1f}" for x in ordenados[1:])
            L.append(f"Varios motores (ITC-BT-47): Ib_calculo = 1,25 x {ordenados[0]:.2f} + ({resto}) "
                      f"= {res['ib_motor']:.2f} A")
        if inp["ascensor_grua"]:
            L.append("Ascensor/grua: factor adicional x1,3 aplicado sobre la intensidad del motor.")

    if inp["alumbrado_descarga"]:
        L.append("Alumbrado de descarga sin corregir f.d.p.: Ib_calculo se multiplica x1,8 (orientativo).")

    L.append(f"Ib de calculo final = {res['ib_calculo']:.2f} A")
    L.append("")
    L.append(f"Factor de correccion = f_temp x f_agrup x f_capas x f_resist = {res['f_temp']:.3f} x "
              f"{res['f_agrup']:.3f} x {res['f_capas']:.3f} x {res['f_resist']:.3f} = {res['factor_total']:.3f}")
    if res["iz_termica"] is not None:
        L.append(f"Iz = Iz_tabla x factor = {res['iz_termica'] / max(res['factor_total'], 1e-9):.1f} x "
                  f"{res['factor_total']:.3f} = {res['iz_termica']:.2f} A")
        cumple_termico = res["iz_termica"] >= (res["ib_calculo"] / (res["n_paralelo"] if res["necesita_paralelo"] else 1))
        L.append(f"Criterio termico: Iz = {res['iz_termica']:.2f} A >= Ib = {res['ib_calculo']:.2f} A "
                  f"-> {'Cumple' if cumple_termico else 'No cumple'} con S = {res['s_termica']:g} mm2")
    L.append("")

    kappa = res["kappa"]
    L.append(f"Conductividad a temperatura de servicio: kappa = {kappa:.2f} m/(ohm x mm2)")
    k_sist = "2" if sistema == SISTEMA_MONO else "raiz(3)=1,732"
    S = res["seccion_final"] if res["seccion_final"] else res["s_termica"]
    L.append(f"Delta U = {k_sist} x L x Ib x (R x cos(phi) + X x sen(phi)),  R = 1/(kappa x S)")
    if S:
        r = 1.0 / (kappa * S)
        L.append(f"R = 1 / ({kappa:.2f} x {S:g}) = {r:.5f} ohm/m")
        L.append(f"Delta U = {res['e_final']:.2f} V  =  {res['e_final_pct']:.2f} % de {inp['tension']:g} V")
        cumple_du = res["e_final_pct"] <= inp["delta_u_max"]
        L.append(f"Criterio de caida de tension: {res['e_final_pct']:.2f} % <= {inp['delta_u_max']:g} % "
                  f"-> {'Cumple' if cumple_du else 'No cumple'}")
    L.append("")

    if res.get("seccion_neutro"):
        L.append(f"Seccion de neutro: Sf={res['seccion_final']:g} mm2 -> Sn={res['seccion_neutro']:g} mm2 "
                  "(regla REBT / IEC 60364-5-52 punto 524)")
    if res.get("seccion_proteccion"):
        L.append(f"Seccion de proteccion (ITC-BT-18): Sf={res['seccion_final']:g} mm2 -> "
                  f"Sp={res['seccion_proteccion']:g} mm2")

    if res.get("cumple_cc") is not None:
        L.append("")
        k_cc = K_CORTOCIRCUITO[(inp["conductor"], inp["aislamiento"])]
        L.append(f"Cortocircuito: S_min = (Icc x raiz(t)) / k = ({inp['icc_ka']:g}x1000 x "
                  f"raiz({inp['tiempo_s']:g})) / {k_cc} = {res['s_min_cc']:g} mm2")

    return L


# ==============================================================================
# 7. PRESUPUESTO (mediciones x precios unitarios editables) + EXPORT EXCEL
# ==============================================================================

def tabla_precios_cable_defecto() -> pd.DataFrame:
    filas = []
    for s in SECCIONES_NORMALIZADAS:
        filas.append({
            "Sección (mm²)": s,
            "€/m Cobre": PRECIOS_CABLE_COBRE_DEFECTO[s],
            "€/m Aluminio": round(PRECIOS_CABLE_COBRE_DEFECTO[s] * RATIO_PRECIO_ALUMINIO, 2),
        })
    return pd.DataFrame(filas)


def tabla_otros_conceptos_defecto(metodo: str) -> pd.DataFrame:
    filas = [
        {"Concepto": "Canalización (tubo / bandeja según método)", "Unidad": "€/m",
         "Precio unitario (€)": PRECIOS_CANALIZACION_DEFECTO.get(metodo, 2.0)},
        {"Concepto": "Mano de obra de instalación", "Unidad": "€/m",
         "Precio unitario (€)": PRECIO_MANO_OBRA_POR_METRO},
        {"Concepto": "Accesorios y pequeño material (cajas, terminales...)", "Unidad": "% s/materiales",
         "Precio unitario (€)": PORCENTAJE_ACCESORIOS},
    ]
    return pd.DataFrame(filas)


def calcular_presupuesto(inp: dict, res: dict, precios_cable: pd.DataFrame,
                          otros_conceptos: pd.DataFrame) -> tuple:
    """Devuelve (df_mediciones, subtotal_materiales, subtotal_mo, total)."""
    seccion = res["seccion_final"]
    if seccion is None:
        return pd.DataFrame(), 0.0, 0.0, 0.0

    n_paralelo = res["n_paralelo"] if res["necesita_paralelo"] else 1
    longitud = inp["longitud"]
    conductor = inp["conductor"]
    columna_precio = "€/m Cobre" if conductor == "Cobre" else "€/m Aluminio"

    def precio_cable(s):
        fila = precios_cable.loc[precios_cable["Sección (mm²)"] == s]
        if fila.empty:
            return 0.0
        return float(fila.iloc[0][columna_precio])

    n_fases = 3 if inp["sistema"] == SISTEMA_TRI else 1
    filas = []

    metros_fase = longitud * n_fases * n_paralelo
    filas.append({
        "Concepto": f"Cable {conductor} {seccion:g} mm² (fase)", "Unidad": "m",
        "Cantidad": metros_fase, "Precio unitario (€)": precio_cable(seccion),
        "Importe (€)": round(metros_fase * precio_cable(seccion), 2),
    })

    if res.get("seccion_neutro"):
        s_n = res["seccion_neutro"]
        metros_n = longitud * n_paralelo
        filas.append({
            "Concepto": f"Cable {conductor} {s_n:g} mm² (neutro)", "Unidad": "m",
            "Cantidad": metros_n, "Precio unitario (€)": precio_cable(s_n),
            "Importe (€)": round(metros_n * precio_cable(s_n), 2),
        })

    if res.get("seccion_proteccion"):
        s_p = res["seccion_proteccion"]
        metros_p = longitud * n_paralelo
        filas.append({
            "Concepto": f"Cable {conductor} {s_p:g} mm² (protección PE)", "Unidad": "m",
            "Cantidad": metros_p, "Precio unitario (€)": precio_cable(s_p),
            "Importe (€)": round(metros_p * precio_cable(s_p), 2),
        })

    fila_canal = otros_conceptos.loc[otros_conceptos["Concepto"].str.startswith("Canalización")]
    precio_canal = float(fila_canal.iloc[0]["Precio unitario (€)"]) if not fila_canal.empty else 0.0
    filas.append({
        "Concepto": "Canalización (tubo / bandeja)", "Unidad": "m",
        "Cantidad": longitud, "Precio unitario (€)": precio_canal,
        "Importe (€)": round(longitud * precio_canal, 2),
    })

    calibre = res["calibre_magnetotermico"]
    precio_mt = PRECIOS_MAGNETOTERMICO_DEFECTO.get(calibre, 30)
    filas.append({
        "Concepto": f"Interruptor automático {calibre} A", "Unidad": "ud",
        "Cantidad": 1, "Precio unitario (€)": precio_mt, "Importe (€)": precio_mt,
    })
    calibre_dif = min((c for c in PRECIOS_DIFERENCIAL_DEFECTO if c >= calibre),
                       default=max(PRECIOS_DIFERENCIAL_DEFECTO))
    precio_dif = PRECIOS_DIFERENCIAL_DEFECTO[calibre_dif]
    filas.append({
        "Concepto": f"Interruptor diferencial {calibre_dif} A", "Unidad": "ud",
        "Cantidad": 1, "Precio unitario (€)": precio_dif, "Importe (€)": precio_dif,
    })

    subtotal_materiales = sum(f["Importe (€)"] for f in filas)

    fila_acc = otros_conceptos.loc[otros_conceptos["Concepto"].str.startswith("Accesorios")]
    pct_acc = float(fila_acc.iloc[0]["Precio unitario (€)"]) if not fila_acc.empty else 0.0
    importe_acc = round(subtotal_materiales * pct_acc / 100.0, 2)
    filas.append({
        "Concepto": "Accesorios y pequeño material", "Unidad": f"{pct_acc:g}% s/materiales",
        "Cantidad": 1, "Precio unitario (€)": importe_acc, "Importe (€)": importe_acc,
    })

    fila_mo = otros_conceptos.loc[otros_conceptos["Concepto"].str.startswith("Mano de obra")]
    precio_mo = float(fila_mo.iloc[0]["Precio unitario (€)"]) if not fila_mo.empty else 0.0
    importe_mo = round(longitud * precio_mo, 2)
    filas.append({
        "Concepto": "Mano de obra de instalación", "Unidad": "m",
        "Cantidad": longitud, "Precio unitario (€)": precio_mo, "Importe (€)": importe_mo,
    })

    df = pd.DataFrame(filas)
    subtotal_mo = importe_mo
    total = round(df["Importe (€)"].sum(), 2)
    return df, round(subtotal_materiales + importe_acc, 2), subtotal_mo, total


def generar_excel_presupuesto(df_presupuesto: pd.DataFrame, inp: dict, res: dict, total: float,
                                desglose: dict = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Presupuesto"

    azul = "122340"
    cobre = "E8A33D"

    ws.merge_cells("A1:E1")
    ws["A1"] = "PRESUPUESTO — SECCIÓN DE CONDUCTORES (REBT)"
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=azul)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    ws["A2"] = "Circuito:"
    ws["B2"] = inp["tipo_circuito"]
    ws["A3"] = "Sistema:"
    ws["B3"] = f"{inp['sistema']} — {inp['tension']:g} V"
    ws["A4"] = "Sección adoptada:"
    ws["B4"] = f"{res['seccion_final']:g} mm² ({inp['conductor']} / {inp['aislamiento']})"
    ws["A5"] = "Fecha:"
    ws["B5"] = date.today().strftime("%d/%m/%Y")
    for r in range(2, 6):
        ws[f"A{r}"].font = Font(bold=True, color=azul)

    header_row = 7
    columnas = list(df_presupuesto.columns)
    for j, col in enumerate(columnas, start=1):
        c = ws.cell(row=header_row, column=j, value=col)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=azul)
        c.alignment = Alignment(horizontal="center")

    thin = Side(style="thin", color="C9CCD1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for i, row in enumerate(df_presupuesto.itertuples(index=False), start=header_row + 1):
        for j, val in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=val)
            c.border = border
            if columnas[j - 1] in ("Precio unitario (€)", "Importe (€)"):
                c.number_format = '#,##0.00 €'
            if columnas[j - 1] == "Cantidad":
                c.number_format = '#,##0.00'

    fila = header_row + len(df_presupuesto) + 1
    n_col = len(columnas)

    def _fila_resumen(etiqueta, valor, negrita=True, relleno=None):
        nonlocal fila
        c1 = ws.cell(row=fila, column=n_col - 1, value=etiqueta)
        c2 = ws.cell(row=fila, column=n_col, value=valor)
        c2.number_format = '#,##0.00 €'
        if negrita:
            c1.font = Font(bold=True)
            c2.font = Font(bold=True, color=azul)
        if relleno:
            c2.fill = PatternFill("solid", fgColor=relleno)
        fila += 1

    if desglose:
        _fila_resumen("PEM (materiales + M.O.)", desglose["pem"], negrita=False)
        _fila_resumen(f"Amortización ({desglose['pct_amortizacion']:g}%)", desglose["amortizacion"], negrita=False)
        _fila_resumen(f"Beneficio industrial ({desglose['pct_beneficio']:g}%)", desglose["beneficio"], negrita=False)
    _fila_resumen("TOTAL", total, negrita=True, relleno=cobre)

    widths = [42, 14, 12, 16, 14]
    for j, w in enumerate(widths[:len(columnas)], start=1):
        ws.column_dimensions[get_column_letter(j)].width = w

    ws_aviso = wb.create_sheet("Notas")
    ws_aviso["A1"] = ("Los precios unitarios son orientativos (punto de partida editable), no precios de "
                       "mercado en tiempo real. Sustitúyelos por los de tu proveedor antes de presupuestar "
                       "en firme. El precio del cobre fluctúa con su cotización en el LME.")
    ws_aviso["A1"].alignment = Alignment(wrap_text=True)
    ws_aviso.column_dimensions["A"].width = 90
    ws_aviso.row_dimensions[1].height = 60

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ==============================================================================
# 8. ESQUEMA UNIFILAR — vista previa SVG + exportación DXF
# ==============================================================================
# No es "arrastrar con el ratón": Streamlit no soporta de forma fiable drag&drop
# libre sin un componente JS compilado aparte. En su lugar, cada circuito es
# una secuencia ordenada de símbolos que se construye con botones (añadir /
# subir / bajar / quitar), y se previsualiza igual que quedaría el DXF. Es el
# mismo flujo de trabajo que un editor de bloques, sin necesitar un build JS.

_CODIGOS_SIMBOLO = {
    "Interruptor automático (magnetotérmico)": "IA",
    "Interruptor diferencial": "ID",
    "Interruptor general (IGA)": "IGA",
    "Seccionador": "SEC",
    "Fusible": "FUS",
    "Contactor": "KM",
    "Guardamotor": "GM",
    "Transformador": "TRAFO",
    "Motor": "M",
    "Contador de energía": "kWh",
    "Condensador": "C",
    "Puesta a tierra": "PAT",
    "Lámpara / receptor": "REC",
}


def _svg_simbolo(simbolo: str, cx: float, cy: float) -> str:
    codigo = _CODIGOS_SIMBOLO.get(simbolo, "?")
    trazo = "#e8edf4"
    relleno = "#121b2e"
    acento = "#e8a33d"
    p = []
    if simbolo == "Motor":
        p.append(f'<circle cx="{cx}" cy="{cy}" r="14" fill="{relleno}" stroke="{trazo}" stroke-width="1.5"/>')
        p.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="11" fill="{acento}" '
                 f'font-family="monospace">M</text>')
    elif simbolo == "Contador de energía":
        p.append(f'<circle cx="{cx}" cy="{cy}" r="14" fill="{relleno}" stroke="{trazo}" stroke-width="1.5"/>')
        p.append(f'<text x="{cx}" y="{cy+3}" text-anchor="middle" font-size="7.5" fill="{acento}" '
                 f'font-family="monospace">kWh</text>')
    elif simbolo == "Transformador":
        p.append(f'<circle cx="{cx-6}" cy="{cy}" r="10" fill="none" stroke="{trazo}" stroke-width="1.5"/>')
        p.append(f'<circle cx="{cx+6}" cy="{cy}" r="10" fill="none" stroke="{trazo}" stroke-width="1.5"/>')
    elif simbolo == "Condensador":
        p.append(f'<line x1="{cx-4}" y1="{cy-10}" x2="{cx-4}" y2="{cy+10}" stroke="{trazo}" stroke-width="2.2"/>')
        p.append(f'<line x1="{cx+4}" y1="{cy-10}" x2="{cx+4}" y2="{cy+10}" stroke="{trazo}" stroke-width="2.2"/>')
    elif simbolo == "Puesta a tierra":
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy+9}" stroke="{trazo}" stroke-width="1.5"/>')
        for i, w in enumerate([16, 10, 5]):
            yy = cy + 9 + i * 5
            p.append(f'<line x1="{cx-w/2}" y1="{yy}" x2="{cx+w/2}" y2="{yy}" stroke="{trazo}" stroke-width="1.5"/>')
    elif simbolo == "Lámpara / receptor":
        p.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="{trazo}" stroke-width="1.5"/>')
        p.append(f'<line x1="{cx-8}" y1="{cy-8}" x2="{cx+8}" y2="{cy+8}" stroke="{trazo}" stroke-width="1.2"/>')
        p.append(f'<line x1="{cx-8}" y1="{cy+8}" x2="{cx+8}" y2="{cy-8}" stroke="{trazo}" stroke-width="1.2"/>')
    else:
        p.append(f'<rect x="{cx-15}" y="{cy-10}" width="30" height="20" fill="{relleno}" stroke="{trazo}" '
                  f'stroke-width="1.5" rx="2"/>')
        p.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="8" fill="{acento}" '
                 f'font-family="monospace">{codigo}</text>')
    return "\n".join(p)


def construir_svg_unifilar(circuitos: list) -> str:
    margen_izq, paso, fila_alto, y0 = 90, 95, 78, 46
    n = max(len(circuitos), 1)
    max_elems = max((len(c["elementos"]) for c in circuitos), default=0)
    ancho = max(560, margen_izq + paso * (max_elems + 1) + 60)
    alto = y0 + fila_alto * n + 30

    partes = [f'<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" '
              f'style="background:#0b1220;border-radius:6px;width:100%;">']
    y_top = y0 - 18
    y_bottom = y0 + fila_alto * (n - 1) + 18
    partes.append(f'<line x1="{margen_izq}" y1="{y_top}" x2="{margen_izq}" y2="{y_bottom}" '
                  f'stroke="#e8a33d" stroke-width="3"/>')
    partes.append(f'<text x="{margen_izq}" y="{y_top-8}" text-anchor="middle" font-size="8" fill="#e8a33d" '
                  f'font-family="monospace">EMBARRADO</text>')

    for i, circuito in enumerate(circuitos):
        y = y0 + i * fila_alto
        x_fin = margen_izq + paso * (len(circuito["elementos"]) + 1)
        partes.append(f'<text x="{margen_izq+8}" y="{y-14}" font-size="10" fill="#e8edf4" '
                      f'font-family="monospace">{circuito["nombre"]}</text>')
        partes.append(f'<line x1="{margen_izq}" y1="{y}" x2="{x_fin}" y2="{y}" stroke="#8b96a8" '
                      f'stroke-width="1.5"/>')
        for j, simbolo in enumerate(circuito["elementos"]):
            cx = margen_izq + paso * (j + 1)
            partes.append(_svg_simbolo(simbolo, cx, y))
            partes.append(f'<text x="{cx}" y="{y+26}" text-anchor="middle" font-size="7.5" fill="#8b96a8" '
                          f'font-family="monospace">{_CODIGOS_SIMBOLO.get(simbolo, "?")}</text>')
    partes.append("</svg>")
    return "\n".join(partes)


def _dxf_simbolo(msp, simbolo: str, cx: float, cy: float):
    codigo = _CODIGOS_SIMBOLO.get(simbolo, "?")
    if simbolo == "Motor":
        msp.add_circle((cx, cy), radius=7)
        msp.add_text("M", dxfattribs={"height": 4}).set_placement((cx - 2, cy - 2))
    elif simbolo == "Contador de energía":
        msp.add_circle((cx, cy), radius=7)
        msp.add_text("kWh", dxfattribs={"height": 2.5}).set_placement((cx - 4, cy - 1.2))
    elif simbolo == "Transformador":
        msp.add_circle((cx - 3, cy), radius=5)
        msp.add_circle((cx + 3, cy), radius=5)
    elif simbolo == "Condensador":
        msp.add_line((cx - 2, cy - 5), (cx - 2, cy + 5))
        msp.add_line((cx + 2, cy - 5), (cx + 2, cy + 5))
    elif simbolo == "Puesta a tierra":
        msp.add_line((cx, cy), (cx, cy + 4.5))
        for i, w in enumerate([8, 5, 2.5]):
            yy = cy + 4.5 + i * 2.5
            msp.add_line((cx - w / 2, yy), (cx + w / 2, yy))
    elif simbolo == "Lámpara / receptor":
        msp.add_circle((cx, cy), radius=6)
        msp.add_line((cx - 4, cy - 4), (cx + 4, cy + 4))
        msp.add_line((cx - 4, cy + 4), (cx + 4, cy - 4))
    else:
        msp.add_lwpolyline(
            [(cx - 7, cy - 5), (cx + 7, cy - 5), (cx + 7, cy + 5), (cx - 7, cy + 5)], close=True)
        msp.add_text(codigo, dxfattribs={"height": 2.2}).set_placement((cx - 5, cy - 1))


def generar_dxf_unifilar(circuitos: list) -> bytes:
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    margen_izq, paso, fila_alto, y0 = 0.0, 25.0, 20.0, 0.0
    n = max(len(circuitos), 1)

    y_top = y0 + 6
    y_bottom = y0 - fila_alto * (n - 1) - 6
    msp.add_line((margen_izq, y_top), (margen_izq, y_bottom))
    msp.add_text("EMBARRADO", dxfattribs={"height": 2}).set_placement((margen_izq - 2, y_top + 2))

    for i, circuito in enumerate(circuitos):
        y = y0 - i * fila_alto
        x_fin = margen_izq + paso * (len(circuito["elementos"]) + 1)
        msp.add_line((margen_izq, y), (x_fin, y))
        msp.add_text(circuito["nombre"], dxfattribs={"height": 2.2}).set_placement((margen_izq + 1, y + 3))
        for j, simbolo in enumerate(circuito["elementos"]):
            cx = margen_izq + paso * (j + 1)
            _dxf_simbolo(msp, simbolo, cx, y)

    buffer = io.StringIO()
    doc.write(buffer, fmt="asc")
    return buffer.getvalue().encode("utf-8")


# ==============================================================================
# 9. INTERFAZ STREAMLIT
# ==============================================================================

def _fmt_eur(valor: float) -> str:
    """Formatea un importe en estilo español: 1.234,56 €."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TMP").replace(".", ",").replace("TMP", ".")
    return f"{texto} €"


def _render_inputs() -> dict:
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
        metodo = st.selectbox("Método de instalación", METODOS_DISPONIBLES, index=1,
                               help="A1/B1/B2: tubo (empotrado o superficie). C/E: bandeja o superficie. "
                                    "F: bandeja perforada de grandes secciones, típica en industria. "
                                    "D: enterrado. A1 y B2 son estimaciones ancladas a B1 — ver pestaña "
                                    "Metodología.")
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

    return dict(
        tipo_circuito=tipo_circuito, sistema=sistema, tension=tension, modo_entrada=modo_entrada,
        potencia_kw=potencia_kw, cos_phi=cos_phi, intensidad_directa=intensidad_directa,
        conductor=conductor, metodo=metodo, aislamiento=aislamiento, longitud=longitud,
        delta_u_max=delta_u_max, es_motor=es_motor, corrientes_motores=corrientes_motores,
        ascensor_grua=ascensor_grua, alumbrado_descarga=alumbrado_descarga, armonicos=armonicos,
        temp_ambiente=temp_ambiente, usar_kappa_20c=usar_kappa_20c, disposicion=disposicion,
        n_circuitos=n_circuitos, n_capas=n_capas, enterrado=enterrado, resistividad=resistividad,
        verificar_cc=verificar_cc, icc_ka=icc_ka, tiempo_s=tiempo_s,
    )


def _render_resultados(inp: dict, res: dict):
    st.markdown('<p class="section-label">Resultado</p>', unsafe_allow_html=True)

    seccion_final = res["seccion_final"]
    if seccion_final is None:
        st.error("No se ha podido determinar una sección con los parámetros indicados. Revisa los valores.")
        return

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'''<div class="result-card hero">
            <div class="result-label">Sección de fase adoptada</div>
            <div class="result-value">{seccion_final:g} mm²</div>
            <div class="result-sub">{inp['conductor']} · {inp['aislamiento']}</div>
        </div>''', unsafe_allow_html=True)
    with r2:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Ib de cálculo</div>
            <div class="result-value small">{res['ib_calculo']:.2f} A</div>
            <div class="result-sub">Iz tabla: {res['iz_termica']:.1f} A (S={res['s_termica']:g} mm²)</div>
        </div>''', unsafe_allow_html=True)
    with r3:
        cumple_du = res["e_final_pct"] <= inp["delta_u_max"]
        badge = "badge-ok" if cumple_du else "badge-fail"
        texto_badge = "Cumple" if cumple_du else "No cumple"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Caída de tensión</div>
            <div class="result-value small">{res['e_final_pct']:.2f} %</div>
            <div class="result-sub"><span class="{badge}">{texto_badge}</span> · máx {inp['delta_u_max']:g}%</div>
        </div>''', unsafe_allow_html=True)
    with r4:
        neutro_txt = f"{res['seccion_neutro']:g}" if res.get("seccion_neutro") else "—"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Neutro / Protección (mm²)</div>
            <div class="result-value small">{neutro_txt} / {res['seccion_proteccion']:g}</div>
            <div class="result-sub">Interruptor sugerido: {res['calibre_magnetotermico']} A</div>
        </div>''', unsafe_allow_html=True)

    if res["necesita_paralelo"]:
        st.warning(f"La corriente de cálculo supera la capacidad de un único conductor de "
                   f"{max(SECCIONES_NORMALIZADAS):g} mm². Se necesitan **{res['n_paralelo']} conductores en "
                   f"paralelo** de {seccion_final:g} mm² por fase (mismo material, longitud y aislamiento, "
                   "condición del REBT para la puesta en paralelo de conductores).")

    if inp["verificar_cc"]:
        if res["cumple_cc"]:
            st.success(f"✅ Verificación de cortocircuito: {seccion_final:g} mm² soporta térmicamente "
                       f"Icc={inp['icc_ka']:g} kA durante {inp['tiempo_s']:g} s (mínimo requerido: "
                       f"{res['s_min_cc']:g} mm²).")
        else:
            st.error(f"⚠️ Verificación de cortocircuito: {seccion_final:g} mm² NO soporta térmicamente "
                     f"Icc={inp['icc_ka']:g} kA durante {inp['tiempo_s']:g} s. Se requieren ≥ "
                     f"{res['s_min_cc']:g} mm², o una protección con actuación más rápida.")

    st.markdown('<p class="section-label">Secciones normalizadas evaluadas</p>', unsafe_allow_html=True)
    chips = "".join(
        f'<span class="regla-chip{" activa" if s == seccion_final else ""}">{s:g}</span>'
        for s in SECCIONES_NORMALIZADAS
    )
    st.markdown(f'<div class="regla-wrap">{chips}</div>', unsafe_allow_html=True)

    for aviso in res["avisos"]:
        st.info(aviso)

    with st.expander("📋 Ver detalle del cálculo, sección por sección"):
        filas = []
        for s in SECCIONES_NORMALIZADAS:
            base = iz_tabla(s, inp["metodo"], inp["aislamiento"], inp["conductor"], res["n_cargados"])
            if base is None:
                continue
            iz_real = base * res["factor_total"]
            e = caida_tension_voltios(inp["sistema"], res["ib_calculo"], inp["longitud"], s,
                                       inp["cos_phi"], res["kappa"])
            pct = e / inp["tension"] * 100
            filas.append({
                "Sección (mm²)": s,
                "Iz tabla (A)": base,
                "Iz corregida (A)": round(iz_real, 1),
                "Cumple térmico": "✅" if iz_real >= res["ib_calculo"] else "❌",
                "ΔU (%)": round(pct, 2),
                "Cumple ΔU": "✅" if pct <= inp["delta_u_max"] else "❌",
            })
        st.dataframe(pd.DataFrame(filas), width='stretch', hide_index=True)
        st.caption("ΔU aquí calculada con la intensidad total (sin repartir en paralelo), para mostrar por "
                   "qué una sección concreta no bastaría por sí sola.")

    pdf_bytes = generar_pdf_memoria(inp, res)
    st.download_button("⬇️ Descargar memoria de cálculo (PDF)", data=pdf_bytes,
                        file_name="memoria_calculo_cable.pdf", mime="application/pdf")


def _fila_formula(latex_str: str, calculo_md: str):
    """Muestra una fórmula en LaTeX junto a su cálculo con valores sustituidos."""
    col_formula, col_calculo = st.columns([1, 1])
    with col_formula:
        st.latex(latex_str)
    with col_calculo:
        st.markdown(calculo_md)
    st.markdown("<hr style='margin:0.3rem 0;'>", unsafe_allow_html=True)


def _render_formulas(inp: dict, res: dict):
    st.markdown('<p class="section-label">Justificación del cálculo</p>', unsafe_allow_html=True)
    st.caption("Cada fórmula, con el cálculo de este circuito justo al lado. Mismo contenido que incluye "
               "la memoria en PDF.")

    if res["seccion_final"] is None:
        st.warning("Ajusta los datos en la pestaña Calculadora para poder mostrar la justificación.")
        return

    sistema = inp["sistema"]
    cos_phi = inp["cos_phi"]

    st.markdown("##### 1 · Corriente de empleo")
    if inp["modo_entrada"] == "Potencia activa":
        p_w = inp["potencia_kw"] * 1000.0
        if sistema == SISTEMA_MONO:
            _fila_formula(
                r"I_b = \dfrac{P}{V \cdot \cos\varphi}",
                f"`Ib = {p_w:.0f} / ({inp['tension']:g} × {cos_phi:.2f})`  \n**Ib = {res['ib']:.2f} A**")
        else:
            _fila_formula(
                r"I_b = \dfrac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}",
                f"`Ib = {p_w:.0f} / (1,732 × {inp['tension']:g} × {cos_phi:.2f})`  \n**Ib = {res['ib']:.2f} A**")
    else:
        _fila_formula(r"I_b = \text{dato directo}", f"**Ib = {res['ib']:.2f} A** (introducida)")

    if res.get("ib_motor") is not None:
        if len(inp["corrientes_motores"]) == 1:
            _fila_formula(
                r"I_{b,\,motor} = 1{,}25 \cdot I_n",
                f"`Ib = 1,25 × {inp['corrientes_motores'][0]:.2f}`  \n**Ib,motor = {res['ib_motor']:.2f} A**")
        else:
            ordenados = sorted(inp["corrientes_motores"], reverse=True)
            resto = " + ".join(f"{x:.1f}" for x in ordenados[1:])
            _fila_formula(
                r"I_{b,\,motor} = 1{,}25 \cdot I_{n,\,mayor} + \textstyle\sum I_{n,\,resto}",
                f"`Ib = 1,25 × {ordenados[0]:.2f} + ({resto})`  \n**Ib,motor = {res['ib_motor']:.2f} A**")
    if inp["alumbrado_descarga"]:
        _fila_formula(r"I_{b,\,cálculo} = I_b \times 1{,}8",
                       f"Alumbrado de descarga sin corregir f.d.p.  \n**Ib,cálculo = {res['ib_calculo']:.2f} A**")

    st.markdown("##### 2 · Criterio térmico (ITC-BT-19 art. 19)")
    _fila_formula(
        r"I_z = I_{z,\,tabla} \cdot f_{temp} \cdot f_{agrup} \cdot f_{capas} \cdot f_{resist}",
        f"`Iz = {res['iz_termica']/max(res['factor_total'],1e-9):.1f} × {res['f_temp']:.3f} × "
        f"{res['f_agrup']:.3f} × {res['f_capas']:.3f} × {res['f_resist']:.3f}`  \n"
        f"**Iz = {res['iz_termica']:.2f} A**")
    cumple_termico = res["iz_termica"] >= (res["ib_calculo"] / (res["n_paralelo"] if res["necesita_paralelo"] else 1))
    _fila_formula(
        r"I_b \leq I_n \leq I_z",
        f"`{res['ib_calculo']:.2f} A <= Iz={res['iz_termica']:.2f} A`  \n"
        f"**{'✅ Cumple' if cumple_termico else '❌ No cumple'} con S = {res['s_termica']:g} mm²**")

    st.markdown("##### 3 · Criterio de caída de tensión")
    kappa = res["kappa"]
    _fila_formula(
        r"\kappa(T) = \dfrac{\kappa_{20°C}}{1 + \alpha \cdot (T_{servicio} - 20)}",
        f"`kappa = {CONDUCTIVIDAD_20C[inp['conductor']]:g} / (1 + {COEF_TEMP_RESIST[inp['conductor']]:g} × "
        f"({TEMP_SERVICIO[inp['aislamiento']]:g} - 20))`  \n**κ = {kappa:.2f} m/(Ω·mm²)**")
    S = res["seccion_final"]
    r_metro = 1.0 / (kappa * S)
    k_sist_txt = "2" if sistema == SISTEMA_MONO else r"\sqrt{3}"
    _fila_formula(
        rf"\Delta U = {k_sist_txt} \cdot L \cdot I_b \cdot (R\cos\varphi + X\sin\varphi), \; R = \dfrac{{1}}{{\kappa S}}",
        f"`R = 1/({kappa:.2f}×{S:g}) = {r_metro:.5f} Ω/m`  \n`ΔU = {res['e_final']:.2f} V`  \n"
        f"**ΔU = {res['e_final_pct']:.2f} %** (máx {inp['delta_u_max']:g} %)")

    if res.get("seccion_neutro"):
        st.markdown("##### 4 · Sección de neutro y conductor de protección")
        _fila_formula(
            r"S_n = S_f \;(S_f\leq16) \qquad S_n \geq S_f/2 \;(S_f>16,\text{ sin armónicos})",
            f"`Sf = {S:g} mm²` → **Sn = {res['seccion_neutro']:g} mm²**")
    if res.get("seccion_proteccion"):
        _fila_formula(
            r"S_p{=}S_f (S_f{\leq}16) \;\; S_p{=}16 (16{<}S_f{\leq}35) \;\; S_p{=}S_f/2 (S_f{>}35)",
            f"`Sf = {S:g} mm²` → **Sp = {res['seccion_proteccion']:g} mm²**")

    if res.get("cumple_cc") is not None:
        st.markdown("##### 5 · Verificación de cortocircuito")
        k_cc = K_CORTOCIRCUITO[(inp["conductor"], inp["aislamiento"])]
        _fila_formula(
            r"S_{min} = \dfrac{I_{cc} \cdot \sqrt{t}}{k}",
            f"`Smin = ({inp['icc_ka']:g}×1000 × √{inp['tiempo_s']:g}) / {k_cc}`  \n"
            f"**Smin = {res['s_min_cc']:g} mm²** → "
            f"{'✅ Cumple' if res['cumple_cc'] else '❌ No cumple'} con S={S:g} mm²")


def _render_presupuesto(inp: dict, res: dict):
    st.markdown('<p class="section-label">Presupuesto</p>', unsafe_allow_html=True)
    st.caption("Base de precios orientativa y totalmente editable — no son precios de mercado en tiempo "
               "real. Ajusta las tablas a los precios de tu proveedor antes de presupuestar en firme.")

    if res["seccion_final"] is None:
        st.warning("Ajusta los datos en la pestaña Calculadora para poder generar el presupuesto.")
        return

    st.session_state.setdefault("presupuesto_manual", [])
    st.session_state.setdefault("precios_catalogo", {
        cat: {item: precio for item, (unidad, precio) in items.items()}
        for cat, items in CATALOGO_MATERIALES.items()
    })

    with st.expander("💶 Precios unitarios — cable y conceptos ligados al cálculo"):
        st.markdown("**Cable por sección (€/m)**")
        precios_cable = st.data_editor(
            tabla_precios_cable_defecto(), key="precios_cable_editor",
            width='stretch', hide_index=True, num_rows="fixed",
        )
        st.markdown("**Canalización / mano de obra / accesorios**")
        otros_conceptos = st.data_editor(
            tabla_otros_conceptos_defecto(inp["metodo"]), key="otros_conceptos_editor",
            width='stretch', hide_index=True, num_rows="fixed",
        )

    with st.expander("🧰 Catálogo de materiales de instalación (editable) y partidas manuales"):
        st.caption("Añade aquí lo que no sale directamente del cálculo del circuito: mecanismos, cuadros, "
                   "puesta a tierra, luminarias... Edita los precios por categoría y añade partidas con la "
                   "cantidad que necesites.")
        categoria = st.selectbox("Categoría", list(CATALOGO_MATERIALES.keys()), key="cat_manual")
        tabla_cat = pd.DataFrame([
            {"Concepto": item, "Unidad": unidad, "Precio unitario (€)":
                st.session_state["precios_catalogo"][categoria].get(item, precio_defecto)}
            for item, (unidad, precio_defecto) in CATALOGO_MATERIALES[categoria].items()
        ])
        tabla_editada = st.data_editor(tabla_cat, key=f"editor_{categoria}", width='stretch',
                                        hide_index=True, num_rows="fixed")
        for _, fila in tabla_editada.iterrows():
            st.session_state["precios_catalogo"][categoria][fila["Concepto"]] = fila["Precio unitario (€)"]

        ca1, ca2, ca3 = st.columns([2, 1, 1])
        with ca1:
            concepto_sel = st.selectbox("Concepto a añadir", tabla_editada["Concepto"].tolist(), key="concepto_manual")
        with ca2:
            cantidad_sel = st.number_input("Cantidad", min_value=0.1, value=1.0, step=1.0, key="cantidad_manual")
        with ca3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Añadir partida"):
                fila_sel = tabla_editada.loc[tabla_editada["Concepto"] == concepto_sel].iloc[0]
                st.session_state["presupuesto_manual"].append({
                    "Concepto": concepto_sel, "Unidad": fila_sel["Unidad"], "Cantidad": cantidad_sel,
                    "Precio unitario (€)": float(fila_sel["Precio unitario (€)"]),
                    "Importe (€)": round(cantidad_sel * float(fila_sel["Precio unitario (€)"]), 2),
                })

        if st.session_state["presupuesto_manual"]:
            st.markdown("**Partidas manuales añadidas**")
            for i, item in enumerate(st.session_state["presupuesto_manual"]):
                fc1, fc2, fc3 = st.columns([3, 1, 0.4])
                fc1.write(f"{item['Concepto']} — {item['Cantidad']:g} {item['Unidad']}")
                fc2.write(_fmt_eur(item["Importe (€)"]))
                if fc3.button("🗑️", key=f"del_manual_{i}"):
                    st.session_state["presupuesto_manual"].pop(i)
                    st.rerun()

    with st.expander("📈 Beneficio y amortización", expanded=True):
        pb1, pb2 = st.columns(2)
        with pb1:
            porcentaje_beneficio = st.number_input(
                "Beneficio industrial (%)", min_value=0.0, max_value=50.0,
                value=PORCENTAJE_BENEFICIO_DEFECTO, step=0.5)
        with pb2:
            porcentaje_amortizacion = st.number_input(
                "Amortización de medios auxiliares (%)", min_value=0.0, max_value=20.0,
                value=PORCENTAJE_AMORTIZACION_DEFECTO, step=0.5,
                help="Herramientas, equipos de medida, andamios/escaleras... como % sobre el PEM.")

    df_auto, subtotal_mat, subtotal_mo, _ = calcular_presupuesto(inp, res, precios_cable, otros_conceptos)
    if df_auto.empty:
        st.warning("No se ha podido calcular el presupuesto.")
        return

    df_manual = pd.DataFrame(st.session_state["presupuesto_manual"])
    df_completo = pd.concat([df_auto, df_manual], ignore_index=True) if not df_manual.empty else df_auto

    st.markdown("**Mediciones y precios**")
    st.dataframe(df_completo, width='stretch', hide_index=True)

    pem = round(df_completo["Importe (€)"].sum(), 2)
    importe_amortizacion = round(pem * porcentaje_amortizacion / 100.0, 2)
    importe_beneficio = round((pem + importe_amortizacion) * porcentaje_beneficio / 100.0, 2)
    total = round(pem + importe_amortizacion + importe_beneficio, 2)

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">PEM (materiales+M.O.)</div>
            <div class="result-value small">{_fmt_eur(pem)}</div>
        </div>''', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Amortización ({porcentaje_amortizacion:g}%)</div>
            <div class="result-value small">{_fmt_eur(importe_amortizacion)}</div>
        </div>''', unsafe_allow_html=True)
    with p3:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Beneficio industrial ({porcentaje_beneficio:g}%)</div>
            <div class="result-value small">{_fmt_eur(importe_beneficio)}</div>
        </div>''', unsafe_allow_html=True)
    with p4:
        st.markdown(f'''<div class="result-card hero">
            <div class="result-label">Total presupuesto</div>
            <div class="result-value">{_fmt_eur(total)}</div>
        </div>''', unsafe_allow_html=True)

    st.caption("No incluye IVA. Cantidades de cable/canalización/protecciones calculadas automáticamente "
               "sobre el resultado de la Calculadora; el resto son las partidas manuales que hayas añadido.")

    desglose = dict(pem=pem, amortizacion=importe_amortizacion, beneficio=importe_beneficio,
                     pct_amortizacion=porcentaje_amortizacion, pct_beneficio=porcentaje_beneficio)
    excel_bytes = generar_excel_presupuesto(df_completo, inp, res, total, desglose)
    st.download_button("⬇️ Descargar presupuesto (Excel)", data=excel_bytes,
                        file_name="presupuesto_cable.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _render_esquema_unifilar():
    st.markdown('<p class="section-label">Esquema unifilar</p>', unsafe_allow_html=True)
    st.caption(
        "Constructor por bloques: añade símbolos a cada circuito con los botones (no hay arrastre libre "
        "con el ratón — Streamlit no soporta eso de forma fiable sin un componente JS aparte — pero el "
        "resultado de diseño es el mismo). La vista previa es exactamente lo que se exporta a DXF."
    )

    st.session_state.setdefault("circuitos_unifilar", [
        {"nombre": "C1 - Alumbrado", "elementos": ["Interruptor automático (magnetotérmico)",
                                                     "Interruptor diferencial", "Lámpara / receptor"]},
    ])
    circuitos = st.session_state["circuitos_unifilar"]

    nc1, nc2 = st.columns([3, 1])
    with nc1:
        nuevo_nombre = st.text_input("Nombre del nuevo circuito", f"C{len(circuitos)+1} - ",
                                      key="nombre_nuevo_circuito")
    with nc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nuevo circuito"):
            circuitos.append({"nombre": nuevo_nombre, "elementos": []})
            st.rerun()

    for idx, circuito in enumerate(circuitos):
        with st.container(border=True):
            tc1, tc2 = st.columns([4, 0.6])
            tc1.markdown(f"**{circuito['nombre']}**")
            if tc2.button("🗑️", key=f"del_circuito_{idx}", help="Eliminar circuito"):
                circuitos.pop(idx)
                st.rerun()

            ac1, ac2 = st.columns([3, 1])
            with ac1:
                simbolo_sel = st.selectbox("Símbolo", SIMBOLOS_UNIFILAR, key=f"simbolo_sel_{idx}")
            with ac2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Añadir a la línea", key=f"add_simbolo_{idx}"):
                    circuito["elementos"].append(simbolo_sel)
                    st.rerun()

            if circuito["elementos"]:
                for j, elem in enumerate(circuito["elementos"]):
                    ec1, ec2, ec3, ec4 = st.columns([3, 0.5, 0.5, 0.5])
                    ec1.write(f"{j+1}. {elem}")
                    if ec2.button("⬆️", key=f"up_{idx}_{j}") and j > 0:
                        circuito["elementos"][j - 1], circuito["elementos"][j] = \
                            circuito["elementos"][j], circuito["elementos"][j - 1]
                        st.rerun()
                    if ec3.button("⬇️", key=f"down_{idx}_{j}") and j < len(circuito["elementos"]) - 1:
                        circuito["elementos"][j + 1], circuito["elementos"][j] = \
                            circuito["elementos"][j], circuito["elementos"][j + 1]
                        st.rerun()
                    if ec4.button("✖️", key=f"rm_{idx}_{j}"):
                        circuito["elementos"].pop(j)
                        st.rerun()

    st.markdown('<p class="section-label">Vista previa</p>', unsafe_allow_html=True)
    if circuitos:
        st.markdown(construir_svg_unifilar(circuitos), unsafe_allow_html=True)
        dxf_bytes = generar_dxf_unifilar(circuitos)
        st.download_button("⬇️ Descargar esquema (DXF)", data=dxf_bytes, file_name="esquema_unifilar.dxf",
                            mime="application/dxf")
        st.caption("DXF con líneas, símbolos simplificados y etiquetas de texto — abre en AutoCAD/ZWCAD "
                   "para escalar, sustituir por bloques normalizados de tu biblioteca y maquetar el plano.")
    else:
        st.info("Añade al menos un circuito para ver la vista previa.")


def _render_tablas():
    st.markdown('<p class="section-label">Tabla A — Intensidades admisibles (A), cobre, no enterrado, '
                'aire a 40°C</p>', unsafe_allow_html=True)
    filas = []
    for s, datos in TABLA_A_COBRE.items():
        b1, ce, f = datos["B1"], datos["CE"], datos["F"]
        a1 = tuple(round(v * FACTOR_A1_SOBRE_B1, 1) for v in b1)
        b2 = tuple(round(v * FACTOR_B2_SOBRE_B1, 1) for v in b1)
        filas.append({
            "Sección (mm²)": s,
            "A1* 2×PVC": a1[IDX_2PVC], "A1* 2×XLPE": a1[IDX_2XLPE],
            "B1 3×PVC": b1[IDX_3PVC], "B1 2×PVC": b1[IDX_2PVC],
            "B1 3×XLPE": b1[IDX_3XLPE], "B1 2×XLPE": b1[IDX_2XLPE],
            "B2* 2×PVC": b2[IDX_2PVC], "B2* 2×XLPE": b2[IDX_2XLPE],
            "C/E 3×PVC": ce[IDX_3PVC], "C/E 2×PVC": ce[IDX_2PVC],
            "C/E 3×XLPE": ce[IDX_3XLPE], "C/E 2×XLPE": ce[IDX_2XLPE],
            "F (S≥25, XLPE)": f"{f:g}" if f is not None else "—",
        })
    st.dataframe(pd.DataFrame(filas), width='stretch', hide_index=True)
    st.caption("Columnas B1, C/E y F: directas de la Guía-BT-19, Tabla A. Columnas marcadas con * (A1, B2): "
               "estimadas aplicando un ratio a B1, anclado a un valor real verificado en cada caso "
               "(ver pestaña Metodología). Aluminio en instalación NO enterrada: ratio orientativo 0,78 "
               "sobre el valor de cobre mostrado aquí (no se tabula aparte).")

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
        f"""
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

### Métodos de instalación — qué es dato directo y qué es estimación

| Método | Origen de los valores |
|---|---|
| B1 — Tubo empotrado en obra o superficie | **Directo** de la Tabla A, Guía-BT-19 |
| C/E — Bandeja no perforada/perforada, superficie | **Directo** de la Tabla A. La propia Guía-BT-19 indica que C y E comparten columna cuando sus valores son "prácticamente iguales" |
| F — Bandeja perforada, unipolares (S≥25mm², XLPE) | **Directo** de la Tabla A |
| D — Enterrado bajo tubo (XLPE) | **Directo** de la Tabla D, Guía-BT-19 |
| A1 — Tubo empotrado en pared aislante | **Estimado**: A1 = B1 × {FACTOR_A1_SOBRE_B1:g}, ratio anclado a un valor real verificado de forma independiente (A1, 2,5 mm², 2 cargados, PVC = 17,5 A) |
| B2 — Cable multiconductor en tubo | **Estimado**: B2 = B1 × {FACTOR_B2_SOBRE_B1:g}, ratio anclado a un ejercicio resuelto independiente (B2, 25 mm², 2 cargados, PVC = 77 A) |

### Casuística contemplada
- Sistemas monofásico (230 V) y trifásico (400 V).
- 6 métodos de instalación (ver tabla anterior).
- Motores según ITC-BT-47: 125 % para motor único; 125 % del mayor + 100 % del resto para varios motores;
  +30 % adicional en ascensores/grúas.
- Alumbrado de descarga sin corregir el factor de potencia (factor orientativo ×1,8).
- Cargas con armónicos significativos → neutro a sección plena.
- Cobre y aluminio, con la sección mínima de 16 mm² del aluminio en instalación fija (ITC-BT-07) y la
  mínima de la LGA (ITC-BT-14).
- Conductores en paralelo cuando la intensidad supera la capacidad de un único conductor de 300 mm².
- Sección del neutro (mitad de fase cuando aplica) y del conductor de protección (ITC-BT-18).
- Justificación de fórmulas con los valores del cálculo sustituidos (pestaña "Fórmulas").
- Memoria de cálculo en PDF con cajetín, y presupuesto orientativo exportable a Excel.

### Limitaciones conocidas — léelas antes de usar en un proyecto firmado
- **A1 y B2 son estimaciones** derivadas de B1 mediante un ratio anclado a un único valor real cada una;
  no son la columna oficial completa de la Guía-BT-19 para esos métodos. Verifica si tu proyecto depende
  críticamente de ellos.
- Los valores de **aluminio en instalación NO enterrada** son una estimación (ratio 0,78 respecto al
  cobre); la Guía-BT-19 remite a UNE-HD 60364-5-52 para esa combinación.
- El factor de corrección por **resistividad térmica del terreno** es orientativo.
- La caída de tensión usa una reactancia lineal orientativa fija (0,08 Ω/km).
- La verificación de cortocircuito comprueba el criterio **térmico** del conductor, no la coordinación de
  protecciones (curvas, poder de corte, selectividad).
- **Los precios del presupuesto son un punto de partida editable**, no precios de mercado en tiempo real;
  el precio del cobre fluctúa con su cotización.

**En definitiva:** esta herramienta acelera el predimensionado y documenta el criterio seguido, pero no
sustituye la verificación de un técnico competente con la edición vigente de la Guía-BT-19 y el resto de
normativa aplicable antes de firmar un proyecto.
        """
    )


# ==============================================================================
# 9. PUNTO DE ENTRADA
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
                <div><span>Rev.</span><strong>2.0</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_calc, tab_formulas, tab_presu, tab_esquema, tab_tablas, tab_metodo = st.tabs(
        ["🔌 Calculadora", "🧮 Fórmulas", "💰 Presupuesto", "📐 Esquema unifilar",
         "📊 Tablas normativas", "📖 Metodología"]
    )

    with tab_calc:
        inputs = _render_inputs()
        resultado = calcular(inputs)
        _render_resultados(inputs, resultado)

    with tab_formulas:
        _render_formulas(inputs, resultado)

    with tab_presu:
        _render_presupuesto(inputs, resultado)

    with tab_esquema:
        _render_esquema_unifilar()

    with tab_tablas:
        _render_tablas()

    with tab_metodo:
        _render_metodologia()


if __name__ == "__main__":
    main()
