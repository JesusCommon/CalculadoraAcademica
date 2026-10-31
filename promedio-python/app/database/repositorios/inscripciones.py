"""Repositorio SQLite de inscripciones."""

from __future__ import annotations

import sqlite3

from app.core.entidades import Inscripcion


def _a_entidad(fila: sqlite3.Row) -> Inscripcion:
    return Inscripcion(
        id=fila["id"],
        estudiante_id=fila["estudiante_id"],
        materia_id=fila["materia_id"],
        periodo_id=fila["periodo_id"],
        estado=fila["estado"],
        creado_en=fila["creado_en"],
    )


class RepositorioInscripcionesSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def agregar(self, inscripcion: Inscripcion) -> None:
        self.conexion.execute(
            """
            INSERT INTO inscripciones
                (id, estudiante_id, materia_id, periodo_id, estado, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                inscripcion.id,
                inscripcion.estudiante_id,
                inscripcion.materia_id,
                inscripcion.periodo_id,
                inscripcion.estado,
                inscripcion.creado_en,
            ),
        )

    def obtener(self, inscripcion_id: str) -> Inscripcion | None:
        fila = self.conexion.execute(
            "SELECT * FROM inscripciones WHERE id = ?", (inscripcion_id,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def obtener_por_clave(
        self, estudiante_id: str, materia_id: str, periodo_id: str
    ) -> Inscripcion | None:
        fila = self.conexion.execute(
            """
            SELECT * FROM inscripciones
             WHERE estudiante_id = ? AND materia_id = ? AND periodo_id = ?
            """,
            (estudiante_id, materia_id, periodo_id),
        ).fetchone()
        return _a_entidad(fila) if fila else None
