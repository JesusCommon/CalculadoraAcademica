"""Registro y administración de calificaciones en escritorio."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from app.core.tiempo import hoy_iso
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
    Tabla,
    avisar_error,
    avisar_info,
    confirmar,
    estilo_estado,
    formatear_promedio,
)


class VistaCalificaciones(VistaBase):
    titulo = "Calificaciones"
    subtitulo = "Registro de notas por estudiante, materia y periodo"

    def construir(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._mapa_estudiantes: dict[str, object] = {}
        self._mapa_materias: dict[str, object] = {}
        self._mapa_periodos: dict[str, object] = {}

        panel = tk.Frame(
            self,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(0, weight=3)
        panel.grid_columnconfigure(1, weight=3)
        panel.grid_columnconfigure(2, weight=2)
        panel.grid_columnconfigure(3, weight=1)
        panel.grid_columnconfigure(4, weight=2)
        panel.grid_columnconfigure(5, weight=3)

        tk.Label(
            panel,
            text="Registrar nueva calificación",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 11, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=6, sticky="w", padx=14, pady=(10, 6))

        self.combo_estudiante = self._campo_combo(
            panel, "Estudiante", 1, 0, columnspan=2
        )
        self.combo_materia = self._campo_combo(panel, "Materia", 1, 2)
        self.combo_periodo = self._campo_combo(panel, "Periodo", 1, 3, columnspan=2)

        self.nota = self._campo_texto(panel, "Nota", 1, 5, ancho=12)
        self.nota.insert(0, "")

        self.fecha = self._campo_texto(panel, "Fecha (AAAA-MM-DD)", 2, 0)
        self.fecha.insert(0, hoy_iso())
        self.descripcion = self._campo_texto(
            panel, "Descripción (opcional)", 2, 1, columnspan=3
        )

        acciones = tk.Frame(panel, bg=BLANCO)
        acciones.grid(row=2, column=4, columnspan=2, sticky="e", padx=14, pady=(0, 12))
        ttk.Button(
            acciones,
            text="Limpiar",
            style="Secondary.TButton",
            command=self._limpiar_formulario,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            acciones,
            text="Registrar calificación",
            style="Primary.TButton",
            command=self._registrar,
        ).pack(side="left")

        filtros = tk.Frame(self, bg=FONDO)
        filtros.grid(row=1, column=0, sticky="ew", pady=(12, 8))
        tk.Label(
            filtros,
            text="Filtrar por",
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.filtro_estudiante = ttk.Combobox(filtros, state="readonly", width=34)
        self.filtro_estudiante.pack(side="left", padx=(0, 8))
        self.filtro_estudiante.bind(
            "<<ComboboxSelected>>", lambda _evento: self._cargar_tabla()
        )

        self.filtro_periodo = ttk.Combobox(filtros, state="readonly", width=28)
        self.filtro_periodo.pack(side="left", padx=(0, 8))
        self.filtro_periodo.bind(
            "<<ComboboxSelected>>", lambda _evento: self._cargar_tabla()
        )

        ttk.Button(
            filtros,
            text="Actualizar",
            style="Secondary.TButton",
            command=self.al_mostrar,
        ).pack(side="left")

        self.tabla = Tabla(
            self,
            [
                ("estudiante", "Estudiante", 210, "w"),
                ("materia", "Materia", 190, "w"),
                ("periodo", "Periodo", 160, "w"),
                ("nota", "Nota", 80, "center"),
                ("fecha", "Fecha", 110, "center"),
                ("descripcion", "Descripción", 220, "w"),
            ],
            altura=12,
        )
        self.tabla.grid(row=2, column=0, sticky="nsew")

        pie = tk.Frame(self, bg=FONDO)
        pie.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.contador = tk.Label(
            pie,
            text="",
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
        )
        self.contador.pack(side="left")

        self.promedio = tk.Label(
            pie,
            text="",
            bg=FONDO,
            fg=AZUL,
            font=(FUENTE, 9, "bold"),
        )
        self.promedio.pack(side="left", padx=18)

        ttk.Button(
            pie,
            text="Anular seleccionada",
            style="Danger.TButton",
            command=self._anular,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Helpers de formulario
    # ------------------------------------------------------------------
    def _campo_combo(
        self,
        maestro: tk.Misc,
        etiqueta: str,
        fila: int,
        columna: int,
        *,
        columnspan: int = 1,
    ) -> ttk.Combobox:
        contenedor = tk.Frame(maestro, bg=BLANCO)
        contenedor.grid(
            row=fila,
            column=columna,
            columnspan=columnspan,
            sticky="ew",
            padx=14,
            pady=(0, 6),
        )
        tk.Label(
            contenedor,
            text=etiqueta.upper(),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        combo = ttk.Combobox(contenedor, state="readonly", font=(FUENTE, 10))
        combo.pack(fill="x", pady=(2, 0))
        return combo

    def _campo_texto(
        self,
        maestro: tk.Misc,
        etiqueta: str,
        fila: int,
        columna: int,
        *,
        columnspan: int = 1,
        ancho: int = 0,
    ) -> tk.Entry:
        contenedor = tk.Frame(maestro, bg=BLANCO)
        contenedor.grid(
            row=fila,
            column=columna,
            columnspan=columnspan,
            sticky="ew",
            padx=14,
            pady=(0, 12),
        )
        tk.Label(
            contenedor,
            text=etiqueta.upper(),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        entrada = tk.Entry(
            contenedor,
            bg=BLANCO,
            fg=AZUL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
            highlightcolor="#C9A227",
            font=(FUENTE, 10),
            insertbackground=AZUL,
            width=ancho,
        )
        entrada.pack(fill="x", ipady=5, pady=(2, 0))
        return entrada

    def _limpiar_formulario(self) -> None:
        self.nota.delete(0, "end")
        self.descripcion.delete(0, "end")
        self.fecha.delete(0, "end")
        self.fecha.insert(0, hoy_iso())
        self.nota.focus_set()

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def al_mostrar(self) -> None:
        with sesion(escritura=False) as servicios:
            estudiantes = servicios.estudiantes.listar()
            materias = servicios.materias.listar()
            periodos = servicios.periodos.listar()

        self._mapa_estudiantes = {
            f"{estudiante.codigo} · {estudiante.nombre}": estudiante
            for estudiante in estudiantes
        }
        self._mapa_materias = {
            f"{materia.codigo} · {materia.nombre}": materia for materia in materias
        }
        self._mapa_periodos = {
            f"{periodo.nombre}  ({periodo.escala_min:g}–{periodo.escala_max:g})": periodo
            for periodo in periodos
        }

        self._actualizar_combo(self.combo_estudiante, list(self._mapa_estudiantes))
        self._actualizar_combo(self.combo_materia, list(self._mapa_materias))
        self._actualizar_combo(self.combo_periodo, list(self._mapa_periodos))

        filtro_estudiante = self.filtro_estudiante.get()
        filtro_periodo = self.filtro_periodo.get()

        self.filtro_estudiante.configure(
            values=["Todos los estudiantes", *self._mapa_estudiantes]
        )
        self.filtro_periodo.configure(
            values=["Todos los periodos", *self._mapa_periodos]
        )
        self.filtro_estudiante.set(
            filtro_estudiante
            if filtro_estudiante in self.filtro_estudiante.cget("values")
            else "Todos los estudiantes"
        )
        self.filtro_periodo.set(
            filtro_periodo
            if filtro_periodo in self.filtro_periodo.cget("values")
            else "Todos los periodos"
        )

        self._cargar_tabla(periodos)

    @staticmethod
    def _actualizar_combo(combo: ttk.Combobox, valores: list[str]) -> None:
        actual = combo.get()
        combo.configure(values=valores)
        if actual in valores:
            combo.set(actual)
        elif valores:
            combo.set(valores[0])
        else:
            combo.set("")

    def _cargar_tabla(self, periodos: list | None = None) -> None:
        estudiante = self._mapa_estudiantes.get(self.filtro_estudiante.get())
        periodo = self._mapa_periodos.get(self.filtro_periodo.get())

        with sesion(escritura=False) as servicios:
            if periodos is None:
                periodos = servicios.periodos.listar()
            detalles = servicios.calificaciones.listar_todas(
                estudiante_id=estudiante.id if estudiante else None,
                periodo_id=periodo.id if periodo else None,
            )

        escalas = {periodo_item.id: periodo_item.escala for periodo_item in periodos}
        filas = []
        notas = []
        for detalle in detalles:
            notas.append(detalle.nota)
            escala = escalas.get(detalle.periodo_id)
            estado = escala.estado(detalle.nota) if escala else "SIN NOTAS"
            filas.append(
                {
                    "iid": detalle.id,
                    "valores": (
                        detalle.estudiante_nombre,
                        detalle.materia_nombre,
                        detalle.periodo_nombre,
                        f"{detalle.nota:.2f}",
                        detalle.fecha,
                        detalle.descripcion or "—",
                    ),
                    "tags": (estilo_estado(estado),),
                    "datos": detalle,
                }
            )

        self.tabla.cargar(filas)
        self.contador.configure(text=f"{len(filas)} calificación(es) activa(s)")

        if notas:
            promedio = sum(notas) / len(notas)
            self.promedio.configure(text=f"Promedio del filtro: {promedio:.2f}")
        else:
            self.promedio.configure(text="Promedio del filtro: —")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _registrar(self) -> None:
        estudiante = self._mapa_estudiantes.get(self.combo_estudiante.get())
        materia = self._mapa_materias.get(self.combo_materia.get())
        periodo = self._mapa_periodos.get(self.combo_periodo.get())

        if estudiante is None or materia is None or periodo is None:
            avisar_info(
                self.app,
                "Selecciona un estudiante, una materia y un periodo.",
                "Datos incompletos",
            )
            return

        texto = self.nota.get().strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            avisar_error(self.app, ValueError("La nota debe ser un número válido."))
            return

        fecha = self.fecha.get().strip() or None
        if fecha is not None:
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                avisar_error(
                    self.app,
                    ValueError("La fecha debe tener el formato AAAA-MM-DD."),
                )
                return

        try:
            with sesion() as servicios:
                servicios.calificaciones.registrar(
                    estudiante.id,
                    materia.id,
                    periodo.id,
                    valor,
                    descripcion=self.descripcion.get().strip() or None,
                    fecha=fecha,
                )
        except Exception as error:
            avisar_error(self.app, error)
            return

        self.nota.delete(0, "end")
        self.descripcion.delete(0, "end")
        self.nota.focus_set()
        self.al_mostrar()

    def _anular(self) -> None:
        detalle = self.tabla.objeto_seleccionado()
        if detalle is None:
            return
        if not confirmar(
            self.app,
            "Anular calificación",
            f"¿Anular la nota {detalle.nota:.2f} de "
            f"{detalle.estudiante_nombre} en {detalle.materia_nombre}?\n\n"
            "La nota se conserva en SQLite, pero dejará de promediar.",
        ):
            return
        try:
            with sesion() as servicios:
                servicios.calificaciones.anular(detalle.id)
        except Exception as error:
            avisar_error(self.app, error)
            return
        self.al_mostrar()
