"""Repositorio SQLite de calificaciones y consultas académicas."""

from __future__ import annotations

import sqlite3

from app.core.entidades import Calificacion, CalificacionDetalle

_COLUMNAS_DETALLE = """
    c.id, c.nota, c.fecha, c.descripcion, c.anulada_en,
    m.id AS materia_id, m.codigo AS materia_codigo,
    m.nombre AS materia_nombre,
    p.id AS periodo_id, p.nombre AS periodo_nombre,
    e.id AS estudiante_id, e.nombre AS estudiante_nombre,
    e.codigo AS estudiante_codigo
"""


def _a_entidad(fila: sqlite3.Row) -> Calificacion:
    return Calificacion(
        id=fila["id"],
        inscripcion_id=fila["inscripcion_id"],
        nota=fila["nota"],
        fecha=fila["fecha"],
        descripcion=fila["descripcion"],
        origen=fila["origen"],
        creado_en=fila["creado_en"],
        anulada_en=fila["anulada_en"],
    )


def _a_detalle(fila: sqlite3.Row) -> CalificacionDetalle:
    return CalificacionDetalle(
        id=fila["id"],
        nota=fila["nota"],
        fecha=fila["fecha"],
        descripcion=fila["descripcion"],
        materia_id=fila["materia_id"],
        materia_codigo=fila["materia_codigo"],
        materia_nombre=fila["materia_nombre"],
        periodo_id=fila["periodo_id"],
        periodo_nombre=fila["periodo_nombre"],
        anulada_en=fila["anulada_en"],
        estudiante_id=fila["estudiante_id"],
        estudiante_nombre=fila["estudiante_nombre"],
        estudiante_codigo=fila["estudiante_codigo"],
    )


class RepositorioCalificacionesSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def agregar(self, calificacion: Calificacion) -> None:
        self.conexion.execute(
            """
            INSERT INTO calificaciones
                (id, inscripcion_id, nota, descripcion, fecha, origen,
                 creado_en, anulada_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                calificacion.id,
                calificacion.inscripcion_id,
                calificacion.nota,
                calificacion.descripcion,
                calificacion.fecha,
                calificacion.origen,
                calificacion.creado_en,
                calificacion.anulada_en,
            ),
        )

    def obtener(self, calificacion_id: str) -> Calificacion | None:
        fila = self.conexion.execute(
            "SELECT * FROM calificaciones WHERE id = ?", (calificacion_id,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def existe(self, calificacion_id: str) -> bool:
        fila = self.conexion.execute(
            "SELECT 1 FROM calificaciones WHERE id = ?", (calificacion_id,)
        ).fetchone()
        return fila is not None

    def anular(self, calificacion_id: str, fecha: str) -> None:
        self.conexion.execute(
            """
            UPDATE calificaciones
               SET anulada_en = ?
             WHERE id = ? AND anulada_en IS NULL
            """,
            (fecha, calificacion_id),
        )

    def listar_por_inscripcion(
        self, inscripcion_id: str, incluir_anuladas: bool = False
    ) -> list[Calificacion]:
        condicion = "" if incluir_anuladas else " AND anulada_en IS NULL"
        filas = self.conexion.execute(
            f"""
            SELECT * FROM calificaciones
             WHERE inscripcion_id = ?{condicion}
             ORDER BY fecha, creado_en
            """,
            (inscripcion_id,),
        ).fetchall()
        return [_a_entidad(fila) for fila in filas]

    def listar_detalle(
        self,
        *,
        estudiante_id: str | None = None,
        periodo_id: str | None = None,
        materia_id: str | None = None,
        incluir_anuladas: bool = False,
        incluir_eliminados: bool = False,
        orden: str = "reciente",
    ) -> list[CalificacionDetalle]:
        """Lista calificaciones enriquecidas con filtros opcionales."""
        condiciones: list[str] = []
        parametros: list[object] = []

        if estudiante_id:
            condiciones.append("i.estudiante_id = ?")
            parametros.append(estudiante_id)
        if periodo_id:
            condiciones.append("i.periodo_id = ?")
            parametros.append(periodo_id)
        if materia_id:
            condiciones.append("i.materia_id = ?")
            parametros.append(materia_id)
        if not incluir_anuladas:
            condiciones.append("c.anulada_en IS NULL")
        if not incluir_eliminados:
            condiciones.append("e.eliminado_en IS NULL")

        where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
        orden_sql = (
            "c.fecha DESC, c.creado_en DESC"
            if orden == "reciente"
            else "p.fecha_inicio, m.codigo, c.fecha, c.creado_en"
        )

        filas = self.conexion.execute(
            f"""
            SELECT {_COLUMNAS_DETALLE}
              FROM calificaciones c
              JOIN inscripciones i ON i.id = c.inscripcion_id
              JOIN materias m ON m.id = i.materia_id
              JOIN periodos p ON p.id = i.periodo_id
              JOIN estudiantes e ON e.id = i.estudiante_id
             {where}
             ORDER BY {orden_sql}
            """,
            parametros,
        ).fetchall()
        return [_a_detalle(fila) for fila in filas]

    def listar_detalle_por_estudiante(
        self, estudiante_id: str, incluir_anuladas: bool = False
    ) -> list[CalificacionDetalle]:
        return self.listar_detalle(
            estudiante_id=estudiante_id,
            incluir_anuladas=incluir_anuladas,
            orden="academico",
        )

    def promedio_por_estudiante_periodo(
        self, estudiante_id: str, periodo_id: str
    ) -> float | None:
        fila = self.conexion.execute(
            """
            SELECT AVG(c.nota) AS promedio
              FROM calificaciones c
              JOIN inscripciones i ON i.id = c.inscripcion_id
             WHERE i.estudiante_id = ? AND i.periodo_id = ?
               AND c.anulada_en IS NULL
            """,
            (estudiante_id, periodo_id),
        ).fetchone()
        return None if fila["promedio"] is None else float(fila["promedio"])

    def contar_activas_por_periodo(self, periodo_id: str) -> int:
        fila = self.conexion.execute(
            """
            SELECT COUNT(*) AS total
              FROM calificaciones c
              JOIN inscripciones i ON i.id = c.inscripcion_id
             WHERE i.periodo_id = ? AND c.anulada_en IS NULL
            """,
            (periodo_id,),
        ).fetchone()
        return int(fila["total"])
