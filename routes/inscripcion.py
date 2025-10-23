from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from models.inscripcion_model import (
    crear_inscripcion, obtener_escuelas_disponibles, 
    obtener_ciclo_activo, obtener_grados,
    puede_inscribirse_alumno, obtener_inscripciones_por_tutor
)
from models.alumno_model import obtener_alumnos_por_tutor
from models.tutor_model import obtener_tutor_por_usuario
from utils.decorators import login_requerido, tutor_requerido

inscripcion_bp = Blueprint("inscripcion", __name__)

@inscripcion_bp.route("/inscripcion")
@login_requerido
@tutor_requerido
def inscripcion():
    """Mostrar formulario de inscripción"""
    usuario_id = session.get('usuario_id')
    
    # Obtener información del tutor
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('panel_tutor.panel_tutor'))
    
    # Obtener alumnos del tutor
    alumnos = obtener_alumnos_por_tutor(tutor['tutor_id'])
    
    # Obtener datos necesarios para el formulario
    escuelas = obtener_escuelas_disponibles()
    ciclo_activo = obtener_ciclo_activo()
    grados = obtener_grados()
    
    # Verificar si hay ciclo activo
    if not ciclo_activo:
        flash("No hay ningún ciclo escolar activo en este momento", "warning")
        return render_template("inscripcion.html", 
                             tutor=tutor,
                             alumnos=[],
                             escuelas=[],
                             ciclo_activo=None,
                             grados=[])
    
    # Verificar si las inscripciones están abiertas
    if not ciclo_activo.get('inscripciones_abiertas'):
        flash("Las inscripciones están cerradas para el ciclo actual", "warning")
    
    return render_template("inscripcion.html",
                         tutor=tutor,
                         alumnos=alumnos,
                         escuelas=escuelas,
                         ciclo_activo=ciclo_activo,
                         grados=grados)

@inscripcion_bp.route("/inscripcion/solicitar", methods=["POST"])
@login_requerido
@tutor_requerido
def solicitar_inscripcion():
    """Procesar solicitud de inscripción"""
    usuario_id = session.get('usuario_id')
    
    # Obtener datos del formulario
    alumno_id = request.form.get('alumno_id')
    escuela_id = request.form.get('escuela_id')
    grado_id = request.form.get('grado_id')
    
    # Validar campos requeridos
    if not all([alumno_id, escuela_id, grado_id]):
        flash("Todos los campos son obligatorios", "error")
        return redirect(url_for('inscripcion.inscripcion'))
    
    try:
        alumno_id = int(alumno_id)
        escuela_id = int(escuela_id)
        grado_id = int(grado_id)
    except ValueError:
        flash("Datos inválidos", "error")
        return redirect(url_for('inscripcion.inscripcion'))
    
    # Obtener ciclo activo
    ciclo = obtener_ciclo_activo()
    if not ciclo:
        flash("No hay ciclo escolar activo", "error")
        return redirect(url_for('inscripcion.inscripcion'))
    
    if not ciclo.get('inscripciones_abiertas'):
        flash("Las inscripciones están cerradas", "error")
        return redirect(url_for('inscripcion.inscripcion'))
    
    # Verificar si el alumno puede inscribirse
    puede, mensaje = puede_inscribirse_alumno(alumno_id, escuela_id)
    
    if not puede:
        flash(f"No se puede realizar la inscripción: {mensaje}", "error")
        return redirect(url_for('inscripcion.inscripcion'))
    
    # Crear inscripción
    inscripcion_id = crear_inscripcion(
        alumno_id=alumno_id,
        escuela_id=escuela_id,
        ciclo_id=ciclo['ciclo_id'],
        grado_id=grado_id,
        usuario_responsable=usuario_id
    )
    
    if inscripcion_id:
        flash("Solicitud de inscripción enviada exitosamente. Recibirás una notificación cuando sea revisada.", "success")
        return redirect(url_for('inscripcion.mis_inscripciones'))
    else:
        flash("Error al procesar la inscripción. Intenta nuevamente.", "error")
        return redirect(url_for('inscripcion.inscripcion'))

@inscripcion_bp.route("/mis-inscripciones")
@login_requerido
@tutor_requerido
def mis_inscripciones():
    """Mostrar historial de inscripciones del tutor"""
    usuario_id = session.get('usuario_id')
    
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('inicio.inicio'))
    
    inscripciones = obtener_inscripciones_por_tutor(tutor['tutor_id'])
    
    return render_template("mis_inscripciones.html",
                         tutor=tutor,
                         inscripciones=inscripciones)

@inscripcion_bp.route("/verificar-elegibilidad/<int:alumno_id>/<int:escuela_id>")
@login_requerido
@tutor_requerido
def verificar_elegibilidad(alumno_id, escuela_id):
    """Endpoint AJAX para verificar si un alumno puede inscribirse"""
    puede, mensaje = puede_inscribirse_alumno(alumno_id, escuela_id)
    return {
        "puede_inscribirse": puede,
        "mensaje": mensaje
    }