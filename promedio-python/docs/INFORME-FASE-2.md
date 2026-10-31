# Informe de cierre — Fase 2

**Proyecto:** Calculadora Académica 3.0
**Fase:** 2 — Núcleo, servicios, SQLite y migración
**Fecha:** 30 de octubre de 2026
**Estado:** Completada y verificada

---

## 1. Resumen ejecutivo

La Fase 2 queda completada. La versión 2.0 sigue funcionando sin cambios de
comportamiento (Tkinter y consola operativas), el JSON original permanece
intacto y la nueva base SQLite contiene exactamente los mismos datos
académicos, con promedios equivalentes.

Se construyó una arquitectura por capas —**presentación → servicios → núcleo**—
con puertos de persistencia, de modo que las interfaces de escritorio y web
compartirán las mismas reglas y casos de uso.

| Indicador | Resultado |
|---|---|
| Pruebas automatizadas | **42 OK** (18 de la 2.0 + 24 nuevas) |
| Estudiantes migrados | 2 |
| Calificaciones migradas | 9 |
| Promedios verificados | Manuela 3.6875 · Luisa 2.9000 |
| Integridad SQLite | `ok` |
| Claves foráneas | Sin problemas |
| JSON original | Sin cambios (SHA-256 idéntico) |
| Idempotencia | Verificada |

---

## 2. Alcance entregado

### 2.1 Núcleo académico (`app/core/`)

Dominio puro, sin Tkinter, FastAPI ni SQLite:

- `escala.py`: escala configurable (mínima, máxima, aprobación, decimales).
  La escala predeterminada reproduce la regla 2.0: 0–5 y aprueba desde 3.0.
- `promedio.py`: promedio aritmético, validación de notas y determinación de
  estado.
- `entidades.py`: `Estudiante`, `Materia`, `Periodo`, `Inscripcion`,
  `Calificacion`, `CalificacionDetalle`.
- `errores.py`: `DatosInvalidos`, `NoEncontrado`, `Conflicto`, `ErrorMigracion`.
- `puertos.py`: `Protocol` de repositorios; los servicios no dependen de SQLite.
- `texto.py` y `tiempo.py`: normalización de nombres, fechas e IDs deterministas.

`app/promedio.py` conserva su API pública y constantes, pero delega en el
núcleo. Esto mantiene la compatibilidad con la consola y la GUI 2.0.

### 2.2 Servicios compartidos (`app/services/`)

- **Estudiantes:** alta con código secuencial, búsqueda sin distinguir
  mayúsculas/acentos básicos, edición y baja lógica.
- **Materias:** código único normalizado, créditos y baja lógica.
- **Periodos:** nombre único y **escala propia congelada al crear el periodo**.
- **Configuración:** escala global usada por los periodos nuevos.
- **Calificaciones:** registro contra la escala del periodo, inscripción única
  por estudiante/materia/periodo, anulación lógica y cálculo de promedios.
- **Fábrica:** `crear_servicios(repos)` construye todo sobre una unidad de
  trabajo.

### 2.3 Persistencia SQLite (`app/database/`)

- Conexión con `foreign_keys = ON`, `busy_timeout`, `synchronous = NORMAL` y
  **WAL** (lectura concurrente entre escritorio y web).
- Esquema versionado (`esquema_version`) con `001_inicial.sql`.
- Tablas: `estudiantes`, `materias`, `periodos`, `inscripciones`,
  `calificaciones`, `configuracion`, `migraciones`, `contadores`, además de
  `roles` y `usuarios` preparadas para una fase posterior.
- Índices para búsquedas y consultas activas.
- Repositorios SQLite que implementan los puertos.
- `UnidadDeTrabajo`: una conexión, una transacción (`BEGIN IMMEDIATE`),
  commit/rollback automático y cierre garantizado.
- Siembra inicial: configuración 0–5/3.0, materia `GEN` y periodo
  `Periodo general`.

### 2.4 Migración JSON → SQLite

- Lector tolerante del formato 2.0 (lista directa o clave `estudiantes`).
- Clasificación de registros: válidos, inválidos, duplicados exactos y posibles
  duplicados por nombre.
- Huella canónica por nombre + notas ordenadas para deduplicar.
- **Simulación** (`--dry-run`) que no escribe ni crea archivos.
- **Aplicación** (`--aplicar`) con:
  1. respaldo del JSON y verificación de su SHA-256;
  2. respaldo consistente de SQLite si ya existía;
  3. importación dentro de una única transacción;
  4. verificación de cantidad de notas y equivalencia de promedios;
  5. `PRAGMA foreign_key_check` e `integrity_check`;
  6. comprobación de que el JSON no cambió;
  7. registro del SHA-256 para idempotencia;
  8. reporte JSON en `datos/backups/`.
- IDs deterministas (UUID5) para que una reejecución no duplique registros.
- CLI accesible por `python -m app.database.migrar_json` o
  `python main.py --migrar-json`.

---

## 3. Verificación de la migración real

### 3.1 Preflight

- Simulación sobre `datos/historial.json`: 2 registros leídos, 2 válidos,
  0 inválidos, 0 duplicados, 9 notas.
- Ensayo completo sobre una copia temporal: importación, verificación e
  idempotencia correctas.
- JSON original con SHA-256
  `cf32636b7cc48ca8562d469652e9b3e1d46fc39191266b136ddfdcc80d9980b5`.

### 3.2 Resultado de la aplicación real

```text
Estudiantes importados: 2
Notas importadas:       9

[OK] EST-000001: promedio 3.687500 coincide.
[OK] EST-000001: 8 nota(s) conservada(s).
[OK] EST-000002: promedio 2.900000 coincide.
[OK] EST-000002: 1 nota(s) conservada(s).
[OK] Claves foráneas íntegras.
[OK] PRAGMA integrity_check = ok.
[OK] JSON original sin cambios (SHA-256 idéntico).
[OK] Respaldo del JSON verificado.
```

### 3.3 Estado final de `datos/academico.db`

| Tabla | Filas |
|---|---|
| `estudiantes` | 2 |
| `materias` | 2 (`GEN`, `GEN-MIG`) |
| `periodos` | 2 (`Periodo general`, `Datos migrados 2.0`) |
| `inscripciones` | 2 |
| `calificaciones` | 9 |
| `migraciones` | 1 |
| `configuracion` | 5 |
| `contadores` | 1 |

- `PRAGMA integrity_check`: `ok`
- `PRAGMA foreign_key_check`: 0 problemas
- `journal_mode`: `wal`
- Versión de esquema: 1

| Código | Estudiante | Notas | Promedio |
|---|---|---|---|
| EST-000001 | Manuela | 8 | 3.6875 |
| EST-000002 | Luisa | 1 | 2.9000 |

### 3.4 Respaldos generados

- `datos/backups/historial-20261031-025408-187018.json` (309 bytes, SHA-256
  idéntico al original).
- `datos/backups/migracion-20261031-025408-266642.json` (reporte completo).
- Segunda ejecución de control (idempotencia):
  `historial-20261031-025554-731723.json`,
  `academico-20261031-025554-744208.db` y
  `migracion-20261031-025554-773325.json`.

El respaldo SQLite fue verificado con `PRAGMA integrity_check = ok` y conserva
2 estudiantes y 9 calificaciones.

### 3.5 Idempotencia comprobada

Una segunda ejecución de `--aplicar` sobre los datos reales produjo:

```text
Estudiantes importados: 0
Notas importadas:       0

[OK] Migración idempotente: no se duplicaron estudiantes ni notas.
[OK] El JSON original no se modificó.

Resultado: Este archivo ya fue migrado antes (mismo SHA-256).
           No se insertaron registros nuevos.
```

Tras la segunda ejecución la base conserva 2 estudiantes, 2 inscripciones,
9 calificaciones y 1 registro de migración.

---

## 4. Pruebas

Comando:

```bash
python -B -m unittest discover -s tests -v
```

Resultado: **42 pruebas OK**.

| Grupo | Archivo | Pruebas |
|---|---|---|
| 2.0 lógica | `tests/test_logica.py` | 8 |
| 2.0 interfaz | `tests/test_interfaz.py` | 10 |
| Núcleo 3.0 | `tests/core/test_escala.py` | 5 |
| Esquema | `tests/database/test_esquema.py` | 2 |
| Servicios | `tests/services/test_servicios.py` | 8 |
| Migración | `tests/database/test_migracion.py` | 5 |
| CLI | `tests/database/test_cli.py` | 4 |
| **Total** | | **42** |

Las 18 pruebas originales de la 2.0 se conservan sin modificaciones.

Cobertura funcional de las pruebas nuevas:

- Escala predeterminada y escalas alternativas; rechazo de valores inválidos.
- Creación de tablas, siembra inicial e idempotencia del esquema.
- CRUD lógico de estudiantes y materias; rollback transaccional.
- Escala global y escala congelada por periodo.
- Registro, promedio, detalle por materia/periodo y anulación de calificaciones.
- Validación contra la escala del periodo e inscripción única.
- Simulación sin escritura; aplicación con respaldo y verificación.
- Idempotencia por SHA-256; clasificación de inválidos y duplicados.
- JSON corrupto o inexistente sin efectos secundarios.
- CLI: `--dry-run`, `--aplicar`, error controlado y enrutamiento desde
  `main.py --migrar-json`.

---

## 5. Compatibilidad con la versión 2.0

- `python main.py` abre la GUI 2.0 correctamente (apertura y cierre
  verificados).
- `python main.py --consola` calcula y muestra el resultado normalmente.
- `datos/historial.json` no se modificó; su SHA-256 sigue siendo
  `cf32636b7cc48ca8562d469652e9b3e1d46fc39191266b136ddfdcc80d9980b5`.
- Las 18 pruebas originales siguen aprobando.
- La GUI 2.0 continúa leyendo/escribiendo JSON; la conexión a SQLite se hará en
  la Fase 3.

---

## 6. Decisiones aplicadas

| Decisión | Estado |
|---|---|
| GUI 2.0 disponible durante la transición | Sí |
| Borrado lógico | Sí (`eliminado_en`, `anulada_en`) |
| Escala configurable por periodo | Sí (instantánea por periodo) |
| Promedio aritmético | Sí |
| Materia general predeterminada | Sí (`GEN`) |
| Sin autenticación ficticia | Sí (tablas preparadas, sin login) |
| Exportaciones CSV, Excel y PDF | Preparadas para la Fase 4 |

---

## 7. Limitaciones conocidas

- La GUI 2.0 aún no usa SQLite; sigue con JSON hasta la Fase 3.
- No hay interfaz 3.0 ni API web todavía.
- Las exportaciones no están implementadas.
- `roles` y `usuarios` existen en el esquema, pero no hay autenticación.
- SQLite no impone la escala de notas a nivel de base; la validación vive en
  los servicios (fuente única de verdad).
- El proyecto no es un repositorio Git, por lo que el control de versiones
  depende de los respaldos.

---

## 8. Recomendaciones para la Fase 3

1. Construir la GUI 3.0 como nueva capa de presentación sobre `crear_servicios`,
   sin duplicar reglas.
2. Abrir una `UnidadDeTrabajo` por operación de usuario, no una conexión
   permanente compartida.
3. Mantener la GUI 2.0 accesible con un selector o argumento (`--clasica`)
   durante la transición.
4. Añadir un dashboard con estudiantes, materias, periodos y calificaciones.
5. Incorporar edición de la escala por periodo y visualización del historial.
6. Antes de la Fase 4, definir el contrato de exportación (CSV primero).
7. Conservar el JSON y los respaldos; no eliminarlos al migrar la GUI.

---

## 9. Conclusión

La Fase 2 cumple los objetivos: existe una base académica compartida,
verificable y transaccional; los datos reales se migraron con equivalencia
exacta de promedios; y la versión 2.0 permanece operativa. El proyecto está
listo para iniciar la Fase 3 (dashboard Tkinter 3.0) una vez recibida la
autorización.
