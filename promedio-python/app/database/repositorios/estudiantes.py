"""Repositorio SQLite de estudiantes."""

from __future__ import annotations

import sqlite3

from app.core.entidades import Estudiante
from app.core.texto import clave_nombre


def _a_entidad(fila: sqlite3.Row) -> Estudiante:
    return Estudiante(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        nombre_normalizado=fila["nombre_normalizado"],
        correo=fila["correo"],
        origen=fila["origen"],
        huella_migracion=fila["huella_migracion"],
        creado_en=fila["creado_en"],
        actualizado_en=fila["actualizado_en"],
        eliminado_en=fila["eliminado_en"],
    )


class RepositorioEstudiantesSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def agregar(self, estudiante: Estudiante) -> None:
        self.conexion.execute(
            """
            INSERT INTO estudiantes
                (id, codigo, nombre, nombre_normalizado, correo, origen,
                 huella_migracion, creado_en, actualizado_en, eliminado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                estudiante.id,
                estudiante.codigo,
                estudiante.nombre,
                estudiante.nombre_normalizado,
                estudiante.correo,
                estudiante.origen,
                estudiante.huella_migracion,
                estudiante.creado_en,
                estudiante.actualizado_en,
                estudiante.eliminado_en,
            ),
        )

    def actualizar(self, estudiante: Estudiante) -> None:
        self.conexion.execute(
            """
            UPDATE estudiantes
               SET nombre = ?, nombre_normalizado = ?, correo = ?,
                   actualizado_en = ?, eliminado_en = ?
             WHERE id = ?
            """,
            (
                estudiante.nombre,
                estudiante.nombre_normalizado,
                estudiante.correo,
                estudiante.actualizado_en,
                estudiante.eliminado_en,
                estudiante.id,
            ),
        )

    def obtener(self, estudiante_id: str) -> Estudiante | None:
        fila = self.conexion.execute(
            "SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def obtener_por_codigo(self, codigo: str) -> Estudiante | None:
        fila = self.conexion.execute(
            "SELECT * FROM estudiantes WHERE codigo = ?", (codigo,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def obtener_por_huella(self, huella: str) -> Estudiante | None:
        fila = self.conexion.execute(
            "SELECT * FROM estudiantes WHERE huella_migracion = ?", (huella,)
        ).fetchone()
        return _a_entidad(fila) if fila else None

    def listar(
        self, busqueda: str | None = None, incluir_eliminados: bool = False
    ) -> list[Estudiante]:
        condiciones: list[str] = []
        parametros: list[object] = []

        if not incluir_eliminados:
            condiciones.append("eliminado_en IS NULL")

        if busqueda:
            patron = f"%{clave_nombre(busqueda)}%"
            condiciones.append("(nombre_normalizado LIKE ? OR lower(codigo) LIKE ?)")
            parametros.extend([patron, patron])

        where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
        filas = self.conexion.execute(
            f"SELECT * FROM estudiantes{where} ORDER BY nombre_normalizado, codigo",
            parametros,
        ).fetchall()
        return [_a_entidad(fila) for fila in filas]

    def eliminar_logico(self, estudiante_id: str, fecha: str) -> None:
        self.conexion.execute(
            """
            UPDATE estudiantes
               SET eliminado_en = ?, actualizado_en = ?
             WHERE id = ? AND eliminado_en IS NULL
            """,
            (fecha, fecha, estudiante_id),
        )

    def siguiente_codigo(self) -> str:
        self.conexion.execute(
            "INSERT OR IGNORE INTO contadores (nombre, valor) VALUES ('estudiante', 0)"
        )
        self.conexion.execute(
            "UPDATE contadores SET valor = valor + 1 WHERE nombre = 'estudiante'"
        )
        fila = self.conexion.execute(
            "SELECT valor FROM contadores WHERE nombre = 'estudiante'"
        ).fetchone()
        return f"EST-{int(fila['valor']):06d}"

    def contar(self, incluir_eliminados: bool = False) -> int:
        where = "" if incluir_eliminados else " WHERE eliminado_en IS NULL"
        fila = self.conexion.execute(
            f"SELECT COUNT(*) AS total FROM estudiantes{where}"
        ).fetchone()
        return int(fila["total"])
