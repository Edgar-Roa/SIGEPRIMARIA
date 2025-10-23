from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from models.escuela_model import (
    obtener_escuela_por_director,
    obtener_estadisticas_escuela,
    obtener_grupos_escuela,
    obtener_alumnos_por_grupo,
    crear_grupo,
    actualizar_grupo
)
from models.inscripcion_model import (
    obtener_inscripciones_pendientes,
    obtener_todas_inscripciones
)
from utils.decorators import login_requerido, director_requerido

panel_director_bp = Blueprint("panel_director", __name__)

@panel_director_bp.route("/panel-director")
@login_requerido
@director_requerido
def panel_director():
    """Panel principal del director"""
    usuario_id = session.get('usuario_id')
    
    # Obtener la escuela del director
    escuela = obtener_escuela_por_director(usuario_id)
    
    if not escuela:
        flash("No se encontró una escuela asignada a tu cuenta", "error")
        return redirect(url_for('inicio.inicio'))
    
    # Guardar escuela_id en sesión para uso en otras rutas
    session['escuela_id'] = escuela['escuela_id']
    
    # Obtener estadísticas
    estadisticas = obtener_estadisticas_escuela(escuela['escuela_id'])
    
    # Obtener inscripciones pendientes
    inscripciones_pendientes = obtener_inscripciones_pendientes(escuela['escuela_id'])
    
    # Obtener grupos
    grupos = obtener_grupos_escuela(escuela['escuela_id'])
    
    return render_template(
        'panel_director.html',
        escuela=escuela,
        estadisticas=estadisticas,
        inscripciones=inscripciones_pendientes,
        grupos=grupos
    )

@panel_director_bp.route("/director/grupos")
@login_requerido
@director_requerido
def gestionar_grupos():
    """Ver y gestionar todos los grupos de la escuela"""
    escuela_id = session.get('escuela_id')
    
    if not escuela_id:
        escuela = obtener_escuela_por_director(session.get('usuario_id'))
        if not escuela:
            flash("No se encontró tu escuela", "error")
            return redirect(url_for('inicio.inicio'))
        escuela_id = escuela['escuela_id']
        session['escuela_id'] = escuela_id
    
    escuela = obtener_escuela_por_director(session.get('usuario_id'))
    grupos = obtener_grupos_escuela(escuela_id)
    
    return render_template(
        'director_grupos.html',
        escuela=escuela,
        grupos=grupos
    )

@panel_director_bp.route("/director/grupo/<int:grupo_id>")
@login_requerido
@director_requerido
def ver_grupo(grupo_id):
    """Ver detalles de un grupo específico"""
    escuela_id = session.get('escuela_id')
    
    # Verificar que el grupo pertenezca a la escuela del director
    alumnos = obtener_alumnos_por_grupo(grupo_id)
    
    # Obtener información del grupo
    from models.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            gr.grupo_id,
            gr.nombre_grupo,
            gr.cupo,
            gr.alumnos_inscritos,
            g.nivel AS grado_nivel,
            g.descripcion AS grado_descripcion,
            u.nombre || ' ' || u.apellido_paterno AS docente_nombre,
            c.nombre AS ciclo_nombre
        FROM grupos gr
        INNER JOIN grados g ON gr.grado_id = g.grado_id
        INNER JOIN ciclos c ON gr.ciclo_id = c.ciclo_id
        LEFT JOIN usuarios u ON gr.docente_usuario_id = u.usuario_id
        WHERE gr.grupo_id = %s AND gr.escuela_id = %s
    """, (grupo_id, escuela_id))
    
    grupo = cursor.fetchone()
    conn.close()
    
    if not grupo:
        flash("Grupo no encontrado o no pertenece a tu escuela", "error")
        return redirect(url_for('panel_director.gestionar_grupos'))
    
    escuela = obtener_escuela_por_director(session.get('usuario_id'))
    
    return render_template(
        'director_grupo_detalle.html',
        grupo=grupo,
        alumnos=alumnos,
        escuela=escuela
    )

@panel_director_bp.route("/director/inscripciones")
@login_requerido
@director_requerido
def ver_inscripciones():
    """Ver todas las inscripciones de la escuela"""
    escuela_id = session.get('escuela_id')
    filtro_status = request.args.get('status')
    
    escuela = obtener_escuela_por_director(session.get('usuario_id'))
    inscripciones = obtener_todas_inscripciones(escuela_id, filtro_status)
    estadisticas = obtener_estadisticas_escuela(escuela_id)
    
    return render_template(
        'director_inscripciones.html',
        escuela=escuela,
        inscripciones=inscripciones,
        estadisticas=estadisticas,
        filtro_actual=filtro_status
    )

@panel_director_bp.route("/director/crear-grupo", methods=["GET", "POST"])
@login_requerido
@director_requerido
def crear_grupo_route():
    """Crear un nuevo grupo en la escuela"""
    escuela_id = session.get('escuela_id')
    escuela = obtener_escuela_por_director(session.get('usuario_id'))
    
    if request.method == "POST":
        grado_id = request.form.get('grado_id')
        nombre_grupo = request.form.get('nombre_grupo', '').strip()
        cupo = request.form.get('cupo')
        
        if not all([grado_id, nombre_grupo, cupo]):
            flash("Todos los campos son obligatorios", "error")
            return redirect(url_for('panel_director.crear_grupo_route'))
        
        try:
            grado_id = int(grado_id)
            cupo = int(cupo)
            
            if cupo < 1 or cupo > 50:
                flash("El cupo debe estar entre 1 y 50 alumnos", "error")
                return redirect(url_for('panel_director.crear_grupo_route'))
        except ValueError:
            flash("Datos inválidos", "error")
            return redirect(url_for('panel_director.crear_grupo_route'))
        
        # Obtener ciclo activo
        from models.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ciclo_id FROM ciclos WHERE activo = TRUE LIMIT 1")
        ciclo = cursor.fetchone()
        conn.close()
        
        if not ciclo:
            flash("No hay ciclo escolar activo", "error")
            return redirect(url_for('panel_director.crear_grupo_route'))
        
        grupo_id = crear_grupo(
            escuela_id=escuela_id,
            grado_id=grado_id,
            ciclo_id=ciclo['ciclo_id'],
            nombre_grupo=nombre_grupo,
            cupo=cupo
        )
        
        if grupo_id:
            flash(f"Grupo {nombre_grupo} creado exitosamente", "success")
            return redirect(url_for('panel_director.gestionar_grupos'))
        else:
            flash("Error al crear el grupo", "error")
    
    # GET - Mostrar formulario
    from models.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT grado_id, nivel, descripcion FROM grados ORDER BY nivel")
    grados = cursor.fetchall()
    conn.close()
    
    return render_template(
        'director_crear_grupo.html',
        escuela=escuela,
        grados=grados
    )