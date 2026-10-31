"""Historial académico por estudiante en la interfaz de escritorio."""

from __future__ import annotations

import tkinter as tk

from app.core.texto import clave_nombre
from app.escritorio.estilos import (
    AZUL,
    BLANCO,
    FONDO,
    FUENTE,
    FUENTE_TITULO,
    GRIS_BORDE,
    GRIS_TEXTO,
    ROJO_SUAVE,
    VERDE_SUAVE,
)
from app.escritorio.sesion import sesion
from app.escritorio.vistas.base import VistaBase
from app.escritorio.widgets import (
    Tabla,
    Tarjeta,
    estilo_estado,
    etiqueta_estado,
    formatear_promedio,
)


class VistaHistorial(VistaBase):
    titulo = "Historial académico"
    subtitulo = "Trayectoria del estudiante por periodo y materia"

    def construir(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._cargando = False

        izquierda = tk.Frame(
            self,
            bg=BLANCO,
            width=330,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        izquierda.grid_propagate(False)
        izquierda.grid_rowconfigure(2, weight=1)
        izquierda.grid_columnconfigure(0, weight=1)

        tk.Label(
            izquierda,
            text="Estudiantes",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        self.busqueda = tk.Entry(
            izquierda,
            bg=BLANCO,
            fg=AZUL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
            highlightcolor="#C9A227",
            font=(FUENTE, 10),
            insertbackground=AZUL,
        )
        self.busqueda.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8), ipady=5)
        self.busqueda.bind("<Return>", lambda _evento: self.al_mostrar())

        self.lista = Tabla(
            izquierda,
            [
                ("nombre", "Nombre", 200, "w"),
                ("promedio", "Prom.", 70, "center"),
            ],
            altura=18,
        )
        self.lista.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.lista.tabla.bind("<<TreeviewSelect>>", self._seleccionar)

        derecha = tk.Frame(self, bg=FONDO)
        derecha.grid(row=0, column=1, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(2, weight=1)

        self.encabezado = tk.Frame(
            derecha,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        self.encabezado.grid(row=0, column=0, sticky="ew")
        self.encabezado.grid_columnconfigure(0, weight=1)

        textos = tk.Frame(self.encabezado, bg=BLANCO)
        textos.grid(row=0, column=0, sticky="w", padx=16, pady=12)
        self.nombre = tk.Label(
            textos,
            text="Selecciona un estudiante",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 15, "bold"),
            anchor="w",
        )
        self.nombre.pack(fill="x")
        self.detalle = tk.Label(
            textos,
            text="",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
            anchor="w",
        )
        self.detalle.pack(fill="x")

        self.insignia = tk.Label(
            self.encabezado,
            text="SIN NOTAS",
            bg=VERDE_SUAVE,
            fg=AZUL,
            font=(FUENTE, 9, "bold"),
            padx=14,
            pady=6,
        )
        self.insignia.grid(row=0, column=1, sticky="e", padx=16)

        fila_tarjetas = tk.Frame(derecha, bg=FONDO)
        fila_tarjetas.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for indice in range(4):
            fila_tarjetas.grid_columnconfigure(indice, weight=1)

        self.tarjetas: dict[str, Tarjeta] = {}
        for indice, (clave, titulo, pista) in enumerate(
            [
                ("promedio", "Promedio", "escala institucional"),
                ("notas", "Calificaciones", "notas activas"),
                ("materias", "Materias", "con notas"),
                ("periodos", "Periodos", "con actividad"),
            ]
        ):
            tarjeta = Tarjeta(fila_tarjetas, titulo, "—", pista)
            tarjeta.grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=(0 if indice == 0 else 8, 0),
            )
            self.tarjetas[clave] = tarjeta

        cuerpo = tk.Frame(derecha, bg=FONDO)
        cuerpo.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        panel_notas = tk.Frame(
            cuerpo,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        panel_notas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(
            panel_notas,
            text="Calificaciones",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 6))
        self.tabla_notas = Tabla(
            panel_notas,
            [
                ("periodo", "Periodo", 140, "w"),
                ("materia", "Materia", 150, "w"),
                ("nota", "Nota", 65, "center"),
                ("fecha", "Fecha", 95, "center"),
                ("descripcion", "Descripción", 150, "w"),
            ],
            altura=10,
        )
        self.tabla_notas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        panel_resumen = tk.Frame(
            cuerpo,
            bg=BLANCO,
            width=330,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        panel_resumen.grid(row=0, column=1, sticky="nsew")
        panel_resumen.grid_propagate(False)
        tk.Label(
            panel_resumen,
            text="Resumen por periodo",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 6))
        self.tabla_periodos = Tabla(
            panel_resumen,
            [
                ("periodo", "Periodo", 140, "w"),
                ("notas", "Notas", 55, "center"),
                ("promedio", "Prom.", 60, "center"),
                ("estado", "Estado", 80, "center"),
            ],
            altura=10,
        )
        self.tabla_periodos.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def al_mostrar(self) -> None:
        with sesion(escritura=False) as servicios:
            resumen = servicios.analisis.resumen()

        texto = clave_nombre(self.busqueda.get().strip())
        filas = [
            fila
            for fila in resumen.estudiantes
            if not texto
            or texto in clave_nombre(fila.estudiante.nombre)
            or texto in fila.estudiante.codigo.casefold()
        ]
        filas.sort(key=lambda fila: fila.estudiante.nombre)

        seleccionado = self.lista.seleccion()
        self._cargando = True
        self.lista.cargar(
            [
                {
                    "iid": fila.estudiante.id,
                    "valores": (
                        fila.estudiante.nombre,
                        formatear_promedio(fila.promedio),
                    ),
                    "tags": (estilo_estado(fila.estado),),
                    "datos": fila,
                }
                for fila in filas
            ]
        )
        self._cargando = False

        ids = [fila.estudiante.id for fila in filas]
        if not ids:
            self._mostrar_vacio()
            return

        objetivo = seleccionado if seleccionado in ids else ids[0]
        self.lista.tabla.selection_set(objetivo)
        self.lista.tabla.focus(objetivo)
        self._cargar_detalle(objetivo)

    def _seleccionar(self, _evento: object = None) -> None:
        if self._cargando:
            return
        estudiante_id = self.lista.seleccion()
        if estudiante_id:
            self._cargar_detalle(estudiante_id)

    def _mostrar_vacio(self) -> None:
        self.nombre.configure(text="Sin estudiantes")
        self.detalle.configure(text="Registra un estudiante para ver su historial.")
        self.insignia.configure(text="—", bg=VERDE_SUAVE, fg=GRIS_TEXTO)
        for tarjeta in self.tarjetas.values():
            tarjeta.actualizar("—", "")
        self.tabla_notas.limpiar()
        self.tabla_periodos.limpiar()

    def _cargar_detalle(self, estudiante_id: str) -> None:
        with sesion(escritura=False) as servicios:
            detalle = servicios.analisis.detalle_estudiante(estudiante_id)

        self.nombre.configure(text=detalle.estudiante.nombre)
        correo = detalle.estudiante.correo or "sin correo"
        self.detalle.configure(
            text=f"{detalle.estudiante.codigo}  ·  {correo}  ·  "
            f"{detalle.estudiante.origen.replace('_', ' ')}"
        )

        aprobado = detalle.estado == "APROBADO"
        self.insignia.configure(
            text=etiqueta_estado(detalle.estado).upper(),
            bg=VERDE_SUAVE if aprobado else ROJO_SUAVE,
            fg="#1E7F4F" if aprobado else "#B3261E",
        )

        self.tarjetas["promedio"].actualizar(
            formatear_promedio(detalle.promedio), "promedio aritmético"
        )
        self.tarjetas["notas"].actualizar(
            str(len(detalle.detalles)), "notas activas"
        )
        self.tarjetas["materias"].actualizar(
            str(len(detalle.por_materia)), "materias con notas"
        )
        self.tarjetas["periodos"].actualizar(
            str(len(detalle.por_periodo)), "periodos con actividad"
        )

        self.tabla_notas.cargar(
            [
                {
                    "iid": nota.id,
                    "valores": (
                        nota.periodo_nombre,
                        nota.materia_nombre,
                        f"{nota.nota:.2f}",
                        nota.fecha,
                        nota.descripcion or "—",
                    ),
                    "datos": nota,
                }
                for nota in detalle.detalles
            ]
        )

        self.tabla_periodos.cargar(
            [
                {
                    "iid": resumen.periodo.id,
                    "valores": (
                        resumen.periodo.nombre,
                        resumen.notas,
                        formatear_promedio(resumen.promedio),
                        etiqueta_estado(resumen.estado),
                    ),
                    "tags": (estilo_estado(resumen.estado),),
                    "datos": resumen,
                }
                for resumen in detalle.por_periodo
            ]
        )
