"""Aplicación de migraciones SQL versionadas."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.tiempo import ahora_iso

_DIRECTORIO_MIGRACIONES = Path(__file__).resolve().parent / "migraciones"


def _archivos_migracion() -> list[tuple[int, Path]]:
    archivos: list[tuple[int, Path]] = []
    for ruta in sorted(_DIRECTORIO_MIGRACIONES.glob("*.sql")):
        try:
            version = int(ruta.name.split("_", 1)[0])
        except ValueError as error:
            raise RuntimeError(f"Nombre de migración inválido: {ruta.name}") from error
        archivos.append((version, ruta))
    return archivos


def aplicar_esquema(conexion: sqlite3.Connection) -> list[int]:
    """Aplica las migraciones pendientes y devuelve sus versiones."""
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS esquema_version (
            version     INTEGER PRIMARY KEY,
            aplicado_en TEXT NOT NULL
        )
        """
    )

    aplicadas = {
        fila["version"]
        for fila in conexion.execute("SELECT version FROM esquema_version")
    }
    nuevas: list[int] = []

    for version, ruta in _archivos_migracion():
        if version in aplicadas:
            continue

        script = ruta.read_text(encoding="utf-8")
        fecha = ahora_iso().replace("'", "''")
        try:
            conexion.executescript(
                "BEGIN;\n"
                f"{script}\n"
                "INSERT INTO esquema_version (version, aplicado_en) "
                f"VALUES ({version}, '{fecha}');\n"
                "COMMIT;"
            )
        except sqlite3.Error:
            if conexion.in_transaction:
                conexion.rollback()
            raise
        nuevas.append(version)

    return nuevas
