"""Pruebas de la aplicación web local con base SQLite temporal."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.database.unidad import UnidadDeTrabajo
from app.services.fabrica import crear_servicios
from app.web.servidor import crear_app


class WebBaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._temp.name) / "web.db"
        with UnidadDeTrabajo(self.ruta) as uow:
            servicios = crear_servicios(uow.repos)
            self.ana = servicios.estudiantes.crear("Ana Pérez", "ana@example.com")
            self.luis = servicios.estudiantes.crear("Luis Torres")
            self.matematica = servicios.materias.crear("MAT-101", "Matemática", 4)
            self.fisica = servicios.materias.crear("FIS-101", "Física", 3)
            self.periodo = servicios.periodos.listar()[0]
            servicios.calificaciones.registrar(
                self.ana.id,
                self.matematica.id,
                self.periodo.id,
                4.5,
                descripcion="Parcial de matemática",
            )
            servicios.calificaciones.registrar(
                self.ana.id, self.fisica.id, self.periodo.id, 3.5
            )
            servicios.calificaciones.registrar(
                self.luis.id, self.matematica.id, self.periodo.id, 2.0
            )

        self.app = crear_app(self.ruta)
        self.cliente = TestClient(self.app)

    def tearDown(self) -> None:
        self.cliente.close()
        self._temp.cleanup()

    def abrir(self) -> UnidadDeTrabajo:
        return UnidadDeTrabajo(self.ruta)


class PaginasWebTest(WebBaseTest):
    def test_todas_las_secciones_responden(self) -> None:
        paginas = {
            "/": "Dashboard académico",
            "/estudiantes": "Gestión de estudiantes",
            "/estudiantes/nuevo": "Nuevo estudiante",
            "/materias": "Gestión de materias",
            "/materias/nuevo": "Nueva materia",
            "/calificaciones": "Registrar nueva calificación",
            "/historial": "Historial académico",
            "/estadisticas": "Estadísticas académicas",
            "/configuracion": "Escala global",
            "/periodos/nuevo": "Nuevo periodo",
        }
        for ruta, texto in paginas.items():
            with self.subTest(ruta=ruta):
                respuesta = self.cliente.get(ruta)
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn(texto, respuesta.text)

    def test_dashboard_muestra_indicadores_y_ranking(self) -> None:
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Ana Pérez", respuesta.text)
        self.assertIn("Promedio por materia", respuesta.text)
        self.assertIn("Reportes y exportaciones", respuesta.text)
        self.assertIn("/exportar/estudiantes.xlsx", respuesta.text)

    def test_historial_muestra_detalle_y_resumenes(self) -> None:
        respuesta = self.cliente.get(f"/historial?estudiante_id={self.ana.id}")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Ana Pérez", respuesta.text)
        self.assertIn("Parcial de matemática", respuesta.text)
        self.assertIn("Resumen por periodo", respuesta.text)
        self.assertIn("Resumen por materia", respuesta.text)

    def test_formularios_de_edicion_cargan_los_datos(self) -> None:
        respuesta = self.cliente.get(f"/estudiantes/{self.ana.id}/editar")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Ana Pérez", respuesta.text)
        self.assertIn("ana@example.com", respuesta.text)

        respuesta = self.cliente.get(f"/materias/{self.matematica.id}/editar")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("MAT-101", respuesta.text)
        self.assertIn("Matemática", respuesta.text)

        respuesta = self.cliente.get(f"/periodos/{self.periodo.id}/editar")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Periodo general", respuesta.text)

        self.assertEqual(
            self.cliente.get(
                "/estudiantes/inexistente/editar", follow_redirects=False
            ).status_code,
            303,
        )
        self.assertEqual(
            self.cliente.get(
                "/materias/inexistente/editar", follow_redirects=False
            ).status_code,
            303,
        )
        self.assertEqual(
            self.cliente.get(
                "/periodos/inexistente/editar", follow_redirects=False
            ).status_code,
            303,
        )

    def test_filtros_y_parametros_invalidos_no_fallan(self) -> None:
        self.assertEqual(self.cliente.get("/estudiantes?busqueda=zzz").status_code, 200)
        self.assertIn("No se encontraron estudiantes", self.cliente.get("/estudiantes?busqueda=zzz").text)
        self.assertEqual(self.cliente.get("/calificaciones?estudiante_id=xxx&periodo_id=yyy").status_code, 200)
        self.assertEqual(self.cliente.get("/historial?estudiante_id=xxx").status_code, 200)
        self.assertEqual(self.cliente.get("/estadisticas?periodo_id=xxx").status_code, 200)
        self.assertEqual(self.cliente.get("/ruta-inexistente").status_code, 404)

    def test_salud_y_archivos_estaticos(self) -> None:
        salud = self.cliente.get("/salud")
        self.assertEqual(salud.status_code, 200)
        datos = salud.json()
        self.assertEqual(datos["estado"], "ok")
        self.assertEqual(datos["estudiantes"], 2)
        self.assertEqual(datos["materias"], 3)
        self.assertTrue(datos["base"].endswith("web.db"))

        self.assertEqual(self.cliente.get("/static/css/estilos.css").status_code, 200)
        self.assertEqual(self.cliente.get("/static/js/app.js").status_code, 200)


class EstudiantesWebTest(WebBaseTest):
    def test_alta_edicion_y_baja_logica(self) -> None:
        respuesta = self.cliente.post(
            "/estudiantes/guardar",
            data={"nombre": "Carla Ruiz", "correo": "carla@example.com"},
            follow_redirects=False,
        )
        self.assertEqual(respuesta.status_code, 303)

        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            carla = [e for e in servicios.estudiantes.listar() if e.nombre == "Carla Ruiz"][0]
            self.assertEqual(carla.codigo, "EST-000003")

        respuesta = self.cliente.post(
            "/estudiantes/guardar",
            data={
                "nombre": "Carla Ruiz Díaz",
                "correo": "carla@example.com",
                "identificador": carla.id,
            },
            follow_redirects=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Estudiante actualizado correctamente.", respuesta.text)
        self.assertIn("Carla Ruiz Díaz", respuesta.text)

        respuesta = self.cliente.post(
            f"/estudiantes/{carla.id}/eliminar", follow_redirects=True
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("notas se conservan", respuesta.text)
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            self.assertEqual(servicios.estudiantes.contar(), 2)
            self.assertEqual(len(servicios.estudiantes.listar(incluir_eliminados=True)), 3)

    def test_nombre_vacio_muestra_error(self) -> None:
        respuesta = self.cliente.post(
            "/estudiantes/guardar",
            data={"nombre": "   ", "correo": ""},
            follow_redirects=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("no puede estar vacío", respuesta.text)
        with self.abrir() as uow:
            self.assertEqual(crear_servicios(uow.repos).estudiantes.contar(), 2)


class MateriasWebTest(WebBaseTest):
    def test_alta_edicion_duplicado_y_baja(self) -> None:
        respuesta = self.cliente.post(
            "/materias/guardar",
            data={"codigo": "qui-101", "nombre": "Química", "creditos": "3,5"},
            follow_redirects=False,
        )
        self.assertEqual(respuesta.status_code, 303)
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            quimica = [m for m in servicios.materias.listar() if m.codigo == "QUI-101"][0]
            self.assertEqual(quimica.creditos, 3.5)

        respuesta = self.cliente.post(
            "/materias/guardar",
            data={"codigo": "QUI-101", "nombre": "Otra", "creditos": "1"},
            follow_redirects=True,
        )
        self.assertIn("Ya existe una materia", respuesta.text)

        respuesta = self.cliente.post(
            "/materias/guardar",
            data={
                "codigo": "QUI-102",
                "nombre": "Química II",
                "creditos": "4",
                "identificador": quimica.id,
            },
            follow_redirects=True,
        )
        self.assertIn("Materia actualizada correctamente.", respuesta.text)

        respuesta = self.cliente.post(
            f"/materias/{quimica.id}/eliminar", follow_redirects=True
        )
        self.assertIn("notas se conservan", respuesta.text)
        with self.abrir() as uow:
            self.assertEqual(len(crear_servicios(uow.repos).materias.listar()), 3)


class CalificacionesWebTest(WebBaseTest):
    def test_registrar_validar_y_anular(self) -> None:
        respuesta = self.cliente.post(
            "/calificaciones/nueva",
            data={
                "estudiante_id": self.luis.id,
                "materia_id": self.fisica.id,
                "periodo_id": self.periodo.id,
                "nota": "4,25",
                "fecha": "2026-10-30",
                "descripcion": " Registro   web ",
            },
            follow_redirects=True,
        )
        self.assertIn("Calificación registrada correctamente.", respuesta.text)
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            notas = servicios.calificaciones.listar_todas(estudiante_id=self.luis.id)
            self.assertEqual(len(notas), 2)
            nueva = [n for n in notas if n.materia_id == self.fisica.id][0]
            self.assertEqual(nueva.nota, 4.25)
            self.assertEqual(nueva.descripcion, "Registro web")

        respuesta = self.cliente.post(
            "/calificaciones/nueva",
            data={
                "estudiante_id": self.luis.id,
                "materia_id": self.fisica.id,
                "periodo_id": self.periodo.id,
                "nota": "9",
            },
            follow_redirects=True,
        )
        self.assertIn("La nota debe estar entre", respuesta.text)
        with self.abrir() as uow:
            self.assertEqual(
                len(crear_servicios(uow.repos).calificaciones.listar_todas()), 4
            )

        respuesta = self.cliente.post(
            f"/calificaciones/{nueva.id}/anular", follow_redirects=True
        )
        self.assertIn("Calificación anulada", respuesta.text)
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            self.assertEqual(len(servicios.calificaciones.listar_todas()), 3)
            self.assertEqual(
                len(servicios.calificaciones.listar_todas(incluir_anuladas=True)), 4
            )

    def test_fecha_invalida_muestra_error(self) -> None:
        respuesta = self.cliente.post(
            "/calificaciones/nueva",
            data={
                "estudiante_id": self.luis.id,
                "materia_id": self.fisica.id,
                "periodo_id": self.periodo.id,
                "nota": "4",
                "fecha": "30/10/2026",
            },
            follow_redirects=True,
        )
        self.assertIn("time data", respuesta.text)


class ConfiguracionWebTest(WebBaseTest):
    def test_actualiza_escala_y_gestiona_periodos(self) -> None:
        respuesta = self.cliente.post(
            "/configuracion/escala",
            data={"minima": "0", "maxima": "100", "aprobacion": "60", "decimales": "1"},
            follow_redirects=True,
        )
        self.assertIn("Escala global actualizada", respuesta.text)
        with self.abrir() as uow:
            escala = crear_servicios(uow.repos).configuracion.obtener_escala()
            self.assertEqual(escala.maxima, 100.0)
            self.assertEqual(escala.aprobacion, 60.0)
            self.assertEqual(escala.decimales, 1)

        respuesta = self.cliente.post(
            "/periodos/guardar",
            data={
                "nombre": "2027",
                "fecha_inicio": "2027-01-10",
                "fecha_fin": "2027-06-30",
                "minima": "0",
                "maxima": "100",
                "aprobacion": "60",
                "activo": "1",
            },
            follow_redirects=True,
        )
        self.assertIn("Periodo creado", respuesta.text)
        with self.abrir() as uow:
            periodos = crear_servicios(uow.repos).periodos.listar()
            nuevo = [p for p in periodos if p.nombre == "2027"][0]
            self.assertEqual(nuevo.escala_max, 100.0)
            self.assertTrue(nuevo.activo)

        respuesta = self.cliente.post(
            "/periodos/guardar",
            data={
                "nombre": "2027-I",
                "fecha_inicio": "2027-01-10",
                "fecha_fin": "2027-07-15",
                "minima": "0",
                "maxima": "100",
                "aprobacion": "60",
                "activo": "1",
                "identificador": nuevo.id,
            },
            follow_redirects=True,
        )
        self.assertIn("Periodo actualizado correctamente.", respuesta.text)
        self.assertIn("2027-I", self.cliente.get("/configuracion").text)

    def test_escala_invalida_muestra_error(self) -> None:
        respuesta = self.cliente.post(
            "/configuracion/escala",
            data={"minima": "10", "maxima": "5", "aprobacion": "7", "decimales": "2"},
            follow_redirects=True,
        )
        self.assertIn("La nota mínima debe ser menor que la máxima", respuesta.text)


class ExportacionesWebTest(WebBaseTest):
    def test_descarga_csv_excel_y_pdf(self) -> None:
        prefijos = {"csv": b"\xef\xbb\xbf", "xlsx": b"PK", "pdf": b"%PDF"}
        for tipo in ("estudiantes", "calificaciones"):
            for formato, prefijo in prefijos.items():
                with self.subTest(tipo=tipo, formato=formato):
                    respuesta = self.cliente.get(f"/exportar/{tipo}.{formato}")
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertTrue(respuesta.content.startswith(prefijo))
                    self.assertIn(
                        "attachment",
                        respuesta.headers.get("content-disposition", ""),
                    )

    def test_exportacion_no_disponible_devuelve_404(self) -> None:
        self.assertEqual(self.cliente.get("/exportar/estudiantes.xml").status_code, 404)
        self.assertEqual(self.cliente.get("/exportar/docentes.csv").status_code, 404)


class BaseCompartidaTest(WebBaseTest):
    def test_escritura_por_servicios_es_visible_en_la_web(self) -> None:
        with self.abrir() as uow:
            servicios = crear_servicios(uow.repos)
            nuevo = servicios.estudiantes.crear("Compartido Desde Escritorio")
            servicios.calificaciones.registrar(
                nuevo.id, self.matematica.id, self.periodo.id, 4.1
            )

        respuesta = self.cliente.get("/estudiantes")
        self.assertIn("Compartido Desde Escritorio", respuesta.text)
        self.assertIn("Compartido Desde Escritorio", self.cliente.get("/").text)

    def test_escritura_web_es_visible_para_los_servicios(self) -> None:
        self.cliente.post(
            "/estudiantes/guardar",
            data={"nombre": "Compartido Desde Web"},
            follow_redirects=False,
        )
        with self.abrir() as uow:
            nombres = [e.nombre for e in crear_servicios(uow.repos).estudiantes.listar()]
        self.assertIn("Compartido Desde Web", nombres)


if __name__ == "__main__":
    unittest.main()
