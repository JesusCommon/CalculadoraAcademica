"""Errores controlados del dominio académico."""

from __future__ import annotations


class ErrorAcademico(Exception):
    """Error base de la aplicación, apto para mostrarse al usuario."""


class DatosInvalidos(ErrorAcademico):
    """Los datos recibidos no cumplen las reglas del dominio."""


class NoEncontrado(ErrorAcademico):
    """El recurso solicitado no existe o fue eliminado."""


class Conflicto(ErrorAcademico):
    """La operación choca con un registro existente (por ejemplo, un código)."""


class ErrorMigracion(ErrorAcademico):
    """La migración no pudo completarse o no superó la verificación."""
