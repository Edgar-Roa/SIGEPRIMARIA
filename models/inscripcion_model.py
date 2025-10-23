from models.database import get_connection
from psycopg2 import DatabaseError

def crear_inscripcion(alumno_id, escuela_id, ciclo_id, grado_id, usuario_responsable):
    """Crear nueva solicitud de inscripción - retorna inscripcion_id o None"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe una inscripción para este ciclo
        cursor.execute("""
            SELECT inscripcion_id FROM inscripciones 
            WHERE alumno_id = %s AND ciclo_id = %s
        """, (alumno_id, ciclo_id))
        
        if cursor.fetchone():
            print("⚠️ El alumno ya tiene una inscripción para este ciclo")
            return None
        
        # Crear inscripción
        cursor.execute("""
            INSERT INTO inscripciones (
                alumno_id, escuela_id, ciclo_id, grado_id, 
                status, usuario_responsable
            ) VALUES (%s, %s, %s, %s, 'pendiente', %s)
            RETURNING inscripcion_id
        """, (alumno_id, escuela_id, ciclo_id, grado_id, usuario_responsable))
        
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError("No se pudo obtener el inscripcion_id")
        
        inscripcion_id = resultado['inscripcion_id']
        conn.commit()
        
        print(f"✅ Inscripción creada exitosamente con ID: {inscripcion_id}")
        return inscripcion_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al crear inscripción: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def obtener_inscripciones_por_tutor(tutor_id):
    """Obtener todas las inscripciones de los alumnos de un tutor"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                i.inscripcion_id,
                i.status,
                i.fecha_solicitud,
                i.motivo_rechazo,
                a.alumno_id,
                a.nombre || ' ' || a.apellido_paterno || ' ' || a.apellido_materno AS alumno_nombre,
                e.nombre AS escuela_nombre,
                e.cct,
                c.nombre AS ciclo_nombre,
                g.descripcion AS grado,
                gr.nombre_grupo AS grupo
            FROM inscripciones i
            INNER JOIN alumnos a ON i.alumno_id = a.alumno_id
            INNER JOIN alumno_tutor at ON a.alumno_id = at.alumno_id
            INNER JOIN escuelas e ON i.escuela_id = e.escuela_id
            INNER JOIN ciclos c ON i.ciclo_id = c.ciclo_id
            INNER JOIN grados g ON i.grado_id = g.grado_id
            LEFT JOIN grupos gr ON i.grupo_id = gr.grupo_id
            WHERE at.tutor_id = %s
            ORDER BY i.fecha_solicitud DESC
        """, (tutor_id,))
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener inscripciones: {e}")
        return []
    finally:
        conn.close()

def obtener_escuelas_disponibles():
    """Obtener lista de escuelas activas con cupos disponibles"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.escuela_id,
                e.cct,
                e.nombre,
                e.municipio,
                e.entidad,
                e.turno,
                e.cupo_total,
                COALESCE(est.cupos_disponibles, e.cupo_total) AS cupos_disponibles
            FROM escuelas e
            LEFT JOIN vista_estadisticas_escuela est ON e.escuela_id = est.escuela_id
            WHERE e.activo = TRUE
            ORDER BY e.nombre
        """)
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener escuelas: {e}")
        return []
    finally:
        conn.close()

def obtener_ciclo_activo():
    """Obtener el ciclo escolar activo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ciclo_id, nombre, fecha_inicio, fecha_fin, inscripciones_abiertas
            FROM ciclos 
            WHERE activo = TRUE
            LIMIT 1
        """)
        return cursor.fetchone()
    except DatabaseError as e:
        print(f"Error al obtener ciclo activo: {e}")
        return None
    finally:
        conn.close()

def obtener_grados():
    """Obtener lista de grados disponibles"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT grado_id, nivel, descripcion FROM grados ORDER BY nivel")
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener grados: {e}")
        return []
    finally:
        conn.close()

def verificar_documentos_completos(alumno_id):
    """Verificar si el alumno tiene todos los documentos requeridos validados"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Contar documentos requeridos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM tipos_documento 
            WHERE requerido = TRUE AND activo = TRUE
        """)
        total_requeridos = cursor.fetchone()['total']
        
        # Contar documentos validados
        cursor.execute("""
            SELECT COUNT(*) as validados
            FROM documento_alumno da
            INNER JOIN tipos_documento td ON da.tipo_doc_id = td.tipo_doc_id
            WHERE da.alumno_id = %s 
            AND td.requerido = TRUE 
            AND da.status = 'validado'
        """, (alumno_id,))
        total_validados = cursor.fetchone()['validados']
        
        return total_validados >= total_requeridos
        
    except DatabaseError as e:
        print(f"Error al verificar documentos: {e}")
        return False
    finally:
        conn.close()

def puede_inscribirse_alumno(alumno_id, escuela_id):
    """Verificar si un alumno puede inscribirse en una escuela"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener ciclo activo
        cursor.execute("SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1")
        ciclo = cursor.fetchone()
        if not ciclo:
            return False, "No hay ciclo escolar activo"
        
        ciclo_id = ciclo['ciclo_id']
        
        # Usar la función de PostgreSQL
        cursor.execute("""
            SELECT puede_inscribirse, mensaje 
            FROM puede_inscribirse(%s, %s, %s)
        """, (alumno_id, escuela_id, ciclo_id))
        
        resultado = cursor.fetchone()
        return resultado['puede_inscribirse'], resultado['mensaje']
        
    except DatabaseError as e:
        print(f"Error al verificar elegibilidad: {e}")
        return False, "Error al verificar elegibilidad"
    finally:
        conn.close()

def obtener_inscripcion_detalle(inscripcion_id):
    """Obtener detalles completos de una inscripción"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vista_inscripciones_completa
            WHERE inscripcion_id = %s
        """, (inscripcion_id,))
        return cursor.fetchone()
    except DatabaseError as e:
        print(f"Error al obtener detalle de inscripción: {e}")
        return None
    finally:
        conn.close()

# ===== FUNCIONES PARA ADMINISTRADOR/DIRECTOR =====

def obtener_inscripciones_pendientes(escuela_id=None):
    """Obtener inscripciones pendientes de revisión"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if escuela_id:
            # Para directores: solo de su escuela
            cursor.execute("""
                SELECT * FROM vista_inscripciones_completa
                WHERE status IN ('pendiente', 'en_revision')
                AND escuela_id = %s
                ORDER BY fecha_solicitud ASC
            """, (escuela_id,))
        else:
            # Para admin SEP: todas las escuelas
            cursor.execute("""
                SELECT * FROM vista_inscripciones_completa
                WHERE status IN ('pendiente', 'en_revision')
                ORDER BY fecha_solicitud ASC
            """)
        
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener inscripciones pendientes: {e}")
        return []
    finally:
        conn.close()

def cambiar_estado_inscripcion(inscripcion_id, nuevo_estado, revisado_por, motivo_rechazo=None, grupo_id=None):
    """Cambiar el estado de una inscripción (aprobar/rechazar)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Validar estado
        estados_validos = ['pendiente', 'en_revision', 'aceptado', 'rechazado']
        if nuevo_estado not in estados_validos:
            print(f"❌ Estado inválido: {nuevo_estado}")
            return False
        
        # Actualizar inscripción
        cursor.execute("""
            UPDATE inscripciones
            SET status = %s::enroll_status,
                revisado_por = %s,
                fecha_revision = CURRENT_TIMESTAMP,
                motivo_rechazo = %s,
                grupo_id = %s
            WHERE inscripcion_id = %s
        """, (nuevo_estado, revisado_por, motivo_rechazo, grupo_id, inscripcion_id))
        
        conn.commit()
        print(f"✅ Inscripción {inscripcion_id} actualizada a estado: {nuevo_estado}")
        return True
        
    except DatabaseError as e:
        print(f"❌ Error al cambiar estado de inscripción: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def obtener_grupos_disponibles(escuela_id, ciclo_id, grado_id):
    """Obtener grupos disponibles para asignar un alumno"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                grupo_id,
                nombre_grupo,
                cupo,
                alumnos_inscritos,
                (cupo - alumnos_inscritos) AS cupos_disponibles
            FROM grupos
            WHERE escuela_id = %s
            AND ciclo_id = %s
            AND grado_id = %s
            AND (cupo - alumnos_inscritos) > 0
            ORDER BY nombre_grupo
        """, (escuela_id, ciclo_id, grado_id))
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener grupos disponibles: {e}")
        return []
    finally:
        conn.close()

def obtener_estadisticas_inscripciones(escuela_id=None):
    """Obtener estadísticas de inscripciones"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if escuela_id:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'pendiente') AS pendientes,
                    COUNT(*) FILTER (WHERE status = 'en_revision') AS en_revision,
                    COUNT(*) FILTER (WHERE status = 'aceptado') AS aceptados,
                    COUNT(*) FILTER (WHERE status = 'rechazado') AS rechazados,
                    COUNT(*) AS total
                FROM inscripciones
                WHERE escuela_id = %s
                AND ciclo_id = (SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1)
            """, (escuela_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'pendiente') AS pendientes,
                    COUNT(*) FILTER (WHERE status = 'en_revision') AS en_revision,
                    COUNT(*) FILTER (WHERE status = 'aceptado') AS aceptados,
                    COUNT(*) FILTER (WHERE status = 'rechazado') AS rechazados,
                    COUNT(*) AS total
                FROM inscripciones
                WHERE ciclo_id = (SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1)
            """)
        
        return cursor.fetchone()
    except DatabaseError as e:
        print(f"Error al obtener estadísticas: {e}")
        return None
    finally:
        conn.close()

def obtener_todas_inscripciones(escuela_id=None, filtro_status=None):
    """Obtener todas las inscripciones con filtros opcionales"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM vista_inscripciones_completa WHERE 1=1"
        params = []
        
        if escuela_id:
            query += " AND escuela_id = %s"
            params.append(escuela_id)
        
        if filtro_status:
            query += " AND status = %s"
            params.append(filtro_status)
        
        query += " ORDER BY fecha_solicitud DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener inscripciones: {e}")
        return []
    finally:
        conn.close()