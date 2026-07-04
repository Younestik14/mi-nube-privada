"""Configuracion global de la aplicacion Proyectista Electrico - REBT.

Este modulo centraliza los parametros de configuracion de la pagina de
Streamlit y cualquier ajuste global de la aplicacion. Mantiene la misma
configuracion que la version original, para no alterar el comportamiento
visible de la aplicacion.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# METADATOS DE LA APLICACION
# ---------------------------------------------------------------------------
NOMBRE_APP: str = "Proyectista Electrico - REBT"
ICONO_APP: str = "\u26A1"
LAYOUT_APP: str = "wide"

#: Numero maximo de entradas que se conservan en el historial de cambios.
MAX_HISTORIAL: int = 200

#: Nombre del logger raiz utilizado en toda la aplicacion.
NOMBRE_LOGGER_RAIZ: str = "proyectista_electrico"


def configurar_pagina() -> None:
    """Configura los parametros globales de la pagina de Streamlit.

    Debe llamarse una unica vez, como primera instruccion de Streamlit
    ejecutada por la aplicacion (antes de cualquier otro comando st.*).
    """
    st.set_page_config(
        page_title=NOMBRE_APP,
        page_icon=ICONO_APP,
        layout=LAYOUT_APP,
    )
