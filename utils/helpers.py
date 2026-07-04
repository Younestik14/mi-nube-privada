"""Funciones auxiliares genericas, reutilizables en toda la aplicacion.

Estas utilidades son puramente auxiliares (formato, conversion segura de
tipos): no participan en ningun calculo electrico ni alteran la logica
REBT del resto de modulos.
"""

from __future__ import annotations

from typing import Any, Optional


def safe_float(valor: Any, defecto: float = 0.0) -> float:
    """Convierte un valor a float de forma segura, devolviendo un valor por defecto si falla.

    Args:
        valor: Valor a convertir (puede venir de un campo vacio, texto, etc.).
        defecto: Valor a devolver si la conversion no es posible.

    Returns:
        El valor convertido a float, o 'defecto' si no se pudo convertir.
    """
    try:
        if valor is None or valor == "":
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def texto_o_guion(valor: Optional[str]) -> str:
    """Devuelve el texto indicado, o un guion '-' si esta vacio o es None."""
    if valor is None or not str(valor).strip():
        return "-"
    return str(valor)


def formatear_moneda(valor: float, simbolo: str = "EUR") -> str:
    """Formatea un importe numerico con separador de miles y dos decimales.

    Ejemplo: formatear_moneda(1234.5) -> '1,234.50 EUR'
    """
    return f"{valor:,.2f} {simbolo}"
