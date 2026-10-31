"""Utilidades de texto compartidas por servicios y migración."""

from __future__ import annotations

import unicodedata


def normalizar_nombre(nombre: object) -> str:
    """Normaliza un nombre para mostrarlo: NFKC, sin extremos ni dobles espacios."""
    if not isinstance(nombre, str):
        raise ValueError("El nombre del estudiante debe ser texto.")
    return " ".join(unicodedata.normalize("NFKC", nombre).split())


def clave_nombre(nombre: str) -> str:
    """Clave de comparación/búsqueda: normalizada y sin distinguir mayúsculas."""
    return normalizar_nombre(nombre).casefold()
