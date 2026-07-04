"""Proyectista Electrico - REBT.

Punto de entrada de la aplicacion de Streamlit. Este archivo se limita
a orquestar los distintos modulos de la aplicacion (configuracion,
estilos, estado del proyecto, barra lateral y panel principal), sin
contener logica de calculo ni de interfaz detallada: toda esa logica
vive en los paquetes 'calculos', 'core', 'datos', 'ui' y 'utils'.

Se mantienen exactamente las mismas funcionalidades que la version
original monolitica de la aplicacion.
"""

from __future__ import annotations

import streamlit as st

from config import configurar_pagina
from core.proyecto import Proyecto
from ui.componentes import mostrar_aviso_normativa, mostrar_encabezado
from ui.dashboard import render_dashboard
from ui.estilos import aplicar_estilos
from ui.sidebar import render_sidebar
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)

TEXTO_AVISO_NORMATIVA = (
    "Esta herramienta calcula valores orientativos de secciones, "
    "protecciones y caidas de tension conforme a criterios generales del REBT / ITC-BT. "
    "Las tablas de intensidades admisibles y demas valores normativos deben verificarse siempre "
    "frente a la edicion vigente del Reglamento Electrotecnico para Baja Tension antes de su uso "
    "en una memoria o proyecto oficial, y el resultado final debe ser revisado y firmado por un "
    "tecnico competente."
)


def main() -> None:
    """Punto de entrada principal de la aplicacion Streamlit."""
    configurar_pagina()
    aplicar_estilos()
    Proyecto.inicializar_estado()

    mostrar_encabezado(
        "⚡ Proyectista Electrico - REBT",
        "Dimensionado, mediciones, presupuesto y documentacion de instalaciones en Baja Tension",
    )
    mostrar_aviso_normativa(TEXTO_AVISO_NORMATIVA)

    modulos, dp = render_sidebar()
    render_dashboard(modulos, dp)

    logger.info("Render de la aplicacion completado correctamente")


if __name__ == "__main__":
    main()
