"""Pruebas de la lógica de negocio (sin interfaz gráfica)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.estudiante import Estudiante
from app.historial import ErrorHistorial, Historial
from app.promedio import (
    NOTA_APROBACION,
    calcular_promedio,
    determinar_estado,
    validar_nota,
)


class ValidacionNotasTest(unittest.TestCase):
    def test_acepta_notas_en_el_rango(self) -> None:
        for valor in (0, 5, 3.5, "4.2", 2):
            self.assertIsInstance(validar_nota(float(valor)), float)

    def test_rechaza_notas_fuera_del_rango(self) -> None:
        for valor in (-0.1, 5.01, 100, -3):
            with self.assertRaises(ValueError):
                validar_nota(valor)

    def test_rechaza_valores_no_numericos_o_no_finitos(self) -> None:
        for valor in ("3.5", None, True, float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                validar_nota(valor)

    def test_promedio_y_estado(self) -> None:
        self.assertAlmostEqual(calcular_promedio([3.0, 4.0, 2.0]), 3.0)
        self.assertEqual(determinar_estado(NOTA_APROBACION), "APROBADO")
        self.assertEqual(determinar_estado(2.99), "REPROBADO")
        with self.assertRaises(ValueError):
            calcular_promedio([])


class EstudianteTest(unittest.TestCase):
    def test_valida_nombre_y_notas(self) -> None:
        with self.assertRaises(ValueError):
            Estudiante(nombre="   ")
        with self.assertRaises(ValueError):
            Estudiante(nombre="Ana", notas=[6])

    def test_gestiona_notas_y_estado(self) -> None:
        estudiante = Estudiante(nombre="  Ana Pérez  ", notas=[4.0])
        self.assertEqual(estudiante.nombre, "Ana Pérez")
        self.assertEqual(estudiante.estado, "APROBADO")

        estudiante.agregar_nota(2.0)
        self.assertAlmostEqual(estudiante.promedio, 3.0)

        self.assertEqual(estudiante.eliminar_nota(1), 2.0)
        with self.assertRaises(IndexError):
            estudiante.eliminar_nota(5)

        vacio = Estudiante(nombre="Luis")
        self.assertIsNone(vacio.promedio)
        self.assertEqual(vacio.estado, "SIN NOTAS")
        self.assertFalse(vacio.aprobado)

    def test_ida_y_vuelta_a_diccionario(self) -> None:
        original = Estudiante(nombre="Ana", notas=[4.5, 3.0])
        recuperado = Estudiante.desde_dict(original.a_dict())
        self.assertEqual(recuperado.nombre, original.nombre)
        self.assertEqual(recuperado.notas, original.notas)
        with self.assertRaises(ValueError):
            Estudiante.desde_dict({"nombre": 123, "notas": []})


class HistorialTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "datos" / "historial.json"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_archivo_inexistente_deja_historial_vacio(self) -> None:
        historial = Historial(self.ruta)
        historial.cargar()
        self.assertEqual(len(historial), 0)

    def test_guardar_y_recuperar(self) -> None:
        historial = Historial(self.ruta)
        historial.agregar(Estudiante("Ana", [4.5, 3.0]))
        historial.agregar(Estudiante("Luis", [1.0]))
        historial.guardar()

        self.assertTrue(self.ruta.exists())
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertEqual(datos["estudiantes"][0]["nombre"], "Ana")

        recuperado = Historial(self.ruta)
        recuperado.cargar()
        self.assertEqual(len(recuperado), 2)
        self.assertEqual(recuperado[0].nombre, "Ana")
        self.assertEqual(recuperado[1].estado, "REPROBADO")
        self.assertAlmostEqual(recuperado[0].promedio, 3.75)

    def test_eliminar_y_reemplazar(self) -> None:
        historial = Historial(self.ruta)
        historial.agregar(Estudiante("Ana", [4.0]))
        historial.agregar(Estudiante("Luis", [2.0]))

        historial.reemplazar(1, Estudiante("Luis", [5.0]))
        self.assertEqual(historial[1].promedio, 5.0)

        eliminado = historial.eliminar(0)
        self.assertEqual(eliminado.nombre, "Ana")
        self.assertEqual(len(historial), 1)
        with self.assertRaises(IndexError):
            historial.eliminar(9)

    def test_json_corrupto_se_respalda(self) -> None:
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text("{ esto no es json", encoding="utf-8")

        historial = Historial(self.ruta)
        with self.assertRaises(ErrorHistorial):
            historial.cargar()

        respaldo = self.ruta.with_suffix(".json.corrupto")
        self.assertTrue(respaldo.exists())
        self.assertEqual(len(historial), 0)

    def test_omite_registros_invalidos_sin_perder_los_validos(self) -> None:
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text(
            json.dumps(
                {
                    "version": 1,
                    "estudiantes": [
                        {"nombre": "Ana", "notas": [4.0]},
                        {"nombre": "", "notas": []},
                        {"nombre": "Luis", "notas": [9.0]},
                    ],
                }
            ),
            encoding="utf-8",
        )

        historial = Historial(self.ruta)
        with self.assertRaises(ErrorHistorial):
            historial.cargar()

        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].nombre, "Ana")


if __name__ == "__main__":
    unittest.main()
