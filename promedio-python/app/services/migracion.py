"""Servicio de migración JSON 2.0 → SQLite 3.0.

La simulación nunca escribe. La aplicación crea respaldos verificados, importa
dentro de una transacción y comprueba la equivalencia antes de confirmar.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.core.entidades import Calificacion, Estudiante, Inscripcion, Materia, Periodo
from app.core.errores import ErrorMigracion
from app.core.escala import ESCALA_PREDETERMINADA
from app.core.promedio import calcular_promedio, determinar_estado
from app.core.texto import clave_nombre
from app.core.tiempo import ahora_iso, id_determinista, nuevo_id, hoy_iso
from app.database.conexion import RUTA_BD_PREDETERMINADA, respaldar_bd
from app.database.json_legacy import AnalisisJSON, analizar_json, calcular_sha256
from app.database.unidad import UnidadDeTrabajo

PERIODO_MIGRACION = "Datos migrados 2.0"
MATERIA_MIGRACION_CODIGO = "GEN-MIG"
MATERIA_MIGRACION_NOMBRE = "Materia general (migración)"
TOLERANCIA_PROMEDIO = 1e-9


@dataclass
class ResultadoMigracion:
    """Resultado verificable de una simulación o de una migración aplicada."""

    archivo: str
    sha256: str
    simulado: bool
    aplicada: bool = False
    ya_existia: bool = False
    total_leidos: int = 0
    validos: int = 0
    invalidos: int = 0
    duplicados: int = 0
    importados: int = 0
    calificaciones_importadas: int = 0
    estudiantes: list[dict[str, object]] = field(default_factory=list)
    invalidos_detalle: list[dict[str, object]] = field(default_factory=list)
    duplicados_detalle: list[dict[str, object]] = field(default_factory=list)
    posibles_duplicados: list[dict[str, object]] = field(default_factory=list)
    respaldo_json: str | None = None
    respaldo_bd: str | None = None
    verificacion: list[str] = field(default_factory=list)
    correcto: bool = False
    mensaje: str = ""

    def a_dict(self) -> dict[str, object]:
        return asdict(self)


class MigracionService:
    """Orquesta análisis, respaldo, importación y verificación."""

    def __init__(
        self,
        ruta_json: str | Path,
        ruta_db: str | Path | None = None,
        backups_dir: str | Path | None = None,
        reloj=ahora_iso,
    ) -> None:
        self.ruta_json = Path(ruta_json)
        self.ruta_db = Path(ruta_db) if ruta_db is not None else RUTA_BD_PREDETERMINADA
        self.backups_dir = (
            Path(backups_dir)
            if backups_dir is not None
            else self.ruta_json.parent / "backups"
        )
        self.reloj = reloj
        self._respaldo_json_sha: str | None = None
        self._ruta_respaldo_json: Path | None = None

    # ------------------------------------------------------------------
    # Simulación
    # ------------------------------------------------------------------
    def simular(self) -> ResultadoMigracion:
        analisis = analizar_json(self.ruta_json, ESCALA_PREDETERMINADA)
        resultado = self._resultado_base(analisis, simulado=True)

        resultado.estudiantes = [
            self._resumen_estudiante(registro) for registro in analisis.validos
        ]
        resultado.verificacion = [
            f"JSON legible con SHA-256 {analisis.sha256}.",
            f"{analisis.total_leidos} registros leídos.",
            f"{len(analisis.validos)} estudiantes válidos y "
            f"{analisis.total_notas} notas listas para importar.",
        ]
        if analisis.invalidos:
            resultado.verificacion.append(
                f"Advertencia: {len(analisis.invalidos)} registro(s) inválido(s) "
                "se omitirán (no bloquean la migración)."
            )
        if analisis.duplicados:
            resultado.verificacion.append(
                f"{len(analisis.duplicados)} duplicado(s) exacto(s) se omitirán."
            )
        if analisis.posibles_duplicados:
            resultado.verificacion.append(
                f"{len(analisis.posibles_duplicados)} posible(s) duplicado(s) por "
                "nombre se conservarán por separado para revisión."
            )

        resultado.correcto = True
        resultado.mensaje = (
            "Simulación correcta. No se escribió ningún archivo ni se modificó "
            "el JSON original."
        )
        return resultado

    # ------------------------------------------------------------------
    # Aplicación
    # ------------------------------------------------------------------
    def aplicar(self) -> ResultadoMigracion:
        analisis = analizar_json(self.ruta_json, ESCALA_PREDETERMINADA)
        resultado = self._resultado_base(analisis, simulado=False)

        # Los respaldos se crean y verifican antes de tocar la base.
        resultado.respaldo_json = str(self._respaldar_json())
        resultado.respaldo_bd = (
            str(self._respaldar_bd()) if self._bd_existe_con_datos() else None
        )

        with UnidadDeTrabajo(self.ruta_db) as uow:
            repos = uow.repos

            if repos.migraciones.existe_sha(analisis.sha256):
                resultado.ya_existia = True
                resultado.correcto = True
                resultado.mensaje = (
                    "Este archivo ya fue migrado antes (mismo SHA-256). "
                    "No se insertaron registros nuevos."
                )
                resultado.verificacion = [
                    "Migración idempotente: no se duplicaron estudiantes ni notas.",
                    "El JSON original no se modificó.",
                ]
            else:
                periodo, materia = self._asegurar_contexto(uow)
                importados_info: list[dict[str, object]] = []

                for registro in analisis.validos:
                    existente = repos.estudiantes.obtener_por_huella(registro.huella)
                    if existente is not None:
                        resultado.duplicados += 1
                        resultado.duplicados_detalle.append(
                            {
                                "indice": registro.indice + 1,
                                "nombre": registro.nombre,
                                "motivo": "Ya existe un estudiante con la misma huella.",
                            }
                        )
                        resultado.estudiantes.append(
                            {
                                **self._resumen_estudiante(registro),
                                "codigo": existente.codigo,
                                "importado": False,
                            }
                        )
                        continue

                    info = self._insertar_estudiante(
                        uow, registro, periodo, materia
                    )
                    importados_info.append(info)
                    resultado.importados += 1
                    resultado.calificaciones_importadas += int(info["notas_importadas"])
                    resultado.estudiantes.append(
                        {
                            **self._resumen_estudiante(registro),
                            "codigo": info["codigo"],
                            "importado": True,
                        }
                    )

                repos.migraciones.registrar(
                    {
                        "id": nuevo_id(),
                        "archivo": str(self.ruta_json),
                        "sha256": analisis.sha256,
                        "ejecutada_en": self.reloj(),
                        "total_leidos": analisis.total_leidos,
                        "importados": resultado.importados,
                        "duplicados": resultado.duplicados,
                        "invalidos": len(analisis.invalidos),
                        "resultado": "ok",
                        "detalle": {
                            "estudiantes": resultado.estudiantes,
                            "duplicados": resultado.duplicados_detalle,
                            "invalidos": resultado.invalidos_detalle,
                            "posibles_duplicados": resultado.posibles_duplicados,
                        },
                    }
                )

                resultado.verificacion = self._verificar(
                    uow, analisis, periodo, importados_info
                )
                resultado.correcto = True
                resultado.aplicada = True
                resultado.mensaje = (
                    "Migración aplicada y verificada. El JSON original sigue intacto."
                )

        self._escribir_reporte(resultado)
        return resultado

    # ------------------------------------------------------------------
    # Construcción del resultado
    # ------------------------------------------------------------------
    def _resultado_base(
        self, analisis: AnalisisJSON, *, simulado: bool
    ) -> ResultadoMigracion:
        return ResultadoMigracion(
            archivo=str(self.ruta_json),
            sha256=analisis.sha256,
            simulado=simulado,
            total_leidos=analisis.total_leidos,
            validos=len(analisis.validos),
            invalidos=len(analisis.invalidos),
            duplicados=len(analisis.duplicados),
            invalidos_detalle=[
                {
                    "indice": registro.indice + 1,
                    "nombre": registro.nombre,
                    "motivo": registro.motivo,
                }
                for registro in analisis.invalidos
            ],
            duplicados_detalle=[
                {
                    "indice": registro.indice + 1,
                    "nombre": registro.nombre,
                    "motivo": registro.motivo,
                }
                for registro in analisis.duplicados
            ],
            posibles_duplicados=list(analisis.posibles_duplicados),
        )

    def _resumen_estudiante(self, registro) -> dict[str, object]:
        if registro.notas:
            promedio = calcular_promedio(registro.notas)
            estado = determinar_estado(promedio, ESCALA_PREDETERMINADA)
        else:
            promedio = None
            estado = "SIN NOTAS"

        return {
            "indice": registro.indice + 1,
            "nombre": registro.nombre,
            "notas": list(registro.notas),
            "cantidad_notas": len(registro.notas),
            "promedio": promedio,
            "estado": estado,
        }

    # ------------------------------------------------------------------
    # Inserción
    # ------------------------------------------------------------------
    def _asegurar_contexto(self, uow: UnidadDeTrabajo) -> tuple[Periodo, Materia]:
        repos = uow.repos
        periodo = repos.periodos.obtener_por_nombre(PERIODO_MIGRACION)
        if periodo is None:
            fecha = self.reloj()
            periodo = Periodo(
                id=id_determinista("periodo:migracion:2.0"),
                nombre=PERIODO_MIGRACION,
                escala_min=ESCALA_PREDETERMINADA.minima,
                escala_max=ESCALA_PREDETERMINADA.maxima,
                aprobacion_min=ESCALA_PREDETERMINADA.aprobacion,
                activo=True,
                creado_en=fecha,
            )
            repos.periodos.agregar(periodo)

        materia = repos.materias.obtener_por_codigo(MATERIA_MIGRACION_CODIGO)
        if materia is None:
            fecha = self.reloj()
            materia = Materia(
                id=id_determinista("materia:migracion"),
                codigo=MATERIA_MIGRACION_CODIGO,
                nombre=MATERIA_MIGRACION_NOMBRE,
                creado_en=fecha,
                actualizado_en=fecha,
            )
            repos.materias.agregar(materia)

        return periodo, materia

    def _insertar_estudiante(
        self,
        uow: UnidadDeTrabajo,
        registro,
        periodo: Periodo,
        materia: Materia,
    ) -> dict[str, object]:
        repos = uow.repos
        fecha = self.reloj()
        estudiante_id = id_determinista(f"estudiante:{registro.huella}")

        existente = repos.estudiantes.obtener(estudiante_id)
        if existente is not None:
            raise ErrorMigracion(
                f"Colisión de identificador para '{registro.nombre}'."
            )

        estudiante = Estudiante(
            id=estudiante_id,
            codigo=repos.estudiantes.siguiente_codigo(),
            nombre=registro.nombre,
            nombre_normalizado=clave_nombre(registro.nombre),
            origen="json_migracion",
            huella_migracion=registro.huella,
            creado_en=fecha,
            actualizado_en=fecha,
        )
        repos.estudiantes.agregar(estudiante)

        inscripcion = Inscripcion(
            id=id_determinista(f"inscripcion:{registro.huella}"),
            estudiante_id=estudiante.id,
            materia_id=materia.id,
            periodo_id=periodo.id,
            creado_en=fecha,
        )
        repos.inscripciones.agregar(inscripcion)

        importadas = 0
        for posicion, nota in enumerate(registro.notas):
            calificacion_id = id_determinista(
                f"calificacion:{registro.huella}:{posicion}"
            )
            if repos.calificaciones.existe(calificacion_id):
                continue
            repos.calificaciones.agregar(
                Calificacion(
                    id=calificacion_id,
                    inscripcion_id=inscripcion.id,
                    nota=nota,
                    fecha=hoy_iso(),
                    descripcion="Importada del historial 2.0",
                    origen="json_migracion",
                    creado_en=fecha,
                )
            )
            importadas += 1

        return {
            "id": estudiante.id,
            "codigo": estudiante.codigo,
            "inscripcion_id": inscripcion.id,
            "notas": list(registro.notas),
            "notas_importadas": importadas,
            "promedio_esperado": (
                calcular_promedio(registro.notas) if registro.notas else None
            ),
        }

    # ------------------------------------------------------------------
    # Verificación y respaldos
    # ------------------------------------------------------------------
    def _verificar(
        self,
        uow: UnidadDeTrabajo,
        analisis: AnalisisJSON,
        periodo: Periodo,
        importados_info: list[dict[str, object]],
    ) -> list[str]:
        repos = uow.repos
        problemas: list[str] = []
        comprobaciones: list[str] = []

        for info in importados_info:
            notas = info["notas"]
            esperado = info["promedio_esperado"]
            if esperado is None:
                continue
            obtenido = repos.calificaciones.promedio_por_estudiante_periodo(
                str(info["id"]), periodo.id
            )
            if obtenido is None:
                problemas.append(f"No se pudo recuperar el promedio de {info['codigo']}.")
            elif abs(float(obtenido) - float(esperado)) > TOLERANCIA_PROMEDIO:
                problemas.append(
                    f"Promedio distinto para {info['codigo']}: "
                    f"esperado {esperado}, obtenido {obtenido}."
                )
            else:
                comprobaciones.append(
                    f"{info['codigo']}: promedio {float(obtenido):.6f} coincide."
                )

            calificaciones = repos.calificaciones.listar_por_inscripcion(
                str(info["inscripcion_id"])
            )
            if len(calificaciones) != len(notas):
                problemas.append(
                    f"{info['codigo']}: se esperaban {len(notas)} notas y hay "
                    f"{len(calificaciones)}."
                )
            else:
                comprobaciones.append(
                    f"{info['codigo']}: {len(notas)} nota(s) conservada(s)."
                )

        clave_foranea = uow.conexion.execute("PRAGMA foreign_key_check").fetchall()
        if clave_foranea:
            problemas.append(
                f"PRAGMA foreign_key_check encontró {len(clave_foranea)} problema(s)."
            )
        else:
            comprobaciones.append("Claves foráneas íntegras.")

        integridad = uow.conexion.execute("PRAGMA integrity_check").fetchone()[0]
        if integridad != "ok":
            problemas.append(f"PRAGMA integrity_check devolvió: {integridad}.")
        else:
            comprobaciones.append("PRAGMA integrity_check = ok.")

        if calcular_sha256(self.ruta_json) != analisis.sha256:
            problemas.append("El JSON original cambió durante la migración.")
        else:
            comprobaciones.append("JSON original sin cambios (SHA-256 idéntico).")

        if self._respaldo_json_sha is not None and self._ruta_respaldo_json is not None:
            respaldo = self._ruta_respaldo_json
            if respaldo.exists() and calcular_sha256(respaldo) != analisis.sha256:
                problemas.append("El respaldo del JSON no coincide con el original.")
            else:
                comprobaciones.append("Respaldo del JSON verificado.")

        if problemas:
            raise ErrorMigracion(
                "La verificación posterior falló: " + " ".join(problemas)
            )

        return comprobaciones

    def _respaldar_json(self) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        marca = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        destino = self.backups_dir / f"historial-{marca}.json"
        try:
            shutil.copy2(self.ruta_json, destino)
        except OSError as error:
            raise ErrorMigracion(f"No se pudo crear el respaldo del JSON: {error}") from error

        esperado = calcular_sha256(self.ruta_json)
        obtenido = calcular_sha256(destino)
        if esperado != obtenido:
            raise ErrorMigracion("El respaldo del JSON no coincide con el original.")

        self._respaldo_json_sha = obtenido
        self._ruta_respaldo_json = destino
        return destino

    def _bd_existe_con_datos(self) -> bool:
        return self.ruta_db.exists() and self.ruta_db.stat().st_size > 0

    def _respaldar_bd(self) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        marca = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        destino = self.backups_dir / f"academico-{marca}.db"
        try:
            respaldar_bd(self.ruta_db, destino)
        except Exception as error:
            raise ErrorMigracion(
                f"No se pudo respaldar la base SQLite antes de migrar: {error}"
            ) from error
        return destino

    def _escribir_reporte(self, resultado: ResultadoMigracion) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        marca = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        destino = self.backups_dir / f"migracion-{marca}.json"
        try:
            destino.write_text(
                json.dumps(resultado.a_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as error:
            raise ErrorMigracion(f"No se pudo escribir el reporte de migración: {error}") from error
        return destino
