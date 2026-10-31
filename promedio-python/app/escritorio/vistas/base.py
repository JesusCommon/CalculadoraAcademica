"""Vista base de la interfaz de escritorio 3.0."""

from __future__ import annotations

import tkinter as tk

from app.escritorio.estilos import FONDO


class VistaBase(tk.Frame):
    """Frame de contenido con título y refresco bajo demanda."""

    titulo = "Sección"
    subtitulo = ""

    def __init__(self, maestro: tk.Misc, aplicacion) -> None:
        super().__init__(maestro, bg=FONDO)
        self.app = aplicacion
        self.construir()

    def construir(self) -> None:  # pragma: no cover - implementado por vistas
        raise NotImplementedError

    def al_mostrar(self) -> None:
        """Se invoca cada vez que la sección pasa a primer plano."""
