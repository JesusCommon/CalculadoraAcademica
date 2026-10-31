"""Gestión de materias en la interfaz de escritorio."""

from __future__ import annotations

import tkinter as tk
from collections import Counter
from tkinter import ttk

from app.core.texto import clave_nombre
from app.escritorio.estilos import (
    AZUL,
    BLANCO,
    FONDO,
    FUENTE,
    GRIS_BORDE,
    GRIS_TEXTO,
)
from app.escritorio.sesion import sesion
from app.escritorio.vistas.base import VistaBase
from app.escritorio.widgets import ModalFormulario, Tabla, avisar_error, confirmar


class VistaMaterias(VistaBase):
    titulo = "Gestión de materias"
    subtitulo = "Catálogo académico con créditos y baja lógica"

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
            text="+  Nueva materia",
            style="Primary.TButton",
            command=self._nueva,
        ).pack(side="right")

        self.tabla = Tabla(
            self,
            [
                ("codigo", "Código", 130, "w"),
                ("nombre", "Materia", 340, "w"),
                ("creditos", "Créditos", 100, "center"),
                ("notas", "Calificaciones", 130, "center"),
                ("estado", "Estado", 110, "center"),
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
            text="Editar seleccionada",
            style="Secondary.TButton",
            command=self._editar,
        ).pack(side="right")

    def al_mostrar(self) -> None:
        with sesion(escritura=False) as servicios:
            materias = servicios.materias.listar()
            detalles = servicios.calificaciones.listar_todas()

        conteo = Counter(detalle.materia_id for detalle in detalles)
        texto = clave_nombre(self.busqueda.get().strip())
        materias = [
            materia
            for materia in materias
            if not texto
            or texto in clave_nombre(materia.nombre)
            or texto in materia.codigo.casefold()
        ]
        materias.sort(key=lambda materia: materia.codigo)

        self.tabla.cargar(
            [
                {
                    "iid": materia.id,
                    "valores": (
                        materia.codigo,
                        materia.nombre,
                        f"{materia.creditos:g}",
                        conteo.get(materia.id, 0),
                        "Activa",
                    ),
                    "tags": ("aprobado",),
                    "datos": materia,
                }
                for materia in materias
            ]
        )
        self.contador.configure(
            text=f"{len(materias)} materia(s) · doble clic para editar"
        )

    def _nueva(self) -> None:
        modal = ModalFormulario(
            self.app,
            "Nueva materia",
            "El código se guarda en mayúsculas",
            alto=400,
        )
        codigo = modal.campo("Código (por ejemplo MAT-101)")
        nombre = modal.campo("Nombre de la materia")
        creditos = modal.campo("Créditos", "0")

        def guardar() -> None:
            try:
                with sesion() as servicios:
                    servicios.materias.crear(
                        codigo.get(),
                        nombre.get(),
                        float(creditos.get().strip().replace(",", ".") or 0),
                    )
            except Exception as error:
                avisar_error(modal, error)
                return
            modal.destroy()
            self.al_mostrar()

        modal.botones(guardar, "Guardar materia")
        codigo.focus_set()
        modal.wait_window()

    def _editar(self) -> None:
        materia = self.tabla.objeto_seleccionado()
        if materia is None:
            return

        modal = ModalFormulario(
            self.app,
            "Editar materia",
            f"{materia.codigo} · {materia.nombre}",
            alto=400,
        )
        codigo = modal.campo("Código", materia.codigo)
        nombre = modal.campo("Nombre de la materia", materia.nombre)
        creditos = modal.campo("Créditos", f"{materia.creditos:g}")

        def guardar() -> None:
            try:
                with sesion() as servicios:
                    servicios.materias.actualizar(
                        materia.id,
                        codigo=codigo.get(),
                        nombre=nombre.get(),
                        creditos=float(
                            creditos.get().strip().replace(",", ".") or 0
                        ),
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
        materia = self.tabla.objeto_seleccionado()
        if materia is None:
            return
        with sesion(escritura=False) as servicios:
            detalles = servicios.calificaciones.listar_todas(materia_id=materia.id)
        if not confirmar(
            self.app,
            "Eliminar materia",
            f"¿Eliminar la materia {materia.codigo} · {materia.nombre}?\n\n"
            f"Se conservarán {len(detalles)} calificación(es) en el historial.",
        ):
            return
        try:
            with sesion() as servicios:
                servicios.materias.eliminar(materia.id)
        except Exception as error:
            avisar_error(self.app, error)
            return
        self.al_mostrar()
