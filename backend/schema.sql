-- 1. Tabla de Roles (RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

-- Insertar roles base para nuam
INSERT INTO roles (nombre_rol) 
VALUES 
    ('Analista'),
    ('Aprobador'),
    ('Auditor')
ON CONFLICT (nombre_rol) DO NOTHING;

-- 2. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(12) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES roles(id) ON DELETE RESTRICT
);

-- 3. Tabla de Declaraciones Juradas (DJ 1949 / 1922)
CREATE TABLE IF NOT EXISTS declaraciones_tributarias (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(50) NOT NULL UNIQUE,
    rut_empresa VARCHAR(12) NOT NULL,
    periodo_tributario INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Borrador' CHECK (estado IN ('Borrador', 'Pendiente', 'Aprobado', 'Rechazado')),
    id_usuario_creador INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_declaracion_usuario FOREIGN KEY (id_usuario_creador) REFERENCES usuarios(id)
);

-- 4. Tabla de Factores Tributarios
CREATE TABLE IF NOT EXISTS factores_tributarios (
    id SERIAL PRIMARY KEY,
    id_declaracion INT NOT NULL UNIQUE,
    factor_1 NUMERIC(12, 8) DEFAULT 0.00000000,
    factor_2 NUMERIC(12, 8) DEFAULT 0.00000000,
    factor_3 NUMERIC(12, 8) DEFAULT 0.00000000,
    factor_29 NUMERIC(12, 8) DEFAULT 0.00000000,
    suma_factores_criticos NUMERIC(12, 8) NOT NULL,
    es_valido BOOLEAN DEFAULT TRUE,
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_factores_declaracion FOREIGN KEY (id_declaracion) REFERENCES declaraciones_tributarias(id) ON DELETE CASCADE,
    CONSTRAINT chk_suma_maxima CHECK (suma_factores_criticos <= 1.00000000)
);