"""Conexiones SQLite configuradas para la aplicación académica."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

RUTA_BD_PREDETERMINADA = Path(__file__).resolve().parent.parent.parent / "datos" / "academico.db"


def es_memoria(ruta: str | Path) -> bool:
    return str(ruta) == ":memory:"


def crear_conexion(
    ruta: str | Path | None = None,
    *,
    crear_directorios: bool = True,
) -> sqlite3.Connection:
    """Abre una conexión con las PRAGMAs seguras del proyecto.

    Cada operación debe usar su propia conexión. No se comparten conexiones
    entre hilos ni entre requests.
    """
    destino = Path(ruta) if ruta is not None else RUTA_BD_PREDETERMINADA

    if not es_memoria(destino):
        if crear_directorios:
            destino.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(str(destino), timeout=5.0, isolation_level=None)
    else:
        conexion = sqlite3.connect(":memory:", timeout=5.0, isolation_level=None)

    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    conexion.execute("PRAGMA synchronous = NORMAL")

    if not es_memoria(destino):
        # WAL mejora la lectura concurrente entre escritorio y web.
        conexion.execute("PRAGMA journal_mode = WAL")

    return conexion


@contextmanager
def transaccion(conexion: sqlite3.Connection, *, inmediata: bool = False) -> Iterator[None]:
    """Transacción explícita con commit/rollback automáticos."""
    conexion.execute("BEGIN IMMEDIATE" if inmediata else "BEGIN")
    try:
        yield
    except Exception:
        conexion.rollback()
        raise
    else:
        conexion.commit()


@contextmanager
def conexion_temporal(ruta: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Conexión de solo lectura/consulta que siempre se cierra."""
    conexion = crear_conexion(ruta)
    try:
        yield conexion
    finally:
        conexion.close()


def respaldar_bd(
    ruta_origen: str | Path,
    ruta_destino: str | Path,
) -> Path:
    """Copia una base SQLite de forma consistente usando su API de backup."""
    origen = Path(ruta_origen)
    destino = Path(ruta_destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    conexion_origen = sqlite3.connect(str(origen), timeout=5.0)
    conexion_destino = sqlite3.connect(str(destino), timeout=5.0)
    try:
        conexion_origen.backup(conexion_destino)
    finally:
        conexion_destino.close()
        conexion_origen.close()

    return destino
