from models.database import get_connection
from psycopg2 import DatabaseError

def registrar_tutor(usuario_id, nombre, apellido_paterno, apellido_materno, telefono, edad):
    """Registrar nuevo tutor - retorna tutor_id o None"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tutores (usuario_id, nombre, apellido_paterno, apellido_materno, telefono, edad)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING tutor_id
        """, (usuario_id, nombre, apellido_paterno, apellido_materno, telefono, edad))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("No se pudo obtener el tutor_id después del INSERT")
        
        # ✅ Acceso como diccionario
        tutor_id = resultado['tutor_id']
        conn.commit()
        
        print(f"✅ Tutor registrado exitosamente con ID: {tutor_id}")
        return tutor_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al registrar tutor: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def obtener_tutor_por_usuario(usuario_id):
    """Obtener tutor por ID de usuario - retorna dict o None"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tutores WHERE usuario_id = %s", (usuario_id,))
        tutor = cursor.fetchone()
        return tutor
    except DatabaseError as e:
        print(f"Error al obtener tutor: {e}")
        return None
    finally:
        conn.close()

def obtener_alumnos_de_tutor(tutor_id):
    """Obtener todos los alumnos de un tutor - retorna lista de dicts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.alumno_id,
                   a.nombre || ' ' || a.apellido_paterno || ' ' || a.apellido_materno AS nombre_completo,
                   g.nivel AS grado,
                   gr.nombre_grupo AS grupo,
                   e.turno
            FROM alumno_tutor at
            INNER JOIN alumnos a ON at.alumno_id = a.alumno_id
            LEFT JOIN inscripciones i ON a.alumno_id = i.alumno_id
            LEFT JOIN grados g ON i.grado_id = g.grado_id
            LEFT JOIN grupos gr ON i.grupo_id = gr.grupo_id
            LEFT JOIN escuelas e ON i.escuela_id = e.escuela_id
            WHERE at.tutor_id = %s
            ORDER BY nombre_completo
        """, (tutor_id,))
        alumnos = cursor.fetchall()
        return alumnos
    except DatabaseError as e:
        print(f"Error al obtener alumnos: {e}")
        return []
    finally:
        conn.close()

def tutor_existe(usuario_id):
    """Validar si el tutor ya está registrado"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tutores WHERE usuario_id = %s", (usuario_id,))
        existe = cursor.fetchone() is not None
        return existe
    except DatabaseError as e:
        print(f"Error al validar tutor: {e}")
        return False
    finally:
        conn.close()