"""Registro de cambios en tiempo real (historial de acciones del usuario).

La clase HistorialCambios reproduce exactamente la misma logica que las
funciones originales 'registrar_cambio' y 'detectar_cambios_df'.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from config import MAX_HISTORIAL
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


class HistorialCambios:
    """Gestiona el historial de cambios del proyecto en 'st.session_state'."""

    CLAVE_ESTADO = "historial"

    @classmethod
    def registrar(cls, accion: str, detalle: str = "") -> None:
        """Anade una entrada al historial de cambios de la sesion actual.

        Args:
            accion: Descripcion breve de la accion realizada.
            detalle: Informacion adicional opcional sobre la accion.
        """
        if cls.CLAVE_ESTADO not in st.session_state:
            st.session_state[cls.CLAVE_ESTADO] = []
        st.session_state[cls.CLAVE_ESTADO].append({
            "hora": datetime.now().strftime("%H:%M:%S"),
            "accion": accion,
            "detalle": detalle,
        })
        # Mantener un historial acotado para no consumir memoria en exceso
        if len(st.session_state[cls.CLAVE_ESTADO]) > MAX_HISTORIAL:
            st.session_state[cls.CLAVE_ESTADO] = st.session_state[cls.CLAVE_ESTADO][-MAX_HISTORIAL:]
        logger.info("Historial: %s | %s", accion, detalle)

    @classmethod
    def detectar_cambios_df(cls, clave_estado: str, df_nuevo: pd.DataFrame, etiqueta: str) -> None:
        """Compara un DataFrame editado con su version anterior y registra el cambio.

        Args:
            clave_estado: Clave de 'st.session_state' donde se guarda el DataFrame.
            df_nuevo: DataFrame recien editado por el usuario.
            etiqueta: Nombre descriptivo utilizado en el mensaje del historial.
        """
        anterior: Optional[pd.DataFrame] = st.session_state.get(clave_estado)
        if anterior is None or not anterior.equals(df_nuevo):
            filas_antes = 0 if anterior is None else len(anterior)
            filas_ahora = len(df_nuevo)
            if filas_ahora > filas_antes:
                cls.registrar(f"Anadida fila en {etiqueta}", f"Total filas: {filas_ahora}")
            elif filas_ahora < filas_antes:
                cls.registrar(f"Eliminada fila en {etiqueta}", f"Total filas: {filas_ahora}")
            else:
                cls.registrar(f"Editado {etiqueta}", f"Total filas: {filas_ahora}")
            st.session_state[clave_estado] = df_nuevo.copy()


def registrar_cambio(accion: str, detalle: str = "") -> None:
    HistorialCambios.registrar(accion, detalle)


def detectar_cambios_df(clave_estado: str, df_nuevo: pd.DataFrame, etiqueta: str) -> None:
    HistorialCambios.detectar_cambios_df(clave_estado, df_nuevo, etiqueta)
