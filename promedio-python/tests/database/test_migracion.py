"""Pruebas de la migración JSON → SQLite."""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app.core.errores import ErrorMigracion
from app.database.json_legacy import calcular_sha256
from app.services.migracion import MigracionService

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "historial_v2.json"


class MigracionServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.dir = Path(self._temp.name)
        self.json = self.dir / "historial.json"
        shutil.copy2(FIXTURE, self.json)
        self.db = self.dir / "academico.db"
        self.backups = self.dir / "backups"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _servicio(self) -> MigracionService:
        return MigracionService(self.json, self.db, self.backups)

    def _conexion(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db)

    def test_simulacion_no_escribe_ni_modifica_el_json(self) -> None:
        antes = calcular_sha256(self.json)
        resultado = self._servicio().simular()

        self.assertTrue(resultado.simulado)
        self.assertTrue(resultado.correcto)
        self.assertEqual(resultado.total_leidos, 2)
        self.assertEqual(resultado.validos, 2)
        self.assertEqual(resultado.invalidos, 0)
        self.assertEqual(resultado.duplicados, 0)
        self.assertEqual(resultado.estudiantes[0]["nombre"], "Manuela")
        self.assertEqual(resultado.estudiantes[0]["promedio"], 3.6875)
        self.assertEqual(resultado.estudiantes[1]["promedio"], 2.9)
        self.assertEqual(sum(e["cantidad_notas"] for e in resultado.estudiantes), 9)
        self.assertFalse(self.db.exists())
        self.assertFalse(self.backups.exists())
        self.assertEqual(calcular_sha256(self.json), antes)

    def test_aplicacion_importa_y_verifica_los_dos_estudiantes(self) -> None:
        antes = calcular_sha256(self.json)
        resultado = self._servicio().aplicar()

        self.assertTrue(resultado.aplicada)
        self.assertTrue(resultado.correcto)
        self.assertEqual(resultado.importados, 2)
        self.assertEqual(resultado.calificaciones_importadas, 9)
        self.assertIsNotNone(resultado.respaldo_json)
        self.assertTrue(Path(resultado.respaldo_json).exists())
        self.assertEqual(calcular_sha256(Path(resultado.respaldo_json)), antes)
        self.assertEqual(calcular_sha256(self.json), antes)

        with closing(self._conexion()) as conexion:
            estudiantes = conexion.execute(
                "SELECT codigo, nombre, origen, huella_migracion FROM estudiantes ORDER BY codigo"
            ).fetchall()
            self.assertEqual([fila[1] for fila in estudiantes], ["Manuela", "Luisa"])
            self.assertEqual([fila[0] for fila in estudiantes], ["EST-000001", "EST-000002"])
            self.assertTrue(all(fila[2] == "json_migracion" for fila in estudiantes))

            notas = conexion.execute("SELECT COUNT(*) FROM calificaciones").fetchone()[0]
            self.assertEqual(notas, 9)

            promedios = dict(
                conexion.execute(
                    """
                    SELECT e.nombre, AVG(c.nota)
                      FROM estudiantes e
                      JOIN inscripciones i ON i.estudiante_id = e.id
                      JOIN calificaciones c ON c.inscripcion_id = i.id
                     GROUP BY e.id
                    """
                ).fetchall()
            )
            self.assertAlmostEqual(promedios["Manuela"], 3.6875)
            self.assertAlmostEqual(promedios["Luisa"], 2.9)
            self.assertEqual(
                conexion.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )

        # Reporte de la migración.
        reportes = list(self.backups.glob("migracion-*.json"))
        self.assertEqual(len(reportes), 1)
        reporte = json.loads(reportes[0].read_text(encoding="utf-8"))
        self.assertTrue(reporte["correcto"])
        self.assertEqual(reporte["importados"], 2)

    def test_segunda_ejecucion_es_idempotente(self) -> None:
        self._servicio().aplicar()
        resultado = self._servicio().aplicar()

        self.assertTrue(resultado.ya_existia)
        self.assertFalse(resultado.aplicada)
        self.assertEqual(resultado.importados, 0)
        self.assertEqual(resultado.calificaciones_importadas, 0)
        with closing(self._conexion()) as conexion:
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0], 2
            )
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM calificaciones").fetchone()[0], 9
            )

    def test_clasifica_invalidos_duplicados_y_posibles_duplicados(self) -> None:
        datos = {
            "version": 1,
            "estudiantes": [
                {"nombre": "Ana", "notas": [4.0, 4.0]},
                {"nombre": "Ana", "notas": [4.0, 4.0]},
                {"nombre": "Ana", "notas": [3.0]},
                {"nombre": "", "notas": [1.0]},
                {"nombre": "Luis", "notas": [6.0]},
                {"nombre": "Eva", "notas": []},
            ],
        }
        self.json.write_text(json.dumps(datos), encoding="utf-8")

        simulacion = self._servicio().simular()
        self.assertEqual(simulacion.total_leidos, 6)
        self.assertEqual(simulacion.validos, 3)
        self.assertEqual(simulacion.duplicados, 1)
        self.assertEqual(simulacion.invalidos, 2)
        self.assertEqual(len(simulacion.posibles_duplicados), 1)
        self.assertEqual(simulacion.estudiantes[-1]["estado"], "SIN NOTAS")

        resultado = self._servicio().aplicar()
        self.assertEqual(resultado.importados, 3)
        self.assertEqual(resultado.calificaciones_importadas, 3)

        with closing(self._conexion()) as conexion:
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0], 3
            )
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM calificaciones").fetchone()[0], 3
            )

    def test_json_corrupto_aborta_sin_escribir(self) -> None:
        self.json.write_text("{ esto no es json", encoding="utf-8")
        antes = calcular_sha256(self.json)

        with self.assertRaises(ErrorMigracion):
            self._servicio().simular()
        with self.assertRaises(ErrorMigracion):
            self._servicio().aplicar()

        self.assertFalse(self.db.exists())
        self.assertFalse(self.backups.exists())
        self.assertEqual(calcular_sha256(self.json), antes)


if __name__ == "__main__":
    unittest.main()
