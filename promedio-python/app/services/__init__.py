"""Servicios de aplicación compartidos por Tkinter y FastAPI."""

from .analisis import AnalisisService
from .calificaciones import CalificacionService
from .configuracion import ConfiguracionService
from .estudiantes import EstudianteService
from .exportacion import ExportacionService
from .fabrica import Servicios, crear_servicios
from .materias import MateriaService
from .periodos import PeriodoService

__all__ = [
    "AnalisisService",
    "CalificacionService",
    "ConfiguracionService",
    "EstudianteService",
    "ExportacionService",
    "MateriaService",
    "PeriodoService",
    "Servicios",
    "crear_servicios",
]
