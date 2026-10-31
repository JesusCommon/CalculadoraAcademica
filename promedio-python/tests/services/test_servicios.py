"""Pruebas de estudiantes, materias, periodos y calificaciones."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.database.unidad import UnidadDeTrabajo
from app.services.fabrica import crear_servicios


class BaseServiciosTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "academico.db"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def abrir(self) -> UnidadDeTrabajo:
        return UnidadDeTrabajo(self.ruta)


class EstudianteServiceTest(BaseServiciosTest):
    def test_crea_lista_busca_actualiza_y_elimina_logicamente(self) -> None:
        with self.abrir() as uow:
            servicio = crear_servicios(uow.repos).estudiantes
            ana = servicio.crear("  Ana   Pérez  ", " ana@example.com ")
            luis = servicio.crear("Luis")

            self.assertEqual(ana.nombre, "Ana Pérez")
            self.assertEqual(ana.codigo, "EST-000001")
            self.assertEqual(luis.codigo, "EST-000002")
            self.assertEqual(servicio.contar(), 2)
            self.assertEqual([e.nombre for e in servicio.listar("ana")], ["Ana Pérez"])
            self.assertEqual(servicio.listar("Pérez")[0].id, ana.id)

            actualizado = servicio.actualizar(
                ana.id, nombre="Ana María", correo="nuevo@example.com"
            )
            self.assertEqual(actualizado.nombre, "Ana María")
            self.assertEqual(actualizado.correo, "nuevo@example.com")

            servicio.eliminar(luis.id)
            self.assertEqual(servicio.contar(), 1)
            self.assertEqual(len(servicio.listar(incluir_eliminados=True)), 2)
            with self.assertRaises(NoEncontrado):
                servicio.obtener(luis.id)

    def test_rollback_no_deja_estudiantes(self) -> None:
        with self.assertRaises(RuntimeError):
            with self.abrir() as uow:
                crear_servicios(uow.repos).estudiantes.crear("Temporal")
                raise RuntimeError("fallo simulado")

        with self.abrir() as uow:
            self.assertEqual(crear_servicios(uow.repos).estudiantes.contar(), 0)


class MateriaServiceTest(BaseServiciosTest):
    def test_gestiona_materias_y_evita_codigos_duplicados(self) -> None:
        with self.abrir() as uow:
            servicio = crear_servicios(uow.repos).materias
            materia = servicio.crear(" mate-101 ", " Matemática I ", 3)
            self.assertEqual(materia.codigo, "MATE-101")
            self.assertEqual(materia.nombre, "Matemática I")
            self.assertEqual(materia.creditos, 3.0)

            with self.assertRaises(Conflicto):
                servicio.crear("MATE-101", "Otra")

            actualizada = servicio.actualizar(
                materia.id, nombre="Matemática II", creditos=4
            )
            self.assertEqual(actualizada.nombre, "Matemática II")
            self.assertEqual(actualizada.creditos, 4.0)

            servicio.eliminar(materia.id)
            with self.assertRaises(NoEncontrado):
                servicio.obtener(materia.id)
            self.assertNotIn(
                materia.id, [m.id for m in servicio.listar()]
            )
            self.assertIn(
                materia.id, [m.id for m in servicio.listar(incluir_eliminadas=True)]
            )


class PeriodoYConfiguracionTest(BaseServiciosTest):
    def test_escala_global_y_instantanea_por_periodo(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            periodos = servicios.periodos
            general = periodos.listar()[0]
            self.assertEqual(general.nombre, "Periodo general")
            self.assertEqual(general.escala.maxima, 5.0)

            nueva = servicios.configuracion.actualizar_escala(0, 100, 60, 1)
            self.assertEqual(nueva.maxima, 100.0)

            periodo_2026 = periodos.crear("2026", fecha_inicio="2026-01-01")
            self.assertEqual(periodo_2026.escala.minima, 0.0)
            self.assertEqual(periodo_2026.escala.maxima, 100.0)
            self.assertEqual(periodo_2026.escala.aprobacion, 60.0)

            # El periodo anterior conserva su escala histórica.
            self.assertEqual(periodos.obtener(general.id).escala.maxima, 5.0)

            with self.assertRaises(Conflicto):
                periodos.crear("2026")


class CalificacionServiceTest(BaseServiciosTest):
    def test_registra_promedia_y_anula_calificaciones(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            estudiante = servicios.estudiantes.crear("Ana")
            materia = servicios.materias.crear("MAT", "Matemática")
            periodo = servicios.periodos.listar()[0]

            primera = servicios.calificaciones.registrar(
                estudiante.id, materia.id, periodo.id, 4.5
            )
            segunda = servicios.calificaciones.registrar(
                estudiante.id, materia.id, periodo.id, 3.0, descripcion="Parcial"
            )

            self.assertEqual(primera.nota, 4.5)
            self.assertEqual(segunda.descripcion, "Parcial")
            self.assertAlmostEqual(
                servicios.calificaciones.promedio(estudiante.id), 3.75
            )
            self.assertEqual(
                len(servicios.calificaciones.listar_por_estudiante(estudiante.id)), 2
            )
            detalles = servicios.calificaciones.listar_por_estudiante(estudiante.id)
            self.assertEqual(detalles[0].materia_nombre, "Matemática")
            self.assertEqual(detalles[0].periodo_nombre, "Periodo general")

            servicios.calificaciones.anular(primera.id)
            self.assertAlmostEqual(
                servicios.calificaciones.promedio(estudiante.id), 3.0
            )
            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.obtener(primera.id)

    def test_rechaza_notas_fuera_de_la_escala_o_entidades_inexistentes(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            estudiante = servicios.estudiantes.crear("Ana")
            materia = servicios.materias.crear("MAT", "Matemática")
            periodo = servicios.periodos.listar()[0]

            with self.assertRaises(DatosInvalidos):
                servicios.calificaciones.registrar(
                    estudiante.id, materia.id, periodo.id, 5.1
                )
            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.registrar(
                    "inexistente", materia.id, periodo.id, 4.0
                )
            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.registrar(
                    estudiante.id, "inexistente", periodo.id, 4.0
                )
            self.assertIsNone(servicios.calificaciones.promedio(estudiante.id))

    def test_usa_la_escala_del_periodo(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            estudiante = servicios.estudiantes.crear("Ana")
            materia = servicios.materias.crear("MAT", "Matemática")
            servicios.configuracion.actualizar_escala(0, 100, 60, 2)
            periodo = servicios.periodos.crear("2027")

            with self.assertRaises(DatosInvalidos):
                servicios.calificaciones.registrar(
                    estudiante.id, materia.id, periodo.id, 101
                )
            calificacion = servicios.calificaciones.registrar(
                estudiante.id, materia.id, periodo.id, 85
            )
            self.assertEqual(calificacion.nota, 85.0)
            self.assertEqual(
                servicios.calificaciones.promedio(estudiante.id, periodo.id), 85.0
            )

    def test_una_sola_inscripcion_por_estudiante_materia_periodo(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            estudiante = servicios.estudiantes.crear("Ana")
            materia = servicios.materias.listar()[0]
            periodo = servicios.periodos.listar()[0]

            servicios.calificaciones.registrar(
                estudiante.id, materia.id, periodo.id, 4.0
            )
            servicios.calificaciones.registrar(
                estudiante.id, materia.id, periodo.id, 5.0
            )

            inscripcion = uow.repos.inscripciones.obtener_por_clave(
                estudiante.id, materia.id, periodo.id
            )
            self.assertIsNotNone(inscripcion)
            self.assertEqual(
                len(
                    uow.repos.calificaciones.listar_por_inscripcion(
                        inscripcion.id
                    )
                ),
                2,
            )


if __name__ == "__main__":
    unittest.main()
