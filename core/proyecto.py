"""Estado global del proyecto (sesion de Streamlit).

La clase Proyecto centraliza la inicializacion, exportacion e
importacion del estado de la sesion, reproduciendo exactamente la
misma logica que las funciones originales 'inicializar_estado',
'estado_a_dict' y 'cargar_estado_desde_dict'.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

import pandas as pd
import streamlit as st

from core.historial import HistorialCambios
from datos.constantes import COLUMNAS_BT, COLUMNAS_MEDICION_MANUAL, COLUMNAS_MOTORES, TIPOS_SUMINISTRO
from datos.tablas import df_vacio
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


class Proyecto:
    """Gestiona el ciclo de vida del estado de un proyecto en 'st.session_state'."""

    @staticmethod
    def inicializar_estado() -> None:
        """Inicializa el estado de sesion la primera vez que se ejecuta la app.

        Si el proyecto ya estaba inicializado en esta sesion, no hace nada
        (evita reiniciar los datos introducidos por el usuario en cada re-run
        de Streamlit).
        """
        if "inicializado" in st.session_state:
            return
        st.session_state["inicializado"] = True
        st.session_state["datos_proyecto"] = {
            "titular": "", "emplazamiento": "", "referencia": "",
            "objeto": "", "normativa": "", "descripcion": "",
            "fecha": str(date.today()),
        }
        st.session_state["tipo_suministro"] = list(TIPOS_SUMINISTRO.keys())[0]
        st.session_state["modulos"] = {"bt": True, "fv": False, "industrial": False}
        st.session_state["df_bt"] = df_vacio(COLUMNAS_BT)
        st.session_state["df_motores"] = df_vacio(COLUMNAS_MOTORES)
        st.session_state["df_mediciones_manual"] = df_vacio(COLUMNAS_MEDICION_MANUAL)
        st.session_state["fv_datos"] = {
            "potencia_pico_kwp": 5.0, "tension_mppt_v": 600.0, "num_paneles": 12,
            "longitud_dc_m": 20.0, "longitud_ac_m": 15.0, "potencia_inversor_kw": 5.0,
            "tension_ac_v": 400.0,
        }
        st.session_state["historial"] = []
        HistorialCambios.registrar("Proyecto iniciado", "Se ha creado una nueva sesion de trabajo")
        logger.info("Nuevo proyecto inicializado en session_state")

    @staticmethod
    def estado_a_dict() -> Dict[str, Any]:
        """Serializa el estado actual del proyecto a un diccionario exportable."""
        return {
            "datos_proyecto": st.session_state.get("datos_proyecto", {}),
            "tipo_suministro": st.session_state.get("tipo_suministro"),
            "modulos": st.session_state.get("modulos", {}),
            "df_bt": st.session_state["df_bt"].to_dict("records"),
            "df_motores": st.session_state["df_motores"].to_dict("records"),
            "df_mediciones_manual": st.session_state["df_mediciones_manual"].to_dict("records"),
            "fv_datos": st.session_state.get("fv_datos", {}),
        }

    @staticmethod
    def cargar_estado_desde_dict(data: Dict[str, Any]) -> None:
        """Carga el estado del proyecto a partir de un diccionario (por ejemplo, un JSON importado)."""
        st.session_state["datos_proyecto"] = data.get("datos_proyecto", {})
        st.session_state["tipo_suministro"] = data.get("tipo_suministro", list(TIPOS_SUMINISTRO.keys())[0])
        st.session_state["modulos"] = data.get("modulos", {"bt": True, "fv": False, "industrial": False})
        st.session_state["df_bt"] = pd.DataFrame(data.get("df_bt", [])) if data.get("df_bt") else df_vacio(COLUMNAS_BT)
        st.session_state["df_motores"] = pd.DataFrame(data.get("df_motores", [])) if data.get("df_motores") else df_vacio(COLUMNAS_MOTORES)
        st.session_state["df_mediciones_manual"] = pd.DataFrame(data.get("df_mediciones_manual", [])) if data.get("df_mediciones_manual") else df_vacio(COLUMNAS_MEDICION_MANUAL)
        st.session_state["fv_datos"] = data.get("fv_datos", {})
        HistorialCambios.registrar("Proyecto importado", "Se ha cargado un archivo de proyecto JSON")
        logger.info("Proyecto cargado desde un diccionario externo (JSON importado)")


def inicializar_estado() -> None:
    Proyecto.inicializar_estado()


def estado_a_dict() -> Dict[str, Any]:
    return Proyecto.estado_a_dict()


def cargar_estado_desde_dict(data: Dict[str, Any]) -> None:
    Proyecto.cargar_estado_desde_dict(data)
