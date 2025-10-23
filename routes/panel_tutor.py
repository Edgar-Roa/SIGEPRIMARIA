from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.tutor_model import obtener_tutor_por_usuario, obtener_alumnos_de_tutor
from models.documento_model import obtener_checklist_documental
from utils.decorators import login_requerido, tutor_requerido

panel_tutor_bp = Blueprint("panel_tutor", __name__)

@panel_tutor_bp.route("/panel-tutor")
@login_requerido
@tutor_requerido
def panel_tutor():
    """Panel principal del tutor"""
    usuario_id = session.get('usuario_id')
    
    # Obtener información del tutor
    tutor = obtener_tutor_por_usuario(usuario_id)
    
    if not tutor:
        flash("No se encontró información del tutor. Por favor contacte al administrador.", "error")
        return redirect(url_for('inicio.inicio'))
    
    # Obtener alumnos (hijos) del tutor
    hijos = obtener_alumnos_de_tutor(tutor['tutor_id'])
    
    # Obtener documentos de cada hijo
    documentos = {}
    documentos_pendientes_total = 0
    
    for hijo in hijos:
        checklist = obtener_checklist_documental(hijo['alumno_id'])
        documentos[hijo['alumno_id']] = [
            {
                'nombre': doc['tipo_documento'],
                'estado': doc['estado']
            }
            for doc in checklist
        ]
        # Contar documentos pendientes
        pendientes = sum(1 for doc in checklist if doc['estado'] == 'Pendiente')
        documentos_pendientes_total += pendientes
    
    # Calcular estadísticas
    estadisticas = {
        'total_alumnos': len(hijos),
        'inscripciones_activas': sum(1 for h in hijos if h.get('grado')),
        'documentos_pendientes': documentos_pendientes_total,
        'notificaciones': 0  # Implementar cuando se agregue el sistema de notificaciones
    }
    
    return render_template(
        'panel_tutor.html',
        tutor=tutor,
        hijos=hijos,
        documentos=documentos,
        estadisticas=estadisticas
    )