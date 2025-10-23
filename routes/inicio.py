from flask import Blueprint, render_template
from models.database import get_connection

inicio_bp = Blueprint('inicio', __name__)

@inicio_bp.route('/')
def inicio():
    """Página de inicio del sistema"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener ciclo escolar activo
        cursor.execute("""
            SELECT ciclo_id, nombre, fecha_inicio, fecha_fin, 
                   activo, inscripciones_abiertas
            FROM ciclos
            WHERE activo = TRUE
            LIMIT 1
        """)
        ciclo_activo = cursor.fetchone()
        
        return render_template('inicio.html', ciclo_activo=ciclo_activo)
        
    except Exception as e:
        print(f"Error al cargar inicio: {e}")
        return render_template('inicio.html', ciclo_activo=None)
    finally:
        if conn:
            conn.close()