from models.database import get_connection
from psycopg2 import DatabaseError

def obtener_usuario_por_correo(correo):
    """Buscar usuario por correo - retorna dict o None"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        return usuario
    except DatabaseError as e:
        print(f"Error al obtener usuario: {e}")
        return None
    finally:
        conn.close()

def registrar_usuario(nombre, apellido_paterno, apellido_materno, correo, password_hash, rol):
    """Registrar nuevo usuario - retorna usuario_id o None"""
    if correo_existe(correo):
        print(f"⚠️ Correo ya registrado: {correo}")
        return None

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido_paterno, apellido_materno, correo, password_hash, rol)
            VALUES (%s, %s, %s, %s, %s, %s::user_role)
            RETURNING usuario_id
        """, (nombre, apellido_paterno, apellido_materno, correo, password_hash, rol))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("No se pudo obtener el usuario_id después del INSERT")
        
        # ✅ Acceso como diccionario
        usuario_id = resultado['usuario_id']
        conn.commit()
        
        print(f"✅ Usuario registrado exitosamente con ID: {usuario_id}")
        return usuario_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al registrar usuario: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def correo_existe(correo):
    """Validar si el correo ya está registrado"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE correo = %s", (correo,))
        existe = cursor.fetchone() is not None
        return existe
    except DatabaseError as e:
        print(f"Error al validar correo: {e}")
        return False
    finally:
        conn.close()

def obtener_password_hash(usuario_id):
    """Obtener hash de contraseña por ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE usuario_id = %s", (usuario_id,))
        resultado = cursor.fetchone()
        # ✅ Acceso como diccionario
        return resultado['password_hash'] if resultado else None
    except DatabaseError as e:
        print(f"Error al obtener hash: {e}")
        return None
    finally:
        conn.close()