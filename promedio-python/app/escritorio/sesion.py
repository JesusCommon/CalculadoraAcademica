"""Acceso transaccional a los servicios desde la interfaz de escritorio."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from app.database.unidad import UnidadDeTrabajo
from app.services.fabrica import Servicios, crear_servicios


@contextmanager
def sesion(*, escritura: bool = True) -> Iterator[Servicios]:
    """Abre una unidad de trabajo y entrega los servicios compartidos.

    Cada operación de la interfaz usa su propia conexión y transacción, de modo
    que escritorio y web nunca comparten una conexión SQLite.
    """
    with UnidadDeTrabajo(transaccional=escritura) as uow:
        yield crear_servicios(uow.repos)
