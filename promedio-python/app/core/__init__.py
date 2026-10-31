"""Núcleo académico compartido de la Calculadora Académica 3.0.

Este paquete no conoce Tkinter, FastAPI, SQLite ni archivos. Contiene las
reglas de negocio que reutilizan tanto la aplicación de escritorio como la web.
"""

from .entidades import Calificacion, CalificacionDetalle, Estudiante, Inscripcion, Materia, Periodo
from .errores import Conflicto, DatosInvalidos, ErrorAcademico, ErrorMigracion, NoEncontrado
from .escala import ESCALA_PREDETERMINADA, Escala
from .promedio import calcular_promedio, determinar_estado, validar_nota

__all__ = [
    "Calificacion",
    "CalificacionDetalle",
    "Conflicto",
    "DatosInvalidos",
    "ESCALA_PREDETERMINADA",
    "ErrorAcademico",
    "ErrorMigracion",
    "Escala",
    "Estudiante",
    "Inscripcion",
    "Materia",
    "NoEncontrado",
    "Periodo",
    "calcular_promedio",
    "determinar_estado",
    "validar_nota",
]
