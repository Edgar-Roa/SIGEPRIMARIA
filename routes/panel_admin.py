from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from models.inscripcion_model import (
    obtener_inscripciones_pendientes,
    cambiar_estado_inscripcion,
    obtener_grupos_disponibles,
    obtener_estadisticas_inscripciones,
    obtener_inscripcion_detalle,
    obtener_todas_inscripciones
)
from utils.decorators import login_requerido
from functools import wraps

panel_admin_bp = Blueprint("panel_admin", __name__)

def admin_requerido(f):
    """Decorador para rutas que solo pueden acceder administradores/directores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        rol = session.get('rol')
        if rol not in ['sep_admin', 'director']:
            flash("No tienes permisos para acceder a esta página", "error")
            return redirect(url_for('inicio.inicio'))
        return f(*args, **kwargs)
    return decorated_function

@panel_admin_bp.route("/panel-admin")
@login_requerido
@admin_requerido
def panel_admin():
    usuario_id = session.get('usuario_id')
    rol = session.get('rol')
    escuela_id = session.get('escuela_id') if rol == 'director' else None

    inscripciones_pendientes = obtener_inscripciones_pendientes(escuela_id)
    estadisticas = obtener_estadisticas_inscripciones(escuela_id)

    return render_template(
        'panel_admin.html',
        inscripciones=inscripciones_pendientes,
        estadisticas=estadisticas,
        rol=rol
    )

@panel_admin_bp.route("/admin/inscripciones")
@login_requerido
@admin_requerido
def gestionar_inscripciones():
    rol = session.get('rol')
    escuela_id = session.get('escuela_id') if rol == 'director' else None
    filtro_status = request.args.get('status')

    inscripciones = obtener_todas_inscripciones(escuela_id, filtro_status)
    estadisticas = obtener_estadisticas_inscripciones(escuela_id)

    return render_template(
        'gestionar_inscripciones.html',
        inscripciones=inscripciones,
        estadisticas=estadisticas,
        filtro_actual=filtro_status,
        rol=rol
    )

@panel_admin_bp.route("/admin/inscripcion/<int:inscripcion_id>")
@login_requerido
@admin_requerido
def detalle_inscripcion(inscripcion_id):
    inscripcion = obtener_inscripcion_detalle(inscripcion_id)

    if not inscripcion:
        flash("Inscripción no encontrada", "error")
        return redirect(url_for('panel_admin.panel_admin'))

    rol = session.get('rol')
    if rol == 'director':
        escuela_id = session.get('escuela_id')
        if inscripcion['escuela_id'] != escuela_id:
            flash("No tienes permisos para ver esta inscripción", "error")
            return redirect(url_for('panel_admin.panel_admin'))

    grupos = []
    if inscripcion['status'] in ['pendiente', 'en_revision']:
        grupos = obtener_grupos_disponibles(
            inscripcion['escuela_id'],
            inscripcion['ciclo_id'],
            inscripcion['grado_nivel']
        )

    return render_template(
        'detalle_inscripcion.html',
        inscripcion=inscripcion,
        grupos=grupos
    )

@panel_admin_bp.route("/admin/inscripcion/<int:inscripcion_id>/revisar", methods=["POST"])
@login_requerido
@admin_requerido
def revisar_inscripcion(inscripcion_id):
    usuario_id = session.get('usuario_id')
    accion = request.form.get('accion')
    motivo_rechazo = request.form.get('motivo_rechazo', '').strip()
    grupo_id = request.form.get('grupo_id')

    if accion not in ['aceptar', 'rechazar', 'revisar']:
        flash("Acción inválida", "error")
        return redirect(url_for('panel_admin.detalle_inscripcion', inscripcion_id=inscripcion_id))

    estado_map = {
        'revisar': 'en_revision',
        'aceptar': 'aceptado',
        'rechazar': 'rechazado'
    }
    nuevo_estado = estado_map[accion]

    if accion == 'rechazar' and not motivo_rechazo:
        flash("Debe proporcionar un motivo de rechazo", "error")
        return redirect(url_for('panel_admin.detalle_inscripcion', inscripcion_id=inscripcion_id))

    if accion == 'aceptar':
        if not grupo_id:
            flash("Debe asignar un grupo al aceptar la inscripción", "error")
            return redirect(url_for('panel_admin.detalle_inscripcion', inscripcion_id=inscripcion_id))
        try:
            grupo_id = int(grupo_id)
        except ValueError:
            flash("ID de grupo inválido", "error")
            return redirect(url_for('panel_admin.detalle_inscripcion', inscripcion_id=inscripcion_id))

    exito = cambiar_estado_inscripcion(
        inscripcion_id=inscripcion_id,
        nuevo_estado=nuevo_estado,
        revisado_por=usuario_id,
        motivo_rechazo=motivo_rechazo if accion == 'rechazar' else None,
        grupo_id=grupo_id if accion == 'aceptar' else None
    )

    if exito:
        mensajes = {
            'revisar': 'Inscripción puesta en revisión',
            'aceptar': 'Inscripción aceptada exitosamente',
            'rechazar': 'Inscripción rechazada'
        }
        flash(mensajes[accion], "success")
    else:
        flash("Error al procesar la inscripción", "error")

    return redirect(url_for('panel_admin.panel_admin'))