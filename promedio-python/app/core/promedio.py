"""Cálculos puros de promedios y estados."""

from __future__ import annotations

from .escala import ESCALA_PREDETERMINADA, Escala


def validar_nota(nota: object, escala: Escala | None = None) -> float:
    """Valida una nota según la escala indicada.

    La firma de un solo argumento se conserva para compatibilidad con 2.0.
    """
    return (escala or ESCALA_PREDETERMINADA).validar(nota)


def calcular_promedio(notas: list[float]) -> float:
    """Calcula el promedio aritmético de una lista de notas.

    Raises:
        ValueError: Si la lista está vacía.
    """
    if not notas:
        raise ValueError("No se puede calcular el promedio de una lista vacía.")

    return sum(notas) / len(notas)


def determinar_estado(promedio: float, escala: Escala | None = None) -> str:
    """Indica si el promedio alcanza el umbral de aprobación."""
    return (escala or ESCALA_PREDETERMINADA).estado(promedio)
