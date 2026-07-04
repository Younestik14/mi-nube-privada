"""Configuracion centralizada de logging para la aplicacion.

Proporciona un logger unico y coherente para todos los modulos del
proyecto, con niveles INFO, WARNING, ERROR y CRITICAL, evitando
duplicar manejadores cuando Streamlit vuelve a ejecutar el script.
"""

from __future__ import annotations

import logging
import sys

from config import NOMBRE_LOGGER_RAIZ

_CONFIGURADO = False


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Configura (una unica vez) el logger raiz de la aplicacion.

    Args:
        nivel: Nivel minimo de severidad que se mostrara (por defecto INFO).
            Los niveles disponibles, de menor a mayor severidad, son:
            DEBUG, INFO, WARNING, ERROR y CRITICAL.

    Returns:
        El logger raiz configurado.
    """
    global _CONFIGURADO
    logger_raiz = logging.getLogger(NOMBRE_LOGGER_RAIZ)

    if not _CONFIGURADO:
        logger_raiz.setLevel(nivel)
        manejador = logging.StreamHandler(sys.stdout)
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        manejador.setFormatter(formato)
        logger_raiz.addHandler(manejador)
        logger_raiz.propagate = False
        _CONFIGURADO = True

    return logger_raiz


def obtener_logger(nombre: str) -> logging.Logger:
    """Devuelve un logger hijo del logger raiz de la aplicacion.

    Args:
        nombre: Nombre del modulo que solicita el logger (normalmente __name__).

    Returns:
        Logger configurado y listo para usar.
    """
    configurar_logging()
    return logging.getLogger(f"{NOMBRE_LOGGER_RAIZ}.{nombre}")
