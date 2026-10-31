"""Sistema visual institucional de la aplicación de escritorio 3.0."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

AZUL = "#0B2545"
AZUL_MEDIO = "#13315C"
AZUL_CLARO = "#1B3A63"
DORADO = "#C9A227"
DORADO_CLARO = "#E7CE7A"
FONDO = "#F4F6F8"
BLANCO = "#FFFFFF"
GRIS_BORDE = "#DDE3E9"
GRIS_TEXTO = "#5B6770"
GRIS_SUAVE = "#EEF1F4"
TEXTO = "#1F2933"
VERDE = "#1E7F4F"
VERDE_SUAVE = "#E6F4EC"
ROJO = "#B3261E"
ROJO_SUAVE = "#FBEAE8"
AMARILLO_SUAVE = "#FFF6DA"

FUENTE = "Segoe UI"
FUENTE_TITULO = "Segoe UI Semibold"


def configurar_estilos(raiz: tk.Misc) -> ttk.Style:
    """Configura ttk con la paleta institucional azul marino y dorado."""
    estilo = ttk.Style(raiz)
    try:
        estilo.theme_use("clam")
    except tk.TclError:  # pragma: no cover - tema no disponible
        pass

    raiz.option_add("*Font", (FUENTE, 10))
    raiz.option_add("*Background", FONDO)
    raiz.option_add("*Foreground", TEXTO)

    estilo.configure("TFrame", background=FONDO)
    estilo.configure("Contenido.TFrame", background=FONDO)
    estilo.configure("Blanco.TFrame", background=BLANCO)
    estilo.configure("Sidebar.TFrame", background=AZUL)

    estilo.configure(
        "H1.TLabel",
        background=FONDO,
        foreground=AZUL,
        font=(FUENTE_TITULO, 22, "bold"),
    )
    estilo.configure(
        "H2.TLabel",
        background=FONDO,
        foreground=AZUL,
        font=(FUENTE_TITULO, 14, "bold"),
    )
    estilo.configure(
        "Sub.TLabel",
        background=FONDO,
        foreground=GRIS_TEXTO,
        font=(FUENTE, 10),
    )
    estilo.configure(
        "Seccion.TLabel",
        background=FONDO,
        foreground=AZUL,
        font=(FUENTE_TITULO, 12, "bold"),
    )
    estilo.configure(
        "Campo.TLabel",
        background=FONDO,
        foreground=GRIS_TEXTO,
        font=(FUENTE, 9, "bold"),
    )
    estilo.configure(
        "Blanco.TLabel", background=BLANCO, foreground=TEXTO, font=(FUENTE, 10)
    )
    estilo.configure(
        "BlancoFuerte.TLabel",
        background=BLANCO,
        foreground=AZUL,
        font=(FUENTE_TITULO, 11, "bold"),
    )

    estilo.configure(
        "Primary.TButton",
        background=AZUL,
        foreground=BLANCO,
        borderwidth=0,
        focusthickness=0,
        padding=(16, 9),
        font=(FUENTE, 10, "bold"),
    )
    estilo.map(
        "Primary.TButton",
        background=[("active", AZUL_CLARO), ("disabled", GRIS_BORDE)],
        foreground=[("disabled", GRIS_TEXTO)],
    )
    estilo.configure(
        "Gold.TButton",
        background=DORADO,
        foreground=AZUL,
        borderwidth=0,
        focusthickness=0,
        padding=(16, 9),
        font=(FUENTE, 10, "bold"),
    )
    estilo.map(
        "Gold.TButton",
        background=[("active", DORADO_CLARO), ("disabled", GRIS_BORDE)],
    )
    estilo.configure(
        "Secondary.TButton",
        background=BLANCO,
        foreground=AZUL,
        borderwidth=1,
        relief="solid",
        padding=(14, 8),
        font=(FUENTE, 10),
    )
    estilo.map(
        "Secondary.TButton",
        background=[("active", GRIS_SUAVE)],
        bordercolor=[("focus", DORADO)],
    )
    estilo.configure(
        "Danger.TButton",
        background=ROJO_SUAVE,
        foreground=ROJO,
        borderwidth=0,
        padding=(14, 8),
        font=(FUENTE, 10, "bold"),
    )
    estilo.map("Danger.TButton", background=[("active", "#F5D7D4")])

    estilo.configure(
        "TEntry",
        fieldbackground=BLANCO,
        foreground=TEXTO,
        bordercolor=GRIS_BORDE,
        lightcolor=GRIS_BORDE,
        darkcolor=GRIS_BORDE,
        padding=7,
    )
    estilo.map("TEntry", bordercolor=[("focus", DORADO)])

    estilo.configure(
        "TCombobox",
        fieldbackground=BLANCO,
        background=BLANCO,
        foreground=TEXTO,
        bordercolor=GRIS_BORDE,
        arrowcolor=AZUL,
        padding=6,
    )
    estilo.map(
        "TCombobox",
        bordercolor=[("focus", DORADO)],
        fieldbackground=[("readonly", BLANCO)],
        foreground=[("readonly", TEXTO)],
    )

    estilo.configure(
        "Academica.Treeview",
        background=BLANCO,
        fieldbackground=BLANCO,
        foreground=TEXTO,
        rowheight=32,
        borderwidth=0,
        font=(FUENTE, 10),
    )
    estilo.map(
        "Academica.Treeview",
        background=[("selected", DORADO_CLARO)],
        foreground=[("selected", AZUL)],
    )
    estilo.configure(
        "Academica.Treeview.Heading",
        background=AZUL,
        foreground=BLANCO,
        relief="flat",
        padding=(8, 9),
        font=(FUENTE, 9, "bold"),
    )
    estilo.map(
        "Academica.Treeview.Heading",
        background=[("active", AZUL_MEDIO)],
    )

    estilo.configure(
        "Vertical.TScrollbar",
        background=GRIS_SUAVE,
        troughcolor=BLANCO,
        bordercolor=BLANCO,
        arrowcolor=GRIS_TEXTO,
    )

    estilo.configure(
        "TCheckbutton",
        background=BLANCO,
        foreground=TEXTO,
        font=(FUENTE, 10),
    )
    estilo.map("TCheckbutton", background=[("active", BLANCO)])

    return estilo
