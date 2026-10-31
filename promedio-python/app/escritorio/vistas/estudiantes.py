"""Gestión de estudiantes en la interfaz de escritorio."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.texto import clave_nombre
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
    ModalFormulario,
    Tabla,
    avisar_error,
    confirmar,
    estilo_estado,
    etiqueta_estado,
    formatear_promedio,
)


class VistaEstudiantes(VistaBase):
    titulo = "Gestión de estudiantes"
    subtitulo = "Altas, edición, búsqueda y baja lógica"

    def construir(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = tk.Frame(self, bg=FONDO)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            barra,
            text="Buscar",
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.busqueda = tk.Entry(
            barra,
            bg=BLANCO,
            fg=AZUL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
            highlightcolor="#C9A227",
            font=(FUENTE, 10),
            insertbackground=AZUL,
            width=32,
        )
        self.busqueda.pack(side="left", ipady=6)
        self.busqueda.bind("<Return>", lambda _evento: self.al_mostrar())

        ttk.Button(
            barra,
            text="Buscar",
            style="Secondary.TButton",
            command=self.al_mostrar,
        ).pack(side="left", padx=8)

        ttk.Button(
            barra,
            text="+  Nuevo estudiante",
            style="Primary.TButton",
            command=self._nuevo,
        ).pack(side="right")

        self.tabla = Tabla(
            self,
            [
                ("codigo", "Código", 110, "w"),
                ("nombre", "Nombre", 280, "w"),
                ("correo", "Correo", 230, "w"),
                ("notas", "Notas", 80, "center"),
                ("promedio", "Promedio", 100, "center"),
                ("estado", "Estado", 120, "center"),
            ],
            altura=14,
        )
        self.tabla.grid(row=1, column=0, sticky="nsew")
        self.tabla.tabla.bind("<Double-1>", lambda _evento: self._editar())

        pie = tk.Frame(self, bg=FONDO)
        pie.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.contador = tk.Label(
            pie,
            text="",
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
        )
        self.contador.pack(side="left")

        ttk.Button(
            pie,
            text="Eliminar",
            style="Danger.TButton",
            command=self._eliminar,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            pie,
            text="Editar seleccionado",
            style="Secondary.TButton",
            command=self._editar,
        ).pack(side="right")

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

        self.tabla.cargar(
            [
                {
                    "iid": fila.estudiante.id,
                    "valores": (
                        fila.estudiante.codigo,
                        fila.estudiante.nombre,
                        fila.estudiante.correo or "—",
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
        self.contador.configure(
            text=f"{len(filas)} estudiante(s) · doble clic para editar"
        )

    def _nuevo(self) -> None:
        modal = ModalFormulario(
            self.app,
            "Nuevo estudiante",
            "El código se asigna automáticamente",
            alto=340,
        )
        nombre = modal.campo("Nombre completo")
        correo = modal.campo("Correo electrónico (opcional)")

        def guardar() -> None:
            try:
                with sesion() as servicios:
                    servicios.estudiantes.crear(nombre.get(), correo.get() or None)
            except Exception as error:
                avisar_error(modal, error)
                return
            modal.destroy()
            self.al_mostrar()

        modal.botones(guardar, "Guardar estudiante")
        nombre.focus_set()
        modal.wait_window()

    def _editar(self) -> None:
        fila = self.tabla.objeto_seleccionado()
        if fila is None:
            return
        estudiante = fila.estudiante

        modal = ModalFormulario(
            self.app,
            "Editar estudiante",
            f"{estudiante.codigo} · {estudiante.nombre}",
            alto=340,
        )
        nombre = modal.campo("Nombre completo", estudiante.nombre)
        correo = modal.campo("Correo electrónico (opcional)", estudiante.correo or "")

        def guardar() -> None:
            try:
                with sesion() as servicios:
                    servicios.estudiantes.actualizar(
                        estudiante.id,
                        nombre=nombre.get(),
                        correo=correo.get(),
                    )
            except Exception as error:
                avisar_error(modal, error)
                return
            modal.destroy()
            self.al_mostrar()

        modal.botones(guardar, "Guardar cambios")
        nombre.focus_set()
        modal.wait_window()

    def _eliminar(self) -> None:
        fila = self.tabla.objeto_seleccionado()
        if fila is None:
            return
        estudiante = fila.estudiante
        if not confirmar(
            self.app,
            "Eliminar estudiante",
            f"¿Eliminar a {estudiante.nombre} del listado activo?\n\n"
            "La baja es lógica: sus calificaciones se conservan en SQLite.",
        ):
            return
        try:
            with sesion() as servicios:
                servicios.estudiantes.eliminar(estudiante.id)
        except Exception as error:
            avisar_error(self.app, error)
            return
        self.al_mostrar()
