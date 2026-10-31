"""Servidor web local de la Calculadora Académica 3.0."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.conexion import RUTA_BD_PREDETERMINADA
from app.web.rutas import router

DIRECTORIO_ESTATICOS = Path(__file__).resolve().parent / "static"


def crear_app(ruta_db: str | Path | None = None) -> FastAPI:
    """Crea la aplicación web usando la base SQLite compartida.

    Args:
        ruta_db: Ruta alternativa a la base. Si se omite se usa la base real
            del proyecto, la misma que consume la interfaz Tkinter.
    """
    aplicacion = FastAPI(
        title="Calculadora Académica 3.0",
        description="Interfaz web local sobre los servicios académicos compartidos.",
        version="3.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    aplicacion.state.ruta_db = (
        Path(ruta_db) if ruta_db is not None else RUTA_BD_PREDETERMINADA
    )

    aplicacion.mount(
        "/static",
        StaticFiles(directory=str(DIRECTORIO_ESTATICOS)),
        name="static",
    )
    aplicacion.include_router(router)
    return aplicacion


app = crear_app()

__all__ = ["app", "crear_app"]
