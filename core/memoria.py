"""Generacion del texto de la Memoria Tecnica de Diseno (MTD).

Reproduce exactamente la misma logica y el mismo texto que la funcion
original 'generar_memoria_texto'.
"""

from __future__ import annotations

from typing import Any, Dict, List

from datos.constantes import TIPOS_SUMINISTRO
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


class MemoriaTecnica:
    """Genera el texto de la Memoria Tecnica de Diseno (MTD) del proyecto."""

    @staticmethod
    def generar_texto(estado: Dict[str, Any]) -> str:
        """Construye el texto completo de la memoria a partir del estado del proyecto.

        Args:
            estado: Diccionario con, al menos, 'datos_proyecto' y 'tipo_suministro'.

        Returns:
            Texto de la memoria, con los apartados separados por saltos de linea.
        """
        datos = estado.get("datos_proyecto", {})
        tipo_sum = estado.get("tipo_suministro", list(TIPOS_SUMINISTRO.keys())[0])
        info_sum = TIPOS_SUMINISTRO.get(tipo_sum, {})
        partes: List[str] = []
        partes.append("MEMORIA TECNICA DE DISENO (MTD)")
        partes.append("")
        partes.append("1. OBJETO DE LA MEMORIA")
        partes.append(datos.get("objeto") or "Definir el objeto de la instalacion proyectada.")
        partes.append("")
        partes.append("2. TITULAR Y EMPLAZAMIENTO")
        partes.append(f"Titular: {datos.get('titular','-')}")
        partes.append(f"Emplazamiento: {datos.get('emplazamiento','-')}")
        partes.append(f"Referencia catastral / CUPS: {datos.get('referencia','-')}")
        partes.append("")
        partes.append("3. REGLAMENTACION Y DISPOSICIONES APLICADAS")
        partes.append(datos.get("normativa") or ("Reglamento Electrotecnico para Baja Tension (REBT) e Instrucciones Tecnicas Complementarias ITC-BT, "
                      "Normas UNE de aplicacion, Normas particulares de la empresa distribuidora y Ordenanzas municipales que resulten de aplicacion."))
        partes.append("")
        partes.append("4. DESCRIPCION GENERAL DE LA INSTALACION")
        partes.append(f"Tipo de suministro: {tipo_sum}")
        partes.append(info_sum.get("descripcion", ""))
        partes.append("Elementos principales de la instalacion:")
        for el in info_sum.get("elementos", []):
            partes.append(f" - {el}")
        partes.append("")
        partes.append(datos.get("descripcion") or "Describir potencia total prevista, uso del inmueble y caracteristicas generales.")
        partes.append("")
        partes.append("5. CALCULOS JUSTIFICATIVOS")
        partes.append("Los calculos justificativos de secciones, caidas de tension y protecciones de cada circuito, "
                      "instalacion fotovoltaica y motores se detallan en los Anexos de calculo adjuntos a la presente memoria.")
        partes.append("")
        partes.append("6. ANEXOS")
        partes.append(" - Anexo I: Calculos de circuitos de Baja Tension")
        partes.append(" - Anexo II: Calculos de instalacion Fotovoltaica")
        partes.append(" - Anexo III: Calculos de motores / instalacion industrial")
        partes.append(" - Anexo IV: Mediciones y Presupuesto")
        partes.append("")
        partes.append("7. CONCLUSION")
        partes.append("La instalacion descrita cumple con las prescripciones del Reglamento Electrotecnico para Baja Tension "
                      "y sus Instrucciones Tecnicas Complementarias, quedando sujeta a verificacion final por tecnico competente.")
        return "\n".join(partes)


def generar_memoria_texto(estado: Dict[str, Any]) -> str:
    return MemoriaTecnica.generar_texto(estado)
