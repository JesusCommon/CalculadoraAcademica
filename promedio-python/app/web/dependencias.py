"""Dependencias FastAPI: una unidad de trabajo por petición."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fastapi import Request

from app.database.unidad import UnidadDeTrabajo
from app.services.fabrica import Servicios, crear_servicios


def ruta_bd(request: Request) -> Path:
    return Path(request.app.state.ruta_db)


@contextmanager
def _abrir(request: Request, *, escritura: bool) -> Iterator[Servicios]:
    with UnidadDeTrabajo(ruta_bd(request), transaccional=escritura) as uow:
        yield crear_servicios(uow.repos)


def servicios_lectura(request: Request) -> Iterator[Servicios]:
    """Sesión de solo lectura, sin bloqueo de escritura."""
    with _abrir(request, escritura=False) as servicios:
        yield servicios


def servicios_escritura(request: Request) -> Iterator[Servicios]:
    """Sesión transaccional: confirma al terminar o revierte si hay error."""
    with _abrir(request, escritura=True) as servicios:
        yield servicios
