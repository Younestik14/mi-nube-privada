"""Validaciones de entrada de usuario.

Estas funciones son ADITIVAS: unicamente detectan valores fuera de
rango o incoherentes para poder avisar al usuario con un mensaje claro
en la interfaz. NO modifican ni sustituyen ningun calculo electrico; los
resultados numericos de la aplicacion son exactamente los mismos con o
sin estas validaciones.
"""

from __future__ import annotations

from typing import List, Optional

from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


def validar_potencia(valor: Optional[float], campo: str = "Potencia") -> Optional[str]:
    """Valida que una potencia sea un numero positivo.

    Returns:
        Mensaje de aviso si el valor no es valido, o None si es correcto.
    """
    if valor is None:
        return f"{campo}: el campo esta vacio."
    if valor < 0:
        return f"{campo}: no puede ser negativa ({valor})."
    if valor == 0:
        return f"{campo}: es igual a cero; revisa si es correcto."
    return None


def validar_longitud(valor: Optional[float], campo: str = "Longitud") -> Optional[str]:
    """Valida que una longitud de cable sea un numero positivo."""
    if valor is None:
        return f"{campo}: el campo esta vacio."
    if valor < 0:
        return f"{campo}: no puede ser negativa ({valor} m)."
    return None


def validar_tension(valor: Optional[float], campo: str = "Tension") -> Optional[str]:
    """Valida que una tension sea un numero positivo dentro de un rango razonable."""
    if valor is None:
        return f"{campo}: el campo esta vacio."
    if valor <= 0:
        return f"{campo}: debe ser mayor que cero ({valor} V)."
    if valor > 36000:
        return f"{campo}: valor inusualmente alto ({valor} V); revisa la unidad introducida."
    return None


def validar_texto_no_vacio(valor: Optional[str], campo: str) -> Optional[str]:
    """Valida que un campo de texto obligatorio no este vacio."""
    if valor is None or not str(valor).strip():
        return f"{campo}: este campo no deberia quedar vacio antes de generar la memoria o el presupuesto."
    return None


def validar_circuito_bt(fila: dict) -> List[str]:
    """Ejecuta todas las validaciones aplicables a una fila de circuito de Baja Tension.

    Returns:
        Lista de mensajes de aviso (vacia si no hay incidencias).
    """
    avisos: List[str] = []
    for validador, clave, etiqueta in (
        (validar_potencia, "Potencia (W)", "Potencia"),
        (validar_tension, "Tension (V)", "Tension"),
        (validar_longitud, "Longitud (m)", "Longitud"),
    ):
        mensaje = validador(fila.get(clave), etiqueta)
        if mensaje:
            avisos.append(mensaje)
    return avisos
