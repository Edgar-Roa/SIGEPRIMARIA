# ============================================
# routes/registro_alumno.py (DEFINITIVO)
# ============================================
from flask import Blueprint, render_template, request, redirect, flash, url_for, session, current_app, jsonify
from models.database import get_connection
from models.alumno_model import registrar_alumno, vincular_alumno_a_tutor, curp_existe
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import mimetypes
import traceback

registro_alumno_bp = Blueprint('registro_alumno', __name__)

# Configuración de carga de archivos
UPLOAD_FOLDER = 'uploads/documentos' # Ruta relativa dentro de static
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def crear_carpeta_uploads():
    """Crear carpeta de uploads física si no existe"""
    physical_path = os.path.join(current_app.root_path, 'static', UPLOAD_FOLDER)
    Path(physical_path).mkdir(parents=True, exist_ok=True)
    return physical_path

def archivo_permitido(filename):
    """Validar extensión del archivo"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_archivo(file, alumno_id, tipo_codigo):
    """Guardar archivo físicamente y retornar la URL web"""
    if not file or file.filename == '': return None
    
    if not archivo_permitido(file.filename): return None
    
    # Crear ruta física: /app/static/uploads/documentos/
    base_path = crear_carpeta_uploads()
    
    # Nombre seguro: ALU{id}_{tipo}_{timestamp}.ext
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"ALU{alumno_id}_{tipo_codigo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    safe_name = secure_filename(filename)
    
    # Guardar
    file.save(os.path.join(base_path, safe_name))
    
    # Retornar URL web: /static/uploads/documentos/archivo.ext
    return f"/static/{UPLOAD_FOLDER}/{safe_name}"

# ----------------------------------------------------------------------------------

@registro_alumno_bp.route('/registro-alumno', methods=['GET', 'POST'])
def registro_alumno():
    usuario_id = session.get('usuario_id')
    rol = session.get('rol')
    
    if not usuario_id or rol != 'tutor':
        flash("Debe iniciar sesión como tutor", "error")
        return redirect(url_for('iniciar_sesion.iniciar_sesion'))

    # GET: Mostrar formulario
    if request.method == 'GET':
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT escuela_id, nombre, turno FROM escuelas WHERE activo = TRUE ORDER BY nombre")
            escuelas = cursor.fetchall()
            
            cursor.execute("SELECT grado_id, nivel, descripcion FROM grados ORDER BY nivel")
            grados = cursor.fetchall()
            
            cursor.execute("SELECT * FROM tutores WHERE usuario_id = %s", (usuario_id,))
            tutor = cursor.fetchone()
            
            if not tutor:
                return redirect(url_for('panel_tutor.panel_tutor'))
            
            return render_template('registro_alumno.html', escuelas=escuelas, grados=grados, tutor=tutor)
            
        except Exception as e:
            print(f"Error carga: {e}")
            return redirect(url_for('panel_tutor.panel_tutor'))
        finally:
            if conn: conn.close()

    # POST: Procesar registro
    if request.method == 'POST':
        conn = None
        try:
            # 1. Datos del Alumno
            nombre = request.form.get('nombre', '').strip()
            ap_pat = request.form.get('apellido_paterno', '').strip()
            ap_mat = request.form.get('apellido_materno', '').strip()
            curp = request.form.get('curp', '').strip().upper()
            nacimiento = request.form.get('fecha_nacimiento')
            sexo = request.form.get('sexo')
            direccion = request.form.get('direccion', '')
            municipio = request.form.get('municipio', '')
            entidad = request.form.get('entidad', '')
            telefono = request.form.get('telefono', '')
            nacionalidad = request.form.get('nacionalidad', 'Mexicana')
            escuela_proc = request.form.get('escuela_procedencia', '')

            if not all([nombre, ap_pat, ap_mat, curp, nacimiento, sexo]):
                flash("Faltan datos obligatorios", "error")
                return redirect(request.url)

            # 2. Registrar Alumno en BD
            alumno_id = registrar_alumno(
                nombre, ap_pat, ap_mat, curp, nacimiento, sexo,
                direccion, municipio, entidad, telefono, nacionalidad, escuela_proc, usuario_id
            )
            
            if not alumno_id:
                flash("Error al guardar alumno (posible CURP duplicado)", "error")
                return redirect(request.url)

            # 3. Vincular con Tutor
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT tutor_id FROM tutores WHERE usuario_id = %s", (usuario_id,))
            res_tutor = cursor.fetchone()
            if res_tutor:
                vincular_alumno_a_tutor(alumno_id, res_tutor['tutor_id'])

            # 4. PROCESAR DOCUMENTOS (Mapeo Optimizado)
            docs_map = {
                'doc_acta': 'acta_nac',
                'doc_curp': 'curp',
                'doc_cartilla': 'cartilla_vac',
                'doc_foto': 'foto',
                'doc_ine': 'ine_tutor',
                'doc_comprobante': 'comprobante_dom',
                'doc_certificado': 'cert_medico',
                'doc_constancia': 'const_est'
            }
            
            docs_guardados = 0

            for input_name, db_code in docs_map.items():
                file = request.files.get(input_name)
                if file and file.filename:
                    # Buscar ID del tipo de documento
                    cursor.execute("SELECT tipo_doc_id FROM tipos_documento WHERE codigo = %s", (db_code,))
                    res_tipo = cursor.fetchone()
                    
                    if res_tipo:
                        tipo_id = res_tipo['tipo_doc_id']
                        # Guardar físico
                        url = guardar_archivo(file, alumno_id, db_code)
                        
                        if url:
                            # Guardar en BD
                            mime = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
                            cursor.execute("""
                                INSERT INTO documento_alumno 
                                (alumno_id, tipo_doc_id, archivo_url, nombre_archivo, mime_type, uploaded_by, status, fecha_subida)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', NOW())
                                ON CONFLICT (alumno_id, tipo_doc_id) DO UPDATE SET
                                archivo_url = EXCLUDED.archivo_url,
                                nombre_archivo = EXCLUDED.nombre_archivo,
                                fecha_subida = NOW(),
                                status = 'pendiente'
                            """, (alumno_id, tipo_id, url, secure_filename(file.filename), mime, usuario_id))
                            docs_guardados += 1
            
            conn.commit()

            # 5. Crear Inscripción (Opcional)
            escuela_id = request.form.get('escuela_id')
            grado_id = request.form.get('grado_id')
            
            inscripcion_creada = False
            if escuela_id and grado_id:
                cursor.execute("SELECT ciclo_id, inscripciones_abiertas FROM ciclos WHERE activo = TRUE LIMIT 1")
                ciclo = cursor.fetchone()
                
                if ciclo and ciclo['inscripciones_abiertas']:
                    cursor.execute("""
                        INSERT INTO inscripciones (alumno_id, escuela_id, ciclo_id, grado_id, status, usuario_responsable)
                        VALUES (%s, %s, %s, %s, 'pendiente', %s)
                    """, (alumno_id, escuela_id, ciclo['ciclo_id'], grado_id, usuario_id))
                    conn.commit()
                    inscripcion_creada = True

            msg = f"Alumno registrado con {docs_guardados} documentos."
            if inscripcion_creada: msg += " Inscripción enviada."
            
            flash(msg, "success")
            return redirect(url_for('panel_tutor.panel_tutor'))

        except Exception as e:
            print(f"❌ Error registro: {e}")
            traceback.print_exc()
            if conn: conn.rollback()
            flash("Ocurrió un error inesperado", "error")
            return redirect(request.url)
        finally:
            if conn: conn.close()

@registro_alumno_bp.route('/validar-curp', methods=['POST'])
def validar_curp():
    """Endpoint AJAX para validar CURP"""
    curp = request.json.get('curp', '').strip().upper()
    
    if len(curp) != 18:
        return jsonify({'valido': False, 'mensaje': 'El CURP debe tener 18 caracteres'})
    
    if curp_existe(curp):
        return jsonify({'valido': False, 'mensaje': 'Este CURP ya está registrado'})
    
    return jsonify({'valido': True, 'mensaje': 'CURP disponible'})