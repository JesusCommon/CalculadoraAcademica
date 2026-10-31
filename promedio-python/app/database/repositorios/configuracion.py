"""Repositorio SQLite de configuración clave/valor."""

from __future__ import annotations

import sqlite3


class RepositorioConfiguracionSQLite:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def obtener_todas(self) -> dict[str, str]:
        filas = self.conexion.execute(
            "SELECT clave, valor FROM configuracion ORDER BY clave"
        ).fetchall()
        return {fila["clave"]: fila["valor"] for fila in filas}

    def obtener(self, clave: str, predeterminado: str | None = None) -> str | None:
        fila = self.conexion.execute(
            "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
        ).fetchone()
        return fila["valor"] if fila else predeterminado

    def establecer_varias(self, valores: dict[str, str], fecha: str) -> None:
        self.conexion.executemany(
            """
            INSERT INTO configuracion (clave, valor, actualizado_en)
            VALUES (?, ?, ?)
            ON CONFLICT(clave) DO UPDATE
               SET valor = excluded.valor,
                   actualizado_en = excluded.actualizado_en
            """,
            [(clave, str(valor), fecha) for clave, valor in valores.items()],
        )
