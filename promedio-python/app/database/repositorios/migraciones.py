"""Repositorio SQLite del registro de migraciones."""

from __future__ import annotations

import json
import sqlite3


class RepositorioMigracionesSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def existe_sha(self, sha256: str) -> bool:
        fila = self.conexion.execute(
            "SELECT 1 FROM migraciones WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return fila is not None

    def registrar(self, datos: dict[str, object]) -> None:
        self.conexion.execute(
            """
            INSERT INTO migraciones
                (id, archivo, sha256, ejecutada_en, total_leidos, importados,
                 duplicados, invalidos, resultado, detalle_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datos["id"],
                datos["archivo"],
                datos["sha256"],
                datos["ejecutada_en"],
                datos["total_leidos"],
                datos["importados"],
                datos["duplicados"],
                datos["invalidos"],
                datos["resultado"],
                json.dumps(datos.get("detalle", {}), ensure_ascii=False),
            ),
        )
