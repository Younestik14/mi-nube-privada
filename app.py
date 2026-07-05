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
# precio base de cada material/mano de obra se aplican estos dos porcentajes
# para obtener el precio de venta (Precio_venta = Precio_base × (1 + %ben + %amort)).
PORCENTAJE_BENEFICIO_DEFECTO = 15.0       # beneficio industrial
PORCENTAJE_AMORTIZACION_DEFECTO = 5.0     # amortización de medios auxiliares / herramientas


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


def _lineas_formulas_fv_texto(inp: dict, res: dict) -> list:
    """Justificación de cálculo del módulo fotovoltaico en texto plano, para
    el Anexo de cálculos (mismo espíritu que _lineas_formulas_texto)."""
    L = []
    L.append(f"Potencia pico = {res['p_pico_kwp']:.2f} kWp  ({res['n_paneles']} paneles de "
              f"{inp['potencia_panel_wp']:g} Wp segun dimensionado)")
    L.append(f"Produccion anual = Ppico x HSP x 365 x PR x (1 - perdidas) = {res['p_pico_kwp']:.2f} x "
              f"{inp['hsp']:g} x 365 x {inp['pr']:.2f} x (1-{inp['perdidas_sombras']:g}/100) = "
              f"{res['produccion_anual_kwh']:,.0f} kWh/anio".replace(",", "."))
    L.append("")
    L.append(f"Configuracion string: {res['n_serie']} paneles serie x {res['n_paralelo']} strings paralelo "
              f"= {res['n_paneles_configurados']} paneles")
    L.append(f"V string en frio = Nserie x Voc x (1 + coef x (25 - Tmin)) = {res['n_serie']} x {inp['voc']:g} "
              f"x (1 + {inp['coef_temp_voc']/100:.4f} x (25-{inp['temp_min']:g})) = {res['v_string_frio']:.1f} V")
    L.append(f"V string en caliente = Nserie x Vmp x (1 + coef x (Tcel-25)) = {res['v_string_caliente']:.1f} V")
    L.append(f"Verificacion ventana MPPT: {inp['vmin_mppt']:g} V <= V string <= {inp['vmax_mppt']:g} V -> "
              f"{'Cumple' if (res['cumple_vmpp_min'] and res['cumple_vmpp_max']) else 'No cumple'}")
    L.append(f"Verificacion tension max. entrada inversor: V string frio ({res['v_string_frio']:.1f} V) <= "
              f"{inp['vmax_entrada_inversor']:g} V -> {'Cumple' if res['cumple_vmax'] else 'No cumple'}")
    L.append("")
    L.append(f"Cableado CC (ITC-BT-40): I diseno = 1,25 x Isc = 1,25 x {inp['isc']:g} = {res['i_diseno_cc']:.2f} A")
    L.append(f"Seccion CC adoptada = {res['s_cc_final']:g} mm2 Cu XLPE  ->  ΔU parcial CC = {res['du_cc_pct']:.2f} %")
    L.append(f"Cableado CA inversor-cuadro: Ib = {res['ib_ca']:.2f} A ; I diseno (125%) = {res['i_diseno_ca']:.2f} A")
    L.append(f"Seccion CA adoptada = {res['s_ca_final']:g} mm2 Cu XLPE  ->  ΔU parcial CA = {res['e_ca_pct']:.2f} %")
    L.append(f"ΔU combinada CC+CA = {res['du_total_pct']:.2f} %  (limite ITC-BT-40: 1,5% entre generador y "
              "punto de interconexion) -> " + ("Cumple" if res["du_total_pct"] <= 1.5 else "No cumple"))
    L.append("")
    if res.get("calibre_fusible_string"):
        L.append(f"Fusible de string sugerido: {res['calibre_fusible_string']} A "
                  f"(criterio orientativo ~1,8 x Isc, UNE-EN 62548)")
    L.append(f"Magnetotermico CA sugerido: {res['calibre_magneto_ca']} A")
    if res.get("ahorro_anual"):
        L.append("")
        L.append(f"Ahorro anual estimado = Produccion x precio_kWh x %autoconsumo = "
                  f"{res['produccion_anual_kwh']:.0f} x {inp['precio_kwh']:.2f} x "
                  f"{inp['pct_autoconsumo']/100:.2f} = {res['ahorro_anual']:.2f} EUR/anio")
        if res.get("payback_anos"):
            L.append(f"Retorno simple = Inversion / Ahorro anual = {inp['inversion_total']:.0f} / "
                      f"{res['ahorro_anual']:.2f} = {res['payback_anos']:.1f} anios")
    return L


def _cajetin_generico(titulo: str, subtitulo: str, datos_proyecto: dict, margin, cajetin_h, AZUL, COBRE, GRIS):
    """Factoría de función de cajetín reutilizable por los distintos documentos
    (MTD, Anexo, Condiciones Generales), con el mismo estilo que la memoria de
    cálculo de la Calculadora de cables."""
    from reportlab.lib.units import cm
    fecha_hoy = date.today().strftime("%d/%m/%Y")

    def _cajetin(c, d):
        from reportlab.lib.pagesizes import A4
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
        c.drawString(margin + 0.35 * cm, top - 0.85 * cm, _pdf_safe(titulo))
        c.setFont("Helvetica", 8.3)
        c.setFillColor(GRIS)
        c.drawString(margin + 0.35 * cm, top - 1.35 * cm, _pdf_safe(subtitulo))
        c.drawString(margin + 0.35 * cm, top - 1.85 * cm,
                      _pdf_safe(f"Titular: {datos_proyecto.get('titular') or '-'}  |  "
                                f"Emplazamiento: {datos_proyecto.get('emplazamiento') or '-'}"))
        campos = [("NORMA", "REBT - ITC-BT"), ("FECHA", fecha_hoy), ("REVISION", "1.0")]
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
        c.drawCentredString(width / 2, margin * 0.45,
                              "Documento generado con la Calculadora de Secciones de Cable. Revisar por un "
                              "tecnico competente antes de su presentacion oficial.")
        c.drawRightString(width - margin, margin * 0.45, f"Pag. {d.page}")
        c.restoreState()

    return _cajetin


def _preparar_doc_pdf(titulo: str, subtitulo: str, datos_proyecto: dict):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm as _cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    AZUL = colors.HexColor("#122340")
    COBRE = colors.HexColor("#b3711f")
    GRIS = colors.HexColor("#5a6472")
    buffer = io.BytesIO()
    margin = 1.6 * _cm
    cajetin_h = 2.6 * _cm
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=margin, rightMargin=margin,
                              topMargin=margin + cajetin_h + 0.3 * _cm, bottomMargin=margin + 0.6 * _cm)
    cajetin = _cajetin_generico(titulo, subtitulo, datos_proyecto, margin, cajetin_h, AZUL, COBRE, GRIS)
    styles = getSampleStyleSheet()
    h2 = ParagraphStyle("h2doc", parent=styles["Heading2"], textColor=AZUL, fontSize=12, spaceBefore=10, spaceAfter=4)
    h3 = ParagraphStyle("h3doc", parent=styles["Heading3"], textColor=COBRE, fontSize=10.5, spaceBefore=8, spaceAfter=3)
    normal = ParagraphStyle("normaldoc", parent=styles["Normal"], fontSize=9.3, leading=13.5)
    return buffer, doc, cajetin, AZUL, colors, h2, h3, normal


def generar_pdf_mtd(datos_proyecto: dict, inputs_cable: dict, resultado_cable: dict,
                     inputs_fv: dict, resultado_fv: dict, total_presupuesto: float) -> bytes:
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "MEMORIA TECNICA DE DISENO (MTD)", "REBT - ITC-BT-04", datos_proyecto)

    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None

    def tabla(datos, colw=(6.5, 9.5)):
        from reportlab.lib.units import cm as _cm
        t = Table(datos, colWidths=[colw[0] * _cm, colw[1] * _cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ccd1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        return t

    story = [Paragraph("1. Datos generales", h2)]
    story.append(tabla([
        ["Campo", "Valor"],
        ["Titular de la instalación", datos_proyecto.get("titular") or "-"],
        ["Emplazamiento", datos_proyecto.get("emplazamiento") or "-"],
        ["Referencia catastral", datos_proyecto.get("referencia_catastral") or "-"],
        ["Uso de la instalación", datos_proyecto.get("uso") or "-"],
    ]))

    story.append(Paragraph("2. Objeto", h2))
    story.append(Paragraph(
        "La presente Memoria Técnica de Diseño (MTD) tiene por objeto describir y justificar las "
        "características técnicas de la instalación eléctrica de baja tensión reseñada, de acuerdo con el "
        "Reglamento Electrotécnico para Baja Tensión (REBT, RD 842/2002) y sus Instrucciones Técnicas "
        "Complementarias, en particular la ITC-BT-04 sobre documentación y puesta en servicio de las "
        "instalaciones.", normal))

    story.append(Paragraph("3. Descripción de la instalación", h2))
    if hay_cable:
        story.append(Paragraph(f"<b>Instalación de baja tensión — {inputs_cable['tipo_circuito']}</b>", h3))
        story.append(tabla([
            ["Concepto", "Valor"],
            ["Sistema", f"{inputs_cable['sistema']} — {inputs_cable['tension']:g} V"],
            ["Conductor / Aislamiento", f"{inputs_cable['conductor']} / {inputs_cable['aislamiento']}"],
            ["Método de instalación", inputs_cable["metodo"]],
            ["Sección de fase adoptada", f"{resultado_cable['seccion_final']:g} mm²"],
            ["Protección (interruptor automático)", f"{resultado_cable['calibre_magnetotermico']} A"],
        ]))
    if hay_fv:
        story.append(Paragraph("<b>Instalación generadora fotovoltaica (RD 244/2019, ITC-BT-40)</b>", h3))
        story.append(tabla([
            ["Concepto", "Valor"],
            ["Modalidad de autoconsumo", inputs_fv["tipo_autoconsumo"]],
            ["Potencia pico instalada", f"{resultado_fv['p_pico_kwp']:.2f} kWp"],
            ["Nº de paneles", f"{resultado_fv['n_paneles_configurados']}"],
            ["Potencia del inversor", f"{inputs_fv['potencia_inversor_kw']:g} kW"],
            ["Producción anual estimada", f"{resultado_fv['produccion_anual_kwh']:,.0f} kWh/año".replace(",", ".")],
        ]))
        umbral = "≤10 kW → Certificado eléctrico" if resultado_fv["p_pico_kwp"] <= 10 else ">10 kW → Proyecto firmado por técnico competente"
        story.append(Paragraph(f"Régimen documental según RD 244/2019: {umbral}.", normal))
    if not hay_cable and not hay_fv:
        story.append(Paragraph("No se ha completado ningún cálculo en las pestañas Calculadora o "
                                "Fotovoltaica de la aplicación. Complétalos antes de generar la MTD "
                                "definitiva.", normal))

    story.append(Paragraph("4. Presupuesto", h2))
    if total_presupuesto:
        story.append(Paragraph(f"El presupuesto de la instalación asciende a la cantidad de "
                                f"<b>{total_presupuesto:,.2f} €</b> ({numero_a_letras_euros(total_presupuesto)}), "
                                "IVA incluido, según el desglose por capítulos que se adjunta en el documento "
                                "de Presupuesto.".replace(",", "."), normal))
    else:
        story.append(Paragraph("No se ha generado presupuesto en la pestaña correspondiente.", normal))

    story.append(Paragraph("5. Documentos que integran el proyecto", h2))
    for linea in ["Memoria Técnica de Diseño (este documento)", "Anexo de cálculos y mediciones",
                  "Condiciones generales de ejecución", "Presupuesto", "Planos (si procede)"]:
        story.append(Paragraph("• " + linea, normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Documento de apoyo generado automáticamente. Antes de su presentación ante el organismo competente, "
        "debe ser revisado, completado y, en su caso, firmado por el instalador autorizado o técnico "
        "competente responsable.", normal))

    doc.build(story, onFirstPage=cajetin, onLaterPages=cajetin)
    return buffer.getvalue()


def generar_pdf_anexo_calculos(datos_proyecto: dict, inputs_cable: dict, resultado_cable: dict,
                                 inputs_fv: dict, resultado_fv: dict, capitulos_presupuesto: list,
                                 pct_beneficio: float, pct_amortizacion: float) -> bytes:
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm as _cm

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "ANEXO DE CALCULOS Y MEDICIONES", "Justificacion tecnica y mediciones", datos_proyecto)

    story = []
    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None

    story.append(Paragraph("1. Cálculos justificativos", h2))
    if hay_cable:
        story.append(Paragraph(f"1.1. Instalación de baja tensión — {inputs_cable['tipo_circuito']}", h3))
        for linea in _lineas_formulas_texto(inputs_cable, resultado_cable):
            if linea:
                story.append(Paragraph(_pdf_safe(linea), normal))
    if hay_fv:
        story.append(Paragraph("1.2. Instalación fotovoltaica", h3))
        for linea in _lineas_formulas_fv_texto(inputs_fv, resultado_fv):
            if linea:
                story.append(Paragraph(_pdf_safe(linea), normal))
    if not hay_cable and not hay_fv:
        story.append(Paragraph("No hay cálculos disponibles: completa la Calculadora de cables y/o el "
                                "módulo Fotovoltaico antes de generar este anexo.", normal))

    story.append(Paragraph("2. Mediciones", h2))
    if capitulos_presupuesto:
        for cap in capitulos_presupuesto:
            if not cap["items"]:
                continue
            story.append(Paragraph(cap["nombre"], h3))
            filas = [["Partida", "Designación", "Ud.", "Cantidad"]]
            for it in cap["items"]:
                filas.append([it.get("partida", "-"), it["designacion"][:70], it["unidades"], f"{it['cantidad']:g}"])
            t = Table(filas, colWidths=[1.6 * _cm, 9.5 * _cm, 1.5 * _cm, 2.4 * _cm])
            t.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ccd1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, 0), AZUL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(t)
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Porcentajes aplicados en el presupuesto: Beneficio industrial {pct_beneficio:g}%, "
                                f"Amortización de medios auxiliares {pct_amortizacion:g}%. El desglose económico "
                                "completo se encuentra en el documento de Presupuesto.", normal))
    else:
        story.append(Paragraph("No se han definido capítulos en la pestaña Presupuesto.", normal))

    doc.build(story, onFirstPage=cajetin, onLaterPages=cajetin)
    return buffer.getvalue()


def generar_pdf_condiciones_generales(datos_proyecto: dict, hay_fv: bool) -> bytes:
    from reportlab.platypus import Paragraph, Spacer

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "CONDICIONES GENERALES DE EJECUCION", "Prescripciones técnicas generales", datos_proyecto)

    story = [Paragraph("1. Normativa de aplicación", h2)]
    story.append(Paragraph(
        "La instalación se ejecutará de acuerdo con el Reglamento Electrotécnico para Baja Tensión (REBT, "
        "RD 842/2002) y sus Instrucciones Técnicas Complementarias (ITC-BT), las normas UNE que le sean de "
        "aplicación, y, en su caso, el Real Decreto 244/2019 de autoconsumo y el Código Técnico de la "
        "Edificación.", normal))

    story.append(Paragraph("2. Materiales", h2))
    for linea in [
        "Todos los materiales y equipos serán de primera calidad y dispondrán del marcado CE cuando "
        "sea de aplicación, cumpliendo las normas UNE correspondientes a cada tipo de material.",
        "Los conductores serán de cobre (salvo justificación expresa de aluminio) con la sección y el "
        "aislamiento indicados en el Anexo de Cálculos.",
        "Los aparatos de mando, maniobra y protección serán adecuados a la intensidad y tensión de la "
        "instalación, y estarán homologados conforme a la normativa vigente.",
    ]:
        story.append(Paragraph("• " + linea, normal))

    story.append(Paragraph("3. Ejecución", h2))
    for linea in [
        "La instalación será ejecutada por instalador autorizado, siguiendo las prescripciones de la "
        "ITC-BT-19 (prescripciones generales), ITC-BT-17 (protección contra sobretensiones y "
        "sobreintensidades) e ITC-BT-24 (protección contra contactos directos e indirectos).",
        "Las canalizaciones se dispondrán de forma que permitan su identificación, mantenimiento e "
        "inspección, evitando su proximidad a otras instalaciones (agua, gas, calefacción) según ITC-BT-20/21.",
        "Se respetarán las distancias y radios de curvatura mínimos de los conductores y canalizaciones "
        "indicados por el fabricante.",
    ]:
        story.append(Paragraph("• " + linea, normal))

    story.append(Paragraph("4. Puesta a tierra y protecciones", h2))
    story.append(Paragraph(
        "La puesta a tierra se ejecutará conforme a la ITC-BT-18, garantizando una resistencia de tierra "
        "compatible con las protecciones diferenciales instaladas (ITC-BT-24). Todas las masas metálicas "
        "accesibles se conectarán al conductor de protección.", normal))

    if hay_fv:
        story.append(Paragraph("5. Condiciones específicas de la instalación fotovoltaica", h2))
        for linea in [
            "La instalación generadora cumplirá la ITC-BT-40 y el Real Decreto 244/2019 sobre condiciones "
            "administrativas, técnicas y económicas del autoconsumo de energía eléctrica.",
            "Los cables de conexión se dimensionarán para una intensidad no inferior al 125% de la intensidad "
            "máxima del generador, con una caída de tensión conjunta (CC+CA) no superior al 1,5% entre el "
            "generador y el punto de interconexión.",
            "Las instalaciones de autoconsumo sin excedentes dispondrán de un mecanismo antivertido conforme "
            "al Anexo I de la ITC-BT-40.",
            "Se dispondrá de un cuadro de mando y protección específico con las protecciones diferenciales "
            "necesarias, y de los dispositivos de desconexión requeridos para las labores de mantenimiento.",
        ]:
            story.append(Paragraph("• " + linea, normal))
        story.append(Paragraph("6. Pruebas y puesta en servicio", h2))
    else:
        story.append(Paragraph("5. Pruebas y puesta en servicio", h2))
    story.append(Paragraph(
        "Antes de la puesta en servicio se realizarán las verificaciones e inspecciones indicadas en la "
        "ITC-BT-05 (verificaciones e inspecciones) y se emitirá el correspondiente Certificado de "
        "Instalación Eléctrica (CIE) o, en su caso, Boletín de instalación, incluyendo medida de resistencia "
        "de aislamiento, continuidad de conductores de protección y resistencia de puesta a tierra.", normal))

    story.append(Paragraph("7. Mantenimiento", h2))
    story.append(Paragraph(
        "El titular de la instalación velará por su correcto mantenimiento, revisando periódicamente el "
        "estado de conductores, protecciones y puesta a tierra, y encargando las inspecciones periódicas "
        "que, en su caso, sean obligatorias según la potencia y el uso de la instalación.", normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Estas condiciones generales son un documento de apoyo estándar; adáptalas a las particularidades "
        "de cada proyecto y a las ordenanzas municipales o autonómicas que puedan resultar de aplicación.",
        normal))

    doc.build(story, onFirstPage=cajetin, onLaterPages=cajetin)
    return buffer.getvalue()



# ==============================================================================
# 7. PRESUPUESTO POR CAPÍTULOS (mismo formato que el excel de referencia:
# Partida/Designación/Unidades/Cantidad/Precio/Importe + panel de Precio
# base/Beneficio/Amortización, y Resumen con IVA e importe en letra) — SIN la
# columna de "Código" que traía el excel original.
# ==============================================================================

def calcular_precio_venta(precio_base: float, pct_beneficio: float, pct_amortizacion: float) -> float:
    """Precio_venta = Precio_base x (1 + %beneficio + %amortizacion), tal y como
    lo calcula la 'Justificación de Precio' del excel de referencia."""
    return round(precio_base * (1 + (pct_beneficio + pct_amortizacion) / 100.0), 4)


def calcular_totales_capitulo(items: list, pct_beneficio: float, pct_amortizacion: float) -> float:
    total = 0.0
    for it in items:
        precio_venta = calcular_precio_venta(it["precio_base"], pct_beneficio, pct_amortizacion)
        total += it["cantidad"] * precio_venta
    return round(total, 2)


# --- Conversión de importes a letras (estilo "Cuatro mil ochocientos treinta
# y nueve euros y setenta céntimos", igual que en el excel de referencia) ---

_UNIDADES_L = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
_DIECI_L = ["diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete",
            "dieciocho", "diecinueve"]
_VEINTI_L = ["veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
             "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_DECENAS_L = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
_CENTENAS_L = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
               "seiscientos", "setecientos", "ochocientos", "novecientos"]


def _dos_digitos_letras(n: int) -> str:
    if n < 10:
        return _UNIDADES_L[n]
    if n < 20:
        return _DIECI_L[n - 10]
    if n < 30:
        return _VEINTI_L[n - 20]
    d, u = divmod(n, 10)
    return _DECENAS_L[d] + (f" y {_UNIDADES_L[u]}" if u else "")


def _tres_digitos_letras(n: int) -> str:
    if n == 0:
        return ""
    if n == 100:
        return "cien"
    c, resto = divmod(n, 100)
    partes = []
    if c:
        partes.append(_CENTENAS_L[c])
    if resto:
        partes.append(_dos_digitos_letras(resto))
    return " ".join(partes)


def _apocope_uno(texto: str) -> str:
    if texto.endswith("veintiuno"):
        return texto[:-3] + "ún"
    if texto.endswith("uno"):
        return texto[:-3] + "un"
    return texto


def numero_entero_a_letras(n: int) -> str:
    if n == 0:
        return "cero"
    partes = []
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    if millones:
        texto_millones = "un millón" if millones == 1 else _tres_digitos_letras(millones) + " millones"
        if miles == 0 and unidades == 0:
            texto_millones += " de"
        partes.append(texto_millones)
    if miles:
        partes.append("mil" if miles == 1 else _tres_digitos_letras(miles) + " mil")
    if unidades:
        partes.append(_tres_digitos_letras(unidades))
    return " ".join(partes)


def numero_a_letras_euros(importe: float) -> str:
    importe = round(importe, 2)
    euros = int(importe)
    centimos = round((importe - euros) * 100)
    texto_euros = _apocope_uno(numero_entero_a_letras(euros))
    resultado = f"{texto_euros.capitalize()} {'euro' if euros == 1 else 'euros'}"
    if centimos:
        texto_cent = _apocope_uno(numero_entero_a_letras(centimos))
        resultado += f" y {texto_cent} {'céntimo' if centimos == 1 else 'céntimos'}"
    return resultado


IVA_DEFECTO_PCT = 21.0


def item_desde_calculo_cable(inp: dict, res: dict) -> list:
    """Traduce el resultado de la Calculadora de cables en líneas de
    presupuesto (acción explícita del usuario: 'importar', nunca automática)."""
    if res.get("seccion_final") is None:
        return []
    seccion = res["seccion_final"]
    n_paralelo = res["n_paralelo"] if res["necesita_paralelo"] else 1
    n_fases = 3 if inp["sistema"] == SISTEMA_TRI else 1
    precio_cable = PRECIOS_CABLE_COBRE_DEFECTO.get(seccion, 5.0) if inp["conductor"] == "Cobre" else \
        round(PRECIOS_CABLE_COBRE_DEFECTO.get(seccion, 5.0) * RATIO_PRECIO_ALUMINIO, 2)
    items = [{
        "designacion": f"Cable {inp['conductor']} {seccion:g} mm² ({inp['aislamiento']}) — fase",
        "unidades": "m", "cantidad": round(inp["longitud"] * n_fases * n_paralelo, 2),
        "precio_base": precio_cable,
    }]
    if res.get("seccion_neutro"):
        items.append({
            "designacion": f"Cable {inp['conductor']} {res['seccion_neutro']:g} mm² — neutro",
            "unidades": "m", "cantidad": round(inp["longitud"] * n_paralelo, 2),
            "precio_base": PRECIOS_CABLE_COBRE_DEFECTO.get(res["seccion_neutro"], 5.0),
        })
    if res.get("seccion_proteccion"):
        items.append({
            "designacion": f"Cable {inp['conductor']} {res['seccion_proteccion']:g} mm² — protección (PE)",
            "unidades": "m", "cantidad": round(inp["longitud"] * n_paralelo, 2),
            "precio_base": PRECIOS_CABLE_COBRE_DEFECTO.get(res["seccion_proteccion"], 5.0),
        })
    items.append({
        "designacion": f"Interruptor automático {res['calibre_magnetotermico']} A",
        "unidades": "ud", "cantidad": 1,
        "precio_base": PRECIOS_MAGNETOTERMICO_DEFECTO.get(res["calibre_magnetotermico"], 30.0),
    })
    items.append({
        "designacion": "Mano de obra de instalación (oficial 1ª electricista)",
        "unidades": "horas", "cantidad": round(max(inp["longitud"] / 10.0, 1.0), 1),
        "precio_base": 33.0,
    })
    return items


def items_desde_calculo_fv(inp: dict, res: dict) -> list:
    """Traduce el resultado del módulo Fotovoltaico en líneas de presupuesto
    (también una acción explícita del usuario, no automática)."""
    items = [
        {"designacion": f"Panel fotovoltaico {inp['potencia_panel_wp']:g} Wp", "unidades": "ud",
         "cantidad": res["n_paneles_configurados"], "precio_base": PRECIOS_FV_DEFECTO["Panel fotovoltaico (según Wp introducido)"][1]},
        {"designacion": f"Inversor {inp['potencia_inversor_kw']:g} kW", "unidades": "ud", "cantidad": 1,
         "precio_base": PRECIOS_FV_DEFECTO["Inversor (según kW introducido)"][1]},
        {"designacion": "Estructura soporte por panel", "unidades": "ud",
         "cantidad": res["n_paneles_configurados"],
         "precio_base": PRECIOS_FV_DEFECTO["Estructura soporte por panel (cubierta inclinada)"][1]},
        {"designacion": f"Cable solar H1Z2Z2-K — tramo CC ({res['s_cc_final']:g} mm²)", "unidades": "m",
         "cantidad": round(inp["longitud_cc"] * 2 * inp["n_strings_paralelo"], 1),
         "precio_base": PRECIOS_FV_DEFECTO["Cable solar H1Z2Z2-K (CC)"][1]},
        {"designacion": f"Cable CA inversor-cuadro ({res['s_ca_final']:g} mm²)", "unidades": "m",
         "cantidad": round(inp["longitud_ca"] * (3 if inp["sistema_ca"] == SISTEMA_TRI else 2), 1),
         "precio_base": PRECIOS_FV_DEFECTO["Cable CA inversor-cuadro (según sección calculada)"][1]},
        {"designacion": "Caja de conexión / string box con fusibles", "unidades": "ud", "cantidad": 1,
         "precio_base": PRECIOS_FV_DEFECTO["Caja de conexión / string box con fusibles"][1]},
        {"designacion": "Protector de sobretensiones DC (DPS tipo 2)", "unidades": "ud", "cantidad": 1,
         "precio_base": PRECIOS_FV_DEFECTO["Protector de sobretensiones DC (DPS tipo 2)"][1]},
        {"designacion": "Interruptor-seccionador CC", "unidades": "ud", "cantidad": 1,
         "precio_base": PRECIOS_FV_DEFECTO["Interruptor-seccionador CC"][1]},
        {"designacion": f"Magnetotérmico CA {res['calibre_magneto_ca']} A (salida inversor)", "unidades": "ud",
         "cantidad": 1, "precio_base": PRECIOS_FV_DEFECTO["Magnetotérmico CA salida inversor"][1]},
        {"designacion": "Diferencial tipo A (salida inversor)", "unidades": "ud", "cantidad": 1,
         "precio_base": PRECIOS_FV_DEFECTO["Diferencial tipo A (salida inversor)"][1]},
        {"designacion": "Mano de obra instalador FV", "unidades": "kWp",
         "cantidad": round(res["p_pico_kwp"], 2),
         "precio_base": PRECIOS_FV_DEFECTO["Mano de obra instalador FV (por kWp)"][1]},
        {"designacion": "Legalización y tramitación (notificación/certificado)", "unidades": "ud",
         "cantidad": 1, "precio_base": PRECIOS_FV_DEFECTO["Legalización y tramitación (notificación/certificado)"][1]},
    ]
    if res.get("calibre_fusible_string"):
        items.append({"designacion": f"Fusible de string {res['calibre_fusible_string']} A (par)", "unidades": "ud",
                       "cantidad": inp["n_strings_paralelo"], "precio_base": 8.0})
    return items


def _sanear_nombre_hoja_excel(nombre: str, existentes: set = None) -> str:
    """Los nombres de hoja de Excel no admiten \\ / ? * [ ] : y tienen un
    límite de 31 caracteres; además deben ser únicos dentro del libro."""
    caracteres_invalidos = '\\/?*[]:'
    limpio = "".join(c for c in nombre if c not in caracteres_invalidos).strip()
    limpio = limpio[:31] if limpio else "Capitulo"
    if existentes is not None:
        base = limpio[:28]
        sufijo = 1
        while limpio in existentes:
            sufijo += 1
            limpio = f"{base} ({sufijo})"
        existentes.add(limpio)
    return limpio


def generar_excel_presupuesto_capitulos(capitulos: list, pct_beneficio: float, pct_amortizacion: float,
                                          pct_iva: float, nombre_proyecto: str = "") -> bytes:
    """Genera un excel con la misma estructura que el de referencia: una hoja
    'Presupuesto' con todos los capítulos seguidos, una hoja por capítulo con
    el desglose de precio (Precio base/Beneficio/Amortización), y una hoja
    'Resumen del presupuesto' con el IVA y el importe final en letra."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    azul = "122340"
    cobre = "E8A33D"
    thin = Side(style="thin", color="C9CCD1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    cols_principales = ["Partida", "Designación", "Unidades", "Cantidad", "Precio", "Importe"]

    wb = Workbook()

    ws_presu = wb.active
    ws_presu.title = "Presupuesto"
    ws_presu.append(["PRESUPUESTO" + (f" — {nombre_proyecto}" if nombre_proyecto else "")])
    ws_presu["A1"].font = Font(bold=True, size=14)
    fila = 3
    for cap in capitulos:
        ws_presu.cell(row=fila, column=1, value=cap["nombre"]).font = Font(bold=True, color=azul)
        fila += 1
        for j, col in enumerate(cols_principales, start=1):
            c = ws_presu.cell(row=fila, column=j, value=col)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=azul)
        fila += 1
        for it in cap["items"]:
            precio_venta = calcular_precio_venta(it["precio_base"], pct_beneficio, pct_amortizacion)
            importe = round(it["cantidad"] * precio_venta, 2)
            valores = [it.get("partida", "-"), it["designacion"], it["unidades"], it["cantidad"], precio_venta, importe]
            for j, val in enumerate(valores, start=1):
                c = ws_presu.cell(row=fila, column=j, value=val)
                c.border = border
                if j in (5, 6):
                    c.number_format = '#,##0.00 €'
            fila += 1
        ws_presu.cell(row=fila, column=4, value="TOTAL").font = Font(bold=True)
        tc = ws_presu.cell(row=fila, column=6, value=calcular_totales_capitulo(cap["items"], pct_beneficio, pct_amortizacion))
        tc.font = Font(bold=True, color=azul)
        tc.number_format = '#,##0.00 €'
        fila += 2
    widths = [10, 55, 10, 11, 13, 13]
    for j, w in enumerate(widths, start=1):
        ws_presu.column_dimensions[get_column_letter(j)].width = w

    nombres_hojas_usados = {"Presupuesto", "Resumen del presupuesto"}
    for cap in capitulos:
        nombre_hoja = _sanear_nombre_hoja_excel(cap["nombre"], nombres_hojas_usados)
        ws = wb.create_sheet(nombre_hoja)
        ws.append([cap["nombre"]])
        ws["A1"].font = Font(bold=True, size=12)
        cabecera = cols_principales + ["", "Precio base", "Beneficio", "Amortización", "Precio"]
        for j, col in enumerate(cabecera, start=1):
            if not col:
                continue
            c = ws.cell(row=3, column=j, value=col)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=azul)
        r = 4
        for it in cap["items"]:
            precio_venta = calcular_precio_venta(it["precio_base"], pct_beneficio, pct_amortizacion)
            importe = round(it["cantidad"] * precio_venta, 2)
            beneficio_importe = round(it["precio_base"] * pct_beneficio / 100.0, 4)
            amortizacion_importe = round(it["precio_base"] * pct_amortizacion / 100.0, 4)
            fila_vals = [it.get("partida", "-"), it["designacion"], it["unidades"], it["cantidad"], precio_venta, importe]
            for j, val in enumerate(fila_vals, start=1):
                c = ws.cell(row=r, column=j, value=val)
                c.border = border
                if j in (5, 6):
                    c.number_format = '#,##0.00 €'
            ws.cell(row=r, column=8, value=it["precio_base"]).number_format = '#,##0.0000 €'
            ws.cell(row=r, column=9, value=beneficio_importe).number_format = '#,##0.0000 €'
            ws.cell(row=r, column=10, value=amortizacion_importe).number_format = '#,##0.0000 €'
            ws.cell(row=r, column=11, value=precio_venta).number_format = '#,##0.0000 €'
            r += 1
        ws.cell(row=r, column=4, value="TOTAL").font = Font(bold=True)
        ws.cell(row=r, column=6, value=calcular_totales_capitulo(cap["items"], pct_beneficio, pct_amortizacion)).number_format = '#,##0.00 €'
        r += 2
        ws.cell(row=r, column=8, value="% Beneficio").font = Font(italic=True)
        ws.cell(row=r, column=9, value="% Amortización").font = Font(italic=True)
        ws.cell(row=r + 1, column=8, value=pct_beneficio / 100.0).number_format = '0%'
        ws.cell(row=r + 1, column=9, value=pct_amortizacion / 100.0).number_format = '0%'
        widths_cap = [10, 55, 10, 11, 13, 13, 3, 13, 12, 13, 13]
        for j, w in enumerate(widths_cap, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w

    ws_r = wb.create_sheet("Resumen del presupuesto")
    ws_r.merge_cells("A1:F1")
    ws_r["A1"] = "RESUMEN DEL PRESUPUESTO"
    ws_r["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws_r["A1"].fill = PatternFill("solid", fgColor=azul)
    ws_r.append([])
    ws_r.append(["Capítulo", "", "", "", "", "Coste parcial"])
    for c in ws_r[3]:
        c.font = Font(bold=True)
    subtotal = 0.0
    for cap in capitulos:
        parcial = calcular_totales_capitulo(cap["items"], pct_beneficio, pct_amortizacion)
        subtotal += parcial
        ws_r.append([cap["nombre"], "", "", "", "", parcial])
        ws_r.cell(row=ws_r.max_row, column=6).number_format = '#,##0.00 €'
    ws_r.append([])
    ws_r.append(["", "", "", "", "Subtotal", round(subtotal, 2)])
    importe_iva = round(subtotal * pct_iva / 100.0, 2)
    ws_r.append(["", "", "", "", f"IVA ({pct_iva:g}%)", importe_iva])
    total = round(subtotal + importe_iva, 2)
    ws_r.append(["", "", "", "", "TOTAL", total])
    fila_total = ws_r.max_row
    for col in (5, 6):
        ws_r.cell(row=fila_total, column=col).font = Font(bold=True, color=azul)
        ws_r.cell(row=fila_total, column=col).fill = PatternFill("solid", fgColor=cobre)
    ws_r.cell(row=fila_total, column=6).number_format = '#,##0.00 €'
    ws_r.append([numero_a_letras_euros(total)])
    ws_r.cell(row=ws_r.max_row, column=1).font = Font(italic=True)
    ws_r.column_dimensions["A"].width = 55
    for col in "BCDE":
        ws_r.column_dimensions[col].width = 13
    ws_r.column_dimensions["F"].width = 15

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ==============================================================================
# 8. INSTALACIONES FOTOVOLTAICAS — módulo de cálculo independiente
# ==============================================================================
# Independiente del todo de la Calculadora de cables: entradas, sesión y motor
# de cálculo propios. Solo comparten las funciones puras de sección de cable
# (iz_tabla, seccion_por_criterio_termico, caida_tension_voltios...) porque son
# la misma física, no porque haya un acoplamiento de datos entre apartados.

ZONAS_CLIMATICAS_HSP = {
    "Norte (Galicia, Asturias, Cantabria, País Vasco)": 3.7,
    "Centro / Meseta (Madrid, Castilla)": 4.4,
    "Mediterráneo / Levante (Cataluña, C. Valenciana, Baleares)": 4.8,
    "Sur (Andalucía, Murcia, Extremadura)": 5.3,
    "Canarias": 5.4,
    "Personalizado (introducir HSP manualmente)": None,
}

TIPO_AUTOCONSUMO_FV = [
    "Sin excedentes",
    "Con excedentes acogido a compensación",
    "Con excedentes no acogido a compensación",
    "Instalación aislada (con batería)",
]

PR_DEFECTO_FV = 0.80

# Módulo y catálogo de referencia orientativos (editables en la propia app).
PANEL_DEFECTO = dict(potencia_wp=450, voc=41.8, isc=13.9, vmp=34.6, imp=13.0, coef_temp_voc=-0.27)
INVERSOR_DEFECTO = dict(potencia_kw=5.0, vmin_mppt=80, vmax_mppt=550, vmax_entrada=600, n_mppt=2)

# Calibres de fusible de string normalizados (A) — criterio orientativo del
# fabricante: In entre 1,5 y 2,4 veces Isc del string (UNE-EN 62548 / IEC 60269-6).
CALIBRES_FUSIBLE_STRING = [2, 4, 6, 8, 10, 12, 15, 16, 20, 25, 32]

PRECIOS_FV_DEFECTO = {
    "Panel fotovoltaico (según Wp introducido)": ("ud", 110.0),
    "Inversor (según kW introducido)": ("ud", 850.0),
    "Estructura soporte por panel (cubierta inclinada)": ("ud", 35.0),
    "Cable solar H1Z2Z2-K (CC)": ("m", 0.95),
    "Cable CA inversor-cuadro (según sección calculada)": ("m", 2.5),
    "Caja de conexión / string box con fusibles": ("ud", 85.0),
    "Protector de sobretensiones DC (DPS tipo 2)": ("ud", 55.0),
    "Interruptor-seccionador CC": ("ud", 45.0),
    "Magnetotérmico CA salida inversor": ("ud", 28.0),
    "Diferencial tipo A (salida inversor)": ("ud", 65.0),
    "Conectores MC4 (par)": ("ud", 3.5),
    "Mano de obra instalador FV (por kWp)": ("kWp", 180.0),
    "Legalización y tramitación (notificación/certificado)": ("ud", 250.0),
}


def calcular_fv(inp: dict) -> dict:
    """Motor de cálculo puro de la instalación fotovoltaica. No depende de la
    Calculadora de cables ni comparte estado con ella."""
    avisos = []

    hsp = inp["hsp"]
    pr = inp["pr"]

    if inp["modo_dimensionado"] == "Por consumo anual (kWh)":
        p_pico_kwp = inp["consumo_anual_kwh"] / max(hsp * 365 * pr, 1e-6)
        n_paneles = math.ceil(p_pico_kwp * 1000 / inp["potencia_panel_wp"])
    elif inp["modo_dimensionado"] == "Por potencia pico deseada (kWp)":
        p_pico_kwp = inp["potencia_pico_deseada"]
        n_paneles = math.ceil(p_pico_kwp * 1000 / inp["potencia_panel_wp"])
    else:  # Por número de paneles
        n_paneles = inp["n_paneles_manual"]
        p_pico_kwp = n_paneles * inp["potencia_panel_wp"] / 1000

    produccion_anual_kwh = p_pico_kwp * hsp * 365 * pr
    perdidas_sombra_pct = inp.get("perdidas_sombras", 0.0)
    produccion_anual_kwh *= (1 - perdidas_sombra_pct / 100.0)

    # --- Configuración del generador (strings) ---
    n_serie = inp["n_paneles_serie"]
    n_paralelo = inp["n_strings_paralelo"]
    n_paneles_configurados = n_serie * n_paralelo

    voc, isc, vmp = inp["voc"], inp["isc"], inp["vmp"]
    coef_v = inp["coef_temp_voc"] / 100.0

    v_string_frio = n_serie * voc * (1 + coef_v * (25 - inp["temp_min"]))
    v_string_caliente = n_serie * vmp * (1 + coef_v * (inp["temp_max_celula"] - 25))
    i_generador = n_paralelo * isc

    cumple_vmax = v_string_frio <= inp["vmax_entrada_inversor"]
    cumple_vmpp_min = v_string_caliente >= inp["vmin_mppt"]
    cumple_vmpp_max = v_string_frio <= inp["vmax_mppt"]
    if not cumple_vmax:
        avisos.append(f"La tensión de string en frío ({v_string_frio:.0f} V) supera la tensión máxima de "
                       f"entrada del inversor ({inp['vmax_entrada_inversor']:.0f} V): reduce paneles en serie.")
    if not cumple_vmpp_min:
        avisos.append(f"La tensión de string en caliente ({v_string_caliente:.0f} V) queda por debajo del "
                       f"mínimo MPPT ({inp['vmin_mppt']:.0f} V): añade paneles en serie o revisa el inversor.")
    if not cumple_vmpp_max:
        avisos.append(f"La tensión de string en frío ({v_string_frio:.0f} V) supera el máximo de la ventana "
                       f"MPPT ({inp['vmax_mppt']:.0f} V).")

    ratio_dc_ac = (p_pico_kwp / inp["potencia_inversor_kw"]) if inp["potencia_inversor_kw"] else None
    if ratio_dc_ac and (ratio_dc_ac < 0.9 or ratio_dc_ac > 1.3):
        avisos.append(f"Ratio DC/AC = {ratio_dc_ac:.2f} fuera del rango habitual (0,9-1,3); revisa la potencia "
                       "del inversor frente a la del generador.")

    # --- Cableado CC (ITC-BT-40: 125% Imax; DeltaU <= 1,5% ENTRE GENERADOR Y
    # PUNTO DE INTERCONEXIÓN, es decir CC+CA combinados, no 1,5% en cada tramo).
    # Se dimensiona cada tramo con un objetivo individual del 1% como margen de
    # trabajo habitual, y se verifica el conjunto contra el 1,5% real. ---
    i_diseno_cc = 1.25 * isc
    kappa_cc = kappa_servicio("Cobre", "XLPE/EPR", usar_20c=False)
    objetivo_parcial_pct = 0.6
    s_cc_termica = None
    for s in SECCIONES_NORMALIZADAS:
        base = iz_tabla(s, METODO_B1, "XLPE/EPR", "Cobre", 2)
        if base is not None and base >= i_diseno_cc:
            s_cc_termica = s
            break
    s_cc_termica = s_cc_termica or max(SECCIONES_NORMALIZADAS)
    s_cc_du = None
    for s in SECCIONES_NORMALIZADAS:
        e = 2 * inp["longitud_cc"] * i_diseno_cc / (kappa_cc * s)
        if e / inp["tension_cc_ref"] * 100 <= objetivo_parcial_pct:
            s_cc_du = s
            break
    s_cc_du = s_cc_du or max(SECCIONES_NORMALIZADAS)
    s_cc_final = max(s_cc_termica, s_cc_du)
    du_cc_pct = (2 * inp["longitud_cc"] * i_diseno_cc / (kappa_cc * s_cc_final)) / inp["tension_cc_ref"] * 100

    # --- Cableado CA (inversor -> cuadro), mismas funciones que la Calculadora
    # de cables pero con datos 100% propios de este módulo. ---
    ib_ca = calcular_intensidad_empleo(inp["sistema_ca"], inp["potencia_inversor_kw"] * 1000.0,
                                        inp["tension_ca"], 1.0)
    i_diseno_ca = 1.25 * ib_ca
    n_cargados_ca = 2 if inp["sistema_ca"] == SISTEMA_MONO else 3
    s_ca_termica, iz_ca, _, _ = seccion_por_criterio_termico(
        i_diseno_ca, METODO_B1, "XLPE/EPR", "Cobre", n_cargados_ca, 1.0)
    kappa_ca = kappa_servicio("Cobre", "XLPE/EPR")
    s_ca_du, e_ca, e_ca_pct = seccion_por_caida_tension(
        inp["sistema_ca"], i_diseno_ca, inp["longitud_ca"], inp["tension_ca"], 1.0, kappa_ca,
        objetivo_parcial_pct, "Cobre")
    candidatos_ca = [s for s in (s_ca_termica, s_ca_du) if s is not None]
    s_ca_final = max(candidatos_ca) if candidatos_ca else None
    if s_ca_final is not None:
        e_ca_real = caida_tension_voltios(inp["sistema_ca"], i_diseno_ca, inp["longitud_ca"], s_ca_final,
                                            1.0, kappa_ca)
        e_ca_pct = e_ca_real / inp["tension_ca"] * 100

    du_total_pct = du_cc_pct + (e_ca_pct if s_ca_final is not None else 0.0)
    if du_total_pct > 1.5:
        avisos.append(f"Caída de tensión combinada CC+CA = {du_total_pct:.2f}% > 1,5% (ITC-BT-40, entre el "
                       "generador y el punto de interconexión): aumenta la sección de algún tramo o reduce "
                       "la longitud.")

    # --- Protecciones ---
    calibre_fusible_string = None
    if n_paralelo >= 2:
        objetivo = 1.8 * isc
        for c in CALIBRES_FUSIBLE_STRING:
            if c >= objetivo:
                calibre_fusible_string = c
                break
        calibre_fusible_string = calibre_fusible_string or CALIBRES_FUSIBLE_STRING[-1]
    calibre_magneto_ca = calibre_magnetotermico_sugerido(i_diseno_ca)

    # --- Económico simplificado ---
    ahorro_anual = produccion_anual_kwh * inp["precio_kwh"] * (inp["pct_autoconsumo"] / 100.0)
    payback_anos = (inp["inversion_total"] / ahorro_anual) if ahorro_anual > 0 and inp["inversion_total"] else None

    return dict(
        p_pico_kwp=p_pico_kwp, n_paneles=n_paneles, produccion_anual_kwh=produccion_anual_kwh,
        n_serie=n_serie, n_paralelo=n_paralelo, n_paneles_configurados=n_paneles_configurados,
        v_string_frio=v_string_frio, v_string_caliente=v_string_caliente, i_generador=i_generador,
        cumple_vmax=cumple_vmax, cumple_vmpp_min=cumple_vmpp_min, cumple_vmpp_max=cumple_vmpp_max,
        ratio_dc_ac=ratio_dc_ac, i_diseno_cc=i_diseno_cc, s_cc_final=s_cc_final, du_cc_pct=du_cc_pct,
        ib_ca=ib_ca, i_diseno_ca=i_diseno_ca, s_ca_final=s_ca_final, iz_ca=iz_ca, e_ca_pct=e_ca_pct,
        du_total_pct=du_total_pct,
        calibre_fusible_string=calibre_fusible_string, calibre_magneto_ca=calibre_magneto_ca,
        ahorro_anual=ahorro_anual, payback_anos=payback_anos, avisos=avisos,
    )


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


def _render_inputs_fv() -> dict:
    st.markdown('<p class="section-label">1 · Dimensionado</p>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1:
        modo_dimensionado = st.selectbox(
            "Punto de partida", ["Por consumo anual (kWh)", "Por potencia pico deseada (kWp)",
                                  "Por número de paneles"])
    consumo_anual_kwh = potencia_pico_deseada = n_paneles_manual = None
    with d2:
        if modo_dimensionado == "Por consumo anual (kWh)":
            consumo_anual_kwh = st.number_input("Consumo anual estimado (kWh)", min_value=1.0, value=4000.0, step=100.0)
        elif modo_dimensionado == "Por potencia pico deseada (kWp)":
            potencia_pico_deseada = st.number_input("Potencia pico deseada (kWp)", min_value=0.1, value=5.0, step=0.5)
        else:
            n_paneles_manual = st.number_input("Número de paneles", min_value=1, value=12, step=1)
    with d3:
        potencia_panel_wp = st.number_input("Potencia unitaria del panel (Wp)", min_value=50.0, value=450.0, step=5.0)

    st.markdown('<p class="section-label">2 · Ubicación y producción</p>', unsafe_allow_html=True)
    u1, u2, u3 = st.columns(3)
    with u1:
        zona = st.selectbox("Zona climática", list(ZONAS_CLIMATICAS_HSP.keys()), index=2,
                             help="HSP orientativo por zona (fuente: IDAE/PVGIS). Para el cálculo definitivo, "
                                  "usa el HSP exacto de PVGIS para tu ubicación.")
        hsp_defecto = ZONAS_CLIMATICAS_HSP[zona] or 4.5
        hsp = st.number_input("HSP (horas de sol pico, h/día)", min_value=1.0, max_value=8.0,
                               value=float(hsp_defecto), step=0.1)
    with u2:
        pr = st.number_input("Performance Ratio (PR)", min_value=0.5, max_value=0.95, value=PR_DEFECTO_FV,
                              step=0.01, help="Típico 0,75-0,85 en instalaciones bien diseñadas.")
        perdidas_sombras = st.number_input("Pérdidas adicionales por sombras/suciedad (%)", min_value=0.0,
                                            max_value=30.0, value=3.0, step=0.5)
    with u3:
        tipo_autoconsumo = st.selectbox("Modalidad (RD 244/2019)", TIPO_AUTOCONSUMO_FV)
        precio_kwh = st.number_input("Precio kWh evitado (€/kWh)", min_value=0.01, value=0.18, step=0.01)

    st.markdown('<p class="section-label">3 · Módulo fotovoltaico (valores de ficha técnica STC)</p>',
                unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        voc = st.number_input("Voc (V)", min_value=1.0, value=PANEL_DEFECTO["voc"], step=0.1)
        isc = st.number_input("Isc (A)", min_value=0.1, value=PANEL_DEFECTO["isc"], step=0.1)
    with m2:
        vmp = st.number_input("Vmp (V)", min_value=1.0, value=PANEL_DEFECTO["vmp"], step=0.1)
        st.number_input("Imp (A)", min_value=0.1, value=PANEL_DEFECTO["imp"], step=0.1, key="imp_fv_display",
                         disabled=True)
    with m3:
        coef_temp_voc = st.number_input("Coef. temperatura Voc (%/°C)", value=PANEL_DEFECTO["coef_temp_voc"],
                                         step=0.01, format="%.2f",
                                         help="Negativo: la tensión SUBE al bajar la temperatura.")
    with m4:
        n_paneles_serie = st.number_input("Paneles en serie por string", min_value=1, value=11, step=1)
        n_strings_paralelo = st.number_input("Strings en paralelo", min_value=1, value=1, step=1)

    st.markdown('<p class="section-label">4 · Inversor y condiciones ambientales</p>', unsafe_allow_html=True)
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        potencia_inversor_kw = st.number_input("Potencia nominal inversor (kW)", min_value=0.1,
                                                value=INVERSOR_DEFECTO["potencia_kw"], step=0.5)
        sistema_ca = st.selectbox("Sistema CA de salida", [SISTEMA_MONO, SISTEMA_TRI])
    with i2:
        vmin_mppt = st.number_input("Tensión mínima MPPT (V)", min_value=1.0,
                                     value=float(INVERSOR_DEFECTO["vmin_mppt"]), step=5.0)
        vmax_mppt = st.number_input("Tensión máxima MPPT (V)", min_value=1.0,
                                     value=float(INVERSOR_DEFECTO["vmax_mppt"]), step=5.0)
    with i3:
        vmax_entrada_inversor = st.number_input("Tensión máxima de entrada (V)", min_value=1.0,
                                                 value=float(INVERSOR_DEFECTO["vmax_entrada"]), step=5.0)
        tension_ca = st.number_input("Tensión de salida CA (V)", min_value=100.0,
                                      value=230.0 if sistema_ca == SISTEMA_MONO else 400.0, step=1.0)
    with i4:
        temp_min = st.number_input("Temperatura mínima histórica (°C)", value=-5.0, step=1.0,
                                    help="Para verificar la tensión de string en frío.")
        temp_max_celula = st.number_input("Temperatura máx. célula en servicio (°C)", value=70.0, step=1.0,
                                           help="Orientativa: temperatura ambiente máxima + 25-30°C.")

    st.markdown('<p class="section-label">5 · Cableado</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        longitud_cc = st.number_input("Longitud de cada string CC (m, ida)", min_value=0.1, value=15.0, step=1.0)
    with c2:
        tension_cc_ref = st.number_input("Tensión CC de referencia para ΔU (V)", min_value=1.0, value=400.0,
                                          step=10.0, help="Orientativa: tensión de string en el punto de máxima potencia.")
    with c3:
        longitud_ca = st.number_input("Longitud CA inversor→cuadro (m)", min_value=0.1, value=10.0, step=1.0)

    with st.expander("💶 Estimación económica (opcional)"):
        e1, e2 = st.columns(2)
        with e1:
            pct_autoconsumo = st.number_input("% de la producción autoconsumida", min_value=0.0, max_value=100.0,
                                               value=65.0, step=5.0)
        with e2:
            inversion_total = st.number_input("Inversión total estimada (€)", min_value=0.0, value=6000.0, step=100.0)

    return dict(
        modo_dimensionado=modo_dimensionado, consumo_anual_kwh=consumo_anual_kwh,
        potencia_pico_deseada=potencia_pico_deseada, n_paneles_manual=n_paneles_manual,
        potencia_panel_wp=potencia_panel_wp, zona=zona, hsp=hsp, pr=pr, perdidas_sombras=perdidas_sombras,
        tipo_autoconsumo=tipo_autoconsumo, precio_kwh=precio_kwh, voc=voc, isc=isc, vmp=vmp,
        coef_temp_voc=coef_temp_voc, n_paneles_serie=n_paneles_serie, n_strings_paralelo=n_strings_paralelo,
        potencia_inversor_kw=potencia_inversor_kw, sistema_ca=sistema_ca, vmin_mppt=vmin_mppt,
        vmax_mppt=vmax_mppt, vmax_entrada_inversor=vmax_entrada_inversor, tension_ca=tension_ca,
        temp_min=temp_min, temp_max_celula=temp_max_celula, longitud_cc=longitud_cc,
        tension_cc_ref=tension_cc_ref, longitud_ca=longitud_ca, pct_autoconsumo=pct_autoconsumo,
        inversion_total=inversion_total,
    )


def _render_resultados_fv(inp: dict, res: dict):
    st.markdown('<p class="section-label">Resultado</p>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'''<div class="result-card hero">
            <div class="result-label">Potencia pico</div>
            <div class="result-value">{res['p_pico_kwp']:.2f} kWp</div>
            <div class="result-sub">{res['n_paneles']} paneles según dimensionado</div>
        </div>''', unsafe_allow_html=True)
    with r2:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Producción anual estimada</div>
            <div class="result-value small">{res['produccion_anual_kwh']:,.0f} kWh/año</div>
            <div class="result-sub">HSP={inp['hsp']:g} h · PR={inp['pr']:.2f}</div>
        </div>'''.replace(",", "."), unsafe_allow_html=True)
    with r3:
        badge_v = "badge-ok" if (res["cumple_vmax"] and res["cumple_vmpp_min"] and res["cumple_vmpp_max"]) else "badge-fail"
        texto_v = "Compatible" if badge_v == "badge-ok" else "Revisar"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">String {res['n_serie']}S{res['n_paralelo']}P</div>
            <div class="result-value small">{res['v_string_frio']:.0f} V (frío)</div>
            <div class="result-sub"><span class="{badge_v}">{texto_v}</span> con el inversor</div>
        </div>''', unsafe_allow_html=True)
    with r4:
        badge_du = "badge-ok" if res["du_total_pct"] <= 1.5 else "badge-fail"
        st.markdown(f'''<div class="result-card">
            <div class="result-label">ΔU CC+CA combinada</div>
            <div class="result-value small">{res['du_total_pct']:.2f} %</div>
            <div class="result-sub"><span class="{badge_du}">{"Cumple" if res["du_total_pct"]<=1.5 else "No cumple"}</span> · máx 1,5% (ITC-BT-40)</div>
        </div>''', unsafe_allow_html=True)

    for aviso in res["avisos"]:
        (st.error if "supera" in aviso or "combinada" in aviso else st.warning)(aviso)

    st.markdown('<p class="section-label">Generador y string</p>', unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Paneles configurados", f"{res['n_paneles_configurados']}")
    g2.metric("V string en caliente", f"{res['v_string_caliente']:.0f} V")
    g3.metric("I generador (Icc total)", f"{res['i_generador']:.1f} A")
    g4.metric("Ratio DC/AC", f"{res['ratio_dc_ac']:.2f}" if res["ratio_dc_ac"] else "—")

    st.markdown('<p class="section-label">Cableado y protecciones</p>', unsafe_allow_html=True)
    cbl = pd.DataFrame([
        {"Tramo": "CC (string → caja de conexión)", "I diseño (125%)": f"{res['i_diseno_cc']:.2f} A",
         "Sección": f"{res['s_cc_final']:g} mm² Cu XLPE", "ΔU parcial": f"{res['du_cc_pct']:.2f} %"},
        {"Tramo": "CA (inversor → cuadro)", "I diseño (125%)": f"{res['i_diseno_ca']:.2f} A",
         "Sección": f"{res['s_ca_final']:g} mm² Cu XLPE" if res["s_ca_final"] else "—",
         "ΔU parcial": f"{res['e_ca_pct']:.2f} %"},
    ])
    st.dataframe(cbl, width='stretch', hide_index=True)

    p1, p2 = st.columns(2)
    p1.metric("Fusible de string sugerido", f"{res['calibre_fusible_string']} A" if res["calibre_fusible_string"] else "No requerido (1 string)")
    p2.metric("Magnetotérmico CA sugerido", f"{res['calibre_magneto_ca']} A")

    if res["ahorro_anual"]:
        st.markdown('<p class="section-label">Estimación económica</p>', unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        e1.metric("Ahorro anual estimado", _fmt_eur(res["ahorro_anual"]))
        e2.metric("Retorno simple (payback)", f"{res['payback_anos']:.1f} años" if res["payback_anos"] else "—")
        st.caption("Estimación simplificada (no considera IPC de la electricidad, degradación del panel ni "
                   "financiación). Para un estudio de viabilidad usa PVGIS y un análisis de flujo de caja.")


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



def _numero_romano(n: int) -> str:
    valores = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    resultado = ""
    for valor, letra in valores:
        while n >= valor:
            resultado += letra
            n -= valor
    return resultado


def _render_presupuesto(inputs_cable: dict, resultado_cable: dict, inputs_fv: dict, resultado_fv: dict):
    st.markdown('<p class="section-label">Presupuesto</p>', unsafe_allow_html=True)
    st.caption("Formato por capítulos (Partida / Designación / Unidades / Cantidad / Precio / Importe), con "
               "desglose de Precio base + Beneficio + Amortización, igual que un presupuesto de instalación "
               "al uso. Los precios son un punto de partida editable, no precios de mercado en tiempo real.")

    st.session_state.setdefault("presupuesto_capitulos", [])
    st.session_state.setdefault("presupuesto_config", {
        "nombre_proyecto": "", "pct_beneficio": PORCENTAJE_BENEFICIO_DEFECTO,
        "pct_amortizacion": PORCENTAJE_AMORTIZACION_DEFECTO, "pct_iva": IVA_DEFECTO_PCT,
    })
    capitulos = st.session_state["presupuesto_capitulos"]
    cfg = st.session_state["presupuesto_config"]

    with st.expander("⚙️ Configuración general", expanded=not capitulos):
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            cfg["nombre_proyecto"] = st.text_input("Nombre del proyecto/instalación", cfg["nombre_proyecto"])
        with cf2:
            cfg["pct_beneficio"] = st.number_input("Beneficio industrial (%)", min_value=0.0, max_value=50.0,
                                                    value=cfg["pct_beneficio"], step=0.5)
        with cf3:
            cfg["pct_amortizacion"] = st.number_input("Amortización medios auxiliares (%)", min_value=0.0,
                                                       max_value=20.0, value=cfg["pct_amortizacion"], step=0.5)
        with cf4:
            cfg["pct_iva"] = st.number_input("IVA (%)", min_value=0.0, max_value=25.0, value=cfg["pct_iva"], step=1.0)

    nc1, nc2 = st.columns([3, 1])
    with nc1:
        nombre_defecto = f"CAPÍTULO {_numero_romano(len(capitulos) + 1)}: "
        nuevo_nombre = st.text_input("Nombre del nuevo capítulo", nombre_defecto, key="nuevo_cap_nombre")
    with nc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nuevo capítulo"):
            capitulos.append({"nombre": nuevo_nombre, "items": []})
            st.rerun()

    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None

    for idx, cap in enumerate(capitulos):
        with st.container(border=True):
            tc1, tc2 = st.columns([5, 0.6])
            tc1.markdown(f"**{cap['nombre']}**")
            if tc2.button("🗑️ Eliminar capítulo", key=f"del_cap_{idx}"):
                capitulos.pop(idx)
                st.rerun()

            ib1, ib2 = st.columns(2)
            with ib1:
                if hay_cable and st.button("📥 Importar de Calculadora de cables", key=f"imp_cable_{idx}"):
                    nuevos = item_desde_calculo_cable(inputs_cable, resultado_cable)
                    for j, it in enumerate(nuevos):
                        it["partida"] = f"{idx + 1}.{len(cap['items']) + j + 1}"
                    cap["items"].extend(nuevos)
                    st.rerun()
            with ib2:
                if hay_fv and st.button("📥 Importar de Fotovoltaica", key=f"imp_fv_{idx}"):
                    nuevos = items_desde_calculo_fv(inputs_fv, resultado_fv)
                    for j, it in enumerate(nuevos):
                        it["partida"] = f"{idx + 1}.{len(cap['items']) + j + 1}"
                    cap["items"].extend(nuevos)
                    st.rerun()

            df_items = pd.DataFrame([
                {"Partida": it.get("partida", "-"), "Designación": it["designacion"], "Unidades": it["unidades"],
                 "Cantidad": it["cantidad"], "Precio base": it["precio_base"]}
                for it in cap["items"]
            ]) if cap["items"] else pd.DataFrame(columns=["Partida", "Designación", "Unidades", "Cantidad", "Precio base"])

            st.caption("Edita, añade o borra filas directamente en la tabla (icono ➕/🗑️ al pasar el ratón).")
            df_editada = st.data_editor(
                df_items, key=f"items_editor_{idx}", num_rows="dynamic", width='stretch', hide_index=True,
                column_config={
                    "Cantidad": st.column_config.NumberColumn(min_value=0.0, step=0.1),
                    "Precio base": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.4f €"),
                },
            )

            nuevos_items = []
            for i, row in df_editada.iterrows():
                designacion = row.get("Designación")
                if not designacion or pd.isna(designacion):
                    continue
                cantidad = row.get("Cantidad")
                precio_base = row.get("Precio base")
                nuevos_items.append({
                    "partida": row.get("Partida") or f"{idx + 1}.{i + 1}",
                    "designacion": designacion,
                    "unidades": row.get("Unidades") or "ud",
                    "cantidad": float(cantidad) if pd.notna(cantidad) else 0.0,
                    "precio_base": float(precio_base) if pd.notna(precio_base) else 0.0,
                })
            cap["items"] = nuevos_items

            if cap["items"]:
                filas_venta = []
                for it in cap["items"]:
                    pv = calcular_precio_venta(it["precio_base"], cfg["pct_beneficio"], cfg["pct_amortizacion"])
                    filas_venta.append({
                        "Partida": it.get("partida", "-"), "Designación": it["designacion"], "Unidades": it["unidades"],
                        "Cantidad": it["cantidad"], "Precio": pv, "Importe": round(it["cantidad"] * pv, 2),
                    })
                st.dataframe(pd.DataFrame(filas_venta), width='stretch', hide_index=True)
                total_cap = calcular_totales_capitulo(cap["items"], cfg["pct_beneficio"], cfg["pct_amortizacion"])
                st.markdown(f"**TOTAL {cap['nombre']}: {_fmt_eur(total_cap)}**")

    if not capitulos:
        st.info("Añade al menos un capítulo para empezar a presupuestar (por ejemplo, uno por cada circuito "
                "o instalación: derivación individual, cuadro de protección, iluminación, fotovoltaica...).")
        return

    st.markdown('<p class="section-label">Resumen del presupuesto</p>', unsafe_allow_html=True)
    filas_resumen = []
    subtotal = 0.0
    for cap in capitulos:
        parcial = calcular_totales_capitulo(cap["items"], cfg["pct_beneficio"], cfg["pct_amortizacion"])
        subtotal += parcial
        filas_resumen.append({"Capítulo": cap["nombre"], "Coste parcial": _fmt_eur(parcial)})
    st.dataframe(pd.DataFrame(filas_resumen), width='stretch', hide_index=True)

    importe_iva = round(subtotal * cfg["pct_iva"] / 100.0, 2)
    total = round(subtotal + importe_iva, 2)

    s1, s2, s3 = st.columns(3)
    s1.markdown(f'''<div class="result-card"><div class="result-label">Subtotal</div>
        <div class="result-value small">{_fmt_eur(subtotal)}</div></div>''', unsafe_allow_html=True)
    s2.markdown(f'''<div class="result-card"><div class="result-label">IVA ({cfg["pct_iva"]:g}%)</div>
        <div class="result-value small">{_fmt_eur(importe_iva)}</div></div>''', unsafe_allow_html=True)
    s3.markdown(f'''<div class="result-card hero"><div class="result-label">TOTAL</div>
        <div class="result-value">{_fmt_eur(total)}</div></div>''', unsafe_allow_html=True)
    st.caption(numero_a_letras_euros(total).capitalize() + ".")

    excel_bytes = generar_excel_presupuesto_capitulos(
        capitulos, cfg["pct_beneficio"], cfg["pct_amortizacion"], cfg["pct_iva"], cfg["nombre_proyecto"])
    st.download_button("⬇️ Descargar presupuesto (Excel, por capítulos)", data=excel_bytes,
                        file_name="presupuesto.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _render_documentacion(inputs_cable: dict, resultado_cable: dict, inputs_fv: dict, resultado_fv: dict):
    st.markdown('<p class="section-label">Documentación</p>', unsafe_allow_html=True)
    st.caption("Genera la Memoria Técnica de Diseño (MTD, ITC-BT-04), el Anexo de Cálculos y Mediciones, y "
               "las Condiciones Generales de ejecución, reuniendo lo que ya tengas calculado en las demás "
               "pestañas. A diferencia de la Calculadora y el módulo Fotovoltaico (independientes entre sí), "
               "estos tres documentos SÍ están pensados para juntar toda la información del proyecto.")

    st.session_state.setdefault("datos_proyecto", {
        "titular": "", "emplazamiento": "", "referencia_catastral": "", "uso": "",
    })
    datos = st.session_state["datos_proyecto"]

    d1, d2 = st.columns(2)
    with d1:
        datos["titular"] = st.text_input("Titular de la instalación", datos["titular"])
        datos["emplazamiento"] = st.text_input("Emplazamiento", datos["emplazamiento"])
    with d2:
        datos["referencia_catastral"] = st.text_input("Referencia catastral (opcional)",
                                                        datos["referencia_catastral"])
        datos["uso"] = st.text_input("Uso de la instalación", datos["uso"],
                                      placeholder="Vivienda unifamiliar, local comercial...")

    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None
    capitulos = st.session_state.get("presupuesto_capitulos", [])
    cfg_presu = st.session_state.get("presupuesto_config", {
        "pct_beneficio": PORCENTAJE_BENEFICIO_DEFECTO, "pct_amortizacion": PORCENTAJE_AMORTIZACION_DEFECTO,
        "pct_iva": IVA_DEFECTO_PCT,
    })

    st.markdown('<p class="section-label">Disponible para incluir</p>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    e1.metric("Cálculo de cable", "Sí" if hay_cable else "No calculado")
    e2.metric("Cálculo fotovoltaico", "Sí" if hay_fv else "No calculado")
    e3.metric("Capítulos de presupuesto", f"{len(capitulos)}")

    subtotal_presupuesto = sum(
        calcular_totales_capitulo(cap["items"], cfg_presu["pct_beneficio"], cfg_presu["pct_amortizacion"])
        for cap in capitulos
    )
    total_presupuesto = subtotal_presupuesto * (1 + cfg_presu["pct_iva"] / 100.0) if capitulos else 0.0

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Memoria Técnica de Diseño**")
        st.caption("Descripción, características técnicas y presupuesto (ITC-BT-04).")
        pdf_mtd = generar_pdf_mtd(datos, inputs_cable, resultado_cable, inputs_fv, resultado_fv,
                                   total_presupuesto)
        st.download_button("⬇️ Descargar MTD (PDF)", data=pdf_mtd, file_name="MTD.pdf",
                            mime="application/pdf")
    with c2:
        st.markdown("**Anexo de Cálculos y Mediciones**")
        st.caption("Justificación técnica completa + mediciones por capítulo.")
        pdf_anexo = generar_pdf_anexo_calculos(datos, inputs_cable, resultado_cable, inputs_fv, resultado_fv,
                                                capitulos, cfg_presu["pct_beneficio"], cfg_presu["pct_amortizacion"])
        st.download_button("⬇️ Descargar Anexo (PDF)", data=pdf_anexo, file_name="anexo_calculos.pdf",
                            mime="application/pdf")
    with c3:
        st.markdown("**Condiciones Generales**")
        st.caption("Prescripciones de ejecución, materiales y puesta en servicio.")
        pdf_cond = generar_pdf_condiciones_generales(datos, hay_fv)
        st.download_button("⬇️ Descargar Condiciones (PDF)", data=pdf_cond, file_name="condiciones_generales.pdf",
                            mime="application/pdf")

    if not hay_cable and not hay_fv:
        st.info("Todavía no hay ningún cálculo hecho: los documentos se generarán igualmente, pero con las "
                "secciones de cálculo vacías. Completa la Calculadora y/o la Fotovoltaica para un contenido "
                "completo.")


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
    st.set_page_config(page_title="Instalaciones Eléctricas · REBT", page_icon="⚡", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="titleblock">
            <div class="titleblock-main">
                <span class="titleblock-eyebrow">Cálculo de instalaciones · Baja tensión</span>
                <h1>Calculadora de Instalaciones Eléctricas</h1>
            </div>
            <div class="titleblock-meta">
                <div><span>Norma</span><strong>REBT · ITC-BT</strong></div>
                <div><span>Módulos</span><strong>Cable · FV · Doc.</strong></div>
                <div><span>Rev.</span><strong>3.0</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_calc, tab_formulas, tab_fv, tab_presu, tab_doc, tab_tablas, tab_metodo = st.tabs(
        ["🔌 Calculadora", "🧮 Fórmulas", "☀️ Fotovoltaica", "💰 Presupuesto",
         "📄 Documentación", "📊 Tablas normativas", "📖 Metodología"]
    )

    with tab_calc:
        inputs_cable = _render_inputs()
        resultado_cable = calcular(inputs_cable)
        _render_resultados(inputs_cable, resultado_cable)

    with tab_formulas:
        _render_formulas(inputs_cable, resultado_cable)

    with tab_fv:
        inputs_fv = _render_inputs_fv()
        resultado_fv = calcular_fv(inputs_fv)
        _render_resultados_fv(inputs_fv, resultado_fv)

    with tab_presu:
        _render_presupuesto(inputs_cable, resultado_cable, inputs_fv, resultado_fv)

    with tab_doc:
        _render_documentacion(inputs_cable, resultado_cable, inputs_fv, resultado_fv)

    with tab_tablas:
        _render_tablas()

    with tab_metodo:
        _render_metodologia()


if __name__ == "__main__":
    main()
