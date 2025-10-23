from models.database import get_connection
from psycopg2 import DatabaseError

def obtener_escuela_por_director(usuario_id):
    """Obtener la escuela asignada a un director"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.escuela_id,
                e.cct,
                e.nombre,
                e.direccion,
                e.municipio,
                e.entidad,
                e.turno,
                e.zona_escolar,
                e.cupo_total,
                e.telefono,
                e.correo_contacto,
                e.activo
            FROM escuelas e
            WHERE e.director_usuario_id = %s
            AND e.activo = TRUE
            LIMIT 1
        """, (usuario_id,))
        return cursor.fetchone()
    except DatabaseError as e:
        print(f"Error al obtener escuela del director: {e}")
        return None
    finally:
        conn.close()

def obtener_estadisticas_escuela(escuela_id, ciclo_id=None):
    """Obtener estadísticas de una escuela específica"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Si no se proporciona ciclo, usar el activo
        if not ciclo_id:
            cursor.execute("SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1")
            ciclo = cursor.fetchone()
            ciclo_id = ciclo['ciclo_id'] if ciclo else None
        
        if not ciclo_id:
            return None
        
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE i.status = 'pendiente') AS pendientes,
                COUNT(*) FILTER (WHERE i.status = 'en_revision') AS en_revision,
                COUNT(*) FILTER (WHERE i.status = 'aceptado') AS aceptados,
                COUNT(*) FILTER (WHERE i.status = 'rechazado') AS rechazados,
                COUNT(*) AS total_solicitudes,
                e.cupo_total,
                (e.cupo_total - COUNT(*) FILTER (WHERE i.status = 'aceptado')) AS cupos_disponibles
            FROM escuelas e
            LEFT JOIN inscripciones i ON e.escuela_id = i.escuela_id AND i.ciclo_id = %s
            WHERE e.escuela_id = %s
            GROUP BY e.escuela_id, e.cupo_total
        """, (ciclo_id, escuela_id))
        
        return cursor.fetchone()
    except DatabaseError as e:
        print(f"Error al obtener estadísticas: {e}")
        return None
    finally:
        conn.close()

def obtener_grupos_escuela(escuela_id, ciclo_id=None):
    """Obtener todos los grupos de una escuela"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Si no se proporciona ciclo, usar el activo
        if not ciclo_id:
            cursor.execute("SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1")
            ciclo = cursor.fetchone()
            ciclo_id = ciclo['ciclo_id'] if ciclo else None
        
        cursor.execute("""
            SELECT 
                gr.grupo_id,
                gr.nombre_grupo,
                g.nivel AS grado_nivel,
                g.descripcion AS grado_descripcion,
                gr.cupo,
                gr.alumnos_inscritos,
                (gr.cupo - gr.alumnos_inscritos) AS cupos_disponibles,
                u.nombre || ' ' || u.apellido_paterno || ' ' || u.apellido_materno AS docente_nombre
            FROM grupos gr
            INNER JOIN grados g ON gr.grado_id = g.grado_id
            LEFT JOIN usuarios u ON gr.docente_usuario_id = u.usuario_id
            WHERE gr.escuela_id = %s AND gr.ciclo_id = %s
            ORDER BY g.nivel, gr.nombre_grupo
        """, (escuela_id, ciclo_id))
        
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener grupos: {e}")
        return []
    finally:
        conn.close()

def obtener_alumnos_por_grupo(grupo_id):
    """Obtener lista de alumnos inscritos en un grupo"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                a.alumno_id,
                a.nombre || ' ' || a.apellido_paterno || ' ' || a.apellido_materno AS nombre_completo,
                a.curp,
                a.fecha_nacimiento,
                EXTRACT(YEAR FROM AGE(a.fecha_nacimiento)) AS edad,
                t.nombre || ' ' || t.apellido_paterno AS tutor_nombre,
                t.telefono AS tutor_telefono,
                i.fecha_solicitud
            FROM inscripciones i
            INNER JOIN alumnos a ON i.alumno_id = a.alumno_id
            LEFT JOIN alumno_tutor at ON a.alumno_id = at.alumno_id AND at.es_representante = TRUE
            LEFT JOIN tutores t ON at.tutor_id = t.tutor_id
            WHERE i.grupo_id = %s AND i.status = 'aceptado'
            ORDER BY a.apellido_paterno, a.apellido_materno, a.nombre
        """, (grupo_id,))
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener alumnos del grupo: {e}")
        return []
    finally:
        conn.close()

def crear_grupo(escuela_id, grado_id, ciclo_id, nombre_grupo, cupo, docente_usuario_id=None):
    """Crear un nuevo grupo en la escuela"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO grupos (escuela_id, grado_id, ciclo_id, nombre_grupo, cupo, docente_usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING grupo_id
        """, (escuela_id, grado_id, ciclo_id, nombre_grupo, cupo, docente_usuario_id))
        
        resultado = cursor.fetchone()
        if not resultado:
            raise ValueError("No se pudo crear el grupo")
        
        grupo_id = resultado['grupo_id']
        conn.commit()
        
        print(f"✅ Grupo creado exitosamente con ID: {grupo_id}")
        return grupo_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al crear grupo: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def actualizar_grupo(grupo_id, nombre_grupo=None, cupo=None, docente_usuario_id=None):
    """Actualizar información de un grupo"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente según los parámetros proporcionados
        updates = []
        params = []
        
        if nombre_grupo is not None:
            updates.append("nombre_grupo = %s")
            params.append(nombre_grupo)
        
        if cupo is not None:
            updates.append("cupo = %s")
            params.append(cupo)
        
        if docente_usuario_id is not None:
            updates.append("docente_usuario_id = %s")
            params.append(docente_usuario_id)
        
        if not updates:
            return True  # No hay nada que actualizar
        
        params.append(grupo_id)
        query = f"UPDATE grupos SET {', '.join(updates)} WHERE grupo_id = %s"
        
        cursor.execute(query, params)
        conn.commit()
        
        print(f"✅ Grupo {grupo_id} actualizado exitosamente")
        return True
        
    except DatabaseError as e:
        print(f"❌ Error al actualizar grupo: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()