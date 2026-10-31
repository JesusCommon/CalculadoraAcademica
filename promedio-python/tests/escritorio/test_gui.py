"""Pruebas de humo de la interfaz Tkinter 3.0."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

import app.database.conexion as conexion
from app.database.unidad import UnidadDeTrabajo
from app.escritorio.aplicacion import SECCIONES, Aplicacion
from app.escritorio.sesion import sesion
from app.services.fabrica import crear_servicios


class Interfaz3Test(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "gui.db"
        self._ruta_original = conexion.RUTA_BD_PREDETERMINADA
        conexion.RUTA_BD_PREDETERMINADA = self.ruta
        self.addCleanup(self._restaurar)

        with UnidadDeTrabajo(self.ruta) as uow:
            servicios = crear_servicios(uow.repos)
            self.ana = servicios.estudiantes.crear("Ana Pérez")
            self.materia = servicios.materias.crear("MAT-101", "Matemática", 4)
            self.periodo = servicios.periodos.listar()[0]
            servicios.calificaciones.registrar(
                self.ana.id, self.materia.id, self.periodo.id, 4.5
            )

    def _restaurar(self) -> None:
        conexion.RUTA_BD_PREDETERMINADA = self._ruta_original
        self._temp.cleanup()

    def _crear_aplicacion(self) -> Aplicacion:
        try:
            aplicacion = Aplicacion()
        except tk.TclError as error:
            self.skipTest(f"Tkinter no disponible: {error}")
        self.addCleanup(aplicacion.destroy)
        aplicacion.update()
        return aplicacion

    def test_navega_por_todas_las_secciones(self) -> None:
        aplicacion = self._crear_aplicacion()
        for clave, _icono, _texto, _vista in SECCIONES:
            with self.subTest(seccion=clave):
                aplicacion.mostrar(clave)
                aplicacion.update()
                self.assertEqual(aplicacion._seccion_actual, clave)
                self.assertTrue(aplicacion.titulo_seccion.cget("text"))

        aplicacion.refrescar_actual()
        aplicacion.update()

    def test_dashboard_y_tablas_reflejan_la_base(self) -> None:
        aplicacion = self._crear_aplicacion()
        dashboard = aplicacion._vistas["dashboard"]
        self.assertEqual(dashboard.tarjetas["estudiantes"].valor.cget("text"), "1")
        self.assertEqual(dashboard.tarjetas["materias"].valor.cget("text"), "2")
        self.assertEqual(dashboard.tarjetas["calificaciones"].valor.cget("text"), "1")
        self.assertEqual(dashboard.tarjetas["promedio"].valor.cget("text"), "4.50")

        aplicacion.mostrar("estudiantes")
        aplicacion.update()
        vista = aplicacion._vistas["estudiantes"]
        nombres = [
            vista.tabla.tabla.item(iid, "values")[1]
            for iid in vista.tabla.tabla.get_children()
        ]
        self.assertIn("Ana Pérez", nombres)

    def test_una_escritura_de_sesion_se_refleja_al_refrescar(self) -> None:
        aplicacion = self._crear_aplicacion()
        aplicacion.mostrar("estudiantes")
        aplicacion.update()

        with sesion() as servicios:
            servicios.estudiantes.crear("Creado Desde Tkinter")

        aplicacion.refrescar_actual()
        aplicacion.update()
        vista = aplicacion._vistas["estudiantes"]
        nombres = [
            vista.tabla.tabla.item(iid, "values")[1]
            for iid in vista.tabla.tabla.get_children()
        ]
        self.assertIn("Creado Desde Tkinter", nombres)

        with UnidadDeTrabajo(self.ruta) as uow:
            nombres_bd = [
                estudiante.nombre
                for estudiante in crear_servicios(uow.repos).estudiantes.listar()
            ]
        self.assertIn("Creado Desde Tkinter", nombres_bd)

    def test_configuracion_muestra_la_escala(self) -> None:
        aplicacion = self._crear_aplicacion()
        aplicacion.mostrar("configuracion")
        aplicacion.update()
        vista = aplicacion._vistas["configuracion"]
        self.assertEqual(vista.minima.get(), "0")
        self.assertEqual(vista.maxima.get(), "5")
        self.assertEqual(vista.aprobacion.get(), "3")
        self.assertEqual(vista.decimales.get(), "2")
        self.assertEqual(vista.tabla.total(), 1)


if __name__ == "__main__":
    unittest.main()
