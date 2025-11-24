import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from models.documento_model import (
    obtener_checklist_documental,
    obtener_tipos_documentos_requeridos,
    guardar_o_actualizar_documento,  # <--- USAMOS LA NUEVA FUNCIÓN
    eliminar_documento,
    resumen_documental
)
from models.alumno_model import obtener_alumnos_por_tutor
from models.tutor_model import obtener_tutor_por_usuario
from utils.decorators import login_requerido, tutor_requerido
from datetime import datetime

documentos_bp = Blueprint("documentos", __name__)

# Configuración de extensiones permitidas
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documentos_bp.route("/documentos/alumno/<int:alumno_id>")
@login_requerido
@tutor_requerido
def ver_documentos(alumno_id):
    """Ver checklist de documentos de un alumno"""
    usuario_id = session.get('usuario_id')
    
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('panel_tutor.panel_tutor'))
    
    alumnos = obtener_alumnos_por_tutor(tutor['tutor_id'])
    alumno = next((a for a in alumnos if a['alumno_id'] == alumno_id), None)
    
    if not alumno:
        flash("No tienes permisos para ver los documentos de este alumno", "error")
        return redirect(url_for('panel_tutor.panel_tutor'))
    
    checklist = obtener_checklist_documental(alumno_id)
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
    """Registrar O Actualizar un documento para un alumno"""
    usuario_id = session.get('usuario_id')
    
    tutor = obtener_tutor_por_usuario(usuario_id)
    if not tutor:
        flash("No se encontró información del tutor", "error")
        return redirect(url_for('panel_tutor.panel_tutor'))
    
    alumnos = obtener_alumnos_por_tutor(tutor['tutor_id'])
    alumno = next((a for a in alumnos if a['alumno_id'] == alumno_id), None)
    
    if not alumno:
        flash("No tienes permisos para gestionar documentos de este alumno", "error")
        return redirect(url_for('panel_tutor.panel_tutor'))
    
    fecha_actual = datetime.now().date()

    if request.method == "POST":
        tipo_doc_id = request.form.get('tipo_doc_id')
        
        # 1. Validaciones de archivo
        if 'archivo_digital' not in request.files:
            flash("No se encontró el archivo adjunto", "error")
            return redirect(request.url)

        file = request.files['archivo_digital']

        if file.filename == '':
            flash("No se seleccionó ningún archivo", "error")
            return redirect(request.url)

        if not tipo_doc_id:
            flash("Debe seleccionar un tipo de documento", "error")
            return redirect(request.url)
        
        try:
            tipo_doc_id = int(tipo_doc_id)
            
            # NOTA: Se eliminó el bloque "if documento_entregado" para permitir actualizaciones.
            
            # 2. Procesar Archivo
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"ALU{alumno_id}_DOC{tipo_doc_id}_{timestamp}_{filename}"
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'documentos')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file.save(os.path.join(upload_folder, unique_filename))
                
                archivo_url = f"/static/uploads/documentos/{unique_filename}"

                # 3. Guardar o Actualizar en BD
                documento_id = guardar_o_actualizar_documento(
                    alumno_id=alumno_id,
                    tipo_doc_id=tipo_doc_id,
                    archivo_url=archivo_url,
                    uploaded_by=usuario_id
                )
                
                if documento_id:
                    flash("Documento subido y registrado exitosamente", "success")
                    return redirect(url_for('documentos.ver_documentos', alumno_id=alumno_id))
                else:
                    flash("Error al guardar en la base de datos", "error")
            else:
                flash("Tipo de archivo no permitido (Use PDF, JPG, PNG)", "error")
                
        except ValueError:
            flash("Datos inválidos", "error")
        except Exception as e:
            print(f"Error al subir archivo: {e}")
            flash("Ocurrió un error al procesar el archivo", "error")
    
    # GET - Mostrar formulario
    
    # CAMBIO IMPORTANTE: Obtenemos todos los tipos, NO filtramos los ya entregados.
    # Esto permite seleccionar un documento "Entregado" para volver a subirlo (corregirlo).
    tipos_documentos = obtener_tipos_documentos_requeridos()
    
    return render_template(
        'registrar_documento.html',
        alumno=alumno,
        tipos_documentos=tipos_documentos, # Enviamos TODOS los tipos
        tutor=tutor,
        max_date=fecha_actual
    )

@documentos_bp.route("/documentos/eliminar/<int:documento_id>", methods=["POST"])
@login_requerido
@tutor_requerido
def eliminar_documento_route(documento_id):
    usuario_id = session.get('usuario_id')
    if eliminar_documento(documento_id, usuario_id):
        flash("Documento eliminado exitosamente", "success")
    else:
        flash("Error al eliminar el documento o sin permisos", "error")
    return redirect(request.referrer or url_for('panel_tutor.panel_tutor'))