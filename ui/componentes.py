"""Componentes de interfaz reutilizables.

Incluye los helpers de campos persistentes (que evitan que el contenido
se vacie al escribir, reproduciendo exactamente la logica original) y
los componentes visuales de tarjetas, avisos y cajas de ayuda.
"""

from __future__ import annotations

from typing import Any, List, Optional

import streamlit as st

from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


def campo_texto_persistente(
    etiqueta: str,
    clave_estado: str,
    valor_por_defecto: str = "",
    help_text: Optional[str] = None,
    area: bool = False,
) -> str:
    """Crea un text_input/text_area cuyo contenido NUNCA se pierde al escribir.

    Se inicializa una unica vez en session_state y el widget se maneja
    exclusivamente a traves de su 'key' (sin volver a pasar 'value' en cada
    ejecucion, que es lo que provocaba que el campo se vaciara en la
    version anterior de la aplicacion).
    """
    if clave_estado not in st.session_state:
        st.session_state[clave_estado] = valor_por_defecto
    if area:
        st.text_area(etiqueta, key=clave_estado, help=help_text)
    else:
        st.text_input(etiqueta, key=clave_estado, help=help_text)
    return st.session_state[clave_estado]


def numero_persistente(
    etiqueta: str,
    clave_estado: str,
    valor_por_defecto: Any,
    help_text: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Igual que 'campo_texto_persistente' pero para campos numericos.

    Evita que el valor se reinicie de forma inesperada al interactuar con
    otros widgets de la pagina.
    """
    if clave_estado not in st.session_state:
        st.session_state[clave_estado] = valor_por_defecto
    st.number_input(etiqueta, key=clave_estado, help=help_text, **kwargs)
    return st.session_state[clave_estado]


def mostrar_aviso_normativa(texto: str) -> None:
    """Muestra una caja de aviso normativo (fondo ambar) con el texto indicado."""
    st.markdown(f'<div class="aviso-normativa">{texto}</div>', unsafe_allow_html=True)


def mostrar_caja_ayuda(texto: str) -> None:
    """Muestra una caja de ayuda contextual (fondo verde) con el texto indicado."""
    st.markdown(f'<div class="caja-ayuda">{texto}</div>', unsafe_allow_html=True)


def mostrar_encabezado(titulo: str, subtitulo: str = "") -> None:
    """Muestra la cabecera principal de la aplicacion con estilo de tarjeta degradada."""
    subtitulo_html = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(
        f'<div class="cabecera-app"><h1>{titulo}</h1>{subtitulo_html}</div>',
        unsafe_allow_html=True,
    )


def mostrar_historial(historial: List[dict], maximo: int = 15) -> None:
    """Muestra las ultimas entradas del historial de cambios en tarjetas compactas."""
    entradas = list(reversed(historial))[:maximo]
    if not entradas:
        st.caption("Todavia no se han registrado cambios en esta sesion.")
        return
    for h in entradas:
        st.markdown(
            f'<div class="caja-log"><b>{h["hora"]}</b> - {h["accion"]}<br><span>{h["detalle"]}</span></div>',
            unsafe_allow_html=True,
        )
