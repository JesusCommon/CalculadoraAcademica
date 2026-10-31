"""Cálculo del promedio de notas (API compatible con la versión 2.0).

Las reglas de validación y cálculo viven en ``app.core``. Este módulo conserva
las constantes, funciones y el flujo de consola que ya usaba la versión 2.0.
"""

from __future__ import annotations

from .core.escala import ESCALA_PREDETERMINADA
from .core.promedio import calcular_promedio, determinar_estado, validar_nota

NOTA_MINIMA = ESCALA_PREDETERMINADA.minima
NOTA_MAXIMA = ESCALA_PREDETERMINADA.maxima
NOTA_APROBACION = ESCALA_PREDETERMINADA.aprobacion


def pedir_cantidad_notas() -> int:
    """Solicita al usuario cuántas notas desea ingresar.

    Repite la pregunta hasta obtener un entero positivo válido.
    """
    while True:
        entrada = input("¿Cuántas notas desea ingresar? ").strip()

        try:
            cantidad = int(entrada)
        except ValueError:
            print("Error: debe ingresar un número entero. Intente de nuevo.")
            continue

        if cantidad <= 0:
            print("Error: la cantidad de notas debe ser mayor que cero.")
            continue

        return cantidad


def pedir_nota(numero: int) -> float:
    """Solicita una nota válida (número entre 0 y 5).

    Args:
        numero: Posición de la nota que se está solicitando (1, 2, 3...).

    Returns:
        La nota ingresada como número decimal.
    """
    while True:
        entrada = input(f"Ingrese la nota {numero}: ").strip()

        try:
            valor = float(entrada)
        except ValueError:
            print("Error: la nota debe ser un número válido. Intente de nuevo.")
            continue

        try:
            # Reutiliza la validación del núcleo compartido.
            return validar_nota(valor)
        except ValueError as error:
            print(f"Error: {error} Intente de nuevo.")
            continue


def ejecutar() -> None:
    """Ejecuta el flujo completo del programa de consola."""
    print("=== Cálculo de promedio de notas ===")

    cantidad = pedir_cantidad_notas()
    notas = [pedir_nota(i) for i in range(1, cantidad + 1)]

    promedio = calcular_promedio(notas)
    estado = determinar_estado(promedio)

    print("\n--- Resultado ---")
    print(f"Notas ingresadas: {', '.join(f'{nota:.2f}' for nota in notas)}")
    print(f"Promedio final: {promedio:.2f}")
    print(f"Estado: {estado}")
