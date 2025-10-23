CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('super_admin','sep_admin','director','docente','tutor','alumno');
CREATE TYPE doc_status AS ENUM ('pendiente','recibido','validado','rechazado');
CREATE TYPE enroll_status AS ENUM ('pendiente','en_revision','aceptado','rechazado');
CREATE TYPE school_shift AS ENUM ('matutino','vespertino','mixto');

SELECT * FROM pg_type WHERE typname = 'user_role';

SELECT * FROM usuarios WHERE correo = 'edgarroa32@gmail.com';

INSERT INTO usuarios (nombre, apellido_paterno, apellido_materno, correo, password_hash, rol)
VALUES ('Edgar', 'Marquez', 'Roa', 'edgarroa32@gmail.com', 'hash_prueba', 'tutor')
RETURNING usuario_id;

DELETE FROM usuarios WHERE correo = 'edgarroa32@gmail.com';

CREATE TABLE usuarios (
    usuario_id SERIAL PRIMARY KEY,
    correo VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NOT NULL,
    rol user_role NOT NULL,
    password_hash TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP WITH TIME ZONE
);

CREATE TABLE escuelas (
    escuela_id SERIAL PRIMARY KEY,
    cct VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    municipio VARCHAR(150),
    entidad VARCHAR(100),
    turno school_shift DEFAULT 'matutino',
    zona_escolar VARCHAR(100),
    cupo_total INTEGER DEFAULT 0 CHECK (cupo_total >= 0),
    telefono VARCHAR(50),
    correo_contacto VARCHAR(255),
    director_usuario_id INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ciclos (
    ciclo_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activo BOOLEAN DEFAULT FALSE,
    inscripciones_abiertas BOOLEAN DEFAULT TRUE,
    CHECK (fecha_fin > fecha_inicio)
);

CREATE TABLE grados (
    grado_id SERIAL PRIMARY KEY,
    nivel INTEGER NOT NULL UNIQUE CHECK (nivel BETWEEN 1 AND 6),
    descripcion VARCHAR(100) NOT NULL
);

CREATE TABLE grupos (
    grupo_id SERIAL PRIMARY KEY,
    escuela_id INTEGER NOT NULL REFERENCES escuelas(escuela_id) ON DELETE CASCADE,
    grado_id INTEGER NOT NULL REFERENCES grados(grado_id) ON DELETE RESTRICT,
    ciclo_id INTEGER NOT NULL REFERENCES ciclos(ciclo_id) ON DELETE RESTRICT,
    nombre_grupo VARCHAR(10) NOT NULL,
    cupo INTEGER DEFAULT 30 CHECK (cupo > 0),
    alumnos_inscritos INTEGER DEFAULT 0 CHECK (alumnos_inscritos >= 0),
    docente_usuario_id INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    UNIQUE (escuela_id, grado_id, ciclo_id, nombre_grupo),
    CHECK (alumnos_inscritos <= cupo)
);

CREATE TABLE tutores (
    tutor_id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NOT NULL,
    parentesco VARCHAR(100),
    telefono VARCHAR(50),
    correo VARCHAR(255),
    direccion TEXT,
    curp VARCHAR(18),
    identificacion_oficial TEXT,
    edad INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alumnos (
    alumno_id SERIAL PRIMARY KEY,
    curp VARCHAR(18) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    sexo CHAR(1) CHECK (sexo IN ('M','F')),
    direccion TEXT,
    municipio VARCHAR(150),
    entidad VARCHAR(100),
    telefono VARCHAR(50),
    nacionalidad VARCHAR(100) DEFAULT 'Mexicana',
    escuela_procedencia VARCHAR(255),
    creado_por_usuario_id INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    creado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (fecha_nacimiento < CURRENT_DATE)
);

CREATE TABLE alumno_tutor (
    alumno_id INTEGER NOT NULL REFERENCES alumnos(alumno_id) ON DELETE CASCADE,
    tutor_id INTEGER NOT NULL REFERENCES tutores(tutor_id) ON DELETE CASCADE,
    es_representante BOOLEAN DEFAULT FALSE,
    contacto_orden INTEGER DEFAULT 1 CHECK (contacto_orden > 0),
    PRIMARY KEY (alumno_id, tutor_id)
);

CREATE TABLE tipos_documento (
    tipo_doc_id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    requerido BOOLEAN DEFAULT TRUE,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE documento_alumno (
    documento_id SERIAL PRIMARY KEY,
    alumno_id INTEGER NOT NULL REFERENCES alumnos(alumno_id) ON DELETE CASCADE,
    tipo_doc_id INTEGER NOT NULL REFERENCES tipos_documento(tipo_doc_id) ON DELETE RESTRICT,
    archivo_url TEXT,
    archivo BYTEA,
    mime_type VARCHAR(50),
    nombre_archivo VARCHAR(255),
    uploaded_by INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    status doc_status DEFAULT 'pendiente',
    observaciones TEXT,
    fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_validacion TIMESTAMP WITH TIME ZONE,
    validado_por INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    UNIQUE (alumno_id, tipo_doc_id),
    CHECK (archivo_url IS NOT NULL OR archivo IS NOT NULL)
);

CREATE TABLE inscripciones (
    inscripcion_id SERIAL PRIMARY KEY,
    alumno_id INTEGER NOT NULL REFERENCES alumnos(alumno_id) ON DELETE CASCADE,
    escuela_id INTEGER NOT NULL REFERENCES escuelas(escuela_id) ON DELETE CASCADE,
    ciclo_id INTEGER NOT NULL REFERENCES ciclos(ciclo_id) ON DELETE RESTRICT,
    grado_id INTEGER NOT NULL REFERENCES grados(grado_id) ON DELETE RESTRICT,
    grupo_id INTEGER REFERENCES grupos(grupo_id) ON DELETE SET NULL,
    fecha_solicitud TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status enroll_status DEFAULT 'pendiente',
    motivo_rechazo TEXT,
    usuario_responsable INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    fecha_revision TIMESTAMP WITH TIME ZONE,
    revisado_por INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    UNIQUE (alumno_id, ciclo_id)
);

CREATE TABLE notificaciones (
    notificacion_id SERIAL PRIMARY KEY,
    tutor_id INTEGER REFERENCES tutores(tutor_id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    inscripcion_id INTEGER REFERENCES inscripciones(inscripcion_id) ON DELETE CASCADE,
    tipo VARCHAR(50) CHECK (tipo IN ('inscripcion', 'documento', 'general', 'recordatorio')),
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    creado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_envio TIMESTAMP WITH TIME ZONE,
    CHECK (tutor_id IS NOT NULL OR usuario_id IS NOT NULL)
);

CREATE TABLE audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
    tabla_afectada VARCHAR(100),
    accion VARCHAR(255) NOT NULL,
    registro_id INTEGER,
    detalles JSONB,
    ip_address INET,
    creado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expediente_medico (
    alumno_id INTEGER PRIMARY KEY REFERENCES alumnos(alumno_id) ON DELETE CASCADE,
    tipo_sangre VARCHAR(3),
    alergias TEXT,
    condiciones TEXT,
    medicamentos TEXT,
    seguro_medico VARCHAR(100),
    observaciones TEXT,
    actualizado_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--Funciones y triggers

CREATE OR REPLACE FUNCTION ensure_single_active_ciclo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.activo = TRUE THEN
        UPDATE ciclos
        SET activo = FALSE
        WHERE ciclo_id != NEW.ciclo_id AND activo = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_single_active_ciclo
BEFORE INSERT OR UPDATE ON ciclos
FOR EACH ROW
WHEN (NEW.activo = TRUE)
EXECUTE FUNCTION ensure_single_active_ciclo();

-- funcion actualizar contador de alumnos en grupos
CREATE OR REPLACE FUNCTION actualizar_alumnos_grupo()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status = 'aceptado' AND NEW.grupo_id IS NOT NULL THEN
            UPDATE grupos
            SET alumnos_inscritos = alumnos_inscritos + 1
            WHERE grupo_id = NEW.grupo_id;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
-- cambio de no aceptado a aceptado
        IF OLD.status != 'aceptado' AND NEW.status = 'aceptado' AND NEW.grupo_id IS NOT NULL THEN
            UPDATE grupos
            SET alumnos_inscritos = alumnos_inscritos + 1
            WHERE grupo_id = NEW.grupo_id;
-- cambio de aceptado a no aceptado
        ELSIF OLD.status = 'aceptado' AND NEW.status != 'aceptado' AND OLD.grupo_id IS NOT NULL THEN
            UPDATE grupos
            SET alumnos_inscritos = GREATEST(0, alumnos_inscritos - 1)
            WHERE grupo_id = OLD.grupo_id;
-- cambio de grupo (manteniendo status aceptado)
        ELSIF OLD.status = 'aceptado' AND NEW.status = 'aceptado' AND OLD.grupo_id != NEW.grupo_id THEN
            IF OLD.grupo_id IS NOT NULL THEN
                UPDATE grupos
                SET alumnos_inscritos = GREATEST(0, alumnos_inscritos - 1)
                WHERE grupo_id = OLD.grupo_id;
            END IF;
            IF NEW.grupo_id IS NOT NULL THEN
                UPDATE grupos
                SET alumnos_inscritos = alumnos_inscritos + 1
                WHERE grupo_id = NEW.grupo_id;
            END IF;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.status = 'aceptado' AND OLD.grupo_id IS NOT NULL THEN
            UPDATE grupos
            SET alumnos_inscritos = GREATEST(0, alumnos_inscritos - 1)
            WHERE grupo_id = OLD.grupo_id;
        END IF;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actualizar_alumnos_grupo
AFTER INSERT OR UPDATE OR DELETE ON inscripciones
FOR EACH ROW
EXECUTE FUNCTION actualizar_alumnos_grupo();

--- funcion: actualizar timestamp en alumnos
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_alumnos_actualizado
BEFORE UPDATE ON alumnos
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();

-- Funcion: valudar que solo un tutor sea representante
CREATE OR REPLACE FUNCTION validar_representante_unico()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.es_representante = TRUE THEN
        UPDATE alumno_tutor
        SET es_representante = FALSE
        WHERE alumno_id = NEW.alumno_id AND tutor_id != NEW.tutor_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_representante_unico
BEFORE INSERT OR UPDATE ON alumno_tutor
FOR EACH ROW
WHEN (NEW.es_representante = TRUE)
EXECUTE FUNCTION validar_representante_unico();

---FUNCIONES AUXILIARES PARA NOMBRE COMPLETO
CREATE OR REPLACE FUNCTION nombre_completo_usuario(uid INTEGER)
RETURNS TEXT AS $$
DECLARE
    resultado TEXT;
BEGIN
    SELECT CONCAT(nombre, ' ', apellido_paterno, ' ', apellido_materno)
    INTO resultado
    FROM usuarios
    WHERE usuario_id = uid;
    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION nombre_completo_alumno(aid INTEGER)
RETURNS TEXT AS $$
DECLARE
    resultado TEXT;
BEGIN
    SELECT CONCAT(nombre, ' ', apellido_paterno, ' ', apellido_materno)
    INTO resultado
    FROM alumnos
    WHERE alumno_id = aid;
    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION nombre_completo_tutor(tid INTEGER)
RETURNS TEXT AS $$
DECLARE
    resultado TEXT;
BEGIN
    SELECT CONCAT(nombre, ' ', apellido_paterno, ' ', apellido_materno)
    INTO resultado
    FROM tutores
    WHERE tutor_id = tid;
    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

---INDICES ----
-- Usuarios
CREATE INDEX idx_usuarios_email ON usuarios(correo);
CREATE INDEX idx_usuarios_rol ON usuarios(rol) WHERE activo = TRUE;
CREATE INDEX idx_usuarios_activo ON usuarios(activo);

-- Alumnos
CREATE INDEX idx_alumnos_curp ON alumnos(curp);
CREATE INDEX idx_alumnos_creado_por ON alumnos(creado_por_usuario_id);
CREATE INDEX idx_alumnos_nombre_apellidos ON alumnos(nombre, apellido_paterno, apellido_materno);
-- Opcional: índice funcional para búsquedas por nombre completo
CREATE INDEX idx_alumnos_nombre_completo ON alumnos (
  (nombre || ' ' || apellido_paterno || ' ' || apellido_materno)
);

-- Inscripciones
CREATE INDEX idx_inscripciones_status ON inscripciones(status);
CREATE INDEX idx_inscripciones_escuela ON inscripciones(escuela_id);
CREATE INDEX idx_inscripciones_ciclo ON inscripciones(ciclo_id);
CREATE INDEX idx_inscripciones_alumno ON inscripciones(alumno_id);
CREATE INDEX idx_inscripciones_escuela_status ON inscripciones(escuela_id, status);

-- Documentos de alumnos
CREATE INDEX idx_documento_alumno_status ON documento_alumno(status);
CREATE INDEX idx_documento_alumno_alumno ON documento_alumno(alumno_id);

-- Escuelas
CREATE INDEX idx_escuelas_director ON escuelas(director_usuario_id);
CREATE INDEX idx_escuelas_cct ON escuelas(cct);
CREATE INDEX idx_escuelas_activo ON escuelas(activo);

-- Tutores
CREATE INDEX idx_tutores_usuario ON tutores(usuario_id);

-- Grupos
CREATE INDEX idx_grupos_escuela ON grupos(escuela_id);
CREATE INDEX idx_grupos_escuela_ciclo ON grupos(escuela_id, ciclo_id);

-- Notificaciones
CREATE INDEX idx_notificaciones_usuario ON notificaciones(usuario_id) WHERE leido = FALSE;
CREATE INDEX idx_notificaciones_tutor ON notificaciones(tutor_id) WHERE leido = FALSE;

-- Auditoría
CREATE INDEX idx_audit_logs_usuario ON audit_logs(usuario_id);
CREATE INDEX idx_audit_logs_fecha ON audit_logs(creado_at DESC);
CREATE INDEX idx_audit_logs_tabla ON audit_logs(tabla_afectada);

-- Relación alumno-tutor
CREATE INDEX idx_alumno_tutor_alumno ON alumno_tutor(alumno_id);
CREATE INDEX idx_alumno_tutor_representante ON alumno_tutor(alumno_id) WHERE es_representante = TRUE;

-- vistas
CREATE OR REPLACE VIEW vista_inscripciones_completa AS
SELECT 
    i.inscripcion_id,
    i.status,
    i.fecha_solicitud,
    i.fecha_revision,
    i.motivo_rechazo,
    a.alumno_id,
    a.curp,
    CONCAT(a.nombre, ' ', a.apellido_paterno, ' ', a.apellido_materno) AS alumno_nombre,
    a.fecha_nacimiento,
    EXTRACT(YEAR FROM AGE(a.fecha_nacimiento)) AS edad,
    e.escuela_id,
    e.cct,
    e.nombre AS escuela_nombre,
    e.municipio,
    e.entidad,
    c.ciclo_id,
    c.nombre AS ciclo_nombre,
    g.nivel AS grado_nivel,
    g.descripcion AS grado_descripcion,
    gr.grupo_id,
    gr.nombre_grupo,
    gr.cupo AS grupo_cupo,
    gr.alumnos_inscritos AS grupo_alumnos,
    t.tutor_id,
    CONCAT(t.nombre, ' ', t.apellido_paterno, ' ', t.apellido_materno) AS tutor_nombre,
    t.telefono AS tutor_telefono,
    t.correo AS tutor_correo,
    t.parentesco,
    CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', u.apellido_materno) AS responsable_revision,
    u.usuario_id AS responsable_usuario_id
FROM inscripciones i
INNER JOIN alumnos a ON i.alumno_id = a.alumno_id
INNER JOIN escuelas e ON i.escuela_id = e.escuela_id
INNER JOIN ciclos c ON i.ciclo_id = c.ciclo_id
INNER JOIN grados g ON i.grado_id = g.grado_id
LEFT JOIN grupos gr ON i.grupo_id = gr.grupo_id
LEFT JOIN alumno_tutor at ON a.alumno_id = at.alumno_id AND at.es_representante = TRUE
LEFT JOIN tutores t ON at.tutor_id = t.tutor_id
LEFT JOIN usuarios u ON i.revisado_por = u.usuario_id;
---Vista:Documentos pendientes por escuelas
CREATE OR REPLACE VIEW vista_documentos_pendientes AS
SELECT 
    e.escuela_id,
    e.nombre AS escuela_nombre,
    e.cct,
    a.alumno_id,
    CONCAT(a.nombre, ' ', a.apellido_paterno, ' ', a.apellido_materno) AS alumno_nombre,
    td.tipo_doc_id,
    td.codigo AS tipo_codigo,
    td.nombre AS tipo_documento,
    td.requerido,
    da.documento_id,
    da.status,
    da.fecha_subida,
    da.observaciones,
    i.inscripcion_id,
    i.status AS inscripcion_status
FROM documento_alumno da
INNER JOIN tipos_documento td ON da.tipo_doc_id = td.tipo_doc_id
INNER JOIN alumnos a ON da.alumno_id = a.alumno_id
INNER JOIN inscripciones i ON a.alumno_id = i.alumno_id
INNER JOIN escuelas e ON i.escuela_id = e.escuela_id
WHERE da.status IN ('pendiente', 'recibido')
  AND i.status IN ('pendiente', 'en_revision')
  AND td.activo = TRUE;

  --vista estadisticas por escuela
  CREATE OR REPLACE VIEW vista_estadisticas_escuela AS
SELECT 
    e.escuela_id,
    e.cct,
    e.nombre,
    e.municipio,
    e.entidad,
    e.turno,
    e.cupo_total,
    e.activo,
    CONCAT(d.nombre, ' ', d.apellido_paterno, ' ', d.apellido_materno) AS director_nombre,
    d.correo AS director_correo,
    COUNT(DISTINCT CASE WHEN i.status = 'aceptado' THEN i.alumno_id END) AS alumnos_aceptados,
    COUNT(DISTINCT CASE WHEN i.status = 'pendiente' THEN i.alumno_id END) AS solicitudes_pendientes,
    COUNT(DISTINCT CASE WHEN i.status = 'en_revision' THEN i.alumno_id END) AS solicitudes_en_revision,
    COUNT(DISTINCT CASE WHEN i.status = 'rechazado' THEN i.alumno_id END) AS solicitudes_rechazadas,
    COUNT(DISTINCT gr.grupo_id) AS grupos_totales,
    COALESCE(SUM(gr.cupo), 0) AS cupo_grupos,
    COALESCE(SUM(gr.alumnos_inscritos), 0) AS total_alumnos_en_grupos,
    e.cupo_total - COUNT(DISTINCT CASE WHEN i.status = 'aceptado' THEN i.alumno_id END) AS cupos_disponibles
FROM escuelas e
LEFT JOIN usuarios d ON e.director_usuario_id = d.usuario_id
LEFT JOIN inscripciones i ON e.escuela_id = i.escuela_id 
    AND i.ciclo_id = (SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1)
LEFT JOIN grupos gr ON e.escuela_id = gr.escuela_id 
    AND gr.ciclo_id = (SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1)
GROUP BY e.escuela_id, e.cct, e.nombre, e.municipio, e.entidad, e.turno, e.cupo_total, e.activo, d.nombre, d.apellido_paterno, d.apellido_materno, d.correo;
---vista:progreso de documentos por alumno
CREATE OR REPLACE VIEW vista_progreso_documentos AS
SELECT 
    a.alumno_id,
    CONCAT(a.nombre, ' ', a.apellido_paterno, ' ', a.apellido_materno) AS alumno_nombre,
    COUNT(DISTINCT td.tipo_doc_id) FILTER (WHERE td.requerido = TRUE) AS documentos_requeridos,
    COUNT(DISTINCT da.tipo_doc_id) FILTER (WHERE td.requerido = TRUE) AS documentos_subidos,
    COUNT(DISTINCT da.tipo_doc_id) FILTER (WHERE td.requerido = TRUE AND da.status = 'validado') AS documentos_validados,
    ROUND(
        100.0 * COUNT(DISTINCT da.tipo_doc_id) FILTER (WHERE td.requerido = TRUE) / 
        NULLIF(COUNT(DISTINCT td.tipo_doc_id) FILTER (WHERE td.requerido = TRUE), 0), 
        2
    ) AS porcentaje_completado
FROM alumnos a
CROSS JOIN tipos_documento td
LEFT JOIN documento_alumno da ON a.alumno_id = da.alumno_id AND td.tipo_doc_id = da.tipo_doc_id
WHERE td.activo = TRUE
GROUP BY a.alumno_id, a.nombre, a.apellido_paterno, a.apellido_materno;
--funciones utiles
CREATE OR REPLACE FUNCTION obtener_documentos_faltantes(p_alumno_id INTEGER)
RETURNS TABLE(
    tipo_doc_id INTEGER, 
    codigo VARCHAR, 
    nombre VARCHAR,
    descripcion TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        td.tipo_doc_id, 
        td.codigo, 
        td.nombre,
        td.descripcion
    FROM tipos_documento td
    WHERE td.requerido = TRUE
      AND td.activo = TRUE
      AND NOT EXISTS (
          SELECT 1 
          FROM documento_alumno da 
          WHERE da.alumno_id = p_alumno_id
            AND da.tipo_doc_id = td.tipo_doc_id
      )
    ORDER BY td.nombre;
END;
$$ LANGUAGE plpgsql;
--Funcion: verificar si un alumno puede inscribirse
CREATE OR REPLACE FUNCTION puede_inscribirse(
    p_alumno_id INTEGER, 
    p_escuela_id INTEGER, 
    p_ciclo_id INTEGER
)
RETURNS TABLE(
    puede_inscribirse BOOLEAN,
    mensaje TEXT
) AS $$
DECLARE
    v_cupos_disponibles INTEGER;
    v_documentos_faltantes INTEGER;
    v_ya_inscrito BOOLEAN;
    v_ciclo_activo BOOLEAN;
    v_inscripciones_abiertas BOOLEAN;
BEGIN
    -- Verificar si el ciclo está activo y acepta inscripciones
    SELECT activo, inscripciones_abiertas 
    INTO v_ciclo_activo, v_inscripciones_abiertas
    FROM ciclos 
    WHERE ciclo_id = p_ciclo_id;

    IF NOT v_ciclo_activo THEN
        RETURN QUERY SELECT FALSE, 'El ciclo escolar no está activo';
        RETURN;
    END IF;

    IF NOT v_inscripciones_abiertas THEN
        RETURN QUERY SELECT FALSE, 'Las inscripciones están cerradas para este ciclo';
        RETURN;
    END IF;

    -- Verificar si ya está inscrito en este ciclo
    SELECT EXISTS(
        SELECT 1 FROM inscripciones 
        WHERE alumno_id = p_alumno_id 
          AND ciclo_id = p_ciclo_id
    ) INTO v_ya_inscrito;

    IF v_ya_inscrito THEN
        RETURN QUERY SELECT FALSE, 'El alumno ya tiene una solicitud de inscripción para este ciclo';
        RETURN;
    END IF;

    -- Verificar cupos disponibles
    SELECT cupos_disponibles INTO v_cupos_disponibles
    FROM vista_estadisticas_escuela
    WHERE escuela_id = p_escuela_id;

    IF v_cupos_disponibles <= 0 THEN
        RETURN QUERY SELECT FALSE, 'No hay cupos disponibles en la escuela';
        RETURN;
    END IF;

    -- Verificar documentos requeridos
    SELECT COUNT(*) INTO v_documentos_faltantes
    FROM obtener_documentos_faltantes(p_alumno_id);

    IF v_documentos_faltantes > 0 THEN
        RETURN QUERY SELECT FALSE, 
            'Faltan ' || v_documentos_faltantes || ' documento(s) requerido(s)';
        RETURN;
    END IF;

    -- Todo correcto
    RETURN QUERY SELECT TRUE, 'El alumno puede inscribirse';
END;
$$ LANGUAGE plpgsql;

-- funcion: obtener ciclo activo
CREATE OR REPLACE FUNCTION obtener_ciclo_activo()
RETURNS INTEGER AS $$
DECLARE
    v_ciclo_id INTEGER;
BEGIN
    SELECT ciclo_id INTO v_ciclo_id
    FROM ciclos
    WHERE activo = TRUE
    LIMIT 1;

    RETURN v_ciclo_id;
END;
$$ LANGUAGE plpgsql;

--funcion: Registrar actividad en auditoria
CREATE OR REPLACE FUNCTION registrar_auditoria(
    p_usuario_id INTEGER,
    p_tabla VARCHAR,
    p_accion VARCHAR,
    p_registro_id INTEGER DEFAULT NULL,
    p_detalles JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_audit_id BIGINT;
BEGIN
    INSERT INTO audit_logs (
        usuario_id, 
        tabla_afectada, 
        accion, 
        registro_id, 
        detalles, 
        ip_address
    )
    VALUES (
        p_usuario_id, 
        p_tabla, 
        p_accion, 
        p_registro_id, 
        p_detalles, 
        p_ip_address
    )
    RETURNING audit_id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

--Datos iniciales

--insertar grados
INSERT INTO grados (nivel, descripcion) VALUES
(1, 'Primer Grado'),
(2, 'Segundo Grado'),
(3, 'Tercer Grado'),
(4, 'Cuarto Grado'),
(5, 'Quinto Grado'),
(6, 'Sexto Grado')
ON CONFLICT (nivel) DO NOTHING;

--insertar tipos de documentos
INSERT INTO tipos_documento (codigo, nombre, descripcion, requerido) VALUES 
('acta_nac', 'Acta de Nacimiento', 'Acta de nacimiento original o copia certificada', TRUE),
('curp', 'CURP', 'CURP del alumno', TRUE),
('comprobante_dom', 'Comprobante de Domicilio', 'Recibo de luz, agua o predial no mayor a 3 meses', TRUE),
('cartilla_vac', 'Cartilla de Vacunación', 'Cartilla de vacunación actualizada', TRUE),
('cert_medico', 'Certificado Médico', 'Certificado médico vigente', FALSE),
('const_est', 'Constancia de Estudios', 'Solo para alumnos que cambian de escuela', FALSE),
('foto', 'Fotografía', '2 fotografías tamaño infantil a color', TRUE),
('ine_tutor', 'INE del Tutor', 'Identificación oficial del padre/madre/tutor', TRUE)
ON CONFLICT (codigo) DO NOTHING;

--insertar usuarios de ejemplo
INSERT INTO usuarios (correo, nombre, apellido_paterno, apellido_materno, rol, password_hash) VALUES
('admin@sep.gob.mx', 'Administrador', 'General', 'SEP', 'sep_admin', crypt('Admin2025!', gen_salt('bf'))),
('director.juarez@escuela.mx', 'Juan Carlos', 'Pérez', 'González', 'director', crypt('Director2025!', gen_salt('bf'))),
('director.hidalgo@escuela.mx', 'María Elena', 'López', 'Hernández', 'director', crypt('Director2025!', gen_salt('bf'))),
('tutor.ramirez@mail.com', 'Pedro', 'Ramírez', 'Torres', 'tutor', crypt('Tutor2025!', gen_salt('bf'))),
('tutor.martinez@mail.com', 'Ana Rosa', 'Martínez', 'Silva', 'tutor', crypt('Tutor2025!', gen_salt('bf')))
ON CONFLICT (correo) DO NOTHING;

--insertar escuelas
INSERT INTO escuelas (
    cct, nombre, direccion, municipio, entidad, turno, zona_escolar, cupo_total, telefono, director_usuario_id
) VALUES
('12DPR0012X', 'Primaria Benito Juárez', 'Av. Benito Juárez #123, Col. Centro', 'Cuauhtémoc', 'Ciudad de México', 'matutino', 'Zona 01', 300, '5555551234', 2),
('12DPR0034Y', 'Primaria Miguel Hidalgo', 'Calle Miguel Hidalgo #456, Col. Reforma', 'Guadalajara', 'Jalisco', 'vespertino', 'Zona 02', 250, '3333334567', 3),
('12DPR0056Z', 'Primaria Sor Juana Inés de la Cruz', 'Av. Constitución #789, Col. Juárez', 'Monterrey', 'Nuevo León', 'matutino', 'Zona 03', 280, '8188887890', NULL)
ON CONFLICT (cct) DO NOTHING;

-- insertar ciclo escolar
INSERT INTO ciclos (nombre, fecha_inicio, fecha_fin, activo, inscripciones_abiertas) VALUES
('2025-2026', '2025-08-20', '2026-07-15', TRUE, TRUE),
('2024-2025', '2024-08-20', '2025-07-15', FALSE, FALSE);
