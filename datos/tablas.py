"""Utilidades para construir tablas (DataFrames) usadas en la aplicacion.

Se mantiene la misma logica que la version original: un unico helper
generico 'df_vacio' que construye un DataFrame vacio a partir de una
lista de columnas, reutilizado por los distintos modulos de calculo y
por el estado del proyecto.
"""

from __future__ import annotations

from typing import List

import pandas as pd


def df_vacio(columnas: List[str]) -> pd.DataFrame:
    """Crea un DataFrame vacio con las columnas indicadas.

    Args:
        columnas: Lista de nombres de columna.

    Returns:
        DataFrame vacio (sin filas) con esas columnas.
    """
    # Se usa dtype "object" en vez de dejar que pandas infiera float64 por
    # defecto en columnas vacias; con float64, los widgets de seleccion
    # (SelectboxColumn) no podian guardar valores de texto en filas nuevas.
    return pd.DataFrame({c: pd.Series(dtype="object") for c in columnas})
