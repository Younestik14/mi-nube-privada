"""Calculo de instalaciones fotovoltaicas (tramos de corriente continua
y corriente alterna).

La clase InstalacionFotovoltaica envuelve exactamente la misma logica
que la funcion original 'calcular_fv'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from calculos.protecciones import CalculadoraProtecciones
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


@dataclass
class InstalacionFotovoltaica:
    """Representa una instalacion fotovoltaica y su calculo asociado."""

    potencia_pico_kwp: float
    tension_mppt_v: float
    num_paneles: int
    longitud_dc_m: float
    longitud_ac_m: float
    potencia_inversor_kw: float
    tension_ac_v: float = 400

    def calcular(self) -> Dict[str, Any]:
        """Calcula intensidad, seccion, proteccion y CDT de los tramos DC y AC.

        Returns:
            Diccionario con las mismas claves que la version original:
            'Intensidad DC (A)', 'Seccion DC (mm2)', 'Proteccion DC (A)',
            'CDT DC (%)', 'Intensidad AC (A)', 'Seccion AC (mm2)',
            'Proteccion AC (A)' y 'CDT AC (%)'.
        """
        calc = CalculadoraProtecciones

        intensidad_dc = (self.potencia_pico_kwp * 1000) / self.tension_mppt_v if self.tension_mppt_v else 0
        seccion_dc, _ = calc.elegir_seccion_por_intensidad(intensidad_dc, "E", 1.0, 1.0)
        cdt_dc = calc.cdt_mono_pct(intensidad_dc, self.longitud_dc_m, seccion_dc, self.tension_mppt_v) if self.tension_mppt_v else 0

        intensidad_ac = calc.intensidad_tri(self.potencia_inversor_kw * 1000, self.tension_ac_v)
        seccion_ac, _ = calc.elegir_seccion_por_intensidad(intensidad_ac, "E", 1.0, 1.0)
        cdt_ac = calc.cdt_tri_pct(intensidad_ac, self.longitud_ac_m, seccion_ac, self.tension_ac_v)

        proteccion_dc = calc.elegir_proteccion(intensidad_dc)
        proteccion_ac = calc.elegir_proteccion(intensidad_ac)

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


def calcular_fv(
    potencia_pico_kwp: float,
    tension_mppt_v: float,
    num_paneles: int,
    longitud_dc_m: float,
    longitud_ac_m: float,
    potencia_inversor_kw: float,
    tension_ac_v: float = 400,
) -> Dict[str, Any]:
    """Funcion de conveniencia equivalente a la original 'calcular_fv'."""
    instalacion = InstalacionFotovoltaica(
        potencia_pico_kwp=potencia_pico_kwp,
        tension_mppt_v=tension_mppt_v,
        num_paneles=num_paneles,
        longitud_dc_m=longitud_dc_m,
        longitud_ac_m=longitud_ac_m,
        potencia_inversor_kw=potencia_inversor_kw,
        tension_ac_v=tension_ac_v,
    )
    return instalacion.calcular()
