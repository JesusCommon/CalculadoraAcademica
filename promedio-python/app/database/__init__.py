"""Capa de persistencia SQLite compartida por escritorio y web."""

from .conexion import RUTA_BD_PREDETERMINADA, crear_conexion, transaccion
from .esquema import aplicar_esquema

__all__ = [
    "RUTA_BD_PREDETERMINADA",
    "aplicar_esquema",
    "crear_conexion",
    "transaccion",
]
