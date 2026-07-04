"""Calculo de motores e instalaciones industriales.

La clase Motor envuelve exactamente la misma logica que la funcion
original 'calcular_motor': mismas formulas, mismo orden de evaluacion y
mismo resultado para los mismos datos de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from calculos.protecciones import CalculadoraProtecciones
from datos.constantes import CDT_MAXIMA, FACTORES_ARRANQUE_MOTOR
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


@dataclass
class Motor:
    """Representa un motor (o circuito industrial) y su calculo asociado."""

    potencia_kw: float
    tension_v: float
    fases: str
    rendimiento_pct: float
    cos_phi: float
    longitud_m: float
    metodo_arranque: str
    metodo_instalacion: str

    @classmethod
    def from_fila(cls, fila: Mapping[str, Any]) -> "Motor":
        """Construye un Motor a partir de una fila del editor de datos."""
        return cls(
            potencia_kw=float(fila.get("Potencia (kW)", 0) or 0),
            tension_v=float(fila.get("Tension (V)", 400) or 400),
            fases=fila.get("Fases", "Trifasico"),
            rendimiento_pct=float(fila.get("Rendimiento (%)", 90) or 90),
            cos_phi=float(fila.get("cos phi", 0.85) or 0.85),
            longitud_m=float(fila.get("Longitud (m)", 0) or 0),
            metodo_arranque=fila.get("Metodo arranque", "directo"),
            metodo_instalacion=fila.get("Metodo instalacion", "B1"),
        )

    @property
    def es_trifasico(self) -> bool:
        return str(self.fases).lower().startswith("tri")

    def calcular(self) -> Dict[str, Any]:
        """Calcula intensidad nominal, intensidad de calculo, seccion,
        proteccion y CDT del motor.

        Returns:
            Diccionario con las mismas claves que la version original:
            'Intensidad nominal (A)', 'Intensidad de calculo (A)',
            'Seccion (mm2)', 'Proteccion (A)', 'CDT (%)' y 'CDT max (%)'.
        """
        calc = CalculadoraProtecciones
        rendimiento = self.rendimiento_pct / 100
        potencia_absorbida_w = (self.potencia_kw * 1000) / rendimiento if rendimiento else 0
        trifasico = self.es_trifasico

        if trifasico:
            intensidad_nominal = calc.intensidad_tri(potencia_absorbida_w, self.tension_v, self.cos_phi)
        else:
            intensidad_nominal = calc.intensidad_mono(potencia_absorbida_w, self.tension_v, self.cos_phi)

        factor_arranque = FACTORES_ARRANQUE_MOTOR.get(self.metodo_arranque, 1.25)
        intensidad_calculo = intensidad_nominal * factor_arranque

        seccion, iz = calc.elegir_seccion_por_intensidad(intensidad_calculo, self.metodo_instalacion, 1.0, 1.0)
        cdt_max = CDT_MAXIMA["Fuerza / Otros usos"]
        seccion_cdt, cdt = calc.elegir_seccion_por_cdt(intensidad_calculo, self.longitud_m, self.tension_v, cdt_max, trifasico, self.cos_phi)
        seccion_final = max(seccion, seccion_cdt)
        proteccion = calc.elegir_proteccion(intensidad_calculo, iz)

        return {
            "Intensidad nominal (A)": round(intensidad_nominal, 2),
            "Intensidad de calculo (A)": round(intensidad_calculo, 2),
            "Seccion (mm2)": seccion_final,
            "Proteccion (A)": proteccion,
            "CDT (%)": round(cdt, 2),
            "CDT max (%)": cdt_max,
        }


def calcular_motor(fila: Mapping[str, Any]) -> Dict[str, Any]:
    """Funcion de conveniencia equivalente a la original 'calcular_motor'."""
    return Motor.from_fila(fila).calcular()
