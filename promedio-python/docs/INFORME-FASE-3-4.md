# Informe de aceptación — Fases 3 y 4

**Proyecto:** Calculadora Académica 3.0
**Fecha:** 30/10/2026
**Alcance:** interfaz Tkinter 3.0 e interfaz web local FastAPI sobre los
servicios y la base SQLite de la Fase 2.

---

## 1. Resultado general

| Criterio | Resultado |
|---|---|
| Interfaz Tkinter 3.0 | **Aceptada** |
| Aplicación web local | **Aceptada** |
| Servicios compartidos | **Verificado** |
| Base SQLite compartida | **Verificado** |
| Comunicación Tkinter ↔ web | **Verificado en ambos sentidos** |
| Compatibilidad con consola y GUI 2.0 | **Conservada** |
| JSON original intacto | **Verificado** |
| Pruebas automatizadas | **70 OK** |
| Integridad de la base real | `PRAGMA integrity_check = ok` |

No se reconstruyó ni se eliminó el núcleo de la Fase 2. Las interfaces nuevas
consumen los casos de uso existentes y las extensiones añadidas se limitan a
consultas agregadas y exportaciones.

---

## 2. Entregables

### 2.1 Escritorio Tkinter 3.0

Archivos principales:

- `app/escritorio/aplicacion.py`: ventana principal, barra lateral institucional
  y navegación entre secciones.
- `app/escritorio/estilos.py`: paleta azul marino, blanco/grises y dorado;
  estilos de botones, campos, tablas y scrollbars.
- `app/escritorio/widgets.py`: tarjetas, tablas, gráficos de barras y dona,
  modales y confirmaciones.
- `app/escritorio/sesion.py`: una unidad de trabajo por acción.
- `app/escritorio/vistas/`:
  - `dashboard.py`
  - `estudiantes.py`
  - `materias.py`
  - `calificaciones.py`
  - `historial.py`
  - `estadisticas.py`
  - `configuracion.py`

Funcionalidad comprobada:

- Dashboard con estudiantes, materias, calificaciones, promedio general,
  promedios por materia, distribución y ranking.
- Navegación por las siete secciones sin errores de construcción.
- Alta, búsqueda, edición y baja lógica de estudiantes.
- Alta, edición y baja lógica de materias, con código único y créditos.
- Registro de calificaciones con validación de escala y anulación lógica.
- Historial por estudiante con promedios por periodo y materia.
- Estadísticas filtradas por periodo.
- Configuración de escala global y periodos con escala propia.
- Refresco manual con `F5`, `Ctrl+R` y botón “Actualizar”.

### 2.2 Aplicación web local

Archivos principales:

- `app/web/servidor.py`: `crear_app(ruta_db=None)` con base configurable,
  montaje de `/static` y `app` ASGI.
- `app/web/rutas.py`: dashboard, estudiantes, materias, calificaciones,
  historial, estadísticas, configuración, periodos, exportaciones y `/salud`.
- `app/web/dependencias.py`: sesión de lectura o de escritura por petición.
- `app/web/plantillas.py`: Jinja2 y filtros de presentación.
- `app/web/templates/`: once plantillas HTML.
- `app/web/static/css/estilos.css`: diseño institucional responsive.
- `app/web/static/js/app.js`: menú móvil, cierre de avisos, confirmaciones y
  filtros automáticos, sin dependencias externas.

La aplicación escucha exclusivamente en `127.0.0.1` y no usa CDN ni recursos de
Internet.

### 2.3 Servicios compartidos ampliados

- `app/services/analisis.py`: resumen general, detalle por estudiante y puntos
  agregados por materia y periodo.
- `app/services/exportacion.py`: CSV, Excel y PDF para estudiantes y
  calificaciones.
- `app/services/fabrica.py`: incorpora `analisis` al contenedor `Servicios`.
- `app/services/calificaciones.py`: `listar_todas` con filtros y validación de
  estudiante, materia y periodo.
- `app/services/periodos.py`: actualización de periodos conservando campos.
- Repositorios: consultas de detalle enriquecidas con estudiante, materia y
  periodo; actualización de periodos.

### 2.4 Entrada unificada

`main.py` mantiene todos los modos:

| Comando | Interfaz |
|---|---|
| `python main.py` | Tkinter 3.0 (predeterminada) |
| `python main.py --clasica` | Tkinter 2.0 |
| `python main.py --web` | Web local en `127.0.0.1:8000` |
| `python main.py --web --puerto 8080` | Web local en otro puerto |
| `python main.py --consola` | Consola 2.0 |
| `python main.py --migrar-json ...` | Migración JSON → SQLite |

---

## 3. Arquitectura y reutilización

La dirección de dependencias se mantiene:

```text
Tkinter 3.0 ─┐
Tkinter 2.0 ─┼─→ servicios ─→ núcleo ─→ puertos ─→ SQLite
Web FastAPI ─┘
```

Verificaciones:

- Ambas interfaces usan `app.services.fabrica.crear_servicios`.
- Ninguna interfaz ejecuta SQL directo para reglas de negocio.
- No se duplicaron validaciones, promedios ni escalas.
- Cada operación/petición abre su propia `UnidadDeTrabajo`.
- La web acepta una ruta de base alternativa para pruebas.
- La base real se comparte mediante `datos/academico.db`.

---

## 4. Pruebas ejecutadas

### 4.1 Comandos

```bash
python -B -m compileall -q app main.py tests
python -B -m unittest discover -s tests -v
```

Resultados:

- Compilación: **OK**.
- Suite: **70 pruebas, OK**.

Desglose:

| Bloque | Pruebas |
|---|---|
| Versión 2.0 (lógica e interfaz) | 18 |
| Fase 2 (core, servicios, SQLite, migración, CLI) | 24 |
| Fase 3/4: análisis, periodos y exportaciones | 7 |
| Fase 3/4: GUI Tkinter 3.0 | 4 |
| Fase 3/4: web, formularios, exportaciones y base compartida | 17 |
| **Total** | **70** |

Las pruebas web usan bases temporales y `TestClient`; no alteran la base real.

### 4.2 Cobertura funcional nueva

- Resumen general y filtrado por periodo.
- Detalle de estudiante con promedios por periodo y materia.
- Filtros de calificaciones y exclusión de anuladas.
- Actualización de periodos conservando fechas, escala y estado.
- Validación de nombres duplicados y periodos inexistentes.
- Exportaciones CSV, Excel y PDF con firmas de archivo verificadas.
- Renderizado de todas las páginas web.
- Alta, edición y baja lógica desde formularios web.
- Validaciones de nombres, códigos duplicados, fechas y notas fuera de escala.
- Configuración de escala y periodos desde la web.
- Descarga de exportaciones y respuesta 404 para formatos no admitidos.
- Comprobación de `/salud` y de los estáticos locales.
- Visibilidad de escrituras entre servicios y web.
- Navegación de las siete secciones Tkinter y refresco tras una escritura.

---

## 5. Verificación cruzada Tkinter ↔ web

Se realizó sobre una base temporal compartida, usando la misma ruta para la
sesión de escritorio y para `crear_app(ruta)`.

### 5.1 Escritura desde Tkinter → lectura web

1. Se creó un estudiante, una materia y una calificación usando
   `app.escritorio.sesion.sesion`, la misma ruta que emplean los botones de la
   GUI.
2. La web mostró inmediatamente:
   - el estudiante en `/estudiantes`;
   - la materia en `/materias`;
   - la nota en `/calificaciones`;
   - el estudiante en el ranking del dashboard `/`.

Resultados: **visibles en todas las consultas**.

### 5.2 Escritura desde web → lectura Tkinter

1. Se registró un estudiante y una calificación mediante peticiones POST a la
   web.
2. Se abrió la GUI 3.0 sobre la misma base.
3. La tabla de estudiantes mostró el registro creado desde la web.
4. La tabla de calificaciones mostró la nota creada desde la web.
5. El dashboard mostró el total actualizado de estudiantes.

Resultados: **visibles en la GUI y en el dashboard**.

### 5.3 Integridad

Tras el flujo cruzado:

- `PRAGMA integrity_check = ok`.
- 2 estudiantes y 2 calificaciones en la base temporal de prueba.
- Sin conexiones compartidas ni bloqueos.

---

## 6. Verificación de la web real

Se arrancó el servidor real con:

```bash
python main.py --web --puerto 8123
```

Comprobaciones:

- `/salud` respondió `200` con:
  ```json
  {"estado": "ok", "base": "...\\datos\\academico.db",
   "estudiantes": 2, "materias": 2, "periodos": 2}
  ```
- `/` respondió `200` y sirvió el dashboard.
- El proceso confirmó la escucha en `127.0.0.1:8123`.
- CSS y JavaScript locales respondieron `200`.
- Todas las rutas principales respondieron `200` con la base temporal:
  `/`, `/estudiantes`, `/materias`, `/calificaciones`, `/historial`,
  `/estadisticas`, `/configuracion`, formularios y `/api/docs`.

### Exportaciones verificadas

| Archivo | Resultado |
|---|---|
| `estudiantes.csv` | 200, prefijo BOM UTF-8 |
| `estudiantes.xlsx` | 200, firma `PK` |
| `estudiantes.pdf` | 200, firma `%PDF` |
| `calificaciones.csv` | 200, prefijo BOM UTF-8 |
| `calificaciones.xlsx` | 200, firma `PK` |
| `calificaciones.pdf` | 200, firma `%PDF` |

---

## 7. Compatibilidad y datos

### 7.1 JSON original

- Archivo: `datos/historial.json`.
- SHA-256:
  `cf32636b7cc48ca8562d469652e9b3e1d46fc39191266b136ddfdcc80d9980b5`.
- **Sin cambios.**

### 7.2 Base real

- Archivo: `datos/academico.db`.
- `PRAGMA integrity_check = ok`.
- 2 estudiantes.
- 2 materias.
- 2 periodos.
- 2 inscripciones.
- 9 calificaciones.
- 0 estudiantes eliminados y 0 calificaciones anuladas.

### 7.3 Interfaces conservadas

- Consola: `python main.py --consola`.
- GUI 2.0: `python main.py --clasica`.
- Migración: `python main.py --migrar-json`.
- Las 42 pruebas previas siguen pasando dentro de la suite de 70.

---

## 8. Requisitos de diseño

| Requisito | Estado |
|---|---|
| Azul marino institucional | Cumplido |
| Blanco y grises académicos | Cumplido |
| Acentos dorados discretos | Cumplido |
| Tarjetas estadísticas | Cumplido en escritorio y web |
| Tablas organizadas | Cumplido |
| Formularios limpios | Cumplido |
| Navegación intuitiva | Cumplido |
| Diseño web responsive | Cumplido (escritorio, tableta y móvil) |
| Sin CDN ni Internet | Cumplido |
| Solo `127.0.0.1` | Cumplido |
| Sin autenticación ficticia | Cumplido |

---

## 9. Observaciones y limitaciones

- La web requiere las dependencias indicadas en el README; si faltan, `main.py`
  muestra un mensaje con el comando de instalación.
- Las exportaciones PDF son reportes tabulares institucionales; no sustituyen
  un generador de reportes personalizables.
- La GUI 2.0 se conserva tal cual para compatibilidad y no se rediseñó.
- Al cerrar la suite pueden aparecer mensajes de limpieza de variables Tkinter
  provenientes de las pruebas de la GUI 2.0. No son fallos: el resumen final es
  `OK`.
- No hay usuarios, roles ni autenticación porque el alcance lo prohíbe
  expresamente y la aplicación es de uso local.

---

## 10. Conclusión

Las Fases 3 y 4 se consideran **completadas y aceptadas**:

- La interfaz Tkinter 3.0 está operativa y conectada a SQLite.
- La aplicación web local está operativa en `127.0.0.1` y usa los mismos
  servicios y la misma base.
- Los cambios se propagan correctamente en ambos sentidos.
- No se perdió información ni se modificó el JSON original.
- La consola, la GUI 2.0 y las pruebas previas siguen funcionando.
- La suite completa queda en **70 pruebas OK**.
