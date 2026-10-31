"""Casos de uso de estudiantes."""

from __future__ import annotations

from app.core.entidades import Estudiante
from app.core.errores import DatosInvalidos, NoEncontrado
from app.core.puertos import RepositorioEstudiantes
from app.core.texto import clave_nombre, normalizar_nombre
from app.core.tiempo import ahora_iso, nuevo_id


class EstudianteService:
    """Alta, consulta, edición y baja lógica de estudiantes."""

    def __init__(
        self,
        repositorio: RepositorioEstudiantes,
        reloj=ahora_iso,
        generador_id=nuevo_id,
    ) -> None:
        self.repositorio = repositorio
        self.reloj = reloj
        self.generador_id = generador_id

    def crear(self, nombre: str, correo: str | None = None) -> Estudiante:
        try:
            nombre_normalizado = normalizar_nombre(nombre)
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        if not nombre_normalizado:
            raise DatosInvalidos("El nombre del estudiante no puede estar vacío.")

        correo_normalizado = self._normalizar_correo(correo)
        fecha = self.reloj()
        estudiante = Estudiante(
            id=self.generador_id(),
            codigo=self.repositorio.siguiente_codigo(),
            nombre=nombre_normalizado,
            nombre_normalizado=clave_nombre(nombre_normalizado),
            correo=correo_normalizado,
            creado_en=fecha,
            actualizado_en=fecha,
        )
        self.repositorio.agregar(estudiante)
        return estudiante

    def obtener(self, estudiante_id: str) -> Estudiante:
        estudiante = self.repositorio.obtener(estudiante_id)
        if estudiante is None or not estudiante.activo:
            raise NoEncontrado("El estudiante no existe o fue eliminado.")
        return estudiante

    def listar(
        self, busqueda: str | None = None, incluir_eliminados: bool = False
    ) -> list[Estudiante]:
        return self.repositorio.listar(busqueda, incluir_eliminados)

    def actualizar(
        self,
        estudiante_id: str,
        *,
        nombre: str | None = None,
        correo: str | None = None,
    ) -> Estudiante:
        estudiante = self.obtener(estudiante_id)

        if nombre is not None:
            try:
                nombre_normalizado = normalizar_nombre(nombre)
            except ValueError as error:
                raise DatosInvalidos(str(error)) from error
            if not nombre_normalizado:
                raise DatosInvalidos("El nombre del estudiante no puede estar vacío.")
            estudiante.nombre = nombre_normalizado
            estudiante.nombre_normalizado = clave_nombre(nombre_normalizado)

        if correo is not None:
            estudiante.correo = self._normalizar_correo(correo)

        estudiante.actualizado_en = self.reloj()
        self.repositorio.actualizar(estudiante)
        return estudiante

    @staticmethod
    def _normalizar_correo(correo: str | None) -> str | None:
        if correo is None:
            return None
        if not isinstance(correo, str):
            raise DatosInvalidos("El correo debe ser texto.")
        return correo.strip() or None

    def eliminar(self, estudiante_id: str) -> None:
        estudiante = self.obtener(estudiante_id)
        self.repositorio.eliminar_logico(estudiante.id, self.reloj())

    def contar(self, incluir_eliminados: bool = False) -> int:
        return self.repositorio.contar(incluir_eliminados)
