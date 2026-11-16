CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO roles (nombre_rol)
VALUES ('Analista'), ('Aprobador'), ('Auditor')
ON CONFLICT (nombre_rol) DO NOTHING;

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(12) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol) REFERENCES roles(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS declaraciones_tributarias (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(50) NOT NULL UNIQUE,
    rut_empresa VARCHAR(12) NOT NULL,
    periodo_tributario INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Borrador'
        CHECK (estado IN ('Borrador', 'Pendiente', 'Aprobado', 'Rechazado')),
    id_usuario_creador INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_declaracion_usuario
        FOREIGN KEY (id_usuario_creador) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS factores_tributarios (
    id SERIAL PRIMARY KEY,
    id_declaracion INT NOT NULL UNIQUE,
    factor_1 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_2 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_3 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_4 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_5 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_6 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_7 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_8 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_9 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_10 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_11 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_12 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_13 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_14 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_15 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_16 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_17 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_18 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_19 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_20 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_21 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_22 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_23 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_24 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_25 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_26 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_27 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_28 NUMERIC(20, 8) DEFAULT 0.00000000,
    factor_29 NUMERIC(20, 8) DEFAULT 0.00000000,
    suma_factores_criticos NUMERIC(20, 8) NOT NULL,
    es_valido BOOLEAN DEFAULT TRUE,
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_factores_declaracion
        FOREIGN KEY (id_declaracion) REFERENCES declaraciones_tributarias(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_suma_maxima
        CHECK (suma_factores_criticos <= 1.00000000),
    CONSTRAINT chk_factores_no_negativos
        CHECK (
            factor_1 >= 0 AND factor_2 >= 0 AND factor_3 >= 0
            AND factor_4 >= 0 AND factor_5 >= 0 AND factor_6 >= 0
            AND factor_7 >= 0 AND factor_8 >= 0 AND factor_9 >= 0
            AND factor_10 >= 0 AND factor_11 >= 0 AND factor_12 >= 0
            AND factor_13 >= 0 AND factor_14 >= 0 AND factor_15 >= 0
            AND factor_16 >= 0 AND factor_17 >= 0 AND factor_18 >= 0
            AND factor_19 >= 0 AND factor_20 >= 0 AND factor_21 >= 0
            AND factor_22 >= 0 AND factor_23 >= 0 AND factor_24 >= 0
            AND factor_25 >= 0 AND factor_26 >= 0 AND factor_27 >= 0
            AND factor_28 >= 0 AND factor_29 >= 0
        )
);

CREATE INDEX IF NOT EXISTS idx_usuarios_rut ON usuarios (rut);
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira_en TIMESTAMPTZ NOT NULL,
    revocado_en TIMESTAMPTZ,
    CONSTRAINT fk_refresh_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_usuario
    ON refresh_tokens (usuario_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expiracion
    ON refresh_tokens (expira_en);
CREATE INDEX IF NOT EXISTS idx_declaraciones_rut_empresa
    ON declaraciones_tributarias (rut_empresa);
CREATE INDEX IF NOT EXISTS idx_declaraciones_periodo
    ON declaraciones_tributarias (periodo_tributario);
CREATE INDEX IF NOT EXISTS idx_declaraciones_estado
    ON declaraciones_tributarias (estado);

CREATE TABLE IF NOT EXISTS calificaciones_tributarias (
    id SERIAL PRIMARY KEY,
    corredor_id INT NOT NULL,
    ejercicio INT NOT NULL CHECK (ejercicio BETWEEN 1900 AND 2200),
    mercado VARCHAR(10) NOT NULL CHECK (mercado IN ('ACN', 'CFI', 'FFMM')),
    instrumento VARCHAR(50) NOT NULL,
    fecha_pago DATE NOT NULL,
    secuencia BIGINT NOT NULL CHECK (secuencia > 10000),
    numero_dividendo INT NOT NULL DEFAULT 0,
    tipo_sociedad CHAR(1) NOT NULL DEFAULT 'A' CHECK (tipo_sociedad IN ('A', 'C')),
    valor_historico NUMERIC(18, 2) NOT NULL DEFAULT 0,
    acogido_isfut BOOLEAN NOT NULL DEFAULT FALSE,
    factor_actualizacion NUMERIC(12, 8) NOT NULL DEFAULT 0,
    descripcion TEXT,
    origen VARCHAR(20) NOT NULL DEFAULT 'CORREDORA' CHECK (origen IN ('CORREDORA', 'SISTEMA')),
    fuente_ingreso VARCHAR(30) NOT NULL DEFAULT 'MANUAL'
        CHECK (fuente_ingreso IN ('MANUAL', 'CSV_FACTORES', 'CSV_MONTOS', 'SISTEMA')),
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado IN ('Pendiente', 'Aprobado', 'Rechazado')),
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_modificacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (corredor_id, ejercicio, mercado, instrumento, secuencia, fecha_pago)
);

DO $$
DECLARE
    indice integer;
BEGIN
    FOR indice IN 8..37 LOOP
        EXECUTE format('ALTER TABLE calificaciones_tributarias ADD COLUMN IF NOT EXISTS monto_%s NUMERIC(18, 2)', indice);
        EXECUTE format('ALTER TABLE calificaciones_tributarias ADD COLUMN IF NOT EXISTS factor_%s NUMERIC(12, 8) NOT NULL DEFAULT 0', indice);
    END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS idx_calificaciones_filtros
    ON calificaciones_tributarias (corredor_id, ejercicio, mercado, estado);
