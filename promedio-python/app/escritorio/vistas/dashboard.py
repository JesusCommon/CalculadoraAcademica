"""Dashboard académico de la interfaz de escritorio."""

from __future__ import annotations

import tkinter as tk

from app.escritorio.estilos import (
    AZUL,
    BLANCO,
    FONDO,
    FUENTE,
    FUENTE_TITULO,
    GRIS_BORDE,
    GRIS_TEXTO,
)
from app.escritorio.sesion import sesion
from app.escritorio.vistas.base import VistaBase
from app.escritorio.widgets import (
    GraficoBarras,
    GraficoDonut,
    Tabla,
    Tarjeta,
    estilo_estado,
    etiqueta_estado,
    formatear_promedio,
)


class VistaDashboard(VistaBase):
    titulo = "Dashboard académico"
    subtitulo = "Visión general del rendimiento institucional"

    def construir(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        fila = tk.Frame(self, bg=FONDO)
        fila.grid(row=0, column=0, sticky="ew")
        for indice in range(4):
            fila.grid_columnconfigure(indice, weight=1)

        self.tarjetas: dict[str, Tarjeta] = {}
        definiciones = [
            ("estudiantes", "Estudiantes", "activos en el sistema"),
            ("materias", "Materias", "registradas"),
            ("calificaciones", "Calificaciones", "notas activas"),
            ("promedio", "Promedio general", "escala institucional"),
        ]
        for indice, (clave, titulo, pista) in enumerate(definiciones):
            tarjeta = Tarjeta(fila, titulo, "—", pista)
            tarjeta.grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=(0 if indice == 0 else 8, 0),
            )
            self.tarjetas[clave] = tarjeta

        zona = tk.Frame(self, bg=FONDO)
        zona.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        zona.grid_columnconfigure(0, weight=3)
        zona.grid_columnconfigure(1, weight=2)
        zona.grid_rowconfigure(0, weight=1)

        marco_barras, cuerpo_barras = self._panel(zona, "Promedio por materia")
        marco_barras.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.barras = GraficoBarras(cuerpo_barras, alto=210)
        self.barras.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        marco_dona, cuerpo_dona = self._panel(zona, "Distribución de estudiantes")
        marco_dona.grid(row=0, column=1, sticky="nsew")
        self.dona = GraficoDonut(cuerpo_dona, alto=210)
        self.dona.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        marco_tabla = tk.Frame(
            self,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        marco_tabla.grid(row=2, column=0, sticky="nsew", pady=(14, 0))

        cabecera = tk.Frame(marco_tabla, bg=BLANCO)
        cabecera.pack(fill="x", padx=12, pady=(10, 8))
        tk.Label(
            cabecera,
            text="Ranking de estudiantes",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
        ).pack(side="left")
        tk.Button(
            cabecera,
            text="Ver estudiantes  →",
            command=lambda: self.app.mostrar("estudiantes"),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            activebackground=BLANCO,
            activeforeground=AZUL,
            bd=0,
            font=(FUENTE, 9),
            cursor="hand2",
        ).pack(side="right")

        self.tabla = Tabla(
            marco_tabla,
            [
                ("codigo", "Código", 110, "w"),
                ("nombre", "Estudiante", 260, "w"),
                ("notas", "Notas", 70, "center"),
                ("promedio", "Promedio", 100, "center"),
                ("estado", "Estado", 120, "center"),
            ],
            altura=6,
        )
        self.tabla.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    @staticmethod
    def _panel(maestro: tk.Misc, titulo: str) -> tuple[tk.Frame, tk.Frame]:
        marco = tk.Frame(
            maestro,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        tk.Label(
            marco,
            text=titulo,
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 4))
        cuerpo = tk.Frame(marco, bg=BLANCO)
        cuerpo.pack(fill="both", expand=True)
        return marco, cuerpo

    def al_mostrar(self) -> None:
        with sesion(escritura=False) as servicios:
            resumen = servicios.analisis.resumen()

        promedio = formatear_promedio(resumen.promedio_general)
        self.tarjetas["estudiantes"].actualizar(
            str(resumen.total_estudiantes),
            f"{resumen.aprobados} aprobados · {resumen.reprobados} reprobados",
        )
        self.tarjetas["materias"].actualizar(
            str(resumen.total_materias),
            f"{resumen.total_periodos} periodos académicos",
        )
        self.tarjetas["calificaciones"].actualizar(
            str(resumen.total_calificaciones),
            f"{resumen.sin_notas} estudiantes sin notas",
        )
        self.tarjetas["promedio"].actualizar(
            promedio,
            "sobre la escala configurada",
        )

        self.barras.dibujar(resumen.por_materia)
        self.dona.dibujar(
            [
                ("Aprobados", resumen.aprobados, "#1E7F4F"),
                ("Reprobados", resumen.reprobados, "#B3261E"),
                ("Sin notas", resumen.sin_notas, "#C9A227"),
            ]
        )

        filas = sorted(
            resumen.estudiantes,
            key=lambda fila: (
                fila.promedio is None,
                -(fila.promedio or 0.0),
                fila.estudiante.nombre,
            ),
        )[:8]
        self.tabla.cargar(
            [
                {
                    "iid": fila.estudiante.id,
                    "valores": (
                        fila.estudiante.codigo,
                        fila.estudiante.nombre,
                        fila.notas,
                        formatear_promedio(fila.promedio),
                        etiqueta_estado(fila.estado),
                    ),
                    "tags": (estilo_estado(fila.estado),),
                    "datos": fila,
                }
                for fila in filas
            ]
        )
        if not filas:
            self.tabla.tabla.insert(
                "",
                "end",
                values=("—", "Aún no hay estudiantes registrados", "", "", ""),
                tags=("sin_notas",),
            )
