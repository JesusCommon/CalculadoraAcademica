"""Repositorio SQLite de materias."""

from __future__ import annotations

import sqlite3

from app.core.entidades import Materia


def _a_entidad(fila: sqlite3.Row) -> Materia:
    return Materia(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        creditos=fila["creditos"],
        creado_en=fila["creado_en"],
        actualizado_en=fila["actualizado_en"],
        eliminado_en=fila["eliminado_en"],
    )


class RepositorioMateriasSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def agregar(self, materia: Materia) -> None:
        self.conexion.execute(
            """
            INSERT INTO materias
                (id, codigo, nombre, creditos, creado_en, actualizado_en, eliminado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                materia.id,
                materia.codigo,
                materia.nombre,
                materia.creditos,
                materia.creado_en,
                materia.actualizado_en,
                materia.eliminado_en,
            ),
        )

    def actualizar(self, materia: Materia) -> None:
        self.conexion.execute(
            """
            UPDATE materias
               SET codigo = ?, nombre = ?, creditos = ?,
                   actualizado_en = ?, eliminado_en = ?
             WHERE id = ?
            """,
            (
                materia.codigo,
                materia.nombre,
                materia.creditos,
                materia.actualizado_en,
                materia.eliminado_en,
                materia.id,
            ),
        )

    def obtener(self, materia_id: str) -> Materia | None:
        fila = self.conexion.execute(
            "SELECT * FROM materias WHERE id = ?", (materia_id,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def obtener_por_codigo(self, codigo: str) -> Materia | None:
        fila = self.conexion.execute(
            "SELECT * FROM materias WHERE codigo = ?", (codigo.strip().upper(),)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def listar(self, incluir_eliminadas: bool = False) -> list[Materia]:
        where = "" if incluir_eliminadas else " WHERE eliminado_en IS NULL"
        filas = self.conexion.execute(
            f"SELECT * FROM materias{where} ORDER BY codigo"
        ).fetchall()
        return [_a_entidad(fila) for fila in filas]

    def eliminar_logico(self, materia_id: str, fecha: str) -> None:
        self.conexion.execute(
            """
            UPDATE materias
               SET eliminado_en = ?, actualizado_en = ?
             WHERE id = ? AND eliminado_en IS NULL
            """,
            (fecha, fecha, materia_id),
        )
