"""Persistencia del historial de estudiantes en un archivo JSON.

La interfaz gráfica no conoce los detalles del almacenamiento: solo usa esta
clase para cargar, modificar y guardar el historial.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .estudiante import Estudiante

# ``app/historial.py`` -> sube dos niveles hasta la raíz del proyecto.
RUTA_PREDETERMINADA = Path(__file__).resolve().parent.parent / "datos" / "historial.json"

VERSION_FORMATO = 1


class ErrorHistorial(Exception):
    """Error controlado al leer o escribir el historial."""


class Historial:
    """Colección ordenada de estudiantes respaldada por un archivo JSON."""

    def __init__(self, ruta: str | Path | None = None) -> None:
        self.ruta = Path(ruta) if ruta is not None else RUTA_PREDETERMINADA
        self._estudiantes: list[Estudiante] = []

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------
    @property
    def estudiantes(self) -> tuple[Estudiante, ...]:
        """Copia inmutable de los estudiantes registrados."""
        return tuple(self._estudiantes)

    def __len__(self) -> int:
        return len(self._estudiantes)

    def __iter__(self):
        return iter(self._estudiantes)

    def __getitem__(self, indice: int) -> Estudiante:
        return self._estudiantes[indice]

    # ------------------------------------------------------------------
    # Modificación en memoria
    # ------------------------------------------------------------------
    def agregar(self, estudiante: Estudiante) -> None:
        """Agrega un estudiante al final del historial."""
        if not isinstance(estudiante, Estudiante):
            raise TypeError("Solo se pueden agregar objetos Estudiante.")
        self._estudiantes.append(estudiante)

    def reemplazar(self, indice: int, estudiante: Estudiante) -> None:
        """Reemplaza el estudiante de la posición indicada."""
        self._validar_indice(indice)
        if not isinstance(estudiante, Estudiante):
            raise TypeError("Solo se pueden guardar objetos Estudiante.")
        self._estudiantes[indice] = estudiante

    def eliminar(self, indice: int) -> Estudiante:
        """Elimina y devuelve el estudiante de la posición indicada."""
        self._validar_indice(indice)
        return self._estudiantes.pop(indice)

    def limpiar(self) -> None:
        """Vacía el historial en memoria (no borra el archivo)."""
        self._estudiantes.clear()

    def _validar_indice(self, indice: int) -> None:
        if isinstance(indice, bool) or not isinstance(indice, int):
            raise ValueError("La posición del historial debe ser un número entero.")
        if not 0 <= indice < len(self._estudiantes):
            raise IndexError("La posición del historial no existe.")

    # ------------------------------------------------------------------
    # Archivo JSON
    # ------------------------------------------------------------------
    def cargar(self) -> None:
        """Carga los estudiantes desde el archivo JSON.

        Si el archivo no existe, el historial queda vacío. Si el archivo está
        dañado, se conserva una copia con extensión ``.corrupto`` para no
        perder información y se lanza ``ErrorHistorial``.
        """
        if not self.ruta.exists():
            self._estudiantes = []
            return

        try:
            contenido = self.ruta.read_text(encoding="utf-8")
            datos = json.loads(contenido) if contenido.strip() else {}
        except (OSError, UnicodeDecodeError) as error:
            raise ErrorHistorial(
                f"No se pudo leer el historial en '{self.ruta}': {error}"
            ) from error
        except json.JSONDecodeError as error:
            respaldo = self._respaldar_archivo_corrupto()
            raise ErrorHistorial(
                "El archivo del historial no es un JSON válido. "
                f"Se guardó una copia en '{respaldo}'."
            ) from error

        if isinstance(datos, list):
            # Tolerancia con versiones anteriores que guardaban solo la lista.
            lista = datos
        elif isinstance(datos, dict):
            lista = datos.get("estudiantes", [])
        else:
            raise ErrorHistorial("El formato del historial no es reconocido.")

        if not isinstance(lista, list):
            raise ErrorHistorial("El historial debe contener una lista de estudiantes.")

        estudiantes: list[Estudiante] = []
        descartados = 0
        for entrada in lista:
            try:
                estudiantes.append(Estudiante.desde_dict(entrada))
            except (ValueError, TypeError):
                # Una entrada dañada no debe impedir cargar el resto.
                descartados += 1

        self._estudiantes = estudiantes

        if descartados:
            raise ErrorHistorial(
                f"Se cargaron {len(estudiantes)} estudiantes, pero se omitieron "
                f"{descartados} registros con datos inválidos."
            )

    def guardar(self) -> None:
        """Guarda el historial en el archivo JSON de forma atómica."""
        datos = {
            "version": VERSION_FORMATO,
            "estudiantes": [estudiante.a_dict() for estudiante in self._estudiantes],
        }

        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            temporal = self.ruta.with_name(f"{self.ruta.name}.tmp")
            with temporal.open("w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")

            # Reemplazo atómico: evita dejar el JSON a medio escribir.
            os.replace(temporal, self.ruta)
        except OSError as error:
            raise ErrorHistorial(
                f"No se pudo guardar el historial en '{self.ruta}': {error}"
            ) from error

    def _respaldar_archivo_corrupto(self) -> Path:
        """Renombra el archivo dañado a ``*.corrupto`` y devuelve la ruta."""
        respaldo = self.ruta.with_suffix(f"{self.ruta.suffix}.corrupto")
        try:
            os.replace(self.ruta, respaldo)
        except OSError:
            return self.ruta
        return respaldo
