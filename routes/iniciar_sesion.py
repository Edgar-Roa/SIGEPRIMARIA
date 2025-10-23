from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from models.database import get_connection
from werkzeug.security import check_password_hash
from datetime import datetime

iniciar_sesion_bp = Blueprint('iniciar_sesion', __name__)

@iniciar_sesion_bp.route('/login', methods=['GET', 'POST'])
def iniciar_sesion():
    """Inicio de sesión para todos los usuarios"""
    
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validaciones básicas
        if not all([correo, password]):
            flash("Por favor completa todos los campos", "error")
            return render_template('iniciar_sesion.html')
        
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Buscar usuario por correo
            cursor.execute("""
                SELECT usuario_id, nombre, apellido_paterno, apellido_materno, 
                       correo, password_hash, rol, activo
                FROM usuarios
                WHERE correo = %s
            """, (correo,))
            
            usuario = cursor.fetchone()
            
            # Verificar si existe el usuario
            if not usuario:
                flash("Correo o contraseña incorrectos", "error")
                return render_template('iniciar_sesion.html')
            
            # Verificar si está activo
            if not usuario['activo']:
                flash("Esta cuenta ha sido desactivada. Contacta al administrador", "error")
                return render_template('iniciar_sesion.html')
            
            # Verificar contraseña
            if not check_password_hash(usuario['password_hash'], password):
                flash("Correo o contraseña incorrectos", "error")
                return render_template('iniciar_sesion.html')
            
            # Actualizar último login
            cursor.execute("""
                UPDATE usuarios
                SET ultimo_login = %s
                WHERE usuario_id = %s
            """, (datetime.now(), usuario['usuario_id']))
            conn.commit()
            
            # Crear sesión
            session['usuario_id'] = usuario['usuario_id']
            session['rol'] = usuario['rol']
            session['nombre'] = usuario['nombre']
            session['correo'] = usuario['correo']
            
            # Redireccionar según el rol
            if usuario['rol'] == 'tutor':
                return redirect(url_for('panel_tutor.panel_tutor'))
            elif usuario['rol'] in ['super_admin', 'sep_admin']:
                return redirect(url_for('panel_admin.panel_admin'))
            elif usuario['rol'] == 'director':
                return redirect(url_for('panel_director.panel_director'))
            elif usuario['rol'] == 'docente':
                return redirect(url_for('panel_docente.panel_docente'))
            else:
                flash("Rol de usuario no reconocido", "error")
                return render_template('iniciar_sesion.html')
            
        except Exception as e:
            print(f"❌ Error en inicio de sesión: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            flash("Ocurrió un error al iniciar sesión", "error")
            return render_template('iniciar_sesion.html')
        finally:
            if conn:
                conn.close()
    
    # GET - Mostrar formulario
    return render_template('iniciar_sesion.html')


@iniciar_sesion_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash("Sesión cerrada exitosamente", "success")
    return redirect(url_for('inicio.inicio'))