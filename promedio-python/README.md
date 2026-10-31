# Calculadora Académica 3.0

Evolución de la **Calculadora de Promedios 2.0** hacia un sistema académico
completo. Conserva la interfaz clásica y la consola, y añade:

- **Interfaz de escritorio Tkinter 3.0** con dashboard, navegación lateral,
  gestión de estudiantes y materias, calificaciones, historial, estadísticas,
  configuración de escala y reportes.
- **Aplicación web local** con FastAPI, Jinja2, HTML5, CSS3 y JavaScript,
  disponible en `http://127.0.0.1:8000`.
- **Servicios compartidos** y una única base **SQLite** (`datos/academico.db`)
  para ambas interfaces.

> **Estado actual: Fases 3 y 4 completadas.** Las 70 pruebas automatizadas
> pasan y la aceptación cruzada Tkinter ↔ web está verificada. El informe está
> en [`docs/INFORME-FASE-3-4.md`](docs/INFORME-FASE-3-4.md).

## Características

### Escritorio Tkinter 3.0

- Dashboard con indicadores, gráfico de promedios por materia, dona de
  distribución de estudiantes y ranking.
- Barra lateral institucional con secciones activas.
- Gestión de estudiantes: alta, búsqueda, edición y baja lógica.
- Gestión de materias: código único, créditos, edición y baja lógica.
- Registro de calificaciones por estudiante, materia y periodo, con validación
  contra la escala del periodo y anulación lógica.
- Historial académico por estudiante con resumen por periodo y materia.
- Estadísticas con filtro por periodo y comparación de rendimiento.
- Configuración de la escala global y de la escala propia de cada periodo.
- Estilo institucional: azul marino, blanco/grises, acentos dorados, tarjetas,
  tablas y formularios limpios.

### Web local

- Dashboard web responsive con los mismos indicadores.
- Navegación lateral adaptable a escritorio, tabletas y móviles.
- Estudiantes, materias, calificaciones, historial, estadísticas y
  configuración con las mismas reglas de negocio.
- Exportaciones **CSV**, **Excel** y **PDF** para estudiantes y calificaciones.
- Comprobación de salud en `/salud`.
- Sin CDN, sin Internet y sin autenticación ficticia: escucha exclusivamente en
  `127.0.0.1`.

### Compatibilidad conservada

- **GUI 2.0** disponible con `python main.py --clasica`.
- **Modo consola** disponible con `python main.py --consola`.
- **Migración JSON → SQLite** con `python main.py --migrar-json`.
- El JSON original `datos/historial.json` nunca se modifica.

## Arquitectura

La regla se mantiene: **presentación → servicios → núcleo**, con puertos de
persistencia y SQLite como infraestructura.

```text
Tkinter 3.0 ─┐
Tkinter 2.0 ─┼─→ app/services ─→ app/core ─→ puertos ─→ SQLite
Web FastAPI ─┘         (mismos casos de uso y mismas reglas)
```

- Cada operación abre su propia `UnidadDeTrabajo` y su propia conexión SQLite.
  Escritorio y web nunca comparten una conexión.
- `AnalisisService` compone los servicios existentes para dashboard, historial
  y estadísticas.
- `ExportacionService` genera archivos desde los servicios, sin consultar
  SQLite directamente.
- No se duplican reglas de negocio en las interfaces.

## Estructura del proyecto

```text
promedio-python/
│
├── app/
│   ├── promedio.py          # API 2.0 compatible; delega en app/core
│   ├── estudiante.py        # Modelo 2.0 (nombre + notas)
│   ├── historial.py         # Persistencia 2.0 en JSON
│   ├── interfaz.py          # GUI 2.0 clásica (--clasica)
│   │
│   ├── core/                # Dominio puro, sin frameworks
│   │   ├── escala.py
│   │   ├── promedio.py
│   │   ├── entidades.py
│   │   ├── errores.py
│   │   ├── puertos.py
│   │   ├── texto.py
│   │   └── tiempo.py
│   │
│   ├── services/            # Casos de uso compartidos
│   │   ├── estudiantes.py
│   │   ├── materias.py
│   │   ├── periodos.py
│   │   ├── configuracion.py
│   │   ├── calificaciones.py
│   │   ├── analisis.py      # Agregados de dashboard e historial
│   │   ├── exportacion.py   # CSV, Excel y PDF
│   │   ├── fabrica.py       # crear_servicios(repos)
│   │   └── migracion.py
│   │
│   ├── database/            # Infraestructura SQLite
│   │   ├── conexion.py      # WAL, claves foráneas, respaldos
│   │   ├── esquema.py
│   │   ├── migraciones/001_inicial.sql
│   │   ├── repositorios/
│   │   ├── unidad.py
│   │   ├── json_legacy.py
│   │   └── migrar_json.py
│   │
│   ├── escritorio/          # GUI 3.0 (Tkinter)
│   │   ├── aplicacion.py    # Ventana, barra lateral y navegación
│   │   ├── estilos.py       # Paleta institucional y ttk
│   │   ├── widgets.py       # Tarjetas, tablas, gráficos, modales
│   │   ├── sesion.py        # Una unidad de trabajo por acción
│   │   └── vistas/          # Dashboard, estudiantes, materias, etc.
│   │
│   └── web/                 # Aplicación web local
│       ├── servidor.py      # crear_app(ruta_db) y app ASGI
│       ├── rutas.py
│       ├── dependencias.py  # Sesiones de lectura/escritura por petición
│       ├── plantillas.py    # Jinja2 y filtros de presentación
│       ├── templates/       # Plantillas HTML
│       └── static/          # CSS y JavaScript locales
│
├── datos/
│   ├── historial.json       # Datos originales de la 2.0 (intactos)
│   ├── academico.db         # Base SQLite compartida
│   └── backups/
│
├── docs/
│   ├── INFORME-FASE-2.md
│   └── INFORME-FASE-3-4.md
│
├── tests/
│   ├── test_logica.py       # 2.0
│   ├── test_interfaz.py     # 2.0
│   ├── core/                # 3.0: escala y cálculos
│   ├── services/            # 3.0: servicios, análisis y exportaciones
│   ├── database/            # 3.0: esquema, migración y CLI
│   ├── escritorio/          # 3.0: humo de la GUI Tkinter
│   └── web/                 # 3.0: rutas, formularios y base compartida
│
├── main.py                  # Punto de entrada
└── README.md
```

## Requisitos

- Python 3.10 o superior (probado con Python 3.13).
- Tkinter incluido con Python (en Linux puede requerir `sudo apt install python3-tk`).
- Dependencias de la web y exportaciones:

```bash
python -m pip install fastapi "uvicorn[standard]" jinja2 python-multipart httpx openpyxl reportlab
```

`httpx` solo se usa en las pruebas con `TestClient`. Las exportaciones usan
`openpyxl` (Excel) y `reportlab` (PDF).

## Cómo ejecutar

Desde la carpeta `promedio-python`:

### Escritorio 3.0 (predeterminado)

```bash
python main.py
```

### Escritorio 2.0 clásico

```bash
python main.py --clasica
```

### Aplicación web local

```bash
python main.py --web
```

Abre `http://127.0.0.1:8000`. Para usar otro puerto local:

```bash
python main.py --web --puerto 8080
```

El servidor escucha **solo en `127.0.0.1`**.

### Consola

```bash
python main.py --consola
```

### Migración JSON → SQLite

Simulación (no escribe nada, modo por defecto):

```bash
python main.py --migrar-json --dry-run
```

Aplicación real (crea respaldos, importa y verifica):

```bash
python main.py --migrar-json --aplicar
```

La migración es **idempotente** y nunca modifica el JSON original.

## Uso de la aplicación

### Escritorio

1. Abre una sección desde la barra lateral.
2. En **Estudiantes** y **Materias**, usa los botones de alta, edición y baja.
3. En **Calificaciones**, selecciona estudiante, materia y periodo, escribe la
   nota y registra. La nota se valida contra la escala del periodo.
4. En **Historial**, selecciona un estudiante para ver su trayectoria.
5. En **Estadísticas**, filtra por periodo para comparar rendimiento.
6. En **Configuración**, ajusta la escala global o crea periodos con escala
   propia.
7. Pulsa `F5` o `Ctrl+R` para refrescar la sección visible.

### Web

| Ruta | Contenido |
|---|---|
| `/` | Dashboard, indicadores, gráficos y ranking |
| `/estudiantes` | Listado, búsqueda, alta, edición y baja lógica |
| `/materias` | Catálogo de materias y créditos |
| `/calificaciones` | Registro, filtros y anulación de notas |
| `/historial` | Historial por estudiante y resúmenes |
| `/estadisticas` | Indicadores y comparación por periodo |
| `/configuracion` | Escala global y periodos académicos |
| `/salud` | Estado del servicio y de la base compartida |
| `/api/docs` | Documentación automática de FastAPI |

Las exportaciones están en:

```text
/exportar/estudiantes.csv      /exportar/calificaciones.csv
/exportar/estudiantes.xlsx     /exportar/calificaciones.xlsx
/exportar/estudiantes.pdf      /exportar/calificaciones.pdf
```

## Persistencia compartida

`datos/academico.db` es la única base de la 3.0. Escritorio y web leen y
escriben en ella mediante servicios comunes. Cada petición o acción abre su
propia unidad de trabajo y confirma o revierte de forma independiente.

Tablas principales:

| Tabla | Propósito |
|---|---|
| `estudiantes` | Identidad, código único y borrado lógico |
| `materias` | Materias con créditos y borrado lógico |
| `periodos` | Periodos con escala propia (mín, máx, aprobación) |
| `inscripciones` | Vínculo único estudiante + materia + periodo |
| `calificaciones` | Notas con anulación lógica y origen |
| `configuracion` | Escala global y preferencias |
| `migraciones` | Registro idempotente por SHA-256 |
| `contadores` | Secuencias de códigos (por ejemplo `EST-000001`) |

Reglas de negocio:

- Promedio **aritmético** de las calificaciones activas.
- La nota se valida contra la **escala del periodo**.
- Bajas **lógicas** (`eliminado_en`, `anulada_en`), nunca físicas.
- Sin autenticación ficticia; no se simulan usuarios ni roles.

### JSON 2.0

`datos/historial.json` se conserva como fuente histórica y no se modifica:

```json
{
  "version": 1,
  "estudiantes": [
    {
      "nombre": "Ana Pérez",
      "notas": [4.5, 3.0, 2.5]
    }
  ]
}
```

SHA-256 verificado del JSON original:

```text
cf32636b7cc48ca8562d469652e9b3e1d46fc39191266b136ddfdcc80d9980b5
```

## Pruebas

```bash
python -B -m unittest discover -s tests -v
```

Resultado esperado: **70 pruebas OK**.

- 18 pruebas de la versión 2.0.
- 24 pruebas de la Fase 2 (núcleo, servicios, SQLite y migración).
- 28 pruebas nuevas de las Fases 3 y 4:
  - análisis, periodos y exportaciones;
  - humo y navegación de la GUI Tkinter 3.0;
  - rutas, formularios, validaciones, exportaciones y base compartida de la web.

En PowerShell el comando puede devolver código de salida 1 aunque el resumen
muestre `OK`; el resultado válido es el resumen de `unittest`.

## Estado de la base real

- 2 estudiantes (`EST-000001` Manuela, `EST-000002` Luisa).
- 9 calificaciones.
- `PRAGMA integrity_check = ok`.
- JSON original intacto con el SHA-256 indicado.
- La migración ya está aplicada y es idempotente.

Los detalles de la Fase 2 están en
[`docs/INFORME-FASE-2.md`](docs/INFORME-FASE-2.md) y la aceptación de las
interfaces en [`docs/INFORME-FASE-3-4.md`](docs/INFORME-FASE-3-4.md).
