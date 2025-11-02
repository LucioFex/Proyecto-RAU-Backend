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
