"""Lectura y normalización del historial JSON de la versión 2.0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.core.errores import ErrorMigracion
from app.core.escala import ESCALA_PREDETERMINADA, Escala
from app.core.texto import clave_nombre, normalizar_nombre


@dataclass
class RegistroValido:
    """Registro del JSON listo para insertarse en SQLite."""

    indice: int
    nombre: str
    notas: list[float]
    clave: str
    huella: str


@dataclass
class RegistroOmitido:
    """Registro que no se importará, con el motivo visible."""

    indice: int
    nombre: str
    motivo: str


@dataclass
class AnalisisJSON:
    """Resultado del análisis previo, sin escribir nada."""

    ruta: Path
    sha256: str
    total_leidos: int
    validos: list[RegistroValido] = field(default_factory=list)
    duplicados: list[RegistroOmitido] = field(default_factory=list)
    invalidos: list[RegistroOmitido] = field(default_factory=list)
    posibles_duplicados: list[dict[str, object]] = field(default_factory=list)

    @property
    def total_notas(self) -> int:
        return sum(len(registro.notas) for registro in self.validos)


def calcular_sha256(ruta: str | Path) -> str:
    """Calcula el SHA-256 binario de un archivo."""
    digest = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _leer_entradas(ruta: Path) -> list[object]:
    if not ruta.exists():
        raise ErrorMigracion(f"No existe el archivo JSON: '{ruta}'.")
    if not ruta.is_file():
        raise ErrorMigracion(f"La ruta JSON no es un archivo: '{ruta}'.")

    try:
        texto = ruta.read_text(encoding="utf-8-sig")
        datos = json.loads(texto)
    except (OSError, UnicodeDecodeError) as error:
        raise ErrorMigracion(f"No se pudo leer el JSON '{ruta}': {error}") from error
    except json.JSONDecodeError as error:
        raise ErrorMigracion(
            f"El archivo '{ruta}' no es un JSON válido: {error}"
        ) from error

    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        entradas = datos.get("estudiantes")
        if entradas is None:
            raise ErrorMigracion("El JSON no contiene la clave 'estudiantes'.")
        if not isinstance(entradas, list):
            raise ErrorMigracion("La clave 'estudiantes' debe contener una lista.")
        return entradas

    raise ErrorMigracion("El formato del JSON no es reconocido.")


def _huella(clave: str, notas: list[float]) -> str:
    """Huella canónica para detectar duplicados exactos sin importar el orden."""
    canonical = json.dumps(
        {"nombre": clave, "notas": sorted(f"{nota:.10f}" for nota in notas)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validar_entrada(
    entrada: object, indice: int, escala: Escala
) -> tuple[RegistroValido | None, str | None, str]:
    nombre_mostrar = f"registro #{indice + 1}"

    if not isinstance(entrada, dict):
        return None, "El registro no es un objeto JSON.", nombre_mostrar

    nombre_bruto = entrada.get("nombre")
    if not isinstance(nombre_bruto, str):
        return None, "El nombre no es texto.", nombre_mostrar

    try:
        nombre = normalizar_nombre(nombre_bruto)
    except ValueError:
        return None, "El nombre no es válido.", nombre_mostrar

    if nombre:
        nombre_mostrar = nombre
    if not nombre:
        return None, "El nombre está vacío.", nombre_mostrar

    notas_brutas = entrada.get("notas")
    if not isinstance(notas_brutas, list):
        return None, "Las notas deben ser una lista.", nombre_mostrar

    notas: list[float] = []
    for posicion, nota_bruta in enumerate(notas_brutas, start=1):
        try:
            notas.append(escala.validar(nota_bruta))
        except ValueError as error:
            return None, f"Nota #{posicion} inválida: {error}", nombre_mostrar

    clave = clave_nombre(nombre)
    return (
        RegistroValido(
            indice=indice,
            nombre=nombre,
            notas=notas,
            clave=clave,
            huella=_huella(clave, notas),
        ),
        None,
        nombre_mostrar,
    )


def analizar_json(
    ruta: str | Path,
    escala: Escala | None = None,
) -> AnalisisJSON:
    """Lee el JSON legado y clasifica registros válidos, inválidos y duplicados.

    No crea, modifica ni elimina archivos.
    """
    ruta = Path(ruta)
    escala = escala or ESCALA_PREDETERMINADA
    entradas = _leer_entradas(ruta)
    sha256 = calcular_sha256(ruta)

    analisis = AnalisisJSON(
        ruta=ruta,
        sha256=sha256,
        total_leidos=len(entradas),
    )

    por_huella: dict[str, RegistroValido] = {}
    por_clave: dict[str, list[RegistroValido]] = {}

    for indice, entrada in enumerate(entradas):
        registro, error, nombre = _validar_entrada(entrada, indice, escala)
        if registro is None:
            analisis.invalidos.append(
                RegistroOmitido(indice=indice, nombre=nombre, motivo=error or "Inválido")
            )
            continue

        anterior = por_huella.get(registro.huella)
        if anterior is not None:
            analisis.duplicados.append(
                RegistroOmitido(
                    indice=indice,
                    nombre=registro.nombre,
                    motivo=(
                        "Duplicado exacto de "
                        f"'{anterior.nombre}' (registro #{anterior.indice + 1})."
                    ),
                )
            )
            continue

        por_huella[registro.huella] = registro
        por_clave.setdefault(registro.clave, []).append(registro)
        analisis.validos.append(registro)

    for clave, registros in por_clave.items():
        huellas = {registro.huella for registro in registros}
        if len(huellas) > 1:
            analisis.posibles_duplicados.append(
                {
                    "nombre": registros[0].nombre,
                    "clave": clave,
                    "registros": [registro.indice + 1 for registro in registros],
                    "motivo": "Mismo nombre con notas distintas; se conservan por separado.",
                }
            )

    total_clasificado = (
        len(analisis.validos) + len(analisis.duplicados) + len(analisis.invalidos)
    )
    if total_clasificado != analisis.total_leidos:
        raise ErrorMigracion(
            "La clasificación del JSON es inconsistente: "
            f"{total_clasificado} clasificados de {analisis.total_leidos}."
        )

    return analisis
