"""Casos de uso de calificaciones."""

from __future__ import annotations

from app.core.entidades import Calificacion, CalificacionDetalle, Inscripcion
from app.core.errores import DatosInvalidos, NoEncontrado
from app.core.promedio import calcular_promedio
from app.core.puertos import (
    RepositorioCalificaciones,
    RepositorioEstudiantes,
    RepositorioInscripciones,
    RepositorioMaterias,
    RepositorioPeriodos,
)
from app.core.tiempo import ahora_iso, hoy_iso, nuevo_id


class CalificacionService:
    """Registra, anula y consulta calificaciones por materia y periodo."""

    def __init__(
        self,
        calificaciones: RepositorioCalificaciones,
        inscripciones: RepositorioInscripciones,
        estudiantes: RepositorioEstudiantes,
        materias: RepositorioMaterias,
        periodos: RepositorioPeriodos,
        reloj=ahora_iso,
        generador_id=nuevo_id,
    ) -> None:
        self.calificaciones = calificaciones
        self.inscripciones = inscripciones
        self.estudiantes = estudiantes
        self.materias = materias
        self.periodos = periodos
        self.reloj = reloj
        self.generador_id = generador_id

    def registrar(
        self,
        estudiante_id: str,
        materia_id: str,
        periodo_id: str,
        nota: float,
        *,
        descripcion: str | None = None,
        fecha: str | None = None,
    ) -> Calificacion:
        estudiante = self.estudiantes.obtener(estudiante_id)
        if estudiante is None or not estudiante.activo:
            raise NoEncontrado("El estudiante no existe o fue eliminado.")

        materia = self.materias.obtener(materia_id)
        if materia is None or not materia.activa:
            raise NoEncontrado("La materia no existe o fue eliminada.")

        periodo = self.periodos.obtener(periodo_id)
        if periodo is None:
            raise NoEncontrado("El periodo no existe.")

        try:
            valor = periodo.escala.validar(nota)
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        inscripcion = self.inscripciones.obtener_por_clave(
            estudiante_id, materia_id, periodo_id
        )
        if inscripcion is None:
            inscripcion = Inscripcion(
                id=self.generador_id(),
                estudiante_id=estudiante_id,
                materia_id=materia_id,
                periodo_id=periodo_id,
                creado_en=self.reloj(),
            )
            self.inscripciones.agregar(inscripcion)

        fecha_registro = fecha or hoy_iso()
        calificacion = Calificacion(
            id=self.generador_id(),
            inscripcion_id=inscripcion.id,
            nota=valor,
            fecha=fecha_registro,
            descripcion=descripcion,
            creado_en=self.reloj(),
        )
        self.calificaciones.agregar(calificacion)
        return calificacion

    def obtener(self, calificacion_id: str) -> Calificacion:
        calificacion = self.calificaciones.obtener(calificacion_id)
        if calificacion is None or not calificacion.activa:
            raise NoEncontrado("La calificación no existe o fue anulada.")
        return calificacion

    def anular(self, calificacion_id: str) -> None:
        calificacion = self.obtener(calificacion_id)
        self.calificaciones.anular(calificacion.id, self.reloj())

    def listar_por_estudiante(
        self, estudiante_id: str, incluir_anuladas: bool = False
    ) -> list[CalificacionDetalle]:
        estudiante = self.estudiantes.obtener(estudiante_id)
        if estudiante is None or not estudiante.activo:
            raise NoEncontrado("El estudiante no existe o fue eliminado.")
        return self.calificaciones.listar_detalle_por_estudiante(
            estudiante_id, incluir_anuladas
        )

    def listar_todas(
        self,
        *,
        estudiante_id: str | None = None,
        periodo_id: str | None = None,
        materia_id: str | None = None,
        incluir_anuladas: bool = False,
    ) -> list[CalificacionDetalle]:
        """Lista calificaciones activas con filtros opcionales."""
        if estudiante_id is not None:
            estudiante = self.estudiantes.obtener(estudiante_id)
            if estudiante is None or not estudiante.activo:
                raise NoEncontrado("El estudiante no existe o fue eliminado.")
        if periodo_id is not None:
            if self.periodos.obtener(periodo_id) is None:
                raise NoEncontrado("El periodo no existe.")
        if materia_id is not None:
            materia = self.materias.obtener(materia_id)
            if materia is None or not materia.activa:
                raise NoEncontrado("La materia no existe o fue eliminada.")

        return self.calificaciones.listar_detalle(
            estudiante_id=estudiante_id,
            periodo_id=periodo_id,
            materia_id=materia_id,
            incluir_anuladas=incluir_anuladas,
        )

    def promedio(
        self, estudiante_id: str, periodo_id: str | None = None
    ) -> float | None:
        estudiante = self.estudiantes.obtener(estudiante_id)
        if estudiante is None or not estudiante.activo:
            raise NoEncontrado("El estudiante no existe o fue eliminado.")

        if periodo_id is not None:
            if self.periodos.obtener(periodo_id) is None:
                raise NoEncontrado("El periodo no existe.")
            return self.calificaciones.promedio_por_estudiante_periodo(
                estudiante_id, periodo_id
            )

        detalles = self.listar_por_estudiante(estudiante_id)
        notas = [detalle.nota for detalle in detalles]
        if not notas:
            return None
        return calcular_promedio(notas)
