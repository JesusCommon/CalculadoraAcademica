"""Componentes visuales reutilizables de la interfaz Tkinter 3.0."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Iterable, Sequence

from app.escritorio.estilos import (
    AZUL,
    AZUL_CLARO,
    AZUL_MEDIO,
    BLANCO,
    DORADO,
    DORADO_CLARO,
    FONDO,
    FUENTE,
    FUENTE_TITULO,
    GRIS_BORDE,
    GRIS_SUAVE,
    GRIS_TEXTO,
    ROJO,
    TEXTO,
    VERDE,
)


def formatear_promedio(valor: float | None) -> str:
    """Formatea un promedio para las tablas y tarjetas."""
    return "—" if valor is None else f"{valor:.2f}"


def etiqueta_estado(estado: str) -> str:
    return {"APROBADO": "Aprobado", "REPROBADO": "Reprobado"}.get(
        estado, "Sin notas"
    )


def estilo_estado(estado: str) -> str:
    return {
        "APROBADO": "aprobado",
        "REPROBADO": "reprobado",
    }.get(estado, "sin_notas")


def confirmar(maestro: tk.Misc, titulo: str, mensaje: str) -> bool:
    return messagebox.askyesno(titulo, mensaje, parent=maestro, icon="warning")


def avisar_error(maestro: tk.Misc, error: object) -> None:
    messagebox.showerror("No se pudo completar", str(error), parent=maestro)


def avisar_info(maestro: tk.Misc, mensaje: str, titulo: str = "Listo") -> None:
    messagebox.showinfo(titulo, mensaje, parent=maestro)


class Tarjeta(tk.Frame):
    """Tarjeta estadística con acento lateral institucional."""

    def __init__(
        self,
        maestro: tk.Misc,
        titulo: str,
        valor: str = "—",
        pista: str = "",
        acento: str = DORADO,
    ) -> None:
        super().__init__(
            maestro,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        self.acento = tk.Frame(self, bg=acento, width=5)
        self.acento.pack(side="left", fill="y")

        cuerpo = tk.Frame(self, bg=BLANCO)
        cuerpo.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        self.titulo = tk.Label(
            cuerpo,
            text=titulo.upper(),
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        )
        self.titulo.pack(fill="x")

        self.valor = tk.Label(
            cuerpo,
            text=valor,
            bg=BLANCO,
            fg=AZUL,
            font=(FUENTE_TITULO, 25, "bold"),
            anchor="w",
        )
        self.valor.pack(fill="x", pady=(2, 0))

        self.pista = tk.Label(
            cuerpo,
            text=pista,
            bg=BLANCO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8),
            anchor="w",
        )
        self.pista.pack(fill="x")

    def actualizar(self, valor: str, pista: str | None = None) -> None:
        self.valor.configure(text=valor)
        if pista is not None:
            self.pista.configure(text=pista)


class Tabla(tk.Frame):
    """Tabla Treeview con estilo académico y acceso a los objetos de fila."""

    def __init__(
        self,
        maestro: tk.Misc,
        columnas: Sequence[tuple[str, str, int, str]],
        altura: int = 10,
    ) -> None:
        super().__init__(
            maestro,
            bg=BLANCO,
            highlightbackground=GRIS_BORDE,
            highlightthickness=1,
        )
        self._objetos: dict[str, object] = {}
        claves = [columna[0] for columna in columnas]

        self.tabla = ttk.Treeview(
            self,
            columns=claves,
            show="headings",
            style="Academica.Treeview",
            height=altura,
            selectmode="browse",
        )
        for clave, titulo, ancho, anclaje in columnas:
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, anchor=anclaje, stretch=True)

        barra = ttk.Scrollbar(
            self, orient="vertical", command=self.tabla.yview, style="Vertical.TScrollbar"
        )
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.tabla.tag_configure("aprobado", foreground=VERDE)
        self.tabla.tag_configure("reprobado", foreground=ROJO)
        self.tabla.tag_configure("sin_notas", foreground=GRIS_TEXTO)
        self.tabla.tag_configure("par", background="#FAFBFC")

    def cargar(self, filas: Iterable[dict[str, object]]) -> None:
        self.limpiar()
        for indice, fila in enumerate(filas):
            iid = str(fila.get("iid", indice))
            etiquetas = tuple(fila.get("tags", ()))
            if indice % 2 and "par" not in etiquetas:
                etiquetas = (*etiquetas, "par")
            self.tabla.insert(
                "",
                "end",
                iid=iid,
                values=tuple(fila.get("valores", ())),
                tags=etiquetas,
            )
            if "datos" in fila:
                self._objetos[iid] = fila["datos"]

    def limpiar(self) -> None:
        for iid in self.tabla.get_children():
            self.tabla.delete(iid)
        self._objetos.clear()

    def seleccion(self) -> str | None:
        seleccion = self.tabla.selection()
        return seleccion[0] if seleccion else None

    def objeto_seleccionado(self) -> object | None:
        iid = self.seleccion()
        return self._objetos.get(iid) if iid else None

    def total(self) -> int:
        return len(self.tabla.get_children())


class GraficoBarras(tk.Canvas):
    """Gráfico horizontal de barras dibujado con Canvas (sin dependencias)."""

    def __init__(self, maestro: tk.Misc, alto: int = 240) -> None:
        super().__init__(
            maestro, bg=BLANCO, highlightthickness=0, height=alto
        )
        self._datos: list[tuple[str, float]] = []
        self._maximo: float | None = None
        self._formato = "{:.2f}"
        self.bind("<Configure>", lambda _evento: self._redibujar())

    def dibujar(
        self,
        datos: Iterable[object],
        *,
        maximo: float | None = None,
        formato: str = "{:.2f}",
    ) -> None:
        normalizados: list[tuple[str, float]] = []
        for dato in datos:
            if hasattr(dato, "etiqueta") and hasattr(dato, "valor"):
                normalizados.append((str(dato.etiqueta), float(dato.valor)))
            else:
                etiqueta, valor = dato
                normalizados.append((str(etiqueta), float(valor)))
        self._datos = normalizados
        self._maximo = maximo
        self._formato = formato
        self._redibujar()

    def _redibujar(self) -> None:
        self.delete("all")
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho <= 2 or alto <= 2:
            return

        if not self._datos:
            self.create_text(
                ancho / 2,
                alto / 2,
                text="Sin datos para mostrar",
                fill=GRIS_TEXTO,
                font=(FUENTE, 10),
            )
            return

        margen = 14
        etiqueta_ancho = min(190, max(110, int(ancho * 0.30)))
        valor_ancho = 58
        inicio_barra = margen + etiqueta_ancho + 12
        fin_barra = ancho - margen - valor_ancho
        alto_util = alto - margen * 2
        filas = len(self._datos)
        alto_fila = max(24, min(46, alto_util / filas))
        alto_barra = max(9, min(18, alto_fila * 0.45))

        maximo = self._maximo or max((valor for _, valor in self._datos), default=0)
        if maximo <= 0:
            maximo = 1.0

        for indice, (etiqueta, valor) in enumerate(self._datos):
            centro_y = margen + alto_fila * indice + alto_fila / 2
            texto = etiqueta
            if len(texto) > 26:
                texto = texto[:25] + "…"
            self.create_text(
                margen + etiqueta_ancho,
                centro_y,
                text=texto,
                anchor="e",
                fill=TEXTO,
                font=(FUENTE, 9),
            )
            # Fondo de la barra
            self.create_rectangle(
                inicio_barra,
                centro_y - alto_barra / 2,
                fin_barra,
                centro_y + alto_barra / 2,
                fill=GRIS_SUAVE,
                outline="",
            )
            ancho_valor = max(2, (fin_barra - inicio_barra) * (valor / maximo))
            self.create_rectangle(
                inicio_barra,
                centro_y - alto_barra / 2,
                inicio_barra + ancho_valor,
                centro_y + alto_barra / 2,
                fill=DORADO if indice % 2 == 0 else AZUL_MEDIO,
                outline="",
            )
            self.create_text(
                fin_barra + 8,
                centro_y,
                text=self._formato.format(valor),
                anchor="w",
                fill=AZUL,
                font=(FUENTE, 9, "bold"),
            )


class GraficoDonut(tk.Canvas):
    """Dona de distribución con leyenda, dibujada con Canvas."""

    def __init__(self, maestro: tk.Misc, alto: int = 220) -> None:
        super().__init__(
            maestro, bg=BLANCO, highlightthickness=0, height=alto
        )
        self._segmentos: list[tuple[str, int, str]] = []
        self.bind("<Configure>", lambda _evento: self._redibujar())

    def dibujar(self, segmentos: Iterable[tuple[str, int, str]]) -> None:
        self._segmentos = [(str(a), int(b), str(c)) for a, b, c in segmentos]
        self._redibujar()

    def _redibujar(self) -> None:
        self.delete("all")
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho <= 2 or alto <= 2:
            return

        total = sum(cantidad for _, cantidad, _ in self._segmentos)
        centro_x = min(105, ancho * 0.30)
        centro_y = alto / 2
        radio = min(72, (alto - 36) / 2)
        grosor = 22

        caja = (
            centro_x - radio,
            centro_y - radio,
            centro_x + radio,
            centro_y + radio,
        )

        if total <= 0:
            self.create_oval(*caja, outline=GRIS_SUAVE, width=grosor)
        else:
            inicio = 90.0
            for _etiqueta, cantidad, color in self._segmentos:
                if cantidad <= 0:
                    continue
                extension = -360.0 * cantidad / total
                self.create_arc(
                    *caja,
                    start=inicio,
                    extent=extension,
                    style="arc",
                    outline=color,
                    width=grosor,
                )
                inicio += extension

        self.create_text(
            centro_x,
            centro_y - 8,
            text=str(total),
            fill=AZUL,
            font=(FUENTE_TITULO, 22, "bold"),
        )
        self.create_text(
            centro_x,
            centro_y + 15,
            text="calificaciones",
            fill=GRIS_TEXTO,
            font=(FUENTE, 8),
        )

        leyenda_x = centro_x + radio + 34
        inicio_y = centro_y - (len(self._segmentos) * 28) / 2 + 14
        for indice, (etiqueta, cantidad, color) in enumerate(self._segmentos):
            y = inicio_y + indice * 28
            self.create_rectangle(
                leyenda_x, y - 6, leyenda_x + 12, y + 6, fill=color, outline=""
            )
            self.create_text(
                leyenda_x + 20,
                y,
                text=f"{etiqueta}  ·  {cantidad}",
                anchor="w",
                fill=TEXTO,
                font=(FUENTE, 9),
            )


class BotonNavegacion(tk.Frame):
    """Botón de la barra lateral con indicador dorado de sección activa."""

    def __init__(
        self,
        maestro: tk.Misc,
        icono: str,
        texto: str,
        comando: Callable[[], None],
    ) -> None:
        super().__init__(maestro, bg=AZUL, cursor="hand2")
        self._activo = False

        self.indicador = tk.Frame(self, bg=AZUL, width=4)
        self.indicador.pack(side="left", fill="y")

        self.boton = tk.Button(
            self,
            text=f"  {icono}   {texto}",
            command=comando,
            bg=AZUL,
            fg="#C9D1DB",
            activebackground=AZUL_CLARO,
            activeforeground=BLANCO,
            bd=0,
            relief="flat",
            anchor="w",
            padx=14,
            pady=11,
            font=(FUENTE, 10),
            cursor="hand2",
            highlightthickness=0,
        )
        self.boton.pack(side="left", fill="both", expand=True)

        for widget in (self, self.boton):
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._salir)

    def _entrar(self, _evento: object = None) -> None:
        if not self._activo:
            self.configure(bg=AZUL_CLARO)
            self.boton.configure(bg=AZUL_CLARO, fg=BLANCO)
            self.indicador.configure(bg=AZUL_CLARO)

    def _salir(self, _evento: object = None) -> None:
        if not self._activo:
            self.configure(bg=AZUL)
            self.boton.configure(bg=AZUL, fg="#C9D1DB")
            self.indicador.configure(bg=AZUL)

    def seleccionar(self, activo: bool) -> None:
        self._activo = activo
        color = AZUL_CLARO if activo else AZUL
        self.configure(bg=color)
        self.boton.configure(bg=color, fg=BLANCO if activo else "#C9D1DB")
        self.indicador.configure(bg=DORADO if activo else color)


class ModalFormulario(tk.Toplevel):
    """Ventana modal con encabezado institucional y formulario simple."""

    def __init__(
        self,
        maestro: tk.Misc,
        titulo: str,
        subtitulo: str = "",
        *,
        ancho: int = 480,
        alto: int = 460,
    ) -> None:
        super().__init__(maestro)
        self.title(titulo)
        self.configure(bg=FONDO)
        self.resizable(False, False)
        self.transient(maestro)
        self._ancho = ancho
        self._alto = alto

        encabezado = tk.Frame(self, bg=AZUL, height=78)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Frame(encabezado, bg=DORADO, width=5).pack(side="left", fill="y")
        textos = tk.Frame(encabezado, bg=AZUL)
        textos.pack(side="left", fill="both", expand=True, padx=18, pady=12)
        tk.Label(
            textos,
            text=titulo,
            bg=AZUL,
            fg=BLANCO,
            font=(FUENTE_TITULO, 14, "bold"),
            anchor="w",
        ).pack(fill="x")
        if subtitulo:
            tk.Label(
                textos,
                text=subtitulo,
                bg=AZUL,
                fg="#C9D1DB",
                font=(FUENTE, 9),
                anchor="w",
            ).pack(fill="x")

        self.cuerpo = tk.Frame(self, bg=FONDO)
        self.cuerpo.pack(fill="both", expand=True, padx=22, pady=16)

        self.pie = tk.Frame(self, bg=FONDO)
        self.pie.pack(fill="x", padx=22, pady=(0, 18))

        self._centrar()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _centrar(self) -> None:
        self.update_idletasks()
        maestro = self.master
        try:
            x = maestro.winfo_rootx() + (maestro.winfo_width() - self._ancho) // 2
            y = maestro.winfo_rooty() + (maestro.winfo_height() - self._alto) // 3
        except tk.TclError:  # pragma: no cover
            x = y = 120
        self.geometry(f"{self._ancho}x{self._alto}+{max(x, 0)}+{max(y, 0)}")

    def campo(self, etiqueta: str, valor: str = "", *, mostrar: str | None = None) -> tk.Entry:
        tk.Label(
            self.cuerpo,
            text=etiqueta.upper(),
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 3))
        entrada = tk.Entry(
            self.cuerpo,
            bg=BLANCO,
            fg=TEXTO,
            relief="flat",
            highlightthickness=1,
            highlightbackground=GRIS_BORDE,
            highlightcolor=DORADO,
            font=(FUENTE, 10),
            insertbackground=AZUL,
            show=mostrar or "",
        )
        entrada.insert(0, valor)
        entrada.pack(fill="x", ipady=6, pady=(0, 8))
        return entrada

    def combo(
        self,
        etiqueta: str,
        valores: Sequence[str],
        valor: str = "",
    ) -> ttk.Combobox:
        tk.Label(
            self.cuerpo,
            text=etiqueta.upper(),
            bg=FONDO,
            fg=GRIS_TEXTO,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 3))
        combinado = ttk.Combobox(
            self.cuerpo,
            values=list(valores),
            state="readonly",
            font=(FUENTE, 10),
        )
        if valor:
            combinado.set(valor)
        combinado.pack(fill="x", pady=(0, 8))
        return combinado

    def casilla(self, texto: str, valor: bool = True) -> tk.BooleanVar:
        variable = tk.BooleanVar(value=valor)
        ttk.Checkbutton(
            self.cuerpo,
            text=texto,
            variable=variable,
            style="TCheckbutton",
        ).pack(anchor="w", pady=(2, 10))
        return variable

    def botones(
        self, guardar: Callable[[], None], texto: str = "Guardar"
    ) -> None:
        ttk.Button(
            self.pie,
            text="Cancelar",
            style="Secondary.TButton",
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            self.pie,
            text=texto,
            style="Primary.TButton",
            command=guardar,
        ).pack(side="right")
