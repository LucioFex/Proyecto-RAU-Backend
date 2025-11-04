"""
Servicio para proporcionar opciones utilizadas en el onboarding.

Actualmente devuelve listas estáticas de carreras universitarias, años
académicos y años de graduación. En un futuro podría consultar una base
de datos para obtener estos valores de manera dinámica.
"""

from __future__ import annotations

from datetime import datetime
from typing import List


class OptionsService:
    """Proporciona las opciones de selección para el proceso de onboarding."""

    def get_careers(self) -> List[str]:
        """
        Devuelve una lista de carreras disponibles. Esta lista puede
        modificarse según las necesidades de la institución.
        """
        return [
            "Ing. en Informática",
            "Abogacía",
            "Lic. en Economía",
            "Lic. en Marketing",
            "Física",
            "Química",
            "Lic. en Finanzas",
            "Lic. en Negocios Digitales",
        ]

    def get_years(self) -> List[str]:
        """
        Devuelve una lista de años académicos posibles.
        """
        return [
            "1º Año",
            "2º Año",
            "3º Año",
            "4º Año",
            "5º Año",
        ]

    def get_grad_years(self) -> List[str]:
        """
        Devuelve una lista de años de graduación estimados. Genera
        dinámicamente los próximos ocho años a partir del año en curso.
        """
        current_year = datetime.now().year
        return [str(current_year + offset) for offset in range(0, 8)]
