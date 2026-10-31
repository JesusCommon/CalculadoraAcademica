"""Fechas e identificadores compartidos."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

# Espacio de nombres estable para IDs deterministas de la migración.
_ESPACIO_ACADEMICO = uuid.UUID("2f6c1e2a-6f3b-4d7a-9d5e-3c1b7a9f0c11")


def ahora_iso() -> str:
    """Fecha y hora actual en UTC, formato ISO-8601."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hoy_iso() -> str:
    """Fecha actual en UTC, formato ISO-8601 (solo día)."""
    return datetime.now(timezone.utc).date().isoformat()


def nuevo_id() -> str:
    """Genera un identificador UUID4 para un registro nuevo."""
    return str(uuid.uuid4())


def id_determinista(clave: str) -> str:
    """Genera un UUID5 estable a partir de una clave lógica."""
    return str(uuid.uuid5(_ESPACIO_ACADEMICO, clave))
