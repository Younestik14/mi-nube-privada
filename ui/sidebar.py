"""Barra lateral de la aplicacion: datos del proyecto, tipo de
suministro, modulos activos, guardado/carga de proyecto e historial.

Reproduce exactamente la misma logica que el bloque original
'with st.sidebar:' del archivo app.py monolitico.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, Tuple

import streamlit as st

from core.historial import HistorialCambios
from core.proyecto import Proyecto
from datos.constantes import TIPOS_SUMINISTRO
from ui.componentes import campo_texto_persistente
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


def _seccion_datos_proyecto() -> Dict[str, Any]:
    """Renderiza los campos de datos generales del proyecto."""
    st.header("Datos del proyecto")
    dp = st.session_state["datos_proyecto"]
    dp["titular"] = campo_texto_persistente(
        "Titular", "campo_titular", dp.get("titular", ""),
        help_text="Nombre y apellidos (o razon social) de la persona o empresa propietaria de la instalacion.",
    )
    dp["emplazamiento"] = campo_texto_persistente(
        "Emplazamiento", "campo_emplazamiento", dp.get("emplazamiento", ""),
        help_text="Direccion completa donde se ubica la instalacion electrica (calle, numero, localidad, provincia).",
    )
    dp["referencia"] = campo_texto_persistente(
        "Referencia catastral / CUPS", "campo_referencia", dp.get("referencia", ""),
        help_text="Referencia catastral del inmueble o codigo CUPS del punto de suministro, si ya se dispone de el.",
    )
    dp["fecha"] = campo_texto_persistente(
        "Fecha", "campo_fecha", dp.get("fecha", str(date.today())),
        help_text="Fecha que aparecera en la memoria y en los documentos exportados.",
    )
    return dp


def _seccion_tipo_suministro() -> None:
    """Renderiza el selector del tipo de suministro electrico."""
    st.subheader("Tipo de suministro")
    opciones_suministro = list(TIPOS_SUMINISTRO.keys())
    if "campo_tipo_suministro" not in st.session_state:
        st.session_state["campo_tipo_suministro"] = st.session_state.get("tipo_suministro", opciones_suministro[0])
    st.selectbox(
        "Como se alimenta la instalacion",
        opciones_suministro,
        key="campo_tipo_suministro",
        help="Indica el esquema de acometida y medida de tu instalacion: CGP para un unico usuario, "
             "centralizacion de contadores en edificios con varios usuarios, transformador propio en "
             "Media Tension, o generacion propia/autoconsumo. Esto cambia los elementos del esquema unifilar.",
    )
    nuevo_tipo = st.session_state["campo_tipo_suministro"]
    if nuevo_tipo != st.session_state.get("tipo_suministro"):
        HistorialCambios.registrar("Cambio de tipo de suministro", f"{st.session_state.get('tipo_suministro')} -> {nuevo_tipo}")
    st.session_state["tipo_suministro"] = nuevo_tipo
    st.caption(TIPOS_SUMINISTRO[nuevo_tipo]["descripcion"])


def _seccion_modulos() -> Dict[str, bool]:
    """Renderiza las casillas de activacion de modulos (BT, FV, Industrial)."""
    st.subheader("Modulos activos")
    modulos = st.session_state["modulos"]
    modulos["bt"] = st.checkbox(
        "Baja Tension", value=modulos.get("bt", True),
        help="Activa el dimensionado de circuitos interiores de Baja Tension (enchufes, alumbrado, electrodomesticos, etc.).",
    )
    modulos["fv"] = st.checkbox(
        "Fotovoltaica", value=modulos.get("fv", False),
        help="Activa el dimensionado de una instalacion solar fotovoltaica (tramos de corriente continua y alterna).",
    )
    modulos["industrial"] = st.checkbox(
        "Industrial / Motores", value=modulos.get("industrial", False),
        help="Activa el dimensionado de motores y circuitos de uso industrial.",
    )
    return modulos


def _seccion_guardar_cargar_proyecto() -> None:
    """Renderiza los botones de descarga/carga del proyecto en formato JSON."""
    st.subheader("Proyecto (guardar / cargar)")
    proyecto_json = json.dumps(Proyecto.estado_a_dict(), indent=2, ensure_ascii=False)
    st.download_button(
        "Descargar proyecto (.json)", data=proyecto_json, file_name="proyecto_electrico.json", mime="application/json",
        help="Guarda todos los datos introducidos en un archivo para poder continuar mas tarde o compartirlo.",
    )
    archivo_proyecto = st.file_uploader(
        "Cargar proyecto (.json)", type=["json"], key="cargador_proyecto",
        help="Sube un archivo .json descargado previamente con este mismo boton para recuperar un proyecto guardado.",
    )
    if archivo_proyecto is not None:
        try:
            data = json.load(archivo_proyecto)
            Proyecto.cargar_estado_desde_dict(data)
            st.success("Proyecto cargado correctamente.")
        except Exception as e:
            logger.error("Error al importar proyecto JSON: %s", e)
            st.error(f"No se ha podido leer el archivo: {e}")


def _seccion_historial() -> None:
    """Renderiza el historial de cambios recientes de la sesion."""
    from ui.componentes import mostrar_historial

    st.subheader("Registro de cambios en tiempo real")
    mostrar_historial(st.session_state.get("historial", []), maximo=15)


def render_sidebar() -> Tuple[Dict[str, bool], Dict[str, Any]]:
    """Renderiza la barra lateral completa de la aplicacion.

    Returns:
        Tupla (modulos activos, datos del proyecto).
    """
    with st.sidebar:
        dp = _seccion_datos_proyecto()
        _seccion_tipo_suministro()
        modulos = _seccion_modulos()
        _seccion_guardar_cargar_proyecto()
        _seccion_historial()
    return modulos, dp
