-- ============================================================
-- RAU – Esquema base (PostgreSQL 17)
-- ============================================================
BEGIN;

-- Recomendado (no requerido): zona horaria de referencia
SET TIME ZONE 'UTC';

-- ============================================================
-- Utilidades: función y trigger para updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.actualizado_en := NOW();
  RETURN NEW;
END
$$;

-- ============================================================
-- Tabla: usuario (autenticación y perfil)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuario (
  usuario_id        BIGSERIAL PRIMARY KEY,
  email             VARCHAR(320) NOT NULL UNIQUE,
  nombreCompleto    VARCHAR(200) NOT NULL,
  username          VARCHAR(64)  UNIQUE,
  rol               VARCHAR(32)  NOT NULL,         -- 'Profesor' | 'Estudiante' (se valida en app)
  bio               VARCHAR(1000),
  avatar_url        VARCHAR(500),
  password_hash     BYTEA        NOT NULL,
  creado_en         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  actualizado_en    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_usuario_updated_at
BEFORE UPDATE ON usuario
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_usuario_username ON usuario (username);
CREATE INDEX IF NOT EXISTS idx_usuario_creado_en ON usuario (creado_en DESC);

-- ============================================================
-- Tabla: password_reset_token (manejo de resets)
-- ============================================================
CREATE TABLE IF NOT EXISTS password_reset_token (
  token_id      BIGSERIAL PRIMARY KEY,
  usuario_id    BIGINT NOT NULL REFERENCES usuario(usuario_id) ON DELETE CASCADE,
  token         BYTEA  NOT NULL,
  expira_en     TIMESTAMPTZ NOT NULL,
  usado_en      TIMESTAMPTZ,
  creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prt_usuario_id     ON password_reset_token (usuario_id);
CREATE INDEX IF NOT EXISTS idx_prt_expira_en      ON password_reset_token (expira_en);

-- ============================================================
-- Tabla: preferencia_usuario (onboarding/preferencias)
-- PK = FK (1:1 con usuario)
-- ============================================================
CREATE TABLE IF NOT EXISTS preferencia_usuario (
  usuario_id        BIGINT PRIMARY KEY REFERENCES usuario(usuario_id) ON DELETE CASCADE,
  carrera_nombre    VARCHAR(120),
  cuatrimestre      SMALLINT,                      -- opcional
  on_boarded        BOOLEAN DEFAULT FALSE,
  actualizado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_pref_usuario_updated_at
BEFORE UPDATE ON preferencia_usuario
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Tabla: comunidad (materias / grupos)
-- ============================================================
CREATE TABLE IF NOT EXISTS comunidad (
  comunidad_id   BIGSERIAL PRIMARY KEY,
  nombre         VARCHAR(200) NOT NULL UNIQUE,
  descripcion    VARCHAR(1000),
  es_oficial     BOOLEAN NOT NULL DEFAULT FALSE,
  creado_por     BIGINT REFERENCES usuario(usuario_id) ON DELETE RESTRICT,
  creado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_comunidad_updated_at
BEFORE UPDATE ON comunidad
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Tabla: comunidad_miembro (membresías)
-- PK compuesta (comunidad_id, usuario_id)
-- rol: 'O' owner, 'M' moderator, 'U' member
-- ============================================================
CREATE TABLE IF NOT EXISTS comunidad_miembro (
  comunidad_id   BIGINT NOT NULL REFERENCES comunidad(comunidad_id) ON DELETE CASCADE,
  usuario_id     BIGINT NOT NULL REFERENCES usuario(usuario_id)     ON DELETE CASCADE,
  rol            CHAR(1) NOT NULL,
  unido_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (comunidad_id, usuario_id),
  CONSTRAINT ck_comunidad_miembro_rol CHECK (rol IN ('O', 'M', 'U'))
);

CREATE INDEX IF NOT EXISTS idx_comunidad_miembro_usuario ON comunidad_miembro (usuario_id);

-- ============================================================
-- Tabla: post (publicaciones)
-- mejor_comentario_id es opcional; si el comentario se borra → SET NULL
-- estado: 'A' Activo, 'H' Oculto, 'E' Eliminado
-- ============================================================
CREATE TABLE IF NOT EXISTS post (
  post_id              BIGSERIAL PRIMARY KEY,
  comunidad_id         BIGINT NOT NULL REFERENCES comunidad(comunidad_id) ON DELETE RESTRICT,
  autor_id             BIGINT NOT NULL REFERENCES usuario(usuario_id)     ON DELETE RESTRICT,
  titulo               VARCHAR(200) NOT NULL,
  cuerpo               TEXT         NOT NULL,
  mejor_comentario_id  BIGINT,
  creado_en            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  actualizado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  estado               CHAR(1)      NOT NULL DEFAULT 'A',
  CONSTRAINT ck_post_estado CHECK (estado IN ('A','H','E'))
);

-- ============================================================
-- Tabla: comentario (anidados)
-- comentario_padre_id permite threads (NULL = toplevel)
-- Al borrar post → borra comentarios; al borrar comentario padre → borra hijos
-- ============================================================
CREATE TABLE IF NOT EXISTS comentario (
  comentario_id       BIGSERIAL PRIMARY KEY,
  post_id             BIGINT NOT NULL REFERENCES post(post_id)        ON DELETE CASCADE,
  autor_id            BIGINT NOT NULL REFERENCES usuario(usuario_id)  ON DELETE RESTRICT,
  comentario_padre_id BIGINT REFERENCES comentario(comentario_id)     ON DELETE CASCADE,
  cuerpo              TEXT NOT NULL,
  creado_en           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Retornamos a "post"

-- FK diferida para mejor_comentario_id (auto-referenciada vía comentario)
ALTER TABLE post
  ADD CONSTRAINT fk_post_mejor_comentario
  FOREIGN KEY (mejor_comentario_id)
  REFERENCES comentario (comentario_id) DEFERRABLE INITIALLY DEFERRED;

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_post_comunidad_id  ON post (comunidad_id);
CREATE INDEX IF NOT EXISTS idx_post_autor_id      ON post (autor_id);
CREATE INDEX IF NOT EXISTS idx_post_creado_en     ON post (creado_en DESC);

-- Volvemos a comentario

CREATE TRIGGER trg_comentario_updated_at
BEFORE UPDATE ON comentario
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_comentario_post_id   ON comentario (post_id);
CREATE INDEX IF NOT EXISTS idx_comentario_autor_id  ON comentario (autor_id);
CREATE INDEX IF NOT EXISTS idx_comentario_padre_id  ON comentario (comentario_padre_id);

-- Ahora que existe comentario, re–creamos la FK de mejor_comentario (ya añadida arriba)

-- ============================================================
-- Tabla: post_voto (up/down)
-- PK compuesta (post_id, usuario_id), valor ∈ {-1, +1}
-- ============================================================
CREATE TABLE IF NOT EXISTS post_voto (
  post_id     BIGINT   NOT NULL REFERENCES post(post_id)       ON DELETE CASCADE,
  usuario_id  BIGINT   NOT NULL REFERENCES usuario(usuario_id) ON DELETE CASCADE,
  valor       SMALLINT NOT NULL,
  votado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (post_id, usuario_id),
  CONSTRAINT ck_post_voto_valor CHECK (valor IN (-1, 1))
);

CREATE INDEX IF NOT EXISTS idx_post_voto_usuario ON post_voto (usuario_id);

-- ============================================================
-- Tabla: comentario_voto (up/down)
-- PK compuesta (comentario_id, usuario_id), valor ∈ {-1, +1}
-- ============================================================
CREATE TABLE IF NOT EXISTS comentario_voto (
  comentario_id BIGINT   NOT NULL REFERENCES comentario(comentario_id) ON DELETE CASCADE,
  usuario_id    BIGINT   NOT NULL REFERENCES usuario(usuario_id)       ON DELETE CASCADE,
  valor         SMALLINT NOT NULL,
  votado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (comentario_id, usuario_id),
  CONSTRAINT ck_comentario_voto_valor CHECK (valor IN (-1, 1))
);

CREATE INDEX IF NOT EXISTS idx_comentario_voto_usuario ON comentario_voto (usuario_id);

-- ============================================================
-- Tabla: post_guardado (bookmarks)
-- PK compuesta (post_id, usuario_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_guardado (
  post_id     BIGINT NOT NULL REFERENCES post(post_id)       ON DELETE CASCADE,
  usuario_id  BIGINT NOT NULL REFERENCES usuario(usuario_id) ON DELETE CASCADE,
  guardado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (post_id, usuario_id)
);

CREATE INDEX IF NOT EXISTS idx_post_guardado_usuario ON post_guardado (usuario_id);

-- ============================================================
-- Extras de integridad / performance (opcionales)
-- ============================================================

-- Evitar que un usuario comente en posts de comunidades donde no es miembro (opcional, si lo querés a nivel DB):
--   Esto puede ser complejo por FK; usualmente se valida en la capa de aplicación.

-- Texto rápido: índices trigram (si activás pg_trgm) para búsquedas por título/cuerpo (opcional).
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_post_titulo_trgm ON post USING gin (titulo gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_post_cuerpo_trgm  ON post USING gin (cuerpo gin_trgm_ops);

COMMIT;


---------------------------------------------- DATA ----------------------------------------------


-- ============================================================
-- Carga de datos de demostración para RAU (PostgreSQL 17)
-- Este script inserta usuarios, preferencias, comunidades,
-- membresías, publicaciones, comentarios, votos y marcadores
-- para poblar la base de datos con contenido ficticio.
-- Los valores siguen la temática académica de RAU y respetan
-- las estructuras esperadas por el backend y el frontend.
-- ============================================================

BEGIN;

-- Establecer la zona horaria de referencia
SET TIME ZONE 'UTC';

-- ------------------------------------------------------------
-- Usuarios: profesores y estudiantes
-- Las contraseñas se generan con bcrypt y se almacenan como
-- bytes usando la función decode(hex, 'hex').
--   'profesor123'   -> $2b$12$xRVc0jNjyMyJRb3LHzdso.vwDmeUaATZTJ5iQMNbQnF4cQ7mLTOLS
--   'estudiante123' -> $2b$12$fwQ2XRBSJcQKQpQIpkhA9uAAS08RswORrrHt5LnmDZkp.JHFhGbrW
INSERT INTO usuario (usuario_id, email, nombreCompleto, username, rol, bio, avatar_url, password_hash)
VALUES
  (1, 'ana.gomez@rau.edu.ar',    'Ana Gómez',          'anag',   'Profesor',  'Docente de Algoritmos y Estructuras de Datos', 'https://example.com/avatar_ana.jpg',    decode('2432622431322478525663306a4e6a794d794a5262334c487a64736f2e7677446d65556141545a544a3569514d4e62516e46346351376d4c544f4c53', 'hex')),
  -- (2, 'carlos.perez@rau.edu.ar', 'Carlos Pérez',       'carlosp','Profesor',  'Profesor de Redes II y comunicaciones',          'https://example.com/avatar_carlos.jpg', decode('2432622431322478525663306a4e6a794d794a5262334c487a64736f2e7677446d65556141545a544a3569514d4e62516e46346351376d4c544f4c53', 'hex')), -- Deprecado
  (3, 'maria.rodriguez@rau.edu.ar','María Rodríguez',  'maria',  'Estudiante','Estudiante de tercer año de Ingeniería en Informática','https://example.com/avatar_maria.jpg', decode('2432622431322466775132585242534a63514b51705149706b6841397541415330385273774f5272724874354c6e6d445a6b702e4a48466847627257', 'hex')),
  (4, 'juan.lopez@rau.edu.ar',   'Juan López',         'juanl',  'Estudiante','Apasionado por la programación y la ciencia de datos',    'https://example.com/avatar_juan.jpg',  decode('2432622431322466775132585242534a63514b51705149706b6841397541415330385273774f5272724874354c6e6d445a6b702e4a48466847627257', 'hex')),
  (5, 'sofia.martinez@rau.edu.ar','Sofía Martínez',    'sofiam', 'Estudiante','Estudiante de primer año, con interés en ciberseguridad','https://example.com/avatar_sofia.jpg', decode('2432622431322466775132585242534a63514b51705149706b6841397541415330385273774f5272724874354c6e6d445a6b702e4a48466847627257', 'hex'));

-- ------------------------------------------------------------
-- Preferencias de usuario (onboarding)
-- Cada fila representa la carrera y cuatrimestre principal del usuario.
INSERT INTO preferencia_usuario (usuario_id, carrera_nombre, cuatrimestre, on_boarded)
VALUES
  (1, 'Ing. en Informática', 8, TRUE),
  (2, 'Ing. en Informática', 8, TRUE),
  (3, 'Ing. en Informática', 3, TRUE),
  (4, 'Ing. en Informática', 2, TRUE),
  (5, 'Lic. en Economía',    1, TRUE);

-- ------------------------------------------------------------
-- Comunidades (materias/grupos)
-- es_oficial indica si es una comunidad oficial de la institución.
-- creado_por referencia al usuario creador.
INSERT INTO comunidad (comunidad_id, nombre, descripcion, es_oficial, creado_por)
VALUES
  (1, 'Ingeniería Informática',           'Carrera de Ingeniería en Informática de RAU',                                TRUE,  1),
  (2, 'Algoritmos y Estructuras de Datos','Espacio para dudas y recursos de AAyED',                                     FALSE, 1),
  (3, 'Redes II',                          'Comunidad sobre redes avanzadas y protocolos',                               FALSE, 2),
  (4, 'Base de Datos',                     'Teoría y práctica de bases de datos',                                        FALSE, 1),
  (5, 'Ciencia de Datos',                  'Discusión sobre proyectos de data science y machine learning',               FALSE, 3);

-- ------------------------------------------------------------
-- Membresías en comunidades
-- rol: 'O' propietario, 'M' moderador, 'U' miembro.
INSERT INTO comunidad_miembro (comunidad_id, usuario_id, rol)
VALUES
  (1, 1, 'O'),
  (1, 2, 'M'),
  (1, 3, 'U'),
  (1, 4, 'U'),
  (1, 5, 'U'),
  (2, 1, 'O'),
  (2, 3, 'U'),
  (2, 4, 'U'),
  (3, 2, 'O'),
  (3, 3, 'U'),
  (3, 4, 'U'),
  (4, 1, 'O'),
  (4, 3, 'U'),
  (5, 3, 'O'),
  (5, 4, 'U'),
  (5, 5, 'U'),
  (5, 2, 'U');

-- ------------------------------------------------------------
-- Publicaciones (posts)
-- Cada post pertenece a una comunidad y tiene un autor.
INSERT INTO post (post_id, comunidad_id, autor_id, titulo, cuerpo, mejor_comentario_id, estado)
VALUES
  (1, 1, 1, 'Bienvenidos a Ingeniería Informática',          'Este es el espacio para compartir novedades y recursos de la carrera.', NULL, 'A'),
  (2, 2, 3, 'Duda sobre complejidad de algoritmos',           '¿Alguien puede explicar la diferencia entre O(log n) y O(n)?',           NULL, 'A'),
  (3, 2, 4, 'Compartir apuntes de recursión',                 'Dejo mis apuntes sobre recursión y divide y conquista.',                 NULL, 'A'),
  (4, 3, 2, 'Material de protocolos TCP/IP',                  'Aquí tienen los enlaces a la RFC y los manuales oficiales.',             NULL, 'A'),
  (5, 5, 3, 'Introducción a pandas',                          'Algunos recursos para comenzar con pandas y análisis de datos.',         NULL, 'A'),
  (6, 4, 1, 'Consulta sobre normalización',                   '¿Qué diferencias hay entre 3FN y BCNF?',                                  NULL, 'A');

-- ------------------------------------------------------------
-- Comentarios
-- comentarios pueden ser toplevel (comentario_padre_id = NULL) o respuestas anidadas.
INSERT INTO comentario (comentario_id, post_id, autor_id, comentario_padre_id, cuerpo)
VALUES
  (1, 1, 3, NULL, '¡Gracias, profe! Muy útil el espacio.'),
  (2, 2, 1, NULL, 'La complejidad logarítmica crece mucho más lento que la lineal.'),
  (3, 2, 2, NULL, 'Sumo un recurso que puede servirte: [enlace].'),
  (4, 3, 5, NULL, '¡Excelente resumen, Juan! Me ayudó mucho.'),
  (5, 5, 4, NULL, 'Recomiendo también practicar con NumPy antes de pandas.'),
  (6, 5, 3, 5,    'Sí, es cierto; NumPy es fundamental.'),
  (7, 6, 2, NULL, 'BCNF es más estricta y evita ciertas dependencias.');

-- ------------------------------------------------------------
-- Marcar el mejor comentario de la pregunta sobre complejidad
UPDATE post SET mejor_comentario_id = 2 WHERE post_id = 2;

-- ------------------------------------------------------------
-- Votos en publicaciones
-- valor: 1 (upvote), -1 (downvote)
INSERT INTO post_voto (post_id, usuario_id, valor)
VALUES
  (1, 3,  1),  -- María upvota el saludo del profesor
  (1, 4,  1),  -- Juan upvota el saludo del profesor
  (2, 4,  1),  -- Juan upvota la duda de María
  (2, 5,  1),  -- Sofía upvota la duda de María
  (3, 3,  1),  -- María upvota el post de Juan
  (3, 5, -1),  -- Sofía considera menos útil el post de Juan
  (4, 3,  1),  -- María upvota el material de Redes
  (4, 5,  1),  -- Sofía upvota el material de Redes
  (5, 4,  1),  -- Juan upvota el post de pandas
  (5, 2,  1),  -- Carlos upvota el post de pandas
  (5, 5, -1),  -- Sofía downvota el post de pandas
  (6, 3,  1);  -- María upvota la consulta sobre normalización

-- ------------------------------------------------------------
-- Votos en comentarios
INSERT INTO comentario_voto (comentario_id, usuario_id, valor)
VALUES
  (1, 4,  1),  -- Juan upvota el agradecimiento de María
  (2, 3,  1),  -- María upvota la explicación del profesor
  (2, 4,  1),  -- Juan también upvota esa explicación
  (3, 5,  1),  -- Sofía upvota el recurso aportado por Carlos
  (5, 2,  1),  -- Carlos upvota el comentario sobre NumPy
  (6, 2,  1),  -- Carlos upvota la respuesta de María a Juan
  (7, 3,  1);  -- María upvota la aclaración sobre BCNF

-- ------------------------------------------------------------
-- Posts guardados (bookmarks)
INSERT INTO post_guardado (post_id, usuario_id)
VALUES
  (2, 3),  -- María guarda su propia pregunta para seguirla
  (5, 5),  -- Sofía guarda el post sobre pandas
  (1, 4);  -- Juan guarda el anuncio de bienvenida

COMMIT;


----------- Workaround aplicado sobre error de publicación de POSTS -----------

SELECT setval(pg_get_serial_sequence('post', 'post_id'), (SELECT MAX(post_id) FROM post));
-- ... POSTs - datos dummy ...
SELECT setval('post_post_id_seq', (SELECT MAX(post_id) FROM post));

-- ... USUARIOs - datos dummy ...
SELECT setval(pg_get_serial_sequence('usuario', 'usuario_id'), (SELECT MAX(usuario_id) FROM usuario));
SELECT setval('post_post_id_seq', (SELECT MAX(usuario_id) FROM usuario));


----------- Workaround aplicado sobre error de tipos de publicaciones POST -----------

ALTER TABLE post ADD COLUMN etiqueta VARCHAR(20) NOT NULL DEFAULT 'Pregunta';
-- Definición de valores permitidos (ya que estamos, no hay porqué no)
ALTER TABLE post ADD CONSTRAINT ck_post_etiqueta CHECK (etiqueta IN ('Pregunta', 'Recurso', 'Apunte', 'Discusión'));
