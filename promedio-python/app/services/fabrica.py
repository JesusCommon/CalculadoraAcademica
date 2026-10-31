"""Fábrica de servicios compartida por las interfaces de escritorio y web."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.puertos import Repositorios
from app.services.analisis import AnalisisService
from app.services.calificaciones import CalificacionService
from app.services.configuracion import ConfiguracionService
from app.services.estudiantes import EstudianteService
from app.services.materias import MateriaService
from app.services.periodos import PeriodoService


@dataclass(frozen=True)
class Servicios:
    estudiantes: EstudianteService
    materias: MateriaService
    periodos: PeriodoService
    configuracion: ConfiguracionService
    calificaciones: CalificacionService
    analisis: AnalisisService


def crear_servicios(repos: Repositorios) -> Servicios:
    """Construye todos los servicios sobre una unidad de trabajo."""
    estudiantes = EstudianteService(repos.estudiantes)
    materias = MateriaService(repos.materias)
    configuracion = ConfiguracionService(repos.configuracion)
    periodos = PeriodoService(repos.periodos, configuracion)
    calificaciones = CalificacionService(
        calificaciones=repos.calificaciones,
        inscripciones=repos.inscripciones,
        estudiantes=repos.estudiantes,
        materias=repos.materias,
        periodos=repos.periodos,
    )
    analisis = AnalisisService(
        estudiantes=estudiantes,
        materias=materias,
        periodos=periodos,
        calificaciones=calificaciones,
        configuracion=configuracion,
    )
    return Servicios(
        estudiantes=estudiantes,
        materias=materias,
        periodos=periodos,
        configuracion=configuracion,
        calificaciones=calificaciones,
        analisis=analisis,
    )
