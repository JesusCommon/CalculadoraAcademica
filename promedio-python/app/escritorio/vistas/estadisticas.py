"""Estadísticas y gráficos de la interfaz de escritorio."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

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
    Tabla,
    Tarjeta,
    estilo_estado,
    etiqueta_estado,
    formatear_promedio,
)


class VistaEstadisticas(VistaBase):
    titulo = "Estadísticas académicas"
    subtitulo = "Indicadores de rendimiento y comparación por periodo"

    def construir(self) -> None:
        self._mapa_periodos: dict[str, object] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        filtros = tk.Frame(self, bg=FONDO)
        filtros.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tk.Label(
            filtros,
            text="Periodo",
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.filtro = ttk.Combobox(filtros, state="readonly", width=34)
        self.filtro.pack(side="left", padx=(0, 8))
        self.filtro.bind("<<ComboboxSelected>>", lambda _evento: self._cargar())

        ttk.Button(
            filtros,
            text="Actualizar",
            style="Secondary.TButton",
            command=self._cargar,
        ).pack(side="left")

        fila = tk.Frame(self, bg=FONDO)
        fila.grid(row=1, column=0, sticky="ew")
        for indice in range(4):
            fila.grid_columnconfigure(indice, weight=1)

        self.tarjetas: dict[str, Tarjeta] = {}
        definiciones = [
            ("promedio", "Promedio general", "del filtro activo"),
            ("aprobados", "Aprobados", "sobre el total"),
            ("reprobados", "Reprobados", "bajo el umbral"),
            ("sin_notas", "Sin notas", "sin calificaciones"),
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
        zona.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        zona.grid_columnconfigure(0, weight=1)
        zona.grid_columnconfigure(1, weight=1)
        zona.grid_rowconfigure(0, weight=1)

        panel_materias, cuerpo_materias = self._panel(zona, "Promedio por materia")
        panel_materias.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.grafico_materias = GraficoBarras(cuerpo_materias, alto=200)
        self.grafico_materias.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        panel_periodos, cuerpo_periodos = self._panel(zona, "Promedio por periodo")
        panel_periodos.grid(row=0, column=1, sticky="nsew")
        self.grafico_periodos = GraficoBarras(cuerpo_periodos, alto=200)
        self.grafico_periodos.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        panel_tabla = tk.Frame(
            self,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        panel_tabla.grid(row=3, column=0, sticky="nsew", pady=(12, 0))

        cabecera = tk.Frame(panel_tabla, bg=BLANCO)
        cabecera.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(
            cabecera,
            text="Rendimiento por estudiante",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
        ).pack(side="left")
        self.resumen_texto = tk.Label(
            cabecera,
            text="",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
        )
        self.resumen_texto.pack(side="right")

        self.tabla = Tabla(
            panel_tabla,
            [
                ("codigo", "Código", 110, "w"),
                ("nombre", "Estudiante", 280, "w"),
                ("notas", "Notas", 80, "center"),
                ("promedio", "Promedio", 110, "center"),
                ("estado", "Estado", 120, "center"),
            ],
            altura=7,
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
            periodos = servicios.periodos.listar()

        self._mapa_periodos = {
            f"{periodo.nombre}  ({periodo.escala_min:g}–{periodo.escala_max:g})": periodo
            for periodo in periodos
        }
        actual = self.filtro.get()
        valores = ["Todos los periodos", *self._mapa_periodos]
        self.filtro.configure(values=valores)
        self.filtro.set(actual if actual in valores else "Todos los periodos")
        self._cargar()

    def _cargar(self) -> None:
        periodo = self._mapa_periodos.get(self.filtro.get())

        with sesion(escritura=False) as servicios:
            resumen = servicios.analisis.resumen(
                periodo_id=periodo.id if periodo else None
            )

        self.tarjetas["promedio"].actualizar(
            formatear_promedio(resumen.promedio_general),
            f"{resumen.total_calificaciones} calificaciones",
        )
        self.tarjetas["aprobados"].actualizar(
            str(resumen.aprobados), f"{resumen.total_estudiantes} estudiantes"
        )
        self.tarjetas["reprobados"].actualizar(
            str(resumen.reprobados), "por debajo del umbral"
        )
        self.tarjetas["sin_notas"].actualizar(
            str(resumen.sin_notas), "sin actividad registrada"
        )

        self.grafico_materias.dibujar(resumen.por_materia)
        self.grafico_periodos.dibujar(resumen.por_periodo)

        filas = sorted(
            resumen.estudiantes,
            key=lambda fila: (
                fila.promedio is None,
                -(fila.promedio or 0.0),
                fila.estudiante.nombre,
            ),
        )
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
        self.resumen_texto.configure(
            text=f"{len(filas)} estudiantes · promedio {formatear_promedio(resumen.promedio_general)}"
        )
