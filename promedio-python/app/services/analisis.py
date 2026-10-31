"""Cálculos agregados para paneles, estadísticas e historial.

Este servicio compone los casos de uso existentes. No accede a SQLite ni
reimplementa reglas: solo agrupa y resume información para las dos interfaces.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.core.entidades import (
    CalificacionDetalle,
    Estudiante,
    Periodo,
)
from app.core.escala import Escala
from app.core.promedio import calcular_promedio
from app.services.calificaciones import CalificacionService
from app.services.configuracion import ConfiguracionService
from app.services.estudiantes import EstudianteService
from app.services.materias import MateriaService
from app.services.periodos import PeriodoService


@dataclass(frozen=True)
class FilaEstudiante:
    """Resumen de un estudiante para tablas y tarjetas."""

    estudiante: Estudiante
    notas: int
    promedio: float | None
    estado: str


@dataclass(frozen=True)
class Punto:
    """Valor agregado con su etiqueta, apto para gráficos."""

    etiqueta: str
    valor: float
    cantidad: int = 0


@dataclass(frozen=True)
class ResumenGeneral:
    """Indicadores globales del sistema académico."""

    total_estudiantes: int
    total_materias: int
    total_periodos: int
    total_calificaciones: int
    promedio_general: float | None
    aprobados: int
    reprobados: int
    sin_notas: int
    estudiantes: list[FilaEstudiante]
    por_periodo: list[Punto]
    por_materia: list[Punto]


@dataclass(frozen=True)
class ResumenPeriodo:
    """Rendimiento del estudiante en un periodo concreto."""

    periodo: Periodo
    notas: int
    promedio: float | None
    estado: str


@dataclass(frozen=True)
class ResumenMateria:
    """Rendimiento del estudiante en una materia concreta."""

    materia_id: str
    codigo: str
    nombre: str
    notas: int
    promedio: float | None


@dataclass(frozen=True)
class DetalleEstudiante:
    """Historial académico completo de un estudiante."""

    estudiante: Estudiante
    detalles: list[CalificacionDetalle]
    promedio: float | None
    estado: str
    escala: Escala
    por_periodo: list[ResumenPeriodo]
    por_materia: list[ResumenMateria]


class AnalisisService:
    """Agrega información académica reutilizable por escritorio y web."""

    def __init__(
        self,
        estudiantes: EstudianteService,
        materias: MateriaService,
        periodos: PeriodoService,
        calificaciones: CalificacionService,
        configuracion: ConfiguracionService,
    ) -> None:
        self.estudiantes = estudiantes
        self.materias = materias
        self.periodos = periodos
        self.calificaciones = calificaciones
        self.configuracion = configuracion

    def resumen(self, periodo_id: str | None = None) -> ResumenGeneral:
        """Calcula indicadores globales, opcionalmente filtrados por periodo."""
        if periodo_id is not None:
            self.periodos.obtener(periodo_id)

        escala = self.configuracion.obtener_escala()
        estudiantes = self.estudiantes.listar()
        detalles = self.calificaciones.listar_todas(periodo_id=periodo_id)

        por_estudiante: dict[str, list[float]] = defaultdict(list)
        for detalle in detalles:
            por_estudiante[detalle.estudiante_id].append(detalle.nota)

        filas: list[FilaEstudiante] = []
        aprobados = reprobados = sin_notas = 0
        for estudiante in estudiantes:
            notas = por_estudiante.get(estudiante.id, [])
            promedio = calcular_promedio(notas) if notas else None
            if promedio is None:
                estado = "SIN NOTAS"
                sin_notas += 1
            else:
                estado = escala.estado(promedio)
                if estado == "APROBADO":
                    aprobados += 1
                else:
                    reprobados += 1
            filas.append(
                FilaEstudiante(
                    estudiante=estudiante,
                    notas=len(notas),
                    promedio=promedio,
                    estado=estado,
                )
            )

        todas_las_notas = [detalle.nota for detalle in detalles]
        return ResumenGeneral(
            total_estudiantes=len(estudiantes),
            total_materias=len(self.materias.listar()),
            total_periodos=len(self.periodos.listar(incluir_inactivos=True)),
            total_calificaciones=len(detalles),
            promedio_general=(
                calcular_promedio(todas_las_notas) if todas_las_notas else None
            ),
            aprobados=aprobados,
            reprobados=reprobados,
            sin_notas=sin_notas,
            estudiantes=filas,
            por_periodo=self._agrupar(detalles, "periodo"),
            por_materia=self._agrupar(detalles, "materia"),
        )

    def detalle_estudiante(self, estudiante_id: str) -> DetalleEstudiante:
        """Construye el historial académico de un estudiante."""
        estudiante = self.estudiantes.obtener(estudiante_id)
        escala = self.configuracion.obtener_escala()
        detalles = self.calificaciones.listar_por_estudiante(estudiante_id)
        notas = [detalle.nota for detalle in detalles]
        promedio = calcular_promedio(notas) if notas else None

        por_periodo: dict[str, list[float]] = defaultdict(list)
        por_materia: dict[str, list[float]] = defaultdict(list)
        for detalle in detalles:
            por_periodo[detalle.periodo_id].append(detalle.nota)
            por_materia[detalle.materia_id].append(detalle.nota)

        periodos = self.periodos.listar(incluir_inactivos=True)
        periodos_por_id = {periodo.id: periodo for periodo in periodos}
        resumen_periodos: list[ResumenPeriodo] = []
        for periodo_id, valores in por_periodo.items():
            periodo = periodos_por_id.get(periodo_id)
            if periodo is None:
                continue
            valor = calcular_promedio(valores)
            resumen_periodos.append(
                ResumenPeriodo(
                    periodo=periodo,
                    notas=len(valores),
                    promedio=valor,
                    estado=periodo.escala.estado(valor),
                )
            )
        resumen_periodos.sort(key=lambda item: item.periodo.nombre)

        materias_por_id = {
            materia.id: materia for materia in self.materias.listar(incluir_eliminadas=True)
        }
        resumen_materias: list[ResumenMateria] = []
        for materia_id, valores in por_materia.items():
            materia = materias_por_id.get(materia_id)
            if materia is None:
                continue
            resumen_materias.append(
                ResumenMateria(
                    materia_id=materia_id,
                    codigo=materia.codigo,
                    nombre=materia.nombre,
                    notas=len(valores),
                    promedio=calcular_promedio(valores),
                )
            )
        resumen_materias.sort(key=lambda item: item.codigo)

        return DetalleEstudiante(
            estudiante=estudiante,
            detalles=detalles,
            promedio=promedio,
            estado=escala.estado(promedio) if promedio is not None else "SIN NOTAS",
            escala=escala,
            por_periodo=resumen_periodos,
            por_materia=resumen_materias,
        )

    @staticmethod
    def _agrupar(
        detalles: list[CalificacionDetalle], criterio: str
    ) -> list[Punto]:
        grupos: dict[str, list[float]] = defaultdict(list)
        nombres: dict[str, str] = {}

        for detalle in detalles:
            if criterio == "periodo":
                clave, nombre = detalle.periodo_id, detalle.periodo_nombre
            else:
                clave, nombre = detalle.materia_id, detalle.materia_nombre
            grupos[clave].append(detalle.nota)
            nombres[clave] = nombre

        puntos = [
            Punto(
                etiqueta=nombres[clave],
                valor=calcular_promedio(valores),
                cantidad=len(valores),
            )
            for clave, valores in grupos.items()
        ]
        puntos.sort(key=lambda punto: punto.etiqueta)
        return puntos
