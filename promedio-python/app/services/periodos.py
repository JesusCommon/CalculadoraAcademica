"""Casos de uso de periodos académicos."""

from __future__ import annotations

from app.core.entidades import Periodo
from app.core.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.core.escala import Escala
from app.core.puertos import RepositorioPeriodos
from app.core.texto import normalizar_nombre
from app.core.tiempo import ahora_iso, nuevo_id
from app.services.configuracion import ConfiguracionService

_SIN_CAMBIOS = object()


class PeriodoService:
    """Crea periodos con una instantánea de la escala vigente."""

    def __init__(
        self,
        repositorio: RepositorioPeriodos,
        configuracion: ConfiguracionService,
        reloj=ahora_iso,
        generador_id=nuevo_id,
    ) -> None:
        self.repositorio = repositorio
        self.configuracion = configuracion
        self.reloj = reloj
        self.generador_id = generador_id

    def crear(
        self,
        nombre: str,
        *,
        fecha_inicio: str | None = None,
        fecha_fin: str | None = None,
        escala: Escala | None = None,
        activo: bool = True,
    ) -> Periodo:
        try:
            nombre_normalizado = normalizar_nombre(nombre)
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error
        if not nombre_normalizado:
            raise DatosInvalidos("El nombre del periodo no puede estar vacío.")

        if self.repositorio.obtener_por_nombre(nombre_normalizado) is not None:
            raise Conflicto(f"Ya existe un periodo llamado '{nombre_normalizado}'.")

        escala = escala or self.configuracion.obtener_escala()
        try:
            periodo = Periodo(
                id=self.generador_id(),
                nombre=nombre_normalizado,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                escala_min=escala.minima,
                escala_max=escala.maxima,
                aprobacion_min=escala.aprobacion,
                activo=activo,
                creado_en=self.reloj(),
            )
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        self.repositorio.agregar(periodo)
        return periodo

    def obtener(self, periodo_id: str) -> Periodo:
        periodo = self.repositorio.obtener(periodo_id)
        if periodo is None:
            raise NoEncontrado("El periodo no existe.")
        return periodo

    def actualizar(
        self,
        periodo_id: str,
        *,
        nombre: str | None = None,
        fecha_inicio: object = _SIN_CAMBIOS,
        fecha_fin: object = _SIN_CAMBIOS,
        escala: Escala | None = None,
        activo: bool | None = None,
    ) -> Periodo:
        """Actualiza un periodo conservando los campos no indicados."""
        periodo = self.obtener(periodo_id)
        nombre_final = periodo.nombre

        if nombre is not None:
            try:
                nombre_final = normalizar_nombre(nombre)
            except ValueError as error:
                raise DatosInvalidos(str(error)) from error
            if not nombre_final:
                raise DatosInvalidos("El nombre del periodo no puede estar vacío.")
            existente = self.repositorio.obtener_por_nombre(nombre_final)
            if existente is not None and existente.id != periodo.id:
                raise Conflicto(f"Ya existe un periodo llamado '{nombre_final}'.")

        escala_final = escala or periodo.escala
        try:
            actualizado = Periodo(
                id=periodo.id,
                nombre=nombre_final,
                fecha_inicio=(
                    periodo.fecha_inicio
                    if fecha_inicio is _SIN_CAMBIOS
                    else fecha_inicio  # type: ignore[arg-type]
                ),
                fecha_fin=(
                    periodo.fecha_fin
                    if fecha_fin is _SIN_CAMBIOS
                    else fecha_fin  # type: ignore[arg-type]
                ),
                escala_min=escala_final.minima,
                escala_max=escala_final.maxima,
                aprobacion_min=escala_final.aprobacion,
                activo=periodo.activo if activo is None else bool(activo),
                creado_en=periodo.creado_en,
            )
        except ValueError as error:
            raise DatosInvalidos(str(error)) from error

        self.repositorio.actualizar(actualizado)
        return actualizado

    def obtener_por_nombre(self, nombre: str) -> Periodo | None:
        return self.repositorio.obtener_por_nombre(nombre)

    def listar(self, incluir_inactivos: bool = False) -> list[Periodo]:
        return self.repositorio.listar(incluir_inactivos)
