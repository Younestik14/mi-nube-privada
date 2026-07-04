"""Motor de calculo compartido: intensidades, caidas de tension, eleccion
de seccion de conductor y eleccion de proteccion normalizada.

Esta clase centraliza la logica comun que utilizan los modulos de Baja
Tension, Motores y Fotovoltaica, evitando duplicar las mismas formulas en
varios sitios (principio DRY). Las formulas y el orden de evaluacion son
IDENTICOS a los de la version original de la aplicacion: no se ha
modificado ningun calculo electrico ni la logica del REBT.
"""

from __future__ import annotations

from typing import Optional, Tuple

from datos.constantes import AMPACIDAD, PROTECCIONES_NORMALIZADAS, RESISTIVIDAD_INV_CU, SECCIONES_MM2
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


class CalculadoraProtecciones:
    """Agrupa las formulas electricas basicas de intensidad, caida de
    tension, eleccion de seccion y eleccion de proteccion."""

    @staticmethod
    def intensidad_mono(potencia_w: float, tension_v: float, cos_phi: float = 0.95) -> float:
        """Intensidad de un circuito monofasico (A)."""
        if tension_v <= 0:
            return 0.0
        return potencia_w / (tension_v * cos_phi)

    @staticmethod
    def intensidad_tri(potencia_w: float, tension_v: float, cos_phi: float = 0.95) -> float:
        """Intensidad de un circuito trifasico (A)."""
        if tension_v <= 0:
            return 0.0
        return potencia_w / (1.732 * tension_v * cos_phi)

    @staticmethod
    def cdt_mono_pct(intensidad_a: float, longitud_m: float, seccion_mm2: float, tension_v: float, cos_phi: float = 0.95) -> float:
        """Caida de tension porcentual en un tramo monofasico."""
        if seccion_mm2 <= 0 or tension_v <= 0:
            return 0.0
        caida_v = (2 * longitud_m * intensidad_a) / (RESISTIVIDAD_INV_CU * seccion_mm2)
        return (caida_v / tension_v) * 100

    @staticmethod
    def cdt_tri_pct(intensidad_a: float, longitud_m: float, seccion_mm2: float, tension_v: float, cos_phi: float = 0.95) -> float:
        """Caida de tension porcentual en un tramo trifasico."""
        if seccion_mm2 <= 0 or tension_v <= 0:
            return 0.0
        caida_v = (1.732 * longitud_m * intensidad_a) / (RESISTIVIDAD_INV_CU * seccion_mm2)
        return (caida_v / tension_v) * 100

    @classmethod
    def elegir_seccion_por_intensidad(
        cls,
        intensidad_a: float,
        metodo: str,
        factor_temp: float = 1.0,
        factor_agrup: float = 1.0,
    ) -> Tuple[float, Optional[float]]:
        """Elige la seccion normalizada minima que soporta la intensidad dada."""
        for s in SECCIONES_MM2:
            fila = AMPACIDAD.get(s, {})
            iz = fila.get(metodo)
            if iz is None:
                continue
            iz_corregida = iz * factor_temp * factor_agrup
            if iz_corregida >= intensidad_a:
                return s, iz_corregida
        return SECCIONES_MM2[-1], None

    @classmethod
    def elegir_seccion_por_cdt(
        cls,
        intensidad_a: float,
        longitud_m: float,
        tension_v: float,
        cdt_max_pct: float,
        trifasico: bool = False,
        cos_phi: float = 0.95,
    ) -> Tuple[float, float]:
        """Elige la seccion normalizada minima que respeta la caida de tension maxima."""
        for s in SECCIONES_MM2:
            if trifasico:
                cdt = cls.cdt_tri_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
            else:
                cdt = cls.cdt_mono_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
            if cdt <= cdt_max_pct:
                return s, cdt
        s = SECCIONES_MM2[-1]
        if trifasico:
            cdt = cls.cdt_tri_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
        else:
            cdt = cls.cdt_mono_pct(intensidad_a, longitud_m, s, tension_v, cos_phi)
        return s, cdt

    @staticmethod
    def elegir_proteccion(intensidad_a: float, iz_a: Optional[float] = None) -> int:
        """Elige la proteccion magnetotermica normalizada adecuada."""
        for p in PROTECCIONES_NORMALIZADAS:
            if p >= intensidad_a:
                if iz_a is not None and p > iz_a:
                    continue
                return p
        return PROTECCIONES_NORMALIZADAS[-1]


# ---------------------------------------------------------------------------
# Funciones de conveniencia (compatibilidad con el uso funcional del resto
# de modulos de calculo)
# ---------------------------------------------------------------------------

def intensidad_mono(potencia_w: float, tension_v: float, cos_phi: float = 0.95) -> float:
    return CalculadoraProtecciones.intensidad_mono(potencia_w, tension_v, cos_phi)


def intensidad_tri(potencia_w: float, tension_v: float, cos_phi: float = 0.95) -> float:
    return CalculadoraProtecciones.intensidad_tri(potencia_w, tension_v, cos_phi)


def cdt_mono_pct(intensidad_a: float, longitud_m: float, seccion_mm2: float, tension_v: float, cos_phi: float = 0.95) -> float:
    return CalculadoraProtecciones.cdt_mono_pct(intensidad_a, longitud_m, seccion_mm2, tension_v, cos_phi)


def cdt_tri_pct(intensidad_a: float, longitud_m: float, seccion_mm2: float, tension_v: float, cos_phi: float = 0.95) -> float:
    return CalculadoraProtecciones.cdt_tri_pct(intensidad_a, longitud_m, seccion_mm2, tension_v, cos_phi)


def elegir_seccion_por_intensidad(intensidad_a: float, metodo: str, factor_temp: float = 1.0, factor_agrup: float = 1.0) -> Tuple[float, Optional[float]]:
    return CalculadoraProtecciones.elegir_seccion_por_intensidad(intensidad_a, metodo, factor_temp, factor_agrup)


def elegir_seccion_por_cdt(intensidad_a: float, longitud_m: float, tension_v: float, cdt_max_pct: float, trifasico: bool = False, cos_phi: float = 0.95) -> Tuple[float, float]:
    return CalculadoraProtecciones.elegir_seccion_por_cdt(intensidad_a, longitud_m, tension_v, cdt_max_pct, trifasico, cos_phi)


def elegir_proteccion(intensidad_a: float, iz_a: Optional[float] = None) -> int:
    return CalculadoraProtecciones.elegir_proteccion(intensidad_a, iz_a)
