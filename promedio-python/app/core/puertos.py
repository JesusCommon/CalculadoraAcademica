"""Puertos de persistencia que implementa la infraestructura.

Los servicios dependen de estos ``Protocol`` y no de SQLite. Así se pueden
probar con repositorios en memoria y sustituir la persistencia en el futuro.
"""

from __future__ import annotations

from typing import Protocol

from .entidades import (
    Calificacion,
    CalificacionDetalle,
    Estudiante,
    Inscripcion,
    Materia,
    Periodo,
)


class RepositorioEstudiantes(Protocol):
    def agregar(self, estudiante: Estudiante) -> None: ...

    def actualizar(self, estudiante: Estudiante) -> None: ...

    def obtener(self, estudiante_id: str) -> Estudiante | None: ...

    def obtener_por_codigo(self, codigo: str) -> Estudiante | None: ...

    def obtener_por_huella(self, huella: str) -> Estudiante | None: ...

    def listar(
        self, busqueda: str | None = None, incluir_eliminados: bool = False
    ) -> list[Estudiante]: ...

    def eliminar_logico(self, estudiante_id: str, fecha: str) -> None: ...

    def siguiente_codigo(self) -> str: ...

    def contar(self, incluir_eliminados: bool = False) -> int: ...


class RepositorioMaterias(Protocol):
    def agregar(self, materia: Materia) -> None: ...

    def actualizar(self, materia: Materia) -> None: ...

    def obtener(self, materia_id: str) -> Materia | None: ...

    def obtener_por_codigo(self, codigo: str) -> Materia | None: ...

    def listar(self, incluir_eliminadas: bool = False) -> list[Materia]: ...

    def eliminar_logico(self, materia_id: str, fecha: str) -> None: ...


class RepositorioPeriodos(Protocol):
    def agregar(self, periodo: Periodo) -> None: ...

    def actualizar(self, periodo: Periodo) -> None: ...

    def obtener(self, periodo_id: str) -> Periodo | None: ...

    def obtener_por_nombre(self, nombre: str) -> Periodo | None: ...

    def listar(self, incluir_inactivos: bool = False) -> list[Periodo]: ...


class RepositorioInscripciones(Protocol):
    def agregar(self, inscripcion: Inscripcion) -> None: ...

    def obtener(self, inscripcion_id: str) -> Inscripcion | None: ...

    def obtener_por_clave(
        self, estudiante_id: str, materia_id: str, periodo_id: str
    ) -> Inscripcion | None: ...


class RepositorioCalificaciones(Protocol):
    def agregar(self, calificacion: Calificacion) -> None: ...

    def obtener(self, calificacion_id: str) -> Calificacion | None: ...

    def existe(self, calificacion_id: str) -> bool: ...

    def anular(self, calificacion_id: str, fecha: str) -> None: ...

    def listar_por_inscripcion(
        self, inscripcion_id: str, incluir_anuladas: bool = False
    ) -> list[Calificacion]: ...

    def listar_detalle(
        self,
        *,
        estudiante_id: str | None = None,
        periodo_id: str | None = None,
        materia_id: str | None = None,
        incluir_anuladas: bool = False,
        incluir_eliminados: bool = False,
        orden: str = "reciente",
    ) -> list[CalificacionDetalle]: ...

    def listar_detalle_por_estudiante(
        self, estudiante_id: str, incluir_anuladas: bool = False
    ) -> list[CalificacionDetalle]: ...

    def promedio_por_estudiante_periodo(
        self, estudiante_id: str, periodo_id: str
    ) -> float | None: ...

    def contar_activas_por_periodo(self, periodo_id: str) -> int: ...


class RepositorioConfiguracion(Protocol):
    def obtener_todas(self) -> dict[str, str]: ...

    def obtener(self, clave: str, predeterminado: str | None = None) -> str | None: ...

    def establecer_varias(self, valores: dict[str, str], fecha: str) -> None: ...


class RepositorioMigraciones(Protocol):
    def existe_sha(self, sha256: str) -> bool: ...

    def registrar(self, datos: dict[str, object]) -> None: ...


class Repositorios(Protocol):
    """Contenedor que agrupa los repositorios de una unidad de trabajo."""

    estudiantes: RepositorioEstudiantes
    materias: RepositorioMaterias
    periodos: RepositorioPeriodos
    inscripciones: RepositorioInscripciones
    calificaciones: RepositorioCalificaciones
    configuracion: RepositorioConfiguracion
    migraciones: RepositorioMigraciones
