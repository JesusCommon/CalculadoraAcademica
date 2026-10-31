"""CLI de migración del historial JSON 2.0 a SQLite 3.0.

Uso:
    python -m app.database.migrar_json --dry-run
    python -m app.database.migrar_json --aplicar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.errores import ErrorMigracion
from app.services.migracion import MigracionService, ResultadoMigracion

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent
JSON_PREDETERMINADO = RAIZ_PROYECTO / "datos" / "historial.json"
DB_PREDETERMINADA = RAIZ_PROYECTO / "datos" / "academico.db"
BACKUPS_PREDETERMINADOS = RAIZ_PROYECTO / "datos" / "backups"


def _configurar_salida() -> None:
    """Evita fallos de codificación en consolas Windows con página de códigos antigua."""
    for flujo in (sys.stdout, sys.stderr):
        configurar = getattr(flujo, "reconfigure", None)
        if configurar is not None:
            try:
                configurar(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migra el historial JSON de la versión 2.0 a SQLite 3.0."
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--dry-run",
        action="store_true",
        help="Analiza y verifica sin escribir nada (modo por defecto).",
    )
    modo.add_argument(
        "--aplicar",
        action="store_true",
        help="Crea respaldos e importa los datos en SQLite.",
    )
    parser.add_argument("--json", dest="ruta_json", type=Path, default=JSON_PREDETERMINADO)
    parser.add_argument("--db", dest="ruta_db", type=Path, default=DB_PREDETERMINADA)
    parser.add_argument(
        "--backups", dest="backups", type=Path, default=BACKUPS_PREDETERMINADOS
    )
    parser.add_argument(
        "--reporte",
        type=Path,
        default=None,
        help="Ruta opcional para guardar el reporte JSON.",
    )
    return parser


def _formato_promedio(valor: object) -> str:
    return "sin notas" if valor is None else f"{float(valor):.4f}"


def _imprimir(resultado: ResultadoMigracion) -> None:
    modo = "SIMULACIÓN (sin escritura)" if resultado.simulado else "APLICACIÓN"
    print("=" * 64)
    print("MIGRACIÓN JSON 2.0 -> SQLITE 3.0")
    print("=" * 64)
    print(f"Modo: {modo}")
    print(f"Archivo: {resultado.archivo}")
    print(f"SHA-256: {resultado.sha256}")
    print()
    print(f"Registros leídos:      {resultado.total_leidos}")
    print(f"Registros válidos:     {resultado.validos}")
    print(f"Registros inválidos:   {resultado.invalidos}")
    print(f"Duplicados exactos:    {resultado.duplicados}")
    if not resultado.simulado:
        print(f"Estudiantes importados: {resultado.importados}")
        print(f"Notas importadas:       {resultado.calificaciones_importadas}")
    print()

    if resultado.estudiantes:
        print("Estudiantes:")
        for estudiante in resultado.estudiantes:
            codigo = estudiante.get("codigo")
            prefijo = f"[{codigo}] " if codigo else ""
            print(
                f"  - {prefijo}{estudiante['nombre']}: "
                f"{estudiante['cantidad_notas']} nota(s), "
                f"promedio {_formato_promedio(estudiante['promedio'])}, "
                f"{estudiante['estado']}"
            )
        print()

    if resultado.invalidos_detalle:
        print("Registros inválidos omitidos:")
        for item in resultado.invalidos_detalle:
            print(f"  - #{item['indice']} {item['nombre']}: {item['motivo']}")
        print()

    if resultado.duplicados_detalle:
        print("Duplicados omitidos:")
        for item in resultado.duplicados_detalle:
            print(f"  - #{item['indice']} {item['nombre']}: {item['motivo']}")
        print()

    if resultado.posibles_duplicados:
        print("Posibles duplicados para revisión manual:")
        for item in resultado.posibles_duplicados:
            print(f"  - {item['nombre']} (registros {item['registros']})")
        print()

    if resultado.verificacion:
        print("Verificación:")
        for comprobacion in resultado.verificacion:
            print(f"  [OK] {comprobacion}")
        print()

    if resultado.respaldo_json:
        print(f"Respaldo JSON: {resultado.respaldo_json}")
    if resultado.respaldo_bd:
        print(f"Respaldo SQLite: {resultado.respaldo_bd}")
    if resultado.respaldo_json or resultado.respaldo_bd:
        print()

    print(f"Resultado: {resultado.mensaje}")
    if resultado.simulado:
        print("No se creó la base de datos ni se modificó el JSON original.")


def _escribir_reporte(resultado: ResultadoMigracion, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(resultado.a_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    _configurar_salida()
    parser = _crear_parser()
    args = parser.parse_args(argv)

    servicio = MigracionService(
        ruta_json=args.ruta_json,
        ruta_db=args.ruta_db,
        backups_dir=args.backups,
    )

    try:
        resultado = servicio.aplicar() if args.aplicar else servicio.simular()
        if args.reporte:
            _escribir_reporte(resultado, args.reporte)
    except ErrorMigracion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # pragma: no cover - protección del CLI
        print(f"ERROR inesperado: {error}", file=sys.stderr)
        return 1

    _imprimir(resultado)
    return 0 if resultado.correcto else 1


if __name__ == "__main__":
    raise SystemExit(main())
