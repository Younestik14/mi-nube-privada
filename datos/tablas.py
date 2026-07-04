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
    return pd.DataFrame({c: [] for c in columnas})
