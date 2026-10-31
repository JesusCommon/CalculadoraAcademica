"""Unidad de trabajo: una conexión, una transacción y sus repositorios."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType

from .conexion import crear_conexion
from .esquema import aplicar_esquema
from .repositorios import Repositorios, crear_repositorios


class UnidadDeTrabajo:
    """Agrupa una conexión y sus repositorios.

    Uso::

        with UnidadDeTrabajo() as uow:
            servicio = EstudianteService(uow.estudiantes)
            servicio.crear("Ana")

    Al salir sin excepciones se confirma la transacción; si hay un error,
    se revierte todo y la conexión se cierra.
    """

    def __init__(
        self,
        ruta: str | Path | None = None,
        *,
        transaccional: bool = True,
        aplicar_esquema_al_abrir: bool = True,
    ) -> None:
        self.ruta = ruta
        self.transaccional = transaccional
        self.aplicar_esquema_al_abrir = aplicar_esquema_al_abrir
        self.conexion: sqlite3.Connection | None = None
        self.repositorios: Repositorios | None = None

    def __enter__(self) -> "UnidadDeTrabajo":
        self.conexion = crear_conexion(self.ruta)
        try:
            if self.aplicar_esquema_al_abrir:
                aplicar_esquema(self.conexion)
            if self.transaccional:
                self.conexion.execute("BEGIN IMMEDIATE")
            self.repositorios = crear_repositorios(self.conexion)
        except Exception:
            self.conexion.close()
            raise
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        valor: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        assert self.conexion is not None

        try:
            if self.transaccional:
                if tipo is None:
                    self.conexion.commit()
                else:
                    self.conexion.rollback()
        finally:
            self.conexion.close()

    @property
    def repos(self) -> Repositorios:
        if self.repositorios is None:
            raise RuntimeError("La unidad de trabajo no está abierta.")
        return self.repositorios
