"""Repositorio SQLite de periodos académicos."""

from __future__ import annotations

import sqlite3

from app.core.entidades import Periodo


def _a_entidad(fila: sqlite3.Row) -> Periodo:
    return Periodo(
        id=fila["id"],
        nombre=fila["nombre"],
        fecha_inicio=fila["fecha_inicio"],
        fecha_fin=fila["fecha_fin"],
        escala_min=fila["escala_min"],
        escala_max=fila["escala_max"],
        aprobacion_min=fila["aprobacion_min"],
        activo=bool(fila["activo"]),
        creado_en=fila["creado_en"],
    )


class RepositorioPeriodosSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def agregar(self, periodo: Periodo) -> None:
        self.conexion.execute(
            """
            INSERT INTO periodos
                (id, nombre, fecha_inicio, fecha_fin, escala_min, escala_max,
                 aprobacion_min, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                periodo.id,
                periodo.nombre,
                periodo.fecha_inicio,
                periodo.fecha_fin,
                periodo.escala_min,
                periodo.escala_max,
                periodo.aprobacion_min,
                int(periodo.activo),
                periodo.creado_en,
            ),
        )

    def obtener(self, periodo_id: str) -> Periodo | None:
        fila = self.conexion.execute(
            "SELECT * FROM periodos WHERE id = ?", (periodo_id,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def actualizar(self, periodo: Periodo) -> None:
        self.conexion.execute(
            """
            UPDATE periodos
               SET nombre = ?, fecha_inicio = ?, fecha_fin = ?,
                   escala_min = ?, escala_max = ?, aprobacion_min = ?,
                   activo = ?
             WHERE id = ?
            """,
            (
                periodo.nombre,
                periodo.fecha_inicio,
                periodo.fecha_fin,
                periodo.escala_min,
                periodo.escala_max,
                periodo.aprobacion_min,
                int(periodo.activo),
                periodo.id,
            ),
        )

    def obtener_por_nombre(self, nombre: str) -> Periodo | None:
        fila = self.conexion.execute(
            "SELECT * FROM periodos WHERE nombre = ?", (nombre,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def listar(self, incluir_inactivos: bool = False) -> list[Periodo]:
        where = "" if incluir_inactivos else " WHERE activo = 1"
        filas = self.conexion.execute(
            f"SELECT * FROM periodos{where} ORDER BY fecha_inicio DESC, nombre"
        ).fetchall()
        return [_a_entidad(fila) for fila in filas]
