"""Paquete con la lógica para el cálculo de promedios de notas."""

from .estudiante import Estudiante
from .historial import ErrorHistorial, Historial
from .promedio import (
    NOTA_APROBACION,
    NOTA_MAXIMA,
    NOTA_MINIMA,
    calcular_promedio,
    determinar_estado,
    ejecutar,
    pedir_cantidad_notas,
    pedir_nota,
    validar_nota,
)

__all__ = [
    "Estudiante",
    "ErrorHistorial",
    "Historial",
    "NOTA_APROBACION",
    "NOTA_MAXIMA",
    "NOTA_MINIMA",
    "calcular_promedio",
    "determinar_estado",
    "ejecutar",
    "pedir_cantidad_notas",
    "pedir_nota",
    "validar_nota",
]
