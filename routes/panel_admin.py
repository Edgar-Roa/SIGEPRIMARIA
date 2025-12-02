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
from models.escuela_model import registrar_escuela_bd
import json
from models.inscripcion_model import (
    obtener_inscripciones_pendientes,
    cambiar_estado_inscripcion,
    obtener_grupos_disponibles,
    obtener_estadisticas_inscripciones,
    obtener_inscripcion_detalle,
    obtener_todas_inscripciones,
    obtener_conteo_por_grado # <--- NUEVA IMPORTACIÓN
)
from models.usuario_model import registrar_usuario, correo_existe
from models.escuela_model import obtener_todas_escuelas_mapa # Para llenar el select de escuelas
from werkzeug.security import generate_password_hash

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

    # AGREGA ESTO AL FINAL DE: panel_admin.py

@panel_admin_bp.route("/admin/registrar-escuela", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def registrar_escuela_route():
    # 1. Seguridad extra: Validar que sea específicamente SEP ADMIN
    if session.get('rol') != 'sep_admin':
        flash("Solo el Administrador de la SEP puede registrar escuelas.", "error")
        return redirect(url_for('panel_admin.panel_admin'))

    if request.method == "POST":
        try:
            # 2. Recolectar datos
            datos_escuela = {
                'cct': request.form.get('cct').strip().upper(),
                'nombre': request.form.get('nombre').strip(),
                'turno': request.form.get('turno'),
                'zona_escolar': request.form.get('zona_escolar'),
                'cupo_total': request.form.get('cupo_total'),
                'direccion': request.form.get('direccion'),
                'municipio': request.form.get('municipio'),
                'entidad': request.form.get('entidad'),
                'telefono': request.form.get('telefono'),
                'latitud': request.form.get('latitud'),
                'longitud': request.form.get('longitud')
            }

            # 3. Guardar
            escuela_id = registrar_escuela_bd(datos_escuela)

            if escuela_id:
                flash(f"Escuela '{datos_escuela['nombre']}' registrada exitosamente.", "success")
                return redirect(url_for('panel_admin.panel_admin'))
            else:
                flash("Error al registrar. Verifique que la CCT no esté duplicada.", "error")

        except Exception as e:
            print(f"Error en ruta registro escuela: {e}")
            flash("Ocurrió un error interno.", "error")

    return render_template('registrar_escuela.html')

@panel_admin_bp.route("/admin/registrar-usuario", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def registrar_usuario_admin():
    # Solo SEP Admin puede registrar directores/admins
    if session.get('rol') != 'sep_admin':
        flash("Acceso no autorizado.", "error")
        return redirect(url_for('panel_admin.panel_admin'))

    # Obtener escuelas para el select (si registra un director)
    # Usamos la función que ya tenías o creamos una simple que traiga ID y Nombre
    escuelas = obtener_todas_escuelas_mapa() 

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        ap_pat = request.form.get("apellido_paterno", "").strip()
        ap_mat = request.form.get("apellido_materno", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        rol_asignar = request.form.get("rol", "")
        escuela_id = request.form.get("escuela_id")

        # Validaciones
        if not all([nombre, ap_pat, correo, password, rol_asignar]):
            flash("Faltan datos obligatorios.", "error")
            return render_template("registrar_usuario_admin.html", escuelas=escuelas)

        if correo_existe(correo):
            flash("El correo ya está registrado.", "error")
            return render_template("registrar_usuario_admin.html", escuelas=escuelas)

        # Validar Director sin Escuela
        if rol_asignar == 'director' and not escuela_id:
            flash("Debes asignar una escuela al Director.", "error")
            return render_template("registrar_usuario_admin.html", escuelas=escuelas)

        try:
            # 1. Crear Usuario
            pw_hash = generate_password_hash(password)
            nuevo_usuario_id = registrar_usuario(nombre, ap_pat, ap_mat, correo, pw_hash, rol_asignar)

            if nuevo_usuario_id:
                # 2. Lógica Especial: Si es Director, actualizar la escuela
                if rol_asignar == 'director' and escuela_id:
                    from models.database import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    # Asignar este usuario como director de la escuela seleccionada
                    cursor.execute("UPDATE escuelas SET director_usuario_id = %s WHERE escuela_id = %s", (nuevo_usuario_id, escuela_id))
                    conn.commit()
                    conn.close()
                    flash(f"Director registrado y asignado a la escuela correctamente.", "success")
                else:
                    flash(f"Usuario {rol_asignar} registrado exitosamente.", "success")
                
                return redirect(url_for('panel_admin.panel_admin'))
            else:
                flash("Error al crear usuario en BD.", "error")

        except Exception as e:
            print(f"Error registro admin: {e}")
            flash("Error interno al registrar.", "error")

    return render_template("registrar_usuario_admin.html", escuelas=escuelas)

@panel_admin_bp.route("/admin/estadisticas")
@login_requerido
@admin_requerido
def ver_estadisticas():
    rol = session.get('rol')
    escuela_id = session.get('escuela_id') if rol == 'director' else None
    
    # A. Obtener datos generales (Pastel)
    # Usamos la función que ya tenías: obtener_estadisticas_inscripciones
    stats_general = obtener_estadisticas_inscripciones(escuela_id)
    
    # B. Obtener datos por grado (Barras)
    stats_grados = obtener_conteo_por_grado(escuela_id)
    
    # C. Preparar datos para Chart.js (JSON)
    data_pastel = {
        'labels': ['Aceptados', 'Pendientes', 'En Revisión', 'Rechazados'],
        'data': [
            stats_general['aceptados'] or 0,
            stats_general['pendientes'] or 0,
            stats_general['en_revision'] or 0,
            stats_general['rechazados'] or 0
        ]
    }
    
    data_barras = {
        'labels': [g['descripcion'] for g in stats_grados],
        'data': [g['total'] for g in stats_grados]
    }

    return render_template(
        'graficas_admin.html',
        data_pastel=json.dumps(data_pastel),
        data_barras=json.dumps(data_barras)
    )