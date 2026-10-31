"""Casos de uso de materias."""

from __future__ import annotations

from app.core.entidades import Materia
from app.core.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.core.puertos import RepositorioMaterias
from app.core.tiempo import ahora_iso, nuevo_id


class MateriaService:
    """Alta, consulta, edición y baja lógica de materias."""

    def __init__(
        self,
        repositorio: RepositorioMaterias,
        reloj=ahora_iso,
        generador_id=nuevo_id,
    ) -> None:
        self.repositorio = repositorio
        self.reloj = reloj
        self.generador_id = generador_id

    def crear(self, codigo: str, nombre: str, creditos: float = 0.0) -> Materia:
        codigo = str(codigo).strip().upper()
        if not codigo:
            raise DatosInvalidos("El código de la materia no puede estar vacío.")
        if self.repositorio.obtener_por_codigo(codigo) is not None:
            raise Conflicto(f"Ya existe una materia con el código '{codigo}'.")

        fecha = self.reloj()
        try:
            materia = Materia(
                id=self.generador_id(),
                codigo=codigo,
                nombre=nombre,
                creditos=creditos,
                creado_en=fecha,
                actualizado_en=fecha,
            )
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        self.repositorio.agregar(materia)
        return materia

    def obtener(self, materia_id: str) -> Materia:
        materia = self.repositorio.obtener(materia_id)
        if materia is None or not materia.activa:
            raise NoEncontrado("La materia no existe o fue eliminada.")
        return materia

    def listar(self, incluir_eliminadas: bool = False) -> list[Materia]:
        return self.repositorio.listar(incluir_eliminadas)

    def actualizar(
        self,
        materia_id: str,
        *,
        codigo: str | None = None,
        nombre: str | None = None,
        creditos: float | None = None,
    ) -> Materia:
        materia = self.obtener(materia_id)

        codigo_final = materia.codigo if codigo is None else str(codigo).strip().upper()
        if not codigo_final:
            raise DatosInvalidos("El código de la materia no puede estar vacío.")

        existente = self.repositorio.obtener_por_codigo(codigo_final)
        if existente is not None and existente.id != materia.id:
            raise Conflicto(f"Ya existe una materia con el código '{codigo_final}'.")

        try:
            actualizada = Materia(
                id=materia.id,
                codigo=codigo_final,
                nombre=materia.nombre if nombre is None else nombre,
                creditos=materia.creditos if creditos is None else creditos,
                creado_en=materia.creado_en,
                actualizado_en=self.reloj(),
                eliminado_en=materia.eliminado_en,
            )
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        self.repositorio.actualizar(actualizada)
        return actualizada

    def eliminar(self, materia_id: str) -> None:
        materia = self.obtener(materia_id)
        self.repositorio.eliminar_logico(materia.id, self.reloj())
