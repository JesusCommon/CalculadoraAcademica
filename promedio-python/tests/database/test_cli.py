"""Pruebas del comando de migración y del punto de entrada."""

from __future__ import annotations

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from app.database.migrar_json import main
from main import main as entrada_principal

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "historial_v2.json"


class BaseCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.dir = Path(self._temp.name)
        self.json = self.dir / "historial.json"
        shutil.copy2(FIXTURE, self.json)
        self.db = self.dir / "academico.db"
        self.backups = self.dir / "backups"
        self.argumentos = [
            "--json",
            str(self.json),
            "--db",
            str(self.db),
            "--backups",
            str(self.backups),
        ]

    def tearDown(self) -> None:
        self._temp.cleanup()


class CliMigracionTest(BaseCliTest):
    def _ejecutar(self, *args: str) -> tuple[int, str, str]:
        salida = io.StringIO()
        errores = io.StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            codigo = main([*args, *self.argumentos])
        return codigo, salida.getvalue(), errores.getvalue()

    def test_dry_run_no_escribe(self) -> None:
        codigo, salida, errores = self._ejecutar("--dry-run")
        self.assertEqual(codigo, 0, errores)
        self.assertIn("SIMULACIÓN", salida)
        self.assertIn("2 estudiantes válidos", salida)
        self.assertIn("9 notas", salida)
        self.assertFalse(self.db.exists())
        self.assertFalse(self.backups.exists())

    def test_aplicar_crea_la_base_y_el_reporte(self) -> None:
        codigo, salida, errores = self._ejecutar("--aplicar")
        self.assertEqual(codigo, 0, errores)
        self.assertIn("APLICACIÓN", salida)
        self.assertTrue(self.db.exists())
        self.assertEqual(len(list(self.backups.glob("migracion-*.json"))), 1)

    def test_error_controlado_si_el_json_no_existe(self) -> None:
        self.json.unlink()
        codigo, _, errores = self._ejecutar("--dry-run")
        self.assertEqual(codigo, 1)
        self.assertIn("No existe el archivo JSON", errores)


class EntradaPrincipalTest(BaseCliTest):
    def test_migrar_json_delega_en_la_cli(self) -> None:
        salida = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            ["main.py", "--migrar-json", "--dry-run", *self.argumentos],
        ):
            with redirect_stdout(salida):
                with self.assertRaises(SystemExit) as contexto:
                    entrada_principal()

        self.assertEqual(contexto.exception.code, 0)
        self.assertIn("SIMULACIÓN", salida.getvalue())
        self.assertFalse(self.db.exists())


if __name__ == "__main__":
    unittest.main()
