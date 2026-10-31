"""Configuración de escala y periodos académicos en escritorio."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.escala import Escala
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
    avisar_info,
)


class VistaConfiguracion(VistaBase):
    titulo = "Configuración académica"
    subtitulo = "Escala de notas y periodos con escala propia"

    def construir(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        izquierda = tk.Frame(
            self,
            bg=BLANCO,
            width=390,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        izquierda.grid_propagate(False)

        tk.Label(
            izquierda,
            text="Escala global",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 2))
        tk.Label(
            izquierda,
            text="Se aplica a los periodos nuevos. Los periodos existentes\n"
            "conservan la escala con la que fueron creados.",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 10))

        self.minima = self._campo(izquierda, "Nota mínima")
        self.maxima = self._campo(izquierda, "Nota máxima")
        self.aprobacion = self._campo(izquierda, "Promedio de aprobación")
        self.decimales = self._campo(izquierda, "Decimales al mostrar (0–6)")

        ttk.Button(
            izquierda,
            text="Guardar escala",
            style="Primary.TButton",
            command=self._guardar_escala,
        ).pack(fill="x", padx=16, pady=(8, 8))

        tk.Label(
            izquierda,
            text="Las notas se validan contra la escala del periodo\n"
            "seleccionado al registrarlas.",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 12))

        derecha = tk.Frame(
            self,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        derecha.grid(row=0, column=1, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(1, weight=1)

        cabecera = tk.Frame(derecha, bg=BLANCO)
        cabecera.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        tk.Label(
            cabecera,
            text="Periodos académicos",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 12, "bold"),
        ).pack(side="left")
        ttk.Button(
            cabecera,
            text="+  Nuevo periodo",
            style="Primary.TButton",
            command=self._nuevo_periodo,
        ).pack(side="right")

        self.tabla = Tabla(
            derecha,
            [
                ("nombre", "Periodo", 180, "w"),
                ("inicio", "Inicio", 105, "center"),
                ("fin", "Fin", 105, "center"),
                ("escala", "Escala", 120, "center"),
                ("aprueba", "Aprueba", 90, "center"),
                ("estado", "Estado", 90, "center"),
            ],
            altura=12,
        )
        self.tabla.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.tabla.tabla.bind("<Double-1>", lambda _evento: self._editar_periodo())

        pie = tk.Frame(derecha, bg=BLANCO)
        pie.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.contador = tk.Label(
            pie,
            text="",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
        )
        self.contador.pack(side="left")
        ttk.Button(
            pie,
            text="Editar periodo",
            style="Secondary.TButton",
            command=self._editar_periodo,
        ).pack(side="right")

    def _campo(self, maestro: tk.Misc, etiqueta: str) -> tk.Entry:
        tk.Label(
            maestro,
            text=etiqueta.upper(),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(2, 2))
        entrada = tk.Entry(
            maestro,
            bg=BLANCO,
            fg=AZUL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
            highlightcolor="#C9A227",
            font=(FUENTE, 10),
            insertbackground=AZUL,
        )
        entrada.pack(fill="x", padx=16, ipady=5, pady=(0, 8))
        return entrada

    def al_mostrar(self) -> None:
        with sesion(escritura=False) as servicios:
            escala = servicios.configuracion.obtener_escala()
            periodos = servicios.periodos.listar(incluir_inactivos=True)

        for entrada, valor in (
            (self.minima, f"{escala.minima:g}"),
            (self.maxima, f"{escala.maxima:g}"),
            (self.aprobacion, f"{escala.aprobacion:g}"),
            (self.decimales, str(escala.decimales)),
        ):
            entrada.delete(0, "end")
            entrada.insert(0, valor)

        self.tabla.cargar(
            [
                {
                    "iid": periodo.id,
                    "valores": (
                        periodo.nombre,
                        periodo.fecha_inicio or "—",
                        periodo.fecha_fin or "—",
                        f"{periodo.escala_min:g}–{periodo.escala_max:g}",
                        f"{periodo.aprobacion_min:g}",
                        "Activo" if periodo.activo else "Inactivo",
                    ),
                    "tags": ("aprobado",) if periodo.activo else ("sin_notas",),
                    "datos": periodo,
                }
                for periodo in periodos
            ]
        )
        self.contador.configure(
            text=f"{len(periodos)} periodo(s) · doble clic para editar"
        )

    def _guardar_escala(self) -> None:
        try:
            with sesion() as servicios:
                servicios.configuracion.actualizar_escala(
                    float(self.minima.get().replace(",", ".")),
                    float(self.maxima.get().replace(",", ".")),
                    float(self.aprobacion.get().replace(",", ".")),
                    int(self.decimales.get()),
                )
        except Exception as error:
            avisar_error(self.app, error)
            return
        avisar_info(self.app, "La escala global se actualizó correctamente.")
        self.al_mostrar()

    def _nuevo_periodo(self) -> None:
        with sesion(escritura=False) as servicios:
            escala = servicios.configuracion.obtener_escala()

        modal = ModalFormulario(
            self.app,
            "Nuevo periodo",
            "La escala queda congelada para este periodo",
            alto=610,
        )
        nombre = modal.campo("Nombre del periodo")
        inicio = modal.campo("Fecha inicial (AAAA-MM-DD, opcional)")
        fin = modal.campo("Fecha final (AAAA-MM-DD, opcional)")
        minima = modal.campo("Nota mínima", f"{escala.minima:g}")
        maxima = modal.campo("Nota máxima", f"{escala.maxima:g}")
        aprobacion = modal.campo("Promedio de aprobación", f"{escala.aprobacion:g}")
        activo = modal.casilla("Periodo activo", True)

        def guardar() -> None:
            try:
                nueva_escala = Escala(
                    minima=float(minima.get().replace(",", ".")),
                    maxima=float(maxima.get().replace(",", ".")),
                    aprobacion=float(aprobacion.get().replace(",", ".")),
                )
                with sesion() as servicios:
                    servicios.periodos.crear(
                        nombre.get(),
                        fecha_inicio=inicio.get().strip() or None,
                        fecha_fin=fin.get().strip() or None,
                        escala=nueva_escala,
                        activo=activo.get(),
                    )
            except Exception as error:
                avisar_error(modal, error)
                return
            modal.destroy()
            self.al_mostrar()

        modal.botones(guardar, "Crear periodo")
        nombre.focus_set()
        modal.wait_window()

    def _editar_periodo(self) -> None:
        periodo = self.tabla.objeto_seleccionado()
        if periodo is None:
            return

        modal = ModalFormulario(
            self.app,
            "Editar periodo",
            f"{periodo.nombre} · escala {periodo.escala_min:g}–{periodo.escala_max:g}",
            alto=610,
        )
        nombre = modal.campo("Nombre del periodo", periodo.nombre)
        inicio = modal.campo("Fecha inicial (AAAA-MM-DD)", periodo.fecha_inicio or "")
        fin = modal.campo("Fecha final (AAAA-MM-DD)", periodo.fecha_fin or "")
        minima = modal.campo("Nota mínima", f"{periodo.escala_min:g}")
        maxima = modal.campo("Nota máxima", f"{periodo.escala_max:g}")
        aprobacion = modal.campo(
            "Promedio de aprobación", f"{periodo.aprobacion_min:g}"
        )
        activo = modal.casilla("Periodo activo", periodo.activo)

        def guardar() -> None:
            try:
                escala = Escala(
                    minima=float(minima.get().replace(",", ".")),
                    maxima=float(maxima.get().replace(",", ".")),
                    aprobacion=float(aprobacion.get().replace(",", ".")),
                )
                with sesion() as servicios:
                    servicios.periodos.actualizar(
                        periodo.id,
                        nombre=nombre.get(),
                        fecha_inicio=inicio.get().strip() or None,
                        fecha_fin=fin.get().strip() or None,
                        escala=escala,
                        activo=activo.get(),
                    )
            except Exception as error:
                avisar_error(modal, error)
                return
            modal.destroy()
            self.al_mostrar()

        modal.botones(guardar, "Guardar cambios")
        nombre.focus_set()
        modal.wait_window()
