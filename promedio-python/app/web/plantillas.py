"""Plantillas Jinja2 y filtros de presentación de la aplicación web."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

DIRECTORIO_PLANTILLAS = Path(__file__).resolve().parent / "templates"

plantillas = Jinja2Templates(directory=str(DIRECTORIO_PLANTILLAS))


def _promedio(valor: float | None) -> str:
    return "—" if valor is None else f"{valor:.2f}"


def _nota(valor: float) -> str:
    return f"{valor:.2f}"


def _estado_legible(estado: str) -> str:
    return {
        "APROBADO": "Aprobado",
        "REPROBADO": "Reprobado",
        "SIN NOTAS": "Sin notas",
    }.get(estado, estado.title())


def _clase_estado(estado: str) -> str:
    return {
        "APROBADO": "aprobado",
        "REPROBADO": "reprobado",
    }.get(estado, "sin-notas")


plantillas.env.filters["promedio"] = _promedio
plantillas.env.filters["nota"] = _nota
plantillas.env.filters["estado_legible"] = _estado_legible
plantillas.env.filters["clase_estado"] = _clase_estado
