from models.database import get_connection
from psycopg2 import DatabaseError

# 📝 Registrar nuevo alumno
def registrar_alumno(nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, sexo, direccion, municipio, entidad, telefono, nacionalidad, escuela_procedencia, creado_por_usuario_id):
    """Registrar nuevo alumno - retorna alumno_id o None"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alumnos (
                nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, sexo,
                direccion, municipio, entidad, telefono, nacionalidad, escuela_procedencia, creado_por_usuario_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING alumno_id
        """, (
            nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, sexo,
            direccion, municipio, entidad, telefono, nacionalidad, escuela_procedencia, creado_por_usuario_id
        ))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("No se pudo obtener el alumno_id después del INSERT.")
        
        # ✅ CORRECCIÓN: Acceso como diccionario
        alumno_id = resultado['alumno_id']
        conn.commit()
        
        print(f"✅ Alumno registrado exitosamente con ID: {alumno_id}")
        return alumno_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al registrar alumno: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# 🔗 Vincular alumno a tutor
def vincular_alumno_a_tutor(alumno_id, tutor_id, es_representante=True, contacto_orden=1):
    """Vincular alumno con tutor - retorna True si exitoso, False si falla"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alumno_tutor (alumno_id, tutor_id, es_representante, contacto_orden)
            VALUES (%s, %s, %s, %s)
        """, (alumno_id, tutor_id, es_representante, contacto_orden))
        conn.commit()
        print(f"✅ Alumno {alumno_id} vinculado con tutor {tutor_id}")
        return True
    except DatabaseError as e:
        print(f"❌ Error al vincular alumno con tutor: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# 🔍 Obtener alumno por CURP
def obtener_alumno_por_curp(curp):
    """Obtener alumno por CURP - retorna dict o None"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE curp = %s", (curp,))
        alumno = cursor.fetchone()
        return alumno
    except DatabaseError as e:
        print(f"Error al obtener alumno por CURP: {str(e)}")
        return None
    finally:
        conn.close()

# 👨‍👧 Obtener todos los alumnos de un tutor
def obtener_alumnos_por_tutor(tutor_id):
    """Obtener alumnos de un tutor - retorna lista de dicts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.alumno_id,
                   a.nombre || ' ' || a.apellido_paterno || ' ' || a.apellido_materno AS nombre_completo,
                   a.curp,
                   a.fecha_nacimiento,
                   a.sexo,
                   a.municipio,
                   a.entidad
            FROM alumno_tutor at
            INNER JOIN alumnos a ON at.alumno_id = a.alumno_id
            WHERE at.tutor_id = %s
            ORDER BY nombre_completo
        """, (tutor_id,))
        alumnos = cursor.fetchall()
        return alumnos
    except DatabaseError as e:
        print(f"Error al obtener alumnos del tutor: {str(e)}")
        return []
    finally:
        conn.close()

# ✅ Validar si CURP ya está registrado
def curp_existe(curp):
    """Validar si CURP existe - retorna True/False"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM alumnos WHERE curp = %s", (curp,))
        existe = cursor.fetchone() is not None
        return existe
    except DatabaseError as e:
        print(f"Error al validar CURP: {str(e)}")
        return False
    finally:
        conn.close()

# 🧾 Obtener resumen escolar del alumno
def obtener_resumen_escolar(alumno_id):
    """Obtener resumen escolar del alumno - retorna dict o None"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.nombre AS ciclo,
                   g.descripcion AS grado,
                   gr.nombre_grupo AS grupo,
                   e.turno,
                   e.nombre AS escuela
            FROM inscripciones i
            INNER JOIN ciclos c ON i.ciclo_id = c.ciclo_id
            INNER JOIN grados g ON i.grado_id = g.grado_id
            LEFT JOIN grupos gr ON i.grupo_id = gr.grupo_id
            INNER JOIN escuelas e ON i.escuela_id = e.escuela_id
            WHERE i.alumno_id = %s
            ORDER BY i.fecha_solicitud DESC
            LIMIT 1
        """, (alumno_id,))
        resumen = cursor.fetchone()
        return resumen
    except DatabaseError as e:
        print(f"Error al obtener resumen escolar: {str(e)}")
        return None
    finally:
        conn.close()