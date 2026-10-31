"""Servicio de configuración de la escala académica."""

from __future__ import annotations

from app.core.escala import Escala
from app.core.puertos import RepositorioConfiguracion
from app.core.tiempo import ahora_iso


class ConfiguracionService:
    """Lee y actualiza la escala global usada por los nuevos periodos."""

    def __init__(self, repositorio: RepositorioConfiguracion, reloj=ahora_iso) -> None:
        self.repositorio = repositorio
        self.reloj = reloj

    def obtener_escala(self) -> Escala:
        valores = self.repositorio.obtener_todas()

        def numero(clave: str, predeterminado: float) -> float:
            texto = valores.get(clave)
            if texto is None:
                return predeterminado
            try:
                return float(texto)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"La configuración '{clave}' no contiene un número válido."
                ) from error

        def entero(clave: str, predeterminado: int) -> int:
            texto = valores.get(clave)
            if texto is None:
                return predeterminado
            try:
                return int(texto)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"La configuración '{clave}' no contiene un entero válido."
                ) from error

        return Escala(
            minima=numero("escala_min", 0.0),
            maxima=numero("escala_max", 5.0),
            aprobacion=numero("aprobacion_min", 3.0),
            decimales=entero("decimales", 2),
        )

    def actualizar_escala(
        self,
        minima: float,
        maxima: float,
        aprobacion: float,
        decimales: int = 2,
    ) -> Escala:
        escala = Escala(
            minima=float(minima),
            maxima=float(maxima),
            aprobacion=float(aprobacion),
            decimales=decimales,
        )
        self.repositorio.establecer_varias(
            {
                "escala_min": str(escala.minima),
                "escala_max": str(escala.maxima),
                "aprobacion_min": str(escala.aprobacion),
                "decimales": str(escala.decimales),
            },
            self.reloj(),
        )
        return escala

    def obtener(self, clave: str, predeterminado: str | None = None) -> str | None:
        return self.repositorio.obtener(clave, predeterminado)
