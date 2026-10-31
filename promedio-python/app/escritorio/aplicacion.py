"""Interfaz de escritorio de la Calculadora Académica 3.0."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from app.escritorio.estilos import (
    AZUL,
    BLANCO,
    DORADO,
    FONDO,
    FUENTE,
    FUENTE_TITULO,
    GRIS_BORDE,
    GRIS_TEXTO,
    VERDE,
    configurar_estilos,
)
from app.escritorio.widgets import BotonNavegacion, avisar_error
from app.escritorio.vistas.calificaciones import VistaCalificaciones
from app.escritorio.vistas.configuracion import VistaConfiguracion
from app.escritorio.vistas.dashboard import VistaDashboard
from app.escritorio.vistas.estadisticas import VistaEstadisticas
from app.escritorio.vistas.estudiantes import VistaEstudiantes
from app.escritorio.vistas.historial import VistaHistorial
from app.escritorio.vistas.materias import VistaMaterias

SECCIONES = [
    ("dashboard", "◈", "Dashboard", VistaDashboard),
    ("estudiantes", "▤", "Estudiantes", VistaEstudiantes),
    ("materias", "▦", "Materias", VistaMaterias),
    ("calificaciones", "✎", "Calificaciones", VistaCalificaciones),
    ("historial", "◷", "Historial", VistaHistorial),
    ("estadisticas", "◔", "Estadísticas", VistaEstadisticas),
    ("configuracion", "⚙", "Configuración", VistaConfiguracion),
]


class Aplicacion(tk.Tk):
    """Ventana principal con barra lateral y panel de contenido."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Calculadora Académica 3.0")
        self.geometry("1380x880")
        self.minsize(1160, 720)
        self.configure(bg=FONDO)
        configurar_estilos(self)

        self._vistas: dict[str, object] = {}
        self._botones: dict[str, BotonNavegacion] = {}
        self._seccion_actual = ""

        self._construir()
        self.mostrar("dashboard")

        self.bind("<Control-r>", lambda _evento: self.refrescar_actual())
        self.bind("<F5>", lambda _evento: self.refrescar_actual())

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _construir(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_barra_lateral()

        contenido = tk.Frame(self, bg=FONDO)
        contenido.grid(row=0, column=1, sticky="nsew")
        contenido.grid_columnconfigure(0, weight=1)
        contenido.grid_rowconfigure(1, weight=1)

        self._construir_encabezado(contenido)

        self.contenedor = tk.Frame(contenido, bg=FONDO)
        self.contenedor.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

    def _construir_barra_lateral(self) -> None:
        barra = tk.Frame(self, bg=AZUL, width=250)
        barra.grid(row=0, column=0, sticky="ns")
        barra.grid_propagate(False)

        marca = tk.Frame(barra, bg=AZUL)
        marca.pack(fill="x", padx=20, pady=(24, 22))

        escudo = tk.Frame(marca, bg=DORADO, width=38, height=38)
        escudo.pack(side="left")
        escudo.pack_propagate(False)
        tk.Label(
            escudo,
            text="A",
            bg=DORADO,
            fg=AZUL,
            font=(FUENTE_TITULO, 18, "bold"),
        ).pack(expand=True)

        textos = tk.Frame(marca, bg=AZUL)
        textos.pack(side="left", padx=10)
        tk.Label(
            textos,
            text="ACADEMIA",
            bg=AZUL,
            fg=BLANCO,
            font=(FUENTE_TITULO, 13, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            textos,
            text="3.0 · Gestión académica",
            bg=AZUL,
            fg="#9FB0C6",
            font=(FUENTE, 8),
            anchor="w",
        ).pack(fill="x")

        tk.Frame(barra, bg="#23405F", height=1).pack(fill="x", padx=18, pady=(0, 12))
        tk.Label(
            barra,
            text="MENÚ PRINCIPAL",
            bg=AZUL,
            fg="#7F93AB",
            font=(FUENTE, 7, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 8))

        for clave, icono, texto, _vista in SECCIONES:
            boton = BotonNavegacion(
                barra,
                icono,
                texto,
                lambda nombre=clave: self.mostrar(nombre),
            )
            boton.pack(fill="x", padx=0, pady=1)
            self._botones[clave] = boton

        pie = tk.Frame(barra, bg=AZUL)
        pie.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Frame(pie, bg="#23405F", height=1).pack(fill="x", pady=(0, 14))
        tk.Label(
            pie,
            text="●  SQLite local",
            bg=AZUL,
            fg="#7FD1A4",
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            pie,
            text="Datos compartidos con la web",
            bg=AZUL,
            fg="#9FB0C6",
            font=(FUENTE, 8),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

    def _construir_encabezado(self, maestro: tk.Misc) -> None:
        encabezado = tk.Frame(
            maestro,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        encabezado.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        encabezado.grid_columnconfigure(0, weight=1)

        textos = tk.Frame(encabezado, bg=BLANCO)
        textos.grid(row=0, column=0, sticky="w", padx=20, pady=13)

        self.titulo_seccion = tk.Label(
            textos,
            text="",
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 17, "bold"),
            anchor="w",
        )
        self.titulo_seccion.pack(fill="x")
        self.subtitulo_seccion = tk.Label(
            textos,
            text="",
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
            anchor="w",
        )
        self.subtitulo_seccion.pack(fill="x")

        acciones = tk.Frame(encabezado, bg=BLANCO)
        acciones.grid(row=0, column=1, sticky="e", padx=20)

        self.fecha = tk.Label(
            acciones,
            text=datetime.now().strftime("%d/%m/%Y"),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 9),
        )
        self.fecha.pack(side="left", padx=(0, 16))

        boton = tk.Button(
            acciones,
            text="↻  Actualizar",
            command=self.refrescar_actual,
            bg=BLANCO,
            fg=AZUL,
            activebackground="#EEF1F4",
            activeforeground=AZUL,
            bd=0,
            relief="flat",
            font=(FUENTE, 9, "bold"),
            padx=12,
            pady=7,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
        )
        boton.pack(side="left")

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def mostrar(self, clave: str) -> None:
        if clave not in dict((c[0], c) for c in SECCIONES):
            return

        vista = self._vistas.get(clave)
        if vista is None:
            definicion = next(seccion for seccion in SECCIONES if seccion[0] == clave)
            vista = definicion[3](self.contenedor, self)
            vista.grid(row=0, column=0, sticky="nsew")
            self._vistas[clave] = vista

        vista.tkraise()
        self._seccion_actual = clave

        for nombre, boton in self._botones.items():
            boton.seleccionar(nombre == clave)

        self.titulo_seccion.configure(text=vista.titulo)
        self.subtitulo_seccion.configure(text=vista.subtitulo)

        try:
            vista.al_mostrar()
        except Exception as error:  # pragma: no cover - protección de UI
            avisar_error(self, error)

    def refrescar_actual(self) -> None:
        if not self._seccion_actual:
            return
        try:
            self._vistas[self._seccion_actual].al_mostrar()
        except Exception as error:  # pragma: no cover - protección de UI
            avisar_error(self, error)

    def refrescar_todo(self) -> None:
        """Refresca la sección visible; las demás se actualizan al abrirse."""
        self.refrescar_actual()


def iniciar_aplicacion() -> None:
    aplicacion = Aplicacion()
    aplicacion.mainloop()
