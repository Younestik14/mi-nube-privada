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
    "Cables (por tipo, además del cálculo automático)": {
        "Cable RZ1-K 0,6/1kV 1,5mm² (libre halógenos)": ("m", 0.42),
        "Cable RZ1-K 0,6/1kV 2,5mm²": ("m", 0.58),
        "Cable RZ1-K 0,6/1kV 4mm²": ("m", 0.88),
        "Cable RZ1-K 0,6/1kV 6mm²": ("m", 1.25),
        "Cable RZ1-K 0,6/1kV 10mm²": ("m", 1.95),
        "Cable RZ1-K 0,6/1kV 16mm²": ("m", 2.95),
        "Cable H07V-K 1,5mm² (unipolar, interior tubo)": ("m", 0.28),
        "Cable H07V-K 2,5mm²": ("m", 0.40),
        "Cable ES07Z1-K 1,5mm² (libre halógenos, unipolar)": ("m", 0.35),
        "Cable ES07Z1-K 2,5mm²": ("m", 0.48),
        "Manguera redonda RV-K 3x1,5mm²": ("m", 1.10),
        "Manguera redonda RV-K 3x2,5mm²": ("m", 1.55),
        "Manguera redonda RV-K 5x6mm²": ("m", 4.20),
        "Cable coaxial / datos UTP Cat6": ("m", 0.60),
        "Cable de acometida CU 3x35+16mm² (LGA)": ("m", 12.50),
    },
    "Canalizaciones": {
        "Tubo corrugado empotrar Ø16mm": ("m", 0.55),
        "Tubo corrugado empotrar Ø20mm": ("m", 0.65),
        "Tubo corrugado empotrar Ø25mm": ("m", 0.85),
        "Tubo corrugado empotrar Ø32mm": ("m", 1.10),
        "Tubo corrugado empotrar Ø40mm": ("m", 1.55),
        "Tubo corrugado empotrar Ø50mm": ("m", 2.10),
        "Tubo rígido metálico superficie Ø20mm": ("m", 2.80),
        "Tubo rígido PVC superficie Ø20mm": ("m", 1.60),
        "Tubo rígido PVC superficie Ø32mm": ("m", 2.40),
        "Tubo enterrado TPC doble capa Ø63mm": ("m", 3.20),
        "Tubo enterrado TPC doble capa Ø110mm": ("m", 5.60),
        "Bandeja perforada 100mm": ("m", 6.50),
        "Bandeja perforada 200mm": ("m", 9.80),
        "Bandeja perforada 300mm": ("m", 13.50),
        "Bandeja perforada 400mm": ("m", 17.20),
        "Bandeja no perforada (rejiband) 200mm": ("m", 8.20),
        "Bandeja de varilla (rejilla) 100mm": ("m", 5.40),
        "Canaleta PVC 20x12mm": ("m", 2.10),
        "Canaleta PVC 40x25mm": ("m", 4.30),
        "Canaleta PVC 60x40mm con tabique": ("m", 7.80),
        "Columna/canal de suelo técnico 2 vías": ("m", 22.00),
    },
    "Cajas y mecanismos": {
        "Caja de derivación empotrar 100x100": ("ud", 1.80),
        "Caja de derivación empotrar 150x150": ("ud", 3.20),
        "Caja de derivación estanca IP65 150x110": ("ud", 6.50),
        "Caja de derivación estanca IP65 190x140": ("ud", 9.80),
        "Caja de mecanismo universal": ("ud", 0.60),
        "Interruptor simple (mecanismo + tecla)": ("ud", 8.50),
        "Conmutador": ("ud", 9.50),
        "Cruzamiento (conmutador de cruce)": ("ud", 11.50),
        "Pulsador timbre": ("ud", 7.50),
        "Detector de movimiento/presencia empotrar": ("ud", 24.00),
        "Regulador de intensidad (dimmer)": ("ud", 18.50),
        "Base de enchufe Schuko 16A": ("ud", 8.90),
        "Base de enchufe Schuko con USB": ("ud", 16.50),
        "Base de enchufe estanca IP44 16A": ("ud", 12.50),
        "Base industrial CETAC 16A 2P+T": ("ud", 18.00),
        "Base industrial CETAC 16A 3P+N+T": ("ud", 22.00),
        "Base industrial CETAC 32A 3P+N+T": ("ud", 35.00),
        "Base industrial CETAC 63A 3P+N+T": ("ud", 68.00),
        "Base de cocina/horno 25A 2P+T": ("ud", 9.50),
        "Marco embellecedor 1 elemento": ("ud", 3.20),
        "Marco embellecedor 2-3 elementos": ("ud", 5.50),
    },
    "Protección y maniobra": {
        "PIA (magnetotérmico) 6-10A, curva C": ("ud", 18.00),
        "PIA (magnetotérmico) 16-20A, curva C": ("ud", 19.50),
        "PIA (magnetotérmico) 25-32A, curva C": ("ud", 22.00),
        "PIA (magnetotérmico) 40-50A, curva C": ("ud", 32.00),
        "PIA (magnetotérmico) 63A, curva C": ("ud", 48.00),
        "Interruptor general automático (IGA) 25-40A": ("ud", 65.00),
        "Interruptor general automático (IGA) 63A": ("ud", 95.00),
        "Diferencial tipo AC 25A 30mA": ("ud", 32.00),
        "Diferencial tipo A 25A 30mA": ("ud", 45.00),
        "Diferencial tipo A 40A 30mA": ("ud", 58.00),
        "Diferencial tipo A superinmunizado (Si) 40A": ("ud", 85.00),
        "Diferencial tipo B (para inversores/FV) 40A": ("ud", 210.00),
        "Relé diferencial rearmable + toroidal": ("ud", 145.00),
        "Contactor 25A": ("ud", 38.00),
        "Contactor 40A": ("ud", 58.00),
        "Contactor 63A": ("ud", 95.00),
        "Guardamotor 0,4-6,3A (según ajuste)": ("ud", 55.00),
        "Guardamotor 6-40A (según ajuste)": ("ud", 75.00),
        "Relé térmico": ("ud", 42.00),
        "Seccionador bajo carga 40A": ("ud", 48.00),
        "Seccionador bajo carga 100A": ("ud", 95.00),
        "Base + fusible cilíndrico 10x38": ("ud", 6.50),
        "Fusible NH tamaño 00": ("ud", 12.00),
        "Fusible NH tamaño 1": ("ud", 16.00),
        "Protector de sobretensiones DPS tipo 1+2": ("ud", 140.00),
        "Protector de sobretensiones DPS tipo 2": ("ud", 55.00),
        "Contador de energía monofásico": ("ud", 62.00),
        "Contador de energía trifásico": ("ud", 110.00),
    },
    "Cuadros eléctricos": {
        "Cuadro superficie 12 módulos": ("ud", 28.00),
        "Cuadro superficie 24 módulos": ("ud", 42.00),
        "Cuadro superficie 36 módulos": ("ud", 58.00),
        "Cuadro superficie 48 módulos": ("ud", 72.00),
        "Cuadro empotrar 12 módulos": ("ud", 32.00),
        "Cuadro empotrar 24 módulos": ("ud", 48.00),
        "Cuadro empotrar 48 módulos": ("ud", 78.00),
        "Armario metálico IP65 (industrial), pequeño": ("ud", 145.00),
        "Armario metálico IP65 (industrial), grande": ("ud", 320.00),
        "Embarrado de peine 12 módulos": ("ud", 9.50),
        "Caja General de Protección (CGP)": ("ud", 85.00),
        "Caja de Protección y Medida (CPM)": ("ud", 130.00),
    },
    "Puesta a tierra": {
        "Pica de acero cobreado 1m Ø14mm": ("ud", 9.50),
        "Pica de acero cobreado 2m Ø14mm": ("ud", 14.00),
        "Grapa de conexión pica-cable": ("ud", 3.50),
        "Soldadura aluminotérmica": ("ud", 9.00),
        "Placa de tierra de cobre 500x500mm": ("ud", 48.00),
        "Cable desnudo Cu 16mm² (tierra)": ("m", 2.60),
        "Cable desnudo Cu 35mm² (tierra)": ("m", 4.80),
        "Cable desnudo Cu 50mm² (tierra)": ("m", 6.90),
        "Conductor de protección verde/amarillo (según sección)": ("m", 0.55),
        "Arqueta de registro de tierra 30x30": ("ud", 32.00),
        "Punto de puesta a tierra (caja + borne)": ("ud", 15.00),
        "Borne principal de tierra": ("ud", 18.00),
    },
    "Luminarias": {
        "Downlight LED 8W empotrar": ("ud", 8.90),
        "Downlight LED 12W empotrar": ("ud", 11.50),
        "Downlight LED 18W empotrar": ("ud", 15.90),
        "Pantalla LED 60x60 40W": ("ud", 28.00),
        "Regleta LED estanca 1x18W": ("ud", 16.50),
        "Luminaria estanca IP65 1x36W LED": ("ud", 24.00),
        "Luminaria estanca IP65 2x58W LED": ("ud", 38.00),
        "Aparato autónomo de emergencia LED": ("ud", 26.00),
        "Proyector LED exterior 30W": ("ud", 32.00),
        "Proyector LED exterior 50W": ("ud", 45.00),
        "Proyector LED exterior 100W": ("ud", 78.00),
        "Baliza LED exterior baja altura": ("ud", 34.00),
        "Columna/farola LED exterior completa": ("ud", 220.00),
    },
    "Fotovoltaica (además del cálculo automático)": {
        "Panel fotovoltaico 450Wp": ("ud", 110.00),
        "Panel fotovoltaico 550Wp": ("ud", 135.00),
        "Microinversor (por panel)": ("ud", 145.00),
        "Optimizador de potencia (por panel)": ("ud", 65.00),
        "Estructura coplanar cubierta inclinada (por panel)": ("ud", 35.00),
        "Estructura triangular cubierta plana (por panel)": ("ud", 65.00),
        "Estructura sobre suelo/carport (por panel)": ("ud", 95.00),
        "Conector MC4 (par)": ("ud", 3.50),
        "Batería de litio 5 kWh": ("ud", 2400.00),
        "Batería de litio 10 kWh": ("ud", 4500.00),
        "Cargador de vehículo eléctrico 7,4kW": ("ud", 650.00),
        "Monitorización/gestión de energía (kit)": ("ud", 180.00),
    },
    "Domótica y automatización": {
        "Actuador de persiana KNX": ("ud", 85.00),
        "Actuador de encendido KNX 4 canales": ("ud", 120.00),
        "Termostato/sonda de temperatura KNX": ("ud", 95.00),
        "Pasarela KNX-IP": ("ud", 210.00),
        "Detector crepuscular/fotocélula": ("ud", 22.00),
        "Interruptor horario/programador": ("ud", 28.00),
        "Central de alarma básica": ("ud", 145.00),
        "Detector de humo/CO conectado": ("ud", 38.00),
    },
    "Varios / accesorios": {
        "Prensaestopas M16": ("ud", 0.70),
        "Prensaestopas M20": ("ud", 0.90),
        "Prensaestopas M25": ("ud", 1.20),
        "Prensaestopas M32": ("ud", 1.60),
        "Terminal/puntera tubular (según sección)": ("ud", 0.35),
        "Brida de nylon": ("ud", 0.08),
        "Etiqueta de señalización normalizada": ("ud", 1.20),
        "Regleta de conexión": ("ud", 2.50),
        "Regleta de conexión estanca": ("ud", 4.80),
        "Cinta aislante": ("ud", 1.50),
        "Manguito termorretráctil": ("ud", 0.60),
        "Tapa ciega de mecanismo": ("ud", 1.10),
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
              f"{inp['potencia_panel_wp']:g} Wp segun dimensionado; superficie necesaria = "
              f"{res['superficie_necesaria_m2']:.1f} m2)")
    L.append(f"Perdidas por orientacion/inclinacion (CTE DB-HE5) = 100 x [1,2e-4 x (beta-phi+10)^2 + "
              f"3,5e-5 x alfa^2] , con beta={inp['inclinacion']:g}, phi={inp['latitud']:g}, "
              f"alfa={inp['azimut']:g}  =>  {res['perdidas_orient_pct']:.2f} %")
    L.append(f"PR efectivo = PR_base x (1-perd.orient) x (1-perd.sombras) x eficiencia_inversor = "
              f"{inp['pr']:.2f} x (1-{res['perdidas_orient_pct']:.2f}/100) x "
              f"(1-{inp['perdidas_sombras']:g}/100) x {inp['eficiencia_inversor']/100:.3f} = "
              f"{res['pr_efectivo']:.3f}")
    L.append(f"Produccion anual = Ppico x HSP x 365 x PR_efectivo = {res['p_pico_kwp']:.2f} x "
              f"{inp['hsp']:g} x 365 x {res['pr_efectivo']:.3f} = "
              f"{res['produccion_anual_kwh']:,.0f} kWh/anio".replace(",", "."))
    L.append(f"Produccion a 10 anios (degradacion {inp['degradacion_anual']:g}%/anio) = "
              f"{res['produccion_ano10']:,.0f} kWh/anio".replace(",", "."))
    L.append(f"Produccion a 25 anios = {res['produccion_ano25']:,.0f} kWh/anio".replace(",", "."))
    L.append(f"CO2 evitado = Produccion x factor_red = {res['produccion_anual_kwh']:.0f} x "
              f"{inp.get('factor_co2', FACTOR_CO2_RED_DEFECTO):.2f} = "
              f"{res['co2_evitado_kg_ano']:.0f} kg CO2/anio ({res['co2_evitado_kg_ano']/1000:.2f} t/anio)")
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
        L.append(f"Fusible de string sugerido: {res['calibre_fusible_string']} A / "
                  f"{res.get('tension_fusible_string','-')} V (criterio orientativo ~1,8 x Isc, tension >= "
                  f"V string frio; UNE-EN 62548)")
    L.append(f"Magnetotermico CA sugerido: {res['calibre_magneto_ca']} A")
    if res.get("capacidad_bateria_kwh"):
        L.append("")
        L.append(f"Bateria: Capacidad = (consumo_diario x dias_autonomia) / prof_descarga = "
                  f"({inp.get('consumo_diario_bateria_kwh',0):.2f} x {inp.get('autonomia_dias',0):g}) / "
                  f"({inp.get('profundidad_descarga',80):g}/100) = {res['capacidad_bateria_kwh']:.1f} kWh")
    if res.get("ahorro_anual"):
        L.append("")
        L.append(f"Energia autoconsumida = Produccion x %autoconsumo = {res['produccion_anual_kwh']:.0f} x "
                  f"{inp['pct_autoconsumo']/100:.2f} = {res['energia_autoconsumida']:.0f} kWh/anio")
        L.append(f"Ahorro por autoconsumo = {res['energia_autoconsumida']:.0f} x {inp['precio_kwh']:.2f} = "
                  f"{res['ahorro_autoconsumo']:.2f} EUR/anio")
        if res["ingreso_excedentes"]:
            L.append(f"Ingreso por excedentes compensados = {res['energia_excedente']:.0f} x "
                      f"{inp.get('precio_compensacion', PRECIO_COMPENSACION_DEFECTO):.2f} = "
                      f"{res['ingreso_excedentes']:.2f} EUR/anio")
        L.append(f"Ahorro anual total = {res['ahorro_anual']:.2f} EUR/anio")
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
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "MEMORIA TECNICA DE DISENO (MTD)", "REBT - ITC-BT-04", datos_proyecto)

    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None
    d = datos_proyecto

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

    story = []

    # ---------------------------------------------------------------- A/B/C
    story.append(Paragraph("A. Datos del titular", h2))
    story.append(tabla([
        ["Campo", "Valor"],
        ["Titular de la instalación (nombre o razón social)", d.get("titular") or "-"],
        ["NIF / CIF", d.get("nif_titular") or "-"],
    ]))

    story.append(Paragraph("B. Instalador autorizado / técnico competente", h2))
    story.append(tabla([
        ["Campo", "Valor"],
        ["Nombre", d.get("instalador") or "-"],
        ["NIF", d.get("nif_instalador") or "-"],
        ["Nº de autorización / colegiado", d.get("n_autorizacion") or "-"],
        ["Categoría", d.get("categoria_instalador") or "-"],
    ]))
    story.append(Paragraph(
        "El instalador autorizado para la categoría de la instalación correspondiente, o el técnico "
        "titulado competente que suscriba esta Memoria, es directamente responsable de que la misma se "
        "adapte a las exigencias reglamentarias vigentes (ITC-BT-04).", normal))

    story.append(Paragraph("C. Datos generales de la instalación", h2))
    story.append(tabla([
        ["Campo", "Valor"],
        ["Emplazamiento", d.get("emplazamiento") or "-"],
        ["Referencia catastral", d.get("referencia_catastral") or "-"],
        ["Uso al que se destina", d.get("uso") or "-"],
        ["Superficie", (d.get("superficie") or "-") + (" m²" if d.get("superficie") else "")],
        ["Tipo de actuación", d.get("tipo_instalacion") or "-"],
    ]))

    # ---------------------------------------------------------------- D. Memoria Descriptiva
    story.append(Paragraph("D. Memoria descriptiva", h2))

    story.append(Paragraph("D.1 Objeto y normativa de aplicación", h3))
    story.append(Paragraph(
        "La presente Memoria Técnica de Diseño (MTD) tiene por objeto describir y justificar las "
        "características técnicas de la instalación eléctrica de baja tensión reseñada, así como servir de "
        "base para su tramitación administrativa y puesta en servicio, de acuerdo con el Reglamento "
        "Electrotécnico para Baja Tensión (REBT, aprobado por Real Decreto 842/2002) y sus Instrucciones "
        "Técnicas Complementarias (ITC-BT), en particular la ITC-BT-04 relativa a la documentación y puesta "
        "en servicio de las instalaciones. Esta MTD es válida para instalaciones de las características "
        "recogidas en el apartado 3 de la ITC-BT-04 que no requieren de Proyecto firmado por técnico "
        "titulado competente.", normal))

    if hay_cable:
        story.append(Paragraph("D.2 Instalación de baja tensión calculada", h3))
        story.append(Paragraph(f"Circuito de referencia: <b>{inputs_cable['tipo_circuito']}</b>.", normal))
        story.append(tabla([
            ["Concepto", "Valor"],
            ["Sistema", f"{inputs_cable['sistema']} — {inputs_cable['tension']:g} V"],
            ["Conductor / Aislamiento", f"{inputs_cable['conductor']} / {inputs_cable['aislamiento']}"],
            ["Método de instalación (canalización)", inputs_cable["metodo"]],
            ["Longitud del circuito", f"{inputs_cable['longitud']:g} m"],
            ["Sección de fase adoptada", f"{resultado_cable['seccion_final']:g} mm²"],
            ["Sección de neutro", f"{resultado_cable['seccion_neutro']:g} mm²" if resultado_cable.get("seccion_neutro") else "—"],
            ["Sección de protección (PE)", f"{resultado_cable['seccion_proteccion']:g} mm²" if resultado_cable.get("seccion_proteccion") else "—"],
            ["Protección (interruptor automático)", f"{resultado_cable['calibre_magnetotermico']} A"],
            ["Caída de tensión", f"{resultado_cable['e_final_pct']:.2f} % (máx. {inputs_cable['delta_u_max']:g} %)"],
        ]))
        story.append(Paragraph(
            "Los dispositivos generales e individuales de mando y protección se han seleccionado conforme a "
            "la ITC-BT-17 (protección contra sobreintensidades) y la ITC-BT-24 (protección contra contactos "
            "directos e indirectos), garantizando la selectividad y el poder de corte necesarios frente a la "
            "intensidad de cortocircuito prevista en el punto de instalación.", normal))
    else:
        story.append(Paragraph("D.2 Instalación de baja tensión", h3))
        story.append(Paragraph("No se ha completado ningún cálculo de circuito en la pestaña Calculadora; "
                                "esta sección se completará cuando se disponga de esos datos.", normal))

    story.append(Paragraph("D.3 Cuadro general de mando y protección", h3))
    story.append(Paragraph(
        "El cuadro general de mando y protección aloja, como mínimo: un interruptor general automático "
        "(IGA) de corte omnipolar, un interruptor diferencial general (o varios, según la previsión de "
        "cargas) y los interruptores automáticos individuales de cada circuito derivado, coordinados entre "
        "sí para garantizar la selectividad. Se recomienda la instalación de un dispositivo de protección "
        "contra sobretensiones (DPS) en cabecera cuando la acometida sea aérea o exista riesgo de "
        "sobretensiones de origen atmosférico (ITC-BT-23).", normal))

    story.append(Paragraph("D.4 Instalación interior. Canalizaciones", h3))
    metodo_txt = inputs_cable.get("metodo", "") if hay_cable else ""
    story.append(Paragraph(
        f"El sistema de canalización empleado se corresponde con el tipo {metodo_txt or '[a determinar]'} "
        "según la clasificación de la ITC-BT-19 y la norma UNE-HD 60364-5-52, seleccionado en función de "
        "las influencias externas del emplazamiento (humedad, temperatura, riesgo mecánico) conforme a la "
        "clasificación de la norma UNE 20460-3.", normal))

    story.append(Paragraph("D.5 Puesta a tierra", h3))
    story.append(Paragraph(
        "La puesta a tierra de la instalación se ejecutará conforme a la ITC-BT-18, mediante electrodo(s) "
        "(picas y/o conductor enterrado) conectado al borne principal de tierra, del que partirá el "
        "conductor de protección hacia todas las masas metálicas de la instalación. La resistencia de tierra "
        "resultante será compatible con la sensibilidad de las protecciones diferenciales instaladas, de "
        "forma que la tensión de contacto no supere los límites de seguridad de la ITC-BT-24.", normal))

    if hay_fv:
        story.append(Paragraph("D.6 Instalación generadora fotovoltaica", h3))
        story.append(tabla([
            ["Concepto", "Valor"],
            ["Modalidad de autoconsumo (RD 244/2019)", inputs_fv["tipo_autoconsumo"]],
            ["Potencia pico instalada", f"{resultado_fv['p_pico_kwp']:.2f} kWp"],
            ["Nº de paneles / configuración", f"{resultado_fv['n_paneles_configurados']} ({resultado_fv['n_serie']}S{resultado_fv['n_paralelo']}P)"],
            ["Potencia del inversor", f"{inputs_fv['potencia_inversor_kw']:g} kW"],
            ["Sección CC / CA", f"{resultado_fv['s_cc_final']:g} mm² / {resultado_fv['s_ca_final']:g} mm²"],
            ["Producción anual estimada", f"{resultado_fv['produccion_anual_kwh']:,.0f} kWh/año".replace(",", ".")],
            ["CO₂ evitado estimado", f"{resultado_fv['co2_evitado_kg_ano']/1000:.2f} t/año"],
        ]))
        umbral = ("≤10 kW → Certificado eléctrico firmado por instalador autorizado"
                  if resultado_fv["p_pico_kwp"] <= 10 else
                  ">10 kW → Proyecto firmado por técnico competente")
        story.append(Paragraph(f"Régimen documental aplicable según RD 244/2019: {umbral}. La conexión se "
                                "realiza a través de un cuadro de mando y protección específico dotado de "
                                "las protecciones diferenciales necesarias, y de un mecanismo antivertido si "
                                "la modalidad es sin excedentes, conforme al Anexo I de la ITC-BT-40.", normal))

    story.append(Paragraph("D.7 Influencias externas", h3))
    story.append(Paragraph(
        "Salvo indicación expresa en contrario, se considera que el emplazamiento presenta condiciones "
        "ambientales normales (AD1, AA4, BA1 según UNE 20460-3), sin riesgo de incendio ni explosión, por lo "
        "que no son de aplicación las prescripciones adicionales de la ITC-BT-29 para locales de "
        "características especiales.", normal))

    # ---------------------------------------------------------------- E. Memoria Justificativa
    story.append(PageBreak())
    story.append(Paragraph("E. Memoria justificativa (resumen de cálculos)", h2))
    story.append(Paragraph(
        "El detalle completo de las fórmulas y valores empleados para justificar las secciones, "
        "protecciones y caídas de tensión se recoge en el Anexo de Cálculos y Mediciones, documento que "
        "forma parte integrante de esta Memoria. A continuación se resume el resultado:", normal))
    filas_resumen = [["Parte de la instalación", "Potencia (kW)", "Longitud (m)", "Sección (mm²)", "ΔU (%)"]]
    if hay_cable:
        filas_resumen.append([
            inputs_cable["tipo_circuito"][:28],
            f"{inputs_cable['potencia_kw']:.2f}" if inputs_cable.get("potencia_kw") else "—",
            f"{inputs_cable['longitud']:g}", f"{resultado_cable['seccion_final']:g}",
            f"{resultado_cable['e_final_pct']:.2f}",
        ])
    if hay_fv:
        filas_resumen.append([
            "Generador FV (tramo CC)", f"{resultado_fv['p_pico_kwp']:.2f}", f"{inputs_fv['longitud_cc']:g}",
            f"{resultado_fv['s_cc_final']:g}", f"{resultado_fv['du_cc_pct']:.2f}",
        ])
        filas_resumen.append([
            "Generador FV (tramo CA)", f"{inputs_fv['potencia_inversor_kw']:g}", f"{inputs_fv['longitud_ca']:g}",
            f"{resultado_fv['s_ca_final']:g}", f"{resultado_fv['e_ca_pct']:.2f}",
        ])
    if len(filas_resumen) > 1:
        story.append(tabla(filas_resumen, colw=(4.5, 3.0, 2.7, 2.9, 2.9)))
    else:
        story.append(Paragraph("No hay cálculos disponibles todavía.", normal))

    # ---------------------------------------------------------------- F/G/H
    story.append(Paragraph("F. Presupuesto", h2))
    if total_presupuesto:
        story.append(Paragraph(f"El presupuesto de la instalación asciende a la cantidad de "
                                f"<b>{_miles(total_presupuesto, 2)} €</b> "
                                f"({numero_a_letras_euros(total_presupuesto)}), "
                                "IVA incluido, según el desglose por capítulos que se adjunta en el documento "
                                "de Presupuesto.", normal))
    else:
        story.append(Paragraph("No se ha generado presupuesto en la pestaña correspondiente.", normal))

    story.append(Paragraph("G. Documentos que integran el proyecto", h2))
    for linea in ["Memoria Técnica de Diseño (este documento)", "Anexo de Cálculos y Mediciones",
                  "Pliego de Condiciones Generales", "Presupuesto",
                  "Esquema unifilar y croquis de emplazamiento (a incorporar por el técnico)",
                  "Certificado de Instalación Eléctrica (CIE), tras la puesta en servicio"]:
        story.append(Paragraph("• " + linea, normal))

    story.append(Paragraph("H. Declaración y firma", h2))
    story.append(Paragraph(
        f"D./Dña. {d.get('instalador') or '_______________________'}, en calidad de "
        f"{(d.get('categoria_instalador') or 'instalador autorizado').lower()}, declara que la instalación "
        "descrita en la presente Memoria Técnica de Diseño se ajusta a las prescripciones del Reglamento "
        "Electrotécnico para Baja Tensión y sus Instrucciones Técnicas Complementarias.", normal))
    story.append(Spacer(1, 24))
    story.append(Paragraph("En ______________________, a ____ de ______________ de 20____", normal))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Firma: _______________________________________", normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Documento de apoyo generado automáticamente a partir de los datos introducidos en la aplicación. "
        "Antes de su presentación ante el organismo competente, debe ser revisado, completado y firmado por "
        "el instalador autorizado o técnico competente responsable.", normal))

    doc.build(story, onFirstPage=cajetin, onLaterPages=cajetin)
    return buffer.getvalue()


def _parrafos_calculo_cable_pdf(inp: dict, res: dict, normal, formula) -> list:
    """Redacta la justificación de cálculo del circuito de baja tensión como
    una memoria de cálculo al uso (fórmula tipográfica + texto explicativo +
    sustitución numérica), en vez de líneas sueltas tipo calculadora."""
    from reportlab.platypus import Paragraph
    P = []
    sistema = inp["sistema"]
    cosphi = inp["cos_phi"]

    if inp["modo_entrada"] == "Potencia activa":
        p_w = inp["potencia_kw"] * 1000.0
        p_w_txt = _miles(p_w)
        if sistema == SISTEMA_MONO:
            P.append(Paragraph("La intensidad de empleo del circuito, para un sistema monofásico, se "
                                "determina mediante la expresión:", normal))
            P.append(Paragraph("I<sub>b</sub> = P / (V · cos φ)", formula))
            P.append(Paragraph(f"Sustituyendo los valores de la instalación (P = {p_w_txt} W, "
                                f"V = {inp['tension']:g} V, cos φ = {cosphi:.2f}), resulta:", normal))
            P.append(Paragraph(f"I<sub>b</sub> = {p_w_txt} / ({inp['tension']:g} × {cosphi:.2f}) = "
                                f"<b>{res['ib']:.2f} A</b>", formula))
        else:
            P.append(Paragraph("La intensidad de empleo del circuito, para un sistema trifásico "
                                "equilibrado, se determina mediante la expresión:", normal))
            P.append(Paragraph("I<sub>b</sub> = P / (√3 · V · cos φ)", formula))
            P.append(Paragraph(f"Sustituyendo los valores de la instalación (P = {p_w_txt} W, "
                                f"V = {inp['tension']:g} V, cos φ = {cosphi:.2f}), resulta:", normal))
            P.append(Paragraph(f"I<sub>b</sub> = {p_w_txt} / (√3 × {inp['tension']:g} × {cosphi:.2f}) = "
                                f"<b>{res['ib']:.2f} A</b>", formula))
    else:
        P.append(Paragraph(f"La intensidad de empleo se ha introducido de forma directa: "
                            f"I<sub>b</sub> = <b>{res['ib']:.2f} A</b>.", normal))

    if res.get("ib_motor") is not None:
        if len(inp["corrientes_motores"]) == 1:
            P.append(Paragraph("Al tratarse de un circuito de motor único, la ITC-BT-47 exige dimensionar "
                                "el conductor para el 125% de la intensidad a plena carga del motor:", normal))
            P.append(Paragraph(f"I<sub>b,motor</sub> = 1,25 · I<sub>n</sub> = 1,25 × "
                                f"{inp['corrientes_motores'][0]:.2f} = <b>{res['ib_motor']:.2f} A</b>", formula))
        else:
            ordenados = sorted(inp["corrientes_motores"], reverse=True)
            resto = " + ".join(f"{x:.1f}" for x in ordenados[1:])
            P.append(Paragraph("Al existir varios motores en el mismo circuito, la ITC-BT-47 exige "
                                "dimensionar el conductor para el 125% de la intensidad del motor de mayor "
                                "potencia, más el 100% de la intensidad del resto:", normal))
            P.append(Paragraph(f"I<sub>b,motor</sub> = 1,25 × {ordenados[0]:.2f} + ({resto}) = "
                                f"<b>{res['ib_motor']:.2f} A</b>", formula))
        if inp["ascensor_grua"]:
            P.append(Paragraph("Por tratarse de un ascensor o grúa, se aplica adicionalmente el factor "
                                "×1,3 previsto en la ITC-BT-47.", normal))
    if inp["alumbrado_descarga"]:
        P.append(Paragraph("Al tratarse de alumbrado con lámparas de descarga sin corregir el factor de "
                            "potencia, se incrementa la intensidad de cálculo con un factor orientativo de "
                            "1,8, según la ITC-BT-44:", normal))
        P.append(Paragraph(f"I<sub>b,cálculo</sub> = I<sub>b</sub> × 1,8 = <b>{res['ib_calculo']:.2f} A</b>",
                            formula))

    P.append(Paragraph("El criterio térmico del artículo 19.2 de la ITC-BT-19 exige que la intensidad "
                        "admisible del cable, corregida por las condiciones reales de la instalación, no "
                        "sea inferior a la intensidad de empleo:", normal))
    P.append(Paragraph("I<sub>b</sub> ≤ I<sub>n</sub> ≤ I<sub>z</sub> ,  con  I<sub>z</sub> = "
                        "I<sub>z,tabla</sub> · f<sub>temp</sub> · f<sub>agrup</sub> · f<sub>capas</sub> · "
                        "f<sub>resist</sub>", formula))
    factor_base = res["iz_termica"] / max(res["factor_total"], 1e-9)
    P.append(Paragraph(f"Para la sección adoptada, la Guía-BT-19 establece una intensidad admisible de "
                        f"base de {factor_base:.1f} A que, corregida por los factores de temperatura "
                        f"({res['f_temp']:.3f}), agrupamiento ({res['f_agrup']:.3f}), capas "
                        f"({res['f_capas']:.3f}) y resistividad del terreno ({res['f_resist']:.3f}), "
                        "resulta:", normal))
    P.append(Paragraph(f"I<sub>z</sub> = {factor_base:.1f} × {res['f_temp']:.3f} × {res['f_agrup']:.3f} × "
                        f"{res['f_capas']:.3f} × {res['f_resist']:.3f} = "
                        f"<b>{res['iz_termica']:.2f} A</b>", formula))
    i_comparar = res["ib_calculo"] / (res["n_paralelo"] if res["necesita_paralelo"] else 1)
    cumple_termico = res["iz_termica"] >= i_comparar
    P.append(Paragraph(f"Al ser I<sub>z</sub> = {res['iz_termica']:.2f} A "
                        f"{'superior' if cumple_termico else 'inferior'} a la intensidad de cálculo "
                        f"({i_comparar:.2f} A), la sección de <b>{res['s_termica']:g} mm²</b> "
                        f"{'satisface' if cumple_termico else 'NO satisface'} el criterio térmico.", normal))

    P.append(Paragraph("Para el criterio de caída de tensión, la conductividad del conductor se toma a su "
                        "temperatura de servicio (más conservadora que a 20°C):", normal))
    P.append(Paragraph("κ(T) = κ<sub>20°C</sub> / [1 + α · (T<sub>servicio</sub> − 20)]", formula))
    kappa = res["kappa"]
    P.append(Paragraph(f"κ = {CONDUCTIVIDAD_20C[inp['conductor']]:g} / [1 + "
                        f"{COEF_TEMP_RESIST[inp['conductor']]:g} × "
                        f"({TEMP_SERVICIO[inp['aislamiento']]:g} − 20)] = <b>{kappa:.2f} m/(Ω·mm²)</b>", formula))
    S = res["seccion_final"]
    r_metro = 1.0 / (kappa * S)
    k_sist_txt = "2" if sistema == SISTEMA_MONO else "√3"
    P.append(Paragraph("La caída de tensión se calcula, con resistencia R = 1/(κ·S), mediante:", normal))
    P.append(Paragraph(f"ΔU = {k_sist_txt} · L · I<sub>b</sub> · (R·cos φ + X·sen φ)", formula))
    P.append(Paragraph(f"Para L = {inp['longitud']:g} m y S = {S:g} mm², R = 1/({kappa:.2f}×{S:g}) = "
                        f"{r_metro:.5f} Ω/m, resultando:", normal))
    P.append(Paragraph(f"ΔU = {res['e_final']:.2f} V = <b>{res['e_final_pct']:.2f} %</b> de "
                        f"{inp['tension']:g} V", formula))
    cumple_du = res["e_final_pct"] <= inp["delta_u_max"]
    P.append(Paragraph(f"Como {res['e_final_pct']:.2f} % es {'inferior' if cumple_du else 'superior'} al "
                        f"máximo admisible del {inp['delta_u_max']:g} % para este tramo, la sección "
                        f"{'satisface' if cumple_du else 'NO satisface'} el criterio de caída de tensión.",
                        normal))

    if res.get("seccion_neutro"):
        P.append(Paragraph("La sección del conductor neutro se obtiene según el criterio general del REBT "
                            "(igual a la de fase hasta 16 mm², o la mitad redondeada para secciones "
                            "mayores sin armónicos significativos):", normal))
        P.append(Paragraph(f"S<sub>f</sub> = {S:g} mm² → <b>S<sub>n</sub> = "
                            f"{res['seccion_neutro']:g} mm²</b>", formula))
    if res.get("seccion_proteccion"):
        P.append(Paragraph("La sección del conductor de protección se obtiene según la tabla de la "
                            "ITC-BT-18:", normal))
        P.append(Paragraph(f"S<sub>f</sub> = {S:g} mm² → <b>S<sub>p</sub> = "
                            f"{res['seccion_proteccion']:g} mm²</b>", formula))

    if res.get("cumple_cc") is not None:
        k_cc = K_CORTOCIRCUITO[(inp["conductor"], inp["aislamiento"])]
        P.append(Paragraph("Por último, se verifica el criterio térmico de cortocircuito (IEC 60364-5-54):",
                            normal))
        P.append(Paragraph("S<sub>mín</sub> = I<sub>cc</sub> · √t / k", formula))
        P.append(Paragraph(f"S<sub>mín</sub> = ({inp['icc_ka']:g}×1000 × √{inp['tiempo_s']:g}) / {k_cc} = "
                            f"<b>{res['s_min_cc']:g} mm²</b>, frente a los {S:g} mm² adoptados: "
                            f"{'cumple' if res['cumple_cc'] else 'NO cumple'}.", normal))
    return P


def _parrafos_calculo_fv_pdf(inp: dict, res: dict, normal, formula) -> list:
    """Redacta la justificación de cálculo de la instalación fotovoltaica
    como memoria de cálculo (mismo espíritu que la función de cable)."""
    from reportlab.platypus import Paragraph
    P = []

    P.append(Paragraph(f"El generador fotovoltaico se dimensiona para una potencia pico de "
                        f"<b>{res['p_pico_kwp']:.2f} kWp</b>, equivalente a {res['n_paneles']} paneles de "
                        f"{inp['potencia_panel_wp']:g} Wp y una superficie de captación de "
                        f"{res['superficie_necesaria_m2']:.1f} m².", normal))

    P.append(Paragraph("Las pérdidas por orientación e inclinación no óptimas se calculan según la "
                        "expresión del Documento Básico HE5 del Código Técnico de la Edificación:", normal))
    P.append(Paragraph("Pérdidas (%) = 100 · [1,2·10⁻⁴·(β − φ + 10)² + 3,5·10⁻⁵·α²]", formula))
    P.append(Paragraph(f"con inclinación β = {inp['inclinacion']:g}°, latitud φ = {inp['latitud']:g}° y "
                        f"azimut α = {inp['azimut']:g}°, lo que da unas pérdidas de "
                        f"<b>{res['perdidas_orient_pct']:.2f} %</b>.", normal))
    P.append(Paragraph("El rendimiento efectivo (Performance Ratio) incorpora además las pérdidas por "
                        "sombras/suciedad y la eficiencia del inversor:", normal))
    P.append(Paragraph(f"PR<sub>efectivo</sub> = PR<sub>base</sub> · (1 − p<sub>orient</sub>) · "
                        f"(1 − p<sub>sombras</sub>) · η<sub>inversor</sub> = {inp['pr']:.2f} × "
                        f"(1 − {res['perdidas_orient_pct']/100:.3f}) × "
                        f"(1 − {inp['perdidas_sombras']/100:.2f}) × {inp['eficiencia_inversor']/100:.3f} = "
                        f"<b>{res['pr_efectivo']:.3f}</b>", formula))
    P.append(Paragraph("La producción anual estimada resulta de aplicar la fórmula del IDAE:", normal))
    P.append(Paragraph("E<sub>anual</sub> = P<sub>pico</sub> · HSP · 365 · PR<sub>efectivo</sub>", formula))
    P.append(Paragraph(f"E<sub>anual</sub> = {res['p_pico_kwp']:.2f} × {inp['hsp']:g} × 365 × "
                        f"{res['pr_efectivo']:.3f} = <b>{_miles(res['produccion_anual_kwh'])} kWh/año</b>",
                        formula))
    P.append(Paragraph(f"Considerando una degradación anual del panel del {inp['degradacion_anual']:g}%, la "
                        f"producción estimada será de {_miles(res['produccion_ano10'])} kWh/año en el año "
                        f"10 y de {_miles(res['produccion_ano25'])} kWh/año en el año 25. El ahorro de "
                        f"emisiones asociado, con un factor de emisión de la red de "
                        f"{inp.get('factor_co2', FACTOR_CO2_RED_DEFECTO):.2f} kg CO₂/kWh, es de "
                        f"<b>{res['co2_evitado_kg_ano']/1000:.2f} toneladas de CO₂ al año</b>.", normal))

    P.append(Paragraph(f"El generador se configura con {res['n_serie']} paneles en serie por string y "
                        f"{res['n_paralelo']} strings en paralelo. La tensión de circuito abierto del "
                        "string en la condición más desfavorable (frío) se calcula como:", normal))
    P.append(Paragraph("V<sub>string,frío</sub> = N<sub>serie</sub> · V<sub>oc</sub> · "
                        "[1 + α<sub>V</sub> · (25 − T<sub>mín</sub>)]", formula))
    P.append(Paragraph(f"V<sub>string,frío</sub> = {res['n_serie']} × {inp['voc']:g} × "
                        f"[1 + {inp['coef_temp_voc']/100:.4f} × (25 − {inp['temp_min']:g})] = "
                        f"<b>{res['v_string_frio']:.1f} V</b>", formula))
    cumple_v = res["cumple_vmax"] and res["cumple_vmpp_min"] and res["cumple_vmpp_max"]
    P.append(Paragraph(f"Este valor {'se mantiene dentro' if cumple_v else 'NO se mantiene dentro'} de la "
                        f"ventana de tensión admisible del inversor "
                        f"({inp['vmin_mppt']:g}-{inp['vmax_mppt']:g} V de rango MPPT, "
                        f"{inp['vmax_entrada_inversor']:g} V de tensión máxima de entrada).", normal))

    P.append(Paragraph("De acuerdo con la ITC-BT-40, los cables de conexión de instalaciones generadoras "
                        "se dimensionan para una intensidad no inferior al 125% de la intensidad máxima del "
                        "generador, con una caída de tensión conjunta (continua + alterna) no superior al "
                        "1,5% entre el generador y el punto de interconexión:", normal))
    P.append(Paragraph(f"I<sub>diseño,CC</sub> = 1,25 · I<sub>sc</sub> = 1,25 × {inp['isc']:g} = "
                        f"<b>{res['i_diseno_cc']:.2f} A</b>  →  sección adoptada "
                        f"<b>{res['s_cc_final']:g} mm²</b> (ΔU = {res['du_cc_pct']:.2f} %)", formula))
    P.append(Paragraph(f"I<sub>diseño,CA</sub> = 1,25 · I<sub>b</sub> = <b>{res['i_diseno_ca']:.2f} A</b>  →  "
                        f"sección adoptada <b>{res['s_ca_final']:g} mm²</b> "
                        f"(ΔU = {res['e_ca_pct']:.2f} %)", formula))
    cumple_total = res["du_total_pct"] <= 1.5
    P.append(Paragraph(f"La caída de tensión conjunta resulta ΔU = {res['du_total_pct']:.2f} %, que "
                        f"{'cumple' if cumple_total else 'NO cumple'} el límite del 1,5% establecido por "
                        "la ITC-BT-40.", normal))

    if res.get("calibre_fusible_string"):
        P.append(Paragraph(f"Al haber más de un string en paralelo, se dispone fusible de protección de "
                            f"cada string, de calibre <b>{res['calibre_fusible_string']} A</b> y tensión "
                            f"nominal <b>{res.get('tension_fusible_string','—')} V</b> (criterio orientativo "
                            "1,5-2,4 veces la Isc del string, UNE-EN 62548).", normal))
    if res.get("capacidad_bateria_kwh"):
        P.append(Paragraph("La capacidad de la batería de acumulación se determina a partir del consumo "
                            "diario a cubrir, la autonomía deseada y la profundidad de descarga admisible:",
                            normal))
        P.append(Paragraph("C<sub>batería</sub> = (Consumo<sub>diario</sub> · Días<sub>autonomía</sub>) / "
                            "Profundidad<sub>descarga</sub>", formula))
        P.append(Paragraph(f"C<sub>batería</sub> = ({inp.get('consumo_diario_bateria_kwh',0):.2f} × "
                            f"{inp.get('autonomia_dias',0):g}) / {inp.get('profundidad_descarga',80)/100:.2f} "
                            f"= <b>{res['capacidad_bateria_kwh']:.1f} kWh</b>", formula))

    if res.get("ahorro_anual"):
        texto_ahorro = (f"Del total producido, se estima que un {inp['pct_autoconsumo']:g}% se "
                        f"autoconsume directamente ({_miles(res['energia_autoconsumida'])} kWh/año), "
                        f"generando un ahorro de <b>{_fmt_eur(res['ahorro_autoconsumo'])}/año</b>")
        if res["ingreso_excedentes"]:
            texto_ahorro += (f", más un ingreso por compensación de excedentes de "
                              f"<b>{_fmt_eur(res['ingreso_excedentes'])}/año</b>")
        texto_ahorro += "."
        P.append(Paragraph(texto_ahorro, normal))
        if res.get("payback_anos"):
            P.append(Paragraph(f"Con una inversión estimada de {_fmt_eur(inp['inversion_total'])} y un "
                                f"ahorro anual de {_fmt_eur(res['ahorro_anual'])}, el retorno simple de la "
                                f"inversión es de <b>{res['payback_anos']:.1f} años</b>.", normal))
    return P


def generar_pdf_anexo_calculos(datos_proyecto: dict, inputs_cable: dict, resultado_cable: dict,
                                 inputs_fv: dict, resultado_fv: dict, capitulos_presupuesto: list,
                                 pct_beneficio: float, pct_amortizacion: float) -> bytes:
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm as _cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "ANEXO DE CALCULOS Y MEDICIONES", "Justificacion tecnica y mediciones", datos_proyecto)
    COBRE = colors.HexColor("#8a5a1f")
    formula = ParagraphStyle("formula", parent=normal, alignment=TA_CENTER, textColor=COBRE,
                              fontSize=10, leading=15, spaceBefore=4, spaceAfter=8)

    story = []
    hay_cable = resultado_cable.get("seccion_final") is not None
    hay_fv = bool(resultado_fv) and resultado_fv.get("p_pico_kwp") is not None

    story.append(Paragraph("0. Introducción y criterios generales", h2))
    story.append(Paragraph(
        "Este Anexo justifica, mediante las fórmulas y valores empleados, las secciones de conductor, "
        "protecciones y caídas de tensión adoptadas en la instalación descrita en la Memoria Técnica de "
        "Diseño, así como las mediciones que dan origen al Presupuesto. Los criterios generales aplicados "
        "son los del artículo 19.2 de la ITC-BT-19 (criterio térmico, criterio de caída de tensión y, "
        "cuando se aporta, criterio térmico de cortocircuito) y, para la instalación fotovoltaica en su "
        "caso, la ITC-BT-40 y el Real Decreto 244/2019.", normal))

    story.append(Paragraph("1. Cálculos justificativos", h2))
    if hay_cable:
        story.append(Paragraph(f"1.1. Instalación de baja tensión — {inputs_cable['tipo_circuito']}", h3))
        story.extend(_parrafos_calculo_cable_pdf(inputs_cable, resultado_cable, normal, formula))
    if hay_fv:
        story.append(Paragraph("1.2. Instalación fotovoltaica", h3))
        story.extend(_parrafos_calculo_fv_pdf(inputs_fv, resultado_fv, normal, formula))
    if not hay_cable and not hay_fv:
        story.append(Paragraph("No hay cálculos disponibles: completa la Calculadora de cables y/o el "
                                "módulo Fotovoltaico antes de generar este anexo.", normal))

    story.append(Paragraph("2. Mediciones", h2))
    story.append(Paragraph(
        "Relación de unidades de obra y materiales, agrupadas por capítulo, que dan origen al Presupuesto "
        "de la instalación:", normal))
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
                                "completo (precios y totales) se encuentra en el documento de Presupuesto.", normal))
    else:
        story.append(Paragraph("No se han definido capítulos en la pestaña Presupuesto.", normal))

    story.append(Paragraph("3. Conclusión", h2))
    story.append(Paragraph(
        "Con los cálculos y mediciones anteriores queda justificada, a juicio del técnico que suscribe, la "
        "idoneidad de las secciones, protecciones y demás elementos descritos en la Memoria Técnica de "
        "Diseño para el uso previsto de la instalación.", normal))

    doc.build(story, onFirstPage=cajetin, onLaterPages=cajetin)
    return buffer.getvalue()


def generar_pdf_condiciones_generales(datos_proyecto: dict, hay_fv: bool) -> bytes:
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm as _cm

    buffer, doc, cajetin, AZUL, colors, h2, h3, normal = _preparar_doc_pdf(
        "PLIEGO DE CONDICIONES GENERALES", "Materiales, ejecución, pruebas y mantenimiento", datos_proyecto)

    def lista(items, style=normal):
        return [Paragraph("• " + t, style) for t in items]

    def tabla(datos, colw=(6.0, 5.0, 5.0)):
        t = Table(datos, colWidths=[c * _cm for c in colw])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ccd1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        return t

    story = [Paragraph("1. Objeto y alcance", h2)]
    story.append(Paragraph(
        "El presente Pliego de Condiciones Generales establece las prescripciones técnicas mínimas que "
        "deben cumplir los materiales, la ejecución, las pruebas y la puesta en servicio de la instalación "
        "eléctrica objeto de la Memoria Técnica de Diseño y su Anexo de Cálculos, sin perjuicio de "
        "condiciones particulares más restrictivas que pueda fijar la Dirección Facultativa, la empresa "
        "distribuidora o las ordenanzas municipales y autonómicas de aplicación.", normal))

    story.append(Paragraph("2. Normativa de aplicación", h2))
    story.extend(lista([
        "Reglamento Electrotécnico para Baja Tensión (REBT), Real Decreto 842/2002, y sus Instrucciones "
        "Técnicas Complementarias (ITC-BT-01 a ITC-BT-53).",
        "Normas UNE armonizadas de materiales, cables (UNE-EN 50525, UNE-HD 60364-5-52) y aparamenta "
        "(UNE-EN 60898, UNE-EN 61008/61009).",
        "Real Decreto 244/2019, condiciones administrativas, técnicas y económicas del autoconsumo de "
        "energía eléctrica (cuando la instalación incluya generación fotovoltaica).",
        "Código Técnico de la Edificación (CTE), en lo relativo a eficiencia energética (DB-HE) y "
        "seguridad en caso de incendio (DB-SI), cuando resulte de aplicación.",
        "Ordenanzas municipales y normas particulares de la empresa distribuidora de energía eléctrica.",
    ]))

    story.append(Paragraph("3. Condiciones de los materiales", h2))
    story.append(Paragraph("3.1 Conductores y cables", h3))
    story.extend(lista([
        "Serán de cobre electrolítico (salvo justificación expresa de aluminio en líneas de gran sección), "
        "con aislamiento y cubierta adecuados al método de instalación definido en el Anexo de Cálculos "
        "(PVC 450/750V para instalación interior, XLPE/EPR 0,6/1kV para acometidas, derivaciones "
        "individuales e instalación fotovoltaica).",
        "La identificación de conductores por color será: azul claro para el neutro, verde-amarillo "
        "exclusivamente para el conductor de protección, y marrón/negro/gris para las fases (ITC-BT-19, "
        "UNE 21089).",
        "Los radios de curvatura mínimos y las tracciones máximas admisibles durante el tendido serán los "
        "indicados por el fabricante del cable; no se admitirán empalmes salvo en cajas de registro "
        "accesibles.",
    ]))
    story.append(Paragraph("3.2 Canalizaciones", h3))
    story.extend(lista([
        "Los tubos protectores (metálicos, PVC rígido o corrugado) cumplirán la norma UNE-EN 61386, con el "
        "grado de protección IP adecuado al local (ITC-BT-30) y un diámetro tal que permita la incorporación "
        "de conductores adicionales según la ITC-BT-21.",
        "Las bandejas y canales portacables cumplirán la norma UNE-EN 61537, con la anchura y el grado de "
        "ocupación indicados en el Anexo de Cálculos, dejando un margen mínimo del 20% para ampliaciones.",
    ]))
    story.append(Paragraph("3.3 Aparamenta de mando y protección", h3))
    story.extend(lista([
        "Los interruptores automáticos (PIA) cumplirán la norma UNE-EN 60898, con un poder de corte no "
        "inferior a la intensidad de cortocircuito prevista en su punto de instalación.",
        "Los interruptores diferenciales cumplirán la norma UNE-EN 61008/61009, siendo de tipo A o "
        "superinmunizado en circuitos con receptores electrónicos o variadores de frecuencia, y de tipo B "
        "en instalaciones fotovoltaicas cuando el inversor no garantice por diseño la ausencia de "
        "componente continua de defecto (ITC-BT-24, guía UNE-HD 60364-5-53).",
        "Todo el material de protección dispondrá del marcado CE y ficha técnica que acredite sus "
        "características (intensidad nominal, poder de corte, curva de disparo, sensibilidad).",
    ]))
    story.append(Paragraph("3.4 Cuadros, mecanismos y receptores", h3))
    story.extend(lista([
        "Los cuadros eléctricos serán de material aislante autoextinguible o metálicos con puesta a tierra, "
        "con grado de protección IP adecuado a su ubicación, y dispondrán de espacio de reserva no inferior "
        "al 20% de los módulos instalados.",
        "Los mecanismos (interruptores, bases de enchufe, tomas industriales) cumplirán las normas UNE-EN "
        "60669 y UNE-EN 60309 según corresponda, con el grado de protección exigido en locales húmedos o "
        "exteriores (mínimo IP44).",
    ]))

    story.append(Paragraph("4. Condiciones de ejecución", h2))
    story.extend(lista([
        "La instalación será ejecutada por instalador eléctrico autorizado en la categoría correspondiente, "
        "o bajo la dirección de técnico titulado competente, siguiendo el orden y las prescripciones de la "
        "ITC-BT-19 (prescripciones generales de instalaciones interiores).",
        "Las canalizaciones se dispondrán separadas de otras instalaciones no eléctricas (agua, gas, "
        "calefacción, telecomunicaciones) según las distancias mínimas de la ITC-BT-20/21, y de forma que "
        "permitan su identificación, ampliación y mantenimiento.",
        "Los circuitos se identificarán en el cuadro mediante etiquetas indelebles, indicando el receptor o "
        "zona que alimentan y su calibre de protección.",
        "En instalaciones con más de un cuadro secundario, se levantará un diagrama de bloques que refleje "
        "la relación de dependencia entre ellos, conforme al modelo oficial de MTD.",
        "Toda modificación respecto a lo indicado en la Memoria y el Anexo de Cálculos deberá quedar "
        "reflejada en la documentación 'as built' entregada al titular.",
    ]))

    if hay_fv:
        story.append(Paragraph("5. Condiciones específicas de la instalación fotovoltaica", h2))
        story.extend(lista([
            "La instalación generadora cumplirá la ITC-BT-40 y el Real Decreto 244/2019, disponiendo de "
            "dispositivos que limiten la inyección de corriente continua y la generación de sobretensiones, "
            "e impidan el funcionamiento en isla de la red de distribución.",
            "Los cables de conexión (tramos CC y CA) se dimensionarán para una intensidad no inferior al "
            "125% de la intensidad máxima del generador, con una caída de tensión conjunta no superior al "
            "1,5% entre el generador y el punto de interconexión.",
            "Las instalaciones de autoconsumo sin excedentes dispondrán de un mecanismo antivertido conforme "
            "al Anexo I de la ITC-BT-40, verificado según los ensayos allí establecidos.",
            "Los conectores del lado de corriente continua serán del tipo normalizado para aplicaciones "
            "fotovoltaicas (p. ej. MC4), estancos e inconfundibles con los de otros sistemas.",
            "Las estructuras metálicas de soporte de los módulos, incluyendo canalizaciones metálicas, se "
            "conectarán equipotencialmente a tierra; si son de aluminio, se emplearán dispositivos de "
            "conexión que eviten pares electroquímicos.",
            "Se dispondrá de un cuadro de mando y protección específico con las protecciones diferenciales "
            "necesarias y los dispositivos de seccionamiento requeridos para las labores de mantenimiento "
            "en condiciones de seguridad.",
        ]))
        num_seccion_pruebas = "6"
    else:
        num_seccion_pruebas = "5"

    story.append(Paragraph(f"{num_seccion_pruebas}. Pruebas y verificaciones antes de la puesta en servicio", h2))
    story.append(Paragraph(
        "Antes de la puesta en servicio se realizarán, como mínimo, las siguientes comprobaciones "
        "(ITC-BT-05 y UNE-HD 60364-6):", normal))
    story.append(tabla([
        ["Ensayo", "Criterio de aceptación"],
        ["Continuidad de conductores de protección y equipotenciales", "Continuidad eléctrica verificada"],
        ["Resistencia de aislamiento (circuitos ≤500V, ensayo a 500V c.c.)", "≥ 0,50 MΩ"],
        ["Resistencia de aislamiento (circuitos MBTS/MBTP, ensayo a 250V c.c.)", "≥ 0,25 MΩ"],
        ["Resistencia de puesta a tierra", "Compatible con la sensibilidad del diferencial instalado"],
        ["Disparo de los interruptores diferenciales (botón de test e Idn)", "Disparo correcto"],
        ["Caída de tensión en los circuitos más desfavorables", "Conforme al Anexo de Cálculos"],
        ["Secuencia de fases y tensiones (instalación trifásica)", "Correcta y equilibrada"],
    ], colw=(9.0, 7.0)))
    story.append(Paragraph(
        "Realizadas las comprobaciones con resultado favorable, se emitirá el correspondiente Certificado "
        "de Instalación Eléctrica (CIE), que se presentará junto con la MTD ante el órgano competente de la "
        "Comunidad Autónoma para su registro.", normal))

    story.append(Paragraph(f"{int(num_seccion_pruebas)+1}. Garantías y recepción", h2))
    story.append(Paragraph(
        "El instalador garantizará la instalación frente a defectos de ejecución durante el plazo legal "
        "aplicable, sin perjuicio de las garantías comerciales de cada fabricante sobre los equipos "
        "suministrados (aparamenta, luminarias, inversor, paneles, baterías). La recepción de la instalación "
        "por el titular no exime al instalador de sus responsabilidades legales y contractuales.", normal))

    story.append(Paragraph(f"{int(num_seccion_pruebas)+2}. Mantenimiento", h2))
    story.append(Paragraph(
        "El titular de la instalación velará por su correcto mantenimiento, revisando periódicamente el "
        "estado de conductores, protecciones y puesta a tierra (accionamiento del botón de test del "
        "diferencial al menos una vez al mes), y encargando las inspecciones periódicas que, en su caso, "
        "sean obligatorias según la potencia y el uso de la instalación (ITC-BT-05).", normal))

    story.append(Paragraph(f"{int(num_seccion_pruebas)+3}. Seguridad y salud", h2))
    story.append(Paragraph(
        "Durante la ejecución de los trabajos se cumplirá la normativa de prevención de riesgos laborales "
        "aplicable (Ley 31/1995 y RD 1627/1997 en su caso), utilizando los equipos de protección individual "
        "adecuados a los trabajos eléctricos y respetando en todo momento las cinco reglas de oro del "
        "trabajo sin tensión cuando proceda.", normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Este pliego es un documento de apoyo estándar; adáptalo a las particularidades de cada proyecto y "
        "a las ordenanzas municipales o autonómicas que puedan resultar de aplicación.", normal))

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
        items.append({"designacion": f"Fusible de string {res['calibre_fusible_string']} A / "
                                      f"{res.get('tension_fusible_string', 1000)} V (par)", "unidades": "ud",
                       "cantidad": inp["n_strings_paralelo"], "precio_base": 8.0})
    if res.get("capacidad_bateria_kwh"):
        items.append({"designacion": f"Batería de litio {res['capacidad_bateria_kwh']:.1f} kWh",
                       "unidades": "kWh", "cantidad": round(res["capacidad_bateria_kwh"], 1),
                       "precio_base": PRECIOS_FV_DEFECTO["Batería de litio (por kWh de capacidad)"][1]})
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
# 7B. CÁLCULOS BT — calculadoras sueltas de referencia rápida (independientes
# entre sí), inspiradas en el catálogo de calculadoras de circuitoelectrico.com:
# cables, cortocircuito, tierras, fotovoltaica rápida y eléctricas generales.
# ==============================================================================

# --- Conversión AWG <-> mm² (fórmula estándar: d(mm) = 0,127 x 92^((36-AWG)/39)) ---
AWG_DISPONIBLES = [0000, 000, 00, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                   16, 17, 18, 19, 20, 21, 22, 23, 24]


def awg_a_mm2(awg) -> float:
    n = {"0000": -3, "000": -2, "00": -1}.get(str(awg), awg if isinstance(awg, (int, float)) else int(awg))
    d_mm = 0.127 * (92 ** ((36 - n) / 39))
    return round(math.pi / 4 * d_mm ** 2, 4)


def mm2_a_awg_mas_cercano(mm2: float) -> tuple:
    mejor = min(AWG_DISPONIBLES, key=lambda a: abs(awg_a_mm2(a) - mm2))
    return mejor, awg_a_mm2(mejor)


# --- Resistencia de electrodos de tierra (ITC-BT-18, Guía técnica, Tabla 5) ---
RESISTIVIDAD_TERRENOS_REF = {
    "Terrenos pantanosos (algunos)": 30,
    "Limo": 100,
    "Humus": 150,
    "Turba húmeda": 5,
    "Arcilla plástica": 50,
    "Terrenos cultivables y fértiles, terraplenes compactos y húmedos": 50,
    "Terraplenes cultivables poco fértiles y otros terraplenes": 500,
    "Suelos pedregosos desnudos, arenas secas permeables": 3000,
    "Arena arcillosa": 100,
    "Calizas blandas": 300,
    "Calizas compactas": 1000,
    "Pizarras": 150,
    "Rocas eruptivas (granito, basalto...)": 5000,
    "Personalizado (introducir ρ manualmente)": None,
}


def resistencia_electrodo_pica(rho: float, longitud: float) -> float:
    """R = ρ / L (ITC-BT-18, Tabla 5)."""
    return rho / max(longitud, 1e-6)


def resistencia_electrodo_placa(rho: float, perimetro: float) -> float:
    """R = 0,8 · ρ / P (ITC-BT-18, Tabla 5)."""
    return 0.8 * rho / max(perimetro, 1e-6)


def resistencia_electrodo_conductor(rho: float, longitud: float) -> float:
    """R = 2 · ρ / L (ITC-BT-18, Tabla 5), conductor enterrado horizontalmente."""
    return 2 * rho / max(longitud, 1e-6)


def resistencia_picas_paralelo(r_una_pica: float, n_picas: int) -> float:
    """Aproximación habitual para picas bien separadas (distancia >= 2xL):
    R_total ≈ R_una_pica / n. Orientativa; en terrenos heterogéneos o picas
    próximas la reducción real puede ser menor."""
    return r_una_pica / max(n_picas, 1)


# --- Cortocircuito simplificado (con/sin datos de red aguas arriba) ---
def impedancia_linea(conductor: str, aislamiento: str, seccion: float, longitud: float,
                      n_cargados: int, reactancia_ohm_km: float = REACTANCIA_LINEAL_DEFECTO) -> tuple:
    """Devuelve (R, X) en ohmios de un tramo de línea, ida simple (no ida+vuelta)."""
    kappa = kappa_servicio(conductor, aislamiento)
    r = longitud / (kappa * seccion)
    x = longitud * reactancia_ohm_km / 1000.0
    return r, x


def icc_trifasico(u: float, r_total: float, x_total: float) -> float:
    """Icc = U / (√3 · Z), Z = sqrt(R²+X²). U en V, resultado en A."""
    z = math.sqrt(r_total ** 2 + x_total ** 2)
    return u / (math.sqrt(3) * max(z, 1e-9))


# --- Colores de resistencias (código de 4 bandas) ---
COLORES_DIGITO = {
    "Negro": 0, "Marrón": 1, "Rojo": 2, "Naranja": 3, "Amarillo": 4,
    "Verde": 5, "Azul": 6, "Violeta": 7, "Gris": 8, "Blanco": 9,
}
COLORES_MULTIPLICADOR = {
    "Negro": 1, "Marrón": 10, "Rojo": 100, "Naranja": 1_000, "Amarillo": 10_000,
    "Verde": 100_000, "Azul": 1_000_000, "Oro": 0.1, "Plata": 0.01,
}
COLORES_TOLERANCIA = {
    "Marrón": "±1%", "Rojo": "±2%", "Verde": "±0,5%", "Azul": "±0,25%",
    "Violeta": "±0,1%", "Gris": "±0,05%", "Oro": "±5%", "Plata": "±10%", "Ninguno": "±20%",
}


def valor_resistencia_4_bandas(c1: str, c2: str, c3: str, c4: str) -> tuple:
    valor = (COLORES_DIGITO[c1] * 10 + COLORES_DIGITO[c2]) * COLORES_MULTIPLICADOR[c3]
    return valor, COLORES_TOLERANCIA.get(c4, "±20%")


# ==============================================================================
# 8. INSTALACIONES FOTOVOLTAICAS — módulo de cálculo independiente
# ==============================================================================
# Independiente del todo de la Calculadora de cables: entradas, sesión y motor
# de cálculo propios. Solo comparten las funciones puras de sección de cable
# (iz_tabla, seccion_por_criterio_termico, caida_tension_voltios...) porque son
# la misma física, no porque haya un acoplamiento de datos entre apartados.

ZONAS_CLIMATICAS_HSP = {
    "Norte (Galicia, Asturias, Cantabria, País Vasco)": (3.7, 43.0),
    "Centro / Meseta (Madrid, Castilla)": (4.4, 40.4),
    "Mediterráneo / Levante (Cataluña, C. Valenciana, Baleares)": (4.8, 39.5),
    "Sur (Andalucía, Murcia, Extremadura)": (5.3, 37.2),
    "Canarias": (5.4, 28.3),
    "Personalizado (introducir HSP y latitud manualmente)": (None, None),
}

TIPO_AUTOCONSUMO_FV = [
    "Sin excedentes",
    "Con excedentes acogido a compensación",
    "Con excedentes no acogido a compensación",
    "Instalación aislada (con batería)",
]

PR_DEFECTO_FV = 0.80
EFICIENCIA_INVERSOR_DEFECTO = 97.0        # % — típico 95-98% (SunFields, fabricantes)
DEGRADACION_ANUAL_DEFECTO = 0.5           # %/año — típico 0,3-0,8%/año
FACTOR_CO2_RED_DEFECTO = 0.20             # kg CO2/kWh — orientativo, mix peninsular reciente (REE, 130-200 gCO2/kWh)
AREA_PANEL_DEFECTO = 1.95                 # m² — panel estándar ~450Wp (aprox. 1,75x1,13 m)
PRECIO_COMPENSACION_DEFECTO = 0.08        # €/kWh excedente compensado (orientativo, varía por comercializadora)

# Módulo y catálogo de referencia orientativos (editables en la propia app).
PANEL_DEFECTO = dict(potencia_wp=450, voc=41.8, isc=13.9, vmp=34.6, imp=13.0, coef_temp_voc=-0.27)
INVERSOR_DEFECTO = dict(potencia_kw=5.0, vmin_mppt=80, vmax_mppt=550, vmax_entrada=600, n_mppt=2)

# Calibres de fusible de string normalizados (A) — criterio orientativo del
# fabricante: In entre 1,5 y 2,4 veces Isc del string (UNE-EN 62548 / IEC 60269-6).
CALIBRES_FUSIBLE_STRING = [2, 4, 6, 8, 10, 12, 15, 16, 20, 25, 32]

# Tensiones nominales normalizadas de fusible cilíndrico fotovoltaico (V CC).
TENSIONES_FUSIBLE_FV = [500, 600, 1000, 1500]

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
    "Batería de litio (por kWh de capacidad)": ("kWh", 450.0),
    "Mano de obra instalador FV (por kWp)": ("kWp", 180.0),
    "Legalización y tramitación (notificación/certificado)": ("ud", 250.0),
}


def perdidas_orientacion_inclinacion_cte(inclinacion: float, azimut: float, latitud: float) -> float:
    """Pérdidas (%) por orientación e inclinación no óptimas, según la
    fórmula oficial del CTE DB-HE5: Pérdidas(%) = 100 x [1,2e-4·(β-φ+10)² +
    3,5e-5·α²], con β=inclinación, φ=latitud, α=azimut (0°=sur, ±180°=norte).
    Válida para |azimut| < 90° y ángulos de inclinación habituales; fuera de
    ese rango se satura al valor en el límite para evitar resultados
    absurdos."""
    beta = max(0.0, min(90.0, inclinacion))
    alfa = max(-180.0, min(180.0, azimut))
    perdidas = 100 * (1.2e-4 * (beta - latitud + 10) ** 2 + 3.5e-5 * alfa ** 2)
    return max(0.0, min(perdidas, 40.0))


def calcular_fv(inp: dict) -> dict:
    """Motor de cálculo puro de la instalación fotovoltaica. No depende de la
    Calculadora de cables ni comparte estado con ella."""
    avisos = []

    hsp = inp["hsp"]
    pr_base = inp["pr"]

    if inp["modo_dimensionado"] == "Por consumo anual (kWh)":
        p_pico_kwp = inp["consumo_anual_kwh"] / max(hsp * 365 * pr_base, 1e-6)
        n_paneles = math.ceil(p_pico_kwp * 1000 / inp["potencia_panel_wp"])
    elif inp["modo_dimensionado"] == "Por potencia pico deseada (kWp)":
        p_pico_kwp = inp["potencia_pico_deseada"]
        n_paneles = math.ceil(p_pico_kwp * 1000 / inp["potencia_panel_wp"])
    else:  # Por número de paneles
        n_paneles = inp["n_paneles_manual"]
        p_pico_kwp = n_paneles * inp["potencia_panel_wp"] / 1000

    # --- Pérdidas por orientación/inclinación (CTE DB-HE5) + sombras/suciedad
    # + eficiencia del inversor, todas aplicadas sobre la producción bruta. ---
    perdidas_orient_pct = perdidas_orientacion_inclinacion_cte(
        inp["inclinacion"], inp["azimut"], inp["latitud"])
    perdidas_sombra_pct = inp.get("perdidas_sombras", 0.0)
    eficiencia_inversor_pct = inp.get("eficiencia_inversor", EFICIENCIA_INVERSOR_DEFECTO)

    pr_efectivo = pr_base * (1 - perdidas_orient_pct / 100.0) * (1 - perdidas_sombra_pct / 100.0) * \
        (eficiencia_inversor_pct / 100.0)
    produccion_anual_kwh = p_pico_kwp * hsp * 365 * pr_efectivo

    if perdidas_orient_pct > 15:
        avisos.append(f"Pérdidas por orientación/inclinación estimadas en {perdidas_orient_pct:.1f}% "
                      "(CTE DB-HE5): revisa si es posible acercar el campo solar a la orientación/"
                      "inclinación óptimas para esta latitud.")

    degradacion_pct = inp.get("degradacion_anual", DEGRADACION_ANUAL_DEFECTO)
    produccion_ano10 = produccion_anual_kwh * (1 - degradacion_pct / 100.0) ** 9
    produccion_ano25 = produccion_anual_kwh * (1 - degradacion_pct / 100.0) ** 24

    superficie_necesaria_m2 = n_paneles * inp.get("area_panel", AREA_PANEL_DEFECTO)

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
    tension_fusible_string = None
    if n_paralelo >= 2:
        objetivo = 1.8 * isc
        for c in CALIBRES_FUSIBLE_STRING:
            if c >= objetivo:
                calibre_fusible_string = c
                break
        calibre_fusible_string = calibre_fusible_string or CALIBRES_FUSIBLE_STRING[-1]
        for v in TENSIONES_FUSIBLE_FV:
            if v >= v_string_frio:
                tension_fusible_string = v
                break
        tension_fusible_string = tension_fusible_string or TENSIONES_FUSIBLE_FV[-1]
        if tension_fusible_string < v_string_frio:
            avisos.append(f"Ningún calibre estándar de tensión de fusible ({TENSIONES_FUSIBLE_FV} V) cubre "
                          f"la tensión de string en frío ({v_string_frio:.0f} V): usa fusibles de mayor "
                          "tensión nominal.")
    calibre_magneto_ca = calibre_magnetotermico_sugerido(i_diseno_ca)

    # --- Batería (opcional: aislada o autoconsumo con almacenamiento) ---
    capacidad_bateria_kwh = None
    if inp.get("con_bateria"):
        consumo_diario_kwh = inp.get("consumo_diario_bateria_kwh") or (produccion_anual_kwh / 365.0)
        autonomia_dias = inp.get("autonomia_dias", 1.0)
        prof_descarga_pct = inp.get("profundidad_descarga", 80.0)
        capacidad_bateria_kwh = (consumo_diario_kwh * autonomia_dias) / max(prof_descarga_pct / 100.0, 0.01)

    # --- Económico: autoconsumo + compensación de excedentes ---
    energia_autoconsumida = produccion_anual_kwh * (inp["pct_autoconsumo"] / 100.0)
    energia_excedente = produccion_anual_kwh - energia_autoconsumida
    ahorro_autoconsumo = energia_autoconsumida * inp["precio_kwh"]
    ingreso_excedentes = 0.0
    if inp["tipo_autoconsumo"] == "Con excedentes acogido a compensación":
        ingreso_excedentes = energia_excedente * inp.get("precio_compensacion", PRECIO_COMPENSACION_DEFECTO)
    ahorro_anual = ahorro_autoconsumo + ingreso_excedentes
    payback_anos = (inp["inversion_total"] / ahorro_anual) if ahorro_anual > 0 and inp["inversion_total"] else None

    # --- CO2 evitado ---
    factor_co2 = inp.get("factor_co2", FACTOR_CO2_RED_DEFECTO)
    co2_evitado_kg_ano = produccion_anual_kwh * factor_co2

    return dict(
        p_pico_kwp=p_pico_kwp, n_paneles=n_paneles, produccion_anual_kwh=produccion_anual_kwh,
        produccion_ano10=produccion_ano10, produccion_ano25=produccion_ano25,
        perdidas_orient_pct=perdidas_orient_pct, pr_efectivo=pr_efectivo,
        superficie_necesaria_m2=superficie_necesaria_m2,
        n_serie=n_serie, n_paralelo=n_paralelo, n_paneles_configurados=n_paneles_configurados,
        v_string_frio=v_string_frio, v_string_caliente=v_string_caliente, i_generador=i_generador,
        cumple_vmax=cumple_vmax, cumple_vmpp_min=cumple_vmpp_min, cumple_vmpp_max=cumple_vmpp_max,
        ratio_dc_ac=ratio_dc_ac, i_diseno_cc=i_diseno_cc, s_cc_final=s_cc_final, du_cc_pct=du_cc_pct,
        ib_ca=ib_ca, i_diseno_ca=i_diseno_ca, s_ca_final=s_ca_final, iz_ca=iz_ca, e_ca_pct=e_ca_pct,
        du_total_pct=du_total_pct,
        calibre_fusible_string=calibre_fusible_string, tension_fusible_string=tension_fusible_string,
        calibre_magneto_ca=calibre_magneto_ca, capacidad_bateria_kwh=capacidad_bateria_kwh,
        energia_autoconsumida=energia_autoconsumida, energia_excedente=energia_excedente,
        ahorro_autoconsumo=ahorro_autoconsumo, ingreso_excedentes=ingreso_excedentes,
        ahorro_anual=ahorro_anual, payback_anos=payback_anos,
        co2_evitado_kg_ano=co2_evitado_kg_ano, avisos=avisos,
    )


# ==============================================================================
# 9. INTERFAZ STREAMLIT
# ==============================================================================

def _fmt_eur(valor: float) -> str:
    """Formatea un importe en estilo español: 1.234,56 €."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TMP").replace(".", ",").replace("TMP", ".")
    return f"{texto} €"


def _miles(valor: float, decimales: int = 0) -> str:
    """Formatea un número en estilo español (1.234,56), SOLO el número — a
    diferencia de un .replace(',', '.') sobre toda la frase, esto no toca las
    comas literales del texto que lo rodea."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "TMP").replace(".", ",").replace("TMP", ".")


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
        area_panel = st.number_input("Superficie unitaria del panel (m²)", min_value=0.5, value=AREA_PANEL_DEFECTO, step=0.05)

    st.markdown('<p class="section-label">2 · Ubicación, orientación y producción</p>', unsafe_allow_html=True)
    u1, u2, u3, u4 = st.columns(4)
    with u1:
        zona = st.selectbox("Zona climática", list(ZONAS_CLIMATICAS_HSP.keys()), index=2,
                             help="HSP y latitud orientativos por zona (IDAE/PVGIS). Para el cálculo "
                                  "definitivo, usa el HSP y la latitud exactos de PVGIS.")
        hsp_defecto, lat_defecto = ZONAS_CLIMATICAS_HSP[zona]
        hsp = st.number_input("HSP (horas de sol pico, h/día)", min_value=1.0, max_value=8.0,
                               value=float(hsp_defecto or 4.5), step=0.1)
        latitud = st.number_input("Latitud (°)", min_value=0.0, max_value=90.0,
                                   value=float(lat_defecto or 40.0), step=0.5)
    with u2:
        inclinacion = st.number_input("Inclinación de los paneles (°)", min_value=0.0, max_value=90.0,
                                       value=max(latitud - 10, 0.0), step=1.0,
                                       help="Óptima orientativa en España: entre la latitud y la latitud-10°.")
        azimut = st.number_input("Azimut / orientación (°, 0=sur, ±90=este/oeste, ±180=norte)",
                                  min_value=-180.0, max_value=180.0, value=0.0, step=5.0)
        perdidas_orient_preview = perdidas_orientacion_inclinacion_cte(inclinacion, azimut, latitud)
        st.caption(f"Pérdida por orientación/inclinación (CTE DB-HE5): **{perdidas_orient_preview:.1f}%**")
    with u3:
        pr = st.number_input("Performance Ratio base (PR)", min_value=0.5, max_value=0.95, value=PR_DEFECTO_FV,
                              step=0.01, help="Típico 0,75-0,85. Aquí NO incluyas orientación/inclinación ni "
                                   "eficiencia del inversor: se aplican aparte para desglosar cada pérdida.")
        perdidas_sombras = st.number_input("Pérdidas adicionales por sombras/suciedad (%)", min_value=0.0,
                                            max_value=40.0, value=3.0, step=0.5)
        eficiencia_inversor = st.number_input("Eficiencia del inversor (%)", min_value=80.0, max_value=99.5,
                                               value=EFICIENCIA_INVERSOR_DEFECTO, step=0.5)
    with u4:
        degradacion_anual = st.number_input("Degradación anual del panel (%/año)", min_value=0.0, max_value=2.0,
                                             value=DEGRADACION_ANUAL_DEFECTO, step=0.05,
                                             help="Típico 0,3-0,8%/año según el fabricante.")
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

    with st.expander("🔋 Batería / almacenamiento (opcional)"):
        con_bateria = st.checkbox("Instalación con batería (autoconsumo con almacenamiento o aislada)",
                                   value=(tipo_autoconsumo == "Instalación aislada (con batería)"))
        consumo_diario_bateria_kwh = autonomia_dias = profundidad_descarga = None
        if con_bateria:
            b1, b2, b3 = st.columns(3)
            with b1:
                consumo_diario_bateria_kwh = st.number_input("Consumo diario a cubrir (kWh)", min_value=0.1,
                                                              value=8.0, step=0.5)
            with b2:
                autonomia_dias = st.number_input("Días de autonomía deseados", min_value=0.5, value=1.0, step=0.5)
            with b3:
                profundidad_descarga = st.number_input("Profundidad de descarga admisible (%)", min_value=20.0,
                                                        max_value=100.0, value=80.0, step=5.0,
                                                        help="Típico 80% para baterías de litio (LiFePO4).")

    with st.expander("💶 Estimación económica y ambiental (opcional)"):
        e1, e2, e3 = st.columns(3)
        with e1:
            pct_autoconsumo = st.number_input("% de la producción autoconsumida", min_value=0.0, max_value=100.0,
                                               value=65.0, step=5.0)
            inversion_total = st.number_input("Inversión total estimada (€)", min_value=0.0, value=6000.0, step=100.0)
        with e2:
            precio_compensacion = st.number_input(
                "Precio de compensación de excedentes (€/kWh)", min_value=0.0,
                value=PRECIO_COMPENSACION_DEFECTO, step=0.01,
                help="Solo aplica si la modalidad es 'con excedentes acogido a compensación'; varía por comercializadora.",
                disabled=(tipo_autoconsumo != "Con excedentes acogido a compensación"))
        with e3:
            factor_co2 = st.number_input("Factor de emisión de la red (kg CO₂/kWh)", min_value=0.0,
                                          value=FACTOR_CO2_RED_DEFECTO, step=0.01,
                                          help="Orientativo (REE); el mix eléctrico varía año a año.")

    return dict(
        modo_dimensionado=modo_dimensionado, consumo_anual_kwh=consumo_anual_kwh,
        potencia_pico_deseada=potencia_pico_deseada, n_paneles_manual=n_paneles_manual,
        potencia_panel_wp=potencia_panel_wp, area_panel=area_panel, zona=zona, hsp=hsp, latitud=latitud,
        inclinacion=inclinacion, azimut=azimut, pr=pr, perdidas_sombras=perdidas_sombras,
        eficiencia_inversor=eficiencia_inversor, degradacion_anual=degradacion_anual,
        tipo_autoconsumo=tipo_autoconsumo, precio_kwh=precio_kwh, voc=voc, isc=isc, vmp=vmp,
        coef_temp_voc=coef_temp_voc, n_paneles_serie=n_paneles_serie, n_strings_paralelo=n_strings_paralelo,
        potencia_inversor_kw=potencia_inversor_kw, sistema_ca=sistema_ca, vmin_mppt=vmin_mppt,
        vmax_mppt=vmax_mppt, vmax_entrada_inversor=vmax_entrada_inversor, tension_ca=tension_ca,
        temp_min=temp_min, temp_max_celula=temp_max_celula, longitud_cc=longitud_cc,
        tension_cc_ref=tension_cc_ref, longitud_ca=longitud_ca, pct_autoconsumo=pct_autoconsumo,
        inversion_total=inversion_total, con_bateria=con_bateria,
        consumo_diario_bateria_kwh=consumo_diario_bateria_kwh, autonomia_dias=autonomia_dias,
        profundidad_descarga=profundidad_descarga, precio_compensacion=precio_compensacion,
        factor_co2=factor_co2,
    )


def _render_resultados_fv(inp: dict, res: dict):
    st.markdown('<p class="section-label">Resultado</p>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'''<div class="result-card hero">
            <div class="result-label">Potencia pico</div>
            <div class="result-value">{res['p_pico_kwp']:.2f} kWp</div>
            <div class="result-sub">{res['n_paneles']} paneles · {res['superficie_necesaria_m2']:.1f} m² necesarios</div>
        </div>''', unsafe_allow_html=True)
    with r2:
        st.markdown(f'''<div class="result-card">
            <div class="result-label">Producción anual estimada</div>
            <div class="result-value small">{res['produccion_anual_kwh']:,.0f} kWh/año</div>
            <div class="result-sub">PR efectivo={res['pr_efectivo']:.3f} (incl. orient./sombra/inversor)</div>
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

    st.markdown('<p class="section-label">Pérdidas y producción a largo plazo</p>', unsafe_allow_html=True)
    pl1, pl2, pl3, pl4 = st.columns(4)
    pl1.metric("Pérdidas orientación/inclinación", f"{res['perdidas_orient_pct']:.1f} %",
               help="CTE DB-HE5, según azimut/inclinación/latitud introducidos.")
    pl2.metric("Producción año 1", f"{res['produccion_anual_kwh']:,.0f} kWh".replace(",", "."))
    pl3.metric("Producción año 10", f"{res['produccion_ano10']:,.0f} kWh".replace(",", "."),
               help=f"Con degradación de {inp['degradacion_anual']:g}%/año.")
    pl4.metric("Producción año 25", f"{res['produccion_ano25']:,.0f} kWh".replace(",", "."))

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

    p1, p2, p3 = st.columns(3)
    p1.metric("Fusible de string sugerido",
              f"{res['calibre_fusible_string']} A / {res['tension_fusible_string']} V"
              if res["calibre_fusible_string"] else "No requerido (1 string)")
    p2.metric("Magnetotérmico CA sugerido", f"{res['calibre_magneto_ca']} A")
    p3.metric("CO₂ evitado", f"{res['co2_evitado_kg_ano']/1000:.2f} t/año")

    if res.get("capacidad_bateria_kwh"):
        st.markdown('<p class="section-label">Batería / almacenamiento</p>', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        b1.metric("Capacidad de batería necesaria", f"{res['capacidad_bateria_kwh']:.1f} kWh")
        b2.metric("Autonomía configurada", f"{inp['autonomia_dias']:g} días · "
                  f"{inp['profundidad_descarga']:g}% descarga admisible")

    if res["ahorro_anual"]:
        st.markdown('<p class="section-label">Estimación económica</p>', unsafe_allow_html=True)
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Energía autoconsumida", f"{res['energia_autoconsumida']:,.0f} kWh".replace(",", "."))
        e2.metric("Ahorro por autoconsumo", _fmt_eur(res["ahorro_autoconsumo"]))
        e3.metric("Ingreso por excedentes", _fmt_eur(res["ingreso_excedentes"]))
        e4.metric("Retorno simple (payback)", f"{res['payback_anos']:.1f} años" if res["payback_anos"] else "—")
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
    st.session_state.setdefault("catalogo_precios", {
        cat: {item: precio for item, (unidad, precio) in items.items()}
        for cat, items in CATALOGO_MATERIALES.items()
    })
    capitulos = st.session_state["presupuesto_capitulos"]
    cfg = st.session_state["presupuesto_config"]
    catalogo = st.session_state["catalogo_precios"]

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

    with st.expander("📚 Base de precios — catálogo editable de materiales típicos", expanded=False):
        st.caption(f"{sum(len(v) for v in catalogo.values())} materiales en {len(catalogo)} categorías, "
                   "con todas sus variantes habituales (secciones, calibres, tipos...). Edita el precio base "
                   "de cualquier fila; se guarda para toda la sesión y se usa al añadir partidas a un capítulo.")
        cat_editar = st.selectbox("Categoría a revisar/editar", list(catalogo.keys()), key="cat_editar_catalogo")
        df_cat = pd.DataFrame([{"Concepto": item, "Precio base (€)": precio}
                                for item, precio in catalogo[cat_editar].items()])
        df_cat_editada = st.data_editor(df_cat, key=f"editor_catalogo_{cat_editar}", width='stretch',
                                         hide_index=True, num_rows="fixed")
        for _, fila in df_cat_editada.iterrows():
            catalogo[cat_editar][fila["Concepto"]] = float(fila["Precio base (€)"])

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

            ac1, ac2, ac3, ac4 = st.columns([2, 2.5, 1, 1])
            with ac1:
                cat_sel = st.selectbox("Categoría catálogo", list(catalogo.keys()), key=f"cat_sel_{idx}")
            with ac2:
                item_sel = st.selectbox("Material", list(catalogo[cat_sel].keys()), key=f"item_sel_{idx}")
            with ac3:
                cant_sel = st.number_input("Cantidad", min_value=0.1, value=1.0, step=1.0, key=f"cant_sel_{idx}")
            with ac4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Añadir", key=f"add_cat_{idx}"):
                    unidad = CATALOGO_MATERIALES[cat_sel][item_sel][0]
                    cap["items"].append({
                        "partida": f"{idx + 1}.{len(cap['items']) + 1}", "designacion": item_sel,
                        "unidades": unidad, "cantidad": cant_sel, "precio_base": catalogo[cat_sel][item_sel],
                    })
                    st.rerun()

            df_items = pd.DataFrame([
                {"Partida": it.get("partida", "-"), "Designación": it["designacion"], "Unidades": it["unidades"],
                 "Cantidad": it["cantidad"], "Precio base": it["precio_base"]}
                for it in cap["items"]
            ]) if cap["items"] else pd.DataFrame(columns=["Partida", "Designación", "Unidades", "Cantidad", "Precio base"])

            st.caption("También puedes editar, añadir o borrar filas directamente en la tabla (con texto libre).")
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
        "titular": "", "nif_titular": "", "emplazamiento": "", "referencia_catastral": "", "uso": "",
        "superficie": "", "tipo_instalacion": "Nueva instalación",
        "instalador": "", "nif_instalador": "", "n_autorizacion": "", "categoria_instalador": "Básica",
    })
    datos = st.session_state["datos_proyecto"]

    st.markdown("**A · Titular**")
    d1, d2, d3 = st.columns(3)
    with d1:
        datos["titular"] = st.text_input("Titular de la instalación (nombre o razón social)", datos["titular"])
    with d2:
        datos["nif_titular"] = st.text_input("NIF/CIF del titular", datos["nif_titular"])
    with d3:
        datos["tipo_instalacion"] = st.selectbox(
            "Tipo de actuación", ["Nueva instalación", "Ampliación", "Reforma"],
            index=["Nueva instalación", "Ampliación", "Reforma"].index(datos["tipo_instalacion"]))

    st.markdown("**B · Emplazamiento**")
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        datos["emplazamiento"] = st.text_input("Emplazamiento (dirección)", datos["emplazamiento"])
    with e2:
        datos["referencia_catastral"] = st.text_input("Referencia catastral (opcional)",
                                                        datos["referencia_catastral"])
    with e3:
        datos["uso"] = st.text_input("Uso de la instalación", datos["uso"],
                                      placeholder="Vivienda unifamiliar, local comercial...")
    with e4:
        datos["superficie"] = st.text_input("Superficie (m²)", datos["superficie"])

    st.markdown("**C · Instalador autorizado / técnico competente**")
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        datos["instalador"] = st.text_input("Nombre del instalador/técnico", datos["instalador"])
    with i2:
        datos["nif_instalador"] = st.text_input("NIF del instalador/técnico", datos["nif_instalador"])
    with i3:
        datos["n_autorizacion"] = st.text_input("Nº de autorización / colegiado", datos["n_autorizacion"])
    with i4:
        datos["categoria_instalador"] = st.selectbox(
            "Categoría", ["Básica", "Especialista", "Técnico titulado competente"],
            index=["Básica", "Especialista", "Técnico titulado competente"].index(datos["categoria_instalador"]))

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
        st.caption("Memoria descriptiva + justificativa, ITC-BT-04. Documento extenso multi-página.")
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
        st.markdown("**Pliego de Condiciones**")
        st.caption("Condiciones generales de materiales, ejecución y pruebas.")
        pdf_cond = generar_pdf_condiciones_generales(datos, hay_fv)
        st.download_button("⬇️ Descargar Condiciones (PDF)", data=pdf_cond, file_name="condiciones_generales.pdf",
                            mime="application/pdf")

    if not hay_cable and not hay_fv:
        st.info("Todavía no hay ningún cálculo hecho: los documentos se generarán igualmente, pero con las "
                "secciones de cálculo vacías. Completa la Calculadora y/o la Fotovoltaica para un contenido "
                "completo.")


def _render_calculos_bt():
    st.markdown('<p class="section-label">Cálculos BT</p>', unsafe_allow_html=True)
    st.caption("Calculadoras sueltas de referencia rápida, independientes entre sí y de las demás pestañas "
               "— inspiradas en el catálogo de calculadoras de circuitoelectrico.com (cables, cortocircuito, "
               "tierras, fotovoltaica rápida y eléctricas generales). Para el dimensionado completo de un "
               "circuito, usa la pestaña Calculadora.")

    # ---------------------------------------------------------------- CABLES
    with st.expander("🔌 Cables eléctricos", expanded=True):
        st.markdown("**Caída de tensión** (dados sección, longitud e intensidad)")
        c1, c2, c3, c4, c5 = st.columns(5)
        sistema_ct = c1.selectbox("Sistema", [SISTEMA_MONO, SISTEMA_TRI], key="bt_ct_sistema")
        s_ct = c2.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=4, key="bt_ct_seccion")
        l_ct = c3.number_input("Longitud (m)", min_value=0.1, value=20.0, key="bt_ct_l")
        i_ct = c4.number_input("Intensidad (A)", min_value=0.1, value=20.0, key="bt_ct_i")
        cond_ct = c5.selectbox("Conductor", ["Cobre", "Aluminio"], key="bt_ct_cond")
        cosphi_ct = st.slider("cos φ", 0.1, 1.0, 0.9, key="bt_ct_cosphi")
        kappa_ct = kappa_servicio(cond_ct, "PVC")
        e_ct = caida_tension_voltios(sistema_ct, i_ct, l_ct, s_ct, cosphi_ct, kappa_ct)
        tension_ref = 230.0 if sistema_ct == SISTEMA_MONO else 400.0
        st.markdown(f"→ ΔU = **{e_ct:.2f} V** = **{e_ct/tension_ref*100:.2f} %** (sobre {tension_ref:g} V)")

        st.divider()
        st.markdown("**Longitud máxima** (para no superar una ΔU objetivo)")
        c1, c2, c3, c4 = st.columns(4)
        sistema_lm = c1.selectbox("Sistema", [SISTEMA_MONO, SISTEMA_TRI], key="bt_lm_sistema")
        s_lm = c2.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=4, key="bt_lm_seccion")
        i_lm = c3.number_input("Intensidad (A)", min_value=0.1, value=20.0, key="bt_lm_i")
        du_lm = c4.number_input("ΔU máx. (%)", min_value=0.1, value=3.0, key="bt_lm_du")
        tension_lm = 230.0 if sistema_lm == SISTEMA_MONO else 400.0
        k_sist_lm = 2.0 if sistema_lm == SISTEMA_MONO else math.sqrt(3)
        kappa_lm = kappa_servicio("Cobre", "PVC")
        l_max = (du_lm / 100 * tension_lm) / (k_sist_lm * i_lm * (0.9 / (kappa_lm * s_lm)))
        st.markdown(f"→ Longitud máxima ≈ **{l_max:.1f} m** (cobre, PVC, cos φ=0,9 orientativo)")

        st.divider()
        st.markdown("**Sección por caída de tensión** / **Sección por corriente (Iz)**")
        c1, c2, c3, c4, c5 = st.columns(5)
        sistema_s = c1.selectbox("Sistema", [SISTEMA_MONO, SISTEMA_TRI], key="bt_s_sistema")
        i_s = c2.number_input("Intensidad (A)", min_value=0.1, value=20.0, key="bt_s_i")
        l_s = c3.number_input("Longitud (m)", min_value=0.1, value=20.0, key="bt_s_l")
        du_s = c4.number_input("ΔU máx. (%)", min_value=0.1, value=3.0, key="bt_s_du")
        metodo_s = c5.selectbox("Método", METODOS_DISPONIBLES, index=1, key="bt_s_metodo")
        aisl_s = "XLPE/EPR" if metodo_s in (METODO_D, METODO_F) else st.selectbox(
            "Aislamiento", ["PVC", "XLPE/EPR"], key="bt_s_aisl")
        tension_s = 230.0 if sistema_s == SISTEMA_MONO else 400.0
        kappa_s = kappa_servicio("Cobre", aisl_s)
        n_carg_s = 2 if sistema_s == SISTEMA_MONO else 3
        s_por_du, _, _ = seccion_por_caida_tension(sistema_s, i_s, l_s, tension_s, 0.9, kappa_s, du_s, "Cobre")
        s_por_iz, iz_val, _, _ = seccion_por_criterio_termico(i_s, metodo_s, aisl_s, "Cobre", n_carg_s, 1.0)
        cc1, cc2 = st.columns(2)
        cc1.metric("Sección mínima por ΔU", f"{s_por_du:g} mm²" if s_por_du else "—")
        cc2.metric("Sección mínima por Iz", f"{s_por_iz:g} mm²" if s_por_iz else "—",
                   help=f"Iz tabla = {iz_val:.1f} A" if iz_val else None)
        if s_por_du and s_por_iz:
            st.markdown(f"→ Sección final adoptada (la mayor de ambas): **{max(s_por_du, s_por_iz):g} mm²**")

        st.divider()
        st.markdown("**Resistencia de un conductor**")
        c1, c2, c3, c4 = st.columns(4)
        cond_r = c1.selectbox("Conductor", ["Cobre", "Aluminio"], key="bt_r_cond")
        s_r = c2.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=4, key="bt_r_seccion")
        l_r = c3.number_input("Longitud (m)", min_value=0.1, value=100.0, key="bt_r_l")
        temp_r = c4.number_input("Temperatura (°C)", value=20.0, key="bt_r_temp")
        kappa_20 = CONDUCTIVIDAD_20C[cond_r]
        alpha_r = COEF_TEMP_RESIST[cond_r]
        kappa_t = kappa_20 / (1 + alpha_r * (temp_r - 20))
        r_cond = l_r / (kappa_t * s_r)
        st.markdown(f"→ R = L/(κ·S) = {l_r:g}/({kappa_t:.2f}×{s_r:g}) = **{r_cond:.4f} Ω** (ida simple)")

        st.divider()
        st.markdown("**Conversión AWG ↔ mm²**")
        c1, c2, c3 = st.columns(3)
        modo_awg = c1.radio("Convertir", ["AWG → mm²", "mm² → AWG"], key="bt_awg_modo", horizontal=True)
        if modo_awg == "AWG → mm²":
            awg_in = c2.selectbox("Calibre AWG", AWG_DISPONIBLES, index=10, key="bt_awg_in")
            c3.metric("Sección equivalente", f"{awg_a_mm2(awg_in):.3f} mm²")
        else:
            mm2_in = c2.number_input("Sección (mm²)", min_value=0.01, value=2.5, key="bt_mm2_in")
            awg_cercano, mm2_exacto = mm2_a_awg_mas_cercano(mm2_in)
            c3.metric("AWG más cercano", f"{awg_cercano} AWG ({mm2_exacto:.3f} mm²)")

        st.divider()
        st.markdown("**Protección contra sobrecarga** (Ib ≤ In ≤ Iz)")
        c1, c2, c3 = st.columns(3)
        ib_p = c1.number_input("Ib, intensidad de empleo (A)", min_value=0.1, value=18.0, key="bt_p_ib")
        in_p = c2.selectbox("In, calibre del interruptor (A)", CALIBRES_MAGNETOTERMICO, index=2, key="bt_p_in")
        iz_p = c3.number_input("Iz, admisible del cable (A)", min_value=0.1, value=21.0, key="bt_p_iz")
        cumple1 = ib_p <= in_p
        cumple2 = in_p <= iz_p
        st.markdown(f"→ Ib≤In: {'✅' if cumple1 else '❌'}  ·  In≤Iz: {'✅' if cumple2 else '❌'}  ·  "
                    f"conjunto: {'✅ Cumple ITC-BT-22' if (cumple1 and cumple2) else '❌ No cumple'}")

        st.markdown("**Protección contra sobrecarga y cortocircuito** (añade verificación térmica)")
        c1, c2, c3, c4 = st.columns(4)
        s_pc = c1.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=4, key="bt_pc_s")
        icc_pc = c2.number_input("Icc en el punto (kA)", min_value=0.01, value=4.0, key="bt_pc_icc")
        t_pc = c3.number_input("Tiempo de actuación (s)", min_value=0.001, value=0.1, format="%.3f", key="bt_pc_t")
        aisl_pc = c4.selectbox("Aislamiento", ["PVC", "XLPE/EPR"], key="bt_pc_aisl")
        cumple_pc, smin_pc = verificar_cortocircuito(s_pc, icc_pc, t_pc, "Cobre", aisl_pc)
        st.markdown(f"→ S_mín térmica = **{smin_pc:g} mm²** frente a {s_pc:g} mm² adoptados: "
                    f"{'✅ Cumple' if cumple_pc else '❌ No cumple'}")

    # ---------------------------------------------------------------- CORTOCIRCUITO
    with st.expander("⚡ Corriente de cortocircuito"):
        st.markdown("**Con datos de la red de BT** (se conoce la Icc o la Scc de origen)")
        c1, c2, c3, c4, c5 = st.columns(5)
        u_cc1 = c1.number_input("Tensión (V)", min_value=100.0, value=400.0, key="bt_cc1_u")
        icc_origen = c2.number_input("Icc en el origen (kA)", min_value=0.1, value=10.0, key="bt_cc1_icc0")
        s_cc1 = c3.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=6, key="bt_cc1_s")
        l_cc1 = c4.number_input("Longitud (m)", min_value=0.1, value=30.0, key="bt_cc1_l")
        n_carg_cc1 = c5.selectbox("Conductores cargados", [2, 3], index=1, key="bt_cc1_n")
        z_red = u_cc1 / (math.sqrt(3) * icc_origen * 1000.0)
        r_lin1, x_lin1 = impedancia_linea("Cobre", "PVC", s_cc1, l_cc1, n_carg_cc1)
        icc_final1 = icc_trifasico(u_cc1, z_red + r_lin1, x_lin1)
        st.markdown(f"→ Z_red = {z_red*1000:.2f} mΩ · Z_línea ≈ {r_lin1*1000:.2f} mΩ  →  "
                    f"**Icc en el punto final = {icc_final1/1000:.2f} kA**")

        st.divider()
        st.markdown("**Sin datos de la red de BT** (se asume red de potencia infinita en origen)")
        c1, c2, c3, c4 = st.columns(4)
        u_cc2 = c1.number_input("Tensión (V)", min_value=100.0, value=400.0, key="bt_cc2_u")
        s_cc2 = c2.selectbox("Sección (mm²)", SECCIONES_NORMALIZADAS, index=6, key="bt_cc2_s")
        l_cc2 = c3.number_input("Longitud (m)", min_value=0.1, value=30.0, key="bt_cc2_l")
        n_carg_cc2 = c4.selectbox("Conductores cargados", [2, 3], index=1, key="bt_cc2_n")
        r_lin2, x_lin2 = impedancia_linea("Cobre", "PVC", s_cc2, l_cc2, n_carg_cc2)
        icc_final2 = icc_trifasico(u_cc2, r_lin2, x_lin2)
        st.markdown(f"→ **Icc estimada = {icc_final2/1000:.2f} kA** (valor máximo teórico, orientativo al "
                    "no considerar la impedancia de la red aguas arriba)")

    # ---------------------------------------------------------------- TIERRAS
    with st.expander("🌍 Resistencia de tierras"):
        st.markdown("**Electrodos de tierra** (ITC-BT-18, Tabla 5)")
        c1, c2 = st.columns(2)
        with c1:
            claves_rho = list(RESISTIVIDAD_TERRENOS_REF.keys())
            terreno_sel = st.selectbox("Naturaleza del terreno", claves_rho,
                                        index=claves_rho.index("Terrenos cultivables y fértiles, "
                                                                "terraplenes compactos y húmedos"))
            rho_defecto = RESISTIVIDAD_TERRENOS_REF[terreno_sel] or 100.0
            rho_t = st.number_input("Resistividad ρ (Ω·m)", min_value=1.0, value=float(rho_defecto))
        with c2:
            tipo_electrodo = st.radio("Tipo de electrodo", ["Pica vertical", "Placa enterrada",
                                                             "Conductor enterrado horizontal"])
        if tipo_electrodo == "Pica vertical":
            long_pica = st.number_input("Longitud de la pica (m)", min_value=0.5, value=2.0, step=0.5)
            r_electrodo = resistencia_electrodo_pica(rho_t, long_pica)
            st.markdown(f"→ R = ρ/L = {rho_t:g}/{long_pica:g} = **{r_electrodo:.2f} Ω**")
        elif tipo_electrodo == "Placa enterrada":
            perimetro_placa = st.number_input("Perímetro de la placa (m)", min_value=0.5, value=2.0, step=0.1)
            r_electrodo = resistencia_electrodo_placa(rho_t, perimetro_placa)
            st.markdown(f"→ R = 0,8·ρ/P = 0,8×{rho_t:g}/{perimetro_placa:g} = **{r_electrodo:.2f} Ω**")
        else:
            long_cond = st.number_input("Longitud del conductor enterrado (m)", min_value=1.0, value=20.0)
            r_electrodo = resistencia_electrodo_conductor(rho_t, long_cond)
            st.markdown(f"→ R = 2·ρ/L = 2×{rho_t:g}/{long_cond:g} = **{r_electrodo:.2f} Ω**")

        st.divider()
        st.markdown("**Picas de tierra en paralelo**")
        c1, c2 = st.columns(2)
        r_una = c1.number_input("Resistencia de una pica (Ω)", min_value=0.1, value=75.0, key="bt_picas_r1")
        n_picas = c2.number_input("Número de picas (bien separadas, ≥2×L)", min_value=1, value=3, key="bt_picas_n")
        r_total_picas = resistencia_picas_paralelo(r_una, int(n_picas))
        st.markdown(f"→ R_total ≈ R/n = {r_una:g}/{n_picas:g} = **{r_total_picas:.2f} Ω** "
                    "(aproximación para picas bien separadas)")

    # ---------------------------------------------------------------- FOTOVOLTAICA RAPIDA
    with st.expander("☀️ Fotovoltaicas — cálculo rápido"):
        st.caption("Para el dimensionado completo (strings, inversor, cableado CC/CA, batería...) usa la "
                   "pestaña Fotovoltaica. Aquí solo estimaciones puntuales rápidas.")
        st.markdown("**Energía máxima diaria** (consumo)")
        c1, c2, c3 = st.columns(3)
        pot_ap = c1.number_input("Potencia del aparato (W)", min_value=1.0, value=100.0, key="bt_fv_pot")
        horas_ap = c2.number_input("Horas de uso al día", min_value=0.1, value=4.0, key="bt_fv_horas")
        n_ap = c3.number_input("Número de aparatos iguales", min_value=1, value=1, key="bt_fv_n")
        energia_dia = pot_ap * horas_ap * n_ap
        st.markdown(f"→ Energía diaria = **{energia_dia:.0f} Wh/día** ({energia_dia/1000:.2f} kWh/día)")

        st.divider()
        st.markdown("**Número de paneles solares**")
        c1, c2, c3, c4 = st.columns(4)
        energia_nec = c1.number_input("Energía necesaria (Wh/día)", min_value=1.0, value=3000.0, key="bt_fv_en")
        pot_panel = c2.number_input("Potencia del panel (Wp)", min_value=10.0, value=450.0, key="bt_fv_pp")
        hsp_fv = c3.number_input("HSP (h/día)", min_value=1.0, value=4.5, key="bt_fv_hsp")
        pr_fv = c4.number_input("PR", min_value=0.5, max_value=0.95, value=0.80, key="bt_fv_pr")
        n_paneles_bt = math.ceil(energia_nec / (pot_panel * hsp_fv * pr_fv))
        st.markdown(f"→ Nº de paneles ≈ **{n_paneles_bt}** paneles de {pot_panel:g} Wp")

        st.divider()
        st.markdown("**Baterías solares**")
        c1, c2, c3, c4 = st.columns(4)
        energia_bat = c1.number_input("Energía a acumular (Wh/día)", min_value=1.0, value=3000.0, key="bt_bat_e")
        dias_aut = c2.number_input("Días de autonomía", min_value=0.5, value=1.0, key="bt_bat_dias")
        v_bat = c3.number_input("Tensión del banco (V)", min_value=1.0, value=48.0, key="bt_bat_v")
        pd_bat = c4.number_input("Profundidad de descarga (%)", min_value=10.0, max_value=100.0, value=80.0,
                                  key="bt_bat_pd")
        capacidad_ah = (energia_bat * dias_aut) / (v_bat * (pd_bat / 100.0))
        st.markdown(f"→ Capacidad necesaria ≈ **{capacidad_ah:.0f} Ah** a {v_bat:g} V "
                    f"({capacidad_ah*v_bat/1000:.2f} kWh)")

    # ---------------------------------------------------------------- ELECTRICAS GENERALES
    with st.expander("📐 Eléctricas generales"):
        st.markdown("**Consumo eléctrico**")
        c1, c2, c3 = st.columns(3)
        pot_ce = c1.number_input("Potencia (W)", min_value=1.0, value=1500.0, key="bt_ce_p")
        horas_ce = c2.number_input("Horas de uso al día", min_value=0.1, value=2.0, key="bt_ce_h")
        precio_ce = c3.number_input("Precio kWh (€)", min_value=0.01, value=0.18, key="bt_ce_precio")
        kwh_dia = pot_ce / 1000 * horas_ce
        st.markdown(f"→ {kwh_dia:.3f} kWh/día · {kwh_dia*30:.1f} kWh/mes · "
                    f"**{_fmt_eur(kwh_dia*30*precio_ce)}/mes**")

        st.divider()
        st.markdown("**Ley de Ohm**")
        c1, c2 = st.columns(2)
        v_ohm = c1.number_input("Tensión V (V)", min_value=0.0, value=230.0, key="bt_ohm_v")
        i_ohm = c2.number_input("Intensidad I (A)", min_value=0.001, value=2.0, key="bt_ohm_i")
        st.markdown(f"→ Con V={v_ohm:g} V e I={i_ohm:g} A: R = V/I = **{v_ohm/max(i_ohm,1e-9):.2f} Ω**")

        st.divider()
        st.markdown("**Potencia eléctrica**")
        c1, c2, c3 = st.columns(3)
        v_pot = c1.number_input("Tensión (V)", min_value=0.0, value=230.0, key="bt_pot_v")
        i_pot = c2.number_input("Intensidad (A)", min_value=0.0, value=5.0, key="bt_pot_i")
        cosphi_pot = c3.slider("cos φ (1 si es CC o carga resistiva)", 0.1, 1.0, 1.0, key="bt_pot_cosphi")
        p_pot = v_pot * i_pot * cosphi_pot
        st.markdown(f"→ P = V·I·cos φ = **{p_pot:.1f} W**")

        st.divider()
        st.markdown("**Código de colores de resistencias** (4 bandas)")
        c1, c2, c3, c4 = st.columns(4)
        col1 = c1.selectbox("1ª banda", list(COLORES_DIGITO.keys()), index=1, key="bt_col1")
        col2 = c2.selectbox("2ª banda", list(COLORES_DIGITO.keys()), index=0, key="bt_col2")
        col3 = c3.selectbox("Multiplicador", list(COLORES_MULTIPLICADOR.keys()), index=2, key="bt_col3")
        col4 = c4.selectbox("Tolerancia", list(COLORES_TOLERANCIA.keys()), index=6, key="bt_col4")
        valor_r, tol_r = valor_resistencia_4_bandas(col1, col2, col3, col4)
        st.markdown(f"→ Valor = **{valor_r:g} Ω** ({tol_r})")

        st.divider()
        st.markdown("**Resistencias en paralelo**")
        texto_r = st.text_input("Valores separados por coma (Ω)", "100, 220, 330", key="bt_rp_texto")
        try:
            valores_r = [float(x.strip()) for x in texto_r.split(",") if x.strip()]
            req = 1.0 / sum(1.0 / v for v in valores_r) if valores_r else 0.0
            st.markdown(f"→ R_eq = **{req:.2f} Ω**")
        except (ValueError, ZeroDivisionError):
            st.warning("Introduce valores numéricos separados por comas.")

        st.divider()
        st.markdown("**Factor de potencia y batería de condensadores**")
        c1, c2, c3 = st.columns(3)
        p_fp = c1.number_input("Potencia activa P (kW)", min_value=0.1, value=10.0, key="bt_fp_p")
        cosphi_actual = c2.number_input("cos φ actual", min_value=0.1, max_value=1.0, value=0.75, key="bt_fp_actual")
        cosphi_obj = c3.number_input("cos φ objetivo", min_value=0.1, max_value=1.0, value=0.95, key="bt_fp_obj")
        tan_actual = math.tan(math.acos(cosphi_actual))
        tan_obj = math.tan(math.acos(cosphi_obj))
        q_condensador = p_fp * (tan_actual - tan_obj)
        st.markdown(f"→ Potencia reactiva de la batería de condensadores: **{max(q_condensador,0):.2f} kVAr**")

        st.divider()
        st.markdown("**Divisor de tensión**")
        c1, c2, c3 = st.columns(3)
        vin_dt = c1.number_input("Tensión de entrada Vin (V)", min_value=0.0, value=12.0, key="bt_dt_vin")
        r1_dt = c2.number_input("R1 (Ω)", min_value=0.01, value=1000.0, key="bt_dt_r1")
        r2_dt = c3.number_input("R2 (Ω)", min_value=0.01, value=1000.0, key="bt_dt_r2")
        vout_dt = vin_dt * r2_dt / (r1_dt + r2_dt)
        st.markdown(f"→ Vout = Vin·R2/(R1+R2) = **{vout_dt:.3f} V**")


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

    tab_calc, tab_formulas, tab_fv, tab_bt, tab_presu, tab_doc, tab_tablas, tab_metodo = st.tabs(
        ["🔌 Calculadora", "🧮 Fórmulas", "☀️ Fotovoltaica", "📐 Cálculos BT", "💰 Presupuesto",
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

    with tab_bt:
        _render_calculos_bt()

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
