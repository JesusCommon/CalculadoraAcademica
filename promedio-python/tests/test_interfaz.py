"""Pruebas de humo de la interfaz Tkinter (sin interacción manual)."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

from app.historial import Historial
from app.interfaz import Aplicacion


class InterfazTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "historial.json"

        try:
            self.app = Aplicacion(historial=Historial(self.ruta))
            self.app.withdraw()
            self.app.update_idletasks()
        except tk.TclError as error:  # pragma: no cover - depende del entorno.
            self._temp.cleanup()
            self.skipTest(f"Tkinter no disponible en este entorno: {error}")

    def tearDown(self) -> None:
        app = getattr(self, "app", None)
        if app is not None:
            try:
                app.destroy()
            except tk.TclError:
                pass  # La prueba ya cerró la ventana.
        self._temp.cleanup()

    def _agregar_notas(self, *notas: str) -> None:
        for nota in notas:
            self.app.nota_var.set(nota)
            self.app._agregar_nota()

    def test_calcula_y_muestra_aprobado(self) -> None:
        self.app.nombre_var.set("Ana")
        self._agregar_notas("4.5", "3,0", "2.5")

        self.assertEqual(self.app.lbl_promedio.cget("text"), "3.33")
        self.assertIn("APROBADO", self.app.lbl_estado.cget("text"))
        self.assertEqual(self.app.lista_notas.size(), 3)

    def test_muestra_reprobado(self) -> None:
        self._agregar_notas("1.0", "2.0")
        self.assertIn("REPROBADO", self.app.lbl_estado.cget("text"))

    def test_rechaza_notas_invalidas(self) -> None:
        self._agregar_notas("5.5")
        self.assertEqual(len(self.app.notas), 0)
        self.assertIn("entre", self.app.estado_var.get())

        self._agregar_notas("abc")
        self.assertEqual(len(self.app.notas), 0)

    def test_elimina_nota_seleccionada(self) -> None:
        self._agregar_notas("4.0", "2.0")
        self.app.lista_notas.selection_set(0)
        self.app._eliminar_nota()

        self.assertEqual(self.app.notas, [2.0])
        self.assertEqual(self.app.lista_notas.size(), 1)
        self.assertEqual(self.app.lbl_promedio.cget("text"), "2.00")

    def test_guardar_recuperar_y_eliminar_del_historial(self) -> None:
        self.app.nombre_var.set("Ana")
        self._agregar_notas("4.0", "5.0")
        self.app._guardar_estudiante()

        self.assertTrue(self.ruta.exists())
        self.assertEqual(len(self.app.historial), 1)
        self.assertEqual(len(self.app.arbol.get_children()), 1)
        self.assertEqual(self.app.nombre_var.get(), "")

        # Recuperar el estudiante desde el historial.
        self.app.arbol.selection_set("0")
        self.app._cargar_seleccionado()
        self.assertEqual(self.app.nombre_var.get(), "Ana")
        self.assertEqual(self.app.notas, [4.0, 5.0])
        self.assertEqual(self.app.boton_guardar.cget("text"), "Actualizar estudiante")

        # Actualizar el registro existente (no debe duplicarlo).
        self.app.notas = [2.0]
        self.app._actualizar_notas()
        self.app._guardar_estudiante()
        self.assertEqual(len(self.app.historial), 1)
        self.assertEqual(self.app.historial[0].promedio, 2.0)

        # Eliminar el registro con confirmación simulada.
        self.app.arbol.selection_set("0")
        with mock.patch("app.interfaz.messagebox.askyesno", return_value=True):
            self.app._eliminar_del_historial()

        self.assertEqual(len(self.app.historial), 0)
        self.assertEqual(len(self.app.arbol.get_children()), 0)

    def test_persistencia_real_entre_ventanas(self) -> None:
        self.app.nombre_var.set("Luis")
        self._agregar_notas("3.0")
        self.app._guardar_estudiante()
        self.app.destroy()

        segunda = Aplicacion(historial=Historial(self.ruta))
        segunda.withdraw()
        try:
            self.assertEqual(len(segunda.historial), 1)
            self.assertEqual(segunda.arbol.item("0", "values")[0], "Luis")
        finally:
            segunda.destroy()


if __name__ == "__main__":
    unittest.main()
