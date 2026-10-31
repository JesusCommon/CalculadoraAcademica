"""Entidades académicas del dominio 3.0."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .escala import ESCALA_PREDETERMINADA, Escala
from .texto import normalizar_nombre

ORIGENES_ESTUDIANTE = ("app", "json_migracion")
ESTADOS_INSCRIPCION = ("activa", "retirada", "finalizada")


@dataclass
class Estudiante:
    """Identidad de un estudiante, independiente de sus calificaciones."""

    id: str
    codigo: str
    nombre: str
    nombre_normalizado: str = ""
    correo: str | None = None
    origen: str = "app"
    huella_migracion: str | None = None
    creado_en: str = ""
    actualizado_en: str = ""
    eliminado_en: str | None = None

    def __post_init__(self) -> None:
        self.nombre = normalizar_nombre(self.nombre)
        if not self.nombre:
            raise ValueError("El nombre del estudiante no puede estar vacío.")
        if not self.nombre_normalizado:
            self.nombre_normalizado = self.nombre.casefold()
        if self.origen not in ORIGENES_ESTUDIANTE:
            raise ValueError(f"Origen de estudiante no válido: {self.origen}")

    @property
    def activo(self) -> bool:
        return self.eliminado_en is None


@dataclass
class Materia:
    """Materia académica con posibles créditos."""

    id: str
    codigo: str
    nombre: str
    creditos: float = 0.0
    creado_en: str = ""
    actualizado_en: str = ""
    eliminado_en: str | None = None

    def __post_init__(self) -> None:
        self.codigo = str(self.codigo).strip().upper()
        self.nombre = normalizar_nombre(self.nombre)
        if not self.codigo:
            raise ValueError("El código de la materia no puede estar vacío.")
        if not self.nombre:
            raise ValueError("El nombre de la materia no puede estar vacío.")
        if isinstance(self.creditos, bool) or not isinstance(self.creditos, (int, float)):
            raise ValueError("Los créditos deben ser un número.")
        self.creditos = float(self.creditos)
        if not math.isfinite(self.creditos) or self.creditos < 0:
            raise ValueError("Los créditos deben ser un número mayor o igual a cero.")

    @property
    def activa(self) -> bool:
        return self.eliminado_en is None


@dataclass
class Periodo:
    """Periodo académico con una instantánea de la escala de calificación."""

    id: str
    nombre: str
    escala_min: float
    escala_max: float
    aprobacion_min: float
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    activo: bool = True
    creado_en: str = ""

    def __post_init__(self) -> None:
        self.nombre = normalizar_nombre(self.nombre)
        if not self.nombre:
            raise ValueError("El nombre del periodo no puede estar vacío.")
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha final no puede ser anterior a la inicial.")
        # Construir la escala valida rangos y umbral de aprobación.
        self.escala

    @property
    def escala(self) -> Escala:
        return Escala(
            minima=float(self.escala_min),
            maxima=float(self.escala_max),
            aprobacion=float(self.aprobacion_min),
        )


@dataclass
class Inscripcion:
    """Vínculo único entre estudiante, materia y periodo."""

    id: str
    estudiante_id: str
    materia_id: str
    periodo_id: str
    estado: str = "activa"
    creado_en: str = ""

    def __post_init__(self) -> None:
        if self.estado not in ESTADOS_INSCRIPCION:
            raise ValueError(f"Estado de inscripción no válido: {self.estado}")


@dataclass
class Calificacion:
    """Nota obtenida por un estudiante en una inscripción."""

    id: str
    inscripcion_id: str
    nota: float
    fecha: str
    descripcion: str | None = None
    origen: str = "app"
    creado_en: str = ""
    anulada_en: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.nota, bool) or not isinstance(self.nota, (int, float)):
            raise ValueError("La nota debe ser un número válido.")
        self.nota = float(self.nota)
        if not math.isfinite(self.nota):
            raise ValueError("La nota debe ser un número válido.")
        if self.descripcion is not None:
            self.descripcion = " ".join(str(self.descripcion).split()) or None

    @property
    def activa(self) -> bool:
        return self.anulada_en is None


@dataclass(frozen=True)
class CalificacionDetalle:
    """Calificación enriquecida con materia, periodo y estudiante."""

    id: str
    nota: float
    fecha: str
    descripcion: str | None
    materia_id: str
    materia_codigo: str
    materia_nombre: str
    periodo_id: str
    periodo_nombre: str
    anulada_en: str | None = None
    estudiante_id: str = ""
    estudiante_nombre: str = ""
    estudiante_codigo: str = ""


@dataclass
class ResumenEstudiante:
    """Resumen académico reutilizable por escritorio y web."""

    estudiante: Estudiante
    notas: list[float] = field(default_factory=list)
    escala: Escala = field(default_factory=lambda: ESCALA_PREDETERMINADA)

    @property
    def promedio(self) -> float | None:
        if not self.notas:
            return None
        return sum(self.notas) / len(self.notas)

    @property
    def estado(self) -> str:
        if self.promedio is None:
            return "SIN NOTAS"
        return self.escala.estado(self.promedio)
