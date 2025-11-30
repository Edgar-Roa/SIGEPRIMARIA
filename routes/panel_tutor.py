from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash # <--- Importante para el cambio de contraseña

# Importación de Modelos
from models.tutor_model import obtener_tutor_por_usuario, obtener_alumnos_de_tutor, actualizar_datos_tutor
from models.documento_model import obtener_checklist_documental
from models.alumno_model import obtener_resumen_escolar
from models.usuario_model import actualizar_password, verificar_password_actual

from utils.decorators import login_requerido, tutor_requerido

# Usamos el mismo Blueprint del panel
panel_tutor_bp = Blueprint("panel_tutor", __name__)

# ---------------------------------------------------------
# RUTA 1: DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@panel_tutor_bp.route("/panel-tutor")
@login_requerido
@tutor_requerido
def panel_tutor():
    """Panel principal del tutor"""
    usuario_id = session.get('usuario_id')
    
    # 1. Obtener información del tutor
    tutor = obtener_tutor_por_usuario(usuario_id)
    
    if not tutor:
        flash("No se encontró información del tutor.", "error")
        return redirect(url_for('inicio.inicio'))
    
    # 2. Obtener hijos
    hijos = obtener_alumnos_de_tutor(tutor['tutor_id'])
    
    # 3. Procesar datos de cada hijo
    documentos = {}
    documentos_pendientes_total = 0
    inscripciones_activas_count = 0
    
    for hijo in hijos:
        # Info Académica
        resumen = obtener_resumen_escolar(hijo['alumno_id'])
        if resumen:
            hijo['grado'] = resumen['grado']
            hijo['grupo'] = resumen['grupo']
            hijo['turno'] = resumen['turno']
            inscripciones_activas_count += 1
        else:
            hijo['grado'] = 'Nuevo Ingreso'
            hijo['grupo'] = 'Sin Asignar'
            hijo['turno'] = '-'

        # Documentos
        checklist = obtener_checklist_documental(hijo['alumno_id'])
        documentos[hijo['alumno_id']] = [
            {
                'nombre': doc['tipo_documento'],
                'estado': doc['estado'],
                'tipo_doc_id': doc['tipo_doc_id']
            }
            for doc in checklist
        ]
        
        pendientes = sum(1 for doc in checklist if doc['estado'] in ['Pendiente', 'Vencido'])
        documentos_pendientes_total += pendientes
    
    estadisticas = {
        'total_alumnos': len(hijos),
        'inscripciones_activas': inscripciones_activas_count,
        'documentos_pendientes': documentos_pendientes_total,
        'notificaciones': 0 
    }
    
    return render_template(
        'panel_tutor.html',
        tutor=tutor,
        hijos=hijos,
        documentos=documentos,
        estadisticas=estadisticas
    )

# ---------------------------------------------------------
# RUTA 2: CONFIGURACIÓN DE CUENTA (NUEVA)
# ---------------------------------------------------------
@panel_tutor_bp.route("/panel-tutor/configuracion", methods=['GET', 'POST'])
@login_requerido
@tutor_requerido
def configuracion():
    usuario_id = session.get('usuario_id')
    tutor = obtener_tutor_por_usuario(usuario_id)
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        # A) ACTUALIZAR DATOS PERSONALES
        if accion == 'actualizar_datos':
            nombre = request.form.get('nombre', '').strip()
            ap_pat = request.form.get('apellido_paterno', '').strip()
            ap_mat = request.form.get('apellido_materno', '').strip()
            telefono = request.form.get('telefono', '').strip()
            correo = request.form.get('correo', '').strip()
            
            if actualizar_datos_tutor(usuario_id, nombre, ap_pat, ap_mat, telefono, correo):
                flash("Datos actualizados correctamente", "success")
                session['nombre'] = nombre # Actualizar nombre en el header
                return redirect(url_for('panel_tutor.configuracion'))
            else:
                flash("Error al actualizar datos", "error")
                
        # B) CAMBIAR CONTRASEÑA
        elif accion == 'cambiar_password':
            pass_actual = request.form.get('password_actual')
            pass_nueva = request.form.get('password_nueva')
            pass_confirmar = request.form.get('password_confirmar')
            
            if not verificar_password_actual(usuario_id, pass_actual):
                flash("La contraseña actual es incorrecta", "error")
            elif pass_nueva != pass_confirmar:
                flash("Las contraseñas nuevas no coinciden", "warning")
            elif len(pass_nueva) < 6:
                flash("La contraseña nueva debe tener al menos 6 caracteres", "warning")
            else:
                # Generar hash seguro compatible con Werkzeug
                nuevo_hash = generate_password_hash(pass_nueva)
                if actualizar_password(usuario_id, nuevo_hash):
                    flash("Contraseña actualizada exitosamente", "success")
                else:
                    flash("Error interno al actualizar la contraseña", "error")
                    
        return redirect(url_for('panel_tutor.configuracion'))

    return render_template('configuracion_tutor.html', tutor=tutor)