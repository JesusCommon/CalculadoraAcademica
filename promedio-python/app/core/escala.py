"""Escala de calificación configurable.

La escala predeterminada reproduce exactamente el comportamiento de la
versión 2.0: notas de 0.0 a 5.0 y aprobación desde 3.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Escala:
    """Rango válido de notas y umbral de aprobación.

    Attributes:
        minima: Nota mínima permitida.
        maxima: Nota máxima permitida.
        aprobacion: Promedio mínimo para aprobar.
        decimales: Cantidad de decimales usada al mostrar notas.
    """

    minima: float = 0.0
    maxima: float = 5.0
    aprobacion: float = 3.0
    decimales: int = 2

    def __post_init__(self) -> None:
        if isinstance(self.decimales, bool) or not isinstance(self.decimales, int):
            raise ValueError("La cantidad de decimales debe ser un número entero.")
        if not 0 <= self.decimales <= 6:
            raise ValueError("La cantidad de decimales debe estar entre 0 y 6.")

        for nombre, valor in (
            ("mínima", self.minima),
            ("máxima", self.maxima),
            ("aprobación", self.aprobacion),
        ):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError(f"La escala {nombre} debe ser numérica.")
            if not math.isfinite(float(valor)):
                raise ValueError(f"La escala {nombre} debe ser un número finito.")

        if self.minima >= self.maxima:
            raise ValueError("La nota mínima debe ser menor que la máxima.")
        if not self.minima <= self.aprobacion <= self.maxima:
            raise ValueError("La nota de aprobación debe estar dentro de la escala.")

    def validar(self, nota: object) -> float:
        """Valida una nota y la devuelve como ``float``.

        Raises:
            ValueError: Si no es numérica, no es finita o está fuera de rango.
        """
        if isinstance(nota, bool) or not isinstance(nota, (int, float)):
            raise ValueError("La nota debe ser un número válido.")

        valor = float(nota)

        if not math.isfinite(valor):
            raise ValueError("La nota debe ser un número válido.")

        if not self.minima <= valor <= self.maxima:
            raise ValueError(
                f"La nota debe estar entre {self.minima} y {self.maxima}."
            )

        return valor

    def estado(self, promedio: float) -> str:
        """Devuelve ``APROBADO`` o ``REPROBADO`` para el promedio indicado."""
        if promedio >= self.aprobacion:
            return "APROBADO"
        return "REPROBADO"

    def formatear(self, valor: float) -> str:
        """Formatea una nota con los decimales configurados."""
        return f"{valor:.{self.decimales}f}"


ESCALA_PREDETERMINADA = Escala()
