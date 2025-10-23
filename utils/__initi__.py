"""
Utilidades compartidas del proyecto
"""
from .decorators import (
    login_requerido,
    tutor_requerido,
    admin_requerido,
    sep_admin_requerido,
    director_requerido,
    roles_requeridos
)

__all__ = [
    'login_requerido',
    'tutor_requerido',
    'admin_requerido',
    'sep_admin_requerido',
    'director_requerido',
    'roles_requeridos'
]