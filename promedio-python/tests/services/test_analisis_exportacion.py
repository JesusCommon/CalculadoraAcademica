"""Pruebas de los servicios de análisis, periodos y exportaciones."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.core.escala import Escala
from app.database.unidad import UnidadDeTrabajo
from app.services.exportacion import ExportacionService
from app.services.fabrica import crear_servicios


class BaseAnalisisTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "analisis.db"
        with UnidadDeTrabajo(self.ruta) as uow:
            self.servicios = crear_servicios(uow.repos)
            self.ana = self.servicios.estudiantes.crear("Ana Pérez", "ana@example.com")
            self.luis = self.servicios.estudiantes.crear("Luis Torres")
            self.matematica = self.servicios.materias.crear("MAT-101", "Matemática", 4)
            self.fisica = self.servicios.materias.crear("FIS-101", "Física", 3)
            self.periodo = self.servicios.periodos.listar()[0]
            self.servicios.calificaciones.registrar(
                self.ana.id, self.matematica.id, self.periodo.id, 4.5
            )
            self.servicios.calificaciones.registrar(
                self.ana.id, self.fisica.id, self.periodo.id, 3.5
            )
            self.servicios.calificaciones.registrar(
                self.luis.id, self.matematica.id, self.periodo.id, 2.0
            )

    def tearDown(self) -> None:
        self._temp.cleanup()

    def abrir(self) -> UnidadDeTrabajo:
        return UnidadDeTrabajo(self.ruta)


class AnalisisServiceTest(BaseAnalisisTest):
    def test_resumen_general_y_agregados(self) -> None:
        with self.abrir() as uow:
            resumen = crear_servicios(uow.repos).analisis.resumen()

        self.assertEqual(resumen.total_estudiantes, 2)
        self.assertEqual(resumen.total_materias, 3)
        self.assertEqual(resumen.total_periodos, 1)
        self.assertEqual(resumen.total_calificaciones, 3)
        self.assertAlmostEqual(resumen.promedio_general, 10 / 3)
        self.assertEqual((resumen.aprobados, resumen.reprobados, resumen.sin_notas), (1, 1, 0))
        self.assertEqual(len(resumen.estudiantes), 2)
        self.assertEqual([p.etiqueta for p in resumen.por_materia], ["Física", "Matemática"])
        self.assertEqual(resumen.por_materia[1].cantidad, 2)
        self.assertEqual(resumen.por_periodo[0].cantidad, 3)

    def test_resumen_filtrado_por_periodo(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            nuevo = servicios.periodos.crear(
                "2026", escala=Escala(0, 100, 60), fecha_inicio="2026-01-01"
            )
            servicios.calificaciones.registrar(
                self.ana.id, self.matematica.id, nuevo.id, 80
            )
            resumen = servicios.analisis.resumen(periodo_id=nuevo.id)

        self.assertEqual(resumen.total_calificaciones, 1)
        self.assertAlmostEqual(resumen.promedio_general, 80.0)
        self.assertEqual((resumen.aprobados, resumen.reprobados, resumen.sin_notas), (1, 0, 1))

    def test_detalle_estudiante(self) -> None:
        with self.abrir() as uow:
            detalle = crear_servicios(uow.repos).analisis.detalle_estudiante(self.ana.id)

        self.assertEqual(detalle.estudiante.id, self.ana.id)
        self.assertAlmostEqual(detalle.promedio, 4.0)
        self.assertEqual(detalle.estado, "APROBADO")
        self.assertEqual(len(detalle.detalles), 2)
        self.assertEqual(len(detalle.por_materia), 2)
        self.assertEqual(len(detalle.por_periodo), 1)
        self.assertEqual(detalle.por_periodo[0].notas, 2)
        self.assertAlmostEqual(detalle.por_periodo[0].promedio, 4.0)
        self.assertEqual(
            [resumen.nombre for resumen in detalle.por_materia], ["Física", "Matemática"]
        )

    def test_listar_todas_filtra_y_excluye_anuladas(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            todas = servicios.calificaciones.listar_todas()
            self.assertEqual(len(todas), 3)
            self.assertEqual(len(servicios.calificaciones.listar_todas(estudiante_id=self.ana.id)), 2)
            self.assertEqual(
                len(servicios.calificaciones.listar_todas(materia_id=self.matematica.id)), 2
            )
            self.assertEqual(
                len(servicios.calificaciones.listar_todas(periodo_id=self.periodo.id)), 3
            )

            servicios.calificaciones.anular(todas[0].id)
            self.assertEqual(len(servicios.calificaciones.listar_todas()), 2)
            self.assertEqual(
                len(servicios.calificaciones.listar_todas(incluir_anuladas=True)), 3
            )

            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.listar_todas(estudiante_id="inexistente")
            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.listar_todas(materia_id="inexistente")
            with self.assertRaises(NoEncontrado):
                servicios.calificaciones.listar_todas(periodo_id="inexistente")


class PeriodoActualizarTest(BaseAnalisisTest):
    def test_actualiza_conservando_campos_no_indicados(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            periodo = servicios.periodos.crear(
                "2026",
                fecha_inicio="2026-01-10",
                fecha_fin="2026-06-30",
                escala=Escala(0, 100, 60),
                activo=True,
            )
            actualizado = servicios.periodos.actualizar(periodo.id, nombre="2026-I")
            self.assertEqual(actualizado.nombre, "2026-I")
            self.assertEqual(actualizado.fecha_inicio, "2026-01-10")
            self.assertEqual(actualizado.fecha_fin, "2026-06-30")
            self.assertEqual(actualizado.escala.minima, 0.0)
            self.assertEqual(actualizado.escala.maxima, 100.0)
            self.assertTrue(actualizado.activo)

            sin_fechas = servicios.periodos.actualizar(
                periodo.id, fecha_inicio=None, fecha_fin=None, activo=False
            )
            self.assertIsNone(sin_fechas.fecha_inicio)
            self.assertIsNone(sin_fechas.fecha_fin)
            self.assertFalse(sin_fechas.activo)

    def test_valida_nombres_duplicados_y_escala(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            primero = servicios.periodos.crear("2026")
            servicios.periodos.crear("2027")

            with self.assertRaises(Conflicto):
                servicios.periodos.actualizar(primero.id, nombre="2027")
            with self.assertRaises(DatosInvalidos):
                servicios.periodos.actualizar(primero.id, nombre="   ")
            with self.assertRaises(NoEncontrado):
                servicios.periodos.actualizar("inexistente", nombre="X")


class ExportacionServiceTest(BaseAnalisisTest):
    def test_genera_csv_excel_y_pdf(self) -> None:
        with self.abrir() as uow:
            exportacion = ExportacionService(crear_servicios(uow.repos))

            csv_estudiantes = exportacion.estudiantes_csv()
            self.assertTrue(csv_estudiantes.startswith(b"\xef\xbb\xbf"))
            texto = csv_estudiantes.decode("utf-8-sig")
            self.assertIn("Código;Nombre", texto)
            self.assertIn("EST-000001", texto)
            self.assertIn("Ana Pérez", texto)

            csv_calificaciones = exportacion.calificaciones_csv().decode("utf-8-sig")
            self.assertIn("Matemática", csv_calificaciones)
            self.assertIn("4.50", csv_calificaciones)

            for contenido in (
                exportacion.estudiantes_excel(),
                exportacion.calificaciones_excel(),
            ):
                self.assertTrue(contenido.startswith(b"PK"))
                self.assertGreater(len(contenido), 1000)

            for contenido in (
                exportacion.estudiantes_pdf(),
                exportacion.calificaciones_pdf(),
            ):
                self.assertTrue(contenido.startswith(b"%PDF"))
                self.assertGreater(len(contenido), 500)


if __name__ == "__main__":
    unittest.main()
