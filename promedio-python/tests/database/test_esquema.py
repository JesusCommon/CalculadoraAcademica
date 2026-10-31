"""Pruebas del esquema SQLite."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database.conexion import crear_conexion
from app.database.esquema import aplicar_esquema


class EsquemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "academico.db"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_crea_tablas_y_aplica_migracion_una_sola_vez(self) -> None:
        conexion = crear_conexion(self.ruta)
        try:
            self.assertEqual(aplicar_esquema(conexion), [1])
            self.assertEqual(aplicar_esquema(conexion), [])

            tablas = {
                fila["name"]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            esperadas = {
                "esquema_version",
                "configuracion",
                "roles",
                "usuarios",
                "estudiantes",
                "materias",
                "periodos",
                "inscripciones",
                "calificaciones",
                "migraciones",
                "contadores",
            }
            self.assertTrue(esperadas.issubset(tablas))
            self.assertEqual(conexion.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(
                conexion.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
        finally:
            conexion.close()

    def test_siembra_configuracion_y_contexto_general(self) -> None:
        conexion = crear_conexion(self.ruta)
        try:
            aplicar_esquema(conexion)
            config = dict(
                conexion.execute("SELECT clave, valor FROM configuracion").fetchall()
            )
            self.assertEqual(config["escala_min"], "0.0")
            self.assertEqual(config["escala_max"], "5.0")
            self.assertEqual(config["aprobacion_min"], "3.0")

            materia = conexion.execute(
                "SELECT codigo, nombre FROM materias WHERE codigo = 'GEN'"
            ).fetchone()
            self.assertIsNotNone(materia)
            self.assertEqual(materia["nombre"], "Materia general")

            periodo = conexion.execute(
                "SELECT nombre, escala_min, escala_max, aprobacion_min FROM periodos"
            ).fetchone()
            self.assertEqual(periodo["nombre"], "Periodo general")
            self.assertEqual(periodo["escala_max"], 5.0)
        finally:
            conexion.close()


if __name__ == "__main__":
    unittest.main()
