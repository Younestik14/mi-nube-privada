"""Calculo de circuitos interiores de Baja Tension.

La clase CircuitoBT envuelve exactamente la misma logica que la funcion
original 'calcular_circuito_bt': mismas formulas, mismo orden de
evaluacion y mismo resultado para los mismos datos de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from calculos.protecciones import CalculadoraProtecciones
from datos.constantes import CDT_MAXIMA, FACTOR_AGRUPAMIENTO, FACTOR_TEMPERATURA
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


@dataclass
class CircuitoBT:
    """Representa un circuito interior de Baja Tension y su calculo.

    Los atributos se extraen de una fila de la tabla editable de la
    interfaz: potencia, tension, fases, longitud, metodo de instalacion,
    factor de agrupamiento, temperatura ambiente, aislamiento y uso.
    """

    potencia_w: float
    tension_v: float
    fases: str
    longitud_m: float
    metodo_instalacion: str
    factor_agrupamiento: int
    temp_ambiente_c: float
    aislamiento: str
    uso: str

    @classmethod
    def from_fila(cls, fila: Mapping[str, Any]) -> "CircuitoBT":
        """Construye un CircuitoBT a partir de una fila del editor de datos."""
        return cls(
            potencia_w=float(fila.get("Potencia (W)", 0) or 0),
            tension_v=float(fila.get("Tension (V)", 230) or 230),
            fases=fila.get("Fases", "Monofasico"),
            longitud_m=float(fila.get("Longitud (m)", 0) or 0),
            metodo_instalacion=fila.get("Metodo instalacion", "B1"),
            factor_agrupamiento=int(fila.get("Factor agrupamiento", 1) or 1),
            temp_ambiente_c=float(fila.get("Temp. ambiente (C)", 40) or 40),
            aislamiento=fila.get("Aislamiento", "PVC"),
            uso=fila.get("Uso", "Fuerza / Otros usos"),
        )

    @property
    def es_trifasico(self) -> bool:
        return str(self.fases).lower().startswith("tri")

    def calcular(self) -> Dict[str, Any]:
        """Calcula intensidad, seccion, proteccion, CDT y cumplimiento normativo.

        Returns:
            Diccionario con las mismas claves que la version original:
            'Intensidad (A)', 'Seccion (mm2)', 'Proteccion (A)', 'CDT (%)',
            'CDT max (%)' y 'Cumple'.
        """
        calc = CalculadoraProtecciones
        trifasico = self.es_trifasico

        if trifasico:
            intensidad = calc.intensidad_tri(self.potencia_w, self.tension_v)
        else:
            intensidad = calc.intensidad_mono(self.potencia_w, self.tension_v)

        tabla_temp = FACTOR_TEMPERATURA.get(self.aislamiento, FACTOR_TEMPERATURA["PVC"])
        temps = sorted(tabla_temp.keys())
        temp_cercana = min(temps, key=lambda t: abs(t - self.temp_ambiente_c))
        f_temp = tabla_temp[temp_cercana]
        f_agrup = FACTOR_AGRUPAMIENTO.get(self.factor_agrupamiento, 0.5)

        seccion_intensidad, iz = calc.elegir_seccion_por_intensidad(intensidad, self.metodo_instalacion, f_temp, f_agrup)
        cdt_max = CDT_MAXIMA.get(self.uso, 3.0)
        seccion_cdt, _cdt = calc.elegir_seccion_por_cdt(intensidad, self.longitud_m, self.tension_v, cdt_max, trifasico)

        seccion_final = max(seccion_intensidad, seccion_cdt)
        proteccion = calc.elegir_proteccion(intensidad, iz)

        if trifasico:
            cdt_final = calc.cdt_tri_pct(intensidad, self.longitud_m, seccion_final, self.tension_v)
        else:
            cdt_final = calc.cdt_mono_pct(intensidad, self.longitud_m, seccion_final, self.tension_v)
        cumple = (cdt_final <= cdt_max) and (iz is not None)

        return {
            "Intensidad (A)": round(intensidad, 2),
            "Seccion (mm2)": seccion_final,
            "Proteccion (A)": proteccion,
            "CDT (%)": round(cdt_final, 2),
            "CDT max (%)": cdt_max,
            "Cumple": "Si" if cumple else "Revisar",
        }


def calcular_circuito_bt(fila: Mapping[str, Any]) -> Dict[str, Any]:
    """Funcion de conveniencia equivalente a la original 'calcular_circuito_bt'.

    Se mantiene para poder usarla directamente con 'DataFrame.apply', igual
    que en la version original de la aplicacion.
    """
    return CircuitoBT.from_fila(fila).calcular()
