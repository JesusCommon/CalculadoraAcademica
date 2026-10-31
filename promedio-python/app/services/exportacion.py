"""Exportaciones CSV, Excel y PDF generadas desde los servicios compartidos."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Iterable, Sequence

from app.services.fabrica import Servicios


def _formato(valor: float | None) -> str:
    return "" if valor is None else f"{valor:.2f}"


class ExportacionService:
    """Construye archivos descargables sin acceder directamente a SQLite."""

    def __init__(self, servicios: Servicios) -> None:
        self.servicios = servicios

    # ------------------------------------------------------------------
    # Datos tabulares
    # ------------------------------------------------------------------
    def filas_estudiantes(self) -> tuple[list[str], list[list[object]]]:
        resumen = self.servicios.analisis.resumen()
        encabezados = [
            "Código",
            "Nombre",
            "Correo",
            "Notas",
            "Promedio",
            "Estado",
        ]
        filas = [
            [
                fila.estudiante.codigo,
                fila.estudiante.nombre,
                fila.estudiante.correo or "",
                fila.notas,
                _formato(fila.promedio),
                fila.estado,
            ]
            for fila in resumen.estudiantes
        ]
        return encabezados, filas

    def filas_calificaciones(self) -> tuple[list[str], list[list[object]]]:
        detalles = self.servicios.calificaciones.listar_todas()
        encabezados = [
            "Código estudiante",
            "Estudiante",
            "Código materia",
            "Materia",
            "Periodo",
            "Nota",
            "Fecha",
            "Descripción",
        ]
        filas = [
            [
                detalle.estudiante_codigo,
                detalle.estudiante_nombre,
                detalle.materia_codigo,
                detalle.materia_nombre,
                detalle.periodo_nombre,
                _formato(detalle.nota),
                detalle.fecha,
                detalle.descripcion or "",
            ]
            for detalle in detalles
        ]
        return encabezados, filas

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------
    def estudiantes_csv(self) -> bytes:
        return self._csv(*self.filas_estudiantes())

    def calificaciones_csv(self) -> bytes:
        return self._csv(*self.filas_calificaciones())

    @staticmethod
    def _csv(encabezados: Sequence[str], filas: Iterable[Sequence[object]]) -> bytes:
        buffer = io.StringIO(newline="")
        escritor = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
        escritor.writerow(encabezados)
        for fila in filas:
            escritor.writerow(fila)
        # BOM para que Excel reconozca UTF-8 y los acentos.
        return buffer.getvalue().encode("utf-8-sig")

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------
    def estudiantes_excel(self) -> bytes:
        return self._excel(
            "Estudiantes", *self.filas_estudiantes(), titulo="Estudiantes"
        )

    def calificaciones_excel(self) -> bytes:
        return self._excel(
            "Calificaciones", *self.filas_calificaciones(), titulo="Calificaciones"
        )

    @staticmethod
    def _excel(
        hoja: str,
        encabezados: Sequence[str],
        filas: Iterable[Sequence[object]],
        *,
        titulo: str,
    ) -> bytes:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        filas = list(filas)
        libro = Workbook()
        pagina = libro.active
        pagina.title = hoja

        azul = "0B2545"
        dorado = "C9A227"
        claro = "F4F6F8"

        pagina.append(list(encabezados))
        for celda in pagina[1]:
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor=azul)
            celda.alignment = Alignment(horizontal="center", vertical="center")

        for indice, fila in enumerate(filas, start=2):
            pagina.append(list(fila))
            if indice % 2 == 0:
                for celda in pagina[indice]:
                    celda.fill = PatternFill("solid", fgColor=claro)

        for indice, encabezado in enumerate(encabezados, start=1):
            ancho = max(
                [len(str(encabezado))]
                + [len(str(fila[indice - 1])) for fila in filas]
            )
            pagina.column_dimensions[get_column_letter(indice)].width = min(
                max(ancho + 3, 12), 42
            )

        pagina.freeze_panes = "A2"
        pagina.auto_filter.ref = pagina.dimensions
        pagina.sheet_view.showGridLines = False

        # Fila decorativa con el acento institucional.
        pagina.sheet_properties.pageSetUpPr.fitToPage = True
        pagina.oddFooter.center.text = f"{titulo} · Calculadora Académica 3.0"
        pagina.oddFooter.center.color = dorado

        buffer = io.BytesIO()
        libro.save(buffer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def estudiantes_pdf(self) -> bytes:
        return self._pdf(
            "Estudiantes",
            *self.filas_estudiantes(),
            apaisado=False,
            resumen=self._resumen_pdf(),
        )

    def calificaciones_pdf(self) -> bytes:
        return self._pdf(
            "Calificaciones",
            *self.filas_calificaciones(),
            apaisado=True,
        )

    def _resumen_pdf(self) -> list[str]:
        resumen = self.servicios.analisis.resumen()
        promedio = _formato(resumen.promedio_general) or "sin notas"
        return [
            f"Estudiantes: {resumen.total_estudiantes}",
            f"Materias: {resumen.total_materias}",
            f"Calificaciones: {resumen.total_calificaciones}",
            f"Promedio general: {promedio}",
            f"Aprobados: {resumen.aprobados} · Reprobados: {resumen.reprobados}",
        ]

    @staticmethod
    def _pdf(
        titulo: str,
        encabezados: Sequence[str],
        filas: Iterable[Sequence[object]],
        *,
        apaisado: bool,
        resumen: Sequence[str] | None = None,
    ) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
        from xml.sax.saxutils import escape

        filas = list(filas)
        buffer = io.BytesIO()
        tamano = landscape(A4) if apaisado else A4
        documento = SimpleDocTemplate(
            buffer,
            pagesize=tamano,
            leftMargin=1.6 * cm,
            rightMargin=1.6 * cm,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            title=f"{titulo} · Calculadora Académica 3.0",
            author="Calculadora Académica 3.0",
        )

        estilos = getSampleStyleSheet()
        azul = colors.HexColor("#0B2545")
        dorado = colors.HexColor("#C9A227")
        gris = colors.HexColor("#5B6770")

        estilo_titulo = ParagraphStyle(
            "TituloInstitucional",
            parent=estilos["Title"],
            textColor=azul,
            fontSize=20,
            spaceAfter=4,
        )
        estilo_subtitulo = ParagraphStyle(
            "Subtitulo",
            parent=estilos["Normal"],
            textColor=gris,
            fontSize=9,
            spaceAfter=14,
        )
        estilo_celda = ParagraphStyle(
            "Celda", parent=estilos["Normal"], fontSize=8, leading=10
        )

        elementos: list[object] = [
            Paragraph(f"Calculadora Académica 3.0 · {titulo}", estilo_titulo),
            Paragraph(
                "Reporte generado el "
                + datetime.now().strftime("%d/%m/%Y %H:%M")
                + " · Datos locales SQLite",
                estilo_subtitulo,
            ),
        ]

        if resumen:
            for linea in resumen:
                elementos.append(Paragraph(linea, estilo_celda))
            elementos.append(Spacer(1, 10))

        datos = [list(encabezados)] + [
            [Paragraph(escape(str(valor)), estilo_celda) for valor in fila]
            for fila in filas
        ]
        tabla = Table(datos, repeatRows=1, hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), azul),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDE3E9")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F8")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, dorado),
                ]
            )
        )
        elementos.append(tabla)
        documento.build(elementos)
        return buffer.getvalue()
