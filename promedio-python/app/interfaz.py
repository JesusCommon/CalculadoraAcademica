"""Interfaz gráfica (Tkinter) de la calculadora de promedios 2.0.

Toda la lógica de negocio vive en ``app.estudiante``, ``app.promedio`` y
``app.historial``. Este módulo solo se encarga de mostrar y capturar datos.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .estudiante import Estudiante
from .historial import ErrorHistorial, Historial
from .promedio import (
    NOTA_APROBACION,
    NOTA_MAXIMA,
    NOTA_MINIMA,
    calcular_promedio,
    determinar_estado,
    validar_nota,
)

# Paleta de colores y tipografía.
FAMILIA = "Segoe UI"
FONDO = "#eef2f7"
BLANCO = "#ffffff"
TEXTO = "#1e293b"
TEXTO_SUAVE = "#64748b"
BORDE = "#cbd5e1"
AZUL = "#2563eb"
AZUL_OSCURO = "#1d4ed8"
VERDE = "#15803d"
VERDE_FONDO = "#dcfce7"
ROJO = "#b91c1c"
ROJO_FONDO = "#fee2e2"
GRIS_FONDO = "#e2e8f0"


class Aplicacion(tk.Tk):
    """Ventana principal de la calculadora de promedios."""

    def __init__(self, historial: Historial | None = None) -> None:
        super().__init__()

        self.historial = historial if historial is not None else Historial()
        self.notas: list[float] = []
        self.indice_edicion: int | None = None

        self.title("Calculadora de Promedios 2.0")
        self.geometry("1000x650")
        self.minsize(900, 600)
        self.configure(bg=FONDO)

        self.nombre_var = tk.StringVar()
        self.nota_var = tk.StringVar()
        self.estado_var = tk.StringVar(value="Listo. Escribe el nombre del estudiante y sus notas.")

        self._configurar_estilos()
        self._construir_interfaz()
        self._cargar_historial()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.entrada_nombre.focus_set()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass  # Se conserva el tema disponible del sistema.

        estilo.configure("TFrame", background=FONDO)
        estilo.configure("TLabel", background=FONDO, foreground=TEXTO)
        estilo.configure("TButton", font=(FAMILIA, 10), padding=(10, 6))
        estilo.configure(
            "Primario.TButton",
            font=(FAMILIA, 10, "bold"),
            padding=(12, 8),
            background=AZUL,
            foreground=BLANCO,
            borderwidth=0,
        )
        estilo.map(
            "Primario.TButton",
            background=[("active", AZUL_OSCURO), ("pressed", AZUL_OSCURO)],
            foreground=[("disabled", GRIS_FONDO)],
        )
        estilo.configure(
            "Historial.Treeview",
            background=BLANCO,
            fieldbackground=BLANCO,
            foreground=TEXTO,
            rowheight=28,
            borderwidth=0,
            font=(FAMILIA, 10),
        )
        estilo.configure(
            "Historial.Treeview.Heading",
            background=GRIS_FONDO,
            foreground=TEXTO,
            font=(FAMILIA, 10, "bold"),
            relief="flat",
            padding=(6, 6),
        )
        estilo.map(
            "Historial.Treeview",
            background=[("selected", AZUL)],
            foreground=[("selected", BLANCO)],
        )
        estilo.configure("TEntry", padding=6)
        estilo.configure("TSeparator", background=BORDE)

    def _construir_interfaz(self) -> None:
        self._construir_cabecera()

        contenido = tk.Frame(self, bg=FONDO)
        contenido.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        contenido.columnconfigure(0, weight=0, minsize=380)
        contenido.columnconfigure(1, weight=1)
        contenido.rowconfigure(0, weight=1)

        self._construir_panel_izquierdo(contenido)
        self._construir_panel_derecho(contenido)

        self.barra_estado = tk.Label(
            self,
            textvariable=self.estado_var,
            bg=FONDO,
            fg=TEXTO_SUAVE,
            anchor="w",
            font=(FAMILIA, 9),
            padx=20,
            pady=6,
        )
        self.barra_estado.pack(fill="x", side="bottom")

    def _construir_cabecera(self) -> None:
        cabecera = tk.Frame(self, bg=AZUL)
        cabecera.pack(fill="x")

        tk.Label(
            cabecera,
            text="Calculadora de Promedios",
            bg=AZUL,
            fg=BLANCO,
            font=(FAMILIA, 18, "bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 0))

        tk.Label(
            cabecera,
            text="Versión 2.0 · Registra estudiantes, gestiona sus notas y conserva el historial",
            bg=AZUL,
            fg="#dbeafe",
            font=(FAMILIA, 10),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(2, 14))

    def _crear_tarjeta(self, padre: tk.Widget, titulo: str) -> tuple[tk.Frame, tk.Frame]:
        """Crea una tarjeta blanca con título y devuelve (tarjeta, cuerpo)."""
        tarjeta = tk.Frame(padre, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1)
        tk.Label(
            tarjeta,
            text=titulo,
            bg=BLANCO,
            fg=TEXTO,
            font=(FAMILIA, 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 8))

        cuerpo = tk.Frame(tarjeta, bg=BLANCO)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        return tarjeta, cuerpo

    def _construir_panel_izquierdo(self, padre: tk.Frame) -> None:
        tarjeta, cuerpo = self._crear_tarjeta(padre, "Datos del estudiante")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        cuerpo.columnconfigure(0, weight=1)

        tk.Label(
            cuerpo,
            text="Nombre del estudiante",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        self.entrada_nombre = ttk.Entry(cuerpo, textvariable=self.nombre_var)
        self.entrada_nombre.grid(row=1, column=0, sticky="ew", pady=(2, 12))

        tk.Label(
            cuerpo,
            text=f"Notas registradas (0.0 a {NOTA_MAXIMA:.1f})",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9, "bold"),
            anchor="w",
        ).grid(row=2, column=0, sticky="w")

        marco_lista = tk.Frame(cuerpo, bg=BLANCO)
        marco_lista.grid(row=3, column=0, sticky="nsew", pady=(2, 8))
        marco_lista.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(3, weight=1)

        self.lista_notas = tk.Listbox(
            marco_lista,
            height=8,
            selectmode="extended",
            bg="#f8fafc",
            fg=TEXTO,
            font=(FAMILIA, 10),
            relief="flat",
            highlightbackground=BORDE,
            highlightthickness=1,
            selectbackground=AZUL,
            selectforeground=BLANCO,
            activestyle="none",
        )
        self.lista_notas.grid(row=0, column=0, sticky="nsew")
        barra_lista = ttk.Scrollbar(marco_lista, orient="vertical", command=self.lista_notas.yview)
        barra_lista.grid(row=0, column=1, sticky="ns")
        self.lista_notas.configure(yscrollcommand=barra_lista.set)

        tk.Label(
            cuerpo,
            text="Nueva nota",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9, "bold"),
            anchor="w",
        ).grid(row=4, column=0, sticky="w", pady=(4, 2))

        marco_agregar = tk.Frame(cuerpo, bg=BLANCO)
        marco_agregar.grid(row=5, column=0, sticky="ew")
        marco_agregar.columnconfigure(0, weight=1)

        self.entrada_nota = ttk.Entry(marco_agregar, textvariable=self.nota_var)
        self.entrada_nota.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entrada_nota.bind("<Return>", self._agregar_nota)
        ttk.Button(
            marco_agregar,
            text="Agregar nota",
            command=self._agregar_nota,
        ).grid(row=0, column=1)

        marco_acciones_notas = tk.Frame(cuerpo, bg=BLANCO)
        marco_acciones_notas.grid(row=6, column=0, sticky="ew", pady=(8, 12))
        ttk.Button(
            marco_acciones_notas,
            text="Eliminar seleccionada",
            command=self._eliminar_nota,
        ).pack(side="left")
        ttk.Button(
            marco_acciones_notas,
            text="Limpiar notas",
            command=self._limpiar_notas,
        ).pack(side="left", padx=(8, 0))

        ttk.Separator(cuerpo, orient="horizontal").grid(row=7, column=0, sticky="ew", pady=(0, 12))

        marco_guardar = tk.Frame(cuerpo, bg=BLANCO)
        marco_guardar.grid(row=8, column=0, sticky="ew")
        self.boton_guardar = ttk.Button(
            marco_guardar,
            text="Guardar estudiante",
            style="Primario.TButton",
            command=self._guardar_estudiante,
        )
        self.boton_guardar.pack(side="left", fill="x", expand=True)
        ttk.Button(
            marco_guardar,
            text="Nuevo",
            command=self._reiniciar_formulario,
        ).pack(side="left", padx=(8, 0))

    def _construir_panel_derecho(self, padre: tk.Frame) -> None:
        panel = tk.Frame(padre, bg=FONDO)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        # --- Tarjeta de resultado -------------------------------------
        tarjeta_resultado, cuerpo_resultado = self._crear_tarjeta(panel, "Resultado")
        tarjeta_resultado.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        cuerpo_resultado.columnconfigure(0, weight=1)

        marco_datos = tk.Frame(cuerpo_resultado, bg=BLANCO)
        marco_datos.grid(row=0, column=0, sticky="ew")
        marco_datos.columnconfigure(0, weight=1)

        tk.Label(
            marco_datos,
            text="PROMEDIO",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.lbl_promedio = tk.Label(
            marco_datos,
            text="—",
            bg=BLANCO,
            fg=TEXTO,
            font=(FAMILIA, 34, "bold"),
            anchor="w",
        )
        self.lbl_promedio.grid(row=1, column=0, sticky="w")

        self.lbl_detalle = tk.Label(
            marco_datos,
            text="Agrega al menos una nota para calcular el promedio.",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9),
            anchor="w",
        )
        self.lbl_detalle.grid(row=2, column=0, sticky="w", pady=(2, 0))

        self.lbl_estado = tk.Label(
            marco_datos,
            text="SIN NOTAS",
            bg=GRIS_FONDO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 12, "bold"),
            padx=16,
            pady=10,
        )
        self.lbl_estado.grid(row=0, column=1, rowspan=3, sticky="e", padx=(16, 0))

        # --- Tarjeta de historial -------------------------------------
        tarjeta_historial, cuerpo_historial = self._crear_tarjeta(panel, "Historial de estudiantes")
        tarjeta_historial.grid(row=1, column=0, sticky="nsew")
        cuerpo_historial.columnconfigure(0, weight=1)
        cuerpo_historial.rowconfigure(0, weight=1)

        marco_tabla = tk.Frame(cuerpo_historial, bg=BLANCO)
        marco_tabla.grid(row=0, column=0, sticky="nsew")
        marco_tabla.columnconfigure(0, weight=1)
        marco_tabla.rowconfigure(0, weight=1)

        self.arbol = ttk.Treeview(
            marco_tabla,
            columns=("nombre", "promedio", "estado"),
            show="headings",
            style="Historial.Treeview",
            selectmode="browse",
        )
        self.arbol.heading("nombre", text="Estudiante", anchor="w")
        self.arbol.heading("promedio", text="Promedio", anchor="center")
        self.arbol.heading("estado", text="Estado", anchor="center")
        self.arbol.column("nombre", width=240, anchor="w")
        self.arbol.column("promedio", width=100, anchor="center", stretch=False)
        self.arbol.column("estado", width=120, anchor="center", stretch=False)
        self.arbol.grid(row=0, column=0, sticky="nsew")
        self.arbol.bind("<Double-1>", self._cargar_seleccionado)
        self.arbol.tag_configure("aprobado", foreground=VERDE)
        self.arbol.tag_configure("reprobado", foreground=ROJO)
        self.arbol.tag_configure("sin_notas", foreground=TEXTO_SUAVE)

        barra_arbol = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.arbol.yview)
        barra_arbol.grid(row=0, column=1, sticky="ns")
        self.arbol.configure(yscrollcommand=barra_arbol.set)

        marco_botones_historial = tk.Frame(cuerpo_historial, bg=BLANCO)
        marco_botones_historial.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.lbl_total = tk.Label(
            marco_botones_historial,
            text="0 estudiantes en el historial",
            bg=BLANCO,
            fg=TEXTO_SUAVE,
            font=(FAMILIA, 9),
        )
        self.lbl_total.pack(side="left")

        ttk.Button(
            marco_botones_historial,
            text="Eliminar del historial",
            command=self._eliminar_del_historial,
        ).pack(side="right")
        ttk.Button(
            marco_botones_historial,
            text="Cargar seleccionado",
            command=self._cargar_seleccionado,
        ).pack(side="right", padx=(0, 8))

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------
    def _cargar_historial(self) -> None:
        try:
            self.historial.cargar()
        except ErrorHistorial as error:
            messagebox.showwarning("Historial", str(error), parent=self)

        self._refrescar_historial()

    def _refrescar_historial(self) -> None:
        for elemento in self.arbol.get_children():
            self.arbol.delete(elemento)

        for indice, estudiante in enumerate(self.historial):
            promedio = estudiante.promedio
            etiqueta = estudiante.estado.lower().replace(" ", "_")
            self.arbol.insert(
                "",
                "end",
                iid=str(indice),
                values=(
                    estudiante.nombre,
                    "—" if promedio is None else f"{promedio:.2f}",
                    estudiante.estado,
                ),
                tags=(etiqueta,),
            )

        total = len(self.historial)
        self.lbl_total.configure(
            text=f"{total} estudiante{'s' if total != 1 else ''} en el historial"
        )

    # ------------------------------------------------------------------
    # Formulario y notas
    # ------------------------------------------------------------------
    def _agregar_nota(self, evento: tk.Event | None = None) -> str:
        texto = self.nota_var.get().strip().replace(",", ".")

        if not texto:
            self._mensaje("Escribe una nota antes de agregarla.", "error")
            self.entrada_nota.focus_set()
            return "break"

        try:
            nota = validar_nota(float(texto))
        except ValueError as error:
            self._mensaje(str(error), "error")
            self.bell()
            self.entrada_nota.focus_set()
            self.entrada_nota.select_range(0, "end")
            return "break"

        self.notas.append(nota)
        self.nota_var.set("")
        self._actualizar_notas()
        self._mensaje(f"Nota {nota:.2f} agregada.", "ok")
        self.entrada_nota.focus_set()
        return "break"

    def _eliminar_nota(self) -> None:
        seleccion = self.lista_notas.curselection()

        if not seleccion:
            self._mensaje("Selecciona al menos una nota de la lista para eliminarla.", "error")
            return

        for indice in reversed(seleccion):
            del self.notas[indice]

        self._actualizar_notas()
        self._mensaje("Nota(s) eliminada(s).", "ok")

    def _limpiar_notas(self) -> None:
        if not self.notas:
            self._mensaje("No hay notas para limpiar.", "error")
            return

        self.notas.clear()
        self._actualizar_notas()
        self._mensaje("Se eliminaron todas las notas del formulario.", "ok")

    def _actualizar_notas(self) -> None:
        self.lista_notas.delete(0, "end")
        for nota in self.notas:
            self.lista_notas.insert("end", f"{nota:.2f}")

        self._actualizar_resultado()

    def _actualizar_resultado(self) -> None:
        if not self.notas:
            self.lbl_promedio.configure(text="—")
            self.lbl_detalle.configure(text="Agrega al menos una nota para calcular el promedio.")
            self.lbl_estado.configure(text="SIN NOTAS", bg=GRIS_FONDO, fg=TEXTO_SUAVE)
            return

        promedio = calcular_promedio(self.notas)
        estado = determinar_estado(promedio)

        self.lbl_promedio.configure(text=f"{promedio:.2f}")
        self.lbl_detalle.configure(
            text=(
                f"{len(self.notas)} nota(s) registrada(s) · "
                f"Mínimo para aprobar: {NOTA_APROBACION:.1f}"
            )
        )

        if estado == "APROBADO":
            self.lbl_estado.configure(text="● APROBADO", bg=VERDE_FONDO, fg=VERDE)
        else:
            self.lbl_estado.configure(text="● REPROBADO", bg=ROJO_FONDO, fg=ROJO)

    def _guardar_estudiante(self) -> None:
        nombre = self.nombre_var.get().strip()

        if not nombre:
            self._mensaje("Escribe el nombre del estudiante.", "error")
            self.entrada_nombre.focus_set()
            return

        if not self.notas:
            self._mensaje("Agrega al menos una nota antes de guardar.", "error")
            self.entrada_nota.focus_set()
            return

        try:
            estudiante = Estudiante(nombre=nombre, notas=list(self.notas))
        except ValueError as error:
            self._mensaje(str(error), "error")
            return

        if self.indice_edicion is None:
            self.historial.agregar(estudiante)
            mensaje = f"Estudiante '{nombre}' guardado en el historial."
        else:
            self.historial.reemplazar(self.indice_edicion, estudiante)
            mensaje = f"Estudiante '{nombre}' actualizado."

        try:
            self.historial.guardar()
        except ErrorHistorial as error:
            messagebox.showerror("No se pudo guardar", str(error), parent=self)
            self._mensaje("No se pudo escribir el archivo del historial.", "error")
        else:
            self._mensaje(mensaje, "ok")

        self._refrescar_historial()
        self._reiniciar_formulario()

    def _cargar_seleccionado(self, evento: tk.Event | None = None) -> None:
        seleccion = self.arbol.selection()

        if not seleccion:
            self._mensaje("Selecciona un estudiante del historial para cargarlo.", "error")
            return

        indice = int(seleccion[0])
        estudiante = self.historial[indice]

        self.nombre_var.set(estudiante.nombre)
        self.notas = list(estudiante.notas)
        self.indice_edicion = indice
        self.boton_guardar.configure(text="Actualizar estudiante")
        self._actualizar_notas()
        self._mensaje(
            f"Editando a '{estudiante.nombre}'. Los cambios se guardan con "
            "'Actualizar estudiante'.",
            "info",
        )

    def _eliminar_del_historial(self) -> None:
        seleccion = self.arbol.selection()

        if not seleccion:
            self._mensaje("Selecciona un estudiante del historial para eliminarlo.", "error")
            return

        indice = int(seleccion[0])
        estudiante = self.historial[indice]

        if not messagebox.askyesno(
            "Eliminar estudiante",
            f"¿Eliminar a '{estudiante.nombre}' del historial?",
            parent=self,
        ):
            return

        self.historial.eliminar(indice)

        # Mantiene coherente la edición si se borran elementos de la lista.
        if self.indice_edicion == indice:
            self._reiniciar_formulario()
        elif self.indice_edicion is not None and self.indice_edicion > indice:
            self.indice_edicion -= 1

        try:
            self.historial.guardar()
        except ErrorHistorial as error:
            messagebox.showerror("No se pudo guardar", str(error), parent=self)
            self._mensaje("Se eliminó en memoria, pero no se pudo escribir el archivo.", "error")
        else:
            self._mensaje(f"Estudiante '{estudiante.nombre}' eliminado del historial.", "ok")

        self._refrescar_historial()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _reiniciar_formulario(self) -> None:
        self.nombre_var.set("")
        self.nota_var.set("")
        self.notas = []
        self.indice_edicion = None
        self.boton_guardar.configure(text="Guardar estudiante")
        self._actualizar_notas()
        self.entrada_nombre.focus_set()

    def _mensaje(self, texto: str, tipo: str = "info") -> None:
        colores = {"info": TEXTO_SUAVE, "ok": VERDE, "error": ROJO}
        self.estado_var.set(texto)
        self.barra_estado.configure(fg=colores.get(tipo, TEXTO_SUAVE))


def iniciar_aplicacion() -> None:
    """Crea la ventana principal y ejecuta el bucle de eventos de Tkinter."""
    aplicacion = Aplicacion()
    aplicacion.mainloop()
