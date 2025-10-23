"""
Decoradores de autenticación y autorización
Evita duplicación de código en las rutas
"""
from flask import session, redirect, url_for, flash
from functools import wraps

def login_requerido(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página", "error")
            return redirect(url_for('iniciar_sesion.iniciar_sesion'))
        return f(*args, **kwargs)
    return decorated_function

def tutor_requerido(f):
    """Decorador para rutas que solo pueden acceder tutores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'tutor':
            flash("No tienes permisos para acceder a esta página", "error")
            return redirect(url_for('inicio.inicio'))
        return f(*args, **kwargs)
    return decorated_function

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

def sep_admin_requerido(f):
    """Decorador para rutas que solo pueden acceder administradores SEP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'sep_admin':
            flash("No tienes permisos para acceder a esta página", "error")
            return redirect(url_for('inicio.inicio'))
        return f(*args, **kwargs)
    return decorated_function

def director_requerido(f):
    """Decorador para rutas que solo pueden acceder directores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'director':
            flash("No tienes permisos para acceder a esta página", "error")
            return redirect(url_for('inicio.inicio'))
        return f(*args, **kwargs)
    return decorated_function

def roles_requeridos(*roles_permitidos):
    """
    Decorador flexible que permite múltiples roles
    Uso: @roles_requeridos('tutor', 'director')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rol = session.get('rol')
            if rol not in roles_permitidos:
                flash("No tienes permisos para acceder a esta página", "error")
                return redirect(url_for('inicio.inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator