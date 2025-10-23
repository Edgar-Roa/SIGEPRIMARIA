from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.documento_model import (
    obtener_checklist_documental,
    obtener_tipos_documentos_requeridos,
    registrar_documento,
    eliminar_documento,
    documento_entregado,
    resumen_documental
)
from models.alumno_model import obtener_alumnos_por_tutor
from models.tutor_model import obtener_tutor_por_usuario
from utils.decorators import login_requerido, tutor_requerido
from datetime import datetime

documentos_bp = Blueprint("documentos", __name__)

@documentos_bp.route("/documentos/alumno/<int:alumno_id>")
@login_requerido
@tutor_requerido
def ver_documentos(alumno_id):
    """Ver checklist de documentos de un alumno"""
    usuario_id = session.get('usuario_id')
    
    # Obtener tutor
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('panel_tutor_bp.panel_tutor'))
    
    # Verificar que el alumno pertenezca al tutor
    alumnos = obtener_alumnos_por_tutor(tutor['tutor_id'])
    alumno = next((a for a in alumnos if a['alumno_id'] == alumno_id), None)
    
    if not alumno:
        flash("No tienes permisos para ver los documentos de este alumno", "error")
        return redirect(url_for('panel_tutor_bp.panel_tutor'))
    
    # Obtener checklist de documentos
    checklist = obtener_checklist_documental(alumno_id)
    
    # Obtener resumen
    resumen = resumen_documental(alumno_id)
    
    return render_template(
        'documentos_alumno.html',
        alumno=alumno,
        checklist=checklist,
        resumen=resumen,
        tutor=tutor
    )

@documentos_bp.route("/documentos/registrar/<int:alumno_id>", methods=["GET", "POST"])
@login_requerido
@tutor_requerido
def registrar_documento_route(alumno_id):
    """Registrar un documento para un alumno"""
    usuario_id = session.get('usuario_id')
    
    # Obtener tutor
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('panel_tutor_bp.panel_tutor'))
    
    # Verificar que el alumno pertenezca al tutor
    alumnos = obtener_alumnos_por_tutor(tutor['tutor_id'])
    alumno = next((a for a in alumnos if a['alumno_id'] == alumno_id), None)
    
    if not alumno:
        flash("No tienes permisos para registrar documentos de este alumno", "error")
        return redirect(url_for('panel_tutor_bp.panel_tutor'))
    
    fecha_maxima = datetime.now().strftime('%Y-%m-%d')

    if request.method == "POST":
        tipo_doc_id = request.form.get('tipo_doc_id')
        observaciones = request.form.get('observaciones', '').strip()
        fecha_entrega = request.form.get('fecha_entrega', datetime.now().date())
        
        if not tipo_doc_id:
            flash("Debe seleccionar un tipo de documento", "error")
            return redirect(url_for('documentos.registrar_documento_route', alumno_id=alumno_id))
        
        try:
            tipo_doc_id = int(tipo_doc_id)
            
            # Verificar si ya fue entregado
            if documento_entregado(alumno_id, tipo_doc_id):
                flash("Este documento ya fue registrado", "warning")
                return redirect(url_for('documentos.ver_documentos', alumno_id=alumno_id))
            
            # Registrar documento
            documento_id = registrar_documento(
                alumno_id=alumno_id,
                tipo_doc_id=tipo_doc_id,
                fecha_entrega=fecha_entrega,
                observaciones=observaciones,
                archivo_url=None,  # Por ahora sin archivo
                uploaded_by=usuario_id
            )
            
            if documento_id:
                flash("Documento registrado exitosamente", "success")
                return redirect(url_for('documentos.ver_documentos', alumno_id=alumno_id))
            else:
                flash("Error al registrar el documento", "error")
                
        except ValueError:
            flash("Datos inválidos", "error")
    
    # GET - Mostrar formulario
    tipos_documentos = obtener_tipos_documentos_requeridos()
    checklist_actual = obtener_checklist_documental(alumno_id)
    
    # Filtrar solo documentos pendientes
    documentos_pendientes = [
        td for td in tipos_documentos
        if not any(c['tipo_doc_id'] == td['tipo_doc_id'] and c['estado'] == 'Entregado' 
                   for c in checklist_actual)
    ]
    
    return render_template(
        'registrar_documento.html',
        alumno=alumno,
        tipos_documentos=documentos_pendientes,
        tutor=tutor,
        max_date=fecha_maxima
    )

@documentos_bp.route("/documentos/eliminar/<int:documento_id>", methods=["POST"])
@login_requerido
@tutor_requerido
def eliminar_documento_route(documento_id):
    """Eliminar un documento"""
    usuario_id = session.get('usuario_id')
    
    if eliminar_documento(documento_id, usuario_id):
        flash("Documento eliminado exitosamente", "success")
    else:
        flash("Error al eliminar el documento o sin permisos", "error")
    
    # Redirigir a la página anterior
    return redirect(request.referrer or url_for('panel_tutor_bp.panel_tutor'))