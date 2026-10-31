"""Repositorios SQLite de la aplicación académica."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .calificaciones import RepositorioCalificacionesSQLite
from .configuracion import RepositorioConfiguracionSQLite
from .estudiantes import RepositorioEstudiantesSQLite
from .inscripciones import RepositorioInscripcionesSQLite
from .materias import RepositorioMateriasSQLite
from .migraciones import RepositorioMigracionesSQLite
from .periodos import RepositorioPeriodosSQLite


@dataclass
class Repositorios:
    estudiantes: RepositorioEstudiantesSQLite
    materias: RepositorioMateriasSQLite
    periodos: RepositorioPeriodosSQLite
    inscripciones: RepositorioInscripcionesSQLite
    calificaciones: RepositorioCalificacionesSQLite
    configuracion: RepositorioConfiguracionSQLite
    migraciones: RepositorioMigracionesSQLite


def crear_repositorios(conexion: sqlite3.Connection) -> Repositorios:
    return Repositorios(
        estudiantes=RepositorioEstudiantesSQLite(conexion),
        materias=RepositorioMateriasSQLite(conexion),
        periodos=RepositorioPeriodosSQLite(conexion),
        inscripciones=RepositorioInscripcionesSQLite(conexion),
        calificaciones=RepositorioCalificacionesSQLite(conexion),
        configuracion=RepositorioConfiguracionSQLite(conexion),
        migraciones=RepositorioMigracionesSQLite(conexion),
    )


__all__ = [
    "Repositorios",
    "RepositorioCalificacionesSQLite",
    "RepositorioConfiguracionSQLite",
    "RepositorioEstudiantesSQLite",
    "RepositorioInscripcionesSQLite",
    "RepositorioMateriasSQLite",
    "RepositorioMigracionesSQLite",
    "RepositorioPeriodosSQLite",
    "crear_repositorios",
]
