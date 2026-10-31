-- Esquema inicial de la Calculadora Académica 3.0.
-- Las claves foráneas se activan por conexión en app/database/conexion.py.

CREATE TABLE IF NOT EXISTS configuracion (
    clave          TEXT PRIMARY KEY,
    valor          TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id              TEXT PRIMARY KEY,
    usuario         TEXT NOT NULL UNIQUE,
    nombre_completo TEXT NOT NULL,
    correo          TEXT,
    hash_contrasena TEXT,
    rol_id          INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id                 TEXT PRIMARY KEY,
    codigo             TEXT NOT NULL UNIQUE,
    nombre             TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    nombre_normalizado TEXT NOT NULL,
    correo             TEXT,
    origen             TEXT NOT NULL DEFAULT 'app'
                       CHECK (origen IN ('app', 'json_migracion')),
    huella_migracion   TEXT UNIQUE,
    creado_en          TEXT NOT NULL,
    actualizado_en     TEXT NOT NULL,
    eliminado_en       TEXT
);

CREATE INDEX IF NOT EXISTS idx_estudiantes_nombre
    ON estudiantes(nombre_normalizado) WHERE eliminado_en IS NULL;

CREATE TABLE IF NOT EXISTS materias (
    id             TEXT PRIMARY KEY,
    codigo         TEXT NOT NULL UNIQUE,
    nombre         TEXT NOT NULL,
    creditos       REAL NOT NULL DEFAULT 0 CHECK (creditos >= 0),
    creado_en      TEXT NOT NULL,
    actualizado_en TEXT NOT NULL,
    eliminado_en   TEXT
);

CREATE TABLE IF NOT EXISTS periodos (
    id             TEXT PRIMARY KEY,
    nombre         TEXT NOT NULL UNIQUE,
    fecha_inicio   TEXT,
    fecha_fin      TEXT,
    escala_min     REAL NOT NULL,
    escala_max     REAL NOT NULL,
    aprobacion_min REAL NOT NULL,
    activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en      TEXT NOT NULL,
    CHECK (escala_min < escala_max),
    CHECK (aprobacion_min >= escala_min AND aprobacion_min <= escala_max)
);

CREATE TABLE IF NOT EXISTS inscripciones (
    id            TEXT PRIMARY KEY,
    estudiante_id TEXT NOT NULL REFERENCES estudiantes(id) ON DELETE RESTRICT,
    materia_id    TEXT NOT NULL REFERENCES materias(id) ON DELETE RESTRICT,
    periodo_id    TEXT NOT NULL REFERENCES periodos(id) ON DELETE RESTRICT,
    estado        TEXT NOT NULL DEFAULT 'activa'
                  CHECK (estado IN ('activa', 'retirada', 'finalizada')),
    creado_en     TEXT NOT NULL,
    UNIQUE (estudiante_id, materia_id, periodo_id)
);

CREATE INDEX IF NOT EXISTS idx_inscripciones_estudiante
    ON inscripciones(estudiante_id);

CREATE INDEX IF NOT EXISTS idx_inscripciones_periodo
    ON inscripciones(periodo_id);

CREATE TABLE IF NOT EXISTS calificaciones (
    id             TEXT PRIMARY KEY,
    inscripcion_id TEXT NOT NULL REFERENCES inscripciones(id) ON DELETE RESTRICT,
    nota           REAL NOT NULL,
    descripcion    TEXT,
    fecha          TEXT NOT NULL,
    origen         TEXT NOT NULL DEFAULT 'app',
    creado_en      TEXT NOT NULL,
    anulada_en     TEXT
);

CREATE INDEX IF NOT EXISTS idx_calificaciones_inscripcion
    ON calificaciones(inscripcion_id) WHERE anulada_en IS NULL;

CREATE INDEX IF NOT EXISTS idx_calificaciones_fecha
    ON calificaciones(fecha);

CREATE TABLE IF NOT EXISTS migraciones (
    id           TEXT PRIMARY KEY,
    archivo      TEXT NOT NULL,
    sha256       TEXT NOT NULL UNIQUE,
    ejecutada_en TEXT NOT NULL,
    total_leidos INTEGER NOT NULL,
    importados   INTEGER NOT NULL,
    duplicados   INTEGER NOT NULL,
    invalidos    INTEGER NOT NULL,
    resultado    TEXT NOT NULL,
    detalle_json TEXT
);

CREATE TABLE IF NOT EXISTS contadores (
    nombre TEXT PRIMARY KEY,
    valor  INTEGER NOT NULL
);

-- Valores iniciales: reproducen la escala de la versión 2.0.
INSERT OR IGNORE INTO configuracion (clave, valor, actualizado_en) VALUES
    ('escala_min', '0.0', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('escala_max', '5.0', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('aprobacion_min', '3.0', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('decimales', '2', strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ('promedio_por_creditos', '0', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));

-- Materia general para registrar notas sin configuración previa.
INSERT OR IGNORE INTO materias
    (id, codigo, nombre, creditos, creado_en, actualizado_en)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'GEN', 'Materia general', 0,
     strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
     strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));

-- Periodo inicial con la escala predeterminada.
INSERT OR IGNORE INTO periodos
    (id, nombre, fecha_inicio, fecha_fin, escala_min, escala_max,
     aprobacion_min, activo, creado_en)
VALUES
    ('00000000-0000-0000-0000-000000000002', 'Periodo general', NULL, NULL,
     0.0, 5.0, 3.0, 1, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));

INSERT OR IGNORE INTO contadores (nombre, valor) VALUES ('estudiante', 0);
