"""Tablas y constantes normativas del REBT / ITC-BT.

Todos los valores reproducen exactamente los utilizados en la version
original de la aplicacion. Se han documentado y tipado, pero NINGUN
valor numerico ni clave de diccionario ha sido modificado, para no
alterar los calculos electricos ni la logica del REBT.

IMPORTANTE: Estos valores son de referencia general. Antes de emitir un
proyecto o memoria oficial deben verificarse frente a la edicion vigente
del Reglamento Electrotecnico para Baja Tension (REBT) y sus
Instrucciones Tecnicas Complementarias (ITC-BT).
"""

from __future__ import annotations

from typing import Dict, List, Optional, TypedDict


#: Secciones normalizadas de conductor de cobre, en mm2.
SECCIONES_MM2: List[float] = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Intensidades admisibles (A) - Cu, aislamiento PVC/XLPE 70-90C, 2 conductores
# cargados, temperatura ambiente de referencia 40C aire / 25C terreno segun
# UNE 20460-5-523 y Tabla 1 de la ITC-BT-19. Metodos de instalacion A1,A2,B1,B2,
# C,D,E,F,G. VALORES ORIENTATIVOS: deben verificarse con la edicion vigente del
# REBT antes de emitir un proyecto o memoria oficial.
AMPACIDAD: Dict[float, Dict[str, Optional[float]]] = {
    1.5: {"A1": 14.5, "A2": 14, "B1": 17.5, "B2": 16.5, "C": 19.5, "D": 22, "E": 22, "F": 23, "G": 26},
    2.5: {"A1": 19.5, "A2": 18.5, "B1": 24, "B2": 23, "C": 27, "D": 29, "E": 30, "F": 31, "G": 36},
    4: {"A1": 26, "A2": 25, "B1": 32, "B2": 30, "C": 36, "D": 38, "E": 40, "F": 42, "G": 49},
    6: {"A1": 34, "A2": 32, "B1": 41, "B2": 38, "C": 46, "D": 47, "E": 51, "F": 54, "G": 63},
    10: {"A1": 46, "A2": 43, "B1": 57, "B2": 52, "C": 63, "D": 63, "E": 70, "F": 75, "G": 86},
    16: {"A1": 61, "A2": 57, "B1": 76, "B2": 69, "C": 85, "D": 81, "E": 94, "F": 100, "G": 115},
    25: {"A1": 80, "A2": 75, "B1": 96, "B2": 90, "C": 112, "D": 104, "E": 119, "F": 127, "G": 149},
    35: {"A1": 99, "A2": 92, "B1": 119, "B2": 111, "C": 138, "D": 125, "E": 147, "F": 158, "G": 185},
    50: {"A1": 119, "A2": 110, "B1": 144, "B2": 133, "C": 168, "D": 148, "E": 178, "F": 192, "G": 225},
    70: {"A1": 151, "A2": 139, "B1": 184, "B2": 171, "C": 213, "D": 183, "E": 229, "F": 246, "G": 289},
    95: {"A1": 182, "A2": 167, "B1": 223, "B2": 207, "C": 258, "D": 216, "E": 278, "F": 298, "G": 352},
    120: {"A1": 210, "A2": 192, "B1": 259, "B2": 239, "C": 299, "D": 246, "E": 322, "F": 346, "G": 410},
    150: {"A1": 240, "A2": 219, "B1": None, "B2": 262, "C": 344, "D": None, "E": 371, "F": 399, "G": 473},
    185: {"A1": 273, "A2": 248, "B1": None, "B2": 296, "C": 392, "D": None, "E": 424, "F": 456, "G": 542},
    240: {"A1": 321, "A2": 291, "B1": None, "B2": 344, "C": 461, "D": None, "E": 500, "F": 538, "G": 641},
    300: {"A1": 367, "A2": 334, "B1": None, "B2": 392, "C": 530, "D": None, "E": 576, "F": 621, "G": 741},
}

METODOS_INSTALACION: Dict[str, str] = {
    "A1": "Conductores aislados en tubo empotrado en pared aislante (interior)",
    "A2": "Cable multiconductor en tubo empotrado en pared aislante",
    "B1": "Conductores aislados en tubo sobre pared o empotrado en obra",
    "B2": "Cable multiconductor en tubo sobre pared o empotrado en obra",
    "C": "Cable multiconductor directamente sobre la pared o techo",
    "D": "Cable multiconductor en conducto enterrado o directamente enterrado",
    "E": "Cable multiconductor al aire libre, bandeja perforada / escalera",
    "F": "Cables unipolares en contacto mutuo, al aire libre (bandeja)",
    "G": "Cables unipolares separados, al aire libre (bandeja / soportes)",
}

FACTOR_TEMPERATURA: Dict[str, Dict[int, float]] = {
    "PVC": {20: 1.22, 25: 1.17, 30: 1.12, 35: 1.06, 40: 1.00, 45: 0.94, 50: 0.87, 55: 0.79, 60: 0.71},
    "XLPE": {20: 1.15, 25: 1.12, 30: 1.08, 35: 1.04, 40: 1.00, 45: 0.96, 50: 0.91, 55: 0.87, 60: 0.82},
}

FACTOR_AGRUPAMIENTO: Dict[int, float] = {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60, 6: 0.57, 7: 0.54, 8: 0.52, 9: 0.50}

PROTECCIONES_NORMALIZADAS: List[int] = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]

CDT_MAXIMA: Dict[str, float] = {
    "Alumbrado": 3.0,
    "Fuerza / Otros usos": 5.0,
    "Derivacion individual": 1.5,
    "Linea general de alimentacion": 0.5,
    "Instalacion fotovoltaica (CC+CA)": 1.5,
}

#: 1/rho (m/ohm*mm2) a 20C, referencia Cu.
RESISTIVIDAD_INV_CU: float = 56.0

FACTORES_ARRANQUE_MOTOR: Dict[str, float] = {
    "directo": 1.25,
    "estrella_triangulo": 1.25,
    "arrancador_suave": 1.10,
    "variador": 1.00,
}

#: Precios por defecto utilizados para mediciones y presupuesto (EUR).
#: Se mantiene como diccionario mutable a proposito: la pestana de
#: Presupuesto permite al usuario editar estos valores en tiempo real,
#: igual que en la version original de la aplicacion.
PRECIOS_DEFECTO: Dict[str, float] = {
    "cable_eur_m_mm2": 0.19,
    "tubo_eur_m": 1.35,
    "proteccion_eur_ud": 14.0,
    "mano_obra_eur_h": 24.0,
    "gastos_generales_pct": 13.0,
    "beneficio_industrial_pct": 6.0,
    "iva_pct": 21.0,
}


class InfoTipoSuministro(TypedDict):
    """Estructura descriptiva de un tipo de suministro electrico."""

    descripcion: str
    elementos: List[str]


TIPOS_SUMINISTRO: Dict[str, InfoTipoSuministro] = {
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

COLUMNAS_BT: List[str] = [
    "Circuito", "Descripcion", "Tipo", "Potencia (W)", "Tension (V)", "Fases", "Longitud (m)",
    "Metodo instalacion", "Factor agrupamiento", "Temp. ambiente (C)", "Aislamiento", "Uso",
]

COLUMNAS_MOTORES: List[str] = [
    "Motor", "Descripcion", "Potencia (kW)", "Tension (V)", "Fases", "Rendimiento (%)",
    "cos phi", "Longitud (m)", "Metodo arranque", "Metodo instalacion",
]

COLUMNAS_MEDICION_MANUAL: List[str] = ["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"]
