# ============================================
# routes/registro_alumno.py
# ============================================
from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from models.database import get_connection
from models.alumno_model import registrar_alumno, vincular_alumno_a_tutor, curp_existe
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from pathlib import Path

registro_alumno_bp = Blueprint('registro_alumno', __name__)

# Configuración de carga de archivos
UPLOAD_FOLDER = 'uploads/alumnos'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def crear_carpeta_uploads():
    """Crear carpeta de uploads si no existe"""
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

def archivo_permitido(filename):
    """Validar extensión del archivo"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_archivo(file, alumno_id, tipo_documento):
    """Guardar archivo en la carpeta de uploads"""
    if not file or file.filename == '':
        return None
    
    # Validar tipo de archivo
    if not archivo_permitido(file.filename):
        return None
    
    # Crear carpeta si no existe
    crear_carpeta_uploads()
    
    # Crear nombre seguro del archivo
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"alumno_{alumno_id}_{tipo_documento}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    
    # Guardar archivo
    file.save(filepath)
    
    return filepath

@registro_alumno_bp.route('/registro-alumno', methods=['GET', 'POST'])
def registro_alumno():
    """Formulario para registrar un nuevo alumno"""
    
    # Verificar que el tutor esté autenticado
    usuario_id = session.get('usuario_id')
    rol = session.get('rol')
    
    if not usuario_id or rol != 'tutor':
        flash("Debe iniciar sesión como tutor para registrar alumnos", "error")
        return redirect(url_for('iniciar_sesion.iniciar_sesion'))
    
    if request.method == 'GET':
        # Obtener escuelas y grados para los selects
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Obtener escuelas activas
            cursor.execute("""
                SELECT escuela_id, nombre, cct, municipio, turno
                FROM escuelas
                WHERE activo = TRUE
                ORDER BY nombre
            """)
            escuelas = cursor.fetchall()
            
            # Obtener grados
            cursor.execute("""
                SELECT grado_id, nivel, descripcion
                FROM grados
                ORDER BY nivel
            """)
            grados = cursor.fetchall()
            
            # Obtener tutor_id
            cursor.execute("""
                SELECT tutor_id, nombre, apellido_paterno, apellido_materno
                FROM tutores
                WHERE usuario_id = %s
            """, (usuario_id,))
            tutor = cursor.fetchone()
            
            if not tutor:
                flash("No se encontró información del tutor", "error")
                return redirect(url_for('panel_tutor.panel_tutor'))
            
            return render_template(
                'registro_alumno.html',
                escuelas=escuelas,
                grados=grados,
                tutor=tutor
            )
            
        except Exception as e:
            print(f"Error al cargar formulario: {e}")
            flash("Error al cargar el formulario", "error")
            return redirect(url_for('panel_tutor.panel_tutor'))
        finally:
            if conn:
                conn.close()
    
    # POST - Procesar el registro
    conn = None
    try:
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        apellido_paterno = request.form.get('apellido_paterno', '').strip()
        apellido_materno = request.form.get('apellido_materno', '').strip()
        curp = request.form.get('curp', '').strip().upper()
        fecha_nacimiento = request.form.get('fecha_nacimiento', '')
        sexo = request.form.get('sexo', '')
        direccion = request.form.get('direccion', '').strip()
        municipio = request.form.get('municipio', '').strip()
        entidad = request.form.get('entidad', '').strip()
        telefono = request.form.get('telefono', '').strip()
        nacionalidad = request.form.get('nacionalidad', 'Mexicana').strip()
        escuela_procedencia = request.form.get('escuela_procedencia', '').strip()
        
        # Datos de inscripción
        escuela_id = request.form.get('escuela_id', '')
        grado_id = request.form.get('grado_id', '')
        
        # Validaciones básicas
        if not all([nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, sexo]):
            flash("Los campos marcados con * son obligatorios", "error")
            return redirect(url_for('registro_alumno.registro_alumno'))
        
        # Validar CURP
        if len(curp) != 18:
            flash("El CURP debe tener 18 caracteres", "error")
            return redirect(url_for('registro_alumno.registro_alumno'))
        
        # Verificar si CURP ya existe
        if curp_existe(curp):
            flash("Ya existe un alumno registrado con este CURP", "error")
            return redirect(url_for('registro_alumno.registro_alumno'))
        
        # Validar fecha de nacimiento
        try:
            fecha_nac_obj = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            edad = (datetime.now().date() - fecha_nac_obj).days // 365
            
            if edad < 5 or edad > 15:
                flash("El alumno debe tener entre 5 y 15 años para primaria", "warning")
        except ValueError:
            flash("Fecha de nacimiento inválida", "error")
            return redirect(url_for('registro_alumno.registro_alumno'))
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener tutor_id
        cursor.execute("SELECT tutor_id FROM tutores WHERE usuario_id = %s", (usuario_id,))
        tutor = cursor.fetchone()
        
        if not tutor:
            flash("Error: No se encontró el tutor", "error")
            return redirect(url_for('panel_tutor.panel_tutor'))
        
        tutor_id = tutor['tutor_id']
        
        # Registrar alumno
        alumno_id = registrar_alumno(
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            curp=curp,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            direccion=direccion,
            municipio=municipio,
            entidad=entidad,
            telefono=telefono,
            nacionalidad=nacionalidad,
            escuela_procedencia=escuela_procedencia,
            creado_por_usuario_id=usuario_id
        )
        
        if not alumno_id:
            flash("Error al registrar al alumno", "error")
            return redirect(url_for('registro_alumno.registro_alumno'))
        
        # Vincular alumno con tutor
        if not vincular_alumno_a_tutor(alumno_id, tutor_id, es_representante=True):
            flash("Alumno registrado pero hubo un error al vincularlo", "warning")
        
        # ========== PROCESAR DOCUMENTOS ==========
        documentos_procesados = 0
        documentos_map = {
            'doc_alumno_acta': ('acta_nac', 'Acta de Nacimiento'),
            'doc_alumno_cartilla': ('cartilla_vac', 'Cartilla de Vacunación'),
            'doc_tutor_identificacion': ('ine_tutor', 'INE del Tutor'),
            'doc_tutor_domicilio': ('comprobante_dom', 'Comprobante de Domicilio'),
            'doc_tutor_autorizacion': ('foto', 'Fotografía')
        }
        
        for field_name, (tipo_codigo, tipo_nombre) in documentos_map.items():
            if field_name in request.files:
                file = request.files[field_name]
                if file and file.filename != '':
                    # Validar tamaño
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > MAX_FILE_SIZE:
                        flash(f"El archivo {tipo_nombre} excede el tamaño máximo (10 MB)", "warning")
                        continue
                    
                    # Validar extensión
                    if not archivo_permitido(file.filename):
                        flash(f"Formato no permitido para {tipo_nombre}", "warning")
                        continue
                    
                    # Obtener tipo_doc_id del código
                    cursor.execute("""
                        SELECT tipo_doc_id FROM tipos_documento WHERE codigo = %s
                    """, (tipo_codigo,))
                    tipo_doc_result = cursor.fetchone()
                    
                    if not tipo_doc_result:
                        print(f"No se encontró tipo de documento con código: {tipo_codigo}")
                        continue
                    
                    tipo_doc_id = tipo_doc_result['tipo_doc_id']
                    
                    # Guardar archivo
                    filepath = guardar_archivo(file, alumno_id, tipo_codigo)
                    if filepath:
                        try:
                            # Obtener MIME type
                            import mimetypes
                            mime_type, _ = mimetypes.guess_type(file.filename)
                            
                            cursor.execute("""
                                INSERT INTO documento_alumno (
                                    alumno_id, tipo_doc_id, archivo_url, 
                                    nombre_archivo, mime_type, uploaded_by, status
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
                                ON CONFLICT (alumno_id, tipo_doc_id) 
                                DO UPDATE SET 
                                    archivo_url = EXCLUDED.archivo_url,
                                    nombre_archivo = EXCLUDED.nombre_archivo,
                                    mime_type = EXCLUDED.mime_type,
                                    fecha_subida = NOW()
                            """, (alumno_id, tipo_doc_id, filepath, 
                                  secure_filename(file.filename), mime_type, usuario_id))
                            
                            documentos_procesados += 1
                        except Exception as e:
                            print(f"Error al guardar documento {tipo_nombre}: {e}")
                            conn.rollback()
        
        # Confirmar cambios
        if documentos_procesados > 0:
            conn.commit()
            flash(f"Se cargaron {documentos_procesados} documento(s) exitosamente", "info")
        
        # Si se seleccionó escuela y grado, crear inscripción
        if escuela_id and grado_id:
            # Obtener ciclo activo
            cursor.execute("""
                SELECT ciclo_id, inscripciones_abiertas
                FROM ciclos
                WHERE activo = TRUE
                LIMIT 1
            """)
            ciclo = cursor.fetchone()
            
            if ciclo and ciclo['inscripciones_abiertas']:
                cursor.execute("""
                    INSERT INTO inscripciones (
                        alumno_id, escuela_id, ciclo_id, grado_id, status
                    )
                    VALUES (%s, %s, %s, %s, 'pendiente')
                """, (alumno_id, escuela_id, ciclo['ciclo_id'], grado_id))
                conn.commit()
                flash("Alumno registrado, documentos cargados e inscripción solicitada exitosamente", "success")
            else:
                flash("Alumno y documentos registrados. Las inscripciones están cerradas actualmente", "warning")
        else:
            flash("Alumno y documentos registrados exitosamente", "success")
        
        return redirect(url_for('panel_tutor.panel_tutor'))
        
    except Exception as e:
        print(f"❌ Error al registrar alumno: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        flash("Ocurrió un error al registrar al alumno", "error")
        return redirect(url_for('registro_alumno.registro_alumno'))
    finally:
        if conn:
            conn.close()


@registro_alumno_bp.route('/validar-curp', methods=['POST'])
def validar_curp():
    """Endpoint AJAX para validar CURP en tiempo real"""
    from flask import jsonify
    
    curp = request.json.get('curp', '').strip().upper()
    
    if len(curp) != 18:
        return jsonify({'valido': False, 'mensaje': 'El CURP debe tener 18 caracteres'})
    
    if curp_existe(curp):
        return jsonify({'valido': False, 'mensaje': 'Este CURP ya está registrado'})
    
    return jsonify({'valido': True, 'mensaje': 'CURP disponible'})