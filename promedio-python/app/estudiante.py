"""Modelo de un estudiante y sus notas.

Este módulo contiene únicamente lógica de negocio: no depende de Tkinter ni
de la consola. Reutiliza las funciones de ``app.promedio`` para calcular el
promedio y determinar el estado (aprobado/reprobado).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .promedio import calcular_promedio, determinar_estado, validar_nota

ESTADO_SIN_NOTAS = "SIN NOTAS"


@dataclass
class Estudiante:
    """Representa a un estudiante con su nombre y su lista de notas.

    Attributes:
        nombre: Nombre del estudiante (no puede estar vacío).
        notas: Notas del estudiante, todas dentro del rango de 0 a 5.
    """

    nombre: str
    notas: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normaliza y valida los datos recibidos."""
        self.nombre = str(self.nombre).strip()
        if not self.nombre:
            raise ValueError("El nombre del estudiante no puede estar vacío.")

        # Copia y valida cada nota, de modo que el objeto nunca quede inválido.
        self.notas = [validar_nota(nota) for nota in self.notas]

    @property
    def promedio(self) -> float | None:
        """Promedio de las notas, o ``None`` si todavía no hay notas."""
        if not self.notas:
            return None
        return calcular_promedio(self.notas)

    @property
    def estado(self) -> str:
        """Estado del estudiante: ``APROBADO``, ``REPROBADO`` o ``SIN NOTAS``."""
        promedio = self.promedio
        if promedio is None:
            return ESTADO_SIN_NOTAS
        return determinar_estado(promedio)

    @property
    def aprobado(self) -> bool:
        """``True`` si el estudiante tiene notas y su promedio alcanza el mínimo."""
        return self.promedio is not None and self.estado == "APROBADO"

    def agregar_nota(self, nota: object) -> float:
        """Valida y agrega una nota a la lista.

        Returns:
            La nota agregada, ya convertida a ``float``.

        Raises:
            ValueError: Si la nota no es válida o está fuera de 0 a 5.
        """
        valor = validar_nota(nota)
        self.notas.append(valor)
        return valor

    def eliminar_nota(self, indice: int) -> float:
        """Elimina y devuelve la nota en la posición indicada (base 0).

        Raises:
            ValueError: Si el índice no es un entero.
            IndexError: Si la posición no existe.
        """
        if isinstance(indice, bool) or not isinstance(indice, int):
            raise ValueError("La posición de la nota debe ser un número entero.")
        if not 0 <= indice < len(self.notas):
            raise IndexError("La posición de la nota no existe.")

        return self.notas.pop(indice)

    def limpiar_notas(self) -> None:
        """Elimina todas las notas del estudiante."""
        self.notas.clear()

    def a_dict(self) -> dict[str, object]:
        """Convierte el estudiante en un diccionario listo para guardarse."""
        return {"nombre": self.nombre, "notas": list(self.notas)}

    @classmethod
    def desde_dict(cls, datos: object) -> "Estudiante":
        """Crea un estudiante a partir de un diccionario cargado del JSON.

        Raises:
            ValueError: Si los datos no tienen el formato esperado.
        """
        if not isinstance(datos, dict):
            raise ValueError("Los datos del estudiante deben ser un objeto JSON.")

        nombre = datos.get("nombre")
        notas = datos.get("notas", [])

        if not isinstance(nombre, str):
            raise ValueError("El estudiante no tiene un nombre válido.")
        if not isinstance(notas, list):
            raise ValueError(f"Las notas de '{nombre}' deben ser una lista.")

        return cls(nombre=nombre, notas=notas)
