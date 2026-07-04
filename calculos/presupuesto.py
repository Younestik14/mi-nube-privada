"""Mediciones y presupuesto del proyecto electrico.

La clase Presupuesto agrupa la generacion automatica de mediciones a
partir de los circuitos calculados y el calculo del presupuesto final
(PEM, gastos generales, beneficio industrial e IVA), reproduciendo
exactamente las mismas formulas que las funciones originales
'generar_mediciones_auto' y 'calcular_presupuesto'.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from datos.constantes import PRECIOS_DEFECTO
from datos.tablas import df_vacio
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


class Presupuesto:
    """Genera mediciones automaticas y calcula el presupuesto del proyecto."""

    @staticmethod
    def clave_cable(seccion_mm2: float, num_conductores: int = 2) -> str:
        """Nombre descriptivo de un cable segun su seccion y numero de conductores."""
        return f"Cable Cu {num_conductores}x{seccion_mm2} mm2"

    @classmethod
    def generar_mediciones_auto(
        cls,
        df_bt_calc: Optional[pd.DataFrame],
        df_motores_calc: Optional[pd.DataFrame],
    ) -> pd.DataFrame:
        """Genera las mediciones automaticas de cable, tubo y protecciones.

        Args:
            df_bt_calc: Resultados calculados de los circuitos de Baja Tension.
            df_motores_calc: Resultados calculados de los motores.

        Returns:
            DataFrame de mediciones (Capitulo, Descripcion, Unidad, Cantidad,
            Precio unitario (EUR)).
        """
        filas = []
        if df_bt_calc is not None and not df_bt_calc.empty:
            for _, r in df_bt_calc.iterrows():
                longitud = float(r.get("Longitud (m)", 0) or 0)
                seccion = r.get("Seccion (mm2)", 1.5)
                proteccion = r.get("Proteccion (A)", 10)
                filas.append({"Capitulo": "Baja Tension", "Descripcion": cls.clave_cable(seccion), "Unidad": "m", "Cantidad": longitud, "Precio unitario (EUR)": round(seccion * PRECIOS_DEFECTO["cable_eur_m_mm2"], 2)})
                filas.append({"Capitulo": "Baja Tension", "Descripcion": f"Tubo protector para {cls.clave_cable(seccion)}", "Unidad": "m", "Cantidad": longitud, "Precio unitario (EUR)": PRECIOS_DEFECTO["tubo_eur_m"]})
                filas.append({"Capitulo": "Baja Tension", "Descripcion": f"Proteccion magnetotermica {proteccion} A", "Unidad": "ud", "Cantidad": 1, "Precio unitario (EUR)": PRECIOS_DEFECTO["proteccion_eur_ud"]})
        if df_motores_calc is not None and not df_motores_calc.empty:
            for _, r in df_motores_calc.iterrows():
                longitud = float(r.get("Longitud (m)", 0) or 0)
                seccion = r.get("Seccion (mm2)", 2.5)
                proteccion = r.get("Proteccion (A)", 16)
                filas.append({"Capitulo": "Industrial / Motores", "Descripcion": cls.clave_cable(seccion, 4), "Unidad": "m", "Cantidad": longitud, "Precio unitario (EUR)": round(seccion * PRECIOS_DEFECTO["cable_eur_m_mm2"] * 1.6, 2)})
                filas.append({"Capitulo": "Industrial / Motores", "Descripcion": f"Guardamotor / proteccion {proteccion} A", "Unidad": "ud", "Cantidad": 1, "Precio unitario (EUR)": PRECIOS_DEFECTO["proteccion_eur_ud"] * 1.8})
        return pd.DataFrame(filas) if filas else df_vacio(["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)"])

    @staticmethod
    def calcular_presupuesto(df_mediciones: Optional[pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Calcula el importe de cada medicion y el resumen del presupuesto.

        Returns:
            Tupla (DataFrame de mediciones con importe, diccionario resumen
            con PEM, Gastos generales, Beneficio industrial, Base de
            licitacion, IVA y TOTAL).
        """
        if df_mediciones is None or df_mediciones.empty:
            return df_vacio(["Capitulo", "Descripcion", "Unidad", "Cantidad", "Precio unitario (EUR)", "Importe (EUR)"]), {}
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


def clave_cable(seccion_mm2: float, num_conductores: int = 2) -> str:
    return Presupuesto.clave_cable(seccion_mm2, num_conductores)


def generar_mediciones_auto(df_bt_calc: Optional[pd.DataFrame], df_motores_calc: Optional[pd.DataFrame]) -> pd.DataFrame:
    return Presupuesto.generar_mediciones_auto(df_bt_calc, df_motores_calc)


def calcular_presupuesto(df_mediciones: Optional[pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[str, float]]:
    return Presupuesto.calcular_presupuesto(df_mediciones)
