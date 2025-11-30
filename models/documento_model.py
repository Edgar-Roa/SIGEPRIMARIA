from models.database import get_connection
from psycopg2 import DatabaseError
from datetime import datetime

# 📄 Registrar documento entregado por alumno
def registrar_documento(alumno_id, tipo_doc_id, fecha_entrega, observaciones, archivo_url=None, uploaded_by=None):
    """Registrar documento de alumno - retorna documento_id o None"""
    if fecha_entrega > datetime.now().date():
        print("⚠️ La fecha de entrega no puede ser futura.")
        return None
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documento_alumno (
                alumno_id, tipo_doc_id, archivo_url, status, observaciones, fecha_subida, uploaded_by
            ) VALUES (%s, %s, %s, 'recibido', %s, %s, %s)
            RETURNING documento_id
        """, (alumno_id, tipo_doc_id, archivo_url, observaciones, fecha_entrega, uploaded_by))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("No se pudo obtener el documento_id después del INSERT.")
        
        documento_id = resultado['documento_id']
        conn.commit()
        
        print(f"✅ Documento registrado exitosamente con ID: {documento_id}")
        return documento_id
        
    except (DatabaseError, ValueError) as e:
        print(f"❌ Error al registrar documento: {type(e).__name__}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# models/documento_model.pyactualizar o guardar documento (insertar o actualizar)
# 1. NUEVA FUNCIÓN: Agregar esta función para permitir "Guardar o Actualizar"
def guardar_o_actualizar_documento(alumno_id, tipo_doc_id, archivo_url, uploaded_by):
    """
    Registra un nuevo documento O actualiza uno existente si ya hay registro.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Usamos ON CONFLICT para manejar "Insertar o Actualizar"
        cursor.execute("""
            INSERT INTO documento_alumno (
                alumno_id, tipo_doc_id, archivo_url, status, fecha_subida, uploaded_by, observaciones
            ) VALUES (%s, %s, %s, 'recibido', CURRENT_TIMESTAMP, %s, NULL)
            ON CONFLICT (alumno_id, tipo_doc_id) 
            DO UPDATE SET
                archivo_url = EXCLUDED.archivo_url,
                status = 'recibido',   -- Reiniciamos status a recibido para revisión
                fecha_subida = CURRENT_TIMESTAMP,
                uploaded_by = EXCLUDED.uploaded_by,
                observaciones = NULL   -- Limpiamos observaciones anteriores
            RETURNING documento_id
        """, (alumno_id, tipo_doc_id, archivo_url, uploaded_by))
        
        resultado = cursor.fetchone()
        documento_id = resultado['documento_id']
        conn.commit()
        
        print(f"✅ Documento guardado/actualizado con ID: {documento_id}")
        return documento_id
        
    except DatabaseError as e:
        print(f"❌ Error al guardar/actualizar documento: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# 📂 Obtener todos los documentos entregados por un alumno
def obtener_documentos_por_alumno(alumno_id):
    """Obtener documentos de un alumno - retorna lista de dicts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                da.documento_id,
                td.nombre AS tipo_documento,
                td.codigo,
                td.requerido,
                da.status,
                da.fecha_subida,
                da.observaciones,
                da.archivo_url
            FROM documento_alumno da
            INNER JOIN tipos_documento td ON da.tipo_doc_id = td.tipo_doc_id
            WHERE da.alumno_id = %s
            ORDER BY td.requerido DESC, td.nombre
        """, (alumno_id,))
        documentos = cursor.fetchall()
        return documentos
    except DatabaseError as e:
        print(f"Error al obtener documentos: {str(e)}")
        return []
    finally:
        conn.close()

# ✅ Validar si un documento ya fue entregado
def documento_entregado(alumno_id, tipo_doc_id):
    """Validar si documento fue entregado - retorna True/False"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM documento_alumno
            WHERE alumno_id = %s AND tipo_doc_id = %s
        """, (alumno_id, tipo_doc_id))
        existe = cursor.fetchone() is not None
        return existe
    except DatabaseError as e:
        print(f"Error al validar documento: {str(e)}")
        return False
    finally:
        conn.close()

# 📋 Obtener checklist documental del alumno
# 2. FUNCIÓN MODIFICADA: Reemplaza tu función 'obtener_checklist_documental' con esta
# EN models/documento_model.py

def obtener_checklist_documental(alumno_id):
    """Obtener checklist documental considerando vencimiento de 3 meses"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # CORRECCIÓN: Agregamos '::text' a da.status para evitar el error de ENUM
        cursor.execute("""
            SELECT 
                td.tipo_doc_id,
                td.codigo,
                td.nombre AS tipo_documento,
                td.descripcion,
                td.requerido,
                CASE 
                    WHEN td.codigo = 'comprobante_dom' 
                         AND da.fecha_subida < (CURRENT_DATE - INTERVAL '3 months') THEN 'Pendiente'
                    WHEN da.documento_id IS NOT NULL THEN 'Entregado' 
                    ELSE 'Pendiente' 
                END AS estado,
                CASE
                    -- Si está vencido, devolvemos el texto 'Vencido'
                    WHEN td.codigo = 'comprobante_dom' 
                         AND da.fecha_subida < (CURRENT_DATE - INTERVAL '3 months') THEN 'Vencido'
                    -- AQUÍ ESTÁ EL TRUCO: Convertimos el ENUM a texto (::text) para que sean compatibles
                    ELSE da.status::text
                END as status,
                da.fecha_subida,
                CASE
                    WHEN td.codigo = 'comprobante_dom' 
                         AND da.fecha_subida < (CURRENT_DATE - INTERVAL '3 months') 
                    THEN 'Su comprobante ha expirado (vigencia 3 meses). Por favor suba uno actual.'
                    ELSE da.observaciones
                END as observaciones,
                da.archivo_url 
            FROM tipos_documento td
            LEFT JOIN documento_alumno da ON da.tipo_doc_id = td.tipo_doc_id AND da.alumno_id = %s
            WHERE td.activo = TRUE
            ORDER BY td.requerido DESC, td.nombre
        """, (alumno_id,))
        
        checklist = cursor.fetchall()
        return checklist
    except DatabaseError as e:
        print(f"Error al obtener checklist: {str(e)}")
        return []
    finally:
        if conn: conn.close()
# 📊 Obtener resumen documental del alumno
def resumen_documental(alumno_id):
    """Obtener resumen de documentos entregados vs totales"""
    checklist = obtener_checklist_documental(alumno_id)
    
    entregados = sum(1 for doc in checklist if doc['estado'] == 'Entregado')
    total = len(checklist)
    
    return {
        "entregados": entregados, 
        "total": total,
        "pendientes": total - entregados,
        "porcentaje": round((entregados / total * 100) if total > 0 else 0, 2)
    }

# 🗑️ Eliminar documento
def eliminar_documento(documento_id, usuario_id):
    """Eliminar un documento - retorna True/False"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar que el documento existe y pertenece al usuario
        cursor.execute("""
            DELETE FROM documento_alumno
            WHERE documento_id = %s
            AND uploaded_by = %s
            RETURNING documento_id
        """, (documento_id, usuario_id))
        
        resultado = cursor.fetchone()
        conn.commit()
        
        if resultado:
            print(f"✅ Documento {documento_id} eliminado exitosamente")
            return True
        else:
            print(f"❌ Documento no encontrado o sin permisos")
            return False
            
    except DatabaseError as e:
        print(f"❌ Error al eliminar documento: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# 📝 Actualizar observaciones de documento
def actualizar_observaciones_documento(documento_id, observaciones):
    """Actualizar observaciones de un documento"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE documento_alumno
            SET observaciones = %s
            WHERE documento_id = %s
        """, (observaciones, documento_id))
        
        conn.commit()
        return True
        
    except DatabaseError as e:
        print(f"Error al actualizar observaciones: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# 📋 Obtener tipos de documentos requeridos
def obtener_tipos_documentos_requeridos():
    """Obtener lista de documentos requeridos"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo_doc_id, codigo, nombre, descripcion, requerido
            FROM tipos_documento
            WHERE activo = TRUE
            ORDER BY requerido DESC, nombre
        """)
        return cursor.fetchall()
    except DatabaseError as e:
        print(f"Error al obtener tipos de documentos: {e}")
        return []
    finally:
        conn.close()