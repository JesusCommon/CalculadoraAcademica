"""Pruebas de la escala y los cálculos del núcleo."""

from __future__ import annotations

import unittest

from app.core.escala import ESCALA_PREDETERMINADA, Escala
from app.core.promedio import calcular_promedio, determinar_estado, validar_nota


class EscalaTest(unittest.TestCase):
    def test_escala_predeterminada_conserva_la_regla_2_0(self) -> None:
        self.assertEqual(ESCALA_PREDETERMINADA.minima, 0.0)
        self.assertEqual(ESCALA_PREDETERMINADA.maxima, 5.0)
        self.assertEqual(ESCALA_PREDETERMINADA.aprobacion, 3.0)
        self.assertEqual(ESCALA_PREDETERMINADA.estado(3.0), "APROBADO")
        self.assertEqual(ESCALA_PREDETERMINADA.estado(2.99), "REPROBADO")

    def test_permite_una_escala_distinta(self) -> None:
        escala = Escala(minima=0, maxima=100, aprobacion=60, decimales=1)
        self.assertEqual(escala.validar(100), 100.0)
        self.assertEqual(escala.formatear(75.56), "75.6")
        self.assertEqual(escala.estado(60), "APROBADO")
        self.assertEqual(escala.estado(59.9), "REPROBADO")

    def test_rechaza_valores_invalidos(self) -> None:
        for valor in (-1, 101, "80", None, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Escala(minima=0, maxima=100, aprobacion=60).validar(valor)

    def test_rechaza_configuraciones_incoherentes(self) -> None:
        with self.assertRaises(ValueError):
            Escala(minima=5, maxima=0)
        with self.assertRaises(ValueError):
            Escala(minima=0, maxima=5, aprobacion=6)
        with self.assertRaises(ValueError):
            Escala(decimales=-1)
        with self.assertRaises(ValueError):
            Escala(decimales=True)

    def test_calculos_basicos(self) -> None:
        self.assertEqual(calcular_promedio([3.0, 4.0, 5.0]), 4.0)
        with self.assertRaises(ValueError):
            calcular_promedio([])
        self.assertEqual(determinar_estado(3.0), "APROBADO")
        self.assertEqual(
            determinar_estado(75, Escala(minima=0, maxima=100, aprobacion=80)),
            "REPROBADO",
        )
        self.assertEqual(validar_nota(4.5), 4.5)


if __name__ == "__main__":
    unittest.main()
