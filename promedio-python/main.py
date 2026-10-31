"""Punto de entrada de la Calculadora Académica 3.0.

Modos disponibles:

* Sin argumentos: interfaz de escritorio Tkinter 3.0 (predeterminada).
* ``--clasica``: interfaz Tkinter 2.0, conservada durante la transición.
* ``--web``: aplicación web local en http://127.0.0.1:8000.
* ``--consola``: flujo de consola de la versión 2.0.
* ``--migrar-json``: migración del JSON original a SQLite (no lo modifica).

Todas las interfaces comparten los mismos servicios y la misma base SQLite.
"""

from __future__ import annotations

import sys


def _valor_opcion(argumentos: list[str], nombre: str, predeterminado: str) -> str:
    """Lee ``--opcion valor`` o ``--opcion=valor`` de la línea de comandos."""
    for indice, argumento in enumerate(argumentos):
        if argumento == nombre and indice + 1 < len(argumentos):
            return argumentos[indice + 1]
        if argumento.startswith(f"{nombre}="):
            return argumento.split("=", 1)[1]
    return predeterminado


def main() -> None:
    """Inicia la interfaz seleccionada por el usuario."""
    argumentos = sys.argv[1:]

    if "--migrar-json" in argumentos:
        # La CLI de migración es independiente de Tkinter y conserva el JSON.
        from app.database.migrar_json import main as migrar_json

        resto = [
            argumento
            for argumento in argumentos
            if argumento != "--migrar-json"
        ]
        raise SystemExit(migrar_json(resto))

    if "--web" in argumentos:
        _iniciar_web(argumentos)
        return

    if "--consola" in argumentos:
        try:
            from app.promedio import ejecutar
        except ImportError:  # pragma: no cover - consola siempre disponible
            from app.core.promedio import ejecutar  # type: ignore[no-redef]

        try:
            ejecutar()
        except (KeyboardInterrupt, EOFError):
            print("\nPrograma cancelado.")
        return

    try:
        if "--clasica" in argumentos:
            # Importación diferida: la interfaz 2.0 sigue disponible.
            from app.interfaz import iniciar_aplicacion as iniciar_clasica

            iniciar_clasica()
        else:
            # Interfaz 3.0: dashboard, servicios compartidos y SQLite.
            from app.escritorio import iniciar_aplicacion

            iniciar_aplicacion()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma cancelado.")


def _iniciar_web(argumentos: list[str]) -> None:
    """Arranca Uvicorn escuchando exclusivamente en 127.0.0.1."""
    try:
        import uvicorn
    except ImportError as error:  # pragma: no cover - depende del entorno
        raise SystemExit(
            "Faltan dependencias web. Instala con: "
            "python -m pip install fastapi 'uvicorn[standard]' jinja2 "
            "python-multipart httpx openpyxl reportlab"
        ) from error

    from app.web.servidor import crear_app

    puerto = int(_valor_opcion(argumentos, "--puerto", "8000"))
    print(f"Calculadora Académica 3.0 · web local en http://127.0.0.1:{puerto}")
    print("Pulsa Ctrl+C para detener el servidor.")
    uvicorn.run(
        crear_app(),
        host="127.0.0.1",
        port=puerto,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
